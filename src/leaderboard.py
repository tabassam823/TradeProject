import json
import os
import numpy as np
from tabulate import tabulate
from typing import Dict, Any

class StrategyLeaderboard:
    """
    Multi-Strategy Leaderboard Generator.
    Reads paper trading sub-ledgers and backtest results to rank strategies
    by risk-adjusted return (Sharpe Ratio, Win Rate, Expected Value E[X], Drawdown).
    """
    def __init__(self, ledger_file: str = "logs/paper_ledger.json"):
        self.ledger_file = ledger_file

    def generate_leaderboard(self) -> Dict[str, Any]:
        """Generates and prints strategy performance leaderboard."""
        if not os.path.exists(self.ledger_file):
            print(f"[Leaderboard] Ledger file {self.ledger_file} not found. Run paper trader first.")
            return {}

        with open(self.ledger_file, "r") as f:
            ledger_data = json.load(f)

        leaderboard_rows = []
        metrics_dict = {}

        for strat_name, data in ledger_data.items():
            capital = data.get("capital", 10000.0)
            initial_cap = 10000.0
            net_pnl = capital - initial_cap
            return_pct = (net_pnl / initial_cap) * 100.0
            
            closed_trades = data.get("closed_trades", [])
            open_positions = data.get("open_positions", {})
            total_trades = len(closed_trades)

            wins = [t for t in closed_trades if t.get("net_pnl", 0) > 0]
            losses = [t for t in closed_trades if t.get("net_pnl", 0) <= 0]
            win_rate = (len(wins) / total_trades * 100.0) if total_trades > 0 else 0.0

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
                sharpe = (np.mean(returns) / (np.std(returns) + 1e-8)) * np.sqrt(365 * 24)
            else:
                max_dd = 0.0
                sharpe = 0.0

            # Status recommendation
            if sharpe >= 1.0 and max_dd <= 10.0:
                status = "🟢 Superior (Live Ready)"
            elif sharpe >= 0.0:
                status = "🟡 Evaluating"
            else:
                status = "🔴 Non-performing"

            leaderboard_rows.append([
                strat_name,
                f"${capital:,.2f}",
                f"${net_pnl:+,.2f} ({return_pct:+.2f}%)",
                f"{total_trades} (Open: {len(open_positions)})",
                f"{win_rate:.1f}%",
                f"${expected_val:+.2f}",
                f"-{max_dd:.2f}%",
                f"{sharpe:.2f}",
                status
            ])

            metrics_dict[strat_name] = {
                "current_capital": capital,
                "net_pnl": net_pnl,
                "return_pct": return_pct,
                "total_trades": total_trades,
                "open_positions": len(open_positions),
                "win_rate": win_rate,
                "expected_value": expected_val,
                "max_drawdown_pct": max_dd,
                "sharpe_ratio": sharpe,
                "status": status
            }

        # Sort leaderboard by Sharpe ratio descending
        leaderboard_rows.sort(key=lambda x: float(x[7]), reverse=True)

        print("\n=======================================================================")
        print("                MULTI-STRATEGY PERFORMANCE LEADERBOARD                ")
        print("=======================================================================")
        print(tabulate(
            leaderboard_rows,
            headers=["Strategy", "Equity", "Net PnL", "Trades", "Win Rate", "Expected E[X]", "Max DD", "Sharpe", "Recommendation"],
            tablefmt="grid"
        ))

        os.makedirs("logs", exist_ok=True)
        with open("logs/leaderboard.json", "w") as f:
            json.dump(metrics_dict, f, indent=2)

        return metrics_dict

if __name__ == "__main__":
    board = StrategyLeaderboard()
    board.generate_leaderboard()
