"""
Multi-Strategy Historical Backtesting Engine.
Evaluates all 6 quantitative strategies simultaneously over historical periods (e.g. 30 days)
with regime-adaptive ATR SL/TP, anti-whipsaw cooldown, BEP / trailing TP lifecycle,
and benchmark market comparison.
"""

import json
import os
import pandas as pd
import numpy as np
from tabulate import tabulate
from typing import Dict, Any, List

from src.core.binance_client import BinanceClient
from src.core.position_sizer import VolatilityTargetPositionSizer
from src.core.position_lifecycle_manager import PositionLifecycleManager
from src.core.math_engine import MathEngine, MarketRegime

from src.strategies.momentum import MultiHorizonMomentumStrategy
from src.strategies.vwap_rejection import VWAPRejectionStrategy
from src.strategies.sentiment_trend import SentimentFilteredTrendStrategy
from src.strategies.factor_regime import FactorRegimeStrategy
from src.strategies.first_passage_value import FirstPassageValueStrategy
from src.strategies.qubo_portfolio_selector import QUBOPortfolioStrategy

class MultiStrategyBacktester:
    """
    Asset-Agnostic Multi-Strategy Backtester with Benchmark & Lifecycle Attribution.
    """
    def __init__(self, config_path: str = "config.json", strategy_config_path: str = "strategy_config.json"):
        with open(config_path, "r") as f:
            self.config = json.load(f)
        with open(strategy_config_path, "r") as f:
            self.strategy_config = json.load(f)

        self.client = BinanceClient(testnet=False)
        self.benchmark_symbol = self.strategy_config.get("benchmark", {}).get("market_symbol", "BTC/USDT")
        
        self.position_sizer = VolatilityTargetPositionSizer(
            max_risk_per_trade=self.config["RISK_LIMITS"]["max_risk_per_trade"]
        )
        self.initial_capital = self.config.get("INITIAL_CAPITAL", 10000.0)
        self.pairs = self.config.get("TRADING_PAIRS", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
        self.timeframe = self.config.get("TIMEFRAME", "1h")

        # Instantiate all enabled strategies
        self.strategies = []
        strat_configs = self.strategy_config.get("strategies", {})
        
        if strat_configs.get("momentum_multi_horizon", {}).get("enabled", True):
            self.strategies.append(MultiHorizonMomentumStrategy(config=strat_configs["momentum_multi_horizon"]))
            
        if strat_configs.get("vwap_mean_reversion", {}).get("enabled", True):
            self.strategies.append(VWAPRejectionStrategy(config=strat_configs["vwap_mean_reversion"]))
            
        if strat_configs.get("sentiment_filtered_trend", {}).get("enabled", True):
            self.strategies.append(SentimentFilteredTrendStrategy(config=strat_configs["sentiment_filtered_trend"]))

        if strat_configs.get("factor_regime_adaptive", {}).get("enabled", True):
            self.strategies.append(FactorRegimeStrategy(config=strat_configs["factor_regime_adaptive"]))

        if strat_configs.get("first_passage_value", {}).get("enabled", True):
            self.strategies.append(FirstPassageValueStrategy(config=strat_configs["first_passage_value"]))

        if strat_configs.get("qubo_portfolio_selector", {}).get("enabled", True):
            self.strategies.append(QUBOPortfolioStrategy(config=strat_configs["qubo_portfolio_selector"]))

    def run_backtest(self, days: int = 30) -> Dict[str, Any]:
        """Runs fast in-memory multi-strategy backtest across historical pairs."""
        print(f"\n===============================================================================")
        print(f"  RUNNING 30-DAY ASSET-AGNOSTIC BACKTEST (LOOKBACK: {days} DAYS, TIMEFRAME: {self.timeframe})")
        print(f"===============================================================================\n")

        # 1. Pre-load benchmark data
        print(f"[Backtester] Fetching benchmark series for {self.benchmark_symbol}...")
        benchmark_ohlcv = self.client.fetch_historical_ohlcv(
            self.benchmark_symbol,
            timeframe=self.timeframe,
            days=days
        )
        if benchmark_ohlcv.empty:
            print(f"[Backtester] Failed to download benchmark {self.benchmark_symbol}.")
            return {}

        bench_ret_30d = ((benchmark_ohlcv['close'].iloc[-1] - benchmark_ohlcv['close'].iloc[0]) / benchmark_ohlcv['close'].iloc[0]) * 100.0
        print(f"  -> Benchmark {self.benchmark_symbol} 30-Day Return: {bench_ret_30d:+.2f}%")

        results = {}

        # 2. Pre-load historical candles for all target pairs
        market_data = {}
        for symbol in self.pairs:
            print(f"[Backtester] Loading historical series for {symbol} ({days} days)...")
            ohlcv_df = self.client.fetch_historical_ohlcv(symbol, timeframe=self.timeframe, days=days)
            if not ohlcv_df.empty and len(ohlcv_df) >= 50:
                market_data[symbol] = ohlcv_df
                print(f"  -> Loaded {len(ohlcv_df)} bars for {symbol}")
            else:
                print(f"  -> Insufficient data for {symbol}, skipped.")

        # 3. Pre-compute rolling features for speed
        bench_closes = benchmark_ohlcv['close']
        bench_log_ret = np.log(bench_closes / bench_closes.shift(1)).fillna(0.0)

        for strategy in self.strategies:
            strat_name = strategy.name
            results[strat_name] = {
                "trades": [],
                "equity_curve": [self.initial_capital],
                "capital": self.initial_capital,
                "bep_events": 0,
                "trailing_events": 0
            }

            for symbol, ohlcv_df in market_data.items():
                capital = results[strat_name]["capital"]
                position = None
                cooldown_until_idx = 0
                trades = []
                n_bars = len(ohlcv_df)

                # Precompute volatility
                returns = ohlcv_df['close'].pct_change().fillna(0.0)
                rolling_vol = returns.rolling(21).std().fillna(0.02).values
                t_log_ret = np.log(ohlcv_df['close'] / ohlcv_df['close'].shift(1)).fillna(0.0)

                for i in range(50, n_bars):
                    sub_df = ohlcv_df.iloc[:i]
                    current_price = float(ohlcv_df['close'].iloc[i])
                    volatility = float(rolling_vol[i])

                    # Fast regime detection from precomputed returns
                    b_ret_tail = bench_log_ret.iloc[max(0, i-24):i]
                    cum_bench = float(b_ret_tail.sum())
                    curr_bench_vol = float(b_ret_tail.std() * np.sqrt(365 * 24)) if len(b_ret_tail) > 1 else 0.20
                    
                    if curr_bench_vol > 0.60:
                        current_regime = "HIGH_VOLATILITY_CRISIS"
                    elif cum_bench > 0.015:
                        current_regime = "BULL_TREND"
                    elif cum_bench < -0.015:
                        current_regime = "BEAR_TREND"
                    else:
                        current_regime = "MEAN_REVERSION_CHOP"

                    # Alpha / Beta
                    target_ret_tail = t_log_ret.iloc[max(0, i-24):i].values
                    bench_ret_tail = b_ret_tail.values
                    if len(target_ret_tail) > 5 and np.var(bench_ret_tail) > 1e-8:
                        beta = float(np.cov(target_ret_tail, bench_ret_tail)[0, 1] / np.var(bench_ret_tail))
                        alpha = float(np.mean(target_ret_tail) - beta * np.mean(bench_ret_tail))
                    else:
                        alpha, beta = 0.0, 1.0

                    market_state = {
                        "regime": current_regime,
                        "alpha": alpha,
                        "beta": beta,
                        "benchmark_return_24h": cum_bench
                    }

                    try:
                        signal_score = strategy.generate_signal(sub_df, market_state=market_state)
                    except TypeError:
                        signal_score = strategy.generate_signal(sub_df)

                    # 1. Evaluate Active Position (BEP, Trailing, Hard SL)
                    if position is not None:
                        action, updated_pos, closed_trade = PositionLifecycleManager.evaluate_active_position(
                            position=position,
                            current_price=current_price
                        )

                        if action == "MOVED_BEP":
                            position = updated_pos
                            results[strat_name]["bep_events"] += 1
                        elif action == "TRAILED_TP":
                            position = updated_pos
                            results[strat_name]["trailing_events"] += 1
                        elif action == "CLOSED" and closed_trade:
                            capital += closed_trade["net_pnl"]
                            trades.append(closed_trade)
                            position = None
                            if "STOP_LOSS" in closed_trade["exit_reason"]:
                                cooldown_until_idx = i + 3 # Cooldown 3 bars
                        else:
                            position = updated_pos

                    # 2. Evaluate New Entry
                    if position is None and i >= cooldown_until_idx:
                        # Regime Hard-Gate
                        is_trend_strat = strat_name in ["sentiment_filtered_trend", "momentum_multi_horizon"]
                        if is_trend_strat and current_regime in ["HIGH_VOLATILITY_CRISIS", "MEAN_REVERSION_CHOP"]:
                            results[strat_name]["equity_curve"].append(capital)
                            continue

                        sizing = self.position_sizer.calculate_position_size(
                            current_price=current_price,
                            capital=capital,
                            score=signal_score,
                            volatility=volatility,
                            risk_budget_ratio=strategy.config.get("risk_budget", 0.01),
                            regime=current_regime
                        )

                        if sizing["direction"] != 0:
                            position = {
                                "symbol": symbol,
                                "direction": sizing["direction"],
                                "entry_price": current_price,
                                "units": sizing["units"],
                                "initial_sl_price": sizing["sl_price"],
                                "current_sl_price": sizing["sl_price"],
                                "initial_tp_price": sizing["tp_price"],
                                "current_tp_price": sizing["tp_price"],
                                "risk_dollar": sizing["risk_dollar"],
                                "is_bep_activated": False,
                                "is_trailing_activated": False,
                                "entry_time": str(sub_df['timestamp'].iloc[-1]),
                                "strategy_name": strat_name
                            }

                    results[strat_name]["equity_curve"].append(capital)

                results[strat_name]["trades"].extend(trades)
                results[strat_name]["capital"] = capital

        # Compute Institutional Performance Metrics Table
        summary_rows = []
        parsed_summary = {}

        for strat_name, res in results.items():
            cap = res["capital"]
            trades = res["trades"]
            total_t = len(trades)
            net_pnl = cap - self.initial_capital
            ret_pct = (net_pnl / self.initial_capital) * 100.0
            
            wins = [t for t in trades if t["net_pnl"] > 0]
            losses = [t for t in trades if t["net_pnl"] <= 0]
            win_rate = (len(wins) / total_t * 100.0) if total_t > 0 else 0.0
            
            gross_win = sum(t["net_pnl"] for t in wins)
            gross_loss = abs(sum(t["net_pnl"] for t in losses))
            pf = (gross_win / gross_loss) if gross_loss > 0 else (gross_win if gross_win > 0 else 1.0)
            
            avg_win = np.mean([t["net_pnl"] for t in wins]) if wins else 0.0
            avg_loss = abs(np.mean([t["net_pnl"] for t in losses])) if losses else 0.0
            ev = ((win_rate / 100.0) * avg_win) - ((1.0 - (win_rate / 100.0)) * avg_loss)

            eq_curve = np.array(res["equity_curve"])
            peak = np.maximum.accumulate(eq_curve)
            dd = (eq_curve - peak) / peak
            max_dd = abs(dd.min()) * 100.0

            returns = np.diff(eq_curve) / eq_curve[:-1]
            std_ret = np.std(returns)
            sharpe = (np.mean(returns) / (std_ret + 1e-8)) * np.sqrt(365 * 24) if std_ret > 0 else 0.0
            excess_return = ret_pct - bench_ret_30d

            if sharpe >= 1.0 and net_pnl > 0:
                verdict = "🟢 Superior Alpha"
            elif net_pnl >= 0:
                verdict = "🟡 Positive Baseline"
            else:
                verdict = "🔴 Capital Defending"

            summary_rows.append([
                strat_name,
                f"${cap:,.2f}",
                f"${net_pnl:+,.2f} ({ret_pct:+.2f}%)",
                total_t,
                f"{win_rate:.1f}%",
                f"{pf:.2f}",
                f"${ev:+.2f}",
                f"-{max_dd:.2f}%",
                f"{sharpe:.2f}",
                f"{excess_return:+.2f}%",
                f"🛡️{res['bep_events']} 🚀{res['trailing_events']}",
                verdict
            ])

            parsed_summary[strat_name] = {
                "capital": cap,
                "net_pnl": net_pnl,
                "ret_pct": ret_pct,
                "total_trades": total_t,
                "win_rate": win_rate,
                "profit_factor": pf,
                "expected_value": ev,
                "max_drawdown": max_dd,
                "sharpe": sharpe,
                "excess_return": excess_return,
                "bep_events": res["bep_events"],
                "trailing_events": res["trailing_events"],
                "verdict": verdict
            }

        summary_rows.sort(key=lambda x: float(x[8]), reverse=True)

        print("\n" + "="*115)
        print("                 30-DAY HISTORICAL BACKTEST PERFORMANCE & BENCHMARK COMPARISON                 ")
        print("="*115)
        print(f" 🌐 30-Day Benchmark: {self.benchmark_symbol} Return: {bench_ret_30d:+.2f}%")
        print("="*115)
        print(tabulate(
            summary_rows,
            headers=["Strategy", "Final Capital", "Net PnL", "Trades", "Win Rate", "Prof Factor", "E[X]", "Max DD", "Sharpe", "Alpha (vs Mkt)", "BEP/Trail", "Verdict"],
            tablefmt="grid"
        ))

        return {
            "benchmark_return_30d": bench_ret_30d,
            "strategies": parsed_summary
        }

if __name__ == "__main__":
    tester = MultiStrategyBacktester()
    tester.run_backtest(days=30)
