## Prompt:
8/17/2026, 10:14:34 PM

lanjut Tahap AA

## Response:
8/17/2026, 10:14:35 PM

# Tahap AA — Dataset, Asset Universe, Timeframe, dan Walk-Forward Experiment

Kita sekarang masuk ke bagian yang menurutku **sangat penting**: mengubah mathematical spine pada Tahap Z menjadi **eksperimen yang bisa direproduksi**.

Kalau Tahap Z menjawab:

> *"Apa sistem matematis kita?"*

maka Tahap AA menjawab:

> **"Data apa yang boleh dilihat model, kapan model boleh melihatnya, bagaimana data antar-pasar diselaraskan, dan bagaimana kita menguji model tanpa kebocoran informasi?"**

Saya akan cukup ketat di sini, karena kesalahan pada tahap ini dapat membuat seluruh hasil VQE/QAOA terlihat bagus padahal sebenarnya terkena **look-ahead bias**.

---

# AA.1. Prinsip dasar: waktu adalah dimensi utama

Misalkan pada waktu $t$, sistem membuat keputusan.

Kita definisikan informasi yang tersedia:

$$
\boxed{
\mathcal F_t
=
\sigma
\left(
D_\tau:\tau\leq t
\right)
}
$$

di mana:

- $D_\tau$ = seluruh data yang benar-benar tersedia pada waktu $\tau$,
- $\mathcal F_t$ = information set pada waktu $t$.

Model hanya boleh menghasilkan:

$$
\boxed{
a_t=f(\mathcal F_t)
}
$$

dan **tidak boleh** menggunakan:

$$
D_{t+\Delta t}.
$$

Jadi:

$$
\boxed{
\text{Decision at }t
\quad\Longrightarrow\quad
\text{uses information available at }t.
}
$$

Ini akan menjadi hukum utama backtest kita.

---

# AA.2. Kita tidak membuat satu dataset

Sistem kita sebenarnya membutuhkan **empat jenis data**.

### 1. Market data

$$
D_t^{market}
$$

berisi OHLCV dan order book.

### 2. Factor data

$$
D_t^{factor}
$$

berisi BTC, ETH, DXY, Gold, SPX, VIX, dan sebagainya.

### 3. Execution data

$$
D_t^{execution}
$$

berisi spread, bid/ask, depth, fill, slippage.

### 4. Portfolio state

$$
D_t^{portfolio}
$$

berisi posisi yang sedang terbuka, cash, exposure, entry, SL, TP.

Jadi:

$$
\boxed{
D_t
=
\{
D_t^{market},
D_t^{factor},
D_t^{execution},
D_t^{portfolio}
\}.
}
$$

---

# AA.3. Asset universe

Saya ingin membagi universe menjadi tiga kelompok.

## A. Target assets

Ini adalah asset yang boleh dipilih optimizer.

Misalnya crypto:

$$
\mathcal A_T^{crypto}
=
\{
SOL,XRP,ADA,DOGE,AVAX,LINK
\}.
$$

Untuk saham:

$$
\mathcal A_T^{equity}
=
\{
AAPL,MSFT,NVDA,AMZN,META
\}.
$$

---

## B. Market factors

Crypto:

$$
\mathcal A_M^{crypto}
=
\{
BTC,ETH
\}.
$$

Saham:

$$
\mathcal A_M^{equity}
=
\{
SPX,NDX
\}.
$$

---

## C. Macro factors

$$
\boxed{
\mathcal F
=
\{
DXY,Gold,VIX,US10Y
\}.
}
$$

Sehingga sistem dapat mengetahui misalnya:

$$
\text{ALT}
\leftarrow
BTC,ETH
$$

dan:

$$
\text{Equity}
\leftarrow
SPX,NDX,DXY,Gold,VIX,US10Y.
$$

---

# AA.4. Jangan mencampur crypto dan saham terlebih dahulu

Walaupun tujuan akhirnya adalah satu framework universal, eksperimen pertama sebaiknya:

$$
\boxed{
Crypto\ System
}
$$

dan:

$$
\boxed{
Equity\ System
}
$$

secara terpisah.

Alasannya sederhana.

Crypto:

$$
24/7.
$$

Saham:

$$
market\ session.
$$

Kalau langsung dicampur, kita akan memiliki masalah:

- timezone,
- market holiday,
- overnight gap,
- asynchronous information,
- different liquidity,
- different trading hours.

Jadi arsitektur sama, dataset berbeda.

---

# AA.5. Timeframe utama

Saya menyarankan:

$$
\boxed{
Decision\ timeframe=1h.
}
$$

Kenapa 1 jam?

Karena kita ingin short-term trading tetapi tidak terlalu mikro.

Jika menggunakan:

$$
1m
$$

atau:

$$
5m,
$$

market microstructure menjadi jauh lebih dominan.

Sementara:

$$
1h
$$

masih cukup cepat untuk:

- intraday,
- swing pendek,
- dynamic TP/SL,
- regime adaptation.

---

# AA.6. Multi-resolution architecture

Namun bukan berarti seluruh sistem hanya menggunakan 1h.

Kita gunakan:

$$
\boxed{
1h = decision\ layer
}
$$

dan:

$$
\boxed{
1m/5m = execution\ layer.
}
$$

Misalnya:

```text
1h data
   │
   ▼
Prediction
   │
   ▼
QUBO
   │
   ▼
Trade decision
   │
   ▼
1m data
   │
   ▼
Order execution
```

---

# AA.7. Mengapa ini penting?

Misalkan model menghasilkan:

$$
P_t=100
$$

dan ingin membeli pada:

$$
P_{entry}=99.5.
$$

Jika candle 1h memiliki:

$$
L_t=99
$$

maka kita tidak boleh langsung mengatakan:

> order pasti filled.

Karena harga bisa saja:

$$
100
\rightarrow
98.9
\rightarrow
101
$$

tanpa pernah tersedia cukup liquidity pada $99.5$.

Karena itu:

$$
\boxed{
Signal\ data\neq Execution\ data.
}
$$

---

# AA.8. Timestamp

Semua data harus mempunyai timestamp yang konsisten:

$$
t_0,t_1,\ldots,t_T.
$$

Saya menyarankan menggunakan:

$$
\boxed{
UTC
}
$$

sebagai internal canonical timezone.

Jangan menyimpan dataset internal dengan:

```text
WIB
EST
UTC
```

secara campur-aduk.

Semua dikonversi ke UTC.

---

# AA.9. Tetapi UTC bukan berarti semua pasar memiliki informasi simultan

Ini jebakan yang sangat penting.

Misalnya:

$$
t=14:00\ UTC.
$$

Data:

- crypto tersedia,
- DXY tersedia,
- Gold tersedia,
- saham AS mungkin baru saja membuka,
- data saham sebelumnya mungkin berasal dari sesi sebelumnya.

Maka kita tidak boleh hanya melakukan:

$$
merge(timestamp).
$$

Kita harus melakukan **information-time alignment**.

---

# AA.10. Market clock

Untuk setiap asset $i$, kita definisikan:

$$
\mathcal T_i
$$

sebagai himpunan timestamp ketika data asset tersebut tersedia.

Misalnya crypto:

$$
\mathcal T_{BTC}
=
\{\text{semua jam}\}.
$$

Saham:

$$
\mathcal T_{AAPL}
=
\{\text{jam trading}\}.
$$

---

# AA.11. Last Observation Carried Forward

Untuk factor yang tidak update setiap jam, kita mungkin menggunakan:

$$
f_t=f_{\tau^\star}
$$

dengan:

$$
\tau^\star
=
\max
\{\tau\leq t:\tau\in\mathcal T_f\}.
$$

Namun **LOCF tidak boleh digunakan secara buta**.

Kita juga harus menyimpan:

$$
Age_t=t-\tau^\star.
$$

Jadi model mengetahui:

$$
\boxed{
f_t,\quad Age_t.
}
$$

---

# AA.12. Contoh DXY

Misalnya:

$$
DXY_{10:00}
=
100.5.
$$

Kemudian tidak ada update sampai:

$$
DXY_{11:00}.
$$

Untuk crypto pada:

$$
10:30,
$$

kita boleh menggunakan:

$$
DXY_{10:00}
$$

jika memang data tersebut sudah tersedia.

Tetapi untuk:

$$
09:30,
$$

kita tidak boleh menggunakan:

$$
DXY_{10:00}.
$$

---

# AA.13. Publication lag

Ini lebih penting lagi untuk data makro.

Misalnya suatu economic indicator mempunyai:

$$
Observation\ Date=t
$$

tetapi baru dipublikasikan:

$$
t+\Delta_{pub}.
$$

Model hanya boleh menggunakan setelah:

$$
\boxed{
t+\Delta_{pub}.
}
$$

Secara formal:

$$
D^{available}_t
=
D^{observation}_\tau
\quad
\text{only if}
\quad
\tau+\Delta_{pub}\le t.
$$

---

# AA.14. Ini menghasilkan konsep "as-of timestamp"

Setiap observasi sebaiknya mempunyai:

$$
\boxed{
observation\_time
}
$$

dan:

$$
\boxed{
available\_time.
}
$$

Misalnya:

| Data | Observation | Available |
|---|---:|---:|
| Gold | 10:00 | 10:01 |
| DXY | 10:00 | 10:01 |
| CPI | 08:00 | 08:30 |
| AAPL close | 16:00 | 16:00+ |

Model menggunakan:

$$
available\_time.
$$

Bukan sekadar observation time.

---

# AA.15. Data structure

Saya menyarankan setiap dataset memiliki kolom:

```text
timestamp
available_at
symbol
open
high
low
close
volume
bid
ask
```

Untuk factor:

```text
timestamp
available_at
factor
value
```

