## Prompt:
8/17/2026, 9:26:47 PM

hebat sekali. kita sudah merancang kerangka utama yang luar biasa. sekarang bisakah kita melanjutkan untuk membangun sistemnya tahap demi tahap? jika kau siap, mari kita mulai dari Tahap A dengan sangat detail. jika perlu, tambahkan penurunan matematis lengkap agar pendasarannya lebih dapat dibuktikan secara matematis namun tetap dengan pertimbangan paradigma finansial yang masuk akal

## Response:
8/17/2026, 9:26:48 PM

> **Remembering**
>
>
> ****
>
> 
>
> **Reviewed Tahap A market-state design and cross-asset factor framework**
>
> 
>
> Worked for 5s

Sangat siap. Dan untuk **Tahap A**, saya justru menyarankan kita bergerak pelan dan cukup rigor, karena seluruh tahap berikutnya—forecast, covariance, QUBO, Ising, sampai QAOA—akan bergantung pada definisi *market state* yang kita buat di sini.

Kita akan membangun Tahap A bukan sebagai sekadar kumpulan indikator, tetapi sebagai **representasi matematis keadaan pasar yang tersedia pada waktu $t$**.

---

# Tahap A — Market State Representation

Tujuan akhirnya adalah memperoleh:

$$
\boxed{
s_t
=
\text{representasi matematis seluruh informasi pasar yang tersedia pada waktu }t
}
$$

yang kemudian menjadi input untuk Tahap B:

$$
s_t
\longrightarrow
\{\boldsymbol{\mu}_t,\Sigma_t,B_t,\text{regime}_t,\ldots\}.
$$

Ada prinsip fundamental yang harus kita pegang:

$$
\boxed{
s_t\text{ hanya boleh mengandung informasi yang tersedia pada atau sebelum }t
}
$$

Ini akan menjadi fondasi untuk mencegah **look-ahead bias**.

---

# A.1. Apa sebenarnya "state" dalam sistem kita?

Misalkan terdapat universe aset:

$$
\mathcal A
=
\{A_1,A_2,\ldots,A_N\}.
$$

Contohnya:

$$
\mathcal A_{\mathrm{crypto}}
=
\{\mathrm{BTC},\mathrm{ETH},\mathrm{SOL},\mathrm{BNB},\ldots\}
$$

atau:

$$
\mathcal A_{\mathrm{equity}}
=
\{\mathrm{NVDA},\mathrm{AAPL},\mathrm{MSFT},\ldots\}.
$$

Kita juga memiliki sekumpulan market factor:

$$
\mathcal F
=
\{F_1,F_2,\ldots,F_K\}.
$$

Misalnya:

$$
\mathcal F_{\mathrm{global}}
=
\{
\mathrm{SPX},
\mathrm{NDX},
\mathrm{GOLD},
\mathrm{USD},
\mathrm{OIL},
\mathrm{VIX},
\ldots
\}.
$$

Untuk crypto:

$$
\mathcal F_{\mathrm{crypto}}
=
\{
\mathrm{BTC},
\mathrm{ETH},
\mathrm{USD},
\ldots
\}.
$$

Tetapi kita harus berhati-hati.

**BTC sendiri dapat menjadi target asset maupun factor.**

Jika kita trading SOL, BTC dapat menjadi factor.

Jika kita trading BTC, BTC tidak boleh sekaligus digunakan sebagai explanatory factor untuk dirinya sendiri.

---

# A.2. Market state bukan hanya harga

Kesalahan yang sering terjadi pada sistem trading sederhana adalah mendefinisikan:

$$
s_t=P_t.
$$

Ini terlalu miskin.

Harga hanya memberi tahu:

> "di mana pasar berada."

Padahal kita juga membutuhkan:

- bagaimana pasar bergerak,
- seberapa cepat bergerak,
- seberapa volatil,
- seberapa likuid,
- bagaimana aset lain bergerak,
- bagaimana factor bergerak,
- bagaimana hubungan antar-aset berubah,
- bagaimana order book tersusun.

Karena itu saya ingin mendefinisikan state sebagai:

$$
\boxed{
s_t=
\left[
X_t,
F_t,
V_t,
C_t,
M_t,
O_t,
L_t,
R_t
\right]
}
$$

dengan:

| Komponen | Makna |
|---|---|
| $X_t$ | price/return state |
| $F_t$ | market-factor state |
| $V_t$ | volatility state |
| $C_t$ | cross-asset dependence |
| $M_t$ | market/microstructure state |
| $O_t$ | order-book state |
| $L_t$ | liquidity state |
| $R_t$ | current portfolio/risk state |

Kita akan turunkan satu per satu.

---

# A.3. Layer pertama: price state

Untuk aset $i$, kita mempunyai:

$$
P_{i,t}
$$

yang merupakan harga pada waktu $t$.

Namun **harga absolut bukan representasi yang baik untuk membandingkan aset yang berbeda**.

Misalnya:

$$
P_{\mathrm{BTC}}=100000
$$

dan:

$$
P_{\mathrm{SOL}}=200.
$$

Angka tersebut tidak dapat dibandingkan secara langsung.

Karena itu kita bekerja dengan return.

---

## A.3.1. Simple return

Definisikan:

$$
\boxed{
r_{i,t}
=
\frac{P_{i,t}-P_{i,t-1}}
{P_{i,t-1}}
}
$$

atau:

$$
r_{i,t}
=
\frac{P_{i,t}}{P_{i,t-1}}-1.
$$

Misalnya:

$$
P_{t-1}=100
$$

dan:

$$
P_t=102.
$$

Maka:

$$
r_t=0.02=2\%.
$$

Return adalah representasi yang lebih tepat karena bersifat relatif terhadap harga sebelumnya.

---

# A.3.2. Log return

Untuk beberapa operasi matematis kita juga akan menggunakan:

$$
\boxed{
\ell_{i,t}
=
\ln\frac{P_{i,t}}{P_{i,t-1}}
}
$$

Perhatikan:

$$
1+r_{i,t}
=
\frac{P_{i,t}}{P_{i,t-1}}
$$

sehingga:

$$
\ell_{i,t}
=
\ln(1+r_{i,t}).
$$

Untuk return kecil:

$$
\ln(1+r)
\approx r.
$$

Namun jangan menganggap keduanya identik.

Untuk holding multi-period:

$$
\frac{P_T}{P_0}
=
\prod_{t=1}^{T}(1+r_t),
$$

sehingga:

$$
\ln\frac{P_T}{P_0}
=
\sum_{t=1}^{T}\ell_t.
$$

Inilah salah satu alasan log-return sangat berguna untuk pemodelan temporal.

---

# A.4. Multi-horizon state

Karena sistem kita adalah **short-horizon trading**, satu return saja tidak cukup.

Kita dapat membentuk:

$$
r_{i,t}^{(\Delta)}
=
\frac{P_{i,t}}{P_{i,t-\Delta}}-1.
$$

Misalnya:

$$
\Delta\in
\{1,5,15,60,240\}
$$

menit, tergantung resolusi data.

Maka state harga dapat memuat:

$$
X_{i,t}
=
\left[
r_{i,t}^{(1)},
r_{i,t}^{(5)},
r_{i,t}^{(15)},
r_{i,t}^{(60)},
r_{i,t}^{(240)}
\right].
$$

Interpretasinya:

- 1 menit → micro-momentum,
- 5 menit → very short-term momentum,
- 15 menit → intraday momentum,
- 1 jam → short-term trend,
- 4 jam → broader local regime.

Ini lebih baik daripada memilih satu timeframe secara arbitrer.

---

# A.5. Layer kedua: market factor state

Sekarang kita masuk ke inti desain global.

Misalkan terdapat $K$ factors:

$$
\mathbf f_t
=
\begin{bmatrix}
f_{1,t}\\
f_{2,t}\\
\vdots\\
f_{K,t}
\end{bmatrix}.
$$

Kita tidak menggunakan harga factor secara langsung.

Kita juga mengubahnya menjadi return:

$$
\boxed{
\mathbf r_t^F
=
\begin{bmatrix}
r_{F_1,t}\\
r_{F_2,t}\\
\vdots\\
r_{F_K,t}
\end{bmatrix}
}
$$

---

# A.6. Contoh factor universe global

Untuk versi pertama sistem, saya menyarankan struktur konseptual seperti ini.

### Equity factors

$$
F_E=
\{
\mathrm{SPX},
\mathrm{NDX},
\mathrm{STOXX},
\mathrm{NIKKEI},
\mathrm{IHSG}
\}.
$$

### Macro factors

