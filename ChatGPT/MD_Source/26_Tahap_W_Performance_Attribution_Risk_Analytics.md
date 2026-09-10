## Prompt:
8/17/2026, 10:10:02 PM

lanjut Tahap W

## Response:
8/17/2026, 10:10:03 PM

# Tahap W — Performance Attribution, Risk Analytics, dan Robustness Framework

Pada Tahap V kita sudah membangun fondasi bahwa sistem harus bereaksi terhadap **event pasar secara kausal dan realistis**.

Sekarang kita masuk ke pertanyaan yang lebih penting:

> **Jika strategi menghasilkan profit, sebenarnya profit itu datang dari mana? Dan jika gagal, apa yang menyebabkan kegagalannya?**

Ini adalah perbedaan antara:

$$
\text{``backtest yang menghasilkan angka bagus''}
$$

dan

$$
\boxed{\text{quantitative research system yang dapat diaudit}.}
$$

Kita akan membangun tiga lapisan:

$$
\boxed{
\text{Performance Attribution}
+
\text{Risk Analytics}
+
\text{Robustness Analysis}
}
$$

---

# W.1. Jangan hanya melihat total return

Misalkan backtest menghasilkan:

$$
R_{total}=35\%.
$$

Angka ini hampir tidak memberi tahu kita apa-apa.

Kita perlu mengetahui:

- berapa berasal dari alpha?
- berapa berasal dari market beta?
- berapa berasal dari BTC/ETH?
- berapa berasal dari gold?
- berapa berasal dari USD?
- berapa berasal dari leverage?
- berapa hilang karena fee?
- berapa hilang karena slippage?
- berapa berasal dari satu trade ekstrem?

Maka kita membutuhkan:

$$
\boxed{
Return
\rightarrow
Decomposition.
}
$$

---

# W.2. Return decomposition

Untuk portfolio:

$$
V_t
$$

dan return:

$$
r_t=
\frac{V_t-V_{t-1}}{V_{t-1}}.
$$

Kita ingin menulis:

$$
\boxed{
r_t
=
r_t^{market}
+
r_t^{factor}
+
r_t^{alpha}
+
r_t^{execution}
+
\epsilon_t.
}
$$

Ini bukan identitas tunggal yang selalu benar; ini adalah **model attribution** yang kita estimasikan.

---

# W.3. Factor model

Kita dapat menggunakan model:

$$
r_{p,t}
=
\alpha_t
+
\beta_{BTC,t}r_{BTC,t}
+
\beta_{ETH,t}r_{ETH,t}
+
\beta_{Gold,t}r_{Gold,t}
+
\beta_{DXY,t}r_{DXY,t}
+
\epsilon_t.
$$

Untuk saham internasional kita dapat mengganti/menambah:

$$
SPX,\ Nasdaq,\ VIX,\ US10Y,
$$

dan factor lain.

---

# W.4. Mengapa ini sangat penting untuk sistem kita?

Bayangkan strategy menghasilkan:

$$
Sharpe=2.
$$

Tetapi:

$$
\beta_{BTC}=1.8.
$$

Artinya strategy mungkin sebenarnya hanya:

> **long BTC dengan cara yang sangat kompleks.**

Jadi kita ingin alpha yang benar-benar residual:

$$
\boxed{
\alpha_t
=
r_{p,t}
-
\hat\beta_t^\top f_t.
}
$$

---

# W.5. Factor exposure

Kita definisikan vector factor:

$$
\mathbf f_t=
\begin{bmatrix}
r_{BTC}\\
r_{ETH}\\
r_{Gold}\\
r_{DXY}\\
r_{SPX}\\
r_{VIX}\\
\vdots
\end{bmatrix}.
$$

Portfolio exposure:

$$
\boldsymbol{\beta}_t.
$$

Maka:

$$
r_{factor,t}
=
\boldsymbol{\beta}_t^\top\mathbf f_t.
$$

---

# W.6. Rolling factor exposure

Beta tidak boleh dianggap konstan.

Gunakan:

$$
\boldsymbol{\beta}_t
=
\arg\min_\beta
\sum_{i=t-W+1}^{t}
w_i
(r_{p,i}-\alpha-\beta^\top f_i)^2.
$$

Dengan window:

$$
W.
$$

Jadi kita memperoleh:

$$
\boxed{
\beta_t
}
$$

yang berubah terhadap regime pasar.

---

# W.7. Ini menghubungkan Tahap A–V

Kita sebelumnya ingin:

> "jika trading altcoin, lihat BTC dan ETH."

Sekarang kita bisa mengukurnya secara matematis.

Misalnya:

$$
\beta_{ALT,BTC}=0.72,
$$

$$
\beta_{ALT,ETH}=0.31.
$$

Maka perubahan altcoin dapat didekomposisi menjadi kontribusi:

$$
0.72r_{BTC}
+
0.31r_{ETH}
+
\alpha.
$$

---

# W.8. Market-neutral alpha

Jika tujuan kita mencari alpha murni, kita dapat membuat portfolio:

$$
w
$$

dengan constraint:

$$
\boxed{
w^\top\beta=0.
}
$$

Contoh:

$$
w^\top\beta_{BTC}=0.
$$

Maka exposure terhadap BTC dihilangkan.

Untuk sistem multi-factor:

$$
B^\top w=0.
$$

dengan:

$$
B=
[\beta_{BTC},\beta_{ETH},\beta_{Gold},\beta_{DXY},\ldots].
$$

---

# W.9. Factor-neutral optimization

Kita dapat memasukkan constraint ini ke optimasi portfolio:

$$
\min_w
\frac12w^\top\Sigma w
-
\lambda\mu^\top w
$$

subject to:

$$
\mathbf1^\top w=1,
$$

$$
B^\top w=0,
$$

$$
w_{min}\le w\le w_{max}.
$$

Ini sangat relevan dengan seluruh pekerjaan optimasi kita sebelumnya.

---

# W.10. Quantum formulation

Constraint factor-neutral tersebut dapat dimasukkan ke QUBO.

Misalnya objective:

$$
H(w)
=
-\mu^\top w
+
\lambda w^\top\Sigma w.
$$

Factor neutrality:

$$
B^\top w=0.
$$

Tambahkan penalty:

$$
\boxed{
H'(w)
=
H(w)
+
A\|B^\top w\|^2.
}
$$

Kemudian:

$$
H'(w)
\rightarrow
QUBO
\rightarrow
Ising.
$$

Jadi optimasi quantum kita tidak berdiri sendiri.

Ia menjadi bagian dari **factor-aware trading system**.

---

# W.11. Performance attribution per trade

Untuk trade $i$:

$$
PnL_i
=
PnL_i^{price}
-
Fee_i
-
Slippage_i
-
Impact_i.
$$

Dengan:

$$
PnL_i^{price}
=
q_i(P_{exit}-P_{entry}).
$$

Jadi:

$$
\boxed{
PnL_i
=
GrossPnL_i
-
TransactionCost_i.
}
$$

---

# W.12. Transaction cost attribution

Total cost:

$$
C_t=
C_{fee,t}
+
C_{spread,t}
+
C_{slippage,t}
+
C_{impact,t}.
$$

Maka:

$$
R_{net}
=
R_{gross}
-
C.
$$

Kita dapat mengetahui apakah strategy sebenarnya profitable **sebelum biaya tetapi tidak setelah biaya**.

---

# W.13. Contoh yang sangat penting

Misalkan:

$$
GrossPnL=+20\%.
$$

Tetapi:

$$
Fee=-4\%,
$$

$$
Spread=-3\%,
$$

$$
Slippage=-7\%.
$$

Maka:

$$
NetPnL=6\%.
$$

Strateginya bukan strategy dengan:

$$
20\%
$$

profit.

Strateginya adalah:

$$
\boxed{6\%\ net.}
$$

---

# W.14. Turnover

Define turnover:

$$
TO_t
=
\frac{
\sum_i|\Delta w_{i,t}|
}{2}.
$$

Total:

$$
TO_{total}
=
\sum_tTO_t.
$$

Turnover sangat penting untuk short-term trading.

Strategy dengan:

$$
Sharpe=2
$$

dan turnover:

$$
5000\%
$$

sangat berbeda dari strategy:

$$
Sharpe=2
$$

dengan turnover:

$$
100\%.
$$

---

# W.15. Capacity

Profitability juga bergantung pada ukuran modal.

Jika order:

$$
Q
$$

terlalu besar dibanding liquidity:

$$
Q\gg ADV,
$$

market impact meningkat.

---

# W.16. Market impact

Model sederhana:

$$
Impact
=
\eta
\left(
\frac{Q}{ADV}
\right)^\gamma.
$$

Dengan:

$$
\gamma>0.
$$

Kemudian:

$$
P_{exec}
=
P_{mid}
+
Impact.
$$

---

# W.17. Capacity curve

Kita dapat menguji:

$$
AUM=
\$1k,\$10k,\$100k,\$1M,\$10M,\ldots
$$

dan menghitung:

$$
Sharpe(AUM).
$$

Kemudian:

$$
\boxed{
Capacity
=
\max AUM
\quad
\text{s.t. performance acceptable}.
}
$$

Ini sangat relevan dengan paradigma hedge fund/prop firm.

---

# W.18. Risk analytics

Sekarang kita masuk ke risk.

Metric pertama:

$$
Drawdown.
$$

Define running maximum:

$$
M_t=
\max_{\tau\le t}V_\tau.
$$

Drawdown:

