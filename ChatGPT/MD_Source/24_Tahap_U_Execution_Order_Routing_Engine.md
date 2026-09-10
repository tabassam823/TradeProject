## Prompt:
8/17/2026, 10:07:53 PM

lanjut Tahap U

## Response:
8/17/2026, 10:07:54 PM

> **Remembering**
>
>
> ****
>
> 
>
> **Reviewed prior Tahap structure and preserved mathematical trading conventions**
>
> 
>
> Worked for 7s

# Tahap U - Execution & Order-Routing Engine

Kita sekarang masuk ke lapisan yang membuat sistem kita berpindah dari **quantitative strategy** menjadi sesuatu yang lebih mendekati **trading infrastructure**.

Pada Tahap T kita sudah menentukan:

$$
\text{berapa besar posisi},
\qquad
SL,
\qquad
TP,
\qquad
risk budget,
\qquad
\text{dan kapan posisi harus dipertahankan/diubah/ditutup}.
$$

Tetapi kita masih mempunyai satu masalah:

> **Bagaimana order tersebut benar-benar masuk ke pasar tanpa membuat asumsi backtest yang terlalu ideal?**

Di dunia nyata, ketika model mengatakan:

$$
\boxed{\text{BUY } q \text{ units at } P}
$$

belum tentu kita mendapatkan:

$$
q\text{ units at }P.
$$

Kita bisa mendapatkan:

$$
q_1<q
$$

pada harga berbeda, sebagian order tidak terisi, harga bergerak sebelum order sampai ke exchange, spread berubah, atau order kita terkena adverse selection.

Maka Tahap U akan membangun:

$$
\boxed{
\text{Execution Engine}
}
$$

yang berada di antara:

$$
\boxed{
\text{Decision Engine}
\rightarrow
\text{Execution Engine}
\rightarrow
\text{Market}
}
$$

---

# U.1. Prinsip utama

Kita harus memisahkan dua objective:

### Portfolio/strategy objective

$$
\max E[U]
$$

dengan tujuan mendapatkan alpha.

### Execution objective

$$
\min E[C_{execution}]
$$

dengan tujuan mendapatkan exposure yang diinginkan **semurah dan seaman mungkin**.

Jadi:

$$
\boxed{
\text{Strategy mencari opportunity}
}
$$

sedangkan:

$$
\boxed{
\text{Execution mencari cara terbaik untuk merealisasikan opportunity tersebut}.
}
$$

---

# U.2. Mengapa harga model bukan harga eksekusi?

Misalkan model menghasilkan:

$$
P_t^{model}=100.
$$

Kita ingin:

$$
q=10.
$$

Order book:

$$
\begin{array}{c|c}
Ask & Volume\\
\hline
100.01&2\\
100.02&3\\
100.05&5\\
100.10&10
\end{array}
$$

Jika kita langsung market buy 10 unit, maka kita memperoleh:

$$
2(100.01)
+
3(100.02)
+
5(100.05).
$$

Average execution:

$$
P_{avg}
=
\frac{
2(100.01)+3(100.02)+5(100.05)
}{10}.
$$

Hasilnya:

$$
P_{avg}=100.033.
$$

Jadi:

$$
P_{avg}-P_{model}
=
0.033.
$$

Itulah salah satu bentuk **execution slippage**.

---

# U.3. Decomposition transaction cost

Saya ingin kita mendefinisikan:

$$
\boxed{
C_{execution}
=
C_{spread}
+
C_{fee}
+
C_{slippage}
+
C_{impact}
+
C_{latency}
+
C_{opportunity}
}
$$

Masing-masing mempunyai makna berbeda.

---

# U.4. Spread cost

Mid-price:

$$
M_t=\frac{A_t+B_t}{2}.
$$

Jika kita membeli menggunakan ask:

$$
C_{spread}
=
A_t-M_t
=
\frac{A_t-B_t}{2}.
$$

Jika menjual menggunakan bid:

$$
C_{spread}
=
M_t-B_t.
$$

Jadi secara sederhana:

$$
\boxed{
C_{spread}=\frac{Spread}{2}.
}
$$

Untuk round trip:

$$
\boxed{
C_{spread,RT}\approx Spread.
}
$$

---

# U.5. Fee

Misalkan fee:

$$
f.
$$

Untuk notional:

$$
N=qP,
$$

maka:

$$
C_{fee}=fN.
$$

Untuk round trip:

$$
C_{fee,RT}
=
f_eN_e+f_xN_x.
$$

Kita tidak boleh hanya memasukkan fee entry.

---

# U.6. Slippage

Definisikan implementation shortfall terhadap decision price:

$$
P_0=P_{decision}.
$$

Untuk long:

$$
IS
=
P_{execution}-P_0.
$$

Untuk short:

$$
IS
=
P_0-P_{execution}.
$$

Secara umum:

$$
\boxed{
IS_t
=
s_t(P_{exec}-P_{decision})
}
$$

dengan:

$$
s_t=
\begin{cases}
+1,&long\\
-1,&short.
\end{cases}
$$

---

# U.7. Implementation Shortfall

Untuk seluruh order:

$$
\boxed{
IS
=
\frac{
\sum_i q_iP_i
}{
Q
}
-P_0
}
$$

untuk long.

Namun implementation shortfall yang lebih lengkap adalah:

$$
\boxed{
IS
=
\underbrace{P_{arrival}-P_{decision}}_{\text{delay}}
+
\underbrace{P_{execution}-P_{arrival}}_{\text{execution}}
+
\underbrace{fees}_{\text{cost}}
}
$$

Ini sangat berguna untuk mengevaluasi execution engine kita.

---

# U.8. Arrival price

Kita membutuhkan sebuah referensi:

$$
P_{arrival}.
$$

Biasanya:

$$
P_{arrival}=M_{t_0}.
$$

Kemudian kita bertanya:

> Berapa biaya yang sebenarnya kita keluarkan sejak keputusan dibuat?

Bukan sekadar:

> Apakah order akhirnya profit?

---

# U.9. Latency

Misalkan:

$$
t_d=\text{decision time},
$$

$$
t_s=\text{signal sent},
$$

$$
t_e=\text{exchange received}.
$$

Maka:

$$
\boxed{
L=t_e-t_d.
}
$$

Dalam market yang cepat, selama:

$$
L>0,
$$

harga dapat berubah.

Maka:

$$
P_{market}(t_e)
\neq
P_{market}(t_d).
$$

---

# U.10. Expected latency cost

Misalkan instantaneous price drift:

$$
\mu_t.
$$

Maka approximation:

$$
E[\Delta P|L]
\approx
\mu_tL.
$$

Tetapi untuk short horizon, stochastic component lebih penting:

$$
\Delta P
=
\mu L+\sigma\sqrt{L}\epsilon.
$$

Sehingga:

$$
\boxed{
Var(\Delta P|L)
=
\sigma^2L.
}
$$

Semakin besar latency:

$$
L\uparrow
\Rightarrow
execution uncertainty\uparrow.
$$

---

# U.11. Market impact

Ini bagian yang jauh lebih menarik.

Jika kita membeli:

$$
q
$$

unit, kita menghabiskan liquidity pada ask.

Harga rata-rata dapat dimodelkan:

$$
P_{exec}
=
P_{mid}
+
SpreadCost
+
Impact(q).
$$

Model sederhana:

$$
\boxed{
Impact(q)
=
Y\sigma
\left(
\frac{q}{V}
\right)^\alpha
}
$$

dengan:

- $Y$: impact coefficient,
- $\sigma$: volatility,
- $V$: volume,
- $q$: order size,
- $\alpha$: impact exponent.

---

# U.12. Mengapa volatility masuk?

Karena market yang volatile cenderung mempunyai:

- wider effective spread,
- lower certainty of liquidity,
- larger price response terhadap order.

Maka:

$$
Impact
\propto
\sigma.
$$

Ini berarti sistem kita secara otomatis menganggap execution menjadi lebih mahal ketika market menjadi lebih volatile.

---

# U.13. Liquidity ratio

Kita dapat mendefinisikan:

$$
\boxed{
ParticipationRate
=
\frac{q}{V_{window}}.
}
$$

Misalnya:

$$
q=1000
$$

dan:

$$
V_{window}=1,000,000.
$$

Maka:

$$
ParticipationRate=0.1\%.
$$

Semakin besar participation rate:

$$
Impact\uparrow.
$$

---

# U.14. Order Book Depth

Untuk short-term trading, historical volume saja tidak cukup.

Kita ingin mengetahui:

$$
D^a_k
=
\sum_{i=1}^{k}v_i^a
$$

untuk $k$ level ask.

Begitu pula:

