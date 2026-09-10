## Prompt:
8/17/2026, 9:55:53 PM

lanjut Tahap L

## Response:
8/17/2026, 9:55:53 PM

# Tahap L — Data Engineering: Dari Data Pasar Mentah Menjadi State Matematis yang Valid

Tahap L adalah fondasi seluruh sistem. Pada tahap ini kita belum berbicara tentang QAOA secara mendalam. Tujuannya adalah memastikan bahwa pada setiap waktu $t$, sistem memiliki **state pasar yang benar-benar hanya dibangun dari informasi yang tersedia pada saat $t$**.

Secara keseluruhan:

$$
\boxed{
\text{Raw Market Data}
\rightarrow
\text{Cleaning}
\rightarrow
\text{Alignment}
\rightarrow
\text{Feature Construction}
\rightarrow
\text{Factor State}
\rightarrow
\mathcal F_t
}
$$

dengan $\mathcal F_t$ sebagai **information set** pada waktu $t$.

---

# L.1. Prinsip paling penting: Information Set

Kita definisikan:

$$
\boxed{
\mathcal F_t
=
\sigma
(
\text{semua informasi yang tersedia sampai waktu }t
)
}
$$

Forecast harus berbentuk:

$$
\boxed{
\hat{\mu}_{t+1}
=
E[r_{t+1}\mid\mathcal F_t].
}
$$

Bukan:

$$
E[r_{t+1}\mid\mathcal F_{t+1}].
$$

Perbedaan satu indeks ini sangat penting.

Model kita harus menjawab:

> "Jika saya benar-benar berada pada pukul 10:00, informasi apa yang saya miliki?"

bukan:

> "Setelah candle berikutnya selesai, apa yang sebenarnya terjadi?"

---

# L.2. Masalah utama: pasar kita tidak memiliki kalender yang sama

Ini menjadi jauh lebih penting ketika kita menggabungkan crypto dengan:

- saham AS,
- emas,
- USD/DXY,
- indeks saham,
- VIX.

Crypto:

$$
24/7.
$$

Saham AS:

$$
\text{weekday + market hours}.
$$

Gold futures:

$$
\text{hampir 24/5}.
$$

DXY:

$$
\text{hari perdagangan tertentu + jam perdagangan tertentu}.
$$

Maka kita tidak boleh sekadar melakukan:

```python
data = pd.concat(...)
```

dan menganggap timestamp-nya otomatis comparable.

---

# L.3. Kita membutuhkan canonical clock

Untuk V1:

$$
\boxed{
\Delta t=1h
}
$$

dan kita gunakan:

$$
t_k=t_0+k\Delta t.
$$

Sehingga semua data akhirnya dipetakan ke grid:

$$
\mathcal T
=
\{
t_0,t_1,\ldots,t_T
\}.
$$

---

# L.4. Timezone

Saya sangat menyarankan seluruh internal engine menggunakan:

$$
\boxed{
UTC
}
$$

sebagai timezone canonical.

Jadi:

$$
timestamp_{raw}
\rightarrow
timestamp_{UTC}.
$$

Baru kemudian ketika menampilkan hasil:

$$
UTC
\rightarrow
Asia/Jakarta
$$

atau timezone lain.

Jangan menyimpan sebagian data dalam WIB dan sebagian dalam UTC.

---

# L.5. Mengapa UTC?

Karena jika kita menggunakan:

$$
Asia/Jakarta
$$

untuk crypto dan:

$$
America/New\_York
$$

untuk saham, DST Amerika akan menciptakan pergeseran jam.

Dengan UTC:

$$
\boxed{
\text{semua timestamp memiliki referensi global yang sama}.
}
$$

---

# L.6. Timestamp candle

Misalkan kita memiliki candle:

$$
[10:00,11:00).
$$

Kita harus menentukan apakah timestamp candle merepresentasikan:

- opening time,
- closing time.

Saya menyarankan:

$$
\boxed{
timestamp = candle\ close\ time.
}
$$

Jadi candle:

$$
[10:00,11:00)
$$

direpresentasikan sebagai:

$$
t=11:00.
$$

Dengan demikian seluruh OHLCV tersebut diketahui pada:

$$
t=11:00.
$$

---

# L.7. Ini menghindari look-ahead

Misalkan:

$$
C_t
$$

adalah close candle pada pukul 11:00.

Kita boleh menggunakan:

$$
C_t
$$

untuk membuat signal pada:

$$
t=11:00.
$$

Tetapi kita **tidak boleh** menggunakan:

$$
C_{t+1}
$$

untuk membuat keputusan pada:

$$
t.
$$

---

# L.8. Data layer

Saya menyarankan struktur:

```text
data/
├── raw/
├── normalized/
├── features/
├── factors/
└── metadata/
```

Dengan:

```text
raw/
    BTCUSDT/
    ETHUSDT/
    SOLUSDT/
    ...
    
factors/
    DXY/
    GOLD/
    SPX/
    VIX/
```

---

# L.9. Raw data harus immutable

Data mentah jangan pernah diedit.

Misalnya:

```text
raw/BTCUSDT/2026-08-17.parquet
```

tidak boleh ditimpa setelah cleaning.

Pipeline:

$$
Raw
\rightarrow
Normalized
$$

bukan:

$$
Raw
\rightarrow
Raw'
$$

---

# L.10. Mengapa?

Jika suatu hari hasil backtest berubah, kita harus dapat mengetahui:

$$
\boxed{
\text{apakah model berubah atau data berubah?}
}
$$

Ini adalah prinsip reproducibility.

---

# L.11. Schema OHLCV

Setiap bar:

$$
\boxed{
D_t=
(
t,O,H,L,C,V
)
}
$$

dengan:

- $t$: timestamp,
- $O$: open,
- $H$: high,
- $L$: low,
- $C$: close,
- $V$: volume.

Untuk sistem kita tambahkan:

$$
VWAP
$$

jika tersedia.

---

# L.12. Validasi OHLC

Harus selalu memenuhi:

$$
H_t\geq
\max(O_t,C_t)
$$

dan:

$$
L_t\leq
\min(O_t,C_t).
$$

Selain itu:

$$
H_t\geq L_t.
$$

Jika tidak:

$$
\boxed{
data\ corrupt.
}
$$

---

# L.13. Volume

Harus:

$$
V_t\geq0.
$$

Jika:

$$
V_t<0,
$$

bar invalid.

Tetapi:

$$
V_t=0
$$

tidak otomatis berarti corrupt.

Untuk instrumen tertentu, volume dapat memang tidak tersedia atau nol.

---

# L.14. Duplicate timestamp

Untuk setiap asset:

$$
\boxed{
t_i\neq t_j
\quad
\forall i\neq j
}
$$

harus berlaku.

Jika terdapat duplicate:

$$
t_i=t_j,
$$

kita harus mempunyai aturan deterministic untuk memilih record yang benar.

Jangan menggunakan:

```python
drop_duplicates()
```

tanpa memahami penyebab duplikat.

---

# L.15. Missing candle

Misalkan canonical grid memiliki:

$$
t_1,t_2,t_3,t_4,t_5.
$$

Tetapi data:

$$
t_1,t_2,t_4,t_5.
$$

Maka:

$$
t_3
$$

missing.

---

# L.16. Jangan sembarangan forward-fill harga

Untuk market data:

$$
P_{t_3}
\neq
P_{t_2}
$$

hanya karena data $t_3$ hilang.

Forward filling dapat menciptakan:

$$
\boxed{
artificial\ zero\ return.
}
$$

Ini berbahaya untuk:

$$
\Sigma.
$$

---

# L.17. Bedakan dua jenis missing data

### Type A

Market memang tutup.

Contoh:

$$
SPX
$$

pada Sabtu.

### Type B

Data seharusnya ada tetapi hilang.

Contoh:

$$
BTC
$$

pada satu jam tertentu.

Kedua kondisi ini **tidak boleh diperlakukan sama**.

---

# L.18. Crypto

Untuk crypto:

$$
\boxed{
missing\ candle
\approx
data\ quality\ problem
}
$$

kecuali exchange memang tidak menghasilkan candle.

Kita perlu flag:

$$
M_{i,t}\in\{0,1\}.
$$

