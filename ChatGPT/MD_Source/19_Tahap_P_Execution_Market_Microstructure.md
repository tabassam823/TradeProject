## Prompt:
8/17/2026, 10:01:13 PM

lanjut Tahap P

## Response:
8/17/2026, 10:01:14 PM

# Tahap P — Execution & Market Microstructure Optimization

Tahap P adalah tahap yang menurut saya **sangat penting** jika tujuan akhirnya memang bukan sekadar membuat *portfolio optimizer*, tetapi membangun sistem **quantitative short-horizon trading** yang realistis.

Sampai Tahap O, kita sudah bisa mengatakan:

> **"Saya ingin LONG BTC dengan risk budget \$1, target tertentu, dan stop-loss tertentu."**

Tetapi pasar tidak bekerja seperti itu.

Kita tidak bisa begitu saja menganggap:

$$
P_{entry}=P_t.
$$

Dalam kenyataan, kita harus menjawab:

- Apakah menggunakan **market order** atau **limit order**?
- Kalau limit order, di harga berapa?
- Berapa probabilitas order tersebut terisi?
- Berapa lama kita bersedia menunggu?
- Jika belum terisi, apakah order dipindahkan?
- Berapa *slippage*?
- Berapa *spread*?
- Berapa besar order yang sedang mengantre di depan kita?
- Apakah order book sedang menunjukkan tekanan beli/jual?
- Jika order kita tidak filled, apakah peluang pasar bergerak tanpa kita lebih buruk daripada menunggu?
- Bagaimana execution memengaruhi \$1 risk budget kita?

Dengan demikian Tahap P memperkenalkan:

$$
\boxed{
\text{Market Microstructure}
}
$$

ke dalam sistem.

---

# P.1. Perubahan paradigma

Sebelumnya kita memiliki:

$$
\boxed{
\text{Decision Price}
}
$$

seolah-olah harga entry adalah:

$$
P_t.
$$

Sekarang kita harus membedakan:

$$
\boxed{
P_t^{mid}
}
$$

$$
P_t^{bid}
$$

$$
P_t^{ask}
$$

$$
P_t^{exec}.
$$

Dengan:

$$
P_t^{mid}
=
\frac{P_t^{bid}+P_t^{ask}}{2}.
$$

Dan:

$$
P_t^{ask}-P_t^{bid}
=
S_t
$$

adalah bid-ask spread.

---

# P.2. Entry signal ≠ execution

Ini merupakan prinsip utama Tahap P:

$$
\boxed{
Signal\ Generation
\neq
Order\ Execution.
}
$$

Model sebelumnya mungkin mengatakan:

$$
LONG.
$$

Tetapi execution optimizer harus menentukan:

$$
\boxed{
\text{HOW to become LONG}.
}
$$

Misalnya:

$$
\begin{aligned}
&BUY\ MARKET,\\
&BUY\ LIMIT\ @P_{bid},\\
&BUY\ LIMIT\ @P_{bid}-1tick,\\
&BUY\ LIMIT\ @P_{bid}-2ticks,\\
&WAIT.
\end{aligned}
$$

---

# P.3. State market microstructure

Sekarang state kita diperluas.

Sebelumnya:

$$
s_t=
\{
P_t,\hat\mu_t,\Sigma_t,\Theta_t,\ldots
\}.
$$

Sekarang:

$$
\boxed{
s_t^{micro}
=
\{
P_t^{bid},
P_t^{ask},
V_t^{bid},
V_t^{ask},
S_t,
I_t,
D_t,
Q_t,
\lambda_t,
\sigma_t
\}.
}
$$

Beberapa variabel penting:

- $V_t^{bid}$: volume bid,
- $V_t^{ask}$: volume ask,
- $S_t$: spread,
- $I_t$: order-book imbalance,
- $D_t$: depth,
- $Q_t$: queue position,
- $\lambda_t$: order arrival intensity,
- $\sigma_t$: short-term volatility.

---

# P.4. Order-book imbalance

Salah satu feature paling dasar adalah:

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

sehingga:

$$
-1\leq I_t\leq1.
$$

Jika:

$$
I_t\rightarrow1,
$$

bid jauh lebih besar daripada ask.

Jika:

$$
I_t\rightarrow-1,
$$

ask jauh lebih besar daripada bid.

---

# P.5. Tetapi imbalance sederhana belum cukup

Misalnya:

$$
V^{bid}_1=100,
\qquad
V^{ask}_1=20.
$$

Kita mendapatkan:

$$
I=0.667.
$$

Tetapi mungkin volume tersebut berada sangat jauh dari mid-price.

Karena itu kita dapat menggunakan **depth-weighted imbalance**.

Misalkan terdapat $K$ level:

$$
k=1,\ldots,K.
$$

Maka:

$$
\boxed{
I_t^{(K)}
=
\frac{
\sum_{k=1}^{K}w_kV_{bid,k}
-
\sum_{k=1}^{K}w_kV_{ask,k}
}{
\sum_{k=1}^{K}w_kV_{bid,k}
+
\sum_{k=1}^{K}w_kV_{ask,k}
}
}
$$

