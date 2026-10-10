# ⚡ Solana Futures Scalping (5m) Machine Learning Trading System

Modul sistem trading kuantitatif berbasis Machine Learning (LightGBM) untuk **Scalping Futures Solana (SOLUSDT)** pada timeframe **5-Menit (5m)** dengan validasi **Purged Rolling Walk-Forward Retraining**, **Self-Improvement Optimization**, dan **Live Forward Testing** terhubung langsung ke **Binance Futures Testnet**.

---

## 📁 Struktur Berkas

- **`config.py`**: Konfigurasi instrumen, timeframe (5m), fee model taker + slippage (0.06%), leverage (2x-3x), dan target metrik.
- **`data_loader.py`**: Pemuatan & caching data historis 5-menit SOL & BTC (17,138 candle / 60 hari).
- **`features.py`**: Alpha features frekuensi tinggi (mikro momentum, volume surge, Parkinson volatility, VWAP deviation, Bollinger squeeze, dan BTC lead-lag).
- **`model.py`**: Purged walk-forward retraining 23 rolling folds (14 hari train, 2 hari test, 3 bars purge gap).
- **`risk_engine.py`**: State machine simulasi order, dynamic ATR trailing stop, strict time-stop (maksimal 2 jam), dan sirkuit jeda loss streak.
- **`optimizer.py`**: Self-improvement engine yang mengeksplorasi ribuan konfigurasi parameter.
- **`backtester.py`**: Visualisasi 3-panel grafik performa (Equity, Drawdown, Distribusi PnL trade).
- **`main.py`**: Orkestrator pipeline backtest & self-improvement.
- **`binance_client.py`**: REST client autentikasi HMAC-SHA256 untuk Binance USDT-M Futures Testnet.
- **`forward_test.py`**: Engine forward testing live / daemon multi-mode (`--mode once` atau `--mode loop`).

---

## 🚀 Cara Menjalankan

### 1. Menjalankan Backtest & Self-Improvement
```bash
/home/tabassam/Documents/TradeProject/.venv/bin/python3 crypto_futures_scalping/main.py
```

### 2. Memeriksa Status Live Forward Testing (Single Tick Evaluation)
```bash
/home/tabassam/Documents/TradeProject/.venv/bin/python3 crypto_futures_scalping/forward_test.py --mode once --testnet
```

### 3. Menjalankan / Menghentikan Daemon di Background
```bash
# Menjalankan daemon
./crypto_futures_scalping/run_scalping_daemon.sh

# Memeriksa status & log
./crypto_futures_scalping/check_scalping_status.sh

# Menghentikan daemon
./crypto_futures_scalping/stop_scalping_daemon.sh
```

---

## 📊 Berkas Output & Laporan
Semua artefak tersimpan di folder `crypto_futures_scalping/output/`:
- `sol_scalping_equity_curve.png`: Grafik kurva ekuitas & drawdown vs Buy & Hold SOL.
- `scalping_backtest_report.md`: Laporan komparasi kuantitatif baseline vs improved scalper.
- `scalping_metrics_summary.json`: Ringkasan metrik performa terstruktur.
- `forward_test_state.json`: State posisi terbuka, saldo wallet, dan ekuitas live.
- `forward_test_trades.csv`: Catatan histori eksekusi trade live forward test.
