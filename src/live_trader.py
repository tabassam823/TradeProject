import json
import os
import datetime
from dotenv import load_dotenv
from typing import Dict, Any

from src.core.binance_client import BinanceClient
from src.core.openbb_client import OpenBBClient
from src.core.position_sizer import VolatilityTargetPositionSizer
from src.strategies.momentum import MultiHorizonMomentumStrategy
from src.strategies.vwap_rejection import VWAPRejectionStrategy
from src.strategies.sentiment_trend import SentimentFilteredTrendStrategy

class LiveTrader:
    """
    Live Trading Execution Engine.
    Executes real-money orders on Binance API using Volatility-Targeted Position Sizing
    and OpenBB News Sentiment Circuit Breaker safeguards.
    """
    def __init__(self, config_path: str = "config.json", strategy_config_path: str = "strategy_config.json"):
        load_dotenv()
        with open(config_path, "r") as f:
            self.config = json.load(f)
        with open(strategy_config_path, "r") as f:
            self.strategy_config = json.load(f)

        api_key = os.getenv("BINANCE_API_KEY", "")
        secret_key = os.getenv("BINANCE_SECRET_KEY", "")
        testnet = self.config.get("BINANCE_SANDBOX", True)

        self.binance = BinanceClient(api_key=api_key, secret_key=secret_key, testnet=testnet)
        self.openbb = OpenBBClient()
        self.position_sizer = VolatilityTargetPositionSizer(
            max_risk_per_trade=self.config["RISK_LIMITS"]["max_risk_per_trade"]
        )

        self.pairs = self.config.get("TRADING_PAIRS", ["BTC/USDT"])
        self.timeframe = self.config.get("TIMEFRAME", "1h")

        # Select Top Strategy based on configuration
        strat_configs = self.strategy_config.get("strategies", {})
        self.strategy = MultiHorizonMomentumStrategy(config=strat_configs.get("momentum_multi_horizon", {}))

    def run_live_tick(self):
        """Executes a single live trading tick across configured pairs."""
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[LIVE TRADER TICK] Executing live tick at {now_str}...")

        if not os.getenv("BINANCE_API_KEY"):
            print("[LIVE TRADER WARNING] No BINANCE_API_KEY found in environment or .env file.")
            print("[LIVE TRADER] Running in Safe Simulation Mode (No real money spent).")

        for symbol in self.pairs:
            df = self.binance.fetch_ohlcv(symbol, timeframe=self.timeframe, limit=100)
            if df.empty or len(df) < 50:
                print(f"[LiveTrader] Skipping {symbol} (insufficient data).")
                continue

            current_price = df['close'].iloc[-1]
            volatility = self.position_sizer.calculate_volatility(df)
            
            # Check Circuit Breaker
            base_coin = symbol.split('/')[0]
            is_circuit_broken = self.openbb.is_circuit_breaker_triggered(base_coin)

            signal_score = self.strategy.generate_signal(df)
            
            # Calculate position size
            sizing = self.position_sizer.calculate_position_size(
                current_price=current_price,
                capital=self.config.get("INITIAL_CAPITAL", 10000.0),
                score=signal_score,
                volatility=volatility,
                risk_budget_ratio=0.01,
                is_circuit_broken=is_circuit_broken
            )

            direction = sizing["direction"]
            target_value = abs(sizing["target_value"])
            units = abs(sizing["target_units"])

            if direction != 0 and units > 0:
                side = "buy" if direction > 0 else "sell"
                print(f"  [LIVE SIGNAL] {side.upper()} {units:.4f} {symbol} @ ${current_price:.2f} (Target Value: ${target_value:.2f})")
                
                # Execute order if real keys are configured
                if os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_SECRET_KEY"):
                    order = self.binance.execute_live_order(symbol, side, units)
                    print(f"  [LIVE ORDER EXECUTED] {order}")
            else:
                print(f"  [LIVE SIGNAL] Neutral or Circuit Broken on {symbol}.")

if __name__ == "__main__":
    live_runner = LiveTrader()
    live_runner.run_live_tick()
