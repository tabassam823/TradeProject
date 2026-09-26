"""
deep_sig_strategy.py
Deep Signature & Sequential PyTorch Trading Strategy.
Extends BaseStrategy. Performs online inference using trained PyTorch models
(SigNetMLP or TimeSeriesLSTM) to predict continuous optimal trading positions.
"""

import os
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import torch

from src.strategies.base_strategy import BaseStrategy
from src.core.sig_math import normalize_path, hoff_lead_lag, compute_signature
from src.core.sig_torch_models import create_model
from src.core.sig_torch_trainer import load_checkpoint


class DeepSignatureTradingStrategy(BaseStrategy):
    """
    PyTorch Machine Learning Strategy for dynamic portfolio allocation.
    Evaluates trained neural network in real-time.
    """
    def __init__(self, name: str = "deep_sig_trading", config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        super().__init__(name, cfg)
        
        self.checkpoint_file = cfg.get("checkpoint_file", "models/torch_checkpoints/best_model.pt")
        self.architecture = cfg.get("architecture", "SigNetMLP")
        self.lookback_window = cfg.get("lookback_window", 48)
        self.signature_order = cfg.get("signature_order", 2)
        self.use_signature = cfg.get("use_signature", True)
        self.feature_cols = cfg.get("feature_cols", ["close", "volume"])
        
        self.model: Optional[torch.nn.Module] = None
        self.metadata: Dict[str, Any] = {}
        
        self._load_model()
        
    def _load_model(self):
        """Loads model checkpoint if file exists."""
        if not os.path.exists(self.checkpoint_file):
            self.model = None
            return
            
        try:
            # Inspect metadata first to build exact architecture
            checkpoint = torch.load(self.checkpoint_file, map_location="cpu")
            meta = checkpoint.get("metadata", {})
            self.metadata = meta
            
            input_dim = meta.get("feature_dim", 15)
            arch = meta.get("architecture", self.architecture)
            self.lookback_window = meta.get("lookback_window", self.lookback_window)
            self.use_signature = meta.get("use_signature", self.use_signature)
            self.signature_order = meta.get("signature_order", self.signature_order)
            
            model = create_model(arch, input_dim=input_dim)
            model.load_state_dict(checkpoint["state_dict"])
            model.eval()
            self.model = model
        except Exception:
            self.model = None
            
    def set_model(self, model: torch.nn.Module, metadata: Dict[str, Any]):
        """Directly sets an in-memory trained model."""
        self.model = model
        self.model.eval()
        self.metadata = metadata
        self.lookback_window = metadata.get("lookback_window", self.lookback_window)
        self.use_signature = metadata.get("use_signature", self.use_signature)
        self.signature_order = metadata.get("signature_order", self.signature_order)
        
    def generate_signal(self, ohlcv_df: pd.DataFrame) -> float:
        """
        Runs forward neural inference on latest market window.
        Returns float in range [-4.0, +4.0].
        """
        if not self.enabled or self.model is None:
            return 0.0
            
        if len(ohlcv_df) < self.lookback_window:
            return 0.0
            
        window_df = ohlcv_df.iloc[-self.lookback_window:].copy()
        cols = [c for c in self.feature_cols if c in window_df.columns]
        if not cols:
            cols = ["close"]
            
        raw_path = window_df[cols].values.astype(np.float64)
        norm_path = normalize_path(raw_path)
        
        with torch.no_grad():
            if self.use_signature:
                ll_path = hoff_lead_lag(norm_path)
                sig = compute_signature(ll_path, order=self.signature_order)
                tensor_in = torch.from_numpy(sig.astype(np.float32)).unsqueeze(0) # (1, sig_dim)
            else:
                tensor_in = torch.from_numpy(norm_path.astype(np.float32)).unsqueeze(0) # (1, T, D)
                
            out = self.model(tensor_in)
            position = float(out.item()) # in [-1.0, 1.0]
            
        # Scale to standard [-4.0, +4.0] signal strength
        return float(np.clip(position * 4.0, -4.0, 4.0))
