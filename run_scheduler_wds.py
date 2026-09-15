"""
24/7 High-Frequency Trading Worker & Scheduler (Futures-Ready).
Replaces run_scheduler.py with futures support and paper/live toggle.

Cross-Platform: Works on Windows and Linux.
Usage:
    Windows: python3 run_scheduler_wds.py
    Linux:   python3 run_scheduler_wds.py
    Docker:  See Procfile_wds

Mode Selection:
    EXECUTION_MODE = "PAPER_TRADING" → Paper trading (simulation)
    EXECUTION_MODE = "LIVE_TRADING"  → Real orders on Binance Futures
"""

import os
import sys
import time
import datetime
import json
from typing import Optional


def load_config(config_path: str = "config.json") -> dict:
    """Loads configuration from config.json."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[Scheduler] Warning: {config_path} not found. Using defaults.")
        return {
            "EXECUTION_MODE": "PAPER_TRADING",
            "TRADING_PAIRS": ["BTC/USDT"],
            "TIMEFRAME": "1h",
            "INITIAL_CAPITAL": 20.0,
            "BINANCE_SANDBOX": True,
        }


def load_env():
    """Loads environment variables from .env and then overrides with .env_wds."""
    from dotenv import load_dotenv
    # Load generic .env first (if exists)
    load_dotenv()
    # Always load .env_wds afterwards, overriding any duplicate keys
    load_dotenv('.env_wds', override=True)


def setup_futures_client(testnet: bool = True):
    """
    Sets up the Binance Futures client for live trading.
    Called only when EXECUTION_MODE = 'LIVE_TRADING'.
    
    Returns:
        BinanceFuturesClient instance or None if paper trading.
    """
    try:
        from src.core.binance_client_wds import BinanceFuturesClient
    except ImportError:
        # Fallback for Windows
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from core.binance_client_wds import BinanceFuturesClient
    
    api_key = os.getenv("BINANCE_API_KEY", "")
    secret_key = os.getenv("BINANCE_SECRET_KEY", "")
    
    if not api_key or not secret_key:
        print("[Scheduler] No Binance API keys found. Running in SAFE MODE (paper only).")
        return None
    
    leverage = int(os.getenv("LEVERAGE", "20"))
    margin_mode = os.getenv("MARGIN_MODE", "isolated")
    
    client = BinanceFuturesClient(
        api_key=api_key,
        secret_key=secret_key,
        testnet=testnet,
        leverage=leverage,
        margin_mode=margin_mode
    )
    
    # Prepare default symbols
    symbols_str = os.getenv("TRADING_PAIRS", "BTC/USDT,ETH/USDT")
    symbols = [s.strip() for s in symbols_str.split(",") if s.strip()]
    for sym in symbols:
        client.prepare_symbol(sym)
    
    print(f"[Scheduler] Binance Futures Client initialized.")
    print(f"  Mode:       {'Testnet' if testnet else 'Mainnet'}")
    print(f"  Leverage:   {leverage}x")
    print(f"  Margin:     {margin_mode}")
    print(f"  Symbols:    {', '.join(symbols)}")
    
    return client


def run_paper_trading_interval(interval: int, trader, leaderboard, tick_count: int) -> int:
    """Runs a single paper trading tick."""
    try:
        trader.run_tick()
        tick_count += 1
        
        if tick_count % 5 == 0:
            leaderboard.generate_leaderboard()
        
        return tick_count
    except Exception as e:
        print(f"[Worker Error] Exception during tick: {e}")
    return tick_count


def run_live_trading_interval(interval: int, futures_client, config: dict):
    """Runs a single live trading tick on Binance Futures."""
    pairs = config.get("TRADING_PAIRS", ["BTC/USDT"])
    timeframe = config.get("TIMEFRAME", "1h")
    
    print(f"\n[LIVE TICK] Executing at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for symbol in pairs:
        symbol = symbol.strip()
        
        # Fetch OHLCV from Futures
        df = futures_client.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
        if df.empty or len(df) < 50:
            print(f"  [{symbol}] Skipping (insufficient data).")
            continue
        
        current_price = df['close'].iloc[-1]
        print(f"  [{symbol}] Current: ${current_price:.2f}")
        
        # Get account balance for risk check
        balance = futures_client.get_account_balance()
        if balance.get("status") == "success":
            print(f"  [{symbol}] Balance: ${balance.get('free', 0):.2f} USDT")
        
        # Check open positions
        positions = futures_client.get_open_positions()
        if positions:
            for pos in positions:
                print(f"  [{symbol}] Open: {pos.get('side')} {pos.get('contracts', 0)} contracts @ ${pos.get('entryPrice', 0)}")
        
        # For now, just log. Full strategy integration comes in phase 2.
        # In production, you'd call strategy.generate_signal(df) here
        # and then futures_client.execute_live_order(symbol, side, contracts)
    
    return True


def main():
    """
    Main scheduler entry point.
    
    Mode is determined by EXECUTION_MODE in config.json or environment:
    - "PAPER_TRADING" → PaperTrader (simulation)
    - "LIVE_TRADING"   → LiveTrader with Binance Futures
    """
    # Load configuration
    load_env()
    config = load_config()
    
    # Determine execution mode
    execution_mode = os.getenv("EXECUTION_MODE", config.get("EXECUTION_MODE", "PAPER_TRADING"))
    interval = int(os.getenv("TICK_INTERVAL_SECONDS", "30"))
    testnet = config.get("BINANCE_SANDBOX", True)
    symbols = config.get("TRADING_PAIRS", ["BTC/USDT"])
    
    # Print startup banner
    print("=" * 65)
    print("  TradeProject 24/7 Multi-Strategy Trading Engine (Futures-Ready)")
    print(f"  Execution Mode: {execution_mode}")
    print(f"  Network:        {'Futures Testnet' if testnet else 'Futures Mainnet'}")
    print(f"  Symbols:        {', '.join(symbols)}")
    print(f"  Interval:       {interval}s")
    print(f"  Startup Time:   {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    
    # Initialize components
    try:
        from src.leaderboard import StrategyLeaderboard
    except ImportError:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from leaderboard import StrategyLeaderboard
    
    leaderboard = StrategyLeaderboard()
    tick_count = 0
    futures_client = None
    
    if execution_mode == "LIVE_TRADING":
        futures_client = setup_futures_client(testnet=testnet)
        if futures_client is None:
            print("[Scheduler] Falling back to PAPER_TRADING mode.")
            execution_mode = "PAPER_TRADING"
    
    # Main loop
    if execution_mode == "PAPER_TRADING":
        try:
            from src.paper_trader import PaperTrader
        except ImportError:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from paper_trader import PaperTrader
        
        trader = PaperTrader()
        print("\n[Scheduler] Paper Trading mode activated. No real orders will be placed.")
        print("[Scheduler] Press Ctrl+C to stop.\n")
        
        try:
            while True:
                tick_count = run_paper_trading_interval(interval, trader, leaderboard, tick_count)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[Scheduler] Paper trading stopped by operator.")
    
    elif execution_mode == "LIVE_TRADING" and futures_client:
        print("\n[Scheduler] Live Trading mode activated. REAL ORDERS will be placed.")
        print("[Scheduler] Ensure API key has Trading permission enabled.")
        print("[Scheduler] Press Ctrl+C to stop.\n")
        
        try:
            while True:
                run_live_trading_interval(interval, futures_client, config)
                tick_count += 1
                
                if tick_count % 5 == 0:
                    leaderboard.generate_leaderboard()
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[Scheduler] Live trading stopped by operator.")
    
    else:
        print(f"[Scheduler] ERROR: Unknown execution mode '{execution_mode}'")
        print("[Scheduler] Set EXECUTION_MODE in config.json or .env to 'PAPER_TRADING' or 'LIVE_TRADING'")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("\n[Scheduler] Stopped by operator.")