$$
D^b_k
=
\sum_{i=1}^{k}v_i^b.
$$

---

# U.15. Market order simulation

Misalkan:

$$
Q=100.
$$

Order book ask:

$$
\begin{array}{c|c}
Price & Volume\\
\hline
100.01&20\\
100.02&30\\
100.03&50
\end{array}
$$

Maka:

$$
Q_1=20,
$$

$$
Q_2=30,
$$

$$
Q_3=50.
$$

Execution price:

$$
P_{VWAP}
=
\frac{
20(100.01)+
30(100.02)+
50(100.03)
}{100}.
$$

Inilah yang seharusnya dilakukan simulator kita.

Bukan:

$$
P_{execution}=100.01.
$$

---

# U.16. VWAP

Secara umum:

$$
\boxed{
VWAP
=
\frac{
\sum_i q_iP_i
}{
\sum_iq_i
}.
}
$$

Untuk market order:

$$
P_{exec}=VWAP_{consumed\ book}.
$$

---

# U.17. Limit order

Sekarang lebih menarik.

Misalkan:

$$
P_{limit}=99.95.
$$

Order tidak langsung dieksekusi.

Kita memiliki:

$$
P(fill)
$$

sebagai random variable.

Jadi:

$$
F\sim Bernoulli(p_{fill}).
$$

Jika:

$$
F=1,
$$

order filled.

Jika:

$$
F=0,
$$

order tidak mendapat exposure.

---

# U.18. Fill probability

Kita dapat membangun:

$$
\boxed{
p_{fill}
=
f(
d,
Q_{ahead},
I,
\sigma,
V,
T
)
}
$$

dengan:

$$
d=|P_{limit}-P_{mid}|
$$

dan:

$$
Q_{ahead}
=
\text{queue volume di depan order kita}.
$$

---

# U.19. Queue position

Misalkan:

$$
Q_{ahead}=500.
$$

Order kita:

$$
Q_{ours}=100.
$$

Jika volume yang dieksekusi pada harga tersebut baru:

$$
300,
$$

maka kita belum filled.

Jika:

$$
V_{executed}=550,
$$

maka secara ideal:

$$
500
$$

untuk queue di depan dan:

$$
50
$$

untuk order kita.

Sehingga:

$$
Q_{filled}=50.
$$

---

# U.20. Partial fill

Maka:

$$
0\le q_{filled}\le q_{target}.
$$

Kita definisikan:

$$
\boxed{
FillRatio
=
\frac{q_{filled}}{q_{target}}.
}
$$

Misalnya:

$$
FillRatio=0.35.
$$

Artinya hanya 35% posisi yang berhasil diperoleh.

---

# U.21. Partial fill adalah decision problem

Kita kemudian harus memutuskan:

$$
a\in
\{
WAIT,
CANCEL,
REPRICE,
MARKET\_FILL
\}.
$$

Misalnya:

$$
q_{remaining}=650.
$$

Kita harus menghitung expected value dari masing-masing action.

---

# U.22. Optimal cancellation

Misalkan:

$$
EV_{wait}
=
p_{fill}EV_{trade}
-
C_{waiting}.
$$

Sedangkan:

$$
EV_{market}
=
EV_{trade}
-
C_{market}.
$$

Kita memilih:

$$
\boxed{
a^\star
=
\arg\max_a EV(a).
}
$$

Ini berarti cancellation bukan aturan arbitrer seperti:

> "Cancel setelah 5 menit."

Tetapi:

$$
\boxed{
cancel\ ketika\ expected\ value\ waiting\ <\ alternative.
}
$$

---

# U.23. Adverse selection

Ini salah satu konsep paling penting untuk limit order.

Misalkan kita memasang buy limit:

$$
P_{limit}=100.
$$

Order kita filled.

Mengapa?

Bisa jadi karena:

$$
P_{future}<100.
$$

Dengan kata lain:

> Kita mendapatkan fill justru ketika informasi pasar sedang buruk bagi kita.

Jadi:

$$
P(fill)
$$

dan:

$$
R_{future}
$$

tidak independen.

---

# U.24. Conditional fill model

Kita harus memodelkan:

$$
\boxed{
E[R_{future}\mid fill,S_t]
}
$$

bukan:

$$
E[R_{future}|S_t].
$$

Ini perbedaan yang sangat penting.

---

# U.25. Expected value limit order

Maka:

