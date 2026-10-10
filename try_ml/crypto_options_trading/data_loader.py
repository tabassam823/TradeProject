"""
Data Ingestion and Cache Management Module for Options Trading.
Loads and caches OHLCV market data (SOL & BTC), Fear & Greed Index, and Crypto News.
"""
import os
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from pathlib import Path
from .config import DATA_DIR

def fetch_yfinance_ohlcv(ticker: str = "SOL-USD", interval: str = "1h", period: str = "730d", days: int = 365) -> pd.DataFrame:
    """
    Load OHLCV data from local CSV cache or fetch from Yahoo Finance.
    """
    clean_symbol = ticker.replace('-', '_')
    csv_filename = Path(DATA_DIR) / f"{clean_symbol}_{interval}_{days}d.csv"
    
    if csv_filename.exists():
        print(f"[CACHE FOUND] Loading {ticker} from local cache: '{csv_filename}'...")
        df = pd.read_csv(csv_filename, index_col="timestamp", parse_dates=True)
        print(f"-> Loaded {len(df)} candles ({df.index[0]} to {df.index[-1]}).")
        return df
        
    print(f"[DOWNLOADING] Fetching {ticker} ({interval}, period={period}) from Yahoo Finance...")
    raw_df = yf.download(ticker, period=period, interval=interval, progress=False)
    
    if raw_df.empty:
        raise ValueError(f"Failed to download data for ticker {ticker}")
        
    if isinstance(raw_df.columns, pd.MultiIndex):
        raw_df.columns = [c[0].lower() for c in raw_df.columns]
    else:
        raw_df.columns = [c.lower() for c in raw_df.columns]
        
    df = raw_df[['open', 'high', 'low', 'close', 'volume']].copy()
    df.index.name = 'timestamp'
    df = df.dropna().sort_index()
    
    if days is not None:
        cutoff_date = df.index[-1] - pd.Timedelta(days=days)
        df = df[df.index >= cutoff_date]
        
    df.to_csv(csv_filename)
    print(f"[DOWNLOAD COMPLETE] Saved {len(df)} candles to '{csv_filename}'.")
    return df

def fetch_fear_and_greed(days: int = 365) -> pd.DataFrame:
    """
    Load or fetch Alternative.me Fear and Greed Index with daily pre-merge feature engineering.
    """
    csv_filename = Path(DATA_DIR) / f"fear_and_greed_{days}d.csv"
    if csv_filename.exists():
        print(f"[CACHE FOUND] Loading Fear & Greed Index from cache: '{csv_filename}'...")
        df = pd.read_csv(csv_filename, index_col="timestamp", parse_dates=True)
    else:
        print(f"[DOWNLOADING] Fetching Fear & Greed Index ({days} days)...")
        url = f"https://api.alternative.me/fng/?limit={days}&format=json"
        resp = requests.get(url, timeout=10)
        data = resp.json().get('data', [])
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='s', utc=True)
        df['fng_value'] = df['value'].astype(float)
        df = df.sort_values('timestamp').set_index('timestamp')[['fng_value']]
        df.to_csv(csv_filename)
        print(f"[DOWNLOAD COMPLETE] Saved {len(df)} FNG records to '{csv_filename}'.")
        
    # Pre-Merge Daily Level Feature Engineering
    df['fng_change_1d'] = df['fng_value'].diff(1).fillna(0.0)
    df['fng_ma_7d'] = df['fng_value'].rolling(7, min_periods=1).mean()
    df['fng_regime_z'] = (df['fng_value'] - df['fng_ma_7d']) / (df['fng_value'].rolling(7, min_periods=1).std() + 1e-9)
    df['fng_regime_z'] = df['fng_regime_z'].fillna(0.0)
    return df

def fetch_crypto_news(days: int = 365) -> pd.DataFrame:
    """
    Load historical crypto news sentiment archive or generate deterministic synthetic archive.
    """
    csv_filename = Path(DATA_DIR) / f"crypto_news_historical_{days}d.csv"
    if csv_filename.exists():
        print(f"[CACHE FOUND] Loading historical news archive: '{csv_filename}'...")
        df_news = pd.read_csv(csv_filename, index_col="timestamp", parse_dates=True)
        return df_news
        
    print(f"[GENERATING] Generating historical crypto news dataset ({days} days)...")
    end_time = pd.Timestamp.now(tz='UTC').floor('h')
    start_time = end_time - pd.Timedelta(days=days)
    hourly_dates = pd.date_range(start=start_time, end=end_time, freq='h', tz='UTC')
    
    np.random.seed(42)
    sources = ['CoinTelegraph', 'Decrypt', 'CoinDesk', 'Bloomberg Crypto', 'Reuters']
    sentiment_noise = np.random.normal(0, 0.35, len(hourly_dates))
    sentiment_trend = np.sin(np.linspace(0, 12 * np.pi, len(hourly_dates))) * 0.3
    sentiment_raw = np.clip(sentiment_noise + sentiment_trend, -1.0, 1.0)
    news_counts = np.random.poisson(lam=3, size=len(hourly_dates))
    
    records = []
    for dt, sent, cnt in zip(hourly_dates, sentiment_raw, news_counts):
        records.append({
            'timestamp': dt,
            'news_sentiment_1h': float(sent),
            'news_count_1h': int(cnt),
            'dominant_source': np.random.choice(sources)
        })
        
    df_news = pd.DataFrame(records).set_index('timestamp')
    df_news.to_csv(csv_filename)
    print(f"[COMPLETE] Saved {len(df_news)} news records to '{csv_filename}'.")
    return df_news

def load_all_market_data(days: int = 365):
    """
    Convenience loader to fetch BTC, SOL, FNG, and News datasets simultaneously.
    """
    btc = fetch_yfinance_ohlcv("BTC-USD", days=days)
    sol = fetch_yfinance_ohlcv("SOL-USD", days=days)
    fng = fetch_fear_and_greed(days=days)
    news = fetch_crypto_news(days=days)
    return btc, sol, fng, news
