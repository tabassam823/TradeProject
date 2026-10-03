=== MODEL ===
Evolusi sistem dari _Week 3_ ke _Week 4_ ini membutuhkan transisi dari sekadar prediksi _machine learning_ statis menuju arsitektur manajemen risiko dinamis dan pemodelan jalur-kritis (_path-dependent_). Berikut adalah rincian implementasi untuk keempat _upgrade_ yang kamu butuhkan ke dalam eksekusi _engine_ algoritma yang ada.

  

**1. Dynamic Position Sizing & TP/SL Berbasis Budget**

Untuk menjaga _survival rate_ modal, ukuran posisi tidak lagi _fixed_, melainkan dihitung mundur dari toleransi risiko absolut terhadap jarak Stop Loss (SL). Di dalam _state machine_ `backtest_adaptive_hysteresis`, kamu perlu melacak modal (`capital`) secara iteratif.

  

- **Risk Logic:**
    
    $Risk = \begin{cases} 1 & \text{if Capital} < 100 \\ 0.01 \times \text{Capital} & \text{if Capital} \ge 100 \end{cases}$
    
      
    
- **Sizing & TP/SL Logic:** Tentukan ATR (Average True Range) sebagai basis volatilitas untuk TP dan SL.
    
      
    - _Stop Loss Distance_ = $1.5 \times \text{ATR}_{14}$
        
          
        
    - _Position Size_ = $Risk / \text{SL Distance}$
        
          
        
    - _Take Profit_ = $Entry Price \pm (2.0 \times \text{ATR}_{14})$ (sesuaikan rasio _Risk:Reward_).
        
        Ketika harga menyentuh TP atau SL di iterasi bar berikutnya, paksa `curr_pos = 0.0` dan _update_ `capital` berdasarkan hasil _trade_ aktual dikalikan _Position Size_.
        
          
        

**2. Validator Tradisional (Trend Filter SMA/MA)**

_Machine learning_ seringkali mencari _mean-reversion_ di tengah _strong trend_, yang berujung pada kerugian jika tren tersebut tidak patah. Integrasi validator tradisional seperti SMA 200 atau EMA 50 berfungsi sebagai _hard-filter_ atau _directional bias_.

  

- Tambahkan fitur `df['sma_200'] = df['close'].rolling(200).mean()`.
    
      
    
- Modifikasi kondisi _entry_ di _state machine_:
    
      
    - **Long Entry Validasi:** `if z > entry_z and df['close'].iloc[i] > df['sma_200'].iloc[i]:`
        
          
        
    - **Short Entry Validasi:** `if allow_short and (z < -entry_z) and df['close'].iloc[i] < df['sma_200'].iloc[i]:`
        
        Ini memaksa model hanya mengambil posisi yang searah dengan inersia makro aset.
        
          
        

**3. Lose-Streak Tracker & Cooldown Treatment**

Sistem yang baik harus tahu kapan harus berhenti saat kondisi pasar tidak sesuai dengan logika algoritma.

  

- Inisialisasi `consecutive_losses = 0` dan `cooldown_timer = 0`.
    
      
    
- Setiap kali sebuah _trade_ ditutup (`curr_pos` kembali ke `0.0`), evaluasi PnL.
    
      
    - Jika PnL < 0, `consecutive_losses += 1`.
        
          
        
    - Jika PnL > 0, `consecutive_losses = 0`.
        
          
        
- _Treatment:_ Jika `consecutive_losses >= 3` (misalnya), set `cooldown_timer = 24` (berhenti _trading_ selama 24 jam ke depan). Selama `cooldown_timer > 0`, sistem memblokir semua sinyal Z-score, melindungi modal hingga _market regime_ bergeser kembali normal.
    
      
    

**4. Integrasi Mekanika Statistika & Signature Trading (Sig-Trading)**

Pendekatan Histeresis Z-Score pada Week 3 pada dasarnya sudah meminjam konsep fisika statistika (seperti model Ising untuk transisi fase magnetik), di mana _state_ (posisi) menolak untuk berubah sampai "medan gaya" (Z-score prediksi) melewati ambang batas energi aktivasi tertentu. Untuk meningkatkan ini, kita beralih ke _Signature Trading_ (Sig-Trading) untuk menangkap fitur lintasan harga masa lalu tanpa distorsi.

  