$$
F_M=
\{
\mathrm{GOLD},
\mathrm{USD},
\mathrm{OIL}
\}.
$$

### Risk factors

$$
F_R=
\{
\mathrm{VIX},
\text{rates}
\}.
$$

### Crypto factors

$$
F_C=
\{
\mathrm{BTC},
\mathrm{ETH}
\}.
$$

Sehingga:

$$
\boxed{
F=
F_E\cup F_M\cup F_R\cup F_C
}
$$

Tetapi **tidak semua factor digunakan untuk setiap aset**.

Itu penting.

---

# A.7. Contoh: target NVDA

Untuk NVDA kita mungkin mempunyai:

$$
\mathbf f_t^{(\mathrm{NVDA})}
=
\begin{bmatrix}
r_{\mathrm{SPX},t}\\
r_{\mathrm{NDX},t}\\
r_{\mathrm{GOLD},t}\\
r_{\mathrm{USD},t}\\
r_{\mathrm{VIX},t}
\end{bmatrix}.
$$

Sedangkan untuk SOL:

$$
\mathbf f_t^{(\mathrm{SOL})}
=
\begin{bmatrix}
r_{\mathrm{BTC},t}\\
r_{\mathrm{ETH},t}\\
r_{\mathrm{SPX},t}\\
r_{\mathrm{USD},t}\\
r_{\mathrm{VIX},t}
\end{bmatrix}.
$$

Dengan demikian model menjadi **asset-conditional**.

---

# A.8. Mengapa factor harus berupa return?

Misalkan:

$$
P_{\mathrm{Gold}}=2500.
$$

Nilai:

$$
2500
$$

sendiri hampir tidak memberikan informasi yang berguna mengenai *shock* pasar.

Yang lebih informatif:

$$
r_{\mathrm{Gold},t}
=
\frac{P_t-P_{t-1}}{P_{t-1}}.
$$

Kemudian kita bisa membandingkan:

$$
r_{\mathrm{Gold}}
$$

dengan:

$$
r_{\mathrm{NVDA}},
$$

tanpa masalah skala harga.

---

# A.9. Gold sebagai macro factor

Kita definisikan:

$$
g_t
=
\ln
\frac{P_{\mathrm{Gold},t}}
{P_{\mathrm{Gold},t-1}}.
$$

Kemudian gold state bukan hanya:

$$
g_t.
$$

Kita bisa memiliki:

$$
G_t=
[
g_t^{(1)},
g_t^{(5)},
g_t^{(15)},
g_t^{(60)},
\sigma_{\mathrm{Gold},t}
].
$$

Dengan demikian sistem dapat mengetahui:

> apakah gold sedang naik, seberapa cepat, dan dalam kondisi volatilitas seperti apa.

---

# A.10. USD factor

Untuk USD kita perlu sedikit lebih hati-hati.

Daripada mengunci model pada satu instrumen tertentu, kita mendefinisikan abstraksi:

$$
D_t=\text{USD factor}.
$$

Kemudian:

$$
d_t
=
\ln
\frac{D_t}{D_{t-1}}.
$$

State-nya:

$$
D_t^{state}
=
[
d_t^{(1)},
d_t^{(5)},
d_t^{(15)},
d_t^{(60)},
\sigma_{\mathrm{USD},t}
].
$$

Dengan demikian implementasi di kemudian hari dapat memilih instrumen representatif USD yang konsisten.

Ini penting untuk membuat sistem **asset-agnostic**.

---

# A.11. Jangan langsung menyebutnya "money flow"

Ini adalah satu perubahan istilah yang menurutku penting.

Misalnya:

$$
r_{\mathrm{BTC}}>0
$$

dan:

$$
r_{\mathrm{SOL}}>0.
$$

Kita tidak boleh menyimpulkan:

> "uang mengalir dari BTC ke SOL."

Harga tidak secara langsung memberi kita observasi arus uang.

Lebih aman secara matematis menyebutnya:

$$
\boxed{
\text{cross-asset transmission}
}
$$

atau:

$$
\boxed{
\text{cross-asset dependency}
}
$$

Kemudian jika kita memiliki volume, order flow, atau flow data yang relevan, barulah kita dapat membangun konsep flow yang lebih eksplisit.

---

# A.12. Layer ketiga: volatility state

Return:

$$
r_{i,t}
$$

belum memberi tahu kita seberapa tidak stabil aset tersebut.

