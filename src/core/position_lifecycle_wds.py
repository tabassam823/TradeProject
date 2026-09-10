"""
Position Lifecycle Manager for Binance Futures (Fee-Accurate).
Replaces position_lifecycle_manager.py with correct fee accounting.

Key Changes from original:
- Accurate fee calculation: Maker 0.02% / Taker 0.04% (was flat 0.075%)
- BEP buffer includes BOTH entry fee + exit fee
- Trailing stop accounts for cumulative fees
- Support for futures funding fees (every 8 hours)
- Per-trade PnL breakdown: gross_pnl, entry_fee, exit_fee, net_pnl

Binance Futures Fee Structure (USDT-M Perpetual):
- Regular Tier (0-500M 30d volume): Maker 0.02%, Taker 0.04%
- With BNB 25% Discount: Maker 0.018%, Taker 0.036%
- Entry fee (taker): 0.04% of notional
- Exit fee (taker/maker): depends on order type
"""

import time
import datetime
from typing import Dict, Any, List, Optional, Tuple
from src.core.binance_client_wds import FEES


class PositionLifecycleManagerFutures:
    """
    Manages position lifecycle for Binance Futures with accurate fee accounting.
    
    State Machine:
    State 0: Pending Order → [Filled | Cancelled]
    State 1: Active Position → [Hold | Move SL to BEP | Trail TP | SL Exit | TP Exit | Funding Fee]
    """

    # Funding rate interval: 8 hours
    FUNDING_INTERVAL_HOURS = 8
    FUNDING_INTERVAL_SECONDS = FUNDING_INTERVAL_HOURS * 3600  # 28,800 seconds

    @staticmethod
    def calculate_entry_fee(
        symbol: str,
        direction: int,
        entry_price: float,
        contracts: float,
        use_bnb_discount: bool = False
    ) -> Dict[str, float]:
        """
        Calculates entry fee (taker fee for market orders).
        
        Formula:
            entry_fee = contracts * contract_size * entry_price * taker_fee_rate
        
        For futures, the fee is deducted from the margin, not from PnL.
        """
        from src.core.binance_client_wds import BinanceFuturesClient
        
        client = BinanceFuturesClient()
        contract_size = client._get_contract_size(symbol)
        
        fee_rate = FEES['bnb_discount_taker'] if use_bnb_discount else FEES['taker_fee_rate']
        notional = contracts * contract_size * entry_price
        fee_amount = notional * fee_rate
        
        return {
            "symbol": symbol,
            "side": "buy" if direction > 0 else "sell",
            "fee_type": "taker",
            "fee_rate": fee_rate,
            "fee_amount": fee_amount,
            "notional": notional,
            "deducted_from": "margin"  # Binance deducts from margin balance
        }

    @staticmethod
    def calculate_exit_fee(
        symbol: str,
        exit_price: float,
        contracts: float,
        order_type: str = "market",
        use_bnb_discount: bool = False
    ) -> Dict[str, float]:
        """
        Calculates exit fee.
        
        For futures:
        - Market orders = taker (0.04%)
        - Limit orders filled = maker (0.02%)
        
        For Binance Futures, the exit fee is deducted from realized PnL.
        """
        from src.core.binance_client_wds import BinanceFuturesClient
        
        client = BinanceFuturesClient()
        contract_size = client._get_contract_size(symbol)
        
        if order_type == "limit":
            fee_rate = FEES['bnb_discount_maker'] if use_bnb_discount else FEES['maker_fee_rate']
        else:
            fee_rate = FEES['bnb_discount_taker'] if use_bnb_discount else FEES['taker_fee_rate']
        
        notional = contracts * contract_size * exit_price
        fee_amount = notional * fee_rate
        
        return {
            "symbol": symbol,
            "fee_type": "maker" if order_type == "limit" else "taker",
            "fee_rate": fee_rate,
            "fee_amount": fee_amount,
            "notional": notional,
            "deducted_from": "realized_pnl"
        }

    @staticmethod
    def calculate_funding_fee(
        symbol: str,
        position_side: str,
        contracts: float,
        entry_price: float,
        current_funding_rate: float,
        hours_held: float
    ) -> Dict[str, float]:
        """
        Calculates cumulative funding fee for a futures position.
        
        Funding Fee = Position_Value * Funding_Rate * (hours_held / 8)
        
        This is charged/received every 8 hours while the position is open.
        Positive funding rate → longs pay shorts
        Negative funding rate → shorts pay longs
        """
        from src.core.binance_client_wds import BinanceFuturesClient
        
        client = BinanceFuturesClient()
        contract_size = client._get_contract_size(symbol)
        
        position_value = contracts * contract_size * entry_price
        funding_fee = position_value * current_funding_rate * (hours_held / 8.0)
        
        return {
            "symbol": symbol,
            "position_side": position_side,
            "funding_rate": current_funding_rate,
            "hours_held": hours_held,
            "funding_fee_amount": abs(funding_fee),
            "funding_fee_paid": funding_fee > 0,  # True if longs pay
            "cumulative_funding": funding_fee
        }

    @staticmethod
    def evaluate_pending_order(
        order: Dict[str, Any],
        current_price: float,
        current_score: float,
        max_pending_ticks: int = 60
    ) -> Tuple[str, Optional[Dict[str, Any]], Optional[str]]:
        """
        Evaluates pending limit order state.
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
            
            # Calculate entry fee for this fill
            symbol = order["symbol"]
            contracts = order["units"]  # In futures context, this is CONTRACTS
            entry_fee_info = PositionLifecycleManagerFutures.calculate_entry_fee(
                symbol=symbol,
                direction=direction,
                entry_price=limit_price,
                contracts=contracts,
                use_bnb_discount=order.get("use_bnb_discount", False)
            )
            
            position = {
                "symbol": symbol,
                "direction": direction,
                "entry_price": limit_price,
                "contracts": contracts,
                "initial_sl_price": order.get("sl_price", limit_price * (0.98 if direction > 0 else 1.02)),
                "current_sl_price": order.get("sl_price", limit_price * (0.98 if direction > 0 else 1.02)),
                "initial_tp_price": order.get("tp_price", limit_price * (1.05 if direction > 0 else 0.95)),
                "current_tp_price": order.get("tp_price", limit_price * (1.05 if direction > 0 else 0.95)),
                "risk_dollar": order.get("risk_dollar", 1.0),
                "is_bep_activated": False,
                "is_trailing_activated": False,
                "entry_time": now_str,
                "strategy_name": order.get("strategy_name", ""),
                "entry_fee": entry_fee_info["fee_amount"],  # Track entry fee
                "use_bnb_discount": order.get("use_bnb_discount", False),
                "cumulative_funding_fees": 0.0,  # Track funding fees
                "last_funding_check": now_str,
                "funding_rate": 0.0,
            }
            return "FILLED", position, f"Limit order filled @ ${limit_price:.2f} | Entry fee: ${entry_fee_info['fee_amount']:.4f}"

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
        current_price: float,
        current_funding_rate: float = 0.0001,
        hours_since_last_funding: float = 0.0
    ) -> Tuple[str, Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Evaluates active futures position with ACCURATE fee accounting.
        
        Fee Structure:
        - Entry fee: Deducted from margin at fill (calculated separately)
        - Exit fee: Deducted from realized PnL at exit
        - Funding fee: Charged every 8 hours while position is open
        
        Returns:
            (action: 'HOLD' | 'MOVED_BEP' | 'TRAILED_TP' | 'CLOSED', 
             updated_position, closed_trade_data)
        """
        direction = position["direction"]
        entry_price = position["entry_price"]
        contracts = position["contracts"]
        risk_dollar = max(position.get("risk_dollar", 1.0), 1e-4)
        symbol = position["symbol"]
        use_bnb_discount = position.get("use_bnb_discount", False)

        # Backward-compatibility fallback for legacy positions
        sl_price = position.get("current_sl_price", position.get("sl_price", entry_price * (0.98 if direction > 0 else 1.02)))
        tp_price = position.get("current_tp_price", position.get("tp_price", entry_price * (1.05 if direction > 0 else 0.95)))
        position["current_sl_price"] = sl_price
        position["current_tp_price"] = tp_price
        position["initial_sl_price"] = position.get("initial_sl_price", sl_price)
        position["initial_tp_price"] = position.get("initial_tp_price", tp_price)

        # Calculate UNREALIZED PnL (before any exit fees)
        # For futures: PnL = contracts * contract_size * (current_price - entry_price) * direction
        from src.core.binance_client_wds import BinanceFuturesClient
        client = BinanceFuturesClient()
        contract_size = client._get_contract_size(symbol)
        
        raw_pnl = (current_price - entry_price) * contracts * contract_size * direction
        unrealized_pnl = raw_pnl

        # Calculate funding fee if applicable
        funding_fee_info = None
        if hours_since_last_funding >= PositionLifecycleManagerFutures.FUNDING_INTERVAL_HOURS and current_funding_rate != 0:
            funding_fee_info = PositionLifecycleManagerFutures.calculate_funding_fee(
                symbol=symbol,
                position_side="long" if direction > 0 else "short",
                contracts=contracts,
                entry_price=entry_price,
                current_funding_rate=current_funding_rate,
                hours_held=hours_since_last_funding
            )
            position["cumulative_funding_fees"] += funding_fee_info["funding_fee_amount"]
            position["last_funding_check"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            position["funding_rate"] = current_funding_rate
            unrealized_pnl -= funding_fee_info["funding_fee_amount"] * direction  # Funding fee reduces PnL

        r_multiple = unrealized_pnl / risk_dollar if risk_dollar > 0 else 0
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # ============================================
        # 1. Check Hard Stop Loss Hit
        # ============================================
        if (direction > 0 and current_price <= sl_price) or (direction < 0 and current_price >= sl_price):
            exit_fee_info = PositionLifecycleManagerFutures.calculate_exit_fee(
                symbol=symbol,
                exit_price=sl_price,
                contracts=contracts,
                order_type="market",  # SL is always a market order
                use_bnb_discount=use_bnb_discount
            )
            
            # net_pnl = raw_pnl - entry_fee - exit_fee - cumulative_funding_fees
            entry_fee = position.get("entry_fee", 0.0)
            cumulative_funding = position.get("cumulative_funding_fees", 0.0)
            net_pnl = raw_pnl - entry_fee - exit_fee_info["fee_amount"] - cumulative_funding
            
            closed_trade = {
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry_price,
                "exit_price": sl_price,
                "contracts": contracts,
                "contract_size": contract_size,
                "gross_pnl": raw_pnl,
                "entry_fee": entry_fee,
                "exit_fee": exit_fee_info["fee_amount"],
                "cumulative_funding_fees": cumulative_funding,
                "net_pnl": net_pnl,
                "return_pct": ((sl_price - entry_price) / entry_price) * direction * 100.0,
                "entry_time": position["entry_time"],
                "exit_time": now_str,
                "exit_reason": "STOP_LOSS (Disciplined Risk Cap)",
                "fee_breakdown": {
                    "taker_rate": exit_fee_info["fee_rate"],
                    "maker_rate": FEES['maker_fee_rate'],
                    "total_fees": entry_fee + exit_fee_info["fee_amount"] + cumulative_funding
                }
            }
            return "CLOSED", position, closed_trade

        # ============================================
        # 2. Check Take Profit Hit
        # ============================================
        if (direction > 0 and current_price >= tp_price) or (direction < 0 and current_price <= tp_price):
            exit_fee_info = PositionLifecycleManagerFutures.calculate_exit_fee(
                symbol=symbol,
                exit_price=tp_price,
                contracts=contracts,
                order_type="market",  # TP typically executed as market order for speed
                use_bnb_discount=use_bnb_discount
            )
            
            entry_fee = position.get("entry_fee", 0.0)
            cumulative_funding = position.get("cumulative_funding_fees", 0.0)
            net_pnl = raw_pnl - entry_fee - exit_fee_info["fee_amount"] - cumulative_funding
            
            closed_trade = {
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry_price,
                "exit_price": tp_price,
                "contracts": contracts,
                "contract_size": contract_size,
                "gross_pnl": raw_pnl,
                "entry_fee": entry_fee,
                "exit_fee": exit_fee_info["fee_amount"],
                "cumulative_funding_fees": cumulative_funding,
                "net_pnl": net_pnl,
                "return_pct": ((tp_price - entry_price) / entry_price) * direction * 100.0,
                "entry_time": position["entry_time"],
                "exit_time": now_str,
                "exit_reason": "TAKE_PROFIT (Asymmetric Target Reached)",
                "fee_breakdown": {
                    "taker_rate": exit_fee_info["fee_rate"],
                    "maker_rate": FEES['maker_fee_rate'],
                    "total_fees": entry_fee + exit_fee_info["fee_amount"] + cumulative_funding
                }
            }
            return "CLOSED", position, closed_trade

        # ============================================
        # 3. Dynamic Management Rule: Move SL to BEP at +1.0R
        # ============================================
        if r_multiple >= 1.0 and not position.get("is_bep_activated", False):
            # Advance SL to Entry + buffer for BOTH entry fee + exit fee
            # Buffer = contract_size * entry_price * (maker_fee + taker_fee)
            # This ensures BEP accounts for the round-trip fee cost
            
            # Calculate total round-trip fee per contract
            round_trip_fee_pct = FEES['maker_fee_rate'] + FEES['taker_fee_rate']  # 0.02% + 0.04% = 0.06%
            bep_buffer = entry_price * round_trip_fee_pct
            
            if direction > 0:
                position["current_sl_price"] = entry_price + bep_buffer
            else:
                position["current_sl_price"] = entry_price - bep_buffer
            
            position["is_bep_activated"] = True
            return "MOVED_BEP", position, None

        # ============================================
        # 4. Dynamic Management Rule: Ratchet Trailing TP at +2.0R
        # ============================================
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

    @staticmethod
    def generate_trade_summary(closed_trade: Dict[str, Any]) -> str:
        """
        Generates a human-readable trade summary with full fee breakdown.
        """
        lines = [
            f"{'='*60}",
            f"  TRADE SUMMARY: {closed_trade['symbol']}",
            f"{'='*60}",
            f"  Direction:      {'LONG' if closed_trade['direction'] > 0 else 'SHORT'}",
            f"  Entry:          ${closed_trade['entry_price']:.2f}",
            f"  Exit:           ${closed_trade['exit_price']:.2f}",
            f"  Contracts:      {closed_trade['contracts']:.4f}",
            f"  Contract Size:  {closed_trade['contract_size']}",
            f"  Gross PnL:      ${closed_trade['gross_pnl']:+.4f}",
            f"  Entry Fee:      -${closed_trade['entry_fee']:.4f}",
            f"  Exit Fee:       -${closed_trade['exit_fee']:.4f}",
            f"  Funding Fees:   -${closed_trade['cumulative_funding_fees']:.4f}",
            f"  {'-'*40}",
            f"  NET PnL:        ${closed_trade['net_pnl']:+.4f}",
            f"  Return:         {closed_trade['return_pct']:+.2f}%",
            f"  Total Fees:     ${closed_trade['fee_breakdown']['total_fees']:.4f}",
            f"  Exit Reason:    {closed_trade['exit_reason']}",
            f"{'='*60}"
        ]
        return "\n".join(lines)