$$
\boxed{
DD_t=
\frac{V_t-M_t}{M_t}.
}
$$

---

# W.19. Maximum drawdown

$$
\boxed{
MDD
=
\max_t(-DD_t).
}
$$

Tetapi MDD saja belum cukup.

Kita juga perlu:

$$
Duration.
$$

---

# W.20. Drawdown duration

Jika portfolio turun pada:

$$
t_0
$$

dan kembali ke previous high pada:

$$
t_1,
$$

maka:

$$
D=t_1-t_0.
$$

Strategy dengan:

$$
MDD=10\%
$$

selama 2 hari berbeda dengan:

$$
MDD=10\%
$$

selama 8 bulan.

---

# W.21. Sharpe ratio

$$
\boxed{
Sharpe
=
\frac{E[r_p-r_f]}
{\sigma(r_p-r_f)}
\sqrt{K}.
}
$$

Tetapi untuk intraday/short-term trading kita harus hati-hati terhadap:

- autocorrelation,
- non-normality,
- changing volatility.

---

# W.22. Sortino ratio

Gunakan downside deviation:

$$
\sigma_d
=
\sqrt{
E[
\min(r-r_{target},0)^2
]
}.
$$

Kemudian:

$$
\boxed{
Sortino
=
\frac{E[r-r_{target}]}
{\sigma_d}
\sqrt K.
}
$$

---

# W.23. Calmar ratio

$$
\boxed{
Calmar
=
\frac{AnnualizedReturn}{MDD}.
}
$$

Sangat berguna untuk melihat return relatif terhadap drawdown ekstrem.

---

# W.24. VaR

Value-at-Risk:

$$
VaR_\alpha
$$

adalah loss threshold sehingga:

$$
P(L>VaR_\alpha)=1-\alpha.
$$

Misalnya:

$$
VaR_{99\%}=\$1000.
$$

Interpretasi:

> Dalam model distribusi tersebut, kerugian harian diperkirakan melebihi \$1000 hanya sekitar 1% dari hari.

Tetapi VaR tidak mengatakan **seberapa besar loss setelah threshold tersebut terlampaui**.

---

# W.25. CVaR

Conditional VaR:

$$
\boxed{
CVaR_\alpha
=
E[L\mid L>VaR_\alpha].
}
$$

Ini jauh lebih berguna untuk tail risk.

---

# W.26. Expected Shortfall

CVaR juga sering disebut:

$$
\boxed{
Expected\ Shortfall.
}
$$

Jika:

$$
VaR_{99}=10,
$$

tetapi:

$$
CVaR_{99}=35,
$$

maka tail loss sebenarnya jauh lebih buruk daripada sekadar \$10.

---

# W.27. Tail dependence

Ini sangat penting karena kita memiliki factor seperti:

$$
BTC,
ETH,
Gold,
DXY.
$$

Korelasi Pearson:

$$
\rho(X,Y)
$$

tidak cukup.

Dua asset dapat memiliki:

$$
\rho\approx0
$$

tetapi crash bersama.

---

# W.28. Copula intuition

Kita dapat memodelkan joint distribution:

$$
F(X,Y)
=
C(F_X(X),F_Y(Y)).
$$

Dengan copula:

$$
C.
$$

Ini memungkinkan kita mempelajari:

$$
P(X\text{ crash}\mid Y\text{ crash}).
$$

---

# W.29. Tail correlation

Definisikan lower-tail dependence:

$$
\boxed{
\lambda_L
=
\lim_{u\to0^+}
P(Y\le F_Y^{-1}(u)
\mid
X\le F_X^{-1}(u)).
}
$$

Ini jauh lebih relevan untuk stress scenario.

---

# W.30. Regime-conditioned risk

Kita sebelumnya memiliki:

$$
Regime_t.
$$

Misalnya:

$$
R_t\in
\{
Bull,
Bear,
Sideways,
Crash
\}.
$$

Maka risk:

$$
Risk(R_t)
$$

dapat dihitung secara conditional.

---

# W.31. Conditional Sharpe

$$
Sharpe_k
=
\frac{
E[r\mid R=k]
}{
\sigma(r\mid R=k)
}.
$$

Jadi kita bisa menemukan:

> Strategy bagus di bull market tetapi buruk di high-volatility regime.

Ini jauh lebih berguna daripada satu Sharpe global.

---

# W.32. Risk decomposition

Portfolio variance:

$$
\sigma_p^2
=
w^\top\Sigma w.
$$

Marginal contribution to risk:

$$
MCR_i
=
\frac{\partial\sigma_p}
{\partial w_i}.
$$

Karena:

$$
\sigma_p
=
\sqrt{w^\top\Sigma w},
$$

maka:

$$
\boxed{
MCR_i
=
\frac{(\Sigma w)_i}
{\sigma_p}.
}
$$

