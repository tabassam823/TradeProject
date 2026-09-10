## Prompt:
8/17/2026, 10:12:59 PM

lanjut Tahap Z

## Response:
8/17/2026, 10:13:01 PM

# Tahap Z — Concrete Model Specification & Implementation Blueprint

Baik. **Tahap Z adalah transisi dari desain matematis ke sistem yang benar-benar dapat diimplementasikan.**

Sampai Tahap Y kita sudah mempunyai:

$$
\mathcal F_t
\rightarrow
s_t
\rightarrow
(\hat\mu_t,\hat\Sigma_t)
\rightarrow
H_t
\rightarrow
x_t^\star
\rightarrow
w_t^\star
\rightarrow
q_t^\star
\rightarrow
O_t
\rightarrow
s_{t+1}.
$$

Sekarang kita harus menjawab pertanyaan yang jauh lebih konkret:

> **"Data apa yang masuk? Diproses bagaimana? Persamaan persisnya apa? Output tiap modul apa? Dan di mana QUBO/Ising/VQE/QAOA benar-benar digunakan?"**

Saya akan membuat Tahap Z sebagai **blueprint teknis versi 1.0**. Kita jangan langsung coding sebelum struktur ini konsisten.

---

# Z.1. Prinsip desain utama

Saya ingin kita memisahkan sistem menjadi **10 layer**:

$$
\boxed{
\text{Data}
\rightarrow
\text{Feature}
\rightarrow
\text{Factor}
\rightarrow
\text{Regime}
\rightarrow
\text{Forecast}
\rightarrow
\text{Optimization}
\rightarrow
\text{Risk}
\rightarrow
\text{Execution}
\rightarrow
\text{Position Management}
\rightarrow
\text{Evaluation}
}
$$

Secara arsitektur:

```text
                    ┌──────────────────┐
                    │ Historical Data  │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │ Feature Engine   │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │ Factor Engine    │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │ Regime Detector  │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │ Forecast Engine  │
                    │ μ̂, Σ̂            │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │ Optimization     │
                    │ QUBO / Ising     │
                    └────────┬─────────┘
                             ▼
                 ┌───────────┴───────────┐
                 ▼                       ▼
          Classical Solver        VQE / QAOA
                 │                       │
                 └───────────┬───────────┘
                             ▼
                    ┌──────────────────┐
                    │ Risk Engine      │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │ Execution Engine │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │ Position Manager │
                    └────────┬─────────┘
                             │
                             ▼
                         New State
                             │
                             └──────► kembali
```

---

# Z.2. Jangan langsung mulai dengan 500 aset

Ini keputusan desain yang penting.

Versi pertama sebaiknya menggunakan **small controlled universe**.

Misalnya untuk crypto:

$$
\mathcal A_{crypto}
=
\{
BTC,ETH,SOL,BNB,XRP,\ldots
\}
$$

sekitar:

$$
N=8-20.
$$

Untuk saham:

$$
\mathcal A_{equity}
=
\{
AAPL,MSFT,NVDA,AMZN,\ldots
\}.
$$

Dan factor:

$$
\mathcal F=
\{
SPX,NDX,DXY,Gold,VIX,US10Y
\}.
$$

Tujuannya bukan membuat sistem terbesar.

Tujuannya:

$$
\boxed{
\text{make the mathematics auditable}.
}
$$

---

# Z.3. Multi-asset universe

Saya menyarankan kita mendefinisikan tiga kategori.

### Tier 1 — Target assets

Asset yang benar-benar boleh ditradingkan:

$$
\mathcal A_T.
$$

Contoh:

$$
\mathcal A_T=
\{
SOL,XRP,ADA,\ldots
\}.
$$

### Tier 2 — Market leaders

Asset yang digunakan sebagai explanatory factors:

$$
\mathcal A_M=
\{
BTC,ETH
\}.
$$

### Tier 3 — Macro factors

$$
\mathcal A_F=
\{
DXY,Gold,VIX,SPX,NDX,US10Y
\}.
$$

Dengan demikian:

$$
\boxed{
\mathcal A
=
\mathcal A_T
\cup
\mathcal A_M
\cup
\mathcal A_F.
}
$$

---

# Z.4. Timeframe

Kita perlu membedakan:

### Data resolution

Misalnya:

$$
\Delta t=1h.
$$

### Decision interval

Misalnya:

$$
\Delta t_D=1h.
$$

### Execution resolution

Misalnya:

$$
\Delta t_E=1m.
$$

Ini sangat penting.

Kita tidak boleh melakukan:

> prediksi 1 jam → eksekusi menggunakan harga close 1 jam

tanpa memodelkan bagaimana order benar-benar terisi.

Jadi:

$$
\boxed{
1h
\rightarrow
decision
}
$$

sedangkan:

$$
\boxed{
1m
\rightarrow
execution.
}
$$

---

# Z.5. Dataset utama

Untuk setiap asset $i$, kita simpan:

$$
D_{i,t}
=
[
O,H,L,C,V
].
$$

Dengan:

- $O$: open,
- $H$: high,
- $L$: low,
- $C$: close,
- $V$: volume.