dengan:

$$
w_k=e^{-\alpha(k-1)}.
$$

Level yang lebih dekat dengan mid mendapat bobot lebih besar.

---

# P.6. Microprice

Mid-price:

$$
M_t=\frac{A_t+B_t}{2}.
$$

Tetapi mid-price tidak memperhitungkan imbalance.

Kita dapat menggunakan:

$$
\boxed{
P_t^{micro}
=
\frac{
A_tV_t^{bid}
+
B_tV_t^{ask}
}{
V_t^{bid}+V_t^{ask}
}
}
$$

dengan:

- $A_t$: best ask,
- $B_t$: best bid.

Jika:

$$
V^{bid}\gg V^{ask},
$$

maka:

$$
P^{micro}
$$

cenderung mendekati ask.

Ini memberi estimasi yang lebih informatif mengenai tekanan harga jangka sangat pendek.

---

# P.7. Short-horizon expected price

Sekarang kita dapat membuat:

$$
\boxed{
\hat P_{t+\Delta}
=
E[P_{t+\Delta}\mid\mathcal F_t].
}
$$

Atau expected return:

$$
\boxed{
\hat r_{t,\Delta}
=
E\left[
\ln\frac{P_{t+\Delta}}{P_t}
\middle|
\mathcal F_t
\right].
}
$$

Dan model dapat menggunakan:

$$
\hat r
=
f(
I_t,
P_t^{micro}-P_t^{mid},
\sigma_t,
\text{factor state},
\text{momentum},
\text{flow}
).
$$

---

# P.8. Sekarang masalah utama: fill probability

Misalkan kita ingin membeli.

Kita mempunyai dua pilihan:

### Market order

Probability fill:

$$
P(Fill)\approx1.
$$

Tetapi:

$$
Cost_{execution}
$$

lebih besar.

### Limit order

Cost lebih rendah.

Tetapi:

$$
P(Fill)<1.
$$

Maka execution sebenarnya adalah trade-off:

$$
\boxed{
Execution\ Cost
\quad\leftrightarrow\quad
Fill\ Probability.
}
$$

---

# P.9. Expected execution utility

Misalkan action:

$$
a
$$

adalah jenis order.

Kita definisikan:

$$
p_F(a)
=
P(\text{fill}\mid a).
$$

Jika filled:

$$
U_F(a).
$$

Jika tidak filled:

$$
U_N(a).
$$

Maka:

$$
\boxed{
E[U(a)]
=
p_F(a)U_F(a)
+
(1-p_F(a))U_N(a).
}
$$

Ini merupakan fondasi execution optimizer kita.

---

# P.10. Mengapa "tidak filled" bukan utility nol?

Ini sangat penting.

Misalkan model sangat yakin:

$$
P_{t+\Delta}>P_t.
$$

Kita menaruh limit buy:

$$
P_L<P_t.
$$

Jika tidak filled dan harga naik, kita kehilangan kesempatan.

Opportunity cost tersebut adalah:

$$
\boxed{
U_N<0.
}
$$

Jadi limit order murah belum tentu optimal.

---

# P.11. Market order versus limit order

Misalkan:

### Market

$$
p_F=0.999.
$$

Expected execution price:

$$
P_M=P_t+\text{slippage}.
$$

### Limit

$$
p_F=0.65.
$$

Execution price:

$$
P_L<P_t.
$$

Tetapi jika tidak filled:

$$
P_{future}>P_t.
$$

Maka:

$$
E[U_{limit}]
$$

bisa saja lebih rendah daripada:

$$
E[U_{market}].
$$

---

# P.12. Implementation shortfall

Kita memerlukan ukuran:

$$
\boxed{
IS
}
$$

atau implementation shortfall.

Untuk long secara sederhana:

$$
\boxed{
IS
=
P_{exec}-P_{decision}
}
$$

dalam satuan harga.

Jika:

$$
P_{exec}>P_{decision},
$$

maka execution lebih buruk.

Dalam return:

$$
IS_r
=
\frac{P_{exec}-P_{decision}}
{P_{decision}}.
$$

---

# P.13. Total execution cost

Kita dapat memecah:

$$
\boxed{
C_{exec}
=
C_{spread}
+
C_{slippage}
+
C_{fee}
+
C_{impact}
+
C_{opportunity}.
}
$$

Perhatikan:

$$
C_{opportunity}
$$

berasal dari order yang tidak terisi.

Jadi limit order tidak benar-benar "gratis".

---

# P.14. Spread cost

Jika kita membeli menggunakan market order:

$$
P_{ask}
$$

sedangkan reference price:

$$
P_{mid}.
$$

Maka:

$$
\boxed{
C_{spread}
=
P_{ask}-P_{mid}
=
\frac{S}{2}.
}
$$

Untuk sell:

$$
P_{mid}-P_{bid}
=
\frac{S}{2}.
$$

---

# P.15. Slippage

Misalkan kita ingin membeli:

$$
q=100.
$$

Tetapi best ask hanya memiliki:

$$
40.
$$

Order kita harus mengambil:

$$
40
$$

pada level pertama,

sisanya:

$$
60
$$

pada level berikutnya.

Execution price menjadi weighted average:

$$
\boxed{
P_{VWAP}
=
\frac{
\sum_kP_kq_k
}{
\sum_kq_k
}.
}
$$

Slippage:

$$
\boxed{
Slippage
=
P_{VWAP}-P_{best}.
}
$$

---

# P.16. Market impact

Jika:

$$
q
$$

cukup besar relatif terhadap liquidity, order kita sendiri mengubah harga.

Secara sederhana:

$$
\boxed{
Impact(q)
\propto
\left(\frac{q}{D}\right)^\alpha
}
$$

dengan:

- $D$: available liquidity,
- $\alpha>0$.

Model yang lebih realistis dapat menggunakan empirical impact function.

---

# P.17. Risk budget sekarang harus memasukkan execution

Sebelumnya:

$$
R=q|P_{entry}-P_{SL}|.
$$

Sekarang entry tidak diketahui secara pasti.

Kita harus menggunakan:

$$
P_{exec}.
$$

Maka:

$$
\boxed{
R
=
q|P_{exec}-P_{SL}|
+
C_{exit}
+
C_{entry}
+
C_{slippage}.
}
$$

Dan constraint kita tetap:

$$
\boxed{
R\leq \$1.
}
$$

Ini sangat penting.

---

# P.18. Execution price uncertainty

Kita bahkan dapat menganggap:

$$
P_{exec}
$$

sebagai random variable.

$$
P_{exec}\sim p(P\mid a,s_t).
$$

Maka risk menjadi:

$$
R(a)
=
E[
q|P_{exec}-P_{SL}|
]
+
C(a).
$$

Tetapi untuk sistem risk-sensitive, expected value saja belum cukup.

Kita dapat menggunakan:

$$
VaR
$$

atau:

$$
CVaR.
$$

---

# P.19. CVaR execution risk

Misalkan:

$$
L_{exec}
$$

adalah execution loss.

Kita dapat membatasi:

$$
\boxed{
CVaR_\alpha(L_{exec})
\leq L_{max}.
}
$$

Dengan demikian order yang memiliki tail slippage besar dapat ditolak meskipun expected slippage kecil.

---

# P.20. Queue position

Sekarang masuk bagian yang sangat menarik.

Misalkan kita menaruh:

$$
BUY\ LIMIT
$$

di:

$$
P=B_t.
$$

Di depan order kita terdapat:

$$
Q_t
$$

unit.

Agar order kita filled, market harus mengonsumsi:

$$
Q_t+q
$$

volume pada harga tersebut, kecuali terdapat cancelation.

Maka:

$$
\boxed{
P(Fill)
=
P(
V_{consumed}
\geq
Q_t+q
).
}
$$

---

# P.21. Queue depletion model

Misalkan order consumption mengikuti counting process:

$$
N_t.
$$

Kita dapat memodelkannya sebagai Poisson:

$$
N_t\sim Pois(\lambda t).
$$

Probability order terisi:

$$
\boxed{
P(Fill\leq t)
=
P(N_t\geq Q_t+q).
}
$$

Secara eksplisit:

$$
P(Fill\leq t)
=
1-
\sum_{k=0}^{Q_t+q-1}
e^{-\lambda t}
\frac{(\lambda t)^k}{k!}.
$$

Ini memberikan hubungan:

$$
\boxed{
Queue
\rightarrow
Fill\ Probability.
}
$$

Model Poisson ini adalah **baseline**, bukan asumsi final; order flow nyata biasanya lebih kompleks dan dapat menunjukkan clustering serta self-excitation.

---

# P.22. Cancellation rate

Queue tidak hanya berkurang karena transaksi.

Order di depan kita dapat dibatalkan.

Misalkan:

$$
\mu
$$

adalah cancellation intensity.

Maka effective queue depletion:

$$
\boxed{
\lambda_{effective}
=
\lambda_{trade}
+
\lambda_{cancel}.
}
$$

Sehingga:

$$
P(Fill)
$$

meningkat jika cancellation rate meningkat.

---

# P.23. Expected time to fill

Dengan intensity:

$$
\lambda_{eff},
$$

secara sederhana:

$$
\boxed{
E[T_{fill}]
\approx
\frac{Q_t+q}{\lambda_{eff}}.
}
$$

Tetapi dalam sistem nyata kita sebaiknya menggunakan distribusi:

$$
T_{fill}\sim F_T(t\mid s_t,a).
$$

---

# P.24. Time-to-fill menjadi decision variable

Sekarang kita dapat menentukan:

$$
\tau_{max}.
$$

Misalnya:

$$
\tau_{max}=15\text{ menit}.
$$

Jika:

$$
T_{fill}>\tau_{max},
$$

order dianggap tidak lagi menarik.

Tetapi $\tau_{max}$ sendiri seharusnya dioptimalkan.

