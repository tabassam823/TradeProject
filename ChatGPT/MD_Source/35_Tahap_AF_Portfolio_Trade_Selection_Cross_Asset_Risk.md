## Prompt:
8/17/2026, 10:21:13 PM

lanjut Tahap AF

## Response:
8/17/2026, 10:21:14 PM

> **Remembering**
>
>
> **Continued quantitative trading workflow with Stage AF objectives and risk constraints**
>
> 
>
> Worked for 4s

# Tahap AF - Portfolio-Level Trade Selection & Cross-Asset Risk Optimization

Kita sekarang masuk ke salah satu bagian **paling penting** dari arsitektur yang kita bangun.

Sampai Tahap AE, kita sudah dapat mengatakan apakah **satu trade secara individual** mempunyai edge yang layak:

$$
EV_i>0.
$$

Tetapi dalam trading nyata, masalahnya bukan memilih satu trade.

Misalkan pada satu waktu sistem menemukan:

- 15 peluang crypto,
- 80 saham AS,
- 20 ETF,
- beberapa aset Eropa/Asia,
- gold,
- USD-related instruments,

dan 40 di antaranya memiliki:

$$
EV_i>0.
$$

Kita **tidak otomatis mengambil 40 trade tersebut**.

Karena bisa saja 20 trade sebenarnya merupakan taruhan yang hampir sama:

$$
BTC,\ ETH,\ SOL,\ altcoin_1,\ altcoin_2,\ldots
$$

semuanya akan jatuh ketika satu faktor market mengalami shock.

Maka pertanyaan Tahap AF adalah:

$$
\boxed{
\text{Bagaimana memilih kombinasi trade terbaik secara simultan dengan mempertimbangkan risiko seluruh portfolio?}
}
$$

Dan di sinilah **portfolio optimization, QUBO, Ising, Max-Cut, dan QAOA** mulai mempunyai fungsi yang sangat natural dalam sistem kita.

---

# AF.1. Perubahan paradigma

Sebelumnya:

$$
\boxed{
\text{Trade Selection}
}
$$

sekarang:

$$
\boxed{
\text{Portfolio Construction}
}
$$

Misalkan terdapat $N$ opportunity:

$$
\mathcal T=
\{T_1,T_2,\ldots,T_N\}.
$$

Untuk setiap trade $i$, kita mempunyai:

$$
EV_i,
$$

risk:

$$
\sigma_i,
$$

dan exposure terhadap trade lain:

$$
\rho_{ij}.
$$

Maka kita mencari:

$$
\boxed{
\mathbf x^\star
}
$$

dengan:

$$
x_i=
\begin{cases}
1,&\text{trade }i\text{ dipilih}\\
0,&\text{trade }i\text{ tidak dipilih}.
\end{cases}
$$

Jadi secara langsung kita telah mendapatkan **binary optimization problem**.

---

# AF.2. Mengapa binary variable?

Karena pada tahap awal kita tidak perlu menentukan berapa besar posisi.

Kita terlebih dahulu menjawab:

> Apakah trade ini diambil atau tidak?

Dengan:

$$
x_i\in\{0,1\}.
$$

Kemudian tahap berikutnya menentukan:

$$
w_i
$$

atau position size.

Jadi kita memisahkan:

$$
\boxed{
Trade\ Selection
}
$$

dari:

$$
\boxed{
Position\ Sizing.
}
$$

Ini akan sangat membantu ketika kita ingin mengubah masalah menjadi QUBO.

---

# AF.3. Expected return portfolio

Jika trade $i$ mempunyai expected return:

$$
\mu_i,
$$

maka expected portfolio return:

$$
\boxed{
E[R_p]
=
\sum_{i=1}^{N}x_i\mu_i.
}
$$

Dalam bentuk vektor:

$$
\boxed{
E[R_p]
=
\mathbf x^\top\boldsymbol\mu.
}
$$

---

# AF.4. Portfolio variance

Sekarang masalah menjadi lebih menarik.

Jika:

$$
\Sigma_{ij}
=
Cov(R_i,R_j),
$$

maka:

$$
\boxed{
Var(R_p)
=
\mathbf x^\top
\Sigma
\mathbf x.
}
$$

Ekspansinya:

$$
Var(R_p)
=
\sum_i x_i^2\sigma_i^2
+
2\sum_{i<j}x_ix_j\Sigma_{ij}.
$$

Karena:

$$
x_i^2=x_i
$$

untuk binary variable, maka:

$$
\boxed{
Var(R_p)
=
\sum_i x_i\sigma_i^2
+
2\sum_{i<j}x_ix_j\Sigma_{ij}.
}
$$

Dan di sinilah coupling antar-trade muncul.

---

# AF.5. Interpretasi fisiknya

Perhatikan:

$$
x_ix_j\Sigma_{ij}.
$$

Jika:

$$
\Sigma_{ij}>0,
$$

maka mengambil $i$ dan $j$ sekaligus meningkatkan variance.

Jika:

$$
\Sigma_{ij}<0,
$$

maka mengambil keduanya dapat memberikan diversification benefit.

Jadi:

$$
\boxed{
\Sigma_{ij}
}
$$