Untuk order book:

$$
OB_t
=
[
B_1,A_1,
Q_{B1},Q_{A1},
\ldots
].
$$

---

# Z.6. Return

Kita gunakan log return:

$$
\boxed{
r_{i,t}
=
\ln
\frac{P_{i,t}}
{P_{i,t-1}}.
}
$$

Untuk multi-asset:

$$
\mathbf r_t
=
[
r_{1,t},
r_{2,t},
\ldots,
r_{N,t}
]^\top.
$$

---

# Z.7. Feature vector

Untuk setiap asset:

$$
X_{i,t}
=
[
r_t,
r_{t-1},
\ldots,
r_{t-L},
Vol_t,
Momentum_t,
ATR_t,
RSI_t,
\ldots
].
$$

Tetapi saya menyarankan **jangan memasukkan puluhan indikator teknikal sejak awal**.

Kita ingin mengetahui kontribusi setiap kelompok informasi.

Maka feature groups:

$$
X_t=
[
X_t^{price},
X_t^{volume},
X_t^{factor},
X_t^{orderflow},
X_t^{regime}
].
$$

---

# Z.8. Factor matrix

Misalkan kita mempunyai:

$$
K
$$

factor.

Maka:

$$
F_t
=
\begin{bmatrix}
f_{1,t}\\
f_{2,t}\\
\vdots\\
f_{K,t}
\end{bmatrix}.
$$

Contoh:

$$
F_t=
[
r_{BTC},
r_{ETH},
r_{DXY},
r_{Gold},
r_{SPX},
r_{VIX},
r_{US10Y}
]^\top.
$$

---

# Z.9. Standardisasi

Karena skala masing-masing factor berbeda:

$$
z_{k,t}
=
\frac{
f_{k,t}-\mu_{k,t}^{train}
}{
\sigma_{k,t}^{train}
}.
$$

Penting:

$$
\mu_{k,t}^{train}
$$

dan:

$$
\sigma_{k,t}^{train}
$$

harus dihitung **hanya menggunakan data yang tersedia sampai waktu training tersebut**.

Tidak boleh:

$$
\text{fit scaler pada seluruh dataset}.
$$

Itu data leakage.

---

# Z.10. Factor model

Kita gunakan:

$$
\boxed{
r_{i,t+1}
=
\alpha_{i,t}
+
\beta_{i,t}^\top F_t
+
\epsilon_{i,t+1}.
}
$$

Secara matrix:

$$
\boxed{
\mathbf r_{t+1}
=
\alpha_t
+
B_tF_t
+
\epsilon_{t+1}.
}
$$

---

# Z.11. Estimasi beta

Untuk versi awal:

$$
\hat\beta_i
=
(X^\top X)^{-1}X^\top y_i.
$$

Namun untuk rolling system:

$$
\hat\beta_{i,t}
=
\operatorname{OLS}
(
r_{i,t-L:t},
F_{t-L:t}
).
$$

Jadi beta berubah terhadap waktu.

---

# Z.12. Expected return

Kita memperoleh:

$$
\boxed{
\hat\mu_t
=
\hat\alpha_t
+
\hat B_tF_t.
}
$$

Tetapi saya menyarankan kita tidak berhenti di sini.

Kita dapat menambahkan signal component:

$$
\hat\mu_t
=
\hat\mu_t^{factor}
+
\hat\mu_t^{signal}.
$$

Misalnya:

$$
\boxed{
\hat\mu_t
=
B_tF_t+
g_\theta(X_t).
}
$$

Dengan demikian:

- factor model memberikan economic structure,
- signal model menangkap nonlinear residual behavior.

---

# Z.13. Versi pertama tidak perlu deep learning

Ini keputusan penting.

Untuk baseline:

$$
g_\theta
$$

bisa berupa:

- linear regression,
- ridge,
- elastic net,
- random forest,
- gradient boosting.

Baru setelah baseline valid, kita bandingkan dengan model neural.

Karena kalau langsung menggunakan deep learning dan hasil bagus:

> kita tidak tahu apakah keuntungan berasal dari model atau leakage/overfitting.

---

# Z.14. Covariance matrix

Residual:

$$
\hat\epsilon_t
=
r_t-
\hat\alpha_t-
\hat B_tF_t.
$$

Covariance factor:

$$
\Sigma_F
=
\operatorname{Cov}(F).
$$

Residual covariance:

$$
D
=
\operatorname{Cov}(\epsilon).
$$

Kemudian:

$$
\boxed{
\hat\Sigma_t
=
\hat B_t
\Sigma_{F,t}
\hat B_t^\top
+
D_t.
}
$$

---

# Z.15. Shrinkage

Covariance matrix short-term biasanya noisy.

Maka kita dapat menggunakan:

$$
\boxed{
\Sigma_{shrunk}
=
\rho T
+
(1-\rho)\Sigma.
}
$$

dengan:

- $T$: target covariance,
- $\rho$: shrinkage intensity.

Ini penting karena optimizer sangat sensitif terhadap covariance.

---

# Z.16. Regime engine

Kita definisikan:

$$
z_t
\in
\{1,\ldots,K\}.
$$

Feature regime:

$$
Y_t=
[
\sigma_t,
VIX_t,
Trend_t,
Breadth_t,
Liquidity_t,
\ldots
].
$$

Versi pertama dapat menggunakan:

$$
\boxed{
z_t
=
\operatorname{HMM}(Y_t).
}
$$

Misalnya:

$$
K=3.
$$

---

# Z.17. Tiga regime awal

Saya menyarankan:

$$
z_t=
\begin{cases}
1 & \text{Calm}\\
2 & \text{Trending}\\
3 & \text{Stress}.
\end{cases}
$$

Kemudian:

$$
\lambda_t
=
\lambda(z_t).
$$

Misalnya secara konseptual:

$$
\lambda_{stress}
>
\lambda_{calm}.
$$

---

# Z.18. Regime juga mengubah expected return

Bukan hanya risk aversion.

Kita dapat menggunakan:

$$
\boxed{
\mu_t
=
\mu^{(z_t)}
+
B^{(z_t)}F_t.
}
$$

Dan:

$$
\boxed{
\Sigma_t
=
B^{(z_t)}
\Sigma_F^{(z_t)}
B^{(z_t)\top}
+
D^{(z_t)}.
}
$$

Ini menjadikan model **regime conditional**.

---

# Z.19. Sekarang masuk ke optimizer

Kita mendefinisikan binary variable:

$$
x_i=
\begin{cases}
1,&asset\ i\ selected\\
0,&otherwise.
\end{cases}
$$

Portfolio:

$$
x\in\{0,1\}^N.
$$

---

# Z.20. Objective

Kita mulai dengan:

$$
\boxed{
H(x)
=
-\mu^\top x
+
\lambda x^\top\Sigma x.
}
$$

Interpretasi:

$$
-\mu^\top x
$$

berusaha memaksimalkan expected return.

Sedangkan:

$$
\lambda x^\top\Sigma x
$$

menghukum risk.

---

# Z.21. Capital constraint

Misalkan setiap asset mempunyai allocation weight $w_i$.

Constraint:

$$
\sum_i w_ix_i\le1.
$$

Penalty:

$$
P_c
\left(
\sum_iw_ix_i-1
\right)^2.
$$

---

# Z.22. Cardinality

Jika maksimum asset:

$$
K_{max},
$$

maka:

$$
\sum_i x_i\le K_{max}.
$$

Penalty:

$$
P_K
\left(
\sum_i x_i-K_{max}
\right)^2.
$$

Jika kita ingin **tepat** $K$:

$$
\boxed{
P_K
\left(
\sum_i x_i-K
\right)^2.
}
$$

---

# Z.23. Turnover

Misalkan:

$$
x_i^{old}.
$$

Biaya:

$$
C_{turn}
=
c_i|x_i-x_i^{old}|.
$$

Karena binary:

$$
|x_i-x_i^{old}|
=
x_i+x_i^{old}
-
2x_ix_i^{old}.
$$

Sehingga:

$$
C_{turn}
=
\sum_i
c_i
(
x_i+x_i^{old}
-
2x_ix_i^{old}
).
$$

Ini quadratic.

Sangat cocok untuk QUBO.

---

# Z.24. Final QUBO

Maka versi pertama:

$$
\boxed{
\begin{aligned}
H_t(x)
={}&
-\mu_t^\top x
+
\lambda_t x^\top\Sigma_t x\\
&+
\sum_i
c_i
|x_i-x_i^{old}|\\
&+
P_K
\left(
\sum_i x_i-K
\right)^2\\
&+
P_C
\left(
\sum_iw_ix_i-C
\right)^2.
\end{aligned}
}
$$

Ini adalah **QUBO utama sistem kita**.

---

# Z.25. Constraint tambahan

Nanti kita dapat menambahkan:

### Maximum sector exposure

$$
\sum_{i\in sector\,j}x_i
\le K_j.
$$

### Maximum correlated assets

$$
x_i+x_j\le1.
$$

### Minimum liquidity

$$
x_i=0
\quad
\text{if}
\quad
ADV_i<ADV_{min}.
$$

### Maximum leverage

$$
\sum_i|w_i|\le L.
$$

Semua ini dapat kita ubah menjadi binary constraints/penalties jika diperlukan.

---

# Z.26. Penalty coefficient

Ini bagian yang sangat sering salah.

Tidak boleh asal:

$$
P=1.
$$

Secara prinsip:

$$
P
>
\text{maximum possible objective gain from violating constraint}.
$$

Misalnya:

$$
P_K
>
\max_x
|\mu^\top x|.
$$

Namun kita harus hati-hati karena penalty terlalu besar juga membuat landscape numeriknya buruk.

Maka nanti kita lakukan:

$$
P\in
\{P_1,P_2,\ldots,P_m\}
$$

dan melakukan sensitivity analysis.

---

# Z.27. QUBO → Ising

Gunakan:

$$
x_i=
\frac{1-Z_i}{2}.
$$

Secara umum:

$$
H(x)
\rightarrow
H(Z).
$$

Kemudian:

$$
\boxed{
H(Z)
=
C
+
\sum_i h_iZ_i
+
\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

Quantum Hamiltonian:

$$
\boxed{
\hat H
=
CI+
\sum_i h_iZ_i+
\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

---

# Z.28. Jumlah qubit

Jika:

$$
N=10
$$

asset binary:

$$
\boxed{
n_q=10.
}
$$

Jika kita menggunakan long/short encoding:

$$
x_i^+,x_i^-,
$$

maka:

$$
\boxed{
n_q=2N.
}
$$

Untuk tahap awal saya sangat menyarankan:

$$
\boxed{
N=8\text{--}12
}
$$

supaya kita dapat membandingkan:

$$
Exact
\leftrightarrow
Classical
\leftrightarrow
VQE
\leftrightarrow
QAOA.
$$

---

# Z.29. Exact solver adalah wajib

Jangan langsung membandingkan:

> VQE vs market.

Kita harus memiliki ground truth.

Untuk:

$$
N=10,
$$

jumlah kemungkinan:

$$
2^{10}=1024.
$$

Kita dapat brute force seluruh state.

Sehingga:

$$
x_{exact}^\star
=
\arg\min_{x\in\{0,1\}^{10}}
H(x).
$$

Ini memberi:

$$
E_{exact}.
$$

---

# Z.30. Quantum approximation ratio

Jika QAOA/VQE menghasilkan:

$$
E_Q,
$$

sedangkan optimum:

$$
E^\star,
$$

kita dapat mengukur:

$$
\boxed{
Gap
=
E_Q-E^\star.
}
$$

Untuk minimization:

$$
Gap\ge0.
$$

Relative gap:

$$
\boxed{
Gap_{rel}
=
\frac{E_Q-E^\star}
{|E^\star|}.
}
$$

Ini jauh lebih ilmiah daripada sekadar:

> "QAOA menghasilkan profit lebih tinggi."

---

# Z.31. VQE baseline

VQE:

$$
|\psi(\theta)\rangle
=
U(\theta)|0\rangle^{\otimes N}.
$$

Energy:

$$
\boxed{
E(\theta)
=
\langle\psi(\theta)|
\hat H_t
|\psi(\theta)\rangle.
}
$$

Optimasi:

$$
\theta^\star
=
\arg\min_\theta E(\theta).
$$

---

# Z.32. Ansatz

Untuk baseline:

$$
U(\theta)
=
U_{ent}
U_{rot}.
$$

Misalnya:

$$
R_y(\theta_i)
$$

dan entanglement:

$$
CX_{i,i+1}.
$$

Kita bisa menggunakan EfficientSU2 untuk baseline.

Namun jangan lupa:

> **ansatz bukan bagian dari market model.**

Ia adalah computational mechanism untuk mendekati ground state.

---

# Z.33. QAOA baseline

Untuk QAOA:

$$
|\gamma,\beta\rangle
=
\prod_{p=1}^{P}
e^{-i\beta_pH_M}
e^{-i\gamma_pH_C}
|+\rangle^{\otimes N}.
$$

Objective:

$$
E(\gamma,\beta)
=
\langle
H_C
\rangle.
$$

---

# Z.34. Classical benchmark

Minimal kita punya:

$$
\boxed{
Exact
}
$$

$$
\boxed{
SLSQP / continuous relaxation
}
$$

$$
\boxed{
MILP / classical QUBO solver
}
$$

$$
\boxed{
VQE
}
$$

$$
\boxed{
QAOA
}
$$

Tidak semua harus digunakan pada versi pertama, tetapi exact solver **harus** ada.

---

# Z.35. Dari binary selection ke actual portfolio

Ini juga penting.

Misalkan QUBO menghasilkan:

$$
x^\star=
[1,0,1,0,1].
$$

Itu **belum** berarti:

$$
w=
[0.33,0,0.33,0,0.33].
$$

Kita perlu allocation layer.

Untuk selected assets:

$$
\mathcal S
=
\{i:x_i^\star=1\}.
$$

Kemudian solve:

$$
\boxed{
w^\star
=
\arg\max_{w}
\left[
w^\top\mu
-
\lambda w^\top\Sigma w
\right]
}
$$

subject to:

$$
w_i=0
\quad
i\notin\mathcal S.
$$

---

# Z.36. Jadi QUBO bukan necessarily optimizer seluruh weight

QUBO kita dapat digunakan sebagai:

$$
\boxed{
\text{asset selection layer}.
}
$$

Sedangkan continuous optimizer digunakan untuk:

$$
\boxed{
\text{capital allocation layer}.
}
$$

Ini menurut saya desain yang jauh lebih kuat.

---

# Z.37. Dari weight ke risk budget

Setelah:

$$
w^\star
$$

didapat, kita hitung:

$$
Risk_{portfolio}
=
\sqrt{
w^{\star\top}
\Sigma
w^\star
}.
$$

Kemudian scaling:

$$
\boxed{
w^{scaled}
=
w^\star
\frac{R_{target}}
{Risk_{portfolio}}.
}
$$

Dengan batas:

$$
\|w^{scaled}\|_1
\le
L_{max}.
$$

---

# Z.38. Dari portfolio weight ke quantity

Jika capital:

$$
C_t,
$$

maka dollar allocation:

$$
A_i
=
C_tw_i.
$$

Quantity:

$$
\boxed{
q_i=
\frac{A_i}{P_i}.
}
$$

Kemudian risk constraint:

$$
q_i|P_i-SL_i|
\le R_i.
$$

Sehingga:

$$
\boxed{
q_i
=
\min
\left[
\frac{C_tw_i}{P_i},
\frac{R_i}{|P_i-SL_i|}
\right].
}
$$

Ini adalah quantity final.

---

# Z.39. Stop-loss engine

Untuk versi awal:

$$
SL_i=
P_i
-
k_\sigma\sigma_i
$$

untuk long.

Untuk short:

$$
SL_i=
P_i
+
k_\sigma\sigma_i.
$$

Lebih tepat jika:

$$
\sigma_i
$$

dikonversi menjadi volatility pada horizon trade.

Misalnya:

$$
\sigma_{\Delta t}
=
\sigma_{daily}
\sqrt{
\frac{\Delta t}{1day}
}.
$$

---

# Z.40. TP engine

Gunakan:

$$
TP_i
=
P_i+\rho_i(P_i-SL_i)
$$

untuk long.

$$
TP_i
=
P_i-\rho_i(SL_i-P_i)
$$

untuk short.

Dengan:

$$
\rho_i
=
f(
\hat\mu_i,
\hat\sigma_i,
regime,
liquidity
).
$$

---

# Z.41. Expected trade value

Kita hitung:

$$
EV_i
=
p_i^{win}R_i
-
(1-p_i^{win})L_i
-
Cost_i.
$$

Trade hanya boleh diteruskan jika:

$$
\boxed{
EV_i>0.
}
$$

Ini menjadi **final gate** setelah optimizer.

---

# Z.42. Execution engine

Execution engine menerima:

```text
TradePlan
├── symbol
├── side
├── quantity
├── entry
├── stop_loss
├── take_profit
├── order_type
└── expiry
```

Kemudian menentukan:

$$
Market
$$

atau:

$$
Limit.
$$

---

# Z.43. Limit order model

Kita harus mensimulasikan:

$$
P(Fill).
$$

Jangan menggunakan:

> "kalau candle menyentuh entry maka order filled."

Itu terlalu optimistik.

Minimal kita perlu mempertimbangkan:

$$
distance,
spread,
volume,
queue,
intrabar\ path.
$$

---

# Z.44. Execution cost

Actual return:

$$
R_{actual}
=
R_{gross}
-
Fee
-
Spread
-
Slippage
-
Impact.
$$

Sehingga:

$$
\boxed{
R_{net}
=
R_{gross}
-
C_{execution}.
}
$$

---

# Z.45. Position manager

Setelah filled:

```text
OPEN
  │
  ├── TP hit ──────► CLOSED_PROFIT
  │
  ├── SL hit ──────► CLOSED_LOSS
  │
  ├── TIMEOUT ─────► CLOSED_TIMEOUT
  │
  └── REASSESS ────► MODIFY
```

---

# Z.46. Reassessment

Setiap:

$$
\Delta t_R
$$

kita hitung:

$$
EV_{hold}.
$$

Kemudian:

$$
EV_{hold}
$$

dibandingkan dengan:

$$
EV_{exit}.
$$

Jika:

$$
EV_{hold}>EV_{exit},
$$

hold.

Jika:

$$
EV_{exit}>EV_{hold},
$$

exit.

---

# Z.47. Break-even rule

Jika:

$$
PnL_t
>
\theta_{BE}R_i,
$$

maka:

$$
SL_t
\rightarrow
Entry.
$$

Namun kita dapat menggunakan:

$$
SL_t
=
Entry+\epsilon
$$

untuk long.

---

# Z.48. Trailing stop

Jika momentum tetap kuat:

$$
SL_t
=
\max
\left(
SL_{t-1},
P_t-k\sigma_t
\right).
$$

Ini memastikan:

$$
SL_t
$$

hanya bergerak ke arah yang mengurangi downside.

---

# Z.49. Dynamic TP

Misalkan:

$$
S_t
=
\frac{\hat\mu_t}{\hat\sigma_t}.
$$

Jika:

$$
S_t>S_{high},
$$

kita dapat mempertahankan/menaikkan TP.

Jika:

$$
S_t<S_{low},
$$

kita kurangi target atau exit.

Jadi:

$$
\boxed{
TP_{t+1}
=
f(TP_t,S_t,z_t,PnL_t).
}
$$

---

# Z.50. Full state object

Secara implementasi, saya menyarankan satu objek konseptual:

```text
State
├── timestamp
├── market
│   ├── prices
│   ├── volume
│   └── order_book
│
├── factors
│   ├── BTC
│   ├── ETH
│   ├── DXY
│   ├── Gold
│   ├── SPX
│   └── VIX
│
├── regime
│   ├── state
│   └── probability
│
├── forecast
│   ├── mu
│   └── Sigma
│
├── portfolio
│   ├── weights
│   ├── positions
│   └── cash
│
├── risk
│   ├── budget
│   ├── volatility
│   └── exposure
│
└── execution
    ├── open_orders
    └── fills
```

---

# Z.51. Pipeline data

Secara computational:

$$
\boxed{
Data
\rightarrow
FeatureData
\rightarrow
FactorData
\rightarrow
RegimeData
\rightarrow
ForecastData
\rightarrow
QUBO
\rightarrow
Solution
\rightarrow
TradePlan
\rightarrow
ExecutionLog.
}
$$

Ini akan sangat membantu ketika nanti kita mulai membuat repository.

---

# Z.52. Struktur repository yang saya sarankan

Saya akan mengubah proyek kita menjadi kira-kira:

```text
quant-system/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── features/
│
├── config/
│   ├── assets.yaml
│   ├── factors.yaml
│   └── strategy.yaml
│
├── src/
│   ├── data/
│   │   ├── loader.py
│   │   └── cleaner.py
│   │
│   ├── features/
│   │   └── feature_engine.py
│   │
│   ├── factors/
│   │   └── factor_model.py
│   │
│   ├── regime/
│   │   └── regime_model.py
│   │
│   ├── forecast/
│   │   └── return_model.py
│   │
│   ├── optimization/
│   │   ├── qubo.py
│   │   ├── ising.py
│   │   ├── exact.py
│   │   ├── classical.py
│   │   ├── vqe.py
│   │   └── qaoa.py
│   │
│   ├── risk/
│   │   ├── sizing.py
│   │   ├── stop_loss.py
│   │   └── risk_manager.py
│   │
│   ├── execution/
│   │   ├── order.py
│   │   ├── fill_model.py
│   │   └── slippage.py
│   │
│   ├── portfolio/
│   │   └── allocator.py
│   │
│   ├── backtest/
│   │   └── engine.py
│   │
│   └── evaluation/
│       ├── metrics.py
│       └── attribution.py
│
├── notebooks/
├── experiments/
├── tests/
└── README.md
```

---

# Z.53. Sangat penting: jangan membuat `quantum.py` sebagai pusat sistem

Quantum hanyalah:

$$
\boxed{
Optimization\ Backend.
}
$$

Struktur:

```text
OptimizationProblem
        │
        ├── ExactSolver
        ├── ClassicalSolver
        ├── VQE
        └── QAOA
```

Semua menerima **problem yang sama**.

Ini memungkinkan kita melakukan eksperimen yang benar-benar fair.

---

# Z.54. Interface solver

Secara konseptual:

```text
solve(problem)
        │
        ├── exact
        ├── classical
        ├── vqe
        └── qaoa
```

Output:

```text
Solution
├── bitstring
├── objective_value
├── feasible
├── runtime
└── metadata
```

Dengan begitu:

$$
Solution_{VQE}
$$

dan:

$$
Solution_{QAOA}
$$

memiliki format yang sama.

---

# Z.55. Backtest engine

Backtest harus berjalan secara chronological:

$$
t_0
\rightarrow
t_1
\rightarrow
t_2
\rightarrow
\cdots
\rightarrow
t_T.
$$

Pada setiap $t$:

1. update data,
2. update feature,
3. estimate factor,
4. detect regime,
5. estimate $\mu,\Sigma$,
6. build QUBO,
7. solve,
8. generate order,
9. simulate execution,
10. update position,
11. update equity.

---

# Z.56. Tidak boleh ada future leakage

Pada waktu:

$$
t,
$$

model hanya boleh menggunakan:

$$
D_{\le t}.
$$

Bukan:

$$
D_{>t}.
$$

Dengan kata lain:

$$
\boxed{
\hat\theta_t
=
Fit(D_{\le t}).
}
$$

Bukan:

$$
Fit(D_{0:T}).
$$

Ini harus menjadi **aturan absolut**.

---

# Z.57. Walk-forward training

Saya menyarankan:

```text
TRAIN
│
├──────────────┐
               ▼
            VALIDATE
               │
               ▼
             TEST
```

Kemudian window bergerak:

```text
Train ─── Validation ─ Test
          Train ─── Validation ─ Test
                    Train ─── Validation ─ Test
```

Ini disebut:

$$
\boxed{
Walk\ Forward\ Validation.
}
$$

---

# Z.58. Contoh

Misalnya:

$$
2021-01
\rightarrow
2022-06
$$

training.

$$
2022-07
\rightarrow
2022-09
$$

validation.

$$
2022-10
\rightarrow
2022-12
$$

test.

Kemudian window bergeser.

---

# Z.59. Benchmark yang wajib

Kita jangan hanya membandingkan:

$$
VQE
$$

vs:

$$
QAOA.
$$

Kita harus membandingkan:

$$
\boxed{
Buy\&Hold
}
$$

$$
\boxed{
Equal\ Weight
}
$$

$$
\boxed{
Markowitz
}
$$

$$
\boxed{
Classical\ QUBO
}
$$

$$
\boxed{
VQE
}
$$

$$
\boxed{
QAOA
}
$$

Dengan **identical data dan execution assumptions**.

---

# Z.60. Metrics

Minimal:

### Return

$$
R_{total}.
$$

### Annualized return

$$
R_{ann}.
$$

### Volatility

$$
\sigma_{ann}.
$$

### Sharpe

$$
\boxed{
Sharpe
=
\frac{R_{ann}-R_f}
{\sigma_{ann}}.
}
$$

### Maximum drawdown

$$
\boxed{
MDD
=
\max_t
\frac{Peak_t-Equity_t}
{Peak_t}.
}
$$

### Calmar

$$
Calmar
=
\frac{R_{ann}}{MDD}.
$$

### Sortino

$$
Sortino
=
\frac{R_{ann}-R_f}
{\sigma_{down}}.
$$

---

# Z.61. Tetapi untuk sistem kita ada metrics tambahan

Karena tujuan kita bukan sekadar profit.

Kita harus mengukur:

$$
\boxed{
Quantum\ Optimization\ Quality
}
$$

misalnya:

$$
Gap_{rel}.
$$

Kemudian:

$$
\boxed{
Feasibility\ Rate
}
$$

berapa persen solusi memenuhi seluruh constraint.

Dan:

$$
\boxed{
Execution\ Efficiency.
}
$$

Misalnya:

$$
ImplementationShortfall.
$$

---

# Z.62. Kita bahkan bisa membuat decomposition

Total performance:

$$
P_{total}
$$

dapat diuraikan menjadi:

$$
\boxed{
P_{total}
=
P_{signal}
+
P_{allocation}
+
P_{execution}
+
P_{risk}
-
P_{cost}.
}
$$

Ini sangat berguna untuk penelitian.

Jika hasil buruk:

> Apakah prediction buruk?

atau:

> QUBO buruk?

atau:

> Execution buruk?

atau:

> Risk management buruk?

---

# Z.63. Quantum advantage tidak boleh didefinisikan sebagai "profit lebih tinggi"

Ini salah satu prinsip penelitian terpenting.

Quantum algorithm dapat memberikan:

$$
E_Q\approx E^\star
$$

tetapi belum tentu:

$$
Profit_Q>Profit_{classical}.
$$

Karena market outcome bersifat stochastic.

Maka kita pisahkan:

### Computational performance

$$
Gap,\ Runtime,\ Qubits,\ Depth.
$$

### Financial performance

$$
Return,\ Sharpe,\ MDD,\ Sortino.
$$

Keduanya harus dilaporkan.

---

# Z.64. Experimental matrix

Saya menyarankan eksperimen seperti:

| Model | Optimizer | Data | Regime | Execution |
|---|---|---|---|---|
| Baseline | Equal Weight | OHLCV | No | Ideal |
| Markowitz | Classical | OHLCV | No | Realistic |
| Factor | Classical | OHLCV+Factors | Yes | Realistic |
| QUBO | Exact | Same | Yes | Realistic |
| QUBO | VQE | Same | Yes | Realistic |
| QUBO | QAOA | Same | Yes | Realistic |

Ini jauh lebih kuat daripada sekadar:

> "Saya menjalankan VQE pada crypto."

---

# Z.65. Tahap Z menghasilkan satu master data flow

Pada akhirnya:

$$
\boxed{
\begin{aligned}
D_{0:t}
&\rightarrow X_t\\
&\rightarrow F_t\\
&\rightarrow z_t\\
&\rightarrow \hat\mu_t,\hat\Sigma_t\\
&\rightarrow H_t(x)\\
&\rightarrow x_t^\star\\
&\rightarrow w_t^\star\\
&\rightarrow q_t^\star\\
&\rightarrow TradePlan_t\\
&\rightarrow Execution_t\\
&\rightarrow Position_t\\
&\rightarrow PnL_t\\
&\rightarrow Evaluation_t.
\end{aligned}
}
$$

---

# Z.66. Versi minimum viable system

Saya justru **tidak** ingin kita langsung membangun semua bagian.

Versi pertama seharusnya:

$$
\boxed{
N=8
}
$$

assets.

$$
\boxed{
\Delta t=1h
}
$$

decision.

Factors:

$$
\boxed{
BTC,\ ETH,\ DXY,\ Gold,\ SPX,\ VIX
}
$$

Forecast:

$$
\boxed{
Factor\ Model + Rolling\ Covariance
}
$$

Regime:

$$
\boxed{
3-state\ HMM
}
$$

Optimization:

$$
\boxed{
QUBO
}
$$

Solver:

$$
\boxed{
Exact + VQE + QAOA
}
$$

Risk:

$$
\boxed{
fixed\ fractional\ risk
}
$$

Execution:

$$
\boxed{
limit/market + spread + slippage
}
$$

Backtest:

$$
\boxed{
walk-forward
}
$$

---

# Z.67. Dan versi pertama sebaiknya belum menggunakan live trading

Urutannya:

$$
\boxed{
Backtest
\rightarrow
Paper\ Trading
\rightarrow
Testnet
\rightarrow
Small\ Capital
\rightarrow
Production.
}
$$

Bukan:

$$
Backtest
\rightarrow
Real\ Money.
$$

Karena bahkan jika mathematical model benar, execution layer masih dapat mempunyai bug.

---

# Z.68. Apa yang akan menjadi "core research question"?

Dengan blueprint ini, kita sekarang bisa mengajukan pertanyaan penelitian yang jauh lebih tajam:

> **Apakah quantum approximate optimization dapat menghasilkan solusi asset-selection yang kompetitif terhadap classical optimization pada short-horizon multi-asset trading dengan factor-conditioned risk, transaction cost, dan realistic execution constraints?**

Kemudian subquestion:

### Q1

Apakah QUBO menghasilkan solusi optimal/near-optimal?

$$
Gap_{QUBO}.
$$

### Q2

Apakah VQE/QAOA mendekati solusi exact?

$$
Gap_{quantum}.
$$

### Q3

Apakah solusi tersebut menghasilkan performa finansial yang lebih baik?

$$
Sharpe,\ MDD,\ Return.
$$

### Q4

Apakah keuntungan bertahan setelah:

$$
fees+spread+slippage?
$$

### Q5

Apakah model tetap robust ketika:

$$
Regime_{train}
\neq
Regime_{test}?
$$

---

# Z.69. Ini juga membuat proyekmu jauh lebih dekat dengan quantitative research sebenarnya

Karena kita tidak lagi memiliki:

$$
\text{indicator}
\rightarrow
\text{buy/sell}.
$$

Melainkan:

$$
\boxed{
\text{Information}
\rightarrow
\text{Statistical Model}
\rightarrow
\text{Conditional Distribution}
\rightarrow
\text{Optimization Problem}
\rightarrow
\text{Constrained Decision}
\rightarrow
\text{Execution}
\rightarrow
\text{Feedback}.
}
$$

Dan **itu** adalah perbedaan besar antara trading bot sederhana dengan quantitative decision system.

---

# Z.70. Arsitektur final Tahap A–Z

Kalau seluruh perjalanan kita diringkas:

```text
A
│
├── Market / financial foundation
│
B
├── Return / risk / factor mathematics
│
C
├── Cross-asset dependency
│
D
├── Forecasting
│
E
├── Regime
│
F
├── Portfolio mathematics
│
G
├── Risk
│
H
├── Short-term trading
│
I
├── Execution
│
J
├── Position management
│
K
├── Dynamic TP/SL
│
L
├── Combinatorial optimization
│
M
├── QUBO
│
N
├── Ising
│
O
├── VQE
│
P
├── QAOA
│
Q
├── Classical benchmark
│
R
├── Backtesting
│
S
├── Walk-forward
│
T
├── Robustness
│
U
├── Risk/execution integration
│
V
├── Multi-asset generalization
│
W
├── Adaptive optimization
│
X
├── Closed-loop trading
│
Y
├── Unified mathematical formulation
│
Z
└── Concrete implementation blueprint
```

Dan sekarang kita mempunyai satu bentuk yang sangat jelas:

$$
\boxed{
\color{black}{
\mathcal F_t
\overset{\Phi}{\longrightarrow}
(\hat\mu_t,\hat\Sigma_t,z_t)
\overset{\mathcal H}{\longrightarrow}
H_t
\overset{\mathcal Q}{\longrightarrow}
x_t^\star
\overset{\Psi}{\longrightarrow}
(w_t^\star,q_t^\star)
\overset{\Omega}{\longrightarrow}
O_t
\overset{F}{\longrightarrow}
s_{t+1}.
}}
$$

**Inilah mathematical spine dari sistem yang kita bangun.**

---

## Langkah setelah Z

Menurut saya, setelah Z kita **jangan langsung membuat Tahap AA yang semakin abstrak**. Kita sudah cukup lama berada di level desain. Sekarang waktunya mulai mengubah blueprint menjadi **spesifikasi eksperimen yang benar-benar konkret**.

Jadi Tahap berikutnya yang paling masuk akal adalah:

# **AA — Definisi Dataset, Asset Universe, Timeframe, dan Walk-Forward Experiment**

Di sana kita akan menentukan secara eksplisit, misalnya:

$$
\boxed{
\text{Crypto Universe}
=
\{BTC,ETH,SOL,\ldots\}
}
$$

$$
\boxed{
\text{Equity Universe}
=
\{AAPL,MSFT,NVDA,\ldots\}
}
$$

$$
\boxed{
\text{Factors}
=
\{DXY,Gold,SPX,VIX,US10Y,BTC,ETH,\ldots\}
}
$$

lalu menentukan **tepat bagaimana data disinkronkan antara pasar crypto 24/7 dan saham yang hanya buka pada jam tertentu**, bagaimana missing data ditangani, bagaimana factor lag dibuat agar tidak terjadi look-ahead bias, bagaimana rolling window dihitung, serta bagaimana satu baris data pada $t$ berubah menjadi satu QUBO $H_t$.

Dan menurut saya bagian sinkronisasi **crypto ↔ saham ↔ DXY ↔ Gold** ini justru sangat penting, karena di situlah desain kita akan mulai berhadapan dengan masalah nyata quantitative research, bukan sekadar matematika di atas kertas.