---

# P.25. Dynamic order placement

Kita sekarang punya kandidat:

$$
a\in\mathcal A_{exec}.
$$

Misalnya:

$$
\mathcal A_{exec}
=
\{
MARKET,
LIMIT_0,
LIMIT_1,
LIMIT_2,
WAIT
\}.
$$

Dengan:

$$
LIMIT_k
=
P_{bid}-k\Delta P.
$$

---

# P.26. Objective execution

Untuk setiap action:

$$
a,
$$

kita menghitung:

$$
\boxed{
U_{exec}(a)
=
E[\Pi\mid a]
-
C_{exec}(a)
-
\lambda_rR(a)
-
\lambda_oOC(a).
}
$$

Kemudian:

$$
\boxed{
a^\star
=
\arg\max_aU_{exec}(a).
}
$$

---

# P.27. Tetapi execution dan alpha saling berinteraksi

Misalkan:

$$
\hat r_{5min}=+0.10\%.
$$

Spread:

$$
0.02\%.
$$

Limit order memberi expected price improvement:

$$
0.015\%.
$$

Tetapi probability fill hanya:

$$
30\%.
$$

Jika harga diperkirakan naik cepat, waiting cost bisa lebih besar daripada price improvement.

Jadi execution optimizer harus mengetahui:

$$
\boxed{
alpha\ decay.
}
$$

---

# P.28. Alpha decay

Misalkan expected return:

$$
\hat r(\tau)
$$

berkurang terhadap waktu:

$$
\boxed{
\hat r(\tau)
=
\hat r_0e^{-\kappa\tau}.
}
$$

Parameter:

$$
\kappa
$$

adalah alpha decay rate.

Jika:

$$
\kappa
$$

besar, kita harus cepat.

Jika:

$$
\kappa
$$

kecil, kita dapat menunggu limit fill.

---

# P.29. Ini menghasilkan trade-off yang sangat elegan

Limit order memberikan:

$$
\text{Price Improvement}.
$$

Tetapi menunggu memberikan:

$$
\text{Alpha Decay}.
$$

Maka:

$$
\boxed{
Execution\ Optimization
=
Price\ Improvement
-
Waiting\ Cost
}
$$

dengan waiting cost bergantung pada:

$$
\alpha\ decay.
$$

---

# P.30. Opportunity cost akibat non-fill

Misalkan jika tidak filled dalam waktu $\tau$, kita kehilangan expected move:

$$
E[\Delta P_\tau].
$$

Maka:

$$
\boxed{
OC(\tau)
=
P(Fill^c,\tau)
\cdot
E[\Delta P_\tau].
}
$$

Untuk long dan expected move positif, waiting bisa sangat mahal.

---

# P.31. Limit order placement sebagai optimasi

Kita dapat memilih:

$$
\delta
$$

sebagai jarak limit dari mid:

$$
P_L=P_{mid}-\delta.
$$

Kemudian:

$$
\boxed{
\delta^\star
=
\arg\max_{\delta}
U_{exec}(\delta).
}
$$

Dengan:

$$
U_{exec}(\delta)
=
p_F(\delta)U_F(\delta)
+
[1-p_F(\delta)]U_N(\delta).
$$

Ini merupakan salah satu core problem Tahap P.

---

# P.32. Sekarang kita bisa membuat execution QUBO

Diskretkan:

$$
\delta
\in
\{
0,1,2,\ldots,K
\}.
$$

Definisikan binary:

$$
x_k\in\{0,1\}.
$$

Dengan:

$$
\sum_{k=0}^{K}x_k=1.
$$

Kemudian:

$$
\delta
=
\sum_{k=0}^{K}\delta_kx_k.
$$

---

# P.33. Objective

Jika:

$$
U_k=U_{exec}(\delta_k),
$$

maka:

$$
\boxed{
E(x)
=
-\sum_kU_kx_k
+
P\left(\sum_kx_k-1\right)^2.
}
$$

Ini sudah menjadi QUBO.

---

# P.34. Jika kita juga mengoptimalkan order size

Sekarang:

$$
q
$$

juga menjadi decision variable.

Misalnya:

$$
q\in
\{0.25q^\star,
0.5q^\star,
0.75q^\star,
q^\star\}.
$$

Kita dapat menggunakan:

$$
x_{k,m}
$$

untuk kombinasi:

$$
(\delta_k,q_m).
$$

Kemudian:

$$
\boxed{
(\delta^\star,q^\star)
=
\arg\max_{\delta,q}
U_{exec}(\delta,q).
}
$$

---

# P.35. Tetapi quantity dibatasi risk

Constraint:

$$
q|P_{exec}-SL|
\leq \$1.
$$

Jika:

$$
P_{exec}
$$

random, kita dapat menggunakan conservative estimate:

$$
q
\left(
P_{exec}^{worst}-SL
\right)
\leq1.
$$

Atau:

$$
\boxed{
CVaR_\alpha(R)\leq1.
}
$$

---

# P.36. Multi-asset execution