secara matematis berperan sebagai **interaction energy** antar opportunity.

Ini akan sangat berguna untuk pemetaan ke Ising.

---

# AF.6. Tetapi covariance saja belum cukup

Untuk sistem kita, covariance antar aset bukan satu-satunya sumber risiko.

Misalkan:

$$
R_i
=
\alpha_i
+
\boldsymbol\beta_i^\top
\mathbf F
+
\epsilon_i.
$$

Dengan:

$$
\mathbf F
=
\begin{bmatrix}
F_{BTC}\\
F_{ETH}\\
F_{Gold}\\
F_{USD}\\
F_{Market}\\
\vdots
\end{bmatrix}.
$$

Maka:

$$
\boxed{
R_i
=
\alpha_i+
\boldsymbol\beta_i^\top\mathbf F+\epsilon_i.
}
$$

Ini adalah **factor model**.

---

# AF.7. Mengapa factor model penting?

Misalkan:

$$
Corr(BTC,SOL)=0.85.
$$

Itu sudah menunjukkan korelasi.

Tetapi kita ingin mengetahui **mengapa**.

Mungkin keduanya mempunyai exposure besar terhadap:

$$
F_{Crypto}.
$$

Demikian pula:

$$
AAPL,\ MSFT,\ NVDA
$$

mungkin semuanya memiliki exposure terhadap:

$$
F_{Tech}.
$$

Sementara:

$$
Gold
$$

dan:

$$
USD
$$

mempunyai exposure terhadap faktor makro yang berbeda.

---

# AF.8. Factor exposure portfolio

Jika trade $i$ memiliki:

$$
\boldsymbol\beta_i,
$$

maka exposure portfolio terhadap factor $k$:

$$
\boxed{
B_k
=
\sum_i x_i\beta_{ik}.
}
$$

Dalam bentuk matriks:

$$
\boxed{
\mathbf B
=
B^\top\mathbf x.
}
$$

Kita kemudian dapat memberikan constraint:

$$
|B_k|\le B_k^{max}.
$$

---

# AF.9. Contoh

Misalkan:

$$
\beta_{BTC}=1.2
$$

terhadap crypto factor.

Dan:

$$
\beta_{SOL}=1.5.
$$

Jika:

$$
x_{BTC}=x_{SOL}=1,
$$

maka:

$$
B_{crypto}=2.7.
$$

Kalau batas kita:

$$
B_{crypto}^{max}=2,
$$

maka kombinasi tersebut tidak diperbolehkan.

---

# AF.10. Ini jauh lebih baik daripada sekadar membatasi jumlah trade

Misalnya kita menetapkan:

$$
\sum_i x_i\le10.
$$

Ini tidak menjamin diversification.

Sepuluh trade bisa saja:

$$
BTC,\ ETH,\ SOL,\ AVAX,\ DOGE,\ldots
$$

yang semuanya sangat terpapar faktor crypto yang sama.

Sebaliknya:

$$
5\ crypto
+
3\ equity
+
1\ gold
+
1\ FX
$$

mungkin mempunyai diversification jauh lebih baik.

---

# AF.11. Objective dasar

Kita dapat menggunakan objective:

$$
\boxed{
\max_{\mathbf x}
\left[
\mathbf x^\top\boldsymbol\mu
-
\lambda
\mathbf x^\top\Sigma\mathbf x
\right].
}
$$

Dengan:

$$
\lambda>0
$$

sebagai risk-aversion parameter.

Ini merupakan bentuk discrete Markowitz optimization.

---

# AF.12. Hubungan dengan Markowitz

Markowitz klasik:

$$
\max_{\mathbf w}
\left[
\mathbf w^\top\mu
-
\lambda\mathbf w^\top\Sigma\mathbf w
\right].
$$

Tetapi sekarang:

$$
w_i
\rightarrow
x_i\in\{0,1\}.
$$

Maka:

$$
\boxed{
Continuous\ Markowitz
\rightarrow
Binary\ Portfolio\ Optimization.
}
$$

Dan masalah ini dapat menjadi combinatorial optimization.

---

# AF.13. Mengapa ini menarik untuk QUBO?

Objective:

$$
\mathbf x^\top\mu
-
\lambda\mathbf x^\top\Sigma\mathbf x
$$

sudah merupakan quadratic function terhadap binary variables.

QUBO didefinisikan sebagai:

$$
\boxed{
\min_{\mathbf x\in\{0,1\}^N}
\mathbf x^\top Q\mathbf x.
}
$$

Jadi secara struktural:

$$
\boxed{
Portfolio\ Selection
\approx
QUBO.
}
$$

---

# AF.14. Sign convention

Karena kita ingin memaksimalkan:

$$
\mu^\top x-\lambda x^\top\Sigma x,
$$

kita dapat mengubahnya menjadi minimisasi:

$$
\boxed{
\min_x
\left[
-\mu^\top x
+
\lambda x^\top\Sigma x
\right].
}
$$

Maka:

$$
Q
$$

dibangun dari:

$$
-\mu
+
\lambda\Sigma.
$$