---

# L.19. Stock market

Untuk saham:

$$
M_{i,t}=0
$$

pada periode ketika market memang tutup.

Tetapi kita tidak boleh menyimpulkan:

$$
r_{i,t}=0.
$$

Tidak ada return hourly jika market tidak trading.

---

# L.20. Calendar-aware data model

Setiap asset harus memiliki:

$$
\boxed{
Calendar_i(t)
}
$$

yang memberi tahu apakah instrumen tersebut aktif pada $t$.

Kemudian:

$$
Active_{i,t}
=
\begin{cases}
1,&market\ open\\
0,&market\ closed.
\end{cases}
$$

---

# L.21. Masalah penting pada factor data

Misalnya crypto trading:

$$
Saturday,\ 03:00\ UTC.
$$

Tetapi:

$$
SPX
$$

tidak memiliki observasi baru.

Kita **boleh menggunakan observasi SPX terakhir yang diketahui** sebagai state factor, tetapi harus memahami maknanya.

Kita tidak boleh menganggap:

$$
SPX_{Saturday}
$$

benar-benar mempunyai return nol.

---

# L.22. Factor state versus factor return

Ini perbedaan penting.

Misalnya harga terakhir SPX:

$$
P_{SPX,t_0}.
$$

Pada saat market tutup:

$$
P_{SPX,t}=P_{SPX,t_0}
$$

sebagai **last observed price**.

Tetapi:

$$
r_{SPX,t}=0
$$

tidak boleh otomatis dianggap sebagai actual market return.

Untuk forecasting crypto, kita dapat menggunakan:

$$
\boxed{
last\ known\ factor\ state
}
$$

dengan flag:

$$
Age_{factor,t}.
$$

---

# L.23. Factor age

Definisikan:

$$
\boxed{
Age_{f,t}
=
t-t^{last}_f.
}
$$

Misalnya:

$$
Age_{SPX,t}=17h.
$$

Artinya informasi SPX terakhir sudah berumur 17 jam.

Ini dapat dimasukkan ke feature model.

---

# L.24. Dengan demikian factor feature menjadi

$$
\boxed{
X_{factor,t}
=
[
r_f,
Age_f,
\beta_f,
\ldots
].
}
$$

Jadi model mengetahui:

> "Saya sedang menggunakan data SPX yang berumur beberapa jam."

---

# L.25. DXY dan Gold

Kita akan perlakukan:

$$
DXY
$$

dan:

$$
Gold
$$

sebagai **macro factor**, bukan sekadar asset tambahan.

Secara konseptual:

$$
r_{crypto}
=
\alpha
+
\beta_{BTC}r_{BTC}
+
\beta_{ETH}r_{ETH}
+
\beta_{USD}r_{DXY}
+
\beta_{Gold}r_{Gold}
+
\epsilon.
$$

---

# L.26. Tanda factor exposure

Perhatikan:

### DXY

Jika:

$$
\beta_{DXY}<0,
$$

kenaikan USD berkorelasi dengan penurunan asset.

### Gold

Jika:

$$
\beta_{Gold}>0,
$$

asset cenderung bergerak searah dengan gold.

Tetapi kita **tidak akan mengasumsikan tanda ini sejak awal**.

Model akan mengestimasinya.

---

# L.27. Factor return

Gunakan:

$$
r_{f,t}
=
\ln
\frac{P_{f,t}}
{P_{f,t-1}}.
$$

Tetapi hanya jika kedua timestamp memang valid:

$$
t-1,t
\in
TradingCalendar_f.
$$

---

# L.28. Cross-sectional alignment

Setelah semua data tersedia:

$$
\boxed{
D_t
=
[
D_{BTC,t},
D_{ETH,t},
D_{SOL,t},
\ldots,
D_{DXY,t},
D_{Gold,t},
D_{SPX,t},
D_{VIX,t}
].
}
$$

Namun bukan berarti semua nilai harus berasal dari candle yang identik.

Kita menggunakan:

$$
t^{last}_i\leq t.
$$

---

# L.29. Last-known-value operator

Definisikan:

$$
\boxed{
P_{i,t}^{LK}
=
P_{i,\tau^\star}
}
$$