---

# AA.16. Return target

Misalnya kita memprediksi return satu jam ke depan:

$$
\boxed{
y_{i,t+1}
=
\ln
\frac{P_{i,t+1}}
{P_{i,t}}.
}
$$

Untuk horizon $H$:

$$
\boxed{
y_{i,t}^{(H)}
=
\ln
\frac{P_{i,t+H}}
{P_{i,t}}.
}
$$

Jadi:

$$
H=1
$$

berarti 1 jam.

---

# AA.17. Jangan menggunakan target sebagai feature

Feature:

$$
X_t
$$

hanya menggunakan:

$$
D_{\le t}.
$$

Target:

$$
Y_t
$$

menggunakan:

$$
D_{t+H}.
$$

Secara eksplisit:

$$
\boxed{
X_t
=
f(D_{\le t})
}
$$

dan:

$$
\boxed{
Y_t
=
g(D_{t+H}).
}
$$

---

# AA.18. Feature matrix

Untuk asset $i$:

$$
X_{i,t}
=
\begin{bmatrix}
r_{i,t}\\
r_{i,t-1}\\
\vdots\\
r_{i,t-L}\\
\sigma_{i,t}\\
Volume_{i,t}\\
Momentum_{i,t}\\
Factor_t
\end{bmatrix}.
$$

Kemudian:

$$
X_t
=
[
X_{1,t},
\ldots,
X_{N,t}
].
$$

---

# AA.19. Rolling window

Misalnya:

$$
L=168.
$$

Karena:

$$
168\text{ jam}=7\text{ hari}.
$$

Maka covariance:

$$
\hat\Sigma_t
=
Cov
(
r_{t-167:t}
).
$$

Expected return:

$$
\hat\mu_t
=
Model
(
D_{t-167:t}
).
$$

---

# AA.20. Jangan selalu memakai satu window

Nanti kita uji:

$$
L\in
\{
48,72,168,336,720
\}.
$$

Yaitu kira-kira:

- 2 hari,
- 3 hari,
- 1 minggu,
- 2 minggu,
- 1 bulan.

Ini menjadi hyperparameter.

---

# AA.21. Tetapi hyperparameter tidak boleh dipilih dari test set

Misalnya kita mencoba:

$$
L=48,72,168,336.
$$

Kita pilih:

$$
L=168
$$

berdasarkan validation.

Kemudian:

$$
L=168
$$

dikunci sebelum test.

Kalau kita melihat test lalu memilih yang terbaik:

$$
\boxed{
\text{test leakage}.
}
$$

---

# AA.22. Walk-forward experiment

Sekarang kita masuk ke inti AA.

Misalkan data:

$$
2021-01-01
\rightarrow
2025-12-31.
$$

Kita buat:

$$
Train
\rightarrow
Validation
\rightarrow
Test.
$$

---

# AA.23. Expanding window

Contoh:

```text
Train:      2021 ─────── 2022
Validation:             2023 Q1
Test:                    2023 Q2

Train:      2021 ─────────── 2023 Q1
Validation:                     2023 Q2
Test:                            2023 Q3

Train:      2021 ─────────────── 2023 Q2
Validation:                         2023 Q3
Test:                                2023 Q4
```

Training semakin besar.

---

# AA.24. Rolling window

Alternatif:

```text
Train:      [──────]
Validation:        [──]
Test:              [──]

Train:             [──────]
Validation:              [──]
Test:                    [──]
```

Training window memiliki panjang tetap.

---

# AA.25. Mana yang kita gunakan?

Untuk sistem kita saya menyarankan:

### Forecast model

Rolling window.

Karena market berubah.

### Factor beta

Rolling/Exponentially weighted.

### Regime

Rolling.

### Long-term baseline

Expanding window sebagai pembanding.

Dengan demikian kita dapat membandingkan:

$$
\boxed{
Adaptability
vs
Stability.
}
$$

---

# AA.26. Contoh satu fold

Misalkan:

$$
T_{train}=720h
$$

$$
T_{validation}=168h
$$

$$
T_{test}=168h.
$$

Maka:

```text
<--------- 720h --------->
TRAIN
                         <---168h--->
                         VALIDATION
                                  <---168h--->
                                  TEST
```

Kemudian window bergeser.

---

# AA.27. Decision timestamp

Pada:

$$
t
$$

kita menjalankan:

$$
\boxed{
\mathcal F_t
\rightarrow
Model_t
\rightarrow
Optimization_t
\rightarrow
Order_t.
}
$$

Order baru boleh dianggap aktif:

$$
t_{submit}\ge t.
$$

---

# AA.28. Order expiration

Order limit tidak boleh hidup selamanya.

Kita definisikan:

$$
T_{expire}.
$$

Jika:

$$
t>T_{expire}
$$

dan order belum filled:

$$
\boxed{
Cancel.
}
$$

Misalnya:

$$
T_{expire}=3h.
$$

---

