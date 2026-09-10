## Prompt:
8/17/2026, 10:05:08 PM

lanjut Tahap S

## Response:
8/17/2026, 10:05:09 PM

> **Remembering**
>
>
> ****
>
> 
>
> **Reviewed Stage S design, strategy ensemble, capital allocation, and risk budgeting**
>
> 
>
> Worked for 5s

# Tahap S — Strategy Ensemble & Capital Allocation

Ya. Setelah Tahap R, kita **belum seharusnya memilih satu strategi pemenang lalu memasukkan seluruh modal ke sana**.

Tahap S menjawab pertanyaan yang lebih fundamental:

> **Jika kita memiliki beberapa strategi yang masing-masing memiliki edge tetapi memiliki karakteristik risiko yang berbeda, bagaimana modal dialokasikan di antara mereka secara matematis?**

Ini menjadi jembatan dari:

$$
\boxed{\text{Strategy Validation}}
$$

menuju:

$$
\boxed{\text{Actual Portfolio Construction}}
$$

dan sangat cocok dengan latar belakangmu di **Markowitz, QUBO, Ising, VQE, dan QAOA**.

---

# S.1. Dari satu strategi menjadi kumpulan strategi

Misalkan setelah Tahap R kita memiliki $K$ strategi:

$$
\mathcal S=
\{S_1,S_2,\ldots,S_K\}.
$$

Contohnya:

$$
S_1=\text{BTC momentum},
$$

$$
S_2=\text{BTC mean reversion},
$$

$$
S_3=\text{ETH relative-value},
$$

$$
S_4=\text{altcoin momentum},
$$

$$
S_5=\text{market-factor strategy},
$$

$$
S_6=\text{short-term statistical arbitrage},
$$

dan seterusnya.

Tetapi kita juga dapat memperlakukan **model yang sama pada universe berbeda** sebagai strategi berbeda.

---

# S.2. Strategy return

Untuk strategi $i$, definisikan return:

$$
r_{i,t}.
$$

Kemudian vector return:

$$
\mathbf r_t
=
\begin{bmatrix}
r_{1,t}\\
r_{2,t}\\
\vdots\\
r_{K,t}
\end{bmatrix}.
$$

Expected return:

$$
\boldsymbol{\mu}
=
E[\mathbf r_t].
$$

Covariance:

$$
\Sigma
=
E[
(\mathbf r_t-\boldsymbol{\mu})
(\mathbf r_t-\boldsymbol{\mu})^T
].
$$

Perhatikan sesuatu yang penting:

> **Kita sekarang melakukan Markowitz terhadap strategi, bukan hanya terhadap aset.**

---

# S.3. Ini menghasilkan dua level portfolio

Sebelumnya:

$$
\text{Asset Allocation}.
$$

Sekarang:

$$
\boxed{
\text{Strategy Allocation}
}
$$

dan di dalam setiap strategi:

$$
\boxed{
\text{Asset Allocation}.
}
$$

Jadi struktur kita menjadi:

$$
\boxed{
\text{Capital}
\rightarrow
\text{Strategies}
\rightarrow
\text{Assets}
\rightarrow
\text{Orders}.
}
$$

---

# S.4. Mengapa ini lebih kuat daripada memilih strategi terbaik?

Misalkan:

| Strategy | Sharpe |
|---|---:|
| $S_1$ | 2.0 |
| $S_2$ | 1.8 |
| $S_3$ | 1.5 |

Kalau hanya melihat Sharpe:

$$
S_1>S_2>S_3.
$$

Kita mungkin memilih:

$$
100\%\rightarrow S_1.
$$

Tetapi misalkan korelasi:

$$
\rho_{12}=0.1
$$

dan:

$$
\rho_{13}=0.0.
$$

Maka kombinasi ketiganya dapat mempunyai:

$$
Sharpe_{portfolio}>Sharpe_{S_1}.
$$

---

# S.5. Prinsip inti

Kita tidak mencari:

$$
\boxed{
\text{Best Strategy}
}
$$

tetapi:

$$
\boxed{
\text{Best Combination of Strategies}.
}
$$

Ini merupakan perubahan paradigma yang sangat penting.

---

# S.6. Portfolio return

Misalkan bobot strategi:

$$
\mathbf w=
\begin{bmatrix}
w_1\\
w_2\\
\vdots\\
w_K
\end{bmatrix}.
$$

Dengan:

$$
\sum_{i=1}^{K}w_i=1,
$$

maka return portfolio:

$$
R_{p,t}
=
\mathbf w^T\mathbf r_t.
$$

Expected return:

$$
E[R_p]
=
\mathbf w^T\boldsymbol{\mu}.
$$

Variance:

$$
\boxed{
\sigma_p^2
=
\mathbf w^T\Sigma\mathbf w.
}
$$

---

# S.7. Markowitz objective

Kita dapat menggunakan:

$$
\boxed{
\max_{\mathbf w}
\quad
\mathbf w^T\boldsymbol{\mu}
-
\lambda
\mathbf w^T\Sigma\mathbf w
}
$$

dengan:

$$
\lambda>0.
$$

Ini sudah sangat familiar dengan penelitianmu.