$$
\boxed{
EV_{limit}
=
P(fill)
E[R|fill]
+
P(no\ fill)
E[R|no\ fill]
-
Cost.
}
$$

Jika no-fill berarti kita kehilangan opportunity:

$$
E[R|no\ fill]
$$

juga harus diperhitungkan.

---

# U.26. Market vs limit order

Sekarang kita bisa membuat decision:

$$
\boxed{
EV_{market}
\quad\text{vs}\quad
EV_{limit}.
}
$$

Jika:

$$
EV_{market}>EV_{limit},
$$

gunakan marketable order.

Jika:

$$
EV_{limit}>EV_{market},
$$

gunakan limit.

Ini lebih sophisticated daripada:

> "Selalu gunakan limit order agar fee murah."

---

# U.27. Order type sebagai optimization variable

Kita definisikan:

$$
o_t
\in
\{
MARKET,
LIMIT,
POST\_ONLY,
IOC,
FOK,
TWAP,
VWAP
\}.
$$

Kemudian:

$$
\boxed{
o_t^\star
=
\arg\max_o
EV(o|S_t).
}
$$

---

# U.28. TWAP

Untuk order besar:

$$
Q.
$$

Daripada membeli semuanya:

$$
Q
$$

sekaligus, kita bagi:

$$
Q_1,Q_2,\ldots,Q_N.
$$

dengan:

$$
\sum_iQ_i=Q.
$$

TWAP mengatur execution relatif merata terhadap waktu.

---

# U.29. VWAP execution

Jika expected market volume:

$$
V_1,V_2,\ldots,V_N,
$$

maka:

$$
Q_i
=
Q
\frac{V_i}{\sum_jV_j}.
$$

Sehingga:

$$
\boxed{
\frac{Q_i}{Q}
=
\frac{V_i}{V_{total}}.
}
$$

Kita mengikuti volume market.

---

# U.30. Tetapi kita bisa membuat execution adaptif

Misalkan alpha kita:

$$
\alpha_t.
$$

Jika:

$$
\alpha_t\gg0,
$$

kita ingin memperoleh exposure lebih cepat.

Jika:

$$
\alpha_t\approx0,
$$

kita dapat lebih sabar.

Jadi execution schedule:

$$
Q_t=f(\alpha_t,\sigma_t,L_t,liquidity_t).
$$

---

# U.31. Urgency

Definisikan:

$$
u_t\in[0,1].
$$

Dengan:

$$
u_t=0
$$

berarti:

$$
\text{patient}.
$$

Sedangkan:

$$
u_t=1
$$

berarti:

$$
\text{urgent}.
$$

Kemudian:

$$
\boxed{
u_t
=
f(
alpha,
time\ decay,
volatility,
fill\ probability
).
}
$$

---

# U.32. Time decay alpha

Misalkan expected alpha:

$$
\alpha(\tau)
=
\alpha_0e^{-\kappa\tau}.
$$

Semakin lama kita menunggu:

$$
\tau\uparrow
$$

maka:

$$
\alpha(\tau)\downarrow.
$$

Maka urgency meningkat:

$$
u(\tau)\uparrow.
$$

---

# U.33. Ini menghasilkan execution policy

$$
\boxed{
Q_t^\star
=
\pi_{execution}
(
\alpha_t,
\sigma_t,
liquidity_t,
spread_t,
queue_t,
latency_t,
time_t
).
}
$$

Jadi execution sendiri menjadi sebuah **policy optimization problem**.

---

# U.34. Market impact vs opportunity cost

Ini inti dari optimal execution.

Kalau kita eksekusi terlalu cepat:

$$
Impact\uparrow.
$$

Kalau terlalu lambat:

$$
OpportunityCost\uparrow.
$$

Maka kita mempunyai:

$$
\boxed{
TotalCost
=
ImpactCost
+
OpportunityCost.
}
$$

Dan:

$$
\boxed{
\tau^\star
=
\arg\min_\tau
[
Impact(\tau)
+
OpportunityCost(\tau)
].
}
$$

---

# U.35. Model sederhana

Misalkan:

$$
ImpactCost(\tau)=\frac{a}{\tau^\gamma}
$$

dan:

$$
OpportunityCost(\tau)=b\tau.
$$

Maka:

$$
C(\tau)
=
\frac{a}{\tau^\gamma}+b\tau.
$$

Turunan:

$$
\frac{dC}{d\tau}
=
-a\gamma\tau^{-(\gamma+1)}+b.
$$