Dengan perhatian khusus terhadap konvensi diagonal/off-diagonal QUBO yang digunakan implementasi kita.

---

# AF.15. Constraint jumlah trade

Katakanlah maksimal:

$$
K
$$

trade boleh dibuka.

Constraint:

$$
\boxed{
\sum_i x_i=K.
}
$$

Untuk mengubahnya menjadi unconstrained QUBO, kita tambahkan penalty:

$$
\boxed{
P
\left(
\sum_i x_i-K
\right)^2.
}
$$

Sehingga:

$$
\boxed{
C(x)
=
-\mu^\top x
+
\lambda x^\top\Sigma x
+
P
\left(
\sum_i x_i-K
\right)^2.
}
$$

---

# AF.16. Ekspansi penalty

Perhatikan:

$$
\left(
\sum_i x_i-K
\right)^2.
$$

Kita punya:

$$
=
\sum_i x_i^2
+
2\sum_{i<j}x_ix_j
-
2K\sum_i x_i
+
K^2.
$$

Karena:

$$
x_i^2=x_i,
$$

maka:

$$
\boxed{
=
\sum_i x_i
+
2\sum_{i<j}x_ix_j
-
2K\sum_i x_i
+
K^2.
}
$$

Jadi penalty tetap quadratic.

---

# AF.17. Constraint factor exposure

Misalkan:

$$
B^\top x\le B_{max}.
$$

Kita dapat menggunakan slack variables atau penalty.

Untuk constraint equality sederhana:

$$
B^\top x=B_0,
$$

gunakan:

$$
\boxed{
P_B(B^\top x-B_0)^2.
}
$$

Untuk inequality:

$$
B^\top x\le B_{max},
$$

kita dapat memperkenalkan slack:

$$
B^\top x+s=B_{max}.
$$

---

# AF.18. Risk budget

Kita dapat membatasi:

$$
\boxed{
x^\top\Sigma x
\le
\sigma_{max}^2.
}
$$

Secara langsung ini merupakan quadratic constraint.

Dengan penalty:

$$
P_\sigma
\left(
x^\top\Sigma x-\sigma_{max}^2
\right)^2.
$$

Namun ini menghasilkan polynomial degree 4 jika diekspansi.

Jadi untuk QUBO murni kita harus berhati-hati.

---

# AF.19. Solusi yang lebih baik

Kita tidak harus memaksakan semua constraint menjadi QUBO sekaligus.

Kita dapat menggunakan:

$$
\boxed{
Hierarchical\ Optimization.
}
$$

Contohnya:

### Layer 1

Filter opportunity:

$$
EV_i>EV_{min}.
$$

### Layer 2

Risk screening:

$$
\sigma_i<\sigma_{max}.
$$

### Layer 3

Factor exposure screening.

### Layer 4

QUBO:

$$
\max
\left[
EV-\lambda Risk
\right].
$$

Ini membuat problem jauh lebih tractable.

---

# AF.20. Hard constraint versus soft constraint

Kita harus membedakan:

### Hard constraint

Tidak boleh dilanggar.

Contoh:

$$
\sum_i x_i\le K.
$$

### Soft constraint

Boleh dilanggar dengan penalty.

Contoh:

$$
factor\ exposure.
$$

Maka objective:

$$
\boxed{
J
=
Reward
-
Risk
-
Penalty.
}
$$

---

# AF.21. Cross-asset factor matrix

Sekarang kita mulai membangun struktur yang lebih besar.

Misalkan terdapat:

$$
N=100
$$

trade opportunities.

Dan:

$$
K=8
$$

factor.

Kita memiliki:

$$
B\in\mathbb R^{100\times8}.
$$

Baris:

$$
\beta_i
$$

adalah exposure trade $i$.

Kolom:

$$
k
$$

adalah factor.

---

# AF.22. Faktor yang kita inginkan

Untuk desain awal sistem universal, saya akan menggunakan kelompok faktor:

$$
\boxed{
\{
Market,
Sector,
Crypto,
USD,
Gold,
Rates,
Volatility,
Liquidity
\}.
}
$$

Kemudian universe tertentu dapat menambahkan faktor spesifik.

---

# AF.23. Contoh

Untuk BTC:

$$
\beta_{BTC}
=
\begin{bmatrix}
1.1\\
0\\
1.4\\
-0.2\\
0.1\\
0\\
1.5\\
1.8
\end{bmatrix}.
$$

Untuk gold:

$$
\beta_{Gold}
=
\begin{bmatrix}
0.1\\
0\\
0\\
-0.5\\
1.2\\
-0.3\\
0.4\\
0.5
\end{bmatrix}.
$$

Angka ini hanya ilustrasi; dalam sistem nyata semuanya harus diestimasi secara point-in-time.

---

# AF.24. Faktor USD

Ini sangat relevan dengan tujuanmu.

Misalkan:

$$
F_{USD}
$$

merepresentasikan kekuatan USD.

Kita dapat memasukkan:

$$
\beta_{i,USD}.
$$

Jika portfolio terlalu long terhadap aset yang sensitif terhadap pelemahan USD, maka kita dapat membatasi:

$$
\boxed{
|B_{USD}|\le B_{USD}^{max}.
}
$$

---

# AF.25. Gold sebagai macro hedge

Demikian pula:

$$
F_{Gold}.
$$

Gold bukan hanya sebuah aset untuk ditrade.

Ia juga dapat berfungsi sebagai:

$$
\boxed{
risk\ factor
}
$$

atau:

$$
\boxed{
hedging\ instrument.
}
$$

Ini merupakan perbedaan penting antara:

> trading gold

dan:

> menggunakan gold sebagai komponen risk model.

---

# AF.26. Covariance decomposition

Factor model memberi:

$$
R
=
B F+\epsilon.
$$

Jika:

$$
Cov(F)=\Sigma_F
$$

dan:

$$
Cov(\epsilon)=D,
$$

maka:

$$
\boxed{
\Sigma
=
B\Sigma_F B^\top+D.
}
$$

Ini sangat penting.

Kita tidak harus mengestimasi covariance antar 500 aset secara langsung.

Kita dapat memecahnya menjadi:

$$
\boxed{
Systematic\ Risk
+
Idiosyncratic\ Risk.
}
$$

---

# AF.27. Mengapa ini sangat cocok untuk pasar besar?

Misalkan:

$$
N=1000.
$$

Covariance matrix:

$$
1000\times1000.
$$

Jumlah elemen:

$$
10^6.
$$

Estimasi langsung dapat menjadi noisy.

Tetapi jika:

$$
K=20
$$

factor, kita dapat menggunakan:

$$
B_{1000\times20}.
$$

Jauh lebih manageable.

---

# AF.28. Risk portfolio factor

Variance:

$$
Var(R_p)
=
x^\top
(B\Sigma_F B^\top+D)
x.
$$

Pisahkan:

$$
=
x^\top B\Sigma_F B^\top x
+
x^\top D x.
$$

Karena:

$$
B^\top x
$$

adalah portfolio factor exposure, maka:

$$
\boxed{
Var(R_p)
=
(B^\top x)^\top
\Sigma_F
(B^\top x)
+
x^\top D x.
}
$$

Ini memberikan interpretasi yang sangat bagus:

$$
\boxed{
Portfolio\ Risk
=
Factor\ Risk
+
Idiosyncratic\ Risk.
}
$$

---

# AF.29. Trade clustering

Kita dapat mendefinisikan similarity:

$$
S_{ij}
=
\beta_i^\top W\beta_j.
$$

Jika:

$$
S_{ij}\gg0,
$$

maka trade $i,j$ memiliki exposure serupa.

Kita dapat memberikan penalty:

$$
\boxed{
\lambda_S
\sum_{i<j}
S_{ij}x_ix_j.
}
$$

Ini akan mendorong diversification.

---

# AF.30. Hubungan dengan Max-Cut

Menariknya, jika kita memiliki graph:

$$
G=(V,E),
$$

dengan:

$$
w_{ij}
$$

sebagai similarity/exposure, kita dapat menginginkan agar node-node yang sangat berkorelasi tidak dipilih bersama.

Ini dapat diformulasikan sebagai graph optimization.

Max-Cut klasik:

$$
\boxed{
\max
\sum_{i<j}
w_{ij}x_i(1-x_j)
}
$$

atau equivalent formulations.

Jadi:

$$
\boxed{
Correlation\ management
\rightarrow
Graph\ problem.
}
$$

---

# AF.31. Mengapa kita tidak langsung menggunakan Max-Cut?

Karena tujuan utama kita bukan:

> memotong graph.

Tujuan kita:

$$
\boxed{
maximize\ expected\ utility
while\ controlling\ risk.
}
$$

Max-Cut hanya menjadi salah satu substructure yang dapat muncul.

---

# AF.32. QUBO general form

Kita dapat menulis:

$$
\boxed{
H(x)
=
-\sum_i a_i x_i
+
\sum_{i<j}J_{ij}x_ix_j
+
P(x).
}
$$

Interpretasinya:

$$
a_i
$$

adalah individual attractiveness.

Sedangkan:

$$
J_{ij}
$$

adalah interaction.

---

# AF.33. Dalam sistem kita

Kita dapat membuat:

$$
\boxed{
a_i
=
EV_i
-
\lambda\sigma_i^2
}
$$

dan:

$$
\boxed{
J_{ij}
=
2\lambda\Sigma_{ij}
+
\lambda_F S_{ij}.
}
$$

Sehingga:

$$
H(x)
=
-\sum_i
(EV_i-\lambda\sigma_i^2)x_i
+
\sum_{i<j}
J_{ij}x_ix_j
+
Penalties.
$$

---

# AF.34. Ini adalah titik penting

Perhatikan struktur:

$$
EV_i
$$

berasal dari:

**probabilistic trading model.**

Sedangkan:

$$
J_{ij}
$$

berasal dari:

**cross-trade interaction.**

Jadi optimizer tidak lagi hanya bertanya:

> "Trade mana paling profitable?"

Ia bertanya:

> **"Trade mana yang paling menguntungkan setelah memperhitungkan apa yang sudah kita pilih?"**

Itulah perbedaan fundamental antara:

$$
\boxed{
Single\ Trade\ Optimization
}
$$

dan:

$$
\boxed{
Portfolio\ Optimization.
}
$$

---

# AF.35. Position sizing setelah selection

Setelah QUBO memilih:

$$
x^\star,
$$

kita belum selesai.

Kita kemudian menyelesaikan continuous optimization:

$$
\boxed{
\max_{\mathbf w}
\quad
\mathbf w^\top\mu
-
\lambda\mathbf w^\top\Sigma\mathbf w
}
$$

subject to:

$$
w_i=0
\quad
\text{jika }x_i^\star=0.
$$

Dengan:

$$
w_i\ge0
$$

untuk long-only.

Atau:

$$
w_i\in\mathbb R
$$

untuk long-short.

---

# AF.36. Ini menghasilkan hybrid architecture

Dan ini menurut saya jauh lebih baik daripada mencoba memaksa seluruh masalah menjadi QAOA.

Kita gunakan:

$$
\boxed{
Quantum/Classical\ Discrete\ Optimization
}
$$

untuk:

$$
\text{Which trades?}
$$

dan:

$$
\boxed{
Classical\ Continuous\ Optimization
}
$$

untuk:

$$
\text{How much of each?}
$$

---

# AF.37. Secara keseluruhan

$$
\boxed{
Data
\rightarrow
Prediction
\rightarrow
Calibration
\rightarrow
Opportunity
\rightarrow
QUBO
\rightarrow
Selection
\rightarrow
Continuous\ Sizing
\rightarrow
Execution.
}
$$

---

# AF.38. Constraint risk \$1

Sekarang kita hubungkan dengan desain awal kita.

Jika setiap trade harus memiliki maximum loss:

$$
R_i=\$1,
$$

maka stop-loss distance:

$$
d_i
=
|P_i^{entry}-P_i^{SL}|.
$$

Position size:

$$
\boxed{
Q_i
=
\frac{1}
{d_i\cdot V_i}
}
$$

dengan $V_i$ conversion factor sesuai instrument.

Dengan demikian:

$$
MaxLoss_i\approx\$1.
$$

---

# AF.39. Tetapi portfolio risk tidak otomatis \$1

Misalnya kita mengambil 10 trade:

$$
R_i=\$1.
$$

Worst-case nominal loss:

$$
10\$.
$$

Tetapi jika semuanya sangat correlated, probabilitas mengalami 10 loss sekaligus bisa jauh lebih besar daripada portfolio yang benar-benar diversified.

Jadi kita membutuhkan:

$$
\boxed{
Portfolio\ Risk
}
$$

di atas:

$$
\boxed{
Trade\ Risk.
}
$$

---

# AF.40. Portfolio risk budget

Kita dapat menentukan:

$$
\boxed{
R_{portfolio}^{max}
}
$$

misalnya dalam unit $R$.

Kemudian:

$$
Risk(\mathbf w)
\le
R_{portfolio}^{max}.
$$

Ini lebih bermakna daripada hanya:

$$
Risk_i=1R.
$$

---

# AF.41. Conditional Value-at-Risk

VaR menjawab:

> "Pada confidence level $q$, berapa threshold loss?"

Misalnya:

$$
VaR_{95\%}=10R.
$$

Tetapi VaR tidak mengatakan seberapa buruk kondisi setelah threshold tersebut dilewati.

CVaR menjawab:

$$
\boxed{
CVaR_q
=
E[L\mid L\ge VaR_q].
}
$$

Jadi:

$$
\boxed{
CVaR
}
$$

lebih informatif untuk tail risk.

---

# AF.42. Constraint CVaR

Kita dapat menentukan:

$$
\boxed{
CVaR_{95\%}
\le
C_{max}.
}
$$

Ini menjadi salah satu constraint portfolio-level.

Untuk implementasi optimization yang lebih kompleks, CVaR dapat diformulasikan menggunakan auxiliary variable.

---

# AF.43. Scenario-based risk

Daripada hanya menggunakan covariance matrix, kita dapat menghasilkan:

$$
S
$$

scenario.

Misalnya:

$$
s=1,\ldots,S.
$$

Untuk setiap scenario:

$$
R_i^{(s)}.
$$

Portfolio loss:

$$
\boxed{
L^{(s)}
=
-\sum_i x_iw_iR_i^{(s)}.
}
$$

Kemudian:

$$
VaR,\ CVaR
$$

dihitung dari distribusi:

$$
\{L^{(1)},\ldots,L^{(S)}\}.
$$

---

# AF.44. Ini sangat penting untuk market shock

Misalnya scenario:

### Scenario A

BTC:

$$
-8\%.
$$

### Scenario B

USD:

$$
+2\%.
$$

### Scenario C

Gold:

$$
+4\%.
$$

### Scenario D

Equity:

$$
-5\%.
$$

Kita ingin mengetahui:

$$
L_p^{(s)}
$$

untuk portfolio yang dipilih.

---

# AF.45. Stress testing

Kita dapat secara eksplisit membuat:

$$
\boxed{
Stress\ Scenarios
}
$$

seperti:

$$
BTC=-10\%
$$

