import json
import os
import pandas as pd
import numpy as np
from tabulate import tabulate
from typing import Dict, Any, List

from src.core.binance_client import BinanceClient
from src.core.position_sizer import VolatilityTargetPositionSizer
from src.strategies.momentum import MultiHorizonMomentumStrategy
from src.strategies.vwap_rejection import VWAPRejectionStrategy
from src.strategies.sentiment_trend import SentimentFilteredTrendStrategy

class MultiStrategyBacktester:
    """
    Backtesting Engine for evaluating multiple quantitative strategies simultaneously
    on historical Binance data. Calculates institutional risk & performance metrics.
    """
    def __init__(self, config_path: str = "config.json", strategy_config_path: str = "strategy_config.json"):
        with open(config_path, "r") as f:
            self.config = json.load(f)
        with open(strategy_config_path, "r") as f:
            self.strategy_config = json.load(f)

        self.client = BinanceClient(testnet=self.config.get("BINANCE_SANDBOX", True))
        self.position_sizer = VolatilityTargetPositionSizer(
            max_risk_per_trade=self.config["RISK_LIMITS"]["max_risk_per_trade"]
        )
        self.initial_capital = self.config.get("INITIAL_CAPITAL", 10000.0)
        self.pairs = self.config.get("TRADING_PAIRS", ["BTC/USDT"])
        self.timeframe = self.config.get("TIMEFRAME", "1h")

        # Instantiate enabled strategies
        self.strategies = []
        strat_configs = self.strategy_config.get("strategies", {})
        
        if strat_configs.get("momentum_multi_horizon", {}).get("enabled", True):
            self.strategies.append(MultiHorizonMomentumStrategy(config=strat_configs["momentum_multi_horizon"]))
            
        if strat_configs.get("vwap_mean_reversion", {}).get("enabled", True):
            self.strategies.append(VWAPRejectionStrategy(config=strat_configs["vwap_mean_reversion"]))
            
        if strat_configs.get("sentiment_filtered_trend", {}).get("enabled", True):
            self.strategies.append(SentimentFilteredTrendStrategy(config=strat_configs["sentiment_filtered_trend"]))

    def run_backtest(self, days: int = 30) -> Dict[str, Any]:
        """Runs multi-strategy backtest across historical pairs."""
        print(f"\n=======================================================")
        print(f"  RUNNING MULTI-STRATEGY BACKTEST ({days} DAYS, TIMEFRAME: {self.timeframe})")
        print(f"=======================================================\n")

        results = {}

        for symbol in self.pairs:
            print(f"[Backtester] Fetching historical data for {symbol}...")
            ohlcv_df = self.client.fetch_historical_ohlcv(symbol, timeframe=self.timeframe, days=days)
            
            if ohlcv_df.empty or len(ohlcv_df) < 50:
                print(f"[Backtester] Insufficient data for {symbol}, skipping.")
                continue

            for strategy in self.strategies:
                strat_name = strategy.name
                if strat_name not in results:
                    results[strat_name] = {
                        "trades": [],
                        "equity_curve": [self.initial_capital],
                        "capital": self.initial_capital
                    }

                capital = self.initial_capital
                position = None  # Current active position dict
                equity_curve = [capital]
                trades = []

                # Rolling simulation step-by-step
                for i in range(50, len(ohlcv_df)):
                    sub_df = ohlcv_df.iloc[:i].copy()
                    current_bar = ohlcv_df.iloc[i]
                    current_price = current_bar['close']

                    # Generate signal from strategy
                    signal_score = strategy.generate_signal(sub_df)
                    volatility = self.position_sizer.calculate_volatility(sub_df)

                    # Position sizing calculation
                    sizing = self.position_sizer.calculate_position_size(
                        current_price=current_price,
                        capital=capital,
                        score=signal_score,
                        volatility=volatility,
                        risk_budget_ratio=strategy.config.get("risk_budget", 0.01)
                    )

                    target_dir = sizing["direction"]
                    target_value = sizing["target_value"]

                    # Execute trade logic
                    if position is None and target_dir != 0:
                        # Open new position
                        entry_price = current_price
                        units = target_value / entry_price
                        position = {
                            "symbol": symbol,
                            "entry_price": entry_price,
                            "units": units,
                            "direction": target_dir,
                            "entry_time": current_bar['timestamp']
                        }
                    elif position is not None and (target_dir != position["direction"] or target_dir == 0):
                        # Close position
                        exit_price = current_price
                        pnl = (exit_price - position["entry_price"]) * position["units"]
                        # Fee deduction (0.075% taker fee)
                        fee = abs(position["units"] * exit_price) * 0.00075
                        net_pnl = pnl - fee
                        capital += net_pnl
                        
                        trades.append({
                            "symbol": symbol,
                            "direction": position["direction"],
                            "entry_price": position["entry_price"],
                            "exit_price": exit_price,
                            "pnl": net_pnl,
                            "pnl_pct": net_pnl / abs(position["units"] * position["entry_price"])
                        })
                        
                        position = None
                        if target_dir != 0:
                            # Re-open in opposite direction
                            units = target_value / current_price
                            position = {
                                "symbol": symbol,
                                "entry_price": current_price,
                                "units": units,
                                "direction": target_dir,
                                "entry_time": current_bar['timestamp']
                            }

                    equity_curve.append(capital)

                results[strat_name]["trades"].extend(trades)
                results[strat_name]["capital"] = capital
                results[strat_name]["equity_curve"].extend(equity_curve)

        # Compute summary statistics
        summary_table = []
        summary_dict = {}

        for strat_name, res in results.items():
            trades = res["trades"]
            eq = np.array(res["equity_curve"])
            total_trades = len(trades)
            
            if total_trades == 0:
                summary_table.append([strat_name, 0, "0.0%", "$0.00", "0.00", "0.0%", "0.00"])
                continue

            wins = [t for t in trades if t["pnl"] > 0]
            losses = [t for t in trades if t["pnl"] <= 0]
            
            win_rate = len(wins) / total_trades if total_trades > 0 else 0.0
            total_pnl = res["capital"] - self.initial_capital
            total_return_pct = (total_pnl / self.initial_capital) * 100.0

            # Calculate Max Drawdown
            peak = np.maximum.accumulate(eq)
            drawdown = (eq - peak) / peak
            max_drawdown = abs(drawdown.min()) * 100.0

            # Expected Value E[X]
            avg_win = np.mean([t["pnl"] for t in wins]) if wins else 0.0
            avg_loss = abs(np.mean([t["pnl"] for t in losses])) if losses else 0.0
            expected_value = (win_rate * avg_win) - ((1.0 - win_rate) * avg_loss)

            # Sharpe Ratio
            returns = np.diff(eq) / eq[:-1]
            sharpe_ratio = (np.mean(returns) / (np.std(returns) + 1e-8)) * np.sqrt(365 * 24)

            summary_table.append([
                strat_name,
                total_trades,
                f"{win_rate * 100:.1f}%",
                f"${total_pnl:+.2f} ({total_return_pct:+.2f}%)",
                f"${expected_value:+.2f}",
                f"-{max_drawdown:.2f}%",
                f"{sharpe_ratio:.2f}"
            ])

            summary_dict[strat_name] = {
                "total_trades": total_trades,
                "win_rate": win_rate,
                "total_return_pct": total_return_pct,
                "expected_value": expected_value,
                "max_drawdown_pct": max_drawdown,
                "sharpe_ratio": sharpe_ratio
            }

        print("\n" + tabulate(
            summary_table,
            headers=["Strategy", "Trades", "Win Rate", "Net Return", "Expected Value E[X]", "Max Drawdown", "Sharpe Ratio"],
            tablefmt="grid"
        ))

        # Save results to logs
        os.makedirs("logs", exist_ok=True)
        with open("logs/backtest_results.json", "w") as f:
            json.dump(summary_dict, f, indent=2)

        return summary_dict

if __name__ == "__main__":
    backtester = MultiStrategyBacktester()
    backtester.run_backtest(days=30)