Set:

$$
\frac{dC}{d\tau}=0.
$$

Maka:

$$
a\gamma\tau^{-(\gamma+1)}=b.
$$

Sehingga:

$$
\boxed{
\tau^\star
=
\left(
\frac{a\gamma}{b}
\right)^{1/(\gamma+1)}.
}
$$

Ini merupakan contoh sederhana bagaimana **execution horizon dapat ditentukan secara matematis**.

---

# U.36. Hubungan dengan alpha

Jika:

$$
b\propto |\alpha|,
$$

maka:

$$
|\alpha|\uparrow
\Rightarrow
\tau^\star\downarrow.
$$

Artinya:

> Alpha kuat → eksekusi lebih cepat.

Sebaliknya:

$$
|\alpha|\downarrow
\Rightarrow
\tau^\star\uparrow.
$$

Ini sangat masuk akal secara finansial.

---

# U.37. Sekarang kita masukkan risk

Execution tidak boleh meningkatkan risk melebihi budget.

Misalkan target:

$$
R_{target}.
$$

Setiap delay memberikan exposure uncertainty:

$$
Var(R_{delay})
=
\sigma^2\tau.
$$

Maka:

$$
\boxed{
\sigma^2\tau
\le
R_{uncertainty,max}^2.
}
$$

Ini menghasilkan upper bound terhadap execution horizon.

---

# U.38. Execution constraint

Jadi:

$$
\boxed{
\tau
\le
\frac{
R_{uncertainty,max}^2
}{
\sigma^2
}.
}
$$

Market semakin volatile:

$$
\sigma\uparrow
$$

maka:

$$
\tau_{max}\downarrow.
$$

Sekali lagi:

> **Volatility tinggi → kita tidak boleh terlalu santai saat eksekusi.**

---

# U.39. Exchange/venue selection

Untuk sistem multi-market, kita mungkin mempunyai:

$$
V=\{v_1,v_2,\ldots,v_n\}.
$$

Setiap venue memiliki:

$$
C_v=
fee_v+
spread_v+
impact_v+
latency_v+
risk_v.
$$

Kita memilih:

$$
\boxed{
v^\star
=
\arg\min_v
E[C_v].
}
$$

---

# U.40. Tetapi venue juga memiliki liquidity

Maka:

$$
C_v=C_v(q).
$$

Sehingga:

$$
\boxed{
v^\star
=
\arg\min_v
C_v(q).
}
$$

Dan untuk order besar, kita bahkan dapat melakukan split:

$$
q_1+q_2+\cdots+q_n=q.
$$

---

# U.41. Venue allocation sebagai optimization problem

Misalkan:

$$
x_v
$$

adalah fraction order ke venue $v$.

Maka:

$$
\sum_vx_v=1,
$$

$$
x_v\ge0.
$$

Objective:

$$
\boxed{
\min_{\mathbf x}
\sum_v
C_v(x_vq)
}
$$

subject to:

$$
\sum_vx_v=1.
$$

Ini sudah merupakan **capital allocation problem**, hanya saja pada level execution.

---

# U.42. Dan di sinilah QUBO dapat muncul lagi

Jika keputusan venue dibatasi menjadi:

$$
x_v\in\{0,1\},
$$

kita dapat membangun:

$$
\boxed{
QUBO_{venue}.
}
$$

Misalnya:

$$
\min
\sum_vc_vx_v
+
\lambda
\left(
\sum_vx_v-1
\right)^2.
$$

Penalty memastikan hanya satu venue dipilih.

---

# U.43. Jika multi-venue splitting

Kita bisa menggunakan discrete quantity:

$$
x_{v,k}\in\{0,1\}
$$

untuk memilih:

> venue $v$ mendapatkan tranche $k$.

Kemudian objective:

$$
\boxed{
\min
\left[
ExecutionCost
+
Impact
+
LatencyRisk
+
Penalty
\right].
}
$$

Ini menjadi candidate problem untuk QUBO.

---

# U.44. Tetapi kita harus disiplin

Jangan menggunakan QAOA hanya karena kita bisa.

Jika:

$$
QUBO
$$

dapat diselesaikan dengan:

- MILP,
- dynamic programming,
- quadratic programming,
- greedy,
- simulated annealing,

maka semuanya harus menjadi benchmark.

Prinsip proyek kita tetap:

$$
\boxed{
Quantum\ algorithm
\neq
automatic\ advantage.
}
$$

---

# U.45. Event-driven execution simulator

Tahap U harus diwujudkan dalam simulator event-driven.

Event:

$$
E_t\in
\{
MARKET\_UPDATE,
ORDER\_SUBMIT,
ORDER\_ACK,
PARTIAL\_FILL,
FULL\_FILL,
CANCEL,
REJECT,
SL\_TRIGGER,
TP\_TRIGGER,
POSITION\_UPDATE
\}.
$$

---

# U.46. State machine

Order memiliki state:

$$
\boxed{
NEW
\rightarrow
SUBMITTED
\rightarrow
ACKNOWLEDGED
\rightarrow
PARTIALLY\_FILLED
\rightarrow
FILLED
}
$$

atau:

$$
SUBMITTED
\rightarrow
CANCELLED
$$

atau:

$$
SUBMITTED
\rightarrow
REJECTED.
$$

Ini penting agar backtest tidak melakukan:

```text
signal = buy
price = close
filled = true
```

secara instan.

---

# U.47. Latency-aware simulator

Kita harus mempunyai:

$$
t_{decision}
$$

$$
t_{submit}
$$

$$
t_{exchange}
$$

$$
t_{fill}.
$$

Dengan:

$$
t_{decision}
<
t_{submit}
<
t_{exchange}
\le
t_{fill}.
$$

Kemudian harga yang digunakan untuk fill adalah:

$$
P(t_{fill}),
$$

bukan:

$$
P(t_{decision}).
$$

---

# U.48. Ini mencegah look-ahead

Misalnya candle 10:00-10:01.

Jika signal baru diketahui pada:

$$
10:01:00,
$$

maka simulator tidak boleh mengisi order menggunakan:

$$
10:00:30.
$$

Ini merupakan:

$$
\boxed{
point\text{-}in\text{-}time\ execution.
}
$$

---

# U.49. Untuk sistem kita, ini wajib

Karena kita menggunakan:

- crypto,
- saham internasional,
- gold,
- USD/DXY,
- market factors,

timestamp antar instrumen bisa berbeda.

Jadi kita membutuhkan:

$$
\boxed{
Event\ Time
}
$$

bukan sekadar row number.

---

# U.50. Multi-asset synchronization

Misalnya:

$$
BTC_t
$$

tersedia setiap detik.

Tetapi:

$$
DXY_t
$$

hanya tersedia ketika market FX buka.

Dan:

$$
SPX_t
$$

memiliki jam perdagangan tertentu.

Kita tidak boleh mengisi data masa depan secara sembarangan.

Untuk setiap asset $i$:

$$
t_i^{last}
=
\max
\{
\tau\le t:
Data_i(\tau)\ available
\}.
$$

Kemudian:

$$
X_i(t)=Data_i(t_i^{last}).
$$

Tetapi kita harus menyimpan timestamp aslinya:

$$
age_i(t)=t-t_i^{last}.
$$

---

# U.51. Staleness penalty

Jika:

$$
age_i(t)
$$

terlalu besar:

$$
age_i(t)>T_{max},
$$

maka:

$$
\boxed{
Data_i(t)=INVALID.
}
$$

Ini penting untuk factor seperti:

$$
DXY,\ Gold,\ VIX.
$$

---

# U.52. Cross-asset latency

Misalkan:

$$
BTC
$$

bergerak sekarang.

Model menggunakan:

$$
DXY
$$

yang terakhir diperbarui 20 menit lalu.

Kita tidak boleh berpura-pura bahwa DXY merupakan informasi real-time.

Maka state kita harus menyimpan:

$$
\boxed{
(age_{BTC},age_{DXY},age_{Gold},age_{SPX},...)
}
$$

sebagai bagian dari market state.

---

# U.53. Execution state

Saya menyarankan state lengkap menjadi:

$$
\boxed{
S_t=
[
MarketState,
PortfolioState,
OrderState,
ExecutionState
].
}
$$

Dengan:

$$
ExecutionState=
[
spread,
depth,
queue,
latency,
fillRate,
impact,
venue
].
$$

---

# U.54. Execution alpha

Ini konsep yang sangat menarik.

Kita memiliki:

$$
\alpha_{strategy}
$$

dan:

$$
\alpha_{execution}.
$$

Strategy alpha mengatakan:

> "Saya memperkirakan harga naik."

