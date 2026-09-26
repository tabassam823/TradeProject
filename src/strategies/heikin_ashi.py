"""
heikin_ashi.py
Heikin-Ashi Trend Following Strategy.
Adapted from quant-trading (Heikin-Ashi backtest.py).
Extends BaseStrategy.

Algorithm:
1. HA_Close = (Open + High + Low + Close) / 4
2. HA_Open = (HA_Open_prev + HA_Close_prev) / 2
3. HA_High = max(High, HA_Open, HA_Close)
4. HA_Low = min(Low, HA_Open, HA_Close)
5. Evaluates consecutive solid candle sequences (no lower/upper wicks) for trend momentum in [-4.0, +4.0].
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from src.strategies.base_strategy import BaseStrategy


class HeikinAshiTrendStrategy(BaseStrategy):
    """
    Heikin-Ashi Smoothed Trend Following Strategy.
    Filters market noise and rides strong directional moves.
    """
    def __init__(self, name: str = "heikin_ashi_trend", config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        super().__init__(name, cfg)
        self.lookback = cfg.get("lookback", 10)

    def generate_signal(self, ohlcv_df: pd.DataFrame) -> float:
        """Calculates Heikin-Ashi trend signal in range [-4.0, +4.0]."""
        if not self.enabled or ohlcv_df is None or len(ohlcv_df) < self.lookback + 5:
            return 0.0

        sub_df = ohlcv_df.iloc[-(self.lookback + 5):].copy()

        ha_close = (sub_df["open"] + sub_df["high"] + sub_df["low"] + sub_df["close"]) / 4.0
        ha_open = np.zeros(len(sub_df))

        # Initial seed
        ha_open[0] = (sub_df["open"].iloc[0] + sub_df["close"].iloc[0]) / 2.0
        for i in range(1, len(sub_df)):
            ha_open[i] = (ha_open[i - 1] + ha_close.iloc[i - 1]) / 2.0

        ha_high = np.maximum(sub_df["high"].values, np.maximum(ha_open, ha_close.values))
        ha_low = np.minimum(sub_df["low"].values, np.minimum(ha_open, ha_close.values))

        # Evaluate recent N candles
        streak = 0
        for i in range(-self.lookback, 0):
            o_val = ha_open[i]
            c_val = ha_close.iloc[i]
            h_val = ha_high[i]
            l_val = ha_low[i]

            body = abs(c_val - o_val)
            rng = h_val - l_val + 1e-12

            if c_val > o_val:
                # Green candle
                lower_wick = o_val - l_val
                # If no lower wick or very small (< 10% of body) -> Strong Bullish
                if lower_wick / (body + 1e-12) < 0.15:
                    streak = streak + 1 if streak >= 0 else 1
                else:
                    streak = max(1, streak)
            elif c_val < o_val:
                # Red candle
                upper_wick = h_val - o_val
                # If no upper wick or very small (< 10% of body) -> Strong Bearish
                if upper_wick / (body + 1e-12) < 0.15:
                    streak = streak - 1 if streak <= 0 else -1
                else:
                    streak = min(-1, streak)
            else:
                streak = 0

        # Scale streak to [-4.0, +4.0]
        score = np.clip(streak * 0.8, -4.0, 4.0)
        return float(score)
