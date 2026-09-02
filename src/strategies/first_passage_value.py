"""
First-Passage Value & Asymmetric Probability Strategy.
Implements Tahap C, D & Tahap AD from ChatGPT/MD_Source + Drysdale Trading Math (strategy.md):
- Gaussian Value Area Boundary First-Passage (Reversion to Center of Gravity).
- Asymmetric Expected Value Gate: E[X] = (P_win * R_reward) - (P_loss * R_risk) > 0.
- Asymmetric Risk:Reward target (1:2.5 to 1:3.0).
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from src.strategies.base_strategy import BaseStrategy
from src.core.math_engine import MathEngine

class FirstPassageValueStrategy(BaseStrategy):
    """
    First-Passage Probability Strategy.
    Enters trades only when mathematical Expected Value E[X] is positive and
    price is positioned at extreme Value Area boundaries.
    """
    def __init__(self, name: str = "first_passage_value", config: Dict[str, Any] = None):
        if config is None:
            config = {
                "enabled": True,
                "vwap_window": 24,
                "entry_num_std": 1.8,
                "reward_risk_ratio": 2.5,
                "estimated_win_rate": 0.42,
                "risk_budget": 0.015
            }
        super().__init__(name, config)
        self.vwap_window = config.get("vwap_window", 24)
        self.num_std = config.get("entry_num_std", 1.8)
        self.rr_ratio = config.get("reward_risk_ratio", 2.5)
        self.est_win_rate = config.get("estimated_win_rate", 0.42)

    def generate_signal(self, ohlcv_df: pd.DataFrame, market_state: Optional[Dict[str, Any]] = None) -> float:
        """
        Evaluates First-Passage value rejection condition with Expected Value validation.
        Returns float score in [-4.0, +4.0].
        """
        if ohlcv_df is None or len(ohlcv_df) < self.vwap_window:
            return 0.0

        # Step 1: Validate Expected Value E[X] > 0
        expected_val = MathEngine.calculate_expected_value(
            win_rate=self.est_win_rate,
            reward_r=self.rr_ratio,
            risk_r=1.0
        )
        if expected_val <= 0:
            return 0.0

        # Step 2: Calculate VWAP Gaussian Bands & Standardized Distance
        vwap, upper_band, lower_band, z_dist = MathEngine.calculate_vwap_bands(
            df=ohlcv_df,
            window=self.vwap_window,
            num_std=self.num_std
        )

        sub_df = ohlcv_df.tail(self.vwap_window)
        current_close = sub_df['close'].iloc[-1]
        prev_close = sub_df['close'].iloc[-2]
        curr_lower = lower_band.iloc[-1]
        curr_upper = upper_band.iloc[-1]

        # Check for Rejection / Return to Value:
        # Long Setup: Price tagged below lower band and rebounded inside Value Area
        if prev_close <= curr_lower and current_close > curr_lower:
            conviction = float(np.clip(1.5 + (abs(z_dist) * 0.5), 1.0, 3.5))
            return conviction

        # Short Setup: Price tagged above upper band and rejected back inside
        if prev_close >= curr_upper and current_close < curr_upper:
            conviction = float(np.clip(1.5 + (abs(z_dist) * 0.5), 1.0, 3.5))
            return -conviction

        return 0.0
