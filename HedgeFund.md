# Analisis Strategi Momentum Hedge Fund

**Sumber Gemini:** [Link](https://gemini.google.com/app/05841e70cf7270b0)
**User prompt:** [Video Youtube](https://youtu.be/54PMBYXA3e0?si=u6nPrPWg-tVjXylA)

**Response:** 
Halo! Sebagai sesama pembelajar di bidang sains kuantitatif, analisis strategi trading algoritmik dari hedge fund seperti Man AHL sangat relevan dengan pemodelan sistem dinamik dan analisis deret waktu (time series analysis) yang biasa kita temui dalam fisika.

Berikut adalah dekonstruksi dan penjelasan struktur komprehensif dari video berjudul "I Found a $60 Billion Hedge Fund's Research Paper. I Tested Their Strategy." dari kanal Unbiased Trading.

## Ringkasan Struktur Utama Video
1. Pendahuluan & Konseptualisasi Man AHL [00:00:00]
2. Aturan Sinyal Momentum & Persamaan Risiko [00:01:58]
3. Arsitektur Pipeline Backtesting dalam Python [00:03:44]
4. Hasil Empiris & Analisis Statistik Kinerja [00:06:37]
5. Kesimpulan & Implikasi Kuantitatif [00:09:29]

## Penjelasan Detail Setiap Bagian

### 1. Pendahuluan & Konseptualisasi Man AHL [00:00:00]
* **Konteks:** Man AHL adalah salah satu quantitative hedge fund tertua di dunia yang mengelola dana sekitar $60–70 miliar. Seluruh perdagangan dilakukan secara kuantitatif/sistematis tanpa campur tangan intuisi manusia.
* **Landasan Akademis:** Strategi yang dibahas didasarkan pada konsep *Time Series Momentum* (mengikuti tren). Dalam literatur keuangan kuantitatif (seperti makalah "Two Centuries of Trend Following" dan makalah akademis Oxford tahun 2012), strategi ini telah diuji pada data historis lebih dari 140 tahun (sejak tahun 1880) dan terbukti menghasilkan positive return di setiap dekade.

### 2. Aturan Sinyal Momentum & Persamaan Risiko [00:01:58]

#### A. Konstruksi Sinyal Momentum (Multi-Horizon Signal)
Sinyal perdagangan dibangun menggunakan pendekatan multi-horizon (memeriksa tren pada beberapa skala waktu sekaligus, analog dengan mengamati respons sistem pada frekuensi atau horizon waktu berbeda):

* Sistem menghitung arah pergerakan harga pada 4 horizon waktu (misalnya 5, 10, 21, dan 42 hari kerja).
* Untuk setiap horizon $i$, tentukan sinyal diskrit:
  $$S_i = \text{sign}(P_t - P_{t-\tau_i}) \in \{+1, -1\}$$
* Skor total $S$ adalah akumulasi dari keempat sinyal:
  $$S = \sum_{i=1}^{4} S_i \in [-4, +4]$$
  * $S = +4$: Posisi Long penuh (keyakinan naik maksimal).
  * $S = -4$: Posisi Short penuh (keyakinan turun maksimal).
  * $S = +2$: Posisi Long setengah (penyesuaian ukuran posisi sesuai derajat keyakinan).

#### B. Persamaan Matematika Manajemen Risiko [00:02:59]
Pengaturan ukuran posisi tidak ditentukan oleh intuisi, melainkan oleh persamaan volatility targeting:

$$\text{Position Size} = \frac{\text{Score} \times \text{Risk Budget}}{\text{Volatility}}$$

* **Penjelasan Parameter & Variabel:**
  * **Position Size (Ukuran Posisi):** Alokasi modal/jumlah unit aset yang ditransaksikan.
  * **Score ($S$):** Skor akumulasi momentum (berkisar dari -4 hingga +4).
  * **Risk Budget (Anggaran Risiko):** Parameter konstan yang menentukan besarnya nilai risiko nominal yang sanggup ditanggung per aset/portofolio.
  * **Volatility ($\sigma$):** Estimasikan deviasi standar dari imbal hasil harga aset pada periode tertentu (mengukur fluktuasi/stokastisitas pasar saat itu).

* **Hubungan & Kesebandingan:**
  * $\text{Position Size} \propto \text{Score}$: Ukuran posisi berbanding lurus dengan skor momentum. Semakin kuat konsensus tren di berbagai horizon, semakin besar alokasi posisinya.
  * $\text{Position Size} \propto \frac{1}{\text{Volatility}}$: Ukuran posisi berbanding terbalik dengan volatilitas pasar.
    * *Interpretasi Fisika/Sistem:* Ini berfungsi sebagai umpan balik negatif (negative feedback loop). Ketika instrumen mengalami fluktuasi ekstrem (volatilitas tinggi), sistem secara otomatis mengecilkan ukuran posisi untuk menjaga kestabilan energi/risiko portofolio. Sebaliknya, saat kondisi tenang (volatilitas rendah), ukuran posisi diperbesar.

### 3. Arsitektur Pipeline Backtesting dalam Python [00:03:44]

**Deskripsi Diagram Alur Sistem [00:05:21]**
Presenter menunjukkan diagram alur (pipeline architecture) untuk mensimulasikan strategi secara ketat tanpa look-ahead bias (mencegah informasi masa depan bocor ke masa lalu):

1. **Universe Selection (Pemilihan Semesta Aset):**
   * Mengambil seluruh pasangan spot USD di bursa kripto.
   * Melakukan perangkingan berbasis trailing 21-day dollar volume.
   * Memilih top 50 (atau top 10) aset terlikuid secara dinamis setiap bulan (rolling window).
2. **Signal Generation (Pembangkitan Sinyal):**
   * Menghitung skor momentum berbasis 4 horizon waktu per aset harian.
3. **Position Sizing (Pengukuran Posisi):**
   * Menerapkan rumus alokasi risiko yang membagi skor dengan volatilitas harian.
4. **Execution & Drift Control (Eksekusi Transaksi):**
   * Perhitungan sinyal dilakukan pada harga penutupan (close) hari $t$ (misal pukul 16:00 New York).
   * Eksekusi transaksi dilakukan pada harga pembukaan (open) hari $t + 1$.
   * Memperhitungkan biaya komisi nyata dan slippage.
   * Perubahan posisi kecil akibat variasi skor yang minor diabaikan (hold small size drift) guna menekan biaya beban transaksi.

### 4. Hasil Empiris & Analisis Statistik Kinerja [00:06:37]

#### A. Parameter & Hasil Kinerja Kuantitatif [00:06:37]
Diuji pada data kripto harian selama 8,5 tahun (~28.000 order, ~9.000 transaksi):

| Metrik Kuantitatif | Nilai Hasil Backtest | Makna & Relevansi Fisika/Kuantitatif |
| :--- | :--- | :--- |
| **CAGR** | 7,33% | Laju pertumbuhan tahunan majemuk (compound annual rate). |
| **Total Return** | 83% | Imbal hasil kumulatif selama periode pengujian. |
| **Sharpe Ratio** | ~0,99 | Rasio risk-adjusted return (Imbal hasil per unit risiko total). |
| **Sortino Ratio** | 2,34 | Rasio imbal hasil terhadap downside risk saja (hanya menghitung deviasi negatif). |
| **Max Drawdown** | -10% | Penurunan maksimum dari puncak ke lembah (peak-to-trough). |
| **Volatilitas Strategi**| 7,6% | Fluktuasi kurva ekuitas yang sangat terdistribusi dan terkontrol. |

* **Deskripsi Visual Kurva Ekuitas (Equity Curve) [00:06:37]:** Kurva menunjukkan pola khas trend following: grafik naik secara tajam saat terjadi tren besar, diselingi periode penurunan perlahan (drawdown landai) saat pasar konsolidasi/sideways.
* **Tabel Kinerja Tahunan [00:07:35]:** Pada tahun krisis pasar kripto (seperti tahun 2020 di mana Bitcoin jatuh ~50%), strategi ini hanya mengalami kerugian maksimal -3% karena mekanisme penyesuaian volatilitasnya.

#### B. Statistik Distribusi & Karakteristik Strategi [00:08:19]
* **Win Rate (Tingkat Kemenangan):** Hanya 29% (artinya sistem rugi pada 71% transaksi).
* **Monthly Skewness (Kemiringan Distribusi):** +1,05 (Positive Skewness).
  * *Sifat Dasar Tren Following:* Strategi ini sengaja menerima banyak kekalahan kecil (small losses) secara beruntun, namun ketika menang, imbal hasilnya sangat besar (large gain) sehingga menutupi seluruh kerugian akumulatif.

#### C. Diagnostik Daya Prediksi Skor (Statistical Significance Test) [00:08:50]
Presenter menguji apakah skor momentum benar-benar memiliki daya prediksi stokastik (predictive power) terhadap imbal hasil hari berikutnya:
* **T-Statistic:** Ditemukan sebesar 2,9.
* **Beta-Adjusted T-Stat:** Setelah mengeliminasi komponen kenaikan umum pasar (market beta / Bitcoin trend), nilai T-stat tetap berada di angka 2,1.
* **Interpretasi Statistik:** Karena nilai $t > 2.0$, secara statistik hipotesis nol ($H_0$: sinyal hanya noise acak) dapat ditolak pada tingkat signifikansi $p < 0.05$. Ini membuktikan sinyal memiliki alpha sejati.

### 5. Kesimpulan & Implikasi Kuantitatif [00:09:29]
* **Mengapa Hedge Fund $60 Miliar Membagikan Strategi Ini?**
  * **Keunggulan Utama (Edge)** bukan terletak pada kerahasiaan rumusnya, melainkan pada eksekusi dan disiplin manajemen risiko. Menghadapi win rate 29% (mengalami kerugian pada 7 dari 10 transaksi) sangat sulit diterima secara psikologis oleh manusia tanpa sistem otomatis.
* **Risk Premium (Premi Risiko):** Strategi ini mengambil keuntungan dari struktur ketidakefisienan perilaku pasar (behavioral bias): manusia cenderung terlambat merespons berita (underreaction awal), lalu ikut-ikutan panik/membeli secara berlebihan (overreaction) ketika tren sudah jelas.

### Diskusi Lanjutan
Sebagai mahasiswa fisika, Anda mungkin tertarik meninjau strategi ini dari perspektif sistem stokastik, analisis Fourier/Wavelet untuk penentuan horizon waktu optimal, atau dinamika fase transisi pada pasar. 

Bagian atau parameter mana dari video ini yang ingin Anda bedah lebih dalam secara matematis atau kodenya?