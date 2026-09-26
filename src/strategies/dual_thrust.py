"""
dual_thrust.py
Dual Thrust Opening Range Breakout Strategy.
Adapted from quant-trading (Dual Thrust backtest.py).
Extends BaseStrategy.

Algorithm:
1. Range = max(HH - LC, HC - LL) over lookback period N.
2. Upper Threshold = Open + k1 * Range
3. Lower Threshold = Open - k2 * Range
4. Breakout above Upper -> Long (+4.0)
   Breakout below Lower -> Short (-4.0)
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from src.strategies.base_strategy import BaseStrategy


class DualThrustStrategy(BaseStrategy):
    """
    Dual Thrust Breakout Strategy.
    Famous classical CTA trend-following breakout system.
    """
    def __init__(self, name: str = "dual_thrust", config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        super().__init__(name, cfg)
        self.lookback = cfg.get("lookback", 14)
        self.k1 = cfg.get("k1", 0.5)
        self.k2 = cfg.get("k2", 0.5)

    def generate_signal(self, ohlcv_df: pd.DataFrame) -> float:
        """
        Calculates Dual Thrust breakout score in range [-4.0, +4.0].
        """
        if not self.enabled or ohlcv_df is None or len(ohlcv_df) < self.lookback + 2:
            return 0.0

        sub_df = ohlcv_df.iloc[-(self.lookback + 1):-1]
        current_candle = ohlcv_df.iloc[-1]

        hh = float(sub_df["high"].max())
        hc = float(sub_df["close"].max())
        lc = float(sub_df["close"].min())
        ll = float(sub_df["low"].min())

        # Range calculation according to Michael Chalek's formula
        range_val = max(hh - lc, hc - ll)
        if range_val <= 1e-8:
            return 0.0

        current_open = float(current_candle["open"])
        current_close = float(current_candle["close"])

        upper_bound = current_open + self.k1 * range_val
        lower_bound = current_open - self.k2 * range_val

        if current_close > upper_bound:
            # Bullish breakout
            overshoot = (current_close - upper_bound) / range_val
            score = 3.0 + min(1.0, overshoot * 2.0)
            return float(np.clip(score, -4.0, 4.0))
        elif current_close < lower_bound:
            # Bearish breakout
            undershoot = (lower_bound - current_close) / range_val
            score = -3.0 - min(1.0, undershoot * 2.0)
            return float(np.clip(score, -4.0, 4.0))
        else:
            # Inside neutral range
            rel_pos = (current_close - lower_bound) / (upper_bound - lower_bound) - 0.5
            return float(rel_pos * 2.0)