Sekarang bayangkan:

$$
BTC,\ ETH,\ SOL,\ XRP.
$$

Kita ingin:

$$
q_i
$$

untuk setiap aset.

Total risk:

$$
\boxed{
R_p
=
w^T\Sigma w
}
$$

atau jika menggunakan dollar risk:

$$
\boxed{
R_p\leq R_{budget}.
}
$$

Execution optimizer sekarang harus menentukan:

$$
\{
q_i,\delta_i,a_i
\}_{i=1}^N.
$$

---

# P.37. Ini kembali menjadi combinatorial optimization

Karena:

$$
a_i
$$

bisa:

$$
MARKET/LIMIT/WAIT,
$$

dan:

$$
\delta_i
$$

diskrit,

kita mendapatkan:

$$
\boxed{
\text{Execution Portfolio Optimization}.
}
$$

Objective:

$$
\max
\sum_i
U_i^{exec}
-
\lambda Risk_p
-
\lambda Cost_p.
$$

---

# P.38. Cross-asset market impact

Ini menjadi menarik untuk crypto.

Misalnya kita ingin membeli:

$$
SOL.
$$

Tetapi:

$$
BTC
$$

mengalami sell pressure besar.

Maka expected SOL return dapat berubah.

Dengan factor model:

$$
r_{SOL}
=
\beta_{SOL,BTC}r_{BTC}
+
\epsilon.
$$

Jika:

$$
r_{BTC}
$$

berubah, execution decision SOL juga berubah.

---

# P.39. Untuk saham internasional

Kita dapat memperluas factor state:

$$
F_t=
[
DXY,
Gold,
SPX,
Nasdaq,
VIX,
Treasury,
BTC,
\ldots
].
$$

Misalnya untuk saham teknologi:

$$
r_i
=
\alpha_i
+
\beta_{i,DXY}r_{DXY}
+
\beta_{i,SPX}r_{SPX}
+
\beta_{i,NQ}r_{NQ}
+
\epsilon_i.
$$

Execution optimizer kemudian mengetahui apakah:

$$
\hat r_i
$$

cukup besar untuk membayar:

$$
spread+slippage+impact.
$$

---

# P.40. Ini menghasilkan konsep penting: alpha after execution

Alpha mentah:

$$
\alpha_{raw}.
$$

Execution cost:

$$
C_{exec}.
$$

Maka:

$$
\boxed{
\alpha_{net}
=
\alpha_{raw}
-
C_{exec}.
}
$$

Tetapi karena fill probability juga penting:

$$
\boxed{
E[\alpha_{net}]
=
p_F(\alpha_{raw}-C_F)
+
(1-p_F)\alpha_{no-fill}.
}
$$

Jadi signal yang terlihat sangat bagus dapat menjadi trade yang buruk setelah execution.

---

# P.41. No-trade region

Ini menghasilkan konsep yang sangat penting.

Jika:

$$
\alpha_{raw}
<
C_{exec},
$$

maka:

$$
\boxed{
NO\ TRADE.
}
$$

Dengan kata lain:

> Model tidak wajib trading hanya karena ada signal.

Kita dapat mendefinisikan:

$$
\boxed{
|\hat\mu_t|
>
C_{exec}+C_{risk}+C_{uncertainty}
}
$$

sebagai syarat minimum untuk melakukan trade.

---

# P.42. Hysteresis execution

Sama seperti Tahap O, jangan terus-menerus memindahkan limit order.

Jika:

$$
U_{new}-U_{old}<C_{modify},
$$

maka:

$$
\boxed{
KEEP\ CURRENT\ ORDER.
}
$$

Dengan demikian sistem tidak mengalami:

$$
Cancel
\rightarrow
Replace
\rightarrow
Cancel
\rightarrow
Replace.
$$

---

# P.43. Order lifecycle

Sekarang setiap order mempunyai state machine.

$$
\boxed{
NEW
\rightarrow
PLACED
\rightarrow
PARTIAL
\rightarrow
FILLED
}
$$

atau:

$$
PLACED
\rightarrow
CANCELLED.
$$

Atau:

$$
PARTIAL
\rightarrow
CANCELLED.
$$

---

# P.44. Mengapa partial fill penting?

Misalkan target:

$$
q^\star=100.
$$

Tetapi hanya:

$$
40
$$

filled.

Maka kita memiliki:

$$
q_{filled}=40.
$$

Remaining:

$$
q_{remaining}=60.
$$

Namun setelah 40 filled, market state dapat berubah.

Maka:

$$
q_{remaining}
$$

tidak boleh dianggap otomatis harus dikejar.

Kita harus melakukan re-optimization.

---

# P.45. Partial fill sebagai decision problem

Setelah partial fill:

$$
\boxed{
a\in
\{
KEEP\_ORDER,
CANCEL,
REPRICE,
MARKET\_REMAINDER,
WAIT
\}.
}
$$

Dan:

$$
a^\star
=
\arg\max_aU(a).
$$

---

# P.46. Adverse selection

