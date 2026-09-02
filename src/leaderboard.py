"""
Multi-Strategy Benchmark Leaderboard Generator.
Implements Tahap 3, Tahap A, Tahap S, Tahap W & Microstructure reporting:
- Ranks all active strategies by risk-adjusted return (Sharpe, Profit Factor, E[X], Max DD, Alpha vs Benchmark).
- Tracks Order Book Execution & Position Lifecycle metrics (BEP Protection, Trailing TP, Pending Orders).
"""

import json
import os
import numpy as np
from tabulate import tabulate
from typing import Dict, Any

class StrategyLeaderboard:
    """
    Quantitative Strategy Leaderboard & Performance Attribution.
    Compares active strategies side-by-side against the Market Benchmark.
    """
    def __init__(self, ledger_file: str = "logs/paper_ledger.json"):
        self.ledger_file = ledger_file

    def generate_leaderboard(self) -> Dict[str, Any]:
        """Generates and prints strategy performance leaderboard with benchmark and lifecycle attribution."""
        if not os.path.exists(self.ledger_file):
            print(f"[Leaderboard] Ledger file {self.ledger_file} not found. Run paper trader first.")
            return {}

        with open(self.ledger_file, "r") as f:
            ledger_data = json.load(f)

        benchmark_meta = ledger_data.get("_benchmark_meta", {})
        benchmark_sym = benchmark_meta.get("benchmark_symbol", "BTC/USDT")
        benchmark_regime = benchmark_meta.get("regime", "N/A")
        benchmark_ret_24h = benchmark_meta.get("benchmark_return_24h", 0.0)

        leaderboard_rows = []
        metrics_dict = {}

        for strat_name, data in ledger_data.items():
            if strat_name.startswith("_"):
                continue

            capital = data.get("capital", 10000.0)
            initial_cap = 10000.0
            net_pnl = capital - initial_cap
            return_pct = (net_pnl / initial_cap) * 100.0
            
            closed_trades = data.get("closed_trades", [])
            open_positions = data.get("open_positions", {})
            pending_orders = data.get("pending_orders", {})
            bep_events = data.get("bep_events", 0)
            trailing_events = data.get("trailing_tp_events", 0)
            total_trades = len(closed_trades)

            wins = [t for t in closed_trades if t.get("net_pnl", 0) > 0]
            losses = [t for t in closed_trades if t.get("net_pnl", 0) <= 0]
            win_rate = (len(wins) / total_trades * 100.0) if total_trades > 0 else 0.0

            # Calculate Profit Factor
            gross_win = sum(t.get("net_pnl", 0) for t in wins)
            gross_loss = abs(sum(t.get("net_pnl", 0) for t in losses))
            profit_factor = (gross_win / gross_loss) if gross_loss > 0 else (gross_win if gross_win > 0 else 1.0)

            # Calculate Expected Value E[X]
            avg_win = np.mean([t["net_pnl"] for t in wins]) if wins else 0.0
            avg_loss = abs(np.mean([t["net_pnl"] for t in losses])) if losses else 0.0
            expected_val = ((win_rate / 100.0) * avg_win) - ((1.0 - (win_rate / 100.0)) * avg_loss)

            # Equity curve statistics
            eq_curve = [item.get("equity", initial_cap) for item in data.get("equity_curve", [])]
            if len(eq_curve) > 1:
                eq_arr = np.array(eq_curve)
                peak = np.maximum.accumulate(eq_arr)
                dd = (eq_arr - peak) / peak
                max_dd = abs(dd.min()) * 100.0
                returns = np.diff(eq_arr) / eq_arr[:-1]
                std_ret = np.std(returns)
                sharpe = (np.mean(returns) / (std_ret + 1e-8)) * np.sqrt(365 * 24 * 60) if std_ret > 0 else 0.0
            else:
                max_dd = 0.0
                sharpe = 0.0

            # Excess Return / Alpha vs Benchmark
            excess_return = return_pct - (benchmark_ret_24h * 100.0)

            # Status recommendation
            if sharpe >= 1.2 and max_dd <= 10.0:
                status = "🟢 Superior (Alpha)"
            elif sharpe >= 0.0:
                status = "🟡 Evaluating"
            else:
                status = "🔴 Non-performing"

            leaderboard_rows.append([
                strat_name,
                f"${capital:,.2f}",
                f"${net_pnl:+,.2f} ({return_pct:+.2f}%)",
                f"{total_trades} (Open:{len(open_positions)}, Pend:{len(pending_orders)})",
                f"{win_rate:.1f}%",
                f"{profit_factor:.2f}",
                f"${expected_val:+.2f}",
                f"-{max_dd:.2f}%",
                f"{sharpe:.2f}",
                f"{excess_return:+.2f}%",
                f"🛡️{bep_events} 🚀{trailing_events}",
                status
            ])

            metrics_dict[strat_name] = {
                "current_capital": capital,
                "net_pnl": net_pnl,
                "return_pct": return_pct,
                "total_trades": total_trades,
                "open_positions": len(open_positions),
                "pending_orders": len(pending_orders),
                "bep_events": bep_events,
                "trailing_tp_events": trailing_events,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "expected_value": expected_val,
                "max_drawdown_pct": max_dd,
                "sharpe_ratio": sharpe,
                "excess_return_vs_benchmark": excess_return,
                "status": status
            }

        # Sort leaderboard by Sharpe ratio descending
        leaderboard_rows.sort(key=lambda x: float(x[8]), reverse=True)

        print("\n" + "="*105)
        print("                   ASSET-AGNOSTIC MULTI-STRATEGY PERFORMANCE LEADERBOARD                   ")
        print("="*105)
        if benchmark_meta:
            print(f" 🌐 Market Benchmark: {benchmark_sym} | 24h Return: {benchmark_ret_24h:+.2%} | Global Regime: [{benchmark_regime}]")
            print("="*105)
            
        print(tabulate(
            leaderboard_rows,
            headers=["Strategy", "Equity", "Net PnL", "Trades", "Win Rate", "Prof Factor", "E[X]", "Max DD", "Sharpe", "Alpha (vs Mkt)", "BEP / Trail", "Verdict"],
            tablefmt="grid"
        ))

        os.makedirs("logs", exist_ok=True)
        with open("logs/leaderboard.json", "w") as f:
            json.dump({
                "benchmark": benchmark_meta,
                "strategies": metrics_dict
            }, f, indent=2)

        return metrics_dict

if __name__ == "__main__":
    board = StrategyLeaderboard()
    board.generate_leaderboard()