Strategi _Sig-Trading_ memodelkan keputusan _trading_ sebagai fungsi linier yang diterapkan pada _signature_ dari suatu jalur. Ini menyelesaikan masalah prediksi pengembalian aset yang seringkali terpapar akumulasi _error_ akibat asumsi probabilistik.

  

- **Definisi Market Factor Process:** Gabungkan aset $X$ dan faktor eksogen $f$ (seperti _Fear & Greed Index_ atau _News Sentiment_ historis) ke dalam sebuah proses multidimensi $\hat{Z}_t = (t, X_t, f_t)$.
    
      
    
- **Transformasi Hoff Lead-Lag:** Lakukan transformasi pada data diskrit menjadi proses _lead-lag_ $\hat{Z}^{LL}$. Transformasi ini krusial karena selisih area antara komponen _lead_ dan _lag_ memungkinkan kita memulihkan integral Itô sejati dari proses stokhastik saat resolusi waktu mendekati nol. Ini menghilangkan _look-ahead bias_ dalam perhitungan PnL dan menangkap _path-dependent volatility_ secara alami.
    
      
    
- **Perhitungan Signature:** Gunakan pustaka Python seperti `signatory` atau `esig` untuk menghitung _truncated signature_ $\hat{\mathbb{Z}}_{0,t}^{\leq M}$ pada level pemotongan $M$ yang ditentukan. Fitur-fitur ini menangkap geometri dan auto-korelasi lintasan harga dan berita (momentum atau _mean-reversion_) tanpa harus melakukan _feature engineering_ manual.
    
      
    
- **Evolusi Mean-Variance (Sig-Factor Model):** Alih-alih melakukan regresi _predict-then-optimize_ menggunakan LightGBM, strategi PnL masa depan dapat diekspresikan sebagai fungsi linier dari _expected Hoff lead-lag signature_.
    
      
    - Hitung atribusi PnL Signature $\mu^{\text{sig}}$ dan matriks Kovarians $\Sigma^{\text{sig}}$ dari dataset pelatihan.
        
          
        
    - Fungsional linier yang optimal diperoleh melalui persamaan analitik $\ell^* = \frac{1}{2\lambda} (\Sigma^{\text{sig}})^{-1} \mu^{\text{sig}}$.
        
          
        
    - Posisi dinamis pada waktu $t$ ditentukan secara langsung oleh $\xi_t = \langle \ell^*, \hat{\mathbb{Z}}_{0,t} \rangle$.
        
          
        

Dengan menggabungkan optimasi _mean-variance_ dinamis ini di dalam ruang _signature_, kamu tidak hanya mengoptimalkan ekspektasi keuntungan per _trade_, tetapi juga secara struktural menerapkan kontrol _drawdown_ di seluruh umur strategi berdasarkan ketergantungan lintasan (_path-dependency_).

  

Apakah kamu membutuhkan contoh struktur kode untuk integrasi `signatory` ke dalam pemrosesan _dataset_ `df_btc_raw` dan `df_news_raw` ini?

=== USER ===

ya

=== MODEL ===

Berikut adalah contoh struktur kode Python untuk mengimplementasikan **Sig-Trading** menggunakan *library* `signatory` dan `PyTorch`.

Kode ini akan menggantikan arsitektur ekstraksi fitur stasioner dan prediksi LightGBM di *Week 3*, beralih ke pembuatan **Market Factor Process** $\hat{Z}_t = (t, X_t, f_t)$ dan menghitung fungsional linier optimal $\ell^*$ berdasarkan *signature*.

### Persiapan *Library*

Pastikan kamu sudah menginstal pustaka yang dibutuhkan:

```bash
pip install torch signatory pandas numpy

```

### Struktur Kode Implementasi Sig-Trading

