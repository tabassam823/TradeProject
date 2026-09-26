"""
bollinger_mean_reversion.py
Bollinger Bands Mean Reversion Strategy.
Adapted from quant-trading and Goldman Sachs gs_quant (technicals.py).
Extends BaseStrategy.

Algorithm:
1. Middle Band = SMA(Close, period)
2. Upper / Lower Bands = Middle +/- k * StdDev(Close, period)
3. %B = (Close - Lower) / (Upper - Lower)
4. Counter-trend mean reversion signal triggered on band penetration & reversal.
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from src.strategies.base_strategy import BaseStrategy


class BollingerMeanReversionStrategy(BaseStrategy):
    """
    Bollinger Bands Statistical Mean Reversion Strategy.
    Exploits price overextension beyond Gaussian standard deviation envelopes.
    """
    def __init__(self, name: str = "bollinger_mean_reversion", config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        super().__init__(name, cfg)
        self.period = cfg.get("period", 20)
        self.k = cfg.get("num_std", 2.0)

    def generate_signal(self, ohlcv_df: pd.DataFrame) -> float:
        """Calculates Bollinger mean reversion signal in range [-4.0, +4.0]."""
        if not self.enabled or ohlcv_df is None or len(ohlcv_df) < self.period + 2:
            return 0.0

        close = ohlcv_df["close"]
        sma = close.rolling(window=self.period).mean()
        std = close.rolling(window=self.period).std(ddof=0)

        middle = sma.iloc[-1]
        vol = std.iloc[-1]

        if np.isnan(middle) or vol <= 1e-8:
            return 0.0

        upper = middle + self.k * vol
        lower = middle - self.k * vol

        cur_close = close.iloc[-1]
        prev_close = close.iloc[-2]

        pct_b = (cur_close - lower) / (upper - lower + 1e-12)

        # Mean Reversion Logic:
        # 1. Extreme Oversold (Price pierced lower band and turns up) -> Long
        if pct_b < 0.05 and cur_close > prev_close:
            oversold_intensity = max(0.0, (0.05 - pct_b) * 10.0)
            score = 3.0 + min(1.0, oversold_intensity)
            return float(score)
        # 2. Extreme Overbought (Price pierced upper band and turns down) -> Short
        elif pct_b > 0.95 and cur_close < prev_close:
            overbought_intensity = max(0.0, (pct_b - 0.95) * 10.0)
            score = -3.0 - min(1.0, overbought_intensity)
            return float(score)
        # 3. Intermediate z-score reversion
        else:
            z_score = (cur_close - middle) / vol
            # Inverse z-score for mean reversion (negative z-score -> positive long bias)
            score = -np.clip(z_score, -3.0, 3.0)
            # Damping as it approaches middle band
            if abs(pct_b - 0.5) < 0.1:
                score *= 0.5
            return float(score)
