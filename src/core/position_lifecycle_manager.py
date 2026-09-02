"""
Sequential Position Lifecycle & Model Predictive Control (MPC) Manager.
Implements Tahap E, O, P, U & AC from ChatGPT/MD_Source + 23 Agustus 2026 Upgrades:
- Order Placement & Unfilled Pending Order Lifecycle (Extended 60-tick patience window).
- Filled Active Position Lifecycle:
  * Floating Loss: Disciplined hold to hard Stop Loss (no emotional early exit).
  * Floating Profit >= +1.0R: Advance Stop Loss to Break-Even (BEP + fees).
  * Floating Profit >= +2.0R: Elevate Take Profit & Ratchet Dynamic Trailing Stop.
"""

import time
import datetime
from typing import Dict, Any, List, Optional, Tuple

class PositionLifecycleManager:
    """
    Manages the sequential state transition of trading orders and open positions:
    State 0: Pending Order in Book -> [Filled | Cancelled/Replaced]
    State 1: Active Position -> [Hold | Move SL to BEP | Trail TP | SL Exit | TP Exit]
    """

    @staticmethod
    def evaluate_pending_order(
        order: Dict[str, Any],
        current_price: float,
        current_score: float,
        max_pending_ticks: int = 60
    ) -> Tuple[str, Optional[Dict[str, Any]], Optional[str]]:
        """
        Evaluates pending limit order state.
        Default max_pending_ticks = 60 (30 minutes on 30s cadence).
        """
        direction = order["direction"]
        limit_price = order["limit_price"]
        ticks_alive = order.get("ticks_alive", 0) + 1
        order["ticks_alive"] = ticks_alive

        # Check Fill Condition
        is_filled = False
        if direction > 0 and current_price <= limit_price:
            is_filled = True
        elif direction < 0 and current_price >= limit_price:
            is_filled = True

        if is_filled:
            now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            position = {
                "symbol": order["symbol"],
                "direction": direction,
                "entry_price": limit_price,
                "units": order["units"],
                "initial_sl_price": order.get("sl_price", limit_price * (0.98 if direction > 0 else 1.02)),
                "current_sl_price": order.get("sl_price", limit_price * (0.98 if direction > 0 else 1.02)),
                "initial_tp_price": order.get("tp_price", limit_price * (1.05 if direction > 0 else 0.95)),
                "current_tp_price": order.get("tp_price", limit_price * (1.05 if direction > 0 else 0.95)),
                "risk_dollar": order.get("risk_dollar", 1.0),
                "is_bep_activated": False,
                "is_trailing_activated": False,
                "entry_time": now_str,
                "strategy_name": order.get("strategy_name", "")
            }
            return "FILLED", position, f"Limit order filled @ ${limit_price:.2f}"

        # Invalidation check: strong signal reversal
        if (direction > 0 and current_score < -1.5) or (direction < 0 and current_score > 1.5):
            return "CANCELLED", None, "Signal strongly reversed before fill. Cancelled and re-optimizing."

        # Invalidation check: price drifted too far (> 3.0% away from limit price)
        price_drift = abs(current_price - limit_price) / limit_price
        if price_drift > 0.03:
            return "CANCELLED", None, f"Price drifted {price_drift:.2%}. Cancelled limit order."

        # Invalidation check: time-in-force expiry (60 ticks / 30 mins)
        if ticks_alive >= max_pending_ticks:
            return "CANCELLED", None, f"Pending order patience window expired ({ticks_alive} ticks). Cancelled."

        return "KEEP", None, "Order remains in order book within valid execution corridor."

    @staticmethod
    def evaluate_active_position(
        position: Dict[str, Any],
        current_price: float
    ) -> Tuple[str, Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Evaluates active position and applies MPC lifecycle rules:
        - Floating Loss: Hold to hard Stop Loss.
        - Floating Profit >= +1.0R: Move Stop Loss to BEP.
        - Floating Profit >= +2.0R: Ratchet Trailing TP & Lock profit.
        Returns: (action: 'HOLD' | 'MOVED_BEP' | 'TRAILED_TP' | 'CLOSED', updated_position, closed_trade_data)
        """
        direction = position["direction"]
        entry_price = position["entry_price"]
        units = position["units"]
        risk_dollar = max(position.get("risk_dollar", 1.0), 1e-4)
        
        # Backward-compatibility fallback for legacy positions
        sl_price = position.get("current_sl_price", position.get("sl_price", entry_price * (0.98 if direction > 0 else 1.02)))
        tp_price = position.get("current_tp_price", position.get("tp_price", entry_price * (1.05 if direction > 0 else 0.95)))
        position["current_sl_price"] = sl_price
        position["current_tp_price"] = tp_price
        position["initial_sl_price"] = position.get("initial_sl_price", sl_price)
        position["initial_tp_price"] = position.get("initial_tp_price", tp_price)

        # Calculate unrealized PnL & R-multiples
        unrealized_pnl = (current_price - entry_price) * units * (1 if direction > 0 else -1)
        r_multiple = unrealized_pnl / risk_dollar
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 1. Check Hard Stop Loss Hit
        if (direction > 0 and current_price <= sl_price) or (direction < 0 and current_price >= sl_price):
            fee = abs(units * current_price) * 0.00075
            net_pnl = ((sl_price - entry_price) * units * (1 if direction > 0 else -1)) - fee
            closed_trade = {
                "symbol": position["symbol"],
                "direction": direction,
                "entry_price": entry_price,
                "exit_price": sl_price,
                "net_pnl": net_pnl,
                "return_pct": ((sl_price - entry_price) / entry_price) * (1 if direction > 0 else -1) * 100.0,
                "entry_time": position["entry_time"],
                "exit_time": now_str,
                "exit_reason": "STOP_LOSS (Disciplined Risk Cap)"
            }
            return "CLOSED", position, closed_trade

        # 2. Check Take Profit Hit
        if (direction > 0 and current_price >= tp_price) or (direction < 0 and current_price <= tp_price):
            fee = abs(units * current_price) * 0.00075
            net_pnl = ((tp_price - entry_price) * units * (1 if direction > 0 else -1)) - fee
            closed_trade = {
                "symbol": position["symbol"],
                "direction": direction,
                "entry_price": entry_price,
                "exit_price": tp_price,
                "net_pnl": net_pnl,
                "return_pct": ((tp_price - entry_price) / entry_price) * (1 if direction > 0 else -1) * 100.0,
                "entry_time": position["entry_time"],
                "exit_time": now_str,
                "exit_reason": "TAKE_PROFIT (Asymmetric Target Reached)"
            }
            return "CLOSED", position, closed_trade

        # 3. Dynamic Management Rule: Move SL to Break-Even (BEP) at +1.0R
        if r_multiple >= 1.0 and not position.get("is_bep_activated", False):
            # Advance SL to Entry + buffer for fees
            bep_buffer = entry_price * 0.001
            if direction > 0:
                position["current_sl_price"] = entry_price + bep_buffer
            else:
                position["current_sl_price"] = entry_price - bep_buffer
                
            position["is_bep_activated"] = True
            return "MOVED_BEP", position, None

        # 4. Dynamic Management Rule: Ratchet Trailing TP & Lock profit at +2.0R
        if r_multiple >= 2.0 and not position.get("is_trailing_activated", False):
            # Lock in +1.0R profit on Stop Loss and extend Take Profit target
            lock_price_dist = (entry_price * (abs(entry_price - position["initial_sl_price"]) / entry_price))
            if direction > 0:
                position["current_sl_price"] = entry_price + lock_price_dist
                position["current_tp_price"] = position["initial_tp_price"] + lock_price_dist
            else:
                position["current_sl_price"] = entry_price - lock_price_dist
                position["current_tp_price"] = position["initial_tp_price"] - lock_price_dist

            position["is_trailing_activated"] = True
            return "TRAILED_TP", position, None

        return "HOLD", position, None
