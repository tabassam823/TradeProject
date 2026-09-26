"""
6_⚔️_Head_to_Head.py
Comparative Benchmark Dashboard (inspired by quant-tool strategy backtester):
Evaluates and benchmarks multiple quantitative models:
1. Buy & Hold (Asset Benchmark)
2. Markowitz MPT (Order 0)
3. Closed-Form SigTrade (Order 1 and Order 2)
4. PyTorch Deep Model (Neural SigNet / LSTM)
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import torch

from src.core.binance_client import BinanceClient
from src.core.sig_calibrator import calibrate_sigtrade, load_weights
from src.core.sig_math import normalize_path, hoff_lead_lag, compute_signature
from src.core.sig_torch_models import create_model

st.set_page_config(
    page_title="Head-to-Head Benchmark",
    page_icon="⚔️",
    layout="wide",
)

st.title("⚔️ Head-to-Head Model Benchmark")
st.markdown("""
Uji komparasi performa strategi kuantitatif secara berdampingan:
**Buy & Hold** vs **Markowitz Klasik (Order 0)** vs **Closed-Form SigTrade (Order 2)** vs **PyTorch Deep Learning**.
""")

st.divider()

# Sidebar Setup
st.sidebar.header("⚙️ Konfigurasi Backtest")
symbol = st.sidebar.selectbox("Aset Benchmark", ["BTCUSDT", "ETHUSDT", "SOLUSDT"], index=0)
timeframe = st.sidebar.selectbox("Timeframe", ["1h", "4h", "1d"], index=0)
limit_candles = st.sidebar.slider("Jumlah Data", min_value=200, max_value=1000, value=400, step=50)

# Fetch Data
@st.cache_data(ttl=60)
def load_data(sym: str, tf: str, lim: int) -> pd.DataFrame:
    client = BinanceClient()
    df = client.fetch_ohlcv(sym, timeframe=tf, limit=lim)
    if df is None or df.empty:
        dates = pd.date_range("2026-01-01", periods=lim, freq="1h")
        price = np.cumsum(np.random.randn(lim) * 50) + 60000.0
        df = pd.DataFrame({
            "timestamp": dates,
            "open": price, "high": price + 20, "low": price - 20,
            "close": price, "volume": np.abs(np.random.randn(lim) * 100 + 50)
        })
    return df

with st.spinner("Mengunduh data pengujian..."):
    df = load_data(symbol, timeframe, limit_candles)

# Simulation Engine
W = 24
stride = 1
prices = df["close"].values
volumes = df["volume"].values
timestamps = df["timestamp"].values

if st.button("🚀 Jalankan Head-to-Head Backtest", type="primary"):
    with st.spinner("Menjalankan simulasi paralel 4 model..."):
        # 1. Train / Calibrate on first 60% of data
        split_idx = int(len(df) * 0.6)
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()
        
        # A. Calibrate Closed-form SigTrade (Order 2)
        feature_cols = ["close", "volume"]
        try:
            l_sig2, _, _, _ = calibrate_sigtrade(train_df, feature_cols=feature_cols, order=2, lookback_window=W)
        except Exception:
            l_sig2 = None
            
        # B. Calibrate Markowitz (Order 0 - Static mean/cov)
        try:
            l_markowitz, _, _, _ = calibrate_sigtrade(train_df, feature_cols=feature_cols, order=0, lookback_window=W)
        except Exception:
            l_markowitz = None
            
        # C. Check if PyTorch Deep Model exists
        torch_model = None
        chk_path = "models/torch_checkpoints/best_signet.pt"
        if os.path.exists(chk_path):
            try:
                chk = torch.load(chk_path, map_location="cpu")
                meta = chk.get("metadata", {})
                torch_model = create_model(meta.get("architecture", "SigNetMLP"), input_dim=meta.get("feature_dim", 21))
                torch_model.load_state_dict(chk["state_dict"])
                torch_model.eval()
            except Exception:
                torch_model = None

        # Out-of-sample forward simulation
        test_prices = test_df["close"].values
        test_timestamps = test_df["timestamp"].values
        test_features = test_df[feature_cols].values
        
        n_test = len(test_df)
        rets_asset = np.diff(test_prices) / test_prices[:-1]
        
        pos_bnh = np.ones(len(rets_asset))
        pos_markowitz = []
        pos_sig2 = []
        pos_torch = []
        
        for t in range(W, len(test_df)):
            window_raw = test_features[t - W:t]
            norm_w = normalize_path(window_raw)
            
            # Closed-form SigTrade Order 2
            if l_sig2 is not None:
                ll_w = hoff_lead_lag(norm_w)
                s2 = compute_signature(ll_w, order=2)
                raw_sig2 = float(np.dot(l_sig2[:len(s2)], s2[:len(l_sig2)]))
                pos_sig2.append(np.tanh(raw_sig2))
            else:
                pos_sig2.append(0.0)
                
            # Markowitz Order 0
            if l_markowitz is not None:
                pos_markowitz.append(np.tanh(float(l_markowitz[0])))
            else:
                pos_markowitz.append(0.0)
                
            # PyTorch Deep Model
            if torch_model is not None:
                with torch.no_grad():
                    ll_w = hoff_lead_lag(norm_w)
                    s_torch = compute_signature(ll_w, order=2)
                    tin = torch.from_numpy(s_torch.astype(np.float32)).unsqueeze(0)
                    pos_torch.append(float(torch_model(tin).item()))
            else:
                pos_torch.append(0.0)
                
        # Align lengths
        min_len = len(pos_sig2)
        rets_eval = rets_asset[-min_len:]
        time_eval = test_timestamps[-min_len:]
        
        pnl_bnh = rets_eval
        pnl_mpt = np.array(pos_markowitz) * rets_eval
        pnl_sig = np.array(pos_sig2) * rets_eval
        pnl_torch = np.array(pos_torch) * rets_eval
        
        # Cumulative Equities
        eq_bnh = np.cumprod(1.0 + pnl_bnh)
        eq_mpt = np.cumprod(1.0 + pnl_mpt)
        eq_sig = np.cumprod(1.0 + pnl_sig)
        eq_torch = np.cumprod(1.0 + pnl_torch)
        
        # Calculate Metrics Function
        def calc_metrics(pnl_arr, eq_arr):
            tot_ret = (eq_arr[-1] - 1.0) * 100.0
            mean_r = np.mean(pnl_arr)
            std_r = np.std(pnl_arr) + 1e-12
            ann_factor = np.sqrt(8760 if timeframe == "1h" else 365)
            sharpe = (mean_r / std_r) * ann_factor
            
            # Max Drawdown
            peak = np.maximum.accumulate(eq_arr)
            dd = (eq_arr - peak) / peak
            mdd = np.min(dd) * 100.0
            
            win_rate = np.mean(pnl_arr > 0) * 100.0
            return {
                "Total Return (%)": f"{tot_ret:+.2f}%",
                "Sharpe Ratio": f"{sharpe:.2f}",
                "Max Drawdown (%)": f"{mdd:.2f}%",
                "Win Rate (%)": f"{win_rate:.1f}%"
            }
            
        metrics_table = {
            "Model": ["Buy & Hold (Asset)", "Markowitz MPT (Order 0)", "SigTrade Analytic (Order 2)", "PyTorch Deep Model"],
            "Total Return (%)": [calc_metrics(pnl_bnh, eq_bnh)["Total Return (%)"],
                                calc_metrics(pnl_mpt, eq_mpt)["Total Return (%)"],
                                calc_metrics(pnl_sig, eq_sig)["Total Return (%)"],
                                calc_metrics(pnl_torch, eq_torch)["Total Return (%)"]],
            "Sharpe Ratio": [calc_metrics(pnl_bnh, eq_bnh)["Sharpe Ratio"],
                             calc_metrics(pnl_mpt, eq_mpt)["Sharpe Ratio"],
                             calc_metrics(pnl_sig, eq_sig)["Sharpe Ratio"],
                             calc_metrics(pnl_torch, eq_torch)["Sharpe Ratio"]],
            "Max Drawdown (%)": [calc_metrics(pnl_bnh, eq_bnh)["Max Drawdown (%)"],
                                 calc_metrics(pnl_mpt, eq_mpt)["Max Drawdown (%)"],
                                 calc_metrics(pnl_sig, eq_sig)["Max Drawdown (%)"],
                                 calc_metrics(pnl_torch, eq_torch)["Max Drawdown (%)"]],
            "Win Rate (%)": [calc_metrics(pnl_bnh, eq_bnh)["Win Rate (%)"],
                             calc_metrics(pnl_mpt, eq_mpt)["Win Rate (%)"],
                             calc_metrics(pnl_sig, eq_sig)["Win Rate (%)"],
                             calc_metrics(pnl_torch, eq_torch)["Win Rate (%)"]]
        }
        
        # Display Table
        st.subheader("📋 Ringkasan Kinerja Komparatif Out-of-Sample")
        st.dataframe(pd.DataFrame(metrics_table), use_container_width=True, hide_index=True)
        
        # Plotly Cumulative Equity Curve
        st.subheader("📈 Kurva Ekuitas Kumulatif (Cumulative Performance)")
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(x=time_eval, y=eq_sig, mode="lines", name="SigTrade Closed-Form (Order 2)", line=dict(color="#00FFAA", width=3)))
        fig_equity.add_trace(go.Scatter(x=time_eval, y=eq_torch, mode="lines", name="PyTorch Deep SigNet", line=dict(color="#FF00AA", width=2.5)))
        fig_equity.add_trace(go.Scatter(x=time_eval, y=eq_mpt, mode="lines", name="Markowitz MPT (Order 0)", line=dict(color="#FFAA00", width=2)))
        fig_equity.add_trace(go.Scatter(x=time_eval, y=eq_bnh, mode="lines", name="Buy & Hold (Asset)", line=dict(color="#888888", dash="dash")))
        fig_equity.update_layout(
            template="plotly_dark",
            xaxis_title="Waktu (Out-of-Sample)",
            yaxis_title="Nilai Portofolio (Base 1.0)",
            hovermode="x unified",
            height=450
        )
        st.plotly_chart(fig_equity, use_container_width=True)
        
        # Underwater Drawdown Plot
        st.subheader("🌊 Underwater Drawdown Profile (Kontrol Risiko Path-Dependent)")
        def calc_dd_curve(eq):
            pk = np.maximum.accumulate(eq)
            return (eq - pk) / pk * 100.0
            
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(x=time_eval, y=calc_dd_curve(eq_sig), mode="lines", name="SigTrade Drawdown", fill="tozeroy", line=dict(color="#00FFAA")))
        fig_dd.add_trace(go.Scatter(x=time_eval, y=calc_dd_curve(eq_bnh), mode="lines", name="Asset Drawdown", fill="tozeroy", line=dict(color="#FF5555", dash="dot")))
        fig_dd.update_layout(
            template="plotly_dark",
            xaxis_title="Waktu",
            yaxis_title="Drawdown (%)",
            height=350
        )
        st.plotly_chart(fig_dd, use_container_width=True)
