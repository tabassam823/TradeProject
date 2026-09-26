"""
signature_trading.py
Closed-Form Signature Trading Strategy implementing Futter et al. (2023).
Extends BaseStrategy. Computes path signature online from sliding window
and applies optimal linear functional l* to produce continuous signal score.
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from src.strategies.base_strategy import BaseStrategy
from src.core.sig_math import normalize_path, hoff_lead_lag, compute_signature
from src.core.sig_calibrator import load_weights


class SignatureTradingStrategy(BaseStrategy):
    """
    Signature Trading Strategy (Closed-Form Analytical Solution).
    Maps joint market factor paths to dynamic portfolio positions.
    """
    def __init__(self, name: str = "signature_trading", config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        super().__init__(name, cfg)
        
        self.truncation_order = cfg.get("truncation_order", 2)
        self.lookback_window = cfg.get("lookback_window", 48)
        self.weights_file = cfg.get("weights_file", "models/sigtrade_weights.json")
        self.scaling_factor = cfg.get("scaling_factor", 1.0)
        self.feature_cols = cfg.get("feature_cols", ["close", "volume"])
        
        self.weights: Optional[np.ndarray] = None
        self.metadata: Dict[str, Any] = {}
        
        self._load_or_init_weights()
        
    def _load_or_init_weights(self):
        """Attempts to load pre-calibrated weights."""
        try:
            self.weights, self.metadata = load_weights(self.weights_file)
            self.truncation_order = self.metadata.get("order", self.truncation_order)
            self.lookback_window = self.metadata.get("lookback_window", self.lookback_window)
        except Exception:
            # If no weights exist yet, use zeros until calibrated
            self.weights = None
            
    def set_weights(self, weights: np.ndarray, metadata: Dict[str, Any]):
        """Directly assigns calibrated weights."""
        self.weights = weights
        self.metadata = metadata
        self.truncation_order = metadata.get("order", self.truncation_order)
        self.lookback_window = metadata.get("lookback_window", self.lookback_window)
        
    def generate_signal(self, ohlcv_df: pd.DataFrame) -> float:
        """
        Calculates signal score from latest OHLCV data.
        Returns float in range [-4.0, +4.0].
        """
        if not self.enabled:
            return 0.0
            
        if self.weights is None:
            # Fallback when weights not yet calibrated
            return 0.0
            
        if len(ohlcv_df) < self.lookback_window:
            return 0.0
            
        # 1. Extract sliding window
        window_df = ohlcv_df.iloc[-self.lookback_window:].copy()
        
        # Available feature columns
        cols = [c for c in self.feature_cols if c in window_df.columns]
        if not cols:
            cols = ["close"]
            
        raw_path = window_df[cols].values.astype(np.float64)
        
        # 2. Normalize and lift to lead-lag
        norm_path = normalize_path(raw_path)
        ll_path = hoff_lead_lag(norm_path)
        
        # 3. Compute truncated signature
        sig = compute_signature(ll_path, order=self.truncation_order)
        
        if len(sig) != len(self.weights):
            # Dimension mismatch protection
            min_len = min(len(sig), len(self.weights))
            raw_score = float(np.dot(self.weights[:min_len], sig[:min_len]))
        else:
            raw_score = float(np.dot(self.weights, sig))
            
        # 4. Map to [-4.0, +4.0] via hyperbolic tangent
        scaled_score = 4.0 * np.tanh(raw_score * self.scaling_factor)
        return float(np.clip(scaled_score, -4.0, 4.0))
