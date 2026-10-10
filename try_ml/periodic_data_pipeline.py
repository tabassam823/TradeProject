"""
Unified Periodic Data Ingestion & Live Streaming Pipeline.
Manages automated, scheduled updates for:
1. Quantitative Market Data (1h & 5m OHLCV for SOL & BTC)
2. Macro Qualitative Data (Alternative.me Fear & Greed Index)
3. Micro Qualitative Data (Live RSS Multi-Source News & Sentiment Scoring)
"""
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crypto_ml_trading.data_loader import (
    fetch_yfinance_ohlcv, fetch_fear_and_greed, fetch_live_crypto_news,
    update_crypto_news_dataset, load_all_market_data
)
from crypto_futures_scalping.data_loader import fetch_5m_ohlcv, load_scalping_market_data
from crypto_ml_trading.config import DATA_DIR

def display_pipeline_status():
    """Displays the freshness, record count, and timestamp range of all cached data."""
    print("\n" + "=" * 75)
    print("📊 DATA INGESTION PIPELINE STATUS")
    print("=" * 75)
    
    files = [
        ("SOL 1h OHLCV", "SOL_USD_1h_365d.csv"),
        ("BTC 1h OHLCV", "BTC_USD_1h_365d.csv"),
        ("SOL 5m OHLCV", "SOL_USD_5m_60d.csv"),
        ("BTC 5m OHLCV", "BTC_USD_5m_60d.csv"),
        ("Fear & Greed Index", "fear_and_greed_365d.csv"),
        ("Crypto News & Sentiment", "crypto_news_historical_365d.csv")
    ]
    
    import pandas as pd
    now = time.time()
    
    for label, fname in files:
        fpath = Path(DATA_DIR) / fname
        if fpath.exists():
            age_min = (now - os.path.getmtime(fpath)) / 60.0
            size_kb = os.path.getsize(fpath) / 1024.0
            try:
                df = pd.read_csv(fpath, index_col=0)
                n_rows = len(df)
                first_ts = str(df.index[0])[:19]
                last_ts = str(df.index[-1])[:19]
                status_str = f"🟢 FRESH ({age_min:.1f}m ago)" if age_min < 60 else f"🟡 AGE ({age_min/60:.1f}h ago)"
                print(f"[{label:<22}] {status_str:<20} | Rows: {n_rows:>6} | Range: {first_ts} to {last_ts}")
            except Exception as e:
                print(f"[{label:<22}] Error reading CSV: {e}")
        else:
            print(f"[{label:<22}] 🔴 NOT FOUND")
    print("=" * 75 + "\n")

def run_news_update():
    """Fetches live RSS news and displays latest articles with sentiment tags."""
    print("\n" + "=" * 75)
    print("📰 FETCHING LIVE RSS CRYPTO NEWS & NLP SENTIMENT")
    print("=" * 75)
    
    live_df = fetch_live_crypto_news(max_per_feed=8)
    if live_df.empty:
        print("[WARNING] No live news fetched. Check internet connection.")
        return
        
    print(f"Captured {len(live_df)} live headlines across CoinTelegraph, Decrypt, and CoinDesk:\n")
    for idx, row in live_df.head(10).iterrows():
        score = row['sentiment_score']
        label = "🟢 BULLISH" if score > 0 else ("🔴 BEARISH" if score < 0 else "⚪ NEUTRAL")
        ts_str = row['timestamp'].strftime('%H:%M UTC')
        print(f"[{ts_str}] [{row['source']:<14}] {label:<10} (Score: {score:+.2f}) : {row['headline']}")
        
    # Merge into historical dataset
    update_crypto_news_dataset(days=365, force_refresh=False)
    print("=" * 75 + "\n")

def run_full_update():
    """Executes full synchronization of all quantitative and qualitative feeds."""
    print("\n" + "=" * 75)
    print(f"🔄 EXECUTING FULL DATA INGESTION CYCLE ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')})")
    print("=" * 75)
    
    # 1. 1h OHLCV
    print("\n[1/4] Updating 1-Hour OHLCV Market Data (SOL & BTC)...")
    fetch_yfinance_ohlcv("BTC-USD", interval="1h", days=365, force_refresh=True)
    fetch_yfinance_ohlcv("SOL-USD", interval="1h", days=365, force_refresh=True)
    
    # 2. 5m OHLCV
    print("\n[2/4] Updating 5-Minute Scalping OHLCV Data (SOL & BTC)...")
    fetch_5m_ohlcv("SOL-USD", days=60, force_refresh=True)
    fetch_5m_ohlcv("BTC-USD", days=60, force_refresh=True)
    
    # 3. Macro Fear & Greed Index
    print("\n[3/4] Updating Macro Fear & Greed Index...")
    fetch_fear_and_greed(days=365, force_refresh=True)
    
    # 4. Micro Live News & Sentiment
    print("\n[4/4] Updating Micro News & Sentiment Feeds...")
    run_news_update()
    
    print("✅ FULL INGESTION CYCLE COMPLETED SUCCESSFULLY!\n")

def run_loop(interval_minutes: int = 60):
    """Runs periodic ingestion loop indefinitely."""
    print("\n" + "=" * 75)
    print(f"🚀 STARTING PERIODIC DATA INGESTION DAEMON (INTERVAL: {interval_minutes} MINUTES)")
    print("=" * 75)
    print("Press Ctrl+C to stop.\n")
    
    try:
        while True:
            run_full_update()
            display_pipeline_status()
            sleep_sec = interval_minutes * 60
            print(f"💤 Sleeping for {interval_minutes}m until next data synchronization cycle...")
            time.sleep(sleep_sec)
    except KeyboardInterrupt:
        print("\n[DAEMON STOPPED] Data ingestion scheduler halted safely.")

def main():
    parser = argparse.ArgumentParser(description="Periodic Data Ingestion & Live Sentiment Pipeline")
    parser.add_argument("--status", action="store_true", help="Display freshness and status of all data files")
    parser.add_argument("--update-all", action="store_true", help="Execute full sync for all market data, FNG, and news")
    parser.add_argument("--update-news", action="store_true", help="Fetch and merge latest RSS crypto news")
    parser.add_argument("--loop", type=int, default=0, help="Run periodic ingestion daemon every N minutes")
    args = parser.parse_args()
    
    if args.status:
        display_pipeline_status()
        return
        
    if args.update_news:
        run_news_update()
        return
        
    if args.loop > 0:
        run_loop(interval_minutes=args.loop)
        return
        
    # Default is update-all
    run_full_update()
    display_pipeline_status()

if __name__ == '__main__':
    main()