Ini salah satu masalah paling penting dalam limit order.

Misalkan kita memasang:

$$
BUY\ LIMIT.
$$

Order kita filled.

Mengapa?

Mungkin karena:

$$
P_t
$$

justru akan turun.

Artinya:

$$
\boxed{
Fill
}
$$

sendiri membawa informasi negatif.

Ini disebut **adverse selection**.

---

# P.47. Fill probability tidak selalu positif

Kita sebelumnya menulis:

$$
p_F.
$$

Tetapi sebenarnya:

$$
P(return>0\mid Fill)
$$

dapat lebih rendah daripada:

$$
P(return>0\mid NoFill).
$$

Jadi kita harus memodelkan:

$$
\boxed{
P(\Delta P>0\mid Fill,s_t).
}
$$

Bukan hanya:

$$
P(Fill).
$$

---

# P.48. Execution alpha

Kita dapat mendefinisikan:

$$
\boxed{
A_{exec}
=
E[\Delta P\mid Fill]
-
E[\Delta P\mid NoFill].
}
$$

Jika:

$$
A_{exec}<0,
$$

fill cenderung terjadi ketika market bergerak melawan kita.

Maka limit order tersebut mungkin memiliki adverse selection yang tinggi.

---

# P.49. Objective execution yang lebih lengkap

Sekarang:

$$
\boxed{
U_{exec}(a)
=
p_F(a)
\left[
E[\Pi\mid Fill,a]
-
C_F(a)
\right]
+
(1-p_F(a))
\left[
E[\Pi\mid NoFill,a]
-
C_N(a)
\right]
}
$$

dan:

$$
\boxed{
a^\star=\arg\max_aU_{exec}(a).
}
$$

Ini jauh lebih realistis daripada:

> "limit order selalu lebih baik karena fee lebih murah."

---

# P.50. Hubungan dengan Tahap O

Tahap O menghasilkan:

$$
P_{entry}^{target},
$$

$$
SL,
$$

$$
TP,
$$

$$
q.
$$

Tahap P kemudian mengatakan:

> Bagaimana kita mendapatkan $q$ tersebut dengan biaya dan risiko execution minimum?

Jadi:

$$
\boxed{
O
\rightarrow
P
}
$$

bukan dua modul independen.

---

# P.51. Execution-aware risk

Misalkan Tahap O mengatakan:

$$
q=100.
$$

Tetapi Tahap P memperkirakan:

$$
slippage=0.3\%.
$$

Maka actual risk:

$$
R_{actual}
>
R_{planned}.
$$

Jika:

$$
R_{actual}>\$1,
$$

maka execution layer harus mengurangi:

$$
q.
$$

Jadi quantity final:

$$
\boxed{
q_{exec}
=
\min(q_{optimal},q_{risk},q_{liquidity}).
}
$$

---

# P.52. Risk budget hierarchy

Kita sekarang memiliki:

$$
R_{total}\leq \$1.
$$

Tetapi:

$$
R_{total}
=
R_{market}
+
R_{execution}
+
R_{gap}
+
R_{model}.
$$

Sehingga secara konseptual:

$$
\boxed{
R_{market}
+
R_{execution}
\leq
R_{budget}.
}
$$

Ini lebih realistis daripada mengalokasikan seluruh \$1 kepada price movement saja.

---

# P.53. Dynamic execution budget

Misalnya:

$$
R_{budget}=1.
$$

Market risk:

$$
R_{market}=0.75.
$$

Maka execution hanya memiliki:

$$
\boxed{
R_{execution}\leq0.25.
}
$$

Jika spread/slippage terlalu besar:

$$
R_{execution}>0.25,
$$

trade harus:

$$
\boxed{
REJECTED.
}
$$

---

# P.54. Ini menghasilkan gate terakhir

Sebelum order dikirim:

$$
\boxed{
Trade\ Gate
}
$$

memeriksa:

$$
\begin{aligned}
EV &>0,\\
Risk &\leq Budget,\\
Liquidity &\geq Minimum,\\
ExecutionCost &\leq Maximum,\\
FillProbability &\geq Minimum,\\
Regime &\text{valid}.
\end{aligned}
$$

Jika salah satu constraint kritis gagal:

$$
\boxed{
NO\ TRADE.
}
$$

---

# P.55. Arsitektur lengkap setelah Tahap P

Sekarang sistem kita menjadi:

```text
                    MARKET DATA
                         │
          ┌──────────────┴──────────────┐
          │                             │
    Fundamental/Price             Order Book
       /Factor Data                 /Trades
          │                             │
          ▼                             ▼
    Forecast Model              Microstructure Model
          │                             │
          └──────────────┬──────────────┘
                         ▼
                  Risk / State Model
                         │
                         ▼
                  ENTRY OPTIMIZER
                    (Tahap O)
                         │
                 target position
                         │
                         ▼
                EXECUTION OPTIMIZER
                    (Tahap P)
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
            MARKET     LIMIT       WAIT
              │          │          │
              └──────────┼──────────┘
                         ▼
                     FILLED?
                    /       \
                  YES        NO
                   │          │
                   ▼          ▼
               POSITION    RE-EVALUATE
               MANAGEMENT
                   │
                   ▼
                Tahap O
```

