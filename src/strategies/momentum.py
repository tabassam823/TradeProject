import numpy as np
import pandas as pd
from typing import Dict, Any, List
from src.strategies.base_strategy import BaseStrategy

class MultiHorizonMomentumStrategy(BaseStrategy):
    """
    Multi-Horizon Time Series Momentum Strategy based on Man AHL research paper (HedgeFund.md).
    Calculates consensus trend signal across multiple lookback windows (e.g. 5, 10, 21, 42).
    Score S = sum(sign(P_t - P_{t-tau_i})) in [-4, +4].
    """
    def __init__(self, name: str = "momentum_multi_horizon", config: Dict[str, Any] = None):
        if config is None:
            config = {
                "enabled": True,
                "horizons": [5, 10, 21, 42],
                "risk_budget": 0.01
            }
        super().__init__(name, config)
        self.horizons: List[int] = config.get("horizons", [5, 10, 21, 42])

    def generate_signal(self, ohlcv_df: pd.DataFrame) -> float:
        """Calculates multi-horizon momentum score."""
        if ohlcv_df is None or len(ohlcv_df) < max(self.horizons) + 1:
            return 0.0

        current_close = ohlcv_df['close'].iloc[-1]
        signals = []

        for tau in self.horizons:
            past_close = ohlcv_df['close'].iloc[-(tau + 1)]
            diff = current_close - past_close
            if diff > 0:
                signals.append(1.0)
            elif diff < 0:
                signals.append(-1.0)
            else:
                signals.append(0.0)

        accumulated_score = float(np.sum(signals))
        return accumulated_score
