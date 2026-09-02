"""
Advanced Risk & Position Sizing Engine.
Implements Tahap C, D & Tahap N from ChatGPT/MD_Source + 23 Agustus 2026 Upgrades:
- Strict Risk Constraint (R_max <= $1.00 or fractional budget).
- Regime-Adaptive ATR SL/TP Scaling (expands SL distance in Crisis/Chop while reducing lot units N).
- Exact Lot Units (N = Risk / |P_entry - P_SL|) and Leverage calculation.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional

class VolatilityTargetPositionSizer:
    """
    Asset-Agnostic Position Sizing Engine.
    Ensures mathematical expected value is maximized while keeping trade downside
    strictly constrained to the risk budget ($1.00 or allocated percentage).
    """
    def __init__(self, max_risk_per_trade: float = 0.02, min_volatility: float = 0.005):
        self.max_risk_per_trade = max_risk_per_trade
        self.min_volatility = min_volatility

    def calculate_volatility(self, ohlcv_df: pd.DataFrame, window: int = 21) -> float:
        """Calculates rolling volatility of returns."""
        if ohlcv_df is None or len(ohlcv_df) < window:
            return 0.02
        returns = ohlcv_df['close'].pct_change().dropna()
        vol = returns.tail(window).std()
        if pd.isna(vol) or vol < self.min_volatility:
            vol = self.min_volatility
        return float(vol)

    def calculate_tiered_risk_dollar(self, capital: float) -> float:
        """
        Tiered Risk Budgeting:
        - Capital <= $100: Risk fixed $1.00 per trade.
        - Capital > $100: Risk 1% of capital per trade.
        """
        if capital <= 100.0:
            return 1.00
        else:
            return capital * 0.01

    def calculate_sl_tp_levels(
        self,
        entry_price: float,
        direction: int,
        volatility: float,
        rr_ratio: float = 2.5,
        regime: Optional[str] = None
    ) -> Tuple[float, float, float]:
        """
        Calculates Stop Loss (1.0R) and Take Profit (rr_ratio * 1.0R) levels with Regime Adaptation.
        In HIGH_VOLATILITY_CRISIS or MEAN_REVERSION_CHOP, scales SL distance up to 2.5x to prevent whipsaws.
        """
        # Regime-adaptive scaling multiplier
        if regime in ["HIGH_VOLATILITY_CRISIS", "MEAN_REVERSION_CHOP"]:
            sl_multiplier = 2.8
            min_sl_distance_pct = 0.025 # 2.5% minimum breathing room
        else:
            sl_multiplier = 1.5
            min_sl_distance_pct = 0.010 # 1.0% minimum breathing room

        sl_pct = max(volatility * sl_multiplier, min_sl_distance_pct)
        tp_pct = sl_pct * rr_ratio

        if direction > 0: # Long
            sl_price = entry_price * (1.0 - sl_pct)
            tp_price = entry_price * (1.0 + tp_pct)
        else: # Short
            sl_price = entry_price * (1.0 + sl_pct)
            tp_price = entry_price * (1.0 - tp_pct)

        return round(sl_price, 4), round(tp_price, 4), sl_pct

    def calculate_exact_lot_units(
        self,
        entry_price: float,
        sl_price: float,
        risk_dollar: float
    ) -> float:
        """
        Calculates exact unit quantity N such that:
        N * |P_entry - P_SL| = risk_dollar
        """
        sl_distance = abs(entry_price - sl_price)
        if sl_distance <= 1e-6:
            return 0.0
        return float(risk_dollar / sl_distance)

    def calculate_position_size(
        self,
        current_price: float,
        capital: float,
        score: float,
        volatility: float,
        risk_budget_ratio: float = 0.01,
        is_circuit_broken: bool = False,
        regime: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes position direction, target value, and exact units bounded by risk constraint.
        """
        if is_circuit_broken or abs(score) < 0.5 or current_price <= 0:
            return {
                "direction": 0,
                "target_value": 0.0,
                "units": 0.0,
                "sl_price": 0.0,
                "tp_price": 0.0,
                "risk_dollar": 0.0
            }

        direction = 1 if score > 0 else -1
        conviction = min(abs(score) / 4.0, 1.0)

        # Risk dollar allocation
        base_risk_dollar = self.calculate_tiered_risk_dollar(capital)
        trade_risk_dollar = base_risk_dollar * conviction

        sl_price, tp_price, sl_pct = self.calculate_sl_tp_levels(
            entry_price=current_price,
            direction=direction,
            volatility=volatility,
            rr_ratio=2.5,
            regime=regime
        )

        units = self.calculate_exact_lot_units(
            entry_price=current_price,
            sl_price=sl_price,
            risk_dollar=trade_risk_dollar
        )

        target_value = units * current_price

        # Cap max position value to 2x capital (2x max leverage limit for safety)
        if target_value > capital * 2.0:
            target_value = capital * 2.0
            units = target_value / current_price

        return {
            "direction": direction,
            "target_value": float(target_value),
            "units": float(units),
            "sl_price": float(sl_price),
            "tp_price": float(tp_price),
            "risk_dollar": float(trade_risk_dollar),
            "sl_pct": float(sl_pct)
        }