---

# P.56. Dan sekarang kita mempunyai tiga lapisan optimasi

Ini mulai menjadi sangat menarik.

### Layer 1 — Portfolio / Entry

$$
\boxed{
\text{What should I trade?}
}
$$

QUBO:

$$
Q_{entry}.
$$

---

### Layer 2 — Position Management

$$
\boxed{
\text{What should I do with the trade?}
}
$$

QUBO:

$$
Q_{manage}.
$$

---

### Layer 3 — Execution

$$
\boxed{
\text{How should I execute the decision?}
}
$$

QUBO:

$$
Q_{exec}.
$$

---

# P.57. Tiga QUBO

Secara ringkas:

$$
\boxed{
Q_{entry}
\rightarrow
Q_{manage}
\rightarrow
Q_{exec}.
}
$$

Atau:

$$
\boxed{
\text{Selection}
\rightarrow
\text{Management}
\rightarrow
\text{Execution}.
}
$$

Dan semuanya menggunakan market state yang diperbarui secara periodik.

---

# P.58. Tetapi saya ingin membuat satu perubahan penting pada desain kita

Jangan membuat:

$$
Q_{entry},
Q_{manage},
Q_{exec}
$$

sepenuhnya terpisah.

Karena ada coupling.

Contohnya:

$$
\text{entry size}
$$

mempengaruhi:

$$
\text{execution impact}.
$$

Execution mempengaruhi:

$$
P_{entry}.
$$

Entry price mempengaruhi:

$$
SL.
$$

SL mempengaruhi:

$$
risk.
$$

Risk mempengaruhi:

$$
portfolio allocation.
$$

Jadi secara ideal:

$$
\boxed{
\text{Hierarchical Optimization}
}
$$

dengan feedback.

---

# P.59. Mathematical feedback loop

Secara konseptual:

$$
x_t^{entry}
\rightarrow
q_t
\rightarrow
a_t^{exec}
\rightarrow
P_t^{exec}
\rightarrow
R_t
\rightarrow
x_t^{manage}.
$$

Kemudian:

$$
x_t^{manage}
\rightarrow
future\ capital
\rightarrow
x_{t+1}^{entry}.
$$

Jadi sistem merupakan:

$$
\boxed{
closed-loop optimization.
}
$$

---

# P.60. Ini juga membuat proyek kita cocok untuk eksperimen quantum

Karena kita dapat menguji:

### Classical baseline

$$
\boxed{
Exact/Brute Force
}
$$

untuk problem kecil.

### Classical heuristic

$$
\boxed{
Simulated\ Annealing
}
$$

$$
\boxed{
Tabu\ Search
}
$$

$$
\boxed{
MILP
}
$$

### Quantum

$$
\boxed{
QAOA
}
$$

Kemudian dibandingkan berdasarkan:

$$
\begin{aligned}
&solution\ quality,\\
&approximation\ ratio,\\
&runtime,\\
&number\ of\ circuit\ evaluations,\\
&constraint\ violation,\\
&execution\ performance.
\end{aligned}
$$

---

# P.61. Metrik yang harus kita simpan

Untuk setiap order:

$$
\boxed{
\begin{aligned}
&P_{decision},\\
&P_{limit},\\
&P_{exec},\\
&spread,\\
&slippage,\\
&fee,\\
&queue\ estimate,\\
&fill\ probability,\\
&actual\ fill\ time,\\
&partial\ fill,\\
&market\ move\ after\ order.
\end{aligned}
}
$$

Ini akan menjadi **dataset execution** kita.

---

# P.62. Ini membuka kemungkinan self-improving execution model

Setelah banyak trade, kita dapat mengestimasi:

$$
P(Fill\mid state,order).
$$

Kemudian:

$$
E[Slippage\mid state,order].
$$

Kemudian:

$$
E[\Delta P\mid Fill,state].
$$

Sehingga execution model semakin baik.

Jadi:

$$
\boxed{
Trading\ system
\rightarrow
Execution\ data
\rightarrow
Better\ execution\ model
\rightarrow
Better\ optimization.
}
$$

---

# P.63. Tetapi jangan langsung menggunakan reinforcement learning

Untuk tahap awal, saya justru menyarankan:

$$
\boxed{
Supervised/Statistical\ Models
+
Optimization
}
$$

daripada:

$$
RL.
$$

Karena kita dapat menjelaskan dengan jelas:

$$
P(Fill),
$$

$$
Slippage,
$$

$$
Impact,
$$

$$
Expected\ Return,
$$

dan objective function.

RL dapat kita pertimbangkan jauh kemudian jika diperlukan.

---

# P.64. Pipeline matematis Tahap P

Saya akan merangkumnya sebagai:

$$
\boxed{
\mathcal F_t
\rightarrow
\text{Order Book Features}
}
$$

$$
\downarrow
$$

