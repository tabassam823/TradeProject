"""
Binance Market Data & Order Execution Client.
Uses Binance public vision data endpoints for robust rate-limit-free OHLCV ingestion
with ccxt fallback for testnet / live order execution.
"""

import requests
import ccxt
import pandas as pd
import datetime
import time
import os
from typing import Optional, Dict, Any, List

class BinanceClient:
    def __init__(self, api_key: str = "", secret_key: str = "", testnet: bool = True):
        self.testnet = testnet
        exchange_params = {
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        }
        if api_key and secret_key:
            exchange_params['apiKey'] = api_key
            exchange_params['secret'] = secret_key
            
        self.exchange = ccxt.binance(exchange_params)
        if testnet:
            self.exchange.set_sandbox_mode(True)
            
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 200) -> pd.DataFrame:
        """Fetches OHLCV candles using public data endpoint with fallback."""
        clean_sym = symbol.replace("/", "").replace(":", "")
        url = "https://data-api.binance.vision/api/v3/klines"
        params = {
            "symbol": clean_sym,
            "interval": timeframe,
            "limit": limit
        }
        try:
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
            pass

        # Fallback to CCXT
        try:
            raw_candles = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(raw_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            return df
        except Exception as e:
            print(f"[BinanceClient] Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_historical_ohlcv(self, symbol: str, timeframe: str = '1h', days: int = 30) -> pd.DataFrame:
        """Fetches up to 1000 candles of historical data from public vision endpoint."""
        clean_sym = symbol.replace("/", "").replace(":", "")
        limit = min(days * 24, 1000)
        url = "https://data-api.binance.vision/api/v3/klines"
        params = {
            "symbol": clean_sym,
            "interval": timeframe,
            "limit": limit
        }
        try:
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
            print(f"[BinanceClient] Warning downloading historical candles for {symbol}: {e}")

        return pd.DataFrame()

    def fetch_ticker_price(self, symbol: str) -> float:
        """Fetches current ticker price for symbol."""
        clean_sym = symbol.replace("/", "").replace(":", "")
        url = "https://data-api.binance.vision/api/v3/ticker/price"
        try:
            resp = requests.get(url, params={"symbol": clean_sym}, timeout=3)
            if resp.status_code == 200:
                return float(resp.json().get("price", 0.0))
        except Exception:
            pass
        return 0.0

    def execute_live_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        """Executes a market/limit order on Binance."""
        try:
            if price:
                order = self.exchange.create_order(symbol, 'limit', side, amount, price)
            else:
                order = self.exchange.create_order(symbol, 'market', side, amount)
            return order
        except Exception as e:
            print(f"[BinanceClient] Order execution failed for {symbol}: {e}")
            return {'status': 'error', 'message': str(e)}