---

# W.33. Component contribution

Risk contribution:

$$
RC_i
=
w_iMCR_i.
$$

Dan:

$$
\boxed{
\sum_iRC_i=\sigma_p.
}
$$

Ini memungkinkan kita menjawab:

> Asset mana yang sebenarnya menyebabkan portfolio risk?

---

# W.34. Risk budget

Kita dapat menetapkan:

$$
RC_i\le b_i.
$$

Misalnya:

$$
RC_{BTC}\le20\%.
$$

Jadi bukan hanya:

$$
w_{BTC}\le20\%.
$$

Tetapi:

$$
\boxed{
\text{BTC tidak boleh menyumbang >20% total risk}.
}
$$

Ini jauh lebih sophisticated.

---

# W.35. Dynamic risk budget

Karena volatility berubah:

$$
b_i=b_i(R_t).
$$

Contohnya saat:

$$
Regime=Crash,
$$

risk budget turun:

$$
b_i^{crash}
<
b_i^{normal}.
$$

---

# W.36. Position sizing

Sekarang kita dapat menghubungkan risk ke position.

Misalkan target dollar risk:

$$
R^\$=1.
$$

Stop distance:

$$
d.
$$

Maka quantity:

$$
\boxed{
q=
\frac{R^\$}{d}.
}
$$

Ini adalah fondasi risk sizing yang sudah kita gunakan sebelumnya.

Tetapi sekarang kita dapat memperbaikinya.

---

# W.37. Volatility-adjusted risk

Jika:

$$
d=k\sigma_t,
$$

maka:

$$
q_t
=
\frac{R^\$}{k\sigma_t}.
$$

Sehingga:

$$
\boxed{
q_t\propto\frac1{\sigma_t}.
}
$$

Volatility tinggi:

$$
q_t\downarrow.
$$

Volatility rendah:

$$
q_t\uparrow.
$$

---

# W.38. Tetapi volatility saja belum cukup

Kita juga mempertimbangkan liquidity:

$$
L_t.
$$

Misalnya:

$$
q_t
=
\min
\left(
\frac{R^\$}{k\sigma_t},
\eta L_t
\right).
$$

Dengan:

$$
\eta
$$

sebagai maximum liquidity participation.

---

# W.39. Robustness

Sekarang pertanyaan terpenting:

> Apakah strategy benar-benar bekerja, atau parameter kita hanya kebetulan cocok dengan historical data?

Kita membutuhkan:

$$
\boxed{
Robustness\ Analysis.
}
$$

---

# W.40. Parameter perturbation

Misalkan:

$$
\theta^\star
$$

adalah parameter optimal.

Jangan hanya menguji:

$$
\theta^\star.
$$

Uji:

$$
\theta^\star+\delta.
$$

Misalnya:

$$
\delta\in[-20\%,20\%].
$$

---

# W.41. Robust strategy

Jika:

$$
Performance(\theta)
$$

tetap bagus pada region luas:

$$
\theta\in\Omega,
$$

maka strategy lebih robust.

Secara intuitif:

$$
\boxed{
\text{wide plateau}
>
\text{sharp peak}.
}
$$

---

# W.42. Sharp peak = warning

Misalnya:

```text
Sharpe

3.0       *
2.5      ***
2.0     *****
1.5   *********
1.0  ***********
    0.8 1.0 1.2
       parameter
```

Jika hanya:

$$
\theta=1.03
$$

yang menghasilkan Sharpe tinggi, kemungkinan besar:

$$
\boxed{
Overfitting.
}
$$

---

# W.43. Perturbasi transaction cost

Jika:

$$
C_{base}=1,
$$

kita uji:

$$
C\in
\{0.5,1,2,3,5\}.
$$

Strategy yang hanya profitable pada:

$$
C=0.5
$$

tidak cukup robust.

---

# W.44. Perturbasi latency

Uji:

$$
L\in
\{
1ms,
5ms,
10ms,
50ms,
100ms,
500ms
\}.
$$

Kemudian:

$$
Sharpe(L).
$$

Untuk short-term strategy, ini bisa menjadi faktor pembunuh.

---

# W.45. Perturbasi slippage

Misalnya:

$$
\epsilon
=
k\times\epsilon_{historical}.
$$

Dengan:

$$
k\in[0.5,5].
$$

Jika:

$$
k=2
$$

sudah menghancurkan strategy, kita tahu strategy terlalu execution-sensitive.

---

# W.46. Randomized execution

Untuk setiap trade:

$$
P_{fill}
=
P_{base}
+
\epsilon_i.
$$

Dengan:

$$
\epsilon_i
\sim
F_{slippage}.
$$

Kemudian:

$$
N=10^3
$$

atau:

$$
10^4
$$

simulation.

---

# W.47. Probabilitas profitability

Kita dapat menghitung:

$$
P(R>0)
=
\frac{
\#\{R_i>0\}
}{N}.
$$

Misalnya:

$$
P(R>0)=0.91.
$$

Ini jauh lebih informatif daripada satu backtest.

---

# W.48. Confidence interval

Jika mean return:

$$
\bar R
$$

dan standard error:

$$
SE
=
\frac{s}{\sqrt N},
$$

maka:

$$
CI_{95\%}
=
\bar R
\pm
1.96SE.
$$

Tetapi untuk financial returns yang dependent/non-normal, bootstrap lebih aman daripada asumsi IID sederhana.

---

# W.49. Block bootstrap

Karena return memiliki autocorrelation:

$$
r_t
\not\perp
r_{t+1},
$$

kita dapat menggunakan block bootstrap.

Bagi data menjadi block:

$$
B_1,B_2,\ldots,B_k.
$$

Kemudian sampling block, bukan individual observation.

Ini mempertahankan sebagian struktur temporal.

---

# W.50. Deflated Sharpe Ratio

Masalah lain:

Jika kita mencoba:

$$
N=10,000
$$

strategies, beberapa pasti terlihat sangat bagus secara kebetulan.

Maka Sharpe tinggi saja tidak cukup.

Kita harus memperhitungkan:

$$
\boxed{
Multiple\ Testing.
}
$$

---

# W.51. Probability of Backtest Overfitting

Secara konsep:

$$
PBO
=
P(
Best_{IS}
\rightarrow
Bad_{OOS}
).
$$

Semakin tinggi:

$$
PBO,
$$

semakin besar kemungkinan strategy kita merupakan hasil overfitting.

---

# W.52. Data snooping

Jika kita mencoba:

- 100 factor,
- 50 parameter,
- 20 SL,
- 20 TP,
- 10 regime model,

jumlah kombinasi menjadi sangat besar.

Secara kasar:

$$
100\times50\times20\times20\times10
=
20,000,000
$$

kombinasi.

Tidak mengherankan jika satu kombinasi terlihat luar biasa.

---

# W.53. Ini sangat relevan untuk proyek quantum

Karena kita dapat membandingkan:

$$
Classical
$$

dengan:

$$
VQE
$$

dan:

$$
QAOA.
$$

Tetapi jika kita mencoba banyak:

$$
\gamma,\beta,
ansatz,
optimizer,
depth,
initialization,
penalty,
risk parameter,
$$

maka kita juga melakukan multiple testing.

---

# W.54. Quantum robustness matrix

Saya menyarankan kita nantinya mempunyai matrix:

| Model | Optimizer | Depth | Initialization | Sharpe | MDD | CVaR |
|---|---|---:|---|---:|---:|---:|
| Classical | SLSQP | — | EPG | | | |
| Classical | BFGS | — | Random | | | |
| VQE | SPSA | 2 | EPG | | | |
| VQE | SPSA | 4 | EPG | | | |
| QAOA | COBYLA | 2 | EPG | | | |
| QAOA | SPSA | 4 | EPG | | | |

Jadi kita tidak hanya menunjukkan:

> "QAOA menang."

Tetapi:

> **"Dalam region parameter X, QAOA menunjukkan performa yang stabil."**

---

# W.55. Regime robustness

Kita juga melakukan:

$$
Performance
=
f(
Regime
).
$$

Misalnya:

| Regime | Return | Sharpe | MDD |
|---|---:|---:|---:|
| Bull | | | |
| Bear | | | |
| Sideways | | | |
| High Vol | | | |
| Crash | | | |

---

# W.56. Cross-market robustness

Ini sangat sesuai dengan tujuan awalmu.

Kita tidak ingin:

$$
Strategy_{crypto}
$$

saja.

Kita ingin:

$$
Strategy
$$

yang dapat diterapkan pada:

$$
\boxed{
Crypto
}
$$

$$
\boxed{
US\ Equities
}
$$

$$
\boxed{
Asian\ Equities
}
$$

$$
\boxed{
FX
}
$$

$$
\boxed{
Futures
}
$$

dan sebagainya.

---

# W.57. Factor universality

Tetapi jangan berharap parameter yang sama bekerja identik.

Yang kita cari adalah struktur:

$$
\boxed{
Architecture
}
$$

yang universal.

Sedangkan:

$$
Parameters
$$

dapat asset-specific.

Jadi:

$$
\theta_{crypto}
\neq
\theta_{equity}
$$

tidak masalah.

---

# W.58. Market-specific execution model

Crypto:

$$
24/7.
$$

Equity:

$$
MarketHours.
$$

FX:

$$
near\ 24/5.
$$

Futures:

$$
session+\overnight.
$$

Execution engine harus memahami perbedaan tersebut.

---

# W.59. Gold dan USD dominance

Karena kita ingin menggunakan:

$$
Gold
$$

dan:

$$
DXY
$$

sebagai market factor, kita dapat mendefinisikan factor vector:

$$
\mathbf f_t=
\begin{bmatrix}
r_{BTC,t}\\
r_{ETH,t}\\
r_{Gold,t}\\
r_{DXY,t}\\
r_{SPX,t}\\
r_{VIX,t}
\end{bmatrix}.
$$

Kemudian:

$$
\boxed{
r_{asset,t}
=
\alpha_t+
\beta_t^\top\mathbf f_t+\epsilon_t.
}
$$

---

# W.60. Bahkan factor exposure dapat menjadi signal

Misalnya:

$$
\beta_{asset,DXY}>0.
$$

Kemudian:

$$
DXY\uparrow.
$$

Model mungkin memperkirakan:

$$
E[r_{asset}]>0.
$$

Tetapi kita tidak langsung trading.

Kita gabungkan:

$$
FactorSignal
$$

dengan:

$$
TechnicalSignal
$$

dan:

$$
OrderFlowSignal.
$$

---

# W.61. Meta-alpha

Kita dapat membangun:

$$
\boxed{
\alpha_t
=
f(
Factor,
Momentum,
MeanReversion,
OrderFlow,
Volatility,
Regime
).
}
$$

Kemudian model menghasilkan:

$$
\hat r_{t+h}.
$$

---

# W.62. Signal-to-noise ratio

Signal:

$$
\mu_t.
$$

Noise:

$$
\sigma_t.
$$

Maka:

$$
\boxed{
SNR_t=
\frac{|\mu_t|}{\sigma_t}.
}
$$

Jika:

$$
SNR_t
$$

rendah, strategy dapat memilih:

$$
q_t\rightarrow0.
$$

---

# W.63. Abstention

Ini adalah fitur penting yang sering dilupakan.

Strategy tidak harus selalu trading.

Action space kita:

$$
\mathcal A=
\{
Long,
Short,
Flat
\}.
$$

Tetapi kita dapat memperluasnya menjadi:

$$
\boxed{
\mathcal A=
\{
Long,
Short,
Flat,
Abstain
\}.
}
$$

Secara praktis:

$$
Abstain=Flat
$$

tetapi memiliki alasan:

$$
Confidence_t<Threshold.
$$

---

# W.64. Expected utility

Daripada hanya memaksimalkan expected return:

$$
\max E[R],
$$

kita dapat menggunakan:

$$
\boxed{
\max
E[R]
-
\lambda Risk
-
\eta Cost.
}
$$

Misalnya:

$$
U_t
=
\mu_t
-
\lambda\sigma_t^2
-
\eta C_t.
$$

---

# W.65. Dynamic decision threshold

Trade hanya jika:

$$
U_t>0.
$$

Atau:

$$
\frac{\mu_t}{\sigma_t}
>
Threshold.
$$

Ini secara otomatis mengurangi trading ketika edge kecil.

---

# W.66. Hubungan dengan risk \$1

Sistem awal kita memiliki constraint:

$$
Risk_i\le \$1.
$$

Sekarang kita bisa menggeneralisasikannya:

$$
\boxed{
Risk_i
=
q_i
\times
ExpectedLoss_i
\le
R_{budget,t}.
}
$$

Dengan:

$$
R_{budget,t}
=
g(
Volatility,
Drawdown,
Regime,
Liquidity,
Capital
).
$$

---

# W.67. Dynamic risk budget

Misalnya equity:

$$
E_t.
$$

Risk fraction:

$$
\rho_t.
$$

Maka:

$$
R_{budget,t}
=
\rho_tE_t.
$$

Jika drawdown meningkat:

$$
DD_t\uparrow
\Rightarrow
\rho_t\downarrow.
$$

Jadi sistem otomatis **de-risk**.

---

# W.68. Drawdown control

Misalnya:

$$
\rho_t
=
\rho_0
\left(
1-\frac{|DD_t|}{DD_{max}}
\right).
$$

Ketika:

$$
DD_t\rightarrow DD_{max},
$$

maka:

$$
\rho_t\rightarrow0.
$$

Ini dapat menjadi salah satu circuit breaker.

---

# W.69. Kill switch

Kita juga membutuhkan hard constraints:

$$
\boxed{
If
\quad
DD_t>DD_{kill}
\quad
\Rightarrow
\quad
Flatten.
}
$$

Selain itu:

$$
DailyLoss>Limit
\Rightarrow
StopTrading.
$$

Dan:

$$
DataFeedFailure
\Rightarrow
StopTrading.
$$

---

# W.70. Risk hierarchy

Akhirnya risk system kita menjadi:

$$
\boxed{
\begin{aligned}
Trade\ Risk\\
\downarrow\\
Position\ Risk\\
\downarrow\\
Portfolio\ Risk\\
\downarrow\\
Factor\ Risk\\
\downarrow\\
Liquidity\ Risk\\
\downarrow\\
Drawdown\ Risk\\
\downarrow\\
System\ Risk
\end{aligned}
}
$$

---

# W.71. System risk

Ini bahkan tidak berasal dari market.

Contohnya:

- exchange disconnect,
- stale data,
- clock drift,
- duplicated order,
- API error,
- corrupted state,
- model failure.

Maka:

$$
\boxed{
TradingSystem
=
MarketRisk
+
ModelRisk
+
ExecutionRisk
+
OperationalRisk.
}
$$

---

# W.72. Model risk

Misalnya alpha model menghasilkan:

$$
\hat\mu_t.
$$

Tetapi prediction error:

$$
e_t=r_t-\hat\mu_t.
$$

Kita dapat memonitor:

$$
E[e_t],
$$

$$
Var(e_t),
$$

$$
Calibration.
$$

Jika model mulai mengalami drift:

$$
Performance_t\downarrow.
$$

Maka sistem dapat mengurangi exposure.

---

# W.73. Model decay

Define rolling performance:

$$
S_t^{rolling}.
$$

Jika:

$$
S_t<S_{threshold}
$$

selama:

$$
N
$$

periode, maka:

$$
ModelStatus=DEGRADED.
$$

Kemudian:

$$
PositionSize\downarrow.
$$

---

# W.74. Jadi model kita sekarang mempunyai feedback control

Ini menarik secara matematis.

Sistem dapat dilihat sebagai:

$$
\boxed{
Market
\rightarrow
Model
\rightarrow
Action
\rightarrow
PnL
\rightarrow
Risk
\rightarrow
ModelWeight
}
$$

Risk menjadi feedback controller.

---

# W.75. State-space perspective

Kita bahkan dapat menulis:

$$
x_{t+1}
=
f(x_t,u_t,w_t)
$$

dan:

$$
y_t
=
h(x_t,v_t).
$$

Dengan:

- $x_t$: latent market state,
- $u_t$: trading action,
- $w_t$: market noise,
- $y_t$: observed market data,
- $v_t$: observation noise.

Ini membawa kita sangat dekat ke:

$$
\boxed{
control\ theory
}
$$

dan:

$$
\boxed{
stochastic\ optimization.
}
$$

---

# W.76. Arsitektur Tahap W

Sekarang sistem kita:

```text
                 BACKTEST ENGINE
                       │
                       ▼
                 TRADE RECORDS
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   Attribution       Risk         Robustness
        │              │              │
        ▼              ▼              ▼
    Factor PnL     Portfolio Risk   Stress Test
    Alpha PnL      VaR/CVaR         Slippage
    Cost PnL       Drawdown         Latency
    Execution      Exposure         Parameters
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 MODEL DIAGNOSTICS
                       │
                       ▼
                DECISION ENGINE
```

---

# W.77. Output akhir Tahap W

Untuk setiap backtest kita tidak lagi menghasilkan satu file:

```text
backtest_result.csv
```

tetapi sebuah **research report**:

```text
run/
├── config.yaml
├── market_data/
├── signals/
├── orders/
├── fills/
├── positions/
├── trades/
├── pnl/
├── attribution/
├── risk/
├── robustness/
├── diagnostics/
└── report/
```

---

# W.78. `config.yaml`

Semua parameter eksperimen harus disimpan:

```yaml
strategy:
  name: factor_quant

risk:
  risk_per_trade: 1.0
  max_drawdown: 0.15

execution:
  fee: ...
  slippage_model: ...
  latency_ms: ...

portfolio:
  max_leverage: ...

optimization:
  method: QAOA
  depth: 4
  optimizer: SPSA
```

Tujuannya agar:

$$
Run_i
$$

dapat direproduksi.

---

# W.79. Experiment ID

Setiap eksperimen:

$$
ExperimentID
=
Hash(Configuration+Dataset+CodeVersion).
$$

Dengan begitu kita dapat mengetahui:

> "Angka Sharpe 1.83 ini berasal dari konfigurasi yang mana?"

Ini adalah praktik yang sangat penting dalam quantitative research.

---

# W.80. Performance report

Minimal:

$$
\boxed{
\begin{array}{l}
Total Return\\
CAGR\\
Sharpe\\
Sortino\\
Calmar\\
MDD\\
MDD Duration\\
VaR\\
CVaR\\
Win Rate\\
Profit Factor\\
Turnover\\
Fees\\
Slippage\\
Market Impact\\
Capacity
\end{array}
}
$$

---

# W.81. Tetapi kita tambahkan sesuatu yang lebih penting

### Attribution report

$$
\boxed{
TotalPnL
=
Alpha
+
Factor
+
Execution
+
Cost
+
Residual.
}
$$