dengan:

$$
\tau^\star
=
\max\{\tau\leq t:
P_{i,\tau}\text{ tersedia}\}.
$$

Kemudian:

$$
Age_{i,t}=t-\tau^\star.
$$

---

# L.30. Batas stale data

Kita tidak boleh menggunakan last-known value selamanya.

Definisikan:

$$
Age_{i,t}\leq A_{max}.
$$

Jika:

$$
Age_{i,t}>A_{max},
$$

factor dianggap:

$$
\boxed{
stale.
}
$$

Misalnya untuk V1:

$$
A_{max}=48h.
$$

---

# L.31. Jadi setiap feature memiliki status

Misalnya:

```text
BTC return       valid
ETH return       valid
DXY return       valid
Gold return      valid
SPX return       stale
VIX return       stale
```

Model tidak boleh kehilangan informasi mengenai status tersebut.

---

# L.32. Asset universe versus factor universe

Kita pisahkan:

$$
\boxed{
\mathcal A
=
\text{tradable assets}
}
$$

dan:

$$
\boxed{
\mathcal F
=
\text{information factors}.
}
$$

Contoh:

$$
\mathcal A=
\{
BTC,ETH,SOL,BNB,XRP,ADA
\}.
$$

Sedangkan:

$$
\mathcal F=
\{
BTC,ETH,DXY,Gold,SPX,VIX
\}.
$$

Overlap diperbolehkan.

---

# L.33. Mengapa pemisahan ini penting?

Karena suatu factor tidak harus ditradingkan.

Misalnya:

$$
DXY
$$

dapat memberikan informasi:

$$
\hat\mu_{BTC}
$$

tanpa pernah masuk ke portfolio.

---

# L.34. Corporate actions pada saham

Ketika kita pindah ke saham internasional, ada masalah:

- stock split,
- reverse split,
- dividend,
- spin-off.

Kita harus menentukan apakah model menggunakan:

$$
Raw\ Price
$$

atau:

$$
Adjusted\ Price.
$$

---

# L.35. Untuk return model

Saya lebih memilih:

$$
\boxed{
adjusted\ price
}
$$

untuk historical return estimation, karena kita ingin mengukur economic return yang comparable.

Tetapi untuk execution simulation:

$$
\boxed{
actual\ tradable\ price
}
$$

harus digunakan.

Jadi:

$$
ResearchPrice
\neq
ExecutionPrice
$$

dapat terjadi.

---

# L.36. Ini menghasilkan dua price streams

```text
Adjusted price
      ↓
return / covariance / factor model

Raw tradable price
      ↓
entry / SL / TP / execution
```

Ini sangat penting ketika nanti kita masuk ke saham.

---

# L.37. Survivorship bias

Misalnya pada 2021 terdapat asset:

$$
A
$$

yang kemudian collapse/delist.

Jika kita hanya menggunakan asset yang masih hidup pada 2026:

$$
A
$$

hilang dari universe.

Akibatnya backtest menjadi terlalu optimistik.

---

# L.38. Solusinya

Universe harus bersifat:

$$
\boxed{
point\ in\ time.
}
$$

Artinya pada:

$$
t
$$

kita hanya menggunakan asset yang memang tersedia pada waktu $t$.

$$
\mathcal A_t.
$$

Bukan:

$$
\mathcal A_{2026}.
$$

---

# L.39. Crypto universe

Jangan langsung menggunakan:

> top 10 crypto saat ini.

Karena itu menciptakan survivorship bias.

Lebih baik:

$$
Universe_t
=
\text{assets satisfying liquidity criteria at }t.
$$

---

# L.40. Liquidity filter

Misalnya:

$$
ADV_i
=
\frac1W
\sum_t VolumeValue_{i,t}.
$$

Kemudian:

$$
ADV_i\geq ADV_{min}.
$$

Untuk crypto kita dapat menggunakan:

$$
VolumeValue
=
P_tV_t.
$$

---

# L.41. Spread filter

Jika data tersedia:

$$
Spread_i
=
\frac{Ask-Bid}{Mid}.
$$

Kita dapat mengharuskan:

$$
Spread_i
\leq
Spread_{max}.
$$

Untuk V1, spread dapat dimodelkan secara konservatif jika order book belum digunakan.

---

# L.42. Data quality score

Saya menyarankan setiap asset memiliki:

$$
\boxed{
Q_i(t)\in[0,1].
}
$$

Misalnya:

$$
Q_i
=
1
-
w_1Missing
-
w_2Stale
-
w_3Corrupt
-
w_4LiquidityRisk.
$$

Jika:

$$
Q_i<Q_{min},
$$

asset dikeluarkan dari universe.

---

# L.43. Feature engineering

Setelah data bersih, kita mulai membangun:

$$
X_t.
$$

Minimal:

$$
\boxed{
X_{i,t}
=
[
r^{1h},
r^{4h},
r^{24h},
\sigma^{24h},
\sigma^{168h},
volume_z,
\beta_{BTC},
\beta_{ETH},
\beta_{DXY},
\beta_{Gold}
].
}
$$

---

# L.44. Momentum

$$
r^{H}_{i,t}
=
\ln
\frac{P_{i,t}}
{P_{i,t-H}}.
$$

Sehingga:

$$
r^{1h},
r^{4h},
r^{24h}.
$$

---

# L.45. Volatility jangka pendek

$$
\sigma_{i,t}^{24h}
=
Std(
r_{i,t-23},
\ldots,
r_{i,t}
).
$$

---

# L.46. Volatility jangka menengah

$$
\sigma_{i,t}^{168h}
=
Std(
r_{i,t-167},
\ldots,
r_{i,t}
).
$$

168 jam:

$$
7\times24.
$$

Ini memberikan proxy:

$$
1day
\quad\text{vs}\quad
1week.
$$

---

# L.47. Volatility regime

Kita dapat membentuk:

$$
VR_{i,t}
=
\frac{
\sigma_{i,t}^{24h}
}{
\sigma_{i,t}^{168h}
}.
$$

Jika:

$$
VR>1,
$$

short-term volatility lebih tinggi daripada baseline.

---

# L.48. Volume z-score

$$
z_{V,i,t}
=
\frac{
V_{i,t}-\mu_{V,i}
}{
\sigma_{V,i}
}.
$$

Lebih baik menggunakan log-volume:

$$
u_{i,t}=\ln(1+V_{i,t})
$$

kemudian:

$$
z_{u,i,t}
=
\frac{
u_{i,t}-\mu_u
}{
\sigma_u
}.
$$

---

# L.49. Factor beta rolling

Untuk factor $f$:

$$
\boxed{
\beta_{i,f,t}
=
\frac{
Cov(r_i,r_f)
}{
Var(r_f)
}.
}
$$

Estimasi dilakukan pada rolling window:

$$
W_\beta.
$$

---

# L.50. Residual return

Setelah factor model:

$$
r_i
=
\alpha_i+\beta_i^Tf+\epsilon_i.
$$

Kita dapat menghitung:

$$
\boxed{
\epsilon_{i,t}
=
r_{i,t}
-
\hat\alpha_i
-
\hat\beta_i^T f_t.
}
$$

Residual ini sangat menarik.

Karena:

$$
\epsilon_i
$$

merepresentasikan pergerakan asset yang **tidak dijelaskan oleh common factors**.

---

# L.51. Ini memberi kita dua jenis signal

### Factor-driven

$$
\beta_i^Tf_t.
$$

### Idiosyncratic

$$
\epsilon_i.
$$

Sehingga:

$$
\boxed{
\hat r_i
=
\hat r_i^{factor}
+
\hat r_i^{idiosyncratic}.
}
$$

---

# L.52. Ini jauh lebih kuat daripada hanya momentum

Karena model dapat mengatakan:

> BTC naik bukan berarti semua altcoin harus dibeli.

Ia dapat melihat:

$$
\beta_{BTC,i}
$$

dan:

$$
\epsilon_i.
$$

Misalnya:

$$
BTC\uparrow
$$

tetapi:

$$
\epsilon_{SOL}\ll0.
$$

Maka SOL mungkin tetap tidak menarik.

---

