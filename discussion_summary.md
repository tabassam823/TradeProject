# Rangkuman Diskusi Perancangan Bot Trading Kuantitatif Dinamis

**Tanggal Diskusi:** 13 Agustus 2026  
**Dokumen Referensi:** [HedgeFund.md](file:///home/tabassam/Documents/TradeProject/HedgeFund.md), [workflow.md](file:///home/tabassam/Documents/TradeProject/workflow.md), [strategy.md](file:///home/tabassam/Documents/TradeProject/strategy.md), [Trading_Workflow_Guide.md](file:///home/tabassam/Documents/TradeProject/FinceptTerminal/Trading_Workflow_Guide.md)

---

## 1. Visi & Konsep Awal Sistem

Pengguna ingin membangun algoritma trading otomatis dengan karakteristik:
* **Strategi Dinamis:** Tidak bergantung pada 1 strategi saja untuk mengantisipasi perubahan rezim pasar (*regime shift*).
* **Manajemen Risiko & Position Sizing:** Mengikuti panduan *volatility targeting* Man AHL ([HedgeFund.md](file:///home/tabassam/Documents/TradeProject/HedgeFund.md)).
* **Arsitektur Self-Improving:** Mengikuti siklus refleksi dan optimasi parameter tunggal (*single-variable mutation*) ([workflow.md](file:///home/tabassam/Documents/TradeProject/workflow.md)).
* **Deployment Cloud:** Dideploy ke platform Railway agar berjalan *always-on* 24/7.

---

## 2. Evaluasi Opsi Otomasi & Solusi $0 AI Token

### A. Perbandingan Platform Otomasi
* **n8n:** Kurang ideal untuk kalkulasi kuantitatif berat (deret waktu, rolling std dev).
* **OpenClaw (di Railway):** Hebat untuk agen otonom, tetapi memicu kekhawatiran biaya API token AI yang tinggi jika dipanggil tiap jam.
* **AGY CLI + Python Bot (Solusi Terpilih):** 
  * **Python Bot Engine:** Menggunakan `ccxt`, `pandas`, `numpy`, dan `apscheduler`. Berjalan otomatis tiap jam dengan **Biaya Token AI = $0 (Gratis)**.
  * **AGY CLI:** Berfungsi sebagai *Control Plane* dan Arsitek Kode di lokal. Digunakan *on-demand* untuk membuat kode, meninjau log transaksi, dan mengoptimalkan konfigurasi strategi.

### B. Dukungan Mode Binance API
Sistem mendukung 3 mode eksekusi yang dapat diganti via `config.json`:
1. `BACKTEST`: Pengujian historis data Binance via API gratis.
2. `PAPER_TRADING`: Simulasi live 1 jam sekali dengan saldo virtual terpisah.
3. `LIVE_TRADING`: Eksekusi modal asli via API Key Binance (Spot/Futures).

---

## 3. Integrasi OpenBB & Fincept Terminal

Berdasarkan aset yang sudah tersedia di repositori ([Trading_Workflow_Guide.md](file:///home/tabassam/Documents/TradeProject/FinceptTerminal/Trading_Workflow_Guide.md)), pembagian perannya ditetapkan sebagai berikut:

### A. OpenBB Platform (Research & Data Engine)
* **Agregator Data Multi-Asset:** Mengambil data harga, indikator teknikal, dan data makroekonomi secara terpadu.
* **News & Sentiment Circuit Breaker:** Mengambil data berita terbaru (`openbb.news`) dan skor sentimen pasar. Jika terjadi berita krisis/panik massal, sistem otomatis menurunkan *Risk Budget* ke $0 untuk memproteksi modal dari kerugian ekstrem (*black swan event*).

### B. Fincept Terminal (Visual GUI & Monitoring Engine)
* **Visual Dashboard:** Menyediakan antarmuka desktop (GUI) untuk memantau saldo, pergerakan posisi terbuka, dan grafik *equity curve* secara real-time tanpa membaca log teks manual.
* **Alpha Arena Paper Trading:** Lingkungan simulasi visual kedua untuk memantau performa strategi sebelum dilepas ke bursa riil.

---

## 4. Arsitektur Multi-Strategi Modular & Leaderboard

### A. Pengkinian Strategi Secara Manual
Pengguna dapat memperbarui atau menambah strategi melalui 3 cara:
1. **Edit JSON Parameter (`strategy_config.json`):** Mengubah horizon momentum, *risk budget*, atau *stop loss* tanpa koding.
2. **Generasi Kode via AGY CLI:** Meminta AGY CLI membuat file strategi baru berbasis ide tertentu (misal: *"AGY, buatkan strategi Donchian Breakout"*).
3. **Koding Manual:** Membuat file Python baru di `src/strategies/` yang mewarisi `BaseStrategy`.

### B. Multi-Strategy Sandbox & Leaderboard Engine
* **Eksekusi Paralel:** Di mode Paper Trading, semua strategi aktif (`enabled: true`) dijalankan secara bersamaan dengan alokasi modal virtual terpisah.
* **Papan Peringkat (Leaderboard):** Sistem secara otomatis menghasilkan matriks evaluasi perbandingan performa:

| Nama Strategi | Win Rate | CAGR | Max Drawdown | Sharpe Ratio | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Momentum_MultiHorizon** | 31% | +14.2% | -4.8% | **1.45** | 🟢 Superior |
| **VWAP_MeanReversion** | 52% | +5.1% | -8.2% | **0.82** | 🟡 Evaluasi |
| **Sentiment_Filtered_Trend**| 40% | +11.5% | -3.1% | **1.38** | 🟢 Superior |

* **Alokasi Modal Dinamis:** Saat beralih ke `LIVE_TRADING`, modal asli difokuskan pada strategi pemenang (*top performing strategies*).

---

## 5. Ringkasan Kerangka Kerja Terintegrasi

```
┌───────────────────────────────────────────────────────────┐
│              OpenBB Platform (Data & News)                │
│  • OHLCV Prices        • News & Sentiment Analysis        │
└─────────────────────────────┬─────────────────────────────┘
                              │ Data Input
                              ▼
┌───────────────────────────────────────────────────────────┐
│            Python Quant Engine (Bot Trading Utama)         │
│  • Multi-Horizon Momentum (HedgeFund.md)                  │
│  • VWAP Mean-Reversion (strategy.md)                      │
│  • Volatility Targeted Position Sizing                    │
│  • OpenBB News Circuit Breaker                            │
│  • $0 AI Token Cost Execution                             │
└───────────────┬───────────────────────────┬───────────────┘
                │ Order Execution           │ Telemetry
                ▼                           ▼
┌──────────────────────────────┐ ┌──────────────────────────┐
│  Binance API (Live/Paper)    │ │ Fincept Terminal         │
│  • Spot / Futures Execution  │ │ • Visual Dashboard GUI   │
└──────────────────────────────┘ └──────────────────────────┘
                ▲
                │ Parameter Updates
┌───────────────┴───────────────────────────┐
│              AGY CLI (Control & Reflection Plane)         │
│  • Multi-Strategy Leaderboard Analysis                    │
│  • Single-Variable Parameter Optimization (workflow.md)   │
└───────────────────────────────────────────────────────────┘
```

---

## 6. Laporan Hasil Eksekusi & Implementasi Lengkap

Seluruh 6 tahap pengembangan telah **selesai dilaksanakan 100%** dan tervalidasi tanpa error:

### A. File Modul & Struktur yang Dibangun
1. **[requirements.txt](file:///home/tabassam/Documents/TradeProject/requirements.txt):** Dependencies (`ccxt`, `pandas`, `numpy`, `apscheduler`, `python-dotenv`, `tabulate`).
2. **[config.json](file:///home/tabassam/Documents/TradeProject/config.json):** Pengaturan mode (`BACKTEST`, `PAPER_TRADING`, `LIVE_TRADING`), pasangan aset (BTC, ETH, SOL, BNB, AVAX), dan toleransi risiko.
3. **[strategy_config.json](file:///home/tabassam/Documents/TradeProject/strategy_config.json):** Konfigurasi parameter strategi multi-horizon, VWAP, dan sentimen.
4. **[.env.example](file:///home/tabassam/Documents/TradeProject/.env.example):** Template API Keys Binance.
5. **[src/core/binance_client.py](file:///home/tabassam/Documents/TradeProject/src/core/binance_client.py):** Wrapper CCXT Binance API untuk penarikan data OHLCV & order execution.
6. **[src/core/openbb_client.py](file:///home/tabassam/Documents/TradeProject/src/core/openbb_client.py):** OpenBB news sentiment parser & Circuit Breaker.
7. **[src/core/position_sizer.py](file:///home/tabassam/Documents/TradeProject/src/core/position_sizer.py):** Man AHL Volatility Targeted Position Sizer & perlindungan *risk decay* $f \le 2\%$.
8. **[src/strategies/base_strategy.py](file:///home/tabassam/Documents/TradeProject/src/strategies/base_strategy.py):** Abstract base class untuk strategi modular.
9. **[src/strategies/momentum.py](file:///home/tabassam/Documents/TradeProject/src/strategies/momentum.py):** Multi-Horizon Time Series Momentum Strategy ($\tau \in \{5, 10, 21, 42\}$).
10. **[src/strategies/vwap_rejection.py](file:///home/tabassam/Documents/TradeProject/src/strategies/vwap_rejection.py):** VWAP Mean-Reversion Value Area Rejection Strategy.
11. **[src/strategies/sentiment_trend.py](file:///home/tabassam/Documents/TradeProject/src/strategies/sentiment_trend.py):** OpenBB Sentiment-Filtered Trend Strategy.
12. **[src/backtester.py](file:///home/tabassam/Documents/TradeProject/src/backtester.py):** Engine simulasi backtest historis multi-strategi.
13. **[src/paper_trader.py](file:///home/tabassam/Documents/TradeProject/src/paper_trader.py):** Engine paper trading live jam demi jam yang memperbarui `logs/paper_ledger.json`.
14. **[src/leaderboard.py](file:///home/tabassam/Documents/TradeProject/src/leaderboard.py):** Generator papan peringkat performa antar strategi (Sharpe Ratio, Win Rate, Expected Value, Drawdown).
15. **[src/live_trader.py](file:///home/tabassam/Documents/TradeProject/src/live_trader.py):** Engine eksekusi modal riil via API Key Binance.
16. **[main.py](file:///home/tabassam/Documents/TradeProject/main.py):** Unified CLI entry point.

---

## 7. Panduan Penggunaan Sistem CLI

Sistem siap dijalankan melalui satu perintah utama:

```bash
# 1. Menjalankan Backtest Historis
python3 main.py --mode backtest --days 30

# 2. Menjalankan 1 Tick Paper Trading (Simulasi Jam Ini)
python3 main.py --mode paper

# 3. Menampilkan Papan Peringkat (Leaderboard)
python3 main.py --mode leaderboard

# 4. Menjalankan Live Trading Real Money (Setelah API Key diisi)
python3 main.py --mode live
```