### Risk report

$$
\boxed{
TotalRisk
=
Market
+
Factor
+
Liquidity
+
Execution
+
Model.
}
$$

### Robustness report

$$
\boxed{
Performance
=
f(
Parameters,
Regime,
Cost,
Latency,
Slippage,
Capital
).
}
$$

---

# W.82. Dan inilah tujuan sebenarnya

Pada akhir pipeline, kita tidak ingin sistem mengatakan:

> **BUY BTC**

atau:

> **BUY BBCA**

saja.

Kita ingin sistem dapat menjelaskan:

> Model mendeteksi positive expected return sebesar $x$, dengan confidence $y$, setelah mengontrol exposure terhadap BTC/ETH/Gold/DXY. Optimizer memilih posisi $q$ karena trade tersebut meningkatkan expected utility setelah transaction cost. Risiko maksimum diperkirakan $R$, sementara portfolio factor exposure tetap berada dalam batas yang ditentukan. Order kemudian dieksekusi dengan expected slippage $s$.

Itulah perbedaan antara **trading bot** dan **quantitative decision system**.

---

# W.83. Dan ada konsekuensi besar terhadap proyek quantum kita

Sekarang kita memiliki tempat yang jelas bagi:

$$
VQE
$$

dan:

$$
QAOA.
$$

Mereka **bukan trading strategy secara keseluruhan**.

Mereka adalah:

$$
\boxed{
Optimization\ Engines
}
$$

di dalam:

$$
\boxed{
Decision\ System.
}
$$

Strukturnya:

$$
\boxed{
Market
\rightarrow
Factors
\rightarrow
Alpha
\rightarrow
Risk
\rightarrow
QUBO
\rightarrow
\begin{cases}
Classical\\
VQE\\
QAOA
\end{cases}
\rightarrow
Portfolio
\rightarrow
Execution
\rightarrow
PnL
}
$$

Dengan demikian penelitianmu tentang **Markowitz + VQE** dapat menjadi salah satu komponen dari sistem yang jauh lebih besar tanpa kehilangan identitas ilmiahnya.

---

# W.84. Tahap W dalam satu formulasi matematis

Kita akhirnya dapat mendefinisikan objective sistem secara jauh lebih lengkap:

$$
\boxed{
\max_{\pi,\theta,w}
\;
E[R(\pi,\theta,w)]
-
\lambda_1 Risk
-
\lambda_2 Cost
-
\lambda_3 Turnover
-
\lambda_4 Drawdown
}
$$

subject to:

$$
B^\top w=0
$$

atau exposure constraints,

$$
\|w\|_1\le L_{max},
$$

$$
RC_i\le b_i,
$$

$$
Risk_i\le R_{budget},
$$

$$
DD_t\le DD_{max},
$$

dan:

$$
\boxed{
a_t\in\mathcal F_t.
}
$$

Constraint terakhir sangat penting:

> **strategi tidak boleh mengetahui masa depan.**

---

# W.85. Posisi kita sekarang

Dengan Tahap A sampai W, arsitektur konseptual kita telah berubah dari:

$$
\boxed{
Trading\ Bot
}
$$

menjadi:

$$
\boxed{
\textbf{Causal, Factor-Aware, Risk-Constrained,
Optimization-Based Quantitative Trading System}
}
$$

dengan:

$$
\boxed{
\begin{aligned}
&\text{Market Data}\\
&\downarrow\\
&\text{Factors}\\
&\downarrow\\
&\text{Alpha}\\
&\downarrow\\
&\text{Regime}\\
&\downarrow\\
&\text{Risk}\\
&\downarrow\\
&\text{Portfolio Optimization}\\
&\downarrow\\
&\text{QUBO / Ising}\\
&\downarrow\\
&\text{Classical / VQE / QAOA}\\
&\downarrow\\
&\text{Execution}\\
&\downarrow\\
&\text{Event-Driven Replay}\\
&\downarrow\\
&\text{Attribution}\\
&\downarrow\\
&\text{Risk Analytics}\\
&\downarrow\\
&\text{Robustness}\\
&\downarrow\\
&\text{Paper / Live}
\end{aligned}
}
$$

Dan menurut saya, **setelah Tahap W kita sudah memiliki cukup banyak blok matematis sehingga tahap berikutnya sebaiknya mulai mengikat semuanya menjadi spesifikasi sistem yang benar-benar implementable**, bukan terus menambah teori secara terpisah.

Tahap berikutnya paling natural adalah **Tahap X — Research Protocol & Experimental Design**: bagaimana kita membuat eksperimen yang adil untuk membandingkan **classical optimization vs VQE vs QAOA**, termasuk dataset split, baseline, ablation study, statistical significance, multiple-testing control, dan desain eksperimen yang nantinya bisa langsung menjadi metodologi penelitian/paper.