Execution alpha mengatakan:

> "Saya memperkirakan sekarang adalah waktu/venue/order type terbaik untuk mendapatkan exposure tersebut."

Jadi:

$$
\boxed{
TotalValue
=
StrategyAlpha
-
ExecutionCost.
}
$$

---

# U.55. Contoh

Strategy:

$$
E[R]=20bps.
$$

Execution A:

$$
Cost=5bps.
$$

Maka:

$$
Net=15bps.
$$

Execution B:

$$
Cost=18bps.
$$

Maka:

$$
Net=2bps.
$$

Keduanya menggunakan signal yang sama.

Tetapi execution engine menentukan apakah trade tersebut masih layak.

---

# U.56. Trade admission

Maka sebelum order:

$$
\boxed{
E[R_{net}]
=
E[R_{gross}]
-
E[C_{execution}]
}
$$

dan trade hanya diterima jika:

$$
\boxed{
E[R_{net}]
>
H.
}
$$

Dengan $H$ sebagai hurdle rate.

---

# U.57. Ini sangat penting untuk short-term trading

Semakin pendek holding period:

$$
T_{hold}\downarrow,
$$

semakin besar kemungkinan:

$$
C_{execution}
$$

mengonsumsi sebagian besar:

$$
E[R_{gross}].
$$

Maka:

$$
\boxed{
Short\ horizon
\Rightarrow
execution\ becomes\ part\ of\ alpha.
}
$$

---

# U.58. Backtest metric baru

Kita tidak cukup menggunakan:

- Sharpe ratio,
- CAGR,
- max drawdown.

Kita harus mengukur execution:

### Implementation Shortfall

$$
IS.
$$

### Fill Ratio

$$
FR=
\frac{Q_{filled}}{Q_{target}}.
$$

### Slippage

$$
S=
P_{exec}-P_{arrival}.
$$

### Market Impact

$$
MI=P_{exec}-P_{mid}.
$$

### Latency

$$
L=t_{fill}-t_{decision}.
$$

### Cancellation Rate

$$
CR=
\frac{N_{cancel}}{N_{submitted}}.
$$

---

# U.59. Adverse Selection Metric

Untuk limit order:

$$
AS(\Delta)
=
E[
P_{future}-P_{fill}
\mid fill
]
$$

untuk long.

Jika:

$$
AS<0,
$$

maka fill cenderung diikuti harga turun.

Itu berarti:

$$
\boxed{
limit\ order\ strategy
mengalami\ adverse\ selection.
}
$$

---

# U.60. Implementation Shortfall decomposition

Kita dapat memecah:

$$
\boxed{
IS
=
Delay
+
Spread
+
Impact
+
Timing
+
Fees.
}
$$

Dengan ini kita dapat mengetahui **mengapa strategy kehilangan performance**.

Misalnya:

$$
Gross\ Alpha=30bps.
$$

Tetapi:

$$
Delay=2bps
$$

$$
Spread=4bps
$$

$$
Impact=6bps
$$

$$
Fees=3bps.
$$

Maka:

$$
Net=15bps.
$$

---

# U.61. Dan ini membuka optimasi yang sangat menarik

Jika kita melihat:

$$
Impact=6bps,
$$

kita bisa mengoptimalkan:

$$
execution\ schedule.
$$

Jika:

$$
Delay=2bps,
$$

kita optimalkan:

$$
latency.
$$

Jika:

$$
Spread=4bps,
$$

kita optimalkan:

$$
order\ type.
$$

Jadi diagnostic decomposition langsung memberikan roadmap improvement.

---

# U.62. Arsitektur Tahap U

Saya sarankan:

```text
                  ┌──────────────────┐
                  │  Strategy Engine │
                  └────────┬─────────┘
                           │
                     Target Position
                           │
                           ▼
                  ┌──────────────────┐
                  │ Execution Router │
                  └────────┬─────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      Market Order     Limit Order      Algo Order
          │                │                │
          ▼                ▼                ▼
      Slippage          Queue Model     TWAP/VWAP
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                  ┌──────────────────┐
                  │ Fill Simulator   │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Position Engine  │
                  └────────┬─────────┘
                           │
                           ▼
                  Updated Market State
```

---

# U.63. Dan kita sekarang mempunyai dua optimizer

Ini menurut saya salah satu hasil terpenting dari Tahap U.

### Optimizer I - Investment/Trading Optimizer

Menentukan:

$$
\boxed{
\text{What should we trade?}
}
$$

Contoh:

$$
QUBO,\quad
Markowitz,\quad
Ising,\quad
QAOA.
$$

### Optimizer II - Execution Optimizer

Menentukan:

$$
\boxed{
\text{How should we trade it?}
}
$$

Contoh:

$$
\text{market/limit},
\quad
venue,
\quad
timing,
\quad
order splitting,
\quad
TWAP/VWAP.
$$

---

# U.64. Unified objective

Akhirnya kita bisa menuliskan:

$$
\boxed{
\max_{\pi,\epsilon}
E[
U(W_T)
]
}
$$

dengan:

$$
\pi
=
\text{strategy policy}
$$

dan:

$$
\epsilon
=
\text{execution policy}.
$$

Subject to:

$$
\boxed{
\begin{aligned}
Risk&\le R_{max},\\
Leverage&\le L_{max},\\
Liquidity&\ge L_{min},\\
Impact&\le I_{max},\\
Drawdown&\le D_{max},\\
ExecutionCost&\le C_{max}.
\end{aligned}
}
$$

Jadi bukan lagi:

$$
\text{maximize trading signal}.
$$

Tetapi:

$$
\boxed{
\text{maximize realized risk-adjusted utility after execution}.
}
$$

---

# U.65. Hubungan dengan sistem keseluruhan

Sekarang rantai kita menjadi:

$$
\boxed{
\begin{aligned}
Market
&\rightarrow
State\\
&\rightarrow
Factor
&\rightarrow
Alpha\\
&\rightarrow
Regime
&\rightarrow
Risk\\
&\rightarrow
Portfolio\\
&\rightarrow
QUBO/Optimization\\
&\rightarrow
Target Position\\
&\rightarrow
Execution Optimization\\
&\rightarrow
Order\\
&\rightarrow
Fill\\
&\rightarrow
Position\\
&\rightarrow
New State.
\end{aligned}
}
$$

Dan karena:

$$
New\ State
$$

kembali masuk ke model, maka sistem benar-benar menjadi:

$$
\boxed{
\textbf{closed-loop adaptive quantitative trading system}.
}
$$

---

# U.66. Hal yang menurut saya paling penting dari Tahap U

Ada satu perubahan paradigma yang ingin saya tetapkan untuk implementasi kita nanti:

> **Backtest tidak boleh lagi menganggap bahwa "signal menghasilkan trade".**

Yang benar adalah:

$$
\boxed{
Signal
\rightarrow
Target\ Position
\rightarrow
Execution\ Decision
\rightarrow
Order
\rightarrow
Fill
\rightarrow
Actual\ Position.
}
$$

Dengan demikian kita dapat membedakan tiga hal:

$$
\boxed{
\text{Paper Alpha}
}
$$

vs.

$$
\boxed{
\text{Executable Alpha}
}
$$

vs.

$$
\boxed{
\text{Realized Alpha}.
}
$$

Ketiganya bisa berbeda secara signifikan.

---

# U.67. Dan ini menjadi fondasi Tahap V

Setelah Tahap U, kita sudah memiliki hampir semua mekanisme yang dibutuhkan untuk membuat **simulator trading event-driven yang realistis**.

Maka Tahap berikutnya seharusnya bukan sekadar menambahkan indikator atau model ML baru. Yang jauh lebih penting adalah:

$$
\boxed{
\textbf{Tahap V - Event-Driven Backtesting & Market Replay Engine}
}
$$

Di sana kita akan menyatukan:

$$
\boxed{
Historical\ Data
+
Market\ State
+
Alpha
+
Portfolio\ Optimizer
+
Risk\ Engine
+
Execution\ Engine
+
Order\ Book
+
Latency
+
Partial\ Fill
+
Fees
+
Slippage
}
$$

menjadi **satu simulator deterministik** yang dapat menjawab pertanyaan paling penting:

> **"Jika seluruh sistem kita benar-benar dijalankan pada informasi yang tersedia pada waktu $t$, dengan order yang benar-benar harus melewati execution process, berapa performance yang sebenarnya akan diperoleh?"**

Dan itu juga akan menjadi tempat kita memastikan tidak terjadi **look-ahead bias, survivorship bias, data leakage, unrealistic fills, atau hindsight optimization**-sebelum hasil sistem kita mulai dibandingkan dengan benchmark klasik maupun QAOA.

