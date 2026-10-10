"""
Data Ingestion and Periodic Cache Management Module for High-Frequency Futures Scalping.
Fetches, verifies freshness, and periodically updates 5-minute OHLCV market data for SOL-USD and BTC-USD.
"""
import os
import time
import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
from .config import DATA_DIR, TARGET_TICKER, LEAD_TICKER, TIMEFRAME, LOOKBACK_DAYS

def fetch_5m_ohlcv(
    ticker: str = "SOL-USD",
    days: int = 60,
    force_refresh: bool = False,
    max_cache_age_minutes: float = 15.0
) -> pd.DataFrame:
    """
    Load 5-minute OHLCV data from local CSV cache or fetch latest if stale / forced.
    """
    clean_symbol = ticker.replace('-', '_')
    csv_filename = Path(DATA_DIR) / f"{clean_symbol}_{TIMEFRAME}_{days}d.csv"
    
    is_stale = False
    if csv_filename.exists():
        file_age_mins = (time.time() - os.path.getmtime(csv_filename)) / 60.0
        if file_age_mins > max_cache_age_minutes:
            is_stale = True
            
    if csv_filename.exists() and not force_refresh and not is_stale:
        print(f"[CACHE FRESH] Loading {ticker} 5m data from cache: '{csv_filename.name}'...")
        df = pd.read_csv(csv_filename, index_col="timestamp", parse_dates=True)
        return df
        
    reason = "FORCED REFRESH" if force_refresh else ("CACHE STALE" if is_stale else "INITIAL DOWNLOAD")
    print(f"[{reason}] Fetching {ticker} ({TIMEFRAME}, period={days}d) from Yahoo Finance...")
    try:
        # Yahoo Finance allows up to 60d for 5m interval
        period_str = f"{min(days, 60)}d"
        raw_df = yf.download(ticker, period=period_str, interval=TIMEFRAME, progress=False)
        
        if raw_df.empty:
            if csv_filename.exists():
                print(f"[WARNING] yfinance returned empty. Using cached '{csv_filename.name}'.")
                return pd.read_csv(csv_filename, index_col="timestamp", parse_dates=True)
            raise ValueError(f"Failed to download 5m data for ticker {ticker}")
            
        if isinstance(raw_df.columns, pd.MultiIndex):
            raw_df.columns = [c[0].lower() for c in raw_df.columns]
        else:
            raw_df.columns = [c.lower() for c in raw_df.columns]
            
        df = raw_df[['open', 'high', 'low', 'close', 'volume']].copy()
        df.index.name = 'timestamp'
        df = df.dropna().sort_index()
        
        df.to_csv(csv_filename)
        print(f"[UPDATED] Saved {len(df)} 5m candles to '{csv_filename.name}'. (Latest: {df.index[-1]})")
        return df
    except Exception as e:
        print(f"[ERROR] Failed to fetch 5m data for {ticker}: {e}")
        if csv_filename.exists():
            return pd.read_csv(csv_filename, index_col="timestamp", parse_dates=True)
        raise

def load_scalping_market_data(days: int = LOOKBACK_DAYS, force_refresh: bool = False):
    """
    Convenience loader to fetch 5m data for Solana (target) and Bitcoin (lead market).
    """
    sol_df = fetch_5m_ohlcv(TARGET_TICKER, days=days, force_refresh=force_refresh)
    btc_df = fetch_5m_ohlcv(LEAD_TICKER, days=days, force_refresh=force_refresh)
    return sol_df, btc_df