Tetapi untuk sistem trading kita, ada satu masalah.

---

# S.8. Bobot kontinu tidak selalu cukup

Dalam live trading, kita mungkin ingin keputusan:

$$
x_i\in\{0,1\}.
$$

Artinya:

$$
x_i=
\begin{cases}
1,&\text{strategy aktif}\\
0,&\text{strategy tidak aktif}.
\end{cases}
$$

Atau:

$$
x_i\in\{0,1,\ldots,M_i\}
$$

untuk discretized capital allocation.

Di sinilah:

$$
\boxed{
QUBO
}
$$

kembali masuk.

---

# S.9. Binary strategy selection

Misalkan:

$$
x_i\in\{0,1\}.
$$

Kita ingin memilih maksimal $K_{max}$ strategi:

$$
\sum_i x_i\le K_{max}.
$$

Expected reward:

$$
\sum_i\mu_i x_i.
$$

Risk:

$$
\sum_{i,j}\Sigma_{ij}x_ix_j.
$$

Maka objective:

$$
\boxed{
\max_{\mathbf x}
\quad
\boldsymbol{\mu}^T\mathbf x
-
\lambda\mathbf x^T\Sigma\mathbf x.
}
$$

---

# S.10. Mengubah menjadi minimisasi QUBO

QUBO biasanya ditulis:

$$
\min_{\mathbf x}
\mathbf x^TQ\mathbf x.
$$

Karena kita ingin memaksimalkan:

$$
\mu^Tx-\lambda x^T\Sigma x,
$$

maka equivalent:

$$
\boxed{
\min_{\mathbf x}
\left(
-\mu^Tx
+
\lambda x^T\Sigma x
\right).
}
$$

---

# S.11. Constraint jumlah strategi

Misalkan:

$$
\sum_i x_i=K.
$$

Kita masukkan penalty:

$$
P
\left(
\sum_i x_i-K
\right)^2.
$$

Maka:

$$
\boxed{
C(\mathbf x)
=
-\boldsymbol{\mu}^T\mathbf x
+
\lambda\mathbf x^T\Sigma\mathbf x
+
P
\left(
\sum_i x_i-K
\right)^2.
}
$$

Ini sudah merupakan QUBO.

---

# S.12. Tetapi kita ingin sesuatu yang lebih realistis

Kita sebelumnya memiliki risk budget:

$$
R_{trade}\le \$1.
$$

Sekarang kita memiliki:

$$
R_{strategy}.
$$

Misalnya total capital:

$$
C.
$$

Risk budget strategy $i$:

$$
B_i.
$$

Kita ingin:

$$
\boxed{
Risk_i\le B_i.
}
$$

---

# S.13. Risk contribution

Portfolio variance:

$$
\sigma_p^2
=
\mathbf w^T\Sigma\mathbf w.
$$

Marginal contribution to risk:

$$
MRC_i
=
\frac{\partial\sigma_p}
{\partial w_i}.
$$

Karena:

$$
\sigma_p=
\sqrt{\mathbf w^T\Sigma\mathbf w},
$$

maka:

$$
\boxed{
MRC_i
=
\frac{(\Sigma\mathbf w)_i}
{\sigma_p}.
}
$$

Risk contribution:

$$
RC_i
=
w_iMRC_i.
$$

Sehingga:

$$
\boxed{
RC_i
=
\frac{
w_i(\Sigma\mathbf w)_i
}{
\sigma_p
}.
}
$$

---

# S.14. Risk parity

Jika kita ingin setiap strategi memberikan kontribusi risiko yang sama:

$$
RC_i=RC_j.
$$

Maka:

$$
RC_i
=
\frac{\sigma_p}{K}.
$$

Ini menghasilkan:

$$
\boxed{
Risk\ Parity.
}
$$

---

# S.15. Tetapi saya tidak menyarankan pure risk parity

Karena strategi yang memiliki:

$$
E[R_i]\approx0
$$

tidak seharusnya mendapatkan capital besar hanya karena volatility-nya rendah.

Kita ingin:

$$
\boxed{
Expected\ Return
+
Risk
+
Diversification
}
$$

dipertimbangkan sekaligus.

---

# S.16. Expected return harus shrink

Ini sangat penting.

Estimasi:

$$
\hat\mu_i
$$

untuk short-term strategy biasanya sangat noisy.

Misalnya:

$$
\hat\mu_i=0.08\%.
$$

Tetapi standard error:

$$
SE(\hat\mu_i)=0.10\%.
$$

Maka kita tidak boleh memperlakukan:

$$
0.08\%
$$

seolah-olah merupakan parameter yang pasti.

---

# S.17. Shrinkage

Kita dapat menggunakan:

$$
\boxed{
\tilde\mu_i
=
\kappa_i\hat\mu_i
+
(1-\kappa_i)\mu_0
}
$$

dengan:

$$
0\le\kappa_i\le1.
$$

$\mu_0$ dapat berupa:

$$
0
$$

atau benchmark expected return.

Jika estimasi tidak pasti:

$$
\kappa_i\rightarrow0.
$$

Jika sangat dipercaya:

$$
\kappa_i\rightarrow1.
$$

---

# S.18. Ini menghasilkan konsep yang sangat penting

