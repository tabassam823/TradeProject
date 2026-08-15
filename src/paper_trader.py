import json
import os
import datetime
import time
from typing import Dict, Any, List

from src.core.binance_client import BinanceClient
from src.core.openbb_client import OpenBBClient
from src.core.position_sizer import VolatilityTargetPositionSizer
from src.strategies.momentum import MultiHorizonMomentumStrategy
from src.strategies.vwap_rejection import VWAPRejectionStrategy
from src.strategies.sentiment_trend import SentimentFilteredTrendStrategy

class PaperTrader:
    """
    Paper Trading Engine (Dry-Run 24/7 Engine).
    Fetches real-time Binance tickers every hour, simulates order execution,
    and updates virtual sub-ledgers for each strategy in logs/paper_ledger.json.
    """
    def __init__(self, config_path: str = "config.json", strategy_config_path: str = "strategy_config.json"):
        with open(config_path, "r") as f:
            self.config = json.load(f)
        with open(strategy_config_path, "r") as f:
            self.strategy_config = json.load(f)

        self.binance = BinanceClient(testnet=self.config.get("BINANCE_SANDBOX", True))
        self.openbb = OpenBBClient()
        self.position_sizer = VolatilityTargetPositionSizer(
            max_risk_per_trade=self.config["RISK_LIMITS"]["max_risk_per_trade"]
        )
        
        self.pairs = self.config.get("TRADING_PAIRS", ["BTC/USDT", "ETH/USDT"])
        self.timeframe = self.config.get("TIMEFRAME", "1h")
        self.initial_capital = self.config.get("INITIAL_CAPITAL", 10000.0)
        self.ledger_file = "logs/paper_ledger.json"

        # Instantiate strategies
        self.strategies = []
        strat_configs = self.strategy_config.get("strategies", {})
        
        if strat_configs.get("momentum_multi_horizon", {}).get("enabled", True):
            self.strategies.append(MultiHorizonMomentumStrategy(config=strat_configs["momentum_multi_horizon"]))
            
        if strat_configs.get("vwap_mean_reversion", {}).get("enabled", True):
            self.strategies.append(VWAPRejectionStrategy(config=strat_configs["vwap_mean_reversion"]))
            
        if strat_configs.get("sentiment_filtered_trend", {}).get("enabled", True):
            self.strategies.append(SentimentFilteredTrendStrategy(config=strat_configs["sentiment_filtered_trend"]))

        self.ledger = self._load_ledger()

    def _load_ledger(self) -> Dict[str, Any]:
        """Loads or initializes paper trading ledger."""
        os.makedirs("logs", exist_ok=True)
        if os.path.exists(self.ledger_file):
            try:
                with open(self.ledger_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[PaperTrader] Warning loading ledger: {e}")

        # Initialize fresh ledger for each strategy
        initial_ledger = {}
        for strategy in self.strategies:
            initial_ledger[strategy.name] = {
                "capital": self.initial_capital,
                "equity_curve": [{"timestamp": str(datetime.datetime.now()), "equity": self.initial_capital}],
                "open_positions": {},
                "closed_trades": []
            }
        return initial_ledger

    def _save_ledger(self):
        """Saves current paper trading ledger to file."""
        os.makedirs("logs", exist_ok=True)
        with open(self.ledger_file, "w") as f:
            json.dump(self.ledger, f, indent=2)

    def run_tick(self):
        """Executes a single paper trading hourly tick."""
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[PAPER TRADER TICK] Executing tick at {now_str}...")

        for symbol in self.pairs:
            # Fetch latest candles
            df = self.binance.fetch_ohlcv(symbol, timeframe=self.timeframe, limit=100)
            if df.empty or len(df) < 50:
                print(f"[PaperTrader] Skipping {symbol} (insufficient candles).")
                continue

            current_price = df['close'].iloc[-1]
            volatility = self.position_sizer.calculate_volatility(df)
            
            # Check Circuit Breaker
            base_coin = symbol.split('/')[0]
            is_circuit_broken = self.openbb.is_circuit_breaker_triggered(base_coin)

            for strategy in self.strategies:
                strat_name = strategy.name
                strat_ledger = self.ledger.get(strat_name, {
                    "capital": self.initial_capital,
                    "open_positions": {},
                    "closed_trades": [],
                    "equity_curve": []
                })

                score = strategy.generate_signal(df)
                
                # Position Sizing
                sizing = self.position_sizer.calculate_position_size(
                    current_price=current_price,
                    capital=strat_ledger["capital"],
                    score=score,
                    volatility=volatility,
                    risk_budget_ratio=strategy.config.get("risk_budget", 0.01),
                    is_circuit_broken=is_circuit_broken
                )

                target_dir = sizing["direction"]
                target_value = sizing["target_value"]
                open_positions = strat_ledger["open_positions"]

                existing_pos = open_positions.get(symbol)

                if existing_pos is None and target_dir != 0:
                    # Open new paper position
                    units = target_value / current_price
                    strat_ledger["open_positions"][symbol] = {
                        "symbol": symbol,
                        "entry_price": current_price,
                        "units": units,
                        "direction": target_dir,
                        "entry_time": now_str,
                        "score": score
                    }
                    print(f"  [{strat_name}] OPEN {'LONG' if target_dir > 0 else 'SHORT'} on {symbol} @ ${current_price:.2f} (Units: {units:.4f})")

                elif existing_pos is not None and (target_dir != existing_pos["direction"] or target_dir == 0):
                    # Close existing position
                    entry_price = existing_pos["entry_price"]
                    units = existing_pos["units"]
                    pnl = (current_price - entry_price) * units
                    fee = abs(units * current_price) * 0.00075
                    net_pnl = pnl - fee
                    
                    strat_ledger["capital"] += net_pnl
                    strat_ledger["closed_trades"].append({
                        "symbol": symbol,
                        "direction": existing_pos["direction"],
                        "entry_price": entry_price,
                        "exit_price": current_price,
                        "net_pnl": net_pnl,
                        "entry_time": existing_pos["entry_time"],
                        "exit_time": now_str
                    })

                    del strat_ledger["open_positions"][symbol]
                    print(f"  [{strat_name}] CLOSE position on {symbol} @ ${current_price:.2f} | Net PnL: ${net_pnl:+.2f}")

                    if target_dir != 0:
                        # Re-open in new direction
                        new_units = target_value / current_price
                        strat_ledger["open_positions"][symbol] = {
                            "symbol": symbol,
                            "entry_price": current_price,
                            "units": new_units,
                            "direction": target_dir,
                            "entry_time": now_str,
                            "score": score
                        }
                        print(f"  [{strat_name}] RE-OPEN {'LONG' if target_dir > 0 else 'SHORT'} on {symbol} @ ${current_price:.2f}")

                # Record equity snapshot
                strat_ledger["equity_curve"].append({
                    "timestamp": now_str,
                    "equity": strat_ledger["capital"]
                })
                
                self.ledger[strat_name] = strat_ledger

        self._save_ledger()
        print(f"[PaperTrader] Tick completed successfully. Ledger updated.\n")

if __name__ == "__main__":
    trader = PaperTrader()
    trader.run_tick()
