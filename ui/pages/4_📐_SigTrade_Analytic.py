"""
4_📐_SigTrade_Analytic.py
Streamlit Dashboard Module for Closed-Form Signature Trading Calibration.
Implements Futter et al. (2023) Theorem 3.1:
- Live data ingestion from Binance / Synthetic
- Closed-form analytical solver for optimal linear functional l*
- Signature Efficient Frontier curve visualization
- Weights inspection and model persistence
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.core.binance_client import BinanceClient
from src.core.sig_calibrator import calibrate_sigtrade, generate_efficient_frontier, save_weights
from src.core.sig_math import get_signature_dim, get_word_catalog

st.set_page_config(
    page_title="SigTrade Analytic Calibrator",
    page_icon="📐",
    layout="wide",
)

st.title("📐 Signature Trading — Analytic Closed-Form Calibrator")
st.markdown("""
Implementasi analitik **Signature Trading (Sig-Trading)** berdasarkan riset *Futter, Horvath, & Wiese (2023)*.
Menghasilkan vektor posisi optimal $\\ell^*$ dalam bentuk **solusi eksak** (closed-form) tanpa memerlukan *gradient descent*.
""")

st.divider()

# Sidebar parameters
st.sidebar.header("⚙️ Konfigurasi Kalibrasi")
symbol = st.sidebar.selectbox("Pilih Aset Tradable", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"], index=0)
timeframe = st.sidebar.selectbox("Timeframe", ["15m", "1h", "4h", "1d"], index=1)
limit_candles = st.sidebar.slider("Jumlah Candle Historis", min_value=100, max_value=1000, value=300, step=50)

st.sidebar.subheader("Parameter Teori Lintasan")
order = st.sidebar.slider("Order Truncation Signature (M)", min_value=1, max_value=3, value=2, help="Order 1 = Increments/Drift, Order 2 = Area/Kovariansi, Order 3 = Non-linear")
lookback_window = st.sidebar.slider("Lookback Window (W candle)", min_value=12, max_value=96, value=24, step=4)
stride = st.sidebar.slider("Window Stride (s)", min_value=1, max_value=6, value=2)

st.sidebar.subheader("Regularisasi & Risiko")
gamma = st.sidebar.select_slider(
    "Tikhonov Regularization (γ)",
    options=[1e-5, 1e-4, 5e-4, 1e-3, 1e-2],
    value=1e-4,
    help="Menjaga invertibilitas matriks kovarians signature"
)
delta = st.sidebar.number_input("Target Varians PnL (Δ)", min_value=0.001, max_value=0.5, value=0.01, step=0.005)

# Fetch Market Data
@st.cache_data(ttl=60)
def load_data(sym: str, tf: str, lim: int) -> pd.DataFrame:
    client = BinanceClient()
    df = client.fetch_ohlcv(sym, timeframe=tf, limit=lim)
    if df is None or df.empty:
        # Fallback to synthetic Brownian data if network issue
        dates = pd.date_range("2026-01-01", periods=lim, freq="1h")
        price = np.cumsum(np.random.randn(lim) * 50) + 60000.0
        df = pd.DataFrame({
            "timestamp": dates,
            "open": price, "high": price + 20, "low": price - 20,
            "close": price, "volume": np.abs(np.random.randn(lim) * 100 + 50)
        })
    return df

with st.spinner(f"Mengunduh data {symbol} ({timeframe})..."):
    df = load_data(symbol, timeframe, limit_candles)

col1, col2, col3 = st.columns(3)
col1.metric("Aset", symbol)
col2.metric("Harga Terakhir", f"${df['close'].iloc[-1]:,.2f}")
ret_total = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
col3.metric("Return Periode", f"{ret_total:+.2%}")

# Run Calibration
feature_cols = ["close", "volume"]
sig_dim = get_signature_dim(2 * len(feature_cols), order)

st.info(f"Dimensi ruang aljabar tensor lead-lag $T^{{({order})}}(\\mathbb{{R}}^{{{2 * len(feature_cols)}}})$: **{sig_dim} komponen/kata**.")

if st.button("🚀 Kalibrasi Solusi Analitik ℓ*", type="primary"):
    with st.spinner("Menghitung ekspektasi signature & inversi matriks kovarians..."):
        try:
            l_opt, mu_sig, Sigma_sig, meta = calibrate_sigtrade(
                df,
                feature_cols=feature_cols,
                target_price_col="close",
                lookback_window=lookback_window,
                stride=stride,
                order=order,
                gamma=gamma,
                target_variance_delta=delta
            )
            
            # Save weights
            save_weights(l_opt, meta, "models/sigtrade_weights.json")
            st.session_state["sigtrade_calib"] = {
                "l_opt": l_opt,
                "mu_sig": mu_sig,
                "Sigma_sig": Sigma_sig,
                "meta": meta
            }
            st.success("✅ Kalibrasi Berhasil! Bobot optimal telah disimpan ke `models/sigtrade_weights.json`.")
        except Exception as e:
            st.error(f"Gagal melakukan kalibrasi: {e}")

# Display Results if Calibrated
if "sigtrade_calib" in st.session_state:
    calib = st.session_state["sigtrade_calib"]
    meta = calib["meta"]
    l_opt = calib["l_opt"]
    mu_sig = calib["mu_sig"]
    Sigma_sig = calib["Sigma_sig"]
    
    st.subheader("📊 Hasil Kalibrasi & Metrik In-Sample")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sampel Lintasan (K)", f"{meta['num_samples']} windows")
    m2.metric("Expected PnL 𝔼[V_T]", f"{meta['expected_pnl']:+.4f}")
    m3.metric("Variance Var(V_T)", f"{meta['actual_variance']:.6f}")
    m4.metric("In-Sample Sharpe", f"{meta['sharpe_calib']:.2f}")
    
    # Efficient Frontier Chart
    st.subheader("📈 Signature Efficient Frontier (Theorem 3.1)")
    st_devs, exp_rets = generate_efficient_frontier(mu_sig, Sigma_sig, gamma=gamma)
    
    fig_ef = go.Figure()
    fig_ef.add_trace(go.Scatter(
        x=st_devs,
        y=exp_rets,
        mode="lines",
        name=f"Signature Frontier (Order {order})",
        line=dict(color="#00FFAA", width=3)
    ))
    
    # Add current calibrated point
    cur_std = np.sqrt(meta['actual_variance'])
    fig_ef.add_trace(go.Scatter(
        x=[cur_std],
        y=[meta['expected_pnl']],
        mode="markers",
        name="Solusi Terpilih (ℓ*)",
        marker=dict(color="#FF0055", size=14, symbol="star")
    ))
    
    fig_ef.update_layout(
        template="plotly_dark",
        title="Kurva Signature Efficient Frontier: Return Ekspektasi vs Volatilitas PnL",
        xaxis_title="Standard Deviation σ(V_T)",
        yaxis_title="Expected Return 𝔼[V_T]",
        hovermode="x unified",
        height=450
    )
    st.plotly_chart(fig_ef, use_container_width=True)
    
    # Top Signature Weights
    st.subheader("🔍 Dekomposisi Bobot Linear Functional ℓ*")
    catalog = get_word_catalog(2 * len(feature_cols), order)
    word_labels = [f"w_{i}" for i in range(len(l_opt))]
    
    top_indices = np.argsort(np.abs(l_opt))[-15:] # top 15 highest magnitude
    top_weights = l_opt[top_indices]
    top_labels = [word_labels[i] for i in top_indices]
    
    fig_bar = go.Figure(go.Bar(
        x=top_weights,
        y=top_labels,
        orientation="h",
        marker=dict(color=np.where(top_weights > 0, "#00FFAA", "#FF5555"))
    ))
    fig_bar.update_layout(
        template="plotly_dark",
        title="Top 15 Bobot Komponen Signature Terbesar (|ℓ*|)",
        xaxis_title="Nilai Bobot",
        yaxis_title="Suku Signature",
        height=400
    )
    st.plotly_chart(fig_bar, use_container_width=True)