```python
import torch
import signatory
import pandas as pd
import numpy as np
from datetime import datetime

# =====================================================================
# 1. Konstruksi Market Factor Process (Add-Time, Asset, Factor)
# =====================================================================
def build_market_factor_process(df_btc, df_news):
    """
    Menggabungkan harga aset dan sinyal eksogen menjadi proses Z_t = (t, X_t, f_t)
    """
    # Merge data (mirip dengan fungsi build_week3_features)
    df = pd.merge_asof(df_btc.sort_index(), df_news.sort_index(), 
                       left_index=True, right_index=True, direction='backward')
    
    df['news_sentiment_1h'] = df['news_sentiment_1h'].ffill().fillna(0.0)
    
    # Normalisasi harga (log harga agar stasioneritas lintasan lebih baik)
    df['log_close'] = np.log(df['close'] / df['close'].iloc[0])
    
    # Add-Time variable (t) - normalisasi waktu (misal fraksi dari 1 tahun)
    df['time_fraction'] = (df.index - df.index[0]).total_seconds() / (365 * 24 * 3600)
    
    # Konstruksi \hat{Z}_t
    Z_df = df[['time_fraction', 'log_close', 'news_sentiment_1h']].copy()
    Z_df.columns = ['t', 'X', 'f']
    
    # Target PnL aktual 1 jam ke depan untuk perhitungan Atribusi PnL (\mu^{sig})
    Z_df['target_return_1h'] = df['close'].shift(-1) / df['close'] - 1.0
    
    return Z_df.dropna()

# =====================================================================
# 2. Pembuatan Rolling Windows & Lead-Lag Transformation
# =====================================================================
def get_rolling_path_tensors(Z_df, window_size=24):
    """
    Mengubah DataFrame time-series menjadi tensor paths [Batch, Length, Channels]
    untuk dimasukkan ke dalam Signatory.
    """
    paths = []
    targets = []
    
    # Ambil nilai numpy
    Z_values = Z_df[['t', 'X', 'f']].values
    target_values = Z_df['target_return_1h'].values
    
    for i in range(len(Z_values) - window_size):
        # Potong lintasan sepanjang window_size (misal 24 jam ke belakang)
        path_window = Z_values[i : i + window_size]
        
        # OPSI: Standard Lead-Lag Transformation (Simplifikasi dari Hoff Lead-Lag)
        # Signatory membutuhkan input [Batch, Stream_Length, Channels]
        # Untuk implementasi dasar, kita gunakan raw path. 
        # (Hoff Lead-Lag penuh bisa ditambahkan dengan interpolasi di sini).
        
        paths.append(path_window)
        targets.append(target_values[i + window_size - 1])
        
    # Convert ke PyTorch Tensors
    tensor_paths = torch.tensor(np.array(paths), dtype=torch.float32)
    tensor_targets = torch.tensor(np.array(targets), dtype=torch.float32)
    
    return tensor_paths, tensor_targets

# =====================================================================
# 3. Menghitung Truncated Signature
# =====================================================================
def compute_signatures(tensor_paths, depth=2):
    """
    Menghitung signature \mathbb{Z}^{\leq M}_{0,t} menggunakan library Signatory
    """
    # Hitung signature sampai kedalaman M (depth)
    # Output shape: [Batch, Signatory_Channels]
    # Jika channels=3 (t, X, f) dan depth=2, ukuran output adalah 3 + 3^2 = 12 terms
    sigs = signatory.signature(tensor_paths, depth=depth)
    
    # Tambahkan elemen order ke-0 yaitu skalar 1.0 ke dalam tensor
    batch_size = sigs.shape[0]
    order_zero = torch.ones((batch_size, 1), dtype=torch.float32)
    
    # Full Truncated Signature
    full_sigs = torch.cat([order_zero, sigs], dim=1)
    
    return full_sigs

# =====================================================================
# 4. Solusi Analitik Sig-Factor (Mean-Variance Optimisation)
# =====================================================================
def fit_sig_trader(full_sigs, tensor_targets, risk_lambda=1.0):
    """
    Mengimplementasikan \ell^* = (1 / 2\lambda) * (\Sigma^{sig})^{-1} \mu^{sig}
    Secara praktis, ini sama dengan Ridge Regression antara Signature dan Target Returns,
    karena kita memetakan state linier signature ke masa depan PnL.
    """
    X = full_sigs.numpy()     # [Batch, Sig_Terms]
    Y = tensor_targets.numpy() # [Batch]
    
    # Hitung \mu^{sig} (Expected PnL Attribution)
    # Rata-rata dari (Target PnL * Signature Term)
    mu_sig = np.mean(X * Y[:, np.newaxis], axis=0)
    
    # Hitung \Sigma^{sig} (Covariance Matrix dari Signature)
    # Ditambahkan regularisasi (ridge penalty) e-6 untuk menghindari matriks singular
    Sigma_sig = np.cov(X.T) + np.eye(X.shape[1]) * 1e-6
    
    # Invers Covariance Matrix
    Sigma_inv = np.linalg.inv(Sigma_sig)
    
    # Fungsional Linier Optimal (\ell^*)
    # l_star = (Sigma_inv @ mu_sig) / (2 * risk_lambda)
    l_star = np.dot(Sigma_inv, mu_sig) / (2 * risk_lambda)
    
    return l_star

# =====================================================================
# 5. Eksekusi Strategi
# =====================================================================
def execute_sig_trading(Z_df, depth=2, window_size=24, risk_lambda=1.0):
    
    # 1. Siapkan data tensor
    tensor_paths, tensor_targets = get_rolling_path_tensors(Z_df, window_size)
    
    # 2. Hitung Signatures
    full_sigs = compute_signatures(tensor_paths, depth=depth)
    
    # (Walk-Forward Validation dapat diimplementasikan dengan membelah full_sigs 
    # menjadi Data Train dan Data Test. Di sini kita contohkan fitting keseluruhan).
    train_size = int(len(full_sigs) * 0.8)
    
    X_train = full_sigs[:train_size]
    Y_train = tensor_targets[:train_size]
    X_test = full_sigs[train_size:]
    
    # 3. Cari Fungsional Linier Optimal (Kalibrasi Model)
    l_star = fit_sig_trader(X_train, Y_train, risk_lambda=risk_lambda)
    
    # 4. Generate Posisi Aktual (\xi_t) pada Data Test
    # \xi_t = \langle \ell^*, \hat{\mathbb{Z}}_{0,t} \rangle
    # Perkalian dot (inner product) antara bobot l_star dan terms signature pada waktu t
    test_positions = np.dot(X_test.numpy(), l_star)
    
    # Normalisasi Posisi dengan Histeresis (Bisa dipadukan dengan poin #1 dan #3 dari kebutuhanmu)
    # misal: terapkan threshold untuk menghilangkan noise "zero-crossing"
    # smooth_positions = apply_deadband_and_budget(test_positions, ...)
    
    return test_positions, l_star

# Contoh Penggunaan:
# test_pos, optimal_weights = execute_sig_trading(build_market_factor_process(df_btc_raw, df_news_raw), depth=2)

```