# AA.29. Mengapa ini cocok dengan desain kita sebelumnya?

Karena Tahap Z mengatakan:

> "setiap jam evaluasi apakah order masih layak."

Maka:

$$
t_0
\rightarrow
Order
$$

Jika belum filled:

$$
t_1
\rightarrow
Re-evaluate.
$$

Jika:

$$
EV_{new}<0,
$$

cancel.

---

# AA.30. State machine

Order:

$$
Pending
\rightarrow
Filled
$$

atau:

$$
Pending
\rightarrow
Cancelled.
$$

Position:

$$
Filled
\rightarrow
Open.
$$

Kemudian:

$$
Open
\rightarrow
BEP
\rightarrow
Trailing
\rightarrow
Closed.
$$

---

# AA.31. Data universe untuk crypto

Untuk eksperimen pertama, saya menyarankan:

### Core factors

$$
\boxed{
BTC,\ ETH
}
$$

### Macro

$$
\boxed{
DXY,\ Gold
}
$$

### Risk sentiment

$$
\boxed{
VIX
}
$$

### Equity market

$$
\boxed{
SPX
}
$$

Jadi:

$$
F_t=
[
r_{BTC},
r_{ETH},
r_{DXY},
r_{Gold},
r_{VIX},
r_{SPX}
].
$$

---

# AA.32. Target crypto

Jangan langsung mengambil semua altcoin.

Pilih misalnya:

$$
\boxed{
SOL,\ XRP,\ ADA,\ AVAX,\ LINK,\ DOGE
}
$$

sebagai contoh universe eksperimen.

BTC dan ETH menjadi factors, bukan target.

---

# AA.33. Kenapa BTC dan ETH tidak sekaligus menjadi target?

Untuk eksperimen awal:

$$
BTC,ETH
$$

digunakan sebagai market leadership.

Kita ingin mengetahui:

$$
\boxed{
\text{Apakah altcoin movement dapat dijelaskan oleh BTC/ETH + macro factors?}
}
$$

Baru nanti kita dapat mengizinkan BTC/ETH menjadi selectable assets.

---

# AA.34. Universe saham

Untuk eksperimen kedua:

$$
\boxed{
AAPL,MSFT,NVDA,AMZN,META,GOOGL
}
$$

dan factors:

$$
\boxed{
SPX,NDX,DXY,Gold,VIX,US10Y.
}
$$

Kita ingin melihat apakah:

$$
\text{individual stock}
$$

dapat dimodelkan melalui:

$$
\text{market}
+
\text{macro}
+
\text{sector}
+
\text{idiosyncratic signal}.
$$

---

# AA.35. Sector factor

Untuk saham, kita bahkan bisa menambahkan:

$$
XLK,\ XLF,\ XLE,\ XLV,\ldots
$$

sebagai sector factors.

Sehingga:

$$
F_t
=
[
SPX,
NDX,
DXY,
Gold,
VIX,
US10Y,
XLK,
XLF,\ldots].
$$

Ini akan membuat factor model jauh lebih ekonomis.

---

# AA.36. Cross-market lag

Ini bagian yang menarik.

Kita tidak hanya menggunakan:

$$
F_t.
$$

Kita gunakan:

$$
F_t,
F_{t-1},
F_{t-2},
\ldots.
$$

Misalnya:

$$
X_t^{factor}
=
[
r_{BTC,t},
r_{BTC,t-1},
r_{BTC,t-2},
r_{ETH,t},
\ldots
].
$$

Karena pengaruh factor mungkin tidak instantaneous.

---

# AA.37. Distributed lag model

Misalnya:

$$
r_{i,t+1}
=
\alpha_i
+
\sum_{k=0}^{K}
\beta_{i,k}F_{t-k}
+
\epsilon_{i,t+1}.
$$

Ini sangat menarik secara finansial.

Karena kita dapat mengetahui apakah:

$$
BTC_t
$$

mempengaruhi altcoin:

$$
t+1,
t+2,
\ldots
$$

bukan hanya correlation contemporaneous.

---

# AA.38. Ini bisa menjadi sumber signal

Misalnya hasil estimasi:

$$
\beta_{SOL,BTC,1}>0.
$$

Artinya secara statistik:

$$
BTC_{t}
$$

mempunyai hubungan dengan:

$$
SOL_{t+1}.
$$

Tetapi kita harus hati-hati membedakan:

$$
correlation
$$

dengan:

$$
causality.
$$

Kita tidak perlu menyebutnya causal tanpa pengujian yang tepat.

---

# AA.39. Factor momentum

Kita juga dapat mendefinisikan:

$$
M_{BTC,t}^{(H)}
=
\sum_{k=0}^{H-1}
r_{BTC,t-k}.
$$

Demikian:

$$
M_{ETH,t}^{(H)}.
$$

Untuk DXY:

$$
M_{DXY,t}^{(H)}.
$$

Gold:

$$
M_{Gold,t}^{(H)}.
$$

