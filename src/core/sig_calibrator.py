"""
sig_calibrator.py
Closed-Form Offline & Rolling Calibrator for Signature Trading (Sig-Trading).
Implements Theorem 3.1 & Theorem 13 from Futter et al. (2023):
- Empirical estimation of mu_sig and Sigma_sig
- Tikhonov-regularized analytical solution for l*
- Scaling lambda against target variance Delta
- Signature Efficient Frontier curve generation
- JSON artifact persistence
"""

import json
import os
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.core.sig_math import normalize_path, hoff_lead_lag, compute_signature, get_signature_dim


def calibrate_sigtrade(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_price_col: str = "close",
    lookback_window: int = 48,
    stride: int = 2,
    order: int = 2,
    gamma: float = 1e-4,
    target_variance_delta: float = 0.01
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict]:
    """
    Calibrates closed-form optimal signature trading linear functional l*.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Historical price dataframe.
    feature_cols : List[str]
        List of feature column names (including asset prices and exogenous signals).
    target_price_col : str
        Target asset column name.
    lookback_window : int
        Lookback horizon W (number of candles).
    stride : int
        Step size between historical sample windows.
    order : int
        Signature truncation order M (default 2).
    gamma : float
        Tikhonov (Ridge) regularization parameter for numerical stability.
    target_variance_delta : float
        Target maximum variance of terminal PnL Delta.
        
    Returns:
    --------
    optimal_l : np.ndarray
        Optimal linear functional vector l*.
    mu_sig : np.ndarray
        Signature expected return vector.
    Sigma_sig : np.ndarray
        Signature covariance matrix.
    metadata : Dict
        Calibration statistics, expected return, variance, and configuration.
    """
    features_data = df[feature_cols].values.astype(np.float64)
    price_data = df[target_price_col].values.astype(np.float64)
    T_total = len(df)
    
    sample_sigs = []
    sample_returns = []
    
    # 1. Slide window across historical dataset
    for start in range(0, T_total - lookback_window - 1, stride):
        end = start + lookback_window
        window_raw = features_data[start:end]
        
        # Calculate forward return of the underlying asset
        p0 = price_data[end - 1]
        p1 = price_data[end]
        ret = (p1 - p0) / (p0 + 1e-12)
        
        # Normalize and lift window
        norm_w = normalize_path(window_raw)
        ll_w = hoff_lead_lag(norm_w)
        sig = compute_signature(ll_w, order=order)
        
        sample_sigs.append(sig)
        sample_returns.append(ret)
        
    if len(sample_sigs) < 10:
        raise ValueError(f"Insufficient sample paths ({len(sample_sigs)}). Need longer data history or smaller window/stride.")
        
    S = np.array(sample_sigs, dtype=np.float64)      # Shape: (K, sig_dim)
    R = np.array(sample_returns, dtype=np.float64)   # Shape: (K,)
    K, sig_dim = S.shape
    
    # 2. Construct empirical PnL attribution matrix Y (K x sig_dim)
    # Each row is the signature modulated by realized forward return
    Y = S * R[:, np.newaxis]
    
    # 3. Estimate mu_sig and Sigma_sig
    mu_sig = np.mean(Y, axis=0) # Expected signature return vector
    
    # Sample covariance matrix
    diff = Y - mu_sig
    Sigma_sig = (diff.T @ diff) / (K - 1)
    
    # 4. Tikhonov Regularization & Matrix Inversion
    reg_matrix = Sigma_sig + gamma * np.eye(sig_dim)
    inv_Sigma = np.linalg.pinv(reg_matrix)
    
    # 5. Closed-form unscaled solution: inv(Sigma) @ mu
    unscaled_l = inv_Sigma @ mu_sig
    
    # 6. Risk-aversion scaling lambda (Theorem 3.1)
    quad_form = float(mu_sig.T @ unscaled_l)
    if quad_form <= 0:
        quad_form = 1e-8
        
    # Scale to target variance Delta: Var(V_T) = l^T Sigma l <= Delta
    scaling = np.sqrt(target_variance_delta) / (np.sqrt(quad_form) + 1e-12)
    optimal_l = unscaled_l * scaling
    
    # Portfolio performance metrics under calibration
    expected_pnl = float(optimal_l.T @ mu_sig)
    actual_var = float(optimal_l.T @ Sigma_sig @ optimal_l)
    sharpe_calib = expected_pnl / (np.sqrt(actual_var) + 1e-12)
    
    metadata = {
        "order": order,
        "lookback_window": lookback_window,
        "stride": stride,
        "gamma": gamma,
        "target_variance_delta": target_variance_delta,
        "num_samples": K,
        "signature_dim": sig_dim,
        "feature_cols": feature_cols,
        "expected_pnl": expected_pnl,
        "actual_variance": actual_var,
        "sharpe_calib": sharpe_calib
    }
    
    return optimal_l, mu_sig, Sigma_sig, metadata


def generate_efficient_frontier(
    mu_sig: np.ndarray,
    Sigma_sig: np.ndarray,
    gamma: float = 1e-4,
    delta_range: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes points on the Signature Efficient Frontier:
    Expected Return E[V_T] vs Standard Deviation sqrt(Var(V_T)).
    
    Returns:
    --------
    std_devs, expected_returns
    """
    if delta_range is None:
        delta_range = np.logspace(-5, -1, 50)
        
    sig_dim = len(mu_sig)
    inv_cov = np.linalg.pinv(Sigma_sig + gamma * np.eye(sig_dim))
    unscaled_l = inv_cov @ mu_sig
    quad_form = float(mu_sig.T @ unscaled_l)
    
    expected_returns = []
    std_devs = []
    
    for delta in delta_range:
        scaling = np.sqrt(delta) / (np.sqrt(max(quad_form, 1e-12)) + 1e-12)
        l_delta = unscaled_l * scaling
        
        ret = float(l_delta.T @ mu_sig)
        var = float(l_delta.T @ Sigma_sig @ l_delta)
        
        expected_returns.append(ret)
        std_devs.append(np.sqrt(max(var, 0.0)))
        
    return np.array(std_devs), np.array(expected_returns)


def save_weights(optimal_l: np.ndarray, metadata: Dict, filepath: str = "models/sigtrade_weights.json"):
    """Saves calibrated weights vector and configuration to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    payload = {
        "metadata": metadata,
        "weights": optimal_l.tolist()
    }
    with open(filepath, "w") as f:
        json.dump(payload, f, indent=2)


def load_weights(filepath: str = "models/sigtrade_weights.json") -> Tuple[np.ndarray, Dict]:
    """Loads weights and metadata from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Weights file not found at: {filepath}")
    with open(filepath, "r") as f:
        payload = json.load(f)
    weights = np.array(payload["weights"], dtype=np.float64)
    metadata = payload.get("metadata", {})
    return weights, metadata
