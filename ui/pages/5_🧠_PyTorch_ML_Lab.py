"""
5_🧠_PyTorch_ML_Lab.py
Interactive Machine Learning Lab for Financial Deep Learning using PyTorch.
Allows users to:
1. Learn PyTorch fundamentals (Tensors, Architectures, Custom Losses, Backprop)
2. Choose between SigNetMLP (Signature Deep Learning) and TimeSeriesLSTM (Recurrent)
3. Train neural networks to optimize Mean-Variance Utility or Sharpe Ratio directly
4. Monitor live training and validation loss curves in real-time
5. Evaluate predicted portfolio allocation distributions and export checkpoints
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import time
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import torch

from src.core.binance_client import BinanceClient
from src.core.sig_torch_models import SigNetMLP, TimeSeriesLSTM, MeanVarianceUtilityLoss, DirectSharpeLoss, create_model
from src.core.sig_torch_trainer import prepare_training_data, train_model, save_checkpoint

st.set_page_config(
    page_title="PyTorch ML Lab",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 PyTorch Machine Learning Lab — Financial Deep Learning")
st.markdown("""
Laboratorium interaktif untuk mempelajari dan melatih model **Deep Learning dengan PyTorch** pada data finansial kuantitatif.
Alih-alih memprediksi harga secara terpisah, model dilatih secara **End-to-End** untuk memaksimalkan fungsi utilitas portofolio atau Sharpe Ratio secara langsung menggunakan *backpropagation*.
""")

st.divider()

# Concept Cards
with st.expander("💡 Konsep Dasar PyTorch yang Dipelajari di Modul Ini", expanded=False):
    st.markdown("""
    1. **`torch.Tensor` & Batches:** Mengorganisir lintasan pasar menjadi tensor multidimensi `(batch_size, sequence_length, features)`.
    2. **Neural Architectures (`nn.Module`):**
       - **SigNetMLP:** Menerima representasi lintasan bebas-derau (*Signature Space*) dan memetakan ke keputusan alokasi melalui layer *Linear, BatchNorm, GELU, Dropout*.
       - **TimeSeriesLSTM:** Mempelajari memori jangka panjang (*hidden states* & *cell states*) langsung dari deret waktu mentah.
    3. **Custom Differentiable Loss:**
       $$\\mathcal{L}_{\\text{Utility}} = -\\left( \\mathbb{E}[R_p] - \\frac{\\lambda}{2}\\text{Var}(R_p) \\right) \\quad \\text{atau} \\quad \\mathcal{L}_{\\text{Sharpe}} = -\\frac{\\text{Mean}(R_p)}{\\text{Std}(R_p) + \\epsilon}$$
       *Loss function* diturunkan secara analitis agar optimizer (Adam) secara otomatis memperbarui bobot neural network menuju posisi portofolio yang paling menguntungkan dengan risiko terukur.
    4. **Train/Validation Split (Anti-Lookahead):** Membagi data secara kronologis (bukan acak) untuk memvalidasi performa di masa depan yang sesungguhnya.
    """)

# Sidebar Controls
st.sidebar.header("⚙️ Konfigurasi Data & Model")
symbol = st.sidebar.selectbox("Aset Tradable", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"], index=0)
timeframe = st.sidebar.selectbox("Timeframe", ["15m", "1h", "4h"], index=1)
limit_candles = st.sidebar.slider("Jumlah Data Historis", min_value=200, max_value=1200, value=500, step=50)

st.sidebar.subheader("Arsitektur Jaringan")
model_type = st.sidebar.radio(
    "Pilih Arsitektur Model",
    ["SigNetMLP (Signature + Deep MLP)", "TimeSeriesLSTM (Recurrent LSTM)"],
    index=0
)
is_signet = "SigNet" in model_type

st.sidebar.subheader("Hyperparameter Pelatihan")
epochs = st.sidebar.slider("Jumlah Epochs", min_value=10, max_value=150, value=40, step=5)
batch_size = st.sidebar.select_slider("Batch Size", options=[16, 32, 64], value=32)
learning_rate = st.sidebar.select_slider("Learning Rate (η)", options=[1e-4, 5e-4, 1e-3, 5e-3, 1e-2], value=1e-3)

loss_choice = st.sidebar.selectbox(
    "Fungsi Rugi (Objective Loss)",
    ["Mean-Variance Utility Loss", "Direct Sharpe Ratio Loss"]
)
risk_lambda = 1.0
if "Mean-Variance" in loss_choice:
    risk_lambda = st.sidebar.slider("Koefisien Penghindaran Risiko (λ)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)

# Fetch Market Data
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

with st.spinner("Memuat data pasar..."):
    df = load_data(symbol, timeframe, limit_candles)

st.subheader(f"📊 Eksplorasi Data: {symbol} ({len(df)} candle)")
st.line_chart(df.set_index("timestamp")["close"])

# Prepare PyTorch Tensors
feature_cols = ["close", "volume"]
lookback_window = 24
sig_order = 2 if is_signet else None

with st.spinner("Menyiapkan dataset tensor PyTorch..."):
    X_train, y_train, X_val, y_val, metadata = prepare_training_data(
        df,
        feature_cols=feature_cols,
        target_price_col="close",
        lookback_window=lookback_window,
        forward_horizon=1,
        stride=2,
        use_signature=is_signet,
        signature_order=2,
        val_split=0.2
    )

c1, c2, c3 = st.columns(3)
c1.metric("Dimensi Input Tensor", f"{X_train.shape[1:]}")
c2.metric("Ukuran Train Set", f"{len(X_train)} sampel")
c3.metric("Ukuran Validation Set", f"{len(X_val)} sampel")

# Training Execution
if st.button("🚀 Mulai Pelatihan Model PyTorch", type="primary"):
    # Build Model
    if is_signet:
        model = SigNetMLP(input_dim=X_train.shape[-1], hidden_dims=[64, 32], dropout=0.2)
    else:
        model = TimeSeriesLSTM(input_size=X_train.shape[-1], hidden_size=32, num_layers=2, dropout=0.2)
        
    # Build Loss
    if "Mean-Variance" in loss_choice:
        loss_fn = MeanVarianceUtilityLoss(risk_aversion_lambda=risk_lambda)
    else:
        loss_fn = DirectSharpeLoss()
        
    st.info(f"Model `{model.__class__.__name__}` diinisialisasi. Memulai loop pelatihan...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    chart_placeholder = st.empty()
    
    # Real-time training loop
    history_train = []
    history_val = []
    
    def on_epoch_end(epoch, total_epochs, t_loss, v_loss):
        pct = epoch / total_epochs
        progress_bar.progress(pct)
        status_text.markdown(f"**Epoch {epoch}/{total_epochs}** — Train Loss: `{t_loss:.6f}` | Val Loss: `{v_loss:.6f}`")
        history_train.append(t_loss)
        history_val.append(v_loss)
        
        # Update live chart every 5 epochs or last epoch
        if epoch % 5 == 0 or epoch == total_epochs:
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=history_train, mode="lines", name="Train Loss", line=dict(color="#00FFAA")))
            fig.add_trace(go.Scatter(y=history_val, mode="lines", name="Validation Loss", line=dict(color="#FF5555")))
            fig.update_layout(
                template="plotly_dark",
                title="Kurva Pembelajaran (Loss Convergence Curve)",
                xaxis_title="Epoch",
                yaxis_title="Loss (Negative Utility)",
                height=350,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            chart_placeholder.plotly_chart(fig, use_container_width=True)
            
    history = train_model(
        model, X_train, y_train, X_val, y_val,
        loss_fn=loss_fn,
        epochs=epochs,
        batch_size=batch_size,
        lr=learning_rate,
        progress_callback=on_epoch_end
    )
    
    # Save checkpoint
    checkpoint_dir = "models/torch_checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    chk_path = os.path.join(checkpoint_dir, "best_signet.pt")
    metadata["architecture"] = model.__class__.__name__
    save_checkpoint(model, metadata, chk_path)
    
    st.success(f"🎉 Pelatihan Selesai! Model terbaik (Val Loss `{history['best_val_loss']:.6f}`) disimpan ke `{chk_path}`.")
    st.session_state["torch_model"] = model
    st.session_state["torch_meta"] = metadata
    st.session_state["val_data"] = (X_val, y_val)

# Evaluation Section
if "torch_model" in st.session_state:
    model = st.session_state["torch_model"]
    X_val, y_val = st.session_state["val_data"]
    
    st.subheader("🎯 Evaluasi Out-of-Sample (Validation Set)")
    
    with torch.no_grad():
        preds = model(X_val).numpy().flatten()
        actual_returns = y_val.numpy().flatten()
        
    col_e1, col_e2 = st.columns(2)
    
    with col_e1:
        # Distribution of positions
        fig_dist = go.Figure(go.Histogram(
            x=preds,
            nbinsx=20,
            marker_color="#00FFAA",
            opacity=0.75
        ))
        fig_dist.update_layout(
            template="plotly_dark",
            title="Distribusi Posisi Trading Diprediksi ξ_t ∈ [-1, +1]",
            xaxis_title="Posisi Alokasi (Minus = Short, Plus = Long)",
            yaxis_title="Frekuensi",
            height=350
        )
        st.plotly_chart(fig_dist, use_container_width=True)
        
    with col_e2:
        # Strategy simulated cumulative return vs buy & hold
        strategy_returns = preds * actual_returns
        cum_strategy = np.cumprod(1.0 + strategy_returns)
        cum_asset = np.cumprod(1.0 + actual_returns)
        
        fig_cum = go.Figure()
        fig_cum.add_trace(go.Scatter(y=cum_strategy, mode="lines", name="PyTorch Deep Model", line=dict(color="#00FFAA", width=2.5)))
        fig_cum.add_trace(go.Scatter(y=cum_asset, mode="lines", name="Buy & Hold Asset", line=dict(color="#888888", dash="dash")))
        fig_cum.update_layout(
            template="plotly_dark",
            title="Kinerja Out-of-Sample: Deep Model vs Buy & Hold",
            xaxis_title="Langkah Waktu (Validation)",
            yaxis_title="Nilai Portofolio Kumulatif",
            height=350
        )
        st.plotly_chart(fig_cum, use_container_width=True)