---

# AA.40. Relative factor flow

Kita bisa membangun:

$$
Flow_t
=
w_1r_{BTC,t}
+
w_2r_{ETH,t}
-
w_3r_{DXY,t}
+
w_4r_{Gold,t}.
$$

Namun saya tidak ingin kita menentukan $w_i$ secara manual.

Kita biarkan:

$$
\boxed{
w^\star
=
\arg\min_w
Loss(w)
}
$$

di training set.

---

# AA.41. Bahkan kita dapat menggunakan PCA

Misalkan:

$$
F_t\in\mathbb R^K.
$$

Covariance:

$$
\Sigma_F.
$$

Eigenproblem:

$$
\Sigma_Fv_j
=
\lambda_jv_j.
$$

Kemudian:

$$
PC_j
=
v_j^\top F_t.
$$

Ini dapat mengurangi dimensionality.

---

# AA.42. Namun untuk versi pertama jangan gunakan PCA sebagai default

Kenapa?

Karena interpretasi:

$$
BTC
\rightarrow
SOL
$$

lebih jelas daripada:

$$
PC_1
\rightarrow
SOL.
$$

Kita ingin menjaga interpretability terlebih dahulu.

---

# AA.43. Feature groups

Saya ingin setiap feature diberi label:

```text
PRICE
VOLUME
VOLATILITY
FACTOR
MOMENTUM
REGIME
ORDERFLOW
```

Dengan demikian nanti kita dapat melakukan:

$$
Ablation\ Study.
$$

---

# AA.44. Ablation study

Misalnya:

### Model A

$$
Price
$$

### Model B

$$
Price+Factor
$$

### Model C

$$
Price+Factor+Regime
$$

### Model D

$$
Price+Factor+Regime+OrderFlow
$$

Kemudian lihat:

$$
\Delta Sharpe.
$$

Ini sangat penting untuk mengetahui apakah kompleksitas benar-benar memberikan nilai.

---

# AA.45. Dataset final

Secara konseptual satu baris:

$$
\boxed{
Row_t
=
[
X_t,
F_t,
Regime_t,
Position_t,
Y_{t+1}
].
}
$$

Tetapi ketika training:

$$
Position_t
$$

harus berasal dari state sebelumnya.

Dan:

$$
Y_{t+1}
$$

tidak boleh tersedia sebagai input.

---

# AA.46. Train/validation/test harus benar-benar temporal

Bukan:

```python
train_test_split(..., shuffle=True)
```

karena itu menghancurkan struktur waktu.

Kita harus:

$$
\boxed{
t_{train}<t_{validation}<t_{test}.
}
$$

---

# AA.47. Purging

Karena target kita menggunakan horizon:

$$
H.
$$

Misalnya:

$$
Y_t=P_{t+1}/P_t.
$$

Observasi di dekat boundary dapat overlap.

Maka kita perlu:

$$
\boxed{
purge\ period\ge H.
}
$$

Misalnya:

```text
TRAIN | purge | VALIDATION
```

untuk menghindari overlapping labels.

---

# AA.48. Embargo

Selain purge, kita bisa menggunakan:

$$
\boxed{
embargo.
}
$$

Artinya setelah validation/test boundary, kita memberikan gap tertentu sebelum data berikutnya digunakan.

Ini berguna terutama jika label overlap dan data sangat autocorrelated.

---

# AA.49. Data leakage checklist

Sebelum model dianggap valid:

### Leakage 1

Scaler menggunakan seluruh data.

❌

### Leakage 2

Covariance dihitung dari masa depan.

❌

### Leakage 3

Hyperparameter dipilih berdasarkan test.

❌

### Leakage 4

Order fill menggunakan future low/high tanpa execution model.

❌

### Leakage 5

Survivorship bias.

❌

### Leakage 6

Delisted stock dihilangkan.

❌

### Leakage 7

Corporate action tidak disesuaikan.

❌

### Leakage 8

Macro data menggunakan revision terakhir.

❌

---

# AA.50. Revision bias

Untuk data ekonomi, ada masalah:

$$
Data_{initial}
\neq
Data_{revised}.
$$

Jika kita menggunakan dataset hari ini:

$$
GDP_{2021}
$$

yang telah mengalami revisi berkali-kali, kita mungkin memberikan model informasi yang pada 2021 belum diketahui.

Idealnya:

$$
\boxed{
point\text{-}in\text{-}time\ data.
}
$$

---

# AA.51. Survivorship bias

Misalkan tahun 2021 kita memilih hanya saham yang masih ada pada 2026.

Maka:

$$
Universe_{2021}
$$

sudah mengandung informasi masa depan.

Salah.

Universe harus dibentuk berdasarkan:

$$
available\ universe_t.
$$

---

# AA.52. Delisting

Jika asset delisting:

$$
P_t\rightarrow0
$$

atau memiliki liquidation event, data tersebut tidak boleh sekadar dihapus.

