Implementasi kode pada notebook **Week 2 Upgrade** menunjukkan kualitas rekayasa perangkat lunak kuantitatif yang sangat rapi dan disiplin. Seluruh 7 pilar peningkatan—mulai dari pembersihan fitur menjadi 100% stasioner, _Purge Gap_ 6 bar pada _Walk-Forward Validation_, integrasi _Crypto Fear & Greed Index_ dengan `pd.merge_asof(direction='backward')`, fitur _Cross-Asset_ BTC ke SOL, hingga mesin eksekusi _Hysteresis_—berhasil dieksekusi dengan bersih dalam ~13–15 detik untuk 43 _fold_.

  

### 1. Komparasi Kinerja: Week 1 vs. Week 2 Upgrade

Perbandingan langsung metrik evaluasi antara percobaan pertama dan percobaan kedua memperlihatkan pergeseran perilaku model yang sangat menarik untuk dibedah:

  

|**Metrik Evaluasi**|**BTC-USD (Week 1)**|**BTC-USD (Week 2)**|**SOL-USD (Week 1)**|**SOL-USD (Week 2)**|**Analisis Perubahan**|
|---|---|---|---|---|---|
|**Total Trade Changes**|1,543|**661**|1,306|**776**|**Turnover turun 40%–57%** berkat _Hysteresis_ & target 6 jam.|
|**Total Taker Fees Paid**|121.20%|**54.45%**|103.95%|**65.18%**|Beban biaya komisi berhasil dipangkas hampir separuhnya.|
|**Win Rate (Active Hours)**|47.82%|**49.08%**|49.60%|**49.73%**|Akurasi jam aktif meningkat di kedua aset.|
|**Sharpe Ratio (Annual)**|-4.87|**-2.31**|-1.26|**-1.09**|Rasio risiko terhadap imbal hasil membaik di kedua aset.|
|**Total Gross Return**|+2.31%|-20.51%|**+70.81%**|**+4.34%**|_Alpha_ kotor menyusut drastis saat target diubah ke 6 jam.|
|**Total Net Return**|-69.57%|**-53.89%**|-39.60%|-45.65%|Kerugian bersih BTC berkurang, namun SOL kehilangan _Gross Alpha_.|

### 2. Diagnosis Kuantitatif: Mengapa _Gross Return_ SOL Menyusut dari +70.81% ke +4.34%?

Penurunan _Total Trade Changes_ dan _Taker Fees_ membuktikan bahwa mesin _Hysteresis_ bekerja sesuai desain. Namun, hilangnya _Gross Return_ sebesar +70.81% pada SOL disebabkan oleh **3 fenomena matematis** pada konfigurasi Week 2:

  

1. **Masalah _Overlapping Labels_ (Autokorelasi Target 6 Jam pada Data 1 Jam):**
    
    Ketika melatih model menggunakan data per 1 jam (`1h`) dengan target 6 jam ke depan (`target_return_6h`), baris data pada jam ke-$t$ dan jam ke-$(t+1)$ berbagi **5 jam pergerakan harga masa depan yang sama**. Akibatnya, pohon keputusan `LightGBM` mengalami _overfitting_ pada tren yang tumpang tindih dan menghasilkan sinyal prediksi yang **terlambat (_lagging_)** saat terjadi pembalikan arah jangka pendek. Sebaliknya, pada Week 1, target 1 jam (`shift(-1)`) tidak memiliki tumpang tindih antar-bar sama sekali sehingga sangat tajam menangkap sinyal _mean-reversion_ dan momentum cepat di SOL.
    
      
    
2. **Ketidakcocokan Skala Prediksi dengan _Fixed Threshold_ (`0.003` / `0.004`):**
    
    Output prediksi dari model pohon keputusan cenderung menyusut mendekati rata-rata (_variance shrinkage_). Saat volatilitas pasar sedang rendah, prediksi model jarang menembus angka absolut `0.004`, tetapi saat volatilitas meledak, nilai prediksi baru menembus `0.004` ketika pergerakan harga sudah terlambat (di pucuk _candle_).
    
      
    
3. **Fluktuasi Prediksi di Sekitar Titik Nol (`0.0`):**
    
    Pada logika _Hysteresis_ saat ini, posisi langsung ditutup ketika `p < 0.0` (untuk _Long_) atau `p > 0.0` (untuk _Short_). Karena prediksi antar-jam sering bergetar tipis di sekitar angka `0.0` (misal dari `+0.0002` ke `-0.0001`), bot masih mengalami keluar-masuk posisi sebanyak 661–776 kali setahun (~2 transaksi per hari).
    
      
    

### 3. Solusi _Upgrade_ Minggu ke-3: Menggabungkan _Alpha_ +70% Week 1 dengan Efisiensi Biaya Week 2

