import time
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from src.paper_trader import PaperTrader

def scheduled_job():
    print(f"\n=======================================================")
    print(f"  CRON TICK: Running Paper Trading ({datetime.datetime.now()})")
    print(f"=======================================================")
    try:
        trader = PaperTrader()
        trader.run_tick()
    except Exception as e:
        print(f"[Cron Error] Exception during tick: {e}")

if __name__ == "__main__":
    print("[Scheduler] Starting 24/7 Trading Scheduler...")
    # Execute immediately once on startup
    scheduled_job()
    
    # Schedule to run every hour at minute 0
    scheduler = BlockingScheduler()
    scheduler.add_job(scheduled_job, 'cron', minute=0)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("[Scheduler] Stopped.")