$$
\boxed{
P(Fill\mid a,s_t)
}
$$

$$
\boxed{
E[Slippage\mid a,s_t]
}
$$

$$
\boxed{
E[\Delta P\mid a,s_t]
}
$$

$$
\downarrow
$$

$$
\boxed{
U_{exec}(a)
}
$$

$$
\downarrow
$$

$$
\boxed{
Q_{exec}
}
$$

$$
\downarrow
$$

$$
\boxed{
a^\star
}
$$

$$
\downarrow
$$

$$
\boxed{
Order\ Placement
}
$$

---

# P.65. Satu persamaan yang merangkum Tahap P

Jika saya harus memilih satu persamaan inti:

$$
\boxed{
a_t^\star
=
\arg\max_{a\in\mathcal A}
\left\{
p_F(a)
\left[
E[\Pi\mid Fill,a]
-
C_{exec}(a)
\right]
+
(1-p_F(a))
E[\Pi\mid NoFill,a]
-
\lambda R(a)
\right\}.
}
$$

Ini adalah inti **execution optimization** kita.

---

# P.66. Dan constraint paling penting tetap:

$$
\boxed{
R(a)\leq \$1.
}
$$

Bahkan setelah memasukkan:

$$
spread,
$$

$$
slippage,
$$

$$
market\ impact,
$$

$$
fees,
$$

dan:

$$
fill\ uncertainty.
$$

Jadi target awal kita:

> **"setiap trade maksimal berisiko \$1"**

sekarang menjadi jauh lebih rigor.

Bukan lagi:

$$
q(P_{entry}-SL)=1,
$$

tetapi kira-kira:

$$
\boxed{
CVaR_\alpha
\left[
q|P_{exec}-SL|
+C_{execution}
+C_{exit}
\right]
\leq \$1.
}
$$

---

# P.67. Posisi sistem kita setelah Tahap P

Kita sekarang memiliki:

$$
\boxed{
\textbf{A--O}
=
Market
\rightarrow
Forecast
\rightarrow
Risk
\rightarrow
Portfolio
\rightarrow
Entry
\rightarrow
Position\ Management
}
$$

dan Tahap P menambahkan:

$$
\boxed{
\textbf{P}
=
Execution
+
Order\ Book
+
Fill\ Probability
+
Slippage
+
Market\ Impact.
}
$$

Sehingga sistem akhirnya mulai menyerupai arsitektur **institutional systematic trading**:

$$
\boxed{
\text{Alpha}
\rightarrow
\text{Portfolio Construction}
\rightarrow
\text{Risk}
\rightarrow
\text{Execution}
\rightarrow
\text{Position Management}
}
$$

dengan optimasi kombinatorial di beberapa lapisan.

---

## Hal yang paling penting dari Tahap P

Ada satu perubahan filosofis yang menurut saya sangat penting untuk proyek kita:

> **Jangan menganggap order sebagai instruksi. Anggap order sebagai keputusan ekonomi yang memiliki probabilitas, biaya, dan konsekuensi.**

Dengan begitu:

$$
\boxed{
BUY
}
$$

bukan lagi sebuah aksi sederhana.

Ia menjadi:

$$
\boxed{
(BUY,\ price,\ quantity,\ order\ type,\ queue,\ lifetime)
}
$$

yang seluruhnya merupakan **decision variables**.

Dan karena sebagian besar variabel tersebut dapat didiskretkan, kita kembali mendapatkan problem:

$$
\boxed{
\text{Combinatorial Optimization}
\rightarrow
\text{QUBO}
\rightarrow
\text{Ising}
\rightarrow
\text{QAOA}.
}
$$

---

### Posisi kita sekarang

Arsitektur besarnya sudah menjadi:

$$
\boxed{
\begin{array}{ccccc}
\text{Market Data}
&\rightarrow&
\text{Forecast}
&\rightarrow&
\text{Risk}
\\
&&\downarrow&&
\\
&&\text{Entry QUBO}&&
\\
&&\downarrow&&
\\
&&\text{Position}&&
\\
&&\downarrow&&
\\
&&\text{Management QUBO}&&
\\
&&\downarrow&&
\\
&&\text{Execution QUBO}&&
\\
&&\downarrow&&
\\
&&\text{Order Book}&&
\\
&&\downarrow&&
\\
&&\text{Real Execution}&&
\\
&&\downarrow&&
\\
&&\text{Feedback}&&
\end{array}
}
$$

**Tahap berikutnya, Tahap Q, sebaiknya kita gunakan untuk membangun bagian yang selama ini menjadi "jembatan" antara semua model tersebut: _Backtesting Engine & Event-Driven Simulation_.** Kita perlu membuat dunia virtual yang benar-benar mensimulasikan urutan **data masuk → signal → QUBO → order → partial fill/non-fill → slippage → posisi → dynamic SL/TP → exit**, tanpa *look-ahead bias* dan tanpa *survivorship bias*. Ini krusial sebelum satu baris algoritma quantum pun dianggap memiliki performa trading yang valid.