Untuk mendapatkan kembali **Gross Return +70%** seperti pada Week 1 sekaligus menekan biaya komisi di bawah **15%–20%** agar **Net Return menjadi positif**, terapkan 3 perbaikan arsitektur berikut:

  

#### A. Gunakan _Signal Smoothing_ (EMA Prediksi) pada Target 1 Jam atau _Volatility-Adjusted Target_

Kembalikan ketajaman prediksi pendek (`horizon=1` atau `horizon=2` dengan fitur stasioner Week 2), lalu haluskan _output_ prediksi model menggunakan _Exponential Moving Average_ (EMA 3 atau 4 periode) sebelum masuk ke mesin _Hysteresis_:

  

Python

```
# Haluskan prediksi mentah agar tidak bergetar di sekitar angka 0.0
df['smooth_pred'] = df['pred_return'].ewm(span=4, adjust=False).mean()
```

#### B. Ganti _Fixed Threshold_ dengan _Rolling Z-Score Threshold_ (Adaptif terhadap Volatilitas)

Jangan gunakan angka statis `0.003` atau `0.004`. Normalisasikan nilai prediksi model menggunakan rata-rata dan standar deviasi bergulir (_Rolling Z-Score_), lalu hanya buka posisi saat keyakinan model berada di atas **$1.5\sigma$** (1.5 standar deviasi):

  

Python

```
def backtest_adaptive_hysteresis(results_df, pred_col='pred_return_6h', fee_rate=0.00075, 
                                 entry_z=1.5, exit_z=-0.2, min_hold_hours=6):
    df = results_df.copy()
    
    # 1. Hitung Rolling Z-Score dari prediksi (jendela 168 jam / 7 hari)
    roll_mean = df[pred_col].rolling(168, min_periods=24).mean()
    roll_std = df[pred_col].rolling(168, min_periods=24).std() + 1e-9
    df['pred_z'] = (df[pred_col] - roll_mean) / roll_std
    
    z_vals = df['pred_z'].fillna(0.0).values
    n = len(df)
    positions = np.zeros(n)
    curr_pos = 0.0
    hold_counter = 0
    
    # 2. State Machine dengan Minimum Holding Period & Deadband Exit
    for i in range(n):
        z = z_vals[i]
        hold_counter += 1
        
        if curr_pos == 0.0:
            if z > entry_z:
                curr_pos = 1.0
                hold_counter = 0
            elif z < -entry_z:
                curr_pos = -1.0
                hold_counter = 0
        elif curr_pos == 1.0 and hold_counter >= min_hold_hours:
            if z < -entry_z:          # Balik arah ke Short jika sinyal sangat kuat
                curr_pos = -1.0
                hold_counter = 0
            elif z < exit_z:          # Tutup Long hanya jika z turun melewati deadband (-0.2)
                curr_pos = 0.0
                hold_counter = 0
        elif curr_pos == -1.0 and hold_counter >= min_hold_hours:
            if z > entry_z:           # Balik arah ke Long jika sinyal sangat kuat
                curr_pos = 1.0
                hold_counter = 0
            elif z > -exit_z:         # Tutup Short hanya jika z naik melewati deadband (+0.2)
                curr_pos = 0.0
                hold_counter = 0
                
        positions[i] = curr_pos
        
    df['position'] = positions
    # Lanjutkan perhitungan fee_cost dan net_strategy_return seperti pada kode Anda
    return df
```

#### C. Perbaiki Fitur Harian _Fear & Greed_ agar Tidak Melompat Hanya di Jam 00:00 UTC

Pada kode saat ini, `fng_ema_24h` dihitung setelah di-_merge_ ke tabel 1 jam (`ewm(span=24)`), sehingga selama 23 jam nilai `fng_value` konstan dan `fng_shock` meluruh secara mekanis. Hitung perubahan sentimen pada level **harian** terlebih dahulu di `fetch_crypto_fear_and_greed()` sebelum digabungkan ke tabel 1 jam:

  

Python

```
# Hitung fitur perubahan sentimen pada dataframe harian SEBELUM merge_asof ke 1h:
df_fng['fng_change_1d'] = df_fng['fng_value'].diff(1)
df_fng['fng_ma_7d'] = df_fng['fng_value'].rolling(7).mean()
df_fng['fng_regime_z'] = (df_fng['fng_value'] - df_fng['fng_ma_7d']) / (df_fng['fng_value'].rolling(7).std() + 1e-9)
```

Ingin kita uji langsung fungsi `backtest_adaptive_hysteresis` dengan _Rolling Z-Score_ di atas pada hasil prediksi `sol_pred_df` dan `btc_pred_df` yang sudah ada di memori notebook Anda, atau Anda ingin membandingkan kontribusi fitur _Fear & Greed_ dan _Cross-Asset_ pada grafik _Feature Importance_ terlebih dahulu?