"""
TradeProject Dashboard -- main entry point (Overview page).

Run with (from the project root, i.e. the folder containing config.json):
    streamlit run ui/app.py

This dashboard is READ-ONLY with respect to the trading engine: it never
starts/stops the worker (run_scheduler.py) and never places trades. It only
reads logs/paper_ledger.json and logs/leaderboard.json, which the worker
writes to continuously while running in a separate process.
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd

from ui.data_loader import (
    load_ledger,
    load_leaderboard,
    get_benchmark_meta,
    get_overview_metrics,
    get_strategy_summary_rows,
)
st.set_page_config(
    page_title="TradeProject Dashboard",
    page_icon="📈",
    layout="wide",
)

st.title("📈 TradeProject — Overview")
st.caption("Dashboard baca-saja untuk engine multi-strategi (logs/paper_ledger.json)")

ledger = load_ledger()

if not ledger:
    st.warning(
        "Belum ada data di `logs/paper_ledger.json`.\n\n"
        "Jalankan worker terlebih dahulu di terminal terpisah:\n\n"
        "```bash\n"
        "python run_scheduler.py\n"
        "```\n"
        "atau satu tick manual dengan `python main.py --mode paper`."
    )
    st.stop()

metrics = get_overview_metrics(ledger)
benchmark = get_benchmark_meta(ledger)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Strategi Aktif", metrics["num_strategies"])
col2.metric("Total Equity", f"${metrics['total_equity']:,.2f}")
col3.metric("Total PnL", f"${metrics['total_pnl']:,.2f}")
col4.metric("Posisi Terbuka", metrics["total_open_positions"])

st.divider()

if benchmark:
    st.subheader("🌐 Market Benchmark")
    b1, b2, b3 = st.columns(3)
    b1.metric("Symbol", benchmark.get("benchmark_symbol", "N/A"))
    b2.metric("Return 24h", f"{benchmark.get('benchmark_return_24h', 0.0):+.2%}")
    b3.metric("Regime", benchmark.get("regime", "N/A"))
    st.divider()

st.subheader("Ringkasan per Strategi")
rows = get_strategy_summary_rows(ledger)
if rows:
    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Equity": st.column_config.NumberColumn(format="$%.2f"),
            "PnL": st.column_config.NumberColumn(format="$%+.2f"),
        },
    )
else:
    st.info("Belum ada strategi tercatat di ledger.")

st.info(
    "Gunakan menu di sidebar kiri untuk melihat **Leaderboard** lengkap "
    "(Sharpe, win rate, profit factor, dll) dan **Equity Curve** interaktif "
    "tiap strategi."
)
