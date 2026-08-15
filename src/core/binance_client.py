import ccxt
import pandas as pd
import datetime
import time
import os
from typing import Optional, Dict, Any

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
        """Fetches OHLCV candles from Binance API and returns a cleaned pandas DataFrame."""
        try:
            raw_candles = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(raw_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            return df
        except Exception as e:
            print(f"[BinanceClient] Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_historical_ohlcv(self, symbol: str, timeframe: str = '1h', days: int = 60) -> pd.DataFrame:
        """Fetches multiple pages of historical OHLCV candles."""
        since = self.exchange.parse8601((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S'))
        all_candles = []
        limit = 1000
        
        while True:
            try:
                candles = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
                if not candles:
                    break
                all_candles.extend(candles)
                since = candles[-1][0] + 1
                if len(candles) < limit:
                    break
                time.sleep(self.exchange.rateLimit / 1000)
            except Exception as e:
                print(f"[BinanceClient] Historical download warning for {symbol}: {e}")
                break

        if not all_candles:
            return pd.DataFrame()

        df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.drop_duplicates(subset=['timestamp'], inplace=True)
        df.sort_values('timestamp', inplace=True)
        df.reset_index(drop=True, inplace=True)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        return df

    def fetch_ticker_price(self, symbol: str) -> float:
        """Fetches current ticker price for symbol."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            print(f"[BinanceClient] Error fetching ticker for {symbol}: {e}")
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