Karena:

$$
\text{removing losers}
$$

akan membuat performance terlihat terlalu bagus.

---

# AA.53. Crypto memiliki masalah berbeda

Crypto tidak terlalu terkena:

$$
market\ close.
$$

Tetapi memiliki:

- listing/delisting,
- exchange-specific liquidity,
- perpetual funding,
- different trading pairs,
- symbol changes.

Jadi universe juga harus memiliki:

$$
listing_t
$$

dan:

$$
delisting_t.
$$

---

# AA.54. Exchange-specific data

Ini sangat penting untuk sistem live nanti.

Harga:

$$
P_{BTC}^{Binance}
\neq
P_{BTC}^{Coinbase}
$$

secara tepat pada setiap waktu.

Maka jangan menggabungkan:

```text
price dari exchange A
order book exchange B
volume exchange C
```

tanpa model yang jelas.

---

# AA.55. Untuk backtest awal

Saya menyarankan:

$$
\boxed{
one\ venue.
}
$$

Misalnya satu exchange untuk crypto.

Kemudian:

$$
P_t,\ Volume_t,\ OrderBook_t
$$

berasal dari venue yang sama.

---

# AA.56. Untuk saham

Gunakan satu sumber consolidated market data untuk baseline.

Kemudian baru nanti kita tambahkan:

$$
market\ microstructure.
$$

---

# AA.57. Data frequency

Untuk decision:

$$
1h.
$$

Untuk execution:

$$
1m.
$$

Untuk order book:

$$
tick/depth
$$

jika tersedia.

Jadi hierarchy:

$$
\boxed{
Tick
\rightarrow
1m
\rightarrow
1h
\rightarrow
Daily.
}
$$

---

# AA.58. Aggregation

Misalnya data 1m:

$$
\{P_{t,1},P_{t,2},...,P_{t,60}\}
$$

menjadi:

$$
O_t=P_{t,1}
$$

$$
H_t=\max_jP_{t,j}
$$

$$
L_t=\min_jP_{t,j}
$$

$$
C_t=P_{t,60}.
$$

Volume:

$$
V_t=\sum_jV_{t,j}.
$$

---

# AA.59. Order book features

Jika tersedia:

Bid:

$$
B_t
$$

Ask:

$$
A_t.
$$

Spread:

$$
\boxed{
S_t=A_t-B_t.
}
$$

Mid-price:

$$
\boxed{
M_t=\frac{A_t+B_t}{2}.
}
$$

---

# AA.60. Order book imbalance

Dengan depth $K$:

$$
I_t
=
\frac{
\sum_{k=1}^{K}Q_{B,k}
-
\sum_{k=1}^{K}Q_{A,k}
}{
\sum_{k=1}^{K}Q_{B,k}
+
\sum_{k=1}^{K}Q_{A,k}
}.
$$

Sehingga:

$$
-1\le I_t\le1.
$$

Ini dapat menjadi feature:

$$
X_t^{OB}.
$$

---

# AA.61. Tetapi jangan memasukkan order book ke model 1h secara mentah

Order book sangat noisy.

Lebih baik agregasikan:

$$
I_t^{1h}
=
Mean(I_{t,\tau})
$$

atau:

$$
Median(I_{t,\tau}).
$$

Bisa juga menggunakan:

$$
quantile.
$$

---

# AA.62. Liquidity feature

Misalnya:

$$
ADV_t
=
\frac1L
\sum_{\tau=t-L}^{t}
DollarVolume_\tau.
$$

Kemudian:

$$
LiquidityScore_i
=
f(ADV_i,Spread_i,Depth_i).
$$

---

# AA.63. Optimizer harus melihat liquidity

Kita dapat menambahkan:

$$
x_i=0
$$

jika:

$$
LiquidityScore_i<L_{min}.
$$

Atau penalty:

$$
P_L
\sum_i
(1-L_i)x_i.
$$

---

# AA.64. Slippage model

Versi pertama:

$$
Slippage_i
=
\alpha
\frac{Spread_i}{2}
+
\beta
\frac{OrderSize_i}{Depth_i}.
$$

Kemudian:

$$
Cost_i
=
Fee_i+Slippage_i.
$$

Nanti kita dapat mengganti dengan model empiris.

---

# AA.65. Ini masuk ke QUBO

Jika asset $i$ memiliki expected net return:

$$
\mu_i^{net}
=
\mu_i
-
Cost_i.
$$

Maka QUBO menggunakan:

$$
\boxed{
-\mu_i^{net}x_i.
}
$$

Jadi optimizer tidak mengoptimalkan:

$$
Gross\ Return
$$

tetapi:

$$
\boxed{
Net\ Expected\ Return.
}
$$

---

# AA.66. Bahkan covariance dapat disesuaikan

Jika execution uncertainty besar:

$$
\Sigma_{effective}
=
\Sigma_{market}
+
\Sigma_{execution}.
$$

Kemudian:

