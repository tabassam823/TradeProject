"""
24/7 High-Frequency Trading Worker & Scheduler.
Runs continuous evaluation ticks and periodically generates the performance leaderboard.
"""

import time
import os
import datetime
from src.paper_trader import PaperTrader
from src.leaderboard import StrategyLeaderboard

def main():
    interval = int(os.getenv("TICK_INTERVAL_SECONDS", "30"))
    print(f"=======================================================")
    print(f"  TradeProject 24/7 Multi-Strategy Paper Trader")
    print(f"  Execution Mode: CONTINUOUS (Interval: {interval}s)")
    print(f"  Startup Time:   {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"=======================================================\n")
    
    trader = PaperTrader()
    leaderboard = StrategyLeaderboard()
    tick_count = 0

    while True:
        try:
            trader.run_tick()
            tick_count += 1
            
            # Periodically output updated leaderboard to logs every 5 ticks
            if tick_count % 5 == 0:
                leaderboard.generate_leaderboard()

        except Exception as e:
            print(f"[Worker Error] Exception during tick: {e}")

        time.sleep(interval)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("\n[Scheduler] Stopped by operator.")
