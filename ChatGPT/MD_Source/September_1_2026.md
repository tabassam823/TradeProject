1# Evaluasi Performa Live Trading, Analisis Masalah, Solusi, dan Laporan Implementasi
**Tanggal:** 1 September 2026  
**Lokasi Evaluasi:** Railway Production Environment (`TradeProject` Worker)  
**Tujuan:** Menganalisis performa multi-strategi dalam kondisi pasar `MEAN_REVERSION_CHOP` dan mengevaluasi efektivitas strategi adaptif vs strategi spesifik rezim.

---

## 1. Ringkasan & Hasil Data Log Live Railway (Current State)

Berdasarkan ekstraksi log dari server Railway pada 1 September 2026:

### Tabel Performa Multi-Strategi:

| Strategi | Ekuitas Akhir | Net PnL ($ / %) | Total Trades | Win Rate | Profit Factor | E[X] | Max Drawdown | Sharpe | Alpha (vs Mkt) | BEP / Trail | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`first_passage_value`** | $\$10,916.86$ | $+\\$916.86\ (+9.17\%)$ | 27 | $66.7\%$ | 2.65 | $+\\$33.96$ | $-2.93\%$ | 3.82 | $+9.16\%$ | 🛡️15 🚀5 | 🟢 Superior (Alpha) |
| **`vwap_mean_reversion`** | $\$10,571.92$ | $+\\$571.92\ (+5.72\%)$ | 16 | $75.0\%$ | 3.74 | $+\\$35.75$ | $-1.01\%$ | 3.44 | $+5.71\%$ | 🛡️12 🚀3 | 🟢 Superior (Alpha) |
| **`factor_regime_adaptive`** | $\$7,961.05$ | $-\\$2,038.95\ (-20.39\%)$ | 75 | $36.0\%$ | 0.33 | $-\\$27.19$ | $-21.73\%$ | -7.24 | $-20.40\%$ | 🛡️26 🚀10 | 🔴 Non-performing |
| **`qubo_portfolio_selector`**| $\$7,735.11$ | $-\\$2,264.89\ (-22.65\%)$ | 71 | $29.6\%$ | 0.22 | $-\\$31.90$ | $-23.25\%$ | -8.83 | $-22.66\%$ | 🛡️19 🚀3 | 🔴 Non-performing |
| **`sentiment_filtered_trend`**| $\$7,433.04$ | $-\\$2,566.96\ (-25.67\%)$ | 91 | $38.5\%$ | 0.33 | $-\\$28.21$ | $-25.68\%$ | -11.68 | $-25.53\%$ | 🛡️35 🚀13 | 🔴 Non-performing |
| **`momentum_multi_horizon`** | $\$7,415.71$ | $-\\$2,584.29\ (-25.84\%)$ | 91 | $44.0\%$ | 0.31 | $-\\$28.40$ | $-25.45\%$ | -11.55 | $-25.85\%$ | 🛡️39 🚀12 | 🔴 Non-performing |

**Benchmark Global:** `BTC/USDT` (Return 24h: $\approx +0.13\%$), Terdeteksi Rezim Pasar: **`MEAN_REVERSION_CHOP`**.

---

## 2. Analisis Akar Masalah (Root Cause Analysis)

Terdapat polaritas hasil yang sangat ekstrem antara strategi *Mean Reversion* dan strategi *Trend/Adaptive*:

### A. Dominasi Rezim Chop (Whipsaw Effect)
- **Kondisi:** Pasar berada dalam kondisi `MEAN_REVERSION_CHOP`, di mana harga bergerak dalam range terbatas tanpa tren yang jelas.
- **Analisis:** Strategi trend-following (`momentum_multi_horizon` dan `sentiment_filtered_trend`) mengalami *whipsaw* berat. Mereka masuk posisi saat mengira tren dimulai, namun harga segera berbalik arah, memicu Stop Loss berulang kali.
- **Dampak:** Penurunan ekuitas drastis hingga $-25\%$.

### B. Kegagalan Adaptasi Strategi QUBO & Factor-Regime
- **Kondisi:** `qubo_portfolio_selector` dan `factor_regime_adaptive` seharusnya mampu menyesuaikan diri dengan rezim pasar.
- **Masalah:** Meskipun terdeteksi sebagai "Chop", strategi ini tetap melakukan trade dengan frekuensi tinggi (71-75 trades) namun dengan win rate rendah ($29-36\%$). Ini menunjukkan bahwa mekanisme *Regime Hard-Gate* atau penyesuaian parameter untuk kondisi Chop belum cukup agresif dalam menekan jumlah trade yang berisiko.

### C. Efektivitas Strategi Mean Reversion
- **Analisis:** `first_passage_value` dan `vwap_mean_reversion` menunjukkan performa superior karena secara fundamental dirancang untuk mengambil profit dari *mean reversion* (kembali ke rata-rata).
- **Hasil:** Win rate yang sangat tinggi ($66-75\%$) membuktikan bahwa strategi ini adalah satu-satunya yang selaras dengan mikrostruktur pasar saat ini.

---

## 3. Kesimpulan & Rekomendasi Implementasi

### 1. Penguatan Regime Hard-Gate
Sistem harus lebih tegas dalam menonaktifkan strategi trend-following ketika rezim `MEAN_REVERSION_CHOP` terdeteksi. Saat ini, strategi tersebut masih aktif dan menggerus modal.

### 2. Kalibrasi Ulang QUBO Portfolio Selector
Strategi QUBO perlu dievaluasi mengapa ia tetap memilih aset yang berujung pada kerugian di rezim Chop. Perlu ada penalti lebih besar pada fungsi objektif QUBO ketika volatilitas rendah namun arah tidak jelas.

### 3. Ekspansi Alokasi untuk Mean Reversion
Meningkatkan bobot modal pada `first_passage_value` dan `vwap_mean_reversion` selama rezim Chop terdeteksi, karena keduanya memiliki Alpha yang sangat positif terhadap benchmark.

---

## 4. Status Akhir
- **Sinyal Utama:** $\text{Market} = \text{Chop} \rightarrow \text{Prefer Mean Reversion}$.
- **Tindakan:** Direkomendasikan untuk melakukan *pause* pada strategi Trend dan QUBO hingga rezim berubah menjadi `BULL_TREND` atau `BEAR_TREND`.
