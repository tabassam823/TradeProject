"""
Binance Futures Testnet Client Module for ML Trading.
Integrates exchange filter rules (LOT_SIZE, PRICE_FILTER, MIN_NOTIONAL),
margin validation, leverage management, and on-exchange native bracket orders (TP/SL)
adapted from the check_api engine.
"""
import os
import math
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from binance.client import Client
from binance.enums import *

def load_env_file(filepath: Path):
    """Loads environment variables safely without overwriting non-empty values."""
    if filepath.exists():
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if v and (k not in os.environ or not os.environ[k]):
                        os.environ[k] = v

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_env_file(PROJECT_ROOT / "crypto_ml_trading" / ".env")
load_env_file(PROJECT_ROOT / ".env")

class BinanceTestnetClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        symbol: str = "SOLUSDT",
        leverage: int = 2,
        testnet: bool = True
    ):
        self.api_key = api_key or os.getenv("BINANCE_TESTNET_API_KEY", "")
        self.api_secret = (
            api_secret
            or os.getenv("BINANCE_TESTNET_SECRET_KEY", "")
            or os.getenv("BINANCE_TESTNET_API_SECRET", "")
        )
        self.symbol = symbol.replace("/", "").replace(":USDT", "").replace("-", "").upper()
        self.leverage = leverage
        self.testnet = testnet
        self.is_connected = False
        self.rules = None
        self.client = None

        if self.api_key and self.api_secret:
            self._verify_connection()

    def _verify_connection(self):
        """Initializes python-binance Client and loads symbol trading rules."""
        try:
            print(f"[BINANCE CLIENT] Connecting to Binance Futures (Testnet={self.testnet})...")
            self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
            
            # Test account connectivity
            acc = self.client.futures_account()
            if acc.get('canTrade'):
                self.is_connected = True
                balance = self.get_usdt_balance()
                print(f"[BINANCE CLIENT] Connection SUCCESSFUL! Available USDT: ${balance:,.2f}")
                self.set_leverage(self.leverage)
                self.rules = self.get_symbol_rules(self.symbol)
            else:
                print(f"[BINANCE CLIENT ERROR] Account cannot trade.")
                self.is_connected = False
        except Exception as e:
            print(f"[BINANCE CLIENT ERROR] Connection failed: {e}")
            self.is_connected = False

    def get_symbol_rules(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetches dynamic stepSize, tickSize, minQty, and minNotional filters from Binance Futures.
        """
        sym = symbol or self.symbol
        try:
            info = self.client.futures_exchange_info()
            for s in info.get("symbols", []):
                if s.get("symbol") == sym:
                    rules = {
                        "min_qty": 0.001,
                        "step_size": "0.001",
                        "tick_size": "0.01",
                        "min_notional": 5.0
                    }
                    for f in s.get("filters", []):
                        f_type = f.get("filterType")
                        if f_type == "LOT_SIZE":
                            rules["min_qty"] = float(f.get("minQty", 0.001))
                            rules["step_size"] = f.get("stepSize", "0.001")
                        elif f_type == "PRICE_FILTER":
                            rules["tick_size"] = f.get("tickSize", "0.01")
                        elif f_type == "MIN_NOTIONAL":
                            notional_val = f.get("notional") or f.get("minNotional") or 5.0
                            rules["min_notional"] = float(notional_val)
                    self.rules = rules
                    return rules
            print(f"[BINANCE CLIENT WARNING] Symbol {sym} not found in exchange info. Using defaults.")
        except Exception as e:
            print(f"[BINANCE CLIENT ERROR] Failed to fetch symbol rules: {e}")
            
        fallback = {"min_qty": 0.01, "step_size": "0.01", "tick_size": "0.01", "min_notional": 5.0}
        self.rules = fallback
        return fallback

    def round_step_size(self, value: float, step_size_str: str) -> float:
        """Rounds down to exact stepSize / tickSize precision."""
        step = Decimal(str(step_size_str))
        val = Decimal(str(value))
        rounded = (val // step) * step
        return float(rounded)

    def round_up_step_size(self, value: float, step_size_str: str) -> float:
        """Rounds UP to ensure notional satisfies exchange minimums."""
        step = float(step_size_str)
        precision = len(step_size_str.split(".")[1].rstrip("0")) if "." in step_size_str else 0
        val = math.ceil(value / step) * step
        return round(val, precision)

    def get_usdt_balance(self) -> float:
        """Fetches available USDT balance for margin trading."""
        if not self.is_connected or not self.client:
            return 0.0
        try:
            balances = self.client.futures_account_balance()
            for b in balances:
                if b.get("asset") == "USDT":
                    avail = (
                        b.get("availableBalance")
                        or b.get("maxWithdrawAmount")
                        or b.get("withdrawAvailable")
                        or b.get("crossWalletBalance")
                        or b.get("balance")
                        or 0.0
                    )
                    return float(avail)
        except Exception as e:
            print(f"[BINANCE CLIENT ERROR] Error fetching balance: {e}")
        return 0.0

    def get_current_position(self) -> Dict[str, Any]:
        """
        Queries open position status on Binance Futures.
        """
        if not self.is_connected or not self.client:
            return {'side': 'FLAT', 'contracts': 0.0, 'entryPrice': 0.0, 'unrealizedPnl': 0.0}
        try:
            positions = self.client.futures_position_information(symbol=self.symbol)
            for pos in positions:
                amt = float(pos.get('positionAmt', 0.0))
                if amt != 0.0:
                    return {
                        'side': 'LONG' if amt > 0 else 'SHORT',
                        'contracts': abs(amt),
                        'signed_contracts': amt,
                        'entryPrice': float(pos.get('entryPrice', 0.0)),
                        'unrealizedPnl': float(pos.get('unRealizedProfit', 0.0)),
                        'leverage': int(pos.get('leverage', 1))
                    }
        except Exception as e:
            print(f"[BINANCE CLIENT ERROR] Error fetching position: {e}")
        return {'side': 'FLAT', 'contracts': 0.0, 'entryPrice': 0.0, 'unrealizedPnl': 0.0}

    def set_leverage(self, leverage: int = 2):
        """Sets trading leverage on Binance Futures."""
        if not self.is_connected or not self.client:
            return
        try:
            res = self.client.futures_change_leverage(symbol=self.symbol, leverage=leverage)
            print(f"[BINANCE CLIENT] Leverage for {self.symbol} configured to {res.get('leverage', leverage)}x.")
        except Exception as e:
            print(f"[BINANCE CLIENT NOTICE] Setting leverage: {e}")

    def cancel_all_algo_orders(self):
        """Cancels all open conditional / algo TP & SL orders on symbol to avoid error -4130."""
        if not self.is_connected or not self.client:
            return
        try:
            self.client.futures_cancel_all_algo_open_orders(symbol=self.symbol)
            print(f"[BINANCE CLIENT] Cleared old open Algo (TP/SL) orders on {self.symbol}.")
        except Exception as e:
            # Fallback to cancel standard open orders if algo cancel not supported
            try:
                self.client.futures_cancel_all_open_orders(symbol=self.symbol)
            except Exception:
                pass

    def place_bracket_order(
        self,
        side: str,
        quantity: float,
        tp_price: Optional[float] = None,
        sl_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes an On-Exchange Bracket Order:
        1. Market Entry
        2. Take Profit Market (closePosition=True)
        3. Stop Loss Market (closePosition=True)
        """
        if not self.is_connected or not self.client:
            print("[BINANCE CLIENT] Cannot place order: client not connected.")
            return {'status': 'ERROR', 'msg': 'Client disconnected'}

        rules = self.rules or self.get_symbol_rules(self.symbol)
        ticker = self.client.futures_symbol_ticker(symbol=self.symbol)
        current_price = float(ticker["price"])

        # Calculate minimum quantity & validate notional
        min_qty_by_notional = (rules["min_notional"] * 1.05) / current_price
        raw_min_qty = max(rules["min_qty"], min_qty_by_notional)
        valid_min_qty = self.round_up_step_size(raw_min_qty, rules["step_size"])

        valid_qty = self.round_step_size(quantity, rules["step_size"])
        if valid_qty < valid_min_qty:
            print(f"[BINANCE CLIENT] Sized quantity ({quantity}) below exchange minimum ({valid_min_qty}). Adjusting to minimum.")
            valid_qty = valid_min_qty

        # Margin sufficiency check
        available_usdt = self.get_usdt_balance()
        notional = valid_qty * current_price
        required_margin = notional / self.leverage
        estimated_fee = notional * 0.001
        total_needed = required_margin + estimated_fee

        if available_usdt < total_needed:
            print(f"[BINANCE CLIENT ERROR] Insufficient Margin: Need ${total_needed:.2f} USDT, Available: ${available_usdt:.2f} USDT")
            return {'status': 'INSUFFICIENT_MARGIN', 'msg': 'Margin shortfall'}

        # Prepare orders
        is_long = side.upper() in ('BUY', 'LONG')
        entry_side = SIDE_BUY if is_long else SIDE_SELL
        exit_side = SIDE_SELL if is_long else SIDE_BUY

        # 1. Reset leverage & clear old algo orders
        self.set_leverage(self.leverage)
        self.cancel_all_algo_orders()

        result = {'entry': None, 'tp': None, 'sl': None, 'status': 'PENDING'}

        # 2. Market Entry Order
        try:
            print(f"[BINANCE CLIENT ORDER] [1/3] Submitting MARKET {entry_side} {valid_qty} {self.symbol}...")
            entry = self.client.futures_create_order(
                symbol=self.symbol,
                side=entry_side,
                type=FUTURE_ORDER_TYPE_MARKET,
                quantity=valid_qty
            )
            result['entry'] = entry
            print(f" -> Entry Order Executed! ID: {entry.get('orderId')} | Status: {entry.get('status')}")
        except Exception as e:
            print(f"[BINANCE CLIENT ERROR] Entry order failed: {e}")
            result['status'] = 'ENTRY_FAILED'
            return result

        # 3. Take Profit Market Order (if specified)
        if tp_price is not None and tp_price > 0:
            formatted_tp = self.round_step_size(tp_price, rules["tick_size"])
            try:
                print(f"[BINANCE CLIENT ORDER] [2/3] Placing on-exchange TAKE_PROFIT_MARKET at ${formatted_tp}...")
                tp_order = self.client.futures_create_order(
                    symbol=self.symbol,
                    side=exit_side,
                    type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
                    stopPrice=formatted_tp,
                    closePosition=True,
                    workingType="MARK_PRICE"
                )
                result['tp'] = tp_order
                tp_id = tp_order.get("algoId") or tp_order.get("orderId")
                print(f" -> TP Order Active! ID: {tp_id}")
            except Exception as e:
                print(f"[BINANCE CLIENT WARNING] Failed to place on-exchange TP: {e}")

        # 4. Stop Loss Market Order (if specified)
        if sl_price is not None and sl_price > 0:
            formatted_sl = self.round_step_size(sl_price, rules["tick_size"])
            try:
                print(f"[BINANCE CLIENT ORDER] [3/3] Placing on-exchange STOP_MARKET at ${formatted_sl}...")
                sl_order = self.client.futures_create_order(
                    symbol=self.symbol,
                    side=exit_side,
                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                    stopPrice=formatted_sl,
                    closePosition=True,
                    workingType="MARK_PRICE"
                )
                result['sl'] = sl_order
                sl_id = sl_order.get("algoId") or sl_order.get("orderId")
                print(f" -> SL Order Active! ID: {sl_id}")
            except Exception as e:
                print(f"[BINANCE CLIENT WARNING] Failed to place on-exchange SL: {e}")

        result['status'] = 'SUCCESS'
        return result

    def update_stop_loss(self, current_side: str, new_sl_price: float) -> Optional[Dict[str, Any]]:
        """
        Updates on-exchange Stop Loss order (used by dynamic Trailing Stop).
        """
        if not self.is_connected or not self.client or new_sl_price <= 0:
            return None

        rules = self.rules or self.get_symbol_rules(self.symbol)
        formatted_sl = self.round_step_size(new_sl_price, rules["tick_size"])
        exit_side = SIDE_SELL if current_side.upper() == 'LONG' else SIDE_BUY

        try:
            # Clear old algo orders
            self.cancel_all_algo_orders()
            # Post updated Stop Loss
            print(f"[BINANCE CLIENT] Updating on-exchange STOP_MARKET to ${formatted_sl}...")
            sl_order = self.client.futures_create_order(
                symbol=self.symbol,
                side=exit_side,
                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                stopPrice=formatted_sl,
                closePosition=True,
                workingType="MARK_PRICE"
            )
            print(f" -> Updated SL Active! ID: {sl_order.get('algoId') or sl_order.get('orderId')}")
            return sl_order
        except Exception as e:
            print(f"[BINANCE CLIENT WARNING] Failed to update on-exchange SL: {e}")
            return None

    def close_position(self, current_side: str, quantity: float) -> Optional[Dict[str, Any]]:
        """
        Closes existing position via reduceOnly Market Order and clears pending algo orders.
        """
        if not self.is_connected or not self.client:
            return None

        rules = self.rules or self.get_symbol_rules(self.symbol)
        valid_qty = self.round_step_size(quantity, rules["step_size"])
        if valid_qty <= 0:
            valid_qty = rules["min_qty"]

        close_side = SIDE_SELL if current_side.upper() == 'LONG' else SIDE_BUY

        # Clean pending TP/SL orders
        self.cancel_all_algo_orders()

        print(f"[BINANCE CLIENT CLOSE] Closing {current_side} ({valid_qty} {self.symbol}) via MARKET {close_side}...")
        try:
            order = self.client.futures_create_order(
                symbol=self.symbol,
                side=close_side,
                type=FUTURE_ORDER_TYPE_MARKET,
                quantity=valid_qty,
                reduceOnly=True
            )
            print(f" -> Position Closed! Order ID: {order.get('orderId')}")
            return order
        except Exception as e:
            print(f"[BINANCE CLIENT ERROR] Failed to close position: {e}")
            return None
