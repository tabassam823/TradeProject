"""
sig_torch_trainer.py
Training Pipeline for PyTorch Signature & Sequential Financial Models.
Provides:
- Data windowing & dataset creation (Signature and Sequential)
- Training & validation loop with early stopping
- Live callback integration for Streamlit progress bars & loss plotting
- Checkpointing (.pt)
"""

import os
from typing import Callable, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset

from src.core.sig_math import normalize_path, hoff_lead_lag, compute_signature


def prepare_training_data(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_price_col: str = "close",
    lookback_window: int = 48,
    forward_horizon: int = 1,
    stride: int = 2,
    use_signature: bool = True,
    signature_order: int = 2,
    val_split: float = 0.2
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, Dict]:
    """
    Constructs sliding window datasets for training PyTorch models.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Historical price data with feature columns.
    feature_cols : List[str]
        Columns to use as features (e.g., ['close', 'volume', 'parkinson_vol']).
    target_price_col : str
        Asset price column for calculating forward return.
    lookback_window : int
        Window length (W candles).
    forward_horizon : int
        Steps ahead to evaluate return.
    stride : int
        Step size between sliding windows.
    use_signature : bool
        If True, transforms each window into truncated signature vector.
    signature_order : int
        Truncation level M.
    val_split : float
        Proportion of chronological data to reserve for validation.
        
    Returns:
    --------
    X_train, y_train, X_val, y_val, metadata
    """
    total_len = len(df)
    features_data = df[feature_cols].values.astype(np.float64)
    price_data = df[target_price_col].values.astype(np.float64)
    
    X_list = []
    y_list = []
    
    max_idx = total_len - forward_horizon
    for start in range(0, max_idx - lookback_window, stride):
        end = start + lookback_window
        window_raw = features_data[start:end]
        
        # Calculate forward percentage return
        p_now = price_data[end - 1]
        p_future = price_data[end - 1 + forward_horizon]
        fwd_ret = (p_future - p_now) / (p_now + 1e-12)
        
        # Normalize window path
        norm_window = normalize_path(window_raw)
        
        if use_signature:
            # Lift to lead-lag and compute truncated signature
            ll_window = hoff_lead_lag(norm_window)
            sig = compute_signature(ll_window, order=signature_order)
            X_list.append(sig)
        else:
            # Sequential input for LSTM: shape (lookback_window, num_features)
            X_list.append(norm_window)
            
        y_list.append(fwd_ret)
        
    X_arr = np.array(X_list, dtype=np.float32)
    y_arr = np.array(y_list, dtype=np.float32).reshape(-1, 1)
    
    # Chronological train/val split (anti-lookahead)
    split_idx = int(len(X_arr) * (1.0 - val_split))
    
    X_train = torch.from_numpy(X_arr[:split_idx])
    y_train = torch.from_numpy(y_arr[:split_idx])
    X_val = torch.from_numpy(X_arr[split_idx:])
    y_val = torch.from_numpy(y_arr[split_idx:])
    
    metadata = {
        "num_samples": len(X_arr),
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "feature_dim": X_train.shape[-1],
        "use_signature": use_signature,
        "signature_order": signature_order if use_signature else None,
        "lookback_window": lookback_window,
        "feature_cols": feature_cols
    }
    
    return X_train, y_train, X_val, y_val, metadata


def train_model(
    model: torch.nn.Module,
    X_train: torch.Tensor,
    y_train: torch.Tensor,
    X_val: torch.Tensor,
    y_val: torch.Tensor,
    loss_fn: torch.nn.Module,
    epochs: int = 50,
    batch_size: int = 32,
    lr: float = 0.001,
    weight_decay: float = 1e-4,
    progress_callback: Optional[Callable[[int, int, float, float], None]] = None
) -> Dict:
    """
    Executes training loop with early stopping and live callback.
    
    Returns:
    --------
    Dict containing training history (epochs, train_losses, val_losses, best_val_loss).
    """
    train_dataset = TensorDataset(X_train, y_train)
    val_dataset = TensorDataset(X_val, y_val)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", patience=5, factor=0.5)
    
    history = {
        "epochs": [],
        "train_loss": [],
        "val_loss": [],
        "best_epoch": 0,
        "best_val_loss": float("inf")
    }
    
    best_weights = None
    
    for epoch in range(1, epochs + 1):
        # 1. Training Pass
        model.train()
        train_batch_losses = []
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            positions = model(batch_x)
            loss = loss_fn(positions, batch_y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_batch_losses.append(loss.item())
            
        epoch_train_loss = float(np.mean(train_batch_losses))
        
        # 2. Validation Pass
        model.eval()
        val_batch_losses = []
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                positions = model(batch_x)
                loss = loss_fn(positions, batch_y)
                val_batch_losses.append(loss.item())
                
        epoch_val_loss = float(np.mean(val_batch_losses))
        scheduler.step(epoch_val_loss)
        
        history["epochs"].append(epoch)
        history["train_loss"].append(epoch_train_loss)
        history["val_loss"].append(epoch_val_loss)
        
        if epoch_val_loss < history["best_val_loss"]:
            history["best_val_loss"] = epoch_val_loss
            history["best_epoch"] = epoch
            best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            
        if progress_callback is not None:
            progress_callback(epoch, epochs, epoch_train_loss, epoch_val_loss)
            
    # Restore best weights
    if best_weights is not None:
        model.load_state_dict(best_weights)
        
    return history


def save_checkpoint(model: torch.nn.Module, metadata: Dict, filepath: str):
    """Saves PyTorch model checkpoint and training metadata."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    payload = {
        "state_dict": model.state_dict(),
        "metadata": metadata
    }
    torch.save(payload, filepath)


def load_checkpoint(filepath: str, model: torch.nn.Module) -> Tuple[torch.nn.Module, Dict]:
    """Loads checkpoint into provided model instance."""
    checkpoint = torch.load(filepath, map_location="cpu")
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model, checkpoint.get("metadata", {})