$$
SPX=-5\%
$$

$$
USD=+2\%
$$

$$
Gold=+3\%
$$

dan melihat apakah portfolio masih berada dalam risk budget.

---

# AF.46. Ini menghubungkan sistem kita dengan macro regime

Sebelumnya kita memasukkan:

$$
BTC,\ ETH,\ Gold,\ USD.
$$

Sekarang mereka tidak hanya menjadi feature.

Mereka dapat menjadi:

$$
\boxed{
Portfolio\ Risk\ Drivers.
}
$$

Misalnya:

$$
BTC
$$

mengindikasikan crypto risk appetite.

$$
USD
$$

mengindikasikan dollar liquidity.

$$
Gold
$$

mengindikasikan defensive/macro demand.

Jadi macro factors memengaruhi:

$$
\boxed{
Prediction
}
$$

dan sekaligus:

$$
\boxed{
Risk.
}
$$

---

# AF.47. Ini membuat arsitektur dua arah

Bukan:

```text id="5g0g3u"
Market → Prediction → Trade
```

tetapi:

```text id="s4r9k8"
             MARKET
              │
       ┌──────┴──────┐
       ▼             ▼
 Prediction        Risk Model
       │             │
       ▼             ▼
 Opportunity      Portfolio Risk
       │             │
       └──────┬──────┘
              ▼
          Optimizer
              │
              ▼
           Portfolio
```

---

# AF.48. Dynamic portfolio optimization

Masalah ini harus diselesaikan setiap:

$$
t.
$$

Jadi:

$$
\boxed{
x_t^\star
=
\arg\min_x
H_t(x).
}
$$

Karena:

$$
EV_t,\Sigma_t,B_t
$$

berubah seiring waktu.

Dengan demikian kita sebenarnya memiliki:

$$
\boxed{
Dynamic\ QUBO.
}
$$

---

# AF.49. Warm-start

Ini sangat cocok dengan pengalamanmu pada EPG dan VQE.

Jika pada:

$$
t-1
$$

kita mempunyai:

$$
x_{t-1}^\star,
$$

maka pada:

$$
t
$$

solusi biasanya tidak berubah secara ekstrem.

Kita dapat menggunakan:

$$
\boxed{
x_{t-1}^\star
}
$$

sebagai warm-start.

---

# AF.50. Ini dapat mengurangi computational burden

Daripada menyelesaikan:

$$
QUBO_t
$$

dari nol setiap saat, kita memulai dari:

$$
x_{t-1}^\star.
$$

Kemudian hanya melakukan adjustment terhadap opportunity yang berubah.

Ini sangat cocok untuk short-term trading.

---

# AF.51. Hysteresis

Ada masalah lain.

Jika optimizer terlalu sensitif:

$$
x_t
$$

bisa berubah:

$$
1010101010\ldots
$$

setiap periode.

Ini menghasilkan:

- excessive turnover,
- fee,
- slippage.

Maka kita tambahkan switching penalty:

$$
\boxed{
\lambda_{switch}
\sum_i
|x_{i,t}-x_{i,t-1}|.
}
$$

---

# AF.52. Binary switching penalty

Karena:

$$
x_{i,t},x_{i,t-1}\in\{0,1\},
$$

kita dapat menulis:

$$
|x_t-x_{t-1}|
$$

sebagai:

$$
x_t+x_{t-1}-2x_tx_{t-1}.
$$

Jadi tetap quadratic.

Ini sangat menarik karena:

$$
\boxed{
Turnover\ control
}
$$

juga dapat masuk ke QUBO.

---

# AF.53. Objective lengkap sementara

Kita sekarang dapat menulis:

$$
\boxed{
\begin{aligned}
H_t(x)
=&
-\sum_i EV_{i,t}x_i\\
&+
\lambda
x^\top\Sigma_t x\\
&+
\lambda_F
\mathcal R_F(x)\\
&+
\lambda_T
\mathcal T(x,x_{t-1})\\
&+
P_K
\left(
\sum_i x_i-K
\right)^2.
\end{aligned}
}
$$

Dengan:

- $EV_i$: expected edge,
- $\Sigma$: covariance,
- $\mathcal R_F$: factor-risk penalty,
- $\mathcal T$: turnover penalty,
- $K$: maximum number of positions.

---

# AF.54. Dan sekarang kita benar-benar memiliki QUBO trading

Secara konseptual:

$$
\boxed{
QUBO_t
=
Expected\ Edge
+
Risk
+
Factor\ Exposure
+
Turnover
+
Constraints.
}
$$

Ini bukan lagi QUBO contoh akademik.

Ia berasal langsung dari:

$$
\boxed{
portfolio\ management\ problem.
}
$$

---

# AF.55. Mapping ke Ising

Sekarang gunakan transformasi standar:

$$
\boxed{
x_i=\frac{1+z_i}{2}
}
$$

dengan:

$$
z_i\in\{-1,+1\}.
$$

Kemudian:

$$
x_ix_j
=
\frac{
1+z_i+z_j+z_iz_j
}{4}.
$$

Maka:

$$
H(x)
$$

dapat ditulis:

