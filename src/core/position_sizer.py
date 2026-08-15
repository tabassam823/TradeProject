import numpy as np
import pandas as pd
from typing import Dict, Any

class VolatilityTargetPositionSizer:
    """
    Calculates position sizing based on Man AHL Volatility Targeting (HedgeFund.md):
    Position Size = (Score * Risk Budget) / Volatility
    """
    def __init__(self, max_risk_per_trade: float = 0.02, min_volatility: float = 0.005):
        self.max_risk_per_trade = max_risk_per_trade
        self.min_volatility = min_volatility

    def calculate_volatility(self, ohlcv_df: pd.DataFrame, window: int = 21) -> float:
        """Calculates rolling standard deviation of percentage returns."""
        if len(ohlcv_df) < window:
            return 0.02  # Default conservative fallback volatility
        
        returns = ohlcv_df['close'].pct_change().dropna()
        volatility = returns.tail(window).std()
        
        if pd.isna(volatility) or volatility < self.min_volatility:
            volatility = self.min_volatility
            
        return float(volatility)

    def calculate_position_size(
        self,
        current_price: float,
        capital: float,
        score: float,
        volatility: float,
        risk_budget_ratio: float = 0.01,
        is_circuit_broken: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates position size in units and dollar value.
        Score is typically in range [-4.0, +4.0].
        """
        if is_circuit_broken or abs(score) < 0.1 or current_price <= 0 or capital <= 0:
            return {
                "target_units": 0.0,
                "target_value": 0.0,
                "direction": 0,
                "reason": "Circuit broken or neutral signal" if is_circuit_broken else "Zero score"
            }

        # Direction (+1 for Long, -1 for Short)
        direction = 1 if score > 0 else -1
        abs_score = abs(score)

        # Risk budget nominal value
        nominal_risk_budget = capital * risk_budget_ratio

        # Man AHL formula: Position Value = (Score * Risk Budget) / Volatility
        raw_position_value = (abs_score * nominal_risk_budget) / volatility

        # Enforce max risk cap per trade (prevent non-linear drawdown decay)
        max_allowed_value = capital * self.max_risk_per_trade * abs_score
        capped_position_value = min(raw_position_value, max_allowed_value)

        # Calculate target units
        target_units = (capped_position_value * direction) / current_price

        return {
            "target_units": target_units,
            "target_value": capped_position_value * direction,
            "direction": direction,
            "score": score,
            "volatility": volatility,
            "raw_position_value": raw_position_value,
            "capped_position_value": capped_position_value
        }