Kita membutuhkan:

$$
\sigma_{i,t}.
$$

Estimator paling sederhana:

$$
\boxed{
\hat\sigma_{i,t}^2
=
\frac{1}{W-1}
\sum_{k=0}^{W-1}
(r_{i,t-k}-\bar r_{i,t})^2
}
$$

dengan:

$$
\bar r_{i,t}
=
\frac1W
\sum_{k=0}^{W-1}r_{i,t-k}.
$$

---

# A.13. Mengapa volatility harus conditional?

Karena:

$$
\sigma_t
\neq
\sigma_{t+1}.
$$

Market memiliki volatility clustering.

Secara sederhana:

$$
|\!r_t\!|\text{ besar}
\Rightarrow
P(|r_{t+1}|\text{ besar})\text{ meningkat}.
$$

Kita tidak perlu langsung menggunakan GARCH pada Tahap A.

Yang penting adalah kita mendefinisikan:

$$
\boxed{
\sigma_{i,t}
=
\text{state variable}
}
$$

yang nanti dapat digunakan untuk:

- position sizing,
- SL,
- TP,
- risk,
- forecast uncertainty.

---

# A.14. Volatility relatif juga penting

Misalnya:

$$
\sigma_{\mathrm{SOL}}=4\%
$$

dan:

$$
\sigma_{\mathrm{BTC}}=1.5\%.
$$

Kita dapat membentuk:

$$
VR_t
=
\frac{\sigma_{\mathrm{SOL},t}}
{\sigma_{\mathrm{BTC},t}}.
$$

Jika:

$$
VR_t\gg1,
$$

SOL sedang jauh lebih volatile daripada BTC.

Ini dapat menjadi informasi regime.

---

# A.15. Layer keempat: cross-asset dependence

Sekarang kita kembali ke ide awalmu tentang BTC, ETH, gold, USD, dan sebagainya.

Untuk dua return:

$$
r_i,r_j,
$$

covariance:

$$
\boxed{
\operatorname{Cov}(r_i,r_j)
=
E[
(r_i-\mu_i)(r_j-\mu_j)
]
}
$$

dan correlation:

$$
\boxed{
\rho_{ij}
=
\frac{\operatorname{Cov}(r_i,r_j)}
{\sigma_i\sigma_j}
}
$$

Namun kita tidak ingin:

$$
\rho_{ij}
$$

yang statis.

Kita ingin:

$$
\boxed{
\rho_{ij,t}
}
$$

menggunakan rolling window.

---

# A.16. Rolling covariance matrix

Untuk $N$ aset:

$$
\mathbf r_t
=
\begin{bmatrix}
r_{1,t}\\
\vdots\\
r_{N,t}
\end{bmatrix}.
$$

Dengan window $W$:

$$
\boxed{
\hat\Sigma_t
=
\frac{1}{W-1}
\sum_{k=0}^{W-1}
(\mathbf r_{t-k}-\bar{\mathbf r}_t)
(\mathbf r_{t-k}-\bar{\mathbf r}_t)^T
}
$$

Perhatikan bentuknya:

$$
\mathbf r\mathbf r^T
$$

menghasilkan matrix.

Karena itu:

$$
\Sigma_t
=
\begin{pmatrix}
\sigma_1^2 & \sigma_{12}&\cdots\\
\sigma_{21}&\sigma_2^2&\cdots\\
\vdots&\vdots&\ddots
\end{pmatrix}.
$$

Ini adalah jembatan langsung menuju Markowitz yang sudah kamu kuasai.

---

# A.17. Tetapi correlation saja belum cukup

Misalnya:

$$
\rho_{\mathrm{BTC,SOL}}=0.8.
$$

Kita tahu hubungan linear kuat.

Tetapi kita belum tahu:

> Apakah SOL mengikuti BTC secara nonlinear?

Karena itu nantinya kita dapat memperluas dependency state menggunakan:

$$
I(X;Y)
$$

yaitu mutual information.

Secara definisi:

$$
\boxed{
I(X;Y)
=
\sum_{x,y}
p(x,y)
\log
\frac{p(x,y)}
{p(x)p(y)}
}
$$

Untuk continuous variables bentuknya:

$$
I(X;Y)
=
\int\int
p(x,y)
\log
\frac{p(x,y)}
{p(x)p(y)}
dx\,dy.
$$

