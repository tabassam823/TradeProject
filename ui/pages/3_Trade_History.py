"""Trade History page -- browse and filter closed trades across all
strategies, sourced from `closed_trades` inside logs/paper_ledger.json
(written by src/core/position_lifecycle_manager.py via src/paper_trader.py).

Fields per trade: symbol, direction (1=long/-1=short), entry_price,
exit_price, net_pnl, return_pct, entry_time, exit_time, exit_reason."""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px

from ui.data_loader import load_ledger, get_strategy_names, get_all_trades_df

st.set_page_config(page_title="Trade History", page_icon="📜", layout="wide")
st.title("📜 Trade History")

ledger = load_ledger()
strategy_names = get_strategy_names(ledger)

if not strategy_names:
    st.warning("Belum ada strategi di ledger. Jalankan worker dulu.")
    st.stop()

all_trades = get_all_trades_df(ledger)

if all_trades.empty:
    st.info(
        "Belum ada trade yang tertutup (closed_trades kosong di semua "
        "strategi). Data akan muncul di sini begitu ada posisi yang "
        "kena Stop Loss atau Take Profit."
    )
    st.stop()

# ---------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------
f1, f2, f3, f4 = st.columns(4)

with f1:
    strat_filter = st.multiselect(
        "Strategi", options=strategy_names, default=strategy_names
    )

with f2:
    symbol_options = sorted(all_trades["symbol"].dropna().unique().tolist())
    symbol_filter = st.multiselect(
        "Symbol", options=symbol_options, default=symbol_options
    )

with f3:
    side_options = sorted(all_trades.get("side", pd.Series(dtype=str)).dropna().unique().tolist())
    side_filter = st.multiselect(
        "Arah", options=side_options, default=side_options
    )

with f4:
    result_filter = st.radio(
        "Hasil", options=["Semua", "Profit saja", "Loss saja"], horizontal=True
    )

# Date range filter (based on exit_time)
if "exit_time" in all_trades.columns and all_trades["exit_time"].notna().any():
    min_date = all_trades["exit_time"].min().date()
    max_date = all_trades["exit_time"].max().date()
    date_range = st.date_input(
        "Rentang tanggal (exit)", value=(min_date, max_date),
        min_value=min_date, max_value=max_date,
    )
else:
    date_range = None

# ---------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------
filtered = all_trades.copy()

if strat_filter:
    filtered = filtered[filtered["strategy"].isin(strat_filter)]
if symbol_filter:
    filtered = filtered[filtered["symbol"].isin(symbol_filter)]
if side_filter and "side" in filtered.columns:
    filtered = filtered[filtered["side"].isin(side_filter)]
if result_filter == "Profit saja":
    filtered = filtered[filtered["net_pnl"] > 0]
elif result_filter == "Loss saja":
    filtered = filtered[filtered["net_pnl"] <= 0]
if date_range and isinstance(date_range, tuple) and len(date_range) == 2 and "exit_time" in filtered.columns:
    start_d, end_d = date_range
    filtered = filtered[(filtered["exit_time"].dt.date >= start_d) & (filtered["exit_time"].dt.date <= end_d)]

st.divider()

# ---------------------------------------------------------------------
# Summary metrics for the filtered set
# ---------------------------------------------------------------------
total_trades = len(filtered)
if total_trades == 0:
    st.info("Tidak ada trade yang cocok dengan filter di atas.")
    st.stop()

wins = filtered[filtered["net_pnl"] > 0]
losses = filtered[filtered["net_pnl"] <= 0]
win_rate = (len(wins) / total_trades * 100.0) if total_trades else 0.0
total_pnl = filtered["net_pnl"].sum()
avg_win = wins["net_pnl"].mean() if not wins.empty else 0.0
avg_loss = losses["net_pnl"].mean() if not losses.empty else 0.0

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Trades", total_trades)
m2.metric("Win Rate", f"{win_rate:.1f}%")
m3.metric("Total Net PnL", f"${total_pnl:+,.2f}")
m4.metric("Rata-rata Win", f"${avg_win:+,.2f}")
m5.metric("Rata-rata Loss", f"${avg_loss:+,.2f}")

st.divider()

# ---------------------------------------------------------------------
# Histogram of win/loss distribution
# ---------------------------------------------------------------------
st.subheader("Distribusi Net PnL per Trade")
hist_fig = px.histogram(
    filtered,
    x="net_pnl",
    color=filtered["net_pnl"].apply(lambda x: "Profit" if x > 0 else "Loss"),
    nbins=30,
    color_discrete_map={"Profit": "#2ecc71", "Loss": "#e74c3c"},
    labels={"net_pnl": "Net PnL ($)", "color": "Hasil"},
)
hist_fig.update_layout(height=350, bargap=0.1, legend_title_text="Hasil")
st.plotly_chart(hist_fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------
# Trade table
# ---------------------------------------------------------------------
st.subheader(f"Daftar Trade ({total_trades})")

display_cols = [c for c in [
    "strategy", "symbol", "side", "entry_time", "exit_time",
    "entry_price", "exit_price", "net_pnl", "return_pct", "exit_reason",
] if c in filtered.columns]

display_df = filtered[display_cols].rename(columns={
    "strategy": "Strategi",
    "symbol": "Symbol",
    "side": "Arah",
    "entry_time": "Waktu Masuk",
    "exit_time": "Waktu Keluar",
    "entry_price": "Harga Masuk",
    "exit_price": "Harga Keluar",
    "net_pnl": "Net PnL",
    "return_pct": "Return %",
    "exit_reason": "Alasan Keluar",
})

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Harga Masuk": st.column_config.NumberColumn(format="$%.4f"),
        "Harga Keluar": st.column_config.NumberColumn(format="$%.4f"),
        "Net PnL": st.column_config.NumberColumn(format="$%+.2f"),
        "Return %": st.column_config.NumberColumn(format="%+.2f%%"),
    },
)

st.caption(
    "Diurutkan dari trade paling baru ke lama (berdasarkan waktu keluar). "
    "Gunakan filter di atas untuk mempersempit hasil."
)