### Penjelasan Transisi ke Week 4:

1. **Tidak Ada Label Overlapping:** Kita langsung mencari matriks kovarians $\Sigma^{\text{sig}}$ dan return ekspektasi $\mu^{\text{sig}}$ secara aljabar menggunakan *inner product* (perkalian matriks), bukan optimasi *Gradient Descent* seperti di LightGBM. Ini eksekusinya jauh lebih cepat secara komputasi.
2. **Path-Dependent Secara Alami:** Variabel `window_size=24` (atau sesuai panjang lintasan yang kamu mau) membentuk "sejarah" pergerakan. `signatory.signature()` merangkum geometri dari "sejarah" 24 jam ini (termasuk volatilitas, korelasi silang antar harga dan berita, dsb) ke dalam sebuah array statis.
3. **Regularisasi & Invertibilitas:** Pada `fit_sig_trader`, ditambahkan matriks identitas kecil (`1e-6`) pada $\Sigma^{\text{sig}}$. Ini diperlukan dalam mekanika statistika saat matriks tidak stabil (*ill-posed*) akibat jumlah level *signature* yang bertambah secara eksponensial.
4. **Integrasi ke Dynamic Sizing:** Output `test_positions` pada tahap akhir ini adalah skor $\xi_t$. Output ini bisa kamu umpankan kembali ke dalam modul **Z-Score Hysteresis & Position Sizing ($)** yang kamu minta pada poin ke-1.