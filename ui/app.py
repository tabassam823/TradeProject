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

metrics = get_overview_metrics(ledger) if ledger else {
    "num_strategies": 0, "total_equity": 10000.0, "total_pnl": 0.0, "total_open_positions": 0
}
benchmark = get_benchmark_meta(ledger) if ledger else None

if not ledger:
    st.info("ℹ️ Worker background belum dijalankan (`logs/paper_ledger.json` kosong). Anda tetap dapat menggunakan modul **SigTrade Analytic**, **PyTorch ML Lab**, dan **Head-to-Head Benchmark** melalui menu navigasi di sidebar kiri.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Strategi Aktif", metrics["num_strategies"])
col2.metric("Total Equity", f"${metrics['total_equity']:,.2f}")
col3.metric("Total PnL", f"${metrics['total_pnl']:,.2f}")
col4.metric("Posisi Terbuka", metrics["total_open_positions"])

st.divider()

# Module Navigator Cards (ala quant-tool)
st.markdown("### 🛠️ Modul Kuantitatif & Machine Learning")
m_col1, m_col2 = st.columns(2)

with m_col1:
    st.markdown("""
    #### 📐 Signature Trading (Closed-Form)
    - **[SigTrade Analytic Calibrator](📐_SigTrade_Analytic)** — Kalibrasi solusi analitik $\\ell^*$ (Theorem 3.1) dari data pasar historis.
    - **Signature Efficient Frontier** — Plot kurva frontier return ekspektasi vs volatilitas untuk alokasi risiko dinamis.
    - **Word Weight Inspection** — Dekomposisi bobot fungsional linear pada aljabar tensor.

    #### ⚔️ Backtesting & Benchmarking
    - **[Head-to-Head Benchmark](⚔️_Head_to_Head)** — Uji komparasi langsung: *Buy & Hold vs Markowitz (Order 0) vs SigTrade (Order 2) vs PyTorch Deep Model*.
    - **Underwater Drawdown Curves** — Validasi kontrol drawdown temporal khas path-dependent signature.
    """)

with m_col2:
    st.markdown("""
    #### 🧠 PyTorch Machine Learning Lab
    - **[PyTorch ML Lab](🧠_PyTorch_ML_Lab)** — Laboratorium interaktif untuk melatih neural network (*SigNetMLP* & *TimeSeriesLSTM*).
    - **Custom Portfolio Loss** — Pelatihan langsung mengoptimalkan *Mean-Variance Utility* atau *Sharpe Ratio* via backpropagation.
    - **Live Loss Convergence** — Pantau kurva konvergensi *Train vs Validation Loss* secara real-time.

    #### 📈 Execution & Post-Trade Analytics
    - **[MFE / MAE Execution Analysis](🎯_MFE_MAE_Analysis)** — Diagnosa kualitas eksekusi dari Quant-Analysis-Toolkit (analisis laba puncak, *left-on-table*, dan efisiensi keluar).
    - **[Leaderboard](1_Leaderboard)** & **[Equity Curve](2_Equity_Curve)** — Pantau metrik performa (Sharpe, Profit Factor, Win Rate) dan riwayat eksekusi posisi live/paper.
    - **Strategi Klasik Aktif** — Dual Thrust (Breakout), Awesome Oscillator (Momentum), Bollinger Reversion (Mean Reversion), dan Heikin-Ashi (Smoothed Trend).
    """)

st.divider()

if benchmark:
    st.subheader("🌐 Market Benchmark")
    b1, b2, b3 = st.columns(3)
    b1.metric("Symbol", benchmark.get("benchmark_symbol", "N/A"))
    b2.metric("Return 24h", f"{benchmark.get('benchmark_return_24h', 0.0):+.2%}")
    b3.metric("Regime", benchmark.get("regime", "N/A"))
    st.divider()

st.subheader("Ringkasan per Strategi")
rows = get_strategy_summary_rows(ledger) if ledger else []
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
    st.caption("Belum ada posisi paper trading aktif. Jalankan `python run_scheduler.py` untuk trading kontinu.")
