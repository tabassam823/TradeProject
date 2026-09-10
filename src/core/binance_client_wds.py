"""
Binance Futures Client (Futures-Ready).
Replaces binance_client.py for direct Binance Futures (USDT-M) trading.

Key Changes from spot client:
- defaultType: 'futures' (was 'spot')
- set_margin_mode('isolated') before trading
- set_leverage() per symbol
- Futures-specific OHLCV endpoint
- Futures contract size mapping for correct lot sizing
"""

import os
import requests
import ccxt
import pandas as pd
import datetime
import time
from typing import Optional, Dict, Any, List

# =============================================
# CONSTANTS
# =============================================

# Binance Futures USDT-M COIN CONTRACT SIZES (in base asset units per 1 contract)
# Source: https://api.binance.com/fapi/v1/exchangeInfo
# These are the minimum position quantities (stepSize)
FUTURES_CONTRACT_SIZES: Dict[str, float] = {
    "BTC/USDT": 0.001,     # 1 contract = 0.001 BTC
    "ETH/USDT": 0.01,      # 1 contract = 0.01 ETH
    "SOL/USDT": 0.01,      # 1 contract = 0.01 SOL
    "BNB/USDT": 0.001,     # 1 contract = 0.001 BNB
    "AVAX/USDT": 0.01,     # 1 contract = 0.01 AVAX
    "XRP/USDT": 1.0,       # 1 contract = 1 XRP
    "DOGE/USDT": 10.0,     # 1 contract = 10 DOGE
    "ADA/USDT": 1.0,       # 1 contract = 1 ADA
    "DOT/USDT": 0.1,       # 1 contract = 0.1 DOT
    "LINK/USDT": 0.01,     # 1 contract = 0.01 LINK
    "UNI/USDT": 0.1,       # 1 contract = 0.1 UNI
    "LTC/USDT": 0.01,      # 1 contract = 0.01 LTC
    "ATOM/USDT": 0.1,      # 1 contract = 0.1 ATOM
    "MATIC/USDT": 10.0,    # 1 contract = 10 MATIC (Polygon)
    "FIL/USDT": 0.1,       # 1 contract = 0.1 FIL
    "AAVE/USDT": 0.01,     # 1 contract = 0.01 AAVE
    "APT/USDT": 0.01,      # 1 contract = 0.01 APT
    "OP/USDT": 1.0,        # 1 contract = 1 OP
    "NEAR/USDT": 0.1,      # 1 contract = 0.1 NEAR
    "SUI/USDT": 0.1,       # 1 contract = 0.1 SUI
    "TIA/USDT": 0.1,       # 1 contract = 0.1 TIA
    "SEI/USDT": 1.0,       # 1 contract = 1 SEI
    "WLD/USDT": 1.0,       # 1 contract = 1 WLD
}

# Binance Futures FEES (USDT-M Perpetual)
# Standard Tier: Maker 0.02%, Taker 0.04%
# With BNB discount: Maker 0.018%, Taker 0.036%
FEES = {
    "maker_fee_rate": 0.0002,    # 0.02%
    "taker_fee_rate": 0.0004,    # 0.04%
    "bnb_discount_maker": 0.00018,  # 0.018%
    "bnb_discount_taker": 0.00036,  # 0.036%
}

# Binance Futures DATA ENDPOINTS (not the Vision API which is spot-only)
FUTURES_KLINES_URL = "https://fapi.binance.com/fapi/v1/klines"
FUTURES_TICKER_URL = "https://fapi.binance.com/fapi/v1/ticker/price"


