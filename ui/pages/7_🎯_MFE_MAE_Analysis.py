"""
7_🎯_MFE_MAE_Analysis.py
Maximum Favorable Excursion (MFE) & Maximum Adverse Excursion (MAE) Dashboard.
Adapted from Quant-Analysis-Toolkit.
Analyzes trade execution quality, stop-loss tightness, and exit efficiency.
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from src.core.mfe_mae_analyzer import compute_trade_mfe_mae, analyze_execution_quality
from src.core.binance_client import BinanceClient

st.set_page_config(
    page_title="MFE / MAE Execution Analysis",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 MFE & MAE Trade Execution Analysis")
st.markdown("""
Modul analisis kualitas eksekusi trading yang diadaptasi dari **Quant-Analysis-Toolkit**:
- **MFE (Maximum Favourable Excursion):** Keuntungan mengambang (*unrealized peak*) tertinggi yang dicapai sebelum keluar.
- **MAE (Maximum Adverse Excursion):** *Drawdown* terdalam yang dialami posisi selama terbuka.
- **Exit Efficiency:** Rasio laba riil terhadap puncak MFE (mengukur berapa banyak potensi laba yang berhasil dikunci vs ditinggalkan di meja pasar).
""")

st.divider()

# Data Source Selection
st.sidebar.header("📁 Sumber Data Trading")
data_source = st.sidebar.radio(
    "Pilih Sumber Transaksi",
    ["Simulasi / Sample Data Kuantitatif", "Ledger Paper Trading (logs/paper_ledger.json)", "Upload CSV"]
)

trades_data = []

if data_source == "Simulasi / Sample Data Kuantitatif":
    st.sidebar.caption("Menghasilkan 30 sampel trade sintetis pada data pasar BTCUSDT terkini untuk demonstrasi analitis.")
    symbol = st.sidebar.selectbox("Aset Evaluasi", ["BTCUSDT", "ETHUSDT"], index=0)
    
    # Fetch real market data
    client = BinanceClient()
    ohlcv = client.fetch_ohlcv(symbol, timeframe="1h", limit=300)
    if ohlcv is None or ohlcv.empty:
        dates = pd.date_range("2026-01-01", periods=300, freq="1h")
        price = np.cumsum(np.random.randn(300) * 50) + 60000.0
        ohlcv = pd.DataFrame({
            "timestamp": dates, "open": price, "high": price + 25, "low": price - 25,
            "close": price, "volume": 100
        })
        
    # Generate realistic sample trades
    np.random.seed(42)
    step = len(ohlcv) // 30
    for i in range(25):
        entry_idx = i * step + 5
        exit_idx = min(entry_idx + np.random.randint(4, 18), len(ohlcv) - 1)
        side = "LONG" if np.random.rand() > 0.45 else "SHORT"
        entry_p = float(ohlcv["open"].iloc[entry_idx])
        exit_p = float(ohlcv["close"].iloc[exit_idx])
        
        trades_data.append({
            "id": f"TR-{i+1:03d}",
            "symbol": symbol,
            "side": side,
            "entry_time": ohlcv["timestamp"].iloc[entry_idx],
            "exit_time": ohlcv["timestamp"].iloc[exit_idx],
            "entry_price": entry_p,
            "exit_price": exit_p
        })

elif data_source == "Ledger Paper Trading (logs/paper_ledger.json)":
    ledger_path = "logs/paper_ledger.json"
    if os.path.exists(ledger_path):
        try:
            with open(ledger_path, "r") as f:
                raw_ledger = json.load(f)
            # Extract closed trades
            for strat_name, strat_data in raw_ledger.get("strategies", {}).items():
                for t in strat_data.get("closed_trades", []):
                    trades_data.append({
                        "id": t.get("trade_id", "N/A"),
                        "symbol": t.get("symbol", "BTC/USDT"),
                        "side": t.get("side", "LONG"),
                        "entry_time": t.get("entry_time"),
                        "exit_time": t.get("exit_time"),
                        "entry_price": t.get("entry_price"),
                        "exit_price": t.get("exit_price")
                    })
        except Exception as e:
            st.error(f"Gagal membaca ledger: {e}")
    else:
        st.warning("File `logs/paper_ledger.json` belum ditemukan.")
        
    # Need market data for reconstruction
    client = BinanceClient()
    ohlcv = client.fetch_ohlcv("BTCUSDT", timeframe="1h", limit=500)

else:
    uploaded = st.sidebar.file_uploader("Upload CSV Transaksi (format: entry_time, exit_time, entry_price, exit_price, side)", type=["csv"])
    if uploaded:
        trades_df = pd.read_csv(uploaded)
        trades_data = trades_df.to_dict(orient="records")
    client = BinanceClient()
    ohlcv = client.fetch_ohlcv("BTCUSDT", timeframe="1h", limit=500)

if not trades_data:
    st.info("Pilih sumber data simulasi atau sediakan riwayat transaksi untuk memulai analisis MFE/MAE.")
    st.stop()

# Run Computation
with st.spinner("Menghitung ekskursi harga intrabar MFE dan MAE..."):
    results_df = compute_trade_mfe_mae(trades_data, ohlcv)
    metrics = analyze_execution_quality(results_df)

# Key Performance Indicators
st.subheader("📊 Ringkasan Kualitas Eksekusi & Efisiensi Keluar (Exit Quality)")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Transaksi", metrics["total_trades"])
m2.metric("Win Rate", f"{metrics['win_rate_pct']}%")
m3.metric("Rata-rata MFE (Peak)", f"+{metrics['avg_mfe_pct']}%")
m4.metric("Rata-rata MAE (Drawdown)", f"-{metrics['avg_mae_pct']}%")
m5.metric("Exit Efficiency", f"{metrics['avg_efficiency']:.2f}")

# Diagnostic Alerts
if metrics.get("recommendations"):
    st.markdown("### 💡 Diagnosa & Rekomendasi Eksekusi Kuantitatif")
    for rec in metrics["recommendations"]:
        st.info(rec)

# Visualizations
col_v1, col_v2 = st.columns(2)

with col_v1:
    # MFE vs Realized PnL Scatter Plot
    fig_mfe = go.Figure()
    
    # 45 degree perfect exit line
    max_mfe = max(results_df["mfe_pct"].max(), 5.0)
    fig_mfe.add_trace(go.Scatter(
        x=[0, max_mfe], y=[0, max_mfe],
        mode="lines",
        name="100% Exit Efficiency (Perfect Exit)",
        line=dict(color="#888888", dash="dash")
    ))
    
    fig_mfe.add_trace(go.Scatter(
        x=results_df["mfe_pct"],
        y=results_df["realized_ret_pct"],
        mode="markers",
        text=results_df["trade_id"],
        marker=dict(
            size=10,
            color=np.where(results_df["realized_ret_pct"] > 0, "#00FFAA", "#FF5555"),
            line=dict(width=1, color="white")
        ),
        name="Trades"
    ))
    
    fig_mfe.update_layout(
        template="plotly_dark",
        title="MFE vs Realized Return (Berapa Banyak Laba yang Ditinggalkan di Meja?)",
        xaxis_title="Maximum Favorable Excursion (MFE %)",
        yaxis_title="Realized Return (%)",
        height=400
    )
    st.plotly_chart(fig_mfe, use_container_width=True)

with col_v2:
    # MAE vs Realized PnL Scatter Plot
    fig_mae = go.Figure()
    
    fig_mae.add_trace(go.Scatter(
        x=results_df["mae_pct"],
        y=results_df["realized_ret_pct"],
        mode="markers",
        text=results_df["trade_id"],
        marker=dict(
            size=10,
            color=np.where(results_df["realized_ret_pct"] > 0, "#00FFAA", "#FF5555"),
            line=dict(width=1, color="white")
        ),
        name="Trades"
    ))
    
    # Optimal stop loss boundary indication
    win_mae_90 = results_df[results_df["realized_ret_pct"] > 0]["mae_pct"].quantile(0.90) if not results_df[results_df["realized_ret_pct"] > 0].empty else 2.0
    fig_mae.add_vline(x=win_mae_90, line_width=2, line_dash="dash", line_color="#FFAA00", annotation_text=f"Saran Batas SL (~{win_mae_90:.1f}%)")
    
    fig_mae.update_layout(
        template="plotly_dark",
        title="MAE vs Realized Return (Berapa Dalam Drawdown Sebelum Laba?)",
        xaxis_title="Maximum Adverse Excursion (MAE %)",
        yaxis_title="Realized Return (%)",
        height=400
    )
    st.plotly_chart(fig_mae, use_container_width=True)

# Efficiency Distribution
st.subheader("📈 Distribusi Efisiensi Exit (Exit Efficiency Distribution)")
fig_eff = px.histogram(
    results_df,
    x="exit_efficiency",
    nbins=25,
    template="plotly_dark",
    color_discrete_sequence=["#00FFAA"],
    title="Frekuensi Efisiensi Keluar (1.0 = Mengunci Tepat di Pucuk MFE, <0 = Berbalik Rugi)"
)
fig_eff.update_layout(height=350)
st.plotly_chart(fig_eff, use_container_width=True)

# Data Table
st.subheader("📋 Rincian Transaksi & Metrik Ekskursi")
st.dataframe(
    results_df[[
        "trade_id", "symbol", "side", "entry_time", "entry_price", "exit_price",
        "mfe_pct", "mae_pct", "realized_ret_pct", "exit_efficiency", "left_on_table_pct"
    ]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "mfe_pct": st.column_config.NumberColumn("MFE (%)", format="+%.2f%%"),
        "mae_pct": st.column_config.NumberColumn("MAE (%)", format="-%.2f%%"),
        "realized_ret_pct": st.column_config.NumberColumn("Realized PnL", format="%+.2f%%"),
        "exit_efficiency": st.column_config.NumberColumn("Efficiency", format="%.2f"),
        "left_on_table_pct": st.column_config.NumberColumn("Left on Table", format="%.2f%%"),
    }
)
