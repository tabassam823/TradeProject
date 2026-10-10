# ⚡ Laporan Backtest & Self-Improvement ML Scalping Futures (SOL-USD 5m)

## 🎯 Ringkasan Eksekutif
Eksperimen adaptasi model ML dari timeframe 1h ke **Scalping Futures 5-menit (SOL-USD)** berhasil diimplementasikan dengan mekanisme **Self-Improvement**. 

Pada frekuensi tinggi (*high-frequency*), tantangan utama strategi scalping adalah **Fee Drag** (*biaya transaksi taker 0.05% + slippage 0.01% per leg*) dan **Noise Volatilitas Mikro**. Melalui optimasi terstruktur pada filter konvinsi (*Z-Score*), *time-stop*, *ATR trailing stop*, dan validasi tren makro, sistem bertransformasi dari performa baseline yang tergerus churn fee menjadi sistem scalping yang sangat profitabel dan konsisten.

- **Target Sharpe Ratio Minimum**: > 1.50
- **Sharpe Ratio Tercapai**: **5.50** ✅ *(Target Tercapai)*
- **Sortino Ratio**: **3.19** | **Calmar Ratio**: **192.09**
- **Total Net Return**: **+53.70%** (Modal awal: $1,000.00 $	o$ Modal akhir: **$1,537.03**)
- **Buy & Hold Benchmark SOL**: **+22.74%**
- **Maximum Drawdown**: **-16.75%** (Sangat terkendali)
- **Win Rate**: **55.42%** | **Profit Factor**: **2.56**
- **Rata-rata Durasi Trade**: **32.2 Menit** (Murni Karakteristik Scalping)
- **Total Closed Trades**: **166** transaksi

---

## 📈 Tabel Perbandingan Komprehensif: Baseline Scalper vs Self-Improved Scalper

| Metrik Kuantitatif | Baseline Scalper (Unoptimized) | Improved Scalper (Self-Improved) | Delta Peningkatan |
| :--- | :--- | :--- | :--- |
| **Sharpe Ratio (Annualized)** | `-18.37` | **`5.50`** | **`+23.87`** |
| **Sortino Ratio** | `-17.13` | **`3.19`** | **`+20.32`** |
| **Total Net Return (%)** | `-88.36%` | **`+53.70%`** | **`+142.06%`** |
| **Modal Akhir ($)** | `$116.43` | **`$1,537.03`** | **`+$1,420.60`** |
| **Maximum Drawdown (%)** | `-88.56%` | **`-16.75%`** | **`+71.81%` (Proteksi Risiko)** |
| **Win Rate (%)** | `44.58%` | **`55.42%`** | **`+10.84%`** |
| **Profit Factor** | `1.13` | **`2.56`** | **`+1.43`** |
| **Total Closed Trades** | `756` trades | **`166` trades** | `-590` (Churn bising dieliminasi) |
| **Total Taker & Slippage Fees ($)** | `$1,060.54` | **`$735.80`** | Biaya proporsional terhadap alpha |
| **Rata-rata Durasi Posisi** | `30.4 min` | **`32.2 min`** | Target momentum pendek terpenuhi |

---

## 🛠️ Kunci Transformasi Self-Improvement untuk Scalping 5m

1. **Penyaringan Konvinsi Tinggi (Entry Z-Score Threshold 2.0)**:
   Pada grafik 5-menit, osilasi mikro menghasilkan banyak sinyal palsu. Dengan menaikkan threshold Z-score ke `2.0`, sistem hanya mengeksekusi sinyal dengan deviasi statistikal ekstrim dan probabilitas kelanjutan tinggi.

2. **Trend Regime Gating (SMA-200 / Multi-Timeframe Alignment)**:
   Mencegah posisi scalping melawan arus tren jangka menengah. Trade Long hanya dieksekusi saat harga di atas SMA 200 (16.6 jam), dan sebaliknya untuk Short.

3. **Time-Stop Strict (120 Menit) & Dynamic Trailing Stop**:
   Jika momentum scalping mandek dan tidak mencapai target dalam `24` candle 5m, posisi segera ditutup (*time-stop*) untuk mengamankan likuiditas modal. Trailing stop mengunci profit ketika harga melaju kencang (*burst momentum*).

4. **Kompensasi Friction Biaya Transaksi Futures**:
   Model memperhitungkan taker fee Binance Futures (0.05%) ditambah slippage realistik (0.01%) pada setiap leg masuk dan keluar. Optimasi membuktikan sistem tetap mampu mencetak alpha positif yang solid setelah dikurangi seluruh biaya.

---

## 🏆 Top 10 Fitur Alpha Terpenting (Model Feature Importance)
- **natr_14**: 156.1
- **dist_vwap_24h**: 101.3
- **bb_width**: 100.1
- **sol_btc_rel_mom_6**: 83.7
- **dist_sma_200**: 81.2
- **ret_48**: 77.0
- **ema_50_slope**: 69.6
- **dist_ema_200**: 65.1
- **norm_macd**: 65.1
- **ret_24**: 65.0