Namun saya **tidak ingin memasukkan mutual information ke versi pertama model**.

Kita simpan sebagai extension setelah baseline covariance bekerja dengan benar.

---

# A.18. Layer kelima: market microstructure

Sekarang kita masuk ke bagian yang membedakan model kita dari portfolio optimizer biasa.

Untuk short-term trading, OHLCV tidak cukup.

Kita membutuhkan order book.

Misalkan:

$$
B_k(t)
$$

adalah harga bid level $k$, dengan quantity:

$$
Q_k^B(t).
$$

Sedangkan:

$$
A_k(t)
$$

adalah ask level $k$, dengan:

$$
Q_k^A(t).
$$

Maka:

$$
OB_t
=
\{
(B_k,Q_k^B),
(A_k,Q_k^A)
\}_{k=1}^{L}.
$$

---

# A.19. Best bid dan ask

Definisikan:

$$
P_t^{bid}=B_1(t)
$$

dan:

$$
P_t^{ask}=A_1(t).
$$

Spread:

$$
\boxed{
S_t=P_t^{ask}-P_t^{bid}
}
$$

Relative spread:

$$
\boxed{
s_t=
\frac{P_t^{ask}-P_t^{bid}}
{P_t^{mid}}
}
$$

dengan:

$$
P_t^{mid}
=
\frac{P_t^{bid}+P_t^{ask}}2.
$$

Ini sangat penting untuk menentukan apakah limit order kita masuk akal.

---

# A.20. Order-book imbalance

Kita dapat mendefinisikan:

$$
V_t^{bid}
=
\sum_{k=1}^{L}Q_k^B(t)
$$

dan:

$$
V_t^{ask}
=
\sum_{k=1}^{L}Q_k^A(t).
$$

Kemudian:

$$
\boxed{
I_t
=
\frac{
V_t^{bid}-V_t^{ask}
}{
V_t^{bid}+V_t^{ask}
}
}
$$

Sehingga:

$$
-1\le I_t\le1.
$$

Interpretasi:

$$
I_t>0
$$

→ bid-side depth lebih besar.

$$
I_t<0
$$

→ ask-side depth lebih besar.

Sekali lagi:

$$
I_t>0
\not\Rightarrow
P_{t+1}>P_t.
$$

Ia hanya menjadi **state information**.

---

# A.21. Microprice

Kita dapat membangun microprice:

$$
\boxed{
P_t^{micro}
=
\frac{
P_t^{ask}Q_t^{bid}
+
P_t^{bid}Q_t^{ask}
}{
Q_t^{bid}+Q_t^{ask}
}
}
$$

Perhatikan jika:

$$
Q^{bid}>Q^{ask},
$$

maka microprice cenderung lebih dekat ke ask.

Selisih:

$$
M_t
=
P_t^{micro}-P_t^{mid}
$$

dapat menjadi feature microstructure.

Ini jauh lebih relevan untuk short-term execution daripada sekadar moving average.

---

# A.22. Layer keenam: liquidity state

Sistem kita perlu mengetahui apakah sebuah posisi dapat dieksekusi tanpa terlalu banyak market impact.

Salah satu representasi sederhana:

$$
L_t
=
\sum_{k=1}^{L}
Q_k^B+
\sum_{k=1}^{L}
Q_k^A.
$$

Tetapi quantity saja tidak cukup.

Kita juga dapat menghitung depth pada jarak $d$ dari mid-price:

$$
D_t(d)
=
\sum_{k:P_k\in[P^{mid}-d,P^{mid}+d]}
Q_k.
$$

Jadi:

$$
\boxed{
\text{Liquidity State}
=
\{Spread,Depth,Volume,Turnover,\ldots\}
}
$$

---

# A.23. Mengapa liquidity harus masuk ke state?

Misalnya dua aset mempunyai:

$$
\mu_1=\mu_2=0.2\%.
$$

dan:

$$
\sigma_1=\sigma_2=1\%.
$$

Secara Markowitz sederhana keduanya tampak identik.

Tetapi:

$$
L_1\gg L_2.
$$

Maka expected execution cost:

$$
C_1\ll C_2.
$$

Jadi secara trading:

$$
A_1
$$

lebih menarik.

Ini menunjukkan bahwa:

$$
\boxed{
\text{Portfolio mathematics}
\neq
\text{Execution mathematics}
}
$$

dan sistem kita harus menggabungkan keduanya.