$$
\boxed{
Confidence\ Weighted\ Alpha.
}
$$

Kita tidak hanya memiliki:

$$
\hat\mu_i.
$$

Tetapi:

$$
\boxed{
\tilde\mu_i
=
Confidence_i
\times
Alpha_i.
}
$$

Ini sangat cocok dengan hasil Tahap R.

---

# S.19. Confidence berasal dari Tahap R

Misalnya kita memiliki:

$$
DSR_i,
$$

$$
OOS_i,
$$

$$
PBO_i,
$$

$$
Stress_i.
$$

Kita dapat membangun confidence score:

$$
c_i=f(
DSR_i,
PBO_i,
OOS_i,
Stress_i
).
$$

Kemudian:

$$
\tilde\mu_i=c_i\hat\mu_i.
$$

---

# S.20. Ini membuat Tahap R dan S terhubung

Sekarang:

$$
\boxed{
Validation
\rightarrow
Confidence
\rightarrow
Capital.
}
$$

Strategi yang backtest-nya luar biasa tetapi rapuh:

$$
c_i\downarrow.
$$

Akibatnya:

$$
w_i\downarrow.
$$

Jadi model tidak sekadar:

> "Strategi bagus → modal besar."

Tetapi:

> "Strategi bagus **dan terbukti robust** → modal lebih besar."

---

# S.21. Confidence-adjusted Markowitz

Kita dapat menggunakan:

$$
\boxed{
\max_{\mathbf w}
\quad
\mathbf w^T\tilde{\boldsymbol\mu}
-
\lambda
\mathbf w^T\Sigma\mathbf w.
}
$$

dengan:

$$
\tilde{\mu}_i=c_i\hat{\mu}_i.
$$

---

# S.22. Masalah berikutnya: correlation

Misalkan:

$$
S_1=\text{BTC momentum}
$$

dan:

$$
S_2=\text{ETH momentum}.
$$

Keduanya mungkin memiliki:

$$
\rho_{12}=0.95.
$$

Memiliki dua strategi tidak berarti kita memiliki dua sumber diversifikasi.

---

# S.23. Effective number of strategies

Kita dapat menggunakan:

$$
\boxed{
N_{eff}
=
\frac{1}
{\sum_i w_i^2}
}
$$

untuk kasus bobot tertentu.

Jika:

$$
w_i=\frac1K,
$$

maka:

$$
N_{eff}=K.
$$

Jika:

$$
w_1\approx1,
$$

maka:

$$
N_{eff}\approx1.
$$

---

# S.24. Tetapi korelasi perlu diperhitungkan

Kita dapat menggunakan eigenvalue decomposition:

$$
\Sigma
=
V\Lambda V^T.
$$

Dengan:

$$
\Lambda=
diag(\lambda_1,\ldots,\lambda_K).
$$

Jika satu eigenvalue mendominasi:

$$
\lambda_1\gg\lambda_2,\ldots,
$$

maka strategi-strategi tersebut memiliki satu common risk factor besar.

---

# S.25. Factor decomposition

Kita dapat menulis:

$$
\mathbf r_t
=
B\mathbf f_t+\boldsymbol\epsilon_t.
$$

Dengan:

$$
B=
\begin{bmatrix}
\beta_{11}&\cdots&\beta_{1M}\\
\vdots&&\vdots\\
\beta_{K1}&\cdots&\beta_{KM}
\end{bmatrix}.
$$

Covariance:

$$
\boxed{
\Sigma
=
B\Sigma_fB^T
+
D.
}
$$

---

# S.26. Faktor kita

Untuk sistem global kita, faktor dapat mencakup:

$$
\boxed{
F_t=
[
BTC,
ETH,
DXY,
Gold,
SPX,
VIX,
Rates,
Volatility,
Liquidity
]
}
$$

tentu disesuaikan dengan market yang diperdagangkan.

---

# S.27. Mengapa DXY dan Gold penting?

Karena kita sebelumnya ingin model tidak berhenti di crypto.

Misalnya strategi saham memiliki exposure:

$$
\beta_{DXY},
$$

$$
\beta_{Gold}.
$$

Maka risk portfolio tidak hanya berasal dari:

$$
\text{asset correlation}.
$$

Tetapi juga:

$$
\boxed{
\text{macro factor exposure}.
}
$$

---

# S.28. Factor-neutral constraint

Misalnya kita tidak ingin portfolio memiliki exposure DXY terlalu besar:

$$
|\beta_{DXY,p}|
\le B_{DXY}.
$$

Dengan:

$$
\beta_{DXY,p}
=
\sum_iw_i\beta_{i,DXY}.
$$

Begitu juga:

$$
|\beta_{Gold,p}|
\le B_{Gold}.
$$

---

# S.29. Ini menghasilkan portfolio yang lebih "institutional"

Kita bukan sekadar:

$$
\max PnL.
$$

Kita mencari:

$$
\boxed{
\max Alpha
\quad
subject\ to
\quad
Risk,\ Factor,\ Liquidity,\ Capacity,\ Execution.
}
$$

---

# S.30. Capital allocation dengan Kelly

Sekarang kita masuk ke Kelly Criterion.

