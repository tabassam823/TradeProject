"""
Equity Curve page — interactive Plotly charts per strategy, sourced
from the `equity_curve` field inside logs/paper_ledger.json (written by
src/paper_trader.py on every tick).
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.data_loader import load_ledger, get_strategy_names, get_equity_curve_df

st.set_page_config(page_title="Equity Curve", page_icon="📉", layout="wide")
st.title("📉 Equity Curve & Drawdown")

ledger = load_ledger()
names = get_strategy_names(ledger)

if not names:
    st.warning("Belum ada strategi di ledger. Jalankan worker dulu.")
    st.stop()

selected = st.multiselect(
    "Pilih strategi untuk dibandingkan",
    options=names,
    default=names,
)

if not selected:
    st.info("Pilih minimal satu strategi di atas.")
    st.stop()

fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    row_heights=[0.7, 0.3],
    vertical_spacing=0.06,
    subplot_titles=("Equity ($)", "Drawdown (%)"),
)

any_data = False
for name in selected:
    df = get_equity_curve_df(ledger, name)
    if df.empty:
        continue
    any_data = True
    fig.add_trace(
        go.Scatter(x=df["timestamp"], y=df["equity"], mode="lines", name=name),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"], y=df["drawdown_pct"], mode="lines",
            name=f"{name} (DD)", showlegend=False, fill="tozeroy",
        ),
        row=2, col=1,
    )

if not any_data:
    st.info(
        "Strategi yang dipilih belum punya titik equity curve. "
        "Ini normal kalau worker baru saja dijalanjakan.")
    st.stop()

fig.update_layout(
    height=650,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=60, b=20),
)
st.plotly_chart(fig, use_container_width=True)

st.caption("Data di‑cache 10 detik (@st.cache_data(ttl=10) di data_loader.py). Refresh browser atau tunggu rerun otomatis untuk melihat tick terbaru.")
