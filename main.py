import argparse
import sys
from src.backtester import MultiStrategyBacktester
from src.paper_trader import PaperTrader
from src.leaderboard import StrategyLeaderboard
from src.live_trader import LiveTrader

def main():
    parser = argparse.ArgumentParser(description="TradeProject: Dynamic Quantitative Trading Engine")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["backtest", "paper", "leaderboard", "live"],
        default="paper",
        help="Execution mode: backtest | paper | leaderboard | live"
    )
    parser.add_argument("--days", type=int, default=30, help="Days of data for backtesting")
    
    args = parser.parse_args()

    if args.mode == "backtest":
        print(f"[Main] Starting Backtest Mode ({args.days} days)...")
        backtester = MultiStrategyBacktester()
        backtester.run_backtest(days=args.days)
        
    elif args.mode == "paper":
        print("[Main] Starting Paper Trading Tick...")
        trader = PaperTrader()
        trader.run_tick()
        
    elif args.mode == "leaderboard":
        print("[Main] Generating Strategy Leaderboard...")
        board = StrategyLeaderboard()
        board.generate_leaderboard()
        
    elif args.mode == "live":
        print("[Main] Starting Live Trading Mode...")
        live_trader = LiveTrader()
        live_trader.run_live_tick()

if __name__ == "__main__":
    main()