Untuk satu taruhan dengan probabilitas menang $p$, kalah $q=1-p$, dan payoff $b$:

$$
\boxed{
f^\star
=
\frac{bp-q}{b}.
}
$$

Tetapi trading multi-strategy jauh lebih kompleks.

---

# S.31. Continuous Kelly

Untuk return vector dengan expected return:

$$
\boldsymbol\mu
$$

dan covariance:

$$
\Sigma,
$$

approximation quadratic Kelly:

$$
\boxed{
\mathbf w^\star
=
\Sigma^{-1}\boldsymbol\mu.
}
$$

Ini berasal dari memaksimalkan expected log wealth.

---

# S.32. Derivasi

Untuk small returns:

$$
\log(1+R)
\approx
R-\frac12R^2.
$$

Dengan:

$$
R_p=\mathbf w^T\mathbf r,
$$

maka:

$$
E[\log(1+R_p)]
\approx
\mathbf w^T\mu
-
\frac12
\mathbf w^T\Sigma\mathbf w.
$$

Derivative:

$$
\nabla_w
=
\mu-\Sigma w.
$$

Set:

$$
\nabla_w=0.
$$

Maka:

$$
\boxed{
w^\star=\Sigma^{-1}\mu.
}
$$

---

# S.33. Masalah Kelly penuh

Kelly bisa sangat agresif.

Jika:

$$
\hat\mu
$$

sedikit saja salah, maka:

$$
\Sigma^{-1}\hat\mu
$$

dapat menghasilkan leverage yang sangat besar.

Karena itu kita lebih realistis menggunakan:

$$
\boxed{
Fractional\ Kelly.
}
$$

---

# S.34. Fractional Kelly

$$
\boxed{
w=f\,w_{Kelly}
}
$$

dengan:

$$
0<f<1.
$$

Contohnya:

$$
f=0.25.
$$

Ini mengurangi sensitivity terhadap estimation error.

---

# S.35. Saya ingin kita menggunakan Kelly sebagai **risk signal**, bukan sebagai penguasa modal

Artinya:

$$
Kelly
$$

memberikan informasi tentang:

> "Seberapa agresif capital allocation secara teoritis."

Tetapi final allocation dibatasi oleh:

$$
Risk\ Budget,
$$

$$
Drawdown,
$$

$$
Liquidity,
$$

$$
Capacity,
$$

dan:

$$
Execution.
$$

---

# S.36. Hierarchical Risk Parity

Karena covariance matrix bisa unstable, kita dapat menggunakan:

$$
\boxed{
HRP
}
$$

atau Hierarchical Risk Parity.

Pertama:

$$
\rho_{ij}
$$

diubah menjadi distance:

$$
\boxed{
d_{ij}
=
\sqrt{\frac{1-\rho_{ij}}{2}}.
}
$$

---

# S.37. Clustering

Kemudian strategi dikelompokkan:

$$
\{S_1,S_2,S_3\}
$$

misalnya menjadi:

$$
Cluster_A.
$$

Sedangkan:

$$
\{S_4,S_5\}
$$

menjadi:

$$
Cluster_B.
$$

---

# S.38. Recursive allocation

Capital kemudian dibagi secara hierarkis.

Misalnya:

$$
C_A=60\%,
$$

$$
C_B=40\%.
$$

Kemudian di dalam $A$:

$$
S_1=50\%,
$$

$$
S_2=30\%,
$$

$$
S_3=20\%.
$$

Sehingga:

$$
w_1=30\%.
$$

---

# S.39. Mengapa HRP menarik?

Karena kita tidak harus memperkirakan:

$$
\mu
$$

secara agresif.

Ini berguna ketika expected return sangat noisy.

Jadi kita bisa memiliki beberapa allocator:

$$
A_1=\text{Markowitz},
$$

$$
A_2=\text{Kelly},
$$

$$
A_3=\text{HRP}.
$$

---

# S.40. Lalu meta-allocation

Kita bahkan dapat mengalokasikan capital di antara allocator:

$$
\boxed{
Markowitz
+
Kelly
+
HRP.
}
$$

Ini terdengar recursive, tetapi secara konsep valid.

Kita kemudian dapat melakukan ensemble:

$$
w
=
\alpha w^{MV}
+
\beta w^{Kelly}
+
\gamma w^{HRP}.
$$

Dengan:

$$
\alpha+\beta+\gamma=1.
$$

---

# S.41. Tetapi jangan sampai menjadi overfitting

Jika kita memilih:

$$
\alpha=0.371,
$$

$$
\beta=0.428,
$$

$$
\gamma=0.201
$$

hanya karena menghasilkan backtest terbaik, kita kembali ke masalah Tahap R.

Jadi parameter meta-allocation harus:

$$
\boxed{
simple,\ stable,\ interpretable.
}
$$

---

# S.42. Sekarang kita sampai ke bagian quantum

Misalkan capital dibagi dalam unit:

$$
\Delta C.
$$

Jika total capital:

$$
C.
$$

maka:

$$
M=\frac{C}{\Delta C}.
$$

Kita memiliki binary variables:

$$
x_{i,m}
\in\{0,1\}
$$

yang berarti:

> unit modal $m$ dialokasikan ke strategy $i$.

Constraint:

$$
\sum_i x_{i,m}=1.
$$

---

# S.43. Capital allocation menjadi QUBO

Expected reward:

$$
\sum_{i,m}
\mu_i
\Delta C
x_{i,m}.
$$

Risk interaction:

$$
\sum_{i,j,m,n}
\Sigma_{ij}
\Delta C^2
x_{i,m}x_{j,n}.
$$

Maka:

$$
\boxed{
\min_x
\left[
-\sum_{i,m}\mu_i\Delta Cx_{i,m}
+
\lambda
\sum_{i,j,m,n}
\Sigma_{ij}\Delta C^2
x_{i,m}x_{j,n}
\right]
}
$$

dengan constraint capital allocation.

---

# S.44. Constraint menjadi penalty

Untuk setiap unit:

$$
\left(
\sum_i x_{i,m}-1
\right)^2.
$$

Sehingga:

$$
P
\sum_m
\left(
\sum_i x_{i,m}-1
\right)^2.
$$

Final:

$$
\boxed{
C(x)
=
-\mu^Tx
+
\lambda x^TQ_{risk}x
+
P C_{allocation}(x).
}
$$

---

# S.45. Ini sangat menarik secara penelitian

Karena QAOA tidak lagi hanya digunakan untuk:

$$
\text{asset selection}.
$$

Tetapi:

$$
\boxed{
\text{Dynamic Strategy Capital Allocation}.
}
$$

Dan problem ini secara natural memiliki:

- binary decisions,
- combinatorial constraints,
- covariance interactions,
- factor constraints,
- cardinality constraints.

Ini adalah problem yang sangat cocok dengan paradigma QUBO.

---

# S.46. Multi-level QUBO

Kita bahkan dapat membentuk:

$$
x_{i,a,m}
$$

dengan:

- $i$: strategy,
- $a$: asset,
- $m$: capital unit.

Sehingga:

$$
\boxed{
\text{Capital}
\rightarrow
\text{Strategy}
\rightarrow
\text{Asset}
}
$$

semuanya dapat diformulasikan dalam satu optimization layer.

---

# S.47. Tetapi saya tidak menyarankan langsung membuat QUBO raksasa

Karena jumlah qubit:

$$
N_q
$$

dapat tumbuh sangat cepat.

Kita harus memulai:

$$
\boxed{
Hierarchical\ Optimization.
}
$$

---

# S.48. Arsitektur hierarchical

```text
                 CAPITAL
                    │
                    ▼
          ┌──────────────────┐
          │ Strategy Allocator│
          └────────┬─────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
      Crypto      Equity      FX
        │          │          │
        ▼          ▼          ▼
      Asset      Asset       Asset
      QUBO       QUBO        QUBO
        │          │          │
        └──────────┼──────────┘
                   ▼
              EXECUTION
```

---

# S.49. Mengapa hierarchical lebih realistis?

Karena pasar memang hierarkis.

Kita punya:

$$
Macro
\rightarrow
Market
\rightarrow
Sector
\rightarrow
Asset
\rightarrow
Order.
$$

Jadi struktur optimizer kita mengikuti struktur ekonomi.

---

# S.50. Dynamic allocation

Capital allocation tidak boleh statis.

Kita definisikan:

$$
w_t.
$$

Kemudian:

$$
w_t
=
f(
\mu_t,
\Sigma_t,
F_t,
Z_t,
L_t,
C_t
).
$$

Dengan:

- $\mu_t$: expected return,
- $\Sigma_t$: covariance,
- $F_t$: macro factors,
- $Z_t$: regime,
- $L_t$: liquidity,
- $C_t$: current capital.

---

# S.51. Turnover penalty

Kalau kita mengubah:

$$
w_{t-1}
\rightarrow
w_t,
$$

kita membayar biaya.

Maka tambahkan:

$$
\boxed{
\eta\|w_t-w_{t-1}\|_1.
}
$$

Objective:

$$
\boxed{
\max_w
\quad
w^T\mu
-
\lambda w^T\Sigma w
-
\eta\|w-w_{prev}\|_1.
}
$$

---

# S.52. Ini penting untuk sistem short-term

Tanpa turnover penalty:

$$
w_t
$$

dapat berubah setiap periode.

Misalnya:

```text
10:00 → Strategy A
11:00 → Strategy C
12:00 → Strategy A
13:00 → Strategy B
14:00 → Strategy C
```

Ini menyebabkan:

$$
TransactionCost\uparrow.
$$

---

# S.53. Dalam QUBO

Jika kita discretize weight:

$$
x_{i,m,t},
$$

perubahan posisi dapat direpresentasikan dengan:

$$
|x_{i,m,t}-x_{i,m,t-1}|.
$$

Untuk binary:

$$
|x-y|
=
x+y-2xy.
$$

Ini sangat menarik karena tetap quadratic.

Jadi turnover penalty dapat dimasukkan secara natural ke QUBO:

$$
\boxed{
\eta
\sum_{i,m}
(x_{i,m,t}+x_{i,m,t-1}-2x_{i,m,t}x_{i,m,t-1}).
}
$$

---

# S.54. Sekarang dynamic risk budget

