import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

class VolatilityTargetPositionSizer:
    """
    Advanced Risk & Position Sizing Engine supporting:
    1. Payoff & Win Rate Expectancy (baseline.md break-even frontier).
    2. Tiered Risk Budgeting ($1 fixed risk for capital < $100, 1% risk for capital >= $100).
    3. Exact Lot & Leverage calculation so trade failure loses strictly target $1 / risk dollar.
    4. Hourly BEP (Break-Even Point) and Dynamic Trailing Stop management.
    """
    def __init__(self, max_risk_per_trade: float = 0.02, min_volatility: float = 0.005):
        self.max_risk_per_trade = max_risk_per_trade
        self.min_volatility = min_volatility

    def calculate_volatility(self, ohlcv_df: pd.DataFrame, window: int = 21) -> float:
        """Calculates rolling standard deviation of percentage returns."""
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
        - Capital < $100: Risk fixed $1.00 per trade.
        - Capital >= $100: Risk 1% of capital per trade.
        """
        if capital < 100.0:
            return 1.00
        else:
            return capital * 0.01

    def calculate_sl_tp_levels(
        self,
        entry_price: float,
        direction: int,
        volatility: float,
        win_rate: float = 0.40,
        min_payoff_margin: float = 1.2
    ) -> Tuple[float, float, float]:
        """
        Calculates Stop Loss and Take Profit levels based on Expected Value & Break-Even Frontier (baseline.md).
        Break-even payoff ratio b_min = (1 - W) / W.
        """
        w = max(min(win_rate, 0.95), 0.05)
        b_min = (1.0 - w) / w
        target_payoff = max(b_min * min_payoff_margin, 1.5)

        sl_pct = max(volatility * 1.5, 0.008)  # Min 0.8% SL distance
        tp_pct = sl_pct * target_payoff

        if direction > 0:
            sl_price = entry_price * (1.0 - sl_pct)
            tp_price = entry_price * (1.0 + tp_pct)
        else:
            sl_price = entry_price * (1.0 + sl_pct)
            tp_price = entry_price * (1.0 - tp_pct)

        return sl_price, tp_price, sl_pct

    def calculate_exact_lot_and_leverage(
        self,
        capital: float,
        entry_price: float,
        sl_price: float,
        risk_dollar: float
    ) -> Dict[str, Any]:
        """
        Calculates exact lot units (N) and required leverage (L) so that touching SL
        results in a loss of EXACTLY risk_dollar ($1.00).
        """
        if entry_price <= 0 or sl_price <= 0 or entry_price == sl_price:
            return {"units": 0.0, "position_value": 0.0, "required_leverage": 1.0}

        sl_distance = abs(entry_price - sl_price)
        sl_pct = sl_distance / entry_price

        units = risk_dollar / sl_distance
        position_value = units * entry_price

        required_leverage = position_value / max(capital, 1.0)
        required_leverage = max(round(required_leverage, 1), 1.0)

        return {
            "units": units,
            "position_value": position_value,
            "required_leverage": required_leverage,
            "sl_distance_pct": sl_pct * 100.0,
            "risk_dollar": risk_dollar
        }

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
        Calculates position size in units and dollar value (Man AHL + Tiered Risk).
        """
        if is_circuit_broken or abs(score) < 0.1 or current_price <= 0 or capital <= 0:
            return {
                "target_units": 0.0,
                "target_value": 0.0,
                "direction": 0,
                "reason": "Circuit broken or neutral signal" if is_circuit_broken else "Zero score"
            }

        direction = 1 if score > 0 else -1
        abs_score = abs(score)

        # Use Tiered Risk Dollar ($1.00 if capital < $100, else 1% of capital)
        nominal_risk_budget = self.calculate_tiered_risk_dollar(capital)

        # Man AHL Volatility Targeting: Position Value = (Score * Risk Budget) / Volatility
        raw_position_value = (abs_score * nominal_risk_budget) / volatility

        max_allowed_value = capital * self.max_risk_per_trade * abs_score
        capped_position_value = min(raw_position_value, max_allowed_value)

        target_units = (capped_position_value * direction) / current_price

        # Also calculate SL/TP and exact leverage needed for $1 loss cap
        sl_price, tp_price, sl_pct = self.calculate_sl_tp_levels(current_price, direction, volatility)
        lot_leverage = self.calculate_exact_lot_and_leverage(capital, current_price, sl_price, nominal_risk_budget)

        return {
            "target_units": target_units,
            "target_value": capped_position_value * direction,
            "direction": direction,
            "score": score,
            "volatility": volatility,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "risk_dollar": nominal_risk_budget,
            "required_leverage": lot_leverage["required_leverage"]
        }

    def evaluate_bep_and_trailing_stop(
        self,
        position: Dict[str, Any],
        current_price: float,
        volatility: float,
        fee_buffer_pct: float = 0.001
    ) -> Dict[str, Any]:
        """
        Evaluates position on hourly tick:
        1. Moves SL to BEP (Break-Even Point) when running profit >= 1R ($1 profit).
        2. Trails SL above entry price as profit increases (Locking in profit).
        """
        direction = position["direction"]
        entry_price = position["entry_price"]
        current_sl = position.get("sl_price", entry_price)
        risk_dollar = position.get("risk_dollar", 1.00)
        units = position["units"]

        running_pnl = (current_price - entry_price) * units
        updated_sl = current_sl
        sl_status = "HOLD"

        bep_price = entry_price * (1.0 + fee_buffer_pct) if direction > 0 else entry_price * (1.0 - fee_buffer_pct)

        if running_pnl >= risk_dollar:
            if (direction > 0 and current_sl < bep_price) or (direction < 0 and current_sl > bep_price):
                updated_sl = bep_price
                sl_status = "MOVED_TO_BEP"

        if running_pnl >= (1.5 * risk_dollar):
            trail_dist = (volatility * 1.5) * current_price
            if direction > 0:
                proposed_sl = current_price - trail_dist
                if proposed_sl > updated_sl:
                    updated_sl = proposed_sl
                    sl_status = "TRAILING_PROFIT"
            else:
                proposed_sl = current_price + trail_dist
                if proposed_sl < updated_sl:
                    updated_sl = proposed_sl
                    sl_status = "TRAILING_PROFIT"

        return {
            "updated_sl": updated_sl,
            "sl_status": sl_status,
            "running_pnl": running_pnl,
            "is_sl_hit": (current_price <= updated_sl) if direction > 0 else (current_price >= updated_sl),
            "is_tp_hit": (current_price >= position.get("tp_price", float('inf'))) if direction > 0 else (current_price <= position.get("tp_price", 0.0))
        }