# L.53. Residual correlation

Kita juga dapat menghitung:

$$
\boxed{
\Sigma_\epsilon
=
Cov(\epsilon).
}
$$

Kemudian portfolio risk dapat dipisahkan menjadi:

$$
\boxed{
\Sigma
=
B\Sigma_fB^T
+
\Sigma_\epsilon.
}
$$

Ini adalah decomposition yang sangat berguna.

---

# L.54. Interpretasi portfolio risk

$$
\boxed{
PortfolioRisk
=
FactorRisk
+
IdiosyncraticRisk.
}
$$

Secara lebih lengkap:

$$
\Sigma_p
=
B\Sigma_fB^T
+
\Sigma_\epsilon.
$$

Ini nantinya dapat dimasukkan langsung ke:

$$
w^T\Sigma w.
$$

---

# L.55. Ini menghubungkan Tahap L dengan Tahap M

Tahap L menghasilkan:

$$
\boxed{
\hat\mu_t,\quad
B_t,\quad
\Sigma_{f,t},\quad
\Sigma_{\epsilon,t}.
}
$$

Tahap M akan menggunakan semuanya untuk:

$$
\boxed{
Forecasting + Risk Engine.
}
$$

---

# L.56. Data matrix

Pada waktu $t$, kita akhirnya mempunyai:

$$
\boxed{
R_t
\in
\mathbb R^{N\times W}.
}
$$

Misalnya:

$$
N=6,
\quad
W=720.
$$

Maka:

$$
R_t
\in
\mathbb R^{6\times720}.
$$

---

# L.57. Factor matrix

Jika kita mempunyai $F=6$ factor:

$$
\boxed{
F_t
\in
\mathbb R^{6\times720}.
}
$$

Kemudian:

$$
R_t
=
A+
BF_t+
E_t.
$$

---

# L.58. Estimasi $B$

Secara OLS:

$$
\boxed{
\hat B
=
R F^T
(FF^T)^{-1}
}
$$

jika matrix invertible.

Dengan intercept, kita augment:

$$
\tilde F
=
\begin{bmatrix}
1\\
F
\end{bmatrix}.
$$

Kemudian:

$$
\hat\Theta
=
R\tilde F^T
(
\tilde F\tilde F^T
)^{-1}.
$$

---

# L.59. Tetapi kita sebaiknya menggunakan regularisasi

Karena factor dapat berkorelasi:

$$
DXY
\leftrightarrow
Gold
\leftrightarrow
SPX
\leftrightarrow
VIX.
$$

Maka:

$$
FF^T
$$

dapat ill-conditioned.

Gunakan ridge:

$$
\boxed{
\hat\Theta
=
RF^T
(
FF^T+\lambda_FI
)^{-1}.
}
$$

---

# L.60. Feature normalization

Untuk forecasting, feature harus dinormalisasi menggunakan **training window saja**.

$$
\boxed{
z_{i,t}
=
\frac{x_{i,t}-\mu_{train}}
{\sigma_{train}}.
}
$$

Jangan menggunakan:

$$
\mu_{all}
$$

yang mencakup future data.

---

# L.61. Pipeline anti-leakage

Secara tepat:

```text
RAW DATA
   ↓
CLEAN
   ↓
TIME ALIGN
   ↓
ROLLING WINDOW ENDING AT t
   ↓
FIT SCALER USING [t-W,t]
   ↓
FIT MODEL USING [t-W,t]
   ↓
GENERATE μ̂(t+1)
   ↓
OPTIMIZE
   ↓
TRADE t+1
```

Bukan:

```text
ALL DATA
   ↓
NORMALIZE
   ↓
TRAIN
   ↓
BACKTEST
```

---

# L.62. Mengapa urutan ini sangat penting?

Karena misalnya:

$$
x_{2026}
$$

mempengaruhi:

$$
\mu_{2021}.
$$

Itu berarti model secara tidak langsung mengetahui masa depan.

Walaupun target tidak secara eksplisit diberikan, leakage tetap terjadi.

---

# L.63. Feature store

Saya menyarankan menyimpan hasil feature:

```text
features/
    2026-01.parquet
    2026-02.parquet
    ...
```