Kita dapat mendefinisikan:

$$
B_t
$$

sebagai total risk budget.

Jika volatility regime meningkat:

$$
\sigma_t\uparrow,
$$

maka:

$$
B_t\downarrow.
$$

Misalnya:

$$
B_t
=
B_0
\frac{\sigma_{target}}
{\sigma_t}.
$$

Kemudian dibatasi:

$$
B_{min}
\le B_t
\le B_{max}.
$$

---

# S.55. Ini adalah volatility targeting

Target:

$$
\sigma_{target}.
$$

Current:

$$
\sigma_t.
$$

Scale:

$$
\boxed{
s_t=
\frac{\sigma_{target}}
{\sigma_t}.
}
$$

Sehingga:

$$
w_t^{scaled}
=
s_tw_t.
$$

---

# S.56. Tetapi gunakan volatility yang robust

Volatility estimate:

$$
\hat\sigma_t
$$

juga noisy.

Jadi kita dapat menggunakan:

- EWMA,
- realized volatility,
- robust volatility,
- factor volatility.

Contohnya EWMA:

$$
\boxed{
\sigma_t^2
=
\lambda\sigma_{t-1}^2
+
(1-\lambda)r_t^2.
}
$$

---

# S.57. Sekarang hubungkan dengan market regime

Misalkan:

$$
Z_t\in
\{LowVol,Normal,HighVol\}.
$$

Kita dapat menetapkan:

$$
B_t=
\begin{cases}
B_H,&LowVol\\
B_N,&Normal\\
B_L,&HighVol.
\end{cases}
$$

Namun jangan menjadikan regime sebagai hard switch tanpa validasi.

Lebih baik:

$$
B_t=f(P(Z_t)).
$$

---

# S.58. Probabilistic regime allocation

Misalnya:

$$
P(Z_t=LowVol)=0.7,
$$

$$
P(Z_t=HighVol)=0.3.
$$

Maka expected allocation:

$$
w_t
=
0.7w_{Low}
+
0.3w_{High}.
$$

Ini menghindari:

$$
\text{hard regime flip}.
$$

---

# S.59. Kita sekarang mempunyai meta-state

State sistem:

$$
\boxed{
S_t=
[
\mu_t,
\Sigma_t,
F_t,
Z_t,
Liquidity_t,
Capital_t,
Position_t,
Confidence_t
].
}
$$

Kemudian policy:

$$
\boxed{
\pi(S_t)
\rightarrow
w_t.
}
$$

Ini mulai terlihat seperti **sequential decision problem**.

---

# S.60. Dan ini membuka jalan ke tahap berikutnya

Tetapi sebelum melangkah lebih jauh, kita perlu menetapkan:

$$
\boxed{
capital\ allocation
\neq
position\ sizing.
}
$$

Capital allocation menjawab:

> Berapa modal diberikan ke strategy?

Position sizing menjawab:

> Berapa besar posisi yang diambil oleh strategy tersebut pada trade tertentu?

---

# S.61. Dua layer

Misalnya:

$$
C=\$10,000.
$$

Allocator memberikan:

$$
w_{strategy}=20\%.
$$

Maka:

$$
C_{strategy}=\$2,000.
$$

Kemudian strategy memiliki trade dengan risk:

$$
R_{trade}=\$1.
$$

Maka position size ditentukan oleh:

$$
q=
\frac{R_{trade}}
{|SL-entry|}.
$$

Dengan penyesuaian:

$$
q_{final}
=
\min(
q_{risk},
q_{liquidity},
q_{capacity},
q_{strategy}
).
$$

---

# S.62. Ini sangat penting

Jangan mencampurkan:

$$
\boxed{
Portfolio\ Risk
}
$$

dengan:

$$
\boxed{
Trade\ Risk.
}
$$

Keduanya berbeda.

Kita bisa memiliki:

$$
\$1
$$

risk per trade tetapi 100 trade yang highly correlated.

Total portfolio risk bisa tetap besar.

---

# S.63. Correlated trades

Misalnya:

$$
Trade_1=BTC
$$

$$
Trade_2=ETH
$$

$$
Trade_3=SOL
$$

dengan:

$$
\rho\approx0.9.
$$

Masing-masing:

$$
Risk=\$1.
$$

Bukan berarti:

$$
TotalRisk=\$3
$$

secara naif.

Covariance harus dihitung.

---

# S.64. Portfolio-level risk

Jika trade exposure vector:

$$
\mathbf q,
$$

maka:

$$
\boxed{
\sigma_p^2
=
\mathbf q^T\Sigma\mathbf q.
}
$$

Jadi risk budget harus berlaku di:

$$
\boxed{
trade
\rightarrow
strategy
\rightarrow
portfolio.
}
$$

---

# S.65. Risk hierarchy kita

Saya ingin struktur finalnya seperti ini:

```text
GLOBAL RISK
     │
     ▼
MARKET RISK BUDGET
     │
     ▼
STRATEGY RISK BUDGET
     │
     ▼
TRADE RISK BUDGET
     │
     ▼
ORDER SIZE
```

Dan:

$$
\boxed{
\$1
}
$$