$$
H(x)
=
-\mu^\top x
+
\lambda x^\top
\Sigma_{effective}
x.
$$

Ini lebih konservatif.

---

# AA.67. Struktur satu decision cycle

Sekarang semuanya bisa kita satukan.

Pada:

$$
t.
$$

### Step 1

Ambil:

$$
D_{\le t}.
$$

### Step 2

Bangun:

$$
X_t.
$$

### Step 3

Update factor:

$$
F_t.
$$

### Step 4

Estimate regime:

$$
z_t.
$$

### Step 5

Estimate:

$$
\hat\mu_t,\hat\Sigma_t.
$$

### Step 6

Build:

$$
H_t(x).
$$

### Step 7

Solve:

$$
x_t^\star.
$$

### Step 8

Allocation:

$$
w_t^\star.
$$

### Step 9

Risk sizing:

$$
q_t^\star.
$$

### Step 10

Generate:

$$
O_t.
$$

### Step 11

Execute.

### Step 12

Update:

$$
State_{t+1}.
$$

---

# AA.68. Formal recursive system

Kita bisa menuliskannya:

$$
\boxed{
S_{t+1}
=
\mathcal T
\left(
S_t,
D_t,
a_t
\right)
}
$$

dengan action:

$$
\boxed{
a_t
=
\pi(\mathcal F_t).
}
$$

Policy kita sebenarnya adalah:

$$
\boxed{
\pi
=
\pi_{execution}
\circ
\pi_{risk}
\circ
\pi_{allocation}
\circ
\pi_{optimization}
\circ
\pi_{forecast}.
}
$$

Ini mulai terlihat seperti **closed-loop stochastic control system**.

---

# AA.69. Dan di sinilah desain kita menjadi menarik

Sistem kita bukan:

$$
Prediction\rightarrow Buy.
$$

Tetapi:

$$
\boxed{
Prediction
\rightarrow
Optimization
\rightarrow
Risk
\rightarrow
Execution
\rightarrow
State
\rightarrow
Prediction.
}
$$

Jadi keputusan hari ini mengubah:

$$
S_{t+1},
$$

yang kemudian mempengaruhi keputusan berikutnya.

---

# AA.70. Eksperimen pertama yang saya rekomendasikan

Kita jangan langsung membuat model besar.

Saya ingin **Experiment AA-1** menjadi sangat sederhana tetapi scientifically clean.

### Universe

$$
\boxed{
SOL,\ XRP,\ ADA,\ AVAX,\ LINK,\ DOGE
}
$$

### Factors

$$
\boxed{
BTC,\ ETH,\ DXY,\ Gold,\ SPX,\ VIX
}
$$

### Timeframe

$$
\boxed{
1h
}
$$

### Forecast horizon

$$
\boxed{
H=1h
}
$$

### Rolling window

$$
\boxed{
L=168h
}
$$

### Regime

3-state.

### Optimizer

Exact QUBO.

### Execution

1m historical simulation.

### Risk

Fixed:

$$
R_{trade}= \$1.
$$

---

# AA.71. Mengapa mulai dari Exact QUBO?

Karena kita ingin memisahkan dua pertanyaan.

Pertanyaan pertama:

> **Apakah mathematical trading problem kita sendiri menghasilkan keputusan yang bagus?**

Kita jawab menggunakan:

$$
Exact\ Solver.
$$

Pertanyaan kedua:

> **Apakah VQE/QAOA mampu menyelesaikan problem tersebut?**

Baru kemudian:

$$
Exact
\leftrightarrow
VQE
\leftrightarrow
QAOA.
$$

Ini sangat penting untuk penelitian quantum.

---

# AA.72. Experiment AA-2

Setelah AA-1:

$$
Exact
$$

kita lakukan:

$$
Classical\ QUBO.
$$

Misalnya:

$$
Simulated\ Annealing
$$

atau solver classical lainnya.

---

# AA.73. Experiment AA-3

Kemudian:

$$
VQE.
$$

Ukur:

$$
Gap_{VQE}
$$

terhadap:

$$
E^\star.
$$

---

# AA.74. Experiment AA-4

Kemudian:

$$
QAOA.
$$

Ukur:

$$
Gap_{QAOA}.
$$

---

# AA.75. Experiment AA-5

Baru kita masukkan:

$$
Execution\ cost.
$$

Bandingkan:

$$
Gross
$$

vs:

$$
Net.
$$

---

# AA.76. Experiment AA-6

Kemudian:

$$
Crypto
$$

vs:

$$
Equity.
$$

Framework yang sama:

$$
\boxed{
\text{different market data}.
}
$$

---

# AA.77. Experiment AA-7

Kemudian stress test:

$$
Bull
$$

$$
Bear
$$

$$
High\ Volatility
$$

$$
Low\ Liquidity
$$

$$
Market\ Crash.
$$

Kita ingin melihat:

$$
Performance(z).
$$

---

# AA.78. Experiment AA-8