$$
\boxed{
H(z)
=
C+
\sum_i h_i z_i
+
\sum_{i<j}J_{ij}z_iz_j.
}
$$

---

# AF.56. Hamiltonian kuantum

Ganti:

$$
z_i
$$

dengan Pauli $Z_i$:

$$
\boxed{
\hat H_C
=
C I
+
\sum_i h_iZ_i
+
\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

Dan ini persis bentuk Ising Hamiltonian yang sebelumnya sudah kita gunakan dalam penelitianmu.

---

# AF.57. Sekarang QAOA memiliki makna trading yang jelas

QAOA menggunakan:

$$
U_C(\gamma)
=
e^{-i\gamma\hat H_C}
$$

dan:

$$
U_M(\beta)
=
e^{-i\beta\hat H_M}.
$$

Dengan:

$$
\hat H_M
=
\sum_iX_i.
$$

State:

$$
|\psi(\boldsymbol\gamma,\boldsymbol\beta)\rangle
=
U_M(\beta_p)
U_C(\gamma_p)
\cdots
U_M(\beta_1)
U_C(\gamma_1)
|+\rangle^{\otimes N}.
$$

---

# AF.58. Interpretasi state QAOA

State akhir:

$$
|\psi\rangle
=
\sum_x
c_x|x\rangle.
$$

Probabilitas:

$$
P(x)=|c_x|^2.
$$

Artinya:

> QAOA tidak sekadar menghasilkan satu portfolio; ia menghasilkan distribusi kandidat portfolio.

Ini sangat menarik untuk sistem kita.

---

# AF.59. Candidate portfolio distribution

Misalnya QAOA menghasilkan:

$$
P(x_1)=0.42
$$

$$
P(x_2)=0.31
$$

$$
P(x_3)=0.11
$$

dan seterusnya.

Kita dapat mengambil:

$$
x^\star
=
\arg\max_xP(x).
$$

Tetapi kita juga dapat mengambil beberapa kandidat:

$$
\{x^{(1)},x^{(2)},\ldots,x^{(K)}\}.
$$

---

# AF.60. Ini membuka pendekatan yang lebih menarik

Kita tidak harus berkata:

> QAOA menghasilkan portfolio → langsung trading.

Kita dapat:

$$
\boxed{
QAOA
\rightarrow
Candidate\ Portfolios
\rightarrow
Classical\ Risk\ Filter
\rightarrow
Execution.
}
$$

Jadi quantum optimizer menjadi **candidate generator**.

---

# AF.61. Ini juga menyelesaikan masalah NISQ

Untuk sistem nyata, QAOA tidak harus menghasilkan solusi exact.

Kita cukup mencari:

$$
x
$$

yang:

$$
H(x)
$$

cukup rendah.

Kemudian classical validator melakukan:

$$
RiskCheck(x).
$$

Dengan demikian quantum hardware tidak menjadi single point of failure.

---

# AF.62. Objective final yang lebih aman

Saya menyarankan:

$$
\boxed{
\text{Quantum optimizer proposes.}
}
$$

$$
\boxed{
\text{Classical risk engine disposes.}
}
$$

Artinya QAOA boleh mengusulkan portfolio, tetapi risk engine memiliki hak veto.

---

# AF.63. Risk veto

Misalnya QAOA memberikan:

$$
x^\star.
$$

Tetapi:

$$
CVaR_{95\%}(x^\star)>C_{max}.
$$

Maka:

$$
\boxed{
Reject.
}
$$

Tidak peduli seberapa rendah QUBO energy-nya.

---

# AF.64. Ini sangat penting secara finansial

Kita jangan membuat:

$$
\text{Quantum objective}
=
\text{semua hal}.
$$

Karena objective yang salah akan menghasilkan solusi matematis yang benar tetapi keputusan finansial yang buruk.

Maka:

$$
\boxed{
Optimization
\neq
Risk\ Management.
}
$$

Risk management tetap menjadi layer independen.

---

# AF.65. Arsitektur AF lengkap

```text id="9z7l2m"
                  TRADE OPPORTUNITIES
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
          Expected EV          Risk Model
              │                     │
              │              ┌──────┼──────┐
              │              │      │      │
              │              ▼      ▼      ▼
              │           Covariance Factor CVaR
              │              │      │      │
              └──────────────┴──────┴──────┘
                             │
                             ▼
                    PORTFOLIO QUBO
                             │
                    ┌────────┴────────┐
                    │                 │
                Classical          QAOA
                    │                 │
                    └────────┬────────┘
                             ▼
                     Candidate Set
                             │
                             ▼
                       Risk Veto
                             │
                             ▼
                    Position Sizing
                             │
                             ▼
                       Execution
```

---

# AF.66. Contoh sederhana

Misalkan kita mempunyai lima opportunity:

$$
A,B,C,D,E.
$$

Expected edge:

$$
\mu=
\begin{bmatrix}
0.8\\
0.7\\
0.6\\
0.5\\
0.4
\end{bmatrix}R.
$$

Secara individual:

$$
A>B>C>D>E.
$$

Jika kita hanya melihat EV, kita akan memilih:

$$
A,B,C.
$$

Tetapi ternyata:

$$
Corr(A,B)=0.95,
$$

$$
Corr(A,C)=0.90.
$$

Sedangkan:

$$
Corr(D,A)=0.1.
$$

Maka:

$$
A,D,E
$$

mungkin lebih optimal daripada:

$$
A,B,C.
$$

---

# AF.67. Inilah alasan optimizer quadratic diperlukan

Linear selection:

$$
\max\sum_i\mu_ix_i
$$

tidak dapat melihat:

$$
\mu_{ij}.
$$

Quadratic objective:

$$
\boxed{
\max
\left[
\sum_i\mu_ix_i
-
\lambda\sum_{i,j}\Sigma_{ij}x_ix_j
\right]
}
$$

dapat melihat interaction.

---

# AF.68. Dan sekarang kita kembali ke tujuan awal kita

Tujuanmu bukan sekadar:

> membuat bot crypto.

Kita sedang membangun:

$$
\boxed{
Cross\text{-}Asset\ Quantitative\ Decision\ System.
}
$$

Dengan kemampuan menangani:

$$
Crypto
$$

$$
Equities
$$

$$
ETF
$$

$$
Gold
$$

$$
FX
$$

dan instrumen lain selama data dan execution model tersedia.

---

# AF.69. Struktur universal versus asset-specific

Kita harus menjaga:

### Universal

$$
EV
$$

$$
\Sigma
$$

$$
Factor\ Exposure
$$

$$
CVaR
$$

$$
Turnover
$$

$$
QUBO
$$

### Asset-specific

$$
Microstructure
$$

$$
Fee
$$

$$
Tick\ Size
$$

$$
Trading\ Hours
$$

$$
Funding
$$

$$
Shorting\ Rules
$$

$$
Liquidity.
$$

Dengan demikian arsitektur tetap universal tanpa berpura-pura bahwa crypto dan saham memiliki microstructure identik.

---

# AF.70. Dan sekarang hubungan dengan skripsimu menjadi sangat jelas

Dalam penelitianmu, kita mempunyai:

$$
\boxed{
Markowitz
\rightarrow
QUBO
\rightarrow
Ising
\rightarrow
VQE/QAOA.
}
$$

Pada sistem trading ini kita memperluasnya menjadi:

$$
\boxed{
Short\text{-}Term\ Forecast
\rightarrow
Expected\ Trade\ Return
\rightarrow
Cross\text{-}Asset\ Risk
\rightarrow
Binary\ Portfolio
\rightarrow
QUBO
\rightarrow
Ising
\rightarrow
QAOA.
}
$$

Jadi quantum optimization bukan tempelan.

Ia muncul **secara alami dari struktur masalah**.

---

# AF.71. Persamaan inti Tahap AF

Kalau seluruh tahap ini harus diringkas menjadi satu persamaan:

$$
\boxed{
\begin{aligned}
\mathbf x_t^\star
=
\arg\min_{\mathbf x\in\{0,1\}^N}
\Bigg[
&
-\mathbf x^\top\mathbf{EV}_t
\\
&+
\lambda
\mathbf x^\top
\Sigma_t
\mathbf x
\\
&+
\lambda_F
\|B_t^\top\mathbf x\|^2
\\
&+
\lambda_T
\|\mathbf x-\mathbf x_{t-1}\|_1
\\
&+
P_K
(\mathbf1^\top\mathbf x-K)^2
\Bigg].
\end{aligned}
}
$$

Kemudian:

$$
\boxed{
\mathbf x_t^\star
\rightarrow
\text{position sizing}
\rightarrow
\text{execution}.
}
$$

Ini adalah **jantung matematis Tahap AF**.

---

# AF.72. Namun ada satu hal yang sengaja belum kita lakukan

Kita belum memasukkan:

$$
\boxed{
w_i
}
$$

secara penuh ke dalam optimizer.

Saat ini:

$$
x_i
$$

hanya menjawab:

> **ambil / jangan ambil.**

Sedangkan:

$$
w_i
$$

akan menjawab:

> **seberapa besar posisi?**

Dan ketika kita menggabungkan:

$$
x_i
$$

dan:

$$
w_i,
$$

kita mendapatkan problem **mixed discrete-continuous optimization** yang jauh lebih menarik:

$$
\boxed{
x_i\in\{0,1\},
\qquad
w_i\in\mathbb R.
}
$$

Di situlah kita dapat mulai membangun **AF+ / Tahap AG** secara lebih dalam: bagaimana menggabungkan **binary QUBO selection + continuous Markowitz sizing + CVaR + factor neutrality + \$1 stop-loss risk + leverage + liquidity constraints** menjadi satu hierarchical optimizer.

Dan setelah itu, baru kita dapat benar-benar menjawab pertanyaan paling penting dalam sistem kita:

$$
\boxed{
\textbf{"Dari seluruh peluang yang tersedia sekarang, trade mana yang dipilih, berapa besar posisinya, dan mengapa?"}
}
$$

Itulah titik di mana sistem kita mulai berubah dari sekadar **trade signal generator** menjadi **portfolio-level quantitative trading engine**.