class BinanceFuturesClient:
    """
    Binance Futures (USDT-M Perpetual) Trading Client.
    
    Supports:
    - Paper trading via Binance Futures Testnet
    - Live trading on Binance Futures Mainnet
    - Isolated/Cross margin mode
    - Per-symbol leverage configuration
    - Accurate fee calculation (maker/taker/BNB discount)
    """

    def __init__(
        self,
        api_key: str = "",
        secret_key: str = "",
        testnet: bool = True,
        leverage: int = 20,
        margin_mode: str = "isolated"
    ):
        self.testnet = testnet
        self.leverage = leverage
        self.margin_mode = margin_mode

        # ccxt exchange configuration for Futures
        exchange_params = {
            'enableRateLimit': True,
            'options': {
                'defaultType': 'futures',  # CRITICAL: Must be 'futures', NOT 'spot'
            }
        }
        
        if api_key and secret_key:
            exchange_params['apiKey'] = api_key
            exchange_params['secret'] = secret_key
            
        self.exchange = ccxt.binance(exchange_params)
        
        if testnet:
            self.exchange.set_sandbox_mode(True)
            # Override URLs to point to Futures Testnet
            self.exchange.urls['api'] = {
                'public': 'https://testnet.binancefuture.com/fapi',
                'private': 'https://testnet.binancefuture.com/fapi',
                'www': 'https://testnet.binancefuture.com',
            }

    def _get_contract_size(self, symbol: str) -> float:
        """Returns the contract size (in base asset) for a symbol."""
        # symbol format: "BTC/USDT" or "BTCUSDT"
        clean_sym = symbol.replace("/", "").replace(":", "")
        
        # Try direct match first
        if clean_sym in FUTURES_CONTRACT_SIZES:
            return FUTURES_CONTRACT_SIZES[clean_sym]
        
        # Try reverse look-up (without /)
        for key, size in FUTURES_CONTRACT_SIZES.items():
            if key.replace("/", "") == clean_sym:
                return size
        
        # Fallback: assume 1.0 (smallest denomination)
        print(f"[BinanceFuturesClient] Warning: Contract size for {symbol} not found. Using 1.0")
        return 1.0

    def set_leverage(self, symbol: str, leverage: int = None) -> Dict[str, Any]:
        """Set leverage for a futures symbol."""
        if not self.exchange.apiKey:
            print("[BinanceFuturesClient] No API key configured. Skipping leverage set.")
            return {"status": "skipped", "reason": "No API key"}
        
        lev = leverage or self.leverage
        symbol_clean = symbol.replace("/", "")
        
        try:
            result = self.exchange.set_leverage(lev, symbol_clean)
            print(f"[BinanceFuturesClient] Leverage set to {lev}x for {symbol_clean}")
            return result
        except Exception as e:
            print(f"[BinanceFuturesClient] Failed to set leverage for {symbol_clean}: {e}")
            return {"status": "error", "message": str(e)}

    def set_margin_mode(self, symbol: str, margin_mode: str = None) -> Dict[str, Any]:
        """Set margin mode (isolated/cross) for a futures symbol."""
        if not self.exchange.apiKey:
            print("[BinanceFuturesClient] No API key configured. Skipping margin mode set.")
            return {"status": "skipped", "reason": "No API key"}
        
        mode = margin_mode or self.margin_mode
        symbol_clean = symbol.replace("/", "")
        
        try:
            result = self.exchange.set_margin_mode(mode, symbol_clean)
            print(f"[BinanceFuturesClient] Margin mode set to '{mode}' for {symbol_clean}")
            return result
        except Exception as e:
            print(f"[BinanceFuturesClient] Failed to set margin mode for {symbol_clean}: {e}")
            return {"status": "error", "message": str(e)}

    def prepare_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Prepare a symbol for futures trading:
        1. Set margin mode
        2. Set leverage
        Returns dict with setup results.
        """
        results = {
            "symbol": symbol,
            "margin_mode": None,
            "leverage": None,
            "contract_size": self._get_contract_size(symbol)
        }
        
        if self.exchange.apiKey:
            results["margin_mode"] = self.set_margin_mode(symbol)
            results["leverage"] = self.set_leverage(symbol)
        
        return results

    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 200) -> pd.DataFrame:
        """
        Fetches OHLCV candles from Binance Futures (NOT spot Vision API).
        
        Uses Futures-specific endpoint: fapi.binance.com/fapi/v1/klines
        Fallback to ccxt exchange.fetch_ohlcv for testnet/mainnet.
        """
        symbol_clean = symbol.replace("/", "").replace(":", "")
        
        # Try Binance Futures public data endpoint
        try:
            url = FUTURES_KLINES_URL
            params = {
                "symbol": symbol_clean,
                "interval": timeframe,
                "limit": limit
            }
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                raw = resp.json()
                df = pd.DataFrame(raw, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            print(f"[BinanceFuturesClient] Futures OHLCV fetch failed for {symbol}: {e}")

        # Fallback to ccxt (testnet/mainnet)
        try:
            raw_candles = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(raw_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            return df
        except Exception as e:
            print(f"[BinanceFuturesClient] Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_historical_ohlcv(self, symbol: str, timeframe: str = '1h', days: int = 30) -> pd.DataFrame:
        """
        Fetches historical OHLCV from Binance Futures.
        Uses futures endpoint with limit = min(days*24, 1000).
        """
        symbol_clean = symbol.replace("/", "").replace(":", "")
        limit = min(days * 24, 1000)
        
        try:
            url = FUTURES_KLINES_URL
            params = {
                "symbol": symbol_clean,
                "interval": timeframe,
                "limit": limit
            }
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                raw = resp.json()
                df = pd.DataFrame(raw, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.drop_duplicates(subset=['timestamp'], inplace=True)
                df.sort_values('timestamp', inplace=True)
                df.reset_index(drop=True, inplace=True)
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            print(f"[BinanceFuturesClient] Warning downloading historical candles for {symbol}: {e}")

        return pd.DataFrame()

    def fetch_ticker_price(self, symbol: str) -> float:
        """Fetches current ticker price from Binance Futures."""
        symbol_clean = symbol.replace("/", "").replace(":", "")
        
        try:
            url = FUTURES_TICKER_URL
            resp = requests.get(url, params={"symbol": symbol_clean}, timeout=3)
            if resp.status_code == 200:
                return float(resp.json().get("price", 0.0))
        except Exception:
            pass
        return 0.0

    def get_futures_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Gets current funding rate for a futures symbol.
        Important for perpetual futures (funding fee every 8 hours).
        """
        if not self.exchange.apiKey:
            return {"status": "skipped"}
        
        symbol_clean = symbol.replace("/", "").replace(":", "")
        try:
            funding = self.exchange.fetch_funding_rate(symbol_clean)
            return funding
        except Exception as e:
            print(f"[BinanceFuturesClient] Failed to get funding rate for {symbol_clean}: {e}")
            return {"status": "error", "message": str(e)}

    def execute_live_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        order_type: str = "market"
    ) -> Dict[str, Any]:
        """
        Executes a market/limit order on Binance Futures.
        
        Args:
            symbol: Trading pair e.g. "BTC/USDT"
            side: "buy" or "sell"
            amount: Quantity in contracts/units
            price: Limit price (required if order_type="limit")
            order_type: "market" or "limit"
        
        Returns:
            Order result dict.
        """
        symbol_clean = symbol.replace("/", "").replace(":", "")
        
        # Prepare the symbol (set margin mode + leverage if first time)
        self.prepare_symbol(symbol)
        
        try:
            if order_type == "limit" and price:
                order = self.exchange.create_order(
                    symbol_clean, 'limit', side, amount, price,
                    params={'isStop': False}
                )
            else:
                order = self.exchange.create_order(
                    symbol_clean, 'market', side, amount,
                    params={'isStop': False}
                )
            print(f"[BinanceFuturesClient] Order executed: {side.upper()} {amount} {symbol_clean} @ {'market' if not price else price}")
            return order
        except Exception as e:
            print(f"[BinanceFuturesClient] Order execution failed for {symbol_clean}: {e}")
            return {'status': 'error', 'message': str(e)}

    def get_account_balance(self) -> Dict[str, Any]:
        """Get futures account balance."""
        if not self.exchange.apiKey:
            return {"status": "skipped"}
        
        try:
            balance = self.exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {})
            return {
                "status": "success",
                "total": usdt_balance.get('total', 0),
                "free": usdt_balance.get('free', 0),
                "used": usdt_balance.get('used', 0),
            }
        except Exception as e:
            print(f"[BinanceFuturesClient] Failed to get balance: {e}")
            return {"status": "error", "message": str(e)}

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open futures positions."""
        if not self.exchange.apiKey:
            return []
        
        try:
            positions = self.exchange.fetch_positions()
            return positions
        except Exception as e:
            print(f"[BinanceFuturesClient] Failed to get positions: {e}")
            return []

    def get_contract_info(self, symbol: str) -> Dict[str, Any]:
        """Get contract details (contract size, lot size, min order QTY)."""
        symbol_clean = symbol.replace("/", "").replace(":", "")
        try:
            info = self.exchange.fetch_market(symbol_clean)
            return {
                "symbol": symbol_clean,
                "contract_size": info.get('contractSize', self._get_contract_size(symbol)),
                "precision": info.get('precision', {}),
                "limits": info.get('limits', {}),
                "status": info.get('status', 'unknown'),
            }
        except Exception as e:
            print(f"[BinanceFuturesClient] Failed to get contract info for {symbol_clean}: {e}")
            return {}

    @staticmethod
    def calculate_fee(
        side: str,
        amount: float,
        price: float,
        use_bnb_discount: bool = False
    ) -> Dict[str, float]:
        """
        Calculate trading fee for a Binance Futures order.
        
        Fee structure:
        - Regular Tier: Maker 0.02% / Taker 0.04%
        - With BNB Discount: Maker 0.018% / Taker 0.036%
        - VIP tiers available (lower rates) - not included here
        
        Returns:
            Dict with 'fee_rate', 'fee_amount', 'side_type'
        """
        if use_bnb_discount:
            fee_rate = FEES['bnb_discount_taker'] if side == 'taker' else FEES['bnb_discount_maker']
        else:
            fee_rate = FEES['taker_fee_rate'] if side == 'taker' else FEES['maker_fee_rate']
        
        fee_amount = amount * price * fee_rate
        
        return {
            "side": side,
            "side_type": "taker" if side == 'taker' else "maker",
            "fee_rate": fee_rate,
            "fee_amount": fee_amount,
            "notional": amount * price
        }
