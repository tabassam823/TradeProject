import numpy as np
import pandas as pd
from typing import Dict, Any
from src.strategies.base_strategy import BaseStrategy

class VWAPRejectionStrategy(BaseStrategy):
    """
    VWAP Value Area Rejection Strategy based on Drysdale Trading Math (strategy.md).
    Identifies mean-reversion trades when price reaches extreme standard deviation bands from VWAP.
    """
    def __init__(self, name: str = "vwap_mean_reversion", config: Dict[str, Any] = None):
        if config is None:
            config = {
                "enabled": True,
                "vwap_window": 24,
                "num_std": 2.0,
                "risk_budget": 0.01
            }
        super().__init__(name, config)
        self.vwap_window = config.get("vwap_window", 24)
        self.num_std = config.get("num_std", 2.0)

    def generate_signal(self, ohlcv_df: pd.DataFrame) -> float:
        """Calculates VWAP value area mean-reversion signal."""
        if ohlcv_df is None or len(ohlcv_df) < self.vwap_window:
            return 0.0

        sub_df = ohlcv_df.tail(self.vwap_window).copy()
        
        # Calculate Typical Price
        tp = (sub_df['high'] + sub_df['low'] + sub_df['close']) / 3.0
        volume = sub_df['volume']

        # Volume-Weighted Average Price
        vwap = (tp * volume).sum() / (volume.sum() + 1e-8)
        
        # Standard deviation around VWAP
        std = np.sqrt(((tp - vwap) ** 2 * volume).sum() / (volume.sum() + 1e-8))
        
        upper_band = vwap + (self.num_std * std)
        lower_band = vwap - (self.num_std * std)

        current_close = sub_df['close'].iloc[-1]
        prev_close = sub_df['close'].iloc[-2]

        # Lower band rejection (oversold -> Long signal +2.0)
        if prev_close <= lower_band and current_close > lower_band:
            return 2.0
            
        # Upper band rejection (overbought -> Short signal -2.0)
        if prev_close >= upper_band and current_close < upper_band:
            return -2.0

        return 0.0