---

# A.24. Layer ketujuh: current position state

Market state saja belum cukup.

Sistem juga harus tahu **apa yang sudah kita miliki**.

Misalnya:

$$
q_{i,t}
=
\text{position size asset }i.
$$

Kemudian:

$$
P_{i,t}^{entry}
$$

adalah average entry price.

Kita juga membutuhkan:

$$
SL_{i,t},
\qquad
TP_{i,t}.
$$

Maka position state:

$$
\boxed{
R_t=
\{
q_t,
P_t^{entry},
SL_t,
TP_t,
u_t
\}
}
$$

dengan $u_t$ dapat merepresentasikan unrealized PnL.

---

# A.25. Unrealized PnL

Untuk long:

$$
U_{i,t}
=
q_i(P_{i,t}-P_i^{entry}).
$$

Untuk short:

$$
U_{i,t}
=
q_i(P_i^{entry}-P_{i,t}).
$$

Atau menggunakan signed position:

$$
q_i\in\mathbb R,
$$

maka:

$$
\boxed{
U_{i,t}
=
q_i(P_{i,t}-P_i^{entry})
}
$$

dengan:

$$
q_i>0
$$

untuk long dan:

$$
q_i<0
$$

untuk short.

---

# A.26. Sekarang kita bisa membangun Market State Vector

Untuk sebuah target asset $i$, misalnya SOL:

$$
\boxed{
s_{i,t}
=
\begin{bmatrix}
X_{i,t}\\
F_{i,t}\\
V_{i,t}\\
C_{i,t}\\
OB_{i,t}\\
L_{i,t}\\
R_{i,t}
\end{bmatrix}
}
$$

Secara lebih eksplisit:

$$
s_{i,t}
=
\begin{bmatrix}
r_i^{(1)}\\
r_i^{(5)}\\
r_i^{(15)}\\
r_i^{(60)}\\
r_{\mathrm{BTC}}^{(1)}\\
r_{\mathrm{ETH}}^{(1)}\\
r_{\mathrm{Gold}}^{(1)}\\
r_{\mathrm{USD}}^{(1)}\\
\sigma_i\\
\sigma_{\mathrm{BTC}}\\
\sigma_{\mathrm{Gold}}\\
\sigma_{\mathrm{USD}}\\
\rho_{i,\mathrm{BTC}}\\
\rho_{i,\mathrm{ETH}}\\
I_{OB}\\
Spread\\
Depth\\
Position\\
UnrealizedPnL\\
SL\\
TP
\end{bmatrix}.
$$

Ini **bukan berarti final feature vector kita harus persis seperti ini**. Ini adalah mathematical specification awal.

---

# A.27. Tetapi ada persoalan yang sangat penting: timestamp

Ini mungkin terlihat sepele, tetapi sangat fundamental.

Misalnya:

- harga saham tersedia pada 10:00,
- harga BTC tersedia terus-menerus,
- gold tersedia pada waktu berbeda,
- USD factor tersedia pada interval berbeda.

Kita harus menentukan:

$$
\boxed{
\mathcal F_t
=
\text{information set available at time }t
}
$$

Setiap feature harus mempunyai timestamp.

Jika:

$$
t_{\mathrm{BTC}}\le t
$$

maka BTC boleh digunakan.

Jika:

$$
t_{\mathrm{Gold}}>t,
$$

maka gold tersebut **tidak boleh digunakan**.

Walaupun secara database datanya sudah tersedia.

---

# A.28. Ini adalah definisi formal anti-look-ahead

Kita definisikan filtration:

$$
\boxed{
\mathcal F_t
=
\sigma(
\text{all observations up to time }t
)
}
$$

Kemudian keputusan:

$$
a_t
$$

harus memenuhi:

$$
\boxed{
a_t
\text{ is }
\mathcal F_t\text{-measurable}
}
$$

Secara intuitif:

> ketika sistem membuat keputusan pada $t$, ia hanya boleh menggunakan informasi yang diketahui pada $t$.

Ini akan menjadi salah satu aturan paling penting pada backtester kita nanti.

---

# A.29. Sampling frequency

Sekarang kita harus memilih satu konsep penting:

$$
\Delta t.
$$

Karena sistem kita short-term tetapi multi-asset, saya tidak ingin semua data dipaksa memiliki timeframe yang sama secara sembarangan.

Kita definisikan:

$$
t_0,t_1,\ldots,t_T
$$

sebagai **decision times**.

Misalnya:

$$
\Delta t=1\text{ jam}.
$$

Kemudian:

$$
s_t
$$

dibentuk pada setiap decision time.

Tetapi data order book dapat memiliki resolusi jauh lebih tinggi.

Jadi:

$$
\boxed{
\text{Decision clock}
\neq
\text{Data clock}
}
$$

Ini sangat penting.

---

# A.30. Contoh

Misalkan decision time:

$$
09:00,\ 10:00,\ 11:00,\ldots
$$

Tetapi order book:

$$
09:00:01,\ 09:00:02,\ldots
$$

Kita dapat menggunakan informasi microstructure sampai:

$$
09:59:59
$$

untuk membuat:

$$
s_{10:00}.
$$

Kemudian keputusan:

$$
a_{10:00}.
$$

Dengan demikian sistem tetap konsisten.

---

# A.31. Market state sebenarnya adalah random variable

Ini penting secara probabilistik.

Kita dapat menulis:

$$
S_t
$$

sebagai random vector.

Future return:

$$
R_{t+\Delta}
$$

bergantung secara conditional pada state:

$$
\boxed{
P(R_{t+\Delta}\mid S_t)
}
$$

Inilah yang nantinya menjadi fondasi Tahap B.

Kita ingin mendapatkan:

$$
E[R_{t+\Delta}\mid S_t]
$$

dan:

$$
\operatorname{Cov}
(R_{t+\Delta}\mid S_t).
$$

Jadi Tahap A sebenarnya membangun **conditioning information** untuk model forecast.

---

# A.32. Ini juga menjelaskan mengapa kita tidak boleh mencampur state dan prediction

Tahap A:

$$
\boxed{
S_t
}
$$

adalah **observed/current information**.

Tahap B:

$$
\boxed{
\mu_t,\Sigma_t
}
$$

adalah **estimated future distribution**.

Tahap C/D:

$$
\boxed{
a_t^*
}
$$

adalah **decision**.

Jadi pipeline kita harus selalu:

$$
\boxed{
S_t
\rightarrow
P(R_{t+\Delta}|S_t)
\rightarrow
a_t^*
}
$$

bukan:

$$
S_t\rightarrow a_t
$$

secara langsung.

---

# A.33. Ini membuat sistem kita jauh lebih bersih

Kita sekarang memiliki tiga objek matematis:

### State

$$
S_t
$$

### Forecast distribution

$$
\boxed{
R_{t+\Delta}
\mid S_t
\sim
\mathcal D_t
}
$$

### Action

$$
\boxed{
a_t^*
=
\arg\max_a
E[
U(a)
\mid S_t
]
}
$$

Ini akan menjadi backbone seluruh sistem.

---

# A.34. Struktur final Tahap A

Saya ingin menetapkan struktur formal berikut sebagai **spesifikasi Tahap A v1**:

$$
\boxed{
S_t=
\left(
S_t^{price},
S_t^{factor},
S_t^{vol},
S_t^{dependence},
S_t^{micro},
S_t^{liquidity},
S_t^{position}
\right)
}
$$

dengan:

$$
S_t^{price}
=
\{r_{i,t}^{(\Delta)}\},
$$

$$
S_t^{factor}
=
\{r_{F_k,t}^{(\Delta)}\},
$$

$$
S_t^{vol}
=
\{\sigma_{i,t},\sigma_{F_k,t}\},
$$

$$
S_t^{dependence}
=
\{\rho_{ij,t},\rho_{iF_k,t}\},
$$

$$
S_t^{micro}
=
\{
OB_t,
I_t,
P_t^{mid},
P_t^{micro}
\},
$$

$$
S_t^{liquidity}
=
\{
Spread_t,
Depth_t,
Volume_t
\},
$$

dan:

$$
S_t^{position}
=
\{
q_t,
P_t^{entry},
SL_t,
TP_t,
PnL_t
\}.
$$

---

# A.35. Satu keputusan desain penting: jangan memasukkan semuanya sekaligus

Walaupun kita sudah mendesain state yang sangat kaya, **implementasi pertama sebaiknya tidak langsung menggunakan seluruhnya**.

Saya sarankan kita membuat tiga tingkat:

### State A0 — Baseline

$$
S_t^{(0)}
=
\{
returns,
volatility,
market\ factors
\}
$$