Terakhir:

$$
Ablation.
$$

Bandingkan:

$$
Price
$$

vs:

$$
Price+Factor
$$

vs:

$$
Price+Factor+Regime
$$

vs:

$$
Price+Factor+Regime+OrderBook.
$$

---

# AA.79. Output yang harus kita simpan

Setiap decision timestamp harus menghasilkan log:

```text
timestamp
regime
mu
covariance
qubo_matrix
ising_h
ising_J
solver
solution
objective
feasibility
weights
quantity
entry
stop_loss
take_profit
expected_return
expected_risk
spread
slippage
fill_status
realized_pnl
```

Ini penting.

Karena nanti kita bisa menjawab:

> "Mengapa trade pada 2026-05-13 pukul 10:00 dilakukan?"

Secara matematis.

---

# AA.80. Kita bahkan bisa merekonstruksi setiap keputusan

Misalnya:

$$
t=10:00.
$$

Model melihat:

$$
BTC=-0.8\sigma
$$

$$
ETH=-0.5\sigma
$$

$$
DXY=+0.7\sigma
$$

$$
Gold=+0.2\sigma
$$

dan:

$$
Regime=Stress.
$$

Kemudian:

$$
\hat\mu_{SOL}=-0.1\%
$$

$$
\hat\mu_{XRP}=+0.4\%.
$$

Optimizer kemudian memilih:

$$
x^\star=
[0,1,0,1,0,0].
$$

Kita dapat mengetahui **seluruh rantai sebab-akibat komputasionalnya**.

---

# AA.81. Dan inilah yang nantinya sangat berguna untuk skripsi/riset

Kita bisa menunjukkan:

$$
\boxed{
Market\ Information
\rightarrow
Mathematical\ Formulation
\rightarrow
Quantum\ Optimization
\rightarrow
Trading\ Decision.
}
$$

Bukan hanya:

> "VQE menghasilkan portfolio."

---

# AA.82. Spesifikasi AA final

Jadi untuk saat ini saya ingin kita **mengunci** konfigurasi baseline:

$$
\boxed{
\begin{array}{ll}
\text{Decision} & 1h\\
\text{Execution} & 1m\\
\text{Crypto Targets} & SOL,XRP,ADA,AVAX,LINK,DOGE\\
\text{Crypto Factors} & BTC,ETH\\
\text{Macro Factors} & DXY,Gold,SPX,VIX\\
\text{Forecast Horizon} & 1h\\
\text{Rolling Window} & 168h\\
\text{Regime States} & 3\\
\text{Risk/trade} & \$1\\
\text{Optimization} & QUBO\\
\text{Initial Solver} & Exact\\
\text{Validation} & Walk-forward\\
\text{Execution} & realistic\\
\text{Timezone} & UTC
\end{array}
}
$$

Ini **bukan berarti angka-angka tersebut final selamanya**. Mereka adalah baseline yang kita gunakan agar eksperimen pertama memiliki definisi yang jelas.

---

# AA.83. Hal yang paling penting dari Tahap AA

Ada satu perubahan konseptual yang ingin saya tekankan.

Sebelumnya kita berpikir:

$$
\boxed{
Data\rightarrow Model.
}
$$

Sekarang kita harus berpikir:

$$
\boxed{
Data
\rightarrow
Information\ Set
\rightarrow
Model
\rightarrow
Decision
\rightarrow
Execution
\rightarrow
Observed\ Outcome.
}
$$

Dengan kata lain, **timestamp adalah bagian dari matematika model**, bukan sekadar metadata dataset.

Dan untuk sistem quantitative trading yang ingin kita bangun, itu mungkin sama pentingnya dengan QUBO, VQE, atau QAOA itu sendiri.

---

## Tahap berikutnya: AB

Setelah AA, saya menyarankan kita masuk ke:

# **Tahap AB — Mathematical Feature & Factor Engine**

Di sana kita mulai benar-benar **menurunkan setiap feature dari data mentah**, bukan sekadar menyebut nama indikator.

Kita akan membangun secara matematis:

$$
\boxed{
OHLCV
\rightarrow
returns
\rightarrow
volatility
\rightarrow
momentum
\rightarrow
cross\text{-}asset\ dependence
\rightarrow
factor\ exposure
\rightarrow
orderflow
\rightarrow
feature\ vector
}
$$

lalu menurunkan **factor model untuk crypto dan saham secara terpadu**, termasuk:

$$
r_{i,t+1}
=
\alpha_i+
B_iF_t+
\sum_{k=1}^{K}B_{i,k}F_{t-k}
+\epsilon_{i,t+1},
$$

estimasi $\beta$ rolling, covariance factor model, shrinkage, cross-asset lag, dan akhirnya bagaimana semua itu masuk ke:

$$
\boxed{
\hat\mu_t,\hat\Sigma_t
}
$$

yang kemudian menjadi input langsung ke **QUBO/Ising** kita.

