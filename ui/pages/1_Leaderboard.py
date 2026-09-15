"""
Leaderboard page -- reads the pre‑computed metrics in
logs/leaderboard.json (produced by src/leaderboard.py). This page does not
recompute anything; it just displays what the engine already calculated.
"""

import streamlit as st
import pandas as pd

from ui.data_loader import load_leaderboard

st.set_page_config(page_title="Leaderboard", page_icon="🏆", layout="wide")
st.title("🏆 Strategy Leaderboard")

board = load_leaderboard()

if not board or "strategies" not in board or not board["strategies"]:
    st.warning(
        "Belum ada `logs/leaderboard.json`. File ini dibuat otomatis setiap "
        "5 tick oleh `run_scheduler.py`, atau jalankan manual:\n\n"
        "```bash\npython main.py --mode leaderboard\n```"
    )
    st.stop()

benchmark = board.get("benchmark", {})
if benchmark:
    st.caption(
        f"Benchmark: **{benchmark.get('benchmark_symbol', 'N/A')}**  |  "
        f"Return 24h: **{benchmark.get('benchmark_return_24h', 0.0):+.2%}**  |  "
        f"Regime: **{benchmark.get('regime', 'N/A')}**"
    )

strategies = board["strategies"]
rows = []
for name, m in strategies.items():
    rows.append({
        "Strategi": name,
        "Equity": m.get("current_capital", 0.0),
        "Net PnL": m.get("net_pnl", 0.0),
        "Return %": m.get("return_pct", 0.0),
        "Trades": m.get("total_trades", 0),
        "Posisi Terbuka": m.get("open_positions", 0),
        "Win Rate %": m.get("win_rate", 0.0),
        "Profit Factor": m.get("profit_factor", 0.0),
        "E[X]": m.get("expected_value", 0.0),
        "Sharpe": m.get('sharpe_ratio', 0.0),
        "Max DD %": m.get("max_drawdown_pct", 0.0),
        "Alpha vs Benchmark %": m.get("excess_return_vs_benchmark", 0.0),
        "Status": m.get("status", ""),
    })

df = pd.DataFrame(rows).sort_values("Sharpe", ascending=False).reset_index(drop=True)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Equity": st.column_config.NumberColumn(format="$%.2f"),
        "Net PnL": st.column_config.NumberColumn(format="$%+.2f"),
        "Return %": st.column_config.NumberColumn(format="%+.2f%%"),
        "E[X]": st.column_config.NumberColumn(format="$%+.2f"),
        "Win Rate %": st.column_config.NumberColumn(format="%.1f%%"),
        "Profit Factor": st.column_config.NumberColumn(format="%.2f"),
        "Sharpe": st.column_config.NumberColumn(format="%.2f"),
        "Max DD %": st.column_config.NumberColumn(format="-%.2f%%"),
        "Alpha vs Benchmark %": st.column_config.NumberColumn(format="%+.2f%%"),
    },
)

st.caption(
    "Diurutkan berdasarkan Sharpe Ratio (tertinggi di atas). Status "
    "🟢/🟡/🔴 dihitung oleh `src/leaderboard.py` berdasarkan Sharpe dan max drawdown."
)

with st.expander("Lihat metrik mentah (JSON)"):
    st.json(board)