### State A1 — Cross-Asset

Tambahkan:

$$
\{
covariance,
correlation,
factor exposure
\}.
$$

### State A2 — Execution-Aware

Tambahkan:

$$
\{
orderbook,
spread,
depth,
imbalance,
liquidity
\}.
$$

Dengan begitu setiap peningkatan dapat diuji:

$$
A0
\rightarrow
A1
\rightarrow
A2.
$$

Kita bisa mengetahui apakah kompleksitas tambahan benar-benar meningkatkan hasil.

---

# A.36. Dan ini penting untuk penelitian

Jangan sampai nanti kita memiliki sistem yang sangat kompleks dan menghasilkan:

$$
Sharpe=1.8
$$

tetapi kita tidak tahu apakah peningkatan tersebut berasal dari:

- market factor,
- order book,
- volatility,
- optimizer,
- atau overfitting.

Dengan baseline bertingkat:

$$
\boxed{
\text{A0 vs A1 vs A2}
}
$$

kita dapat melakukan ablation study.

Misalnya:

$$
\Delta Sharpe_{factor}
=
Sharpe(A1)-Sharpe(A0)
$$

dan:

$$
\Delta Sharpe_{micro}
=
Sharpe(A2)-Sharpe(A1).
$$

Ini jauh lebih ilmiah.

---

# A.37. Hubungan Tahap A dengan seluruh proyek

Sekarang kita sudah bisa melihat gambaran besarnya:

$$
\boxed{
\begin{array}{ccccc}
\text{Tahap A} &&
\text{Tahap B} &&
\text{Tahap C/D}\\
S_t &\rightarrow&
(\mu_t,\Sigma_t,B_t)&\rightarrow&
\text{Optimization}\\
&&&&\\
\text{Market State}&&
\text{Forecast}&&
\text{Decision}
\end{array}
}
$$

Kemudian:

$$
\text{Decision}
\rightarrow
\text{Execution}
\rightarrow
\text{New State}
\rightarrow
\text{Forecast}
\rightarrow
\text{Re-optimization}.
$$

Dengan demikian akhirnya kita memperoleh:

$$
\boxed{
S_t
\rightarrow
\mathcal D_t
\rightarrow
a_t
\rightarrow
S_{t+\Delta}
\rightarrow\cdots
}
$$

yang merupakan inti **adaptive systematic trading system** kita.

---

## A.38. Kesimpulan Tahap A

Jadi, untuk saat ini fondasi matematis kita adalah:

$$
\boxed{
\mathcal F_t
\rightarrow
S_t
}
$$

di mana:

$$
\boxed{
S_t=
[
\text{price},
\text{factors},
\text{volatility},
\text{dependence},
\text{microstructure},
\text{liquidity},
\text{position}
]
}
$$

dan kita menetapkan aturan fundamental:

$$
\boxed{
S_t\subseteq\mathcal F_t
}
$$

serta:

$$
\boxed{
a_t\text{ hanya boleh bergantung pada }\mathcal F_t.
}
$$

Kemudian Tahap B akan membangun:

$$
\boxed{
P(
\mathbf R_{t+\Delta}
\mid
S_t
)
}
$$

dan dari distribusi tersebut kita mendapatkan:

$$
\boxed{
\boldsymbol{\mu}_t
\quad\text{dan}\quad
\Sigma_t
}
$$

yang nantinya menjadi bahan bakar **optimization engine**.

Dan ada satu hal yang menurutku sangat penting untuk menjaga proyek ini tetap realistis: **gold, USD, BTC, ETH, indeks saham, dan aset target tidak kita anggap sebagai hubungan kausal yang sudah diketahui.** Mereka masuk sebagai observasi/factor candidate; kekuatan dan arah hubungannya harus **diestimasi dari data secara out-of-sample**. Dengan begitu kita tidak membangun cerita finansial terlebih dahulu lalu memaksa matematika membenarkannya.

Tahap A secara konseptual sudah selesai. **Tahap B nantinya akan menjadi jauh lebih matematis:** kita akan mengambil $S_t$ ini dan menurunkan *conditional expected return*, *dynamic covariance*, *factor loading*, dan *regime-dependent distribution* sampai akhirnya memperoleh $\boldsymbol{\mu}_t$ dan $\Sigma_t$ yang benar-benar layak diberikan kepada optimizer.