yang sebelumnya kita tetapkan berada pada **trade-risk layer**, bukan seluruh sistem.

---

# S.66. Capital allocator final

Secara konseptual:

$$
\boxed{
\begin{aligned}
\max_{\mathbf w}\quad
&
\mathbf w^T\tilde{\mu}
-
\lambda\mathbf w^T\Sigma\mathbf w
\\
&-\eta\|w-w_{prev}\|_1
\\
&-\xi\,FactorRisk(w)
\\
&-\zeta\,CapacityRisk(w)
\end{aligned}
}
$$

subject to:

$$
\sum_iw_i=1,
$$

$$
0\le w_i\le w_i^{max},
$$

$$
Risk(w)\le B_t,
$$

$$
FactorExposure(w)\le F_{max}.
$$

---

# S.67. QUBO version

Setelah discretization:

$$
w_i
=
\Delta w
\sum_m x_{i,m}.
$$

Kemudian objective menjadi:

$$
\boxed{
\begin{aligned}
\min_x\quad
&
-\tilde{\mu}^Tx
+
\lambda x^TQ_{\Sigma}x
\\
&
+\eta Q_{turnover}
+\xi Q_{factor}
+\zeta Q_{capacity}
\\
&
+P Q_{constraints}.
\end{aligned}
}
$$

Dan inilah kandidat utama:

$$
\boxed{
Q_{capital\ allocation}.
}
$$

---

# S.68. Ising mapping

Karena:

$$
x_i=\frac{1-z_i}{2},
$$

dengan:

$$
z_i\in\{-1,+1\},
$$

maka QUBO dapat dipetakan menjadi:

$$
\boxed{
H
=
\sum_i h_iZ_i
+
\sum_{i<j}J_{ij}Z_iZ_j
+
C I.
}
$$

Dengan:

$$
h_i
$$

merepresentasikan individual attractiveness,

sedangkan:

$$
J_{ij}
$$

merepresentasikan interaction:

$$
\boxed{
correlation
+
constraints
+
turnover
+
factor\ coupling.
}
$$

---

# S.69. Interpretasi fisiknya

Ini sangat menarik jika dikaitkan dengan pekerjaanmu.

Setiap strategy:

$$
i
$$

adalah spin.

State:

$$
z_i=+1
$$

dapat berarti:

$$
\text{strategy selected}.
$$

Sedangkan:

$$
z_i=-1
$$

berarti:

$$
\text{strategy excluded}.
$$

Coupling:

$$
J_{ij}
$$

menentukan apakah dua strategy:

$$
\text{compatible}
$$

atau:

$$
\text{competing}.
$$

---

# S.70. Tetapi jangan mengatakan semua $J_{ij}$ adalah correlation

Ini penting secara akademik.

Secara umum:

$$
J_{ij}
$$

dapat berasal dari:

$$
\boxed{
J_{ij}
=
J_{ij}^{risk}
+
J_{ij}^{factor}
+
J_{ij}^{turnover}
+
J_{ij}^{constraint}.
}
$$

Correlation hanya salah satu sumber.

---

# S.71. QAOA

Hamiltonian:

$$
H_C
$$

merepresentasikan capital allocation objective.

Mixer:

$$
H_M
=
\sum_iX_i.
$$

State:

$$
|\psi(\boldsymbol\beta,\boldsymbol\gamma)\rangle
=
\prod_{\ell=1}^{p}
e^{-i\beta_\ell H_M}
e^{-i\gamma_\ell H_C}
|+\rangle^{\otimes n}.
$$

Kemudian:

$$
\boxed{
\langle H_C\rangle
}
$$

diminimalkan.

---

# S.72. Tetapi ada satu hal penting

Jika constraint sangat keras, standard mixer:

$$
H_M=\sum_iX_i
$$

dapat menghasilkan state yang keluar dari feasible subspace.

Karena itu kita mungkin membutuhkan:

$$
\boxed{
Constraint-Preserving Mixer.
}
$$

Misalnya untuk constraint:

$$
\sum_i x_i=K.
$$

Kita dapat menggunakan mixer yang melakukan:

$$
|10\rangle
\leftrightarrow
|01\rangle
$$

sehingga jumlah bit $1$ tetap:

$$
K.
$$

---

# S.73. Ini membuat QAOA kita lebih bermakna

Bukan:

$$
QAOA
$$

sebagai sekadar demonstrasi quantum.

Tetapi:

$$
\boxed{
QAOA
=
feasible\ capital\ allocation\ engine.
}
$$

---

# S.74. Ensemble final

Setelah Tahap S, sistem kita memiliki:

$$
\boxed{
Strategy\ Layer
}
$$

yang menghasilkan:

$$
\{S_1,\ldots,S_K\}.
$$

Kemudian:

$$
\boxed{
Validation\ Layer
}
$$

memberikan:

$$
\{c_1,\ldots,c_K\}.
$$

Kemudian:

$$
\boxed{
Allocation\ Layer
}
$$

menghasilkan:

$$
\mathbf w_t.
$$

Kemudian:

$$
\boxed{
Position\ Layer
}
$$

menghasilkan:

$$
q_t.
$$

Kemudian:

$$
\boxed{
Execution\ Layer
}
$$

