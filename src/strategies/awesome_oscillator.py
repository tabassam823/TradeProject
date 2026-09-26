"""
awesome_oscillator.py
Awesome Oscillator (AO) Momentum Strategy.
Adapted from quant-trading (Awesome Oscillator backtest.py).
Extends BaseStrategy.

Algorithm:
1. Median Price MP = (High + Low) / 2
2. AO = SMA(MP, fast_period) - SMA(MP, slow_period)
3. Zero-line cross & Saucer momentum patterns map to signal score [-4.0, +4.0].
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from src.strategies.base_strategy import BaseStrategy


class AwesomeOscillatorStrategy(BaseStrategy):
    """
    Awesome Oscillator Momentum Strategy.
    Compares 5-period and 34-period moving averages of bar midpoints.
    """
    def __init__(self, name: str = "awesome_oscillator", config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        super().__init__(name, cfg)
        self.fast_period = cfg.get("fast_period", 5)
        self.slow_period = cfg.get("slow_period", 34)

    def generate_signal(self, ohlcv_df: pd.DataFrame) -> float:
        """Calculates AO momentum signal in range [-4.0, +4.0]."""
        if not self.enabled or ohlcv_df is None or len(ohlcv_df) < self.slow_period + 3:
            return 0.0

        median_price = (ohlcv_df["high"] + ohlcv_df["low"]) / 2.0
        fast_sma = median_price.rolling(window=self.fast_period).mean()
        slow_sma = median_price.rolling(window=self.slow_period).mean()

        ao = fast_sma - slow_sma

        current_ao = ao.iloc[-1]
        prev_ao = ao.iloc[-2]
        prev2_ao = ao.iloc[-3]

        if np.isnan(current_ao) or np.isnan(prev_ao):
            return 0.0

        # Normalization scaling factor (percentage of price)
        close_price = ohlcv_df["close"].iloc[-1]
        ao_rel = (current_ao / (close_price + 1e-12)) * 100.0

        # Base score from oscillator magnitude and sign
        score = np.tanh(ao_rel * 2.0) * 3.0

        # Saucer pattern detection:
        # Bullish saucer: AO > 0, prev_ao < prev2_ao, and current_ao > prev_ao
        if current_ao > 0 and current_ao > prev_ao and prev_ao < prev2_ao:
            score += 1.0
        # Bearish saucer: AO < 0, prev_ao > prev2_ao, and current_ao < prev_ao
        elif current_ao < 0 and current_ao < prev_ao and prev_ao > prev2_ao:
            score -= 1.0

        return float(np.clip(score, -4.0, 4.0))