dengan schema:

```text
timestamp
asset
return_1h
return_4h
return_24h
vol_24h
vol_168h
volume_z
beta_btc
beta_eth
beta_dxy
beta_gold
factor_age_dxy
factor_age_gold
regime
data_quality
```

---

# L.64. State vector

Semua informasi yang diperlukan optimizer pada waktu $t$:

$$
\boxed{
S_t
=
[
\hat\mu_t,
\Sigma_t,
B_t,
Regime_t,
Liquidity_t,
w_{t-1},
Position_t
].
}
$$

Ini adalah **market state** kita.

---

# L.65. Kemudian optimizer menerima

$$
\boxed{
Optimizer(S_t)
\rightarrow
w_t^\star.
}
$$

Dengan kata lain, QAOA **tidak membaca data mentah**.

QAOA menerima:

$$
\boxed{
mathematical\ representation
}
$$

dari kondisi pasar.

Ini arsitektur yang jauh lebih bersih.

---

# L.66. Data layer dan quantum layer menjadi terpisah

```text
              MARKET
                 │
                 ▼
          DATA ENGINEERING
                 │
                 ▼
        FEATURE / FACTOR ENGINE
                 │
                 ▼
            MARKET STATE
                 │
        ┌────────┴────────┐
        ▼                 ▼
 CLASSICAL SOLVER       QAOA
        │                 │
        └────────┬────────┘
                 ▼
           PORTFOLIO
                 │
                 ▼
          EXECUTION ENGINE
```

Ini memungkinkan kita menguji:

$$
\text{same state}
$$

dengan:

$$
Classical
$$

dan:

$$
Quantum.
$$

Itu sangat penting untuk penelitian yang fair.

---

# L.67. Cross-market extension

Sekarang kita kembali ke tujuan besarmu: **tidak berhenti di crypto**.

Kita definisikan factor architecture:

$$
\boxed{
F_t=
[
Crypto,
Equity,
USD,
Commodity,
Volatility
].
}
$$

Contohnya:

$$
F_t=
[
BTC,
ETH,
SPX,
DXY,
Gold,
VIX
].
$$

Kemudian universe dapat berubah menjadi:

$$
\mathcal A=
\{
AAPL,
MSFT,
NVDA,
AMZN,
META,
TSLA
\}.
$$

Model yang sama masih berlaku.

---

# L.68. Yang berubah hanya data adapter

Crypto:

```text
CryptoDataAdapter
```

Saham:

```text
EquityDataAdapter
```

Gold:

```text
CommodityDataAdapter
```

DXY:

```text
MacroDataAdapter
```

Tetapi output semuanya harus sama:

$$
\boxed{
CanonicalMarketData
}
$$

Ini prinsip **interface normalization**.

---

# L.69. Contoh canonical schema

```text
timestamp
symbol
asset_class
open
high
low
close
volume
currency
market_open
data_age
data_quality
```

Kemudian downstream tidak perlu tahu apakah:

$$
BTC
$$

atau:

$$
AAPL.
$$

---

# L.70. Multi-currency

Ini menjadi sangat penting ketika masuk saham internasional.

Misalnya:

$$
AAPL
$$

dalam USD.

Tetapi jika nanti kita membeli saham Jepang:

$$
7203.T
$$

dalam JPY.

Portfolio base currency kita misalnya:

$$
USD.
$$

Maka return harus mempertimbangkan FX.

---

# L.71. Local return versus base-currency return

Jika:

$$
P_t^{JPY}
$$

dan:

$$
FX_t
=
USD/JPY,
$$

maka:

$$
P_t^{USD}
=
\frac{P_t^{JPY}}
{FX_t}.
$$

Sehingga return investor USD menjadi:

$$
\boxed{
r^{USD}
=
r^{local}
-
r^{FX}
}
$$

secara log-return approximation/exact sesuai definisi FX.

Jadi FX juga akhirnya menjadi factor.

---

# L.72. Ini berarti arsitektur kita benar-benar global

Nanti:

$$
\boxed{
Global\ Factor\ Model
}
$$

dapat mencakup:

$$
\{
BTC,
ETH,
DXY,
Gold,
SPX,
VIX,
USDJPY,
EURUSD,
\ldots
\}.
$$

Tetapi jangan masukkan semuanya sekaligus.

Kita akan menambah factor secara bertahap melalui ablation test.

---

# L.73. Data lineage

Setiap angka yang masuk ke QUBO idealnya dapat dilacak:

$$
Q_{ij,t}
$$

harus dapat ditelusuri ke:

$$
\hat\mu_t
$$

dan:

$$
\Sigma_t,
$$

yang dapat ditelusuri ke:

$$
R_{t-W:t},
$$

yang dapat ditelusuri ke:

$$
RawMarketData.
$$

Sehingga:

$$
\boxed{
Q
\leftarrow
\Sigma,\mu
\leftarrow
Features
\leftarrow
NormalizedData
\leftarrow
RawData.
}
$$

---

# L.74. Ini sangat berguna ketika hasil aneh

Misalnya QAOA tiba-tiba memilih:

$$
w_{BTC}=50\%.
$$

Kita dapat menelusuri:

$$
w_{BTC}
\rightarrow
Q
\rightarrow
\mu_{BTC},\Sigma
\rightarrow
features
\rightarrow
raw\ candles.
$$

Kita tidak mempunyai black box.

---

# L.75. Checkpoint yang wajib ada

Sebelum masuk Tahap M, saya ingin pipeline kita dapat melewati **7 checkpoint**.

### Checkpoint 1

Semua timestamp:

$$
UTC.
$$

### Checkpoint 2

Tidak ada duplicate candle.

### Checkpoint 3

OHLC valid.

### Checkpoint 4

Missing data teridentifikasi.

### Checkpoint 5

Market calendar benar.

### Checkpoint 6

Tidak ada feature menggunakan future information.

### Checkpoint 7

Rolling features dapat direproduksi.

---

# L.76. Unit test matematis

Kita bahkan dapat membuat test:

### Return

Untuk:

$$
P=[100,101]
$$

harus:

$$
r=\ln(101/100).
$$

### Volatility

Bandingkan dengan manual calculation.

### Beta

Untuk synthetic data dengan:

$$
r_i=2r_f,
$$

model harus menghasilkan:

$$
\hat\beta\approx2.
$$

### Factor decomposition

Jika:

$$
r=Bf+\epsilon,
$$

maka residual harus memenuhi kira-kira:

$$
Cov(\epsilon,f)\approx0.
$$

---

# L.77. Synthetic data test

Sebelum menggunakan data pasar nyata, buat:

$$
r_i
=
\beta_i f+\epsilon_i
$$

dengan parameter yang kita ketahui.

Misalnya:

$$
\beta=
\begin{bmatrix}
1\\
2\\
-1\\
0.5
\end{bmatrix}.
$$

Kemudian lihat apakah engine dapat merecovery:

$$
\hat\beta
\approx
\beta.
$$

Ini jauh lebih mudah untuk debugging.

---

# L.78. Setelah data engine benar

Barulah kita dapat mengatakan:

$$
\boxed{
S_t
\text{ valid}.
}
$$

Dan dari sini kita masuk ke:

# **Tahap M — Forecasting & Factor Engine**

Di Tahap M kita akan benar-benar menurunkan:

$$
\boxed{
\hat{\boldsymbol\mu}_t
}
$$

dari factor model + momentum + volatility + residual dynamics.

Kita juga akan membangun:

$$
\boxed{
\Sigma_t
=
B_t\Sigma_{F,t}B_t^T
+
\Sigma_{\epsilon,t}
}
$$

secara matematis.

Kemudian kita dapat menjawab pertanyaan yang lebih menarik:

> **Jika BTC naik, DXY turun, Gold naik, VIX naik, dan residual SOL negatif, secara matematis berapa expected return SOL untuk satu jam berikutnya, berapa covariance antar aset, dan bagaimana informasi tersebut akhirnya mengubah koefisien $Q_{ij}$ dalam QUBO?**

Itulah jembatan langsung dari **data pasar → matematika finansial → QUBO → Hamiltonian Ising → QAOA** yang akan kita bangun pada tahap berikutnya.