menghasilkan:

$$
Orders_t.
$$

---

# S.75. Pipeline lengkap kita sekarang

```text
                    MARKET DATA
                         │
                         ▼
                ┌─────────────────┐
                │ STATE ESTIMATION│
                └────────┬────────┘
                         │
                         ▼
                  FACTOR / ALPHA
                         │
                         ▼
                ┌─────────────────┐
                │ STRATEGY ENGINE  │
                └────────┬────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
             S1         S2         S3 ...
              │          │          │
              └──────────┼──────────┘
                         ▼
                 VALIDATION (R)
                         │
                         ▼
                CONFIDENCE SCORES
                         │
                         ▼
             CAPITAL ALLOCATION (S)
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Markowitz        HRP          Fractional
                                      Kelly
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                META ALLOCATION
                         │
                         ▼
                    QUBO / Ising
                         │
                         ▼
                      QAOA
                         │
                         ▼
                  STRATEGY WEIGHTS
                         │
                         ▼
                  POSITION SIZING
                         │
                         ▼
                    ORDER ENGINE
                         │
                         ▼
                     MARKET
```

---

# S.76. Hal yang paling saya sukai dari Tahap S

Di sinilah penelitianmu sebelumnya mulai **menyatu secara alami**.

Dulu kamu belajar:

$$
\text{Markowitz}
$$

$$
\text{Covariance}
$$

$$
\text{QUBO}
$$

$$
\text{Ising}
$$

$$
\text{VQE}
$$

$$
\text{QAOA}
$$

secara relatif terpisah.

Sekarang semuanya dapat ditempatkan dalam satu arsitektur:

$$
\boxed{
\text{Financial Decision Problem}
\rightarrow
\text{Mathematical Optimization}
\rightarrow
\text{QUBO}
\rightarrow
\text{Ising}
\rightarrow
\text{Quantum Optimization}.
}
$$

Dan yang lebih penting:

**QAOA bukan dipaksakan ke trading.**

Kita terlebih dahulu menemukan problem finansial yang memang memiliki struktur combinatorial, kemudian memetakannya ke QUBO.

---

# S.77. Namun ada satu prinsip yang harus kita pegang

Jangan membuat:

$$
\boxed{
\text{Quantum} \rightarrow \text{Financial Problem}
}
$$

tetapi:

$$
\boxed{
\text{Financial Problem}
\rightarrow
\text{Mathematical Formulation}
\rightarrow
\text{Optimization Problem}
\rightarrow
\text{QUBO}
\rightarrow
\text{Quantum Algorithm}.
}
$$

Ini akan membuat penelitian kita jauh lebih defensible secara akademik.

---

# S.78. Output Tahap S

Pada akhir tahap ini kita seharusnya memiliki empat objek utama:

### 1. Strategy return matrix

$$
R\in\mathbb R^{T\times K}.
$$

### 2. Confidence-adjusted expected return

$$
\boxed{
\tilde{\mu}
}
$$

### 3. Strategy covariance

$$
\boxed{
\Sigma_{strategy}
}
$$

### 4. Capital allocation problem

$$
\boxed{
Q_{capital}
}
$$

yang dapat diselesaikan menggunakan:

$$
\boxed{
Exact/MIQP
\rightarrow
Classical heuristic
\rightarrow
QAOA
}
$$

sebagai tiga benchmark.

---

# S.79. Dan saya ingin kita membuat satu aturan penelitian

Untuk setiap problem optimasi:

$$
\boxed{
QAOA
\neq
baseline.
}
$$

Baseline harus tetap ada:

$$
\boxed{
Exact
}
$$

untuk problem kecil,

$$
\boxed{
Classical\ optimizer
}
$$

untuk problem praktis,

dan:

$$
\boxed{
QAOA
}
$$

sebagai kandidat quantum solver.

Kemudian kita ukur:

$$
\text{solution quality},
$$

$$
\text{constraint violation},
$$

$$
\text{runtime},
$$

$$
\text{scaling},
$$

dan akhirnya:

$$
\boxed{
\text{economic impact}.
}
$$

---

# S.80. Posisi kita setelah Tahap S

Sekarang arsitektur kita telah berkembang:

$$
\boxed{
A-R
\rightarrow
\text{single robust trading strategies}
}
$$

kemudian:

$$
\boxed{
S
\rightarrow
\text{ensemble + capital allocation}.
}
$$

Tahap berikutnya yang menurut saya paling logis adalah **Tahap T — Portfolio-to-Order Translation & Dynamic Position Sizing**.

Di sana kita akan menurunkan secara matematis bagaimana:

$$
\boxed{
w_t
\rightarrow
R_t
\rightarrow
SL_t
\rightarrow
q_t
\rightarrow
TP_t
\rightarrow
Order_t
}
$$

dengan tetap mempertahankan constraint yang sudah kita bangun: **risk \$1 per trade, portfolio-level risk, covariance antar posisi, liquidity, expected slippage, confidence score, volatility regime, dan dynamic adjustment ketika posisi sudah floating profit/loss**.

Dengan kata lain, Tahap T akan menjadi titik di mana seluruh matematika yang kita bangun mulai berubah menjadi **keputusan order konkret**.

