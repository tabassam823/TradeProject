# Algoritma Trading Multi-strategi

**User:** Anonymous  
**Created:** 8/17/2026 20:00:17  
**Updated:** 8/18/2026 11:50:47  
**Exported:** 8/18/2026 12:02:10  
**Link:** [https://chatgpt.com/c/6a8305e1-25a4-83ec-bfaf-49a4769a569f](https://chatgpt.com/c/6a8305e1-25a4-83ec-bfaf-49a4769a569f)  

## Prompt:
8/17/2026, 8:00:03 PM

https://github.com/tabassam823/TradeProject.git

bisakah kau melihat isi dari repository ini? bisakah kau menjelaskan padaku algoritma utama yang bekerja pada kode yang ada pada repo tersebut?

## Response:
8/17/2026, 8:00:17 PM

> **Searching the web**
>
>
> **Searching github.com**
>
> 
>
> Worked for 10s

Ya. Aku bisa melihat repository tersebut, dan aku sudah menelusuri struktur utama serta kode strategi di dalamnya. Repository ini adalah [`tabassam823/TradeProject`](https://github.com/tabassam823/TradeProject?utm_source=chatgpt.com), dan saat ini branch `main` berisi engine backtesting, paper trading, live trading, tiga strategi, position sizing berbasis volatilitas, serta integrasi Binance dan OpenBB. ([GitHub](https://github.com/tabassam823/TradeProject.git))

Yang menarik: **kode aktualnya tidak persis sama dengan narasi "AI self-improving trading agent" yang ada di `workflow.md`**. Implementasi trading yang benar-benar berjalan saat ini lebih tepat disebut **multi-strategy quantitative trading system dengan volatility-targeted risk management**. ([GitHub](https://github.com/tabassam823/TradeProject/blob/main/workflow.md))

## 1. Gambaran besar algoritmanya

Secara konseptual, alurnya adalah:

```text
                  MARKET DATA
                      │
                      ▼
               Binance OHLCV
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
     Momentum       VWAP        Sentiment
     Strategy     Rejection       Trend
          │           │            │
          └───────────┼────────────┘
                      ▼
                 Signal Score
                      │
                      ▼
            Volatility Calculation
                      │
                      ▼
             Position Sizing
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
       Risk Check            Direction
          │                       │
          └───────────┬───────────┘
                      ▼
                 Order Size
                      │
              ┌───────┴────────┐
              ▼                ▼
          Paper Trade       Live Trade
```

Ada tiga lapisan yang sebaiknya kamu pisahkan secara mental:

1. **Signal generation** → "Apakah saya long/short?"
2. **Risk & position sizing** → "Seberapa besar posisi saya?"
3. **Execution** → "Bagaimana order dikirim ke Binance?"

Ini penting karena **algoritma trading-nya bukan sekadar satu indikator**.

---

# 2. Tiga strategi utama

`strategy_config.json` mengaktifkan tiga strategi:

| Strategi | Ide utama | Signal |
|---|---|---|
| Multi-Horizon Momentum | Trend-following | -4 sampai +4 |
| VWAP Rejection | Mean reversion | -2, 0, +2 |
| Sentiment-Filtered Trend | EMA + news sentiment | -3, 0, +3 |

Konfigurasi saat ini menggunakan horizon momentum `[5,10,21,42]`, VWAP window 24 candle dengan ±2σ, serta EMA 10/30 untuk sentiment trend. ([GitHub](https://github.com/tabassam823/TradeProject/blob/main/strategy_config.json))

---

## 3. Strategi #1 - Multi-Horizon Momentum

Ini menurutku merupakan **strategi paling sederhana sekaligus paling penting** di repository.

Kode:

[`src/strategies/momentum.py`](https://github.com/tabassam823/TradeProject/blob/main/src/strategies/momentum.py?utm_source=chatgpt.com)

Algoritmanya melihat empat horizon:

$$
\tau \in \{5,10,21,42\}
$$

Kemudian untuk masing-masing horizon dihitung:

$$
\Delta P_\tau=P_t-P_{t-\tau}
$$

Lalu:

$$
s_\tau =
\begin{cases}
+1,&P_t>P_{t-\tau}\\
-1,&P_t<P_{t-\tau}\\
0,&P_t=P_{t-\tau}
\end{cases}
$$

Kemudian semua signal dijumlahkan:

$$
S_{\text{momentum}}
=
\sum_{\tau\in\{5,10,21,42\}}s_\tau
$$

Sehingga:

$$
S_{\text{momentum}}\in[-4,+4]
$$

Implementasinya memang persis seperti itu: setiap horizon memberikan `+1`, `-1`, atau `0`, kemudian dijumlahkan. ([GitHub](https://github.com/tabassam823/TradeProject/blob/main/src/strategies/momentum.py))

### Contoh

Misalnya:

```text
5 candle  → harga naik  → +1
10 candle → harga naik  → +1
21 candle → harga turun → -1
42 candle → harga naik  → +1
```

Maka:

$$
S=1+1-1+1=2
$$

Artinya bias sistem adalah **long**.

Jadi ini bukan machine learning.

Ini adalah **multi-time-horizon trend consensus**.

---

# 4. Strategi #2 - VWAP Mean Reversion

Kode:

[`src/strategies/vwap_rejection.py`](https://github.com/tabassam823/TradeProject/blob/main/src/strategies/vwap_rejection.py?utm_source=chatgpt.com)

Ini jauh lebih menarik secara matematis.

Pertama dihitung typical price:

$$
TP_t=\frac{H_t+L_t+C_t}{3}
$$

Kemudian VWAP:

$$
VWAP=
\frac{\sum_t TP_tV_t}
{\sum_tV_t}
$$

Kemudian deviasi standar berbobot volume:

$$
\sigma=
\sqrt{
\frac{
\sum_t (TP_t-VWAP)^2V_t
}{
\sum_tV_t
}
}
$$

Kemudian dibuat dua batas:

$$
U=VWAP+2\sigma
$$

$$
L=VWAP-2\sigma
$$

Karena konfigurasi menggunakan:

```text
vwap_window = 24
num_std = 2
```

maka sistem melihat area ±2σ di sekitar VWAP. ([GitHub](https://github.com/tabassam823/TradeProject/blob/main/strategy_config.json))

### Entry long

Jika:

$$
P_{t-1}\le L
$$

tetapi kemudian:

$$
P_t>L
$$

maka:

$$
S=+2
$$

Interpretasinya:

> harga sebelumnya berada di bawah lower value area, lalu kembali masuk → dianggap rejection → long.

Sebaliknya:

$$
P_{t-1}\ge U
$$

dan:

$$
P_t<U
$$

memberikan:

$$
S=-2
$$

yaitu short.

Jadi secara konsep:

```text
              +2σ
               │
        SHORT ◄┤ rejection
               │
             VWAP
               │
        LONG  ◄┤ rejection
               │
              -2σ
```

Ini **mean-reversion strategy**, bukan trend following.

---

# 5. Strategi #3 - Sentiment-Filtered Trend

Kode:

[`src/strategies/sentiment_trend.py`](https://github.com/tabassam823/TradeProject/blob/main/src/strategies/sentiment_trend.py?utm_source=chatgpt.com)

Di sini digunakan dua EMA:

$$
EMA_{fast}=EMA_{10}
$$

dan

$$
EMA_{slow}=EMA_{30}
$$

Kemudian sistem mengambil sentiment berita melalui OpenBB.

Untuk long:

$$
EMA_{10}>EMA_{30}
$$

dan:

$$
Sentiment\ge -0.2
$$

maka:

$$
S=+3
$$

Untuk short:

$$
EMA_{10}<EMA_{30}
$$

dan:

$$
Sentiment\le +0.2
$$

maka:

$$
S=-3
$$

Jika tidak memenuhi kondisi:

$$
S=0
$$

([GitHub](https://github.com/tabassam823/TradeProject/blob/main/src/strategies/sentiment_trend.py))

Jadi ide dasarnya:

> **Technical trend + fundamental/news confirmation.**

---

# 6. Bagian yang menurutku paling penting: Position Sizing

Justru menurutku **bagian paling "quantitative" dari repository ini bukan signal generation-nya, tetapi risk engine-nya.**

Kode:

[`src/core/position_sizer.py`](https://github.com/tabassam823/TradeProject/blob/main/src/core/position_sizer.py?utm_source=chatgpt.com)

Volatilitas dihitung dari return:

$$
r_t=\frac{P_t-P_{t-1}}{P_{t-1}}
$$

kemudian:

$$
\sigma_t
=
Std(r_{t-20},...,r_t)
$$

dengan lookback 21 candle. ([GitHub](https://github.com/tabassam823/TradeProject/blob/main/src/core/position_sizer.py))

Kemudian volatilitas digunakan untuk menentukan ukuran posisi.

Ini berarti:

> **signal menentukan arah, volatilitas menentukan seberapa agresif posisi.**

---

# 7. Risk budget

Ada mekanisme tiered risk:

Jika modal:

$$
C<100
$$

maka:

$$
R=\$1
$$

Jika:

$$
C\ge100
$$

maka:

$$
R=0.01C
$$

Jadi dengan modal \$10,000:

$$
R=0.01(10000)=\$100
$$

Artinya sistem mencoba membatasi kerugian per trade sekitar \$100. ([GitHub](https://github.com/tabassam823/TradeProject/blob/main/src/core/position_sizer.py))

Ini jauh lebih masuk akal daripada:

> "Saya punya signal kuat → masuk 100% modal."

---

# 8. Stop loss dan take profit juga dihitung matematis

Ini bagian yang sangat menarik.

Repository menggunakan konsep expected value:

$$
E[X]
=
Wp-(1-W)
$$

secara konseptual, dengan payoff ratio minimum:

$$
b_{\min}=\frac{1-W}{W}
$$

Kode kemudian mengambil:

$$
b_{\text{target}}
=
\max
\left(
1.2b_{\min},
1.5
\right)
$$

Kemudian:

$$
SL\%=
\max(1.5\sigma,1\%)
$$

dan:

$$
TP\%=SL\%\times b_{\text{target}}
$$

([GitHub](https://github.com/tabassam823/TradeProject/blob/main/src/core/position_sizer.py))

Jadi sistem tidak sekadar mengatakan:

> "Stop loss = 2%."

Tetapi secara prinsip:

$$
\boxed{\text{Volatility}\rightarrow SL\rightarrow TP}
$$

---

# 9. Position size kemudian diturunkan dari risk

Misalkan:

- harga entry = $P$
- stop loss = $P_{SL}$
- risiko yang diizinkan = $R$

Jarak stop:

$$
D=|P-P_{SL}|
$$

Jumlah unit:

$$
N=\frac{R}{D}
$$

Itulah yang dilakukan kode:

```text
units = risk_dollar / sl_distance
```

([GitHub](https://github.com/tabassam823/TradeProject/blob/main/src/core/position_sizer.py))

Contoh sederhana:

$$
P=100
$$

$$
P_{SL}=98
$$

sehingga:

$$
D=2
$$

Jika risiko:

$$
R=\$100
$$

maka:

$$
N=\frac{100}{2}=50
$$

Jika stop loss tersentuh:

$$
50\times2=\$100
$$

Jadi **position sizing berasal dari risk budget, bukan dari confidence signal semata.**

---

# 10. Backtesting

Backtester utamanya ada di:

[`src/backtester.py`](https://github.com/tabassam823/TradeProject/blob/main/src/backtester.py?utm_source=chatgpt.com)

Ia mengambil historical OHLCV dari Binance, kemudian menjalankan ketiga strategi tersebut. ([GitHub](https://github.com/tabassam823/TradeProject/blob/main/src/backtester.py))

Strukturnya:

```text
Historical Binance Data
          │
          ▼
     ┌────────────┐
     │ Momentum   │
     ├────────────┤
     │ VWAP       │
     ├────────────┤
     │ Sentiment  │
     └─────┬──────┘
           │
           ▼
      Signal Score
           │
           ▼
      Risk Engine
           │
           ▼
      Simulated Trade
           │
           ▼
     Performance
```

Yang perlu diperhatikan:

**backtester mengevaluasi strategi secara terpisah**, bukan sebuah neural network yang belajar dari hasil backtest.

---

# 11. Paper trading

Paper trader menggunakan data Binance secara real-time dan mensimulasikan eksekusi. Kode bahkan menjelaskan bahwa engine ini mengambil ticker real-time setiap jam dan menyimpan virtual ledger ke `logs/paper_ledger.json`. ([GitHub](https://github.com/tabassam823/TradeProject/blob/main/src/paper_trader.py))

Jadi:

$$
\text{Market Data}
\rightarrow
\text{Strategy}
\rightarrow
\text{Risk}
\rightarrow
\text{Virtual Order}
$$

Tidak ada uang sungguhan.

---

# 12. Live trading

Live trader menghubungkan:

```text
Binance API
+
OpenBB
+
Position Sizer
+
Momentum Strategy
```

dan kemudian dapat mengirim order ke Binance. ([GitHub](https://github.com/tabassam823/TradeProject/blob/main/src/live_trader.py))

Menariknya, ada **circuit breaker** berbasis OpenBB sentiment:

```text
Market
  │
  ▼
Signal
  │
  ▼
Sentiment/Circuit Breaker
  │
  ├── BLOCK → jangan trade
  │
  └── PASS
       │
       ▼
 Position Sizing
       │
       ▼
 Binance Order
```

Tetapi ada satu hal yang sangat penting:

### LiveTrader saat ini hanya memilih `MultiHorizonMomentumStrategy`

Di constructor-nya terlihat:

```text
self.strategy = MultiHorizonMomentumStrategy(...)
```

Jadi walaupun konfigurasi memiliki tiga strategi, **live execution tidak menjalankan ketiganya sebagai ensemble**. ([GitHub](https://github.com/tabassam823/TradeProject/blob/main/src/live_trader.py))

Ini perbedaan penting antara:

> "repository memiliki tiga strategi"

dan:

> "live trading menjalankan tiga strategi."

Yang kedua **belum sepenuhnya benar** berdasarkan kode saat ini.

---

# 13. Lalu apakah ini "AI Trading Agent"?

**Menurutku: belum dalam arti machine-learning/AI agent yang kuat.**

Ini lebih tepat disebut:

$$
\boxed{
\text{Quantitative Trading Engine}
}
$$

dengan komponen:

$$
\boxed{
\text{Rule-Based Strategies}
+
\text{Risk Management}
+
\text{Execution}
}
$$

Memang `workflow.md` berbicara tentang:

- self-improving agent
- feedback loop
- autonomous optimization
- perubahan parameter
- scientific method
- Sharpe ratio
- AI agent

([GitHub](https://github.com/tabassam823/TradeProject/blob/main/workflow.md))

Tetapi **kode trading yang sekarang tidak menunjukkan adanya optimizer/ML loop yang benar-benar mengubah parameter strategi berdasarkan hasil trading**.

Dengan kata lain:

```text
DOKUMENTASI

AI Agent
   ↓
Self Improvement
   ↓
Change Parameters
   ↓
Evaluate
   ↓
New Baseline
```

sedangkan implementasi aktual lebih dekat ke:

```text
Fixed Parameters
      ↓
Rule-Based Strategy
      ↓
Signal
      ↓
Risk Management
      ↓
Trade
```

Itu perbedaan yang cukup besar.

---

# 14. Jadi algoritma utamanya sebenarnya apa?

Kalau aku harus merangkum repository ini dalam satu persamaan konseptual:

$$
\boxed{
\text{Trade}
=
f(
\text{Momentum},
\text{VWAP},
\text{Sentiment},
\text{Volatility},
\text{Risk Budget}
)
}
$$

Lebih detail:

$$
\text{Market Data}
\rightarrow
\underbrace{\text{Signal Generation}}_{\text{WHAT}}
\rightarrow
\underbrace{\text{Risk Engine}}_{\text{HOW MUCH}}
\rightarrow
\underbrace{\text{Execution}}_{\text{HOW}}
$$

dengan:

$$
\text{Signal Generation}
=
\begin{cases}
\text{Multi-Horizon Momentum}\\
\text{VWAP Mean Reversion}\\
\text{EMA + Sentiment}
\end{cases}
$$

dan:

$$
\text{Risk Engine}
=
\text{Volatility}
+
\text{Risk Budget}
+
\text{SL/TP}
+
\text{Position Size}
$$

---

## 15. Ada satu hal yang menurutku sangat relevan dengan proyekmu

Kalau tujuanmu adalah **mengembangkan repository ini lebih lanjut**, terutama mengingat kita sebelumnya membahas algoritma trading otomatis dan QAOA/VQE, maka repository ini sebenarnya menyediakan tempat yang sangat jelas untuk memasukkan algoritma optimasi yang lebih canggih.

Saat ini:

$$
\boxed{\text{Strategy} \rightarrow \text{Signal} \rightarrow \text{Position Size}}
$$

Tetapi bisa dikembangkan menjadi:

$$
\boxed{
\text{Strategies}
\rightarrow
\text{Portfolio/Signal Optimization}
\rightarrow
\text{Position Allocation}
\rightarrow
\text{Execution}
}
$$

Misalnya tiga strategi menghasilkan:

$$
S=
\begin{bmatrix}
S_{\text{momentum}}\\
S_{\text{VWAP}}\\
S_{\text{sentiment}}
\end{bmatrix}
$$

Kemudian kita mencari bobot:

$$
w=
\begin{bmatrix}
w_1\\w_2\\w_3
\end{bmatrix}
$$

sehingga:

$$
S_{\text{final}}
=
w_1S_{\text{momentum}}
+w_2S_{\text{VWAP}}
+w_3S_{\text{sentiment}}
$$

Nah, **di sinilah sebenarnya QAOA/VQE atau metode optimasi lainnya bisa masuk secara natural**-bukan menggantikan indikator, tetapi mengoptimalkan **allocation/weighting/portfolio decision** di atas signal yang sudah tersedia.

Dan itu menurutku jauh lebih menarik daripada sekadar mengganti salah satu indikator dengan "AI".

Kalau kamu mau, langkah berikutnya yang paling berguna adalah **aku bedah `backtester.py` baris demi baris dan turunkan seluruh persamaan matematis yang sebenarnya dipakai repository ini**, termasuk bagaimana `signal score → volatility → SL/TP → leverage → position size → PnL` bekerja. Itu akan memberi kita gambaran yang sangat jelas tentang **algoritma trading sebenarnya**, bukan hanya dokumentasinya. ([GitHub](https://github.com/tabassam823/TradeProject/blob/main/src/backtester.py))

---

**Sources:**

- [GitHub - tabassam823/TradeProject · GitHub](https://github.com/tabassam823/TradeProject.git)

## Prompt:
8/17/2026, 8:00:47 PM

aku ingin bertanya lebih lanjut mengenai quantitative trading yang semestinya dilakukan oleh hedge fund dan prop firm tapi denan matematika yang lebih lanjut. maksudku adalah optimasi yang kasusnya TSP, maxcut, portofolio optimization, dst. tapi digunakan untuk trading jangka pendek? mungkin bayanganku seperti ini

1. menggunakan data training harga histori aset yang ingin ditradingkan dan beberapa harga aset yang berhubungan seperti jika ingin membeli altcoin dengan marketcap menengah, maka harus melihat harga btc dan eth (bertujuan untuk menentukan money flow dari aset-aset yang berkaitan)
2. hasil data training digunakan untuk meletakkan order book (tidak langsung eksekusi) berikut TP dan SL sesuai dengan algoritma yang sudah ada agar tetap mengikuti resiko $1
3. setiap jam atau periode tertentu, posisi dievaluasi apakah masih bisa dipertahankan jika order book belum terpanggil? atau jika order book sudah terpanggil, ada 2 kondisi : jika floating loss, biarkan saja tapi jika floating profit, apakah setup nya layak dipertahankan atau harus setting ulang stop loss nya
4. jika stop loss sudah diletakkan di BEP atau titik tertentu sesuai dengan algoritma dan ternyata masih floating profit tinggi, mungkin bisa dipertimbangan TP nya dinaikkan lagi

## Response:
8/17/2026, 8:00:48 PM

> **Personalizing**
>
>
> ****
>
> 
>
> **Personalized quantitative trading plans around Binance automation and risk controls**
>
> 
>
> Worked for 5s

Ya. Dan menurutku bayanganmu **sudah mengarah ke sesuatu yang jauh lebih menarik daripada sekadar "bot trading dengan indikator"**.

Yang kamu gambarkan sebenarnya bisa diformulasikan sebagai **short-horizon quantitative trading system dengan beberapa layer optimasi**:

$$
\boxed{
\text{Market State}
\rightarrow
\text{Forecast}
\rightarrow
\text{Combinatorial Optimization}
\rightarrow
\text{Order Placement}
\rightarrow
\text{Risk Control}
\rightarrow
\text{Dynamic Re-optimization}
}
$$

Namun ada satu koreksi penting: **TSP, MaxCut, dan QUBO tidak harus dipaksakan langsung menjadi "algoritma untuk menentukan buy/sell".** Justru penggunaan yang lebih natural adalah mengubah bagian-bagian tertentu dari masalah trading menjadi masalah optimasi kombinatorial.

Dan menurutku, kalau kita ingin membangun ini di atas `TradeProject`, arsitektur yang bagus adalah seperti berikut.

---

# 1. Gambaran sistem yang kamu bayangkan

Misalnya kita ingin trading:

$$
X=\text{SOL}
$$

tetapi tidak hanya menggunakan data SOL.

Kita masukkan:

$$
\mathbf{x}_t =
[
P_{\mathrm{SOL}},
P_{\mathrm{BTC}},
P_{\mathrm{ETH}},
V_{\mathrm{SOL}},
V_{\mathrm{BTC}},
V_{\mathrm{ETH}},
\mathrm{OB}_{\mathrm{SOL}},
\mathrm{OB}_{\mathrm{BTC}},
\mathrm{OB}_{\mathrm{ETH}},
\ldots
]
$$

Jadi keadaan pasar bukan:

> "SOL naik atau turun?"

melainkan:

> "Bagaimana keadaan SOL relatif terhadap ekosistem aset yang memengaruhinya?"

Kemudian sistem melakukan:

```text
Historical Market Data
        │
        ▼
Feature / State Construction
        │
        ├── SOL
        ├── BTC
        ├── ETH
        ├── volume
        ├── volatility
        ├── order book
        └── correlations
        │
        ▼
Short-Term Forecast
        │
        ▼
Optimization Problem
        │
        ├── Entry price
        ├── Order type
        ├── Position size
        ├── SL
        ├── TP
        └── Exit policy
        │
        ▼
Pending Order
        │
        ▼
Market Monitoring
        │
        ▼
Re-optimization
        │
        ├── Cancel
        ├── Keep
        ├── Move SL
        ├── Move TP
        └── Close
```

**Ini sudah jauh lebih dekat dengan cara berpikir systematic trading daripada sekadar strategi teknikal.**

---

# 2. Bagian pertama yang sangat penting: jangan hanya menggunakan harga aset target

Contohmu tentang altcoin + BTC + ETH itu tepat.

Misalnya kita ingin memprediksi return SOL pada horizon 1 jam:

$$
r_{\mathrm{SOL},t\rightarrow t+1h}
$$

Daripada hanya:

$$
r_{\mathrm{SOL},t}
$$

kita bisa menggunakan:

$$
\mathbf{r}_t=
\begin{bmatrix}
r_{\mathrm{SOL},t}\\
r_{\mathrm{BTC},t}\\
r_{\mathrm{ETH},t}\\
r_{\mathrm{BNB},t}\\
\vdots
\end{bmatrix}
$$

Kemudian kita dapat membangun model:

$$
\hat r_{\mathrm{SOL},t+1}
=
f(\mathbf{x}_t)
$$

Tetapi yang menarik adalah kita tidak harus berhenti pada korelasi Pearson.

Kita dapat membangun **conditional dependence**.

Misalnya:

$$
\operatorname{Corr}
(r_{\mathrm{SOL}},r_{\mathrm{BTC}})
$$

tetapi juga:

$$
\operatorname{Corr}
(r_{\mathrm{SOL}},r_{\mathrm{BTC}}
\mid r_{\mathrm{ETH}})
$$

atau bahkan mutual information:

$$
I(X;Y)
=
\sum_{x,y}
p(x,y)
\log
\frac{p(x,y)}{p(x)p(y)}
$$

Ini mulai masuk ke wilayah **information-theoretic quantitative finance**.

---

# 3. Bahkan "money flow" yang kamu maksud dapat dibuat matematis

Misalnya BTC bergerak:

$$
+2\%
$$

ETH:

$$
+3\%
$$

sementara SOL:

$$
+0.2\%
$$

Sistem dapat melihat:

> BTC dan ETH sudah bergerak, tetapi SOL belum mengikuti.

Namun jangan langsung menganggap:

> "SOL pasti naik."

Lebih tepat:

$$
E[r_{\mathrm{SOL}}\mid
r_{\mathrm{BTC}},r_{\mathrm{ETH}},
V,\sigma,\text{order book}]
$$

Kemudian kita mencari:

$$
\boxed{
\mu_t=E[r_{t+\Delta t}\mid\mathcal F_t]
}
$$

dan:

$$
\boxed{
\sigma_t^2=
\operatorname{Var}(r_{t+\Delta t}\mid\mathcal F_t)
}
$$

Jadi setiap keputusan memiliki dua komponen:

$$
\boxed{\text{Expected Return}+\text{Expected Risk}}
$$

---

# 4. Lalu masuk ke optimasi

Nah, **di sinilah ide TSP/MaxCut/QUBO yang kamu sebut menjadi relevan.**

Misalkan kita memiliki 10 kandidat aset:

$$
A=\{A_1,\ldots,A_{10}\}
$$

dan hanya boleh memilih 3.

Kita dapat mendefinisikan binary variable:

$$
x_i\in\{0,1\}
$$

dengan:

$$
x_i=
\begin{cases}
1 & \text{aset dipilih}\\
0 & \text{tidak}
\end{cases}
$$

Constraint:

$$
\sum_i x_i=3
$$

Kemudian objective:

$$
\max_x
\left[
\sum_i\mu_i x_i
-
\lambda
\sum_{i<j}
\Sigma_{ij}x_ix_j
\right]
$$

Ini sudah menjadi **binary portfolio optimization**.

Dan dapat ditulis sebagai QUBO:

$$
\boxed{
\min_x
x^TQx
}
$$

dengan penalty:

$$
P
\left(
\sum_i x_i-K
\right)^2
$$

untuk memastikan jumlah aset = $K$.

Ini sangat natural untuk:

- QAOA
- simulated annealing
- classical branch-and-bound
- tabu search
- quantum annealing

dan sebagainya.

---

# 5. Tetapi untuk short-term trading, optimasinya bisa lebih menarik

Daripada hanya:

> "aset mana yang dibeli?"

kita bisa membuat decision variable:

$$
x_{i,p,s}
$$

dengan:

- $i$ = aset
- $p$ = price level
- $s$ = side

Contohnya:

$$
x_{\mathrm{SOL},p,\mathrm{long}}
$$

berarti:

> pasang limit buy SOL pada harga $p$.

Kemudian:

$$
x_{\mathrm{SOL},p,\mathrm{short}}
$$

berarti:

> pasang short pada harga $p$.

Sekarang masalahnya berubah menjadi:

> **Di mana saya harus menaruh order?**

Ini jauh lebih dekat dengan yang kamu bayangkan.

---

# 6. Order book sebenarnya dapat dijadikan optimization landscape

Misalnya order book:

```text
ASK
101.0   20 SOL
100.9   15 SOL
100.8   50 SOL
----------------
100.7   ← current
----------------
100.6   10 SOL
100.5   35 SOL
100.4   80 SOL
BID
```

Kita dapat membuat candidate entry:

$$
p\in
\{100.4,100.5,100.6\}
$$

Untuk setiap $p$, hitung:

$$
P(\text{fill}\mid p)
$$

dan:

$$
E[R\mid p]
$$

serta:

$$
P(\text{adverse move}\mid p)
$$

Kemudian:

$$
\boxed{
p^*
=
\arg\max_p
E[\text{utility}\mid p]
}
$$

Ini sudah menjadi **optimal execution / order placement problem**.

Dan menurutku ini jauh lebih cocok untuk matematika lanjutan daripada sekadar membuat RSI yang lebih rumit.

---

# 7. Constraint \$1 yang kamu sebut sangat bagus

Kamu mengatakan:

> tetap mengikuti risiko \$1.

Kita bisa menjadikannya hard constraint.

Misalnya:

$$
R_{\max}=\$1
$$

Jika entry:

$$
P_e
$$

dan stop:

$$
P_{SL}
$$

maka:

$$
N=
\frac{1}
{|P_e-P_{SL}|}
$$

sehingga:

$$
\boxed{
N|P_e-P_{SL}|\le1
}
$$

Ini sangat penting.

Karena sekarang optimizer **tidak boleh mencari solusi yang bagus tetapi mempertaruhkan \$10 atau \$100**.

Risk constraint menjadi bagian dari mathematical optimization problem.

---

# 8. Bahkan TP dan SL dapat menjadi variable optimasi

Ini menurutku salah satu bagian terbaik dari ide kamu.

Jangan menetapkan:

$$
SL=2\%
$$

dan:

$$
TP=3\%
$$

secara statis.

Anggap:

$$
s=\text{stop distance}
$$

$$
t=\text{take-profit distance}
$$

Kita ingin mencari:

$$
(s^*,t^*)
=
\arg\max_{s,t}
E[U(s,t)]
$$

dengan constraint:

$$
\text{Expected Loss}\le\$1
$$

dan mungkin:

$$
P(\text{TP hit})
$$

diperoleh dari historical distribution.

Misalnya:

| SL | TP | P(TP) | P(SL) | Expected PnL |
|---:|---:|---:|---:|---:|
| 0.5% | 0.8% | 0.70 | 0.30 | +... |
| 0.5% | 1.2% | 0.52 | 0.48 | +... |
| 1.0% | 1.5% | 0.48 | 0.52 | +... |
| 1.5% | 3.0% | 0.32 | 0.68 | +... |

Optimizer memilih kombinasi terbaik **berdasarkan kondisi pasar saat itu**.

---

# 9. Kemudian masuk ke ide kamu nomor 3

Ini menurutku sangat bagus.

Misalnya order:

$$
O_0=(P_e,P_{SL},P_{TP},N)
$$

dipasang pada:

$$
t_0
$$

Tetapi pada:

$$
t_1=t_0+1h
$$

order belum filled.

Kita jangan bertanya:

> "Apakah waktunya sudah 1 jam?"

Tetapi:

$$
P(\text{fill}\mid\mathcal F_{t_1})
$$

dan:

$$
E[U(\text{keep})]
$$

dibandingkan dengan:

$$
E[U(\text{cancel and re-optimize})]
$$

Jadi keputusan:

$$
\boxed{
\text{Keep}
\quad\text{vs}\quad
\text{Cancel + Re-optimize}
}
$$

sendiri merupakan optimization problem.

---

# 10. Kalau sudah filled, problem-nya berubah

Ini penting.

Sebelum filled:

$$
\boxed{\text{Optimal Entry Problem}}
$$

Setelah filled:

$$
\boxed{\text{Optimal Position Management Problem}}
$$

Misalnya posisi long.

Kondisi:

$$
P_t<P_e
$$

→ floating loss.

Sedangkan:

$$
P_t>P_e
$$

→ floating profit.

Tetapi **jangan otomatis mengatakan floating loss harus dibiarkan dan floating profit harus dikelola**.

Yang lebih matematis adalah:

$$
E[V_{\text{hold}}\mid\mathcal F_t]
$$

dibandingkan:

$$
V_{\text{close}}
$$

Jadi:

$$
\boxed{
\text{Hold if }
E[V_{\text{future}}\mid\mathcal F_t]
>
V_{\text{close}}
}
$$

---

# 11. Ini sebenarnya merupakan sequential decision problem

Dan ini menurutku adalah bagian paling penting dari seluruh ide kamu.

Trading bukan:

$$
\text{Buy}\rightarrow\text{Wait}\rightarrow\text{Sell}
$$

tetapi:

$$
\boxed{
a_t
\rightarrow
s_{t+1}
\rightarrow
a_{t+1}
\rightarrow
s_{t+2}
\rightarrow
\cdots
}
$$

dengan:

$$
s_t=\text{market state}
$$

dan:

$$
a_t=\text{trading action}
$$

Misalnya:

$$
a_t\in
\{
\text{cancel},
\text{keep},
\text{enter},
\text{move SL},
\text{move TP},
\text{close}
\}
$$

Ini sudah mulai menyerupai:

$$
\boxed{\text{Markov Decision Process}}
$$

atau bahkan:

$$
\boxed{\text{Model Predictive Control (MPC)}}
$$

---

# 12. Dan MPC menurutku sangat cocok dengan ide kamu

Bayangkan setiap jam sistem melakukan:

### State estimation

$$
s_t=
[
P_t,
V_t,
\sigma_t,
r_{\mathrm{BTC}},
r_{\mathrm{ETH}},
OB_t,
\mu_t,
\Sigma_t,
\text{position}
]
$$

Kemudian optimizer menghitung:

$$
a_t^*
=
\arg\max_a
E[
U(s_{t+1})
\mid s_t,a
]
$$

Lalu hanya menjalankan keputusan pertama.

Satu jam kemudian:

$$
s_{t+1}
$$

berubah.

Optimizer dijalankan lagi.

Ini adalah prinsip **receding horizon control**.

```text
              ┌──────────────┐
              │ Market State │
              └──────┬───────┘
                     ↓
              ┌──────────────┐
              │ Optimization │
              └──────┬───────┘
                     ↓
              Optimal Action
                     ↓
              Execute 1 step
                     ↓
                  Market
                     ↓
              New Market State
                     │
                     └───────────────┐
                                     ↓
                              Optimize again
```

Ini sangat dekat dengan apa yang kamu gambarkan sebagai **evaluasi setiap periode**.

---

# 13. Sekarang kasus floating profit yang kamu sebut

Misalnya:

$$
P_e=100
$$

kemudian:

$$
P_t=105
$$

dan SL awal:

$$
SL=98
$$

Kita tidak sekadar berkata:

> "Profit 5%, geser SL ke 100."

Kita dapat menghitung ulang distribusi return:

$$
p(r_{t+\Delta t}\mid\mathcal F_t)
$$

Misalnya ternyata:

$$
E[r_{t+\Delta t}]=+1.8\%
$$

dengan volatilitas:

$$
\sigma=0.7\%
$$

maka probabilitas continuation mungkin masih cukup tinggi.

Tetapi jika:

$$
E[r_{t+\Delta t}]=-0.2\%
$$

maka momentum sudah melemah.

Jadi keputusan trailing stop dapat menjadi:

$$
SL_t^*
=
\arg\max_{SL}
E[U(SL)\mid\mathcal F_t]
$$

---

# 14. Bahkan TP dapat dinaikkan secara optimal

Ini persis ide nomor 4 milikmu.

Misalnya:

$$
P_e=100
$$

$$
TP=105
$$

Harga sekarang:

$$
P_t=104
$$

Kemudian model memperkirakan:

$$
P(P_{t+1}>105)=0.72
$$

dan:

$$
P(P_{t+1}>108)=0.51
$$

Maka kita dapat membandingkan:

$$
TP=105
$$

versus:

$$
TP=108
$$

dan menghitung:

$$
E[U(TP=105)]
$$

versus:

$$
E[U(TP=108)]
$$

Kalau:

$$
E[U(108)]>E[U(105)]
$$

maka TP dinaikkan.

Jadi:

$$
\boxed{
TP_t
\rightarrow
TP_{t+1}
\rightarrow
TP_{t+2}
}
$$

secara dinamis.

---

# 15. Nah, di sinilah TSP/MaxCut/QAOA mulai bisa masuk

Kita sekarang mempunyai banyak kandidat keputusan.

Misalnya:

### Candidate actions

$$
A=
\{
\begin{array}{l}
\text{Keep TP 105}\\
\text{Raise TP 106}\\
\text{Raise TP 108}\\
\text{Move SL to 101}\\
\text{Move SL to 102}\\
\text{Close position}
\end{array}
\}
$$

Kita dapat mendefinisikan binary variables:

$$
x_i\in\{0,1\}
$$

dengan constraint:

$$
\sum_i x_i=1
$$

dan objective:

$$
\max_x
\sum_i U_i x_i
-
\lambda
\sum_{i<j}C_{ij}x_ix_j
$$

Ini menjadi QUBO.

Kemudian:

$$
\boxed{
\text{QUBO}
\rightarrow
\text{QAOA}
}
$$

bisa menjadi salah satu solver.

---

# 16. Tapi jangan gunakan QAOA untuk semuanya

Ini sangat penting kalau kamu ingin membuat proyek yang benar-benar serius.

Misalnya:

> "Saya menggunakan QAOA untuk menentukan apakah BTC akan naik."

Menurutku itu **bukan penggunaan terbaik**.

Lebih masuk akal:

$$
\text{Statistical/ML Model}
\rightarrow
\text{Forecast}
$$

kemudian:

$$
\text{QUBO/QAOA}
\rightarrow
\text{Decision Optimization}
$$

Jadi:

### Classical model

menjawab:

> **Apa yang kemungkinan terjadi?**

Sedangkan:

### Optimization model

menjawab:

> **Dengan kemungkinan tersebut, keputusan terbaik apa yang dapat saya ambil?**

Ini pemisahan yang sangat penting.

---

# 17. Bahkan arsitektur akhirnya bisa seperti ini

Menurutku ini jauh lebih kuat:

```text
                 MARKET DATA
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
         BTC        ETH       Target
          │          │          │
          └──────────┼──────────┘
                     ↓
             Feature Engine
                     │
       ┌─────────────┼──────────────┐
       ↓             ↓              ↓
   Correlation    Volatility    Order Book
       │             │              │
       └─────────────┼──────────────┘
                     ↓
              State Estimator
                     │
                     ↓
            Return Distribution
                     │
              ┌──────┴──────┐
              ↓             ↓
          E[Return]       Risk
              │             │
              └──────┬──────┘
                     ↓
             OPTIMIZATION LAYER
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
       Asset      Entry       Exit
      Selection   Price       Policy
          │          │          │
          └──────────┼──────────┘
                     ↓
                 QUBO / NLP
                     ↓
                Optimal Trade
                     │
                     ↓
               Risk Engine
                     │
              Risk ≤ $1
                     │
                     ↓
               Order Book
                     │
                     ↓
                 POSITION
                     │
                     ↓
              Periodic Review
                     │
                     ↓
             Re-optimization
                     │
                     └──────→ ...
```

---

# 18. Kalau dikaitkan langsung dengan `TradeProject`

Repository yang sekarang sebenarnya sudah memiliki fondasi:

$$
\text{Market Data}
\rightarrow
\text{Strategy}
\rightarrow
\text{Position Sizer}
\rightarrow
\text{Execution}
$$

Yang kita perlukan adalah menambahkan satu layer besar:

$$
\boxed{\text{Optimization Engine}}
$$

sehingga:

```text
TradeProject
│
├── Data
│
├── Forecasting
│
├── Strategies
│
├── Optimization       ← layer baru
│   ├── Portfolio
│   ├── Entry
│   ├── Order placement
│   ├── SL/TP
│   └── Exit
│
├── Risk
│
├── Execution
│
└── Backtesting
```

Dan yang paling penting: **backtester harus bisa mensimulasikan seluruh siklus ini**, bukan hanya menghitung apakah signal menghasilkan profit.

---

# 19. Ada satu masalah besar yang harus kita selesaikan: look-ahead bias

Kalau kita melakukan ini dengan historical data, bahaya terbesar bukan QAOA, bukan VQE, dan bukan optimizer.

Tetapi:

$$
\boxed{\text{look-ahead bias}}
$$

Misalnya pada:

$$
t=10:00
$$

sistem memutuskan order.

Ia hanya boleh mengetahui:

$$
\mathcal F_{10:00}
$$

Tidak boleh mengetahui:

$$
P_{10:30}
$$

walaupun data tersebut tersedia dalam dataset historis.

Jadi simulasi harus benar-benar:

$$
\boxed{
\text{Past}
\rightarrow
\text{Decision}
\rightarrow
\text{Future}
}
$$

bukan:

$$
\text{Past + Future}
\rightarrow
\text{Decision}
$$

---

# 20. Masalah kedua: order book jauh lebih sulit daripada OHLCV

Kalau kita benar-benar ingin melakukan pendekatan yang kamu bayangkan, aku justru menyarankan **jangan langsung mulai dari OHLCV saja**.

Karena untuk short-term trading:

$$
\text{OHLCV}
$$

tidak cukup untuk mengetahui:

- bid/ask imbalance,
- queue position,
- spread,
- depth,
- liquidity,
- slippage,
- fill probability,
- market impact.

Kita perlu mempertimbangkan:

$$
OB_t=
\{
P_i^{bid},Q_i^{bid},
P_i^{ask},Q_i^{ask}
\}
$$

Misalnya order-book imbalance:

$$
I_t=
\frac{
V_{\mathrm{bid}}-V_{\mathrm{ask}}
}{
V_{\mathrm{bid}}+V_{\mathrm{ask}}
}
$$

Kemudian:

$$
I_t>0
$$

memberikan indikasi tekanan beli.

Tetapi lagi-lagi, **indikasi ≠ prediksi pasti**.

---

# 21. Jadi kalau aku harus mendefinisikan proyek ini secara akademis

Aku tidak akan menyebutnya:

> "AI trading bot."

Aku akan mendefinisikannya sebagai:

$$
\boxed{
\textbf{Short-Horizon Systematic Trading via Dynamic Mathematical Optimization}
}
$$

dengan komponen:

### Layer 1 — Market State

$$
\mathcal F_t
$$

### Layer 2 — Statistical Forecasting

$$
p(r_{t+\Delta t}\mid\mathcal F_t)
$$

### Layer 3 — Combinatorial Optimization

$$
x^*=\arg\min_x x^TQx
$$

### Layer 4 — Risk-Constrained Execution

$$
\text{Risk}(x)\le\$1
$$

### Layer 5 — Sequential Re-optimization

$$
x_{t+1}^*
=
\arg\max_x
E[U(x)\mid\mathcal F_{t+1}]
$$

---

## Dan ini menghasilkan sesuatu yang menurutku sangat menarik

Kamu sebenarnya sedang menggabungkan **tiga bidang**:

$$
\boxed{
\text{Quantitative Finance}
+
\text{Operations Research}
+
\text{Quantum Optimization}
}
$$

Bukan:

$$
\text{Quantum Computing}
\rightarrow
\text{prediksi harga}
$$

tetapi:

$$
\boxed{
\text{Market Modeling}
\rightarrow
\text{Optimization}
\rightarrow
\text{Execution}
}
$$

Dan ini juga membuat pengalamanmu dengan **Markowitz → QUBO → Ising → VQE/QAOA** menjadi sangat relevan. Portfolio optimization yang kamu kerjakan untuk skripsi sebenarnya bisa menjadi **versi long-horizon/static** dari problem yang sekarang ingin kamu bawa menjadi **short-horizon/dynamic optimization**.

Perbedaannya kira-kira:

$$
\boxed{
\begin{array}{ccc}
\text{Skripsi} & \longrightarrow & \text{Trading System}\\
\hline
\text{Asset allocation} && \text{Order/action allocation}\\
\text{Expected return} && \text{Short-term forecast}\\
\text{Covariance} && \text{Dynamic risk}\\
\text{QUBO} && \text{Dynamic QUBO}\\
\text{VQE} && \text{QAOA / hybrid solver}\\
\text{One optimization} && \text{Repeated optimization}\\
\end{array}
}
$$

**Menurutku, justru bagian "repeated optimization" inilah yang membuat proyek ini jauh lebih menarik.**

Langkah berikut yang paling masuk akal adalah kita **jangan langsung coding**. Kita desain dulu *mathematical formulation* untuk satu kasus konkret, misalnya **BTC sebagai market factor + ETH sebagai related asset + satu altcoin target**, lalu kita turunkan dari data historis → probabilitas return → optimal limit-entry → SL/TP → \$1 risk constraint → evaluasi 1 jam → re-optimization. Setelah formulasi klasiknya benar, baru kita tentukan **bagian mana yang benar-benar cocok dijadikan QUBO/Ising/QAOA dan bagian mana yang lebih baik diselesaikan secara classical**.

## Prompt:
8/17/2026, 9:03:30 PM

aku suka semua hal yang baru saja kau sampaikan kepadaku. aku ingin semuanya dapat terwujud, terutama karena banyak hal yang sudah aku pelajari sebelumnya. sekarang aku ingin melanjutnya desaim matematisnya. aku tidak ingin berhenti hanya di kripto saja. aku ingin juga model kita dapat bekerja di pasar saham internasional dengan melihat market factor emas dan usd dominance

## Response:
8/17/2026, 9:03:31 PM

> **Remembering**
>
>
> ****
>
> 
>
> **Extended quantitative trading framework across assets, factors, Markowitz, QUBO, gold, and USD dominance**
>
> 
>
> Worked for 5s

Ya. Dan menurutku **kita sebaiknya mengubah desain ini dari "crypto trading model" menjadi sebuah kerangka general untuk systematic trading lintas aset**. Dengan begitu, kripto hanyalah salah satu *market universe*, sementara saham internasional, ETF, komoditas, FX, dan aset lain dapat masuk ke kerangka yang sama.

Ini juga sangat cocok dengan fondasi yang sudah kamu kuasai: **Markowitz → covariance → QUBO/Ising → VQE/QAOA**, tetapi sekarang kita menambahkan **time dependence, market factors, execution, dan dynamic re-optimization**. 

---

# 1. Kita mulai dari prinsip paling dasar

Aku ingin memisahkan tiga hal:

$$
\boxed{
\text{Asset}
\neq
\text{Market Factor}
\neq
\text{Trading Decision}
}
$$

Contohnya:

### Crypto

Target:

$$
A_i=\mathrm{SOL}
$$

Market factors:

$$
F=
\{
\mathrm{BTC},
\mathrm{ETH},
\mathrm{USD}
\}
$$

### Saham AS

Target:

$$
A_i=\mathrm{NVDA}
$$

Market factors:

$$
F=
\{
\mathrm{SPX},
\mathrm{NASDAQ},
\mathrm{GOLD},
\mathrm{USD}
\}
$$

### Saham Jepang

Target:

$$
A_i=\mathrm{Toyota}
$$

Market factors:

$$
F=
\{
\mathrm{Nikkei},
\mathrm{USDJPY},
\mathrm{GOLD},
\mathrm{USD}
\}
$$

### Saham emerging market

Target:

$$
A_i=\mathrm{BBCA}
$$

Market factors:

$$
F=
\{
\mathrm{IHSG},
\mathrm{USDIDR},
\mathrm{GOLD},
\mathrm{USD}
\}
$$

Jadi kita tidak ingin membuat:

> "algoritma crypto"

dan

> "algoritma saham".

Kita ingin membuat:

$$
\boxed{
\textbf{Asset-Agnostic Quantitative Trading Framework}
}
$$

---

# 2. Market factor menjadi variabel fundamental dalam model

Misalkan terdapat $N$ aset.

Return aset $i$:

$$
r_{i,t}
=
\frac{P_{i,t}-P_{i,t-1}}{P_{i,t-1}}
$$

Kita memiliki $K$ market factors:

$$
\mathbf f_t
=
\begin{bmatrix}
f_{1,t}\\
f_{2,t}\\
\vdots\\
f_{K,t}
\end{bmatrix}
$$

Kemudian kita gunakan **factor model**:

$$
\boxed{
r_{i,t}
=
\alpha_i+
\boldsymbol{\beta}_i^T\mathbf f_t+
\epsilon_{i,t}
}
$$

atau:

$$
r_{i,t}
=
\alpha_i+
\sum_{k=1}^{K}\beta_{ik}f_{k,t}
+
\epsilon_{i,t}.
$$

Ini adalah salah satu perubahan paling penting dari desain sebelumnya.

Kita tidak lagi hanya bertanya:

> "Bagaimana harga aset ini bergerak?"

tetapi:

> "Berapa banyak pergerakan aset ini yang dapat dijelaskan oleh market factors?"

---

# 3. Untuk desain awal, kita gunakan tiga kelompok factor

Aku menyarankan kita membedakan:

## A. Equity / Market factor

Misalnya:

$$
F_{\mathrm{equity}}
=
\{\mathrm{SPX},\mathrm{NDX},\mathrm{STOXX},\mathrm{NIKKEI},\mathrm{IHSG},\ldots\}
$$

## B. Macro factor

Misalnya:

$$
F_{\mathrm{macro}}
=
\{\mathrm{Gold},\mathrm{USD},\mathrm{Oil},\ldots\}
$$

## C. Cross-asset factor

Misalnya:

$$
F_{\mathrm{cross}}
=
\{\mathrm{BTC},\mathrm{ETH},\mathrm{VIX},\mathrm{rates},\ldots\}
$$

Sehingga:

$$
\boxed{
\mathbf F_t
=
[
\mathbf F_{\mathrm{equity}},
\mathbf F_{\mathrm{macro}},
\mathbf F_{\mathrm{cross}}
]
}
$$

---

# 4. Gold dan USD bukan sekadar "dua aset tambahan"

Ini penting.

Kalau kita memasukkan emas dan USD ke model, kita tidak sekadar berkata:

$$
r_{\mathrm{Gold}}
$$

dan:

$$
r_{\mathrm{USD}}
$$

melainkan kita ingin menangkap **regime informasi**.

Misalnya secara konseptual:

$$
\Delta Gold_t>0
$$

dan:

$$
\Delta USD_t<0
$$

dapat merepresentasikan kondisi tertentu pada global macro environment.

Sebaliknya:

$$
\Delta Gold_t<0,
\qquad
\Delta USD_t>0
$$

merepresentasikan kondisi yang berbeda.

Jadi kita bisa membuat:

$$
\boxed{
\text{Market Regime}_t
=
g(
r_{\mathrm{Equity}},
r_{\mathrm{Gold}},
r_{\mathrm{USD}},
\sigma,
VIX,\ldots
)
}
$$

Ini jauh lebih powerful daripada sekadar memasukkan harga emas sebagai feature.

---

# 5. Saya ingin kita mendefinisikan "market state"

Pada setiap waktu $t$, sistem memiliki:

$$
\boxed{
s_t
}
$$

yang merupakan seluruh informasi yang tersedia saat itu.

Misalnya:

$$
s_t=
\begin{bmatrix}
\mathbf r_t\\
\mathbf f_t\\
\boldsymbol{\sigma}_t\\
\boldsymbol{\beta}_t\\
\mathbf{OB}_t\\
\mathbf V_t\\
\mathbf C_t\\
\mathbf P_t
\end{bmatrix}
$$

dengan:

- $\mathbf r_t$: return aset,
- $\mathbf f_t$: market factors,
- $\boldsymbol\sigma_t$: volatility,
- $\boldsymbol\beta_t$: factor exposure,
- $\mathbf{OB}_t$: order book,
- $\mathbf V_t$: volume,
- $\mathbf C_t$: correlation/dependence,
- $\mathbf P_t$: current positions.

Jadi:

$$
\boxed{
s_t=\text{state pasar saat ini}
}
$$

---

# 6. Dari state tersebut kita estimasi expected return

Kita ingin:

$$
\boxed{
\boldsymbol{\mu}_{t+\Delta}
=
E[
\mathbf r_{t+\Delta}
\mid
s_t
]
}
$$

Ini adalah salah satu input utama optimizer.

Misalnya:

$$
\boldsymbol{\mu}
=
\begin{bmatrix}
0.002\\
0.001\\
-0.0005\\
0.003
\end{bmatrix}
$$

berarti model memperkirakan return jangka pendek empat aset tersebut.

Tetapi kita **tidak boleh hanya menggunakan $\mu$**.

Kita juga memerlukan:

$$
\boxed{
\Sigma_t
=
\operatorname{Cov}
(
\mathbf r_{t+\Delta}
\mid s_t
)
}
$$

Ini langsung menghubungkan sistem baru dengan Markowitz yang sudah kamu kerjakan.

---

# 7. Tetapi covariance kita harus dynamic

Dalam skripsimu, covariance secara umum adalah:

$$
\Sigma
$$

Sekarang kita naikkan menjadi:

$$
\boxed{
\Sigma_t
}
$$

karena hubungan antar-aset berubah terhadap waktu.

Misalnya:

$$
\operatorname{Corr}
(
r_{\mathrm{NVDA}},
r_{\mathrm{SPX}}
)
$$

tidak harus sama sepanjang waktu.

Begitu juga:

$$
\operatorname{Corr}
(
r_{\mathrm{BTC}},
r_{\mathrm{NASDAQ}}
)
$$

bisa berubah ketika market memasuki regime berbeda.

Jadi model kita harus mengestimasi:

$$
\Sigma_t
$$

secara rolling atau conditional.

---

# 8. Factor model memberikan struktur covariance

Dari:

$$
r_t
=
\alpha+
Bf_t+\epsilon_t
$$

kita memperoleh:

$$
\boxed{
\Sigma_t
=
B_t
\Sigma_{F,t}
B_t^T
+
D_t
}
$$

dengan:

- $B_t$: factor loading,
- $\Sigma_{F,t}$: covariance factor,
- $D_t$: idiosyncratic covariance.

Ini sangat bagus untuk sistem kita.

Karena kita dapat mengatakan:

$$
\text{Risk}
=
\text{Systematic Risk}
+
\text{Idiosyncratic Risk}
$$

atau:

$$
\boxed{
\Sigma_t
=
\underbrace{B_t\Sigma_{F,t}B_t^T}_{\text{factor risk}}
+
\underbrace{D_t}_{\text{asset-specific risk}}
}
$$

---

# 9. Sekarang kita punya "expected return surface"

Misalnya kita ingin trading NVDA.

Model tidak hanya mengatakan:

$$
E[r_{\mathrm{NVDA}}]=0.2\%
$$

tetapi:

$$
E[
r_{\mathrm{NVDA},t+1}
\mid
r_{\mathrm{SPX}},
r_{\mathrm{NDX}},
r_{\mathrm{Gold}},
r_{\mathrm{USD}},
\sigma,
OB
]
$$

Jadi secara konseptual:

$$
\boxed{
\mu_i
=
f(
\text{asset},
\text{equity factors},
\text{macro factors},
\text{cross-asset factors},
\text{microstructure}
)
}
$$

---

# 10. Sekarang kita masuk ke optimization problem

Kita mempunyai:

$$
\boldsymbol{\mu}_t
$$

dan:

$$
\Sigma_t.
$$

Kita ingin menentukan portfolio/action:

$$
\mathbf x_t.
$$

Versi continuous Markowitz:

$$
\max_{\mathbf x}
\left[
\boldsymbol{\mu}^T\mathbf x
-
\lambda
\mathbf x^T\Sigma\mathbf x
\right]
$$

dengan:

$$
\sum_i x_i=1.
$$

Tetapi trading kita memiliki keputusan diskrit.

Misalnya:

$$
x_i\in\{-1,0,+1\}
$$

yang berarti:

- $-1$: short,
- $0$: tidak memiliki posisi,
- $+1$: long.

Sekarang masalahnya menjadi jauh lebih menarik.

---

# 11. Kita dapat mengubahnya menjadi binary variables

Gunakan:

$$
x_i^+,x_i^-\in\{0,1\}
$$

dan:

$$
x_i=x_i^+-x_i^-.
$$

Dengan constraint:

$$
x_i^++x_i^-\le1.
$$

Kemudian objective:

$$
\max
\left[
\sum_i\mu_i x_i
-
\lambda
\sum_{i,j}\Sigma_{ij}x_ix_j
\right].
$$

Sekarang kita sudah sangat dekat dengan:

$$
\boxed{\text{QUBO}}
$$

---

# 12. Dan di sinilah MaxCut menjadi relevan

Misalnya kita ingin memilih kumpulan aset yang memiliki:

- expected return tinggi,
- correlation rendah,
- factor exposure tertentu.

Kita bisa membuat graph:

$$
G=(V,E)
$$

dengan:

$$
w_{ij}=f(\Sigma_{ij},\text{dependence}_{ij})
$$

Kemudian memilih subset aset yang memenuhi objective tertentu.

Problem tersebut dapat memiliki struktur:

$$
\boxed{
\text{MaxCut / QUBO}
}
$$

Jadi MaxCut bukan sekadar "contoh quantum algorithm".

Ia menjadi cara untuk memecahkan **asset-selection / clustering / diversification problem**.

---

# 13. TSP juga bisa masuk, tetapi di tempat yang berbeda

TSP menurutku **bukan optimizer utama untuk portfolio allocation**.

Tetapi ada problem trading yang lebih natural.

Misalnya kita mempunyai beberapa execution venue:

$$
V=
\{
\text{NYSE},
\text{NASDAQ},
\text{CBOE},
\ldots
\}
$$

dan ingin mengoptimalkan sequence/order routing.

Atau jika sistem harus melakukan serangkaian transaksi:

$$
A_1\rightarrow A_2\rightarrow A_3\rightarrow\cdots
$$

dengan biaya transaksi, latency, spread, dan market impact.

Maka kita bisa mendapatkan bentuk routing/scheduling problem yang lebih dekat ke:

$$
\boxed{\text{TSP-like optimization}}
$$

Jadi kita tidak memaksakan TSP ke semua masalah.

---

# 14. Saya ingin membangun empat optimizer berbeda

Ini menurutku akan menjadi arsitektur matematis yang sangat kuat:

| Problem | Mathematical form | Solver potensial |
|---|---|---|
| Asset selection | QUBO | QAOA / SA |
| Portfolio allocation | QUBO / NLP | VQE / classical |
| Order placement | discrete optimization | QAOA / MILP |
| Execution routing | TSP / routing | QAOA / classical |
| Dynamic exit | sequential optimization | MPC / DP |

Sehingga kita tidak memiliki:

> "satu algoritma quantum untuk trading."

Tetapi:

$$
\boxed{
\textbf{Optimization Stack}
}
$$

---

# 15. Sekarang kita masukkan \$1 risk constraint

Ini harus berada **di atas optimizer**, bukan setelah optimizer.

Kita definisikan:

$$
R_{\max}=\$1.
$$

Untuk posisi $i$:

$$
R_i=
N_i|P_i^{entry}-P_i^{SL}|.
$$

Kemudian:

$$
\boxed{
\sum_iR_i\le R_{\max}
}
$$

Jika kita hanya mengizinkan satu trade:

$$
R_i\le1.
$$

Dengan beberapa posisi:

$$
\sum_iR_i\le1.
$$

Ini membuat optimizer tidak bisa mengambil keputusan yang secara matematis menguntungkan tetapi secara risk management tidak valid.

---

# 16. Dan ini membawa kita ke konsep yang lebih penting: risk budget

Aku bahkan lebih suka jika kita tidak selalu menganggap \$1 sebagai angka absolut.

Kita definisikan:

$$
B_t=\text{available risk budget}.
$$

Misalnya:

$$
B_t=\$1.
$$

Jika ada tiga posisi:

$$
R_1=0.30,
\quad
R_2=0.40,
\quad
R_3=0.20
$$

maka:

$$
\sum R_i=0.90.
$$

Masih tersedia:

$$
B_{\mathrm{remaining}}=0.10.
$$

Sehingga optimizer harus memperlakukan risk sebagai resource.

Ini secara matematis sangat mirip **resource-constrained optimization**.

---

# 17. Sekarang kita masuk ke order

Misalnya optimizer menghasilkan:

$$
x^*=
\{
\text{NVDA long}
\}
$$

Itu belum cukup.

Kita perlu:

$$
a_t=
(
P_e,
P_{SL},
P_{TP},
N,
T_{\mathrm{expiry}}
)
$$

Jadi action lengkap adalah:

$$
\boxed{
a_t=
(\text{side},
\text{entry},
\text{SL},
\text{TP},
\text{size},
\text{expiry})
}
$$

Dan:

$$
a_t^*
=
\arg\max_a
E[
U(a)
\mid
s_t
]
$$

dengan constraint:

$$
R(a)\le1.
$$

**Nah, ini menurutku adalah inti matematis dari trading engine kita.**

---

# 18. Pending order

Misalnya:

$$
a_t^*
=
(\text{LONG},100,98,106,N)
$$

Order belum filled.

Kita kemudian mengestimasi:

$$
P(F\mid a_t,s_t)
$$

yaitu probabilitas order terisi.

Expected utility:

$$
EU_{\mathrm{keep}}
=
P(F)EU_{\mathrm{trade}}
+
(1-P(F))EU_{\mathrm{nothing}}.
$$

Sedangkan jika dibatalkan:

$$
EU_{\mathrm{cancel}}
=
EU_{\mathrm{new\ opportunity}}.
$$

Keputusan:

$$
\boxed{
\text{Keep if }
EU_{\mathrm{keep}}>EU_{\mathrm{cancel}}
}
$$

Ini sudah memberikan formulasi matematis untuk ide nomor 3 yang kamu berikan sebelumnya.

---

# 19. Setelah filled, kita masuk ke optimal stopping

Misalkan:

$$
P_t>P_e.
$$

Posisi sedang profit.

Kita memiliki tiga pilihan:

$$
A=
\{
\text{hold},
\text{close},
\text{modify}
\}.
$$

Kemudian:

$$
a_t^*
=
\arg\max_{a\in A}
E[
U(a)
\mid s_t
].
$$

Jika modify:

$$
a=
(
SL_{\mathrm{new}},
TP_{\mathrm{new}}
)
$$

maka:

$$
(SL^*,TP^*)
=
\arg\max_{SL,TP}
E[
U(SL,TP)
\mid s_t
].
$$

---

# 20. Dengan demikian trailing TP milikmu menjadi masalah optimasi

Bukan:

> "Kalau profit 5%, TP naik."

Tetapi:

$$
\boxed{
TP_t^*
=
\arg\max_{TP}
E[
U(TP)
\mid s_t
]
}
$$

Dan:

$$
\boxed{
SL_t^*
=
\arg\max_{SL}
E[
U(SL)
\mid s_t
]
}
$$

Ini menurutku jauh lebih elegan.

---

# 21. Sekarang kita tambahkan regime

Aku ingin model kita memiliki:

$$
z_t
$$

sebagai **latent market regime**.

Misalnya:

$$
z_t\in
\{
\text{risk-on},
\text{neutral},
\text{risk-off}
\}.
$$

Tetapi regime tidak kita tentukan secara manual.

Kita estimasi:

$$
P(z_t=k\mid s_t).
$$

Contohnya:

$$
P(\text{risk-on})=0.72
$$

$$
P(\text{neutral})=0.20
$$

$$
P(\text{risk-off})=0.08.
$$

Kemudian:

$$
\mu_t
=
\sum_k
P(z_t=k\mid s_t)
\mu_t^{(k)}
$$

dan:

$$
\Sigma_t
=
\sum_k
P(z_t=k\mid s_t)
\Sigma_t^{(k)}
$$

plus komponen variance antar-regime jika kita ingin formulasi lengkap.

---

# 22. Gold dan USD kemudian menjadi bagian dari regime detector

Sekarang kita mendapatkan peran yang lebih tepat untuk:

$$
G_t=\text{Gold}
$$

dan:

$$
D_t=\text{USD dominance / USD factor}.
$$

Kita dapat membangun state:

$$
m_t=
[
r_{\mathrm{Gold}},
r_{\mathrm{USD}},
\sigma_{\mathrm{Gold}},
\sigma_{\mathrm{USD}},
r_{\mathrm{Equity}},
\ldots
].
$$

Kemudian:

$$
P(z_t\mid m_t).
$$

Jadi model tidak berkata:

> "Gold naik → short saham."

Melainkan:

> "Perubahan gold + USD + equity + volatility memberikan probabilitas bahwa kita sedang berada pada regime tertentu."

Itu jauh lebih defensible secara kuantitatif.

---

# 23. Bahkan USD harus kita perlakukan dengan hati-hati

Untuk model global, "USD dominance" harus kita definisikan secara eksplisit.

Kita dapat menggunakan sebuah **USD factor** $D_t$, bukan menganggap satu ticker tertentu sebagai hukum universal.

Secara abstrak:

$$
D_t=
f(
USD\text{ index},
FX,
USD\text{ liquidity}
)
$$

Kemudian:

$$
\beta_{i,\mathrm{USD}}
$$

menunjukkan sensitivitas aset terhadap faktor USD.

Misalnya:

$$
\beta_{\mathrm{NVDA},USD}<0
$$

berarti, dalam model kita, NVDA cenderung memiliki hubungan negatif dengan penguatan USD.

Tetapi nilai tersebut **harus diestimasi dari data**, bukan diasumsikan.

---

# 24. Ini menghasilkan factor exposure vector

Untuk setiap aset:

$$
\boxed{
\boldsymbol{\beta}_i
=
[
\beta_{i,\mathrm{equity}},
\beta_{i,\mathrm{gold}},
\beta_{i,\mathrm{USD}},
\beta_{i,\mathrm{rates}},
\beta_{i,\mathrm{oil}},
\ldots
]
}
$$

Contohnya secara ilustratif:

$$
\boldsymbol{\beta}_{A}
=
\begin{bmatrix}
1.2\\
0.15\\
-0.6
\end{bmatrix}
$$

artinya aset tersebut sensitif terhadap:

- equity factor,
- gold,
- USD.

Kemudian portfolio exposure:

$$
\boxed{
\boldsymbol{\beta}_{p}
=
B^T\mathbf w
}
$$

Ini memungkinkan kita membuat constraint seperti:

$$
|\beta_{\mathrm{USD}}|\le\beta_{\max}
$$

atau:

$$
|\beta_{\mathrm{Gold}}|\le\beta_{\max}.
$$

---

# 25. Dan sekarang QUBO kita menjadi jauh lebih kaya

Objective:

$$
\max_{\mathbf x}
\left[
\boldsymbol{\mu}^T\mathbf x
-
\lambda\mathbf x^T\Sigma\mathbf x
\right]
$$

ditambah factor exposure penalty:

$$
-\eta
\|
B^T\mathbf x-\beta^*
\|^2.
$$

Ditambah transaction cost:

$$
-\kappa C(\mathbf x).
$$

Ditambah risk constraint penalty:

$$
-P_R
\left(
R(\mathbf x)-R_{\max}
\right)^2.
$$

Secara keseluruhan:

$$
\boxed{
\max_{\mathbf x}
\left[
\mu^Tx
-\lambda x^T\Sigma x
-\eta\|B^Tx-\beta^*\|^2
-\kappa C(x)
-P_R(R(x)-R_{\max})^2
\right]
}
$$

dengan:

$$
x_i\in\{0,1\}
$$

atau encoding long/short yang sesuai.

Setelah ekspansi kuadratik:

$$
\boxed{
\min_{\mathbf x}
\mathbf x^TQ\mathbf x
+
\mathbf q^T\mathbf x
}
$$

yang merupakan QUBO.

**Ini sudah sangat dekat dengan sesuatu yang benar-benar bisa kita mapping ke Ising Hamiltonian.**

---

# 26. Dan akhirnya kita dapat arsitektur matematis lengkap

Aku akan mendefinisikannya seperti ini:

```text
                         GLOBAL MARKET
                              │
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
     EQUITIES              COMMODITIES             FX
        │                     │                     │
     SPX/NDX                GOLD                  USD
     Nikkei                 OIL                   ...
     IHSG                   ...
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ↓
                     MARKET FACTOR MODEL
                              │
                    β, μ, Σ, regime
                              │
                              ↓
                     MARKET STATE s_t
                              │
             ┌────────────────┼─────────────────┐
             ↓                ↓                 ↓
          Forecast         Risk Model       Order Book
             │                │                 │
             └────────────────┼─────────────────┘
                              ↓
                     OPTIMIZATION ENGINE
                              │
       ┌──────────────────────┼──────────────────────┐
       ↓                      ↓                      ↓
 Asset Selection         Entry/Order             Exit
       │                   Placement             Policy
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              ↓
                           QUBO / NLP
                              │
                     Classical / Quantum
                              │
                              ↓
                         Optimal Action
                              │
                     Risk ≤ $1 constraint
                              │
                              ↓
                         EXECUTION
                              │
                              ↓
                          POSITION
                              │
                              ↓
                     PERIODIC RE-EVALUATION
                              │
                              ↓
                     NEW STATE s_(t+Δt)
                              │
                              └──────────────→ ...
```

---

# 27. Ada satu prinsip yang ingin aku tetapkan sejak awal

**Jangan mulai dari QAOA.**

Kita mulai dari:

$$
\boxed{\text{market mathematics}}
$$

kemudian:

$$
\boxed{\text{optimization mathematics}}
$$

baru:

$$
\boxed{\text{QUBO}}
$$

baru:

$$
\boxed{\text{Ising}}
$$

baru:

$$
\boxed{\text{QAOA/VQE}}
$$

Dengan demikian, kalau nanti QAOA ternyata tidak mengalahkan classical solver, kita masih memiliki penelitian yang valid.

Kita bisa melakukan perbandingan yang fair:

$$
\text{MILP}
\leftrightarrow
\text{Simulated Annealing}
\leftrightarrow
\text{QAOA}
$$

pada **problem, encoding, dan objective yang sama**, lalu mengevaluasi:

$$
\begin{aligned}
&\text{objective value}\\
&\text{optimality gap}\\
&\text{convergence}\\
&\text{runtime}\\
&\text{number of evaluations}\\
&\text{quantum resources}\\
&\text{trading PnL}\\
&\text{Sharpe}\\
&\text{max drawdown}.
\end{aligned}
$$

Ini sejalan dengan pendekatan perbandingan terkontrol yang sebelumnya kita gunakan untuk pekerjaan VQE/QAOA-mu. 

---

# 28. Tahap desain berikutnya

Menurutku sekarang **jangan langsung membangun seluruh sistem sekaligus**. Kita turunkan secara matematis dalam urutan berikut:

### Tahap A - Market State

Kita definisikan secara rigor:

$$
s_t
$$

beserta data:

$$
\text{OHLCV}
+
\text{order book}
+
\text{BTC/ETH}
+
\text{equity indices}
+
\text{Gold}
+
\text{USD}
+
\text{FX}
$$

---

### Tahap B - Dynamic Factor Model

Kita turunkan:

$$
r_{i,t}
=
\alpha_i+
\beta_i^Tf_t+
\epsilon_{i,t}
$$

hingga:

$$
\Sigma_t
=
B_t\Sigma_{F,t}B_t^T+D_t.
$$

---

### Tahap C - Short-Horizon Forecast

Kita definisikan:

$$
\mu_{i,t+\Delta}
=
E[
r_{i,t+\Delta}|s_t
]
$$

dan:

$$
\sigma_{i,t+\Delta}^2
=
Var[
r_{i,t+\Delta}|s_t
].
$$

---

### Tahap D - Trading Optimization

Kita turunkan:

$$
\boxed{
a_t^*
=
\arg\max_a
E[U(a)|s_t]
}
$$

dengan:

$$
R(a)\le\$1.
$$

---

### Tahap E - QUBO

Kita ubah decision variables menjadi binary:

$$
x_i\in\{0,1\}
$$

dan turunkan seluruh objective menjadi:

$$
\boxed{
x^TQx+c^Tx
}
$$

---

### Tahap F - Ising

Kemudian:

$$
x_i=\frac{1-z_i}{2}
$$

sehingga:

$$
\boxed{
H_C
=
\sum_i h_iZ_i+
\sum_{i<j}J_{ij}Z_iZ_j
}
$$

dan baru kita bahas:

$$
\boxed{\text{QAOA}}
$$

---

### Tahap G - Dynamic Re-optimization

Setelah posisi terbuka:

$$
s_t
\rightarrow
a_t
\rightarrow
s_{t+\Delta}
$$

kita ulangi optimasi:

$$
a_{t+\Delta}^*
=
\arg\max_a
E[
U(a)|s_{t+\Delta}
].
$$

Di sinilah sistem berubah dari **static portfolio optimizer** menjadi **dynamic quantitative trading system**.

---

Dan aku kira **inilah desain yang seharusnya kita kejar**: bukan "bot crypto yang memakai QAOA", melainkan **kerangka mathematical systematic trading yang asset-agnostic**, di mana crypto, saham AS, Jepang, Eropa, Indonesia, emas, FX, dan sebagainya hanyalah instansiasi dari universe yang berbeda.

Yang paling penting, desain ini memungkinkan seluruh pengetahuan yang sudah kamu bangun sebelumnya tetap hidup: **Markowitz memberikan objective risk-return, factor model memberikan market context, covariance memberikan risk coupling, QUBO memberikan discrete optimization, Ising memberikan Hamiltonian, dan QAOA/VQE menjadi solver-sementara MPC/sequential optimization mengubah semuanya menjadi sistem trading yang terus mengambil keputusan ulang.**

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

## Prompt:
8/17/2026, 9:42:43 PM

lanjut tahap B

## Response:
8/17/2026, 9:42:43 PM

Tentu. **Tahap B adalah bagian yang sangat penting**, karena di sinilah `market state` yang kita bangun pada Tahap A mulai diubah menjadi **distribusi probabilistik return masa depan**. Dengan kata lain, kita berpindah dari:

$$
\boxed{\text{Apa yang sedang terjadi di pasar?}}
$$

menjadi:

$$
\boxed{\text{Apa yang secara probabilistik mungkin terjadi berikutnya?}}
$$

Dan saya ingin menjaga disiplin desain kita: **Tahap B belum melakukan optimasi trading**. Ia hanya menghasilkan informasi yang nanti dikonsumsi optimizer.

---

# Tahap B — Conditional Forecast & Dynamic Risk Model

Secara keseluruhan kita ingin membangun:

$$
\boxed{
S_t
\longrightarrow
P(\mathbf R_{t+\Delta}\mid S_t)
}
$$

kemudian mengambil:

$$
\boxed{
\boldsymbol{\mu}_t
=
E[\mathbf R_{t+\Delta}\mid S_t]
}
$$

dan:

$$
\boxed{
\Sigma_t
=
\operatorname{Cov}
(\mathbf R_{t+\Delta}\mid S_t)
}
$$

serta:

$$
\boxed{
B_t
=
\text{factor loading}
}
$$

sehingga nantinya:

$$
\boxed{
\Sigma_t
=
B_t\Sigma_{F,t}B_t^T+D_t.
}
$$

Inilah objek yang akan masuk ke Tahap C/D.

---

# B.1. Mengapa kita membutuhkan distribusi, bukan sekadar prediksi harga?

Misalkan sistem mengatakan:

$$
E[r_{\mathrm{SOL},t+1}\mid S_t]=0.5\%.
$$

Sekilas ini terlihat bagus.

Tetapi ada dua kemungkinan:

### Kondisi A

$$
r_{t+1}\sim\mathcal N(0.005,0.002^2)
$$

### Kondisi B

$$
r_{t+1}\sim\mathcal N(0.005,0.02^2)
$$

Expected return keduanya sama:

$$
\mu=0.5\%.
$$

Tetapi risk-nya sangat berbeda.

Karena itu optimizer kita tidak boleh hanya mendapatkan:

$$
\mu.
$$

Ia harus mendapatkan:

$$
\boxed{
(\mu,\Sigma)
}
$$

atau bahkan distribusi lengkap:

$$
\boxed{
P(\mathbf R_{t+\Delta}\mid S_t).
}
$$

---

# B.2. Definisi formal

Misalkan:

$$
\mathbf R_{t+\Delta}
=
\begin{bmatrix}
R_{1,t+\Delta}\\
R_{2,t+\Delta}\\
\vdots\\
R_{N,t+\Delta}
\end{bmatrix}
$$

adalah vector return masa depan.

Kita ingin memodelkan:

$$
\boxed{
\mathbf R_{t+\Delta}
\mid
S_t.
}
$$

Secara umum:

$$
\mathbf R_{t+\Delta}
\mid S_t
\sim
\mathcal D
\left(
\boldsymbol{\mu}_t,
\Sigma_t,
\Theta_t
\right)
$$

dengan $\Theta_t$ berisi parameter distribusi lain jika diperlukan.

Untuk versi pertama, kita dapat menggunakan:

$$
\boxed{
\mathbf R_{t+\Delta}
\mid S_t
\approx
\mathcal N(\boldsymbol{\mu}_t,\Sigma_t)
}
$$

tetapi ini adalah **working approximation**, bukan klaim bahwa return finansial benar-benar Gaussian.

---

# B.3. Mengapa conditional?

Perhatikan perbedaan:

### Unconditional

$$
E[R_i]
$$

hanya menggunakan sejarah return.

### Conditional

$$
\boxed{
E[R_{i,t+\Delta}\mid S_t]
}
$$

mempertimbangkan keadaan pasar saat ini.

Ini jauh lebih sesuai dengan sistem kita.

Misalnya historical average return SOL:

$$
E[R_{\mathrm{SOL}}]=0.1\%.
$$

Tetapi ketika:

$$
S_t=s_{\mathrm{risk-off}},
$$

mungkin:

$$
E[R_{\mathrm{SOL}}\mid S_t]
=
-0.3\%.
$$

Sedangkan ketika:

$$
S_t=s_{\mathrm{risk-on}},
$$

mungkin:

$$
E[R_{\mathrm{SOL}}\mid S_t]
=
0.4\%.
$$

Jadi:

$$
\boxed{
\mu_t
\neq
\text{historical mean tetap}.
}
$$

---

# B.4. Kita mulai dari model factor

Sekarang kita gunakan struktur yang sudah kita tetapkan.

Untuk aset $i$:

$$
\boxed{
r_{i,t}
=
\alpha_i+
\boldsymbol{\beta}_i^T\mathbf f_t+
\epsilon_{i,t}
}
$$

dengan:

$$
\mathbf f_t
=
\begin{bmatrix}
f_{1,t}\\
\vdots\\
f_{K,t}
\end{bmatrix}.
$$

Dalam bentuk vector:

$$
\boxed{
\mathbf r_t
=
\boldsymbol{\alpha}
+
B\mathbf f_t
+
\boldsymbol{\epsilon}_t
}
$$

dengan:

$$
B=
\begin{bmatrix}
\beta_{11}&\cdots&\beta_{1K}\\
\vdots&\ddots&\vdots\\
\beta_{N1}&\cdots&\beta_{NK}
\end{bmatrix}.
$$

---

# B.5. Apa arti $B$?

Misalnya:

$$
B=
\begin{pmatrix}
1.2 & -0.4 & 0.1\\
0.8 & -0.2 & 0.3\\
1.5 & -0.6 & 0.05
\end{pmatrix}
$$

dengan factor:

$$
\mathbf f=
\begin{bmatrix}
\text{Equity}\\
\text{USD}\\
\text{Gold}
\end{bmatrix}.
$$

Maka untuk aset pertama:

$$
r_1
=
\alpha_1+
1.2f_{\mathrm{Equity}}
-0.4f_{\mathrm{USD}}
+0.1f_{\mathrm{Gold}}
+\epsilon_1.
$$

Jadi beta bukan sekadar indikator.

Ia merupakan **pemetaan matematis dari factor shock ke asset return**.

---

# B.6. Penurunan expected return

Mulai dari:

$$
\mathbf r_{t+1}
=
\boldsymbol{\alpha}
+
B\mathbf f_{t+1}
+
\boldsymbol{\epsilon}_{t+1}.
$$

Kita mengambil conditional expectation:

$$
E[
\mathbf r_{t+1}
\mid S_t
].
$$

Karena expectation linear:

$$
=
E[\boldsymbol{\alpha}\mid S_t]
+
E[B\mathbf f_{t+1}\mid S_t]
+
E[\boldsymbol{\epsilon}_{t+1}\mid S_t].
$$

Jika:

$$
\boldsymbol{\alpha}
$$

dan $B$ dianggap parameter:

$$
=
\boldsymbol{\alpha}
+
B
E[
\mathbf f_{t+1}\mid S_t
]
+
E[
\boldsymbol{\epsilon}_{t+1}\mid S_t].
$$

Kita asumsikan:

$$
E[
\boldsymbol{\epsilon}_{t+1}
\mid S_t
]=0.
$$

Maka:

$$
\boxed{
\boldsymbol{\mu}_t
=
\boldsymbol{\alpha}
+
B\boldsymbol{\mu}_{F,t}
}
$$

dengan:

$$
\boxed{
\boldsymbol{\mu}_{F,t}
=
E[
\mathbf f_{t+1}\mid S_t
].
}
$$

Ini adalah persamaan fundamental Tahap B.

---

# B.7. Perhatikan sesuatu yang sangat penting

Expected return aset:

$$
\mu_{i,t}
$$

sekarang berasal dari:

$$
\boxed{
\text{asset-specific component}
+
\text{factor-driven component}.
}
$$

Secara eksplisit:

$$
\mu_{i,t}
=
\alpha_i
+
\sum_{k=1}^{K}
\beta_{ik}\mu_{F_k,t}.
$$

Contohnya:

$$
\mu_{\mathrm{NVDA},t}
=
\alpha_{\mathrm{NVDA}}
+
\beta_{\mathrm{SPX}}\mu_{\mathrm{SPX},t}
+
\beta_{\mathrm{USD}}\mu_{\mathrm{USD},t}
+
\beta_{\mathrm{Gold}}\mu_{\mathrm{Gold},t}
+\cdots.
$$

---

# B.8. Tetapi ada masalah

Bagaimana kita memperoleh:

$$
\mu_{F_k,t}
=
E[f_{k,t+1}\mid S_t]?
$$

Kita membutuhkan **factor forecasting model**.

Ini berarti Tahap B sebenarnya mempunyai dua tingkat:

$$
\boxed{
S_t
\rightarrow
\text{factor forecast}
\rightarrow
\text{asset forecast}.
}
$$

Bukan:

$$
S_t\rightarrow\mu_i
$$

secara black-box.

---

# B.9. Factor forecast

Untuk setiap factor $k$, kita dapat membuat:

$$
f_{k,t+1}
=
g_k(S_t)+\eta_{k,t+1}.
$$

Sehingga:

$$
\boxed{
\mu_{F_k,t}
=
g_k(S_t).
}
$$

Maka:

$$
\boxed{
\boldsymbol{\mu}_t
=
\boldsymbol{\alpha}
+
B g(S_t).
}
$$

Ini membuat arsitektur model sangat jelas.

---

# B.10. Tetapi jangan langsung memakai model machine learning yang rumit

Untuk baseline, saya sangat menyarankan model linear/dynamic terlebih dahulu.

Misalnya:

$$
f_{k,t+1}
=
c_k+
\boldsymbol{\theta}_k^T S_t+
\eta_{k,t+1}.
$$

Maka:

$$
\boxed{
\mu_{F_k,t}
=
c_k+
\boldsymbol{\theta}_k^T S_t.
}
$$

Dengan demikian:

$$
\boxed{
\boldsymbol{\mu}_t
=
\boldsymbol{\alpha}
+
B
\left(
\mathbf c+\Theta S_t
\right)
}
$$

untuk representasi matrix yang sesuai.

---

# B.11. Kenapa baseline linear penting?

Karena nanti kita ingin menjawab:

> Apakah peningkatan performa benar-benar berasal dari model yang lebih pintar?

Kita bisa membandingkan:

$$
\text{Historical Mean}
$$

vs.

$$
\text{Linear Factor Model}
$$

vs.

$$
\text{Nonlinear ML}
$$

vs.

$$
\text{Regime-dependent Model}.
$$

Tanpa baseline, kita tidak tahu apakah kompleksitas kita berguna.

---

# B.12. Estimasi beta

Sekarang kita perlu memperoleh:

$$
B_t.
$$

Untuk satu aset:

$$
r_i
=
\alpha_i+
\beta_i^Tf+
\epsilon_i.
$$

Kita memiliki observasi:

$$
t=1,\ldots,T.
$$

Dengan matrix design:

$$
X=
\begin{bmatrix}
1&f_{1,1}&\cdots&f_{K,1}\\
1&f_{1,2}&\cdots&f_{K,2}\\
\vdots&\vdots&&\vdots\\
1&f_{1,T}&\cdots&f_{K,T}
\end{bmatrix}
$$

dan:

$$
\mathbf y_i=
\begin{bmatrix}
r_{i,1}\\
r_{i,2}\\
\vdots\\
r_{i,T}
\end{bmatrix}.
$$

Model:

$$
\mathbf y_i=X\boldsymbol{\theta}_i+\boldsymbol\epsilon_i
$$

dengan:

$$
\boldsymbol{\theta}_i=
\begin{bmatrix}
\alpha_i\\
\beta_{i1}\\
\vdots\\
\beta_{iK}
\end{bmatrix}.
$$

OLS memberikan:

$$
\boxed{
\hat{\boldsymbol{\theta}}_i
=
(X^TX)^{-1}X^T\mathbf y_i
}
$$

jika $X^TX$ invertible.

---

# B.13. Tetapi beta tidak boleh dianggap konstan selamanya

Untuk short-term trading:

$$
\beta_{i,t}
$$

lebih masuk akal daripada:

$$
\beta_i.
$$

Karena hubungan:

$$
\mathrm{NVDA}\leftrightarrow\mathrm{NDX}
$$

atau:

$$
\mathrm{SOL}\leftrightarrow\mathrm{BTC}
$$

dapat berubah.

Maka kita menggunakan rolling estimation:

$$
\boxed{
\hat B_t
=
\operatorname{OLS}
(
\text{window ending at }t
)
}
$$

atau nantinya metode yang lebih canggih seperti exponentially weighted estimation atau state-space/Kalman filtering.

Untuk versi pertama:

$$
\boxed{\text{rolling OLS}}
$$

sudah cukup.

---

# B.14. Dynamic covariance

Sekarang bagian yang paling penting untuk optimizer.

Mulai:

$$
\mathbf r_t
=
\boldsymbol{\alpha}
+
B_t\mathbf f_t
+
\boldsymbol\epsilon_t.
$$

Covariance:

$$
\Sigma_t
=
\operatorname{Cov}
(\mathbf r_t\mid S_t).
$$

Karena:

$$
\mathbf r_t
=
B_t\mathbf f_t+\epsilon_t
$$

untuk bagian random:

$$
\operatorname{Cov}
(B_t\mathbf f_t+\epsilon_t).
$$

Dengan sifat covariance:

$$
\operatorname{Cov}(AX)
=
A\operatorname{Cov}(X)A^T
$$

maka:

$$
\operatorname{Cov}(B_t\mathbf f_t)
=
B_t
\Sigma_{F,t}
B_t^T.
$$

Jika factor dan residual uncorrelated:

$$
\operatorname{Cov}(\mathbf f_t,\epsilon_t)=0,
$$

maka:

$$
\boxed{
\Sigma_t
=
B_t\Sigma_{F,t}B_t^T
+
D_t
}
$$

dengan:

$$
D_t
=
\operatorname{Cov}(\epsilon_t).
$$

Ini adalah persamaan yang sangat penting untuk seluruh proyek.

---

# B.15. Mengapa decomposition ini sangat berguna?

Kita dapat memisahkan:

$$
\boxed{
\text{Total Risk}
=
\text{Systematic Risk}
+
\text{Idiosyncratic Risk}.
}
$$

Systematic:

$$
\boxed{
\Sigma_t^{sys}
=
B_t\Sigma_{F,t}B_t^T
}
$$

Idiosyncratic:

$$
\boxed{
\Sigma_t^{idio}=D_t.
}
$$

Jadi:

$$
\boxed{
\Sigma_t
=
\Sigma_t^{sys}
+
\Sigma_t^{idio}.
}
$$

---

# B.16. Contoh sederhana

Misalkan:

$$
B=
\begin{bmatrix}
1.2\\
0.8
\end{bmatrix}
$$

dan factor covariance:

$$
\Sigma_F=
\begin{bmatrix}
0.0004
\end{bmatrix}.
$$

Maka:

$$
B\Sigma_FB^T
=
\begin{bmatrix}
1.2\\
0.8
\end{bmatrix}
(0.0004)
\begin{bmatrix}
1.2&0.8
\end{bmatrix}
$$

sehingga:

$$
=
\begin{bmatrix}
0.000576&0.000384\\
0.000384&0.000256
\end{bmatrix}.
$$

Terlihat bahwa **satu common factor saja sudah menghasilkan covariance antar-aset**.

Ini adalah salah satu alasan factor model sangat natural untuk sistem kita.

---

# B.17. Estimasi factor covariance

Kita perlu:

$$
\Sigma_{F,t}.
$$

Versi sederhana:

$$
\boxed{
\hat\Sigma_{F,t}
=
\operatorname{Cov}
(
\mathbf f_{t-W+1:t}
)
}
$$

menggunakan rolling window.

Tetapi karena kita memodelkan masa depan:

$$
\boxed{
\Sigma_{F,t}
=
\operatorname{Cov}
(
\mathbf f_{t+\Delta}
\mid S_t
)
}
$$

secara ideal.

Ini berarti kita nantinya juga membutuhkan **conditional volatility model**.

---

# B.18. Volatility clustering

Untuk satu factor:

$$
f_t=\mu_t+\epsilon_t
$$

dan:

$$
\epsilon_t=\sigma_t z_t
$$

dengan:

$$
z_t\sim\text{standardized noise}.
$$

Kemudian:

$$
\sigma_t^2
$$

dapat dimodelkan secara dinamis.

Contoh klasik:

$$
\boxed{
\sigma_t^2
=
\omega
+
\alpha\epsilon_{t-1}^2
+
\beta\sigma_{t-1}^2
}
$$

yaitu GARCH(1,1).

Namun sekali lagi, saya **tidak akan menjadikan GARCH sebagai keharusan versi pertama**.

Kita dapat mulai dengan EWMA.

---

# B.19. EWMA volatility

Definisikan:

$$
\boxed{
\sigma_t^2
=
\lambda\sigma_{t-1}^2
+
(1-\lambda)r_{t-1}^2
}
$$

dengan:

$$
0<\lambda<1.
$$

Unroll:

$$
\sigma_t^2
=
\lambda^2\sigma_{t-2}^2
+
\lambda(1-\lambda)r_{t-2}^2
+
(1-\lambda)r_{t-1}^2.
$$

Teruskan:

$$
\boxed{
\sigma_t^2
\approx
(1-\lambda)
\sum_{j=1}^{\infty}
\lambda^{j-1}r_{t-j}^2.
}
$$

Jadi return terbaru mendapatkan bobot terbesar.

Ini sangat sesuai dengan short-term trading.

---

# B.20. Dynamic correlation

Volatility saja belum cukup.

Kita membutuhkan:

$$
\Sigma_t
=
D_t^{1/2}R_tD_t^{1/2}
$$

dengan:

$$
D_t
=
\operatorname{diag}
(
\sigma_{1,t}^2,\ldots,\sigma_{N,t}^2
)
$$

dan:

$$
R_t
=
\text{correlation matrix}.
$$

Ini adalah bentuk yang sangat berguna:

$$
\boxed{
\Sigma_t
=
D_t^{1/2}
R_t
D_t^{1/2}.
}
$$

---

# B.21. Mengapa ini penting?

Misalnya:

$$
\sigma_1=2\%,
\qquad
\sigma_2=3\%.
$$

dan:

$$
\rho_{12}=0.8.
$$

Maka covariance:

$$
\Sigma_{12}
=
\rho_{12}\sigma_1\sigma_2.
$$

Sehingga:

$$
\Sigma_{12}
=
0.8(0.02)(0.03)
=
0.00048.
$$

Risk portfolio kemudian bergantung bukan hanya pada individual volatility, tetapi juga hubungan:

$$
\boxed{
\text{Risk}
\leftrightarrow
\text{correlation}.
}
$$

Ini nantinya menghasilkan coupling:

$$
J_{ij}
$$

dalam QUBO/Ising kita.

---

# B.22. Factor model vs direct covariance

Sekarang ada dua cara untuk mendapatkan covariance.

### Cara 1

Direct:

$$
\Sigma_t^{direct}.
$$

### Cara 2

Factor:

$$
\boxed{
\Sigma_t^{factor}
=
B_t\Sigma_{F,t}B_t^T+D_t.
}
$$

Saya menyarankan **keduanya kita hitung**.

Karena nanti kita dapat menguji:

$$
\Sigma_t^{direct}
$$

vs.

$$
\Sigma_t^{factor}.
$$

Factor model biasanya jauh lebih menarik ketika:

$$
N\gg K.
$$

---

# B.23. Mengapa?

Misalnya:

$$
N=100
$$

aset.

Covariance matrix mempunyai:

$$
\frac{N(N+1)}2
$$

parameter unik.

Untuk:

$$
N=100:
$$

$$
5050
$$

parameter.

Sedangkan jika:

$$
K=10
$$

factors, kita hanya membutuhkan struktur factor:

$$
B\in\mathbb R^{100\times10}
$$

plus:

$$
\Sigma_F\in\mathbb R^{10\times10}
$$

dan residual variances.

Jauh lebih terstruktur.

---

# B.24. Regime dependence

Sekarang kita tambahkan ide yang menurutku sangat penting dari desain awal kita:

$$
z_t
$$

sebagai market regime.

Misalnya:

$$
z_t\in\{1,2,3\}.
$$

Kita dapat memiliki:

$$
\mu_t^{(k)}
$$

dan:

$$
\Sigma_t^{(k)}
$$

untuk setiap regime $k$.

Jika:

$$
p_{k,t}
=
P(z_t=k\mid S_t),
$$

maka:

$$
\boxed{
\mu_t
=
\sum_kp_{k,t}\mu_t^{(k)}
}
$$

---

# B.25. Tetapi covariance mixture tidak sesederhana weighted average

Ini penting secara matematis.

Jika:

$$
R\mid z=k
\sim
(\mu_k,\Sigma_k)
$$

dan:

$$
P(z=k)=p_k,
$$

maka:

$$
E[R]
=
\sum_kp_k\mu_k.
$$

Namun covariance:

$$
\operatorname{Cov}(R)
=
E[\operatorname{Cov}(R\mid z)]
+
\operatorname{Cov}(E[R\mid z]).
$$

Sehingga:

$$
\boxed{
\Sigma
=
\sum_kp_k\Sigma_k
+
\sum_kp_k
(\mu_k-\mu)
(\mu_k-\mu)^T
}
$$

dengan:

$$
\mu=\sum_kp_k\mu_k.
$$

Term kedua sering terlupakan.

Ia merepresentasikan **uncertainty akibat ketidakpastian regime**.

---

# B.26. Ini sangat menarik untuk trading

Misalnya:

$$
P(\text{risk-on})=0.5
$$

dan:

$$
P(\text{risk-off})=0.5.
$$

Meskipun masing-masing regime memiliki volatility kecil, perbedaan expected return antar-regime dapat membuat unconditional conditional-on-state variance menjadi besar.

Artinya:

$$
\boxed{
\text{regime uncertainty itself is risk}.
}
$$

Ini sangat cocok untuk risk-aware optimizer kita.

---

# B.27. Bagaimana kita menentukan regime?

Untuk baseline, kita dapat menggunakan fitur:

$$
S_t^{macro}
=
[
r_{\mathrm{Gold}},
r_{\mathrm{USD}},
r_{\mathrm{SPX}},
r_{\mathrm{VIX}},
\sigma_{\mathrm{market}},
\ldots
].
$$

Kemudian model:

$$
P(z_t=k\mid S_t).
$$

Ada beberapa pendekatan:

### Model 1 — threshold

Sederhana, tetapi kasar.

### Model 2 — clustering

$$
k\text{-means}
$$

atau Gaussian Mixture Model.

### Model 3 — Hidden Markov Model

$$
\boxed{\text{HMM}}
$$

lebih menarik karena regime memiliki persistence.

Untuk sistem kita, **HMM adalah kandidat yang sangat bagus**, tetapi saya akan menjadikannya versi B2, bukan baseline B0.

---

# B.28. Dynamic factor model

Sekarang kita bisa menyusun keseluruhan model:

$$
\boxed{
\mathbf r_{t+1}
=
\boldsymbol{\alpha}_t
+
B_t\mathbf f_{t+1}
+
\boldsymbol{\epsilon}_{t+1}
}
$$

dengan:

$$
E[
\mathbf f_{t+1}\mid S_t
]
=
\boldsymbol{\mu}_{F,t}
$$

dan:

$$
\operatorname{Cov}
(
\mathbf f_{t+1}\mid S_t
)
=
\Sigma_{F,t}.
$$

Sehingga:

$$
\boxed{
\boldsymbol{\mu}_t
=
\boldsymbol{\alpha}_t+
B_t\boldsymbol{\mu}_{F,t}
}
$$

dan:

$$
\boxed{
\Sigma_t
=
B_t\Sigma_{F,t}B_t^T+D_t.
}
$$

Ini adalah **output utama Tahap B**.

---

# B.29. Tetapi kita belum selesai

Karena target kita adalah **short-term trading**.

Expected return:

$$
\mu_t
$$

harus dibandingkan dengan biaya transaksi.

Misalnya expected gross return:

$$
\mu_{gross}.
$$

Expected cost:

$$
C_t.
$$

Maka:

$$
\boxed{
\mu_{net,t}
=
\mu_{gross,t}-C_t.
}
$$

Lebih lengkap:

$$
C_t
=
C_{\mathrm{spread}}
+
C_{\mathrm{fee}}
+
C_{\mathrm{slippage}}
+
C_{\mathrm{impact}}.
$$

Ini sangat penting.

Jika:

$$
\mu_{gross}=0.08\%
$$

tetapi:

$$
C=0.10\%,
$$

maka:

$$
\mu_{net}=-0.02\%.
$$

Secara trading:

$$
\boxed{\text{jangan trade}}
$$

meskipun forecast gross return positif.

---

# B.30. Kita juga perlu probabilitas arah

Dari distribusi:

$$
R\sim\mathcal N(\mu,\sigma^2)
$$

kita dapat memperoleh:

$$
P(R>0)
=
\Phi
\left(
\frac{\mu}{\sigma}
\right).
$$

Misalnya:

$$
\mu=0.002
$$

dan:

$$
\sigma=0.01.
$$

Maka:

$$
P(R>0)
=
\Phi(0.2)
\approx0.579.
$$

Jadi expected return positif, tetapi probabilitas naik hanya sekitar 58%.

Ini jauh lebih informatif daripada:

> "model memprediksi harga naik."

---

# B.31. Bahkan kita dapat menghitung probability of hitting TP/SL

Ini akan sangat berguna di Tahap C/D.

Misalnya entry:

$$
P_0.
$$

Stop:

$$
P_{SL}
$$

dan target:

$$
P_{TP}.
$$

Kita ingin:

$$
P(\text{TP hit before SL}\mid S_t).
$$

Untuk proses diffusion sederhana, kita dapat menggunakan model first-passage probability.

Jika log-price mengikuti:

$$
dX_t=\mu dt+\sigma dW_t,
$$

dengan:

$$
X_0=0,
$$

upper barrier:

$$
u>0
$$

dan lower barrier:

$$
-l<0,
$$

maka probabilitas mencapai upper barrier sebelum lower barrier dapat diturunkan sebagai:

$$
\boxed{
P_{\mathrm{TP}}
=
\frac{
1-e^{-2\mu l/\sigma^2}
}{
e^{2\mu u/\sigma^2}
-
e^{-2\mu l/\sigma^2}
}
}
$$

untuk $\mu\neq0$, dengan formulasi yang ekuivalen tergantung definisi barrier.

Untuk:

$$
\mu=0,
$$

hasilnya menyederhana menjadi:

$$
\boxed{
P_{\mathrm{TP}}
=
\frac{l}{u+l}.
}
$$

**Ini belum kita gunakan sekarang**, tetapi nantinya sangat berguna ketika menentukan TP/SL secara matematis.

---

# B.32. Jadi Tahap B mulai terhubung langsung dengan ide awalmu

Kamu sebelumnya mengusulkan:

> setiap trade memiliki risk \$1.

Sekarang kita dapat memisahkan:

### Forecast

$$
\mu_t,\Sigma_t
$$

### Risk

$$
SL
$$

### Reward

$$
TP
$$

### Probability

$$
P(TP\text{ before }SL)
$$

sehingga expected value dapat ditulis:

$$
\boxed{
EV
=
P_{TP}G
-
(1-P_{TP})L
-
C
}
$$

dengan:

$$
L=\$1
$$

sebagai loss budget.

Ini nantinya menjadi salah satu objective yang sangat natural untuk trading engine.

---

# B.33. Kita sekarang memiliki hierarki matematika

Perhatikan:

$$
\boxed{
S_t
}
$$

↓

$$
\boxed{
\text{Factor Forecast}
}
$$

↓

$$
\boxed{
\boldsymbol{\mu}_{F,t},\Sigma_{F,t}
}
$$

↓

$$
\boxed{
B_t
}
$$

↓

$$
\boxed{
\boldsymbol{\mu}_t,\Sigma_t
}
$$

↓

$$
\boxed{
P(TP),P(SL),EV
}
$$

↓

Tahap C/D:

$$
\boxed{
\text{Optimization}
}
$$

Ini sangat bersih secara matematis.

---

# B.34. Spesifikasi Tahap B versi pertama

Saya sarankan kita membuat **B0** terlebih dahulu:

$$
\boxed{
\mathbf r_{t+1}
=
\alpha+
B_t\mathbf f_{t+1}
+
\epsilon_{t+1}
}
$$

dengan:

### Factor mean

$$
\boxed{
\mu_{F,t}
=
\text{rolling conditional estimate}
}
$$

### Factor covariance

$$
\boxed{
\Sigma_{F,t}
=
\text{rolling/EWMA covariance}
}
$$

### Factor loading

$$
\boxed{
B_t
=
\text{rolling OLS}
}
$$

### Residual covariance

Versi pertama:

$$
\boxed{
D_t
=
\operatorname{diag}
(
\sigma_{\epsilon_1,t}^2,\ldots,
\sigma_{\epsilon_N,t}^2
)
}
$$

### Output

$$
\boxed{
\mu_t=\alpha+B_t\mu_{F,t}
}
$$

dan:

$$
\boxed{
\Sigma_t
=
B_t\Sigma_{F,t}B_t^T+D_t.
}
$$

---

# B.35. Kemudian B1

Setelah B0 berhasil:

$$
\boxed{\text{EWMA dynamic volatility}}
$$

sehingga:

$$
\sigma_{i,t}
$$

dan:

$$
\Sigma_{F,t}
$$

menjadi time-varying.

---

# B.36. B2

Kemudian:

$$
\boxed{\text{regime model}}
$$

misalnya:

$$
P(z_t=k\mid S_t).
$$

Kemudian:

$$
\mu_t
=
\sum_kp_{k,t}\mu_t^{(k)}
$$

dan:

$$
\Sigma_t
=
\sum_kp_{k,t}\Sigma_t^{(k)}
+
\sum_kp_{k,t}
(\mu_t^{(k)}-\mu_t)
(\mu_t^{(k)}-\mu_t)^T.
$$

---

# B.37. B3

Barulah kita dapat mencoba model nonlinear:

$$
\mu_t
=
f_\theta(S_t)
$$

misalnya:

- Gradient Boosting,
- Random Forest,
- Neural Network,
- temporal model,
- atau model lain.

Tetapi model nonlinear tersebut **harus dibandingkan terhadap B0/B1/B2**, bukan langsung dianggap lebih baik.

---

# B.38. B4 — Distributional forecast

Jika ingin lebih jauh:

$$
R_{t+\Delta}\mid S_t
$$

tidak lagi dianggap Gaussian.

Kita bisa menggunakan:

$$
\text{Student-}t
$$

untuk heavy tails:

$$
R\sim t_\nu(\mu,\sigma).
$$

Ini masuk akal secara finansial karena return memiliki tail risk yang sering lebih besar daripada Gaussian.

Kemudian:

$$
P(R<-L)
$$

dapat dihitung secara lebih realistis.

---

# B.39. Dan ini sangat relevan dengan risk \$1

Misalkan dua model menghasilkan:

$$
\mu=0.3\%.
$$

Model Gaussian:

$$
\sigma=0.5\%.
$$

Model Student-$t$:

$$
\sigma=0.5\%,
\quad
\nu=4.
$$

Keduanya memiliki mean dan variance yang sama, tetapi tail probability berbeda.

Untuk trading dengan SL:

$$
L=\$1,
$$

perbedaan tail behavior tersebut dapat menghasilkan perbedaan besar pada:

$$
P(SL).
$$

Jadi pada akhirnya:

$$
\boxed{
\text{distributional modeling}
\rightarrow
\text{better risk estimation}.
}
$$

---

# B.40. Hal yang paling saya sukai dari desain ini

Sekarang sistem kita tidak lagi terlihat seperti:

> "Saya punya AI yang memprediksi harga."

Ia menjadi:

$$
\boxed{
\text{State}
\rightarrow
\text{Conditional Distribution}
\rightarrow
\text{Risk/Reward Distribution}
\rightarrow
\text{Optimization}
\rightarrow
\text{Execution}.
}
$$

Itu jauh lebih dekat dengan cara kita seharusnya memformulasikan **systematic trading problem**.

---

# B.41. Hubungan dengan quantum optimization

Dan sekarang kita bisa melihat dengan jelas mengapa QUBO/Ising akan muncul secara natural.

Tahap B menghasilkan:

$$
\mu_t
$$

dan:

$$
\Sigma_t.
$$

Kemudian Tahap C/D akan membuat objective seperti:

$$
\max_x
\left[
\mu_t^Tx
-
\lambda x^T\Sigma_tx
-
C(x)
-
P_{\mathrm{risk}}(x)
\right].
$$

Perhatikan:

$$
\boxed{
\Sigma_t
}
$$

muncul pada quadratic term.

Artinya:

$$
\Sigma_{ij,t}
$$

akan menjadi coupling antara decision $i$ dan $j$.

Secara konseptual:

$$
\boxed{
\Sigma_{ij,t}
\longrightarrow
Q_{ij,t}
\longrightarrow
J_{ij,t}
}
$$

dan akhirnya:

$$
\boxed{
J_{ij,t}Z_iZ_j
}
$$

di Hamiltonian.

Jadi covariance yang kita bangun di Tahap B bukan sekadar statistik tambahan.

**Ia pada akhirnya menjadi interaksi antar-qubit dalam Ising Hamiltonian kita.**

Itulah hubungan yang sangat bagus antara finance dan quantum computing dalam arsitektur ini.

---

# B.42. Pipeline yang sekarang sudah kita miliki

```text
                    MARKET DATA
                         │
                         ↓
                ┌─────────────────┐
                │    Tahap A      │
                │   Market State  │
                └────────┬────────┘
                         │
                         ↓
              S_t ∈ Information Set
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
     Factor Mean    Factor Cov.    Factor Loading
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                ┌─────────────────┐
                │    Tahap B      │
                │ Conditional     │
                │ Forecast Model  │
                └────────┬────────┘
                         │
                 ┌───────┴────────┐
                 ↓                ↓
              μ_t              Σ_t
                 │                │
                 └───────┬────────┘
                         ↓
                 Tahap C / D
                 Optimization
                         │
                         ↓
                    QUBO / Ising
                         │
                         ↓
                     QAOA / Solver
                         │
                         ↓
                      ACTION
                         │
                         ↓
                    EXECUTION
                         │
                         ↓
                    NEW STATE
                         │
                         └────────→ ...
```

---

## Posisi kita sekarang

Saya akan menetapkan **output resmi Tahap B** sebagai tiga objek:

$$
\boxed{
\mathcal B_t=
\{
\boldsymbol{\mu}_t,
\Sigma_t,
B_t
\}
}
$$

dengan:

$$
\boxed{
\boldsymbol{\mu}_t
=
E[
\mathbf R_{t+\Delta}\mid S_t
]
}
$$

$$
\boxed{
\Sigma_t
=
\operatorname{Cov}
[
\mathbf R_{t+\Delta}\mid S_t
]
}
$$

dan:

$$
\boxed{
B_t
=
\text{exposure aset terhadap market factors}.
}
$$

Untuk **versi implementasi pertama**, saya sangat menyarankan kita **jangan langsung memasukkan HMM, GARCH, neural network, mutual information, dan lain-lain**. Kita bangun dulu B0:

$$
\boxed{
\text{Rolling Factor Regression}
+
\text{EWMA Volatility/Covariance}
}
$$

dan pastikan ia dapat menghasilkan $\mu_t$ dan $\Sigma_t$ yang masuk akal secara *out-of-sample*. Setelah baseline itu kokoh, baru kita tambahkan regime dan model nonlinear satu per satu.

Dan satu hal yang sangat penting: **Tahap B belum boleh "melihat masa depan" ketika melakukan rolling estimation.** Untuk setiap decision time $t$, seluruh parameter $B_t,\mu_{F,t},\Sigma_{F,t},D_t$ harus dibentuk hanya dari data $\mathcal F_t$. Ini akan menjadi aturan keras ketika nanti kita masuk ke implementasi backtester.

Dengan fondasi ini, **Tahap C akan menjadi sangat menarik**, karena kita akan mengambil $\mu_t,\Sigma_t,B_t$ dan secara matematis menurunkan **masalah trading optimization yang sebenarnya**: mulai dari menentukan *universe*, long/short/flat decision, entry, position size, \$1 risk budget, transaction cost, factor exposure constraint, hingga akhirnya membentuk **QUBO lengkap**. Dari sana barulah kita punya alasan matematis yang kuat untuk melakukan mapping:

$$
\boxed{
\text{Trading Problem}
\rightarrow
\text{QUBO}
\rightarrow
\text{Ising Hamiltonian}
\rightarrow
\text{QAOA}.
}
$$

## Prompt:
8/17/2026, 9:44:08 PM

lanjut Tahap C

## Response:
8/17/2026, 9:44:08 PM

Tentu. **Tahap C adalah titik di mana proyek kita mulai benar-benar berubah dari model forecasting menjadi sistem quantitative trading.**

Tahap A memberi kita **state pasar**:

$$
S_t
$$

Tahap B memberi kita **forecast distribusi return**:

$$
\boxed{
\boldsymbol{\mu}_t,\quad \Sigma_t,\quad B_t
}
$$

Sekarang Tahap C harus menjawab:

> **Pada kondisi pasar $S_t$, aset mana yang sebaiknya diperdagangkan, dalam arah apa, dengan ukuran posisi berapa, pada harga entry/SL/TP seperti apa, sehingga expected utility maksimum dengan batas risiko yang telah ditentukan?**

Dan di sinilah **TSP, Max-Cut, portfolio optimization, QUBO, Ising, dan akhirnya QAOA** mulai masuk secara natural.

---

# C. Tujuan Tahap C

Kita ingin mengubah:

$$
\boxed{
(\boldsymbol{\mu}_t,\Sigma_t,B_t)
}
$$

menjadi:

$$
\boxed{
\mathbf x_t^\star
}
$$

dengan $\mathbf x_t^\star$ adalah keputusan trading optimal.

Secara abstrak:

$$
\boxed{
\mathbf x_t^\star
=
\arg\max_{\mathbf x\in\mathcal X}
U(\mathbf x\mid S_t)
}
$$

dengan:

- $\mathbf x$: keputusan trading,
- $\mathcal X$: himpunan keputusan yang diperbolehkan,
- $U$: objective/utility.

---

# C.1. Jangan langsung berpikir "portfolio"

Untuk sistem kita, decision variable sebenarnya lebih kaya.

Untuk setiap aset $i$, kita ingin mengetahui:

$$
\boxed{
x_i
=
\text{posisi trading aset }i
}
$$

Tetapi:

$$
x_i
$$

tidak cukup.

Karena kita perlu membedakan:

$$
\text{LONG}
$$

$$
\text{SHORT}
$$

$$
\text{FLAT}.
$$

Maka secara konseptual:

$$
x_i\in\{-1,0,+1\}.
$$

Yaitu:

$$
-1=\text{short}
$$

$$
0=\text{flat}
$$

$$
+1=\text{long}.
$$

Ini sudah merupakan **discrete optimization problem**.

Dan ini penting karena quantum optimization sangat cocok dengan decision variable diskrit.

---

# C.2. Tetapi position size juga harus diputuskan

Misalkan:

$$
x_i=1.
$$

Itu hanya mengatakan:

> "Trade long."

Belum mengatakan berapa besar posisi.

Kita definisikan:

$$
w_i\ge0
$$

sebagai position size/notional.

Maka:

$$
p_i=x_iw_i.
$$

Jika:

$$
x_i=+1,
$$

maka:

$$
p_i=+w_i.
$$

Jika:

$$
x_i=-1,
$$

maka:

$$
p_i=-w_i.
$$

Jika:

$$
x_i=0,
$$

maka:

$$
p_i=0.
$$

---

# C.3. Namun kita mempunyai constraint yang sangat spesifik

Sebelumnya kamu menentukan:

> setiap trade harus memiliki risiko \$1.

Ini sangat penting.

Misalkan:

$$
P_i
$$

adalah entry price.

Stop loss:

$$
SL_i.
$$

Risk per unit:

$$
d_i
=
|P_i-SL_i|.
$$

Jika posisi berukuran:

$$
q_i
$$

unit, maka dollar risk:

$$
R_i=q_id_i.
$$

Kita ingin:

$$
\boxed{
R_i\le R_{\max}
}
$$

dengan:

$$
R_{\max}=\$1.
$$

Jika ingin tepat \$1:

$$
\boxed{
q_i=
\frac{1}{|P_i-SL_i|}
}
$$

untuk aset dengan satuan harga yang sesuai.

---

# C.4. Ini menghasilkan hubungan penting

Position size bukan dipilih sembarangan.

Ia berasal dari:

$$
\boxed{
\text{Risk Budget}
\div
\text{Stop Distance}
}
$$

atau:

$$
\boxed{
q_i=
\frac{R_{\max}}
{|P_i-SL_i|}
}
$$

Contoh:

Entry:

$$
P_i=100
$$

SL:

$$
SL_i=99.
$$

Maka:

$$
d_i=1.
$$

Jika:

$$
R_{\max}=\$1,
$$

maka:

$$
q_i=1.
$$

Tetapi jika:

$$
SL_i=98,
$$

maka:

$$
d_i=2
$$

dan:

$$
q_i=0.5.
$$

Jadi:

$$
\boxed{
\text{wider SL}\Rightarrow\text{smaller position}.
}
$$

---

# C.5. Mengapa ini berbeda dari portfolio optimization biasa?

Markowitz biasanya berbicara tentang:

$$
w_i
$$

sebagai bobot modal.

Sistem kita lebih dekat ke:

$$
\boxed{
\text{risk-normalized position}.
}
$$

Kita tidak mengatakan:

> "Saya mau mengalokasikan 10% modal."

Kita mengatakan:

> "Jika trade ini gagal dan SL tersentuh, kerugiannya maksimal \$1."

Ini jauh lebih cocok untuk short-term systematic trading.

---

# C.6. Sekarang kita masukkan forecast

Tahap B memberi:

$$
\mu_i
=
E[R_i\mid S_t].
$$

Expected PnL jika posisi $p_i$:

$$
E[P_i]
=
p_i\mu_i.
$$

Untuk seluruh portfolio:

$$
\boxed{
E[P]
=
\mathbf p^T\boldsymbol{\mu}.
}
$$

Jika:

$$
\mathbf p=
[p_1,\ldots,p_N]^T,
$$

maka:

$$
E[P]
=
\sum_i p_i\mu_i.
$$

---

# C.7. Sekarang masuk covariance

Variance portfolio:

$$
\boxed{
\sigma_P^2
=
\mathbf p^T\Sigma\mathbf p.
}
$$

Ekspansi:

$$
\sigma_P^2
=
\sum_i\sum_j
p_ip_j\Sigma_{ij}.
$$

Perhatikan:

$$
\Sigma_{ij}
$$

menciptakan interaksi antara trade $i$ dan $j$.

Ini sangat penting.

Misalnya kita memiliki dua aset:

$$
BTC
$$

dan:

$$
ETH.
$$

Jika:

$$
\rho_{BTC,ETH}\approx1,
$$

membuka long BTC dan long ETH bukan dua independent bets.

Mereka hampir merupakan:

$$
\boxed{\text{one common risk exposure}}
$$

---

# C.8. Maka objective dasar kita

Kita dapat menggunakan mean-variance utility:

$$
\boxed{
U(\mathbf p)
=
\boldsymbol{\mu}^T\mathbf p
-
\lambda
\mathbf p^T\Sigma\mathbf p.
}
$$

Dengan:

$$
\lambda>0
$$

sebagai risk aversion.

Ini mirip Markowitz, tetapi sekarang:

$$
\mathbf p
$$

adalah **trading positions**, bukan sekadar strategic portfolio weights.

---

# C.9. Tetapi kita mempunyai factor exposure

Tahap B juga memberikan:

$$
B.
$$

Portfolio factor exposure:

$$
\boxed{
\mathbf e_F
=
B^T\mathbf p.
}
$$

Misalnya factor:

$$
F=
[
BTC,
ETH,
USD,
GOLD,
SPX
].
$$

Maka:

$$
B^T\mathbf p
$$

memberitahu kita berapa besar portfolio sebenarnya bertaruh terhadap faktor-faktor tersebut.

---

# C.10. Ini sangat penting untuk contoh altcoin

Misalkan kita membuka:

$$
LONG(SOL)
$$

dan:

$$
LONG(AVAX).
$$

Mungkin kita berpikir:

> "Saya punya dua trade."

Tetapi factor model mengatakan:

$$
\beta_{\mathrm{SOL},BTC}=1.3
$$

dan:

$$
\beta_{\mathrm{AVAX},BTC}=1.5.
$$

Maka:

$$
e_{BTC}
=
1.3p_{\mathrm{SOL}}
+
1.5p_{\mathrm{AVAX}}.
$$

Jadi portfolio kita sebenarnya adalah:

$$
\boxed{
\text{large BTC directional bet}
}
$$

meskipun kita tidak membeli BTC.

---

# C.11. Maka kita bisa memberikan constraint

Misalnya:

$$
|e_{BTC}|
\le E_{BTC}^{max}.
$$

Secara matematis:

$$
\boxed{
|
B_{BTC}^T\mathbf p
|
\le
E_{BTC}^{max}.
}
$$

Begitu juga:

$$
|e_{USD}|
\le E_{USD}^{max}.
$$

dan:

$$
|e_{Gold}|
\le E_{Gold}^{max}.
$$

---

# C.12. Ini membuat sistem kita jauh lebih menarik

Karena sekarang optimizer tidak hanya bertanya:

> "Trade mana yang menghasilkan profit terbesar?"

Tetapi:

> "Trade mana yang memberikan profit terbesar **setelah memperhitungkan covariance dan factor exposure**?"

Itu jauh lebih dekat dengan quantitative portfolio construction.

---

# C.13. Sekarang kita masuk ke entry

Forecast $\mu_i$ sebenarnya belum cukup.

Kita perlu menentukan:

$$
P_i^{entry}.
$$

Ada beberapa kemungkinan:

### Market entry

$$
P_i^{entry}=P_{market}.
$$

### Limit entry

$$
P_i^{entry}=P_{market}-\delta_i
$$

untuk long.

Atau:

$$
P_i^{entry}=P_{market}+\delta_i
$$

untuk short.

Jadi entry distance:

$$
\boxed{
\delta_i
}
$$

sendiri menjadi decision variable.

---

# C.14. Sekarang TP dan SL

Untuk long:

$$
SL_i=P_i-\Delta_i^{SL}
$$

dan:

$$
TP_i=P_i+\Delta_i^{TP}.
$$

Untuk short:

$$
SL_i=P_i+\Delta_i^{SL}
$$

dan:

$$
TP_i=P_i-\Delta_i^{TP}.
$$

Maka kita mempunyai dua parameter:

$$
\boxed{
d_i^{SL}
}
$$

dan:

$$
\boxed{
d_i^{TP}.
}
$$

---

# C.15. Risk-reward ratio

Definisikan:

$$
RR_i
=
\frac{d_i^{TP}}
{d_i^{SL}}.
$$

Misalnya:

$$
d^{SL}=1
$$

dan:

$$
d^{TP}=2.
$$

Maka:

$$
RR=2.
$$

---

# C.16. Tetapi RR tinggi tidak otomatis bagus

Misalnya:

$$
RR=3.
$$

Tetapi:

$$
P(TP)=0.20.
$$

Expected value:

$$
EV
=
0.20(3)
-
0.80(1).
$$

Sehingga:

$$
EV=-0.20.
$$

Sebaliknya:

$$
RR=1.5
$$

dengan:

$$
P(TP)=0.60
$$

memberikan:

$$
EV
=
0.60(1.5)-0.40(1)
$$

$$
=0.5.
$$

Jadi optimizer kita harus mempertimbangkan:

$$
\boxed{
P(TP),\quad P(SL),\quad RR.
}
$$

---

# C.17. Expected trade value

Misalkan:

$$
G_i
$$

adalah keuntungan jika TP tercapai.

Dan:

$$
L_i
$$

adalah kerugian jika SL tercapai.

Maka:

$$
\boxed{
EV_i
=
P_i^{TP}G_i
-
P_i^{SL}L_i
-
C_i.
}
$$

Jika kita memaksa:

$$
L_i=\$1,
$$

maka:

$$
\boxed{
EV_i
=
P_i^{TP}G_i
-
P_i^{SL}
-
C_i.
}
$$

Jika hanya ada TP/SL:

$$
P_i^{SL}=1-P_i^{TP},
$$

maka:

$$
\boxed{
EV_i
=
P_i^{TP}G_i
-
(1-P_i^{TP})
-
C_i.
}
$$

---

# C.18. Sekarang kita mempunyai dua level objective

### Level individual trade

$$
EV_i.
$$

### Level portfolio

$$
U(\mathbf p)
=
\boldsymbol{\mu}^T\mathbf p
-
\lambda\mathbf p^T\Sigma\mathbf p.
$$

Kita tidak ingin memilih trade hanya berdasarkan:

$$
EV_i.
$$

Karena dua trade dengan EV tinggi dapat sangat berkorelasi.

Maka objective akhir harus menggabungkan keduanya.

---

# C.19. Salah satu formulasi awal yang sangat bagus

Definisikan expected net return vector:

$$
\tilde{\boldsymbol{\mu}}
=
\begin{bmatrix}
EV_1\\
EV_2\\
\vdots\\
EV_N
\end{bmatrix}.
$$

Kemudian:

$$
\boxed{
U(\mathbf p)
=
\tilde{\boldsymbol{\mu}}^T\mathbf p
-
\lambda\mathbf p^T\Sigma\mathbf p.
}
$$

Ini adalah:

$$
\boxed{
\text{expected trading value}
-
\text{portfolio risk penalty}.
}
$$

---

# C.20. Sekarang masalah kita sudah menjadi optimization problem

$$
\boxed{
\max_{\mathbf p}
\quad
\tilde{\boldsymbol{\mu}}^T\mathbf p
-
\lambda\mathbf p^T\Sigma\mathbf p
}
$$

subject to:

$$
|p_i|\le p_i^{max}
$$

$$
\sum_i |p_i|\le L_{\max}
$$

$$
|B^T\mathbf p|
\le
\mathbf e_{\max}.
$$

Dan:

$$
\text{risk budget}\le R_{\max}.
$$

---

# C.21. Tetapi kita belum mempunyai binary optimization

Karena:

$$
p_i
$$

masih continuous.

Untuk masuk ke QUBO/Ising, kita perlu membuat keputusan diskrit.

Saya ingin membangun ini **secara bertahap**, bukan memaksakan continuous optimization menjadi Ising.

---

# C.22. Kita mulai dengan decision variable binary

Untuk setiap aset:

$$
y_i^L\in\{0,1\}
$$

dan:

$$
y_i^S\in\{0,1\}.
$$

Interpretasi:

$$
y_i^L=1
\Rightarrow
\text{long}
$$

$$
y_i^S=1
\Rightarrow
\text{short}.
$$

Kita harus mencegah:

$$
y_i^L=y_i^S=1.
$$

Constraint:

$$
\boxed{
y_i^L+y_i^S\le1.
}
$$

---

# C.23. Posisi signed

Definisikan:

$$
\boxed{
x_i=y_i^L-y_i^S.
}
$$

Maka:

$$
x_i\in\{-1,0,+1\}.
$$

| $y_i^L$ | $y_i^S$ | $x_i$ |
|---:|---:|---:|
| 0 | 0 | 0 |
| 1 | 0 | +1 |
| 0 | 1 | −1 |
| 1 | 1 | forbidden |

---

# C.24. Ini sudah sangat dekat dengan QUBO

Kita punya:

$$
x_i=y_i^L-y_i^S.
$$

Expected value:

$$
\tilde\mu_i x_i.
$$

Risk:

$$
x^TQx
$$

dengan:

$$
Q\sim\Sigma.
$$

Jadi objective:

$$
\boxed{
U(y)
=
\sum_i
\tilde\mu_i
(y_i^L-y_i^S)
-
\lambda
\sum_{ij}
(y_i^L-y_i^S)
\Sigma_{ij}
(y_j^L-y_j^S).
}
$$

---

# C.25. Constraint long-short

Kita tambahkan penalty:

$$
P_{LS}
\sum_i
y_i^Ly_i^S.
$$

Karena jika:

$$
y_i^L=y_i^S=1,
$$

maka:

$$
y_i^Ly_i^S=1.
$$

Sehingga objective menjadi lebih buruk.

Jadi:

$$
\boxed{
U'
=
U
-
P_{LS}
\sum_i y_i^Ly_i^S.
}
$$

Jika:

$$
P_{LS}\gg
\text{maximum possible benefit},
$$

solusi optimal tidak akan memilih keduanya.

---

# C.26. Constraint jumlah trade

Misalkan maksimum:

$$
K
$$

trade sekaligus.

Kita ingin:

$$
\sum_i
(y_i^L+y_i^S)
\le K.
$$

Untuk QUBO, constraint inequality dapat diubah menggunakan penalty.

Misalnya:

$$
\left(
\sum_i(y_i^L+y_i^S)-K
\right)^2.
$$

Kemudian:

$$
\boxed{
P_K
\left(
\sum_i(y_i^L+y_i^S)-K
\right)^2
}
$$

ditambahkan ke objective sebagai penalty.

---

# C.27. Constraint factor exposure

Misalnya kita ingin:

$$
B_k^Tx
=
0
$$

untuk market-neutral terhadap factor $k$.

Kita tambahkan:

$$
\boxed{
P_F
(B_k^Tx)^2.
}
$$

Karena jika:

$$
B_k^Tx=0,
$$

penalty:

$$
0.
$$

Jika exposure besar:

$$
(B_k^Tx)^2
$$

membesar.

---

# C.28. Misalnya kita ingin membatasi BTC beta

Kita tidak harus selalu memaksa:

$$
B_{BTC}^Tx=0.
$$

Kita bisa memberikan target:

$$
B_{BTC}^Tx=b^\star.
$$

Penalty:

$$
\boxed{
P_{BTC}
(B_{BTC}^Tx-b^\star)^2.
}
$$

Ini jauh lebih fleksibel.

---

# C.29. Sekarang constraint gross exposure

Misalkan:

$$
\sum_i |x_i|\le K.
$$

Untuk binary long-short:

$$
|x_i|
=
y_i^L+y_i^S
$$

jika long dan short tidak boleh simultan.

Maka:

$$
\boxed{
\sum_i(y_i^L+y_i^S)\le K.
}
$$

Sekali lagi dapat dipenalti:

$$
P_K
\left(
\sum_i(y_i^L+y_i^S)-K
\right)^2.
$$

---

# C.30. Sekarang risk budget

Risk portfolio:

$$
R(\mathbf x)
=
\mathbf x^T\Sigma\mathbf x.
$$

Jika kita ingin:

$$
R(\mathbf x)\le R_{\max},
$$

kita bisa menggunakan:

$$
P_R
\left[
\max
\left(
0,
\mathbf x^T\Sigma\mathbf x-R_{\max}
\right)
\right]^2.
$$

Namun fungsi $\max$ tidak langsung QUBO-friendly.

Untuk versi QUBO, kita lebih baik menggunakan:

### quadratic equality dengan slack variables

$$
\mathbf x^T\Sigma\mathbf x+s-R_{\max}=0.
$$

Kemudian:

$$
\boxed{
P_R
(
\mathbf x^T\Sigma\mathbf x+s-R_{\max}
)^2.
}
$$

Tetapi ini dapat meningkatkan jumlah qubit secara signifikan.

---

# C.31. Karena itu saya menyarankan pendekatan berbeda untuk versi pertama

Jangan langsung memasukkan semua constraint.

Kita buat tiga tingkat.

### C0

$$
\boxed{
\text{return}
+
\text{risk}
}
$$

### C1

Tambahkan:

$$
\boxed{
trade-count
}
$$

dan:

$$
\boxed{
long/short exclusivity
}
$$

### C2

Tambahkan:

$$
\boxed{
factor exposure
}
$$

### C3

Tambahkan:

$$
\boxed{
risk budget
}
$$

dan constraint yang lebih kompleks.

Ini akan membuat debugging jauh lebih mudah.

---

# C.32. Hubungan dengan Max-Cut

Sekarang muncul sesuatu yang menarik.

Risk term:

$$
x^T\Sigma x
$$

memiliki pairwise interaction:

$$
\Sigma_{ij}x_ix_j.
$$

Max-Cut juga memiliki objective pairwise:

$$
\sum_{i<j}w_{ij}(1-x_ix_j)
$$

untuk:

$$
x_i\in\{-1,+1\}.
$$

Artinya kedua masalah memiliki struktur:

$$
\boxed{
\text{pairwise interaction graph}.
}
$$

Untuk trading:

$$
\Sigma_{ij}
$$

adalah coupling ekonomi.

Untuk Max-Cut:

$$
w_{ij}
$$

adalah edge weight.

Jadi kita benar-benar sedang mengubah **asset correlation network menjadi optimization graph**.

---

# C.33. Interpretasi graph

Anggap setiap aset:

$$
i
$$

sebagai node.

Edge:

$$
(i,j)
$$

memiliki weight:

$$
w_{ij}\sim\Sigma_{ij}.
$$

Maka:

- positive covariance → posisi searah meningkatkan risk,
- negative covariance → posisi searah dapat mengurangi risk,
- covariance besar → interaction kuat.

Dengan demikian optimizer mencari kombinasi node yang memberikan:

$$
\boxed{
\text{high expected alpha}
+
\text{low interaction risk}.
}
$$

Ini jauh lebih menarik daripada sekadar memilih top-$k$ predicted returns.

---

# C.34. Sekarang TSP juga bisa masuk

TSP tidak cocok sebagai **core asset-selection problem** kita.

Tetapi TSP sangat masuk akal untuk **execution/order sequencing**.

Misalnya sistem ingin melakukan:

$$
N
$$

order.

Ada urutan:

$$
i_1\rightarrow i_2\rightarrow\cdots\rightarrow i_N.
$$

Jika latency/slippage bergantung pada urutan eksekusi, kita dapat membuat:

$$
c_{ij}
$$

sebagai cost berpindah dari order $i$ ke $j$.

Kemudian:

$$
\min
\sum_{ij}c_{ij}x_{ij}.
$$

Ini adalah TSP-like optimization.

Jadi:

$$
\boxed{
\text{Portfolio selection}
\rightarrow
\text{QUBO}
}
$$

sedangkan:

$$
\boxed{
\text{Execution sequencing}
\rightarrow
\text{TSP/QUBO}.
}
$$

Kita tidak perlu memaksakan TSP ke masalah yang sebenarnya bukan TSP.

---

# C.35. Dan Max-Cut?

Max-Cut bisa digunakan untuk:

$$
\boxed{
\text{market-neutral clustering / long-short allocation}.
}
$$

Misalnya kita ingin membagi aset menjadi:

$$
\mathcal L
$$

dan:

$$
\mathcal S.
$$

Dengan objective berdasarkan covariance/correlation graph.

Secara konseptual:

$$
\boxed{
\text{positive correlation}
\rightarrow
\text{prefer opposite sides}
}
$$

jika tujuan kita adalah hedging.

Sedangkan:

$$
\boxed{
\text{negative correlation}
\rightarrow
\text{prefer same side}
}
$$

tergantung definisi objective.

---

# C.36. Jadi kita tidak memiliki "satu quantum algorithm"

Arsitektur kita justru dapat memiliki beberapa optimizer.

### Problem 1 — Asset selection

$$
\boxed{\text{QUBO}}
$$

### Problem 2 — Long/short allocation

$$
\boxed{\text{QUBO / Max-Cut-like}}
$$

### Problem 3 — Position sizing

$$
\boxed{\text{continuous / integer optimization}}
$$

### Problem 4 — Execution sequencing

$$
\boxed{\text{TSP}}
$$

### Problem 5 — Rebalancing

$$
\boxed{\text{dynamic optimization}}
$$

Ini jauh lebih realistis.

---

# C.37. Sekarang kita turunkan bentuk QUBO secara eksplisit

Definisikan vector binary:

$$
\mathbf y=
[
y_1^L,\ldots,y_N^L,
y_1^S,\ldots,y_N^S
]^T.
$$

Kita ingin:

$$
\boxed{
\min_{\mathbf y\in\{0,1\}^{2N}}
\mathbf y^TQ\mathbf y
+
\mathbf c^T\mathbf y
+
c_0.
}
$$

Kenapa minimization?

Karena QUBO biasanya ditulis:

$$
\min.
$$

Sedangkan utility kita:

$$
\max U.
$$

Maka:

$$
\boxed{
\min(-U).
}
$$

---

# C.38. Expected-return term

Utility:

$$
U_{\mu}
=
\sum_i
\tilde\mu_i
(y_i^L-y_i^S).
$$

Maka minimization objective:

$$
-U_\mu
=
-\sum_i\tilde\mu_i y_i^L
+
\sum_i\tilde\mu_i y_i^S.
$$

Jadi linear coefficient:

$$
\boxed{
c_i^L=-\tilde\mu_i
}
$$

dan:

$$
\boxed{
c_i^S=+\tilde\mu_i.
}
$$

Ini masuk akal.

Jika:

$$
\tilde\mu_i>0,
$$

long mendapatkan reward:

$$
-\tilde\mu_i.
$$

Short mendapatkan penalty:

$$
+\tilde\mu_i.
$$

---

# C.39. Risk term

Dengan:

$$
x_i=y_i^L-y_i^S,
$$

maka:

$$
x^T\Sigma x
=
(y^L-y^S)^T
\Sigma
(y^L-y^S).
$$

Expand:

$$
=
(y^L)^T\Sigma y^L
-
(y^L)^T\Sigma y^S
-
(y^S)^T\Sigma y^L
+
(y^S)^T\Sigma y^S.
$$

Karena:

$$
\Sigma=\Sigma^T,
$$

maka:

$$
\boxed{
x^T\Sigma x
=
(y^L)^T\Sigma y^L
-
2(y^L)^T\Sigma y^S
+
(y^S)^T\Sigma y^S.
}
$$

Maka risk term:

$$
\boxed{
\lambda
\left[
(y^L)^T\Sigma y^L
-
2(y^L)^T\Sigma y^S
+
(y^S)^T\Sigma y^S
\right].
}
$$

Ini secara langsung membentuk quadratic matrix $Q$.

---

# C.40. Tambahkan exclusivity

$$
P_{LS}\sum_i y_i^Ly_i^S.
$$

Sehingga:

$$
\boxed{
Q_{L_i,S_i}
\leftarrow
Q_{L_i,S_i}
+
P_{LS}.
}
$$

Dengan konvensi QUBO yang konsisten, faktor 2 pada off-diagonal harus ditangani hati-hati ketika mengimplementasikan $y^TQy$. Ini nanti kita tetapkan sekali dalam kode agar tidak terjadi double-counting.

---

# C.41. Tambahkan maximum number of trades

Constraint:

$$
\sum_i(y_i^L+y_i^S)\le K.
$$

Untuk tahap awal, kita dapat menggunakan:

$$
P_K
\left(
\sum_i(y_i^L+y_i^S)-K
\right)^2.
$$

Expand:

$$
=
P_K
\left[
\left(\sum_i z_i\right)^2
-2K\sum_i z_i
+K^2
\right]
$$

dengan:

$$
z_i=y_i^L+y_i^S.
$$

Karena:

$$
z_i^2
$$

untuk binary variable memiliki sifat:

$$
z_i^2=z_i
$$

hanya jika $z_i$ sendiri binary; karena $z_i$ merupakan jumlah dua binary, kita sebaiknya expand langsung dalam $y_i^L,y_i^S$, bukan memperlakukan $z_i$ sebagai binary.

Ini contoh kecil mengapa **penurunan QUBO harus dilakukan secara hati-hati**, bukan sekadar "lempar constraint ke penalty."

---

# C.42. Dan di sinilah kita mulai mendapatkan Hamiltonian Ising

Setelah QUBO:

$$
\boxed{
E(\mathbf y)
=
\mathbf y^TQ\mathbf y
+
\mathbf c^T\mathbf y
}
$$

kita gunakan transformasi:

$$
\boxed{
y_i=\frac{1-Z_i}{2}
}
$$

dengan:

$$
Z_i\in\{-1,+1\}.
$$

Maka:

$$
y_iy_j
=
\frac{
1-Z_i-Z_j+Z_iZ_j
}{4}.
$$

Substitusi menghasilkan:

$$
H_{\mathrm{Ising}}
=
C
+
\sum_i h_iZ_i
+
\sum_{i<j}J_{ij}Z_iZ_j.
$$

Konstanta $C$ tidak mempengaruhi argmin.

Jadi:

$$
\boxed{
H
=
\sum_i h_iZ_i
+
\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

Dan **inilah Hamiltonian yang nantinya dapat diberikan kepada QAOA**.

---

# C.43. Ini merupakan hubungan paling penting sejauh ini

Kita sekarang mempunyai:

$$
\boxed{
\text{Market Data}
}
$$

$$
\downarrow
$$

$$
\boxed{
S_t
}
$$

$$
\downarrow
$$

$$
\boxed{
\mu_t,\Sigma_t,B_t
}
$$

$$
\downarrow
$$

$$
\boxed{
\text{Trading Optimization}
}
$$

$$
\downarrow
$$

$$
\boxed{
Q
}
$$

$$
\downarrow
$$

$$
\boxed{
H_{\mathrm{Ising}}
}
$$

$$
\downarrow
$$

$$
\boxed{
U_{\mathrm{QAOA}}
}
$$

$$
\downarrow
$$

$$
\boxed{
\text{Long / Short / Flat}
}
$$

---

# C.44. Tetapi ada satu masalah besar yang harus kita selesaikan

Kita tidak boleh membuat QUBO yang:

> secara matematis bagus tetapi secara finansial tidak bisa dieksekusi.

Contohnya optimizer mengatakan:

$$
LONG\ BTC
$$

dengan:

$$
SL=0.01\%
$$

dari entry.

Secara matematis risk \$1 dapat dicapai dengan posisi sangat besar.

Tetapi market impact dan spread dapat membuat strategi itu buruk.

Maka Tahap C harus memiliki:

$$
\boxed{
\text{execution feasibility constraints}.
}
$$

---

# C.45. Kita masukkan transaction cost

Misalkan:

$$
C_i^{fixed}
$$

adalah fixed cost.

Dan:

$$
C_i^{prop}|p_i|
$$

adalah proportional cost.

Maka:

$$
C(\mathbf p)
=
\sum_i
C_i^{fixed}z_i
+
C_i^{prop}|p_i|.
$$

Dalam binary approximation:

$$
|p_i|
\propto
y_i^L+y_i^S.
$$

Sehingga:

$$
\boxed{
C(\mathbf y)
=
\sum_i
c_i^{trade}
(y_i^L+y_i^S).
}
$$

Ini hanya menambah linear term ke QUBO.

---

# C.46. Slippage

Untuk short-term trading, kita juga dapat menggunakan:

$$
C_i^{slippage}
=
\kappa_i|p_i|^\eta.
$$

Misalnya:

$$
\eta\approx1
$$

untuk model sederhana.

Atau:

$$
\eta>1
$$

untuk market impact nonlinear.

Jika position size binary-fixed:

$$
|p_i|=q_i z_i,
$$

maka:

$$
C_i^{slippage}
\approx
\kappa_iq_i^\eta z_i
$$

yang kembali menjadi linear.

Ini sangat menguntungkan untuk QUBO.

---

# C.47. Jadi objective yang lebih realistis

Sekarang:

$$
\boxed{
U=
EV
-
\lambda Risk
-
TransactionCost
-
Slippage
-
ConstraintPenalties.
}
$$

Atau minimization:

$$
\boxed{
E=
-\text{Expected Value}
+
\lambda\text{Risk}
+
\text{Cost}
+
\text{Penalty}.
}
$$

Ini adalah bentuk yang akan kita gunakan.

---

# C.48. C0 — formulasi pertama yang saya sarankan

Untuk menghindari sistem terlalu kompleks, kita mulai dari:

$$
\boxed{
\min_{\mathbf y}
\quad
-\tilde{\boldsymbol\mu}^T\mathbf x
+
\lambda\mathbf x^T\Sigma\mathbf x
+
C(\mathbf y)
}
$$

subject to:

$$
x_i=y_i^L-y_i^S
$$

dan:

$$
y_i^L+y_i^S\le1.
$$

Kemudian:

$$
\sum_i(y_i^L+y_i^S)\le K.
$$

---

# C.49. Apa yang belum masuk?

Belum:

- dynamic stop loss,
- trailing stop,
- TP adjustment,
- order-book placement,
- execution timing,
- portfolio turnover,
- regime transition,
- liquidity constraints,
- maximum drawdown,
- daily loss limit.

**Dan itu memang sengaja.**

Karena semua itu sebaiknya datang setelah kita mempunyai core optimizer yang benar.

---

# C.50. Struktur Tahap C lengkap

Saya akan membaginya menjadi:

### C1 — Trade candidate generation

Dari:

$$
\mu_i,\sigma_i,EV_i
$$

tentukan candidate trade.

---

### C2 — Discrete position selection

$$
x_i\in\{-1,0,+1\}.
$$

---

### C3 — Position sizing

$$
q_i=
\frac{R_{\max}}
{|P_i-SL_i|}.
$$

---

### C4 — Portfolio optimization

$$
\max
\mu^Tx-\lambda x^T\Sigma x.
$$

---

### C5 — Factor constraints

$$
|B^Tx|\le E_{\max}.
$$

---

### C6 — Execution cost

$$
C(x).
$$

---

### C7 — QUBO

$$
\boxed{
\min_x x^TQx+c^Tx.
}
$$

---

### C8 — Ising

$$
\boxed{
H=
\sum_i h_iZ_i+
\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

---

# C.51. Dan satu hal yang sangat penting untuk skripsimu

Ada hubungan langsung dengan apa yang sudah kamu kerjakan sebelumnya.

Kamu sebelumnya telah mempelajari:

$$
\boxed{\text{Markowitz}}
$$

$$
\boxed{\text{QUBO}}
$$

$$
\boxed{\text{Ising}}
$$

$$
\boxed{\text{VQE}}
$$

$$
\boxed{\text{QAOA}}
$$

dan:

$$
\boxed{\text{EPG warm-start}}.
$$

Sekarang semuanya dapat ditempatkan pada satu arsitektur yang jauh lebih besar:

$$
\boxed{
\text{Quantitative Trading}
}
$$

↓

$$
\boxed{
\text{Conditional Factor Model}
}
$$

↓

$$
\boxed{
\text{Dynamic Portfolio Optimization}
}
$$

↓

$$
\boxed{
\text{QUBO}
}
$$

↓

$$
\boxed{
\text{Ising}
}
$$

↓

$$
\boxed{
\text{QAOA}
}
$$

dan kalau kita ingin menggunakan penelitianmu sebelumnya:

$$
\boxed{
\text{EPG Nash Equilibrium}
\rightarrow
\text{QAOA Initial State / Warm Start}.
}
$$

Jadi penelitian quantum portfolio optimization yang kamu kerjakan bukan sesuatu yang terpisah. Ia dapat menjadi **salah satu optimizer di dalam trading architecture yang lebih besar**.

---

# C.52. Namun saya ingin kita membuat satu keputusan desain yang penting

**Jangan membuat QAOA memutuskan semuanya.**

Untuk sistem yang realistis, saya menyarankan:

$$
\boxed{
\text{Classical model}
\rightarrow
\text{candidate generation}
}
$$

$$
\boxed{
\text{Quantum optimizer}
\rightarrow
\text{discrete combinatorial selection}
}
$$

$$
\boxed{
\text{Classical risk engine}
\rightarrow
\text{position sizing}
}
$$

$$
\boxed{
\text{Execution engine}
\rightarrow
\text{order placement}
}
$$

Karena quantum optimization paling masuk akal ketika masalahnya memang **combinatorial**, bukan ketika kita memaksa seluruh sistem menjadi quantum.

---

# C.53. Bentuk akhir Tahap C

Dengan demikian, pada waktu $t$:

### Input

$$
\boxed{
\mathcal B_t=
(\mu_t,\Sigma_t,B_t)
}
$$

plus:

$$
\boxed{
\mathcal M_t=
(\text{price, spread, liquidity, fees})
}
$$

### Candidate generation

$$
\boxed{
\mathcal A_t
=
\{i:
EV_i>EV_{\min}\}
}
$$

### Decision

$$
\boxed{
y_i^L,y_i^S\in\{0,1\}
}
$$

### Objective

$$
\boxed{
E(\mathbf y)
=
-\tilde\mu^T\mathbf x
+
\lambda\mathbf x^T\Sigma\mathbf x
+
C(\mathbf y)
+
P(\mathbf y)
}
$$

### QUBO

$$
\boxed{
E(\mathbf y)
=
\mathbf y^TQ\mathbf y+
\mathbf c^T\mathbf y+C
}
$$

### Ising

$$
\boxed{
H
=
\sum_i h_iZ_i
+
\sum_{i<j}J_{ij}Z_iZ_j
}
$$

### Solver

$$
\boxed{
\text{QAOA / classical exact solver / classical heuristic}
}
$$

### Output

$$
\boxed{
\mathbf y^\star
\rightarrow
\{
LONG,SHORT,FLAT
\}
}
$$

---

## Dan menurutku inilah bagian yang paling penting

Kita sekarang telah berhasil membangun **rantai matematis yang utuh**:

$$
\boxed{
\underbrace{S_t}_{\text{market state}}
\rightarrow
\underbrace{(\mu_t,\Sigma_t,B_t)}_{\text{conditional forecast}}
\rightarrow
\underbrace{U(x)}_{\text{trading utility}}
\rightarrow
\underbrace{Q}_{\text{QUBO}}
\rightarrow
\underbrace{H}_{\text{Ising}}
\rightarrow
\underbrace{\text{QAOA}}_{\text{combinatorial optimizer}}
}
$$

dan yang paling menarik, **$\Sigma_t$ dari Tahap B menjadi sumber coupling $J_{ij}$**. Jadi korelasi antar-aset bukan hanya statistik deskriptif; ia secara langsung menentukan interaksi antar-qubit dalam Hamiltonian trading.

Sementara itu, **TSP tidak perlu dipaksakan ke asset selection**. Ia lebih natural ditempatkan nanti pada *execution sequencing*. **Max-Cut** dapat muncul pada long/short partition atau hedging, dan **portfolio optimization** menjadi parent problem yang menghasilkan QUBO kita.

Dengan demikian kita tidak sedang membuat "bot trading yang kebetulan memakai QAOA". Kita sedang membangun:

$$
\boxed{
\textbf{dynamic stochastic combinatorial optimization framework for systematic trading}
}
$$

yang kebetulan memiliki **quantum optimization layer**.

Dan setelah Tahap C ini, **Tahap D seharusnya bukan langsung coding QAOA**. Tahap D yang paling logis adalah **menurunkan QUBO trading kita secara lengkap dengan contoh numerik kecil**—misalnya 4 aset, masing-masing LONG/SHORT/FLAT, risk \$1, TP/SL, transaction cost, covariance, dan factor exposure—sampai kita benar-benar mendapatkan matriks $Q$, lalu mengubahnya menjadi $h_i$ dan $J_{ij}$. Setelah itu baru kita bisa melihat dengan jelas **apa sebenarnya yang sedang dioptimalkan oleh QAOA** dan berapa qubit yang diperlukan.

## Prompt:
8/17/2026, 9:44:47 PM

lanjut Tahap D

## Response:
8/17/2026, 9:44:52 PM

> **Constructing example**
>
> I’m setting up a small four-asset, two-sided portfolio example with binary long/short variables. I’ll derive covariance, returns, turnover costs, constraints, and the resulting numeric QUBO matrix.
>
> **Constructed an example**
>
> 
>
> **Computing a Four-Asset QUBO Portfolio Example**
>
>
> ****
>
> 
>
> **Computed and corrected a four-asset QUBO portfolio optimization example**
>
> 
>
> Worked for 41s

Baik. **Tahap D akan kita jadikan tahap konstruksi matematis konkret**. Di sini kita berhenti berbicara pada level arsitektur dan benar-benar mengambil sebuah kasus kecil, lalu menurunkannya:

$$
\boxed{
\text{data}
\rightarrow
\text{trade candidates}
\rightarrow
\text{objective}
\rightarrow
\text{QUBO}
\rightarrow
\text{Ising}
\rightarrow
\text{QAOA}
}
$$

Saya akan menggunakan **4 aset** agar seluruh matriks masih bisa kita lihat secara eksplisit.

> **Catatan penting:** angka di bawah adalah angka sintetis untuk demonstrasi matematis, bukan estimasi pasar aktual. Nanti ketika masuk implementasi, seluruh angka ini akan berasal dari data historis.

---

# D.1. Kasus konkret

Misalkan pada waktu $t$, sistem sedang mengevaluasi empat kandidat:

$$
\mathcal A=
\{
BTC,ETH,AAPL,GLD
\}.
$$

Kita ingin memilih **tepat 2 trade**.

Setiap aset memiliki tiga kemungkinan:

$$
\boxed{
LONG,\quad SHORT,\quad FLAT.
}
$$

Dan setiap trade yang dipilih memiliki risk budget:

$$
\boxed{R_{\max}=\$1.}
$$

---

# D.2. Tahap pertama: menentukan stop loss dan position size

Misalkan sinyal menghasilkan:

| Asset | Entry | SL distance |
|---|---:|---:|
| BTC | \$60,000 | 1.00% |
| ETH | \$3,000 | 1.20% |
| AAPL | \$200 | 1.00% |
| GLD | \$250 | 0.80% |

Untuk setiap trade:

$$
q_i=
\frac{R_{\max}}
{|P_i-SL_i|}.
$$

### BTC

Stop distance:

$$
60000(0.01)=600.
$$

Sehingga:

$$
q_{BTC}
=
\frac{1}{600}
=
0.001667\ BTC.
$$

---

### ETH

$$
d_{ETH}
=
3000(0.012)=36.
$$

Sehingga:

$$
q_{ETH}
=
\frac{1}{36}
=
0.02778\ ETH.
$$

---

### AAPL

$$
d_{AAPL}=200(0.01)=2.
$$

Sehingga:

$$
q_{AAPL}=0.5\text{ saham}.
$$

---

### GLD

$$
d_{GLD}=250(0.008)=2.
$$

Sehingga:

$$
q_{GLD}=0.5.
$$

Jadi **setiap trade yang dipilih mempunyai nominal posisi berbeda**, tetapi jika SL tersentuh:

$$
\boxed{\text{loss}\approx \$1.}
$$

Ini penting karena optimizer nantinya tidak boleh membandingkan BTC dan AAPL hanya berdasarkan nominal harga.

---

# D.3. Expected trade value

Dari Tahap B, model forecasting kita menghasilkan expected net PnL untuk satu trade yang sudah dinormalisasi terhadap risk \$1.

Misalkan:

$$
\tilde{\boldsymbol\mu}
=
\begin{bmatrix}
0.18\\
0.15\\
0.10\\
0.08
\end{bmatrix}.
$$

Artinya:

| Asset | Expected net PnL |
|---|---:|
| BTC | \$0.18 |
| ETH | \$0.15 |
| AAPL | \$0.10 |
| GLD | \$0.08 |

Ini bukan berarti model berkata:

> BTC pasti menghasilkan \$0.18.

Melainkan:

$$
E[\text{PnL}_i\mid S_t]=\$0.18.
$$

---

# D.4. Covariance antar-trade

Sekarang bagian yang sangat penting.

Misalkan covariance matrix dari **risk-normalized PnL** adalah:

$$
\Sigma=
\begin{pmatrix}
0.6400&0.5400&0.0900&-0.0240\\
0.5400&0.8100&0.0810&-0.0135\\
0.0900&0.0810&0.2025&-0.02025\\
-0.0240&-0.0135&-0.02025&0.0900
\end{pmatrix}.
$$

Urutan:

$$
(BTC,ETH,AAPL,GLD).
$$

Perhatikan:

$$
\Sigma_{BTC,ETH}=0.54.
$$

Sangat positif.

Sedangkan:

$$
\Sigma_{AAPL,GLD}=-0.02025.
$$

Negatif.

Ini akan menghasilkan konsekuensi yang menarik.

---

# D.5. Mengapa covariance menjadi penting?

Bandingkan dua portfolio:

### Portfolio A

$$
LONG\ BTC
$$

dan:

$$
LONG\ ETH.
$$

Expected value:

$$
0.18+0.15=0.33.
$$

Tetapi variance:

$$
\sigma^2
=
\Sigma_{BTC,BTC}
+
\Sigma_{ETH,ETH}
+
2\Sigma_{BTC,ETH}.
$$

Sehingga:

$$
=
0.64+0.81+2(0.54)
$$

$$
=
2.53.
$$

---

### Portfolio B

$$
LONG\ AAPL
$$

dan:

$$
LONG\ GLD.
$$

Expected value:

$$
0.10+0.08=0.18.
$$

Variance:

$$
=
0.2025+0.09
+
2(-0.02025)
$$

$$
=
0.252.
$$

Jadi:

$$
\boxed{
BTC+ETH:
\quad
EV=0.33,\quad
Var=2.53
}
$$

sedangkan:

$$
\boxed{
AAPL+GLD:
\quad
EV=0.18,\quad
Var=0.252.
}
$$

Ini tepat alasan kita tidak boleh melakukan:

$$
\text{sort predicted return}
$$

lalu mengambil dua teratas.

---

# D.6. Risk aversion

Misalkan:

$$
\lambda=0.1.
$$

Objective dasar:

$$
U(x)
=
\boldsymbol{\mu}^Tx
-
\lambda x^T\Sigma x.
$$

Untuk BTC+ETH:

$$
U
=
0.33-0.1(2.53)
$$

$$
=
0.077.
$$

Untuk AAPL+GLD:

$$
U
=
0.18-0.1(0.252)
$$

$$
=
0.1548.
$$

Maka:

$$
\boxed{
AAPL+GLD
>
BTC+ETH.
}
$$

Walaupun:

$$
EV_{BTC+ETH}>EV_{AAPL+GLD}.
$$

Ini adalah perilaku yang kita inginkan dari optimizer.

---

# D.7. Sekarang masukkan factor exposure

Sekarang kita ingin sistem tidak hanya melihat covariance.

Misalkan ada faktor:

$$
F_{DXY}.
$$

Beta ilustratif:

$$
\boldsymbol{\beta}_{DXY}
=
\begin{bmatrix}
-0.8\\
-0.6\\
-0.3\\
+0.2
\end{bmatrix}.
$$

Artinya secara ilustratif:

- BTC sensitif negatif terhadap DXY,
- ETH negatif,
- AAPL negatif,
- GLD sedikit positif.

Exposure portfolio:

$$
E_{DXY}
=
\boldsymbol{\beta}_{DXY}^Tx.
$$

Kita ingin menghindari exposure DXY terlalu besar.

Untuk demonstrasi pertama kita targetkan:

$$
E_{DXY}^{target}=0.
$$

Penalty:

$$
P_F
(E_{DXY})^2.
$$

Misalkan:

$$
P_F=0.5.
$$

---

# D.8. Contoh factor exposure

Untuk:

$$
LONG\ BTC+LONG\ ETH,
$$

kita mendapatkan:

$$
E_{DXY}
=
-0.8-0.6
=
-1.4.
$$

Penalty:

$$
0.5(-1.4)^2
=
0.98.
$$

Cukup besar.

Sedangkan AAPL+GLD:

$$
E_{DXY}
=
-0.3+0.2
=
-0.1.
$$

Penalty:

$$
0.5(-0.1)^2
=
0.005.
$$

Jadi optimizer semakin menyukai AAPL+GLD.

---

# D.9. Transaction cost

Misalkan biaya efektif:

$$
c=
\begin{bmatrix}
0.02\\
0.02\\
0.01\\
0.01
\end{bmatrix}.
$$

Jadi:

- BTC: \$0.02,
- ETH: \$0.02,
- AAPL: \$0.01,
- GLD: \$0.01.

Biaya ini bisa berasal dari:

$$
\text{spread}
+
\text{commission}
+
\text{estimated slippage}.
$$

---

# D.10. Sekarang kita buat decision variables

Untuk setiap aset kita membutuhkan dua binary variable:

$$
y_i^L
$$

dan:

$$
y_i^S.
$$

Maka:

$$
y_{BTC}^L,\quad y_{BTC}^S
$$

$$
y_{ETH}^L,\quad y_{ETH}^S
$$

$$
y_{AAPL}^L,\quad y_{AAPL}^S
$$

$$
y_{GLD}^L,\quad y_{GLD}^S.
$$

Total:

$$
\boxed{8\text{ binary variables}.}
$$

---

# D.11. Kita susun vector

$$
\mathbf y=
\begin{bmatrix}
y_{BTC}^L\\
y_{ETH}^L\\
y_{AAPL}^L\\
y_{GLD}^L\\
y_{BTC}^S\\
y_{ETH}^S\\
y_{AAPL}^S\\
y_{GLD}^S
\end{bmatrix}.
$$

Kemudian signed position:

$$
x_i=y_i^L-y_i^S.
$$

Sehingga:

$$
\mathbf x
=
\begin{bmatrix}
x_{BTC}\\
x_{ETH}\\
x_{AAPL}\\
x_{GLD}
\end{bmatrix}.
$$

---

# D.12. Constraint pertama: tidak boleh long dan short bersamaan

Kita ingin:

$$
y_i^L+y_i^S\le1.
$$

Daripada constraint inequality, untuk QUBO kita gunakan penalty:

$$
\boxed{
P_{LS}
\sum_i y_i^Ly_i^S.
}
$$

Misalkan:

$$
P_{LS}=5.
$$

Jika:

$$
y_i^L=y_i^S=1,
$$

maka kita mendapatkan penalty:

$$
5.
$$

Karena benefit trade normal jauh lebih kecil, solusi optimal akan menghindarinya.

---

# D.13. Constraint kedua: tepat dua posisi

Untuk contoh ini kita pakai:

$$
K=2.
$$

Kita inginkan:

$$
\sum_i(y_i^L+y_i^S)=2.
$$

Gunakan:

$$
\boxed{
P_K
\left[
\sum_i(y_i^L+y_i^S)-2
\right]^2.
}
$$

Misalkan:

$$
P_K=3.
$$

Perhatikan bahwa ini **memaksa tepat 2 trade**, bukan "maksimal 2 trade".

Untuk implementasi produksi nanti, kita bisa mengubahnya menjadi inequality dengan slack variable.

---

# D.14. Objective lengkap

Sekarang:

$$
\boxed{
E(\mathbf y)
=
-\tilde{\boldsymbol\mu}^T\mathbf x
+
\lambda\mathbf x^T\Sigma\mathbf x
+
C(\mathbf y)
+
P_F(\beta^T\mathbf x)^2
+
P_{LS}\sum_i y_i^Ly_i^S
+
P_K
\left(
\sum_i(y_i^L+y_i^S)-2
\right)^2.
}
$$

Inilah **objective utama Tahap D**.

---

# D.15. Mengapa expected return diberi tanda minus?

Karena QUBO biasanya kita tulis sebagai:

$$
\min E.
$$

Sedangkan kita sebenarnya ingin:

$$
\max U.
$$

Karena:

$$
\max U
\iff
\min(-U).
$$

Jadi:

$$
-\tilde{\mu}^Tx
$$

adalah reward yang diubah menjadi cost.

---

# D.16. Kita sekarang ekspansi bagian return

Karena:

$$
x_i=y_i^L-y_i^S,
$$

maka:

$$
-\tilde{\mu}^Tx
=
-\sum_i\tilde{\mu}_iy_i^L
+
\sum_i\tilde{\mu}_iy_i^S.
$$

Tambahkan transaction cost:

$$
c_i(y_i^L+y_i^S).
$$

Maka linear coefficient awal:

### Long

$$
c_i^L=-\tilde{\mu}_i+c_i
$$

### Short

$$
c_i^S=+\tilde{\mu}_i+c_i.
$$

Sehingga:

| Asset | Long coefficient | Short coefficient |
|---|---:|---:|
| BTC | $-0.16$ | $0.20$ |
| ETH | $-0.13$ | $0.17$ |
| AAPL | $-0.09$ | $0.11$ |
| GLD | $-0.07$ | $0.09$ |

Sebelum penalty.

Ini sudah sangat intuitif.

Untuk BTC:

$$
-0.16
$$

membuat LONG menarik.

Sedangkan:

$$
+0.20
$$

membuat SHORT tidak menarik.

---

# D.17. Risk term

Kita memiliki:

$$
x^T\Sigma x.
$$

Dengan:

$$
x=y^L-y^S.
$$

Maka:

$$
x^T\Sigma x
=
(y^L-y^S)^T
\Sigma
(y^L-y^S).
$$

Expand:

$$
=
(y^L)^T\Sigma y^L
-
2(y^L)^T\Sigma y^S
+
(y^S)^T\Sigma y^S.
$$

Ini adalah bagian yang menghasilkan **coupling antar-qubit**.

---

# D.18. Contoh coupling BTC–ETH

Dari:

$$
\Sigma_{BTC,ETH}=0.54.
$$

Untuk dua LONG:

$$
\lambda(2)(0.54)y_{BTC}^Ly_{ETH}^L.
$$

Dengan:

$$
\lambda=0.1,
$$

maka:

$$
0.108
y_{BTC}^Ly_{ETH}^L.
$$

Artinya memilih BTC dan ETH secara bersamaan menghasilkan additional risk cost.

Inilah analogi langsung:

$$
\boxed{
\text{financial correlation}
\longleftrightarrow
\text{qubit coupling}.
}
$$

---

# D.19. Contoh AAPL–GLD

$$
\Sigma_{AAPL,GLD}
=
-0.02025.
$$

Maka coupling:

$$
2\lambda\Sigma_{AAPL,GLD}
=
2(0.1)(-0.02025)
$$

$$
=
-0.00405.
$$

Jadi:

$$
-0.00405
y_{AAPL}^Ly_{GLD}^L.
$$

**Negative coupling berarti memilih keduanya bersama-sama justru mengurangi risk term.**

Ini adalah salah satu alasan kombinasi AAPL+GLD menjadi menarik.

---

# D.20. Factor penalty juga menghasilkan coupling

Kita mempunyai:

$$
P_F(\beta^Tx)^2.
$$

Expand:

$$
P_F
\sum_i\sum_j
\beta_i\beta_jx_ix_j.
$$

Jadi jika dua aset mempunyai beta factor yang sama arahnya, mereka memperoleh positive coupling.

Dengan kata lain:

$$
\boxed{
\text{factor exposure}
\rightarrow
\text{additional graph coupling}.
}
$$

---

# D.21. Sekarang kita dapat membentuk QUBO

Secara umum:

$$
\boxed{
E(\mathbf y)
=
\mathbf y^TQ\mathbf y
+
\mathbf c^T\mathbf y
+
C.
}
$$

Untuk contoh kita, dengan urutan 8 variable tadi, matrix $Q$ yang dihasilkan adalah:

$$
Q\approx
\begin{pmatrix}
3.384&3.294&3.129&2.918&5.116&2.706&2.871&3.082\\
3.294&3.261&3.098&2.939&2.706&5.239&2.902&3.061\\
3.129&3.098&3.065&2.968&2.871&2.902&5.435&3.032\\
2.918&2.939&2.968&3.029&3.082&3.061&3.032&5.471\\
5.116&2.706&2.871&3.082&3.384&3.294&3.129&2.918\\
2.706&5.239&2.902&3.061&3.294&3.261&3.098&2.939\\
2.871&2.902&5.435&3.032&3.129&3.098&3.065&2.968\\
3.082&3.061&3.032&5.471&2.918&2.939&2.968&3.029
\end{pmatrix}.
$$

dan:

$$
\mathbf c=
\begin{bmatrix}
-12.16\\
-12.13\\
-12.09\\
-12.07\\
-11.80\\
-11.83\\
-11.89\\
-11.91
\end{bmatrix}.
$$

Konstanta:

$$
C=12.
$$

---

# D.22. Kenapa coefficient-nya terlihat besar?

Ini pertanyaan yang mungkin langsung muncul.

Karena:

$$
P_K=3
$$

dan:

$$
P_{LS}=5
$$

menghasilkan coefficient penalty yang jauh lebih besar daripada expected return.

Itu **memang disengaja**.

Penalty harus cukup besar sehingga optimizer lebih memilih:

> solusi feasible dengan utility sedikit lebih rendah

daripada:

> solusi infeasible dengan utility tinggi.

Namun dalam sistem produksi, penalty tidak boleh dipilih asal besar. Kita akan membuat metode sistematis untuk menentukan lower bound penalty berdasarkan upper bound objective benefit.

---

# D.23. Mari kita lihat solusi optimal

Kita dapat melakukan brute-force karena hanya ada:

$$
2^8=256
$$

state.

Untuk contoh ini, ground-state solution adalah:

$$
\boxed{
y_{AAPL}^L=1
}
$$

dan:

$$
\boxed{
y_{GLD}^L=1.
}
$$

Semua lainnya:

$$
0.
$$

Jadi:

$$
\mathbf y^\star
=
[0,0,1,1,0,0,0,0]^T.
$$

Dan:

$$
\boxed{
\mathbf x^\star
=
[0,0,+1,+1]^T.
}
$$

Artinya:

$$
\boxed{
LONG\ AAPL
}
$$

$$
\boxed{
LONG\ GLD
}
$$

dan:

$$
BTC=FLAT
$$

$$
ETH=FLAT.
$$

---

# D.24. Mari kita verifikasi objective secara manual

Expected value:

$$
EV
=
0.10+0.08
=
0.18.
$$

Risk:

$$
x^T\Sigma x
=
0.252.
$$

Risk penalty:

$$
\lambda Risk
=
0.1(0.252)
=
0.0252.
$$

Transaction cost:

$$
0.01+0.01=0.02.
$$

DXY exposure:

$$
-0.3+0.2=-0.1.
$$

Factor penalty:

$$
0.5(-0.1)^2
=
0.005.
$$

Exclusivity penalty:

$$
0.
$$

Count penalty:

$$
0.
$$

Maka:

$$
E^\star
=
-0.18
+
0.0252
+
0.02
+
0.005.
$$

Sehingga:

$$
\boxed{
E^\star=-0.1298.
}
$$

Karena kita melakukan minimization, semakin negatif semakin baik.

---

# D.25. Bandingkan dengan BTC + ETH

Untuk:

$$
x=[1,1,0,0].
$$

Expected:

$$
0.33.
$$

Risk:

$$
2.53.
$$

DXY exposure:

$$
-1.4.
$$

Maka:

$$
E
=
-0.33
+
0.1(2.53)
+
0.04
+
0.5(1.4)^2.
$$

$$
=
-0.33+0.253+0.04+0.98.
$$

$$
\boxed{
E=0.943.
}
$$

Jauh lebih buruk.

---

# D.26. Ini memberikan insight yang sangat penting

Kalau kita hanya memakai expected return:

$$
BTC+ETH
$$

akan menang.

Tetapi ketika kita mempertimbangkan:

$$
\boxed{
\text{return}
+
risk
+
factor exposure
+
transaction cost,
}
$$

hasilnya:

$$
\boxed{
AAPL+GLD.
}
$$

Inilah alasan optimizer combinatorial kita diperlukan.

---

# D.27. Sekarang kita ubah QUBO menjadi Ising

Kita gunakan:

$$
\boxed{
y_i=\frac{1-Z_i}{2}.
}
$$

Dengan:

$$
Z_i\in\{-1,+1\}.
$$

Interpretasi:

$$
Z_i=-1
\Rightarrow
y_i=1
$$

dan:

$$
Z_i=+1
\Rightarrow
y_i=0.
$$

---

# D.28. Transformasi pasangan

Untuk:

$$
y_iy_j
$$

kita memperoleh:

$$
\boxed{
y_iy_j
=
\frac14
(1-Z_i-Z_j+Z_iZ_j).
}
$$

Inilah formula yang mengubah QUBO menjadi Ising.

---

# D.29. Bentuk Ising

Secara umum:

$$
H
=
C'
+
\sum_i a_iZ_i
+
\sum_{i<j}b_{ij}Z_iZ_j.
$$

Konstanta:

$$
C'
$$

boleh dibuang karena tidak mempengaruhi state minimum.

Sehingga:

$$
\boxed{
H
=
\sum_i a_iZ_i
+
\sum_{i<j}b_{ij}Z_iZ_j.
}
$$

---

# D.30. Hubungan QUBO → Ising

Jika:

$$
E(y)=y^TQy+c^Ty+C,
$$

maka dengan konvensi $y_i^2=y_i$, define:

$$
b_i=c_i+Q_{ii}.
$$

Kemudian:

$$
\boxed{
a_i
=
-\frac12b_i
-\frac12\sum_{j\neq i}Q_{ij}
}
$$

dan:

$$
\boxed{
b_{ij}
=
\frac12Q_{ij}.
}
$$

---

# D.31. Hasil Ising untuk contoh kita

Coefficient linear $a_i$:

$$
\begin{aligned}
a_1&=-7.170\\
a_2&=-7.185\\
a_3&=-7.205\\
a_4&=-7.215\\
a_5&=-7.350\\
a_6&=-7.335\\
a_7&=-7.305\\
a_8&=-7.295.
\end{aligned}
$$

Dan pairwise coupling:

$$
b_{ij}=\frac{Q_{ij}}2.
$$

Misalnya:

$$
b_{12}=1.647
$$

karena:

$$
Q_{12}=3.294.
$$

Sedangkan:

$$
b_{13}=1.5645.
$$

---

# D.32. Hati-hati dengan konvensi Hamiltonian

Dalam banyak literatur Ising/QAOA kita menggunakan:

$$
H=
\sum_i h_iZ_i+
\sum_{i<j}J_{ij}Z_iZ_j.
$$

Tetapi dalam formulasi yang pernah kita gunakan untuk skripsimu:

$$
\boxed{
H=
-\sum_i h_iZ_i
-
\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

Jadi:

$$
\boxed{
h_i=-a_i
}
$$

dan:

$$
\boxed{
J_{ij}=-b_{ij}.
}
$$

Dengan demikian:

$$
h_i>0
$$

dan banyak $J_{ij}$ menjadi negatif untuk contoh kita.

Ini **bukan perbedaan fisika**, hanya perbedaan konvensi tanda.

Kita harus menetapkan satu konvensi secara konsisten di implementasi.

---

# D.33. Bentuk Hamiltonian akhir

Menggunakan konvensi skripsimu:

$$
\boxed{
H_C
=
-\sum_i h_iZ_i
-
\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

Inilah:

$$
\boxed{\textbf{Cost Hamiltonian}.}
$$

Dan sekarang kita sudah benar-benar mempunyai Hamiltonian yang berasal dari masalah trading.

Bukan Hamiltonian yang dibuat sembarang.

---

# D.34. Interpretasi fisiknya

Ini bagian yang menurutku sangat menarik untuk penelitianmu.

Dalam sistem ini:

$$
\boxed{
h_i
}
$$

merepresentasikan **local preference** terhadap keputusan tertentu.

Sedangkan:

$$
\boxed{
J_{ij}
}
$$

merepresentasikan **interaction** antara dua keputusan.

Interaction tersebut dapat berasal dari:

$$
\text{covariance}
$$

$$
+
$$

$$
\text{factor exposure}
$$

$$
+
$$

$$
\text{constraints}.
$$

Jadi:

$$
\boxed{
\text{financial dependency}
\rightarrow
\text{Ising coupling}.
}
$$

---

# D.35. Ini persis alasan Ising sangat cocok

Bayangkan graph:

$$
BTC
\longleftrightarrow
ETH
$$

memiliki coupling kuat karena:

$$
\rho_{BTC,ETH}\gg0.
$$

Sedangkan:

$$
AAPL
\longleftrightarrow
GLD
$$

memiliki coupling negatif karena covariance negatif.

Maka sistem kita secara matematis berubah menjadi:

$$
\boxed{
\text{financial interaction graph}
\rightarrow
\text{spin interaction graph}.
}
$$

---

# D.36. Sekarang kita sampai ke QAOA

Setelah mendapatkan:

$$
H_C,
$$

kita membutuhkan state yang mencari:

$$
\boxed{
\arg\min H_C.
}
$$

QAOA menggunakan dua Hamiltonian.

---

## Cost Hamiltonian

$$
\boxed{
H_C
}
$$

yang baru saja kita turunkan.

---

## Mixer Hamiltonian

Untuk standard QAOA:

$$
\boxed{
H_M
=
\sum_iX_i.
}
$$

Atau sering ditulis:

$$
H_M
=
-\sum_iX_i.
$$

Tanda tidak terlalu penting selama konvensinya konsisten dengan unitary.

---

# D.37. State awal

Standard QAOA:

$$
|s\rangle
=
|+\rangle^{\otimes n}
$$

dengan:

$$
|+\rangle
=
\frac{|0\rangle+|1\rangle}{\sqrt2}.
$$

Untuk:

$$
n=8,
$$

kita memiliki:

$$
|s\rangle
=
|+\rangle^{\otimes8}.
$$

---

# D.38. Operator QAOA

Cost unitary:

$$
\boxed{
U_C(\gamma)
=
e^{-i\gamma H_C}.
}
$$

Mixer:

$$
\boxed{
U_M(\beta)
=
e^{-i\beta H_M}.
}
$$

Untuk $p=1$:

$$
\boxed{
|\psi(\gamma,\beta)\rangle
=
U_M(\beta)
U_C(\gamma)
|+\rangle^{\otimes8}.
}
$$

Untuk $p$ layer:

$$
\boxed{
|\psi_p\rangle
=
\prod_{k=1}^{p}
U_M(\beta_k)
U_C(\gamma_k)
|+\rangle^{\otimes8}.
}
$$

---

# D.39. Classical optimizer kemudian mencari

$$
\boxed{
(\boldsymbol\gamma^\star,\boldsymbol\beta^\star)
=
\arg\min
\langle\psi_p|
H_C
|\psi_p\rangle.
}
$$

Ini menghasilkan parameter:

$$
\gamma_1,\ldots,\gamma_p
$$

dan:

$$
\beta_1,\ldots,\beta_p.
$$

Kemudian kita sampling quantum circuit.

---

# D.40. Apa yang keluar dari QAOA?

Misalnya hasil sampling:

$$
|00110000\rangle
$$

dengan probabilitas tinggi.

Dengan mapping:

$$
y_i=\frac{1-Z_i}{2},
$$

kita decode:

$$
y_{AAPL}^L=1
$$

dan:

$$
y_{GLD}^L=1.
$$

Sehingga:

$$
\boxed{
LONG\ AAPL
}
$$

$$
\boxed{
LONG\ GLD.
}
$$

---

# D.41. Tetapi jangan langsung percaya bitstring paling sering

Ini sangat penting untuk trading.

Quantum optimizer dapat menghasilkan:

$$
P(y)
$$

bukan hanya satu solusi.

Misalnya:

| State | Probability |
|---|---:|
| AAPL + GLD | 0.41 |
| ETH + GLD | 0.17 |
| BTC + GLD | 0.12 |
| BTC − ETH | 0.08 |
| lainnya | 0.22 |

Maka kita sebenarnya mendapatkan **distribution over candidate portfolios**.

Ini bisa menjadi sangat berguna untuk sistem kita.

---

# D.42. Kita bisa mendefinisikan confidence

Misalnya:

$$
P^\star
=
P(y^\star).
$$

Jika:

$$
P^\star=0.41,
$$

confidence tidak terlalu tinggi.

Tetapi jika:

$$
P^\star=0.85,
$$

maka optimizer sangat konsisten terhadap solusi tersebut.

Kita dapat menggunakan:

$$
\boxed{
P^\star>P_{\min}
}
$$

sebagai salah satu syarat eksekusi.

---

# D.43. Bahkan entropy yang pernah kamu pelajari bisa masuk lagi

Kamu sebelumnya telah mempelajari Von Neumann entropy.

Di sini kita dapat menghitung entropy distribusi solusi:

$$
H_{\mathrm{Shannon}}
=
-\sum_xP(x)\log P(x).
$$

Jika distribusi sangat terkonsentrasi:

$$
P(x^\star)\approx1,
$$

maka entropy rendah.

Jika distribusi tersebar:

$$
P(x)\approx\frac1{2^N},
$$

entropy tinggi.

Jadi kita bisa mendefinisikan:

$$
\boxed{
\text{optimizer confidence}
\sim
\text{low solution entropy}.
}
$$

Ini akan menjadi hubungan yang menarik dengan penelitianmu mengenai entropy.

---

# D.44. Dan sekarang kita bisa menghubungkan dengan EPG

Di penelitianmu sebelumnya, EPG menghasilkan:

$$
x_{\mathrm{EPG}}.
$$

Misalnya:

$$
x_{\mathrm{EPG}}
=
[0,0,+1,+1].
$$

Ini dapat digunakan sebagai:

$$
\boxed{
\text{warm-start}.
}
$$

Daripada:

$$
|+\rangle^{\otimes8},
$$

kita dapat membangun initial state yang lebih dekat ke solusi EPG.

Secara konseptual:

$$
\boxed{
\text{EPG}
\rightarrow
\text{candidate equilibrium}
\rightarrow
\text{QAOA initial state}.
}
$$

---

# D.45. Dan sekarang kita mendapatkan arsitektur yang sangat kuat

Tahap A:

$$
\boxed{
Market State
}
$$

↓

Tahap B:

$$
\boxed{
Conditional Forecast
}
$$

↓

Tahap C:

$$
\boxed{
Trading Utility
}
$$

↓

Tahap D:

$$
\boxed{
QUBO
\rightarrow
Ising
\rightarrow
QAOA
}
$$

↓

kemudian:

$$
\boxed{
Trade Execution
}
$$

---

# D.46. Tetapi ada satu koreksi penting terhadap desain awal kita

Kita **belum boleh mengatakan**:

> "QAOA memutuskan TP dan SL."

Dalam formulasi yang baru kita bangun, QAOA memutuskan:

$$
\boxed{
\text{which trades and which direction}
}
$$

sedangkan:

$$
SL,\ TP,\ position\ size
$$

sebaiknya berasal dari **trade construction layer**.

Untuk tahap berikutnya kita bisa membuatnya jauh lebih sophisticated.

Misalnya untuk setiap kandidat:

$$
i
$$

bukan hanya satu state:

$$
LONG_i.
$$

Tetapi:

$$
LONG_{i,1}
$$

untuk:

$$
SL=1ATR,\ TP=2ATR,
$$

$$
LONG_{i,2}
$$

untuk:

$$
SL=1.5ATR,\ TP=3ATR,
$$

dan seterusnya.

Maka optimizer sebenarnya memilih:

$$
\boxed{
(asset,\ direction,\ entry,\ SL,\ TP)
}
$$

secara bersamaan.

Tetapi jumlah qubit akan meningkat.

---

# D.47. Ini membawa kita ke formulasi yang jauh lebih menarik

Daripada:

$$
x_i\in\{-1,0,+1\},
$$

kita bisa membuat:

$$
x_{i,d,e,s,p}\in\{0,1\}.
$$

Contohnya:

$$
x_{\text{BTC,L,limit,1ATR,2ATR}}.
$$

Dengan demikian QUBO dapat memilih:

> **BTC long, limit entry tertentu, SL 1 ATR, TP 2 ATR.**

Ini jauh lebih dekat dengan sistem trading yang kamu bayangkan sejak awal.

Namun tentu saja:

$$
N_{\text{qubit}}
$$

akan meningkat sangat cepat.

---

# D.48. Dan di sinilah kita harus berhati-hati

Misalnya:

$$
N_{asset}=50
$$

dan kita punya:

- 2 directions,
- 3 entry types,
- 3 SL choices,
- 4 TP choices.

Maka:

$$
50\times2\times3\times3\times4
=
3600
$$

binary variables.

Artinya:

$$
\boxed{
3600\text{ qubits}
}
$$

bahkan sebelum menambahkan auxiliary variables.

Ini tidak realistis untuk NISQ hardware saat ini.

Maka kita membutuhkan:

$$
\boxed{
candidate\ reduction
}
$$

sebelum quantum optimization.

---

# D.49. Ini membuat pipeline produksi kita menjadi

$$
\boxed{
1000+\ assets
}
$$

↓

classical screening

↓

$$
\boxed{
20-50 candidates
}
$$

↓

trade construction

↓

$$
\boxed{
5-10 candidates
}
$$

↓

QUBO

↓

$$
\boxed{
10-20\text{ qubits}
}
$$

untuk prototype.

Baru kemudian kita menguji:

$$
20
\rightarrow
50
\rightarrow
100
$$

qubits pada simulator/quantum hardware yang tersedia.

---

# D.50. Jadi Tahap D menghasilkan sesuatu yang sangat konkret

Kita sekarang mempunyai:

### Decision space

$$
y_i^L,y_i^S\in\{0,1\}.
$$

### Signed position

$$
x_i=y_i^L-y_i^S.
$$

### Utility

$$
U=
\mu^Tx
-\lambda x^T\Sigma x
-C
-P_F(\beta^Tx)^2
-P_{constraint}.
$$

### QUBO

$$
\boxed{
E(y)=y^TQy+c^Ty+C.
}
$$

### Ising

$$
\boxed{
H_C=
\sum_i a_iZ_i
+
\sum_{i<j}b_{ij}Z_iZ_j.
}
$$

atau dengan konvensi skripsimu:

$$
\boxed{
H_C=
-\sum_i h_iZ_i
-\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

### QAOA

$$
\boxed{
|\psi_p(\gamma,\beta)\rangle
=
\prod_{k=1}^{p}
e^{-i\beta_kH_M}
e^{-i\gamma_kH_C}
|+\rangle^{\otimes n}.
}
$$

### Output

$$
\boxed{
P(\text{LONG/SHORT/FLAT combinations})
}
$$

---

# D.51. Satu insight besar yang saya ingin kamu pegang

Perhatikan rantai berikut:

$$
\Sigma_{ij}
$$

↓

$$
Q_{ij}
$$

↓

$$
J_{ij}
$$

↓

$$
Z_iZ_j.
$$

Jadi ada hubungan matematis langsung:

$$
\boxed{
\text{asset covariance}
\rightarrow
\text{QUBO coupling}
\rightarrow
\text{Ising coupling}
\rightarrow
\text{two-qubit interaction}.
}
$$

Dengan kata lain, **struktur korelasi pasar diterjemahkan menjadi struktur interaksi qubit.**

Dan factor model memberikan coupling tambahan:

$$
\boxed{
\text{market factors}
\rightarrow
\text{factor exposure penalty}
\rightarrow
\text{additional }J_{ij}.
}
$$

Jadi nanti jika kita masukkan:

$$
BTC,\ ETH,\ SPX,\ DXY,\ GOLD,\ VIX
$$

sebagai market factors, mereka bukan sekadar indikator yang kita tampilkan pada chart. Mereka benar-benar dapat memengaruhi **Hamiltonian trading**.

---

# D.52. Tetapi Tahap D belum selesai secara sistem trading

Yang baru kita bangun adalah:

$$
\boxed{
\text{Decision Engine}.
}
$$

Kita belum membangun:

$$
\boxed{
\text{Execution Engine}
}
$$

dan:

$$
\boxed{
\text{Position Management Engine}.
}
$$

Padahal itu persis bagian yang kamu tanyakan di awal:

> kalau order belum terpanggil, apakah masih valid?

> kalau floating loss, apakah dipertahankan?

> kalau floating profit, apakah SL dinaikkan?

> kalau profit tinggi, apakah TP diperpanjang?

Itu tidak seharusnya ditangani oleh QUBO statis.

Kita membutuhkan **dynamic receding-horizon optimization**.

Dan menurutku itu adalah **Tahap E yang paling menarik**.

Kita akan mengubah sistem dari:

$$
\boxed{
\text{optimizer menghasilkan trade}
}
$$

menjadi:

$$
\boxed{
\text{optimizer menghasilkan policy}
}
$$

dengan state:

$$
S_t
$$

yang terus berubah.

Secara matematis:

$$
\boxed{
\pi^\star(S_t)
=
\arg\max_a
E[
U_{t:t+H}
\mid S_t,a
].
}
$$

Jadi setiap satu jam, atau bahkan setiap beberapa menit:

$$
S_t
\rightarrow
\text{re-optimize}
\rightarrow
a_t
\rightarrow
S_{t+\Delta t}
\rightarrow
\text{re-optimize}.
$$

**Di situlah sistem kita mulai menjadi benar-benar "quantitative trading system", bukan sekadar portfolio optimizer.**

Dan untuk Tahap E nanti kita perlu membangun secara matematis **state machine posisi: PENDING → OPEN → BEP → TRAILING → EXIT**, lalu menggabungkannya dengan **model probabilitas TP/SL, expected remaining value, trailing-stop optimization, order cancellation/replacement, dan receding-horizon/QUBO re-optimization**. Itu akan langsung menjawab empat mekanisme trading yang kamu bayangkan pada awal percakapan.

## Prompt:
8/17/2026, 9:46:27 PM

lanjut Tahap E

## Response:
8/17/2026, 9:46:27 PM

Baik. **Tahap E adalah bagian yang menurut saya paling penting untuk mengubah rancangan kita dari “optimizer yang memilih trade” menjadi sistem quantitative trading yang benar-benar dinamis.**

Pada Tahap D kita memiliki:

$$
\text{Market data}
\rightarrow
\text{forecast}
\rightarrow
\text{QUBO/Ising}
\rightarrow
\text{optimal trade}.
$$

Masalahnya, **trade yang optimal pada $t_0$ belum tentu optimal pada $t_1$**.

Karena itu Tahap E akan memperkenalkan:

$$
\boxed{\text{Dynamic Position Management + Receding-Horizon Optimization}}
$$

dengan prinsip:

> **Jangan menganggap keputusan entry sebagai keputusan final. Setiap posisi adalah keputusan yang terus dievaluasi berdasarkan informasi baru.**

---

# E.1. Masalah yang ingin kita selesaikan

Bayangkan sistem kita menghasilkan:

$$
LONG\ BTC
$$

pada:

$$
P_0=60,000.
$$

Dengan:

$$
SL=59,400
$$

dan:

$$
TP=61,200.
$$

Pada awalnya:

$$
R=\$1.
$$

Tetapi satu jam kemudian ada beberapa kemungkinan.

### Skenario A

Harga:

$$
P_t=59,500.
$$

Floating loss.

Apakah langsung ditutup?

**Belum tentu.**

---

### Skenario B

Harga:

$$
P_t=60,600.
$$

Floating profit.

Apakah langsung menaikkan SL?

**Belum tentu.**

---

### Skenario C

Harga:

$$
P_t=61,000.
$$

Profit besar, tetapi model sekarang mengatakan probabilitas continuation semakin kecil.

Mungkin lebih baik:

$$
TP\rightarrow\text{lebih dekat}
$$

atau:

$$
SL\rightarrow\text{dikunci}.
$$

---

### Skenario D

Harga:

$$
P_t=60,800
$$

tetapi BTC dominance, ETH/BTC, DXY, gold, volatility regime, dan order flow berubah drastis.

Maka:

$$
\boxed{
\text{trade yang awalnya optimal dapat menjadi tidak optimal.}
}
$$

---

# E.2. Kita membutuhkan state

Kita definisikan keadaan sistem pada waktu $t$:

$$
\boxed{
S_t
}
$$

sebagai:

$$
S_t=
(
M_t,
P_t,
V_t,
F_t,
O_t,
R_t,
\Pi_t
).
$$

Mari kita uraikan.

### $M_t$

Market state:

$$
M_t=
\{
returns,
volatility,
trend,
momentum,
correlation,
liquidity
\}.
$$

### $P_t$

Harga saat ini.

### $V_t$

Volatility state.

Misalnya:

$$
ATR_t,\quad
\sigma_t,\quad
VIX_t.
$$

### $F_t$

Factor state:

$$
F_t=
\{
DXY,
Gold,
SPX,
BTC.D,
ETH/BTC,
...
\}.
$$

### $O_t$

Order-book state:

$$
O_t=
\{
spread,
depth,
imbalance,
orderflow
\}.
$$

### $R_t$

Risk state:

$$
R_t=
\{
realized\ PnL,
remaining\ risk,
drawdown,
exposure
\}.
$$

### $\Pi_t$

Current positions:

$$
\Pi_t=
\{
pending,
open,
BEP,
trailing
\}.
$$

---

# E.3. Jadi sekarang keputusan bukan lagi $x$

Pada Tahap D kita mempunyai:

$$
x_t.
$$

Sekarang kita mempunyai:

$$
\boxed{
a_t
}
$$

sebagai **action**.

Contohnya:

$$
a_t\in
\{
WAIT,
PLACE,
CANCEL,
HOLD,
MOVE\ SL,
MOVE\ TP,
CLOSE
\}.
$$

Jadi:

$$
\boxed{
a_t=\pi(S_t).
}
$$

Artinya:

> keputusan trading merupakan fungsi dari keadaan pasar saat ini.

---

# E.4. Kita bentuk Markov Decision Process

Secara matematis sistem dapat dipandang sebagai:

$$
\boxed{
(S_t,a_t,S_{t+1},r_t).
}
$$

Dengan:

$$
S_t
\overset{a_t}{\longrightarrow}
S_{t+1}.
$$

Reward:

$$
r_t.
$$

Tetapi saya **tidak menyarankan kita langsung menggunakan reinforcement learning**.

Kita bisa membangun policy secara model-based terlebih dahulu.

Ini lebih mudah dianalisis dan lebih sesuai dengan pendekatan matematis yang sedang kita bangun.

---

# E.5. Expected remaining value

Misalkan kita sedang memegang posisi.

Harga sekarang:

$$
P_t.
$$

Kita memiliki:

$$
SL_t
$$

dan:

$$
TP_t.
$$

Definisikan:

$$
p_{TP}(t)
=
P(\text{TP hit before SL}\mid S_t).
$$

Maka jika:

$$
G_t
$$

adalah profit apabila TP tercapai, dan:

$$
L_t
$$

adalah loss apabila SL tercapai, expected value sederhananya:

$$
\boxed{
EV_t
=
p_{TP}(t)G_t
-
[1-p_{TP}(t)]L_t.
}
$$

---

# E.6. Contoh

Misalkan:

$$
G_t=2R
$$

dan:

$$
L_t=1R.
$$

Jika:

$$
p_{TP}=0.6,
$$

maka:

$$
EV
=
0.6(2)
-
0.4(1)
$$

$$
=
0.8R.
$$

Dengan:

$$
R=\$1,
$$

maka:

$$
EV=\$0.8.
$$

Masih sangat menarik.

---

# E.7. Tetapi kita belum memperhitungkan opportunity cost

Misalkan posisi dipertahankan selama satu jam.

Ada kemungkinan muncul trade baru dengan expected value:

$$
EV_{\text{new}}=0.5R.
$$

Jika posisi sekarang hanya memiliki:

$$
EV_{\text{current}}=0.1R,
$$

maka mempertahankan posisi lama mungkin tidak optimal.

Kita dapat mendefinisikan:

$$
\boxed{
EV_{\mathrm{hold}}
=
EV_{\mathrm{current}}
-
EV_{\mathrm{opportunity}}.
}
$$

Jika:

$$
EV_{\mathrm{hold}}<0,
$$

kita memiliki alasan matematis untuk menutup posisi.

---

# E.8. Ini menjawab pertanyaanmu tentang floating loss

Kamu sebelumnya mengatakan:

> jika floating loss, biarkan saja.

Saya akan mengubahnya menjadi aturan yang lebih rigor:

$$
\boxed{
\text{Floating loss bukan alasan untuk HOLD.}
}
$$

Keputusan HOLD ditentukan oleh:

$$
\boxed{
EV_{\mathrm{hold}}(S_t)>EV_{\mathrm{exit}}(S_t).
}
$$

Misalnya posisi:

$$
PnL=-0.4R.
$$

Tetapi model memperkirakan:

$$
P(TP|S_t)=0.65.
$$

Maka HOLD masih bisa rasional.

Sebaliknya:

$$
PnL=-0.1R
$$

tetapi:

$$
P(TP|S_t)=0.15.
$$

Maka exit mungkin lebih rasional.

---

# E.9. Ini prinsip yang sangat penting

Kita **tidak boleh menggunakan PnL saat ini sebagai satu-satunya dasar keputusan**.

Karena:

$$
PnL_t
$$

adalah hasil masa lalu.

Yang kita butuhkan adalah:

$$
\boxed{
E[\text{future PnL}\mid S_t].
}
$$

Jadi sistem bersifat forward-looking.

---

# E.10. Sekarang kasus floating profit

Misalkan:

$$
PnL_t=+1.2R.
$$

Pertanyaannya:

> Apakah kita harus menggeser SL?

Tidak otomatis.

Kita evaluasi tiga action:

$$
a_1=HOLD
$$

$$
a_2=TRAIL
$$

$$
a_3=EXIT.
$$

Kemudian:

$$
a^\star
=
\arg\max_a
EV(a|S_t).
$$

---

# E.11. Expected value HOLD

Misalnya:

$$
P(\text{continue})=0.55
$$

dan jika continuation:

$$
G=+2.0R.
$$

Jika reversal:

$$
L=-0.2R
$$

karena SL sudah dinaikkan.

Maka:

$$
EV_{\mathrm{hold}}
=
0.55(2)
+
0.45(-0.2)
$$

$$
=
1.01R.
$$

---

# E.12. Expected value EXIT

Jika kita tutup sekarang:

$$
EV_{\mathrm{exit}}
=
+1.2R.
$$

Maka:

$$
1.2>1.01.
$$

Secara expected-value murni:

$$
\boxed{
EXIT
}
$$

lebih baik.

---

# E.13. Tetapi risk-adjusted EV lebih masuk akal

Expected return saja tidak cukup.

Kita bisa menggunakan:

$$
\boxed{
J(a)
=
E[\Pi_a]
-
\lambda Var(\Pi_a).
}
$$

Atau lebih sophisticated:

$$
J(a)
=
E[\Pi_a]
-
\lambda_1 Var(\Pi_a)
-
\lambda_2 CVaR_\alpha(\Pi_a).
$$

Ini jauh lebih dekat dengan paradigma hedge fund.

---

# E.14. CVaR

Misalkan:

$$
\alpha=0.95.
$$

Value at Risk:

$$
VaR_{0.95}.
$$

Sedangkan:

$$
CVaR_{0.95}
$$

mengukur rata-rata kerugian pada tail terburuk 5%.

Kita dapat memasukkan:

$$
\boxed{
J=
E[\Pi]
-
\lambda Var(\Pi)
-
\eta CVaR_{0.95}.
}
$$

Dengan demikian sistem tidak hanya bertanya:

> "Berapa expected profit?"

tetapi:

> "Seberapa buruk tail risk jika saya mempertahankan trade ini?"

---

# E.15. Sekarang kita masuk ke trailing stop

Misalkan:

$$
P_t>P_0
$$

untuk LONG.

Kita definisikan trailing distance:

$$
d_t.
$$

Maka:

$$
\boxed{
SL_t=P_t-d_t.
}
$$

Tetapi:

$$
d_t
$$

tidak harus konstan.

Kita bisa membuat:

$$
d_t=k_t ATR_t.
$$

---

# E.16. Adaptive trailing stop

Misalkan:

$$
k_t
=
f(
\sigma_t,
trend_t,
orderflow_t,
p_{continuation,t}
).
$$

Contoh:

Jika:

$$
p_{continuation}=0.8
$$

dan trend kuat:

$$
k_t=2.5.
$$

Jika:

$$
p_{continuation}=0.3,
$$

maka:

$$
k_t=0.8.
$$

Jadi:

$$
\boxed{
strong\ trend
\rightarrow
looser\ trailing
}
$$

sedangkan:

$$
\boxed{
weak\ trend
\rightarrow
tighter\ trailing.
}
$$

---

# E.17. Mengapa ini lebih baik daripada aturan fixed?

Misalnya:

$$
SL=P-1ATR.
$$

Dalam market yang sangat volatile, ini terlalu dekat.

Sedangkan:

$$
SL=P-3ATR
$$

dalam market yang tenang mungkin terlalu longgar.

Maka:

$$
\boxed{
SL_t=P_t-k(S_t)ATR_t.
}
$$

lebih adaptif.

---

# E.18. Optimasi $k_t$

Kita bahkan bisa menjadikan $k$ sebagai optimization variable.

Misalkan:

$$
k\in\{0.5,1,1.5,2,2.5,3\}.
$$

Untuk setiap kandidat:

$$
k_j,
$$

kita hitung:

$$
J(k_j|S_t).
$$

Kemudian:

$$
\boxed{
k^\star
=
\arg\max_{k_j}J(k_j|S_t).
}
$$

Ini jauh lebih menarik daripada:

> "kalau profit 1%, SL digeser."

---

# E.19. TP juga dapat dibuat dinamis

Misalkan:

$$
TP_t=P_t+g_tATR_t.
$$

Dengan:

$$
g_t
=
g(S_t).
$$

Jika continuation probability tinggi:

$$
g_t\uparrow.
$$

Jika continuation probability turun:

$$
g_t\downarrow.
$$

Sehingga:

$$
\boxed{
TP_t
=
P_t+
g(S_t)ATR_t.
}
$$

---

# E.20. Tetapi jangan memindahkan TP secara sembarangan

Misalkan awal:

$$
TP=2R.
$$

Harga sudah mencapai:

$$
+1.8R.
$$

Model mengatakan momentum masih kuat.

Kita mungkin ingin:

$$
TP\rightarrow3R.
$$

Tetapi ada biaya opportunity:

$$
P(\text{reversal})
$$

meningkat.

Maka keputusan harus membandingkan:

$$
J(TP=2R)
$$

dengan:

$$
J(TP=3R).
$$

Jadi:

$$
\boxed{
TP^\star
=
\arg\max_{TP}
J(TP|S_t).
}
$$

---

# E.21. Sekarang kita punya tiga optimization problem

Untuk posisi terbuka:

### Stop-loss

$$
\boxed{
SL^\star
=
\arg\max_{SL}J(SL|S_t)
}
$$

### Take-profit

$$
\boxed{
TP^\star
=
\arg\max_{TP}J(TP|S_t)
}
$$

### Exit

$$
\boxed{
a^\star
=
\arg\max_{a\in\{HOLD,EXIT,TRAIL\}}
J(a|S_t).
}
$$

---

# E.22. Sekarang kita gabungkan dengan QUBO

Ini bagian yang sangat penting.

Pada Tahap D:

$$
Q_t
$$

dibentuk dari:

$$
\mu_t,\Sigma_t,\beta_t.
$$

Tetapi pada waktu berikutnya:

$$
t+\Delta t,
$$

data berubah.

Maka:

$$
\mu_{t+\Delta t}
\neq
\mu_t
$$

$$
\Sigma_{t+\Delta t}
\neq
\Sigma_t
$$

$$
\beta_{t+\Delta t}
\neq
\beta_t.
$$

Sehingga:

$$
\boxed{
Q_{t+\Delta t}
\neq Q_t.
}
$$

---

# E.23. Receding horizon

Jadi kita menjalankan:

$$
Q_t
\rightarrow
x_t^\star
$$

kemudian setelah:

$$
\Delta t:
$$

$$
Q_{t+\Delta t}
\rightarrow
x_{t+\Delta t}^\star.
$$

Ini disebut:

$$
\boxed{
\text{receding-horizon optimization}.
}
$$

Kita tidak mengatakan:

> "trade ini harus dipertahankan sampai TP."

Kita mengatakan:

> "berdasarkan informasi yang tersedia sekarang, keputusan terbaik adalah HOLD."

Lalu keputusan itu **ditinjau ulang**.

---

# E.24. State machine sistem

Sekarang kita dapat membuat state machine:

$$
\boxed{
FLAT
}
$$

↓

signal valid

↓

$$
\boxed{
PENDING
}
$$

↓

order filled

↓

$$
\boxed{
OPEN
}
$$

↓

profit sufficient

↓

$$
\boxed{
PROTECTED
}
$$

↓

trailing optimization

↓

$$
\boxed{
TRAILING
}
$$

↓

exit condition

↓

$$
\boxed{
CLOSED
}
$$

Tetapi ada juga cabang:

$$
PENDING
\rightarrow
CANCELLED
$$

jika signal invalid.

---

# E.25. PENDING state

Misalkan sistem memasang:

$$
LIMIT\ ENTRY=P_0.
$$

Namun order belum filled.

Setiap interval:

$$
\Delta t
$$

kita hitung:

$$
EV_{\mathrm{entry}}(S_t).
$$

Jika:

$$
EV_{\mathrm{entry}}<EV_{\min},
$$

maka:

$$
\boxed{
CANCEL.
}
$$

Ini menjawab pertanyaanmu:

> "jika order book belum terpanggil, apakah masih bisa dipertahankan?"

Jawabannya:

$$
\boxed{
hanya jika expected value conditional masih cukup tinggi.
}
$$

---

# E.26. Entry decay

Ini bahkan dapat dimodelkan sebagai:

$$
EV_{\mathrm{entry}}(t)
=
EV_0e^{-\kappa t}
+
\Delta EV(S_t).
$$

Dengan:

$$
\kappa>0.
$$

Artinya semakin lama order tidak tersentuh, original signal semakin "basi".

Ini masuk akal karena model yang menghasilkan signal tersebut dibuat dari:

$$
S_{t_0}.
$$

Bukan:

$$
S_t.
$$

---

# E.27. Kita dapat mendefinisikan signal half-life

Jika:

$$
EV(t)=EV_0e^{-\kappa t},
$$

maka half-life:

$$
\boxed{
t_{1/2}
=
\frac{\ln2}{\kappa}.
}
$$

Ini merupakan parameter yang bisa kita estimasi dari data historis.

Misalnya:

$$
t_{1/2}=3\text{ jam}.
$$

Maka setelah 3 jam tanpa fill, informasi signal secara statistik sudah jauh berkurang.

---

# E.28. OPEN state

Setelah fill:

$$
P_t=P_{\mathrm{entry}}.
$$

Kita hitung:

$$
PnL_t
=
q(P_t-P_{\mathrm{entry}})
$$

untuk LONG.

Untuk SHORT:

$$
PnL_t
=
q(P_{\mathrm{entry}}-P_t).
$$

Kemudian:

$$
R_t
=
\frac{PnL_t}{R_0}.
$$

Dengan:

$$
R_0=\$1.
$$

Sehingga sistem selalu berbicara dalam unit:

$$
\boxed{R}.
$$

---

# E.29. Ini membuat semua aset comparable

Misalnya:

BTC:

$$
PnL=+\$0.80
$$

berarti:

$$
+0.8R.
$$

AAPL:

$$
PnL=+\$0.80
$$

juga:

$$
+0.8R.
$$

Tidak peduli harga aset berbeda jauh.

Ini sangat penting untuk portfolio multi-asset.

---

# E.30. Risk budget portfolio

Kita tidak boleh hanya membatasi:

$$
Risk_i\le1R.
$$

Kita juga membutuhkan:

$$
\boxed{
\sum_i Risk_i\le R_{\mathrm{portfolio}}.
}
$$

Misalnya:

$$
R_{\mathrm{portfolio}}=3R.
$$

Maka maksimal tiga unit risk aktif.

Tetapi karena correlation:

$$
\text{effective risk}
$$

bisa lebih besar daripada:

$$
3R.
$$

Jadi kita gunakan:

$$
\boxed{
x^T\Sigma x
\le
V_{\max}.
}
$$

---

# E.31. Risk budget dinamis

Bahkan:

$$
R_{\mathrm{portfolio}}
$$

dapat bergantung pada market regime.

Misalnya:

$$
R_{\max}(t)
=
R_0
\cdot
g(V_t).
$$

Ketika volatility tinggi:

$$
V_t\uparrow
\Rightarrow
R_{\max}\downarrow.
$$

Ketika volatility rendah:

$$
V_t\downarrow
\Rightarrow
R_{\max}\uparrow.
$$

Jadi sistem secara otomatis menjadi defensive ketika market stress.

---

# E.32. Sekarang kita masukkan DXY dan Gold

Kamu sebelumnya mengatakan ingin sistem tidak berhenti pada crypto.

Kita dapat mendefinisikan factor vector:

$$
F_t=
\begin{bmatrix}
DXY_t\\
Gold_t\\
SPX_t\\
VIX_t\\
BTC.D_t
\end{bmatrix}.
$$

Untuk setiap asset:

$$
r_{i,t}
=
\alpha_i
+
\beta_i^TF_t
+
\epsilon_{i,t}.
$$

Jadi:

$$
\boxed{
\beta_i
=
\begin{bmatrix}
\beta_{DXY}\\
\beta_{Gold}\\
\beta_{SPX}\\
\beta_{VIX}\\
\beta_{BTC.D}
\end{bmatrix}.
}
$$

---

# E.33. Factor surprise

Bukan hanya level factor.

Kita dapat menggunakan:

$$
\Delta F_t
=
F_t-F_{t-\Delta t}.
$$

Lebih baik lagi:

$$
z_{F,t}
=
\frac{
\Delta F_t-\mu_F
}{
\sigma_F
}.
$$

Sehingga sistem mengetahui:

$$
\boxed{
\text{factor shock}.
}
$$

Misalnya:

$$
z_{DXY}=+2.1.
$$

Artinya terjadi positive DXY shock.

Jika BTC memiliki:

$$
\beta_{BTC,DXY}<0,
$$

maka expected return BTC dapat dikoreksi turun.

---

# E.34. Conditional expected return

Sekarang:

$$
\mu_{i,t}
$$

tidak lagi sekadar historical average.

Kita buat:

$$
\boxed{
\mu_{i,t}
=
f(
X_{i,t},
F_t,
O_t,
Regime_t
).
}
$$

Misalnya:

$$
\mu_{i,t}
=
\alpha_i
+
\beta_i^TF_t
+
\theta_i^TX_{i,t}
+
\phi_i^TO_{i,t}.
$$

Ini adalah bagian yang nantinya dapat kita isi dengan:

- statistical model,
- gradient boosting,
- neural network,
- quantum model,
- atau kombinasi semuanya.

---

# E.35. Tetapi optimizer tetap terpisah dari predictor

Ini arsitektur yang sangat penting:

$$
\boxed{
Prediction
\neq
Optimization.
}
$$

Model forecasting mengatakan:

$$
P(\text{future return}\mid S_t).
$$

Optimizer mengatakan:

$$
\arg\max_x
U(x\mid S_t).
$$

Execution engine mengatakan:

$$
\arg\max_a
J(a\mid x,S_t).
$$

Jadi kita mempunyai tiga layer.

---

# E.36. Arsitektur matematis lengkap

$$
\boxed{
\text{Market Data}
}
$$

↓

$$
\boxed{
S_t
}
$$

↓

$$
\boxed{
\text{Forecast Model}
}
$$

↓

$$
\mu_t,\Sigma_t,\beta_t
$$

↓

$$
\boxed{
\text{QUBO Builder}
}
$$

↓

$$
Q_t
$$

↓

$$
\boxed{
\text{QAOA / Classical Solver}
}
$$

↓

$$
x_t^\star
$$

↓

$$
\boxed{
\text{Trade Construction}
}
$$

↓

$$
ENTRY,SL,TP,q
$$

↓

$$
\boxed{
\text{Execution}
}
$$

↓

$$
\boxed{
\text{Position State}
}
$$

↓

setiap:

$$
\Delta t
$$

↓

$$
\boxed{
\text{Re-evaluation}
}
$$

↓

$$
\boxed{
Q_{t+\Delta t}
}
$$

dan kembali lagi.

---

# E.37. Inilah bentuk feedback loop

Secara matematis:

$$
\boxed{
S_t
\rightarrow
Q_t
\rightarrow
a_t
\rightarrow
S_{t+\Delta t}
\rightarrow
Q_{t+\Delta t}
\rightarrow
a_{t+\Delta t}
\rightarrow\cdots
}
$$

Jadi sistem bukan:

$$
\text{predict}\rightarrow\text{trade}\rightarrow\text{wait}.
$$

Tetapi:

$$
\boxed{
\text{predict}
\rightarrow
\text{optimize}
\rightarrow
\text{execute}
\rightarrow
\text{observe}
\rightarrow
\text{re-optimize}.
}
$$

---

# E.38. Pseudocode matematis

Secara konseptual:

```text
INITIALIZE capital
INITIALIZE risk budget

while market_is_open:

    S_t = collect_market_state()

    update:
        returns
        volatility
        correlations
        market factors
        order book
        current positions

    μ_t, Σ_t, β_t = forecast(S_t)

    Q_t = build_QUBO(
        μ_t,
        Σ_t,
        β_t,
        constraints,
        transaction_cost
    )

    candidate_trades = solve(Q_t)

    for pending_order:

        EV_entry = evaluate_entry(
            pending_order,
            S_t
        )

        if EV_entry < threshold:
            cancel_order()

    for open_position:

        evaluate:
            P(TP | S_t)
            P(SL | S_t)
            expected continuation
            expected exit
            CVaR
            opportunity cost

        optimize:
            SL*
            TP*
            HOLD / EXIT

        execute optimal action

    update risk budget

    wait Δt
```

---

# E.39. Tetapi ada satu masalah besar: look-ahead bias

Ini **sangat penting** jika nanti kita melakukan backtest.

Misalnya kita menggunakan:

$$
\Sigma_t
$$

yang dihitung menggunakan data sampai:

$$
t+1.
$$

Maka sistem secara tidak sengaja melihat masa depan.

Backtest menjadi:

$$
\boxed{\text{invalid}.}
$$

Semua feature harus memenuhi:

$$
\boxed{
X_t=f(D_{\le t}).
}
$$

Tidak boleh:

$$
X_t=f(D_{\le t+\Delta}).
$$

---

# E.40. Hal yang sama berlaku pada optimizer

QUBO pada:

$$
t
$$

harus dibangun dari informasi yang tersedia pada:

$$
t.
$$

Bukan menggunakan covariance yang dihitung dari seluruh dataset.

Jadi:

$$
\boxed{
Q_t=f(D_{\le t}).
}
$$

Ini akan menjadi prinsip fundamental backtesting kita.

---

# E.41. Kita juga membutuhkan walk-forward optimization

Tidak cukup:

$$
train\rightarrow test
$$

sekali.

Lebih realistis:

$$
\boxed{
Train_1
\rightarrow
Test_1
}
$$

kemudian:

$$
Train_2
\rightarrow
Test_2
$$

dan seterusnya.

Misalnya:

$$
2021-01
\rightarrow
2022-01
$$

training,

$$
2022-02
\rightarrow
2022-04
$$

testing.

Kemudian window bergeser.

---

# E.42. Bahkan parameter trailing harus di-walk-forward

Jangan mencari:

$$
k=2.37
$$

menggunakan seluruh data 2021–2026 lalu mengatakan:

> strategy works.

Kita harus:

$$
k_t^\star
=
\arg\max_k
J_k
$$

menggunakan **training window**, lalu menguji pada window berikutnya.

---

# E.43. Ini juga berlaku untuk QAOA

Parameter:

$$
\gamma,\beta
$$

tidak boleh dioptimalkan menggunakan informasi masa depan.

Pada setiap periode:

$$
Q_t
$$

dibangun.

Kemudian:

$$
(\gamma_t^\star,\beta_t^\star)
$$

dicari.

Kemudian solusi diterapkan pada future interval.

---

# E.44. Jadi kita memiliki dua jenis optimization

Ini perlu dibedakan.

### Optimization level 1

**Combinatorial optimization**

$$
\boxed{
\min_x x^TQx
}
$$

menggunakan QAOA.

Tujuannya:

> trade mana yang dipilih?

---

### Optimization level 2

**Continuous/control optimization**

$$
\boxed{
\max_{SL,TP}
J(SL,TP|S_t).
}
$$

Tujuannya:

> bagaimana trade dikelola?

Jadi QAOA tidak perlu dipaksa melakukan semuanya.

---

# E.45. Ini justru membuat arsitektur lebih masuk akal

Kita menggunakan quantum optimization di tempat yang memang cocok:

$$
\boxed{
\text{discrete combinatorial selection}.
}
$$

Sedangkan continuous optimization dapat menggunakan:

- BFGS,
- SLSQP,
- SPSA,
- Bayesian optimization,
- grid search,
- atau metode lainnya.

Dengan demikian:

$$
\boxed{
Quantum
+
Classical
}
$$

bukan kompetisi.

Mereka bekerja sebagai hybrid system.

---

# E.46. Bentuk akhir Tahap E

Kita sekarang dapat mendefinisikan objective posisi:

$$
\boxed{
J_t(a)
=
E[
PnL_{t:t+H}
\mid
S_t,a
]
-
\lambda
Var[
PnL_{t:t+H}
]
-
\eta
CVaR_\alpha
-
\kappa
TC(a).
}
$$

Kemudian:

$$
\boxed{
a_t^\star
=
\arg\max_{a\in\mathcal A}
J_t(a).
}
$$

Ini menjadi **otak Position Management Engine**.

---

# E.47. Dan akhirnya, empat pertanyaan awalmu mendapatkan formulasi matematis

### 1. Order belum terpanggil

Hitung:

$$
EV_{\mathrm{entry}}(S_t).
$$

Jika:

$$
EV_{\mathrm{entry}}<\theta,
$$

maka:

$$
\boxed{CANCEL}.
$$

---

### 2. Floating loss

Jangan gunakan:

$$
PnL<0
$$

sebagai exit signal.

Gunakan:

$$
\boxed{
J(HOLD)>J(EXIT).
}
$$

---

### 3. Floating profit

Evaluasi:

$$
J(HOLD),
\quad
J(TRAIL),
\quad
J(EXIT).
$$

Kemudian:

$$
\boxed{
a^\star=\arg\max J(a).
}
$$

---

### 4. Profit sangat tinggi

Optimalkan:

$$
SL^\star
$$

dan:

$$
TP^\star.
$$

Jika:

$$
J(TP_{\mathrm{new}})
>
J(TP_{\mathrm{old}}),
$$

maka:

$$
\boxed{
TP\rightarrow TP_{\mathrm{new}}.
}
$$

---

# E.48. Hal yang paling menarik dari seluruh desain ini

Sistem kita sekarang mempunyai **tiga skala waktu**:

### Fast

Order book:

$$
seconds\rightarrow minutes.
$$

Digunakan untuk:

$$
entry,\ slippage,\ execution.
$$

### Medium

Trading signal:

$$
minutes\rightarrow hours.
$$

Digunakan untuk:

$$
QUBO/QAOA.
$$

### Slow

Market regime:

$$
days\rightarrow weeks.
$$

Digunakan untuk:

$$
risk\ budget,
factor\ model,
correlation\ structure.
$$

Sehingga:

$$
\boxed{
\text{microstructure}
+
\text{trading signal}
+
\text{macro regime}
}
$$

bertemu dalam satu sistem.

---

# E.49. Dan ini membawa kita ke Tahap F

Sampai sini kita sudah mempunyai:

$$
\boxed{
A:\ Market\ State
}
$$

$$
\boxed{
B:\ Forecasting
}
$$

$$
\boxed{
C:\ Financial\ Objective
}
$$

$$
\boxed{
D:\ QUBO/Ising/QAOA
}
$$

$$
\boxed{
E:\ Dynamic\ Position\ Management
}
$$

Maka Tahap F seharusnya bukan sekadar "coding".

Kita perlu membangun **mesin backtesting yang benar-benar event-driven**.

Karena sistem kita memiliki:

- pending orders,
- partial fills,
- spread,
- slippage,
- TP,
- SL,
- trailing,
- cancellation,
- re-optimization,
- portfolio risk,
- multiple assets,
- factor data,
- dan QAOA/classical solver.

Jadi backtest sederhana seperti:

$$
\texttt{if close > signal: buy}
$$

sudah tidak cukup.

Tahap F sebaiknya kita turunkan menjadi:

$$
\boxed{
\text{Event-Driven Backtesting Engine}
}
$$

dengan **order book → order → fill → position → PnL → risk → reoptimization**, termasuk derivasi bagaimana mencegah **look-ahead bias, survivorship bias, data leakage, unrealistic fills, dan overfitting**.

Dan setelah mesin itu benar, barulah kita bisa menguji pertanyaan yang paling penting secara empiris:

$$
\boxed{
\text{Apakah QAOA benar-benar memberikan nilai tambah dibandingkan optimizer klasik?}
}
$$

Itulah eksperimen yang pada akhirnya akan membuat bagian quantum dari proyek ini **ilmiah**, bukan sekadar menempelkan QAOA pada strategi trading.

## Prompt:
8/17/2026, 9:47:24 PM

lanjut Tahap F

## Response:
8/17/2026, 9:47:25 PM

Tentu. **Tahap F adalah fondasi eksperimental seluruh sistem kita.** Kalau Tahap A–E adalah membangun "otak" strategi, maka Tahap F adalah membangun **dunia virtual yang cukup realistis untuk menguji otak tersebut**.

Dan saya ingin menekankan satu perubahan paradigma:

> Kita tidak lagi membuat backtest sebagai fungsi sederhana `signal → return`. Kita membuat **event-driven market simulator** yang mereplikasi urutan kejadian: market data → signal → order → fill → position → risk management → cancellation/modification → exit → PnL.

Dengan begitu, nanti kita benar-benar bisa menguji apakah QAOA/quantum optimizer memberikan keuntungan dibandingkan metode klasik.

---

# Tahap F — Event-Driven Backtesting & Simulation Engine

Arsitektur besar kita sekarang:

$$
\boxed{
\text{Historical Market Data}
\rightarrow
\text{Market State}
\rightarrow
\text{Forecast}
\rightarrow
\text{Optimization}
\rightarrow
\text{Orders}
\rightarrow
\text{Execution Simulator}
\rightarrow
\text{Positions}
\rightarrow
\text{Risk Manager}
\rightarrow
\text{Re-optimization}
}
$$

dan semuanya berjalan secara temporal:

$$
t_0<t_1<t_2<\cdots<t_T.
$$

---

# F.1. Mengapa backtest biasa tidak cukup?

Bayangkan kita mempunyai signal:

$$
LONG\quad BTC
$$

pada:

$$
t=10:00.
$$

Harga:

$$
P_{10:00}=60,000.
$$

Strategi mengatakan:

$$
Entry=59,950.
$$

Kemudian harga bergerak:

$$
59,980
\rightarrow
59,960
\rightarrow
59,950
\rightarrow
59,900
\rightarrow
60,100.
$$

Backtest sederhana mungkin melihat candle:

$$
Low=59,900,
$$

lalu mengatakan:

> limit order pasti terisi.

Tetapi itu **belum tentu benar**.

Mengapa?

Karena kita tidak tahu:

- apakah order kita berada di depan atau belakang antrean,
- berapa banyak volume yang tersedia,
- apakah harga benar-benar menyentuh order,
- apakah fill hanya sebagian,
- bagaimana spread berubah,
- bagaimana latency memengaruhi order.

Jadi kita harus memodelkan:

$$
\boxed{
\text{price path}
+
\text{liquidity}
+
\text{order state}.
}
$$

---

# F.2. Waktu menjadi variabel fundamental

Sebelumnya kita hanya memikirkan:

$$
P_t.
$$

Sekarang kita harus memiliki:

$$
\boxed{
\mathcal D_t
}
$$

sebagai informasi pasar yang tersedia **tepat pada waktu $t$**.

Misalnya:

$$
\mathcal D_t=
\{
P_{\leq t},
V_{\leq t},
O_{\leq t},
F_{\leq t}
\}.
$$

Maka seluruh keputusan strategi harus memenuhi:

$$
\boxed{
a_t=\pi(\mathcal D_t).
}
$$

Tidak boleh:

$$
a_t=\pi(\mathcal D_{t+\Delta}).
$$

Ini adalah prinsip anti-look-ahead bias.

---

# F.3. Event-driven architecture

Kita definisikan event:

$$
e_t.
$$

Contohnya:

$$
e_t\in
\{
MARKET\_UPDATE,
SIGNAL,
ORDER\_SUBMIT,
ORDER\_FILL,
ORDER\_CANCEL,
SL\_UPDATE,
TP\_UPDATE,
POSITION\_UPDATE,
RISK\_UPDATE
\}.
$$

Backtester kemudian menjalankan:

$$
\boxed{
e_1\rightarrow e_2\rightarrow e_3\rightarrow\cdots
}
$$

berdasarkan timestamp.

---

# F.4. Market Event

Misalnya data datang:

$$
e_t^{market}.
$$

Informasinya:

$$
M_t=
\{
bid_t,
ask_t,
last_t,
volume_t,
orderbook_t
\}.
$$

Dari sini kita memperbarui:

$$
S_t.
$$

---

# F.5. State machine

Engine kita memiliki state global:

$$
\boxed{
\mathcal S_t
=
(
MarketState,
PortfolioState,
OrderState,
RiskState
).
}
$$

### MarketState

$$
M_t.
$$

### PortfolioState

$$
\Pi_t.
$$

### OrderState

$$
O_t.
$$

### RiskState

$$
R_t.
$$

---

# F.6. Order state machine

Setiap order mempunyai state:

$$
\boxed{
CREATED
}
$$

↓

$$
SUBMITTED
$$

↓

$$
PARTIALLY\ FILLED
$$

↓

$$
FILLED
$$

atau:

$$
CANCELLED
$$

atau:

$$
EXPIRED.
$$

Ini penting karena order kita bukan hanya:

$$
0/1.
$$

---

# F.7. Contoh

Misalkan:

$$
Q=100.
$$

Kita ingin membeli:

$$
100\ BTC\text{-equivalent units}.
$$

Namun hanya 40 yang tersedia pada harga tersebut.

Maka:

$$
Q_{\mathrm{filled}}=40.
$$

Remaining:

$$
Q_{\mathrm{remaining}}=60.
$$

Sehingga:

$$
\boxed{
Q=Q_{\mathrm{filled}}+Q_{\mathrm{remaining}}.
}
$$

---

# F.8. Fill model

Untuk market order sederhana:

$$
P_{\mathrm{fill}}
\approx
P_{\mathrm{ask}}
+
slippage.
$$

Untuk LONG:

$$
P_{\mathrm{fill}}
=
P_{\mathrm{ask}}
+
\delta.
$$

Untuk SHORT:

$$
P_{\mathrm{fill}}
=
P_{\mathrm{bid}}
-
\delta.
$$

---

# F.9. Slippage

Slippage dapat dimodelkan:

$$
\boxed{
\delta_t
=
f(
Q_t,
Depth_t,
Volatility_t,
Spread_t
).
}
$$

Model sederhana:

$$
\delta_t
=
\lambda
\frac{Q_t}{Depth_t}.
$$

Sehingga:

$$
Q_t\uparrow
\Rightarrow
\delta_t\uparrow.
$$

Ini sangat penting ketika nanti strategi kita mulai melakukan portfolio multi-asset.

---

# F.10. Spread

Misalkan:

$$
Bid_t=100
$$

dan:

$$
Ask_t=100.02.
$$

Maka:

$$
Spread_t=Ask_t-Bid_t=0.02.
$$

Relative spread:

$$
\boxed{
s_t=
\frac{Ask_t-Bid_t}
{(Ask_t+Bid_t)/2}.
}
$$

Strategi jangka pendek sangat sensitif terhadap:

$$
s_t.
$$

---

# F.11. Transaction cost

Total biaya kita definisikan:

$$
TC_t
=
Fee_t
+
SpreadCost_t
+
Slippage_t
+
MarketImpact_t.
$$

Kemudian:

$$
\boxed{
PnL_{\mathrm{net}}
=
PnL_{\mathrm{gross}}
-
TC.
}
$$

Ini harus dimasukkan sejak awal.

Kalau tidak, strategi yang terlihat profitabel dapat berubah menjadi loss setelah biaya.

---

# F.12. Market impact

Untuk ukuran order yang cukup besar:

$$
\Delta P
\propto
Q^\alpha.
$$

Model sederhana:

$$
\boxed{
Impact(Q)
=
\eta
\left(
\frac{Q}{ADV}
\right)^\alpha.
}
$$

Dengan:

$$
ADV=\text{average daily volume}.
$$

Biasanya:

$$
0<\alpha<1.
$$

---

# F.13. Kita sekarang bisa menghitung execution price

Misalnya LONG:

$$
P_{\mathrm{exec}}
=
Ask_t
+
Impact(Q)
+
Slippage_t.
$$

Maka:

$$
Cost_{\mathrm{execution}}
=
Q(P_{\mathrm{exec}}-P_{\mathrm{mid}}).
$$

---

# F.14. Position accounting

Setelah fill, kita memiliki:

$$
q_t
$$

sebagai posisi.

Untuk LONG:

$$
q_t>0.
$$

Untuk SHORT:

$$
q_t<0.
$$

Untuk FLAT:

$$
q_t=0.
$$

Nilai posisi:

$$
V_t=q_tP_t.
$$

---

# F.15. Average entry price

Jika posisi masuk secara bertahap:

$$
(q_1,P_1),
(q_2,P_2),
\dots
$$

maka:

$$
\boxed{
P_{\mathrm{avg}}
=
\frac{
\sum_iq_iP_i
}{
\sum_iq_i
}.
}
$$

Ini penting ketika terjadi partial fill.

---

# F.16. Unrealized PnL

Untuk LONG:

$$
PnL_t^{unreal}
=
q(P_t-P_{\mathrm{avg}}).
$$

Untuk SHORT:

$$
PnL_t^{unreal}
=
q(P_{\mathrm{avg}}-P_t),
$$

dengan $q>0$ sebagai absolute quantity.

Atau kita bisa menyatukannya menggunakan signed position:

$$
\boxed{
PnL_t^{unreal}
=
q_t(P_t-P_{\mathrm{avg}}).
}
$$

---

# F.17. Realized PnL

Ketika posisi ditutup:

$$
PnL^{realized}
=
q_{\mathrm{closed}}
(P_{\mathrm{exit}}-P_{\mathrm{entry}})
-
TC.
$$

Kemudian:

$$
Equity_t
=
Equity_0
+
\sum_{\tau\leq t}
PnL_\tau^{realized}
+
PnL_t^{unrealized}.
$$

---

# F.18. Risk unit

Kita sebelumnya menetapkan:

$$
R=\$1.
$$

Maka setiap trade harus mempunyai:

$$
Risk_i\leq R.
$$

Misalnya entry:

$$
P_e=100.
$$

SL:

$$
P_{SL}=99.
$$

Risk per unit:

$$
r=1.
$$

Untuk:

$$
R=\$1,
$$

quantity:

$$
\boxed{
q=\frac{R}{|P_e-P_{SL}|}.
}
$$

Sehingga:

$$
q=1.
$$

---

# F.19. Contoh lain

Entry:

$$
P_e=100.
$$

SL:

$$
P_{SL}=98.
$$

Maka risk per unit:

$$
2.
$$

Jika:

$$
R=\$1,
$$

maka:

$$
q=\frac{1}{2}.
$$

Jika SL terkena:

$$
Loss\approx\$1
$$

sebelum biaya.

---

# F.20. Tetapi kita harus memperhitungkan gap

Misalkan:

$$
SL=98.
$$

Namun harga melompat:

$$
100\rightarrow95.
$$

Maka actual loss:

$$
100-95=5.
$$

Bukan:

$$
100-98=2.
$$

Jadi:

$$
\boxed{
Risk_{\mathrm{realized}}
\neq
Risk_{\mathrm{planned}}.
}
$$

Untuk saham, gap risk sangat penting.

Untuk crypto 24/7, gap biasanya berbeda karakter tetapi tetap dapat muncul pada perubahan likuiditas ekstrem.

---

# F.21. Maka kita membutuhkan risk multiplier

Misalnya:

$$
q
=
\frac{R}
{
E[Loss|SL]
}.
$$

Bukan sekadar:

$$
\frac{R}{SL-distance}.
$$

Jika expected execution loss:

$$
E[Loss]=1.25
$$

maka:

$$
q=\frac{1}{1.25}=0.8.
$$

---

# F.22. Order lifecycle

Sekarang mari kita ikuti satu trade.

### t₀

Model menghasilkan:

$$
x^\star=1.
$$

Artinya LONG.

---

### t₁

Trade constructor menghasilkan:

$$
Entry=100
$$

$$
SL=99
$$

$$
TP=102.
$$

---

### t₂

Order dikirim.

State:

$$
PENDING.
$$

---

### t₃

Market:

$$
Bid=99.99
$$

$$
Ask=100.01.
$$

Order belum filled.

---

### t₄

Market berubah.

Model baru:

$$
EV_{\mathrm{entry}}<\theta.
$$

Maka:

$$
CANCEL.
$$

Trade tidak pernah terjadi.

**Ini harus tercatat sebagai cancellation, bukan loss.**

---

# F.23. Contoh kedua

Order filled:

$$
P_e=100.
$$

SL:

$$
99.
$$

TP:

$$
102.
$$

Kemudian:

$$
P_t=100.8.
$$

Model menghitung:

$$
J(HOLD)>J(EXIT).
$$

Tetap HOLD.

---

# F.24. Kemudian

Harga:

$$
101.2.
$$

Model menghitung:

$$
SL^\star=100.7.
$$

Maka:

$$
SL:99\rightarrow100.7.
$$

Sekarang maximum planned loss bukan lagi:

$$
1R.
$$

Tetapi posisi sudah memiliki locked profit:

$$
0.7R.
$$

---

# F.25. Kemudian

Harga:

$$
102.5.
$$

Model mengatakan:

$$
TP^\star=104.
$$

Maka:

$$
TP:102\rightarrow104.
$$

---

# F.26. Kemudian harga turun

$$
102.7
\rightarrow
101.9
\rightarrow
100.7.
$$

SL terkena.

Realized PnL:

$$
+0.7R
$$

sebelum biaya.

Inilah contoh konkret dari **dynamic position management**.

---

# F.27. Data yang diperlukan

Sekarang kita harus menentukan data minimum.

Untuk tahap awal:

### Asset data

$$
OHLCV.
$$

### Market factors

Untuk saham internasional:

$$
DXY,
Gold,
SPX,
VIX,
Treasury\ yields.
$$

Untuk crypto:

$$
BTC,
ETH,
BTC.D,
ETH/BTC.
$$

Kemudian:

$$
\text{asset-specific data}.
$$

---

# F.28. Untuk strategi short-term, timeframe harus multi-resolution

Saya menyarankan kita tidak hanya memiliki satu timeframe.

Misalnya:

### Slow

$$
1D
$$

untuk regime.

### Medium

$$
1H
$$

untuk signal.

### Fast

$$
5m
$$

untuk entry.

Jika data tersedia:

### Microstructure

$$
1m
$$

atau bahkan tick/order book.

Sehingga:

$$
\boxed{
S_t=
(S_t^{1D},
S_t^{1H},
S_t^{5m},
S_t^{1m})
}
$$

---

# F.29. Mengapa multi-timeframe?

Misalnya:

Daily:

$$
Trend=UP.
$$

Hourly:

$$
Momentum=UP.
$$

5-minute:

$$
Pullback.
$$

1-minute:

$$
Bid\ imbalance>0.
$$

Maka semua layer konsisten.

Sebaliknya:

Daily:

$$
Trend=DOWN.
$$

5-minute:

$$
Momentum=UP.
$$

Mungkin LONG jangka pendek tetap bisa dilakukan, tetapi confidence harus lebih rendah.

---

# F.30. Data leakage menjadi lebih rumit

Misalkan kita sedang berada di:

$$
10:00.
$$

Candle 1H:

$$
10:00-11:00.
$$

Kita **tidak boleh menggunakan close 1H** pada 10:15 karena candle belum selesai.

Kita hanya boleh menggunakan:

$$
Open_{10:00},
High_{\leq10:15},
Low_{\leq10:15},
Volume_{\leq10:15}.
$$

Ini kesalahan yang sangat umum dalam backtest.

---

# F.31. Point-in-time data

Prinsipnya:

$$
\boxed{
Feature_t
=
f(Data\ available\ at\ t).
}
$$

Bahkan untuk fundamental data:

jangan menggunakan laporan yang baru dipublikasikan pada:

$$
t+2
$$

seolah-olah sudah diketahui pada:

$$
t.
$$

Untuk strategi kita, ini menjadi prinsip wajib.

---

# F.32. Walk-forward framework

Sekarang kita masuk ke struktur validasi.

Misalnya:

$$
T_1=\text{training}
$$

$$
V_1=\text{validation}
$$

$$
O_1=\text{out-of-sample}.
$$

Kemudian rolling:

$$
T_2
\rightarrow
V_2
\rightarrow
O_2.
$$

Sehingga:

$$
\boxed{
\text{Train}
\rightarrow
\text{Validate}
\rightarrow
\text{Trade unseen data}
}
$$

berulang.

---

# F.33. Mengapa tidak random train-test split?

Karena data finansial adalah time series.

Jika kita melakukan:

```text
random train/test split
```

maka:

$$
t_{future}
$$

bisa masuk training sementara:

$$
t_{past}
$$

masuk test.

Ini merusak temporal causality.

Jadi:

$$
\boxed{
\text{No random shuffling}.
}
$$

---

# F.34. Parameter yang harus di-fit

Banyak sekali parameter kita:

$$
\theta=
\{
\lambda,
\gamma,
\beta,
k_{SL},
k_{TP},
\kappa,
threshold,
lookback,
risk\ budget,
...
\}.
$$

Masalahnya:

$$
|\theta|
$$

bisa sangat besar.

Jika kita terlalu agresif melakukan optimization:

$$
\theta^\star
=
\arg\max_\theta
Performance(\theta)
$$

pada historical data, kita bisa mendapatkan:

$$
\boxed{
Overfitting.
}
$$

---

# F.35. In-sample performance bukan bukti

Misalkan:

$$
Sharpe=4.8
$$

pada training data.

Itu belum berarti apa-apa.

Kita lebih tertarik pada:

$$
Sharpe_{\mathrm{OOS}}.
$$

Dan bahkan:

$$
Sharpe_{\mathrm{OOS}}
$$

yang tinggi sekali juga harus dicurigai jika parameter terlalu banyak.

---

# F.36. Parameter stability

Kita ingin melihat:

$$
Performance(\theta)
$$

tidak hanya bagus di satu titik.

Misalnya:

$$
k_{SL}=1.8
$$

menghasilkan Sharpe:

$$
1.7.
$$

Tetapi:

$$
k_{SL}=1.7\rightarrow1.6
$$

juga menghasilkan:

$$
1.65,\ 1.61.
$$

Ini bagus.

Sebaliknya:

$$
k_{SL}=1.80
\rightarrow
Sharpe=2.5
$$

tetapi:

$$
k_{SL}=1.79
\rightarrow
0.3.
$$

Itu tanda kuat overfitting.

---

# F.37. Kita perlu baseline

Ini sangat penting untuk proyek quantum kita.

Kita tidak boleh hanya mengatakan:

> "QAOA menghasilkan profit."

Kita harus membandingkan:

$$
\boxed{
QAOA
\quad vs \quad
Classical\ Optimizer.
}
$$

Minimal:

### Baseline 1

Equal weighting.

### Baseline 2

Greedy selection.

### Baseline 3

Classical QUBO solver.

Misalnya:

$$
Simulated\ Annealing.
$$

### Baseline 4

MILP / exact solver untuk problem kecil.

### Baseline 5

Heuristic portfolio selection.

---

# F.38. Baru kemudian QAOA

Misalnya:

$$
QUBO
$$

yang sama diberikan kepada:

$$
\begin{cases}
Exact\\
Simulated\ Annealing\\
Greedy\\
QAOA
\end{cases}
$$

Semua menghasilkan:

$$
x^\star.
$$

Kemudian masing-masing diteruskan ke **execution simulator yang sama**.

Ini sangat penting.

Kalau execution model berbeda, perbandingan tidak fair.

---

# F.39. Eksperimen yang benar

Kita definisikan:

$$
\mathcal A=
\{
A_{greedy},
A_{SA},
A_{exact},
A_{QAOA}
\}.
$$

Untuk setiap:

$$
A_i,
$$

gunakan:

$$
\boxed{
Data,\ Cost,\ Risk,\ Execution
}
$$

yang sama.

Kemudian ukur:

$$
Performance(A_i).
$$

---

# F.40. Metrics

Jangan hanya menggunakan profit.

Minimal:

$$
Total\ Return
$$

$$
CAGR
$$

$$
Volatility
$$

$$
Sharpe
$$

$$
Sortino
$$

$$
Max\ Drawdown
$$

$$
Calmar
$$

$$
Win\ Rate
$$

$$
Profit\ Factor
$$

$$
Turnover
$$

$$
Transaction\ Cost.
$$

---

# F.41. Sharpe Ratio

Dengan return:

$$
r_t,
$$

maka:

$$
\boxed{
Sharpe
=
\frac{
E[r-r_f]
}{
\sigma(r-r_f)
}
}
\sqrt{K}.
$$

Untuk intraday, $K$ harus dipilih sesuai frekuensi sampling secara konsisten.

---

# F.42. Maximum Drawdown

Equity:

$$
E_t.
$$

Running maximum:

$$
M_t=\max_{\tau\leq t}E_\tau.
$$

Drawdown:

$$
DD_t
=
\frac{E_t-M_t}{M_t}.
$$

Maka:

$$
\boxed{
MDD
=
\min_t DD_t.
}
$$

---

# F.43. Tetapi untuk strategi kita ada metric tambahan

Karena kita menggunakan optimizer kombinatorial:

### Solution quality

$$
Gap
=
\frac{
C(x_{\mathrm{QAOA}})
-
C(x^\star)
}{
|C(x^\star)|
}.
$$

Jika exact solution tersedia.

---

# F.44. Quantum-specific metrics

Kita bisa mengukur:

$$
Approximation\ Ratio.
$$

Untuk maximization:

$$
\boxed{
AR=
\frac{
C(x_{QAOA})
}{
C(x^\star)
}.
}
$$

Kemudian:

$$
\text{QAOA runtime}
$$

$$
\text{number of circuit evaluations}
$$

$$
\text{depth}
$$

$$
\text{shots}.
$$

---

# F.45. Ini penting untuk tesis/proyekmu

Karena kalau QAOA menghasilkan:

$$
Return=18\%
$$

sementara classical:

$$
Return=16\%,
$$

itu menarik.

Tetapi kalau QAOA membutuhkan:

$$
10^6
$$

circuit evaluations dan classical solver hanya:

$$
10^3,
$$

kita tidak bisa hanya mengatakan:

> QAOA lebih baik.

Kita harus mempertimbangkan:

$$
\boxed{
Performance
+
Computational\ Cost.
}
$$

---

# F.46. Kita dapat membuat objective eksperimental

Misalnya:

$$
\boxed{
Score
=
Sharpe
-
\lambda MDD
-
\eta TC
-
\xi ComputationalCost.
}
$$

Atau mempertahankan metrics terpisah agar tidak mencampur interpretasi.

Untuk penelitian, saya lebih menyukai **menyimpan semua metrik secara terpisah**, lalu membandingkan Pareto frontier.

---

# F.47. Pareto frontier

Misalnya kita punya:

$$
x-axis=Sharpe
$$

dan:

$$
y-axis=ComputationalCost.
$$

Kita ingin mencari solusi yang tidak didominasi:

$$
\boxed{
Pareto\ optimal.
}
$$

Ini sangat relevan untuk membandingkan:

$$
QAOA
$$

dengan:

$$
classical.
$$

---

# F.48. Stress testing

Backtest normal belum cukup.

Kita harus menguji:

### Spread meningkat

$$
Spread\rightarrow2Spread.
$$

### Slippage meningkat

$$
Slippage\rightarrow3Slippage.
$$

### Latency meningkat

$$
Latency\rightarrow5\times.
$$

### Volatility meningkat

$$
\sigma\rightarrow2\sigma.
$$

### Liquidity turun

$$
Depth\rightarrow0.5Depth.
$$

Jika strategi langsung runtuh, kita tahu strategi terlalu rapuh.

---

# F.49. Monte Carlo trade reshuffling

Misalkan kita memiliki trade returns:

$$
r_1,r_2,\dots,r_N.
$$

Kita dapat melakukan bootstrap:

$$
r_1^\star,\dots,r_N^\star.
$$

Kemudian membentuk equity curve baru.

Ulangi:

$$
B=10,000
$$

kali misalnya.

Kita mendapatkan distribusi:

$$
MDD^\star,
$$

$$
Return^\star,
$$

$$
Sharpe^\star.
$$

Bukan hanya satu angka.

---

# F.50. Probability of ruin

Jika risk per trade:

$$
R=\$1,
$$

dan capital:

$$
C_0.
$$

Kita dapat mengestimasi probabilitas:

$$
P(C_t<C_{\min}).
$$

Ini jauh lebih informatif daripada hanya melihat CAGR.

---

# F.51. Regime stress test

Karena kita memiliki:

$$
F_t=
(DXY,Gold,SPX,VIX,BTC.D,\dots),
$$

kita dapat membagi data:

$$
Regime\ 1=\text{low volatility}
$$

$$
Regime\ 2=\text{high volatility}
$$

$$
Regime\ 3=\text{risk-on}
$$

$$
Regime\ 4=\text{risk-off}.
$$

Kemudian:

$$
Performance(A|Regime_k).
$$

Ini memungkinkan kita mengetahui:

> kapan QAOA-based strategy bekerja dan kapan tidak.

---

# F.52. Ini membawa kita pada konsep yang lebih menarik

Kita sebenarnya tidak hanya menguji:

$$
QAOA\ vs Classical.
$$

Kita menguji:

$$
\boxed{
Algorithm
\times
Market\ Regime
\times
Execution\ Condition.
}
$$

Misalnya:

| Regime | QAOA | Classical |
|---|---:|---:|
| Low vol | 1.4 Sharpe | 1.3 |
| High vol | 0.8 | 0.7 |
| Risk-on | 1.8 | 1.5 |
| Risk-off | 0.5 | 0.6 |

Mungkin QAOA unggul pada regime tertentu tetapi tidak pada lainnya.

**Itu justru hasil penelitian yang jauh lebih menarik daripada klaim "quantum selalu lebih baik".**

---

# F.53. Arsitektur software yang saya sarankan

Saya akan membagi project menjadi:

```text
TradeProject/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── features/
│
├── market/
│   ├── market_state.py
│   ├── orderbook.py
│   └── factors.py
│
├── forecasting/
│   ├── returns.py
│   ├── volatility.py
│   ├── correlation.py
│   └── regime.py
│
├── optimization/
│   ├── qubo.py
│   ├── ising.py
│   ├── classical.py
│   └── qaoa.py
│
├── execution/
│   ├── order.py
│   ├── fill.py
│   ├── slippage.py
│   └── transaction_cost.py
│
├── portfolio/
│   ├── position.py
│   ├── pnl.py
│   └── risk.py
│
├── strategy/
│   ├── entry.py
│   ├── position_manager.py
│   └── exit.py
│
├── backtest/
│   ├── engine.py
│   ├── events.py
│   └── simulator.py
│
├── validation/
│   ├── walk_forward.py
│   ├── stress_test.py
│   └── monte_carlo.py
│
└── experiments/
    ├── qaoa_vs_classical.py
    └── regime_analysis.py
```

Ini jauh lebih baik daripada satu file besar yang berisi seluruh algoritma.

---

# F.54. Event loop utama

Secara matematis:

$$
\boxed{
\mathcal S_{t+1}
=
\mathcal T(
\mathcal S_t,
e_t,
a_t
)
}
$$

dengan:

$$
\mathcal T
$$

sebagai transition function.

Secara konseptual:

```text
initialize()

for event in chronological_events:

    update_market(event)

    update_orders(event)

    process_fills(event)

    update_positions(event)

    update_pnl(event)

    update_risk(event)

    if decision_time(event):

        state = build_state()

        forecast = model(state)

        optimization = optimizer(forecast)

        orders = strategy(optimization)

        submit_or_modify(orders)

    record_state()
```

---

# F.55. Ini adalah "digital twin" kecil dari trading system kita

Kita sebenarnya sedang membuat:

$$
\boxed{
\text{Market Simulator}
}
$$

yang memungkinkan kita bertanya:

> "Apa yang akan terjadi jika algoritma ini benar-benar beroperasi?"

Tanpa harus mempertaruhkan uang nyata.

---

# F.56. Namun ada satu hal yang belum kita selesaikan

**Data order book historis.**

Jika kita ingin benar-benar melakukan:

$$
order\ placement
+
queue\ position
+
partial\ fill,
$$

OHLCV saja tidak cukup.

Idealnya kita memiliki:

$$
L2/L3\ order book.
$$

Misalnya:

$$
Bid:
\begin{cases}
100.00:100\\
99.99:150\\
99.98:300
\end{cases}
$$

dan:

$$
Ask:
\begin{cases}
100.01:120\\
100.02:200\\
100.03:350
\end{cases}.
$$

Dari sini kita dapat menghitung:

$$
OBI
=
\frac{
V_{bid}-V_{ask}
}{
V_{bid}+V_{ask}
}.
$$

---

# F.57. Order Book Imbalance

$$
\boxed{
OBI_t
=
\frac{
\sum_{i=1}^{k}B_i
-
\sum_{i=1}^{k}A_i
}{
\sum_{i=1}^{k}B_i
+
\sum_{i=1}^{k}A_i
}.
}
$$

Dengan:

$$
-1\leq OBI\leq1.
$$

Jika:

$$
OBI\rightarrow1,
$$

bid dominance.

Jika:

$$
OBI\rightarrow-1,
$$

ask dominance.

Ini bisa menjadi feature untuk:

$$
\mu_t.
$$

---

# F.58. Tetapi kita jangan langsung melompat ke L2

Untuk **versi pertama sistem**, saya justru menyarankan tiga tingkat fidelity.

### Level 1 — Research backtest

Gunakan:

$$
OHLCV.
$$

Model:

$$
spread,
slippage
$$

secara parametrik.

---

### Level 2 — Execution-aware backtest

Tambahkan:

$$
Bid/Ask,
volume,
trade\ data.
$$

---

### Level 3 — Microstructure simulator

Tambahkan:

$$
L2/L3,
queue,
partial\ fill,
latency.
$$

Dengan demikian kita tidak membuat sistem terlalu kompleks sebelum fondasinya tervalidasi.

---

# F.59. Urutan implementasi yang saya rekomendasikan

Jangan langsung membuat semuanya.

Kita lakukan:

$$
\boxed{F_1}
$$

Historical data engine.

↓

$$
\boxed{F_2}
$$

Event engine.

↓

$$
\boxed{F_3}
$$

Order simulator.

↓

$$
\boxed{F_4}
$$

Position/PnL engine.

↓

$$
\boxed{F_5}
$$

Risk engine.

↓

$$
\boxed{F_6}
$$

Dynamic position management.

↓

$$
\boxed{F_7}
$$

Walk-forward validation.

↓

$$
\boxed{F_8}
$$

QAOA vs classical experiment.

---

# F.60. Hubungan Tahap A–F

Sekarang keseluruhan sistem kita mulai terlihat sangat jelas:

```text
                    ┌─────────────────┐
                    │ Historical Data │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │   A: State      │
                    │   Estimation    │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ B: Forecasting  │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ C: Financial    │
                    │    Objective    │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ D: QUBO / Ising │
                    │ QAOA / Classical│
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Trade Candidate │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ E: Position     │
                    │    Management   │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ F: Execution    │
                    │    Simulator    │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ New Market State│
                    └────────┬────────┘
                             │
                             └──────────────→ A
```

Jadi sistemnya **closed-loop**.

---

# F.61. Satu prinsip yang saya ingin kita pegang

Jangan mengoptimalkan:

$$
\boxed{
\text{historical profit}.
}
$$

Yang harus kita optimalkan adalah:

$$
\boxed{
\text{robust decision-making under uncertainty}.
}
$$

Karena tujuan akhirnya bukan:

> menemukan parameter yang paling cocok dengan masa lalu.

Tetapi:

> menemukan algoritma yang tetap masuk akal ketika kondisi pasar berubah.

---

# F.62. Dan di sinilah proyek ini mulai menjadi penelitian quantitative trading yang serius

Kita nantinya bisa menguji beberapa hipotesis:

### H1

Apakah factor-aware forecasting lebih baik daripada price-only forecasting?

$$
H_1:
\quad
Performance(X,F)>Performance(X).
$$

### H2

Apakah combinatorial optimization lebih baik daripada greedy selection?

$$
H_2:
\quad
J(x_{\mathrm{QUBO}})
>
J(x_{\mathrm{greedy}}).
$$

### H3

Apakah QAOA mendekati solusi classical/exact?

$$
H_3:
\quad
AR_{\mathrm{QAOA}}\approx1.
$$

### H4

Apakah dynamic position management meningkatkan risk-adjusted return?

$$
H_4:
\quad
Sharpe_{\mathrm{dynamic}}
>
Sharpe_{\mathrm{static}}.
$$

### H5

Apakah keunggulan QAOA tetap ada setelah transaction cost dan slippage?

$$
H_5:
\quad
J_{\mathrm{QAOA}}^{net}
>
J_{\mathrm{classical}}^{net}.
$$

**H5 justru merupakan salah satu eksperimen terpenting.**

Karena sebuah metode bisa terlihat unggul sebelum biaya eksekusi, tetapi keunggulannya hilang setelah biaya dimasukkan.

---

# F.63. Posisi kita sekarang

Dengan Tahap F selesai secara desain, pipeline kita sudah menjadi:

$$
\boxed{
\begin{aligned}
&\text{Market/Fundamental Data}\\
&\downarrow\\
&\text{Point-in-Time State}\\
&\downarrow\\
&\text{Factor + Statistical Forecast}\\
&\downarrow\\
&\text{Risk-Aware Financial Objective}\\
&\downarrow\\
&\text{QUBO/Ising}\\
&\downarrow\\
&\text{QAOA / Classical Optimization}\\
&\downarrow\\
&\text{Entry + SL + TP}\\
&\downarrow\\
&\text{Event-Driven Execution}\\
&\downarrow\\
&\text{Dynamic Position Management}\\
&\downarrow\\
&\text{Walk-Forward Backtest}\\
&\downarrow\\
&\text{Statistical Validation}\\
&\downarrow\\
&\text{QAOA vs Classical}
\end{aligned}
}
$$

Dan ada satu hal yang menurut saya **sengaja harus kita tahan dulu**: jangan langsung menghubungkan ini ke Binance atau broker nyata.

Tahap berikutnya, **Tahap G**, sebaiknya kita gunakan untuk membangun **mathematical specification dari seluruh objective function dan QUBO final**—termasuk bagaimana **expected return, covariance, factor exposure (DXY/gold/SPX/BTC/ETH), transaction cost, turnover, position constraints, dan risk budget** semuanya masuk ke satu formulasi:

$$
\boxed{
\min_{x\in\{0,1\}^N}x^TQx
}
$$

lalu diturunkan secara eksplisit sampai menjadi **Ising Hamiltonian**

$$
\boxed{
H_C
=
\sum_i h_i Z_i+
\sum_{i<j}J_{ij}Z_iZ_j
}
$$

yang benar-benar bisa kita masukkan ke **QAOA**.

Itu akan menjadi titik di mana seluruh pembahasan quantitative finance kita bertemu langsung dengan quantum computing yang sudah kamu pelajari.

## Prompt:
8/17/2026, 9:49:12 PM

lanjut Tahap G

## Response:
8/17/2026, 9:49:14 PM

Baik. **Tahap G adalah titik di mana seluruh arsitektur yang kita bangun mulai dipadatkan menjadi satu formulasi matematis yang benar-benar bisa dieksekusi oleh QAOA.**

Sampai Tahap F kita sudah punya banyak komponen:

$$
\text{market data}
\rightarrow
\text{state}
\rightarrow
\text{forecast}
\rightarrow
\text{risk}
\rightarrow
\text{candidate trades}
\rightarrow
\text{execution}
\rightarrow
\text{dynamic management}.
$$

Sekarang kita harus menjawab pertanyaan yang jauh lebih fundamental:

> **"Sebenarnya apa tepatnya yang sedang dioptimalkan oleh QAOA?"**

Dan kita akan membangun jawabannya dari **objective finansial → binary decision → QUBO → Ising Hamiltonian → QAOA**.

---

# Tahap G — Mathematical Formulation of the Trading Optimization Problem

Saya akan membaginya menjadi:

1. mendefinisikan universe aset,
2. mendefinisikan keputusan trading,
3. expected return,
4. covariance/risk,
5. market factors,
6. transaction cost,
7. turnover,
8. exposure constraints,
9. risk budget,
10. mengubah semuanya menjadi QUBO,
11. mapping QUBO → Ising,
12. membentuk cost Hamiltonian,
13. membentuk mixer,
14. QAOA,
15. interpretasi output QAOA sebagai trade.

---

# G.1. Universe aset

Misalkan pada waktu $t$ kita memiliki:

$$
N
$$

aset.

Kita definisikan:

$$
\mathcal A=
\{1,2,\ldots,N\}.
$$

Contoh untuk crypto:

$$
\mathcal A=
\{
BTC,ETH,SOL,BNB,XRP,\ldots
\}.
$$

Untuk saham:

$$
\mathcal A=
\{
AAPL,MSFT,NVDA,AMZN,\ldots
\}.
$$

Tetapi sistem kita juga mempunyai **factor assets**.

Misalnya:

$$
F=
\{
DXY,
Gold,
SPX,
VIX
\}.
$$

Untuk crypto:

$$
F=
\{
BTC,
ETH,
BTC.D,
ETH/BTC
\}.
$$

---

# G.2. Keputusan pertama: apakah aset dipilih?

Kita definisikan binary variable:

$$
\boxed{
x_i\in\{0,1\}
}
$$

dengan:

$$
x_i=
\begin{cases}
1,&\text{aset }i\text{ diperdagangkan},\\
0,&\text{tidak}.
\end{cases}
$$

Jadi:

$$
x=
(x_1,x_2,\ldots,x_N).
$$

Contoh:

$$
x=
\begin{bmatrix}
1\\
0\\
1\\
0
\end{bmatrix}.
$$

Artinya:

$$
A_1,A_3
$$

dipilih.

---

# G.3. Tetapi trading bukan sekadar "dipilih/tidak"

Kita membutuhkan arah.

Karena:

$$
BUY\neq SELL.
$$

Ada dua pendekatan.

## Pendekatan A — dua binary variables

Definisikan:

$$
b_i\in\{0,1\}
$$

untuk BUY,

dan:

$$
s_i\in\{0,1\}
$$

untuk SELL.

Dengan constraint:

$$
\boxed{
b_i+s_i\leq1.
}
$$

---

## Pendekatan B — spin

Kita dapat menggunakan:

$$
z_i\in\{-1,0,+1\}.
$$

dengan:

$$
z_i=
\begin{cases}
+1,&BUY\\
0,&FLAT\\
-1,&SELL.
\end{cases}
$$

Namun:

$$
z_i\in\{-1,0,+1\}
$$

bukan binary.

Karena QUBO secara natural menggunakan:

$$
x_i\in\{0,1\},
$$

saya menyarankan untuk **versi pertama menggunakan dua binary variables**.

---

# G.4. Representasi BUY/SELL

Kita punya:

$$
b_i,s_i\in\{0,1\}.
$$

Net direction:

$$
\boxed{
d_i=b_i-s_i.
}
$$

Maka:

$$
d_i\in\{-1,0,+1\}.
$$

Contoh:

| $b_i$ | $s_i$ | $d_i$ |
|---:|---:|---:|
| 0 | 0 | 0 |
| 1 | 0 | +1 |
| 0 | 1 | −1 |
| 1 | 1 | 0* |

Tetapi kombinasi:

$$
b_i=s_i=1
$$

harus dilarang.

---

# G.5. Constraint arah

Kita tambahkan:

$$
b_i+s_i\leq1.
$$

Dalam QUBO kita bisa menulis penalti:

$$
\boxed{
P_{\mathrm{dir}}
\sum_i b_is_i.
}
$$

Karena jika:

$$
b_i=s_i=1,
$$

maka:

$$
b_is_i=1
$$

dan sistem menerima penalti.

---

# G.6. Expected return

Sekarang kita membutuhkan:

$$
\mu_i(t).
$$

Ini bukan sekadar historical mean.

Kita definisikan:

$$
\boxed{
\mu_t=
E[r_{t+\Delta}\mid S_t].
}
$$

Jadi:

$$
\mu_t=
\begin{bmatrix}
\mu_1\\
\mu_2\\
\vdots\\
\mu_N
\end{bmatrix}.
$$

Nilainya dapat berasal dari model forecasting Tahap B.

Misalnya:

$$
\mu_i
=
\alpha_i
+
\beta_i^TF_t
+
\theta_i^TX_{i,t}.
$$

---

# G.7. Apa arti $\mu_i$?

Misalkan:

$$
\mu_{BTC}=0.002.
$$

Artinya model memperkirakan:

$$
E[r_{BTC,t+\Delta}]
=
0.2\%.
$$

Jika:

$$
\mu_i<0,
$$

maka LONG tidak menarik.

Tetapi SHORT mungkin menarik.

Karena expected directional return adalah:

$$
\boxed{
d_i\mu_i.
}
$$

Jika:

$$
d_i=-1
$$

dan:

$$
\mu_i=-0.002,
$$

maka:

$$
d_i\mu_i
=
(+0.002).
$$

Jadi SHORT mendapatkan expected return positif.

---

# G.8. Expected return objective

Kita ingin:

$$
\max_d
\sum_i d_i\mu_i.
$$

Karena QUBO biasanya ditulis sebagai minimization, kita ubah menjadi:

$$
\boxed{
C_{\mathrm{return}}
=
-\sum_i\mu_i(b_i-s_i).
}
$$

---

# G.9. Risk

Sekarang kita memasukkan covariance.

$$
\Sigma
=
E[
(r-\mu)(r-\mu)^T
].
$$

Dengan:

$$
\Sigma_{ij}
=
Cov(r_i,r_j).
$$

---

# G.10. Portfolio risk

Jika:

$$
d=
(d_1,\ldots,d_N)^T,
$$

maka:

$$
\boxed{
\sigma_p^2
=
d^T\Sigma d.
}
$$

Ekspansi:

$$
\sigma_p^2
=
\sum_i\sum_j
d_i\Sigma_{ij}d_j.
$$

Karena:

$$
d_i=b_i-s_i,
$$

maka:

$$
\sigma_p^2
=
(b-s)^T
\Sigma
(b-s).
$$

---

# G.11. Ini adalah sumber coupling QUBO

Perhatikan:

$$
d^T\Sigma d.
$$

Ada:

$$
d_id_j.
$$

Artinya keputusan memilih aset $i$ bergantung pada apakah kita juga memilih aset $j$.

Inilah struktur:

$$
\boxed{
\text{combinatorial interaction}.
}
$$

Dan ini alasan mengapa QUBO/Ising menjadi relevan.

---

# G.12. Objective dasar Markowitz

Kita dapat menggunakan:

$$
\boxed{
C(d)
=
-\mu^Td
+
\lambda d^T\Sigma d.
}
$$

Dengan:

$$
\lambda>0.
$$

Semakin besar:

$$
\lambda,
$$

semakin risk-averse.

---

# G.13. Tetapi trading kita tidak boleh berhenti di Markowitz

Kita ingin:

$$
DXY,
Gold,
SPX,
VIX,
BTC.D,\ldots
$$

masuk ke model.

Ada dua cara.

Cara pertama:

factor sudah masuk ke:

$$
\mu_t.
$$

Tetapi itu belum cukup.

Kita juga ingin mengendalikan **factor exposure**.

---

# G.14. Factor model

Kita definisikan:

$$
r_i
=
\alpha_i+
\beta_i^Tf+\epsilon_i.
$$

Dengan:

$$
f=
(f_1,\ldots,f_K)^T.
$$

Untuk aset $i$:

$$
\beta_i=
(\beta_{i1},\ldots,\beta_{iK}).
$$

Kita susun:

$$
B=
\begin{bmatrix}
\beta_{11}&\beta_{12}&\cdots&\beta_{1K}\\
\beta_{21}&\beta_{22}&\cdots&\beta_{2K}\\
\vdots&\vdots&\ddots&\vdots\\
\beta_{N1}&\beta_{N2}&\cdots&\beta_{NK}
\end{bmatrix}.
$$

---

# G.15. Portfolio factor exposure

$$
\boxed{
E_f=B^Td.
}
$$

Untuk factor $k$:

$$
E_k
=
\sum_i\beta_{ik}d_i.
$$

---

# G.16. Mengapa ini berguna?

Misalnya kita memiliki:

$$
\beta_{DXY,BTC}=-0.7.
$$

Jika kita LONG BTC:

$$
d_{BTC}=+1,
$$

maka:

$$
E_{DXY}<0.
$$

Artinya portfolio kita memiliki negative DXY exposure.

Jika model macro mengatakan:

$$
DXY\uparrow
$$

dengan kuat, kita mungkin ingin mengurangi exposure tersebut.

---

# G.17. Factor exposure constraint

Misalnya kita tidak ingin:

$$
|E_{DXY}|>E_{\max}.
$$

Secara matematis:

$$
-E_{\max}
\leq
B_{DXY}^Td
\leq
E_{\max}.
$$

Namun QUBO lebih mudah menggunakan squared penalty:

$$
\boxed{
P_F
(B_{DXY}^Td-E_{DXY}^{target})^2.
}
$$

---

# G.18. Multi-factor penalty

Untuk semua factor:

$$
\boxed{
C_F
=
\sum_{k=1}^{K}
P_k
\left(
\beta_k^Td
-
e_k^\star
\right)^2.
}
$$

Di mana:

$$
e_k^\star
$$

adalah target exposure.

Contoh:

$$
e_{DXY}^\star=0.
$$

Artinya kita ingin portfolio market-neutral terhadap DXY.

---

# G.19. Ini menarik untuk strategi global

Misalnya kita trading:

$$
AAPL,\ NVDA,\ AMD,\ TSLA.
$$

Model menemukan semua expected return positif.

Naifnya:

$$
LONG\ AAPL,NVDA,AMD,TSLA.
$$

Tetapi semuanya mungkin mempunyai:

$$
\beta_{SPX}>0.
$$

Maka portfolio sebenarnya hanya satu taruhan:

$$
\text{US equity risk-on}.
$$

Factor penalty mencegah optimizer menganggap keempatnya sebagai empat sumber alpha yang independen.

---

# G.20. Risk decomposition

Covariance juga dapat ditulis melalui factor model:

$$
\boxed{
\Sigma
=
BFB^T+D
}
$$

dengan:

$$
F=\text{factor covariance}
$$

dan:

$$
D=\text{idiosyncratic covariance}.
$$

Maka:

$$
d^T\Sigma d
=
d^TBFB^Td+d^TDd.
$$

Sehingga:

$$
\boxed{
Risk=
FactorRisk+IdiosyncraticRisk.
}
$$

Ini jauh lebih informatif daripada covariance matrix mentah.

---

# G.21. Transaction cost

Sekarang kita masukkan biaya.

Untuk aset $i$:

$$
c_i
=
fee_i
+
spread_i
+
slippage_i
+
impact_i.
$$

Jika kita hanya mempertimbangkan apakah aset ditradingkan:

$$
C_{TC}
=
\sum_i c_i(b_i+s_i).
$$

---

# G.22. Tetapi kita juga ingin turnover

Misalkan posisi sebelumnya:

$$
d_i^{prev}.
$$

Kita tidak ingin optimizer setiap periode berubah total.

Definisikan:

$$
\Delta d_i
=
d_i-d_i^{prev}.
$$

Transaction cost lebih tepat:

$$
\boxed{
C_{TC}
=
\sum_i c_i|\Delta d_i|.
}
$$

Masalahnya:

$$
|\cdot|
$$

tidak quadratic.

Untuk versi binary sederhana kita bisa mengaproksimasi dengan penalti switching.

Misalnya jika posisi sebelumnya LONG:

$$
b_i^{prev}=1,
$$

maka pindah ke FLAT/SHORT diberi biaya.

---

# G.23. Binary switching penalty

Salah satu bentuk sederhana:

$$
\boxed{
C_{\mathrm{switch}}
=
P_{switch}
\sum_i
(b_i-b_i^{prev})^2
+
(s_i-s_i^{prev})^2.
}
$$

Karena:

$$
x^2=x
$$

untuk binary variable, ekspansi menjadi quadratic.

---

# G.24. Kenapa turnover penting?

Tanpa turnover penalty:

$$
\lambda_{\mathrm{turnover}}=0,
$$

optimizer mungkin melakukan:

$$
LONG
\rightarrow
SHORT
\rightarrow
LONG
\rightarrow
SHORT
$$

setiap periode kecil.

Secara teori terlihat optimal.

Secara nyata:

$$
TC\rightarrow\text{besar}.
$$

Jadi:

$$
\boxed{
\text{alpha harus mengalahkan trading cost}.
}
$$

---

# G.25. Cardinality constraint

Kita mungkin tidak ingin 50 aset sekaligus.

Misalnya maksimal:

$$
K=5.
$$

Maka:

$$
\boxed{
\sum_i(b_i+s_i)\leq K.
}
$$

---

# G.26. Mengubah cardinality menjadi penalty

Kita bisa menggunakan:

$$
\boxed{
C_K
=
P_K
\left(
\sum_i(b_i+s_i)-K
\right)^2.
}
$$

Tetapi hati-hati.

Bentuk ini memberikan minimum ketika jumlah posisi tepat:

$$
K,
$$

bukan:

$$
\leq K.
$$

Jika kita benar-benar ingin "maksimal $K$", formulasi QUBO perlu auxiliary variables atau bentuk penalty yang sesuai.

Untuk versi awal, justru kita dapat menggunakan:

$$
\sum_i(b_i+s_i)=K.
$$

Misalnya:

> pilih tepat 5 kandidat trade.

---

# G.27. Budget constraint

Misalkan setiap aset membutuhkan capital:

$$
w_i.
$$

Kita ingin:

$$
\sum_iw_i(b_i+s_i)
=
W.
$$

Penalty:

$$
\boxed{
C_W
=
P_W
\left(
\sum_iw_i(b_i+s_i)-W
\right)^2.
}
$$

---

# G.28. Risk budget

Kita ingin:

$$
d^T\Sigma d
\leq
R_{\max}.
$$

Ini merupakan constraint quadratic yang agak lebih sulit.

Untuk binary QUBO, ada dua pendekatan.

### Pendekatan pertama

Masukkan risk langsung ke objective:

$$
\lambda d^T\Sigma d.
$$

### Pendekatan kedua

Gunakan auxiliary/slack variables untuk mengubah inequality menjadi equality.

Untuk versi pertama, saya menyarankan pendekatan pertama.

---

# G.29. Objective lengkap versi pertama

Sekarang kita sudah memiliki:

$$
\boxed{
C=
C_{\mathrm{return}}
+
C_{\mathrm{risk}}
+
C_{\mathrm{factor}}
+
C_{\mathrm{TC}}
+
C_{\mathrm{cardinality}}
+
C_{\mathrm{direction}}
+
C_{\mathrm{switch}}.
}
$$

Mari kita tulis semuanya.

---

# G.30. Full binary formulation

Dengan:

$$
d=b-s,
$$

kita definisikan:

$$
\boxed{
\begin{aligned}
C(b,s)
={}&
-\mu^T(b-s)
\\
&+
\lambda(b-s)^T\Sigma(b-s)
\\
&+
\sum_k
P_k
\left[
\beta_k^T(b-s)-e_k^\star
\right]^2
\\
&+
\sum_i c_i(b_i+s_i)
\\
&+
P_{\mathrm{dir}}
\sum_i b_is_i
\\
&+
P_{\mathrm{card}}
\left[
\sum_i(b_i+s_i)-K
\right]^2
\\
&+
P_{\mathrm{switch}}
\sum_i
\left[
(b_i-b_i^{prev})^2
+
(s_i-s_i^{prev})^2
\right].
\end{aligned}
}
$$

dengan:

$$
b_i,s_i\in\{0,1\}.
$$

**Inilah inti mathematical specification sistem kita.**

---

# G.31. Kenapa fungsi ini adalah QUBO?

Karena semua komponennya maksimal quadratic.

Bentuk umum:

$$
\boxed{
C(x)
=
x^TQx+c^Tx+c_0.
}
$$

dengan:

$$
x=
\begin{bmatrix}
b_1\\
\vdots\\
b_N\\
s_1\\
\vdots\\
s_N
\end{bmatrix}.
$$

Karena:

$$
x_i\in\{0,1\},
$$

maka ini adalah:

$$
\boxed{
\text{QUBO}.
}
$$

---

# G.32. Sekarang kita turunkan matrix $Q$

Ini bagian penting.

Misalkan:

$$
d=b-s.
$$

Risk term:

$$
d^T\Sigma d.
$$

Ekspansi:

$$
(b-s)^T\Sigma(b-s).
$$

Maka:

$$
=
b^T\Sigma b
-
b^T\Sigma s
-
s^T\Sigma b
+
s^T\Sigma s.
$$

Karena:

$$
\Sigma=\Sigma^T,
$$

maka:

$$
b^T\Sigma s
=
s^T\Sigma b.
$$

Sehingga:

$$
\boxed{
d^T\Sigma d
=
b^T\Sigma b
-
2b^T\Sigma s
+
s^T\Sigma s.
}
$$

---

# G.33. Matrix block structure

Maka risk matrix memiliki struktur:

$$
\boxed{
Q_{\mathrm{risk}}
=
\lambda
\begin{bmatrix}
\Sigma&-\Sigma\\
-\Sigma&\Sigma
\end{bmatrix}.
}
$$

Ini sangat elegan.

Bagian:

$$
\Sigma
$$

menghubungkan BUY-BUY.

Bagian:

$$
-\Sigma
$$

menghubungkan BUY-SELL.

---

# G.34. Return term

Kita memiliki:

$$
-\mu^T(b-s).
$$

Sehingga:

$$
-\mu^Tb+\mu^Ts.
$$

Linear coefficient:

$$
\boxed{
q_b=-\mu
}
$$

dan:

$$
\boxed{
q_s=+\mu.
}
$$

---

# G.35. Factor penalty

Untuk satu factor:

$$
P_F(\beta^Td-e^\star)^2.
$$

Dengan:

$$
d=b-s.
$$

Definisikan:

$$
a=
\begin{bmatrix}
\beta\\
-\beta
\end{bmatrix}.
$$

Maka:

$$
\beta^Td
=
a^Tx.
$$

Sehingga:

$$
P_F(a^Tx-e^\star)^2.
$$

Ekspansi:

$$
P_F
[
x^Taa^Tx
-
2e^\star a^Tx
+
(e^\star)^2
].
$$

Jadi quadratic contribution:

$$
\boxed{
Q_F=P_Faa^T.
}
$$

---

# G.36. Ini berarti factor exposure menciptakan coupling

Jika:

$$
\beta_i\neq0
$$

dan:

$$
\beta_j\neq0,
$$

maka:

$$
\beta_i\beta_j
$$

menghasilkan:

$$
x_ix_j.
$$

Jadi factor neutrality juga menghasilkan:

$$
\boxed{
\text{quadratic interaction}.
}
$$

---

# G.37. Cardinality penalty

Misalkan:

$$
y_i=b_i+s_i.
$$

Kemudian:

$$
P_K
\left(
\sum_i y_i-K
\right)^2.
$$

Ekspansi:

$$
P_K
\left[
\sum_i y_i^2
+
2\sum_{i<j}y_iy_j
-
2K\sum_i y_i
+
K^2
\right].
$$

Karena:

$$
y_i^2=y_i
$$

jika $y_i$ binary hanya bila $y_i$ sendiri binary; tetapi:

$$
y_i=b_i+s_i
$$

dapat bernilai 2 jika constraint direction belum diberlakukan.

Lebih aman mengekspansi langsung $b,s$.

---

# G.38. Direction constraint

$$
P_{\mathrm{dir}}\sum_i b_is_i.
$$

Mudah:

$$
Q_{b_is_i}
\mathrel{+}=P_{\mathrm{dir}}.
$$

Jadi:

$$
b_i=s_i=1
$$

menjadi mahal.

---

# G.39. Switching penalty

Misalnya:

$$
P_s(b_i-b_i^{prev})^2.
$$

Karena:

$$
b_i^2=b_i,
$$

maka:

$$
=
P_s[
b_i
-2b_i b_i^{prev}
+
(b_i^{prev})^2
].
$$

Karena:

$$
b_i^{prev}\in\{0,1\},
$$

maka:

$$
\boxed{
q_i
\mathrel{+}=
P_s(1-2b_i^{prev}).
}
$$

Jadi posisi sebelumnya mempengaruhi linear coefficient.

Ini berarti QUBO kita **dinamis**.

---

# G.40. QUBO pada setiap waktu

Pada setiap:

$$
t,
$$

kita memiliki:

$$
\boxed{
Q_t
=
Q(
\mu_t,
\Sigma_t,
B_t,
TC_t,
d_{t-1}
).
}
$$

Jadi:

$$
Q_{t_1}\neq Q_{t_2}
$$

secara umum.

Ini merupakan konsekuensi langsung dari dynamic optimization yang kita bahas di Tahap E.

---

# G.41. Sekarang kita masuk ke Ising

QAOA bekerja secara natural dengan:

$$
Z_i
$$

yang memiliki eigenvalue:

$$
z_i\in\{-1,+1\}.
$$

Sedangkan QUBO menggunakan:

$$
x_i\in\{0,1\}.
$$

Gunakan mapping:

$$
\boxed{
x_i=\frac{1-z_i}{2}.
}
$$

atau:

$$
\boxed{
z_i=1-2x_i.
}
$$

---

# G.42. Mengubah linear term

Misalkan:

$$
c_ix_i.
$$

Dengan:

$$
x_i=\frac{1-z_i}{2},
$$

maka:

$$
c_ix_i
=
\frac{c_i}{2}
-
\frac{c_i}{2}z_i.
$$

Jadi:

$$
\boxed{
c_ix_i
\rightarrow
\frac{c_i}{2}
-
\frac{c_i}{2}Z_i.
}
$$

---

# G.43. Quadratic term

Misalkan:

$$
Q_{ij}x_ix_j.
$$

Substitusi:

$$
x_ix_j
=
\frac{(1-z_i)(1-z_j)}{4}.
$$

Maka:

$$
=
\frac14
(
1-z_i-z_j+z_iz_j
).
$$

Jadi:

$$
\boxed{
Q_{ij}x_ix_j
\rightarrow
\frac{Q_{ij}}4
(1-Z_i-Z_j+Z_iZ_j).
}
$$

---

# G.44. Maka Hamiltonian

Secara umum:

$$
C(x)=x^TQx+c^Tx+c_0.
$$

menjadi:

$$
\boxed{
H_C
=
C_0I
+
\sum_i h_iZ_i
+
\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

Konstanta:

$$
C_0
$$

tidak memengaruhi argmin.

---

# G.45. Koefisien Ising

Tergantung konvensi apakah $Q$ menyimpan faktor dua pada off-diagonal, tetapi secara konseptual:

$$
\boxed{
J_{ij}\propto Q_{ij}.
}
$$

Sedangkan:

$$
\boxed{
h_i
}
$$

berasal dari kombinasi:

- linear QUBO coefficient,
- quadratic couplings yang melibatkan $i$.

Untuk implementasi nanti kita harus memilih **satu konvensi matrix Q** dan tidak boleh mencampurnya.

Ini penting sekali karena kesalahan faktor 2 adalah salah satu bug paling umum ketika mengubah QUBO ke Ising.

---

# G.46. Cost Hamiltonian

Kita akhirnya memperoleh:

$$
\boxed{
\hat H_C
=
\sum_i h_i Z_i
+
\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

Jika computational basis:

$$
|z\rangle
=
|z_1z_2\cdots z_n\rangle,
$$

maka:

$$
\hat H_C|z\rangle
=
C(z)|z\rangle.
$$

Artinya:

$$
\boxed{
\text{eigenvalue Hamiltonian}
=
\text{cost trading decision}.
}
$$

Ini adalah koneksi langsung antara quantum mechanics dan optimization problem kita.

---

# G.47. Interpretasi fisiknya

Misalkan:

$$
h_i<0.
$$

Maka sistem cenderung memilih:

$$
Z_i=+1
$$

atau, tergantung mapping yang kita gunakan:

$$
x_i=0.
$$

Sebaliknya jika:

$$
h_i>0,
$$

kecenderungannya berbeda.

Tetapi keputusan akhir tidak hanya ditentukan oleh:

$$
h_i.
$$

Ada:

$$
J_{ij}.
$$

Jadi aset tidak berdiri sendiri.

---

# G.48. Coupling $J_{ij}$

Misalnya:

$$
J_{ij}>0.
$$

Term:

$$
J_{ij}Z_iZ_j
$$

cenderung meminimalkan energi ketika:

$$
Z_iZ_j=-1.
$$

Artinya konfigurasi anti-aligned.

Sedangkan:

$$
J_{ij}<0
$$

cenderung:

$$
Z_iZ_j=+1.
$$

Ini memberikan interpretasi Ising.

Dalam konteks trading, coupling dapat berasal dari:

- covariance,
- factor exposure,
- cardinality,
- transaction cost,
- constraints.

Jadi:

$$
\boxed{
J_{ij}
\text{ bukan hanya correlation.}
}
$$

Ia merupakan gabungan seluruh interaksi dalam objective.

---

# G.49. Cost Hamiltonian bukan portfolio Hamiltonian murni

Ini penting.

Kita jangan mengatakan:

$$
J_{ij}=\text{correlation}.
$$

Lebih tepat:

$$
\boxed{
J_{ij}
=
f(
\Sigma_{ij},
\beta_i,
\beta_j,
constraints,
costs,
\ldots
).
}
$$

---

# G.50. QAOA

Sekarang kita mempunyai:

$$
\hat H_C.
$$

QAOA menggunakan mixer:

$$
\boxed{
\hat H_M
=
\sum_i X_i.
}
$$

Untuk unconstrained binary optimization.

---

# G.51. Initial state

Kita mulai dengan:

$$
|+\rangle^{\otimes n}.
$$

Dengan:

$$
|+\rangle
=
\frac{|0\rangle+|1\rangle}{\sqrt2}.
$$

Sehingga:

$$
|\psi_0\rangle
=
\frac{1}{\sqrt{2^n}}
\sum_{x\in\{0,1\}^n}
|x\rangle.
$$

Artinya seluruh kandidat trading decision memiliki amplitude awal yang sama.

---

# G.52. QAOA layer

Untuk:

$$
p
$$

layers:

$$
\boxed{
|\psi(\boldsymbol\gamma,\boldsymbol\beta)\rangle
=
\prod_{l=1}^{p}
e^{-i\beta_lH_M}
e^{-i\gamma_lH_C}
|\psi_0\rangle.
}
$$

Urutannya:

$$
U_C(\gamma)
=
e^{-i\gamma H_C}
$$

kemudian:

$$
U_M(\beta)
=
e^{-i\beta H_M}.
$$

---

# G.53. Mengapa cost Hamiltonian tidak mengubah probabilitas langsung?

Karena:

$$
U_C
$$

di computational basis hanya memberikan phase:

$$
|x\rangle
\rightarrow
e^{-i\gamma C(x)}
|x\rangle.
$$

Jadi:

$$
\boxed{
\text{cost layer}
\rightarrow
\text{phase encoding}.
}
$$

Kemudian mixer:

$$
U_M
$$

mengubah amplitudes antar state.

Interferensi antara keduanya menyebabkan state dengan cost yang lebih baik memperoleh probability lebih besar setelah parameter QAOA dioptimalkan.

---

# G.54. Objective QAOA

Kita ingin:

$$
\boxed{
E(\gamma,\beta)
=
\langle\psi(\gamma,\beta)|
H_C
|\psi(\gamma,\beta)\rangle
}
$$

seminimal mungkin.

Jadi:

$$
(\gamma^\star,\beta^\star)
=
\arg\min_{\gamma,\beta}
E(\gamma,\beta).
$$

Perhatikan:

**ini adalah optimization kedua.**

---

# G.55. Dua optimization yang sering tertukar

Optimization pertama:

$$
\boxed{
x^\star
=
\arg\min_x C(x)
}
$$

adalah **trading combinatorial optimization**.

Optimization kedua:

$$
\boxed{
(\gamma^\star,\beta^\star)
=
\arg\min_{\gamma,\beta}
\langle H_C\rangle
}
$$

adalah **variational parameter optimization**.

Jadi QAOA adalah nested optimization:

$$
\boxed{
\text{classical optimizer}
\rightarrow
(\gamma,\beta)
\rightarrow
\text{quantum circuit}
\rightarrow
\langle H_C\rangle.
}
$$

---

# G.56. Setelah QAOA

Setelah parameter optimal:

$$
(\gamma^\star,\beta^\star),
$$

kita memperoleh:

$$
|\psi^\star\rangle.
$$

Kemudian kita lakukan measurement:

$$
M
$$

shots.

Contoh:

$$
011001
$$

muncul:

$$
2,430
$$

kali.

State dengan frequency tertinggi menjadi kandidat:

$$
x^\star.
$$

---

# G.57. Contoh interpretasi

Misalkan kita memiliki 4 aset:

$$
\{BTC,ETH,SOL,BNB\}.
$$

Dengan 2 bits per asset:

$$
(b_1,b_2,b_3,b_4)
$$

dan:

$$
(s_1,s_2,s_3,s_4).
$$

Total:

$$
n=8
$$

qubits.

Misalnya hasil QAOA:

$$
b=(1,0,1,0)
$$

$$
s=(0,0,0,1).
$$

Maka:

$$
d=b-s
$$

menjadi:

$$
\boxed{
d=(1,0,1,-1).
}
$$

Interpretasi:

$$
LONG\ BTC
$$

$$
FLAT\ ETH
$$

$$
LONG\ SOL
$$

$$
SHORT\ BNB.
$$

---

# G.58. Kemudian trade constructor

QAOA **tidak langsung menghasilkan**:

$$
SL=...
$$

atau:

$$
TP=...
$$

Ia menghasilkan:

$$
\boxed{
\text{discrete trading allocation/selection}.
}
$$

Kemudian Trade Construction Engine menggunakan:

$$
S_t
$$

untuk menentukan:

$$
Entry_i,
SL_i,
TP_i,
q_i.
$$

---

# G.59. Ini pembagian kerja yang sangat penting

### QAOA

Menjawab:

> **Apa yang harus diperdagangkan?**

### Classical risk/position optimizer

Menjawab:

> **Seberapa besar?**

### Position manager

Menjawab:

> **Kapan harus mempertahankan, memodifikasi, atau keluar?**

### Execution engine

Menjawab:

> **Bagaimana order tersebut dieksekusi?**

Dengan demikian kita tidak memaksa QAOA menjadi "super algorithm" yang melakukan segala sesuatu.

---

# G.60. Position sizing

Misalkan QAOA memilih:

$$
LONG\ BTC.
$$

Trade constructor menghitung:

$$
q_i
=
\frac{R_i}
{
E[Loss_i|SL_i]
}.
$$

Jika:

$$
R_i=\$1
$$

dan:

$$
E[Loss_i|SL_i]=\$0.8
$$

maka:

$$
q_i=1.25.
$$

---

# G.61. Tetapi kita perlu portfolio risk adjustment

Jika ada tiga posisi:

$$
BTC,\ ETH,\ SOL
$$

masing-masing:

$$
R_i=\$1,
$$

tidak berarti total risk:

$$
\$3.
$$

Karena:

$$
Cov(BTC,ETH)>0.
$$

Jadi kita menghitung:

$$
\sigma_p^2
=
q^T\Sigma q.
$$

Kemudian melakukan scaling:

$$
\boxed{
q_{\mathrm{scaled}}
=
c q
}
$$

dengan:

$$
c=
\min
\left(
1,
\sqrt{
\frac{
V_{\max}
}{
q^T\Sigma q
}
}
\right).
$$

---

# G.62. Ini memberi dua lapis risk control

### Lapisan 1

QUBO:

$$
\text{risk-aware selection}.
$$

### Lapisan 2

Position sizing:

$$
\text{risk-aware allocation}.
$$

Ini jauh lebih aman daripada hanya mengandalkan optimizer.

---

# G.63. Sekarang masalah penting: discrete vs continuous

Kita sebenarnya mempunyai:

$$
w_i\in\mathbb R
$$

untuk position size.

Sedangkan QAOA bekerja dengan:

$$
x_i\in\{0,1\}.
$$

Jangan dipaksakan semuanya menjadi binary.

Saya menyarankan:

$$
\boxed{
QAOA
=
\text{asset/direction selection}
}
$$

dan:

$$
\boxed{
Classical optimizer
=
\text{continuous sizing}.
}
$$

Ini hybrid architecture yang lebih natural.

---

# G.64. Maka final architecture kita

$$
\boxed{
\begin{array}{c}
\text{Market State}\\
\downarrow\\
\mu,\Sigma,B,TC\\
\downarrow\\
\text{QUBO}\\
\downarrow\\
\text{QAOA}\\
\downarrow\\
\text{Selected Assets + Direction}\\
\downarrow\\
\text{Continuous Position Sizing}\\
\downarrow\\
Entry/SL/TP\\
\downarrow\\
\text{Execution}\\
\downarrow\\
\text{Dynamic Management}
\end{array}
}
$$

---

# G.65. Tetapi ada masalah besar yang harus kita selesaikan sebelum coding

Jumlah qubit.

Jika:

$$
N=100
$$

dan kita menggunakan:

$$
2N
$$

binary variables:

$$
n=200
$$

qubits.

QAOA simulasi statevector membutuhkan:

$$
2^{200}
$$

amplitudes.

Ini mustahil secara brute-force.

Maka kita harus menggunakan **candidate universe reduction**.

---

# G.66. Candidate selection

Jangan berikan 5,000 saham kepada QAOA.

Gunakan classical pre-filter:

$$
\mathcal A_{\mathrm{candidate}}
\subset
\mathcal A.
$$

Misalnya:

$$
5000
\rightarrow
100
\rightarrow
20.
$$

Baru:

$$
20
$$

masuk QUBO.

---

# G.67. Bagaimana memilih candidate?

Misalnya:

$$
Score_i
=
f(
\mu_i,
liquidity_i,
volatility_i,
factor\ compatibility_i
).
$$

Ambil:

$$
Top-K.
$$

Misalnya:

$$
K=12.
$$

Maka:

$$
2K=24
$$

qubits untuk direction encoding.

Ini jauh lebih realistis untuk eksperimen awal.

---

# G.68. Tetapi candidate pre-filter harus causal

Jangan menggunakan:

$$
future\ return
$$

untuk memilih candidate.

Harus:

$$
Score_i(t)
=
f(D_{\leq t}).
$$

Ini kembali ke prinsip Tahap F.

---

# G.69. Alternative encoding

Kita juga bisa menggunakan satu binary variable:

$$
x_i\in\{0,1\}
$$

dan direction ditentukan oleh sign:

$$
sign(\mu_i).
$$

Misalnya:

$$
\mu_i>0
\Rightarrow LONG,
$$

$$
\mu_i<0
\Rightarrow SHORT.
$$

Kemudian QAOA hanya memilih:

$$
x_i.
$$

Ini membutuhkan:

$$
N
$$

qubits, bukan:

$$
2N.
$$

Untuk versi awal saya sangat menyarankan **encoding ini sebagai baseline**.

---

# G.70. Formulasi simplified QUBO

Kita definisikan:

$$
d_i=s_i x_i
$$

dengan:

$$
s_i=\operatorname{sign}(\mu_i).
$$

Maka:

$$
d_i\in\{-1,0,+1\}.
$$

Tetapi karena sign sudah ditentukan:

$$
d_i=
\operatorname{sign}(\mu_i)x_i.
$$

Objective:

$$
\boxed{
C(x)
=
-\sum_i
|\mu_i|x_i
+
\lambda
\sum_{ij}
s_i s_j\Sigma_{ij}x_ix_j
+
\text{penalties}.
}
$$

Sekarang hanya:

$$
N
$$

qubits.

---

# G.71. Apa kelemahannya?

Kita tidak bisa secara independen memilih:

$$
LONG
$$

atau:

$$
SHORT.
$$

Direction ditentukan oleh forecast.

Namun ini justru dapat menjadi **baseline QAOA pertama yang sangat bersih**.

Kemudian kita bandingkan dengan:

$$
2N
$$

direction-aware formulation.

---

# G.72. Saya menyarankan eksperimen bertahap

### Model G1

Asset selection only.

$$
N\text{ qubits}.
$$

Direction berasal dari forecast.

---

### Model G2

Asset + direction.

$$
2N\text{ qubits}.
$$

---

### Model G3

Asset + direction + cardinality.

---

### Model G4

Asset + direction + factor exposure.

---

### Model G5

Full formulation:

$$
return
+
risk
+
factor
+
cost
+
turnover
+
constraints.
$$

Dengan demikian kita dapat melihat kontribusi setiap komponen.

---

# G.73. Ini sangat penting untuk eksperimen ilmiah

Kalau kita langsung memasukkan:

$$
20
$$

constraint sekaligus dan performanya buruk, kita tidak tahu penyebabnya.

Dengan ablation study:

$$
G1
\rightarrow
G2
\rightarrow
G3
\rightarrow
G4
\rightarrow
G5,
$$

kita dapat melihat:

$$
\Delta Performance.
$$

---

# G.74. Contoh ablation

Misalnya hasil:

| Model | Sharpe | MDD | Turnover |
|---|---:|---:|---:|
| G1 | 1.12 | −18% | 4.2 |
| G2 | 1.25 | −16% | 4.8 |
| G3 | 1.39 | −13% | 3.1 |
| G4 | 1.51 | −11% | 2.8 |
| G5 | 1.57 | −9% | 1.9 |

Maka kita dapat mengatakan:

> factor exposure dan transaction-cost-aware optimization memberikan kontribusi terhadap peningkatan risk-adjusted performance.

Itu jauh lebih kuat secara ilmiah.

---

# G.75. Dan sekarang kita dapat melihat hubungan dengan skripsimu

Ada hubungan yang sangat langsung dengan apa yang telah kamu pelajari sebelumnya.

Kamu sudah bekerja dengan:

$$
\boxed{
\text{Markowitz}
\rightarrow
\text{QUBO}
\rightarrow
\text{Ising}
\rightarrow
\text{VQE/QAOA}.
}
$$

Dalam proyek ini kita memperluasnya menjadi:

$$
\boxed{
\text{Markowitz}
+
\text{factor model}
+
\text{transaction cost}
+
\text{turnover}
+
\text{dynamic state}
}
$$

kemudian:

$$
\boxed{
\rightarrow QUBO
\rightarrow Ising
\rightarrow QAOA.
}
$$

Jadi ini bukan algoritma quantum yang ditempelkan ke trading.

Kita mulai dari **financial optimization problem**, lalu menunjukkan bahwa problem tersebut memiliki struktur combinatorial yang dapat dipetakan ke QUBO.

---

# G.76. Bahkan ada hubungan langsung dengan Hamiltonian Ising yang sudah kamu pelajari

Kita sebelumnya menulis:

$$
\hat H
=
-\sum_i h_iZ_i
-
\sum_{i<j}J_{ij}Z_iZ_j.
$$

Sekarang kita dapat menginterpretasikan:

$$
h_i
$$

sebagai efek individual keputusan trading, sedangkan:

$$
J_{ij}
$$

sebagai interaksi antar keputusan.

Interaksi tersebut dapat berasal dari:

$$
\boxed{
\text{covariance}
+
\text{factor exposure}
+
\text{constraints}
+
\text{transaction costs}.
}
$$

Jadi secara fisik:

$$
\boxed{
\text{market portfolio}
\leftrightarrow
\text{spin system}
}
$$

dengan energy landscape yang merepresentasikan objective finansial.

---

# G.77. Tetapi jangan membuat klaim terlalu besar

Kita **tidak** boleh mengatakan:

> "Karena pasar adalah sistem Ising."

Itu tidak benar.

Yang benar:

> Kita memetakan **masalah optimasi diskrit yang berasal dari portfolio/trading problem** ke bentuk QUBO/Ising.

Jadi Ising adalah **representasi matematis optimization problem**, bukan klaim bahwa pasar secara literal merupakan material magnetik.

Ini penting secara akademik.

---

# G.78. Tahap G dalam satu persamaan

Kalau seluruh pembahasan ini harus diringkas menjadi satu formula, saya akan menggunakan:

$$
\boxed{
\begin{aligned}
\min_{b,s}
\quad
&
-\mu_t^T(b-s)
+
\lambda(b-s)^T\Sigma_t(b-s)
\\
&+
\sum_k
P_k
\left[
\beta_{k,t}^T(b-s)-e_{k,t}^{\star}
\right]^2
\\
&+
\sum_i c_{i,t}(b_i+s_i)
\\
&+
P_{\mathrm{switch}}
\|b-b_{t-1}\|_2^2
+
P_{\mathrm{switch}}
\|s-s_{t-1}\|_2^2
\\
&+
P_{\mathrm{dir}}\sum_i b_is_i
\\
&+
P_K
\left[
\sum_i(b_i+s_i)-K
\right]^2
\\
\text{s.t.}
\quad
&
b_i,s_i\in\{0,1\}.
\end{aligned}
}
$$

Kemudian:

$$
\boxed{
\min_{x\in\{0,1\}^{2N}}
x^TQ_tx+c_t^Tx+c_0
}
$$

kemudian:

$$
\boxed{
x_i=\frac{1-Z_i}{2}
}
$$

kemudian:

$$
\boxed{
H_C(t)
=
\sum_i h_i(t)Z_i
+
\sum_{i<j}J_{ij}(t)Z_iZ_j.
}
$$

Dan akhirnya:

$$
\boxed{
|\psi_t(\gamma,\beta)\rangle
=
\prod_{l=1}^{p}
e^{-i\beta_lH_M}
e^{-i\gamma_lH_C(t)}
|+\rangle^{\otimes n}.
}
$$

Dengan:

$$
\boxed{
(\gamma^\star,\beta^\star)
=
\arg\min_{\gamma,\beta}
\langle H_C(t)\rangle.
}
$$

---

# G.79. Namun ada satu hal yang sangat penting untuk Tahap H

Kita sekarang sudah mempunyai **mathematical formulation**.

Tetapi masih ada satu pertanyaan besar:

> **Bagaimana kita menentukan $\mu_t$, $\Sigma_t$, dan $\beta_t$ secara benar dari data?**

Karena seluruh QUBO bergantung pada:

$$
\boxed{
\mu_t,\quad
\Sigma_t,\quad
B_t.
}
$$

Kalau estimasinya buruk, QAOA bisa memberikan **solusi optimal untuk QUBO yang salah**.

Dan ini merupakan jebakan yang sangat penting:

$$
\boxed{
\text{Optimization quality}
\neq
\text{forecast quality}.
}
$$

QAOA bisa menemukan:

$$
x^\star
$$

dengan sangat baik, tetapi jika:

$$
\mu_t
$$

salah, maka:

$$
x^\star
$$

tetap bisa menjadi trade yang buruk.

---

# G.80. Maka Tahap H seharusnya bukan langsung coding QAOA

Menurut saya, tahap berikutnya justru harus kita bangun sebagai:

# **Tahap H — Forecasting & State Estimation Engine**

Di sana kita akan menurunkan secara matematis:

$$
\boxed{
\mu_t
}
$$

dari:

- historical returns,
- momentum,
- volatility,
- volume,
- BTC/ETH,
- DXY,
- gold,
- SPX/VIX,
- cross-asset correlation,
- order-book imbalance,

kemudian membangun:

$$
\boxed{
\Sigma_t
}
$$

secara **rolling / exponentially weighted / shrinkage**, dan:

$$
\boxed{
B_t
}
$$

untuk factor exposure.

Yang paling menarik, kita juga bisa membuat **regime-dependent estimator**, sehingga:

$$
\mu_t,\Sigma_t,B_t
=
f(S_t).
$$

Dengan demikian QUBO kita benar-benar menjadi:

$$
\boxed{
Q_t=f(\text{market state at }t)
}
$$

dan bukan sekadar QUBO statis yang dihitung sekali dari historical data.

**Baru setelah Tahap H selesai**, kita mempunyai seluruh bahan yang dibutuhkan untuk membuat implementasi QAOA yang serius: bukan hanya circuit-nya, tetapi juga **bagaimana angka-angka yang masuk ke circuit tersebut diperoleh secara causal dari pasar**.

## Prompt:
8/17/2026, 9:50:26 PM

lanjut Tahap H

## Response:
8/17/2026, 9:50:28 PM

Baik. **Tahap H adalah salah satu tahap paling penting dari seluruh sistem**, karena di sinilah kita menentukan *angka apa yang sebenarnya masuk ke QUBO*. QAOA hanya mengoptimalkan objective yang kita berikan. Jika estimasi expected return, covariance, dan factor exposure buruk, QAOA dapat menemukan solusi matematis yang sangat optimal tetapi secara finansial buruk.

Jadi Tahap H kita bangun sebagai:

# Tahap H — Forecasting & State Estimation Engine

Arsitektur besarnya menjadi:

$$
\boxed{
\text{Raw Market Data}
\rightarrow
\text{Feature Construction}
\rightarrow
\text{Market State}
\rightarrow
\begin{cases}
\mu_t\\
\Sigma_t\\
B_t\\
\text{confidence}\\
\text{regime}
\end{cases}
\rightarrow
Q_t
\rightarrow
\text{QAOA}
}
$$

Saya ingin membuat tahap ini cukup matematis sehingga nantinya kita bisa langsung menerjemahkannya menjadi kode.

---

# H.1. Masalah fundamental: apa yang sebenarnya kita prediksi?

Pada waktu:

$$
t,
$$

kita tidak mengetahui return masa depan:

$$
r_{t+\Delta}.
$$

Yang kita miliki hanyalah informasi:

$$
\mathcal F_t
$$

yaitu seluruh informasi yang tersedia sampai waktu $t$.

Maka target forecasting yang benar adalah:

$$
\boxed{
\mu_{i,t}
=
E[
r_{i,t+\Delta}
\mid
\mathcal F_t
]
}
$$

Perhatikan simbol:

$$
\mathcal F_t.
$$

Ini sangat penting.

Model tidak boleh menggunakan informasi:

$$
t+\Delta
$$

ketika membuat keputusan pada:

$$
t.
$$

Inilah prinsip **causality / no look-ahead bias**.

---

# H.2. Return

Kita menggunakan log return:

$$
\boxed{
r_{i,t}
=
\ln
\frac{P_{i,t}}{P_{i,t-1}}
}
$$

atau:

$$
r_{i,t}
=
\ln(P_{i,t})-\ln(P_{i,t-1}).
$$

Untuk horizon:

$$
\Delta,
$$

target dapat didefinisikan:

$$
\boxed{
y_{i,t}^{(\Delta)}
=
\ln
\frac{P_{i,t+\Delta}}{P_{i,t}}.
}
$$

Misalnya:

- $\Delta=5$ menit,
- $\Delta=1$ jam,
- $\Delta=4$ jam,
- $\Delta=1$ hari.

---

# H.3. Kita sebaiknya mempunyai beberapa horizon

Trading jangka pendek tidak harus memiliki satu horizon.

Misalnya:

$$
\Delta_1=15\text{ menit}
$$

$$
\Delta_2=1\text{ jam}
$$

$$
\Delta_3=4\text{ jam}.
$$

Maka:

$$
\mu_{i,t}^{(15m)}
$$

$$
\mu_{i,t}^{(1h)}
$$

$$
\mu_{i,t}^{(4h)}.
$$

Ini memungkinkan sistem mengetahui apakah signal hanya bersifat sangat pendek atau memiliki persistence.

---

# H.4. State vector

Sekarang kita definisikan seluruh informasi pasar menjadi:

$$
\boxed{
S_t
}
$$

atau lebih eksplisit:

$$
S_t=
\begin{bmatrix}
S_t^{price}\\
S_t^{momentum}\\
S_t^{volatility}\\
S_t^{volume}\\
S_t^{factor}\\
S_t^{microstructure}\\
S_t^{regime}
\end{bmatrix}.
$$

Kemudian:

$$
\boxed{
\mu_t=f_\theta(S_t).
}
$$

Di sini:

$$
\theta
$$

adalah parameter model forecasting.

---

# H.5. Jangan langsung menggunakan harga mentah

Harga:

$$
P_t
$$

biasanya bukan feature yang baik untuk cross-sectional model.

Lebih berguna menggunakan:

$$
r_t,
$$

volatility,

momentum,

relative strength,

volume,

factor return,

dan sebagainya.

---

# H.6. Feature block 1 — momentum

Contoh:

$$
M_{i,t}^{(k)}
=
\sum_{j=0}^{k-1}r_{i,t-j}.
$$

Ini sama dengan:

$$
M_{i,t}^{(k)}
=
\ln
\frac{P_{i,t}}{P_{i,t-k}}.
$$

Kita dapat memiliki:

$$
M^{(5)},
M^{(20)},
M^{(60)}.
$$

Untuk data 1 jam misalnya:

- 5 jam,
- 20 jam,
- 60 jam.

---

# H.7. Feature block 2 — volatility

Volatility historis sederhana:

$$
\boxed{
\sigma_{i,t}^{(k)}
=
\sqrt{
\frac{1}{k-1}
\sum_{j=0}^{k-1}
(r_{i,t-j}-\bar r_{i,t})^2
}.
}
$$

Tetapi untuk trading yang lebih responsif, saya lebih menyukai EWMA.

---

# H.8. EWMA volatility

Definisikan:

$$
\boxed{
\sigma_{i,t}^2
=
\lambda_\sigma
\sigma_{i,t-1}^2
+
(1-\lambda_\sigma)r_{i,t-1}^2.
}
$$

dengan:

$$
0<\lambda_\sigma<1.
$$

Jika:

$$
\lambda_\sigma
$$

besar, estimator lebih lambat.

Jika kecil, estimator lebih responsif.

---

# H.9. Mengapa EWMA cocok untuk sistem kita?

Karena pasar bukan stationary process sempurna.

Misalnya:

$$
\sigma_{t-100}
\ll
\sigma_t.
$$

Jika kita menggunakan rolling volatility panjang, model masih "mengingat" kondisi lama.

EWMA memberi:

$$
\text{recent observations}
>
\text{old observations}.
$$

---

# H.10. Feature block 3 — volume

Volume dapat digunakan sebagai:

$$
V_t.
$$

Tetapi volume absolut tidak comparable antar aset.

Lebih baik:

$$
\boxed{
RVOL_t
=
\frac{V_t}
{EMA_k(V_t)}.
}
$$

Jika:

$$
RVOL_t>1,
$$

volume lebih besar dari normal.

Misalnya:

$$
RVOL_t=2.4
$$

berarti volume sekitar:

$$
2.4\times
$$

rata-rata eksponensialnya.

---

# H.11. Feature block 4 — volatility-adjusted momentum

Momentum mentah:

$$
M_t.
$$

Tidak cukup.

Kita dapat menormalisasi:

$$
\boxed{
Z^{mom}_{i,t}
=
\frac{M_{i,t}}
{\sigma_{i,t}\sqrt{k}}.
}
$$

Ini memberi semacam signal-to-noise ratio.

---

# H.12. Feature block 5 — market factors

Sekarang bagian yang sangat penting dari desain kita.

Untuk saham internasional:

$$
F_t=
\begin{bmatrix}
r_{DXY,t}\\
r_{Gold,t}\\
r_{SPX,t}\\
r_{VIX,t}
\end{bmatrix}.
$$

Untuk crypto:

$$
F_t=
\begin{bmatrix}
r_{BTC,t}\\
r_{ETH,t}\\
\Delta BTC.D_t\\
r_{DXY,t}\\
r_{Gold,t}
\end{bmatrix}.
$$

Jadi model tidak melihat sebuah aset secara terisolasi.

---

# H.13. Contoh: altcoin

Misalkan:

$$
r_{SOL,t}
=
\alpha
+
\beta_{BTC}r_{BTC,t}
+
\beta_{ETH}r_{ETH,t}
+
\beta_{DXY}r_{DXY,t}
+
\epsilon_t.
$$

Jika:

$$
\beta_{BTC}=1.3,
$$

maka SOL sangat sensitif terhadap BTC.

Jika BTC mengalami:

$$
+1\%,
$$

model secara kasar mengantisipasi kontribusi:

$$
1.3\%.
$$

tentu dengan asumsi hubungan linear tersebut masih berlaku.

---

# H.14. Factor model

Secara umum:

$$
\boxed{
r_t=B_tf_t+\alpha_t+\epsilon_t.
}
$$

Dengan:

$$
r_t\in\mathbb R^N
$$

$$
f_t\in\mathbb R^K
$$

$$
B_t\in\mathbb R^{N\times K}.
$$

---

# H.15. Estimasi beta

Beta dapat diperoleh melalui rolling regression.

Untuk aset $i$:

$$
r_{i,\tau}
=
\alpha_i
+
\beta_i^Tf_\tau
+
\epsilon_{i,\tau}.
$$

Untuk window:

$$
\tau=t-W+1,\ldots,t.
$$

Secara OLS:

$$
\boxed{
\hat\beta_i
=
(F^TF)^{-1}F^Tr_i.
}
$$

Namun ada masalah.

---

# H.16. Masalah multicollinearity

Misalnya:

$$
BTC
$$

dan:

$$
ETH
$$

sangat berkorelasi.

Maka:

$$
F^TF
$$

bisa ill-conditioned.

Solusinya:

$$
\boxed{
\hat\beta
=
(F^TF+\lambda_\beta I)^{-1}F^Tr.
}
$$

Ini adalah Ridge Regression.

---

# H.17. Mengapa Ridge menarik untuk kita?

Karena kita tidak hanya ingin forecasting.

Kita juga ingin:

$$
B_t
$$

untuk factor exposure constraint.

Beta yang terlalu noisy akan membuat:

$$
Q_t
$$

berubah-ubah secara tidak stabil.

Ridge memberikan:

$$
\text{stability}
>
\text{pure OLS}.
$$

---

# H.18. Forecasting expected return

Sekarang kita dapat membuat model:

$$
\boxed{
\mu_{i,t}
=
\alpha_i
+
\beta_i^Tf_t
+
\theta_i^TX_{i,t}.
}
$$

Tetapi kita bisa memperluasnya:

$$
\boxed{
\mu_{i,t}
=
f_\theta
(
X_{i,t},
F_t,
B_t,
\Sigma_t,
R_t
)
}
$$

dengan:

$$
R_t
$$

sebagai market regime.

---

# H.19. Saya menyarankan model forecasting tidak langsung memprediksi harga

Jangan:

$$
P_{t+\Delta}.
$$

Lebih baik:

$$
\boxed{
E[r_{t+\Delta}].
}
$$

Bahkan lebih baik lagi, model dapat memprediksi:

$$
\boxed{
(\mu_{t+\Delta},
\sigma_{t+\Delta},
p_{up})
}
$$

sekaligus.

---

# H.20. Probabilistic forecast

Misalkan:

$$
r_{i,t+\Delta}
\sim
\mathcal D(\mu_i,\sigma_i).
$$

Kita dapat menggunakan:

$$
p_i
=
P(r_i>0\mid S_t).
$$

Kemudian expected return:

$$
\mu_i
=
E[r_i\mid S_t].
$$

Ini memberikan dua informasi:

$$
\text{magnitude}
$$

dan:

$$
\text{confidence}.
$$

---

# H.21. Signal strength

Kita dapat membuat:

$$
\boxed{
IR_{i,t}
=
\frac{\mu_{i,t}}
{\sigma_{i,t}}.
}
$$

Ini secara konseptual mirip expected return per unit volatility.

Untuk LONG:

$$
IR>0.
$$

Untuk SHORT:

$$
IR<0.
$$

Semakin besar:

$$
|IR|,
$$

semakin menarik signal.

---

# H.22. Tetapi jangan gunakan $\mu/\sigma$ secara naif

Karena:

$$
\mu
$$

adalah forecast yang noisy.

Misalnya:

$$
\mu=0.2\%
$$

dan:

$$
\sigma=0.5\%.
$$

Maka:

$$
IR=0.4.
$$

Tetapi jika confidence model hanya:

$$
20\%,
$$

signal tersebut tidak boleh diperlakukan sama dengan signal:

$$
IR=0.4
$$

dengan confidence:

$$
80\%.
$$

---

# H.23. Confidence-adjusted alpha

Kita dapat mendefinisikan:

$$
\boxed{
\tilde\mu_i
=
c_i\mu_i
}
$$

dengan:

$$
0\leq c_i\leq1.
$$

Contoh:

$$
c_i=P(\text{forecast valid}\mid S_t).
$$

Maka QUBO menggunakan:

$$
\boxed{
\tilde\mu_t
}
$$

bukan:

$$
\mu_t
$$

mentah.

---

# H.24. Ini sangat penting secara praktis

Bayangkan dua aset:

### Asset A

$$
\mu_A=0.8\%
$$

$$
c_A=0.9
$$

sehingga:

$$
\tilde\mu_A=0.72\%.
$$

### Asset B

$$
\mu_B=1.0\%
$$

$$
c_B=0.3.
$$

Maka:

$$
\tilde\mu_B=0.30\%.
$$

Optimizer sekarang memilih A meskipun raw forecast B lebih besar.

---

# H.25. Market regime

Sekarang kita masuk ke bagian yang lebih advanced.

Hubungan:

$$
BTC\rightarrow SOL
$$

tidak selalu sama.

Begitu pula:

$$
DXY\rightarrow AAPL.
$$

Maka kita membutuhkan:

$$
R_t.
$$

Contoh:

$$
R_t\in
\{
\text{Risk-On},
\text{Risk-Off},
\text{High Volatility},
\text{Low Volatility}
\}.
$$

---

# H.26. Regime sederhana

Kita dapat mendefinisikan:

$$
R_t=
f(
\sigma_{market},
trend_{market},
VIX,
DXY,
correlation
).
$$

Contoh:

$$
R_t=
\begin{cases}
1,&\sigma_t>\sigma^\star\\
0,&\sigma_t\leq\sigma^\star.
\end{cases}
$$

Ini versi paling sederhana.

---

# H.27. Regime yang lebih formal

Kita bisa menggunakan Hidden Markov Model:

$$
P(R_t=j\mid R_{t-1}=i)
=
P_{ij}.
$$

Dengan observation:

$$
Y_t=
[
r_{SPX,t},
r_{DXY,t},
r_{Gold,t},
\sigma_t,
VIX_t
].
$$

Maka:

$$
P(R_t\mid Y_{1:t})
$$

memberikan probabilitas regime.

---

# H.28. Jangan memilih regime secara hard

Daripada:

$$
R_t=1,
$$

kita dapat mempertahankan:

$$
p_t^{(1)},p_t^{(2)},\ldots,p_t^{(M)}.
$$

Kemudian expected forecast:

$$
\boxed{
\mu_t
=
\sum_{m=1}^{M}
P(R_t=m\mid\mathcal F_t)
\mu_t^{(m)}.
}
$$

Ini jauh lebih smooth.

---

# H.29. Covariance estimation

Sekarang kita masuk ke komponen kedua yang sangat penting:

$$
\boxed{
\Sigma_t.
}
$$

Estimator covariance sample:

$$
\hat\Sigma
=
\frac{1}{T-1}
\sum_t
(r_t-\bar r)(r_t-\bar r)^T.
$$

Masalahnya:

Jika:

$$
N
$$

besar dibandingkan:

$$
T,
$$

covariance matrix sangat noisy.

---

# H.30. Shrinkage covariance

Kita gunakan:

$$
\boxed{
\Sigma_{\mathrm{shrink}}
=
(1-\delta)\hat\Sigma
+
\delta F.
}
$$

dengan:

$$
0\leq\delta\leq1.
$$

$F$ adalah target covariance yang lebih stabil.

Contoh:

$$
F=\operatorname{diag}(\hat\Sigma).
$$

---

# H.31. Mengapa shrinkage penting untuk QAOA?

Karena covariance menjadi:

$$
J_{ij}.
$$

Jika covariance noise:

$$
\Rightarrow
J_{ij}\text{ noise}.
$$

Akibatnya:

$$
H_C
$$

berubah secara tidak stabil.

QAOA kemudian mengoptimalkan landscape yang sebenarnya merupakan artefak estimation error.

Jadi:

$$
\boxed{
\text{better covariance}
\rightarrow
\text{better Hamiltonian}.
}
$$

---

# H.32. Factor covariance

Kita sebelumnya mempunyai:

$$
\Sigma
=
BFB^T+D.
$$

Ini sebenarnya sangat menarik.

Daripada mengestimasi:

$$
N\times N
$$

covariance secara langsung, kita bisa mengestimasi:

$$
B
$$

dan:

$$
F.
$$

Jika:

$$
K\ll N,
$$

maka dimensionality reduction sangat besar.

Misalnya:

$$
N=100,
$$

tetapi:

$$
K=5.
$$

---

# H.33. Estimasi idiosyncratic covariance

Secara sederhana:

$$
\epsilon_{i,t}
=
r_{i,t}
-
\hat\alpha_i
-
\hat\beta_i^Tf_t.
$$

Kemudian:

$$
D
=
\operatorname{diag}
(
Var(\epsilon_1),
\ldots,
Var(\epsilon_N)
).
$$

Dengan asumsi residual cross-correlation kecil.

Maka:

$$
\boxed{
\Sigma
\approx
BFB^T+D.
}
$$

---

# H.34. Keuntungan besar

Portfolio risk:

$$
d^T\Sigma d
$$

menjadi:

$$
d^T BFB^T d+d^TDd.
$$

Definisikan:

$$
e=B^Td.
$$

Maka:

$$
\boxed{
Risk=e^TFe+d^TDd.
}
$$

Interpretasinya:

$$
\boxed{
Total Risk=
Factor Risk+
Specific Risk.
}
$$

---

# H.35. Ini sangat cocok dengan sistem kita

Kita ingin:

- alpha dari asset,
- factor exposure,
- covariance,
- risk.

Semuanya berasal dari satu model:

$$
\boxed{
r=Bf+\alpha+\epsilon.
}
$$

Ini membuat architecture jauh lebih konsisten.

---

# H.36. Dynamic covariance

Pasar berubah.

Jadi kita gunakan:

$$
\Sigma_t.
$$

Misalnya EWMA:

$$
\boxed{
\Sigma_t
=
\lambda_\Sigma\Sigma_{t-1}
+
(1-\lambda_\Sigma)
r_{t-1}r_{t-1}^T.
}
$$

Namun untuk sistem yang lebih besar, saya lebih menyukai:

$$
\boxed{
\Sigma_t
=
B_tF_tB_t^T+D_t.
}
$$

karena lebih interpretable.

---

# H.37. Market factor covariance

Misalnya:

$$
F_t=
\begin{bmatrix}
Var(DXY)&Cov(DXY,Gold)&\cdots\\
Cov(Gold,DXY)&Var(Gold)&\cdots\\
\vdots&&\ddots
\end{bmatrix}.
$$

Ini juga dapat menggunakan EWMA/shrinkage.

---

# H.38. Factor exposure target harus dynamic

Kita sebelumnya menulis:

$$
e_k^\star.
$$

Tetapi seharusnya:

$$
\boxed{
e_{k,t}^\star
}
$$

karena target factor exposure bergantung pada regime.

Misalnya saat:

$$
P(\text{Risk-Off})\uparrow,
$$

kita mungkin ingin:

$$
E_{SPX}\rightarrow0.
$$

Sedangkan saat:

$$
P(\text{Risk-On})\uparrow,
$$

kita dapat memberikan:

$$
E_{SPX}>0.
$$

---

# H.39. Contoh regime-dependent factor target

Misalkan:

$$
R_t=
\text{Risk-On}.
$$

Kita bisa menetapkan:

$$
E_{SPX}^\star=+0.5.
$$

Tetapi jika:

$$
R_t=
\text{Risk-Off},
$$

maka:

$$
E_{SPX}^\star=-0.2.
$$

Sehingga:

$$
C_F
=
P_F
(
B^Td-e_t^\star
)^2
$$

secara otomatis berubah.

---

# H.40. DXY dan Gold

Untuk sistem global yang kamu inginkan, saya ingin membedakan tiga hal.

### DXY

Proxy untuk:

$$
USD\ strength.
$$

### Gold

Proxy untuk:

$$
safe-haven/inflation/real-rate dynamics.
$$

### Equity index

Proxy untuk:

$$
risk appetite.
$$

Jadi state macro kita dapat berupa:

$$
\boxed{
F_t=
[
DXY,
Gold,
SPX,
VIX
].
}
$$

Untuk crypto ditambah:

$$
BTC,
ETH,
BTC.D.
$$

---

# H.41. Jangan langsung menggunakan level DXY

Kita lebih tertarik pada:

$$
r_{DXY,t}.
$$

Dan fitur turunannya:

$$
M_{DXY,t}^{(k)},
$$

$$
\sigma_{DXY,t},
$$

$$
Z_{DXY,t}.
$$

Misalnya:

$$
Z_{DXY,t}
=
\frac{
DXY_t-EMA(DXY)_t
}{
\sigma_{DXY,t}
}.
$$

---

# H.42. Cross-asset signal

Kita dapat membuat signal:

$$
X_{i,t}^{factor}
=
\beta_i^Tf_t.
$$

Kemudian residual:

$$
\boxed{
\tilde r_{i,t}
=
r_{i,t}
-
\beta_i^Tf_t.
}
$$

Ini menarik.

Karena kita dapat bertanya:

> Apakah saham/crypto naik karena market factor, atau karena alpha idiosyncratic?

---

# H.43. Idiosyncratic alpha

Misalnya:

$$
NVDA
$$

naik:

$$
+2\%.
$$

Tetapi:

$$
SPX
$$

naik:

$$
+1.8\%.
$$

Maka sebagian besar gerakan mungkin berasal dari market.

Tetapi jika:

$$
NVDA=+2\%
$$

sementara:

$$
SPX=-1\%,
$$

maka residual return dapat sangat positif.

Ini jauh lebih menarik sebagai alpha candidate.

---

# H.44. Residual momentum

Kita bahkan dapat mendefinisikan:

$$
\boxed{
M_{i,t}^{res}
=
\sum_{j=0}^{k-1}
\tilde r_{i,t-j}.
}
$$

Ini mengukur momentum yang tidak dijelaskan oleh factor.

Dan:

$$
M^{res}
$$

dapat menjadi input forecasting.

---

# H.45. Forecast model akhirnya

Kita dapat membangun:

$$
X_{i,t}
=
\begin{bmatrix}
M_{i,t}\\
M_{i,t}^{res}\\
Z_{i,t}^{mom}\\
RVOL_{i,t}\\
\sigma_{i,t}\\
\beta_{i,t}\\
f_t\\
regime_t
\end{bmatrix}.
$$

Kemudian:

$$
\boxed{
\mu_{i,t}
=
f_\theta(X_{i,t}).
}
$$

---

# H.46. Model $f_\theta$ tidak harus deep learning

Ini penting.

Kita dapat memulai dengan:

$$
\boxed{
\mu_t=X_t\theta.
}
$$

Linear model.

Kemudian:

$$
\boxed{
\mu_t=f_{\mathrm{GBM}}(X_t)
}
$$

atau model lain.

Baru setelah baseline kuat, kita bisa mencoba:

$$
LSTM,
Transformer,
Temporal CNN,
$$

dan sebagainya.

---

# H.47. Mengapa baseline sederhana lebih baik?

Karena tujuan kita bukan:

> "membuat model AI paling rumit."

Tujuannya:

$$
\boxed{
\text{forecast}
\rightarrow
\text{optimization}
\rightarrow
\text{execution}
\rightarrow
\text{PnL}.
}
$$

Kalau model linear menghasilkan:

$$
Sharpe=1.5
$$

sedangkan neural network:

$$
Sharpe=1.1,
$$

maka model sederhana lebih baik.

---

# H.48. Forecast harus dievaluasi out-of-sample

Jangan hanya melihat:

$$
R^2.
$$

Kita membutuhkan:

$$
IC
=
Corr(
\hat r_t,
r_{t+\Delta}
).
$$

atau:

$$
RankIC.
$$

Kemudian:

$$
Directional Accuracy.
$$

Tetapi akhirnya yang terpenting:

$$
\boxed{
\text{economic value}.
}
$$

---

# H.49. Economic value

Forecast yang bagus belum tentu trading strategy bagus.

Misalnya:

$$
IC=0.05.
$$

Terlihat kecil.

Tetapi jika:

$$
TC
$$

rendah dan signal stabil, mungkin tetap profitable.

Sebaliknya:

$$
IC=0.15
$$

tetapi turnover sangat tinggi, bisa menjadi:

$$
negative\ PnL.
$$

---

# H.50. Maka forecasting objective dan trading objective berbeda

Forecasting:

$$
\min_\theta
Loss(
\hat r,r
).
$$

Trading:

$$
\max
E[PnL]
-
\lambda Risk
-
TC.
$$

Ini dua optimization problem berbeda.

---

# H.51. Ini mengarah ke konsep yang sangat penting: forecast-to-trade transformation

Kita memiliki:

$$
\hat\mu_t.
$$

Tidak langsung:

$$
BUY.
$$

Melainkan:

$$
\boxed{
\hat\mu_t
\rightarrow
Q_t
\rightarrow
x_t^\star.
}
$$

Jadi QAOA berfungsi sebagai **decision layer**.

---

# H.52. Confidence-aware QUBO

Saya bahkan menyarankan objective menggunakan:

$$
\tilde\mu_t
=
c_t\odot\mu_t.
$$

Sehingga:

$$
C_{\mathrm{return}}
=
-\tilde\mu_t^Td.
$$

Ini membuat optimizer secara otomatis mengurangi perhatian terhadap signal yang tidak dipercaya.

---

# H.53. Prediction uncertainty yang lebih formal

Daripada sekadar $c_i$, kita dapat menggunakan:

$$
r_{i,t+\Delta}
\sim
\mathcal N(
\mu_{i,t},
\tau_{i,t}^2
).
$$

Maka signal-to-noise:

$$
\boxed{
SNR_{i,t}
=
\frac{\mu_{i,t}}{\tau_{i,t}}.
}
$$

Kita kemudian dapat menggunakan:

$$
\tilde\mu_i
=
\frac{\mu_i}{1+\kappa\tau_i}.
$$

Semakin uncertainty besar:

$$
\tau_i\uparrow,
$$

semakin kecil effective alpha.

---

# H.54. Ini juga dapat mengendalikan position size

Setelah QAOA memilih aset, kita bisa menggunakan:

$$
q_i
\propto
\frac{\mu_i}{\sigma_i^2}
$$

sebagai baseline.

Namun kita dapat memasukkan uncertainty:

$$
\boxed{
q_i
\propto
\frac{\mu_i}
{\sigma_i^2+\kappa\tau_i^2}.
}
$$

Jadi forecast uncertainty tidak hanya memengaruhi selection tetapi juga sizing.

---

# H.55. State estimation pipeline

Pada setiap waktu $t$:

### Step 1

Ambil data:

$$
D_{\leq t}.
$$

### Step 2

Hitung:

$$
r_t.
$$

### Step 3

Hitung features:

$$
X_t.
$$

### Step 4

Estimasi regime:

$$
P(R_t\mid\mathcal F_t).
$$

### Step 5

Estimasi:

$$
B_t.
$$

### Step 6

Estimasi:

$$
F_t.
$$

### Step 7

Estimasi:

$$
D_t.
$$

### Step 8

Bangun:

$$
\Sigma_t=B_tF_tB_t^T+D_t.
$$

### Step 9

Forecast:

$$
\mu_t.
$$

### Step 10

Forecast uncertainty:

$$
\tau_t.
$$

---

# H.56. Kemudian QUBO

Setelah itu:

$$
\boxed{
Q_t=
Q(
\mu_t,
\Sigma_t,
B_t,
TC_t,
d_{t-1},
R_t
).
}
$$

Jadi QUBO bukan hard-coded.

Ia **dihasilkan ulang dari market state**.

---

# H.57. Ini menghasilkan konsep yang sangat menarik

Sistem kita sebenarnya adalah:

$$
\boxed{
\text{State-Dependent QAOA}
}
$$

karena:

$$
H_C(t)
=
H_C(S_t).
$$

Dengan demikian:

$$
H_C(t_1)
\neq
H_C(t_2)
$$

ketika market state berubah.

---

# H.58. Market berubah → Hamiltonian berubah

Misalnya:

### Normal regime

$$
\sigma_t=low
$$

$$
DXY=stable
$$

$$
SPX=up.
$$

Hamiltonian:

$$
H_C^{normal}.
$$

Kemudian market crash:

$$
\sigma_t\uparrow\uparrow
$$

$$
DXY\uparrow
$$

$$
SPX\downarrow.
$$

Maka:

$$
\boxed{
H_C^{crisis}
\neq
H_C^{normal}.
}
$$

---

# H.59. Ini berbeda dari QAOA portfolio optimization statis

Dalam portfolio optimization biasa:

$$
Q
$$

dibuat sekali.

Kemudian:

$$
QAOA(Q)
$$

dijalankan.

Dalam sistem kita:

$$
\boxed{
Q_t
=
f(S_t)
}
$$

dan:

$$
QAOA(Q_t)
$$

dijalankan secara rolling.

Ini membuatnya jauh lebih dekat dengan **dynamic trading system**.

---

# H.60. Tetapi kita tidak boleh menjalankan QAOA setiap tick

Itu tidak praktis.

Misalnya data:

$$
1\text{ minute}.
$$

Kita bisa melakukan:

$$
QAOA
$$

setiap:

$$
15\text{ menit}
$$

atau:

$$
1\text{ jam}.
$$

Di antara interval itu:

$$
\text{position management}
$$

berjalan secara classical.

---

# H.61. Arsitektur temporal

Misalnya:

$$
\boxed{
\text{Forecast/QAOA cycle}=1h
}
$$

sedangkan:

$$
\boxed{
\text{Risk monitoring}=1min.
}
$$

Jadi:

### Setiap jam

$$
State
\rightarrow
Forecast
\rightarrow
QUBO
\rightarrow
QAOA
\rightarrow
new\ portfolio.
$$

### Setiap menit

$$
Price
\rightarrow
SL/TP
\rightarrow
risk\ check
\rightarrow
execution.
$$

---

# H.62. Ini cocok dengan desain yang kita bahas sebelumnya

Kita memiliki:

$$
\boxed{
\text{Strategic Layer}
}
$$

untuk QAOA.

Dan:

$$
\boxed{
\text{Tactical Layer}
}
$$

untuk trade management.

Serta:

$$
\boxed{
\text{Execution Layer}
}
$$

untuk order.

---

# H.63. Hierarchical architecture

Secara lengkap:

$$
\boxed{
\begin{array}{ccc}
\text{Macro State} &&\\
\downarrow&&\\
\text{Forecasting}&&\\
\downarrow&&\\
\text{QAOA Selection}&&\\
\downarrow&&\\
\text{Position Sizing}&&\\
\downarrow&&\\
\text{Trade Construction}&&\\
\downarrow&&\\
\text{Execution}&&\\
\downarrow&&\\
\text{Position Management}&&\\
\downarrow&&\\
\text{Risk Monitoring}
\end{array}
}
$$

Dan feedback:

$$
\text{Position Management}
\rightarrow
\text{next state}.
$$

---

# H.64. Satu masalah yang belum kita masukkan: order book

Untuk trading jangka pendek, OHLCV saja belum cukup.

Kita ingin:

$$
OB_t
$$

(order book state).

Contoh feature:

$$
I_t
=
\frac{V_{bid}-V_{ask}}
{V_{bid}+V_{ask}}.
$$

Ini disebut order-book imbalance.

Jika:

$$
I_t\rightarrow+1,
$$

bid jauh lebih dominan.

Jika:

$$
I_t\rightarrow-1,
$$

ask dominan.

---

# H.65. Microstructure feature

Kita bisa memiliki:

$$
X_t^{micro}
=
\begin{bmatrix}
spread_t\\
depth_t\\
imbalance_t\\
trade\ intensity_t\\
signed\ volume_t\\
VWAP_t-P_t
\end{bmatrix}.
$$

Kemudian:

$$
\mu_t
=
f(
X_t^{macro},
X_t^{asset},
X_t^{micro}
).
$$

---

# H.66. Ini membuat model dua skala

### Slow information

$$
DXY,
Gold,
SPX,
VIX
$$

berubah relatif lambat.

### Fast information

$$
order\ book,
spread,
imbalance
$$

berubah cepat.

Maka state kita sebenarnya:

$$
\boxed{
S_t=
(S_t^{slow},S_t^{fast}).
}
$$

---

# H.67. Saya bahkan menyarankan dua model forecast

### Model 1 — medium horizon

$$
\mu_t^{slow}
=
f_{slow}(macro,trend,factor).
$$

### Model 2 — short horizon

$$
\mu_t^{fast}
=
f_{fast}(orderbook,microstructure).
$$

Kemudian:

$$
\boxed{
\mu_t
=
w_t\mu_t^{slow}
+
(1-w_t)\mu_t^{fast}.
}
$$

Bobot:

$$
w_t
$$

bergantung pada horizon trading dan kondisi market.

---

# H.68. Contoh

Jika market sangat tenang:

$$
w_t=0.7.
$$

Medium-term information lebih dominan.

Jika terjadi sudden order-flow imbalance:

$$
w_t=0.3.
$$

Microstructure menjadi lebih penting.

---

# H.69. Sekarang kita punya state estimator yang jauh lebih lengkap

$$
\boxed{
S_t=
\left[
\begin{array}{c}
\text{price returns}\\
\text{momentum}\\
\text{volatility}\\
\text{volume}\\
\text{BTC/ETH}\\
\text{DXY}\\
\text{Gold}\\
\text{SPX}\\
\text{VIX}\\
\text{factor exposure}\\
\text{order book}\\
\text{regime}
\end{array}
\right].
}
$$

Kemudian:

$$
\boxed{
(\mu_t,\tau_t,B_t,\Sigma_t)
=
\mathcal E(S_t)
}
$$

dengan:

$$
\mathcal E
$$

sebagai **state estimation engine**.

---

# H.70. Dan akhirnya

$$
\boxed{
Q_t
=
\mathcal Q
(
\mu_t,
\tau_t,
\Sigma_t,
B_t,
TC_t,
d_{t-1},
R_t
)
}
$$

kemudian:

$$
\boxed{
H_C(t)=
\mathcal I(Q_t)
}
$$

dengan:

$$
\mathcal I
$$

sebagai mapping QUBO → Ising.

Kemudian:

$$
\boxed{
x_t^\star
=
QAOA(H_C(t)).
}
$$

---

# H.71. Satu hal yang menurut saya sangat penting untuk proyek kita

Jangan menganggap:

$$
QAOA
$$

sebagai sumber alpha.

Alpha berasal dari:

$$
\boxed{
\text{data + forecasting + market structure}.
}
$$

QAOA berperan sebagai:

$$
\boxed{
\text{combinatorial decision optimizer}.
}
$$

Dengan kata lain:

$$
\boxed{
\text{Alpha Model}
\rightarrow
\text{Optimization Problem}
\rightarrow
\text{QAOA}
}
$$

bukan:

$$
\text{Market Data}
\rightarrow
\text{QAOA}
\rightarrow
\text{Magic Profit}.
$$

Ini akan menjadi prinsip desain utama sistem kita.

---

# H.72. Pipeline Tahap A–H sekarang

Kita akhirnya memiliki:

$$
\boxed{
\begin{aligned}
A &: \text{Market & trading problem formulation}\\
B &: \text{Market state / information structure}\\
C &: \text{Forecast / alpha formulation}\\
D &: \text{Risk & portfolio formulation}\\
E &: \text{Dynamic position management}\\
F &: \text{Execution & causal backtesting}\\
G &: \text{QUBO/Ising/QAOA formulation}\\
H &: \text{State estimation & parameter generation}.
\end{aligned}
}
$$

Dan alur aktualnya:

$$
\boxed{
D_{\leq t}
\rightarrow
S_t
\rightarrow
\{\mu_t,\Sigma_t,B_t,\tau_t,R_t\}
\rightarrow
Q_t
\rightarrow
H_C(t)
\rightarrow
QAOA
\rightarrow
x_t^\star
\rightarrow
q_t^\star
\rightarrow
Orders
\rightarrow
Position\ Management.
}
$$

---

# H.73. Tahap berikutnya: Tahap I

Setelah Tahap H, menurut saya **kita belum boleh langsung coding QAOA**.

Kita perlu terlebih dahulu membangun:

# **Tahap I — Backtesting, Walk-Forward Validation, dan Statistical Evaluation**

Ini sangat penting karena kita sekarang mempunyai sistem yang sangat mudah terkena:

- look-ahead bias,
- survivorship bias,
- data snooping,
- overfitting,
- regime overfitting,
- transaction-cost underestimation,
- slippage,
- QAOA parameter overfitting,
- optimizer overfitting.

Kita perlu membangun matematika untuk:

$$
\boxed{
\text{Train}
\rightarrow
\text{Validation}
\rightarrow
\text{Test}
\rightarrow
\text{Walk Forward}
\rightarrow
\text{Paper Trading}
\rightarrow
\text{Live}
}
$$

serta menguji bukan hanya:

$$
PnL,
$$

tetapi:

$$
Sharpe,
Sortino,
Calmar,
MDD,
VaR,
CVaR,
Turnover,
Hit\ Rate,
Profit\ Factor,
IC,
RankIC,
$$

dan yang menurut saya sangat menarik untuk proyek kita:

$$
\boxed{
\text{QAOA vs Classical Optimizer}
}
$$

pada **QUBO yang persis sama**.

Itulah yang nantinya memungkinkan kita menjawab pertanyaan ilmiah yang jauh lebih menarik daripada sekadar *"apakah bot ini menghasilkan uang?"*:

> **Apakah QAOA memberikan kualitas solusi atau efisiensi optimasi yang berbeda dibandingkan classical solver pada dynamic short-horizon portfolio/trading problem yang sama, setelah mempertimbangkan estimation error dan biaya transaksi?**

Itu sudah mulai menjadi **research-grade quantitative trading + quantum optimization framework**, bukan sekadar bot trading.

## Prompt:
8/17/2026, 9:51:37 PM

lanjut Tahap I

## Response:
8/17/2026, 9:51:38 PM

Baik. Kita masuk ke **Tahap I — Backtesting, Walk-Forward Validation, dan Statistical Evaluation**.

Menurut saya, ini justru tahap yang akan menentukan apakah seluruh arsitektur A–H kita benar-benar ilmiah atau hanya terlihat bagus di atas kertas. Kita sudah membangun forecasting, factor model, covariance, regime, QUBO, QAOA, execution, dan position management. Sekarang semuanya harus diuji **tanpa memberikan sistem informasi yang pada saat itu belum tersedia**.

Saya akan membangun Tahap I dari prinsip paling dasar sampai akhirnya menjadi protokol eksperimen yang bisa langsung kita implementasikan.

---

# Tahap I — Backtesting dan Statistical Validation

Tujuan Tahap I:

$$
\boxed{
\text{Historical Data}
\rightarrow
\text{Causal Simulation}
\rightarrow
\text{Trading Decisions}
\rightarrow
\text{PnL}
\rightarrow
\text{Statistical Inference}
}
$$

Tetapi ada satu prinsip yang harus menjadi fondasi:

$$
\boxed{
\text{Pada waktu }t,\text{ sistem hanya boleh mengetahui }\mathcal F_t.
}
$$

Tidak lebih.

---

# I.1. Mengapa backtesting biasa berbahaya?

Bayangkan kita mempunyai data:

$$
P_1,P_2,\ldots,P_T.
$$

Kemudian kita melatih model menggunakan seluruh data:

$$
P_{1:T}.
$$

Setelah itu kita menguji strategy pada data yang sama.

Misalnya diperoleh:

$$
Sharpe=3.7.
$$

Ini hampir tidak berarti.

Sebab model sudah melihat masa depan.

Secara matematis kita ingin:

$$
\boxed{
\theta_t
=
\operatorname{Train}
(
D_{\leq t}
)
}
$$

bukan:

$$
\theta
=
\operatorname{Train}
(
D_{\leq T}
).
$$

---

# I.2. Causal information set

Pada waktu:

$$
t,
$$

definisikan:

$$
\boxed{
\mathcal F_t
=
\sigma
(
D_1,D_2,\ldots,D_t
).
}
$$

Artinya semua keputusan harus merupakan fungsi:

$$
a_t
=
\pi(\mathcal F_t).
$$

Bukan:

$$
a_t
=
\pi(\mathcal F_{t+1}).
$$

Ini kelihatannya sederhana, tetapi hampir seluruh sumber **look-ahead bias** berasal dari pelanggaran konsep ini.

---

# I.3. Contoh look-ahead bias

Misalkan kita menggunakan:

$$
r_t
=
\ln\frac{P_t}{P_{t-1}}.
$$

Jika pada akhir candle $t$ kita membuat keputusan untuk:

$$
t+1,
$$

maka menggunakan:

$$
r_t
$$

masih sah.

Tetapi jika kita menggunakan:

$$
r_{t+1},
$$

maka kita sudah menggunakan informasi masa depan.

---

# I.4. Bahkan preprocessing bisa menyebabkan leakage

Misalnya kita melakukan standardization:

$$
Z_t
=
\frac{x_t-\mu}{\sigma}.
$$

Jika:

$$
\mu
=
\frac1T\sum_{t=1}^{T}x_t,
$$

maka $\mu$ menggunakan data masa depan.

Seharusnya:

$$
\boxed{
\mu_t
=
\frac{1}{N_t}
\sum_{\tau\leq t}x_\tau.
}
$$

Demikian juga:

$$
\sigma_t.
$$

---

# I.5. Jadi seluruh pipeline harus causal

Bukan hanya model forecasting.

Harus:

$$
\boxed{
\begin{aligned}
Feature_t &= f(D_{\leq t})\\
Scaler_t &= f(D_{\leq t})\\
Forecast_t &= f(Feature_t,\theta_t)\\
Covariance_t &= f(D_{\leq t})\\
QUBO_t &= f(\mu_t,\Sigma_t,\ldots)\\
QAOA_t &= f(QUBO_t)\\
Order_t &= f(QAOA_t).
\end{aligned}
}
$$

---

# I.6. Train/validation/test

Kita tidak menggunakan random train-test split.

Untuk time series:

$$
\boxed{
\text{Time must flow forward.}
}
$$

Misalnya data:

$$
2021-2025.
$$

Kita bisa membaginya:

$$
\underbrace{2021-2023}_{Train}
\rightarrow
\underbrace{2024}_{Validation}
\rightarrow
\underbrace{2025}_{Test}.
$$

Tetapi untuk sistem kita saya ingin sesuatu yang lebih kuat:

$$
\boxed{\text{Walk-Forward Validation}}.
$$

---

# I.7. Walk-forward validation

Misalkan:

$$
T_0
$$

adalah awal training.

Kita mempunyai:

$$
Train_1=[t_1,t_2]
$$

dan:

$$
Test_1=[t_3,t_4].
$$

Kemudian:

$$
Train_2=[t_1,t_4]
$$

dan:

$$
Test_2=[t_5,t_6].
$$

Begitu seterusnya.

Secara umum:

$$
\boxed{
\theta_k
=
Train(D_{\leq T_k})
}
$$

kemudian:

$$
\boxed{
Performance_k
=
Test(
\theta_k,
D_{T_k+1:T_{k+1}}
).
}
$$

---

# I.8. Expanding window

Contohnya:

```text
TRAIN       TEST
███████████ ██
██████████████ ██
█████████████████ ██
████████████████████ ██
```

Training semakin panjang.

Secara matematis:

$$
\mathcal T_k
=
[t_0,T_k].
$$

Ini cocok jika informasi historis lama masih relevan.

---

# I.9. Rolling window

Alternatif:

```text
TRAIN       TEST
   ███████████ ██
      ███████████ ██
         ███████████ ██
```

Training window tetap:

$$
W.
$$

Sehingga:

$$
\mathcal T_k
=
[T_k-W,T_k].
$$

Ini lebih cocok jika market mengalami structural change.

---

# I.10. Untuk sistem kita: hybrid

Saya menyarankan:

$$
\boxed{
\text{rolling estimation}
+
\text{expanding model validation}.
}
$$

Misalnya:

- covariance: rolling 60–120 hari,
- beta: rolling 60–120 hari,
- regime: rolling,
- forecasting model: retrain berkala,
- hyperparameter validation: expanding walk-forward.

Ini lebih masuk akal secara finansial.

---

# I.11. Nested walk-forward

Kalau kita ingin benar-benar research-grade, bahkan pemilihan hyperparameter tidak boleh menggunakan test period.

Strukturnya:

$$
\boxed{
\text{Outer Test}
}
$$

dan di dalam training period:

$$
\boxed{
\text{Inner Train}
\rightarrow
\text{Inner Validation}.
}
$$

Jadi:

```text
OUTER TRAIN                  OUTER TEST
┌────────────────────────┐   ┌───────────┐
│ INNER TRAIN │ INNER VAL│   │ untouched │
└────────────────────────┘   └───────────┘
```

Ini mencegah kita memilih model berdasarkan test performance.

---

# I.12. Contoh konkret

Misalnya:

$$
2021-01-01
\rightarrow
2025-12-31.
$$

Outer test:

$$
2025.
$$

Training:

$$
2021-2024.
$$

Di dalam 2021–2024:

- 2021–2023 → inner train,
- 2024 → inner validation.

Pilih:

$$
\theta^\star
$$

berdasarkan validation.

Kemudian **bekukan model**.

Baru jalankan:

$$
2025
$$

sebagai out-of-sample test.

---

# I.13. Tetapi ada masalah yang lebih besar

Kita bukan hanya mempunyai satu model.

Kita mungkin mencoba:

- 5 feature sets,
- 4 forecasting models,
- 3 covariance estimators,
- 5 QAOA depths,
- 4 risk coefficients,
- 3 transaction cost assumptions.

Jumlah kombinasi:

$$
5\times4\times3\times5\times4\times3
=
3600.
$$

Kalau kita memilih yang menghasilkan Sharpe tertinggi, kita telah melakukan:

$$
\boxed{
\text{multiple testing}.
}
$$

---

# I.14. Backtest overfitting

Misalkan semua strategi sebenarnya tidak punya alpha:

$$
E[SR]=0.
$$

Tetapi kita mencoba 1.000 strategi.

Kemungkinan besar ada beberapa yang memperoleh:

$$
SR>2.
$$

Bukan karena benar-benar bagus.

Tetapi karena:

$$
\boxed{
\text{selection by luck}.
}
$$

---

# I.15. Inilah mengapa kita perlu experiment registry

Setiap eksperimen harus memiliki:

$$
ExperimentID
$$

dan mencatat:

$$
\begin{aligned}
FeatureSet\\
Model\\
Hyperparameters\\
CovarianceModel\\
QUBOParameters\\
QAOAParameters\\
TransactionCost\\
DateRange
\end{aligned}
$$

sehingga kita tahu berapa banyak eksperimen yang sebenarnya sudah kita lakukan.

---

# I.16. Kita harus membedakan tiga jenis hasil

### In-sample

$$
IS.
$$

### Out-of-sample

$$
OOS.
$$

### Paper/live

$$
LIVE.
$$

Targetnya:

$$
\boxed{
Performance_{IS}
\geq
Performance_{OOS}
\approx
Performance_{LIVE}.
}
$$

Tidak harus sama, tetapi divergence harus masuk akal.

---

# I.17. Return portfolio

Misalkan keputusan portfolio:

$$
w_t.
$$

Return:

$$
\boxed{
R_{p,t+1}
=
w_t^Tr_{t+1}.
}
$$

Tetapi ini belum memasukkan transaction cost.

---

# I.18. Transaction cost

Misalkan:

$$
\Delta w_t
=
w_t-w_{t-1}.
$$

Cost sederhana:

$$
C_t
=
c^T|\Delta w_t|.
$$

Maka:

$$
\boxed{
R_{net,t+1}
=
w_t^Tr_{t+1}
-
c^T|\Delta w_t|.
}
$$

Ini minimal harus ada.

---

# I.19. Spread dan slippage

Untuk trading jangka pendek, kita sebaiknya menggunakan:

$$
C_t
=
C_t^{commission}
+
C_t^{spread}
+
C_t^{slippage}.
$$

Misalnya:

$$
C_t
=
\kappa_t^T|\Delta q_t|.
$$

Dengan:

$$
\kappa_t
=
\text{effective cost per unit}.
$$

---

# I.20. Market impact

Jika order besar:

$$
Q_t
$$

dibandingkan liquidity:

$$
ADV_t,
$$

cost meningkat.

Model sederhana:

$$
\boxed{
Impact_t
=
\eta
\left(
\frac{|Q_t|}{ADV_t}
\right)^\gamma.
}
$$

Misalnya:

$$
\gamma\approx\frac12.
$$

Sehingga:

$$
Impact
\propto
\sqrt{\frac{|Q|}{ADV}}.
$$

Ini jauh lebih realistis daripada fixed transaction cost.

---

# I.21. Net PnL

Maka:

$$
\boxed{
PnL_t
=
w_t^Tr_{t+1}
-
TC_t
-
Impact_t.
}
$$

Semua metrik performance harus menggunakan:

$$
PnL_{net}.
$$

Bukan gross PnL.

---

# I.22. Equity curve

Mulai dari:

$$
V_0.
$$

Kemudian:

$$
\boxed{
V_t
=
V_{t-1}(1+R_{net,t}).
}
$$

Atau log wealth:

$$
\ln V_t
=
\ln V_{t-1}
+
\ln(1+R_{net,t}).
$$

---

# I.23. Cumulative return

$$
\boxed{
R_{cum}
=
\frac{V_T}{V_0}-1.
}
$$

Tetapi ini **tidak cukup**.

Strategi:

$$
+100\%
$$

dengan:

$$
MDD=-80\%
$$

sangat berbeda dari:

$$
+80\%
$$

dengan:

$$
MDD=-10\%.
$$

---

# I.24. Maximum Drawdown

Peak:

$$
M_t
=
\max_{\tau\leq t}V_\tau.
$$

Drawdown:

$$
\boxed{
DD_t
=
\frac{V_t-M_t}{M_t}.
}
$$

Maximum drawdown:

$$
\boxed{
MDD
=
\min_t DD_t.
}
$$

---

# I.25. Sharpe ratio

Jika:

$$
\bar R
=
\frac1T\sum_tR_t,
$$

dan:

$$
s_R
=
Std(R_t),
$$

maka:

$$
\boxed{
SR
=
\frac{\bar R-r_f}{s_R}
\sqrt{A}.
}
$$

$A$ adalah annualization factor.

Misalnya hourly:

$$
A\approx252\times24
$$

untuk pasar yang berjalan 24/7, meskipun annualization harus disesuaikan dengan definisi return dan jam trading yang digunakan.

---

# I.26. Tetapi Sharpe memiliki kelemahan

Sharpe menganggap:

$$
\sigma
$$

sebagai risk measure yang cukup.

Padahal downside:

$$
R_t<0
$$

lebih penting bagi trader.

Maka:

$$
\boxed{
Sortino
=
\frac{\bar R-r_f}
{\sigma_{downside}}
\sqrt A.
}
$$

---

# I.27. Calmar ratio

Untuk sistem trading yang mengalami drawdown:

$$
\boxed{
Calmar
=
\frac{CAGR}{|MDD|}.
}
$$

Ini sangat berguna untuk membandingkan strategy dengan risk profile berbeda.

---

# I.28. Tail risk

Kita juga perlu:

$$
VaR_\alpha.
$$

Misalnya:

$$
VaR_{95\%}.
$$

Tetapi saya lebih tertarik pada:

$$
\boxed{
CVaR_\alpha.
}
$$

Expected Shortfall:

$$
CVaR_\alpha
=
E[
-L
\mid
L\geq VaR_\alpha
].
$$

Ini menjawab:

> Jika kita masuk ke 5% kondisi terburuk, rata-rata kerugiannya berapa?

---

# I.29. Trading-specific metrics

Kita juga perlu:

$$
HitRate
=
\frac{\# profitable trades}
{\# trades}.
$$

Tetapi hit rate bisa menipu.

Misalnya:

$$
HitRate=80\%
$$

namun satu loss besar menghapus seluruh profit.

Maka kita membutuhkan:

$$
\boxed{
ProfitFactor
=
\frac{\sum Profit}
{|\sum Loss|}.
}
$$

---

# I.30. Expectancy

Untuk setiap trade:

$$
W=average\ win
$$

$$
L=average\ loss
$$

$$
p=P(win).
$$

Expected value:

$$
\boxed{
E
=
pW-(1-p)L.
}
$$

Strategy profitable jika:

$$
E>0.
$$

---

# I.31. Tetapi untuk sistem kita, expectancy harus conditional

Kita memiliki signal strength:

$$
s_t.
$$

Maka kita bisa menghitung:

$$
E[PnL\mid s_t\in bin_k].
$$

Misalnya:

| Signal | Expected PnL |
|---|---:|
| weak | -0.01% |
| medium | +0.03% |
| strong | +0.12% |
| very strong | +0.18% |

Jika hubungan seperti ini konsisten OOS, signal kita lebih meyakinkan.

---

# I.32. Information Coefficient

Untuk cross-sectional trading, kita dapat menghitung:

$$
\boxed{
IC_t
=
Corr(
\hat\mu_t,
r_{t+\Delta}
).
}
$$

Kemudian:

$$
IC_{avg}
=
\frac1T\sum_tIC_t.
$$

Ini mengukur apakah model dapat melakukan ranking asset.

---

# I.33. Rank IC

Karena portfolio optimization sering hanya membutuhkan ranking:

$$
RankIC_t
=
Corr_{Spearman}
(
Rank(\hat\mu_t),
Rank(r_{t+\Delta})
).
$$

Ini sering lebih robust terhadap outlier.

---

# I.34. Forecast quality ≠ portfolio quality

Kita harus melakukan dua evaluasi terpisah.

### Forecast layer

$$
\hat\mu
\rightarrow
IC.
$$

### Portfolio layer

$$
\hat\mu,\Sigma
\rightarrow
Portfolio
\rightarrow
PnL.
$$

Ini sangat penting ketika nanti membandingkan QAOA.

---

# I.35. Eksperimen utama kita

Kita ingin membandingkan:

$$
\boxed{
QAOA
\quad vs \quad
Classical Solver
}
$$

tetapi **dengan problem yang identik**.

Misalnya:

$$
\min_x
x^TQ_tx.
$$

Jangan membandingkan QAOA dengan classical optimizer pada objective berbeda.

---

# I.36. Classical baseline

Kita bisa menggunakan:

### Exact brute force

untuk:

$$
N\leq20
$$

misalnya.

Karena jumlah konfigurasi:

$$
2^N.
$$

Ini memungkinkan kita mengetahui:

$$
x^\star_{exact}.
$$

---

# I.37. Mengukur approximation ratio

Misalkan objective minimization:

$$
C(x).
$$

QAOA menghasilkan:

$$
C_{QAOA}.
$$

Exact:

$$
C^\star.
$$

Maka:

$$
\boxed{
Gap
=
\frac{
C_{QAOA}-C^\star
}{
|C^\star|
}.
}
$$

Semakin kecil:

$$
Gap\rightarrow0,
$$

semakin dekat dengan optimum.

---

# I.38. Probability of finding optimum

QAOA tidak selalu menghasilkan optimum.

Misalnya:

$$
P(x^\star)=0.37.
$$

Artinya jika kita melakukan sampling:

$$
37\%
$$

probabilitas menghasilkan konfigurasi optimal.

Kita dapat mencatat:

$$
\boxed{
P_{opt}.
}
$$

---

# I.39. Expected objective dari QAOA

Jika output distribution:

$$
p_\theta(x),
$$

maka:

$$
\boxed{
E[C]
=
\sum_xp_\theta(x)C(x).
}
$$

Ini bahkan lebih informatif daripada hanya best sample.

---

# I.40. Quantum advantage belum tentu PnL advantage

Ini sangat penting untuk skripsi/proyek kita.

Misalnya:

$$
Gap_{QAOA}
<
Gap_{classical}.
$$

Tetapi setelah trading:

$$
PnL_{QAOA}
<
PnL_{classical}.
$$

Mengapa?

Karena:

$$
\text{estimation error}
$$

dan:

$$
\text{transaction cost}
$$

mungkin mendominasi optimization quality.

---

# I.41. Jadi kita harus punya tiga level benchmark

## Level 1 — Mathematical

$$
QAOA
\quad vs\quad
Exact.
$$

Mengukur:

$$
objective\ gap.
$$

---

## Level 2 — Computational

$$
QAOA
\quad vs\quad
Classical\ optimizer.
$$

Mengukur:

- runtime,
- iterations,
- objective,
- scalability.

---

## Level 3 — Financial

$$
Portfolio_{QAOA}
\quad vs\quad
Portfolio_{classical}.
$$

Mengukur:

- PnL,
- Sharpe,
- MDD,
- turnover,
- CVaR,
- transaction cost.

---

# I.42. Ini menghasilkan eksperimen yang sangat kuat

Kita bisa mempunyai:

$$
\boxed{
\begin{array}{c|c}
Method & Performance\\
\hline
Exact & \cdots\\
Simulated\ Annealing & \cdots\\
MILP/QP & \cdots\\
Classical\ heuristic & \cdots\\
QAOA & \cdots
\end{array}
}
$$

Kemudian:

$$
\boxed{
\text{same data}
+
\text{same QUBO}
+
\text{same constraints}
+
\text{same costs}.
}
$$

Barulah perbandingan adil.

---

# I.43. Kita juga perlu baseline trading

Bukan hanya classical optimizer.

Bandingkan terhadap:

### Buy & Hold

$$
B\&H.
$$

### Equal Weight

$$
w_i=\frac1N.
$$

### Momentum

$$
w_i\propto M_i.
$$

### Mean-Variance

$$
\max_w
\mu^Tw-\lambda w^T\Sigma w.
$$

### Classical combinatorial optimizer

$$
QUBO_{classical}.
$$

### QAOA

$$
QUBO_{QAOA}.
$$

---

# I.44. Dengan begitu kita dapat menjawab pertanyaan yang jauh lebih menarik

Bukan:

> "Apakah QAOA menghasilkan profit?"

Tetapi:

> Apakah QAOA menghasilkan solusi yang lebih baik daripada classical optimization **untuk masalah combinatorial portfolio/trading yang sama?**

Dan:

> Apakah improvement tersebut cukup besar untuk bertahan setelah estimation error, transaction cost, slippage, dan regime changes?

---

# I.45. Stress testing

Backtest normal belum cukup.

Kita perlu stress:

$$
\boxed{
\text{Market Regimes}.
}
$$

Misalnya:

### Bull

$$
r_{market}>0,\quad\sigma\ low.
$$

### Bear

$$
r_{market}<0.
$$

### Crisis

$$
\sigma\gg median.
$$

### Sideways

$$
|\mu|\approx0.
$$

### Liquidity shock

$$
spread\uparrow,\quad depth\downarrow.
$$

---

# I.46. Factor stress

Karena sistem kita menggunakan:

$$
DXY,
Gold,
SPX,
BTC,
ETH,
$$

kita dapat melakukan scenario:

$$
DXY +2\sigma
$$

atau:

$$
SPX -3\sigma.
$$

Kemudian hitung:

$$
\Delta Portfolio.
$$

---

# I.47. Stress test portfolio

Misalnya portfolio memiliki factor exposure:

$$
E=B^Tw.
$$

Shock:

$$
\Delta f.
$$

Approximate PnL:

$$
\boxed{
\Delta P
\approx
E^T\Delta f.
}
$$

Ini sangat powerful.

Kita dapat mengetahui:

> "Jika USD tiba-tiba menguat 2σ, apa yang terjadi pada portfolio?"

---

# I.48. Scenario-based stress

Secara umum:

$$
f^{stress}
=
f_t+\Delta f.
$$

Kemudian:

$$
\mu^{stress}
=
\mu(f^{stress})
$$

dan:

$$
\Sigma^{stress}
=
\Sigma(f^{stress}).
$$

Lalu kita dapat membangun:

$$
Q^{stress}.
$$

Bahkan:

$$
QAOA(Q^{stress}).
$$

---

# I.49. Ini berarti QAOA dapat menjadi regime-adaptive

Normal:

$$
Q_t^{normal}.
$$

Stress:

$$
Q_t^{stress}.
$$

Crisis:

$$
Q_t^{crisis}.
$$

Dengan demikian sistem tidak sekadar:

$$
\text{buy/sell}.
$$

Tetapi:

$$
\boxed{
\text{re-optimize portfolio under changing market state}.
}
$$

---

# I.50. Monte Carlo

Kita juga perlu menguji apakah performance hanya terjadi karena satu trajectory historis.

Misalkan residual:

$$
\epsilon_t.
$$

Kita dapat menghasilkan synthetic paths:

$$
\epsilon_t^{(b)}.
$$

untuk:

$$
b=1,\ldots,B.
$$

Kemudian menjalankan strategy pada:

$$
B
$$

simulasi.

---

# I.51. Bootstrap

Kita dapat menggunakan block bootstrap karena return time-series tidak IID sempurna.

Ambil block:

$$
(r_t,\ldots,r_{t+k})
$$

kemudian resample block.

Ini mempertahankan sebagian temporal dependence.

---

# I.52. Distribusi Sharpe

Misalnya dari:

$$
B=1000
$$

simulasi kita memperoleh:

$$
SR^{(1)},SR^{(2)},\ldots,SR^{(B)}.
$$

Kemudian kita bisa melihat:

$$
P(SR>0).
$$

Bahkan:

$$
5\%,50\%,95\%
$$

quantile.

---

# I.53. Probabilistic performance

Daripada mengatakan:

> Sharpe = 1.72

kita bisa mengatakan:

$$
\boxed{
SR_{median}=1.72
}
$$

dengan:

$$
95\%\,CI=[0.83,2.41].
$$

Ini jauh lebih ilmiah.

---

# I.54. Deflated Sharpe Ratio

Karena kita melakukan banyak eksperimen:

$$
SR_{observed}
$$

harus dikoreksi terhadap multiple testing.

Konsep yang relevan adalah:

$$
\boxed{
Deflated\ Sharpe\ Ratio.
}
$$

Intinya:

> semakin banyak strategi/model yang kita coba, semakin tinggi Sharpe yang dapat muncul secara kebetulan.

---

# I.55. Probability of Backtest Overfitting

Kita juga dapat menggunakan pendekatan:

$$
PBO
$$

untuk mengukur probabilitas strategy yang terlihat terbaik di-sample akan gagal out-of-sample.

Ini akan sangat berguna ketika kita mulai bereksperimen dengan:

- feature,
- QUBO coefficient,
- QAOA depth,
- risk penalty,
- stop loss,
- take profit.

---

# I.56. Parameter QAOA juga bisa overfit

Misalnya kita memilih:

$$
p=1,2,3,\ldots,10
$$

dan:

$$
\beta,\gamma
$$

berdasarkan profit OOS.

Hati-hati.

Kita telah melakukan hyperparameter optimization.

Jadi:

$$
p
$$

harus dipilih berdasarkan training/validation.

Test tidak boleh disentuh.

---

# I.57. Quantum hyperparameter validation

Misalnya:

$$
p\in\{1,2,3\}
$$

dan optimizer:

$$
\{SPSA,Adam\}.
$$

Kita pilih berdasarkan:

$$
Validation\ Objective.
$$

Kemudian:

$$
Test
$$

hanya digunakan sekali.

---

# I.58. Tetapi ada pertanyaan yang lebih penting

Apakah kita benar-benar membutuhkan QAOA?

Kita harus memberikan kesempatan kepada classical method untuk menang.

Ini penting secara ilmiah.

Jika classical optimizer ternyata:

$$
10\times
$$

lebih cepat dan menghasilkan:

$$
identical\ portfolio,
$$

maka itu adalah hasil yang valid.

Kita tidak boleh memaksakan:

$$
QAOA > Classical.
$$

---

# I.59. Justru hasil negatif dapat menjadi penelitian yang bagus

Misalnya hasil:

$$
Objective_{QAOA}
=
Objective_{classical}+0.5\%.
$$

Tetapi:

$$
Runtime_{QAOA}
>
Runtime_{classical}.
$$

Maka kesimpulan:

> Pada ukuran masalah dan simulator/hardware yang digunakan, QAOA belum memberikan computational advantage.

Itu jauh lebih kredibel daripada memaksakan klaim quantum advantage.

---

# I.60. Eksperimen ablation

Kita juga perlu menghapus komponen satu per satu.

Misalnya:

$$
Model_A
$$

tanpa factor.

$$
Model_B
$$

dengan factor.

$$
Model_C
$$

dengan factor + regime.

$$
Model_D
$$

dengan factor + regime + QAOA.

Kemudian:

$$
Performance_A
\rightarrow
Performance_B
\rightarrow
Performance_C
\rightarrow
Performance_D.
$$

---

# I.61. Contoh ablation table

| Model | Factor | Regime | QAOA | Sharpe |
|---|---:|---:|---:|---:|
| Baseline | ✗ | ✗ | ✗ | 0.72 |
| Factor | ✓ | ✗ | ✗ | 0.91 |
| Factor + Regime | ✓ | ✓ | ✗ | 1.08 |
| Factor + Regime + Classical | ✓ | ✓ | Classical | 1.21 |
| Factor + Regime + QAOA | ✓ | ✓ | QAOA | 1.24 |

Jika hasil seperti ini terjadi secara OOS, kita memiliki cerita penelitian yang sangat kuat.

---

# I.62. Kita juga perlu turnover analysis

Turnover:

$$
\boxed{
TO_t
=
\frac12
\sum_i
|w_{i,t}-w_{i,t-1}|.
}
$$

Kenapa faktor:

$$
\frac12?
$$

Karena setiap pembelian biasanya mempunyai sisi penjualan counterpart dalam rebalancing portfolio.

---

# I.63. Alpha vs turnover

Kita ingin mengetahui:

$$
PnL_{gross}
$$

terhadap:

$$
TO.
$$

Misalnya:

$$
PnL_{gross}=10\%
$$

tetapi:

$$
TC=12\%.
$$

Strategy sebenarnya tidak viable.

Maka kita membutuhkan:

$$
\boxed{
Net\ Alpha
=
Gross\ Alpha
-
Transaction\ Cost.
}
$$

---

# I.64. Capacity

Untuk hedge fund/prop firm, profit tidak cukup.

Kita juga bertanya:

$$
\boxed{
\text{Berapa besar capital yang dapat strategy tanggung?}
}
$$

Jika:

$$
AUM
$$

naik, market impact:

$$
Impact\uparrow.
$$

Maka:

$$
PnL_{net}(AUM)
$$

akhirnya menurun.

---

# I.65. Capacity curve

Kita dapat menghasilkan:

$$
AUM
\rightarrow
Net\ Sharpe.
$$

Misalnya:

$$
\begin{array}{c|c}
AUM & Sharpe\\
\hline
\$10k&2.1\\
\$100k&1.9\\
\$1M&1.4\\
\$10M&0.6
\end{array}
$$

Ini jauh lebih dekat dengan quantitative trading profesional.

---

# I.66. Execution realism

Untuk setiap signal:

$$
t.
$$

Kita tidak boleh mengasumsikan:

$$
Fill_t=100\%.
$$

Harus ada:

$$
P(fill_t\mid order,market).
$$

Misalnya limit order:

$$
P(fill)
=
f(
distance\ from\ mid,
queue,
volume,
volatility
).
$$

---

# I.67. Limit order

Jika kita memasang:

$$
P_{limit}
=
P_{mid}-\delta
$$

untuk long.

Maka fill hanya terjadi jika market menyentuh atau menembus level tersebut **dan** order kita mendapatkan execution.

Jadi backtest idealnya memiliki:

$$
\boxed{
FillModel.
}
$$

---

# I.68. Stop-loss juga harus realistis

Misalnya stop:

$$
P_{SL}.
$$

Jika market gap:

$$
P_t<P_{SL},
$$

kita tidak boleh menganggap fill tepat:

$$
P_{SL}.
$$

Harus menggunakan:

$$
P_{fill}
$$

yang mungkin lebih buruk.

---

# I.69. Ini sangat penting untuk crypto

Karena:

- volatility tinggi,
- spread berubah,
- liquidity berubah,
- liquidation cascade,
- market order impact.

Jadi:

$$
SL
$$

bukan guaranteed price.

---

# I.70. Evaluation hierarchy

Saya ingin sistem kita melewati:

$$
\boxed{
Level\ 0:
Unit\ Tests
}
$$

kemudian:

$$
\boxed{
Level\ 1:
Mathematical Validation
}
$$

kemudian:

$$
\boxed{
Level\ 2:
Historical Backtest
}
$$

kemudian:

$$
\boxed{
Level\ 3:
Walk-Forward
}
$$

kemudian:

$$
\boxed{
Level\ 4:
Stress Test
}
$$

kemudian:

$$
\boxed{
Level\ 5:
Paper Trading
}
$$

kemudian:

$$
\boxed{
Level\ 6:
Small Live Capital
}
$$

---

# I.71. Unit test matematis

Contohnya kita harus memastikan:

$$
\Sigma=\Sigma^T.
$$

dan:

$$
\lambda_{\min}(\Sigma)\geq0.
$$

Jika tidak:

$$
\Sigma
$$

bukan positive semidefinite.

Kemudian:

$$
Q
$$

harus memiliki bentuk yang benar.

---

# I.72. Test QUBO

Untuk:

$$
N
$$

kecil, lakukan brute force:

$$
x\in\{0,1\}^N.
$$

Hitung:

$$
C(x)
$$

untuk semua:

$$
2^N
$$

kombinasi.

Kemudian:

$$
x^\star
=
\arg\min_xC(x).
$$

Bandingkan dengan QAOA.

---

# I.73. Test portfolio

Pastikan:

$$
\sum_iw_i=1
$$

jika fully invested.

Pastikan:

$$
w_i\geq0
$$

untuk long-only.

Jika cardinality:

$$
\sum_i x_i\leq K.
$$

Harus selalu dipenuhi.

---

# I.74. Test causality

Ini salah satu unit test paling penting.

Ambil data sampai:

$$
t.
$$

Jalankan model:

$$
Prediction_t.
$$

Kemudian tambahkan data:

$$
t+1.
$$

Prediction pada waktu $t$ **tidak boleh berubah**.

Jika berubah:

$$
\boxed{
\text{look-ahead leakage}.
}
$$

---

# I.75. Ini dapat kita jadikan automated test

Secara konsep:

$$
Model(D_{\leq t})
=
Model(D_{\leq t+1})|_{prediction_t}
$$

harus menghasilkan:

$$
identical.
$$

Ini salah satu test yang sangat berharga untuk pipeline kita.

---

# I.76. Test survivorship bias

Universe asset juga tidak boleh hanya berisi aset yang masih hidup sekarang.

Misalnya:

$$
2021
$$

ada 100 saham.

Pada:

$$
2026
$$

hanya 70 yang masih ada.

Kalau backtest 2021 menggunakan hanya 70 saham yang masih hidup, kita sudah menggunakan future information.

---

# I.77. Untuk crypto

Masalahnya sedikit berbeda karena banyak token:

- listing,
- delisting,
- liquidity collapse.

Universe harus berdasarkan:

$$
Universe_t.
$$

bukan:

$$
Universe_{2026}.
$$

---

# I.78. Corporate action

Untuk saham internasional kita harus memperhatikan:

- stock split,
- dividend,
- rights issue,
- merger,
- delisting.

Return yang digunakan harus konsisten.

---

# I.79. Currency normalization

Ini penting karena kita ingin:

$$
\text{crypto}
+
\text{US equities}
+
\text{international equities}
+
\text{Gold}
+
\text{USD}.
$$

Portfolio base currency misalnya:

$$
USD.
$$

Jika asset dalam:

$$
EUR,
JPY,
GBP,
$$

return harus memperhitungkan FX.

Jika:

$$
P_{asset}^{EUR}
$$

dan:

$$
FX_{USD/EUR},
$$

maka USD price:

$$
P^{USD}
=
P^{EUR}\times FX_{USD/EUR}.
$$

---

# I.80. Ini berarti FX juga menjadi factor

Untuk international equities:

$$
r_{USD}
=
r_{local}
+
r_{FX}
+
r_{local}r_{FX}.
$$

Dengan log return:

$$
\boxed{
r^{USD}
=
r^{local}
+
r^{FX}.
}
$$

Ini salah satu alasan mengapa:

$$
USD
$$

menjadi market factor penting.

---

# I.81. Financial objective akhir

Kita akhirnya dapat mendefinisikan:

$$
\boxed{
J
=
E[R_{net}]
-
\lambda Var(R_{net})
-
\eta CVaR
-
\kappa Turnover
}
$$

dan QUBO kita merupakan pendekatan diskrit terhadap objective ini.

---

# I.82. Tetapi evaluasi juga menggunakan objective tersebut

Jangan hanya:

$$
PnL.
$$

Kita evaluasi:

$$
\boxed{
\begin{aligned}
Return\\
Sharpe\\
Sortino\\
Calmar\\
MDD\\
CVaR\\
Turnover\\
Transaction\ Cost\\
Capacity
\end{aligned}
}
$$

---

# I.83. Framework eksperimen final

Saya menyarankan eksperimen utama kita nantinya seperti ini:

```text
                    HISTORICAL DATA
                           │
                           ▼
                  ┌─────────────────┐
                  │ Causal Features │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Forecast Model  │
                  └────────┬────────┘
                           │
                    μ, σ, regime
                           │
                           ▼
                  ┌─────────────────┐
                  │ Risk Estimator  │
                  └────────┬────────┘
                           │
                         Σ, B
                           │
                           ▼
                  ┌─────────────────┐
                  │ QUBO Generator  │
                  └────────┬────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
      Classical Solver                QAOA
             │                           │
             └─────────────┬─────────────┘
                           ▼
                   Portfolio / Orders
                           │
                           ▼
                    Execution Model
                           │
                           ▼
                       Net PnL
                           │
                           ▼
                 Statistical Evaluation
```

---

# I.84. Dan eksperimen kita harus memiliki "frozen test set"

Ini saya anggap **aturan keras**.

Misalnya:

$$
2021-2024
$$

digunakan untuk seluruh pengembangan.

Kemudian:

$$
2025
$$

adalah:

$$
\boxed{\text{LOCKED TEST SET}.}
$$

Kita tidak melihat performance 2025 untuk memilih:

- feature,
- model,
- QAOA depth,
- $\lambda$,
- stop loss,
- take profit,
- rebalance interval.

Setelah semua desain selesai:

$$
\boxed{
\text{ONE FINAL RUN ON 2025}.
}
$$

---

# I.85. Bahkan lebih baik: temporal holdout

Kalau data memungkinkan:

$$
2021-2023
\rightarrow
development
$$

$$
2024
\rightarrow
validation
$$

$$
2025
\rightarrow
test
$$

$$
2026
\rightarrow
paper/live forward.
$$

Dengan tanggal sekarang **17 Agustus 2026**, data sampai periode sekarang nantinya dapat diperlakukan sebagai forward period setelah seluruh parameter dikunci.

---

# I.86. Apa yang sebenarnya kita ingin buktikan?

Setelah Tahap I, penelitian kita seharusnya bisa menjawab empat pertanyaan:

### Pertanyaan 1

Apakah forecasting model memiliki predictive power?

$$
IC>0?
$$

---

### Pertanyaan 2

Apakah portfolio optimization meningkatkan risk-adjusted return?

$$
SR_{optimized}
>
SR_{baseline}?
$$

---

### Pertanyaan 3

Apakah QAOA mampu menemukan solusi QUBO yang kompetitif?

$$
Gap_{QAOA}
\approx
Gap_{classical/exact}?
$$

---

### Pertanyaan 4

Apakah keunggulan tersebut bertahan setelah:

$$
\boxed{
cost+
slippage+
market\ impact+
parameter\ uncertainty+
regime\ changes?
}
$$

Pertanyaan keempat adalah yang paling penting.

---

# I.87. Dan ada satu eksperimen yang menurut saya wajib kita lakukan

Kita buat **empat strategy**:

$$
S_1=\text{Equal Weight}
$$

$$
S_2=\text{Forecast + Classical Optimization}
$$

$$
S_3=\text{Forecast + QAOA}
$$

$$
S_4=\text{Forecast + QAOA + Dynamic Position Management}.
$$

Kemudian:

$$
S_1\rightarrow S_2
$$

mengukur manfaat optimization.

$$
S_2\rightarrow S_3
$$

mengukur manfaat QAOA.

$$
S_3\rightarrow S_4
$$

mengukur manfaat dynamic trade management.

Ini merupakan **ablation study** yang sangat bersih.

---

# I.88. Bahkan kita dapat melakukan "QAOA replacement test"

Ambil QUBO:

$$
Q_t.
$$

Jangan ubah apa pun.

Jalankan:

$$
x_t^{QAOA}
$$

dan:

$$
x_t^{classical}.
$$

Kemudian:

$$
PnL(QAOA)
$$

vs.

$$
PnL(classical).
$$

Dengan demikian semua perbedaan berasal dari **optimizer**, bukan dari data atau forecasting.

Ini adalah eksperimen yang menurut saya paling penting jika tujuan akhirnya adalah penelitian quantum optimization.

---

# I.89. Struktur final penelitian kita

Dengan Tahap I, keseluruhan framework A–I sekarang menjadi:

$$
\boxed{
\begin{array}{ll}
A & \text{Market Problem}\\
B & \text{Market State}\\
C & \text{Alpha/Forecasting}\\
D & \text{Risk}\\
E & \text{Position Management}\\
F & \text{Execution}\\
G & \text{QUBO + Ising + QAOA}\\
H & \text{State Estimation}\\
I & \text{Validation + Backtesting}
\end{array}
}
$$

Dan semuanya terhubung dalam satu persamaan konseptual:

$$
\boxed{
D_{\leq t}
\overset{\mathcal E}{\longrightarrow}
S_t
\overset{\mathcal F}{\longrightarrow}
(\mu_t,\Sigma_t,B_t,\tau_t,R_t)
\overset{\mathcal Q}{\longrightarrow}
Q_t
\overset{\mathrm{QAOA}}{\longrightarrow}
x_t^\star
\overset{\mathrm{Sizing}}{\longrightarrow}
w_t^\star
\overset{\mathrm{Execution}}{\longrightarrow}
PnL_{t+1}.
}
$$

Kemudian:

$$
PnL_{t+1}
\rightarrow
S_{t+1},
$$

sehingga sistem menjadi **closed-loop dynamic system**.

---

## Hal yang menurut saya paling penting setelah Tahap I

Kita **sudah tidak lagi sekadar mendesain strategi trading**. Kita sekarang memiliki kerangka eksperimen yang memungkinkan kita memisahkan tiga sumber keberhasilan:

$$
\boxed{
\text{Prediction}
}
$$

dari:

$$
\boxed{
\text{Optimization}
}
$$

dari:

$$
\boxed{
\text{Execution}.
}
$$

Ini sangat penting untuk proyekmu. Kalau nanti QAOA memberikan hasil lebih baik, kita dapat mengatakan *di mana* peningkatannya terjadi. Kalau tidak lebih baik, kita juga dapat menunjukkan apakah masalahnya berasal dari QAOA, forecasting, covariance estimation, atau execution.

Dan menurut saya, **setelah Tahap I, tahap berikutnya sebaiknya bukan langsung "Tahap J = coding"**. Kita perlu terlebih dahulu membuat **Tahap J — Formal Mathematical Specification**, yaitu menyatukan A–I menjadi satu sistem matematis lengkap: mendefinisikan semua variabel, indeks waktu, asset universe, state vector, forecast, covariance, factor exposure, objective, constraint, QUBO, Ising Hamiltonian, QAOA circuit, position sizing, TP/SL, dan transition equation secara konsisten. Setelah itu barulah kita punya *blueprint* yang cukup ketat untuk diterjemahkan ke kode tanpa ada bagian algoritma yang ambigu.

## Prompt:
8/17/2026, 9:53:11 PM

lanjut Tahap J

## Response:
8/17/2026, 9:53:12 PM

Tentu. **Tahap J adalah tahap yang sangat penting**, karena di sini seluruh gagasan A–I kita satukan menjadi **satu spesifikasi matematis formal**. Setelah Tahap J selesai, kita seharusnya dapat mengambil dokumen ini dan menerjemahkannya hampir satu-ke-satu menjadi software.

Saya akan membuatnya cukup formal, tetapi tetap menjaga interpretasi finansialnya.

# Tahap J — Formal Mathematical Specification

## J.0. Tujuan Tahap J

Kita ingin mendefinisikan sistem:

$$
\boxed{
\text{Market Data}
\rightarrow
\text{State Estimation}
\rightarrow
\text{Forecast}
\rightarrow
\text{Risk}
\rightarrow
\text{Optimization}
\rightarrow
\text{Execution}
\rightarrow
\text{Position Management}
\rightarrow
\text{PnL}
}
$$

sebagai sebuah **dynamic stochastic control system**.

Secara abstrak:

$$
\boxed{
\mathcal M=
(\mathcal S,\mathcal A,\mathcal P,\mathcal R)
}
$$

dengan:

- $\mathcal S$: state space,
- $\mathcal A$: action space,
- $\mathcal P$: transition dynamics,
- $\mathcal R$: reward/PnL function.

Namun kita **tidak perlu langsung memaksakan sistem menjadi reinforcement learning**. Kita dapat menggunakan formulasi ini sebagai kerangka matematis, sementara policy kita dibangun melalui forecasting + optimization.

---

# J.1. Notasi utama

Kita definisikan:

$$
t=1,2,\ldots,T
$$

sebagai indeks waktu.

Jumlah aset:

$$
N.
$$

Harga asset $i$:

$$
P_{i,t}.
$$

Vektor harga:

$$
\mathbf P_t
=
(P_{1,t},P_{2,t},\ldots,P_{N,t})^T.
$$

---

# J.2. Return

Kita menggunakan log-return:

$$
\boxed{
r_{i,t}
=
\ln
\left(
\frac{P_{i,t}}
{P_{i,t-1}}
\right).
}
$$

Vektor return:

$$
\boxed{
\mathbf r_t
=
(r_{1,t},\ldots,r_{N,t})^T.
}
$$

Dengan demikian:

$$
\mathbf r_t\in\mathbb R^N.
$$

---

# J.3. Information set

Semua keputusan pada waktu $t$ harus berdasarkan:

$$
\boxed{
\mathcal F_t
=
\sigma(
\mathbf r_1,\ldots,\mathbf r_t,
\mathbf f_1,\ldots,\mathbf f_t,
\mathbf o_1,\ldots,\mathbf o_t
)
}
$$

dengan:

- $\mathbf f_t$: market factors,
- $\mathbf o_t$: order-book/execution information.

Keputusan:

$$
\boxed{
a_t=\pi(\mathcal F_t).
}
$$

Ini menjadi aturan kausal utama seluruh sistem.

---

# J.4. Market factor vector

Kita tidak ingin model hanya melihat harga asset yang ditradingkan.

Kita definisikan:

$$
\boxed{
\mathbf f_t
=
\begin{bmatrix}
r^{BTC}_t\\
r^{ETH}_t\\
r^{Gold}_t\\
r^{DXY}_t\\
r^{SPX}_t\\
r^{VIX}_t\\
\vdots
\end{bmatrix}.
}
$$

Komposisinya dapat berubah berdasarkan asset class.

Misalnya untuk crypto:

$$
\mathbf f_t^{crypto}
=
[
r^{BTC}_t,
r^{ETH}_t,
r^{DXY}_t,
r^{Gold}_t,
r^{SPX}_t
]^T.
$$

Untuk saham:

$$
\mathbf f_t^{equity}
=
[
r^{SPX}_t,
r^{DXY}_t,
r^{Gold}_t,
r^{VIX}_t
]^T.
$$

---

# J.5. Factor model

Kita menggunakan:

$$
\boxed{
\mathbf r_t
=
B_t\mathbf f_t
+
\boldsymbol\epsilon_t
}
$$

dengan:

$$
B_t\in\mathbb R^{N\times K}.
$$

Elemen:

$$
B_{ik,t}
$$

adalah exposure asset $i$ terhadap factor $k$.

---

# J.6. Estimasi beta

Secara sederhana:

$$
\beta_{ik,t}
=
\frac{
Cov(r_{i},f_k)
}{
Var(f_k)
}.
$$

Tetapi kita ingin multivariate regression:

$$
\boxed{
\mathbf B_t
=
\arg\min_B
\sum_{\tau=t-W+1}^{t}
\|
\mathbf r_\tau-B\mathbf f_\tau
\|_2^2.
}
$$

$W$ adalah rolling estimation window.

---

# J.7. Residual return

Setelah memperoleh $B_t$:

$$
\boxed{
\hat{\boldsymbol\epsilon}_t
=
\mathbf r_t
-
B_t\mathbf f_t.
}
$$

Residual ini mencoba menangkap:

$$
\text{asset-specific movement}.
$$

---

# J.8. Expected return

Model forecasting kita menghasilkan:

$$
\boxed{
\hat{\boldsymbol\mu}_{t+1}
=
E[
\mathbf r_{t+1}
\mid
\mathcal F_t
].
}
$$

Tetapi kita dapat memecahnya:

$$
\boxed{
\hat{\boldsymbol\mu}_{t+1}
=
B_t\hat{\mathbf f}_{t+1}
+
\hat{\boldsymbol\alpha}_{t+1}.
}
$$

Ini sangat penting.

Ada dua sumber alpha:

$$
\boxed{
\text{factor prediction}
+
\text{idiosyncratic prediction}.
}
$$

---

# J.9. Forecast horizon

Kita harus eksplisit mengenai horizon.

Misalnya:

$$
H=1h.
$$

Maka:

$$
\hat\mu_{i,t}^{(1h)}
=
E[
r_{i,t+1h}
\mid\mathcal F_t
].
$$

Untuk horizon lebih panjang:

$$
H=4h,24h,\ldots
$$

model harus memiliki target yang berbeda.

---

# J.10. Multi-horizon forecasting

Kita bahkan dapat mendefinisikan:

$$
\boxed{
\hat{\mu}_{i,t}^{(H)}
=
E[
r_{i,t+H}
\mid\mathcal F_t
].
}
$$

Kemudian:

$$
H\in
\{15m,1h,4h,24h\}.
$$

Ini sangat berguna untuk menentukan apakah posisi:

- masuk,
- dipertahankan,
- ditutup,
- atau dire-optimasi.

---

# J.11. Covariance

Kita memerlukan:

$$
\boxed{
\Sigma_t
=
Cov(
\mathbf r_{t+1}
\mid\mathcal F_t
).
}
$$

Untuk factor model:

$$
\boxed{
\Sigma_t
=
B_tF_tB_t^T
+
D_t
}
$$

dengan:

$$
F_t=Cov(\mathbf f_t)
$$

dan:

$$
D_t=Cov(\boldsymbol\epsilon_t).
$$

---

# J.12. Mengapa factor covariance penting?

Jika:

$$
BTC
$$

dan:

$$
ETH
$$

bergerak bersama, covariance mereka tidak boleh dianggap independen.

Demikian pula:

$$
Gold
$$

dan:

$$
DXY
$$

memiliki hubungan makro yang dapat mempengaruhi portfolio.

Dengan factor model:

$$
\Sigma
$$

mempunyai struktur yang lebih interpretable.

---

# J.13. Portfolio weights

Definisikan:

$$
\boxed{
\mathbf w_t
=
(w_{1,t},\ldots,w_{N,t})^T.
}
$$

Jika long-only fully invested:

$$
\boxed{
w_i\geq0
}
$$

dan:

$$
\boxed{
\sum_iw_i=1.
}
$$

Tetapi untuk sistem trading kita, saya menyarankan **memisahkan asset selection dan position sizing**.

---

# J.14. Asset selection

Definisikan:

$$
x_{i,t}\in\{0,1\}.
$$

Dengan:

$$
x_{i,t}=1
$$

jika asset $i$ dipilih.

Cardinality constraint:

$$
\boxed{
\sum_i x_{i,t}\leq K.
}
$$

Ini adalah salah satu sumber naturally combinatorial optimization.

---

# J.15. Position sizing

Kemudian:

$$
\boxed{
w_{i,t}=x_{i,t}z_{i,t}
}
$$

dengan:

$$
z_{i,t}
$$

sebagai size conditional on selection.

Contohnya:

$$
z_i
\propto
\frac{\hat\mu_i}{\hat\sigma_i^2}.
$$

Atau:

$$
z_i
\propto
\frac{signal_i}{risk_i}.
$$

---

# J.16. Risk budget

Kita tidak ingin:

$$
w_i
$$

ditentukan hanya oleh expected return.

Definisikan portfolio variance:

$$
\boxed{
\sigma_p^2
=
\mathbf w^T\Sigma\mathbf w.
}
$$

Kemudian risk constraint:

$$
\boxed{
\mathbf w^T\Sigma\mathbf w
\leq
\sigma_{\max}^2.
}
$$

---

# J.17. Factor exposure constraint

Karena kita mengetahui:

$$
B,
$$

kita dapat membatasi:

$$
\boxed{
\mathbf e_t
=
B_t^T\mathbf w_t.
}
$$

Misalnya:

$$
|e_{DXY}|\leq E_{DXY}^{max}.
$$

atau:

$$
|e_{BTC}|\leq E_{BTC}^{max}.
$$

Ini mencegah portfolio diam-diam menjadi taruhan besar terhadap satu factor.

---

# J.18. Portfolio objective

Objective continuous ideal kita:

$$
\boxed{
\max_{\mathbf w}
\quad
\hat{\boldsymbol\mu}^T\mathbf w
-
\lambda
\mathbf w^T\Sigma\mathbf w
-
\kappa TC(\mathbf w,\mathbf w_{t-1})
-
\eta R(\mathbf w).
}
$$

Empat komponennya:

$$
\text{return}
-
\text{risk}
-
\text{transaction cost}
-
\text{tail/factor risk}.
$$

---

# J.19. Mengubah maximization menjadi minimization

Quantum optimization lebih mudah kita tulis sebagai:

$$
\boxed{
\min_{\mathbf w}
\quad
\lambda\mathbf w^T\Sigma\mathbf w
-
\hat{\boldsymbol\mu}^T\mathbf w
+
\kappa TC
+
\eta R.
}
$$

Definisikan:

$$
C(\mathbf w).
$$

Maka:

$$
\boxed{
\mathbf w^\star
=
\arg\min_{\mathbf w}
C(\mathbf w).
}
$$

---

# J.20. Tetapi QAOA membutuhkan binary variables

Maka kita harus melakukan discretization.

Misalnya size:

$$
w_i
=
\delta
\sum_{k=0}^{M-1}
2^k b_{ik}
$$

dengan:

$$
b_{ik}\in\{0,1\}.
$$

Ini adalah **binary encoding**.

---

# J.21. Binary representation

Misalnya:

$$
w_i
=
\delta
(b_{i0}+2b_{i1}+4b_{i2}).
$$

Maka kemungkinan:

$$
0,\delta,2\delta,\ldots,7\delta.
$$

Jika:

$$
\delta=0.01,
$$

maka:

$$
w_i\in
\{0,0.01,\ldots,0.07\}.
$$

---

# J.22. Selection + sizing

Kita dapat langsung menggunakan:

$$
x_i
$$

untuk selection dan:

$$
b_{ik}
$$

untuk size.

Hubungkan keduanya:

$$
w_i
\leq
w_i^{max}x_i.
$$

Dalam binary formulation, constraint ini dapat dipenalti.

---

# J.23. Constraint penalty

Misalkan:

$$
\sum_iw_i=1.
$$

Kita tambahkan:

$$
\boxed{
P_{budget}
=
A
\left(
\sum_iw_i-1
\right)^2.
}
$$

Sehingga objective:

$$
C(\mathbf w)
=
\lambda w^T\Sigma w
-
\mu^Tw
+
A
(\mathbf1^Tw-1)^2.
$$

---

# J.24. Cardinality penalty

Untuk:

$$
\sum_i x_i\leq K,
$$

kita dapat menggunakan:

$$
P_{card}
=
B
\max
\left(
0,\sum_ix_i-K
\right)^2.
$$

Untuk QUBO murni, kita dapat menggunakan slack variable.

---

# J.25. Slack variable

Ubah:

$$
\sum_i x_i\leq K
$$

menjadi:

$$
\boxed{
\sum_i x_i+s=K.
}
$$

dengan:

$$
s\geq0.
$$

Kemudian representasikan $s$ secara binary.

---

# J.26. QUBO final

Secara umum:

$$
\boxed{
C(\mathbf z)
=
\mathbf z^TQ_t\mathbf z
+
\mathbf c_t^T\mathbf z
+
c_0.
}
$$

dengan:

$$
\mathbf z\in\{0,1\}^M.
$$

Di sinilah seluruh financial problem kita akhirnya masuk ke bentuk combinatorial optimization.

---

# J.27. Dari QUBO ke Ising

Kita menggunakan:

$$
\boxed{
z_i
=
\frac{1+s_i}{2}
}
$$

dengan:

$$
s_i\in\{-1,+1\}.
$$

Substitusi ke:

$$
C(\mathbf z).
$$

Maka:

$$
\boxed{
C(\mathbf s)
=
C_0
+
\sum_i h_i s_i
+
\sum_{i<j}J_{ij}s_is_j.
}
$$

---

# J.28. Hamiltonian

Kita kemudian mengganti:

$$
s_i
\rightarrow
Z_i.
$$

Sehingga:

$$
\boxed{
\hat H_C
=
C_0I
+
\sum_i h_iZ_i
+
\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

Inilah **cost Hamiltonian**.

---

# J.29. Mengapa Hamiltonian ini sangat penting?

Karena:

$$
\boxed{
\hat H_C|z\rangle
=
C(z)|z\rangle.
}
$$

Dengan kata lain setiap computational basis state:

$$
|z\rangle
$$

merepresentasikan satu portfolio candidate.

Eigenvalue-nya:

$$
C(z).
$$

Maka:

$$
\boxed{
\text{ground state}
=
\text{optimal portfolio}.
}
$$

---

# J.30. QAOA

Kita mulai dari:

$$
|+\rangle^{\otimes M}.
$$

Kemudian:

$$
\boxed{
|\psi(\boldsymbol\gamma,\boldsymbol\beta)\rangle
=
\prod_{\ell=1}^{p}
e^{-i\beta_\ell H_M}
e^{-i\gamma_\ell H_C}
|+\rangle^{\otimes M}.
}
$$

---

# J.31. Mixer Hamiltonian

Untuk unconstrained QAOA:

$$
\boxed{
H_M
=
\sum_iX_i.
}
$$

Tetapi nanti untuk constraint yang lebih ketat kita dapat menggunakan:

$$
\boxed{
H_M^{constraint}.
}
$$

agar evolution tidak keluar dari feasible subspace.

Ini akan menjadi pengembangan penting.

---

# J.32. Parameter optimization

Kita mencari:

$$
\boxed{
(\gamma^\star,\beta^\star)
=
\arg\min_{\gamma,\beta}
\langle
\psi(\gamma,\beta)
|
H_C
|
\psi(\gamma,\beta)
\rangle.
}
$$

Objective:

$$
E(\gamma,\beta).
$$

---

# J.33. Measurement

Setelah optimal:

$$
|\psi^\star\rangle,
$$

kita lakukan measurement.

Probability:

$$
\boxed{
p(z)
=
|\langle z|\psi^\star\rangle|^2.
}
$$

Kita mengambil:

$$
z^\star
=
\arg\max_zp(z)
$$

atau best feasible sample.

---

# J.34. Dari binary solution ke portfolio

Setelah measurement:

$$
z^\star,
$$

decode:

$$
z^\star
\rightarrow
x^\star
\rightarrow
w^\star.
$$

Kemudian:

$$
\boxed{
w^\star_t
=
Decode(
Measure(
QAOA(Q_t)
)).
}
$$

---

# J.35. Risk-based capital allocation

Di sini kita perlu memisahkan **portfolio optimization** dari **trade risk management**.

Misalnya portfolio menentukan:

$$
w_i^\star.
$$

Tetapi trade-level risk menentukan:

$$
R_i.
$$

Jika modal:

$$
A_t,
$$

dan risk budget:

$$
\rho A_t,
$$

maka:

$$
\boxed{
R_{max,t}
=
\rho A_t.
}
$$

Misalnya:

$$
\rho=0.01.
$$

Maka:

$$
R_{max}=1\%\times A_t.
$$

---

# J.36. Stop loss

Untuk posisi long:

$$
P_{SL}
=
P_{entry}
-
d_{SL}.
$$

Risk per unit:

$$
r_i
=
P_{entry}-P_{SL}.
$$

Position size:

$$
\boxed{
Q_i
=
\frac{R_{max}}
{r_i}.
}
$$

Dengan demikian:

$$
Q_i r_i
=
R_{max}.
$$

Ini adalah mathematical foundation dari ide kita sebelumnya:

> **setiap trade tetap memiliki risk sekitar \$1.**

---

# J.37. Volatility-adjusted stop

Daripada fixed distance:

$$
d_{SL}=constant,
$$

kita gunakan:

$$
\boxed{
d_{SL}
=
k\sigma_i
}
$$

atau:

$$
d_{SL}
=
k ATR_i.
$$

Sehingga:

$$
Q_i
=
\frac{R_{max}}
{k\sigma_i}.
$$

Volatility tinggi:

$$
\sigma\uparrow
\Rightarrow
Q\downarrow.
$$

Volatility rendah:

$$
\sigma\downarrow
\Rightarrow
Q\uparrow.
$$

Ini secara finansial jauh lebih masuk akal.

---

# J.38. Take profit

Misalnya:

$$
P_{TP}
=
P_{entry}
+
k_{TP}\sigma_i.
$$

Risk-reward ratio:

$$
\boxed{
RR
=
\frac{
|P_{TP}-P_{entry}|
}{
|P_{entry}-P_{SL}|
}.
}
$$

Tetapi kita tidak akan membuat:

$$
RR=2
$$

secara arbitrer.

Idealnya:

$$
TP
$$

ditentukan berdasarkan conditional return distribution.

---

# J.39. TP berbasis distribution

Misalkan:

$$
R_{i,t+H}
\sim
F_i.
$$

Kita dapat menentukan TP sebagai quantile:

$$
\boxed{
TP
=
Q_{q}
(
R_{i,t+H}
).
}
$$

Misalnya:

$$
q=0.75.
$$

---

# J.40. Dynamic trade management

Setelah posisi terbuka:

$$
state_t^{trade}
=
(
P_t,
P_{entry},
P_{SL},
P_{TP},
PnL_t,
\sigma_t,
\mu_t,
regime_t
).
$$

Kita definisikan action:

$$
a_t^{trade}
\in
\{
Hold,
Close,
MoveSL,
MoveTP
\}.
$$

---

# J.41. Floating loss

Jika:

$$
PnL_t<0,
$$

kita tidak otomatis close.

Kita evaluasi:

$$
P(
R_{future}>0
\mid
\mathcal F_t).
$$

Jika probabilitas masih tinggi:

$$
P_{win}\geq p_{min},
$$

position dapat dipertahankan.

---

# J.42. Floating profit

Jika:

$$
PnL_t>0,
$$

kita dapat menghitung:

$$
P(
R_{future}>0
\mid
\mathcal F_t).
$$

Kemudian:

$$
\boxed{
\text{expected continuation value}
}
$$

dibandingkan dengan:

$$
\boxed{
\text{value of closing}.
}
$$

---

# J.43. Continuation value

Definisikan:

$$
V_{hold}(t)
=
E[
PnL_{future}
\mid
\mathcal F_t,
Hold
].
$$

Sedangkan:

$$
V_{close}(t)
=
PnL_t.
$$

Maka:

$$
\boxed{
Hold
\quad\text{jika}\quad
V_{hold}>V_{close}.
}
$$

Ini mengubah trailing stop dari rule arbitrer menjadi decision problem.

---

# J.44. Stop-loss adjustment

Jika:

$$
P_t>P_{entry}
$$

cukup jauh, kita dapat memindahkan SL.

Definisikan:

$$
P_{SL,new}
=
P_t-k\sigma_t.
$$

Tetapi harus memenuhi:

$$
P_{SL,new}>P_{SL,old}.
$$

Dengan demikian stop hanya bergerak ke arah profit protection.

---

# J.45. Dynamic TP

Jika momentum masih kuat:

$$
\hat\mu_t>0
$$

dan:

$$
P(
R_{future}>0)
$$

tinggi, TP dapat diperbesar.

Misalnya:

$$
\boxed{
TP_{new}
=
P_t+
k_{TP,t}\sigma_t
}
$$

dengan:

$$
k_{TP,t}
=
f(
\hat\mu_t,
\sigma_t,
regime_t,
liquidity_t
).
$$

---

# J.46. Tetapi kita harus mencegah infinite TP expansion

Jika tidak:

$$
TP\rightarrow\infty.
$$

Maka:

$$
k_{TP,t}
\leq
k_{max}.
$$

Selain itu:

$$
\frac{dTP}{dt}
$$

harus dibatasi.

---

# J.47. Portfolio reoptimization

Pada interval:

$$
\tau_r
$$

kita melakukan:

$$
\boxed{
\mathbf w_{t+\tau_r}^{\star}
=
Optimize(
\hat\mu_{t+\tau_r},
\Sigma_{t+\tau_r},
B_{t+\tau_r},
Regime_{t+\tau_r}
).
}
$$

Jadi portfolio tidak statis.

---

# J.48. Reoptimization trigger

Tidak harus berdasarkan waktu saja.

Kita dapat memiliki:

$$
Trigger_t
=
\mathbf1[
D(S_t,S_{t-1})>\delta
].
$$

Jika market state berubah cukup besar:

$$
Trigger_t=1.
$$

Maka:

$$
Reoptimize.
$$

---

# J.49. Distance antar-regime

Misalnya:

$$
D_t
=
\|
\mathbf s_t-\mathbf s_{t-1}
\|_2.
$$

Jika:

$$
D_t>\delta,
$$

kita menganggap market state berubah signifikan.

---

# J.50. Full state vector

Sekarang kita dapat mendefinisikan state:

$$
\boxed{
S_t
=
\begin{bmatrix}
\mathbf r_t\\
\mathbf f_t\\
\hat{\boldsymbol\mu}_t\\
\operatorname{diag}(\Sigma_t)\\
\mathbf B_t\\
Regime_t\\
Liquidity_t\\
Position_t\\
PnL_t
\end{bmatrix}.
}
$$

Ini merupakan informasi yang digunakan oleh policy.

---

# J.51. Action vector

Definisikan:

$$
\boxed{
A_t
=
(
\mathbf w_t,
\mathbf Q_t,
\mathbf P_{SL,t},
\mathbf P_{TP,t},
\mathbf O_t
).
}
$$

dengan:

- $\mathbf w_t$: target portfolio,
- $\mathbf Q_t$: order size,
- $P_{SL}$: stop-loss,
- $P_{TP}$: take-profit,
- $\mathbf O_t$: order type/status.

---

# J.52. State transition

Market bergerak:

$$
S_t
\rightarrow
S_{t+1}.
$$

Secara umum:

$$
\boxed{
S_{t+1}
\sim
P(
S_{t+1}\mid S_t,A_t
).
}
$$

Ini adalah stochastic transition model.

---

# J.53. Reward

Reward utama:

$$
\boxed{
R_t
=
PnL_t
-
TC_t
-
Impact_t
-
RiskPenalty_t.
}
$$

Misalnya:

$$
RiskPenalty_t
=
\lambda\sigma_{p,t}^2.
$$

Maka:

$$
\boxed{
R_t
=
w_t^Tr_{t+1}
-
TC_t
-
Impact_t
-
\lambda
w_t^T\Sigma_tw_t.
}
$$

---

# J.54. Objective global

Jika seluruh periode:

$$
t=1,\ldots,T,
$$

maka:

$$
\boxed{
J(\pi)
=
E_\pi
\left[
\sum_{t=1}^{T}
R_t
\right].
}
$$

Inilah objective global sistem.

Tetapi implementasi kita tidak harus memakai RL.

Policy:

$$
\pi
$$

dapat dibentuk secara modular dari:

$$
Forecast
+
Risk
+
QAOA
+
Execution
+
Trade Management.
$$

---

# J.55. Full mathematical pipeline

Sekarang kita dapat menulis sistem kita secara ringkas:

$$
\boxed{
\mathcal F_t
\rightarrow
S_t
}
$$

kemudian:

$$
\boxed{
S_t
\rightarrow
(\hat\mu_t,\Sigma_t,B_t,Regime_t)
}
$$

kemudian:

$$
\boxed{
(\hat\mu_t,\Sigma_t,B_t)
\rightarrow
Q_t
}
$$

kemudian:

$$
\boxed{
Q_t
\rightarrow
H_{C,t}
}
$$

kemudian:

$$
\boxed{
H_{C,t}
\overset{QAOA}{\longrightarrow}
z_t^\star
}
$$

kemudian:

$$
\boxed{
z_t^\star
\rightarrow
w_t^\star
}
$$

kemudian:

$$
\boxed{
w_t^\star
\rightarrow
Order_t
}
$$

kemudian:

$$
\boxed{
Order_t
\rightarrow
Position_t
}
$$

kemudian:

$$
\boxed{
Position_t
\rightarrow
PnL_{t+1}.
}
$$

---

# J.56. Closed-loop system

Dan yang paling penting:

$$
PnL_{t+1}
$$

menjadi bagian dari:

$$
\mathcal F_{t+1}.
$$

Sehingga:

$$
\boxed{
\mathcal F_t
\rightarrow
A_t
\rightarrow
PnL_{t+1}
\rightarrow
\mathcal F_{t+1}
\rightarrow
A_{t+1}
\rightarrow\cdots
}
$$

Ini membuat sistem kita **closed-loop**.

---

# J.57. Arsitektur matematis lengkap

Jika kita gambarkan:

```text
                     MARKET
                       │
                       ▼
              ┌─────────────────┐
              │ Raw Data D_t    │
              │ Price/Volume/OB  │
              │ BTC/ETH/Gold/USD │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Feature Engine  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ State Estimator │
              │ μ, Σ, B, Regime │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Financial Model │
              │ Return/Risk     │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ QUBO Generator  │
              └────────┬────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
        Classical             QAOA
        Optimizer             Optimizer
              │                 │
              └────────┬────────┘
                       ▼
                 Target Portfolio
                       │
                       ▼
                 Risk Allocation
                       │
                       ▼
               Order Construction
                       │
                       ▼
                 Execution Model
                       │
                       ▼
                 Open Position
                       │
             ┌─────────┴─────────┐
             │                   │
             ▼                   ▼
          TP / SL            Monitoring
             │                   │
             └─────────┬─────────┘
                       ▼
                     PnL
                       │
                       ▼
                  New State
```

---

# J.58. Satu hal penting: QAOA bukan keseluruhan trading system

Ini harus kita pegang.

QAOA hanya berada di:

$$
\boxed{
\text{Optimization Layer}.
}
$$

Bukan:

$$
\text{Prediction Layer}.
$$

Bukan:

$$
\text{Execution Layer}.
$$

Bukan:

$$
\text{Risk Management Layer}.
$$

Sehingga:

$$
\boxed{
Trading\ System
\neq
QAOA.
}
$$

Lebih tepat:

$$
\boxed{
Trading\ System
=
Forecast
+
Risk
+
Optimization
+
Execution
+
Control.
}
$$

QAOA adalah salah satu optimizer yang kita uji di dalamnya.

---

# J.59. Ini juga membuat eksperimen kita jauh lebih bersih

Kita dapat mengganti:

$$
Optimizer
$$

tanpa mengubah komponen lain.

Misalnya:

$$
\mathcal O_1
=
Classical
$$

dan:

$$
\mathcal O_2
=
QAOA.
$$

Maka:

$$
\boxed{
\pi_{classical}
=
Risk\circ
Classical\circ
Forecast
}
$$

sedangkan:

$$
\boxed{
\pi_{QAOA}
=
Risk\circ
QAOA\circ
Forecast.
}
$$

Semua komponen lainnya identik.

---

# J.60. Formulasi penelitian paling penting

Kalau seluruh proyek ini akhirnya kita jadikan paper/skripsi yang serius, saya akan merumuskan pertanyaan utamanya sebagai:

$$
\boxed{
\textit{
Can a quantum approximate optimization procedure provide
competitive solutions to dynamic, factor-aware, risk-constrained
short-horizon portfolio optimization under realistic trading costs?
}
}
$$

Bukan:

> "Apakah quantum computing bisa menghasilkan profit?"

Itu pertanyaan yang terlalu sederhana.

---

# J.61. Dan hipotesisnya

Kita dapat memiliki:

### H₀

Tidak terdapat perbedaan signifikan antara QAOA dan classical optimization:

$$
H_0:
J_{QAOA}=J_{classical}.
$$

### H₁

QAOA menghasilkan performa yang berbeda:

$$
H_1:
J_{QAOA}\neq J_{classical}.
$$

Atau jika kita ingin menguji keunggulan:

$$
H_1:
J_{QAOA}>J_{classical}.
$$

Tetapi kita harus membiarkan data menentukan hasilnya.

---

# J.62. Yang menarik: kita sekarang memiliki tiga "ground truth"

Untuk ukuran kecil:

$$
\boxed{
Exact\ Optimization
}
$$

memberikan:

$$
C^\star.
$$

Kemudian:

$$
\boxed{
Classical\ Approximation
}
$$

memberikan:

$$
C_{classical}.
$$

Dan:

$$
\boxed{
QAOA
}
$$

memberikan:

$$
C_{QAOA}.
$$

Sehingga:

$$
C^\star
\leq
C_{classical},
C_{QAOA}.
$$

Untuk minimization.

Kemudian kita dapat mengukur:

$$
Gap_{classical}
=
\frac{C_{classical}-C^\star}{|C^\star|}
$$

dan:

$$
Gap_{QAOA}
=
\frac{C_{QAOA}-C^\star}{|C^\star|}.
$$

Ini memberi kita **ground-truth mathematical benchmark**.

---

# J.63. Baru setelah itu kita lihat uang

Kemudian:

$$
C^\star
\rightarrow
Portfolio^\star
\rightarrow
PnL^\star.
$$

dan:

$$
C_{QAOA}
\rightarrow
Portfolio_{QAOA}
\rightarrow
PnL_{QAOA}.
$$

Ini memungkinkan kita menjawab pertanyaan menarik:

$$
\boxed{
\text{Apakah improvement dalam optimization objective}
\Rightarrow
\text{improvement dalam financial outcome?}
}
$$

Jawabannya belum tentu.

Dan justru **ketidaksetaraan tersebut merupakan sesuatu yang sangat menarik untuk diteliti**.

---

# J.64. Spesifikasi akhir kita

Jadi secara matematis sistem kita dapat diringkas menjadi:

$$
\boxed{
\begin{aligned}
\mathbf r_t
&=
B_t\mathbf f_t+\boldsymbol\epsilon_t,
\\[2mm]
\hat{\boldsymbol\mu}_{t+1}
&=
E[\mathbf r_{t+1}|\mathcal F_t],
\\[2mm]
\Sigma_t
&=
B_tF_tB_t^T+D_t,
\\[2mm]
\mathbf w_t^\star
&=
\arg\min_{\mathbf w}
\left[
\lambda\mathbf w^T\Sigma_t\mathbf w
-
\hat{\boldsymbol\mu}_{t+1}^T\mathbf w
+
TC_t
+
R_t
\right],
\\[2mm]
\mathbf w
&\rightarrow
\mathbf z\in\{0,1\}^M,
\\[2mm]
C_t(\mathbf z)
&=
\mathbf z^TQ_t\mathbf z+
\mathbf c_t^T\mathbf z+c_0,
\\[2mm]
\mathbf z
&\rightarrow
\mathbf s,
\\[2mm]
C_t(\mathbf s)
&=
C_0+
\sum_i h_i s_i+
\sum_{i<j}J_{ij}s_is_j,
\\[2mm]
H_{C,t}
&=
C_0I+
\sum_i h_iZ_i+
\sum_{i<j}J_{ij}Z_iZ_j,
\\[2mm]
|\psi_t\rangle
&=
\prod_{\ell=1}^{p}
e^{-i\beta_{\ell,t}H_M}
e^{-i\gamma_{\ell,t}H_{C,t}}
|+\rangle^{\otimes M},
\\[2mm]
(\gamma_t^\star,\beta_t^\star)
&=
\arg\min_{\gamma,\beta}
\langle H_{C,t}\rangle,
\\[2mm]
\mathbf z_t^\star
&=
Measure(|\psi_t^\star\rangle),
\\[2mm]
Q_t^{trade}
&=
\frac{R_{max,t}}
{|P_{entry,t}-P_{SL,t}|},
\\[2mm]
PnL_{t+1}
&=
w_t^T\mathbf r_{t+1}
-
TC_t
-
Impact_t,
\\[2mm]
\mathcal F_{t+1}
&=
\mathcal F_t
\cup
\{
D_{t+1},PnL_{t+1}
\}.
\end{aligned}
}
$$

**Ini adalah mathematical backbone dari keseluruhan sistem kita.**

---

## J.65. Satu perubahan desain yang saya rekomendasikan

Setelah menyatukan A–J, saya justru ingin sedikit mengubah filosofi sistem kita:

Jangan membuat:

$$
\boxed{
QAOA\rightarrow BUY/SELL
}
$$

secara langsung.

Lebih baik:

$$
\boxed{
Market
\rightarrow
State
\rightarrow
Forecast
\rightarrow
Risk
\rightarrow
Portfolio
\rightarrow
QUBO
\rightarrow
QAOA
\rightarrow
Target\ Allocation
\rightarrow
Execution.
}
$$

Dengan begitu **QAOA menyelesaikan masalah yang memang cocok untuk quantum optimization**, yaitu:

$$
\boxed{
\text{discrete, constrained, combinatorial allocation}.
}
$$

Sementara forecasting tetap menggunakan metode statistik/machine learning yang memang cocok untuk forecasting, dan execution tetap menggunakan model microstructure.

Itu membuat keseluruhan sistem jauh lebih masuk akal secara finansial **dan** jauh lebih kuat secara ilmiah.

---

# J.66. Setelah J, kita sebenarnya sudah siap masuk ke implementasi

Tetapi ada satu tahap yang menurut saya **sangat berharga sebelum coding**:

## Tahap K — Concrete Market Specification

Di Tahap K kita berhenti berbicara secara abstrak dan menentukan **satu instansiasi nyata** dari seluruh framework.

Misalnya kita menetapkan:

$$
\boxed{
Universe=
\{
BTC,ETH,SOL,\ldots
\}
}
$$

untuk crypto, lalu:

$$
\boxed{
Factors=
\{
BTC,ETH,DXY,Gold,SPX,VIX
\}.
}
$$

Kemudian menentukan secara eksplisit:

- timeframe,
- data source,
- lookback window,
- forecast horizon,
- model forecasting,
- covariance estimator,
- regime model,
- jumlah asset yang boleh dipilih,
- discretization weight,
- seluruh QUBO coefficient,
- penalty coefficient,
- encoding qubit,
- QAOA depth $p$,
- mixer,
- optimizer,
- risk budget,
- SL,
- TP,
- trailing logic,
- reoptimization interval,
- transaction cost,
- slippage,
- walk-forward scheme,
- dan **baseline classical optimizer**.

Dengan kata lain:

$$
\boxed{
\text{Tahap J = Mathematical Blueprint}
}
$$

sedangkan:

$$
\boxed{
\text{Tahap K = Numerical/Experimental Specification}.
}
$$

Setelah K selesai, kita dapat membuat **versi 1.0 dari algoritma lengkap**, pseudocode end-to-end, struktur repository, database schema, dan kemudian mulai mengimplementasikannya secara modular tanpa lagi mengubah-ubah definisi matematis di tengah coding.

## Prompt:
8/17/2026, 9:54:27 PM

lanjut Tahap K

## Response:
8/17/2026, 9:54:28 PM

> **Remembering**
>
>
> ****
>
> 
>
> **Clarified Stage J/K trading system and QAOA portfolio design**
>
> 
>
> Worked for 6s

# Tahap K — Concrete Market & Numerical Specification

Sekarang kita masuk ke tahap yang menurut saya **lebih penting daripada sekadar mulai coding**.

Pada Tahap J kita sudah mempunyai:

$$
\boxed{\text{kerangka matematis abstrak}}
$$

Pada Tahap K kita akan menentukan **angka, variabel, data, horizon, constraint, encoding, dan prosedur eksperimen secara konkret** sehingga sistem tersebut dapat benar-benar diimplementasikan.

Saya akan membuat Tahap K sebagai **spesifikasi V1.0**. Artinya, kita jangan langsung membuat sistem terlalu kompleks. Kita buat sistem yang cukup kecil untuk divalidasi secara matematis, tetapi arsitekturnya sudah mampu berkembang dari crypto ke saham internasional.

---

# K.1. Prinsip desain utama

Ada satu keputusan yang sangat penting:

> **Jangan langsung mencoba membuat "hedge-fund-grade system" dalam versi pertama.**

Kita akan membuat:

$$
\boxed{
V1 =
\text{small but mathematically rigorous}
}
$$

Kemudian:

$$
V1
\rightarrow
V2
\rightarrow
V3
\rightarrow
\cdots
$$

Dengan demikian setiap peningkatan dapat diuji secara independen.

---

# K.2. Universe V1

Untuk tahap pertama saya memilih **6 aset crypto** sebagai universe utama:

$$
\boxed{
\mathcal U_C=
\{
BTC,ETH,SOL,BNB,XRP,ADA
\}
}
$$

Alasannya bukan karena enam aset ini pasti merupakan pilihan trading terbaik, tetapi karena jumlah ini cukup untuk menghasilkan masalah kombinatorial namun masih sangat mudah diverifikasi secara exact.

Jumlah aset:

$$
N=6.
$$

Kemudian kita mempunyai beberapa **factor assets** yang tidak harus masuk ke portfolio:

$$
\boxed{
\mathcal F=
\{
BTC,ETH,DXY,Gold,SPX,VIX
\}.
}
$$

BTC dan ETH dapat berfungsi ganda sebagai:

1. tradable asset,
2. market factor.

---

# K.3. Mengapa kita tidak langsung menggunakan 50–500 aset?

Karena kita ingin membandingkan:

$$
Exact
$$

melawan:

$$
Classical
$$

melawan:

$$
QAOA.
$$

Untuk $N=6$, jika setiap aset hanya mempunyai binary selection:

$$
2^6=64
$$

portfolio.

Itu sangat kecil.

Kita dapat melakukan:

$$
\boxed{
brute\ force
}
$$

untuk menemukan global optimum secara pasti.

Ini menjadi **ground truth**.

Kemudian kita dapat meningkatkan kompleksitas.

---

# K.4. Tahap eskalasi ukuran

Saya menyarankan:

| Experiment | Assets | Binary variables | Tujuan |
|---|---:|---:|---|
| E1 | 4 | 4–8 | Validasi matematis |
| E2 | 6 | 6–12 | Benchmark exact |
| E3 | 10 | 10–20 | QUBO benchmark |
| E4 | 20 | 20–40 | Scaling |
| E5 | 50+ | 50+ | Realistic portfolio |

Dengan demikian:

$$
\boxed{
E1\rightarrow E2\rightarrow E3\rightarrow E4\rightarrow E5
}
$$

dan bukan langsung melompat ke E5.

---

# K.5. Timeframe utama

Untuk V1 kita menggunakan:

$$
\boxed{
\Delta t=1\ hour
}
$$

sebagai timeframe trading.

Mengapa?

Karena kita ingin berada di antara:

- terlalu cepat seperti HFT,
- terlalu lambat seperti daily portfolio management.

Jadi sistem kita adalah:

$$
\boxed{
short\ horizon\ systematic\ trading
}
$$

bukan HFT.

---

# K.6. Forecast horizon

Forecast utama:

$$
\boxed{
H=1h.
}
$$

Sehingga:

$$
\hat\mu_{i,t}
=
E[
r_{i,t+1h}
\mid\mathcal F_t
].
$$

Namun kita juga akan menghitung:

$$
H\in
\{1h,4h,24h\}
$$

untuk **trade management**, bukan sebagai tiga model terpisah pada tahap pertama.

---

# K.7. Training window

Kita menggunakan rolling window:

$$
\boxed{
W=30\text{ days}
}
$$

untuk V1.

Karena:

$$
30\times24=720
$$

observasi hourly.

Jadi pada waktu $t$:

$$
\mathcal D_t
=
\{
\mathbf r_{t-719},
\ldots,
\mathbf r_t
\}.
$$

---

# K.8. Mengapa rolling window?

Karena kita tidak ingin mengasumsikan:

$$
P(\mathbf r_{t+1}\mid\mathcal F_t)
=
P(\mathbf r_{t+1})
$$

selamanya sama.

Pasar memiliki:

$$
\boxed{
non-stationarity.
}
$$

Dengan rolling window:

$$
\theta_t
=
f(
D_{t-W:t}
)
$$

sehingga parameter dapat berubah terhadap waktu.

---

# K.9. Data yang dibutuhkan

Untuk setiap asset:

$$
\boxed{
OHLCV
}
$$

yaitu:

- Open,
- High,
- Low,
- Close,
- Volume.

Selain itu:

$$
\boxed{
market\ factors
}
$$

dan kemudian, pada versi berikutnya:

$$
\boxed{
order\ book.
}
$$

---

# K.10. Kita jangan langsung memasukkan order book ke V1

Ini keputusan desain yang penting.

Order book memiliki dimensi yang jauh lebih besar:

$$
Bid_1,\ldots,Bid_L
$$

$$
Ask_1,\ldots,Ask_L
$$

beserta:

$$
Q^{bid}_l,\quad Q^{ask}_l.
$$

Kalau kita memasukkannya sekarang, kita akan sulit mengetahui apakah perubahan performa berasal dari:

- forecasting,
- factor model,
- QUBO,
- QAOA,
- atau microstructure.

Jadi:

$$
\boxed{
V1:
OHLCV + factors
}
$$

dan:

$$
\boxed{
V2:
+ order\ book.
}
$$

---

# K.11. Return

Gunakan:

$$
\boxed{
r_{i,t}
=
\ln
\frac{P_{i,t}}
{P_{i,t-1}}
}
$$

seperti yang sudah kita tetapkan.

---

# K.12. Feature vector

Untuk setiap asset $i$, kita buat:

$$
\mathbf x_{i,t}
=
[
r_{i,t}^{(1)},
r_{i,t}^{(4)},
r_{i,t}^{(24)},
\sigma_{i,t},
v_{i,t},
\beta_{BTC,i,t},
\beta_{ETH,i,t},
\beta_{DXY,i,t},
\beta_{Gold,i,t}
]^T.
$$

Di sini:

$$
r^{(H)}
=
\sum_{k=0}^{H-1}r_{t-k}.
$$

---

# K.13. Volatility

Rolling volatility:

$$
\boxed{
\sigma_{i,t}
=
\sqrt{
\frac{1}{W-1}
\sum_{\tau=t-W+1}^{t}
(r_{i,\tau}-\bar r_i)^2
}
}
$$

dengan:

$$
\bar r_i
=
\frac1W
\sum_{\tau=t-W+1}^{t}r_{i,\tau}.
$$

---

# K.14. Volume feature

Gunakan normalized volume:

$$
\boxed{
v_{i,t}
=
\frac{
V_{i,t}
}{
EMA_W(V_i)
}.
}
$$

Sehingga:

$$
v_i>1
$$

berarti volume relatif tinggi.

---

# K.15. Factor exposure

Untuk setiap asset:

$$
\mathbf f_t=
[
r_{BTC,t},
r_{ETH,t},
r_{DXY,t},
r_{Gold,t},
r_{SPX,t},
r_{VIX,t}
]^T.
$$

Kemudian:

$$
r_{i,t}
=
\alpha_i+
\boldsymbol\beta_i^T\mathbf f_t+
\epsilon_{i,t}.
$$

---

# K.16. Forecast model V1

Kita jangan langsung menggunakan neural network.

V1 menggunakan model yang sangat interpretable:

$$
\boxed{
\hat r_{i,t+1}
=
\alpha_i+
\boldsymbol\theta_i^T\mathbf x_{i,t}.
}
$$

Secara vector:

$$
\boxed{
\hat{\boldsymbol\mu}_{t+1}
=
A_t+\Theta_tX_t.
}
$$

Ini sengaja sederhana.

Karena kalau QAOA kemudian memberikan hasil buruk, kita dapat mengatakan:

> masalahnya berasal dari optimization layer,

bukan:

> mungkin neural network-nya buruk.

---

# K.17. Regularisasi forecasting

Agar parameter tidak terlalu overfit:

$$
\boxed{
\min_\theta
\|
y-X\theta
\|_2^2
+
\lambda_f\|\theta\|_2^2.
}
$$

Ini adalah ridge regression.

Solusinya:

$$
\boxed{
\theta^\star
=
(X^TX+\lambda_fI)^{-1}X^Ty.
}
$$

---

# K.18. Covariance estimator

Untuk V1:

$$
\boxed{
\Sigma_t
=
\operatorname{Cov}
(
\mathbf r_{t-W+1:t}
).
}
$$

Tetapi untuk implementasi yang lebih stabil, saya menyarankan shrinkage:

$$
\boxed{
\Sigma_t^{shrunk}
=
(1-\rho)\Sigma_t
+
\rho D_t
}
$$

dengan:

$$
D_t=\operatorname{diag}(\Sigma_t).
$$

---

# K.19. Mengapa shrinkage?

Karena covariance matrix empiris dapat menjadi noisy.

Terutama ketika:

$$
N
$$

mendekati:

$$
W.
$$

Shrinkage membuat:

$$
\Sigma
$$

lebih stabil dan positive definite.

---

# K.20. Regime detection V1

Kita menggunakan tiga regime sederhana:

$$
\boxed{
Regime_t
\in
\{
Bull,
Neutral,
Bear
\}.
}
$$

Definisikan market return:

$$
r_{M,t}
=
\frac{1}{N}
\sum_i r_{i,t}.
$$

Kemudian:

$$
z_t
=
\frac{
EMA(r_M)-EMA_{long}(r_M)
}{
\sigma_M
}.
$$

Aturan sederhana:

$$
Regime_t=
\begin{cases}
Bull,&z_t>\delta\\
Neutral,&|z_t|\leq\delta\\
Bear,&z_t<-\delta.
\end{cases}
$$

---

# K.21. Tetapi regime jangan langsung menjadi constraint

Ini penting.

Regime pada V1 digunakan sebagai:

$$
\boxed{
feature
}
$$

dan bukan:

$$
hard\ constraint.
$$

Jadi model dapat belajar bahwa:

$$
Bear
$$

mungkin mengurangi expected return, tetapi tidak otomatis memaksa:

$$
w=0.
$$

---

# K.22. Universe selection

Setiap periode:

$$
t
$$

kita ranking asset berdasarkan:

$$
Score_i
=
\frac{
\hat\mu_i
}{
\hat\sigma_i
}.
$$

Kemudian pilih:

$$
K=3.
$$

Sehingga:

$$
\boxed{
\sum_i x_i\leq3.
}
$$

---

# K.23. Mengapa hanya tiga?

Karena kita ingin membuat:

$$
selection
+
allocation
$$

menjadi masalah combinatorial yang nyata.

Jika semua asset boleh dipilih:

$$
x_i=1
$$

untuk semuanya, masalah selection menjadi kurang menarik.

---

# K.24. Weight discretization

Gunakan step:

$$
\boxed{
\delta_w=0.05.
}
$$

Maka weight:

$$
w_i
\in
\{0,0.05,0.10,\ldots,0.50\}.
$$

Maximum per asset:

$$
w_i^{max}=0.50.
$$

---

# K.25. Binary encoding

Karena:

$$
0.50/0.05=10,
$$

kita membutuhkan representasi integer:

$$
q_i\in\{0,\ldots,10\}.
$$

Binary encoding:

$$
q_i
=
b_{i0}
+
2b_{i1}
+
4b_{i2}
+
8b_{i3}.
$$

Kemudian:

$$
\boxed{
w_i
=
0.05q_i.
}
$$

---

# K.26. Ada masalah dengan angka 8

Karena:

$$
q_i
$$

dengan empat bit dapat mencapai:

$$
15.
$$

Sedangkan maksimum kita hanya:

$$
10.
$$

Maka konfigurasi:

$$
q_i>10
$$

harus dibuat infeasible.

Kita dapat menambahkan:

$$
P_{range}.
$$

Ini contoh kecil tetapi penting dari desain QUBO.

---

# K.27. Budget constraint

Kita ingin:

$$
\boxed{
\sum_iw_i=1.
}
$$

Penalty:

$$
\boxed{
P_B
=
A_B
\left(
\sum_iw_i-1
\right)^2.
}
$$

---

# K.28. Cardinality constraint

$$
\sum_i x_i\leq3.
$$

Penalty:

$$
\boxed{
P_K
=
A_K
\max
\left(
0,
\sum_ix_i-3
\right)^2.
}
$$

Untuk QUBO murni nanti kita ubah menggunakan slack variable.

---

# K.29. Selection-size coupling

Kita harus memastikan:

$$
x_i=0
\Rightarrow
w_i=0.
$$

Gunakan:

$$
\boxed{
P_{coupling}
=
A_C
\sum_i
w_i(1-x_i).
}
$$

Jika:

$$
x_i=0
$$

tetapi:

$$
w_i>0,
$$

maka ada penalty.

---

# K.30. Financial objective V1

Kita gunakan:

$$
\boxed{
C(\mathbf w)
=
-\hat{\boldsymbol\mu}^T\mathbf w
+
\lambda
\mathbf w^T\Sigma\mathbf w
+
\kappa
\|\mathbf w-\mathbf w_{prev}\|_1.
}
$$

Tiga komponen:

$$
-\mu^Tw
$$

= reward expected return,

$$
\lambda w^T\Sigma w
$$

= risk,

dan:

$$
\kappa\|w-w_{prev}\|_1
$$

= turnover penalty.

---

# K.31. Mengapa turnover penting?

Tanpa turnover penalty:

$$
w_t^\star
$$

dapat berubah drastis setiap jam.

Misalnya:

$$
w_t=[0.5,0.3,0.2]
$$

kemudian satu jam kemudian:

$$
w_{t+1}=[0,0.1,0.9].
$$

Secara matematis mungkin optimal.

Secara trading:

$$
\boxed{\text{sangat mahal}}
$$

karena banyak transaksi.

---

# K.32. Transaction cost

Kita gunakan model awal:

$$
\boxed{
TC_t
=
c_{linear}
\sum_i
|w_{i,t}-w_{i,t-1}|
}
$$

dengan:

$$
c_{linear}
$$

sebagai biaya efektif.

Kemudian pada versi order-book:

$$
TC
=
Fee+
Spread+
Slippage+
MarketImpact.
$$

---

# K.33. Objective lengkap

Jadi:

$$
\boxed{
\begin{aligned}
C_t(\mathbf w,\mathbf x)
={}&
-\hat{\boldsymbol\mu}_t^T\mathbf w
+
\lambda
\mathbf w^T\Sigma_t\mathbf w
\\
&+
\kappa
\|\mathbf w-\mathbf w_{t-1}\|_1
\\
&+
A_B
(\mathbf1^T\mathbf w-1)^2
\\
&+
A_K
P_K(\mathbf x)
\\
&+
A_C
\sum_iw_i(1-x_i).
\end{aligned}
}
$$

---

# K.34. Risk aversion

Parameter:

$$
\boxed{\lambda}
$$

mengontrol:

$$
Return
\leftrightarrow
Risk.
$$

Jika:

$$
\lambda\rightarrow0,
$$

model semakin agresif.

Jika:

$$
\lambda\rightarrow\infty,
$$

model semakin konservatif.

Kita jangan menentukan $\lambda$ dengan melihat hasil backtest kemudian.

Itu akan menjadi:

$$
\boxed{data\ leakage}.
$$

---

# K.35. Parameter calibration

Kita menggunakan training period untuk menentukan:

$$
\lambda,
\kappa,
A_B,
A_K,A_C.
$$

Kemudian parameter dibekukan selama test period.

---

# K.36. Penentuan penalty coefficient

Penalty harus lebih besar daripada keuntungan yang mungkin diperoleh dari melanggar constraint.

Secara konseptual:

$$
\boxed{
A_{constraint}
>
\max|\Delta C_{financial}|.
}
$$

Sehingga:

$$
\text{constraint violation}
$$

tidak pernah lebih menguntungkan daripada solusi feasible.

---

# K.37. QUBO

Setelah semua binary substitution:

$$
w_i=w_i(\mathbf b_i)
$$

dan:

$$
x_i=b_{x_i},
$$

kita akan mendapatkan:

$$
\boxed{
C(\mathbf z)
=
\mathbf z^TQ\mathbf z
+
\mathbf c^T\mathbf z
+c.
}
$$

Dengan:

$$
\mathbf z\in\{0,1\}^M.
$$

---

# K.38. Jumlah qubit

Untuk enam asset:

### Selection

$$
6\text{ qubits}.
$$

### Weight

4 qubits per asset:

$$
6\times4=24.
$$

Total:

$$
\boxed{
M=30
}
$$

sebelum slack variables.

Ini sudah cukup besar untuk menunjukkan mengapa masalah ini menarik secara quantum optimization.

---

# K.39. Tetapi jangan langsung menjalankan QAOA 30 qubit

Ini sangat penting.

Untuk validasi:

$$
N=4
$$

terlebih dahulu.

Misalnya:

$$
M\approx20.
$$

Kemudian:

$$
N=6
$$

dan seterusnya.

---

# K.40. Classical exact solver

Untuk:

$$
M\leq25
$$

kita dapat menggunakan brute force jika memungkinkan.

Untuk setiap:

$$
z\in\{0,1\}^M
$$

hitung:

$$
C(z).
$$

Kemudian:

$$
\boxed{
z^\star
=
\arg\min_zC(z).
}
$$

Ini adalah ground truth.

---

# K.41. Classical optimization baseline

Kita tidak cukup hanya membandingkan:

$$
QAOA
$$

dengan brute force.

Kita perlu baseline realistis:

$$
\boxed{
MILP/QUBO classical solver
}
$$

dan:

$$
\boxed{
simulated\ annealing.
}
$$

Untuk continuous version:

$$
\boxed{
SLSQP
}
$$

atau optimizer constrained classical yang setara.

---

# K.42. Jadi kita mempunyai empat baseline

$$
\boxed{
Exact
}
$$

$$
\boxed{
Classical\ Continuous
}
$$

$$
\boxed{
Classical\ Combinatorial
}
$$

$$
\boxed{
QAOA
}
$$

Ini jauh lebih kuat daripada sekadar:

> "Saya menjalankan QAOA."

---

# K.43. QAOA V1

Cost Hamiltonian:

$$
\boxed{
H_C
=
\sum_i h_iZ_i
+
\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

Mixer:

$$
\boxed{
H_M
=
\sum_iX_i.
}
$$

Depth awal:

$$
\boxed{
p=1.
}
$$

Kemudian:

$$
p=2,3
$$

sebagai eksperimen scaling.

---

# K.44. Mengapa mulai dari $p=1$?

Karena:

$$
p\uparrow
$$

berarti:

- circuit semakin dalam,
- parameter semakin banyak,
- optimization semakin sulit,
- noise semakin besar jika hardware digunakan.

Kita ingin mengetahui apakah:

$$
p=1
$$

sudah memberikan solusi yang berguna.

---

# K.45. QAOA parameter optimizer

V1:

$$
\boxed{
COBYLA
}
$$

atau optimizer derivative-free sejenis.

Kemudian dibandingkan dengan:

$$
SPSA.
$$

Karena kita memang sebelumnya sudah mempelajari SPSA dan parameter-shift.

---

# K.46. Objective QAOA

$$
\boxed{
E(\gamma,\beta)
=
\langle
\psi(\gamma,\beta)
|
H_C
|
\psi(\gamma,\beta)
\rangle.
}
$$

Cari:

$$
\boxed{
(\gamma^\star,\beta^\star)
=
\arg\min_{\gamma,\beta}E.
}
$$

---

# K.47. Quality metric QAOA

Jangan hanya mengukur apakah QAOA menghasilkan profit.

Pertama:

$$
\boxed{
Approximation\ Ratio
}
$$

atau cost gap.

Untuk minimization:

$$
Gap
=
\frac{
C_{QAOA}-C^\star
}{
|C^\star|
}.
$$

Semakin dekat:

$$
Gap\rightarrow0,
$$

semakin baik.

---

# K.48. Probability of sampling optimum

Karena QAOA menghasilkan distribusi:

$$
p(z),
$$

kita dapat mengukur:

$$
\boxed{
P_{opt}
=
p(z^\star).
}
$$

Ini sangat penting.

QAOA tidak harus selalu menghasilkan optimum dalam setiap measurement.

Yang kita inginkan adalah:

$$
P_{opt}
$$

cukup tinggi.

---

# K.49. Feasibility probability

Kita juga ukur:

$$
\boxed{
P_{feasible}
=
\sum_{z\in\mathcal F}
p(z)
}
$$

dengan:

$$
\mathcal F
$$

adalah set solusi feasible.

Ini bahkan bisa menjadi lebih penting daripada:

$$
P_{opt}.
$$

---

# K.50. Mengapa?

Bayangkan:

$$
P_{opt}=0.05
$$

tetapi:

$$
P_{feasible}=0.95.
$$

Ini masih cukup bagus.

Tetapi jika:

$$
P_{opt}=0.20
$$

dan:

$$
P_{feasible}=0.25,
$$

maka sebagian besar distribution QAOA menghasilkan portfolio yang melanggar constraint.

---

# K.51. Trade construction

Setelah portfolio:

$$
w^\star,
$$

kita menentukan entry signal.

Jangan langsung market order.

Kita definisikan:

$$
Signal_i=
f(
\hat\mu_i,
\sigma_i,
Regime,
Liquidity
).
$$

---

# K.52. Entry threshold

Misalnya:

$$
\boxed{
\hat\mu_i
>
\theta_\mu\sigma_i.
}
$$

Dengan kata lain:

expected return harus cukup besar dibanding uncertainty.

Jika:

$$
\frac{\hat\mu_i}{\sigma_i}
\leq
\theta_\mu,
$$

tidak ada trade.

---

# K.53. Limit order

Jika signal valid:

$$
Order_i
=
Limit(P_{entry}).
$$

Order **tidak langsung dieksekusi**.

Ini sesuai dengan filosofi yang kita bangun sebelumnya.

---

# K.54. Order expiry

Limit order tidak boleh hidup selamanya.

Definisikan:

$$
T_{expiry}
=
t+H_{entry}.
$$

Misalnya:

$$
H_{entry}=1h.
$$

Jika tidak fill:

$$
\boxed{
Cancel.
}
$$

---

# K.55. Fill model V1

Karena kita belum menggunakan tick-level order book:

$$
Fill
$$

ditentukan berdasarkan OHLC.

Misalnya untuk long:

$$
P_{low,t}\leq P_{entry}
$$

maka order dianggap fill.

Tetapi ini memiliki masalah:

> Apakah harga menyentuh entry sebelum SL/TP?

Karena itu kita memerlukan aturan konservatif.

---

# K.56. Ambiguity rule

Jika dalam satu candle:

$$
Low\leq SL
$$

dan:

$$
High\geq TP,
$$

kita **tidak boleh memilih outcome yang menguntungkan**.

Gunakan worst-case ordering:

$$
\boxed{
SL
\text{ dianggap terjadi lebih dahulu}.
}
$$

Ini menghindari look-ahead bias.

---

# K.57. Initial stop-loss

Untuk long:

$$
\boxed{
SL
=
P_{entry}
-
k_{SL}\sigma_i.
}
$$

V1:

$$
\boxed{
k_{SL}=2.
}
$$

Jadi:

$$
d_{SL}=2\sigma_i.
$$

---

# K.58. Risk per trade

Misalnya:

$$
R_{trade}=\$1.
$$

Maka:

$$
\boxed{
Q_i
=
\frac{1}
{
|P_{entry}-P_{SL}|
}.
}
$$

Tetapi ini belum memperhitungkan fee/slippage.

Nanti:

$$
Q_i
=
\frac{
R_{trade}
}{
d_{SL}
+
Cost_{roundtrip}
}.
$$

---

# K.59. Portfolio-level risk

Jika ada tiga posisi:

$$
R_1=R_2=R_3=\$1,
$$

maka bukan berarti portfolio risk otomatis:

$$
\$3.
$$

Karena posisi dapat correlated.

Portfolio risk:

$$
\boxed{
\sigma_p
=
\sqrt{
w^T\Sigma w
}.
}
$$

Ini alasan factor/covariance model tetap diperlukan pada trade-level.

---

# K.60. Maximum aggregate risk

V1:

$$
\boxed{
R_{portfolio,max}
=
3R_{trade}.
}
$$

Tetapi kemudian kita akan menggunakan correlation-adjusted risk.

---

# K.61. Take profit V1

Gunakan:

$$
\boxed{
TP
=
P_{entry}
+
k_{TP}\sigma_i.
}
$$

Dengan:

$$
k_{TP}=3.
$$

Sehingga initial:

$$
RR
=
\frac{3\sigma}{2\sigma}
=
1.5.
$$

Ini **bukan angka sakral**. Nanti diuji melalui walk-forward training.

---

# K.62. Dynamic SL

Jika:

$$
PnL>0
$$

dan:

$$
\frac{P_t-P_{entry}}{\sigma_i}
>
k_{BE},
$$

kita dapat memindahkan:

$$
SL\rightarrow BEP.
$$

Misalnya:

$$
k_{BE}=1.
$$

---

# K.63. Trailing stop

Setelah BEP:

$$
SL_t
=
\max
(
SL_{t-1},
P_t-k_{trail}\sigma_t
).
$$

Ini menjamin:

$$
SL_t\geq SL_{t-1}.
$$

---

# K.64. Dynamic TP

Jika continuation value:

$$
V_{hold}>V_{close},
$$

maka:

$$
TP
$$

dapat diperbesar.

Misalnya:

$$
k_{TP,new}
=
\min(
k_{TP,old}+\Delta k,
k_{TP,max}
).
$$

V1:

$$
\Delta k=0.5
$$

dan:

$$
k_{TP,max}=5.
$$

---

# K.65. Exit decision

Setiap satu jam:

$$
\boxed{
EvaluatePosition()
}
$$

dengan:

$$
\begin{aligned}
&\hat\mu_t,\\
&\sigma_t,\\
&Regime_t,\\
&V_{hold},\\
&V_{close},\\
&SL_t,\\
&TP_t.
\end{aligned}
$$

---

# K.66. Decision rule

Secara konseptual:

$$
Decision=
\begin{cases}
Close,&V_{hold}<V_{close}\\
MoveSL,&V_{hold}>V_{close},\ PnL>0\\
MoveTP,&V_{hold}\gg V_{close}\\
Hold,&otherwise.
\end{cases}
$$

Ini akan kita buat lebih formal ketika masuk ke tahap implementasi trade-management.

---

# K.67. Maximum holding period

Sebuah trade tidak boleh bertahan selamanya.

Definisikan:

$$
\boxed{
T_{max}=24h.
}
$$

Jika:

$$
t-t_{entry}>24h,
$$

maka:

$$
Close.
$$

---

# K.68. Ini penting untuk menghindari hidden risk

Tanpa:

$$
T_{max},
$$

sistem short-term dapat berubah menjadi:

$$
buy\ and\ hope.
$$

Padahal model kita seharusnya:

$$
short\ horizon.
$$

---

# K.69. Walk-forward backtesting

Sekarang bagian yang sangat penting.

**Tidak boleh:**

$$
Train_{2021-2024}
\rightarrow
Test_{2021-2024}.
$$

Itu bukan backtest yang valid.

Kita gunakan:

$$
\boxed{
Walk\ Forward.
}
$$

---

# K.70. Struktur walk-forward

Misalnya:

```text
TRAIN
|--------------------|

TEST
                     |------|

TRAIN
       |--------------------|

TEST
                            |------|

TRAIN
              |--------------------|

TEST
                                   |------|
```

Setiap test period benar-benar out-of-sample.

---

# K.71. Contoh konkret

Misalnya:

$$
Train=30\ days
$$

dan:

$$
Test=7\ days.
$$

Kemudian:

$$
Train_{2}
=
Train_1
+
7days.
$$

---

# K.72. Rolling versus expanding

Untuk sistem kita:

$$
\boxed{
rolling\ window
}
$$

lebih sesuai.

Jadi:

$$
D_t
=
[t-W,t].
$$

Bukan:

$$
D_t=[0,t].
$$

---

# K.73. Kenapa?

Karena market regime berubah.

Data sepuluh tahun lalu mungkin mempunyai relevansi lebih rendah daripada:

$$
30\text{ hari terakhir}.
$$

Tetapi ini adalah hipotesis yang harus diuji, bukan asumsi final.

---

# K.74. Backtest pipeline

Pada setiap waktu $t$:

$$
\boxed{
\begin{aligned}
1.&\ Load\ historical\ data\\
2.&\ Build\ features\\
3.&\ Estimate\ factors\\
4.&\ Forecast\ returns\\
5.&\ Estimate\ covariance\\
6.&\ Generate\ QUBO\\
7.&\ Solve\ QUBO\\
8.&\ Generate\ target\ allocation\\
9.&\ Generate\ orders\\
10.&\ Simulate\ execution\\
11.&\ Manage\ positions\\
12.&\ Record\ PnL.
\end{aligned}
}
$$

Kemudian:

$$
t\rightarrow t+1.
$$

---

# K.75. Yang harus disimpan setiap timestamp

Database/backtest record minimal:

$$
\boxed{
Record_t=
\{
timestamp,
state,
forecast,
covariance,
qubo,
solution,
orders,
fills,
positions,
SL,
TP,
PnL
\}.
}
$$

Ini akan sangat berguna untuk debugging.

---

# K.76. Performance metrics

Kita tidak boleh hanya menggunakan:

$$
Total\ PnL.
$$

Minimal:

### Return

$$
R_{total}.
$$

### Sharpe

$$
\boxed{
Sharpe
=
\frac{
E[R_p-R_f]
}{
\sigma_p
}
}
$$

### Sortino

$$
\boxed{
Sortino
=
\frac{
E[R_p-R_f]
}{
\sigma_{down}
}
}
$$

### Maximum Drawdown

$$
\boxed{
MDD
=
\max_t
\left(
\frac{Peak_t-Equity_t}
{Peak_t}
\right).
}
$$

---

# K.77. Trade metrics

Kita juga ukur:

$$
WinRate
=
\frac{N_{win}}
{N_{trade}}.
$$

Profit factor:

$$
\boxed{
PF
=
\frac{
GrossProfit
}{
|GrossLoss|
}.
}
$$

Average win:

$$
\bar W.
$$

Average loss:

$$
\bar L.
$$

Expectancy:

$$
\boxed{
E
=
p_w\bar W
-
(1-p_w)|\bar L|.
}
$$

---

# K.78. QAOA-specific metrics

Selain financial metrics:

$$
\boxed{
\begin{aligned}
Cost\ Gap\\
Approximation\ Quality\\
P_{opt}\\
P_{feasible}\\
Circuit\ Depth\\
Number\ of\ Qubits\\
Classical\ Runtime\\
QAOA\ Runtime
\end{aligned}
}
$$

---

# K.79. Ini menghasilkan dua evaluation layers

### Layer 1 — Mathematical

$$
\boxed{
QAOA
\quad vs \quad
Classical
}
$$

berdasarkan:

$$
C(z).
$$

### Layer 2 — Financial

$$
\boxed{
Trading\ Strategy
}
$$

berdasarkan:

$$
PnL,
Sharpe,
MDD,
PF,\ldots
$$

Kita **harus memisahkan kedua layer ini**.

---

# K.80. Eksperimen inti

Saya menyarankan eksperimen utama berikut.

### Experiment A

$$
Exact
$$

vs

$$
QAOA.
$$

Tujuan:

> Apakah QAOA mampu menemukan solusi dekat optimum?

---

### Experiment B

$$
Classical
$$

vs

$$
QAOA.
$$

Tujuan:

> Apakah QAOA kompetitif terhadap classical combinatorial optimizer?

---

### Experiment C

Trading tanpa QAOA:

$$
Forecast
\rightarrow
Classical
\rightarrow
Trading.
$$

Bandingkan dengan:

$$
Forecast
\rightarrow
QAOA
\rightarrow
Trading.
$$

---

# K.81. Experiment D — no-factor model

Gunakan:

$$
\hat\mu_i
=
f(asset_i)
$$

tanpa:

$$
BTC,ETH,DXY,Gold,\ldots
$$

Kemudian bandingkan dengan:

$$
Factor-aware.
$$

Ini menguji apakah market factors benar-benar menambah informasi.

---

# K.82. Experiment E — no dynamic management

Bandingkan:

### Static

$$
SL,TP
$$

tidak berubah.

melawan:

### Dynamic

$$
SL_t,TP_t
$$

berubah berdasarkan state.

Ini menguji ide yang kita diskusikan sejak awal.

---

# K.83. Experiment F — transaction cost sensitivity

Jalankan:

$$
TC=0
$$

kemudian:

$$
TC=low
$$

kemudian:

$$
TC=medium
$$

kemudian:

$$
TC=high.
$$

Jika strategy hanya profitable ketika:

$$
TC=0,
$$

maka secara praktis strategy tersebut tidak menarik.

---

# K.84. Experiment G — regime robustness

Evaluasi terpisah:

$$
Bull,
Neutral,
Bear.
$$

Kita ingin mengetahui apakah strategy hanya bekerja dalam satu regime.

---

# K.85. Experiment H — quantum depth

Bandingkan:

$$
p=1
$$

$$
p=2
$$

$$
p=3.
$$

Kemudian:

$$
Gap(p).
$$

Kita ingin mengetahui:

$$
\frac{dGap}{dp}.
$$

Apakah depth tambahan benar-benar memberikan improvement?

---

# K.86. Experiment I — scaling

Naikkan:

$$
N=4,6,10,20.
$$

Catat:

$$
M(N)
$$

dan:

$$
Runtime(N).
$$

Kemudian:

$$
\boxed{
Scaling\ Curve
}
$$

menjadi salah satu hasil penelitian yang sangat menarik.

---

# K.87. Experiment J — stochastic robustness

Karena QAOA menghasilkan probabilitas:

$$
p(z),
$$

jalankan measurement berulang:

$$
Shots=
\{100,500,1000,5000\}.
$$

Kemudian ukur:

$$
P_{opt}(Shots).
$$

---

# K.88. Data split

Kita harus mempunyai tiga bagian:

$$
\boxed{
Train
}
$$

$$
\boxed{
Validation
}
$$

$$
\boxed{
Test.
}
$$

Test set **tidak boleh digunakan untuk memilih parameter**.

---

# K.89. Parameter yang harus dibekukan

Setelah validation selesai:

$$
\boxed{
\Theta^\star=
\{
W,
\lambda,
\kappa,
\delta_w,
K,
k_{SL},
k_{TP},
T_{max},
p
\}
}
$$

dibekukan.

Baru kemudian:

$$
Test.
$$

---

# K.90. Anti-lookahead rule

Ini akan menjadi salah satu aturan paling keras dalam implementasi.

Pada timestamp $t$:

$$
\boxed{
\text{model hanya boleh mengetahui informasi }\leq t.
}
$$

Tidak boleh menggunakan:

$$
P_{t+1}
$$

untuk menentukan:

$$
A_t.
$$

---

# K.91. Bahkan covariance harus lagged correctly

Jika:

$$
\Sigma_t
$$

digunakan untuk membuat portfolio $t$, maka:

$$
\Sigma_t
$$

harus dihitung dari:

$$
r_{\leq t}.
$$

Bukan:

$$
r_{t+1}.
$$

Ini terlihat sepele tetapi merupakan salah satu sumber terbesar backtest leakage.

---

# K.92. Execution lag

Kita juga jangan mengasumsikan:

$$
Signal_t
\rightarrow
Fill_t
$$

secara instan.

Minimal:

$$
Signal_t
\rightarrow
Order_t
\rightarrow
Fill_{t+\Delta}.
$$

Untuk V1:

$$
\boxed{
\Delta=1\ candle.
}
$$

---

# K.93. Mengapa?

Karena jika:

$$
P_t
$$

digunakan untuk menghasilkan signal dan kita langsung menganggap entry pada:

$$
P_t,
$$

kita berpotensi mendapatkan harga yang tidak benar-benar tersedia setelah signal dihitung.

---

# K.94. Struktur final V1

Jadi sistem V1 kita:

$$
\boxed{
\begin{aligned}
Data
&=
OHLCV+Factors
\\
Timeframe
&=
1h
\\
Forecast
&=
Ridge
\\
Window
&=
30d
\\
Covariance
&=
Shrinkage
\\
Regime
&=
3-state
\\
Universe
&=
6\ assets
\\
Selection
&=
K\leq3
\\
Weight
&=
5\%\ increments
\\
MaxWeight
&=
50\%
\\
Risk
&=
Covariance-based
\\
Optimizer
&=
QUBO
\\
Quantum
&=
QAOA
\\
Depth
&=
p=1,2,3
\\
SL
&=
2\sigma
\\
TP
&=
3\sigma
\\
Risk/trade
&=
\$1
\\
MaxHolding
&=
24h
\\
Reoptimization
&=
1h
\\
Backtest
&=
Walk-forward
\end{aligned}
}
$$

---

# K.95. Arsitektur software

Sekarang spesifikasi matematis ini dapat diterjemahkan menjadi modul:

```text
trade_system/
│
├── data/
│   ├── downloader
│   ├── cleaner
│   ├── resampler
│   └── factor_data
│
├── features/
│   ├── returns
│   ├── volatility
│   ├── momentum
│   └── factor_exposure
│
├── forecasting/
│   ├── ridge
│   └── prediction
│
├── risk/
│   ├── covariance
│   ├── shrinkage
│   └── portfolio_risk
│
├── optimization/
│   ├── classical
│   ├── exact
│   ├── qubo
│   ├── ising
│   └── qaoa
│
├── execution/
│   ├── order_generator
│   ├── fill_model
│   └── transaction_cost
│
├── position/
│   ├── stop_loss
│   ├── take_profit
│   ├── trailing
│   └── position_manager
│
├── backtest/
│   ├── engine
│   ├── walk_forward
│   └── metrics
│
└── experiments/
    ├── exact_vs_qaoa
    ├── factor_ablation
    ├── cost_sensitivity
    ├── qaoa_depth
    └── scaling
```

---

# K.96. Dan di sinilah proyek kita menjadi sangat menarik

Perhatikan bahwa **QAOA hanya membutuhkan sebagian kecil dari keseluruhan sistem**.

Strukturnya:

$$
\boxed{
\text{Econometrics}
\rightarrow
\text{Financial Mathematics}
\rightarrow
\text{Combinatorial Optimization}
\rightarrow
\text{Quantum Computing}
\rightarrow
\text{Market Microstructure}
}
$$

Jadi proyek ini bukan sekadar:

> "Saya menggunakan quantum computer untuk trading."

Lebih tepat:

> **Saya membangun dynamic factor-aware portfolio/trading optimization problem yang kemudian diformulasikan sebagai QUBO/Ising dan diselesaikan menggunakan QAOA, dengan evaluasi terhadap classical optimization dan realistic execution constraints.**

Itu jauh lebih kuat secara akademik.

---

# K.97. Satu hal yang perlu kita luruskan sejak sekarang

Saya ingin **memisahkan dua sistem**:

### Sistem penelitian

$$
\boxed{
QAOA\ Trading\ Research\ Engine
}
$$

Tujuannya:

$$
\text{mengukur apakah QAOA berguna}.
$$

### Sistem live trading

$$
\boxed{
Production\ Trading\ Engine
}
$$

Tujuannya:

$$
\text{menghasilkan keputusan trading secara aman}.
$$

Jangan mencampurkan keduanya.

Production engine baru boleh dibuat setelah:

$$
Backtest
\rightarrow
Paper\ Trading
\rightarrow
Stress\ Test
\rightarrow
Live\ Small\ Capital.
$$

---

# K.98. Roadmap setelah Tahap K

Sekarang seluruh desain abstrak kita sudah cukup konkret.

Urutan selanjutnya seharusnya:

$$
\boxed{
K
\rightarrow
L
\rightarrow
M
\rightarrow
N
\rightarrow
O
}
$$

dengan:

### **Tahap L — Data Engineering**

Kita menentukan secara konkret:

$$
DataSource
\rightarrow
Schema
\rightarrow
Timestamp
\rightarrow
Cleaning
\rightarrow
Alignment
\rightarrow
Storage.
$$

Termasuk masalah yang sangat penting seperti:

- timezone,
- missing candle,
- survivorship bias,
- delisted assets,
- corporate action untuk saham,
- perbedaan jam perdagangan saham vs crypto,
- DXY/Gold/SPX yang tidak trading 24/7,
- dan bagaimana factor data disejajarkan dengan hourly crypto data.

### **Tahap M — Forecasting & Factor Engine**

Kita turunkan secara lengkap:

$$
X
\rightarrow
\hat\mu
$$

dan:

$$
X
\rightarrow
B,\Sigma,Regime.
$$

### **Tahap N — QUBO/Ising Engine**

Ini akan menjadi salah satu bagian paling matematis:

$$
Financial\ Objective
\rightarrow
Binary\ Encoding
\rightarrow
QUBO
\rightarrow
Ising
\rightarrow
Hamiltonian.
$$

Kita bahkan dapat mengambil **contoh numerik 4 aset** dan menurunkan seluruh elemen:

$$
Q,\quad h_i,\quad J_{ij}
$$

secara eksplisit sampai menjadi:

$$
\hat H_C.
$$

### **Tahap O — QAOA + Classical Benchmark**

Baru kita implementasikan:

$$
Exact
\leftrightarrow
Classical
\leftrightarrow
QAOA.
$$

Dan kita ukur:

$$
Gap,\quad
P_{opt},\quad
P_{feasible},\quad
Runtime.
$$

---

## Posisi kita sekarang

Dengan Tahap A–K, kita sudah berpindah dari sekadar ide:

> **"Bagaimana kalau kita menggunakan QAOA untuk trading?"**

menjadi sebuah objek penelitian yang jauh lebih terdefinisi:

$$
\boxed{
\begin{array}{c}
\text{Short-Horizon Factor-Aware Trading}\\
\downarrow\\
\text{Forecast } \hat\mu_t\\
\downarrow\\
\text{Risk } \Sigma_t\\
\downarrow\\
\text{Discrete Portfolio Selection}\\
\downarrow\\
\text{QUBO}\\
\downarrow\\
\text{Ising Hamiltonian}\\
\downarrow\\
\text{QAOA}\\
\downarrow\\
\text{Target Allocation}\\
\downarrow\\
\text{Risk-Based \$1 Trades}\\
\downarrow\\
\text{Dynamic SL/TP}\\
\downarrow\\
\text{Execution}\\
\downarrow\\
\text{Walk-Forward PnL}
\end{array}
}
$$

Dan yang menurut saya paling penting: **arsitektur ini tidak terkunci pada crypto**. Ketika kita pindah ke saham internasional, bagian optimization engine pada dasarnya tetap sama. Yang berubah terutama adalah universe, market-calendar handling, factor set, liquidity model, dan execution model. Faktor seperti **Gold dan USD/DXY** dapat tetap menjadi latent/common drivers, sementara factor equity seperti SPX/VIX dapat ditambahkan.

**Tahap berikutnya yang paling tepat adalah Tahap L — Data Engineering**, karena sebelum kita menurunkan QUBO secara numerik, kita harus memastikan bahwa $\hat\mu_t$, $\Sigma_t$, dan seluruh factor exposure yang masuk ke QUBO benar-benar berasal dari data yang secara temporal konsisten dan bebas look-ahead. Ini justru salah satu bagian yang paling sering membuat backtest kuantitatif terlihat bagus padahal salah.

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

## Prompt:
8/17/2026, 9:57:44 PM

lanjut Tahap M

## Response:
8/17/2026, 9:57:44 PM

> **Remembering**
>
>
> ****
>
> 
>
> **Continued Tahap M design by connecting forecasting inputs and clarifying QUBO transition**
>
> 
>
> Worked for 7s

# Tahap M — Forecasting & Factor Engine

Kita sekarang masuk ke salah satu bagian **paling penting secara matematis** dari sistem kita.

Pada Tahap L kita mengubah data mentah menjadi market state:

$$
S_t=
\left[
X_t,\,
B_t,\,
\Sigma_{F,t},\,
\Sigma_{\epsilon,t},\,
\text{regime}_t,\,
\text{liquidity}_t,\,
w_{t-1}
\right].
$$

Tahap M menjawab pertanyaan:

> **Dari state pasar $S_t$, berapa expected return setiap aset pada horizon trading berikutnya, dan bagaimana ketidakpastian serta hubungan antar-aset berubah?**

Output utama kita adalah:

$$
\boxed{
\hat{\boldsymbol\mu}_t
}
$$

dan

$$
\boxed{
\hat{\boldsymbol\Sigma}_t.
}
$$

Keduanya nantinya menjadi bahan baku langsung untuk optimasi portfolio/QUBO.

---

# M.1. Arsitektur Tahap M

Pipeline kita:

$$
\boxed{
S_t
\rightarrow
\text{Factor Forecast}
\rightarrow
\text{Asset Forecast}
\rightarrow
\text{Residual Forecast}
\rightarrow
\hat{\mu}_t
}
$$

dan secara paralel:

$$
\boxed{
S_t
\rightarrow
B_t
\rightarrow
\Sigma_{F,t}
\rightarrow
\Sigma_t
}
$$

sehingga:

$$
\boxed{
(\hat{\mu}_t,\Sigma_t)
\rightarrow
Portfolio\ Optimization.
}
$$

---

# M.2. Jangan langsung memprediksi harga

Ini keputusan desain penting.

Kita **tidak** ingin:

$$
\hat P_{t+1}=f(P_t).
$$

Lebih masuk akal menggunakan return:

$$
r_{i,t+1}
=
\ln\frac{P_{i,t+1}}{P_{i,t}}.
$$

Kemudian:

$$
\boxed{
\mu_{i,t}
=
E[r_{i,t+1}\mid\mathcal F_t].
}
$$

Alasannya sederhana:

harga bersifat non-stationary, sedangkan return relatif lebih cocok untuk model statistik.

---

# M.3. Horizon trading

Karena sistem kita ditujukan untuk short-term trading, kita perlu menentukan:

$$
\Delta.
$$

Untuk V1 kita gunakan:

$$
\boxed{
\Delta=1\text{ jam}.
}
$$

Maka:

$$
r_{i,t+1}
=
\ln
\frac{P_{i,t+1h}}
{P_{i,t}}.
$$

Kemudian:

$$
\boxed{
\mu_{i,t}
=
E[r_{i,t+1h}\mid\mathcal F_t].
}
$$

---

# M.4. Mengapa expected return saja tidak cukup?

Misalkan:

$$
\mu_A=0.20\%
$$

dan:

$$
\mu_B=0.15\%.
$$

Secara naïf kita memilih A.

Tetapi ternyata:

$$
\sigma_A=1.5\%
$$

sedangkan:

$$
\sigma_B=0.3\%.
$$

Maka A memiliki return lebih tinggi tetapi risk yang jauh lebih besar.

Karena itu kita membutuhkan:

$$
\boxed{
(\mu,\Sigma)
}
$$

bukan hanya:

$$
\mu.
$$

---

# M.5. Model factor dasar

Misalkan terdapat $N$ asset dan $K$ factor.

Kita definisikan:

$$
\mathbf r_t
=
\boldsymbol\alpha_t
+
B_t\mathbf f_t
+
\boldsymbol\epsilon_t.
$$

Dengan:

$$
\mathbf r_t\in\mathbb R^N
$$

dan:

$$
\mathbf f_t\in\mathbb R^K.
$$

---

# M.6. Contoh factor kita

Misalnya:

$$
\mathbf f_t=
\begin{bmatrix}
r_{BTC,t}\\
r_{ETH,t}\\
r_{DXY,t}\\
r_{Gold,t}\\
r_{SPX,t}\\
r_{VIX,t}
\end{bmatrix}.
$$

Untuk saham internasional nanti factor tersebut dapat diperluas.

Tetapi prinsipnya tetap sama.

---

# M.7. Matrix exposure

Untuk asset $i$:

$$
\boldsymbol\beta_i
=
\begin{bmatrix}
\beta_{i,BTC}\\
\beta_{i,ETH}\\
\beta_{i,DXY}\\
\beta_{i,Gold}\\
\beta_{i,SPX}\\
\beta_{i,VIX}
\end{bmatrix}.
$$

Seluruh asset:

$$
B=
\begin{bmatrix}
\beta_1^T\\
\beta_2^T\\
\vdots\\
\beta_N^T
\end{bmatrix}.
$$

Sehingga:

$$
B\in\mathbb R^{N\times K}.
$$

---

# M.8. Forecast factor

Sekarang kita tidak hanya ingin mengetahui:

$$
f_t.
$$

Kita ingin:

$$
\boxed{
\hat{\mathbf f}_{t+1}
=
E[\mathbf f_{t+1}\mid\mathcal F_t].
}
$$

Ini sangat penting.

Misalnya sistem mendeteksi:

$$
\hat r_{BTC,t+1}>0,
$$

tetapi:

$$
\hat r_{DXY,t+1}>0.
$$

Keduanya dapat memberikan pengaruh berbeda terhadap asset yang sama.

---

# M.9. Forecast asset dari factor

Dari:

$$
r_{i,t+1}
=
\alpha_i+
\beta_i^Tf_{t+1}
+
\epsilon_{i,t+1},
$$

ambil conditional expectation:

$$
E[r_{i,t+1}\mid\mathcal F_t].
$$

Maka:

$$
\mu_{i,t}
=
\alpha_i
+
\beta_i^T
E[f_{t+1}\mid\mathcal F_t]
+
E[\epsilon_{i,t+1}\mid\mathcal F_t].
$$

Sehingga:

$$
\boxed{
\hat\mu_{i,t}
=
\hat\alpha_{i,t}
+
\hat\beta_{i,t}^T
\hat f_{t+1}
+
\hat\epsilon_{i,t+1}.
}
$$

Ini adalah persamaan inti Factor Engine kita.

---

# M.10. Kita pecah expected return menjadi tiga bagian

$$
\boxed{
\hat\mu_i
=
\underbrace{\hat\alpha_i}_{\text{baseline}}
+
\underbrace{\hat\beta_i^T\hat f}_{\text{factor contribution}}
+
\underbrace{\hat\epsilon_i}_{\text{idiosyncratic contribution}}.
}
$$

Interpretasinya:

### 1. Baseline

$$
\hat\alpha_i.
$$

### 2. Market/factor-driven component

$$
\hat\beta_i^T\hat f.
$$

### 3. Asset-specific component

$$
\hat\epsilon_i.
$$

---

# M.11. Mengapa residual prediction penting?

Bayangkan:

$$
BTC\uparrow.
$$

Sebuah altcoin memiliki:

$$
\beta_{BTC}=1.5.
$$

Secara factor model:

$$
\hat r_{alt}
\approx
1.5\hat r_{BTC}.
$$

Tetapi ternyata asset tersebut sedang mengalami:

$$
\epsilon_t<0.
$$

Maka forecast sebenarnya:

$$
\hat\mu
=
1.5\hat r_{BTC}
+
\hat\epsilon.
$$

Ini jauh lebih informatif daripada sekadar:

> BTC naik → beli altcoin.

---

# M.12. Residual bukan noise yang harus dibuang

Pada model sederhana:

$$
r=Bf+\epsilon,
$$

orang sering menganggap:

$$
\epsilon
$$

sebagai noise.

Tetapi untuk trading:

$$
\boxed{
\epsilon_t
$$

dapat mengandung alpha.

Misalnya residual mengalami mean reversion:

$$
\epsilon_{t+1}
=
\phi\epsilon_t+\eta_{t+1}.
$$

Jika:

$$
-1<\phi<0,
$$

residual memiliki kecenderungan reversal.

---

# M.13. Model residual AR(1)

Kita dapat menggunakan:

$$
\boxed{
\epsilon_{i,t+1}
=
c_i+
\phi_i\epsilon_{i,t}
+\eta_{i,t+1}.
}
$$

Maka:

$$
E[\epsilon_{i,t+1}\mid\mathcal F_t]
=
c_i+\phi_i\epsilon_{i,t}.
$$

Jadi:

$$
\boxed{
\hat\epsilon_{i,t+1}
=
\hat c_i+\hat\phi_i\epsilon_{i,t}.
}
$$

---

# M.14. Jika $\phi<0$

Misalkan:

$$
\phi=-0.4
$$

dan:

$$
\epsilon_t=-1\%.
$$

Maka:

$$
\hat\epsilon_{t+1}
=
(-0.4)(-1\%)
=
+0.4\%.
$$

Artinya asset sedang mengalami underperformance terhadap factor model dan model memperkirakan sebagian reversal.

---

# M.15. Jika $\phi>0$

Misalkan:

$$
\phi=0.4.
$$

Jika:

$$
\epsilon_t=1\%,
$$

maka:

$$
\hat\epsilon_{t+1}=0.4\%.
$$

Ini lebih menyerupai momentum.

Jadi:

$$
\boxed{
\phi
}
$$

membantu menentukan karakteristik residual.

---

# M.16. Tetapi jangan langsung percaya residual

Kita harus menguji apakah:

$$
\hat\phi
$$

stabil.

Rolling estimation:

$$
\phi_t
=
\operatorname{OLS}
(
\epsilon_{t-W:t}
).
$$

Jika:

$$
\phi_t
$$

berubah-ubah drastis, residual model tidak stabil.

Maka confidence terhadap signal harus turun.

---

# M.17. Confidence-adjusted expected return

Ini ide penting untuk sistem kita.

Jangan hanya menggunakan:

$$
\hat\mu.
$$

Tambahkan:

$$
q_i\in[0,1]
$$

sebagai confidence.

Kemudian:

$$
\boxed{
\tilde\mu_i
=
q_i\hat\mu_i.
}
$$

Jika model sangat yakin:

$$
q_i\approx1.
$$

Jika tidak yakin:

$$
q_i\approx0.
$$

---

# M.18. Apa yang menentukan confidence?

Kita dapat membangun:

$$
q_i
=
f(
R^2,
parameter\ stability,
sample\ size,
data\ quality,
regime\ stability
).
$$

Misalnya:

$$
q_i
=
q_{data}
q_{model}
q_{regime}.
$$

---

# M.19. Jangan membuat confidence secara arbitrer

Untuk V1, lebih baik kita membuatnya sebagai fungsi yang sederhana dan dapat diuji.

Misalnya:

$$
q_i
=
\operatorname{clip}
\left(
\frac{IC_i}{IC_{max}},
0,1
\right).
$$

dengan Information Coefficient:

$$
IC
=
Corr(
\hat\mu_t,r_{t+1}
).
$$

---

# M.20. Information coefficient

Jika:

$$
IC>0,
$$

forecast cenderung benar secara arah.

Jika:

$$
IC\approx0,
$$

forecast tidak berguna.

Jika:

$$
IC<0,
$$

model bahkan berlawanan arah.

Namun:

$$
IC
$$

harus dihitung **out-of-sample**.

---

# M.21. Forecast factor dengan model sederhana terlebih dahulu

Untuk V1 kita tidak membutuhkan deep learning.

Kita dapat mulai dengan:

$$
\boxed{
\hat f_{t+1}
=
A_t f_t+c_t.
}
$$

Ini adalah VAR(1).

---

# M.22. VAR(1)

Dengan:

$$
\mathbf f_{t+1}
=
\mathbf c+
A\mathbf f_t+
\boldsymbol\eta_{t+1}.
$$

Maka:

$$
\boxed{
\hat{\mathbf f}_{t+1}
=
\mathbf c+
A\mathbf f_t.
}
$$

---

# M.23. Mengapa VAR menarik?

Karena factor kita saling berhubungan.

Misalnya:

$$
BTC
\leftrightarrow
ETH
$$

dan:

$$
DXY
\leftrightarrow
Gold
\leftrightarrow
SPX.
$$

VAR menangkap cross-factor dynamics:

$$
A_{ij}\neq0.
$$

---

# M.24. Contoh

Misalnya:

$$
\hat r_{BTC,t+1}
=
0.2r_{BTC,t}
-
0.1r_{DXY,t}
$$

dan:

$$
\hat r_{ETH,t+1}
=
0.5r_{BTC,t}
+
0.1r_{ETH,t}.
$$

Maka sistem tidak hanya bertanya:

> bagaimana BTC bergerak?

tetapi:

> bagaimana kondisi seluruh factor memengaruhi perkembangan factor berikutnya?

---

# M.25. Namun VAR memiliki masalah

Jika:

$$
K=6
$$

dan kita menggunakan lag:

$$
p=10,
$$

jumlah parameter cepat meningkat.

Dengan:

$$
K^2p
$$

parameter.

Karena itu kita dapat menggunakan ridge:

$$
\boxed{
\hat A
=
\arg\min_A
\left\{
\|F_{future}-AF_{past}\|_F^2
+
\lambda\|A\|_F^2
\right\}.
}
$$

---

# M.26. Forecast factor uncertainty

Forecast tidak hanya:

$$
\hat f.
$$

Kita juga membutuhkan:

$$
\boxed{
\Sigma_{\hat f}.
}
$$

Misalkan:

$$
f_{t+1}=c+Af_t+\eta_{t+1}
$$

dengan:

$$
Cov(\eta)=\Omega.
$$

Untuk one-step forecast:

$$
\boxed{
\Sigma_{\hat f}
=
\Omega.
}
$$

---

# M.27. Asset covariance

Kembali ke:

$$
r_t=B_tf_t+\epsilon_t.
$$

Jika:

$$
Cov(f_t)=\Sigma_F
$$

dan:

$$
Cov(\epsilon_t)=\Sigma_\epsilon,
$$

serta factor dan residual dianggap tidak berkorelasi:

$$
Cov(f,\epsilon)=0,
$$

maka:

$$
\boxed{
\Sigma_r
=
B\Sigma_FB^T
+
\Sigma_\epsilon.
}
$$

Ini adalah persamaan inti risk engine.

---

# M.28. Penurunan matematis

Mulai:

$$
r=Bf+\epsilon.
$$

Covariance:

$$
Cov(r)
=
E[(r-E[r])(r-E[r])^T].
$$

Karena:

$$
r-E[r]
=
B(f-E[f])
+
(\epsilon-E[\epsilon]),
$$

maka:

$$
Cov(r)
=
B\Sigma_FB^T
+
\Sigma_\epsilon
+
B\,Cov(f,\epsilon)
+
Cov(\epsilon,f)B^T.
$$

Jika:

$$
Cov(f,\epsilon)=0,
$$

maka:

$$
\boxed{
\Sigma_r
=
B\Sigma_FB^T+\Sigma_\epsilon.
}
$$

---

# M.29. Mengapa ini lebih baik daripada covariance langsung?

Covariance sample biasa:

$$
\hat\Sigma
=
\frac1{T-1}
RR^T.
$$

Masalahnya:

- noisy,
- unstable,
- sensitive terhadap regime,
- buruk jika $N$ besar dan $T$ relatif kecil.

Factor decomposition memberikan struktur:

$$
\boxed{
Systematic\ Risk
+
Idiosyncratic\ Risk.
}
$$

---

# M.30. Factor risk

$$
\boxed{
\Sigma_{factor}
=
B\Sigma_FB^T.
}
$$

Jika dua asset mempunyai:

$$
\beta_{i,BTC}>0
$$

dan:

$$
\beta_{j,BTC}>0,
$$

mereka dapat memiliki covariance tinggi meskipun tidak selalu terlihat dari short sample.

---

# M.31. Idiosyncratic risk

$$
\boxed{
\Sigma_\epsilon.
}
$$

Pada model paling sederhana:

$$
\Sigma_\epsilon
=
diag(
\sigma_{\epsilon,1}^2,\ldots,
\sigma_{\epsilon,N}^2
).
$$

Tetapi ini terlalu sederhana.

---

# M.32. Residual correlation

Kita dapat mengestimasi:

$$
Corr(\epsilon_i,\epsilon_j).
$$

Jika signifikan, maka:

$$
\Sigma_\epsilon
$$

tidak diagonal.

Ini memungkinkan kita menemukan hubungan yang tidak dijelaskan factor global.

---

# M.33. Shrinkage

Sample covariance residual dapat noisy.

Gunakan:

$$
\boxed{
\Sigma_\epsilon^{shrunk}
=
(1-\lambda)\hat\Sigma_\epsilon
+
\lambda T.
}
$$

Misalnya:

$$
T=diag(\hat\Sigma_\epsilon).
$$

---

# M.34. Dynamic covariance

Pasar short-term berubah.

Maka:

$$
\Sigma_t
\neq
\Sigma_{t-1}.
$$

Kita membutuhkan dynamic estimation.

Salah satu baseline yang sangat baik:

$$
\boxed{
\Sigma_t^{EWMA}
=
\lambda\Sigma_{t-1}^{EWMA}
+
(1-\lambda)r_{t-1}r_{t-1}^T.
}
$$

---

# M.35. Factor covariance EWMA

Kita dapat menerapkan hal yang sama pada factor:

$$
\boxed{
\Sigma_{F,t}
=
\lambda_F\Sigma_{F,t-1}
+
(1-\lambda_F)f_{t-1}f_{t-1}^T.
}
$$

Dengan demikian covariance lebih responsif terhadap perubahan regime.

---

# M.36. Volatility regime

Misalnya:

$$
\sigma_t^{short}
$$

dibandingkan:

$$
\sigma_t^{long}.
$$

Definisikan:

$$
VR_t
=
\frac{
\sigma_t^{short}
}{
\sigma_t^{long}
}.
$$

Jika:

$$
VR_t\gg1,
$$

kita berada pada high-volatility regime.

---

# M.37. Mengapa regime penting untuk $\mu$?

Signal momentum yang bekerja pada:

$$
low\ volatility
$$

belum tentu bekerja pada:

$$
high\ volatility.
$$

Jadi:

$$
\boxed{
\mu_t
=
\mu(S_t)
}
$$

bukan konstanta.

---

# M.38. Regime-dependent forecast

Secara sederhana:

$$
\hat\mu_t
=
\begin{cases}
\hat\mu_t^{low},&
Regime=Low\\
\hat\mu_t^{high},&
Regime=High.
\end{cases}
$$

Tetapi kita tidak perlu langsung membuat dua model terpisah.

Kita dapat memasukkan regime sebagai feature:

$$
X_t=
[
returns,
volatility,
factors,
regime
].
$$

---

# M.39. Mean model

Sekarang kita dapat membangun model:

$$
\boxed{
\hat\mu_{i,t}
=
\alpha_i
+
\beta_i^T\hat f_{t+1}
+
\phi_i\epsilon_{i,t}
+
\theta_i^TX_{i,t}.
}
$$

Ini menjadi baseline forecasting engine kita.

---

# M.40. Tetapi hati-hati: jangan terlalu banyak parameter

Kita tidak ingin membuat:

$$
\hat\mu
=
f(1000\ features)
$$

dengan dataset terbatas.

Karena:

$$
Overfitting
$$

akan menjadi musuh utama.

V1 harus **sederhana tetapi mathematically defensible**.

---

# M.41. Maka arsitektur V1 saya tetapkan

Saya sarankan:

$$
\boxed{
\hat\mu
=
\hat\mu^{factor}
+
\hat\mu^{residual}
+
\hat\mu^{momentum}
}
$$

dengan:

$$
\hat\mu^{factor}
=
B\hat f,
$$

$$
\hat\mu^{residual}
=
\phi\epsilon_t,
$$

dan:

$$
\hat\mu^{momentum}
=
\theta^Tr_t^{multi-horizon}.
$$

---

# M.42. Secara eksplisit

Untuk asset $i$:

$$
\boxed{
\hat\mu_{i,t}
=
\alpha_i
+
\beta_i^T\hat f_{t+1}
+
\phi_i\epsilon_{i,t}
+
\theta_{i,1}r_{i,t}^{1h}
+
\theta_{i,2}r_{i,t}^{4h}
+
\theta_{i,3}r_{i,t}^{24h}.
}
$$

Ini sudah cukup kaya untuk V1.

---

# M.43. Regularisasi

Parameter:

$$
\theta,\beta,\phi
$$

dapat diestimasi dengan ridge:

$$
\boxed{
\hat w
=
\arg\min_w
\left[
\|y-Xw\|_2^2
+
\lambda\|w\|_2^2
\right].
}
$$

Solusinya:

$$
\boxed{
\hat w
=
(X^TX+\lambda I)^{-1}X^Ty.
}
$$

---

# M.44. Mengapa ridge cocok?

Karena features kita dapat berkorelasi.

Contoh:

$$
r_{BTC}^{1h}
$$

dan:

$$
r_{BTC}^{4h}
$$

jelas tidak independen.

Begitu pula:

$$
DXY
$$

dan:

$$
Gold.
$$

Ridge mengurangi coefficient explosion.

---

# M.45. Standardisasi

Sebelum ridge:

$$
x_j
$$

harus dinormalisasi menggunakan training window.

$$
z_j
=
\frac{x_j-\mu_j^{train}}
{\sigma_j^{train}}.
$$

Kemudian model dilatih.

---

# M.46. Forecast output

Pada setiap timestamp:

$$
t
$$

engine menghasilkan:

$$
\boxed{
\hat\mu_t
=
\begin{bmatrix}
\hat\mu_{1,t}\\
\hat\mu_{2,t}\\
\vdots\\
\hat\mu_{N,t}
\end{bmatrix}.
}
$$

Contoh:

$$
\hat\mu_t=
\begin{bmatrix}
0.0018\\
0.0009\\
-0.0003\\
0.0021
\end{bmatrix}.
$$

Artinya:

$$
0.18\%,0.09\%,-0.03\%,0.21\%
$$

expected log-return satu jam ke depan.

---

# M.47. Tetapi expected return harus dibandingkan dengan biaya

Ini sangat penting untuk trading.

Jika:

$$
\hat\mu_i=0.08\%
$$

tetapi:

$$
transaction\ cost=0.10\%,
$$

maka:

$$
\boxed{
NetAlpha_i<0.
}
$$

Karena itu kita definisikan:

$$
\boxed{
\alpha_i^{net}
=
\hat\mu_i
-
C_i.
}
$$

---

# M.48. Cost model

Minimal:

$$
C_i
=
fee_i
+
spread_i
+
slippage_i.
$$

Sehingga:

$$
\boxed{
\tilde\mu_i
=
\hat\mu_i
-
C_i.
}
$$

Inilah expected return yang seharusnya masuk optimizer.

---

# M.49. Market impact

Untuk order yang lebih besar:

$$
Impact(q)
$$

meningkat terhadap ukuran order.

Model sederhana:

$$
Impact(q)
=
\eta
\left(
\frac{q}{ADV}
\right)^\gamma.
$$

Maka:

$$
C(q)
=
fee+
spread+
Impact(q).
$$

Ini nantinya menjadi bagian penting dari optimasi position sizing.

---

# M.50. Kita sekarang mempunyai problem optimasi yang lebih realistis

Bukan:

$$
\max_w
\left(
\mu^Tw-\gamma w^T\Sigma w
\right).
$$

Tetapi:

$$
\boxed{
\max_w
\left[
\tilde\mu^Tw
-
\gamma w^T\Sigma w
-
C(w)
\right].
}
$$

Di sinilah sistem kita mulai berbeda dari portfolio optimization akademik sederhana.

---

# M.51. Hubungan dengan risk budget

Karena sebelumnya kita ingin setiap trade mengikuti:

$$
\$1
$$

risk budget, kita nantinya akan menghubungkan:

$$
w_i
$$

dengan:

$$
SL_i.
$$

Jika stop distance:

$$
d_i
$$

dan position size:

$$
q_i,
$$

maka approximate dollar risk:

$$
R_i
=
q_i d_i.
$$

Constraint:

$$
\boxed{
R_i\leq R_{\max}.
}
$$

Misalnya:

$$
R_{\max}=1.
$$

---

# M.52. Expected return menjadi expected PnL

Jika:

$$
q_i
$$

unit asset dan:

$$
\hat\mu_i
$$

expected return:

$$
E[PnL_i]
\approx
q_iP_i\hat\mu_i.
$$

Sedangkan risk:

$$
\sigma_{PnL,i}
\approx
q_iP_i\sigma_i.
$$

Jadi:

$$
\boxed{
\text{forecast layer}
\rightarrow
\text{position layer}
}
$$

mulai terbentuk.

---

# M.53. Sekarang covariance menjadi sangat penting

Untuk portfolio:

$$
w=
\begin{bmatrix}
w_1\\
\vdots\\
w_N
\end{bmatrix},
$$

expected return:

$$
\boxed{
E[R_p]=w^T\mu.
}
$$

Risk:

$$
\boxed{
Var(R_p)=w^T\Sigma w.
}
$$

---

# M.54. Ini langsung menuju QUBO

Misalnya binary decision:

$$
x_i\in\{0,1\}.
$$

Kita definisikan:

$$
w_i=q_ix_i.
$$

Objective:

$$
\max_x
\left[
\sum_i\mu_iq_ix_i
-
\gamma
\sum_{i,j}
\Sigma_{ij}q_iq_jx_ix_j
\right].
$$

Karena:

$$
x_i^2=x_i,
$$

maka objective dapat ditulis sebagai:

$$
\boxed{
\max_x
\left[
\sum_i a_ix_i
-
\sum_{i<j}b_{ij}x_ix_j
\right].
}
$$

Ini adalah QUBO.

---

# M.55. Koefisien linear

$$
\boxed{
a_i
=
\tilde\mu_iq_i
-
\gamma\Sigma_{ii}q_i^2.
}
$$

Jadi expected return forecast mempengaruhi:

$$
\boxed{
Q_{ii}.
}
$$

---

# M.56. Koefisien interaksi

Untuk $i\neq j$:

$$
\boxed{
b_{ij}
=
2\gamma
\Sigma_{ij}q_iq_j.
}
$$

Jadi covariance forecast menentukan interaksi:

$$
\boxed{
Q_{ij}.
}
$$

Ini sangat penting:

> **Factor Engine bukan modul terpisah dari QAOA.**

Outputnya secara langsung menentukan landscape energi yang akan dieksplorasi quantum optimizer.

---

# M.57. Hubungan lengkap

Sekarang kita memiliki:

$$
\boxed{
\text{Market Data}
}
$$

$$
\downarrow
$$

$$
\boxed{
\text{Factors}
}
$$

$$
\downarrow
$$

$$
\boxed{
\hat\mu,\Sigma
}
$$

$$
\downarrow
$$

$$
\boxed{
QUBO
}
$$

$$
\downarrow
$$

$$
\boxed{
H_C
}
$$

$$
\downarrow
$$

$$
\boxed{
QAOA
}
$$

$$
\downarrow
$$

$$
\boxed{
Portfolio / Trade Selection
}
$$

---

# M.58. Bahkan factor exposure dapat masuk ke constraint

Misalnya kita tidak ingin portfolio terlalu exposed terhadap BTC.

Portfolio beta:

$$
\beta_p
=
B^Tw.
$$

Kita dapat memberikan constraint:

$$
\boxed{
|\beta_{p,BTC}|
\leq
\beta_{max}.
}
$$

Begitu juga:

$$
|\beta_{p,DXY}|
\leq
\beta_{DXY,max}.
$$

Ini memungkinkan kita mengontrol **factor risk**, bukan hanya volatility.

---

# M.59. Factor-neutral portfolio

Jika kita menginginkan:

$$
\beta_p\approx0,
$$

maka:

$$
\boxed{
B^Tw\approx0.
}
$$

Ini menghasilkan portfolio yang relatif netral terhadap factor tertentu.

Contohnya:

$$
\beta_{p,DXY}\approx0.
$$

Dengan demikian profit/loss lebih banyak berasal dari:

$$
idiosyncratic\ alpha.
$$

---

# M.60. Tetapi untuk sistem trading kita

Kita tidak selalu ingin factor-neutral.

Karena jika model memperkirakan:

$$
\hat r_{BTC}>0,
$$

kita mungkin **memang ingin mengambil BTC exposure**.

Jadi factor exposure sebaiknya menjadi:

$$
\boxed{
decision\ variable
}
$$

bukan selalu constraint nol.

---

# M.61. Dynamic factor exposure

Kita dapat menentukan target:

$$
\beta_p^\star
$$

berdasarkan regime.

Misalnya:

$$
\beta_{BTC,p}^\star
=
f(
\hat r_{BTC},
\sigma_{BTC},
regime
).
$$

Kemudian optimizer mencari portfolio yang mendekati target tersebut.

Ini sudah jauh lebih advanced.

---

# M.62. Tetapi belum kita masukkan ke V1

Untuk menjaga eksperimen tetap dapat dibuktikan, V1:

$$
\boxed{
\text{factor exposure}
\rightarrow
\mu,\Sigma
}
$$

sedangkan:

$$
factor\ constraints
$$

kita masukkan setelah baseline tervalidasi.

Ini penting untuk menghindari sistem menjadi terlalu kompleks sebelum kita tahu apakah alpha dasarnya benar-benar ada.

---

# M.63. Output final Tahap M

Pada setiap waktu $t$, Factor Engine harus menghasilkan object konseptual:

$$
\boxed{
\mathcal M_t
=
\{
\hat\mu_t,
\Sigma_t,
B_t,
\hat f_{t+1},
\Sigma_{F,t},
\Sigma_{\epsilon,t},
\hat\epsilon_t,
C_t,
Q_t
\}.
}
$$

Dengan:

### Forecast

$$
\hat\mu_t.
$$

### Risk

$$
\Sigma_t.
$$

### Factor exposure

$$
B_t.
$$

### Factor forecast

$$
\hat f_{t+1}.
$$

### Residual forecast

$$
\hat\epsilon_t.
$$

### Trading cost

$$
C_t.
$$

### Confidence-adjusted alpha

$$
Q_t.
$$

---

# M.64. Quality control Tahap M

Sebelum kita menggunakan output ini untuk trading, kita harus menguji:

### 1. Directional accuracy

$$
P(
sign(\hat\mu_t)
=
sign(r_{t+1})
).
$$

### 2. Information coefficient

$$
IC=
Corr(\hat\mu_t,r_{t+1}).
$$

### 3. Calibration

Apakah:

$$
\hat\mu=0.2\%
$$

benar-benar menghasilkan realized return sekitar:

$$
0.2\%
$$

secara statistik?

### 4. Stability

Apakah parameter stabil terhadap waktu?

### 5. Turnover

Apakah signal berubah terlalu cepat?

---

# M.65. Yang paling penting: forecast tidak dinilai dari satu trade

Misalnya model mengatakan:

$$
\hat\mu=0.15\%.
$$

Tetapi realized:

$$
r=-0.3\%.
$$

Itu tidak berarti model gagal.

Yang kita evaluasi adalah:

$$
E[r\mid\hat\mu].
$$

Jika secara agregat:

$$
\hat\mu\uparrow
\quad\Rightarrow\quad
r\uparrow,
$$

model memiliki predictive power.

---

# M.66. Kita juga harus membandingkan dengan baseline

Model kita tidak boleh hanya dibandingkan dengan dirinya sendiri.

Minimal:

$$
\boxed{
Baseline\ 1:
\mu=0
}
$$

$$
\boxed{
Baseline\ 2:
historical\ mean
}
$$

$$
\boxed{
Baseline\ 3:
momentum\ only
}
$$

$$
\boxed{
Baseline\ 4:
factor\ model
}
$$

$$
\boxed{
Model\ 5:
factor+residual+momentum.
}
$$

Baru kita dapat mengetahui apakah kompleksitas tambahan memang menghasilkan alpha.

---

# M.67. Ini juga penting untuk tesis quantum kita

Karena nanti kita ingin membandingkan:

$$
Classical\ optimizer
$$

vs.

$$
QAOA.
$$

Kita **tidak boleh** membiarkan perbedaan forecasting membuat perbandingan optimizer menjadi tidak fair.

Maka:

$$
\boxed{
\text{same }\hat\mu_t
\text{ and same }\Sigma_t
}
$$

harus diberikan kepada:

$$
Classical,\ Exact,\ QAOA.
$$

Dengan demikian yang dibandingkan benar-benar:

$$
\boxed{
Optimization\ method
}
$$

bukan:

$$
Data/forecasting\ method.
$$

---

# M.68. Arsitektur lengkap sampai Tahap M

Sekarang sistem kita sudah menjadi:

```text
                    RAW MARKET DATA
                           │
                           ▼
                 ┌───────────────────┐
                 │   DATA ENGINE     │
                 │     Tahap L       │
                 └─────────┬─────────┘
                           │
                           ▼
                       F_t, X_t
                           │
                           ▼
                 ┌───────────────────┐
                 │  FACTOR ENGINE    │
                 │     Tahap M       │
                 └─────────┬─────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
        Forecast μ                  Risk Σ
             │                           │
             └─────────────┬─────────────┘
                           ▼
                     NET ALPHA
                           │
                           ▼
                     QUBO ENGINE
                           │
                           ▼
                    ISING HAMILTONIAN
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
             CLASSICAL             QAOA
                 │                   │
                 └─────────┬─────────┘
                           ▼
                    TRADE SELECTION
                           │
                           ▼
                    EXECUTION ENGINE
```

---

# M.69. Satu hal yang sangat penting

Sekarang kita dapat melihat bahwa **QAOA bukan predictor harga**.

QAOA tidak perlu mengetahui:

$$
BTC=115000.
$$

Ia juga tidak perlu mengetahui:

$$
DXY=98.3.
$$

Semua informasi tersebut sudah diproses menjadi:

$$
\boxed{
\hat\mu
\quad\text{dan}\quad
\Sigma.
}
$$

QAOA hanya menyelesaikan:

$$
\boxed{
\text{given current expected returns and risk structure,}
}
$$

> **kombinasi trade mana yang secara matematis paling optimal?**

Ini adalah pemisahan yang sangat sehat antara:

$$
\boxed{
Prediction
\neq
Optimization.
}
$$

---

# M.70. Dan inilah inti sistem kita

Secara keseluruhan:

$$
\boxed{
\mathcal F_t
\rightarrow
S_t
\rightarrow
(\hat\mu_t,\Sigma_t)
\rightarrow
Q_t
\rightarrow
H_C
\rightarrow
QAOA
\rightarrow
x_t^\star
}
$$

dengan:

$$
\boxed{
\hat\mu_t
=
E[r_{t+1}\mid\mathcal F_t]
}
$$

dan:

$$
\boxed{
\Sigma_t
=
B_t\Sigma_{F,t}B_t^T
+
\Sigma_{\epsilon,t}.
}
$$

Kemudian:

$$
\boxed{
Q_t
=
Q(\hat\mu_t,\Sigma_t,C_t,R_t)
}
$$

dan akhirnya:

$$
\boxed{
x_t^\star
=
\arg\min_{x\in\{0,1\}^n}
x^TQ_tx.
}
$$

Itulah jembatan matematis yang kita cari sejak awal.

---

## Apa yang berubah setelah Tahap M?

Sebelum Tahap M, kita hanya mempunyai:

$$
\text{market data}.
$$

Sekarang kita mempunyai **belief matematis tentang masa depan pasar**:

$$
\boxed{
\hat\mu_t
}
$$

serta **geometri risiko pasar**:

$$
\boxed{
\Sigma_t.
}
$$

Dan keduanya sekarang sudah siap diubah menjadi **masalah optimasi diskret**.

Tahap berikutnya yang paling natural adalah **Tahap N — Dynamic QUBO Construction & Position Sizing**. Di sana kita bisa menurunkan secara penuh, mulai dari

$$
\max_w
\left(
\mu^Tw-\gamma w^T\Sigma w
\right),
$$

kemudian memasukkan **transaction cost, SL/TP, \$1 risk budget, liquidity, maximum concurrent positions, long/short, cardinality, dan rebalancing**, lalu secara sistematis mengubahnya menjadi

$$
\boxed{x^TQx}
$$

dan akhirnya ke

$$
\boxed{
H_C=\sum_i h_iZ_i+\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

Di titik itulah koneksi antara **quantitative trading yang realistis** dan **QAOA/Ising optimization** akan menjadi sangat konkret.

## Prompt:
8/17/2026, 9:58:53 PM

lanjut Tahap N

## Response:
8/17/2026, 9:58:54 PM

> **Remembering**
>
>
> ****
>
> 
>
> **Recalled staged trading formulations and connected QUBO with risk sizing**
>
> 
>
> Worked for 5s

# Tahap N — Dynamic QUBO Construction & Position Sizing

Sekarang kita masuk ke tahap yang menurut saya **menjadi jantung matematis sistem trading kita**.

Pada Tahap M kita sudah memiliki:

$$
\hat{\boldsymbol\mu}_t
$$

sebagai expected return,

dan

$$
\hat{\boldsymbol\Sigma}_t
$$

sebagai covariance/risk structure.

Tetapi keduanya masih berada pada level **continuous portfolio theory**.

Trading nyata membutuhkan keputusan diskret:

> aset mana yang dibeli, berapa besar posisinya, long atau short, pada harga berapa, dengan stop-loss berapa, dan apakah kombinasi seluruh posisi tersebut masih memenuhi risk budget?

Maka Tahap N bertugas melakukan transformasi:

$$
\boxed{
(\hat{\mu}_t,\Sigma_t)
\longrightarrow
\text{Trading Optimization}
\longrightarrow
\text{QUBO}
\longrightarrow
\text{Ising Hamiltonian}
}
$$

dan pada akhirnya menghasilkan:

$$
\boxed{x_t^\star}
$$

yang dapat diberikan kepada execution engine.

---

# N.1. Masalah sebenarnya yang ingin kita selesaikan

Misalkan terdapat $N$ aset.

Untuk setiap aset $i$, kita mengetahui:

$$
P_i
$$

harga saat ini,

$$
\hat\mu_i
$$

expected return,

$$
\sigma_i^2
$$

variance,

dan:

$$
\Sigma_{ij}
$$

covariance.

Kita ingin menentukan:

$$
w_i.
$$

Secara klasik:

$$
\boxed{
\max_{\mathbf w}
\left[
\hat{\boldsymbol\mu}^T\mathbf w
-
\gamma
\mathbf w^T
\Sigma
\mathbf w
\right].
}
$$

Tetapi ini belum cukup untuk trading kita.

---

# N.2. Mengapa Markowitz biasa belum cukup?

Markowitz menganggap:

$$
w_i\in\mathbb R.
$$

Padahal sistem kita memiliki keputusan seperti:

$$
\text{BUY}
$$

atau:

$$
\text{DO NOTHING}
$$

atau:

$$
\text{SHORT}.
$$

Selain itu kita memiliki:

- minimum order size,
- maximum position,
- \$1 risk budget,
- stop-loss,
- take-profit,
- transaction cost,
- slippage,
- liquidity,
- maximum number of simultaneous positions.

Jadi problem sebenarnya adalah:

$$
\boxed{
\text{Mixed discrete-constrained portfolio optimization}.
}
$$

---

# N.3. Kita mulai dari satu trade

Sebelum membuat portfolio, mari kita pahami satu posisi.

Misalkan kita ingin long asset $i$.

Harga:

$$
P_i.
$$

Stop-loss:

$$
SL_i.
$$

Definisikan stop distance:

$$
\boxed{
d_i=P_i-SL_i
}
$$

untuk long.

Jika kita membeli:

$$
q_i
$$

unit, maka approximate maximum loss:

$$
R_i=q_i d_i.
$$

Kita ingin:

$$
R_i\leq R_{\max}.
$$

Dengan risk budget:

$$
\boxed{
R_{\max}=\$1.
}
$$

Maka:

$$
q_i d_i\leq1.
$$

Sehingga:

$$
\boxed{
q_i\leq\frac{1}{d_i}.
}
$$

Ini adalah dasar position sizing kita.

---

# N.4. Position sizing bukan berdasarkan modal

Ini perbedaan penting.

Sistem kita tidak berkata:

> Saya memiliki \$1000, maka saya membeli \$100 BTC.

Sebaliknya:

> Berapa ukuran posisi yang menghasilkan maksimal \$1 loss jika SL tersentuh?

Secara sederhana:

$$
\boxed{
q_i=
\frac{R_{\max}}
{d_i}.
}
$$

Dengan:

$$
R_{\max}=1.
$$

---

# N.5. Contoh

Misalkan:

$$
P_i=100
$$

dan:

$$
SL_i=98.
$$

Maka:

$$
d_i=2.
$$

Dengan:

$$
R_{\max}=1,
$$

kita memperoleh:

$$
q_i=\frac{1}{2}=0.5.
$$

Notional:

$$
N_i=q_iP_i=50.
$$

Jadi posisi \$50 memiliki stop-loss sekitar \$1.

---

# N.6. Tetapi kita tidak ingin $q_i$ selalu kontinu

Quantum optimization paling natural ketika keputusan kita diskret.

Maka kita melakukan **discretization**.

Misalkan kita memiliki level position:

$$
q_{i,1},q_{i,2},\ldots,q_{i,L}.
$$

Contohnya:

$$
L=3
$$

dengan:

$$
q_{i,1}=0.25q_i^{max},
$$

$$
q_{i,2}=0.50q_i^{max},
$$

$$
q_{i,3}=1.00q_i^{max}.
$$

---

# N.7. Binary encoding

Definisikan binary variables:

$$
x_{i,k}\in\{0,1\}.
$$

Dengan:

$$
x_{i,k}=1
$$

berarti level $k$ dipilih.

Position:

$$
\boxed{
q_i
=
\sum_{k=1}^{L}
q_{i,k}x_{i,k}.
}
$$

---

# N.8. Tetapi kita harus mencegah memilih dua level sekaligus

Misalnya:

$$
x_{i,1}=1
$$

dan:

$$
x_{i,3}=1.
$$

Maka kita mendapatkan:

$$
q_i=q_{i,1}+q_{i,3},
$$

yang tidak kita inginkan jika level tersebut mutually exclusive.

Constraint:

$$
\boxed{
\sum_kx_{i,k}\leq1.
}
$$

---

# N.9. Mengubah constraint menjadi penalty

Karena QUBO membutuhkan objective tanpa constraint eksplisit, kita masukkan penalty:

$$
P_i
\left(
\sum_kx_{i,k}-1
\right)^2.
$$

Tetapi jika zero position diperbolehkan, kita sebenarnya membutuhkan:

$$
\sum_kx_{i,k}\leq1.
$$

Untuk binary variable, bentuk penalty yang lebih tepat dapat menggunakan:

$$
\boxed{
P_i\sum_{k<l}x_{i,k}x_{i,l}.
}
$$

Jika dua level dipilih sekaligus, penalty muncul.

---

# N.10. Sekarang kita masukkan expected return

Untuk position:

$$
q_i,
$$

expected PnL:

$$
E[\Pi_i]
\approx
P_iq_i\hat\mu_i.
$$

Definisikan:

$$
a_{i,k}
=
P_iq_{i,k}\tilde\mu_i.
$$

Dengan:

$$
\tilde\mu_i
=
\hat\mu_i-C_i.
$$

Maka contribution:

$$
\boxed{
\Pi_i^{expected}
=
\sum_k
a_{i,k}x_{i,k}.
}
$$

---

# N.11. Mengapa kita menggunakan net alpha?

Karena expected return mentah:

$$
\hat\mu_i
$$

belum mempertimbangkan:

$$
fee+spread+slippage+impact.
$$

Maka:

$$
\boxed{
\tilde\mu_i
=
\hat\mu_i-C_i.
}
$$

Kalau:

$$
\tilde\mu_i<0,
$$

trade tersebut secara expected value sudah buruk bahkan sebelum risk diperhitungkan.

---

# N.12. Sekarang masukkan portfolio risk

Position vector dalam notional:

$$
w_i=P_iq_i.
$$

Maka:

$$
w^T\Sigma w
$$

adalah portfolio variance.

Karena:

$$
w_i
=
P_i
\sum_kq_{i,k}x_{i,k},
$$

kita memperoleh:

$$
\boxed{
Var(R_p)
=
\sum_i\sum_j
w_iw_j\Sigma_{ij}.
}
$$

---

# N.13. Ekspansi binary

Substitusi:

$$
w_i=P_i\sum_kq_{i,k}x_{i,k}.
$$

Maka:

$$
Var(R_p)
=
\sum_{i,j}
P_iP_j
\Sigma_{ij}
\left(
\sum_kq_{i,k}x_{i,k}
\right)
\left(
\sum_lq_{j,l}x_{j,l}
\right).
$$

Sehingga:

$$
\boxed{
Var(R_p)
=
\sum_{i,j}
\sum_{k,l}
P_iP_j
q_{i,k}q_{j,l}
\Sigma_{ij}
x_{i,k}x_{j,l}.
}
$$

Inilah yang membuat masalah kita menjadi QUBO.

---

# N.14. Objective utama

Kita ingin:

$$
\max
\left[
Expected\ PnL
-
Risk\ Penalty
-
Trading\ Cost
-
Constraint\ Penalty
\right].
$$

Secara matematis:

$$
\boxed{
\max_x
\left[
\tilde\mu^Tw
-
\gamma w^T\Sigma w
-
P(x)
\right].
}
$$

---

# N.15. Karena QUBO biasanya ditulis sebagai minimization

Kita ubah tanda:

$$
\boxed{
\min_x
\left[
-\tilde\mu^Tw
+
\gamma w^T\Sigma w
+
P(x)
\right].
}
$$

Definisikan:

$$
E(x)=
-\tilde\mu^Tw
+
\gamma w^T\Sigma w
+
P(x).
$$

Maka:

$$
\boxed{
x^\star=\arg\min_xE(x).
}
$$

---

# N.16. Dari sini QUBO muncul secara alami

Karena:

$$
x_i^2=x_i
$$

untuk:

$$
x_i\in\{0,1\},
$$

semua objective dapat ditulis:

$$
\boxed{
E(x)
=
\sum_aQ_{aa}x_a
+
\sum_{a<b}Q_{ab}x_ax_b
+
C.
}
$$

atau:

$$
\boxed{
E(x)=x^TQx+C.
}
$$

---

# N.17. Index $a$ sekarang berarti apa?

Kita gabungkan:

$$
a=(i,k).
$$

Artinya satu binary variable mewakili:

> memilih asset $i$ pada position level $k$.

Misalnya:

$$
x_{BTC,1}
$$

berarti:

> pilih BTC dengan position level 1.

---

# N.18. Struktur QUBO kita

Secara konseptual:

$$
\boxed{
Q=
Q^{return}
+
Q^{risk}
+
Q^{cost}
+
Q^{constraint}.
}
$$

Ini sangat berguna karena kita dapat menganalisis setiap komponen secara terpisah.

---

# N.19. Return term

Untuk variable $x_{i,k}$:

$$
\boxed{
Q^{return}_{(i,k)}
=
-
P_iq_{i,k}\tilde\mu_i.
}
$$

Semakin besar expected profit:

$$
\tilde\mu_i,
$$

semakin negatif diagonal QUBO.

Karena optimizer ingin:

$$
E\rightarrow minimum.
$$

---

# N.20. Risk diagonal

Variance asset:

$$
\Sigma_{ii}.
$$

Contribution:

$$
\gamma
(P_iq_{i,k})^2
\Sigma_{ii}.
$$

Sehingga:

$$
\boxed{
Q^{risk}_{aa}
=
\gamma
(P_iq_{i,k})^2
\Sigma_{ii}.
}
$$

---

# N.21. Risk interaction

Untuk dua posisi:

$$
(i,k)
$$

dan:

$$
(j,l),
$$

interaction:

$$
\boxed{
Q^{risk}_{ab}
\propto
\gamma
P_iP_j
q_{i,k}q_{j,l}
\Sigma_{ij}.
}
$$

Interpretasinya sangat menarik.

Jika:

$$
\Sigma_{ij}>0,
$$

memilih kedua posisi bersama menghasilkan penalty.

Jika:

$$
\Sigma_{ij}<0,
$$

kombinasi tersebut dapat menurunkan portfolio risk.

---

# N.22. Ini sebenarnya inti "quantitative trading"

Misalnya:

$$
A
$$

memiliki expected return tinggi.

Tetapi:

$$
A
$$

sangat berkorelasi dengan:

$$
B.
$$

Optimizer dapat berkata:

> A bagus.

Tetapi:

> A + B terlalu redundant.

Sebaliknya:

$$
A+C
$$

mungkin lebih baik karena:

$$
Corr(A,C)<0.
$$

Jadi optimizer tidak hanya mencari:

$$
\text{best asset}.
$$

Ia mencari:

$$
\boxed{
\text{best combination}.
}
$$

---

# N.23. Maximum number of positions

Kita mungkin tidak ingin membuka 20 trade sekaligus.

Definisikan:

$$
y_i=
\sum_kx_{i,k}.
$$

Karena:

$$
y_i\in\{0,1\}
$$

jika level position dibuat mutually exclusive.

Constraint:

$$
\boxed{
\sum_i y_i\leq K_{max}.
}
$$

---

# N.24. Penalty cardinality

Kita dapat menggunakan:

$$
P_K
\left(
\sum_i y_i-K_{target}
\right)^2.
$$

Tetapi ini memaksa tepat $K_{target}$.

Jika yang kita inginkan adalah **maksimal** $K_{max}$, penalty dapat dibuat dengan auxiliary variables atau formulasi inequality-to-equality.

Untuk V1, saya menyarankan:

$$
\boxed{
\sum_i y_i\leq K_{max}
}
$$

ditangani melalui slack variable.

---

# N.25. Slack variable

Misalnya:

$$
\sum_i y_i+s=K_{max},
$$

dengan:

$$
s\geq0.
$$

Kemudian:

$$
s
$$

direpresentasikan dalam binary encoding:

$$
s=
\sum_m2^mz_m.
$$

Constraint menjadi:

$$
P_K
\left(
\sum_i y_i
+
\sum_m2^mz_m
-
K_{max}
\right)^2.
$$

Ini kemudian masuk QUBO.

---

# N.26. Risk budget portfolio

Sekarang masuk constraint yang lebih penting.

Kita ingin total worst-case stop-loss risk:

$$
\sum_iR_i
\leq R_{portfolio}.
$$

Dengan:

$$
R_i=q_i d_i.
$$

Maka:

$$
\boxed{
\sum_i
\sum_k
q_{i,k}d_i
x_{i,k}
\leq
R_{portfolio}.
}
$$

---

# N.27. Contoh

Jika:

$$
R_{portfolio}=\$5,
$$

dan:

$$
R_i=\$1
$$

untuk setiap posisi, maka maksimal lima posisi secara kasar dapat dibuka.

Tetapi optimizer juga melihat covariance.

Jadi mungkin ia memilih:

$$
3
$$

posisi saja jika ketiganya sangat correlated.

---

# N.28. Ini penting

Risk budget dan variance risk **bukan hal yang sama**.

Risk budget:

$$
\sum_iR_i.
$$

Variance:

$$
w^T\Sigma w.
$$

Kita membutuhkan keduanya.

Risk budget menjawab:

> Berapa banyak uang yang bisa hilang jika SL tersentuh?

Variance menjawab:

> Seberapa besar ketidakpastian portfolio secara statistik?

---

# N.29. Position sizing yang lebih realistis

Sebelumnya:

$$
q_i=\frac{1}{d_i}.
$$

Tetapi volatility juga harus dipertimbangkan.

Misalkan:

$$
\sigma_i
$$

besar.

Maka position yang secara SL-risk aman belum tentu secara portfolio volatility aman.

Jadi kita memiliki dua filter:

$$
\boxed{
Stop\ Risk
}
$$

dan:

$$
\boxed{
Statistical\ Risk.
}
$$

---

# N.30. Volatility-adjusted risk

Kita dapat mendefinisikan target risk:

$$
R_i^{stat}
=
w_i\sigma_i.
$$

Kemudian:

$$
R_i^{stat}\leq R_{i,max}^{stat}.
$$

Ini bisa menjadi constraint tambahan.

---

# N.31. Tetapi kita harus hati-hati dengan double counting

Jika:

$$
\Sigma
$$

sudah masuk objective:

$$
\gamma w^T\Sigma w,
$$

kita tidak perlu memberikan penalty volatility individual terlalu besar lagi.

Kalau tidak:

$$
\sigma_i
$$

akan dihukum dua kali.

Karena itu:

> **SL risk digunakan sebagai hard/soft constraint, sedangkan covariance digunakan sebagai portfolio risk objective.**

Ini desain yang lebih bersih.

---

# N.32. Long dan short

Sekarang sistem kita harus mampu:

$$
x_i^{long}
$$

dan:

$$
x_i^{short}.
$$

Kita tidak bisa menggunakan satu binary variable lagi.

Gunakan:

$$
x_i^L\in\{0,1\},
$$

$$
x_i^S\in\{0,1\}.
$$

---

# N.33. Mutually exclusive long-short

Tidak boleh:

$$
x_i^L=x_i^S=1.
$$

Constraint:

$$
\boxed{
x_i^L+x_i^S\leq1.
}
$$

Penalty:

$$
\boxed{
P_{LS}x_i^Lx_i^S.
}
$$

---

# N.34. Signed position

Position:

$$
w_i
=
w_i^L-w_i^S.
$$

Dengan:

$$
w_i^L
=
\sum_kq_{i,k}^LP_i x_{i,k}^L
$$

dan:

$$
w_i^S
=
\sum_kq_{i,k}^SP_i x_{i,k}^S.
$$

Maka:

$$
\boxed{
w_i
=
w_i^L-w_i^S.
}
$$

---

# N.35. Expected return short

Jika:

$$
\hat\mu_i<0,
$$

short dapat memiliki expected profit:

$$
E[PnL_i^{short}]
=
-w_i\hat\mu_i.
$$

Secara umum:

$$
\boxed{
E[PnL]
=
\sum_iw_i\hat\mu_i.
}
$$

Karena $w_i<0$ untuk short.

---

# N.36. Covariance untuk long-short

Tidak perlu membuat formula baru.

Tetap:

$$
\boxed{
Var(R_p)=w^T\Sigma w.
}
$$

Karena $w_i$ sekarang signed.

Menariknya, posisi short secara alami menghasilkan perubahan tanda pada covariance term.

---

# N.37. Hedging muncul otomatis

Misalkan:

$$
Corr(A,B)=0.9.
$$

Jika kita long A dan short B:

$$
w_A>0,
$$

$$
w_B<0.
$$

Maka:

$$
w_Aw_B\Sigma_{AB}<0.
$$

Portfolio variance dapat turun.

Jadi optimizer dapat menemukan:

$$
\boxed{
hedging\ structure
}
$$

secara matematis.

---

# N.38. Take Profit

Sekarang kita masuk ke TP.

Misalkan entry:

$$
P_i.
$$

TP:

$$
TP_i.
$$

Untuk long:

$$
g_i=TP_i-P_i.
$$

Reward:

$$
G_i=q_ig_i.
$$

Stop loss:

$$
L_i=q_id_i.
$$

Reward-risk ratio:

$$
\boxed{
RR_i=\frac{g_i}{d_i}.
}
$$

---

# N.39. TP tidak harus masuk langsung ke objective

Ini keputusan desain penting.

Expected return:

$$
\hat\mu_i
$$

sudah menggambarkan forecast return.

Jika kita sekaligus memasukkan TP sebagai expected return tanpa model probabilitas menyentuh TP, kita akan melakukan double counting.

Jadi untuk V1:

$$
\boxed{
TP
\rightarrow
execution/risk\ layer
}
$$

bukan langsung:

$$
TP
\rightarrow
expected\ return.
$$

---

# N.40. Tetapi TP dapat digunakan sebagai feasibility constraint

Misalnya kita hanya mau trade jika:

$$
E[R_i]
$$

cukup besar dibandingkan stop risk.

Definisikan:

$$
RR_i^{expected}
=
\frac{\hat\mu_i}{d_i/P_i}.
$$

Kita dapat meminta:

$$
\boxed{
RR_i^{expected}\geq RR_{min}.
}
$$

---

# N.41. Expected return relatif terhadap stop

Fractional stop distance:

$$
s_i
=
\frac{d_i}{P_i}.
$$

Expected return:

$$
\hat\mu_i.
$$

Maka:

$$
\boxed{
ER/SL_i
=
\frac{\hat\mu_i}{s_i}.
}
$$

Jika:

$$
\frac{\hat\mu_i}{s_i}
$$

terlalu kecil, trade mungkin tidak menarik.

---

# N.42. Tetapi jangan menyamakan ini dengan probability of TP

Ini penting secara finansial.

$$
\hat\mu_i
$$

adalah conditional expected return.

Sedangkan:

$$
P(TP)
$$

adalah hitting probability.

Keduanya berbeda.

Jika nanti kita membangun **Barrier-Hitting Model**, barulah TP dan SL dapat masuk secara probabilistik.

Untuk Tahap N kita belum melakukan itu.

---

# N.43. Liquidity constraint

Position tidak boleh lebih besar daripada liquidity.

Misalnya:

$$
ADV_i
$$

average daily volume.

Kita dapat menetapkan:

$$
\boxed{
|w_i|
\leq
\eta ADV_iP_i.
}
$$

Dengan:

$$
\eta
$$

misalnya hanya sebagian kecil dari volume yang dianggap aman.

---

# N.44. Untuk short-term trading, order book lebih baik

Karena sistem kita memang akan menggunakan order book, kita dapat mengganti ADV dengan:

$$
D_i^{book}
$$

depth yang tersedia di sekitar harga entry.

Maka:

$$
\boxed{
q_i
\leq
\eta D_i^{book}.
}
$$

Ini jauh lebih relevan untuk execution.

---

# N.45. Slippage

Jika depth tipis:

$$
Slippage_i(q)
$$

meningkat.

Jadi cost:

$$
C_i(q)
=
fee_i
+
spread_i
+
slippage_i(q).
$$

Karena:

$$
slippage_i(q)
$$

bergantung pada $q$, objective dapat menjadi nonlinear.

---

# N.46. Untuk QUBO kita discretize cost

Misalnya setiap position level:

$$
q_{i,k}
$$

mempunyai:

$$
C_{i,k}.
$$

Maka:

$$
\boxed{
Cost
=
\sum_{i,k}
C_{i,k}x_{i,k}.
}
$$

Dengan demikian cost tetap linear dalam binary variables.

Ini salah satu alasan mengapa discretization sangat berguna.

---

# N.47. QUBO final V1

Sekarang kita dapat menulis:

$$
\boxed{
E(x)
=
E_{return}
+
E_{risk}
+
E_{cost}
+
E_{SL}
+
E_{cardinality}
+
E_{exclusive}
+
E_{liquidity}.
}
$$

---

# N.48. Return term

$$
\boxed{
E_{return}
=
-\sum_{i,k}
P_iq_{i,k}\hat\mu_i x_{i,k}.
}
$$

---

# N.49. Risk term

$$
\boxed{
E_{risk}
=
\gamma
\sum_{i,j}
\sum_{k,l}
P_iP_j
q_{i,k}q_{j,l}
\Sigma_{ij}
x_{i,k}x_{j,l}.
}
$$

---

# N.50. Cost term

$$
\boxed{
E_{cost}
=
\sum_{i,k}
C_{i,k}x_{i,k}.
}
$$

---

# N.51. SL-risk constraint

Define:

$$
r_{i,k}
=
q_{i,k}d_i.
$$

Constraint:

$$
\sum_{i,k}
r_{i,k}x_{i,k}
\leq
R_{\max}.
$$

Dengan slack:

$$
\sum_{i,k}
r_{i,k}x_{i,k}
+s
=
R_{\max}.
$$

Penalty:

$$
\boxed{
E_{SL}
=
\lambda_{SL}
\left(
\sum_{i,k}
r_{i,k}x_{i,k}
+s-R_{\max}
\right)^2.
}
$$

---

# N.52. Cardinality

Misalnya maksimal:

$$
K_{\max}
$$

positions.

$$
\sum_i y_i+s_K=K_{\max}.
$$

Penalty:

$$
\boxed{
E_{cardinality}
=
\lambda_K
\left(
\sum_i y_i+s_K-K_{\max}
\right)^2.
}
$$

---

# N.53. Long-short exclusivity

$$
\boxed{
E_{exclusive}
=
\lambda_{LS}
\sum_i
x_i^Lx_i^S.
}
$$

---

# N.54. Liquidity

Jika position level sudah dibatasi sehingga:

$$
q_{i,k}\leq q_{i,max}^{liquidity},
$$

maka liquidity constraint sebenarnya dapat diselesaikan **sebelum** QUBO.

Ini lebih baik daripada menambahkan penalty.

Kita dapat menghapus position levels yang tidak feasible.

---

# N.55. Ini adalah prinsip desain penting

Tidak semua constraint harus menjadi QUBO penalty.

Ada tiga jenis:

### Hard preprocessing

Contoh:

$$
q_{i,k}>q_{max}
$$

langsung dibuang.

### QUBO penalty

Constraint yang memang perlu dioptimasi bersama.

### Objective

Return dan risk.

Dengan demikian QUBO tidak menjadi terlalu besar.

---

# N.56. Final QUBO

Setelah semua ekspansi:

$$
\boxed{
E(x)
=
x^TQx+C.
}
$$

Kemudian:

$$
\boxed{
x^\star
=
\arg\min_{x\in\{0,1\}^M}
x^TQx.
}
$$

Dengan:

$$
M
=
N\times L\times D
$$

untuk kombinasi:

- $N$: assets,
- $L$: position levels,
- $D$: direction.

---

# N.57. Contoh ukuran problem

Misalkan:

$$
N=20
$$

aset.

Position levels:

$$
L=3.
$$

Direction:

$$
D=2.
$$

Maka:

$$
M=20\times3\times2=120
$$

binary variables.

QUBO:

$$
Q\in\mathbb R^{120\times120}.
$$

Kemudian:

$$
120
$$

qubits diperlukan untuk direct QAOA encoding.

Ini mulai menjadi problem yang serius.

---

# N.58. Dan di sinilah quantum advantage tidak boleh diasumsikan

Kita **tidak boleh** mengatakan:

> QAOA pasti lebih cepat.

Belum tentu.

Untuk ukuran kecil:

$$
N=4,8,12
$$

classical solver mungkin jauh lebih cepat.

Nilai penelitian kita adalah menguji:

$$
\boxed{
QAOA
\text{ vs classical optimization}
}
$$

pada **problem yang sama**.

---

# N.59. Exact solver sebagai ground truth

Untuk problem kecil, kita bisa melakukan exhaustive search:

$$
2^M
$$

kombinasi.

Kemudian:

$$
E_{min}
=
\min_xE(x).
$$

Ini menjadi:

$$
\boxed{
E_{ground\ truth}.
}
$$

QAOA kemudian dibandingkan terhadap ground truth.

---

# N.60. Approximation ratio

Jika objective kita adalah minimization:

$$
r
=
\frac{E_{QAOA}-E_{min}}
{|E_{min}|}.
$$

Semakin:

$$
r\rightarrow0,
$$

semakin dekat QAOA terhadap optimum.

---

# N.61. Tetapi untuk trading kita membutuhkan metrik kedua

Quantum optimizer mungkin menemukan solusi dengan:

$$
E(x)
$$

sangat bagus.

Tetapi belum tentu realized PnL bagus.

Karena itu kita membutuhkan dua level evaluasi:

### Optimization quality

$$
E(x).
$$

### Financial quality

$$
PnL,
Sharpe,
MDD,
turnover,
hit\ rate,
risk\ adherence.
$$

---

# N.62. Ini menghasilkan dua eksperimen berbeda

### Eksperimen A

> Apakah QAOA dapat menemukan solusi QUBO yang dekat dengan optimum?

### Eksperimen B

> Apakah solusi tersebut menghasilkan trading performance yang baik out-of-sample?

Jangan mencampurkan keduanya.

---

# N.63. Dynamic QUBO

Inilah alasan kita menyebut Tahap N **Dynamic**.

Setiap periode:

$$
t
$$

kita mendapatkan:

$$
\hat\mu_t,
\Sigma_t,
P_t,
SL_t,
C_t,
Liquidity_t.
$$

Maka:

$$
\boxed{
Q_t
=
Q(
\hat\mu_t,
\Sigma_t,
P_t,
SL_t,
C_t,
Liquidity_t
).
}
$$

Jadi:

$$
Q_{t+1}\neq Q_t
$$

secara umum.

---

# N.64. Pasar mengubah Hamiltonian

Ini menurut saya bagian paling menarik dari keseluruhan desain.

Karena:

$$
Q_t
$$

berasal dari market state, maka:

$$
H_C(t)
$$

juga berubah.

Secara konseptual:

$$
\boxed{
Market
\rightarrow
Q_t
\rightarrow
H_C(t)
}
$$

Jadi kita memiliki **time-dependent optimization landscape**.

---

# N.65. Namun QAOA tidak "memprediksi" perubahan landscape

Forecasting layer:

$$
\mathcal F_t
\rightarrow
\hat\mu_t,\Sigma_t.
$$

Optimization layer:

$$
(\hat\mu_t,\Sigma_t)
\rightarrow
Q_t.
$$

Quantum layer:

$$
Q_t
\rightarrow
x_t^\star.
$$

Ini tiga layer yang harus tetap dipisahkan:

$$
\boxed{
Prediction
\rightarrow
Optimization
\rightarrow
Execution.
}
$$

---

# N.66. Menghubungkannya ke Ising

Setelah QUBO:

$$
x_i\in\{0,1\},
$$

kita gunakan:

$$
\boxed{
x_i=\frac{1-Z_i}{2}.
}
$$

Dengan:

$$
Z_i\in\{-1,+1\}.
$$

Substitusi:

$$
x^TQx
$$

menghasilkan:

$$
\boxed{
H_C
=
\sum_i h_iZ_i
+
\sum_{i<j}J_{ij}Z_iZ_j
+
C.
}
$$

Konstanta $C$ tidak memengaruhi argmin.

---

# N.67. Interpretasi fisiknya

Sekarang setiap qubit merepresentasikan keputusan:

$$
Z_i=-1
$$

atau:

$$
Z_i=+1.
$$

Yang secara ekonomi berarti:

$$
\boxed{
trade\ tidak\ dipilih
}
$$

atau:

$$
\boxed{
trade\ dipilih.
}
$$

Kemudian:

$$
J_{ij}
$$

merepresentasikan interaction antara dua keputusan.

---

# N.68. Hubungan dengan covariance

Ini sangat menarik.

Karena QUBO memiliki:

$$
\Sigma_{ij},
$$

maka Ising coupling akan mengandung:

$$
\boxed{
J_{ij}
\sim
\gamma
P_iP_jq_iq_j\Sigma_{ij}.
}
$$

Jadi:

> **correlation structure pasar diterjemahkan menjadi coupling antar-qubit.**

Asset yang highly correlated:

$$
\Sigma_{ij}>0
$$

menghasilkan coupling tertentu yang membuat pemilihan keduanya menjadi kurang/lebih energetically favorable tergantung konvensi tanda Hamiltonian.

---

# N.69. Factor model bahkan masuk secara tidak langsung ke coupling

Ingat:

$$
\Sigma
=
B\Sigma_FB^T+\Sigma_\epsilon.
$$

Maka:

$$
J_{ij}
\sim
\gamma
P_iP_j
\left(
B_i\Sigma_FB_j^T
+
\Sigma_{\epsilon,ij}
\right).
$$

Artinya:

$$
\boxed{
J_{ij}
}
$$

sebenarnya membawa informasi:

- BTC exposure,
- ETH exposure,
- Gold exposure,
- USD exposure,
- equity exposure,
- volatility exposure,
- residual correlation.

Dengan kata lain:

> **market structure menjadi quantum interaction structure.**

Ini adalah salah satu bagian paling kuat dari arsitektur penelitian kita.

---

# N.70. Contoh sederhana

Misalkan terdapat:

$$
BTC,\ ETH,\ Gold.
$$

Factor matrix:

$$
B=
\begin{bmatrix}
1.0&0.5&0&0\\
0.8&0.7&0&0\\
0&0&1.2&-0.3
\end{bmatrix}.
$$

Dengan factor:

$$
[BTC,ETH,Gold,DXY].
$$

Maka covariance asset tidak lagi muncul sebagai angka arbitrer.

Ia berasal dari:

$$
\boxed{
B\Sigma_FB^T+\Sigma_\epsilon.
}
$$

---

# N.71. Ini membuat sistem kita jauh lebih interpretable

Kita dapat menjawab:

> Mengapa optimizer tidak memilih asset A?

Bisa jadi:

$$
\hat\mu_A
$$

rendah.

Atau:

$$
\Sigma_{AA}
$$

tinggi.

Atau:

$$
\Sigma_{AB}
$$

tinggi dengan posisi B yang sudah dipilih.

Atau:

$$
SL_A
$$

terlalu dekat/jauh.

Atau:

$$
cost_A
$$

terlalu besar.

Atau risk budget sudah habis.

Ini jauh lebih baik daripada black-box:

$$
input\rightarrow BUY.
$$

---

# N.72. Position sizing dan SL sekarang terhubung

Kita dapat merumuskan:

$$
q_{i,k}
=
\frac{\rho_kR_{\max}}{d_i},
$$

dengan:

$$
\rho_k\in(0,1].
$$

Misalnya:

$$
\rho=
\{0.25,0.5,1.0\}.
$$

Maka setiap asset secara otomatis memiliki position size yang menyesuaikan SL.

---

# N.73. Contoh

Asset A:

$$
d_A=0.5.
$$

Asset B:

$$
d_B=2.
$$

Dengan:

$$
R_{\max}=1.
$$

Maka maximum position:

$$
q_A^{max}=2,
$$

sedangkan:

$$
q_B^{max}=0.5.
$$

Jadi asset dengan SL lebih lebar secara otomatis mendapatkan position lebih kecil.

---

# N.74. Ini menjawab salah satu masalah utama trading

Kita tidak boleh mengatakan:

> setiap trade membeli nominal yang sama.

Karena:

$$
\$100
$$

pada asset volatility rendah tidak sama risikonya dengan:

$$
\$100
$$

pada asset volatility tinggi.

Risk-based sizing memperbaiki hal tersebut.

---

# N.75. Tetapi \$1 bukan berarti guaranteed loss = \$1

Ini harus kita definisikan dengan benar.

Secara model:

$$
R_i=q_id_i\leq1.
$$

Tetapi realized loss dapat lebih besar karena:

$$
slippage,
$$

$$
gap,
$$

$$
market\ impact,
$$

atau:

$$
execution\ failure.
$$

Jadi \$1 adalah:

$$
\boxed{
modelled\ stop\ risk
}
$$

bukan jaminan matematis bahwa realized loss selalu tepat \$1.

---

# N.76. Maka kita dapat menambahkan safety multiplier

Misalnya:

$$
\kappa>1.
$$

Effective risk budget:

$$
\boxed{
R_i^{effective}
=
\kappa q_id_i.
}
$$

Jika:

$$
\kappa=1.2,
$$

kita menganggap ada 20% buffer.

Namun nilai $\kappa$ nantinya harus **diestimasi dari data execution**, bukan dipilih sembarangan.

---

# N.77. Sekarang kita memiliki formulasi V1 yang cukup lengkap

Saya akan merangkum objective utama kita:

$$
\boxed{
\begin{aligned}
\min_x\quad
&
-\sum_{i,k}
P_iq_{i,k}\tilde\mu_i x_{i,k}
\\
&+
\gamma
\sum_{i,j}
\sum_{k,l}
P_iP_j
q_{i,k}q_{j,l}
\Sigma_{ij}
x_{i,k}x_{j,l}
\\
&+
\sum_{i,k}
C_{i,k}x_{i,k}
\\
&+
\lambda_{SL}
\left(
\sum_{i,k}
r_{i,k}x_{i,k}
+s-R_{\max}
\right)^2
\\
&+
\lambda_K
\left(
\sum_i y_i+s_K-K_{\max}
\right)^2
\\
&+
\lambda_{LS}
\sum_i x_i^Lx_i^S.
\end{aligned}
}
$$

Dengan:

$$
r_{i,k}=q_{i,k}d_i.
$$

---

# N.78. Ini kemudian menjadi

$$
\boxed{
E(x)=x^TQ_tx+C_t.
}
$$

Kemudian:

$$
\boxed{
x_t^\star
=
\arg\min_x
x^TQ_tx.
}
$$

Dan:

$$
\boxed{
x_t^\star
\rightarrow
Trade\ Plan_t.
}
$$

---

# N.79. Trade Plan

Output optimizer bukan langsung:

> BUY BTC.

Tetapi sesuatu seperti:

```text
Asset       Direction     Level     Position     SL       TP
BTC         LONG          2         0.004 BTC    ...      ...
ETH         LONG          1         0.010 ETH    ...      ...
SOL         NONE          -         0            -        -
```

Kemudian execution engine baru menentukan:

$$
limit\ price,
$$

$$
order\ book\ placement,
$$

$$
TP,
$$

$$
SL.
$$

---

# N.80. Ini juga menjaga desain kita dari masalah besar

Optimizer **tidak boleh** mengatur execution microstructure secara langsung.

QUBO menentukan:

$$
\boxed{
WHAT
}
$$

sedangkan execution engine menentukan:

$$
\boxed{
HOW
}
$$

Contoh:

**Optimizer:**

> Long BTC, risk \$1, position level 2.

**Execution engine:**

> Letakkan limit order pada bid/ask tertentu, tunggu fill, pasang SL/TP, monitor order book.

Pemisahan ini akan sangat penting ketika kita nanti benar-benar menghubungkannya ke Binance dan kemudian broker saham.

---

# N.81. Dynamic re-optimization

Misalkan order belum filled.

Pada:

$$
t_0:
$$

kita memiliki:

$$
Q_{t_0}.
$$

Satu jam kemudian:

$$
t_1:
$$

market berubah:

$$
Q_{t_1}\neq Q_{t_0}.
$$

Maka sistem menghitung ulang:

$$
x_{t_1}^\star.
$$

Jika trade lama tidak lagi optimal, order dapat:

$$
cancel.
$$

Kemudian:

$$
replace.
$$

Ini persis menjawab rancangan awalmu mengenai:

> setiap periode mengevaluasi apakah pending order masih layak dipertahankan.

---

# N.82. Untuk posisi yang sudah filled

Kita harus membedakan:

$$
Pending\ Order
$$

dengan:

$$
Open\ Position.
$$

Untuk pending:

$$
Q_t
$$

dapat digunakan langsung untuk memutuskan:

$$
keep/cancel/replace.
$$

Untuk open position, kita tidak langsung melakukan liquidation hanya karena:

$$
x_t^\star
$$

berubah.

Kita membutuhkan **Position Management Layer**.

Itu akan menjadi bagian dari tahap berikutnya.

---

# N.83. Mengapa?

Misalnya:

$$
t_0:
$$

model berkata:

$$
BUY.
$$

Trade filled.

Kemudian:

$$
t_1:
$$

model berubah menjadi:

$$
HOLD.
$$

Tidak berarti:

$$
SELL
$$

secara otomatis.

Kita harus mempertimbangkan:

- unrealized PnL,
- time-in-trade,
- distance to SL,
- distance to TP,
- updated expected return,
- updated volatility,
- updated factor regime,
- opportunity cost.

Jadi keputusan:

$$
ENTER
$$

dan:

$$
MANAGE
$$

adalah dua masalah optimasi yang berbeda.

---

# N.84. Ini sangat cocok dengan desain awal kita

Kita sekarang mempunyai:

$$
\boxed{
Optimization\ Problem\ A:
Entry\ Selection
}
$$

dan nantinya:

$$
\boxed{
Optimization\ Problem\ B:
Position\ Management.
}
$$

Problem B akan menjawab:

> Apakah posisi tetap dipertahankan?

> Apakah SL dinaikkan ke BEP?

> Apakah TP diperpanjang?

> Apakah sebagian posisi ditutup?

---

# N.85. Bahkan itu bisa menjadi QUBO kedua

Misalnya sebuah posisi memiliki:

$$
3
$$

aksi:

$$
a_1=\text{KEEP},
$$

$$
a_2=\text{MOVE SL},
$$

$$
a_3=\text{PARTIAL EXIT}.
$$

Maka kita dapat membangun:

$$
x_{i,a}\in\{0,1\}
$$

dan mengoptimasi expected future utility.

Jadi arsitektur akhirnya bukan hanya satu QUBO.

Kita dapat mempunyai:

$$
\boxed{
QUBO_{entry}
}
$$

dan:

$$
\boxed{
QUBO_{management}.
}
$$

Ini akan sangat menarik secara penelitian.

---

# N.86. Posisi kita sekarang

Setelah Tahap N:

$$
\boxed{
Market
\rightarrow
Factor
\rightarrow
Forecast
\rightarrow
Risk
\rightarrow
Position\ Sizing
\rightarrow
QUBO
\rightarrow
Ising
\rightarrow
QAOA
}
$$

sudah tersambung secara matematis.

Dan yang paling penting, setiap layer memiliki fungsi yang jelas:

| Layer | Pertanyaan |
|---|---|
| Data | Apa yang sedang terjadi? |
| Factor | Faktor apa yang menggerakkan pasar? |
| Forecast | Apa yang mungkin terjadi berikutnya? |
| Risk | Seberapa tidak pasti? |
| Position sizing | Berapa besar posisi yang aman? |
| QUBO | Kombinasi trade mana yang optimal? |
| Ising | Bagaimana merepresentasikan optimasi secara quantum? |
| QAOA | Bagaimana mencari state energi rendah? |
| Execution | Bagaimana mengeksekusi keputusan? |
| Management | Apakah posisi perlu dipertahankan/diubah? |

---

## Persamaan inti Tahap N

Kalau seluruh Tahap N harus dipadatkan menjadi beberapa persamaan utama, saya akan mempertahankan enam ini:

### 1. Position sizing

$$
\boxed{
q_{i,k}
=
\frac{\rho_kR_{\max}}{d_i}
}
$$

### 2. Net expected return

$$
\boxed{
\tilde\mu_i
=
\hat\mu_i-C_i
}
$$

### 3. Portfolio risk

$$
\boxed{
\sigma_p^2
=
w^T\Sigma w
}
$$

### 4. Risk budget

$$
\boxed{
\sum_iq_id_i\leq R_{\max}
}
$$

### 5. Dynamic QUBO

$$
\boxed{
Q_t=
Q(\hat\mu_t,\Sigma_t,P_t,SL_t,C_t,R_t)
}
$$

### 6. Optimization

$$
\boxed{
x_t^\star
=
\arg\min_{x\in\{0,1\}^M}
x^TQ_tx
}
$$

Kemudian:

$$
\boxed{
x_i=\frac{1-Z_i}{2}
}
$$

memberikan:

$$
\boxed{
H_C
=
\sum_i h_iZ_i+
\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

---

### Satu konsekuensi penting dari Tahap N

Kita sekarang dapat melihat dengan sangat jelas **di mana matematika quantum benar-benar masuk ke quantitative trading kita**.

Bukan pada forecasting:

$$
P_{t+1}=f(P_t),
$$

dan bukan pada prediksi BTC.

Quantum masuk setelah seluruh informasi pasar telah direduksi menjadi:

$$
\boxed{
\hat\mu_t,\quad
\Sigma_t,\quad
SL_t,\quad
C_t,\quad
R_t.
}
$$

Informasi tersebut membentuk **QUBO**, dan QUBO membentuk **Ising Hamiltonian**. Dengan demikian, apabila nanti kita membandingkan **Exact Solver vs Classical Optimizer vs VQE/QAOA**, ketiganya benar-benar menerima **problem matematis yang identik**. Ini sangat penting agar penelitian kita tidak berubah menjadi sekadar "menggunakan quantum karena quantum", tetapi menjadi eksperimen yang dapat dipertanggungjawabkan.

Tahap berikutnya secara logis adalah **Tahap O — Position Management & Dynamic Rebalancing**: kita akan memformalkan bagian yang sejak awal paling kamu inginkan, yaitu **apa yang dilakukan setelah order pending/filled**, termasuk floating loss, floating profit, break-even stop, trailing SL, dynamic TP, partial exit, time stop, dan kapan sistem harus membangun ulang QUBO. Di sana kita bisa mulai membentuk **QUBO kedua untuk pengelolaan posisi yang sudah terbuka**.

## Prompt:
8/17/2026, 10:00:00 PM

lanjut Tahap O

## Response:
8/17/2026, 10:00:01 PM

> **Remembering**
>
>
> **Clarified Tahap N/O design, dynamic QUBO, and position sizing memory**
>
> 
>
> Worked for 4s

# Tahap O - Position Management & Dynamic Rebalancing

Tahap O adalah kelanjutan yang sangat penting dari Tahap N.

Pada Tahap N kita telah menyelesaikan pertanyaan:

> **"Trade mana yang sebaiknya dibuka sekarang?"**

Sekarang pertanyaannya berubah menjadi:

> **"Setelah trade dibuka, apakah trade tersebut masih layak dipertahankan, dan jika iya, bagaimana SL, TP, serta ukuran posisi harus dikelola?"**

Ini bukan lagi masalah *entry optimization*. Kita sekarang membangun **dynamic position management**.

Arsitektur kita menjadi:

$$
\boxed{
\text{Entry Optimization}
\rightarrow
\text{Execution}
\rightarrow
\text{Position Management}
\rightarrow
\text{Exit}
}
$$

dan Position Management sendiri akan terus berjalan sepanjang umur posisi.

---

# O.1. Mengapa position management harus dipisahkan dari entry?

Misalkan pada waktu:

$$
t_0
$$

model menghasilkan:

$$
x_{t_0}^{\star}=\text{LONG BTC}.
$$

Order kemudian filled.

Pada:

$$
t_1=t_0+1\text{ jam},
$$

kondisi pasar berubah.

Misalnya:

$$
\hat{\mu}_{BTC,t_1}<\hat{\mu}_{BTC,t_0}.
$$

Tetapi BTC masih berada:

$$
+1.8R
$$

dari entry.

Apakah kita langsung menjual?

**Tidak.**

Karena informasi yang relevan sekarang bukan hanya:

$$
\hat{\mu}_{t_1},
$$

tetapi juga:

$$
\text{unrealized PnL},
$$

$$
\text{distance to SL},
$$

$$
\text{distance to TP},
$$

$$
\text{time in trade},
$$

$$
\text{updated volatility},
$$

$$
\text{updated factor regime}.
$$

Jadi kita membutuhkan state tambahan.

---

# O.2. State posisi

Untuk setiap posisi $i$, kita definisikan:

$$
\boxed{
s_i(t)
=
\left[
P_i^{entry},
P_i(t),
SL_i(t),
TP_i(t),
q_i(t),
\tau_i(t),
PnL_i(t),
\sigma_i(t),
\hat{\mu}_i(t),
R_i(t)
\right]
}
$$

dengan:

- $P_i^{entry}$: harga entry,
- $P_i(t)$: harga sekarang,
- $SL_i(t)$: stop-loss sekarang,
- $TP_i(t)$: take-profit sekarang,
- $q_i(t)$: quantity,
- $\tau_i$: umur posisi,
- $PnL_i$: unrealized PnL,
- $\sigma_i$: volatility terkini,
- $\hat{\mu}_i$: expected return terkini,
- $R_i$: remaining risk.

Maka sistem tidak lagi hanya melihat:

$$
\text{market state}.
$$

Ia melihat:

$$
\boxed{
\text{market state}
+
\text{position state}.
}
$$

---

# O.3. Normalisasi PnL menggunakan $R$

Karena sejak Tahap N kita menggunakan risk budget, ukuran yang sangat berguna adalah:

$$
\boxed{
R_i(t)
=
\frac{PnL_i(t)}
{R_i^{initial}}
}
$$

Misalnya initial risk:

$$
R_i^{initial}=\$1.
$$

Jika floating loss:

$$
PnL=-\$0.5,
$$

maka:

$$
R_i=-0.5R.
$$

Jika profit:

$$
PnL=+\$2,
$$

maka:

$$
R_i=+2R.
$$

Ini jauh lebih konsisten daripada menggunakan dollar PnL secara langsung.

---

# O.4. Mengapa $R$-multiple sangat penting?

Misalkan:

Trade A:

$$
+\$10
$$

dengan initial risk:

$$
\$20.
$$

Maka:

$$
R_A=0.5R.
$$

Trade B:

$$
+\$10
$$

dengan initial risk:

$$
\$2.
$$

Maka:

$$
R_B=5R.
$$

Secara nominal sama:

$$
\$10,
$$

tetapi secara risk-adjusted sangat berbeda.

Karena sistem kita memang dibangun berdasarkan:

$$
\boxed{\$1\text{ modeled risk}}
$$

maka seluruh position management sebaiknya menggunakan $R$.

---

# O.5. Tiga keadaan posisi

Kita dapat membagi posisi menjadi:

### State I - Floating Loss

$$
R_i<0
$$

### State II - Floating Profit

$$
R_i>0
$$

### State III - Near Exit

Misalnya:

$$
P_i\rightarrow TP_i
$$

atau:

$$
P_i\rightarrow SL_i.
$$

Tetapi kita tidak boleh menggunakan PnL saja.

Kita juga perlu mengetahui apakah **thesis** trade masih valid.

---

# O.6. Thesis score

Definisikan:

$$
\boxed{
\Theta_i(t)
}
$$

sebagai ukuran seberapa kuat alasan awal trade masih berlaku.

Misalnya:

$$
\Theta_i
=
f(
\hat{\mu}_i,
factor_i,
momentum_i,
volatility_i,
liquidity_i,
correlation_i
).
$$

Secara sederhana:

$$
\Theta_i>0
$$

berarti thesis masih mendukung posisi.

Sedangkan:

$$
\Theta_i<0
$$

berarti thesis mulai invalid.

---

# O.7. Kita tidak ingin threshold arbitrer

Daripada:

> Kalau profit 2%, geser SL.

lebih matematis jika menggunakan:

$$
R,
$$

volatility,

dan expected future return.

Jadi keputusan tidak bergantung pada:

$$
2\%.
$$

Melainkan pada keadaan relatif terhadap:

$$
\sigma_t
$$

dan:

$$
R_i.
$$

---

# O.8. Stop-loss awal

Saat entry:

$$
P_0.
$$

Untuk long:

$$
SL_0=P_0-d.
$$

Risk:

$$
R_0=qd.
$$

Kita telah menetapkan:

$$
R_0\leq \$1.
$$

Stop ini disebut:

$$
\boxed{
SL_{initial}.
}
$$

---

# O.9. Jangan langsung mempersempit SL ketika floating loss

Ini prinsip yang penting.

Misalnya:

$$
R=-0.5R.
$$

Kemudian model memperbarui prediksi.

Jika thesis masih valid:

$$
\Theta>0,
$$

maka kita tidak boleh otomatis melakukan:

$$
SL\rightarrow P_{entry}.
$$

Karena itu dapat mengubah trade yang secara statistik masih valid menjadi stop-out hanya karena noise.

---

# O.10. Floating loss decision

Kita definisikan future expected utility:

$$
U_i(t)
=
E[\Pi_i^{future}\mid\mathcal F_t].
$$

Jika:

$$
U_i(t)>0
$$

dan:

$$
\Theta_i(t)>0,
$$

maka posisi masih memiliki alasan untuk dipertahankan.

Sebaliknya jika:

$$
U_i(t)<0,
$$

thesis tidak lagi mendukung posisi.

---

# O.11. Keputusan exit yang lebih matematis

Kita dapat mendefinisikan:

$$
\boxed{
V_i^{hold}(t)
=
E[\Pi_i^{future}\mid\mathcal F_t]
-
C_i^{future}.
}
$$

Jika:

$$
V_i^{hold}>0,
$$

hold memiliki expected value positif.

Jika:

$$
V_i^{hold}<0,
$$

exit menjadi lebih rasional.

---

# O.12. Opportunity cost

Tetapi ada satu hal lagi.

Modal yang digunakan oleh posisi lama tidak dapat digunakan untuk trade baru.

Misalkan ada candidate trade baru $j$ dengan:

$$
V_j^{entry}.
$$

Maka kita dapat membandingkan:

$$
V_i^{hold}
$$

dengan:

$$
V_j^{entry}.
$$

Definisikan:

$$
\boxed{
OC_{i\rightarrow j}
=
V_j^{entry}-V_i^{hold}.
}
$$

Jika:

$$
OC>0,
$$

trade baru memiliki expected value lebih tinggi.

Ini menghasilkan konsep:

$$
\boxed{
dynamic\ capital\ reallocation.
}
$$

---

# O.13. Jadi floating loss tidak otomatis berarti exit

Kita memperoleh aturan konseptual:

$$
\boxed{
\text{Loss}
\not\Rightarrow
\text{Exit}.
}
$$

Yang menentukan adalah:

$$
\boxed{
\text{Future Expected Value}
}
$$

dan:

$$
\boxed{
\text{Thesis Validity}.
}
$$

---

# O.14. Sekarang floating profit

Misalkan:

$$
R_i=+1.5R.
$$

Pertanyaan kita:

> Apakah kita mengambil profit sekarang?

atau:

> Apakah kita membiarkan profit berkembang?

Secara matematis kita membandingkan:

$$
V_{hold}
$$

dengan:

$$
V_{exit}.
$$

---

# O.15. Immediate exit value

Jika kita keluar sekarang:

$$
\boxed{
V_{exit}(t)=PnL_i(t)-C_{exit}.
}
$$

Sedangkan jika hold:

$$
\boxed{
V_{hold}(t)
=
E[PnL_i(T)\mid\mathcal F_t]
-
C_{future}.
}
$$

Maka:

$$
\boxed{
\Delta V
=
V_{hold}-V_{exit}.
}
$$

---

# O.16. Jika $\Delta V>0$

Lebih baik mempertahankan posisi.

Jika:

$$
\Delta V<0,
$$

lebih baik exit.

Ini memberikan dasar matematis untuk:

> "floating profit tinggi, apakah TP harus dinaikkan?"

---

# O.17. TP bukan angka statis

Awalnya:

$$
TP_0.
$$

Tetapi setelah market berubah:

$$
TP_t
$$

dapat menjadi:

$$
TP_t>TP_0.
$$

Namun kenaikan TP hanya dilakukan jika:

$$
E[P_{future}]
$$

masih mendukung target tersebut.

---

# O.18. Kita membutuhkan target distribution

Daripada hanya memprediksi:

$$
\hat\mu_t,
$$

lebih ideal kita memiliki:

$$
\boxed{
p(\Delta P_{t\rightarrow T}\mid\mathcal F_t).
}
$$

Dari distribusi tersebut kita dapat menghitung:

$$
P(P_T>TP).
$$

Dan:

$$
P(P_T<SL).
$$

Ini jauh lebih berguna untuk position management.

---

# O.19. Expected value dengan TP dan SL

Misalkan:

$$
p_T=P(TP\ hit),
$$

$$
p_S=P(SL\ hit),
$$

dan:

$$
p_H=1-p_T-p_S
$$

untuk kondisi lainnya.

Expected PnL:

$$
\boxed{
EV
=
p_TG
-
p_SL
+
p_HE_H.
}
$$

Jika:

$$
EV>0,
$$

target tersebut masih layak.

---

# O.20. Dynamic TP

Misalkan kandidat TP:

$$
TP^{(1)},
TP^{(2)},
TP^{(3)}.
$$

Kita dapat menghitung:

$$
EV^{(1)},
EV^{(2)},
EV^{(3)}.
$$

Kemudian:

$$
\boxed{
TP^\star
=
\arg\max_{TP^{(k)}}EV^{(k)}.
}
$$

Jadi TP tidak lagi:

> "naik 2% setiap kali profit."

Tetapi:

> **pilih target yang memiliki expected utility tertinggi berdasarkan state pasar sekarang.**

---

# O.21. Dynamic Stop-Loss

Sekarang masalah yang lebih menarik.

Kita ingin memilih:

$$
SL_t.
$$

Kandidatnya dapat berupa:

$$
SL^{(1)}=SL_{initial},
$$

$$
SL^{(2)}=BEP,
$$

$$
SL^{(3)}=trailing\ stop,
$$

$$
SL^{(4)}=volatility\ stop.
$$

---

# O.22. Break-even stop

Untuk long:

$$
SL_t=P_{entry}.
$$

Namun sebenarnya BEP harus memperhitungkan biaya.

Jika:

$$
C_{entry}+C_{exit}
$$

tidak nol, maka break-even sebenarnya:

$$
\boxed{
P_{BEP}
=
P_{entry}
+
\frac{C_{total}}{q}.
}
$$

Jadi:

$$
SL=P_{entry}
$$

belum tentu benar-benar break-even.

---

# O.23. Trailing stop berbasis volatility

Misalkan:

$$
ATR_t
$$

atau volatility scale:

$$
\sigma_t.
$$

Untuk long:

$$
\boxed{
SL_t
=
P_t-k\sigma_tP_t
}
$$

dengan:

$$
k>0.
$$

Tetapi SL hanya boleh bergerak satu arah:

$$
\boxed{
SL_t\geq SL_{t-1}
}
$$

untuk long.

Untuk short:

$$
SL_t\leq SL_{t-1}.
$$

---

# O.24. Mengapa tidak hanya memakai trailing stop?

Karena trailing stop tidak mengetahui thesis.

Misalnya volatility meningkat.

Trailing stop dapat menjadi:

$$
SL_t=P_t-k\sigma_tP_t.
$$

Jika $\sigma_t$ meningkat tajam, stop justru dapat bergerak **lebih jauh**.

Maka position management harus mempertimbangkan:

$$
\boxed{
Price
+
Volatility
+
Thesis
+
Expected\ Value.
}
$$

---

# O.25. Kandidat action

Sekarang kita formalasikan decision space.

Untuk posisi yang sedang terbuka, kita memiliki:

$$
a_i\in\mathcal A.
$$

Misalnya:

$$
\mathcal A=
\{
KEEP,
EXIT,
BEP,
TRAIL,
TP\_UP,
PARTIAL\_EXIT
\}.
$$

---

# O.26. Binary encoding

Definisikan:

$$
z_{i,a}\in\{0,1\}.
$$

Dengan constraint:

$$
\boxed{
\sum_{a\in\mathcal A}
z_{i,a}=1.
}
$$

Artinya satu action dipilih.

---

# O.27. Utility setiap action

Untuk action $a$:

$$
U_{i,a}
=
E[\Pi_i\mid a,\mathcal F_t]
-
C_{i,a}
-
Risk_{i,a}.
$$

Kemudian kita ingin:

$$
\boxed{
a_i^\star
=
\arg\max_aU_{i,a}.
}
$$

---

# O.28. Ini dapat menjadi QUBO kedua

Ubah menjadi minimization:

$$
\boxed{
E_i(z)
=
-\sum_aU_{i,a}z_{i,a}
+
P
\left(
\sum_az_{i,a}-1
\right)^2.
}
$$

Dengan:

$$
z_{i,a}\in\{0,1\}.
$$

Ini adalah QUBO.

---

# O.29. Tetapi kita dapat membuatnya jauh lebih kuat

Jika kita memiliki beberapa posisi:

$$
i=1,\ldots,N_p,
$$

maka setiap action memiliki interaksi.

Misalnya:

> exit BTC memungkinkan capital dialihkan ke ETH.

Maka:

$$
U_{i,a}
$$

tidak lagi independen.

Kita membutuhkan:

$$
U(z)
=
\sum_{i,a}u_{i,a}z_{i,a}
+
\sum_{i,j,a,b}
J_{ia,jb}z_{i,a}z_{j,b}.
$$

Dan kembali kita mendapatkan QUBO.

---

# O.30. Position management QUBO

Secara umum:

$$
\boxed{
E_{manage}(z)
=
-z^TUz
+
P(z)
}
$$

atau sesuai konvensi:

$$
\boxed{
E_{manage}(z)
=
-\sum_{i,a}U_{i,a}z_{i,a}
+
\sum_{i,j,a,b}
C_{ia,jb}
z_{i,a}z_{j,b}
+
P(z).
}
$$

---

# O.31. Apa yang dimaksud interaction antar-action?

Misalnya dua posisi:

$$
BTC
$$

dan:

$$
ETH.
$$

Jika BTC ditutup:

$$
EXIT_{BTC},
$$

capital tersedia.

Jika ETH dipertahankan:

$$
KEEP_{ETH},
$$

tidak ada masalah.

Tetapi jika:

$$
KEEP_{BTC}
$$

dan:

$$
ENTER_{SOL},
$$

total risk mungkin melebihi:

$$
R_{portfolio}.
$$

Maka interaction penalty muncul.

---

# O.32. Dynamic portfolio risk

Pada waktu $t$:

$$
w_t
$$

adalah posisi aktual.

Jika kita mempertimbangkan action $a$, kita memperoleh:

$$
w_t^{(a)}.
$$

Risk:

$$
\boxed{
\sigma_p^2(a)
=
w_t^{(a)T}
\Sigma_t
w_t^{(a)}.
}
$$

Maka action yang meningkatkan risk terlalu besar dapat dihukum.

---

# O.33. Remaining risk

Ini sangat penting untuk sistem kita.

Jika:

$$
P_t>P_{entry}
$$

untuk long, dan SL telah dinaikkan:

$$
SL_t>P_{entry},
$$

maka posisi sudah memiliki:

$$
\boxed{
locked\ profit.
}
$$

Define:

$$
L_i(t)
=
q_i(SL_i(t)-P_{entry}).
$$

Untuk long.

Jika:

$$
L_i>0,
$$

minimum realized profit setelah SL tersentuh sudah positif, mengabaikan gap/slippage.

---

# O.34. Locked profit

Dalam $R$-multiple:

$$
\boxed{
R_{locked}
=
\frac{L_i}{R_{initial}}.
}
$$

Misalnya:

$$
R_{locked}=0.8R.
$$

Artinya meskipun trade berbalik dan menyentuh SL, secara model kita masih mempertahankan:

$$
+0.8R.
$$

---

# O.35. Ini mengubah objective

Sebelum profit:

$$
R_{locked}\leq0.
$$

Setelah BEP:

$$
R_{locked}\approx0.
$$

Setelah trailing:

$$
R_{locked}>0.
$$

Maka position management harus memaksimalkan:

$$
\boxed{
Expected\ additional\ profit
}
$$

tanpa mengorbankan terlalu banyak:

$$
\boxed{
locked\ profit.
}
$$

---

# O.36. Objective baru

Definisikan:

$$
G_i(a)
=
E[\text{future PnL}\mid a].
$$

dan:

$$
L_i(a)
=
\text{locked profit under }a.
$$

Kita dapat membuat:

$$
\boxed{
U_i(a)
=
G_i(a)
+
\eta L_i(a)
-
\lambda Risk_i(a).
}
$$

Parameter:

$$
\eta
$$

mengontrol seberapa penting capital protection.

---

# O.37. Tetapi kita harus menghindari "profit fixation"

Jika:

$$
\eta
$$

terlalu besar, sistem akan terlalu cepat:

$$
EXIT.
$$

Jika:

$$
\eta
$$

terlalu kecil, sistem akan membiarkan profit menguap.

Jadi:

$$
\eta
$$

adalah parameter yang harus diuji melalui walk-forward validation.

---

# O.38. Dynamic TP dan SL sebagai joint optimization

Jangan memilih:

$$
TP
$$

dan:

$$
SL
$$

secara terpisah.

Karena keduanya saling berhubungan.

Kita definisikan action:

$$
a=(SL_k,TP_l).
$$

Kemudian:

$$
a\in\mathcal A.
$$

Misalnya:

$$
\mathcal A=
\{
(SL_1,TP_1),
(SL_1,TP_2),
(SL_2,TP_2),
(SL_3,TP_3),
\ldots
\}.
$$

---

# O.39. Expected utility

Untuk setiap kombinasi:

$$
(SL_k,TP_l),
$$

hitung:

$$
\boxed{
U_{kl}
=
EV(SL_k,TP_l)
-
Cost_{kl}
-
Risk_{kl}.
}
$$

Kemudian:

$$
\boxed{
(SL^\star,TP^\star)
=
\arg\max_{k,l}U_{kl}.
}
$$

---

# O.40. Ini menjawab pertanyaan awalmu

Kamu sebelumnya membayangkan:

> jika floating profit tinggi, mungkin TP dinaikkan lagi.

Jawabannya sekarang menjadi:

**Ya, tetapi bukan karena profit sudah tinggi.**

TP dinaikkan jika:

$$
\boxed{
U(TP_{new},SL_{new})
>
U(TP_{old},SL_{old}).
}
$$

Jadi keputusan tersebut berasal dari **expected future utility**, bukan dari rule arbitrer.

---

# O.41. Time stop

Ada kondisi lain:

> Trade tidak loss, tetapi juga tidak bergerak.

Misalnya:

$$
R\approx0
$$

selama:

$$
\tau=8\text{ jam}.
$$

Capital menjadi terkunci.

Kita definisikan:

$$
\boxed{
U_{time}
=
E[\Pi_{future}]
-
\lambda_\tau\tau.
}
$$

Jika:

$$
U_{time}<0,
$$

exit dapat menjadi optimal.

---

# O.42. Opportunity cost kembali masuk

Semakin lama posisi stagnan:

$$
\tau\uparrow,
$$

semakin besar opportunity cost.

Jadi:

$$
\boxed{
Time\ in\ trade
}
$$

adalah variabel matematis, bukan sekadar informasi tambahan.

---

# O.43. Regime change

Ini bahkan lebih penting.

Misalkan ketika entry:

$$
Regime_t=Bull.
$$

Kemudian:

$$
Regime_{t+1}=Neutral/Bear.
$$

Expected return:

$$
\hat\mu_t
$$

dapat berubah drastis.

Maka:

$$
U_{hold}
$$

harus dihitung ulang.

---

# O.44. Regime-conditioned management

Kita dapat menulis:

$$
\boxed{
U_i(a\mid z_t)
}
$$

dengan:

$$
z_t
$$

adalah market regime.

Contoh:

$$
z_t\in
\{
Trend,
MeanReversion,
HighVol,
LowVol,
RiskOn,
RiskOff
\}.
$$

---

# O.45. Gold dan DXY juga kembali masuk

Karena sebelumnya kita ingin sistem bekerja tidak hanya pada crypto tetapi juga saham internasional, factor layer kita dapat memberi:

$$
F_t=
[
BTC,
ETH,
Gold,
DXY,
SPX,
VIX,
\ldots].
$$

Jika misalnya:

$$
DXY\uparrow
$$

dan:

$$
Gold\downarrow,
$$

model dapat memperbarui:

$$
\hat\mu_i,
$$

$$
\Sigma_i,
$$

dan akhirnya:

$$
U_i(a).
$$

Dengan demikian perubahan faktor global dapat memicu:

$$
\boxed{
position\ management.
}
$$

---

# O.46. Dynamic rebalancing

Sekarang kita dapat mendefinisikan proses periodik.

Pada waktu:

$$
t.
$$

Kita memiliki:

$$
\mathcal P_t
=
\text{all open positions}.
$$

Update market:

$$
\mathcal F_t.
$$

Kemudian:

$$
\hat\mu_t,\Sigma_t
$$

dihitung ulang.

---

# O.47. Langkah pertama: valuasi posisi

Untuk setiap posisi:

$$
i:
$$

hitung:

$$
PnL_i,
$$

$$
R_i,
$$

$$
R_{locked,i},
$$

$$
\tau_i,
$$

$$
\Theta_i,
$$

$$
U_{hold,i}.
$$

---

# O.48. Langkah kedua: generate candidate actions

Untuk setiap posisi:

$$
\mathcal A_i=
\{
KEEP,
EXIT,
BEP,
TRAIL,
TP_1,
TP_2,
PARTIAL
\}.
$$

---

# O.49. Langkah ketiga: bangun management QUBO

$$
\boxed{
Q_t^{manage}
=
Q(
PnL_t,
\hat\mu_t,
\Sigma_t,
SL_t,
TP_t,
\tau_t,
Liquidity_t,
Factor_t
).
}
$$

---

# O.50. Langkah keempat: solve

Kita dapat menggunakan:

$$
\boxed{
x_t^{manage}
=
\arg\min_x
x^TQ_t^{manage}x.
}
$$

Solver dapat berupa:

- exhaustive search untuk problem kecil,
- classical QUBO solver,
- simulated annealing,
- tabu search,
- MILP,
- QAOA.

Dengan demikian quantum bukan satu-satunya solver.

---

# O.51. Langkah kelima: execution

Jika hasilnya:

$$
KEEP:
$$

tidak melakukan apa-apa.

Jika:

$$
BEP:
$$

modify SL.

Jika:

$$
TP\_UP:
$$

modify TP.

Jika:

$$
PARTIAL:
$$

reduce quantity.

Jika:

$$
EXIT:
$$

close position.

---

# O.52. Setelah execution

Kita kembali ke:

$$
Market\ Monitoring.
$$

Sehingga terdapat loop:

$$
\boxed{
Observe
\rightarrow
Estimate
\rightarrow
Optimize
\rightarrow
Execute
\rightarrow
Monitor
\rightarrow
Re-optimize.
}
$$

Ini adalah inti sistem kita.

---

# O.53. Full mathematical loop

Secara matematis:

$$
\mathcal F_t
\rightarrow
\theta_t
\rightarrow
(\hat\mu_t,\Sigma_t)
$$

kemudian:

$$
(\hat\mu_t,\Sigma_t)
\rightarrow
Q_t^{entry}
$$

kemudian:

$$
Q_t^{entry}
\rightarrow
x_t^\star
$$

kemudian execution menghasilkan:

$$
s_t.
$$

Kemudian:

$$
(s_t,\mathcal F_t)
\rightarrow
Q_t^{manage}
$$

dan:

$$
Q_t^{manage}
\rightarrow
a_t^\star.
$$

---

# O.54. Kita sekarang memiliki dua Hamiltonian

Entry:

$$
\boxed{
H_C^{entry}(t)
}
$$

Management:

$$
\boxed{
H_C^{manage}(t)
}
$$

Keduanya berasal dari market state yang sama tetapi memiliki tujuan berbeda.

---

# O.55. Ini memungkinkan arsitektur yang jauh lebih menarik

Secara keseluruhan:

$$
\boxed{
\begin{array}{c}
Market\ Data\\
\downarrow\\
Feature/Factor\ Model\\
\downarrow\\
Forecast\\
\downarrow\\
Risk\ Model\\
\downarrow\\
\boxed{Entry\ QUBO}\\
\downarrow\\
QAOA/Classical\\
\downarrow\\
Order\ Placement\\
\downarrow\\
\boxed{Position\ Management\ QUBO}\\
\downarrow\\
QAOA/Classical\\
\downarrow\\
SL/TP/Exit\\
\downarrow\\
Market
\end{array}
}
$$

---

# O.56. Namun ada satu hal yang harus kita cegah: excessive re-optimization

Jika kita menjalankan optimizer setiap:

$$
1\text{ detik},
$$

sistem mungkin:

$$
KEEP
\rightarrow
EXIT
\rightarrow
KEEP
\rightarrow
EXIT
$$

hanya karena noise.

Ini disebut:

$$
\boxed{
decision\ churning.
}
$$

---

# O.57. Hysteresis

Kita dapat membuat threshold.

Misalnya keputusan baru hanya dilakukan jika:

$$
\boxed{
U_{new}-U_{current}
>
\delta.
}
$$

Dengan:

$$
\delta>0.
$$

Jadi optimizer tidak mengubah posisi hanya karena improvement sangat kecil.

---

# O.58. Transaction cost secara alami menghasilkan hysteresis

Sebenarnya kita dapat membuat:

$$
U_{switch}
=
U_{new}-U_{current}-C_{switch}.
$$

Switch hanya jika:

$$
\boxed{
U_{switch}>0.
}
$$

Jadi biaya transaksi sendiri membantu mencegah overtrading.

---

# O.59. Rebalancing bukan berarti selalu mengubah posisi

Ini penting.

Dynamic rebalancing berarti:

$$
\boxed{
\text{re-evaluate}
}
$$

bukan:

$$
\boxed{
\text{always trade}.
}
$$

Jika posisi saat ini masih optimal:

$$
a^\star=KEEP.
$$

Maka:

$$
\text{No action}.
$$

---

# O.60. Position management sebagai optimal stopping

Ada perspektif matematika yang lebih dalam.

Pertanyaan:

> Kapan sebaiknya saya keluar?

sebenarnya adalah masalah:

$$
\boxed{
Optimal\ Stopping.
}
$$

Kita memiliki state:

$$
X_t
=
(P_t,\hat\mu_t,\sigma_t,\Theta_t,\tau_t,\ldots).
$$

Kemudian kita mencari stopping time:

$$
\boxed{
\tau^\star
=
\inf\{t:V(X_t)=G(X_t)\}.
}
$$

dengan:

- $V(X_t)$: value of continuing,
- $G(X_t)$: value of exiting.

---

# O.61. Ini sangat penting secara teoritis

Jadi position management kita sebenarnya dapat dipandang sebagai:

$$
\boxed{
Dynamic\ Programming
+
Optimal\ Stopping
+
Combinatorial\ Optimization.
}
$$

Dan QUBO adalah representasi diskrit dari keputusan kombinatorial tersebut.

---

# O.62. Bahkan kita bisa melihatnya sebagai MDP

State:

$$
s_t.
$$

Action:

$$
a_t.
$$

Reward:

$$
r_t.
$$

Transition:

$$
P(s_{t+1}|s_t,a_t).
$$

Maka kita memiliki:

$$
\boxed{
Markov\ Decision\ Process.
}
$$

Namun kita **tidak harus menggunakan reinforcement learning**.

Kita dapat menggunakan probabilistic forecast + optimization.

Ini lebih mudah dijelaskan dan divalidasi untuk penelitian kuantitatif.

---

# O.63. Hubungan dengan QAOA

QAOA tidak menggantikan keseluruhan MDP.

QAOA menyelesaikan subproblem:

$$
\boxed{
\text{Which action configuration is optimal at }t?
}
$$

Jadi:

$$
MDP
\rightarrow
Optimization\ Subproblem
\rightarrow
QUBO
\rightarrow
QAOA.
$$

Ini framing yang jauh lebih tepat.

---

# O.64. Contoh konkret

Misalkan:

$$
R_{initial}=\$1.
$$

Posisi BTC:

$$
R=+2.4R.
$$

Thesis score:

$$
\Theta=0.72.
$$

Expected future return:

$$
\hat\mu>0.
$$

Current SL:

$$
+0.8R
$$

locked.

Candidate actions:

| Action | Locked profit | Expected future profit | Risk |
|---|---:|---:|---:|
| EXIT | $2.4R$ | $0$ | 0 |
| KEEP | $0.8R$ | $1.1R$ | tinggi |
| TRAIL | $1.2R$ | $0.8R$ | sedang |
| TP-UP | $0.8R$ | $1.5R$ | tinggi |

Model menghitung:

$$
U(a).
$$

Misalnya hasil:

$$
U_{EXIT}=2.35,
$$

$$
U_{KEEP}=1.90,
$$

$$
U_{TRAIL}=2.00,
$$

$$
U_{TP-UP}=2.15.
$$

Maka:

$$
\boxed{
EXIT
}
$$

menjadi optimal.

Bukan karena:

> profit sudah 2.4R.

Tetapi karena:

$$
\boxed{
expected\ value\ of\ continuing
<
value\ of\ exiting.
}
$$

---

# O.65. Contoh kedua

Misalkan:

$$
R=+2.4R
$$

tetapi:

$$
\Theta=0.91,
$$

dan expected future return masih tinggi.

Mungkin:

$$
U_{KEEP}=2.8
$$

dan:

$$
U_{EXIT}=2.35.
$$

Maka:

$$
\boxed{
KEEP.
}
$$

Bahkan:

$$
TP
$$

dapat dinaikkan jika:

$$
U(TP_{new})>U(TP_{old}).
$$

---

# O.66. Contoh floating loss

Misalkan:

$$
R=-0.6R.
$$

Tetapi:

$$
\Theta=0.85,
$$

dan:

$$
U_{hold}=0.3.
$$

Sedangkan:

$$
U_{exit}=-0.6.
$$

Maka:

$$
\boxed{
KEEP.
}
$$

Ini menjawab bagian awal desainmu:

> floating loss tidak otomatis ditutup.

---

# O.67. Tetapi jika thesis rusak

Misalnya:

$$
R=-0.6R,
$$

namun:

$$
\Theta=-0.8,
$$

dan:

$$
U_{hold}=-1.2.
$$

Sedangkan:

$$
U_{exit}=-0.6.
$$

Maka:

$$
\boxed{
EXIT.
}
$$

Jadi stop-loss bukan satu-satunya exit mechanism.

---

# O.68. Kita sekarang bisa mendefinisikan empat alasan exit

### 1. Risk exit

$$
P_t\leq SL_t.
$$

### 2. Target exit

$$
P_t\geq TP_t.
$$

### 3. Thesis exit

$$
\Theta_t<\Theta_{min}.
$$

### 4. Opportunity-cost exit

$$
V_{new}>V_{hold}+C_{switch}.
$$

Ini jauh lebih kuat daripada hanya:

$$
TP/SL.
$$

---

# O.69. Tetapi SL/TP tetap menjadi safety layer

Ini penting untuk deployment.

Optimizer tidak boleh menjadi satu-satunya proteksi.

Jika:

$$
QAOA
$$

hang,

atau:

$$
network
$$

putus,

atau:

$$
model
$$

menghasilkan output aneh,

SL yang sudah terpasang tetap harus bekerja.

Jadi:

$$
\boxed{
Hard\ Risk\ Controls
}
$$

harus berada di bawah:

$$
\boxed{
Optimization\ Layer.
}
$$

---

# O.70. Hierarki kontrol

Saya menyarankan arsitektur:

$$
\boxed{
Hard\ Risk\ Layer
}
$$

di paling bawah.

Di atasnya:

$$
\boxed{
Execution\ Layer
}
$$

kemudian:

$$
\boxed{
Position\ Management
}
$$

kemudian:

$$
\boxed{
Entry\ Optimization
}
$$

dan paling atas:

$$
\boxed{
Forecast/Research
}
$$

Sehingga optimizer tidak pernah bisa berkata:

> "Saya yakin sekali, jadi abaikan maximum loss."

Constraint risiko tetap menang.

---

# O.71. Tahap O dalam bentuk algoritma

Secara konseptual:

```text
INITIALIZE position state

WHILE market is open:

    observe market

    update:
        price
        volatility
        factors
        expected return
        covariance
        liquidity

    FOR every open position:

        calculate:
            PnL
            R-multiple
            locked profit
            time-in-trade
            thesis score
            future expected value

        generate candidate actions:
            KEEP
            EXIT
            BEP
            TRAIL
            TP-UP
            PARTIAL EXIT

    construct management QUBO

    solve QUBO

    IF new decision is sufficiently better:
        execute action

    update SL/TP/state

    periodically:
        rebuild entry QUBO
        evaluate new opportunities

END
```

---

# O.72. Arsitektur final setelah Tahap O

Sekarang sistem kita telah berkembang menjadi:

$$
\boxed{
\begin{aligned}
Market\ Data
&\rightarrow
Feature\ Engineering
\\
&\rightarrow
Factor\ Model
\\
&\rightarrow
Forecast
\\
&\rightarrow
Risk\ Model
\\
&\rightarrow
Entry\ QUBO
\\
&\rightarrow
QAOA/Classical
\\
&\rightarrow
Order\ Placement
\\
&\rightarrow
Position\ State
\\
&\rightarrow
Management\ QUBO
\\
&\rightarrow
QAOA/Classical
\\
&\rightarrow
SL/TP/Exit
\\
&\rightarrow
Rebalancing.
\end{aligned}
}
$$

---

# O.73. Dan sekarang ada sesuatu yang sangat menarik

Sebelum Tahap O, kita hanya mempunyai:

$$
\boxed{
\text{Static Portfolio Optimization}.
}
$$

Setelah Tahap O, kita mulai memiliki:

$$
\boxed{
\text{Dynamic Sequential Portfolio Optimization}.
}
$$

Artinya keputusan pada waktu $t$ mempengaruhi state pada:

$$
t+1.
$$

Misalnya:

$$
EXIT_{BTC}
$$

membebaskan capital.

Capital tersebut dapat digunakan untuk:

$$
BUY_{ETH}.
$$

Jadi keputusan kita memiliki **intertemporal effect**.

---

# O.74. Persamaan konseptual terpenting Tahap O

Saya akan merangkum Tahap O dengan satu persamaan:

$$
\boxed{
a_t^\star
=
\arg\max_{a\in\mathcal A}
\left[
E(\Pi_{t:T}\mid s_t,a)
-
C(a)
-
\lambda R(a)
+
\eta L(a)
-
\lambda_\tau\tau
\right].
}
$$

dengan:

$$
s_t
=
\{
P_t,
PnL_t,
SL_t,
TP_t,
\hat\mu_t,
\Sigma_t,
\Theta_t,
\tau_t,
Liquidity_t,
Factor_t
\}.
$$

Kemudian keputusan diskrit tersebut kita transformasikan menjadi:

$$
\boxed{
Q_t^{manage}
}
$$

dan akhirnya:

$$
\boxed{
Q_t^{manage}
\rightarrow
H_C^{manage}
\rightarrow
QAOA.
}
$$

---

# O.75. Posisi kita sekarang

Kita sudah memiliki dua problem optimasi yang berbeda:

$$
\boxed{
\textbf{Problem 1 - Entry}
}
$$

$$
\hat\mu_t,\Sigma_t
\rightarrow
Q_t^{entry}
\rightarrow
\text{trade selection}.
$$

dan:

$$
\boxed{
\textbf{Problem 2 - Management}
}
$$

$$
s_t,\hat\mu_t,\Sigma_t
\rightarrow
Q_t^{manage}
\rightarrow
\text{KEEP/EXIT/SL/TP/PARTIAL}.
$$

Keduanya dapat diuji dengan:

$$
\boxed{
Exact
\quad vs\quad
Classical
\quad vs\quad
QAOA
}
$$

pada problem yang **identik**.

---

## Dan menurut saya, ini adalah titik di mana proyek kita mulai menjadi jauh lebih serius.

Kita tidak lagi sekadar membuat:

> "bot trading yang memakai QAOA."

Kita sedang membangun sebuah **dynamic quantitative decision system**, di mana:

$$
\boxed{
\text{market dynamics}
\rightarrow
\text{statistical estimation}
\rightarrow
\text{risk}
\rightarrow
\text{combinatorial optimization}
\rightarrow
\text{quantum optimization}
\rightarrow
\text{execution}
\rightarrow
\text{optimal stopping}
}
$$

dan setiap keputusan dapat ditulis secara matematis.

Yang juga sangat penting: **QAOA hanyalah solver**, bukan sumber alpha. Alpha berasal dari data, factor model, forecasting, dan risk model. QAOA menjawab pertanyaan kombinatorial: *dari seluruh keputusan diskrit yang feasible, mana yang paling baik menurut objective kita?*

Dengan Tahap O selesai, fondasi matematis untuk **entry + position management** sudah terbentuk. Tahap berikutnya secara alami adalah **Tahap P - Execution & Microstructure Optimization**, yaitu membawa keputusan abstrak seperti *"LONG BTC dengan risk \$1"* menjadi keputusan nyata: **harga limit order, kedalaman order book, probabilitas fill, expected slippage, queue position, cancel/replace, dan kapan sebuah order sebaiknya tidak diletakkan sama sekali**. Di situlah sistem kita mulai benar-benar bersentuhan dengan *short-horizon trading* dan market microstructure.

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

## Prompt:
8/17/2026, 10:02:18 PM

lanjut Tahap Q

## Response:
8/17/2026, 10:02:18 PM

# Tahap Q — Event-Driven Backtesting & Market Simulator

Ya. **Tahap Q adalah titik yang sangat penting**, karena seluruh matematika A–P yang kita bangun sekarang harus ditempatkan ke dalam lingkungan yang bisa menjawab pertanyaan paling fundamental:

> **"Jika sistem ini benar-benar berada di pasar pada waktu $t$, dengan hanya informasi yang tersedia pada saat itu, apa yang sebenarnya akan terjadi?"**

Tanpa ini, model kita mudah menghasilkan backtest yang terlihat luar biasa tetapi sebenarnya menggunakan *look-ahead bias*, mengabaikan spread, menganggap semua limit order pasti filled, atau menghitung stop-loss dengan informasi masa depan.

Jadi Tahap Q bukan sekadar "membuat backtester".

Kita akan membangun:

$$
\boxed{
\text{Event-Driven Market Simulator}
}
$$

yang menjadi **laboratorium virtual** untuk seluruh sistem.

---

# Q.1. Paradigma utama

Backtester sederhana biasanya berpikir seperti:

$$
P_t
\rightarrow
Signal_t
\rightarrow
Return_{t+1}.
$$

Itu terlalu sederhana untuk sistem kita.

Kita ingin:

$$
\boxed{
\mathcal F_t
\rightarrow
State_t
\rightarrow
Optimization_t
\rightarrow
Order_t
\rightarrow
Execution_t
\rightarrow
Position_t
\rightarrow
PnL_t
}
$$

dan kemudian:

$$
\boxed{
State_{t+1}
}
$$

bergantung pada apa yang benar-benar terjadi pada $t$.

---

# Q.2. Event-driven, bukan candle-driven

Ini perbedaan fundamental.

Misalnya kita mempunyai candle:

$$
O=100,\quad H=105,\quad L=97,\quad C=103.
$$

Jika strategi memasang:

$$
BUY\ LIMIT=98
$$

dan:

$$
SL=97,
$$

kita **tidak bisa langsung mengatakan**:

> "Low = 97, jadi limit order filled lalu stop-loss terkena."

Karena kita tidak tahu urutan intrabar.

Bisa saja:

$$
100
\rightarrow
105
\rightarrow
98
\rightarrow
103
\rightarrow
97
$$

atau:

$$
100
\rightarrow
97
\rightarrow
98
\rightarrow
105
\rightarrow
103.
$$

Konsekuensinya berbeda.

---

# Q.3. Urutan kejadian adalah informasi

Misalkan:

$$
TP=105,
$$

$$
SL=97.
$$

Dalam satu candle:

$$
H=105,\quad L=97.
$$

Apakah TP atau SL terjadi terlebih dahulu?

Data OHLC saja tidak dapat menjawab.

Karena itu:

$$
\boxed{
OHLC\ Backtest
\neq
Market\ Simulation.
}
$$

---

# Q.4. Hierarki data

Untuk sistem kita, idealnya data dibagi menjadi:

### Level 1 — Macro

$$
DXY,\ Gold,\ SPX,\ Nasdaq,\ VIX,\ BTC,\ ETH,\ldots
$$

### Level 2 — Market

$$
OHLCV.
$$

### Level 3 — Microstructure

$$
Bid,\ Ask,\ Depth,\ Trades,\ Order\ Book.
$$

### Level 4 — Event

$$
Order\ Submitted,
Order\ Filled,
Order\ Cancelled,
Stop\ Triggered,
TP\ Triggered.
$$

---

# Q.5. Informasi filtration

Ini bagian matematis yang sangat penting.

Misalkan:

$$
\mathcal F_t
$$

adalah seluruh informasi yang tersedia sampai waktu $t$.

Strategi harus memenuhi:

$$
\boxed{
a_t
\in
\mathcal F_t.
}
$$

Artinya keputusan pada waktu $t$ **tidak boleh bergantung pada informasi dari $t+\Delta t$**.

Ini disebut *adapted strategy*.

---

# Q.6. Larangan utama

Tidak boleh:

$$
a_t=f(P_{t+1}).
$$

Tidak boleh pula:

$$
a_t=f(H_{t:t+1},L_{t:t+1}).
$$

Keputusan hanya boleh:

$$
\boxed{
a_t=f(\mathcal F_t).
}
$$

---

# Q.7. Mengapa ini sangat penting untuk sistem kita?

Karena model kita memiliki:

$$
\hat\mu_t,
$$

$$
\hat\Sigma_t,
$$

$$
P(Fill),
$$

$$
QUBO_t,
$$

$$
SL_t,
$$

$$
TP_t.
$$

Semua harus dihitung berdasarkan:

$$
\boxed{
\mathcal F_t
}
$$

dan bukan berdasarkan seluruh dataset.

---

# Q.8. Rolling information set

Misalnya kita melakukan backtest pada:

$$
2021-01-01
\rightarrow
2023-12-31.
$$

Pada:

$$
t=2022-05-01,
$$

model hanya boleh mengetahui:

$$
2021-01-01
\rightarrow
2022-05-01.
$$

Bukan:

$$
2022-05-02
\rightarrow
2023-12-31.
$$

---

# Q.9. Training → validation → test

Dataset harus dibagi secara temporal.

Misalnya:

$$
\boxed{
Train
=
2021-2022
}
$$

$$
\boxed{
Validation
=
2023\ Q1
}
$$

$$
\boxed{
Test
=
2023\ Q2-Q4
}
$$

Tetapi untuk sistem yang adaptif, kita sebaiknya melangkah lebih jauh:

$$
\boxed{
Walk\ Forward\ Validation.
}
$$

---

# Q.10. Walk-forward

Misalkan:

$$
W_1:
\text{Train }[t_0,t_1]
\rightarrow
\text{Test }[t_1,t_2].
$$

Kemudian:

$$
W_2:
\text{Train }[t_0,t_2]
\rightarrow
\text{Test }[t_2,t_3].
$$

Kemudian:

$$
W_3:
\text{Train }[t_0,t_3]
\rightarrow
\text{Test }[t_3,t_4].
$$

Sehingga:

$$
\boxed{
\text{Model selalu menghadapi masa depan yang belum dilihat.}
}
$$

---

# Q.11. Purging

Jika target prediction menggunakan horizon:

$$
h
$$

dan sample training berdekatan dengan validation, dapat terjadi overlap.

Misalnya:

$$
X_t\rightarrow Y_{t+10}.
$$

Kemudian validation dimulai pada:

$$
t+5.
$$

Maka informasi target overlap.

Karena itu kita dapat menggunakan:

$$
\boxed{
Purged\ Walk\ Forward.
}
$$

---

# Q.12. Embargo

Setelah training set berakhir, kita dapat memberikan gap:

$$
\boxed{
[t_{train,end},t_{test,start}]
}
$$

untuk mengurangi leakage akibat dependensi temporal.

---

# Q.13. Market simulator

Sekarang kita definisikan simulator:

$$
\boxed{
\mathcal M
}
$$

yang menerima:

$$
(state_t,event_t,action_t)
$$

dan menghasilkan:

$$
(state_{t+1},event_{t+1},reward_t).
$$

Secara matematis:

$$
\boxed{
S_{t+1}
=
\mathcal M(S_t,A_t,E_t).
}
$$

---

# Q.14. State

State sistem:

$$
S_t=
\{
M_t,
F_t,
O_t,
P_t,
R_t,
C_t
\}.
$$

Dengan:

- $M_t$: market state,
- $F_t$: factor state,
- $O_t$: open orders,
- $P_t$: positions,
- $R_t$: risk state,
- $C_t$: capital.

---

# Q.15. Event

Event:

$$
E_t\in\mathcal E.
$$

Misalnya:

$$
\mathcal E=
\{
MarketUpdate,
Signal,
OrderSubmit,
OrderFill,
OrderCancel,
StopTrigger,
TakeProfit,
Timer
\}.
$$

---

# Q.16. Event queue

Simulator mempunyai:

$$
\boxed{
PriorityQueue
}
$$

berdasarkan timestamp.

Misalnya:

```text
09:30:00.000 MarketUpdate
09:30:00.005 Signal
09:30:00.006 OrderSubmit
09:30:00.120 Trade
09:30:00.121 PartialFill
09:30:02.000 Trade
09:30:02.001 Fill
09:31:15.000 Timer
```

Simulator memproses satu per satu.

---

# Q.17. Event loop

Secara konseptual:

```text
while event_queue not empty:

    event = next_event()

    update_market_state(event)

    process_open_orders()

    process_positions()

    if decision_event:
        generate_signal()

    if optimization_event:
        solve_QUBO()

    if execution_event:
        place_or_modify_orders()

    update_PnL()

    update_risk()

    record_state()
```

Ini adalah jantung backtester.

---

# Q.18. Timestamp discipline

Setiap data harus memiliki:

$$
\boxed{
timestamp.
}
$$

Dan timestamp harus konsisten:

$$
UTC
$$

atau timezone yang jelas.

Tidak boleh mencampur:

$$
UTC+0
$$

dengan:

$$
UTC+7
$$

tanpa konversi.

---

# Q.19. Clock model

Kita dapat menggunakan:

$$
t_0<t_1<t_2<\cdots<t_N.
$$

Setiap event:

$$
e_i=(t_i,type_i,data_i).
$$

Kemudian:

$$
t_{i+1}\geq t_i.
$$

---

# Q.20. Order model

Setiap order kita representasikan sebagai:

$$
O_i=
(
id,
symbol,
side,
type,
price,
quantity,
remaining,
timestamp,
status,
SL,
TP
).
$$

Misalnya:

$$
O_i=
(BTC,BUY,LIMIT,100000,0.001,\ldots).
$$

---

# Q.21. Order status

$$
\boxed{
NEW
\rightarrow
OPEN
\rightarrow
PARTIAL
\rightarrow
FILLED
}
$$

atau:

$$
OPEN\rightarrow CANCELLED.
$$

atau:

$$
PARTIAL\rightarrow CANCELLED.
$$

---

# Q.22. Market order simulation

Market buy:

$$
P_{exec}
=
VWAP_{ask}(q).
$$

Market sell:

$$
P_{exec}
=
VWAP_{bid}(q).
$$

Jika hanya OHLCV tersedia, kita perlu menggunakan model slippage.

Misalnya:

$$
P_{exec}
=
P_t
+
\epsilon(q,\sigma,D).
$$

---

# Q.23. Limit order simulation

Jika:

$$
P_{ask}\leq P_{limit}
$$

untuk buy, order berpotensi filled.

Tetapi **tidak otomatis filled**.

Kita harus mempertimbangkan:

$$
Q_{queue}.
$$

---

# Q.24. Queue simulator

Misalkan:

$$
Q_t=500.
$$

Order kita:

$$
q=100.
$$

Kemudian market sells consume:

$$
200.
$$

Maka:

$$
Q_{remaining}=300.
$$

Order kita belum filled.

Jika kemudian:

$$
400
$$

unit dikonsumsi:

$$
300
$$

menghabiskan queue depan.

Maka:

$$
100
$$

dapat mengisi order kita.

---

# Q.25. Partial fill

Jika hanya:

$$
70
$$

unit yang tersedia setelah queue habis:

$$
q_{filled}=70.
$$

Remaining:

$$
q_{remaining}=30.
$$

Simulator harus mempertahankan state tersebut.

---

# Q.26. Fill probability model

Jika order book tidak tersedia secara historis, kita dapat membuat:

$$
\boxed{
\hat p_F
=
f(
spread,
depth,
imbalance,
queue,
volatility,
flow,
distance
).
}
$$

Misalnya logistic model:

$$
\boxed{
p_F
=
\sigma(
\beta_0+
\beta^Tx
)
}
$$

dengan:

$$
\sigma(z)=\frac1{1+e^{-z}}.
$$

---

# Q.27. Tetapi ada masalah besar

Kita **tidak boleh** melatih:

$$
p_F
$$

dengan data masa depan lalu menggunakannya pada masa lalu.

Jadi:

$$
\beta
$$

harus diperoleh dari training window.

Kemudian digunakan pada test window.

---

# Q.28. Stop-loss simulation

Misalkan posisi long:

$$
P_{entry}=100.
$$

SL:

$$
95.
$$

Jika market tick menyentuh:

$$
95,
$$

stop triggered.

Tetapi execution mungkin:

$$
95.1
$$

atau:

$$
94.8
$$

karena slippage.

Maka:

$$
\boxed{
P_{exit}\neq P_{SL}.
}
$$

---

# Q.29. Gap risk

Misalkan:

$$
SL=95.
$$

Tetapi harga berikutnya:

$$
90.
$$

Maka:

$$
P_{exit}\approx90,
$$

bukan:

$$
95.
$$

Ini penting untuk saham.

Untuk crypto yang berjalan 24/7, gap masih dapat terjadi secara efektif melalui lonjakan harga, meskipun mekanisme penutupan pasar berbeda.

---

# Q.30. TP juga bukan guaranteed price

Jika:

$$
TP=105
$$

dan market melompat:

$$
103\rightarrow108,
$$

execution dapat:

$$
P_{exit}>105.
$$

Sebaliknya jika liquidity buruk:

$$
P_{exit}
$$

bisa lebih buruk.

---

# Q.31. PnL

Untuk long:

$$
\boxed{
PnL_t
=
q(P_t-P_{entry})
-
C_t.
}
$$

Untuk short:

$$
\boxed{
PnL_t
=
q(P_{entry}-P_t)
-
C_t.
}
$$

Dengan:

$$
C_t
=
fees+slippage+impact.
$$

---

# Q.32. Realized dan unrealized PnL

$$
PnL_t
=
PnL_t^{realized}
+
PnL_t^{unrealized}.
$$

Realized:

$$
PnL^{realized}
$$

hanya berasal dari posisi yang sudah ditutup.

---

# Q.33. Equity curve

Capital:

$$
C_0.
$$

Maka:

$$
\boxed{
C_t
=
C_0+
\sum_{\tau\leq t}PnL_\tau.
}
$$

Equity curve:

$$
E(t)=C_t.
$$

Ini yang akhirnya kita gunakan untuk evaluasi strategi.

---

# Q.34. Drawdown

High-water mark:

$$
H_t=\max_{\tau\leq t}E_\tau.
$$

Drawdown:

$$
\boxed{
DD_t
=
\frac{H_t-E_t}{H_t}.
}
$$

Maximum drawdown:

$$
\boxed{
MDD=\max_tDD_t.
}
$$

---

# Q.35. Tetapi Sharpe Ratio saja tidak cukup

Kita akan mengukur:

$$
Sharpe
=
\frac{E[R_p-R_f]}
{\sigma(R_p)}.
$$

Tetapi juga:

$$
Sortino,
$$

$$
Calmar,
$$

$$
MDD,
$$

$$
Profit\ Factor,
$$

$$
Win\ Rate,
$$

$$
Expectancy,
$$

$$
Tail\ Risk.
$$

---

# Q.36. Trade expectancy

Jika:

$$
p_w=P(win),
$$

$$
G=E[gain],
$$

$$
L=E[loss],
$$

maka:

$$
\boxed{
E[\Pi]
=
p_wG-(1-p_w)L.
}
$$

Namun untuk sistem kita, expectancy harus sudah memasukkan:

$$
fees,
$$

$$
slippage,
$$

$$
execution.
$$

---

# Q.37. Contoh penting

Strategi A:

$$
WinRate=60\%.
$$

Strategi B:

$$
WinRate=40\%.
$$

Belum tentu A lebih baik.

Misalnya:

### A

$$
Gain=1
$$

$$
Loss=2.
$$

Expectancy:

$$
0.6(1)-0.4(2)
=
-0.2.
$$

### B

$$
Gain=3
$$

$$
Loss=1.
$$

$$
0.4(3)-0.6(1)
=
0.6.
$$

Jadi:

$$
\boxed{
WinRate\neq Strategy\ Quality.
}
$$

---

# Q.38. Risk-adjusted performance

Karena kita menetapkan:

$$
R_{trade}\leq \$1,
$$

kita juga dapat mengukur:

$$
\boxed{
Return/Risk.
}
$$

Misalnya:

$$
\frac{E[PnL]}{E[Risk]}.
$$

Ini lebih relevan terhadap filosofi sistem kita.

---

# Q.39. Transaction Cost Analysis

Tahap Q juga harus memecah PnL:

$$
\boxed{
Gross\ Alpha
}
$$

menjadi:

$$
Gross\ Alpha
-
Spread
-
Slippage
-
Fees
-
Impact
-
Opportunity\ Cost.
$$

Sehingga:

$$
\boxed{
Net\ Alpha
}
$$

dapat dihitung.

---

# Q.40. Ini akan sangat penting

Bayangkan:

$$
Gross\ Return=20\%.
$$

Tetapi:

$$
Transaction\ Cost=18\%.
$$

Maka:

$$
Net=2\%.
$$

Model tersebut secara praktis hampir tidak berguna.

---

# Q.41. Sensitivity analysis

Kita tidak boleh hanya menjalankan satu konfigurasi.

Misalnya:

$$
Spread
\times
\{
0.5,1,2\}
$$

$$
Slippage
\times
\{
0.5,1,2\}
$$

$$
Fee
\times
\{
0.5,1,2\}.
$$

Kemudian lihat apakah strategi tetap profitable.

---

# Q.42. Stress testing

Market regime:

$$
\mathcal R=
\{
Normal,
HighVol,
Crash,
LowLiquidity,
Trend,
MeanReversion
\}.
$$

Backtester harus mengukur:

$$
Performance(\mathcal R_i).
$$

---

# Q.43. Contoh

Jika:

$$
Sharpe_{normal}=2.1
$$

tetapi:

$$
Sharpe_{crash}=-4.0,
$$

kita harus memahami mengapa.

Bukan sekadar mengatakan:

> "Sharpe total = 1.7."

---

# Q.44. Monte Carlo trade reshuffling

Setelah memperoleh sequence:

$$
\Pi_1,\Pi_2,\ldots,\Pi_N,
$$

kita dapat melakukan bootstrap.

Misalnya:

$$
10,000
$$

simulasi urutan trade.

Kemudian hitung:

$$
MDD^{(i)}.
$$

Sehingga diperoleh distribusi:

$$
P(MDD>x).
$$

---

# Q.45. Ini membantu menjawab:

> "Apakah drawdown terbesar yang saya lihat memang representatif?"

Misalnya backtest menunjukkan:

$$
MDD=12\%.
$$

Tetapi Monte Carlo menunjukkan:

$$
95\%\text{ quantile}=24\%.
$$

Maka strategi sebenarnya jauh lebih berisiko daripada yang tampak dari satu historical path.

---

# Q.46. Parameter uncertainty

Kita juga harus mempertimbangkan:

$$
\hat\theta
$$

bukan:

$$
\theta.
$$

Misalnya:

$$
\hat\beta,
\hat\Sigma,
\hat\mu,
\hat\lambda.
$$

Semua memiliki uncertainty.

Maka:

$$
\boxed{
Model\ Risk
}
$$

harus masuk dalam evaluasi.

---

# Q.47. Optimizer uncertainty

Ini bahkan lebih relevan untuk quantum.

Misalkan:

$$
QUBO^\star
$$

menghasilkan solusi:

$$
x^\star.
$$

Tetapi QAOA hanya memperoleh:

$$
\tilde x.
$$

Kita harus mengukur:

$$
\boxed{
Gap
=
E(x^\star)-E(\tilde x).
}
$$

---

# Q.48. Quantum trading backtest

Ini akan menjadi salah satu bagian paling menarik dari proyek kita.

Untuk setiap problem:

$$
Q_t
$$

kita dapat menjalankan:

### Exact

$$
x_t^{exact}.
$$

### Classical heuristic

$$
x_t^{classical}.
$$

### QAOA

$$
x_t^{QAOA}.
$$

Kemudian:

$$
PnL^{exact},
$$

$$
PnL^{classical},
$$

$$
PnL^{QAOA}.
$$

---

# Q.49. Tetapi jangan langsung membandingkan PnL

Misalnya QAOA menghasilkan PnL:

$$
10\%.
$$

Classical:

$$
12\%.
$$

Belum tentu QAOA buruk.

Kita harus mengetahui:

$$
\text{Problem Size},
$$

$$
\text{Runtime},
$$

$$
\text{Solution Quality},
$$

$$
\text{Constraint Violation}.
$$

---

# Q.50. Approximation ratio

Untuk minimization:

$$
\boxed{
\rho
=
\frac{E_{QAOA}}
{E_{optimal}}
}
$$

dengan definisi yang harus disesuaikan dengan konvensi objective.

Untuk maximization:

$$
\boxed{
\rho
=
\frac{E_{QAOA}}
{E_{optimal}}.
}
$$

Jika:

$$
\rho\rightarrow1,
$$

solusi semakin dekat optimum.

---

# Q.51. Yang lebih penting: economic degradation

Kita dapat mendefinisikan:

$$
\boxed{
\Delta PnL
=
PnL_{optimal}
-
PnL_{QAOA}.
}
$$

Kemudian:

$$
\boxed{
Economic\ Cost\ of\ Approximation
}
$$

adalah:

$$
EC_{approx}
=
\Delta PnL.
$$

Jadi kita tidak hanya mengatakan:

> "QAOA mempunyai approximation ratio 95%."

Tetapi:

> "Approximation error 5% tersebut menyebabkan penurunan expected PnL sebesar X."

Ini jauh lebih bermakna secara finansial.

---

# Q.52. Event-driven backtest architecture

Saya menyarankan struktur:

```text
TradeProject/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── features/
│
├── market/
│   ├── market_state.py
│   ├── order_book.py
│   └── factor_state.py
│
├── strategy/
│   ├── alpha.py
│   ├── signal.py
│   └── regime.py
│
├── optimization/
│   ├── portfolio_qubo.py
│   ├── entry_qubo.py
│   ├── management_qubo.py
│   └── execution_qubo.py
│
├── execution/
│   ├── order.py
│   ├── fill_model.py
│   ├── slippage.py
│   └── impact.py
│
├── portfolio/
│   ├── position.py
│   ├── pnl.py
│   └── risk.py
│
├── backtest/
│   ├── engine.py
│   ├── event.py
│   ├── clock.py
│   └── simulator.py
│
├── evaluation/
│   ├── metrics.py
│   ├── drawdown.py
│   ├── monte_carlo.py
│   └── stress_test.py
│
└── experiments/
```

---

# Q.53. Satu prinsip arsitektur yang sangat penting

**Strategy tidak boleh mengetahui masa depan.**

Jadi jangan membuat:

```python
strategy(data)
```

dengan:

```python
data = entire_dataset
```

lalu strategy mengambil apa saja.

Lebih aman:

```python
strategy.on_event(event, state)
```

dan:

```python
state
```

hanya berisi informasi sampai:

$$
t.
$$

---

# Q.54. Data leakage audit

Kita harus memiliki pemeriksaan:

$$
\boxed{
timestamp(data)
\leq
timestamp(decision).
}
$$

Untuk setiap feature:

$$
X_{i,t}
$$

harus memenuhi:

$$
X_{i,t}\in\mathcal F_t.
$$

---

# Q.55. Contoh bug yang sangat berbahaya

Misalkan kita menghitung:

$$
20\text{-day moving average}
$$

menggunakan:

```python
rolling(20).mean()
```

itu relatif aman.

Tetapi jika kita menggunakan:

```python
center=True
```

maka feature pada $t$ dapat menggunakan:

$$
P_{t+1},P_{t+2},\ldots
$$

dan backtest menjadi invalid.

---

# Q.56. Bug lain: normalization

Jika kita melakukan:

$$
z_t=
\frac{x_t-\mu_{all}}
{\sigma_{all}}
$$

dengan:

$$
\mu_{all}
$$

dihitung menggunakan seluruh dataset, maka future information bocor.

Harus:

$$
\boxed{
z_t=
\frac{x_t-\mu_t^{past}}
{\sigma_t^{past}}.
}
$$

---

# Q.57. Bug lain: covariance

Dalam portfolio optimizer kita menggunakan:

$$
\Sigma_t.
$$

Jangan menghitung:

$$
\Sigma_{2021-2023}
$$

untuk membuat keputusan pada:

$$
2021.
$$

Harus:

$$
\boxed{
\Sigma_t
=
Cov(
r_{t-L:t}
).
}
$$

---

# Q.58. Bug lain: universe selection

Misalnya memilih saham berdasarkan:

> "saham yang sekarang masih aktif dan performanya bagus."

Kemudian digunakan untuk backtest 2015.

Ini:

$$
\boxed{
Survivorship\ Bias.
}
$$

Universe harus direkonstruksi berdasarkan informasi yang tersedia pada saat itu.

---

# Q.59. Bug lain: delisting

Jika saham hilang dari dataset karena bangkrut, lalu kita hanya menyimpan saham yang masih ada, hasil backtest terlalu optimistis.

Karena itu dataset historical harus mempertahankan:

$$
delisted\ assets.
$$

---

# Q.60. Bug lain: corporate actions

Untuk saham:

$$
split,
dividend,
rights,
merger
$$

harus diperhatikan.

Jika tidak, return dapat salah.

---

# Q.61. Crypto memiliki masalah yang berbeda

Crypto:

- 24/7,
- exchange fragmentation,
- funding rate,
- liquidation,
- perpetual futures,
- maker/taker fee,
- spread yang berubah cepat.

Jadi simulator crypto perlu:

$$
\boxed{
Funding\ Model.
}
$$

---

# Q.62. Jika menggunakan perpetual futures

PnL tidak hanya:

$$
price\ PnL.
$$

Tetapi:

$$
\boxed{
PnL
=
PricePnL
+
FundingPnL
-
Fees
-
Slippage.
}
$$

Funding:

$$
FundingPnL
=
qP_t f_t
$$

dengan konvensi tanda yang sesuai dengan posisi long/short dan funding rate.

---

# Q.63. Untuk saham internasional

Kita perlu:

$$
FX.
$$

Misalnya saham Jepang:

$$
JPY.
$$

Tetapi account base:

$$
USD.
$$

Maka:

$$
\boxed{
PnL_{USD}
=
PnL_{JPY}
\times
FX_{JPY/USD}.
}
$$

Ini membuat faktor:

$$
DXY
$$

dan FX exposure menjadi bagian dari risk model.

---

# Q.64. Gold dan USD dominance

Karena kita sebelumnya ingin sistem lintas pasar, state global dapat:

$$
F_t=
[
r_{Gold},
r_{DXY},
r_{SPX},
r_{NQ},
r_{BTC},
r_{ETH},
r_{VIX},
\ldots
].
$$

Kemudian:

$$
r_i
=
\alpha_i+\beta_i^TF_t+\epsilon_i.
$$

---

# Q.65. Event-driven factor update

Jika:

$$
DXY
$$

berubah pada:

$$
t,
$$

maka factor state langsung berubah:

$$
F_t\rightarrow F_{t+1}.
$$

Kemudian:

$$
\hat\mu_{asset}
$$

dihitung ulang.

Dengan demikian:

$$
\boxed{
Macro\ information
\rightarrow
Asset\ forecast
\rightarrow
Optimization
}
$$

secara dinamis.

---

# Q.66. Re-optimization

Kita tidak perlu menjalankan QUBO pada setiap tick.

Kita dapat menetapkan:

$$
\Delta t_{opt}.
$$

Misalnya:

$$
\Delta t_{opt}=1h.
$$

Tetapi execution dapat berjalan pada resolusi lebih tinggi.

Jadi:

$$
\boxed{
Forecast/Optimization:
1h
}
$$

sementara:

$$
\boxed{
Execution:
tick/second/minute
}
$$

tergantung data.

---

# Q.67. Ini menghasilkan multi-timescale architecture

Misalnya:

$$
\boxed{
Macro:
1D
}
$$

$$
\boxed{
Factor:
1H
}
$$

$$
\boxed{
Alpha:
5M
}
$$

$$
\boxed{
Execution:
1S
}
$$

atau bahkan:

$$
Tick.
$$

---

# Q.68. Ini sangat cocok dengan konsep sebelumnya

Kita sebenarnya memiliki:

$$
\boxed{
Slow\ State
}
$$

dan:

$$
\boxed{
Fast\ State.
}
$$

Slow:

$$
DXY,\ Gold,\ regime,\ covariance.
$$

Fast:

$$
Orderbook,\ imbalance,\ spread,\ flow.
$$

Kemudian:

$$
\boxed{
Decision
=
f(SlowState,FastState).
}
$$

---

# Q.69. Akhirnya kita mendapatkan hierarchical control

Secara konseptual:

$$
\boxed{
\text{Strategic Layer}
}
$$

menentukan:

$$
\text{What}.
$$

$$
\boxed{
\text{Tactical Layer}
}
$$

menentukan:

$$
\text{When}.
$$

$$
\boxed{
\text{Execution Layer}
}
$$

menentukan:

$$
\text{How}.
$$

---

# Q.70. Dan semuanya diuji oleh simulator

Jadi:

```text
Historical Market
       │
       ▼
┌──────────────────┐
│ Event Generator  │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Market Simulator │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Strategy Engine  │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ QUBO / QAOA      │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Execution Engine │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Portfolio/Risk   │
└────────┬─────────┘
         │
         └──────────────┐
                        ▼
                 Next Event
```

---

# Q.71. Kriteria bahwa backtester kita sudah "benar"

Saya tidak ingin kita mengatakan:

> "Backtester selesai karena grafik equity curve sudah muncul."

Backtester baru layak dipercaya jika kita bisa membuktikan:

### 1. No look-ahead

$$
a_t\in\mathcal F_t.
$$

### 2. No survivorship bias

Universe historical valid.

### 3. Realistic execution

$$
P_{exec}\neq P_{close}.
$$

### 4. Realistic limit fill

$$
P(Fill)<1.
$$

### 5. Transaction costs

$$
Fee+Spread+Slippage+Impact.
$$

### 6. Partial fills

Didukung.

### 7. Dynamic SL/TP

Didukung.

### 8. Multi-asset capital constraint

Didukung.

### 9. Walk-forward

Didukung.

### 10. Monte Carlo/stress test

Didukung.

---

# Q.72. Unit test yang harus kita buat

Sebelum menjalankan strategi besar, kita buat market kecil yang kita **tahu jawabannya**.

Misalnya:

$$
P_0=100,
$$

kemudian:

$$
100\rightarrow101\rightarrow102.
$$

Jika:

$$
BUY=100,
$$

$$
SELL=102,
$$

maka:

$$
PnL=2q.
$$

Simulator harus menghasilkan tepat itu.

Kemudian tambahkan:

$$
fee.
$$

Kemudian:

$$
slippage.
$$

Kemudian:

$$
partial fill.
$$

Dengan demikian setiap komponen dapat diverifikasi.

---

# Q.73. Invariant risk

Simulator harus selalu memeriksa:

$$
\boxed{
R_{open}\leq R_{max}.
}
$$

Jika:

$$
R_{open}>\$1
$$

untuk sebuah trade, sistem harus menghasilkan error atau reject.

Bukan diam-diam melanjutkan.

---

# Q.74. Capital invariant

Jika capital:

$$
C_t
$$

maka:

$$
Margin_t\leq C_t
$$

atau sesuai leverage/margin rules.

Tidak boleh:

$$
Position
>
AvailableCapital
$$

kecuali leverage memang dimodelkan.

---

# Q.75. Position invariant

Misalnya strategi melarang short.

Maka:

$$
q_t\geq0.
$$

Jika futures:

$$
q_t\in\mathbb R.
$$

Semua constraint harus eksplisit.

---

# Q.76. Audit trail

Setiap keputusan harus dapat dijelaskan.

Misalnya:

```text
2026-08-17 10:00

Signal:
LONG SOL

Expected return:
0.31%

Risk:
$0.73

QUBO solution:
BUY = 1

Execution:
LIMIT @ 182.40

Fill probability:
0.71

Queue:
1,243 SOL

Expected slippage:
0.004%

Decision:
PLACE LIMIT
```

Ini akan sangat berguna ketika kita melakukan debugging.

---

# Q.77. Bahkan QAOA harus diaudit

Misalnya:

```text
QAOA

n_qubits = 12
p = 2
shots = 4096

best bitstring:
101001101010

objective:
-17.42

exact optimum:
-17.91

approximation ratio:
0.973
```

Kemudian:

$$
\boxed{
economic\ impact
}
$$

dari solusi tersebut dicatat.

---

# Q.78. Backtest report

Setiap eksperimen sebaiknya menghasilkan:

```text
Experiment ID
Data Version
Feature Version
Model Version
QUBO Version
Optimizer Version
Transaction Cost Model
Random Seed
Start Date
End Date
```

Sehingga eksperimen:

$$
E_1
$$

dapat direproduksi.

---

# Q.79. Ini penting untuk quantum

Karena QAOA stochastic.

Misalnya:

$$
seed=1
$$

menghasilkan:

$$
PnL=14\%.
$$

Sedangkan:

$$
seed=2
$$

menghasilkan:

$$
PnL=8\%.
$$

Kita tidak boleh memilih seed yang paling bagus.

Harus:

$$
\boxed{
E_{\text{seed}}[PnL]
}
$$

dan:

$$
Var_{\text{seed}}(PnL).
$$

---

# Q.80. QAOA sebagai stochastic optimizer

Secara konseptual:

$$
x^\star
=
QAOA(Q_t;\theta,\xi)
$$

dengan:

$$
\xi
$$

adalah stochastic measurement noise.

Maka:

$$
P(x)
$$

bukan deterministic.

Backtester harus mampu menangani hal tersebut.

---

# Q.81. Ini membawa kita ke metrik yang sangat menarik

Bukan hanya:

$$
PnL.
$$

Tetapi:

$$
\boxed{
PnL\ per\ QAOA\ evaluation.
}
$$

atau:

$$
\boxed{
Economic\ Value
/
Computational\ Cost.
}
$$

Misalnya:

$$
EV_{quantum}
=
\frac{
E[PnL_{QAOA}]
-
E[PnL_{classical}]
}{
Runtime_{QAOA}
}.
$$

Ini jauh lebih dekat dengan pertanyaan:

> Apakah optimasi quantum benar-benar memberikan nilai ekonomi?

---

# Q.82. Tahap Q mengubah proyek kita

Sebelum Q:

> "Kita mempunyai model trading yang kompleks."

Setelah Q:

> **"Kita mempunyai eksperimen yang dapat diverifikasi terhadap market timeline."**

Itu perbedaan besar.

---

# Q.83. Hubungan seluruh tahapan

Sekarang pipeline kita secara konseptual:

$$
\boxed{
A
\rightarrow
B
\rightarrow
C
\rightarrow
\cdots
\rightarrow
P
\rightarrow
Q
}
$$

dan Q bertindak sebagai **validation environment**.

Lebih tepatnya:

$$
\boxed{
Q
\supset
A\text{--}P
}
$$

dalam arti simulator menjalankan seluruh komponen tersebut dalam waktu historis.

---

# Q.84. Arsitektur final sementara

Saya akan menggambarkannya seperti ini:

```text
                    HISTORICAL DATA
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
     MACRO             MARKET          MICROSTRUCTURE
   DXY/GOLD/SPX       OHLCV             ORDER BOOK
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                    FEATURE ENGINE
                          │
                          ▼
                    STATE ESTIMATOR
                          │
                          ▼
                    ALPHA FORECAST
                          │
                          ▼
                 PORTFOLIO OPTIMIZER
                          │
                          ▼
                     ENTRY QUBO
                          │
                          ▼
                  POSITION MANAGER
                          │
                          ▼
                  EXECUTION QUBO
                          │
                          ▼
                  ORDER SIMULATOR
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
             FILLED               NO FILL
                │                   │
                ▼                   ▼
             POSITION            REOPTIMIZE
                │
                ▼
             SL / TP
                │
                ▼
              EXIT
                │
                ▼
               PnL
                │
                ▼
           RISK / METRICS
                │
                ▼
          WALK-FORWARD TEST
                │
                ▼
          MONTE CARLO / STRESS
                │
                ▼
          ECONOMIC EVALUATION
```

---

# Q.85. Dan sekarang kita sampai pada satu titik yang sangat menarik

Kita sebenarnya telah mengubah masalah:

> **"Buat trading bot."**

menjadi:

$$
\boxed{
\text{Sequential Stochastic Constrained Optimization Problem}
}
$$

dengan state:

$$
S_t,
$$

action:

$$
A_t,
$$

constraint:

$$
g(S_t,A_t)\leq0,
$$

objective:

$$
J=
E\left[
\sum_t
\gamma^t
R(S_t,A_t)
\right].
$$

Tetapi **kita belum perlu menyebutnya reinforcement learning**.

Kita dapat menyelesaikan setiap keputusan menggunakan optimizer yang sesuai.

---

# Q.86. Formulasi matematis keseluruhan

Secara abstrak:

$$
\boxed{
S_{t+1}
=
F(S_t,A_t,\epsilon_t)
}
$$

dengan:

$$
A_t
=
\arg\max_{a\in\mathcal A(S_t)}
U(S_t,a).
$$

Reward:

$$
R_t
=
PnL_t
-
C_t
-
\lambda Risk_t.
$$

Kemudian objective:

$$
\boxed{
\max_{\pi}
E_\pi
\left[
\sum_{t=0}^{T}
\gamma^t
R_t
\right].
}
$$

Ini adalah fondasi matematis yang nantinya memungkinkan kita, **jika memang diperlukan**, mengubah beberapa modul menjadi MDP/RL.

---

# Q.87. Tetapi untuk sekarang saya akan mempertahankan prinsip

$$
\boxed{
Don't use RL just because we can.
}
$$

Kita ingin setiap komponen memiliki interpretasi finansial dan matematis:

$$
\text{Forecast}
$$

$$
\downarrow
$$

$$
\text{Optimization}
$$

$$
\downarrow
$$

$$
\text{Execution}
$$

$$
\downarrow
$$

$$
\text{Risk}
$$

$$
\downarrow
$$

$$
\text{PnL}.
$$

Dengan demikian apabila sistem gagal, kita dapat mengetahui:

> **di mana ia gagal.**

---

# Q.88. Tahap Q selesai jika kita mampu melakukan eksperimen ini

Misalnya:

$$
2023-01-01
\rightarrow
2023-12-31
$$

dan simulator menghasilkan:

```text
Capital
Initial       $1,000
Final         $1,137

Trades        428
Win rate      47.4%
Profit factor 1.31

Sharpe        1.42
Sortino       1.96
Max DD        8.7%

Avg risk      $0.73
Max risk      $1.00

Avg slippage  0.031%
Avg fee       0.040%

Limit fills   62.1%
Partial fills 14.7%
```

Tetapi yang jauh lebih penting:

**setiap angka tersebut harus dapat ditelusuri kembali ke event dan keputusan yang menghasilkan angka itu.**

---

# Q.89. Deliverable Tahap Q

Jadi implementasi nyata Tahap Q nantinya harus menghasilkan minimal:

### Engine

$$
\boxed{
EventDrivenBacktester
}
$$

### Market simulator

$$
\boxed{
MarketSimulator
}
$$

### Order simulator

$$
\boxed{
OrderBookSimulator
}
$$

### Fill model

$$
\boxed{
FillModel
}
$$

### Cost model

$$
\boxed{
TransactionCostModel
}
$$

### Portfolio

$$
\boxed{
PortfolioLedger
}
$$

### Risk

$$
\boxed{
RiskEngine
}
$$

### Evaluation

$$
\boxed{
PerformanceAnalyzer
}
$$

### Validation

$$
\boxed{
WalkForwardEngine
}
$$

### Robustness

$$
\boxed{
MonteCarloEngine
}
$$

---

# Q.90. Dan satu aturan emas

**Jangan optimasi QAOA terhadap historical PnL secara langsung terlebih dahulu.**

Pertama:

$$
\boxed{
Past\ Data
\rightarrow
Valid\ Simulator
}
$$

kemudian:

$$
\boxed{
Simulator
\rightarrow
Baseline\ Strategy
}
$$

kemudian:

$$
\boxed{
Baseline
\rightarrow
Classical\ Optimization
}
$$

baru:

$$
\boxed{
Classical
\rightarrow
QAOA
}
$$

Dengan demikian jika QAOA menghasilkan hasil buruk, kita bisa mengetahui apakah masalahnya berasal dari:

- data,
- signal,
- formulasi QUBO,
- optimizer,
- execution,
- atau memang QAOA.

---

## Posisi kita sekarang

Tahap Q memberi kita **"physics engine" untuk eksperimen trading**.

Secara keseluruhan:

$$
\boxed{
\text{Market}
\rightarrow
\text{State}
\rightarrow
\text{Forecast}
\rightarrow
\text{Optimization}
\rightarrow
\text{Execution}
\rightarrow
\text{Market Response}
}
$$

dan loop tersebut berjalan:

$$
t=0,1,2,\ldots,T.
$$

Itulah yang membuat sistem kita berbeda dari sekadar script trading yang membaca candle lalu membeli/jual.

**Tahap berikutnya, Tahap R, menurut saya sebaiknya menjadi _Robustness, Statistical Validation & Anti-Overfitting_.** Setelah kita memiliki simulator event-driven, kita perlu menjawab pertanyaan yang jauh lebih keras: *apakah edge yang kita lihat benar-benar ada, atau hanya artefak dari parameter tuning?* Di sana kita bisa masuk ke **Deflated Sharpe Ratio, Probability of Backtest Overfitting, White's Reality Check, stationary/block bootstrap, purged walk-forward, regime-conditioned performance, multiple-hypothesis correction**, dan akhirnya menentukan apakah suatu hasil QAOA/classical optimizer layak disebut *genuine statistical edge*.

## Prompt:
8/17/2026, 10:03:38 PM

lanjut Tahap R

## Response:
8/17/2026, 10:03:39 PM

# Tahap R — Robustness, Statistical Validation & Anti-Overfitting

Ya. Kalau Tahap Q adalah **"membangun dunia virtual tempat strategi diuji"**, maka Tahap R adalah **"membuktikan bahwa hasil yang terlihat di dunia virtual itu bukan kebetulan."**

Ini justru salah satu tahap paling penting untuk sistem kita.

Karena kita sekarang memiliki banyak komponen:

$$
\text{factor model}
\rightarrow
\text{forecast}
\rightarrow
\text{QUBO}
\rightarrow
\text{QAOA/classical optimizer}
\rightarrow
\text{execution}
\rightarrow
\text{dynamic SL/TP}
$$

maka jumlah derajat kebebasan kita juga sangat besar.

Dan semakin banyak derajat kebebasan, semakin mudah kita secara tidak sengaja menemukan strategi yang **terlihat bagus hanya karena kita telah mencoba terlalu banyak hal**.

---

# R.1. Masalah fundamental: backtest yang bagus belum tentu strategi yang bagus

Misalkan kita melakukan:

$$
N=10\,000
$$

eksperimen.

Kita menemukan satu strategi:

$$
Sharpe=3.1.
$$

Apakah:

$$
H_1:\text{strategy memiliki genuine edge}
$$

benar?

Belum tentu.

Karena jika kita mencoba cukup banyak strategi, sebagian akan terlihat bagus **secara kebetulan**.

Ini disebut:

$$
\boxed{\text{Multiple Testing / Data Snooping}}
$$

---

# R.2. Contoh sederhana

Misalkan seluruh strategi sebenarnya tidak mempunyai alpha:

$$
E[R]=0.
$$

Kita mencoba 1.000 strategi.

Secara statistik, sangat mungkin beberapa memiliki:

$$
Sharpe>2,
$$

bahkan:

$$
Sharpe>3.
$$

Kemudian kita mengambil strategi terbaik.

Kita akan mengatakan:

> "Lihat! Sharpe = 3.2!"

Padahal:

$$
\boxed{
\text{kita memilihnya karena ia menang secara kebetulan.}
}
$$

---

# R.3. Inilah musuh utama kita

Ada beberapa bentuk:

$$
\boxed{
Overfitting
}
$$

$$
\boxed{
Data\ Snooping
}
$$

$$
\boxed{
Selection\ Bias
}
$$

$$
\boxed{
Multiple\ Testing
}
$$

$$
\boxed{
Parameter\ Mining
}
$$

$$
\boxed{
Regime\ Overfitting
}
$$

dan:

$$
\boxed{
Backtest\ Overfitting.
}
$$

---

# R.4. Kita perlu membedakan dua konsep

### In-sample performance

$$
IS
$$

adalah performa pada data yang digunakan untuk membangun model.

### Out-of-sample performance

$$
OOS
$$

adalah performa pada data yang **tidak digunakan** untuk memilih model.

Tujuan kita:

$$
\boxed{
Performance_{OOS}
\approx
Performance_{IS}
}
$$

bukan:

$$
Performance_{OOS}
\rightarrow0.
$$

---

# R.5. Tetapi kita bahkan tidak boleh hanya menggunakan satu OOS

Misalkan:

$$
2021-2023
$$

digunakan sebagai training.

Lalu:

$$
2024
$$

sebagai test.

Jika kita terus mengubah model berdasarkan hasil 2024, maka:

$$
2024
$$

secara perlahan berubah menjadi training data.

Karena itu kita membutuhkan:

$$
\boxed{
Nested\ / Walk\ Forward\ Validation.
}
$$

---

# R.6. Walk-forward validation

Misalkan:

```text
Train 1       Test 1
───────────│─────────
2021        │ 2022 Q1

Train 2       Test 2
─────────────│────────
2021-Q1 2022 │ 2022 Q2

Train 3       Test 3
────────────────│─────
2021-Q2 2022   │ 2022 Q3
```

dan seterusnya.

Model selalu:

$$
\boxed{
Train \rightarrow Predict\ Future
}
$$

bukan:

$$
Train\rightarrow Predict\ Past.
$$

---

# R.7. Purged walk-forward

Karena target kita dapat memiliki horizon:

$$
H.
$$

Misalnya:

$$
H=1h.
$$

Jika sample training terakhir berada terlalu dekat dengan validation, targetnya bisa overlap.

Kita buang bagian tersebut.

Jika training berakhir:

$$
t_{train},
$$

validation dimulai:

$$
t_{test},
$$

maka:

$$
t_{test}-t_{train}>H.
$$

---

# R.8. Embargo

Kita juga dapat menetapkan:

$$
E>0
$$

sebagai embargo.

Sehingga:

$$
[t_{train,end},t_{test,start}]
$$

memiliki gap.

Secara sederhana:

$$
\boxed{
\text{Train}
\rightarrow
\text{Purging}
\rightarrow
\text{Embargo}
\rightarrow
\text{Test}.
}
$$

---

# R.9. Mengapa ini sangat relevan untuk sistem kita?

Karena kita mempunyai feature seperti:

$$
\mu_t,
$$

$$
\Sigma_t,
$$

$$
DXY_t,
$$

$$
Gold_t,
$$

$$
BTC_t,
$$

$$
ETH_t,
$$

dan microstructure.

Beberapa di antaranya memiliki autocorrelation dan cross-correlation.

Jadi sample kita **tidak independent and identically distributed (IID)**.

---

# R.10. Jangan menggunakan random train-test split

Misalnya:

```python
train_test_split(X, y)
```

secara acak.

Ini berbahaya untuk time series.

Karena:

$$
X_{2023}
$$

dapat berada di training sementara:

$$
X_{2022}
$$

berada di test.

Model secara tidak langsung melihat struktur masa depan.

Untuk sistem kita:

$$
\boxed{
\text{Temporal Split Only}.
}
$$

---

# R.11. Distribution shift

Pasar tidak stationary.

Secara ideal kita ingin:

$$
P_{train}(X,Y)
=
P_{test}(X,Y).
$$

Tetapi kenyataannya:

$$
\boxed{
P_{train}(X,Y)
\neq
P_{test}(X,Y).
}
$$

Ini disebut:

$$
\boxed{
Distribution\ Shift.
}
$$

---

# R.12. Regime

Misalkan:

$$
Z_t\in
\{
Bull,
Bear,
Sideways,
HighVol,
LowVol
\}.
$$

Maka:

$$
P(R_t|Z_t)
$$

dapat berbeda drastis.

Karena itu performa harus dianalisis:

$$
E[R|Z=Bull],
$$

$$
E[R|Z=Bear],
$$

dst.

---

# R.13. Strategi yang hanya bekerja di satu regime

Misalnya:

$$
Sharpe_{Bull}=3.5
$$

tetapi:

$$
Sharpe_{Bear}=-2.0.
$$

Strategi tersebut bukan otomatis buruk.

Tetapi kita perlu memahami:

$$
\boxed{
conditional\ edge.
}
$$

Mungkin strategi memang dirancang untuk:

$$
Bull regime.
$$

---

# R.14. Regime detector

Kita dapat mendefinisikan:

$$
Z_t=f(F_t)
$$

dengan faktor:

$$
F_t=
[
\sigma_t,
DXY_t,
Gold_t,
VIX_t,
BTC_t,
SPX_t,\ldots].
$$

Kemudian strategi:

$$
\pi_t
=
\pi(S_t,Z_t).
$$

---

# R.15. Tetapi jangan overfit regime

Ini bahaya.

Misalnya kita menemukan:

> "Strategi bekerja bagus jika VIX antara 17.23 dan 21.87."

Kemudian:

> "DXY harus naik 0.17%."

Kemudian:

> "Gold harus turun 0.08%."

Kita telah membuat filter yang sangat spesifik.

Itu kemungkinan besar:

$$
\boxed{
overfitting.
}
$$

---

# R.16. Parameter stability

Misalkan parameter strategi:

$$
\theta=(\lambda,\gamma,\beta,p).
$$

Kita tidak ingin hanya:

$$
\theta^\star
$$

yang menghasilkan performa bagus.

Kita ingin neighborhood:

$$
\mathcal N(\theta^\star)
$$

juga relatif bagus.

Secara visual:

$$
\boxed{
\text{Performance surface should be smooth.}
}
$$

---

# R.17. Contoh

Buruk:

$$
Sharpe(1.01)=0.8
$$

$$
Sharpe(1.02)=0.9
$$

$$
Sharpe(1.03)=3.8
$$

$$
Sharpe(1.04)=0.7.
$$

Ini mencurigakan.

Lebih sehat:

$$
2.0,\ 2.1,\ 2.2,\ 2.1,\ 2.0.
$$

---

# R.18. Robust optimum

Idealnya:

$$
\boxed{
\theta^\star
$$

berada di area yang relatif datar.

Bukan puncak tajam.

Secara matematis:

$$
\nabla_\theta J(\theta^\star)\approx0
$$

dan:

$$
\nabla_\theta^2J
$$

tidak menghasilkan permukaan yang terlalu tajam.

Ini sebenarnya sangat mirip dengan konsep **robust optimization**.

---

# R.19. Robust optimization

Daripada:

$$
\max_\theta E[J(\theta)],
$$

kita dapat mempertimbangkan:

$$
\boxed{
\max_\theta
\min_{P\in\mathcal U}
E_P[J(\theta)]
}
$$

dengan:

$$
\mathcal U
$$

adalah uncertainty set distribusi pasar.

Artinya kita tidak mencari strategi yang terbaik pada satu estimasi distribusi.

Kita mencari strategi yang:

> **tetap cukup baik ketika asumsi kita salah.**

---

# R.20. Ini sangat cocok dengan proyek kita

Karena:

$$
\hat\mu
$$

dan:

$$
\hat\Sigma
$$

tidak pernah diketahui secara sempurna.

Misalnya:

$$
\hat\mu=\mu+\epsilon_\mu.
$$

$$
\hat\Sigma=\Sigma+\epsilon_\Sigma.
$$

Maka optimizer harus robust terhadap:

$$
(\epsilon_\mu,\epsilon_\Sigma).
$$

---

# R.21. Stress test terhadap covariance

Misalkan:

$$
\Sigma.
$$

Kita dapat membuat:

$$
\Sigma'
=
\Sigma+\Delta\Sigma.
$$

Dengan:

$$
\|\Delta\Sigma\|\leq\epsilon.
$$

Kemudian jalankan optimizer.

Jika strategi langsung rusak:

$$
\boxed{
\text{model terlalu sensitif terhadap estimation error}.
}
$$

---

# R.22. Stress test terhadap expected return

Demikian juga:

$$
\mu'
=
\mu+\Delta\mu.
$$

Kemudian:

$$
\|\Delta\mu\|\leq\epsilon.
$$

Kita lihat apakah portfolio/order decision berubah drastis.

---

# R.23. Sensitivity terhadap transaction cost

Misalkan base:

$$
c=0.05\%.
$$

Kemudian:

$$
c\in
\{
0.025\%,
0.05\%,
0.10\%,
0.20\%,
0.50\%
\}.
$$

Kita hitung:

$$
PnL(c).
$$

Jika:

$$
PnL(0.05\%)>0
$$

tetapi:

$$
PnL(0.10\%)<0,
$$

maka edge kita sangat tipis.

---

# R.24. Slippage stress

Demikian juga:

$$
s
\in
\{0.5s_0,s_0,2s_0,3s_0\}.
$$

Kita ingin:

$$
\boxed{
PnL(s)
}
$$

tetap masuk akal.

---

# R.25. Liquidity stress

Kita dapat menurunkan:

$$
Depth
$$

secara artifisial.

Misalnya:

$$
D'=0.5D.
$$

Kemudian:

$$
P_{impact}
$$

akan meningkat.

Jika strategi langsung collapse:

$$
\boxed{
strategy\ liquidity-sensitive.
}
$$

---

# R.26. Monte Carlo return bootstrap

Misalkan kita memiliki trade return:

$$
r_1,\ldots,r_N.
$$

Kita dapat melakukan bootstrap:

$$
r_1^\star,\ldots,r_N^\star
$$

dengan sampling ulang.

Kemudian:

$$
Equity^\star_t.
$$

Ulangi:

$$
B=10\,000.
$$

Kita memperoleh distribusi:

$$
MDD^{(1)},\ldots,MDD^{(B)}.
$$

---

# R.27. Tetapi IID bootstrap tidak selalu cocok

Karena return financial time series mempunyai:

- autocorrelation,
- volatility clustering,
- regime persistence.

Maka lebih baik:

$$
\boxed{
Block\ Bootstrap.
}
$$

---

# R.28. Block bootstrap

Kita membagi return:

$$
R_1,\ldots,R_T
$$

menjadi blok:

$$
B_1,B_2,\ldots,B_K.
$$

Kemudian sampling blok.

Dengan demikian struktur lokal tetap dipertahankan.

---

# R.29. Stationary bootstrap

Alternatif yang lebih fleksibel:

$$
L\sim Geometric(p)
$$

untuk menentukan panjang blok.

Kemudian blok dimulai secara random.

Ini menghasilkan:

$$
\boxed{
Stationary\ Bootstrap.
}
$$

---

# R.30. Yang kita cari bukan hanya confidence interval PnL

Kita ingin:

$$
P(Sharpe>0),
$$

$$
P(MDD<MDD_{max}),
$$

$$
P(Capital>0),
$$

dan:

$$
P(\text{ruin}).
$$

---

# R.31. Probability of ruin

Misalkan capital:

$$
C_0.
$$

Threshold:

$$
C_{min}.
$$

Kita definisikan:

$$
\boxed{
P_{ruin}
=
P\left(
\min_t C_t<C_{min}
\right).
}
$$

Ini jauh lebih berguna daripada sekadar melihat maximum drawdown historis.

---

# R.32. Deflated Sharpe Ratio

Sekarang kita masuk ke alat yang sangat penting.

Sharpe ratio observasi:

$$
SR_{obs}.
$$

Jika kita mencoba banyak strategi, maximum Sharpe yang kita lihat akan cenderung meningkat walaupun tidak ada skill.

Kita perlu memperhitungkan:

$$
\boxed{
selection\ bias.
}
$$

Inilah motivasi:

$$
\boxed{
Deflated\ Sharpe\ Ratio
}
$$

yang secara konseptual menyesuaikan Sharpe berdasarkan:

- number of trials,
- non-normality,
- skewness,
- kurtosis,
- sample length,
- correlation antar strategi.

---

# R.33. Mengapa sangat relevan bagi kita?

Karena kita mungkin mencoba:

$$
QUBO_1,
QUBO_2,
\ldots,
QUBO_N.
$$

Kemudian:

$$
\theta_1,\ldots,\theta_M.
$$

Kemudian:

$$
SL_1,\ldots,SL_K.
$$

Jumlah kombinasi bisa menjadi:

$$
N\times M\times K.
$$

Jika kita kemudian mengambil yang terbaik:

$$
\boxed{
selection\ bias
}
$$

hampir pasti menjadi masalah.

---

# R.34. Effective number of trials

Tidak selalu:

$$
N_{trials}
=
N.
$$

Jika strategi sangat berkorelasi:

$$
\rho_{ij}\approx1,
$$

maka informasi yang diperoleh dari eksperimen tersebut tidak independen.

Kita dapat mempertimbangkan:

$$
\boxed{
N_{eff}.
}
$$

Ini lebih masuk akal daripada sekadar menghitung jumlah file eksperimen.

---

# R.35. Probability of Backtest Overfitting

Salah satu konsep penting berikutnya:

$$
\boxed{
PBO
}
$$

atau:

$$
\boxed{
Probability\ of\ Backtest\ Overfitting.
}
$$

Ide dasarnya:

> Apakah strategi yang kita pilih sebagai pemenang in-sample juga cenderung menjadi pemenang out-of-sample?

Jika tidak:

$$
PBO
$$

tinggi.

---

# R.36. Combinatorial Purged Cross Validation

Untuk time series, kita dapat menggunakan:

$$
\boxed{
CPCV
}
$$

yaitu:

$$
Combinatorial\ Purged\ Cross\ Validation.
$$

Data dibagi menjadi beberapa kelompok temporal.

Kemudian berbagai kombinasi train/test dibuat sambil menerapkan:

$$
purging
$$

dan:

$$
embargo.
$$

---

# R.37. Mengapa ini lebih kuat?

Misalkan kita memiliki:

$$
N=6
$$

fold:

$$
F_1,\ldots,F_6.
$$

Kita tidak hanya mempunyai satu test period.

Kita dapat membuat banyak jalur:

$$
F_1,F_3,F_5
$$

sebagai test pada kombinasi tertentu, misalnya dengan tetap menjaga urutan temporal dan aturan purging.

Akhirnya kita memperoleh distribusi performa OOS.

---

# R.38. White's Reality Check

Sekarang masalah:

> "Saya mencoba banyak strategi. Apakah strategi terbaik saya benar-benar memiliki predictive ability?"

Kita dapat menguji:

$$
H_0:
E[R_i]\leq0
$$

untuk seluruh strategi $i$.

Alternative:

$$
H_1:
\exists i:
E[R_i]>0.
$$

White's Reality Check dirancang untuk memperhitungkan data snooping dalam evaluasi banyak model.

---

# R.39. Hansen's SPA

Alternatif yang juga sangat relevan:

$$
\boxed{
Superior\ Predictive\ Ability
}
$$

atau SPA test.

Pertanyaannya:

> Apakah strategi terbaik benar-benar mengalahkan benchmark setelah memperhitungkan data snooping?

Ini lebih dekat dengan kebutuhan kita daripada hanya:

$$
Sharpe>1.
$$

---

# R.40. Multiple hypothesis testing

Misalkan kita menguji:

$$
H_1,H_2,\ldots,H_m.
$$

Jika masing-masing menggunakan:

$$
\alpha=0.05,
$$

probabilitas setidaknya satu false positive meningkat seiring $m$.

Jika test independen:

$$
P(\text{at least one false positive})
=
1-(1-\alpha)^m.
$$

Untuk:

$$
m=100,
$$

maka:

$$
1-0.95^{100}
\approx99.4\%.
$$

Itulah sebabnya:

$$
p<0.05
$$

sendirian tidak cukup.

---

# R.41. False Discovery Rate

Kita dapat menggunakan:

$$
\boxed{
FDR
}
$$

misalnya prosedur:

$$
Benjamini-Hochberg.
$$

Ini berguna ketika kita mengevaluasi banyak faktor atau banyak hipotesis alpha.

---

# R.42. Tetapi ada satu masalah penting

Dalam trading, kita sering melakukan:

> "Coba parameter."

Kemudian:

> "Tidak bagus."

Coba lagi.

Kemudian:

> "Masih tidak bagus."

Coba lagi.

Sampai:

> "Wow, Sharpe 2.8!"

Secara statistik kita telah melakukan:

$$
\boxed{
implicit\ multiple\ testing.
}
$$

Walaupun kita tidak menulis 1.000 eksperimen secara eksplisit.

---

# R.43. Karena itu experiment registry wajib

Setiap eksperimen harus dicatat:

$$
ExperimentID
$$

$$
DataVersion
$$

$$
FeatureVersion
$$

$$
ModelVersion
$$

$$
ParameterSet
$$

$$
Seed
$$

$$
Timestamp.
$$

---

# R.44. Jangan menghapus eksperimen buruk

Ini penting.

Jika:

$$
E_1:\ Sharpe=-0.3
$$

$$
E_2:\ Sharpe=0.2
$$

$$
E_3:\ Sharpe=2.1
$$

kita tidak boleh hanya menyimpan:

$$
E_3.
$$

Karena jumlah percobaan:

$$
N_{trials}=3.
$$

bukan:

$$
1.
$$

---

# R.45. Ini juga berlaku untuk QAOA

Misalnya kita menguji:

$$
p\in\{1,2,3,4,5\}
$$

dan:

$$
\beta,\gamma
$$

dengan banyak kombinasi.

Jika kita memilih kombinasi yang menghasilkan PnL terbesar:

$$
(\beta^\star,\gamma^\star,p^\star),
$$

maka pencarian tersebut sendiri adalah:

$$
\boxed{
model\ selection.
}
$$

Harus dihitung sebagai bagian dari trial history.

---

# R.46. Bahkan ansatz adalah hyperparameter

Misalnya:

$$
EfficientSU2
$$

vs.

$$
UCC
$$

vs.

$$
hardware-efficient.
$$

Jika kita mencoba semuanya lalu memilih yang terbaik, itu juga:

$$
multiple\ testing.
$$

---

# R.47. Dan optimizer

Misalnya:

$$
SPSA,
$$

$$
Adam,
$$

$$
COBYLA,
$$

$$
Nelder-Mead.
$$

Pemilihan optimizer berdasarkan hasil test juga merupakan:

$$
model selection.
$$

---

# R.48. Kita perlu membedakan tiga dataset

Ini sangat penting.

$$
\boxed{
Training
}
$$

digunakan untuk:

$$
fit.
$$

$$
\boxed{
Validation
}
$$

digunakan untuk:

$$
model\ selection.
$$

$$
\boxed{
Test
}
$$

digunakan hanya untuk:

$$
final\ evaluation.
$$

---

# R.49. Test set adalah "vault"

Idealnya:

$$
\boxed{
\text{Test set tidak disentuh sampai model dibekukan.}
}
$$

Jika kita melihat hasil test kemudian mengubah model:

$$
Test
\rightarrow
Training.
$$

---

# R.50. Final evaluation

Setelah model benar-benar dibekukan:

$$
\boxed{
\theta_{final}
}
$$

baru kita jalankan:

$$
Test_{final}.
$$

Dan tidak boleh melakukan tuning lagi berdasarkan hasil tersebut.

---

# R.51. Statistical significance

Misalkan rata-rata trade return:

$$
\bar r.
$$

Sample standard deviation:

$$
s.
$$

Standard error sederhana:

$$
SE(\bar r)=\frac{s}{\sqrt N}.
$$

Test statistic:

$$
t=
\frac{\bar r}{SE(\bar r)}.
$$

Tetapi financial returns sering:

- non-normal,
- autocorrelated,
- heteroskedastic.

Jadi asumsi sederhana ini harus diperlakukan hati-hati.

---

# R.52. HAC / Newey-West

Jika terdapat autocorrelation, variance estimator dapat diperbaiki menggunakan:

$$
\boxed{
Heteroskedasticity\ and\ Autocorrelation\ Consistent
}
$$

atau HAC.

Ini memungkinkan standard error lebih realistis.

---

# R.53. Sharpe juga memiliki masalah

Standard Sharpe:

$$
SR=\frac{\bar r}{s}.
$$

Jika return non-normal, Sharpe tidak sepenuhnya menggambarkan risk.

Kita harus memperhatikan:

$$
Skewness
$$

dan:

$$
Kurtosis.
$$

---

# R.54. Tail risk

Kita dapat mengukur:

$$
VaR_\alpha.
$$

Misalnya:

$$
VaR_{95\%}.
$$

Tetapi saya lebih menyukai:

$$
\boxed{
CVaR
}
$$

atau Expected Shortfall:

$$
ES_\alpha
=
E[L|L\ge VaR_\alpha].
$$

---

# R.55. Mengapa?

VaR menjawab:

> "Pada quantile 95%, seberapa besar loss?"

Sedangkan ES menjawab:

> "Jika kita sudah masuk 5% kejadian terburuk, rata-rata loss-nya berapa?"

Untuk tail-heavy financial distributions, ini sangat penting.

---

# R.56. Drawdown distribution

Jangan hanya:

$$
MDD.
$$

Kita juga dapat melihat:

$$
Duration_{DD},
$$

$$
RecoveryTime,
$$

$$
AverageDD,
$$

$$
ExpectedDD.
$$

Karena:

$$
MDD=10\%
$$

selama 2 hari berbeda dengan:

$$
MDD=10\%
$$

selama 8 bulan.

---

# R.57. Recovery time

Misalkan equity mencapai peak:

$$
E_{peak}.
$$

Kemudian turun.

Recovery time:

$$
\boxed{
T_{recover}
=
t_{new\ peak}
-
t_{drawdown}.
}
$$

Ini sangat penting untuk strategi short-term yang mungkin memiliki banyak drawdown kecil.

---

# R.58. Capacity analysis

Ini satu hal yang sangat sering dilupakan.

Jika strategy menghasilkan:

$$
\$100
$$

profit dengan:

$$
\$1,000
$$

capital, bagus.

Tetapi apakah bisa:

$$
\$10,000,000?
$$

Belum tentu.

Karena:

$$
MarketImpact(q)
$$

meningkat dengan:

$$
q.
$$

---

# R.59. Impact model

Secara sederhana:

$$
\boxed{
Impact(q)
=
\eta\sigma
\left(
\frac{q}{V}
\right)^\alpha
}
$$

dengan:

- $q$: order size,
- $V$: market volume,
- $\sigma$: volatility,
- $\eta,\alpha$: parameter.

---

# R.60. Capacity

Kita dapat mencari:

$$
q^\star
$$

sehingga:

$$
ExpectedAlpha(q^\star)
=
TransactionCost(q^\star).
$$

Di atas:

$$
q>q^\star,
$$

strategy tidak lagi economic.

Jadi:

$$
\boxed{
Capacity
}
$$

adalah bagian dari robustness.

---

# R.61. Latency stress

Untuk short-term trading, kita juga harus menguji:

$$
\tau
$$

sebagai latency.

Misalnya:

$$
\tau
\in
\{0,10,50,100,500\}\ ms.
$$

Kemudian:

$$
PnL(\tau).
$$

Jika edge hilang pada:

$$
\tau=50ms,
$$

strategi kita mungkin membutuhkan infrastructure yang sangat cepat.

---

# R.62. Execution degradation curve

Kita dapat mendefinisikan:

$$
\boxed{
D(\tau)
=
PnL(0)-PnL(\tau).
}
$$

Ini memberikan gambaran:

> seberapa cepat alpha kita decay.

---

# R.63. Alpha half-life

Misalkan signal:

$$
S_t.
$$

Autocorrelation:

$$
\rho(k).
$$

Kita dapat mencari:

$$
k_{1/2}
$$

ketika:

$$
\rho(k_{1/2})\approx0.5.
$$

Itulah pendekatan sederhana untuk:

$$
\boxed{
Alpha\ Half-Life.
}
$$

Jika half-life sangat pendek, execution menjadi kritikal.

---

# R.64. Ini menghubungkan Tahap R dengan Tahap Q

Tahap Q:

$$
\text{execution simulation}.
$$

Tahap R:

$$
\text{berapa sensitif hasil terhadap execution assumptions?}
$$

Jadi:

$$
\boxed{
Q\rightarrow R
}
$$

secara alami.

---

# R.65. Robustness terhadap universe

Misalnya awalnya:

$$
Universe=
\{BTC,ETH,SOL,\ldots\}.
$$

Kita harus menguji:

$$
Universe_1,
Universe_2,
Universe_3.
$$

Jika strategi hanya bekerja pada satu subset yang dipilih setelah melihat hasil:

$$
\boxed{
selection bias.
}
$$

---

# R.66. Cross-market validation

Karena tujuan kita bukan hanya crypto, kita dapat menguji:

$$
Crypto
$$

$$
US\ Equities
$$

$$
European\ Equities
$$

$$
Asian\ Equities
$$

$$
FX
$$

jika data dan execution model mendukung.

---

# R.67. Tetapi hati-hati

Kita tidak boleh mengatakan:

> "Model bekerja di BTC, maka pasti bekerja di saham."

Justru kita harus menguji apakah struktur matematisnya transferable.

Misalnya:

$$
\text{factor model}
$$

mungkin transferable.

Tetapi:

$$
\text{microstructure}
$$

jelas berbeda.

---

# R.68. Hierarchical robustness

Saya ingin robustness kita dibagi menjadi empat tingkat:

### Level 1 — Statistical

$$
\text{Significance}
$$

### Level 2 — Temporal

$$
\text{OOS / Walk-forward}
$$

### Level 3 — Market

$$
\text{Regime / Asset / Geography}
$$

### Level 4 — Operational

$$
\text{Fees / Slippage / Latency / Liquidity}.
$$

Jika model melewati keempatnya, tingkat kepercayaan jauh lebih tinggi.

---

# R.69. Robustness score

Kita bahkan dapat membangun dashboard internal:

$$
R_{score}
=
w_1R_{stat}
+w_2R_{temporal}
+w_3R_{market}
+w_4R_{operational}.
$$

Tetapi **jangan menggunakan skor ini sebagai pengganti statistical test**.

Ini hanya alat ringkasan.

---

# R.70. Stress matrix

Saya menyarankan kita membuat:

| Stress | Parameter |
|---|---|
| Cost | $1-5\times$ |
| Slippage | $1-5\times$ |
| Latency | $0-500ms+$ |
| Liquidity | $0.1-1.0\times$ |
| Volatility | $0.5-3\times$ |
| Factor error | $\pm\epsilon$ |
| Covariance error | $\pm\Delta\Sigma$ |
| Fill probability | $\pm\epsilon$ |

Kemudian:

$$
Performance
=
f(
Cost,
Slippage,
Latency,
Liquidity,\ldots
).
$$

---

# R.71. Yang kita cari bukan "profit maksimum"

Kita ingin:

$$
\boxed{
\text{Stable Positive Region}
}
$$

dalam ruang parameter.

Secara visual:

```text
Performance
    ^
    │       ███████
    │     ███████████
    │    █████████████
    │     ███████████
    │       ███████
    │
    └──────────────────> parameter
```

Bukan:

```text
Performance
    ^
    │            █
    │            █
    │            █
    │____________████________
    └───────────────────────>
```

---

# R.72. Dari sini kita bisa mendefinisikan "robust alpha"

Saya mengusulkan definisi operasional:

$$
\boxed{
\text{Robust Alpha}
=
\text{Positive OOS Edge}
+
\text{Statistical Evidence}
+
\text{Parameter Stability}
+
\text{Regime Robustness}
+
\text{Execution Robustness}.
}
$$

Ini jauh lebih kuat daripada:

$$
Sharpe>2.
$$

---

# R.73. Dan sekarang bagian yang sangat penting untuk quantum

Kita memiliki tiga hipotesis berbeda.

### H1 — Optimization hypothesis

> Apakah QAOA mampu menyelesaikan formulasi optimasi dengan kualitas yang memadai?

### H2 — Trading hypothesis

> Apakah formulasi optimasi tersebut menghasilkan keputusan trading yang memiliki edge?

### H3 — Quantum advantage hypothesis

> Apakah QAOA memberikan nilai ekonomi atau komputasional yang tidak diperoleh classical optimizer?

Ketiganya:

$$
\boxed{
\text{bukan hipotesis yang sama}.
}
$$

---

# R.74. Ini mencegah kesalahan besar

Misalkan:

$$
QAOA
$$

menghasilkan solusi bagus.

Itu membuktikan:

$$
H_1.
$$

Belum membuktikan:

$$
H_2.
$$

Dan bahkan jika:

$$
H_2
$$

benar, belum membuktikan:

$$
H_3.
$$

---

# R.75. Quantum comparison matrix

Kita akhirnya akan membandingkan:

| Model | Solution Quality | Runtime | PnL | Sharpe | MDD | Cost |
|---|---:|---:|---:|---:|---:|---:|
| Exact | 100% | — | — | — | — | — |
| Classical | — | — | — | — | — | — |
| QAOA | — | — | — | — | — | — |

Dan:

$$
\boxed{
Economic\ Value
}
$$

harus menjadi salah satu kolom utama.

---

# R.76. "Quantum advantage" yang realistis

Saya tidak ingin kita mendefinisikan:

$$
Quantum\ Advantage
=
PnL_{QAOA}>PnL_{classical}.
$$

Itu definisi yang buruk.

Karena optimizer yang berbeda bisa menghasilkan keputusan berbeda akibat stochasticity.

Lebih masuk akal:

$$
\boxed{
Quantum\ Advantage
=
f(
solution\ quality,
runtime,
scalability,
economic\ value
).
}
$$

---

# R.77. Scaling test

Misalnya jumlah aset:

$$
N=4,8,12,16,20,\ldots
$$

Kita ukur:

$$
T_{classical}(N)
$$

dan:

$$
T_{QAOA}(N).
$$

Juga:

$$
Gap(N).
$$

Maka kita memperoleh:

$$
\boxed{
Scaling\ Curve.
}
$$

---

# R.78. Ini mungkin menjadi kontribusi ilmiah yang lebih kuat

Daripada:

> "Saya menggunakan QAOA untuk trading dan menghasilkan profit."

Lebih ilmiah jika:

> "Kami mengevaluasi hubungan antara approximation quality, computational cost, dan economic degradation pada dynamic financial optimization problem di bawah realistic transaction-cost and execution constraints."

Itu sudah menjadi penelitian yang jauh lebih serius.

---

# R.79. Statistical validation pipeline final

Saya ingin Tahap R kita akhirnya berbentuk:

```text
RAW DATA
   │
   ▼
TEMPORAL SPLIT
   │
   ▼
PURGED WALK-FORWARD
   │
   ▼
MODEL TRAINING
   │
   ▼
VALIDATION
   │
   ▼
MODEL SELECTION
   │
   ▼
MODEL FREEZE
   │
   ▼
FINAL OOS TEST
   │
   ├───────────────┐
   ▼               ▼
BOOTSTRAP       STRESS TEST
   │               │
   ▼               ▼
CONFIDENCE      ROBUSTNESS
INTERVAL        ANALYSIS
   │               │
   └───────┬───────┘
           ▼
   MULTIPLE TESTING
           │
           ▼
     DSR / PBO / SPA
           │
           ▼
     FINAL EVIDENCE
```

---

# R.80. Decision gate

Setelah Tahap R, saya ingin sistem kita mempunyai **gate**.

Misalnya:

$$
G_{stat}
$$

untuk statistical evidence,

$$
G_{OOS}
$$

untuk out-of-sample,

$$
G_{robust}
$$

untuk robustness,

dan:

$$
G_{execution}
$$

untuk execution.

Kemudian:

$$
\boxed{
Deploy
=
G_{stat}
\land
G_{OOS}
\land
G_{robust}
\land
G_{execution}.
}
$$

Kalau salah satu gagal:

$$
\boxed{
NO\ LIVE\ DEPLOYMENT.
}
$$

---

# R.81. Saya bahkan menyarankan tiga status

### RED

$$
\boxed{
Insufficient\ Evidence
}
$$

Strategi belum boleh dipakai.

### YELLOW

$$
\boxed{
Promising\ but\ Uncertain
}
$$

Lanjutkan penelitian/paper trading.

### GREEN

$$
\boxed{
Robust\ OOS\ Evidence
}
$$

Baru boleh masuk tahap paper/live dengan risk limit yang sangat kecil.

---

# R.82. Dan ini sangat cocok dengan filosofi \$1 risk kita

Risk budget tetap:

$$
\boxed{
R_{trade}\leq \$1.
}
$$

Tetapi sekarang kita menambahkan:

$$
\boxed{
R_{model}
}
$$

dan:

$$
\boxed{
R_{execution}.
}
$$

Jadi:

$$
TotalRisk
\neq
Risk_{trade}
$$

saja.

Kita memiliki:

$$
\boxed{
Total\ System\ Risk
=
Market
+
Model
+
Execution
+
Liquidity
+
Operational.
}
$$

---

# R.83. Model risk

Misalnya:

$$
\hat\mu
$$

salah.

Maka:

$$
QUBO
$$

dapat menghasilkan keputusan yang salah.

Jadi:

$$
\boxed{
Model\ uncertainty
\rightarrow
Decision\ uncertainty.
}
$$

Ini harus masuk dalam stress testing.

---

# R.84. Decision uncertainty

Jika dua solusi memiliki objective yang hampir sama:

$$
E(x_1)\approx E(x_2),
$$

tetapi keputusan trading sangat berbeda:

$$
x_1\neq x_2,
$$

maka sistem tidak boleh terlalu percaya diri.

Kita dapat mendefinisikan:

$$
\Delta E
=
|E(x_1)-E(x_2)|.
$$

Jika:

$$
\Delta E\ll\epsilon,
$$

kita berada di daerah:

$$
\boxed{
Optimization\ Indifference.
}
$$

---

# R.85. Ini membuka jalan untuk tahap berikutnya

Karena jika beberapa solusi hampir sama:

$$
x_1,x_2,\ldots,x_k,
$$

kita tidak harus selalu memilih:

$$
x^\star.
$$

Kita bisa membangun:

$$
\boxed{
solution\ ensemble.
}
$$

atau bahkan:

$$
P(x)
$$

sebagai distribusi keputusan.

Ini akan sangat menarik jika dikombinasikan dengan output probabilistik QAOA.

---

# R.86. Dan di sinilah proyek kita mulai menjadi jauh lebih dalam

Kita awalnya ingin:

$$
\text{Trading Bot}.
$$

Sekarang arsitektur kita telah berkembang menjadi:

$$
\boxed{
\text{Statistical Decision System under Uncertainty}
}
$$

dengan:

$$
\underbrace{\text{Market Uncertainty}}_{\epsilon_M}
$$

$$
\underbrace{\text{Model Uncertainty}}_{\epsilon_\theta}
$$

$$
\underbrace{\text{Optimization Uncertainty}}_{\epsilon_Q}
$$

$$
\underbrace{\text{Execution Uncertainty}}_{\epsilon_E}.
$$

Dan keputusan:

$$
A_t
$$

harus tetap robust terhadap keempatnya.

---

# R.87. Target akhir Tahap R

Pada akhir Tahap R, kita seharusnya tidak lagi bertanya:

> **"Apakah backtest menghasilkan profit?"**

Pertanyaan kita berubah menjadi:

> **"Seberapa kuat bukti bahwa expected economic edge tetap positif ketika kita memperhitungkan temporal dependence, multiple testing, model uncertainty, regime changes, transaction costs, execution uncertainty, dan optimization error?"**

Secara matematis:

$$
\boxed{
P\left(
E[R_{OOS}]
>
0
\mid
\mathcal D,
\mathcal M,
\mathcal E
\right)
}
$$

harus cukup tinggi, dengan:

- $\mathcal D$: data,
- $\mathcal M$: model assumptions,
- $\mathcal E$: execution assumptions.

Dan bahkan itu belum berarti kita "membuktikan profit". Yang kita dapatkan adalah **evidence yang lebih kuat atau lebih lemah** terhadap adanya edge.

---

## Posisi kita setelah Tahap R

Kita sekarang memiliki:

$$
\boxed{
A-P:
\text{Mathematical Trading System}
}
$$

$$
\boxed{
Q:
\text{Event-Driven Market Simulator}
}
$$

$$
\boxed{
R:
\text{Statistical Validation \& Robustness}
}
$$

Sehingga pipeline besarnya menjadi:

$$
\boxed{
\text{Market Data}
\rightarrow
\text{State Estimation}
\rightarrow
\text{Alpha}
\rightarrow
\text{Optimization}
\rightarrow
\text{Execution}
\rightarrow
\text{Simulation}
\rightarrow
\text{Statistical Validation}
}
$$

Dan menurut saya, **Tahap S berikutnya sebaiknya bukan langsung masuk live trading**. Kita perlu membangun **S — Portfolio/Strategy Ensemble & Capital Allocation**, yaitu bagaimana beberapa strategi/optimizer/factor model yang masing-masing telah lolos validasi R digabungkan secara matematis menjadi satu *meta-portfolio*, termasuk korelasi antar-strategi, risk budgeting, Kelly/fractional Kelly, hierarchical risk parity, regime-dependent allocation, dan—yang sangat cocok dengan arah penelitian kita—**formulasi capital allocation tersebut sebagai QUBO/Ising problem**.

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

## Prompt:
8/17/2026, 10:06:15 PM

lanjut Tahap T

## Response:
8/17/2026, 10:06:16 PM

# Tahap T — Portfolio-to-Order Translation & Dynamic Position Sizing

Ya. **Tahap T adalah salah satu tahap paling penting**, karena di sinilah seluruh lapisan matematika yang kita bangun sebelumnya akhirnya diterjemahkan menjadi keputusan trading konkret:

$$
\boxed{
\text{Market State}
\rightarrow
\text{Alpha}
\rightarrow
\text{Strategy}
\rightarrow
\text{Capital Allocation}
\rightarrow
\text{Position}
\rightarrow
\text{Order}
}
$$

Dan saya ingin mempertahankan prinsip yang sudah kita bangun:

> **Optimizer tidak menentukan order secara langsung.**  
> Optimizer menentukan *berapa banyak risk/capital yang layak diberikan kepada suatu opportunity*.  
> Execution engine kemudian menentukan bagaimana risk tersebut diwujudkan menjadi entry, SL, TP, dan order management.

Ini penting agar arsitektur kita tidak menjadi satu model besar yang sulit diuji.

---

# T.1. Hirarki keputusan

Kita sekarang mempunyai lima level:

$$
\boxed{
\begin{aligned}
\text{Level 1: Market State} &\rightarrow Z_t\\
\text{Level 2: Strategy Allocation} &\rightarrow w_{s,t}\\
\text{Level 3: Trade Allocation} &\rightarrow R_{i,t}\\
\text{Level 4: Position Sizing} &\rightarrow q_{i,t}\\
\text{Level 5: Order Execution} &\rightarrow O_{i,t}
\end{aligned}
}
$$

Misalnya:

$$
C_t=\$10,000.
$$

Capital allocator mengatakan:

$$
w_{strategy}=20\%.
$$

Maka:

$$
C_{strategy}=\$2,000.
$$

Tetapi itu **belum berarti membeli aset senilai \$2,000**.

Strategy kemudian menghasilkan sebuah trade opportunity dengan risk budget:

$$
R_{trade}=\$1.
$$

Barulah position-sizing engine menentukan jumlah aset.

---

# T.2. Risk budget sebagai mata uang universal

Saya menyarankan kita menjadikan **risk** sebagai bahasa penghubung seluruh sistem.

Bukan:

> "Strategi A mendapatkan \$2,000."

Tetapi:

> "Strategi A mendapatkan risk budget sebesar $R_A$."

Misalnya:

$$
R_A=\$10/day.
$$

Sebuah trade kemudian mendapatkan:

$$
R_{trade}=\$1.
$$

Maka secara kasar:

$$
N_{trade,max}
=
\frac{R_A}{R_{trade}}
=
10.
$$

Namun jumlah aktual tetap harus memperhitungkan correlation dan portfolio risk.

---

# T.3. Trade risk

Untuk sebuah posisi long:

$$
P_e=\text{entry price},
$$

$$
P_{SL}=\text{stop-loss price},
$$

$$
q=\text{quantity}.
$$

Gross loss jika SL terkena:

$$
L_{SL}
=
q(P_e-P_{SL}).
$$

Jika ada biaya:

$$
F_e,\quad F_{SL},
$$

dan expected slippage:

$$
S_e,\quad S_{SL},
$$

maka:

$$
\boxed{
R_{trade}
=
q
\left[
(P_e-P_{SL})
+
S_e+S_{SL}
\right]
+
F_e+F_{SL}.
}
$$

Untuk short, tanda harga dibalik.

---

# T.4. Position sizing

Kita ingin:

$$
R_{trade}\le R_{budget}.
$$

Sehingga:

$$
q
\le
\frac{
R_{budget}-F_e-F_{SL}
}{
|P_e-P_{SL}|+S_e+S_{SL}
}.
$$

Jadi:

$$
\boxed{
q_{risk}
=
\frac{
R_{budget}-F
}{
D_{SL}+S
}
}
$$

dengan:

$$
D_{SL}=|P_e-P_{SL}|.
$$

Ini merupakan **position sizing engine paling dasar**.

---

# T.5. Tetapi kita tidak boleh berhenti di sini

Karena:

$$
q_{risk}
$$

belum mempertimbangkan:

- liquidity,
- market impact,
- portfolio exposure,
- correlation,
- factor exposure,
- leverage,
- confidence,
- regime.

Maka quantity final harus:

$$
\boxed{
q_{final}
=
\min
(
q_{risk},
q_{liquidity},
q_{portfolio},
q_{leverage},
q_{capacity}
).
}
$$

---

# T.6. Stop-loss tidak boleh menentukan risk budget

Ini prinsip penting.

Urutannya bukan:

$$
SL
\rightarrow
Risk.
$$

Tetapi:

$$
\boxed{
Risk
\rightarrow
SL
\rightarrow
Position Size.
}
$$

Mengapa?

Karena kita terlebih dahulu menentukan:

> "Berapa kerugian maksimum yang bersedia diterima?"

Kemudian menentukan struktur trade yang masuk akal.

---

# T.7. Menentukan Stop Loss

SL sebaiknya bukan angka arbitrer.

Kita dapat menggunakan kombinasi:

### Volatility

$$
D_{SL}
=
k\sigma_{ATR}.
$$

Misalnya:

$$
D_{SL}=2ATR.
$$

### Market structure

$$
P_{SL}
=
P_{swing\ low}-\epsilon.
$$

### Statistical boundary

Misalnya:

$$
P_{SL}
=
P_e-z_\alpha\sigma_h.
$$

---

# T.8. Model SL gabungan

Misalnya kita memiliki tiga estimasi:

$$
D_{vol},
$$

$$
D_{structure},
$$

$$
D_{stat}.
$$

Kita dapat menggunakan:

$$
\boxed{
D_{SL}
=
\max
(
D_{vol},
D_{structure},
D_{stat}
).
}
$$

Tujuannya agar SL tidak terlalu dekat sehingga terkena noise.

---

# T.9. Tetapi ada trade-off

SL semakin jauh:

$$
D_{SL}\uparrow
$$

maka:

$$
q_{risk}\downarrow.
$$

Karena:

$$
q_{risk}
\propto
\frac1{D_{SL}}.
$$

Jadi volatility tinggi secara otomatis menyebabkan:

$$
\boxed{
position\ size\downarrow.
}
$$

Ini jauh lebih masuk akal daripada selalu membeli jumlah aset yang sama.

---

# T.10. Take Profit

Sekarang kita menentukan TP.

Definisikan:

$$
D_{TP}=|P_{TP}-P_e|.
$$

Risk distance:

$$
D_{SL}=|P_e-P_{SL}|.
$$

Risk-reward ratio:

$$
\boxed{
RR=
\frac{D_{TP}}{D_{SL}}.
}
$$

---

# T.11. Tetapi TP seharusnya berasal dari expected distribution

Ini lebih menarik.

Misalkan model kita memperkirakan:

$$
R_{future}\sim
\mathcal D(\theta).
$$

Kita ingin memilih TP:

$$
P_{TP}
$$

berdasarkan distribusi return, bukan sekadar:

$$
TP=2\times SL.
$$

---

# T.12. Expected value

Misalkan:

$$
p_w=P(\text{TP hit}),
$$

$$
p_l=P(\text{SL hit}),
$$

dan:

$$
p_n=1-p_w-p_l.
$$

Dengan payoff:

$$
G=TP-entry,
$$

$$
L=entry-SL.
$$

Expected PnL:

$$
\boxed{
E[PnL]
=
p_wG-p_lL+E[PnL|neutral]p_n.
}
$$

Jika neutral diabaikan:

$$
E[PnL]
=
p_wG-p_lL.
$$

---

# T.13. Break-even probability

Jika:

$$
E[PnL]>0,
$$

maka:

$$
p_wG>p_lL.
$$

Jika hanya dua outcome:

$$
p_l=1-p_w.
$$

Maka:

$$
p_wG>(1-p_w)L.
$$

Sehingga:

$$
p_w(G+L)>L.
$$

Jadi:

$$
\boxed{
p_w>
\frac{L}{G+L}.
}
$$

Untuk:

$$
RR=\frac{G}{L},
$$

maka:

$$
\boxed{
p_w>\frac1{1+RR}.
}
$$

---

# T.14. Contoh

Jika:

$$
RR=2,
$$

maka:

$$
p_w>\frac13.
$$

Jadi win rate hanya:

$$
33.3\%
$$

sudah cukup secara teoritis sebelum biaya dan slippage.

Tetapi tentu model harus menghasilkan probability yang *out-of-sample calibrated*.

---

# T.15. Expected utility

Kita bisa menjadi lebih sophisticated.

Daripada:

$$
\max E[PnL],
$$

gunakan utility:

$$
\boxed{
U(W)
=
E[W]
-
\frac{\lambda}{2}Var(W).
}
$$

Untuk trade:

$$
U
=
E[R]
-
\frac{\lambda}{2}Var(R).
$$

Maka TP dipilih untuk:

$$
\boxed{
TP^\star
=
\arg\max_{TP}
U(TP).
}
$$

---

# T.16. Ini membuat TP menjadi optimization problem

Bukan:

```text
TP = 2 × SL
```

tetapi:

$$
\boxed{
TP^\star
=
\arg\max_{TP}
\left[
E[PnL(TP)]
-
\frac{\lambda}{2}
Var(PnL(TP))
-
Cost(TP)
\right].
}
$$

Ini jauh lebih sesuai dengan sistem kita.

---

# T.17. Sekarang masalah yang kamu tanyakan sebelumnya

> Jika posisi sudah floating profit tinggi, apakah TP dinaikkan?

Jawabannya:

**bisa, tetapi bukan karena profitnya tinggi.**

Kita harus bertanya:

$$
\boxed{
\text{Apakah conditional expected return masih positif?}
}
$$

---

# T.18. Conditional expected return

Misalkan posisi sudah menghasilkan:

$$
P_t>P_e.
$$

State sekarang:

$$
S_t.
$$

Model menghitung:

$$
E[R_{t:t+H}|S_t].
$$

Jika:

$$
E[R_{future}|S_t]>0,
$$

maka posisi masih memiliki expected edge.

Jika:

$$
E[R_{future}|S_t]\approx0,
$$

maka tidak ada alasan kuat untuk mempertahankannya.

Jika:

$$
E[R_{future}|S_t]<0,
$$

maka exit mungkin lebih rasional.

---

# T.19. Ini menghasilkan prinsip penting

Jangan menggunakan:

$$
\text{floating profit}
$$

sebagai signal utama.

Gunakan:

$$
\boxed{
\text{future conditional edge}.
}
$$

Floating profit hanya merupakan bagian dari state.

---

# T.20. State posisi

Kita definisikan:

$$
X_t=
[
P_t,
P_e,
SL_t,
TP_t,
MFE_t,
MAE_t,
\tau_t,
\sigma_t,
\hat\mu_t,
Z_t,
L_t
].
$$

Dengan:

- $MFE$: maximum favorable excursion,
- $MAE$: maximum adverse excursion,
- $\tau_t$: holding time,
- $Z_t$: regime,
- $L_t$: liquidity.

---

# T.21. Dynamic Stop Loss

Kita definisikan:

$$
SL_t=f(X_t).
$$

Tetapi kita harus menghindari:

$$
SL_t
$$

yang terus bergerak mengikuti harga tanpa alasan statistik.

---

# T.22. Break-even transition

Misalnya:

$$
R_t
=
\frac{P_t-P_e}
{P_e-P_{SL,0}}.
$$

Jika:

$$
R_t\ge r_{BE},
$$

maka SL dapat dipindahkan ke:

$$
SL_t=P_e+c
$$

dengan $c$ memperhitungkan fees/slippage.

---

# T.23. Contoh

Initial:

$$
P_e=100.
$$

SL:

$$
95.
$$

Risk:

$$
5.
$$

Jika harga:

$$
P_t=105,
$$

maka:

$$
R_t=1R.
$$

Kita dapat memindahkan:

$$
SL=100
$$

atau sedikit di atas:

$$
SL=100+\epsilon.
$$

---

# T.24. Tetapi BEP terlalu agresif

Masalah:

$$
SL=entry
$$

membuat trade sangat mudah keluar akibat noise.

Jadi kita dapat menggunakan:

$$
SL_t
=
P_e+
\alpha ATR_t.
$$

Misalnya:

$$
\alpha=0.2.
$$

Untuk long:

$$
SL_t=P_e+0.2ATR_t.
$$

---

# T.25. Trailing stop berbasis volatility

Alternatif:

$$
\boxed{
SL_t
=
P_t-k\sigma_t
}
$$

untuk long.

Dan:

$$
\boxed{
SL_t
=
P_t+k\sigma_t
}
$$

untuk short.

Tetapi:

$$
k
$$

harus dikalibrasi menggunakan data OOS.

---

# T.26. Bahkan lebih baik: trailing stop berdasarkan distribution

Misalkan model menghasilkan:

$$
P(R_{t+h}<-\delta|S_t).
$$

Kita ingin SL berada pada quantile tertentu:

$$
\boxed{
P(R_{future}< -D_{SL}|S_t)
=
\alpha.
}
$$

Sehingga:

$$
D_{SL}
=
Quantile_{\alpha}
(
-Loss_{future}|S_t
).
$$

Ini menghasilkan **probabilistic stop-loss**.

---

# T.27. TP dinamis

Demikian pula:

$$
TP_t
=
f(
P_t,
S_t,
\hat\mu_t,
\hat\sigma_t,
Z_t
).
$$

Kita dapat menentukan:

$$
TP_t^\star
=
\arg\max_{TP}
E[U|S_t].
$$

---

# T.28. Tetapi TP tidak boleh terus dinaikkan

Misalkan:

$$
TP_0=110.
$$

Harga:

$$
P_t=108.
$$

Model baru mengatakan target optimal:

$$
TP^\star=109.
$$

Maka kita **tidak** menaikkan TP menjadi 115 hanya karena harga sedang profit.

Kita justru menurunkannya.

Jadi:

$$
\boxed{
TP_t
=
\text{model-driven},
}
$$

bukan:

$$
\text{profit-driven}.
$$

---

# T.29. Ini memberi kita tiga aksi

Pada setiap evaluation period:

$$
a_t
\in
\{
HOLD,
MODIFY,
EXIT
\}.
$$

### HOLD

Jika:

$$
E[R_{future}|S_t]>threshold.
$$

### MODIFY

Jika:

$$
E[R_{future}|S_t]>0
$$

tetapi optimal:

$$
SL_t^\star\ne SL_{t-1}
$$

atau:

$$
TP_t^\star\ne TP_{t-1}.
$$

### EXIT

Jika:

$$
E[R_{future}|S_t]\le0.
$$

---

# T.30. Ini sebenarnya adalah optimal stopping problem

Secara matematis:

$$
\boxed{
\tau^\star
=
\inf
\{
t:
V(S_t)\le E_{exit}(S_t)
\}.
}
$$

Dengan:

$$
V(S_t)
$$

sebagai continuation value.

---

# T.31. Continuation value

Kita dapat mendefinisikan:

$$
V_t
=
E[
U(W_{t+\Delta})
\mid S_t,
\text{continue}
].
$$

Exit value:

$$
E_t^{exit}
=
U(W_t-C_{exit}).
$$

Maka:

$$
\boxed{
\text{Continue}
\iff
V_t>E_t^{exit}.
}
$$

Ini jauh lebih fundamental daripada aturan:

> "Kalau floating profit, geser SL."

---

# T.32. Holding time juga penting

Misalkan trade sudah berjalan:

$$
\tau=3\text{ jam}.
$$

Model awal memprediksi edge dalam:

$$
H=2\text{ jam}.
$$

Jika setelah 3 jam target belum tercapai:

$$
P(TP|\tau)
$$

mungkin sudah turun.

Ini disebut **time decay of alpha**.

---

# T.33. Hazard function

Kita dapat mendefinisikan:

$$
h_{TP}(t)
=
\lim_{\Delta t\rightarrow0}
\frac{
P(t\le T_{TP}<t+\Delta t
\mid T_{TP}\ge t)
}{\Delta t}.
$$

Jika:

$$
h_{TP}(t)
$$

menurun secara signifikan, continuation probability juga turun.

---

# T.34. Maximum holding time

Kita dapat menentukan:

$$
\tau_{max}
$$

dengan:

$$
E[R_{future}|S_t,\tau]
<
threshold.
$$

Maka:

$$
\boxed{
\tau>\tau_{max}
\Rightarrow EXIT.
}
$$

---

# T.35. Sekarang portfolio interaction

Ini sangat penting.

Misalkan kita memiliki:

$$
Trade_A=BTC
$$

dan:

$$
Trade_B=ETH.
$$

Keduanya floating profit.

Trade A memiliki:

$$
+\$3.
$$

Trade B:

$$
+\$2.
$$

Tetapi market suddenly masuk regime:

$$
HighVol.
$$

Correlation:

$$
\rho_{BTC,ETH}\uparrow.
$$

Portfolio risk meningkat.

Maka mungkin kita tidak mempertahankan keduanya.

---

# T.36. Portfolio-level position management

Kita harus menghitung:

$$
\boxed{
\sigma_{portfolio,t}
=
\sqrt{
\mathbf q_t^T
\Sigma_t
\mathbf q_t
}.
}
$$

Jika:

$$
\sigma_{portfolio,t}>B_t,
$$

maka kita harus melakukan **risk reduction**.

---

# T.37. Trade selection saat risk budget penuh

Misalkan terdapat tiga posisi:

$$
A,B,C.
$$

Risk contributions:

$$
RC_A=40\%,
$$

$$
RC_B=35\%,
$$

$$
RC_C=25\%.
$$

Tetapi expected future alpha:

$$
\alpha_A=0.1,
$$

$$
\alpha_B=0.5,
$$

$$
\alpha_C=0.3.
$$

Jika perlu mengurangi risk, kita tidak otomatis menutup posisi yang paling profit.

Kita mencari:

$$
\boxed{
\text{lowest marginal utility of risk}.
}
$$

---

# T.38. Marginal utility of risk

Definisikan:

$$
U_p
=
E[R_p]
-
\lambda\sigma_p^2.
$$

Marginal contribution:

$$
\frac{\partial U_p}{\partial w_i}
=
\mu_i
-
2\lambda(\Sigma w)_i.
$$

Jika:

$$
\frac{\partial U_p}{\partial w_i}<0,
$$

strategy tersebut sedang memberikan kontribusi marginal negatif terhadap objective.

---

# T.39. Ini menghasilkan exit ranking

Kita dapat menghitung:

$$
Score_i
=
\frac{
Marginal\ Alpha_i
}{
Marginal\ Risk_i
}.
$$

Kemudian posisi dengan:

$$
Score_i
$$

paling rendah dikurangi terlebih dahulu.

---

# T.40. Ini jauh lebih baik daripada FIFO

Bukan:

> posisi tertua ditutup.

Bukan:

> posisi yang profit paling kecil ditutup.

Bukan:

> posisi yang profit paling besar ditutup.

Tetapi:

$$
\boxed{
posisi\ dengan\ marginal\ risk-adjusted\ value\ terendah
}
$$

yang dikurangi.

---

# T.41. Liquidity constraint

Sekarang kita masuk ke masalah nyata.

Kita tidak boleh menganggap:

$$
q
$$

bisa berapa pun.

Misalkan:

$$
ADV
=
\text{average daily volume}.
$$

Kita dapat membatasi:

$$
\boxed{
q\le\eta ADV.
}
$$

Dengan:

$$
\eta
$$

misalnya beberapa persen atau jauh lebih kecil tergantung market.

---

# T.42. Market impact

Approximation sederhana:

$$
Impact(q)
=
Y\sigma
\left(
\frac{q}{V}
\right)^\alpha.
$$

Dengan:

- $Y$: impact coefficient,
- $\sigma$: volatility,
- $V$: volume,
- $\alpha$: scaling exponent.

Maka effective execution price menjadi:

$$
P_{exec}
=
P_{mid}
+
Impact(q).
$$

---

# T.43. Sekarang position size menjadi fixed point

Karena:

$$
q
$$

menentukan:

$$
Impact(q),
$$

dan impact mempengaruhi:

$$
Risk(q).
$$

Maka:

$$
q
=
\frac{R_{budget}}
{
D_{SL}+Impact(q)
}.
$$

Jadi:

$$
\boxed{
q^\star
=
\arg\max_q
U(q)
}
$$

dengan impact diperhitungkan.

---

# T.44. Untuk market sangat liquid

Jika:

$$
Impact(q)\approx0,
$$

maka:

$$
q^\star
\approx
q_{risk}.
$$

Tetapi untuk:

- small-cap stocks,
- mid-cap crypto,
- altcoins,
- thin order books,

impact dapat menjadi faktor dominan.

---

# T.45. Order book

Kita sekarang masuk ke order execution.

Order book:

$$
\mathcal B_t
=
\{(p_i^b,v_i^b)\}
$$

dan:

$$
\mathcal A_t
=
\{(p_j^a,v_j^a)\}.
$$

Bid:

$$
B_t=\max p_i^b.
$$

Ask:

$$
A_t=\min p_j^a.
$$

Spread:

$$
\boxed{
S_t=A_t-B_t.
}
$$

---

# T.46. Mid price

$$
M_t
=
\frac{A_t+B_t}{2}.
$$

Microprice dapat menggunakan imbalance.

Order book imbalance:

$$
\boxed{
I_t
=
\frac{
V_t^b-V_t^a
}{
V_t^b+V_t^a
}.
}
$$

---

# T.47. Order book sebagai short-term alpha

Misalnya:

$$
I_t>0.
$$

Artinya bid-side depth relatif besar.

Model dapat menganggap:

$$
P(\Delta P>0|I_t)
$$

meningkat.

Tetapi:

$$
I_t
$$

tidak boleh dianggap sebagai signal independen; ia harus masuk ke model state kita.

---

# T.48. Entry decision

Sekarang opportunity score:

$$
A_t
=
f(
\hat\mu_t,
\sigma_t,
I_t,
spread_t,
liquidity_t,
regime_t
).
$$

Trade hanya dibuat jika:

$$
\boxed{
A_t>A_{min}.
}
$$

---

# T.49. Expected edge setelah transaction cost

Ini sangat penting.

Model tidak boleh menggunakan:

$$
E[R].
$$

Tetapi:

$$
\boxed{
E[R_{net}]
=
E[R_{gross}]
-
E[fee]
-
E[spread]
-
E[slippage]
-
E[impact].
}
$$

Trade hanya valid jika:

$$
\boxed{
E[R_{net}]>0.
}
$$

---

# T.50. Bahkan harus melewati hurdle rate

Karena estimation error:

$$
E[R_{net}]
>
H_t.
$$

Hurdle:

$$
H_t
=
k\sigma_{\hat\mu}
+
Cost.
$$

Sehingga:

$$
\boxed{
\hat\mu_t
>
Cost_t
+
kSE(\hat\mu_t).
}
$$

Ini membuat model lebih konservatif.

---

# T.51. Pending order

Kamu sebelumnya menginginkan:

> order diletakkan tetapi tidak langsung dieksekusi.

Maka kita memiliki:

$$
P_{limit}.
$$

Order valid selama:

$$
t\le t_{expiry}.
$$

Jika belum terisi:

$$
Order\rightarrow Cancel
$$

ketika:

$$
P(
fill|S_t)
$$

turun terlalu rendah.

---

# T.52. Fill probability

Kita dapat memodelkan:

$$
P_{fill}
=
f(
distance,
queue,
volume,
volatility,
orderbook
).
$$

Misalnya:

$$
P_{fill}
=
\sigma(
\theta_0
+
\theta_1d
+
\theta_2I
+
\theta_3V
).
$$

Dengan sigmoid:

$$
\sigma(x)=\frac1{1+e^{-x}}.
$$

---

# T.53. Expected value pending order

Trade limit order bukan hanya:

$$
E[PnL|\text{trade}].
$$

Tetapi:

$$
\boxed{
EV_{limit}
=
P_{fill}EV_{trade}
-
Cost_{waiting}
-
OpportunityCost.
}
$$

Jadi order hanya diletakkan jika:

$$
\boxed{
EV_{limit}>0.
}
$$

---

# T.54. Ini sangat penting

Karena limit order memiliki:

$$
Adverse\ Selection.
$$

Jika order hanya filled ketika harga bergerak melawan kita, maka:

$$
P_{fill}
$$

tidak independen terhadap future return.

Sehingga:

$$
P(fill|future\ loss)
\neq
P(fill).
$$

Ini harus dimodelkan.

---

# T.55. Kita sekarang memiliki lifecycle lengkap

```text id="s8w7hj"
SIGNAL
  │
  ▼
EXPECTED RETURN
  │
  ▼
CONFIDENCE
  │
  ▼
TRADE APPROVED?
  │
  ├── NO → WAIT
  │
  ▼
RISK BUDGET
  │
  ▼
SL MODEL
  │
  ▼
POSITION SIZE
  │
  ▼
LIQUIDITY CHECK
  │
  ▼
PORTFOLIO RISK CHECK
  │
  ▼
ENTRY PRICE
  │
  ▼
TP / SL
  │
  ▼
ORDER BOOK
  │
  ▼
PENDING
  │
  ├── EXPIRED → CANCEL
  │
  ▼
FILLED
  │
  ▼
POSITION MANAGEMENT
  │
  ├── EXIT
  ├── HOLD
  └── MODIFY SL/TP
```

---

# T.56. Dynamic management loop

Setiap:

$$
\Delta t
$$

kita menghitung:

$$
S_t.
$$

Kemudian:

$$
\boxed{
\pi_t
=
\pi(S_t)
}
$$

menghasilkan action:

$$
a_t.
$$

Secara formal:

$$
a_t
=
\arg\max_a
E[
U_{t:t+H}
\mid
S_t,a
].
$$

---

# T.57. Action space

Untuk posisi yang sudah aktif:

$$
a_t\in
\{
EXIT,
HOLD,
MOVE\_SL,
MOVE\_TP,
PARTIAL\_EXIT,
ADD,
REDUCE
\}.
$$

Saya justru menyarankan **ADD** diperlakukan sangat hati-hati.

Jangan melakukan averaging down hanya karena posisi loss.

---

# T.58. Averaging down

Misalnya:

$$
P_t<P_e.
$$

Kita tidak mengatakan:

> "Harga turun, beli lagi supaya average price turun."

Sebaliknya:

$$
EV_{new}
=
EV(
portfolio+new\ position
).
$$

ADD hanya dilakukan jika:

$$
\boxed{
\Delta U>0
}
$$

dan:

$$
Risk_{portfolio,new}
\le B_t.
$$

---

# T.59. Floating loss

Sekarang menjawab salah satu pertanyaan awalmu:

> Jika floating loss, biarkan saja?

**Tidak secara otomatis.**

Floating loss bukan alasan untuk exit.

Tetapi juga bukan alasan untuk hold.

Kita evaluasi:

$$
V_{continue}
$$

vs:

$$
V_{exit}.
$$

---

# T.60. Decision matrix

Secara sederhana:

| Kondisi | Action |
|---|---|
| Loss + alpha masih kuat | HOLD |
| Loss + alpha melemah | REDUCE |
| Loss + alpha negatif | EXIT |
| Profit + alpha kuat | HOLD / TRAIL |
| Profit + alpha melemah | Tighten / Partial |
| Profit + alpha negatif | EXIT |
| Portfolio risk terlalu tinggi | REDUCE |
| Liquidity memburuk | REDUCE / EXIT |

Jadi:

$$
\boxed{
PnL\ bukan\ decision\ variable\ tunggal.
}
$$

---

# T.61. Mark-to-market bias

Ada bahaya psikologis maupun matematis:

$$
P_t-P_e.
$$

Informasi tersebut bisa membuat model terlalu terikat pada entry price.

Padahal setelah trade masuk, pertanyaan optimal adalah:

> Jika **sekarang saya tidak memiliki posisi**, apakah saya masih ingin membuka posisi ini?

Ini disebut **decision from current state**, bukan sunk-cost reasoning.

---

# T.62. Counterfactual decision

Kita dapat menghitung:

$$
EV_{enter}(S_t)
$$

seandainya kita belum memiliki posisi.

Bandingkan dengan:

$$
EV_{hold}(S_t).
$$

Jika:

$$
EV_{enter}<0,
$$

maka posisi seharusnya tidak dipertahankan kecuali ada alasan exit-cost yang membuat continuation masih optimal.

---

# T.63. Ini memberi kita prinsip yang sangat kuat

$$
\boxed{
Every\ evaluation\ period:
pretend\ the\ position\ does\ not\ exist.
}
$$

Kemudian tanyakan:

$$
\boxed{
Would\ the\ model\ enter\ this\ position\ now?
}
$$

Jika tidak:

$$
\text{reduce/exit}
$$

menjadi kandidat kuat.

---

# T.64. Namun kita masih harus memperhitungkan exit cost

Jika posisi ditutup sekarang:

$$
C_{exit}.
$$

Continuation value:

$$
V_{hold}.
$$

Maka:

$$
\boxed{
Exit
\iff
V_{exit}>V_{hold}.
}
$$

Ini menghindari churn.

---

# T.65. Dynamic risk budget

Risk budget juga harus berubah.

Misalkan:

$$
DD_t
$$

adalah drawdown.

Kita dapat mendefinisikan:

$$
B_t
=
B_0
g(DD_t).
$$

Misalnya:

$$
g(DD)=
\begin{cases}
1,&DD<D_1\\
0.75,&D_1\le DD<D_2\\
0.5,&D_2\le DD<D_3\\
0,&DD\ge DD_3.
\end{cases}
$$

Ini adalah **drawdown control layer**.

---

# T.66. Tetapi kita dapat membuatnya continuous

Misalnya:

$$
\boxed{
B_t
=
B_0
\exp(-\kappa DD_t).
}
$$

Ketika drawdown meningkat:

$$
DD_t\uparrow
$$

maka:

$$
B_t\downarrow.
$$

---

# T.67. Ini membuat sistem self-regulating

Saat performa memburuk:

$$
Risk\downarrow.
$$

Saat kondisi membaik:

$$
Risk\uparrow.
$$

Tetapi tetap dibatasi:

$$
B_{min}
\le B_t
\le B_{max}.
$$

---

# T.68. Sekarang kita bisa menggabungkan semuanya

Trade risk:

$$
R_{trade}.
$$

Strategy risk:

$$
R_{strategy}.
$$

Portfolio risk:

$$
R_{portfolio}.
$$

Market risk:

$$
R_{market}.
$$

Kita ingin:

$$
\boxed{
R_{trade}
\le
R_{strategy}
\le
R_{portfolio}
\le
R_{market}.
}
$$

Ini bukan inequality matematis literal dalam setiap implementasi, tetapi merupakan **hierarki risk budget**.

---

# T.69. Final position sizing equation

Secara konseptual saya ingin kita menggunakan:

$$
\boxed{
q_t^\star
=
\min
\left[
q_{risk},
q_{portfolio},
q_{liquidity},
q_{leverage},
q_{capacity}
\right]
}
$$

dengan:

$$
q_{risk}
=
\frac{
R_{trade,t}-C_t
}{
D_{SL,t}+S_t
}.
$$

Tetapi risk budget-nya sendiri dinamis:

$$
\boxed{
R_{trade,t}
=
R_0
\cdot
c_t
\cdot
g(Z_t)
\cdot
g(DD_t)
\cdot
g(\sigma_t)
}
$$

dengan $c_t$ sebagai confidence.

---

# T.70. Ini menghubungkan hampir seluruh tahap sebelumnya

Perhatikan:

$$
\boxed{
R_{trade,t}
=
R_0
\times
Confidence
\times
Regime
\times
Drawdown
\times
Volatility.
}
$$

Jadi:

### Model confidence tinggi

$$
c_t\uparrow
\Rightarrow
R_t\uparrow.
$$

### Regime buruk

$$
g(Z_t)\downarrow
\Rightarrow
R_t\downarrow.
$$

### Drawdown tinggi

$$
g(DD_t)\downarrow
\Rightarrow
R_t\downarrow.
$$

### Volatility tinggi

$$
g(\sigma_t)\downarrow
\Rightarrow
R_t\downarrow.
$$

---

# T.71. Tetapi jangan double-count risk

Ini peringatan penting.

Jika:

$$
\sigma_t
$$

sudah masuk ke:

$$
\Sigma_t
$$

dan kita juga memasukkan:

$$
g(\sigma_t)
$$

terlalu agresif, kita bisa melakukan:

$$
\boxed{
double\ risk\ scaling.
}
$$

Jadi setiap adjustment harus memiliki definisi yang jelas.

---

# T.72. Architecture final Tahap T

Saya ingin engine kita nanti dipisahkan menjadi:

```text
T1  Signal Validation
T2  Alpha Estimation
T3  Confidence
T4  Risk Budget
T5  SL Engine
T6  TP Engine
T7  Position Sizing
T8  Portfolio Constraint
T9  Liquidity / Impact
T10 Order Placement
T11 Fill Management
T12 Position Management
T13 Dynamic SL/TP
T14 Exit Engine
T15 Risk Shutdown
```

Masing-masing bisa diuji secara independen.

---

# T.73. Pseudocode konseptual

```text
for every evaluation_time t:

    market_state = estimate_state(t)

    alpha = estimate_alpha(market_state)

    confidence = estimate_confidence(alpha)

    strategy_weight = allocate_capital(
        alpha,
        covariance,
        factors,
        confidence
    )

    for each candidate trade:

        expected_return = estimate_expected_return()

        if expected_return <= transaction_cost + hurdle:
            continue

        risk_budget = compute_dynamic_risk_budget(
            strategy_weight,
            confidence,
            volatility,
            regime,
            drawdown
        )

        stop_loss = estimate_SL(
            volatility,
            market_structure,
            distribution
        )

        position_size = solve_position_size(
            risk_budget,
            stop_loss,
            slippage,
            liquidity
        )

        if portfolio_risk_after_trade > risk_limit:
            reduce_size()

        take_profit = optimize_TP(
            expected_return_distribution,
            stop_loss,
            utility
        )

        order = construct_order(
            entry,
            position_size,
            stop_loss,
            take_profit
        )

        execute_or_place(order)
```

---

# T.74. Dan posisi aktif

```text
for every active_position:

    state = update_position_state()

    continuation_value = estimate_hold_value(state)

    exit_value = estimate_exit_value(state)

    if portfolio_risk > limit:
        reduce_position()

    elif continuation_value < exit_value:
        exit_position()

    else:

        new_SL = optimize_SL(state)
        new_TP = optimize_TP(state)

        if new_SL improves expected utility:
            modify_SL(new_SL)

        if new_TP improves expected utility:
            modify_TP(new_TP)
```

---

# T.75. Satu hal yang sengaja belum kita lakukan

Kita **belum** membuat machine learning model yang sangat kompleks.

Ini disengaja.

Kita ingin terlebih dahulu memastikan:

$$
\boxed{
Decision\ Theory
}
$$

benar.

Barulah model seperti:

- XGBoost,
- LightGBM,
- neural network,
- transformer,
- temporal model,

digunakan untuk memperkirakan:

$$
P(R_{future}|S_t)
$$

atau:

$$
E[R_{future}|S_t].
$$

Model ML hanyalah **estimator**.

Optimizer dan risk engine tetap menjadi lapisan keputusan.

---

# T.76. Ini membuat sistem kita berbeda dari bot trading biasa

Bot biasa:

$$
Signal
\rightarrow
Buy/Sell.
$$

Sistem kita:

$$
\boxed{
State
\rightarrow
Alpha
\rightarrow
Confidence
\rightarrow
Risk
\rightarrow
Optimization
\rightarrow
Position
\rightarrow
Execution
\rightarrow
Continuous\ Re-evaluation.
}
$$

Dan yang lebih penting:

$$
\boxed{
\text{Tidak ada keputusan trading yang berdiri sendiri.}
}
$$

---

# T.77. Hubungan dengan TSP, MaxCut, dan portfolio optimization

Sekarang kita bisa melihat di mana problem combinatorial sebenarnya muncul.

### Portfolio allocation

$$
\boxed{
QUBO / QAOA
}
$$

### Strategy selection

$$
\boxed{
QUBO / QAOA
}
$$

### Execution routing

Misalnya memilih venue:

$$
\boxed{
QUBO
}
$$

### Order scheduling

Memilih urutan eksekusi:

$$
\boxed{
TSP-like
}
$$

### Pair / asset selection

Memaksimalkan diversity:

$$
\boxed{
MaxCut-like
}
$$

### Capital allocation

$$
\boxed{
QUBO
}
$$

Jadi kita tidak memaksakan satu algoritma quantum ke semua hal.

---

# T.78. Contoh MaxCut dalam sistem kita

Misalkan kita memiliki:

$$
10
$$

strategi.

Kita ingin membagi strategi menjadi dua kelompok:

$$
Cluster_A
$$

dan:

$$
Cluster_B.
$$

Kita ingin strategi yang highly correlated berada di kelompok berbeda atau setidaknya mendapatkan penalti.

Graph:

$$
G=(V,E).
$$

Edge weight:

$$
w_{ij}=|\rho_{ij}|.
$$

MaxCut:

$$
\boxed{
\max
\sum_{(i,j)\in E}
w_{ij}
x_i(1-x_j).
}
$$

Ini dapat digunakan untuk mencari diversification structure.

---

# T.79. TSP-like execution

Misalkan kita perlu mengeksekusi:

$$
N
$$

order pada beberapa venue.

Kita ingin meminimalkan:

$$
\boxed{
ExecutionCost
+
Slippage
+
Latency
+
MarketImpact.
}
$$

Jika urutan eksekusi penting, problem dapat memiliki struktur:

$$
\boxed{
TSP / routing.
}
$$

---

# T.80. Jadi akhirnya kita memiliki "optimization toolbox"

Bukan:

$$
\text{QAOA trading bot}.
$$

Tetapi:

$$
\boxed{
\text{Quantitative Trading Optimization System}
}
$$

dengan toolbox:

$$
\begin{array}{c}
\text{Convex Optimization}\\
\text{Quadratic Programming}\\
\text{QUBO}\\
\text{Ising}\\
\text{QAOA}\\
\text{MaxCut}\\
\text{TSP}\\
\text{Dynamic Programming}\\
\text{Statistical Decision Theory}
\end{array}
$$

---

# T.81. Tahap T dalam satu persamaan besar

Secara konseptual, seluruh keputusan order dapat dirangkum:

$$
\boxed{
O_t^\star
=
\arg\max_{O_t}
E
\left[
U(W_{t:t+H})
\mid
S_t,O_t
\right]
}
$$

subject to:

$$
\boxed{
\begin{aligned}
R_{trade}&\le B_{trade,t},\\
R_{portfolio}&\le B_{portfolio,t},\\
FactorExposure&\le F_{max},\\
Leverage&\le L_{max},\\
Impact&\le I_{max},\\
Liquidity&\ge L_{min},\\
PositionSize&\le Capacity,\\
ExecutionCost&\le C_{max}.
\end{aligned}
}
$$

Inilah sebenarnya tujuan akhir dari seluruh sistem.

---

# T.82. Dan sekarang kita memiliki loop tertutup

Sebelumnya sistem kita terlihat seperti:

$$
Market
\rightarrow
Signal
\rightarrow
Order.
$$

Sekarang:

$$
\boxed{
Market
\rightarrow
State
\rightarrow
Optimization
\rightarrow
Order
\rightarrow
Position
\rightarrow
New\ State
\rightarrow
Optimization
\rightarrow
...
}
$$

Jadi:

$$
\boxed{
\text{closed-loop adaptive trading system}.
}
$$

---

# T.83. Posisi Tahap T dalam keseluruhan proyek

```text
A  Market & Data
B  Return / Factor Modeling
C  Alpha Construction
D  Market Regime
E  Risk Modeling
F  Strategy Construction
G  Portfolio / QUBO
H  Quantum Mapping
I  QAOA / Optimization
J  Backtesting
K  Execution Modeling
L  Transaction Cost
M  Robustness
N  Walk Forward
O  Stress Testing
P  Statistical Validation
Q  Strategy Selection
R  Strategy Validation
S  Strategy Ensemble & Capital Allocation
T  Portfolio → Order + Dynamic Position Management
          │
          ▼
          U
```

Dan menurut saya **Tahap U nanti harus menjadi tahap yang sangat berbeda dari T**: bukan lagi sekadar bagaimana menentukan order, tetapi bagaimana kita membangun **execution/routing engine yang realistis terhadap order book, queue position, latency, slippage, partial fills, maker/taker fee, cancellation, dan adverse selection**.

Itu akan menjadi lapisan yang sangat penting jika tujuan akhirnya adalah membuat sistem yang benar-benar mendekati paradigma **quantitative trading infrastructure**, bukan sekadar backtest strategy.

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

## Prompt:
8/17/2026, 10:09:11 PM

lanjut Tahap V

## Response:
8/17/2026, 10:09:12 PM

# Tahap V — Event-Driven Backtesting & Market Replay Engine

Sekarang kita masuk ke salah satu tahap **paling penting** dari seluruh arsitektur kita.

Kalau Tahap U menjawab:

> **"Bagaimana keputusan trading diterjemahkan menjadi order yang realistis?"**

maka Tahap V menjawab:

> **"Bagaimana kita menghidupkan kembali pasar masa lalu sedemikian rupa sehingga strategi kita hanya mengetahui informasi yang memang tersedia pada saat itu?"**

Ini yang akan menentukan apakah hasil backtest kita **layak dipercaya** atau hanya terlihat bagus karena simulator terlalu ideal.

---

# V.1. Perubahan paradigma

Backtest sederhana biasanya seperti ini:

$$
\boxed{
Data_t
\rightarrow
Signal_t
\rightarrow
Position_t
\rightarrow
Return_t
}
$$

Masalahnya, proses tersebut sering secara implisit mengasumsikan:

- order langsung terisi,
- harga eksekusi sama dengan harga signal,
- tidak ada latency,
- tidak ada spread,
- tidak ada partial fill,
- tidak ada queue,
- tidak ada rejection,
- tidak ada order cancellation,
- semua data tersedia secara simultan.

Untuk sistem kita, itu **tidak boleh**.

Kita ingin:

$$
\boxed{
Data
\rightarrow
Event
\rightarrow
State
\rightarrow
Decision
\rightarrow
Order
\rightarrow
Exchange
\rightarrow
Fill
\rightarrow
Position
\rightarrow
PnL
}
$$

---

# V.2. Event-driven architecture

Pasar kita representasikan sebagai sequence:

$$
\mathcal{E}
=
\{e_1,e_2,\ldots,e_N\}
$$

dengan:

$$
t_1<t_2<\cdots<t_N.
$$

Setiap event:

$$
e_i=(t_i,type_i,data_i).
$$

Contohnya:

$$
e_i=
(10{:}00{:}01.023,
MARKET\_UPDATE,
BTC).
$$

Atau:

$$
e_j=
(10{:}00{:}01.051,
ORDER\_FILL,
Order_{17}).
$$

---

# V.3. Mengapa event lebih baik daripada candle?

Misalkan candle 1 menit:

$$
[100,105,99,103].
$$

Kita hanya mengetahui:

$$
O=100,
H=105,
L=99,
C=103.
$$

Tetapi kita tidak mengetahui urutan sebenarnya.

Apakah:

$$
100\rightarrow105\rightarrow99\rightarrow103
$$

atau:

$$
100\rightarrow99\rightarrow105\rightarrow103?
$$

Untuk strategi intraday dengan:

- SL,
- TP,
- limit order,

perbedaan tersebut sangat besar.

---

# V.4. Ambiguity pada candle

Misalkan kita punya:

$$
Entry=100,
$$

$$
SL=98,
$$

$$
TP=105.
$$

Candle:

$$
O=100,\quad
H=106,\quad
L=97,\quad
C=103.
$$

Dari OHLC saja kita tidak tahu apakah:

$$
TP\rightarrow SL
$$

atau:

$$
SL\rightarrow TP.
$$

Tetapi PnL bisa sangat berbeda.

Karena itu:

$$
\boxed{
OHLC\ alone
\neq
sufficient\ for\ realistic\ execution.
}
$$

---

# V.5. Market replay

Kita ingin melakukan:

$$
\boxed{
Replay(Data_{historical})
}
$$

seolah-olah waktu berjalan dari masa lalu ke masa depan.

Pada setiap event:

$$
t_i,
$$

engine hanya boleh membaca:

$$
\boxed{
\mathcal F_{t_i}
}
$$

yaitu information set yang tersedia sampai $t_i$.

---

# V.6. Filtration

Dalam bahasa stochastic process, kita mendefinisikan filtration:

$$
\mathcal F_t
=
\sigma
(
X_\tau:
\tau\le t
).
$$

Strategi kita harus memenuhi:

$$
\boxed{
a_t
\in
\mathcal F_t.
}
$$

Artinya keputusan trading pada waktu $t$ hanya boleh bergantung pada informasi yang tersedia hingga $t$.

Ini adalah fondasi matematis untuk menghindari:

$$
\boxed{\text{look-ahead bias}.}
$$

---

# V.7. Contoh look-ahead bias

Misalkan kita ingin memprediksi return:

$$
r_{t+1}.
$$

Tetapi secara tidak sengaja feature menggunakan:

$$
Close_{t+1}.
$$

Maka:

$$
X_t=
f(
Close_t,
Close_{t+1}
).
$$

Strategi memang akan terlihat sangat bagus.

Tetapi:

$$
Close_{t+1}\notin\mathcal F_t.
$$

Jadi strategi tersebut **tidak kausal**.

---

# V.8. Causality condition

Secara formal:

$$
\boxed{
Decision_t
=
\pi(\mathcal F_t).
}
$$

Bukan:

$$
Decision_t
=
\pi(\mathcal F_{t+k})
$$

untuk:

$$
k>0.
$$

---

# V.9. Market state

Kita definisikan state:

$$
S_t.
$$

Misalnya:

$$
S_t=
\begin{bmatrix}
P_t\\
V_t\\
Spread_t\\
Depth_t\\
Volatility_t\\
BTC_t\\
ETH_t\\
Gold_t\\
DXY_t\\
Position_t\\
Cash_t\\
Orders_t
\end{bmatrix}.
$$

Kemudian:

$$
\boxed{
S_{t+1}
=
F(S_t,e_{t+1}).
}
$$

---

# V.10. Strategy sebagai policy

Strategy kita sekarang dapat ditulis:

$$
\boxed{
a_t=\pi_\theta(S_t).
}
$$

dengan:

$$
a_t
=
\{
target\ position,
order\ type,
quantity,
price,
SL,
TP
\}.
$$

Parameter:

$$
\theta
$$

berasal dari seluruh model kita:

- factor model,
- alpha,
- regime,
- risk,
- optimizer,
- execution policy.

---

# V.11. Event loop

Secara konseptual:

```text
while historical_data remains:

    event = next_event()

    update_market_state(event)

    update_orders(event)

    process_fills(event)

    update_positions()

    update_risk()

    generate_signal()

    optimize_target_position()

    generate_execution_plan()

    submit_orders()

    record_state()
```

Tetapi urutan ini harus sangat hati-hati.

Kita tidak boleh menggunakan informasi dari event sebelum event tersebut diproses.

---

# V.12. Urutan kausal

Pada timestamp $t$:

$$
\boxed{
MarketUpdate
\rightarrow
StateUpdate
\rightarrow
Signal
\rightarrow
Order
}
$$

Order tersebut baru dapat diproses pada:

$$
t+\Delta t_{latency}.
$$

Jadi:

$$
\boxed{
t_{decision}
<
t_{exchange}
\le
t_{fill}.
}
$$

---

# V.13. Decision timestamp

Setiap keputusan harus mempunyai:

$$
t_{decision}.
$$

Contoh:

$$
10:15:00.000.
$$

Kemudian:

$$
t_{submit}=10:15:00.003,
$$

$$
t_{exchange}=10:15:00.010,
$$

$$
t_{fill}=10:15:00.021.
$$

Dengan demikian kita dapat menghitung:

$$
L_{total}
=
t_{fill}-t_{decision}.
$$

---

# V.14. Order object

Saya menyarankan setiap order memiliki struktur:

$$
O_i=
\{
id,
symbol,
side,
type,
quantity,
limit\_price,
stop\_price,
timestamp,
status
\}.
$$

Misalnya:

$$
O_{17}
=
\{
BTC,
BUY,
LIMIT,
0.01,
60000,
...
\}.
$$

---

# V.15. Order lifecycle

Order:

$$
NEW
$$

kemudian:

$$
SUBMITTED
$$

kemudian:

$$
ACKNOWLEDGED.
$$

Setelah itu:

$$
PARTIALLY\_FILLED
$$

atau:

$$
FILLED.
$$

Atau:

$$
CANCELLED.
$$

Atau:

$$
REJECTED.
$$

---

# V.16. Position state

Untuk setiap asset:

$$
q_t.
$$

Cash:

$$
C_t.
$$

Portfolio value:

$$
V_t=C_t+q_tP_t.
$$

Untuk multi-asset:

$$
\boxed{
V_t
=
C_t+
\sum_iq_{i,t}P_{i,t}.
}
$$

---

# V.17. Realized dan unrealized PnL

Unrealized:

$$
PnL_t^{unrealized}
=
q_t(P_t-P_{entry}).
$$

Realized:

$$
PnL_t^{realized}
=
\sum_{closed\ trades}
PnL_j.
$$

Total:

$$
\boxed{
PnL_t
=
PnL_t^{realized}
+
PnL_t^{unrealized}.
}
$$

---

# V.18. Cash accounting

Untuk buy:

$$
C_{t+1}
=
C_t-qP_{exec}-Fee.
$$

Untuk sell:

$$
C_{t+1}
=
C_t+qP_{exec}-Fee.
$$

Ini sederhana tetapi sangat penting.

Jangan pernah menghitung return hanya dari:

$$
P_{close}.
$$

---

# V.19. Short selling

Untuk short:

$$
q_t<0.
$$

Portfolio value tetap:

$$
V_t=C_t+q_tP_t.
$$

Jika:

$$
P_t\downarrow,
$$

maka:

$$
q_t(P_t-P_{entry})>0.
$$

---

# V.20. Leverage

Gross exposure:

$$
G_t=
\sum_i|q_{i,t}P_{i,t}|.
$$

Leverage:

$$
\boxed{
L_t=
\frac{G_t}{V_t}.
}
$$

Constraint:

$$
L_t\le L_{max}.
$$

---

# V.21. Margin

Jika short atau leveraged position digunakan, simulator harus mempunyai:

$$
MarginRequirement_t.
$$

Jika:

$$
Equity_t
<
MaintenanceMargin_t,
$$

maka:

$$
\boxed{
ForcedLiquidation.
}
$$

Ini harus disimulasikan.

---

# V.22. Stop-loss bukan sekadar angka

Misalkan:

$$
SL=95.
$$

Kita tidak boleh otomatis mengatakan:

$$
P_{low}<95
\Rightarrow
Fill=95.
$$

Realitanya:

$$
P_{trigger}=95
$$

kemudian market order dikirim.

Harga fill dapat:

$$
P_{fill}<95.
$$

Jadi:

$$
\boxed{
SL_{trigger}
\neq
SL_{execution}.
}
$$

---

# V.23. Stop-loss slippage

Untuk long:

$$
P_{SL,fill}
=
P_{SL}
-
\epsilon_{SL}.
$$

Dengan:

$$
\epsilon_{SL}\ge0.
$$

Pada crash:

$$
\epsilon_{SL}
$$

dapat sangat besar.

Ini sangat penting untuk crypto dan small-cap stocks.

---

# V.24. Take-profit juga tidak sempurna

Jika TP menggunakan limit:

$$
P_{TP}.
$$

Maka:

$$
P_{fill}=P_{TP}
$$

hanya jika liquidity tersedia.

Jika menggunakan market:

$$
P_{fill}
\neq P_{TP}
$$

karena slippage.

---

# V.25. OCO logic

Position biasanya mempunyai:

$$
SL
$$

dan:

$$
TP.
$$

Keduanya harus dihubungkan sebagai:

$$
\boxed{
OCO=
One\ Cancels\ Other.
}
$$

Jika TP filled:

$$
Cancel(SL).
$$

Jika SL filled:

$$
Cancel(TP).
$$

---

# V.26. Kalau tidak menggunakan OCO

Simulator dapat melakukan hal absurd:

$$
TP\ filled
$$

kemudian beberapa event berikutnya:

$$
SL\ filled.
$$

Hasilnya posisi menjadi terbalik.

Ini adalah salah satu bug backtest yang sangat umum.

---

# V.27. Trailing stop

Misalkan:

$$
SL_t
=
P_t-d.
$$

Tetapi SL hanya boleh bergerak satu arah untuk long:

$$
SL_{t+1}
\ge
SL_t.
$$

Jadi:

$$
\boxed{
SL_{t+1}
=
\max(SL_t,P_{t+1}-d).
}
$$

Untuk short:

$$
\boxed{
SL_{t+1}
=
\min(SL_t,P_{t+1}+d).
}
$$

---

# V.28. Break-even stop

Misalkan entry:

$$
P_e.
$$

Setelah profit mencapai threshold:

$$
R_t\ge R_{BE},
$$

kita ubah:

$$
SL=P_e.
$$

Namun sebenarnya kita harus mempertimbangkan biaya.

Jika fee + expected exit cost:

$$
C,
$$

maka true break-even:

$$
\boxed{
P_{BE}
=
P_e+C.
}
$$

Untuk long.

---

# V.29. Dynamic TP

Ini menghubungkan langsung dengan ide kita sebelumnya.

Misalkan:

$$
TP_t=f(
volatility,
alpha,
regime,
liquidity,
position_age
).
$$

Jadi TP tidak harus fixed.

Misalnya:

$$
TP_t
=
P_e+
k_t\sigma_t.
$$

Dengan:

$$
k_t=f(\alpha_t,regime_t).
$$

---

# V.30. Tetapi jangan mengubah TP karena hindsight

Misalnya harga sudah naik 5%.

Tidak boleh kemudian:

> "Karena sekarang terlihat kuat, TP kita naikkan."

Kita hanya boleh menaikkan TP jika:

$$
\boxed{
Decision_t
=
f(\mathcal F_t).
}
$$

---

# V.31. Market replay untuk cross-asset system

State kita harus mencakup:

$$
\mathbf X_t=
[
BTC,
ETH,
Altcoin,
Gold,
DXY,
SPX,
VIX,
Rates,
...
].
$$

Tetapi setiap asset memiliki timestamp sendiri.

Kita menggunakan:

$$
\boxed{
Event\ Queue
}
$$

yang menggabungkan semua event berdasarkan timestamp.

---

# V.32. Priority queue

Misalkan:

$$
E=
\{
e_1,e_2,\ldots,e_N
\}.
$$

Sort:

$$
t(e_1)
\le
t(e_2)
\le\cdots.
$$

Engine selalu mengambil:

$$
\boxed{
e^\star
=
\arg\min_{e\in E}t(e).
}
$$

Kemudian memprosesnya.

Ini merupakan inti event-driven simulator.

---

# V.33. Data hierarchy

Saya menyarankan data kita dibagi menjadi:

### Level 0

Raw market data.

$$
Tick
$$

### Level 1

Order book:

$$
L1/L2/L3.
$$

### Level 2

Trades:

$$
TradePrint.
$$

### Level 3

Bars:

$$
1s,1m,5m,...
$$

### Level 4

Derived features:

$$
Volatility,
Momentum,
Correlation,
Flow.
$$

### Level 5

Model state:

$$
Alpha,
Regime,
Risk.
$$

---

# V.34. Jangan mencampur level

Raw data:

$$
D_{raw}
$$

harus immutable.

Kemudian:

$$
D_{raw}
\rightarrow
D_{clean}
\rightarrow
D_{feature}
\rightarrow
D_{signal}.
$$

Ini memungkinkan kita melakukan audit.

---

# V.35. Point-in-time dataset

Untuk setiap feature:

$$
X_{i,t}
$$

kita harus menyimpan:

$$
timestamp_{observation}
$$

dan:

$$
timestamp_{availability}.
$$

Karena:

$$
timestamp_{observation}
\neq
timestamp_{availability}.
$$

---

# V.36. Contoh fundamental data

Misalnya laporan perusahaan:

$$
Q1.
$$

Tanggal laporan:

$$
May\ 10.
$$

Tetapi periode laporan:

$$
Jan-Mar.
$$

Kita tidak boleh menggunakan data Q1 sebelum:

$$
May\ 10.
$$

Maka:

$$
AvailabilityDate
$$

adalah yang menentukan kapan informasi boleh masuk ke model.

---

# V.37. Ini disebut point-in-time data

Untuk setiap observation:

$$
\boxed{
X=
(value,
observation\_time,
availability\_time).
}
$$

Backtest menggunakan:

$$
availability\_time.
$$

---

# V.38. Survivorship bias

Misalkan pada 2026 kita melihat:

$$
Top\ 100\ stocks.
$$

Kemudian backtest 2021 menggunakan daftar tersebut.

Itu salah.

Karena pada 2021 kita belum tahu perusahaan mana yang akan menjadi top 100 pada 2026.

Universe harus:

$$
\boxed{
Universe_t
}
$$

dan berubah sesuai waktu.

---

# V.39. Delisted assets

Jika perusahaan delisting pada:

$$
2024,
$$

kita tidak boleh menghapus seluruh history-nya dari database.

Justru:

$$
Data_{2021-2024}
$$

harus tetap ada.

Jika tidak:

$$
SurvivorshipBias\uparrow.
$$

---

# V.40. Corporate actions

Untuk saham:

- split,
- dividend,
- rights issue,
- merger,
- delisting.

Semua harus dipertimbangkan.

Misalnya:

$$
2:1\ split.
$$

Harga:

$$
100\rightarrow50.
$$

Tetapi posisi:

$$
1\ share\rightarrow2\ shares.
$$

Simulator harus mengubah quantity dan price secara konsisten.

---

# V.41. Crypto memiliki masalah berbeda

Untuk crypto:

- exchange listing,
- delisting,
- token migration,
- redenomination,
- perpetual funding,
- liquidation,
- maker/taker fee,
- funding rate.

Jadi engine kita harus modular.

---

# V.42. Funding rate

Untuk perpetual futures:

$$
PnL_{funding}
=
qP\times fundingRate.
$$

Secara periodik:

$$
C_{funding}
=
Notional\times f.
$$

Maka total PnL:

$$
\boxed{
PnL
=
PnL_{price}
+
PnL_{funding}
-
Fees.
}
$$

---

# V.43. Karena itu strategi crypto dan saham tidak boleh hard-coded

Kita sebaiknya mempunyai interface:

$$
\boxed{
MarketModel
}
$$

dengan implementasi:

$$
CryptoMarketModel,
$$

$$
EquityMarketModel,
$$

$$
FXMarketModel,
$$

$$
FuturesMarketModel.
$$

---

# V.44. Tetapi strategy tetap sama

Strategy menerima:

$$
State_t.
$$

Kemudian:

$$
Action_t=\pi(State_t).
$$

Market model yang menentukan bagaimana action tersebut dieksekusi.

Ini membuat arsitektur:

$$
\boxed{
Strategy\;agnostic
}
$$

terhadap asset class.

---

# V.45. Deterministic replay

Ini sangat penting untuk penelitian.

Jika kita menjalankan:

$$
Backtest(A)
$$

dua kali pada dataset yang sama, seharusnya:

$$
Result_1=Result_2.
$$

Kecuali kita memang memasukkan stochastic process.

Untuk stochastic model kita gunakan:

$$
seed.
$$

Sehingga:

$$
seed=s
$$

memberikan:

$$
\boxed{
reproducible\ simulation.
}
$$

---

# V.46. Monte Carlo execution

Setelah deterministic replay bekerja, baru kita masukkan uncertainty.

Misalnya slippage:

$$
\epsilon
\sim
Distribution(\sigma,liquidity).
$$

Kemudian:

$$
P_{fill}
=
P_{model}+\epsilon.
$$

Kita lakukan:

$$
N
$$

simulasi.

---

# V.47. Distribution of outcomes

Kita mendapatkan:

$$
\{
PnL_1,\ldots,PnL_N
\}.
$$

Kemudian:

$$
E[PnL],
$$

$$
Var(PnL),
$$

$$
VaR,
$$

$$
CVaR.
$$

Jadi bukan hanya:

$$
\boxed{
"strategy menghasilkan 23\%."
}
$$

tetapi:

$$
\boxed{
E[R]=23\%,
\quad
CI_{95\%}=[...,...].
}
$$

---

# V.48. Stress testing

Kita juga mengubah:

$$
spread,
$$

$$
slippage,
$$

$$
latency,
$$

$$
volatility,
$$

$$
impact.
$$

Misalnya:

$$
Spread\times2.
$$

Jika strategy masih profitable:

$$
Robustness\uparrow.
$$

Jika langsung hancur:

$$
StrategyFragile.
$$

---

# V.49. Execution stress matrix

Kita bisa membangun:

$$
\boxed{
Performance
=
f(
Slippage,
Spread,
Latency,
Impact
).
}
$$

Contoh:

| Scenario | Slippage | Spread | Latency | Sharpe |
|---|---:|---:|---:|---:|
| Optimistic | 0.5× | 0.5× | 0.5× | ... |
| Base | 1× | 1× | 1× | ... |
| Conservative | 2× | 2× | 2× | ... |
| Stress | 5× | 3× | 5× | ... |

Ini jauh lebih informatif daripada satu angka backtest.

---

# V.50. Walk-forward testing

Kita tidak boleh:

$$
Train_{2021-2025}
$$

kemudian:

$$
Test_{2021-2025}.
$$

Sebaliknya:

$$
\boxed{
Train
\rightarrow
Validation
\rightarrow
Test
}
$$

berdasarkan waktu.

---

# V.51. Rolling walk-forward

Misalnya:

$$
Train:
2021-2022
$$

$$
Validation:
2023Q1
$$

$$
Test:
2023Q2.
$$

Kemudian window bergeser:

$$
Train:
2021Q2-2023Q1
$$

$$
Validation:
2023Q2
$$

$$
Test:
2023Q3.
$$

Dan seterusnya.

---

# V.52. Parameter stability

Misalkan optimizer menghasilkan:

$$
\theta^\star.
$$

Kita tidak ingin:

$$
\theta^\star
$$

berubah drastis setiap periode.

Definisikan:

$$
\Delta\theta_t
=
\|\theta_t-\theta_{t-1}\|.
$$

Jika:

$$
\Delta\theta_t\gg0,
$$

bisa jadi model overfit terhadap regime tertentu.

---

# V.53. Hyperparameter optimization

Ini harus dilakukan **hanya pada training/validation**.

Bukan test.

Jika:

$$
Test
$$

digunakan untuk memilih parameter terbaik, maka:

$$
Test
$$

bukan lagi out-of-sample.

---

# V.54. Nested optimization

Arsitektur kita akhirnya akan mempunyai:

$$
\boxed{
Data
\rightarrow
Model
\rightarrow
Portfolio
\rightarrow
Execution
}
$$

dan masing-masing memiliki parameter.

Kita harus membedakan:

$$
\theta_{alpha},
$$

$$
\theta_{portfolio},
$$

$$
\theta_{execution}.
$$

---

# V.55. Jangan optimalkan semuanya sekaligus

Jika kita langsung melakukan:

$$
\arg\max_{\theta}
Sharpe(\theta)
$$

terhadap:

- alpha,
- risk,
- QUBO,
- execution,
- TP,
- SL,
- trailing,
- leverage,

kita hampir pasti memperoleh overfitting.

Lebih baik:

$$
\boxed{
Layered\ validation.
}
$$

---

# V.56. Validation hierarchy

### Layer 1

Market data integrity.

### Layer 2

Feature correctness.

### Layer 3

Signal correctness.

### Layer 4

Portfolio optimization.

### Layer 5

Execution.

### Layer 6

Full-system backtest.

### Layer 7

Stress test.

### Layer 8

Out-of-sample.

### Layer 9

Paper trading.

### Layer 10

Live trading dengan size sangat kecil.

---

# V.57. Ini sangat penting untuk proyek kita

Karena kita menggunakan:

$$
QUBO,
$$

$$
Ising,
$$

$$
VQE,
$$

$$
QAOA,
$$

kita harus membuktikan bahwa improvement bukan berasal dari:

- look-ahead,
- data leakage,
- unrealistic execution,
- parameter tuning,
- random seed,
- simulator artifact.

---

# V.58. Quantum benchmark

Misalkan classical optimizer menghasilkan:

$$
R_C.
$$

Quantum optimizer menghasilkan:

$$
R_Q.
$$

Kita tidak boleh langsung menyimpulkan:

$$
R_Q>R_C
\Rightarrow
Quantum\ advantage.
$$

Kita harus memastikan:

$$
\boxed{
Data,
Constraints,
Initialization,
Execution,
Risk,
TransactionCost
}
$$

semuanya sama.

---

# V.59. Paired experiment

Untuk setiap periode:

$$
t,
$$

jalankan:

$$
Strategy_C(t)
$$

dan:

$$
Strategy_Q(t)
$$

dengan kondisi identik.

Kemudian:

$$
\Delta R_t
=
R_Q(t)-R_C(t).
$$

Kita bisa menguji:

$$
H_0:
E[\Delta R]=0.
$$

---

# V.60. Dan bukan hanya return

Bandingkan:

$$
Sharpe,
$$

$$
Sortino,
$$

$$
MaxDD,
$$

$$
CVaR,
$$

$$
Turnover,
$$

$$
ExecutionCost,
$$

$$
FillRate,
$$

$$
Latency,
$$

$$
PnL.
$$

Jadi benchmark menjadi multidimensional.

---

# V.61. Architecture final Tahap V

Secara keseluruhan:

```text
                 HISTORICAL DATA
                       │
                       ▼
              ┌─────────────────┐
              │ Event Generator │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Event Queue     │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Market State    │
              └────────┬────────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Feature Engine       Order Engine
             │                   │
             ▼                   ▼
       Alpha / Regime       Fill Simulator
             │                   │
             ▼                   ▼
       Risk / Portfolio     Execution State
             │                   │
             └─────────┬─────────┘
                       ▼
                Position Engine
                       │
                       ▼
                   PnL Engine
                       │
                       ▼
                Risk Analytics
                       │
                       ▼
                 Backtest Report
```

---

# V.62. Output dari engine

Setiap event sebaiknya menghasilkan log:

$$
\boxed{
L_t=
[
timestamp,
state,
signal,
action,
order,
fill,
position,
PnL,
risk
].
}
$$

Dengan ini kita dapat melakukan **full forensic analysis** terhadap setiap trade.

---

# V.63. Trade journal otomatis

Untuk setiap trade:

$$
Trade_i=
\{
signal,
entry,
execution,
exit,
PnL,
risk,
slippage,
MAE,
MFE,
holding\ time
\}.
$$

Dua metrik yang sangat penting:

### MAE

Maximum Adverse Excursion:

$$
MAE_i
=
\min_t(R_{i,t}).
$$

### MFE

Maximum Favorable Excursion:

$$
MFE_i
=
\max_t(R_{i,t}).
$$

---

# V.64. Mengapa MAE/MFE penting?

Misalnya kita menemukan:

$$
MAE
$$

sebagian besar trade hanya:

$$
-0.3R,
$$

tetapi SL kita:

$$
-1R.
$$

Mungkin SL terlalu longgar.

Sebaliknya jika:

$$
MAE
\approx-0.9R
$$

sebelum trade yang akhirnya menang,

SL terlalu ketat dapat membunuh strategy.

Jadi:

$$
\boxed{
MAE/MFE
\rightarrow
SL/TP\ design.
}
$$

---

# V.65. Feedback loop

Sekarang sistem kita menjadi benar-benar adaptif:

$$
\boxed{
Backtest
\rightarrow
Diagnostics
\rightarrow
Model Improvement
\rightarrow
Backtest
}
$$

Tetapi hati-hati:

$$
Test
$$

tidak boleh masuk ke feedback loop.

Kalau masuk:

$$
Test
\rightarrow
Optimization
$$

maka:

$$
Test
$$

sudah terkontaminasi.

---

# V.66. Tiga dataset

Saya ingin kita menetapkan tiga wilayah:

$$
\boxed{
TRAIN
}
$$

untuk membangun model.

$$
\boxed{
VALIDATION
}
$$

untuk memilih model/parameter.

$$
\boxed{
TEST
}
$$

untuk evaluasi final.

Kemudian setelah test:

$$
\boxed{
PAPER
}
$$

dan baru:

$$
\boxed{
LIVE.
}
$$

---

# V.67. Dan ada satu lapisan lagi: Shadow Mode

Sebelum live execution:

$$
Market\rightarrow Strategy
$$

tetapi:

$$
Order\neq Sent.
$$

Kita hanya mencatat:

$$
\hat P_{fill},
$$

$$
\hat PnL,
$$

$$
\hat Slippage.
$$

Kemudian dibandingkan dengan market sebenarnya.

Ini disebut:

$$
\boxed{
Shadow\ Trading.
}
$$

---

# V.68. Hierarki deployment kita

Saya sarankan:

$$
\boxed{
Backtest
\rightarrow
Stress Test
\rightarrow
Walk Forward
\rightarrow
Monte Carlo
\rightarrow
Shadow
\rightarrow
Paper
\rightarrow
Micro Live
\rightarrow
Scale.
}
$$

Bukan:

$$
Backtest
\rightarrow
Real\ Money.
$$

---

# V.69. Apa yang sebenarnya kita bangun?

Pada titik ini, proyek kita sudah jauh melampaui:

> "bot trading."

Kita sedang membangun:

$$
\boxed{
\textbf{Research-grade Quantitative Trading Platform}
}
$$

dengan struktur:

$$
\boxed{
\begin{aligned}
Market\ Data\\
\downarrow\\
State\ Estimation\\
\downarrow\\
Factor\ Model\\
\downarrow\\
Alpha\ Model\\
\downarrow\\
Regime\ Model\\
\downarrow\\
Risk\ Model\\
\downarrow\\
Portfolio\ Optimization\\
\downarrow\\
Quantum/Classical\ Optimization\\
\downarrow\\
Execution\ Optimization\\
\downarrow\\
Event\ Driven\ Simulator\\
\downarrow\\
Risk\ &\ Performance\ Analytics
\end{aligned}
}
$$

---

# V.70. Tahap V dalam satu persamaan

Kalau seluruh Tahap V harus diringkas dalam satu persamaan, saya akan menuliskannya sebagai:

$$
\boxed{
S_{t+1}
=
F
\left(
S_t,
E_{t+1},
\pi_\theta(\mathcal F_t)
\right)
}
$$

dengan constraint:

$$
\boxed{
\pi_\theta(\mathcal F_t)
\in
\mathcal A_t
}
$$

dan PnL:

$$
\boxed{
W_{t+1}
=
W_t
+
PnL(
S_t,
E_{t+1},
a_t
)
-
C_{execution}.
}
$$

Karena:

$$
a_t\in\mathcal F_t,
$$

maka sistem bersifat **causal**.

Dan karena:

$$
E_{t+1}
$$

diproses satu per satu, kita memperoleh:

$$
\boxed{
\text{event-driven market replay}.
}
$$

---

# V.71. Hubungan Tahap A → V

Sekarang kita dapat melihat mengapa tahap-tahap sebelumnya sebenarnya saling mengunci:

$$
\boxed{
A
\rightarrow
B
\rightarrow
C
\rightarrow\cdots\rightarrow
U
\rightarrow
V
}
$$

bukan kumpulan modul terpisah.

Secara konseptual:

$$
\boxed{
\text{Market}
\rightarrow
\text{Information}
\rightarrow
\text{Prediction}
\rightarrow
\text{Optimization}
\rightarrow
\text{Risk}
\rightarrow
\text{Execution}
\rightarrow
\text{Reality Check}.
}
$$

Tahap V adalah **reality check** tersebut.

---

## V.72. Hal yang harus kita implementasikan setelah ini

Sebelum masuk ke tahap berikutnya, saya justru menyarankan kita **tidak langsung melanjutkan menambah teori**.

Kita sudah mempunyai cukup banyak teori untuk mulai membangun engine pertama.

Urutan implementasi yang paling masuk akal:

### V.1 — Data schema

Bangun format:

```text
MarketEvent
TradeEvent
OrderBookEvent
OrderEvent
FillEvent
PositionEvent
```

### V.2 — Event queue

Implementasikan:

$$
PriorityQueue(E)
$$

berdasarkan timestamp.

### V.3 — Market state

Implementasikan:

$$
S_t.
$$

### V.4 — Order state machine

Implementasikan:

$$
NEW
\rightarrow
SUBMITTED
\rightarrow
FILLED/CANCELLED/REJECTED.
$$

### V.5 — Execution simulator

Mulai dari:

$$
MarketOrder
$$

kemudian:

$$
LimitOrder
$$

kemudian:

$$
PartialFill.
$$

### V.6 — Position & PnL

Implementasikan accounting yang benar.

### V.7 — SL/TP/OCO

Kemudian:

$$
Trailing/BEP/DynamicTP.
$$

### V.8 — Transaction cost

Masukkan:

$$
fee+spread+slippage+impact.
$$

### V.9 — Walk-forward engine

Baru setelah simulator benar:

$$
Train\rightarrow Validate\rightarrow Test.
$$

### V.10 — Monte Carlo & stress

Dan terakhir:

$$
Robustness.
$$

---

## V.73. Satu keputusan desain yang sangat penting

Untuk proyek kita, saya menyarankan **jangan membuat backtest engine yang hanya menerima dataframe OHLC lalu menghasilkan equity curve**.

Kita sebaiknya membangun:

$$
\boxed{
\textbf{Market Replay Engine}
}
$$

yang menerima event:

$$
E_1,E_2,\ldots,E_N
$$

dan menghasilkan:

$$
S_1,S_2,\ldots,S_N.
$$

Dengan begitu, engine yang sama nantinya dapat digunakan untuk:

$$
\boxed{
Historical\ Backtest
}
$$

dan kemudian, dengan interface yang sama:

$$
\boxed{
Paper\ Trading
}
$$

dan bahkan:

$$
\boxed{
Live\ Trading.
}
$$

Artinya kita tidak perlu memiliki tiga sistem berbeda. Kita memiliki **satu trading engine**, hanya sumber event-nya yang berubah:

$$
\boxed{
\begin{array}{ccc}
Historical & Paper & Live\\
Data & Exchange\ Stream & Exchange\ Stream\\
\downarrow & \downarrow & \downarrow\\
\multicolumn{3}{c}{\textbf{Same Strategy + Risk + Execution Engine}}
\end{array}
}
$$

Menurut saya, ini adalah titik arsitektural yang sangat penting untuk proyek kita: **backtest bukan versi mainan dari live trading; backtest adalah live engine yang diberi historical event stream.**

Setelah fondasi ini selesai, **Tahap W** secara alami dapat kita gunakan untuk membangun **Performance Attribution, Risk Analytics, dan Robustness Framework**—yaitu menjawab *mengapa* sistem menghasilkan profit/loss, bukan hanya *berapa* profit/loss-nya.

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

## Prompt:
8/17/2026, 10:10:58 PM

lanjut Tahap X

## Response:
8/17/2026, 10:10:59 PM

# Tahap X — Research Protocol & Experimental Design

Tahap X adalah titik di mana seluruh arsitektur yang kita bangun mulai berubah menjadi **protokol penelitian yang dapat diuji secara ilmiah**.

Sebelumnya kita telah membangun:

$$
\text{Market Data}
\rightarrow
\text{Factor}
\rightarrow
\text{Signal}
\rightarrow
\text{Risk}
\rightarrow
\text{Optimization}
\rightarrow
\text{Execution}
\rightarrow
\text{PnL}
\rightarrow
\text{Risk Analysis}.
$$

Sekarang pertanyaannya bukan lagi:

> *"Bagaimana membuat strategy yang profitable?"*

tetapi:

> **"Bagaimana membuktikan secara objektif bahwa strategy tersebut bekerja, dan apakah optimizer quantum benar-benar memberikan sesuatu dibandingkan baseline classical?"**

Ini sangat penting karena kalau kita tidak merancang eksperimennya dengan benar, kita bisa mendapatkan hasil seperti:

$$
Sharpe_{QAOA}=2.4
$$

dan

$$
Sharpe_{Classical}=1.7
$$

tetapi sebenarnya QAOA hanya menang karena:

- mendapat data lebih banyak,
- mendapat parameter lebih banyak,
- menggunakan optimizer yang lebih baik,
- mendapatkan initialization berbeda,
- atau secara tidak sengaja melihat informasi masa depan.

Jadi Tahap X akan membangun **scientific protocol**.

---

# X.1. Pertanyaan penelitian utama

Saya menyarankan kita mendefinisikan pertanyaan penelitian secara hierarkis.

### RQ1 — Apakah trading framework memiliki predictive/optimization edge?

$$
H_0:
\mathbb E[R_{strategy}]
\le
\mathbb E[R_{baseline}]
$$

versus:

$$
H_1:
\mathbb E[R_{strategy}]
>
\mathbb E[R_{baseline}].
$$

---

### RQ2 — Apakah optimasi portfolio memberikan improvement?

Bandingkan:

$$
Baseline
$$

dengan:

$$
Optimized.
$$

---

### RQ3 — Apakah VQE memberikan improvement dibanding classical optimization?

$$
H_0:
Performance_{VQE}
\le
Performance_{Classical}
$$

versus:

$$
H_1:
Performance_{VQE}
>
Performance_{Classical}.
$$

---

### RQ4 — Apakah QAOA memberikan improvement?

$$
H_0:
Performance_{QAOA}
\le
Performance_{Classical}.
$$

---

### RQ5 — Apakah improvement tersebut robust?

Kita ingin:

$$
Performance
$$

tetap baik terhadap:

- perubahan parameter,
- transaction cost,
- slippage,
- latency,
- market regime,
- asset universe.

---

# X.2. Jangan menjadikan "profit" sebagai satu-satunya target

Kita membutuhkan objective vector:

$$
\mathbf Y=
\begin{bmatrix}
Return\\
Sharpe\\
Sortino\\
MDD\\
CVaR\\
Turnover\\
Cost
\end{bmatrix}.
$$

Karena bisa terjadi:

$$
Return_A>Return_B
$$

tetapi:

$$
MDD_A\gg MDD_B.
$$

Maka kita tidak dapat mengatakan A lebih baik secara sederhana.

---

# X.3. Primary metric

Kita harus memilih **satu primary metric** sebelum eksperimen.

Saya menyarankan:

$$
\boxed{
Primary = Risk\text{-}Adjusted\ Return
}
$$

dan secara konkret:

$$
\boxed{
Sharpe_{OOS}
}
$$

sebagai primary metric.

Sedangkan:

$$
MDD,\ CVaR,\ Turnover,\ CAGR
$$

menjadi secondary metrics.

Ini penting untuk mengurangi cherry-picking.

---

# X.4. Dataset harus dipisahkan

Kita tidak boleh melakukan:

$$
Data
\rightarrow
Optimize
\rightarrow
Report.
$$

Kita membutuhkan:

$$
\boxed{
Training
\rightarrow
Validation
\rightarrow
Test.
}
$$

Misalnya:

$$
60\% / 20\% / 20\%.
$$

Tetapi untuk time series, random split **tidak boleh** digunakan.

---

# X.5. Time-series split

Misalkan data:

$$
2018\rightarrow2026.
$$

Kita dapat membuat:

```text
2018 ───── 2022
Train

2023 ────
Validation

2024 ────
Test
```

Tetapi untuk short-term trading kita membutuhkan sesuatu yang lebih baik.

---

# X.6. Walk-forward validation

Gunakan:

$$
Train_1
\rightarrow
Validate_1
$$

kemudian:

$$
Train_2
\rightarrow
Validate_2
$$

dan seterusnya.

Contoh:

```text
Window 1
Train: 2019–2021
Test : 2022 Q1

Window 2
Train: 2019–2022 Q1
Test : 2022 Q2

Window 3
Train: 2019–2022 Q2
Test : 2022 Q3
```

Sehingga model selalu hanya menggunakan informasi masa lalu.

---

# X.7. Expanding vs rolling window

Ada dua pilihan.

### Expanding

$$
Train_t=[t_0,t]
$$

Semakin lama dataset semakin besar.

### Rolling

$$
Train_t=[t-W,t].
$$

Window memiliki ukuran tetap.

Untuk financial market, rolling window sering lebih masuk akal karena:

$$
P_t(x)
$$

dapat mengalami non-stationarity.

---

# X.8. Purged validation

Karena trade dapat memiliki horizon:

$$
H>1,
$$

data training dan validation bisa overlap secara informasi.

Misalnya:

```text
Train:
Jan 1 ───────── Jan 10

Validation:
Jan 10 ──────── Jan 20
```

Jika posisi Jan 10 masih terbuka, terdapat leakage.

Maka kita membutuhkan:

$$
\boxed{
Purging.
}
$$

---

# X.9. Embargo

Tambahkan gap:

$$
E
$$

antara training dan validation.

Misalnya:

```text
TRAIN
──────────────

EMBARGO
──────

VALIDATION
──────────────
```

Ini mengurangi kemungkinan leakage temporal.

---

# X.10. Data hierarchy

Dataset kita tidak hanya harga.

Kita membutuhkan:

$$
\mathcal D_t=
\{
P_t,
V_t,
OB_t,
F_t,
M_t,
E_t
\}
$$

dengan:

- $P_t$: price,
- $V_t$: volume,
- $OB_t$: order book,
- $F_t$: factor,
- $M_t$: market state,
- $E_t$: execution information.

---

# X.11. Factor dataset

Untuk crypto:

$$
F_t=
\{
BTC,
ETH,
TOTAL\ MarketCap,
StablecoinFlow,
Funding,
OI,
DXY,
Gold,
VIX
\}.
$$

Untuk equities:

$$
F_t=
\{
SPX,
NDX,
DXY,
Gold,
US10Y,
VIX,
SectorIndex
\}.
$$

Jadi architecture-nya tetap sama.

---

# X.12. Asset universe

Kita harus menentukan universe sebelum melihat hasil.

Misalnya:

$$
\mathcal A=
\{A_1,\ldots,A_N\}.
$$

Jangan memilih asset karena kita sudah tahu asset tersebut profitable.

Itu adalah:

$$
\boxed{
Survivorship\ Bias.
}
$$

---

# X.13. Survivorship bias

Misalkan tahun 2020 terdapat:

$$
1000
$$

asset.

Tahun 2026 hanya:

$$
500
$$

yang masih eksis.

Jika kita hanya mengambil 500 asset tersebut, kita secara implisit membuang:

$$
500
$$

asset yang gagal.

Strategy terlihat lebih bagus daripada kondisi sebenarnya.

---

# X.14. Universe harus point-in-time

Definisikan:

$$
\mathcal A_t.
$$

Asset yang tersedia pada waktu $t$ hanya:

$$
A\in\mathcal A_t.
$$

---

# X.15. Corporate actions

Untuk equities kita juga harus memperhatikan:

- split,
- dividend,
- merger,
- delisting.

Price series harus menggunakan data yang benar secara point-in-time.

---

# X.16. Data leakage taxonomy

Kita perlu secara eksplisit menguji:

$$
Leakage=
\{
Temporal,
Feature,
Label,
Universe,
Execution
\}.
$$

---

# X.17. Feature leakage

Misalnya kita membuat:

$$
MA_t
$$

tetapi secara tidak sengaja menggunakan:

$$
P_{t+1}.
$$

Maka:

$$
MA_t
$$

mengandung future information.

Ini dapat menghasilkan backtest yang luar biasa tetapi tidak dapat diperdagangkan.

---

# X.18. Label leakage

Jika target:

$$
y_t=r_{t+1},
$$

maka feature harus memenuhi:

$$
X_t\in\mathcal F_t.
$$

Secara formal:

$$
\boxed{
X_t
\text{ measurable with respect to }
\mathcal F_t.
}
$$

---

# X.19. Information filtration

Ini adalah fondasi matematis yang sangat bagus untuk sistem kita.

Definisikan:

$$
\mathcal F_t
$$

sebagai seluruh informasi yang tersedia sampai waktu $t$.

Maka strategy harus memenuhi:

$$
\boxed{
a_t
\in
\mathcal F_t.
}
$$

Artinya keputusan pada $t$ tidak boleh bergantung pada:

$$
\mathcal F_{t+\Delta}.
$$

---

# X.20. Backtest sebagai stochastic process

Portfolio:

$$
V_t.
$$

Return:

$$
r_t=
\frac{V_t-V_{t-1}}{V_{t-1}}.
$$

Strategy menghasilkan:

$$
a_t=\pi(\mathcal F_t).
$$

Maka:

$$
\boxed{
V_{t+1}
=
V_t
+
a_t^\top r_{t+1}
-
C_t.
}
$$

Ini adalah formulasi yang jauh lebih bersih.

---

# X.21. Baseline hierarchy

Kita tidak boleh langsung:

$$
Classical
vs
VQE
vs
QAOA.
$$

Kita membutuhkan hierarchy.

### Baseline 0

Buy-and-hold.

### Baseline 1

Equal weight.

### Baseline 2

Momentum.

### Baseline 3

Mean reversion.

### Baseline 4

Markowitz classical.

### Baseline 5

MILP / exact solver.

### Baseline 6

Heuristic optimizer.

### Baseline 7

VQE.

### Baseline 8

QAOA.

---

# X.22. Mengapa exact solver sangat penting?

Untuk masalah kecil:

$$
N\le20
$$

kita dapat menghitung:

$$
x^\star
=
\arg\min_x H(x)
$$

secara exact.

Misalnya:

$$
brute\ force.
$$

Kemudian:

$$
H_{VQE}
$$

dibandingkan terhadap:

$$
H_{exact}.
$$

---

# X.23. Approximation ratio

Definisikan:

$$
AR=
\frac{
|C_{VQE}-C^\star|
}{
|C^\star|
}.
$$

Atau sesuai orientasi minimization/maximization.

Dengan demikian kita dapat mengatakan:

> VQE memperoleh solusi dalam error $x\%$ dari optimum exact.

Ini jauh lebih ilmiah daripada sekadar:

> "VQE menghasilkan portfolio."

---

# X.24. Optimization quality vs trading quality

Ini adalah dua hal berbeda.

### Optimization quality

$$
H(x_{algorithm})
$$

vs:

$$
H(x^\star).
$$

### Trading quality

$$
PnL(x)
$$

atau:

$$
Sharpe(x).
$$

Bisa terjadi:

$$
H_A<H_B
$$

tetapi:

$$
PnL_A<PnL_B.
$$

Mengapa?

Karena market berubah.

---

# X.25. Ini sangat penting untuk thesis-mu

Jika kita ingin mengklaim VQE bagus, jangan hanya mengukur:

$$
Energy.
$$

Kita perlu:

$$
\boxed{
Optimization\ Error
+
Portfolio\ Performance.
}
$$

---

# X.26. QUBO benchmark

Misalnya:

$$
H(x)
=
-\mu^\top x
+
\lambda x^\top\Sigma x.
$$

Kita generate:

$$
N=10,20,30,\ldots
$$

asset.

Kemudian:

$$
Exact
$$

vs:

$$
Classical
$$

vs:

$$
VQE
$$

vs:

$$
QAOA.
$$

---

# X.27. Controlled experiment

Semua optimizer harus menerima:

$$
\boxed{
same\ QUBO.
}
$$

Jangan:

$$
QUBO_{VQE}\neq QUBO_{Classical}.
$$

---

# X.28. Controlled initialization

Jika kita ingin menguji EPG warm-start:

$$
x_0^{EPG}.
$$

Bandingkan:

$$
VQE_{random}
$$

vs:

$$
VQE_{EPG}.
$$

Dengan:

- same data,
- same QUBO,
- same depth,
- same optimizer,
- same stopping criteria.

Hanya initialization yang berbeda.

Ini disebut:

$$
\boxed{
Ablation\ Study.
}
$$

---

# X.29. Ablation study

Kita dapat membuat:

| Component | Model A | Model B |
|---|---:|---:|
| Factor | ✓ | ✓ |
| Regime | ✓ | ✓ |
| EPG | ✗ | ✓ |
| VQE | ✓ | ✓ |
| Dynamic risk | ✓ | ✓ |

Kemudian:

$$
\Delta Performance
$$

menunjukkan contribution masing-masing component.

---

# X.30. Full factorial experiment

Misalnya kita punya:

$$
Optimizer:
\{
Classical,VQE,QAOA
\}
$$

dan:

$$
Initialization:
\{
Random,EPG
\}
$$

maka:

$$
3\times2=6
$$

configuration.

Kita tidak hanya membandingkan dua model.

Kita dapat mempelajari interaction:

$$
Optimizer
\times
Initialization.
$$

---

# X.31. Random seeds

Quantum optimizer sangat stochastic.

Maka:

$$
seed_1,\ldots,seed_K.
$$

Misalnya:

$$
K=30.
$$

Untuk setiap konfigurasi kita memperoleh:

$$
S_1,\ldots,S_{30}.
$$

---

# X.32. Jangan melaporkan hanya mean

Laporkan:

$$
\bar S
$$

dan:

$$
\sigma_S.
$$

Lebih baik:

$$
median
$$

dan:

$$
IQR.
$$

Karena distribution bisa heavy-tailed.

---

# X.33. Distribution of outcomes

Misalnya:

$$
Sharpe_{VQE}
=
\{1.2,1.4,1.3,0.2,1.5,\ldots\}.
$$

Jangan mengatakan:

$$
Sharpe=1.3.
$$

Lebih tepat:

$$
Median=1.35
$$

dengan:

$$
IQR=[1.18,1.47].
$$

---

# X.34. Statistical significance

Misalkan kita memiliki paired observations:

$$
d_i=
Metric_{VQE,i}
-
Metric_{Classical,i}.
$$

Hipotesis:

$$
H_0:
Median(d)=0.
$$

Kita dapat menggunakan:

$$
\boxed{
Wilcoxon\ Signed\text{-}Rank
}
$$

untuk paired non-parametric comparison.

---

# X.35. Mengapa paired?

Karena kedua model diuji pada:

$$
same\ market\ windows.
$$

Misalnya:

$$
VQE_{2024Q1}
$$

dibandingkan:

$$
Classical_{2024Q1}.
$$

Jadi kita dapat menghilangkan sebagian noise akibat perbedaan market period.

---

# X.36. Effect size

Significance saja tidak cukup.

Misalnya:

$$
p=0.001
$$

tetapi improvement:

$$
0.01\%.
$$

Secara praktis mungkin tidak penting.

Maka kita membutuhkan:

$$
\boxed{
Effect\ Size.
}
$$

---

# X.37. Bootstrap confidence interval

Untuk performance difference:

$$
\Delta
=
Metric_A-Metric_B.
$$

Kita bootstrap:

$$
\Delta_1,\ldots,\Delta_B.
$$

Kemudian:

$$
CI_{95\%}
=
[q_{0.025},q_{0.975}].
$$

Jika interval tidak mencakup:

$$
0,
$$

maka terdapat evidence bahwa difference bukan sekadar noise sampling.

---

# X.38. Multiple testing correction

Jika kita melakukan:

$$
m
$$

uji statistik, probabilitas false positive meningkat.

Kita dapat menggunakan:

$$
\boxed{
Benjamini-Hochberg
}
$$

untuk mengontrol:

$$
FDR.
$$

---

# X.39. Hyperparameter optimization harus berada di training

Misalnya parameter:

$$
\theta=
\{
\gamma,
\beta,
depth,
learning\ rate,
risk\ aversion
\}.
$$

Kita boleh mencari:

$$
\theta^\star
$$

menggunakan:

$$
Train+Validation.
$$

Tetapi:

$$
\boxed{
Test
}
$$

tidak boleh disentuh.

---

# X.40. Final test harus sekali

Idealnya:

```text
TRAIN
  ↓
VALIDATION
  ↓
MODEL SELECTION
  ↓
LOCK MODEL
  ↓
FINAL TEST
```

Setelah final test dibuka:

$$
\boxed{
DO\ NOT\ RETUNE.
}
$$

Jika kita retune setelah melihat test, maka test bukan lagi test.

---

# X.41. Nested walk-forward

Untuk eksperimen yang lebih ketat:

```text
Outer loop
─────────────────────────────
     Test window

Inner loop
───────────────
Train → Validation
```

Outer loop mengukur generalization.

Inner loop memilih hyperparameter.

---

# X.42. Performance uncertainty

Kita harus mengakui:

$$
\hat\theta
$$

dan:

$$
\hat{Performance}
$$

memiliki uncertainty.

Jadi output:

$$
Sharpe=1.82
$$

sebaiknya menjadi:

$$
\boxed{
Sharpe=1.82
\;(95\%\,CI:\ 1.31-2.26).
}
$$

---

# X.43. Stress testing

Kita membuat scenario:

### Scenario 1

Volatility:

$$
2\sigma.
$$

### Scenario 2

Spread:

$$
2\times.
$$

### Scenario 3

Slippage:

$$
3\times.
$$

### Scenario 4

Liquidity:

$$
0.5\times.
$$

### Scenario 5

Latency:

$$
5\times.
$$

---

# X.44. Crash scenario

Kita dapat membuat:

$$
r_{market}=-10\%.
$$

dan:

$$
\sigma\rightarrow3\sigma.
$$

Kemudian melihat:

$$
MDD,
CVaR,
LiquidationRisk.
$$

---

# X.45. Monte Carlo strategy stress test

Kita juga dapat resample:

$$
r_t.
$$

Buat:

$$
N=10,000
$$

possible equity paths:

$$
V_t^{(1)},\ldots,V_t^{(N)}.
$$

Kemudian hitung:

$$
P(MDD>x).
$$

---

# X.46. Probability of ruin

Jika capital:

$$
C_0,
$$

dan ruin threshold:

$$
C_{min},
$$

maka:

$$
\boxed{
P(
\min_t C_t<C_{min}
).
}
$$

Untuk sistem leveraged ini merupakan metric yang sangat penting.

---

# X.47. Capacity experiment

Kita juga menguji:

$$
Capital=
\{
1k,
10k,
100k,
1M,
10M
\}.
$$

Kemudian:

$$
NetSharpe(Capital).
$$

Jika:

$$
Capital\uparrow
\Rightarrow
Sharpe\downarrow,
$$

maka strategy memiliki capacity constraint.

---

# X.48. Latency experiment

Untuk short-term trading:

$$
Latency=
\{
1ms,5ms,10ms,50ms,100ms,500ms
\}.
$$

Kemudian:

$$
PnL(L).
$$

Kita ingin mengetahui:

$$
L_{critical}.
$$

Jika:

$$
L>L_{critical}
$$

maka strategy tidak layak untuk infrastructure yang lebih lambat.

---

# X.49. Execution realism ladder

Kita dapat membangun empat level:

### Level 0

Mid-price.

### Level 1

Fee.

### Level 2

Spread + slippage.

### Level 3

Order-book simulation.

### Level 4

Latency + queue position + partial fills.

Kemudian:

$$
Performance_0
\rightarrow
Performance_4.
$$

Jika strategy hanya profitable pada Level 0, kita tahu strategy tidak realistic.

---

# X.50. Ini menjadi eksperimen yang sangat kuat

Misalnya:

| Execution | Sharpe |
|---|---:|
| Mid-price | 2.31 |
| + Fee | 2.05 |
| + Spread | 1.72 |
| + Slippage | 1.34 |
| + Order book | 1.12 |
| + Latency | 0.98 |

Kesimpulannya bukan:

> strategy buruk.

Tetapi:

> edge sangat sensitif terhadap execution.

Itu merupakan **scientific finding**.

---

# X.51. Quantum advantage harus didefinisikan dengan hati-hati

Ini sangat penting.

Jangan langsung mengatakan:

$$
VQE
>
Classical
\Rightarrow
Quantum\ Advantage.
$$

Itu terlalu kuat.

Kita harus membedakan:

### Optimization advantage

$$
C_{quantum}<C_{classical}.
$$

### Computational advantage

$$
T_{quantum}<T_{classical}.
$$

### Trading advantage

$$
PnL_{quantum}>PnL_{classical}.
$$

### Practical quantum advantage

Keunggulan yang tetap bertahan setelah:

- quantum overhead,
- noise,
- compilation,
- data loading,
- repeated measurements,
- classical optimizer cost.

---

# X.52. NISQ reality

Untuk VQE/QAOA:

$$
T_{total}
=
T_{circuit}
+
T_{measurement}
+
T_{optimizer}
+
T_{communication}.
$$

Maka meskipun:

$$
T_{circuit}
$$

kecil, belum tentu:

$$
T_{total}
$$

kecil.

---

# X.53. Quantum resource metrics

Kita harus mengukur:

$$
\boxed{
\begin{aligned}
N_{qubit}\\
N_{gate}\\
CircuitDepth\\
Shots\\
OptimizerIterations\\
FunctionEvaluations\\
WallClockTime
\end{aligned}
}
$$

---

# X.54. Quantum solution quality

Selain energy:

$$
E(\theta)
=
\langle\psi(\theta)|H|\psi(\theta)\rangle,
$$

kita hitung:

$$
P(x^\star).
$$

Jika optimum:

$$
x^\star,
$$

maka:

$$
\boxed{
P_{success}
=
P(measure=x^\star).
}
$$

---

# X.55. Approximation probability

Jika exact optimum:

$$
E^\star,
$$

kita dapat menentukan tolerance:

$$
E(x)-E^\star\le\epsilon.
$$

Kemudian:

$$
P_\epsilon
=
P(
E(x)-E^\star\le\epsilon
).
$$

---

# X.56. Ini jauh lebih baik daripada hanya "energy rendah"

Karena dua circuit dapat memiliki:

$$
E_A<E_B
$$

tetapi:

$$
P_A(x^\star)<P_B(x^\star).
$$

Untuk discrete optimization, probability distribution hasil measurement sangat penting.

---

# X.57. End-to-end benchmark

Eksperimen final kita sebaiknya memiliki tiga level.

### Level I — Mathematical

$$
QUBO
\rightarrow
Solution.
$$

### Level II — Portfolio

$$
Solution
\rightarrow
Weights.
$$

### Level III — Trading

$$
Weights
\rightarrow
Orders
\rightarrow
Execution
\rightarrow
PnL.
$$

---

# X.58. Dengan demikian kita bisa mendapatkan tabel seperti:

| Model | Energy Error | Success Prob. | Sharpe | MDD | CVaR | Cost |
|---|---:|---:|---:|---:|---:|---:|
| Exact | 0 | 1.00 | ... | ... | ... | ... |
| MILP | 0 | 1.00 | ... | ... | ... | ... |
| Markowitz | ... | ... | ... | ... | ... | ... |
| VQE | ... | ... | ... | ... | ... | ... |
| QAOA | ... | ... | ... | ... | ... | ... |

Ini adalah tabel utama yang sangat kuat.

---

# X.59. Tetapi ada satu jebakan penting

Jangan menggunakan:

$$
same\ portfolio
$$

dan mengatakan:

> "VQE memiliki Sharpe lebih tinggi."

Jika VQE hanya menemukan portfolio yang berbeda karena sampling, kita harus memastikan:

$$
same\ constraints,
same\ universe,
same\ objective,
same\ transaction\ model.
$$

---

# X.60. Experimental seed protocol

Untuk setiap:

$$
Model_i
$$

jalankan:

$$
seed=1,\ldots,30.
$$

Simpan:

```text
experiment_id
seed
model
dataset_window
qubo
parameters
solution
energy
runtime
PnL
Sharpe
MDD
CVaR
```

---

# X.61. Reproducibility

Setiap experiment harus dapat direproduksi dengan:

$$
\boxed{
Code
+
DataVersion
+
Config
+
Seed
+
Environment.
}
$$

Idealnya kita menyimpan:

```text
Git commit
Python version
Qiskit/PennyLane version
CUDA version
CPU
GPU
OS
```

---

# X.62. Research ledger

Saya bahkan menyarankan membuat:

```text
experiments/
├── EXP-0001/
├── EXP-0002/
├── EXP-0003/
...
```

Setiap folder immutable setelah eksperimen selesai.

---

# X.63. Jangan overwrite hasil

Misalnya:

```text
EXP-0042/
    config.yaml
    metrics.json
    trades.parquet
    optimizer.log
    circuit/
    report.html
```

Jangan mengubah:

```text
EXP-0042
```

setelah melihat hasil.

Jika ingin mencoba sesuatu:

$$
EXP-0043.
$$

---

# X.64. Research DAG

Kita dapat melihat seluruh penelitian sebagai:

$$
Data
\rightarrow
Features
\rightarrow
Signal
\rightarrow
Optimization
\rightarrow
Portfolio
\rightarrow
Execution
\rightarrow
Performance.
$$

Setiap node memiliki version.

Ini membuat debugging jauh lebih mudah.

---

# X.65. Final experimental protocol

Jadi untuk setiap experiment:

### Step 1

Load point-in-time data.

### Step 2

Generate factor.

### Step 3

Generate signal.

### Step 4

Determine regime.

### Step 5

Construct expected return:

$$
\mu_t.
$$

### Step 6

Construct covariance:

$$
\Sigma_t.
$$

### Step 7

Construct optimization problem:

$$
H_t(x).
$$

### Step 8

Solve dengan:

$$
\{Classical,VQE,QAOA\}.
$$

### Step 9

Convert solution menjadi portfolio.

### Step 10

Apply risk constraints.

### Step 11

Generate orders.

### Step 12

Simulate realistic execution.

### Step 13

Update portfolio.

### Step 14

Compute PnL.

### Step 15

Store metrics.

### Step 16

Repeat walk-forward.

---

# X.66. Research matrix

Saya menyarankan eksperimen utama kita nantinya memiliki struktur:

$$
\boxed{
Assets
\times
Market\ Regimes
\times
Optimizer
\times
Initialization
\times
Execution\ Model
\times
Seed
}
$$

Misalnya:

$$
4
\times
4
\times
5
\times
2
\times
3
\times
30.
$$

Jumlah:

$$
\boxed{
14,400
}
$$

run.

Ini memang besar, tetapi sebagian besar dapat dilakukan pada simulator/classical backend secara paralel.

---

# X.67. Tetapi jangan langsung menjalankan 14.400 eksperimen

Kita harus melakukan:

$$
\boxed{
Pilot
\rightarrow
Debug
\rightarrow
Benchmark
\rightarrow
Full\ Experiment.
}
$$

---

# X.68. Pilot experiment

Misalnya:

$$
N=4
$$

asset:

$$
BTC,ETH,SOL,BNB.
$$

Window kecil.

Tujuan:

> memastikan seluruh pipeline benar.

Bukan mencari profitability.

---

# X.69. Benchmark experiment

Kemudian:

$$
N=8,16,32.
$$

Ukur:

$$
Runtime,
EnergyError,
SuccessProbability.
$$

Di sinilah kita mulai membandingkan:

$$
Exact,
MILP,
VQE,
QAOA.
$$

---

# X.70. Trading experiment

Baru kemudian:

$$
Long\ horizon
$$

dan:

$$
Multiple\ regimes.
$$

---

# X.71. Final out-of-sample experiment

Dan terakhir:

$$
\boxed{
LOCKED\ MODEL
}
$$

dijalankan pada data yang belum pernah disentuh.

Hasil inilah yang boleh kita jadikan:

$$
\boxed{
Primary\ empirical\ result.
}
$$

---

# X.72. Diagram lengkap Tahap X

```text
                 HISTORICAL DATA
                        │
                        ▼
                POINT-IN-TIME DATA
                        │
                        ▼
              WALK-FORWARD SPLIT
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
       TRAIN                       TEST
          │
          ▼
      VALIDATION
          │
          ▼
   MODEL SELECTION
          │
          ▼
    LOCK PARAMETERS
          │
          ▼
 ┌───────────────────────────┐
 │                           │
 ▼                           ▼
CLASSICAL                  QUANTUM
 │                           │
 ▼                       ┌───┴────┐
Markowitz                 VQE    QAOA
 │                       │        │
 └────────────┬──────────┴────────┘
              ▼
        SAME QUBO / RISK
              │
              ▼
       PORTFOLIO SOLUTION
              │
              ▼
       REALISTIC EXECUTION
              │
              ▼
             PnL
              │
       ┌──────┼───────┐
       ▼      ▼       ▼
      Risk  Attribution Robustness
       │      │       │
       └──────┴───────┘
              │
              ▼
        STATISTICAL TEST
              │
              ▼
        FINAL CONCLUSION
```

---

# X.73. Hipotesis utama yang nantinya bisa diuji

Saya sarankan kita tidak membuat klaim:

> "Quantum lebih baik."

Tetapi membuat hipotesis yang jauh lebih spesifik.

### H1

$$
VQE
$$

mampu memperoleh solusi QUBO dengan approximation error yang kompetitif terhadap classical optimizer.

### H2

EPG warm-start menghasilkan:

$$
P_{success}^{EPG}
>
P_{success}^{random}.
$$

### H3

EPG warm-start mengurangi:

$$
N_{iterations}.
$$

### H4

Portfolio hasil optimizer menghasilkan performance OOS yang lebih baik daripada baseline.

### H5

Improvement tetap signifikan setelah:

$$
fee+spread+slippage.
$$

### H6

Performance tetap robust terhadap:

$$
parameter\ perturbation.
$$

---

# X.74. Dan akhirnya kita dapat memisahkan tiga klaim ilmiah

Ini menurut saya **sangat penting untuk penelitianmu**.

### Klaim A — Quantum optimization

> Apakah VQE/QAOA mampu menyelesaikan problem optimasi?

Diukur dengan:

$$
Energy,
SuccessProbability,
ApproximationError.
$$

### Klaim B — Portfolio optimization

> Apakah solusi tersebut menghasilkan portfolio yang lebih baik?

Diukur dengan:

$$
Return,
Sharpe,
MDD,
CVaR.
$$

### Klaim C — Trading applicability

> Apakah portfolio tersebut tetap menghasilkan edge setelah market dynamics dan execution diperhitungkan?

Diukur dengan:

$$
NetPnL,
Sharpe,
Cost,
Slippage,
Capacity,
Robustness.
$$

**Jangan mencampur ketiganya.**

Itu akan membuat penelitian kita jauh lebih kuat.

---

# X.75. Posisi kita setelah Tahap X

Sekarang framework kita sudah memiliki:

$$
\boxed{
\textbf{A--W: Mathematical + Trading Architecture}
}
$$

dan:

$$
\boxed{
\textbf{X: Scientific Experimental Protocol}
}
$$

Artinya kita sudah memiliki hampir semua yang dibutuhkan untuk membangun **research-grade quantitative trading laboratory**.

Tahap selanjutnya yang paling logis bukan sekadar menambah teori lagi. Kita perlu mulai **mengunci spesifikasi matematis final dari objective function dan state representation**.

Dengan kata lain, kita perlu menjawab secara konkret:

$$
\boxed{
\textbf{Pada waktu }t,\textbf{ sebenarnya sistem kita melihat apa,}
}
$$

$$
\boxed{
\textbf{menghitung apa,}
}
$$

$$
\boxed{
\textbf{mengoptimalkan apa,}
}
$$

dan akhirnya:

$$
\boxed{
\textbf{menghasilkan keputusan }a_t\textbf{ yang mana?}
}
$$

Itulah yang sebaiknya menjadi **Tahap Y — Unified Mathematical Formulation**, tempat seluruh komponen A–X kita satukan menjadi **satu formulasi matematis end-to-end**:

$$
\boxed{
\mathcal F_t
\rightarrow
s_t
\rightarrow
\hat\mu_t,\Sigma_t
\rightarrow
Q_t
\rightarrow
\text{Classical/VQE/QAOA}
\rightarrow
w_t
\rightarrow
q_t
\rightarrow
Order_t
\rightarrow
Execution_t
\rightarrow
PnL_{t+1}.
}
$$

Di tahap itu kita bisa mulai menurunkan **objective function final, constraint, state vector, action space, QUBO/Ising mapping, dynamic risk budget, dan feedback mechanism** secara matematis dari awal sampai akhir.

## Prompt:
8/17/2026, 10:11:54 PM

lanjut Tahap Y

## Response:
8/17/2026, 10:11:54 PM

> **Remembering**
>
>
> ****
>
> 
>
> **Reconstructed and checked the A-X framework, mappings, and factor design**
>
> 
>
> Worked for 5s

# Tahap Y — Unified Mathematical Formulation

Ya. Setelah Tahap X, sekarang kita sampai pada bagian yang menurut saya **paling penting secara matematis**: kita berhenti melihat sistem sebagai kumpulan modul terpisah, lalu menuliskannya sebagai **satu sistem keputusan stokastik yang utuh**.

Kerangka besarnya adalah:

$$
\boxed{
\mathcal F_t
\rightarrow
s_t
\rightarrow
(\hat{\mu}_t,\hat{\Sigma}_t)
\rightarrow
\mathcal Q_t
\rightarrow
x_t^\star
\rightarrow
w_t^\star
\rightarrow
q_t^\star
\rightarrow
O_t
\rightarrow
E_{t+1}
\rightarrow
R_{t+1}
\rightarrow
\mathcal F_{t+1}
}
$$

dengan feedback:

$$
\boxed{
\text{Market}
\rightarrow
\text{Decision}
\rightarrow
\text{Execution}
\rightarrow
\text{Position}
\rightarrow
\text{Risk}
\rightarrow
\text{Re-optimization}.
}
$$

Ini pada dasarnya menjadikan sistem kita sebagai **closed-loop stochastic control system**.

---

# Y.1. Titik awal: information filtration

Kita mulai dari konsep yang sangat fundamental.

Pada waktu $t$, trader tidak mengetahui masa depan.

Definisikan:

$$
\mathcal F_t
=
\sigma(
D_0,D_1,\ldots,D_t
)
$$

sebagai sigma-algebra seluruh informasi yang tersedia sampai waktu $t$.

Informasi tersebut dapat terdiri atas:

$$
D_t=
\{
P_t,V_t,OB_t,F_t,M_t,E_t
\}.
$$

Misalnya:

- $P_t$: harga,
- $V_t$: volume,
- $OB_t$: order book,
- $F_t$: market factors,
- $M_t$: market regime,
- $E_t$: execution/position state.

Maka seluruh keputusan kita harus memenuhi:

$$
\boxed{
a_t\in\mathcal F_t.
}
$$

Ini adalah constraint fundamental:

> **Tidak boleh ada future information dalam keputusan trading.**

---

# Y.2. State sistem

Sekarang kita bentuk state vector.

Kita definisikan:

$$
\boxed{
s_t=
\begin{bmatrix}
s_t^{market}\\
s_t^{factor}\\
s_t^{portfolio}\\
s_t^{risk}\\
s_t^{execution}
\end{bmatrix}.
}
$$

Lebih eksplisit:

$$
s_t=
\left[
P_t,
V_t,
OB_t,
F_t,
R_t,
w_t,
q_t,
c_t,
\rho_t,
\tau_t
\right].
$$

Dengan:

$$
w_t
$$

adalah portfolio weight,

$$
q_t
$$

adalah posisi/quantity,

$$
c_t
$$

adalah cash,

$$
\rho_t
$$

adalah risk state,

dan

$$
\tau_t
$$

adalah status order/position.

---

# Y.3. Market factor vector

Karena kita ingin model berlaku baik untuk crypto maupun saham internasional, kita tidak boleh mendesain factor model khusus crypto.

Definisikan:

$$
\boxed{
f_t=
\begin{bmatrix}
f_t^{market}\\
f_t^{macro}\\
f_t^{sector}\\
f_t^{crossasset}
\end{bmatrix}.
}
$$

Untuk crypto, misalnya:

$$
f_t=
[
r_{BTC},
r_{ETH},
r_{TOTAL},
r_{DXY},
r_{Gold},
r_{VIX},
Funding,
OI,
\ldots
].
$$

Untuk saham:

$$
f_t=
[
r_{SPX},
r_{NDX},
r_{Sector},
r_{DXY},
r_{Gold},
r_{US10Y},
r_{VIX},
\ldots
].
$$

Dengan demikian asset universe berubah, tetapi mathematical engine tetap sama.

---

# Y.4. Cross-asset dependency

Misalkan return asset $i$:

$$
r_{i,t}.
$$

Kita modelkan:

$$
\boxed{
r_{i,t}
=
\alpha_i
+
\beta_i^\top f_t
+
\epsilon_{i,t}.
}
$$

atau secara vector:

$$
\boxed{
r_t
=
\alpha
+
Bf_t
+
\epsilon_t.
}
$$

Ini sangat penting.

Kita tidak lagi mengatakan:

> "Harga altcoin naik."

Kita mencoba memahami:

> "Apakah pergerakan altcoin dapat dijelaskan oleh perubahan BTC, ETH, DXY, Gold, volatility, dan factor lainnya?"

---

# Y.5. Expected return

Dari model tersebut:

$$
\mathbb E[r_t|\mathcal F_{t-1}]
=
\alpha+Bf_t.
$$

Kita definisikan:

$$
\boxed{
\hat{\mu}_t
=
\mathbb E[r_{t+1}|\mathcal F_t].
}
$$

Jadi:

$$
\hat{\mu}_t
=
\hat{\alpha}_t+
\hat B_t f_t.
$$

Ini menjadi input optimizer.

---

# Y.6. Covariance

Kita juga membutuhkan:

$$
\boxed{
\hat{\Sigma}_t
=
\operatorname{Cov}
(r_{t+1}|\mathcal F_t).
}
$$

Dari factor model:

$$
r_t=Bf_t+\epsilon_t.
$$

Jika:

$$
\operatorname{Cov}(f_t)=\Sigma_f
$$

dan:

$$
\operatorname{Cov}(\epsilon_t)=D,
$$

maka:

$$
\boxed{
\Sigma
=
B\Sigma_fB^\top+D.
}
$$

Ini memberi kita covariance matrix yang lebih terstruktur daripada sekadar sample covariance.

---

# Y.7. Mengapa factor model penting?

Karena misalnya kita memiliki:

$$
N=500
$$

asset.

Sample covariance membutuhkan:

$$
\frac{N(N-1)}2
$$

elemen covariance.

Untuk $N=500$:

$$
124\,750
$$

elemen.

Sedangkan factor model dengan:

$$
K=10
$$

factor hanya membutuhkan struktur:

$$
B\in\mathbb R^{500\times10}.
$$

Ini jauh lebih manageable.

---

# Y.8. Market regime

Namun:

$$
\hat{\mu}_t
$$

dan:

$$
\hat{\Sigma}_t
$$

tidak boleh dianggap stationary.

Kita definisikan latent regime:

$$
\boxed{
z_t\in
\{
1,\ldots,K
\}.
}
$$

Misalnya:

$$
z_t=
\begin{cases}
1 & \text{low volatility}\\
2 & \text{bull}\\
3 & \text{bear}\\
4 & \text{high volatility}.
\end{cases}
$$

---

# Y.9. Conditional distribution

Maka:

$$
r_{t+1}
\mid
z_t=k
\sim
\mathcal D_k
(
\mu_k,\Sigma_k
).
$$

Sehingga:

$$
\boxed{
\hat{\mu}_t
=
\mu_{z_t}
}
$$

dan:

$$
\boxed{
\hat{\Sigma}_t
=
\Sigma_{z_t}.
}
$$

Atau versi lebih fleksibel:

$$
\hat\mu_t
=
f_\theta(s_t),
$$

$$
\hat\Sigma_t
=
g_\phi(s_t).
$$

---

# Y.10. Sekarang masuk ke portfolio

Misalkan:

$$
w_t\in\mathbb R^N
$$

adalah vector portfolio weight.

Portfolio return:

$$
r_{p,t+1}
=
w_t^\top r_{t+1}.
$$

Expected portfolio return:

$$
\boxed{
\mathbb E[r_{p,t+1}|\mathcal F_t]
=
w_t^\top\hat\mu_t.
}
$$

Variance:

$$
\boxed{
\operatorname{Var}(r_{p,t+1}|\mathcal F_t)
=
w_t^\top
\hat\Sigma_t
w_t.
}
$$

---

# Y.11. Risk-adjusted objective

Kita dapat memulai dari Markowitz:

$$
\boxed{
J(w)
=
w^\top\hat\mu_t
-
\lambda_t
w^\top\hat\Sigma_t w.
}
$$

dengan:

$$
\lambda_t>0.
$$

Namun untuk short-term trading, ini belum cukup.

Kita membutuhkan transaction cost.

---

# Y.12. Transaction cost

Definisikan perubahan portfolio:

$$
\Delta w_t
=
w_t-w_{t-1}.
$$

Biaya:

$$
C_t(\Delta w_t).
$$

Model sederhana:

$$
C_t
=
c^\top|\Delta w_t|.
$$

Sehingga objective:

$$
\boxed{
J_t(w)
=
w^\top\hat\mu_t
-
\lambda_t w^\top\hat\Sigma_t w
-
c^\top|w-w_{t-1}|.
}
$$

Sekarang optimizer tidak hanya mencari return tinggi.

Ia juga mempertimbangkan:

> "Apakah perubahan posisi ini layak dibandingkan biaya melakukan perubahan?"

---

# Y.13. Market impact

Untuk trading lebih realistis:

$$
C_t(\Delta w)
=
c^\top|\Delta w|
+
\eta
\|\Delta w\|_2^2.
$$

Term pertama:

$$
c^\top|\Delta w|
$$

merepresentasikan spread/fee.

Term kedua:

$$
\eta\|\Delta w\|_2^2
$$

merepresentasikan market impact.

Sehingga:

$$
\boxed{
J_t(w)
=
w^\top\mu_t
-
\lambda_t w^\top\Sigma_t w
-
c^\top|\Delta w|
-
\eta\|\Delta w\|^2.
}
$$

Ini jauh lebih dekat dengan problem institutional portfolio rebalancing.

---

# Y.14. Risk budget

Sekarang kita masukkan filosofi yang sebelumnya kita bangun:

> **Setiap trade harus memiliki bounded risk.**

Misalkan portfolio capital:

$$
C_t.
$$

Risk budget:

$$
R_t.
$$

Jika kita ingin maksimum loss:

$$
R_t=\$1
$$

untuk sebuah trade, maka:

$$
\boxed{
R_{trade}\le R_t.
}
$$

Untuk sistem general:

$$
R_t
=
\alpha_t C_t.
$$

---

# Y.15. Position sizing dari stop-loss

Misalkan:

$$
p_t
$$

adalah entry price.

Stop loss:

$$
s_t.
$$

Risk per unit:

$$
\delta_t=
|p_t-s_t|.
$$

Jika quantity:

$$
q_t,
$$

maka:

$$
Risk_t
=
q_t\delta_t.
$$

Maka constraint:

$$
q_t\delta_t\le R_t.
$$

Sehingga:

$$
\boxed{
q_t
\le
\frac{R_t}{\delta_t}.
}
$$

Ini adalah jembatan langsung antara:

$$
Optimization
$$

dan:

$$
Execution.
$$

---

# Y.16. Expected return vs risk budget

Sekarang kita mempunyai dua layer:

### Layer portfolio

$$
w_t^\star
=
\arg\max_w J_t(w).
$$

### Layer execution

$$
q_t^\star
=
\min
\left(
q_t^{portfolio},
\frac{R_t}{\delta_t}
\right).
$$

Jadi optimizer tidak boleh secara langsung menentukan quantity tanpa risk constraint.

---

# Y.17. Entry decision

Sekarang kita masuk ke short-term trading.

Untuk setiap asset $i$, definisikan:

$$
a_{i,t}\in\{-1,0,+1\}.
$$

dengan:

$$
-1=\text{short},
$$

$$
0=\text{flat},
$$

$$
+1=\text{long}.
$$

Maka action vector:

$$
\boxed{
a_t\in\{-1,0,+1\}^N.
}
$$

---

# Y.18. Mengapa discrete action?

Karena order placement sebenarnya discrete:

$$
Buy
$$

atau:

$$
Sell
$$

atau:

$$
No\ Trade.
$$

Inilah yang membuat masalah ini cocok untuk:

$$
QUBO
$$

dan:

$$
Ising.
$$

---

# Y.19. Binary representation

Untuk long-only:

$$
x_i\in\{0,1\}.
$$

Untuk long/short kita membutuhkan dua binary variable:

$$
x_i^+,\quad x_i^-.
$$

dengan constraint:

$$
\boxed{
x_i^++x_i^-\le1.
}
$$

Kemudian:

$$
a_i=x_i^+-x_i^-.
$$

---

# Y.20. Portfolio selection QUBO

Misalkan:

$$
x_i\in\{0,1\}.
$$

Objective:

$$
J(x)
=
\mu^\top x
-
\lambda x^\top\Sigma x.
$$

Untuk minimization:

$$
\boxed{
H(x)
=
-\mu^\top x
+
\lambda x^\top\Sigma x.
}
$$

Inilah QUBO fundamental kita.

---

# Y.21. Cardinality constraint

Misalnya maksimum:

$$
K
$$

asset.

Constraint:

$$
\sum_i x_i=K.
$$

Masukkan penalty:

$$
P
\left(
\sum_i x_i-K
\right)^2.
$$

Maka:

$$
\boxed{
H(x)
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

# Y.22. Transaction-aware QUBO

Kita juga ingin memasukkan turnover.

Misalkan portfolio sebelumnya:

$$
x_i^{old}.
$$

Turnover:

$$
|x_i-x_i^{old}|.
$$

Maka:

$$
H(x)
=
-\mu^\top x
+
\lambda x^\top\Sigma x
+
\kappa
\sum_i
|x_i-x_i^{old}|.
$$

Karena:

$$
x_i,x_i^{old}\in\{0,1\},
$$

kita memiliki:

$$
|x_i-x_i^{old}|
=
x_i+x_i^{old}-2x_ix_i^{old}.
$$

Jadi seluruh objective tetap dapat ditulis sebagai quadratic polynomial.

---

# Y.23. Sekarang faktor macro masuk ke QUBO secara tidak langsung

Ini sangat penting.

Kita **tidak perlu** membuat:

$$
DXY
$$

atau:

$$
Gold
$$

menjadi qubit tersendiri.

Mereka memengaruhi:

$$
\hat\mu_t
$$

dan:

$$
\hat\Sigma_t.
$$

Sehingga:

$$
DXY_t
\rightarrow
\hat\mu_t
\rightarrow
H_t(x).
$$

Contoh:

$$
DXY\uparrow
$$

dapat mengubah:

$$
\hat\mu_{crypto}
$$

menjadi lebih rendah.

Kemudian optimizer otomatis mengubah:

$$
x^\star.
$$

---

# Y.24. Ini adalah arsitektur yang kita inginkan

```text
DXY ───────┐
Gold ──────┤
BTC ───────┤
ETH ───────┤
VIX ───────┤
SPX ───────┤
           ▼
       Factor Model
           │
           ▼
       μ̂t , Σ̂t
           │
           ▼
     Optimization
           │
           ▼
        x* / w*
           │
           ▼
        Trading
```

Jadi macro factor tidak langsung menentukan order.

Ia mempengaruhi **conditional expectation**.

---

# Y.25. Regime-dependent risk aversion

Sekarang kita manfaatkan regime.

Kita definisikan:

$$
\boxed{
\lambda_t
=
\lambda(z_t).
}
$$

Contoh:

$$
\lambda_{bull}<\lambda_{normal}<\lambda_{crisis}.
$$

Dalam crisis:

$$
\lambda_t\uparrow.
$$

Sehingga penalti risk meningkat:

$$
\lambda_t w^\top\Sigma w.
$$

Akibatnya portfolio secara otomatis menjadi lebih defensif.

---

# Y.26. Dynamic risk budget

Risk budget juga dapat bergantung pada regime:

$$
\boxed{
R_t
=
R_{base}
g(z_t,\sigma_t,\text{liquidity}_t).
}
$$

Misalnya:

$$
g<1
$$

ketika:

$$
\sigma_t
$$

tinggi.

Jadi:

$$
Volatility\uparrow
\Rightarrow
PositionSize\downarrow.
$$

---

# Y.27. Entry signal

Kita sekarang membutuhkan threshold.

Misalkan expected excess return:

$$
\alpha_{i,t}
=
\hat\mu_{i,t}
-
r_{benchmark,t}.
$$

Trade hanya jika:

$$
\boxed{
|\alpha_{i,t}|>\theta_i.
}
$$

Tetapi threshold juga dapat mempertimbangkan uncertainty:

$$
\boxed{
\frac{|\hat\mu_{i,t}|}
{\hat\sigma_{i,t}}
>
\theta.
}
$$

Ini lebih masuk akal daripada hanya melihat return prediction.

---

# Y.28. Signal-to-risk ratio

Definisikan:

$$
SR_{i,t}^{local}
=
\frac{\hat\mu_{i,t}}
{\sqrt{\hat\Sigma_{ii,t}}}.
$$

Kemudian:

$$
a_{i,t}
=
\begin{cases}
+1,&SR_{i,t}>\theta\\
0,&|SR_{i,t}|\le\theta\\
-1,&SR_{i,t}<-\theta.
\end{cases}
$$

Namun dalam sistem kita, ini hanya **candidate signal**.

Final decision masih berasal dari optimizer.

---

# Y.29. Candidate set

Kita tidak perlu mengoptimalkan seluruh dunia.

Definisikan:

$$
\mathcal C_t
=
\left\{
i:
|\alpha_{i,t}|>\theta
\right\}.
$$

Kemudian optimizer bekerja pada:

$$
N_t=|\mathcal C_t|.
$$

Ini sangat penting untuk scalability.

---

# Y.30. Order generation

Setelah mendapatkan:

$$
x_t^\star,
$$

kita menentukan:

$$
entry_t,
SL_t,
TP_t,
q_t.
$$

Jadi:

$$
\boxed{
x_t^\star
\rightarrow
TradePlan_t.
}
$$

Kita definisikan:

$$
TradePlan_t
=
(
direction,
entry,
SL,
TP,
quantity,
expiry
).
$$

---

# Y.31. Stop-loss mathematically

Untuk long:

$$
SL_t
=
P_t-\delta_t.
$$

Untuk short:

$$
SL_t
=
P_t+\delta_t.
$$

Dengan:

$$
\delta_t
=
k_\sigma\hat\sigma_{i,t}
$$

atau volatility-adjusted distance.

Misalnya:

$$
\boxed{
\delta_t
=
k\sigma_{i,t}\sqrt{\Delta t}.
}
$$

---

# Y.32. Take-profit

Jika reward-risk ratio:

$$
\rho
=
\frac{TP-entry}{entry-SL},
$$

maka:

$$
TP
=
entry+\rho(entry-SL)
$$

untuk long.

Sehingga:

$$
\boxed{
TP_t
=
P_t+\rho\delta_t.
}
$$

---

# Y.33. Expected value trade

Jika:

$$
p_w
$$

adalah probability of winning,

dan:

$$
p_l=1-p_w,
$$

dengan reward:

$$
R
$$

dan risk:

$$
L,
$$

maka:

$$
EV
=
p_wR-p_lL.
$$

Trade hanya layak jika:

$$
\boxed{
EV>0.
}
$$

Lebih realistis:

$$
EV_{net}
=
p_wR
-
p_lL
-
Cost.
$$

Maka:

$$
\boxed{
EV_{net}>0.
}
$$

---

# Y.34. Ini menghubungkan optimizer dengan TP/SL

Sebelumnya portfolio optimizer menghasilkan:

$$
x^\star.
$$

Sekarang kita evaluasi apakah trade individual memenuhi:

$$
EV_{net}>0.
$$

Jadi:

$$
\boxed{
Portfolio\ Selection
\neq
Trade\ Acceptance.
}
$$

Keduanya adalah layer berbeda.

---

# Y.35. Order book

Misalkan best bid:

$$
B_t
$$

dan best ask:

$$
A_t.
$$

Spread:

$$
S_t=A_t-B_t.
$$

Mid-price:

$$
M_t=
\frac{A_t+B_t}{2}.
$$

Entry order harus mempertimbangkan:

$$
M_t,\ S_t,\ Depth_t.
$$

---

# Y.36. Probability of fill

Untuk limit order:

$$
P(Fill)
=
p_{fill}(q,d,OB_t,\lambda_t).
$$

dengan:

- $q$: quantity,
- $d$: distance dari mid,
- $OB_t$: order book,
- $\lambda_t$: order-flow state.

---

# Y.37. Expected value of placing order

Ini menjadi menarik.

Misalkan:

$$
p_f=P(Fill).
$$

Expected utility:

$$
\boxed{
EU
=
p_f EV_{trade}
-
(1-p_f)C_{opportunity}.
}
$$

Jadi kita tidak hanya bertanya:

> "Apakah trade profitable?"

Tetapi:

> "Apakah menunggu limit order lebih baik daripada langsung market order?"

---

# Y.38. Market order vs limit order

Misalkan:

$$
EU_{limit}
$$

dan:

$$
EU_{market}.
$$

Pilih:

$$
\boxed{
a_t=
\arg\max
\{
EU_{limit},EU_{market},EU_{wait}
\}.
}
$$

Sekarang execution juga menjadi optimization problem.

---

# Y.39. Posisi terbuka

Setelah order filled:

$$
position_t\neq0.
$$

Kita memasuki state baru.

Definisikan:

$$
\boxed{
p_t^{pos}
}
$$

sebagai entry price.

Floating PnL:

$$
PnL_t
=
q_t(P_t-p_t^{pos})
$$

untuk long.

---

# Y.40. Position state

Kita dapat definisikan:

$$
z_t^{pos}
=
\{
entry,
SL,
TP,
PnL,
MFE,
MAE,
age
\}.
$$

dengan:

- MFE = Maximum Favorable Excursion,
- MAE = Maximum Adverse Excursion.

---

# Y.41. Inilah tempat feedback dimulai

Setiap periode:

$$
s_t^{pos}
$$

dievaluasi.

Kita hitung:

$$
EV_{continue}.
$$

Bandingkan dengan:

$$
EV_{exit}.
$$

Kemudian:

$$
\boxed{
a_t^{position}
=
\arg\max
\{
EV_{hold},
EV_{reduce},
EV_{exit},
EV_{reverse}
\}.
}
$$

---

# Y.42. Floating loss tidak otomatis berarti exit

Ini penting.

Jika:

$$
PnL_t<0,
$$

bukan berarti:

$$
Exit.
$$

Kita harus bertanya:

$$
P(Recovery|\mathcal F_t)
$$

dan:

$$
EV_{hold}.
$$

Jika thesis masih valid:

$$
EV_{hold}>EV_{exit},
$$

maka posisi dapat dipertahankan.

---

# Y.43. Floating profit juga tidak otomatis berarti TP

Jika:

$$
PnL_t>0,
$$

kita mengevaluasi:

$$
EV_{hold}
$$

versus:

$$
EV_{exit}.
$$

Jadi keputusan tidak berdasarkan:

> "sudah profit, tutup."

Melainkan:

> "Apakah expected future reward masih lebih besar daripada expected downside dan opportunity cost?"

---

# Y.44. Dynamic stop-loss

Kita dapat mendefinisikan stop:

$$
SL_t
=
f(
entry,
PnL,
volatility,
regime,
orderflow
).
$$

Contohnya:

$$
SL_t
=
\max
\left(
SL_{t-1},
P_t-k\sigma_t
\right)
$$

untuk long.

Karena:

$$
SL_t\ge SL_{t-1},
$$

stop tidak boleh mundur.

---

# Y.45. Break-even

Jika profit mencapai threshold:

$$
PnL_t\ge\theta_{BE},
$$

kita dapat memindahkan:

$$
SL_t
\rightarrow
entry+\epsilon.
$$

Secara matematis:

$$
\boxed{
SL_t
=
\max
(SL_{t-1},entry+\epsilon).
}
$$

---

# Y.46. Dynamic TP

Sekarang ide yang sebelumnya kamu berikan dapat diformalkan.

Jika:

$$
EV_{hold}>EV_{exit},
$$

maka kita dapat meningkatkan target:

$$
TP_t\rightarrow TP_{t+1}.
$$

Misalnya:

$$
TP_{t+1}
=
P_t+
\rho_t\delta_t.
$$

dengan:

$$
\rho_{t+1}>\rho_t
$$

jika momentum/regime masih mendukung.

---

# Y.47. Tetapi jangan menaikkan TP hanya karena profit

Kita membutuhkan condition:

$$
\boxed{
\frac{\hat\mu_t}
{\hat\sigma_t}
>
\theta_{continuation}.
}
$$

Jika:

$$
signal\ strength
$$

melemah, TP justru dapat diturunkan atau posisi ditutup.

---

# Y.48. State transition

Sekarang kita bisa menuliskan sistem sebagai:

$$
\boxed{
s_{t+1}
=
F(s_t,a_t,\xi_{t+1})
}
$$

dengan:

$$
\xi_{t+1}
$$

adalah random market shock.

Keputusan:

$$
\boxed{
a_t
=
\pi_\theta(s_t).
}
$$

Jadi keseluruhan strategy adalah policy:

$$
\boxed{
\pi:
\mathcal S
\rightarrow
\mathcal A.
}
$$

---

# Y.49. Objective global

Sekarang kita sampai pada formulasi yang benar-benar menyatukan semuanya.

Kita tidak ingin hanya memaksimalkan satu-period return.

Kita ingin:

$$
\boxed{
\max_\pi
\mathbb E
\left[
\sum_{t=0}^{T}
\gamma^t
U(R_{t+1},Risk_{t+1},Cost_{t+1})
\right].
}
$$

Misalnya:

$$
U_t
=
R_{t+1}
-
\lambda_t Risk_t
-
C_t.
$$

Maka:

$$
\boxed{
\max_\pi
\mathbb E
\left[
\sum_t
\gamma^t
\left(
R_{t+1}
-
\lambda_t Risk_t
-
C_t
\right)
\right].
}
$$

Ini adalah **global control objective**.

---

# Y.50. Tetapi optimizer quantum tidak menyelesaikan objective global secara langsung

Ini distinction penting.

VQE/QAOA kita gunakan untuk menyelesaikan **local combinatorial optimization**:

$$
\boxed{
x_t^\star
=
\arg\min_x H_t(x).
}
$$

Sedangkan:

$$
\pi
$$

adalah keseluruhan trading policy.

Jadi arsitektur kita adalah:

$$
\boxed{
Global\ Policy
\rightarrow
Local\ Optimization
\rightarrow
Execution.
}
$$

---

# Y.51. Local-to-global hierarchy

Secara formal:

$$
\pi_\theta:
s_t
\rightarrow
\mathcal Q_t
$$

kemudian:

$$
\mathcal Q_t
\rightarrow
x_t^\star
$$

kemudian:

$$
x_t^\star
\rightarrow
w_t^\star
$$

kemudian:

$$
w_t^\star
\rightarrow
q_t^\star
$$

kemudian:

$$
q_t^\star
\rightarrow
Order_t.
$$

---

# Y.52. Ising mapping

QUBO:

$$
H(x)
=
x^\top Qx+c^\top x+c_0.
$$

Gunakan:

$$
\boxed{
x_i=\frac{1-z_i}{2}
}
$$

dengan:

$$
z_i\in\{-1,+1\}.
$$

Substitusi menghasilkan:

$$
H(z)
=
C
+
\sum_i h_i z_i
+
\sum_{i<j}J_{ij}z_iz_j.
$$

Kemudian:

$$
\boxed{
\hat H
=
C I
+
\sum_i h_i Z_i
+
\sum_{i<j}J_{ij}Z_iZ_j.
}
$$

Ini adalah Hamiltonian yang masuk ke VQE/QAOA.

---

# Y.53. VQE

VQE mencari:

$$
\theta^\star
=
\arg\min_\theta
\langle\psi(\theta)|
\hat H
|\psi(\theta)\rangle.
$$

Kemudian measurement menghasilkan:

$$
z^\star.
$$

Konversi:

$$
z^\star
\rightarrow
x^\star.
$$

---

# Y.54. QAOA

QAOA menggunakan:

$$
U(\boldsymbol\gamma,\boldsymbol\beta)
=
\prod_{p}
e^{-i\beta_p H_M}
e^{-i\gamma_p H_C}.
$$

State:

$$
|\psi(\gamma,\beta)\rangle
=
U(\gamma,\beta)|+\rangle^{\otimes N}.
$$

Kemudian:

$$
\langle H_C\rangle
$$

dioptimalkan.

---

# Y.55. Yang menarik: $\gamma,\beta$ bukan market variables

Mereka adalah:

$$
\boxed{
\text{variational parameters}.
}
$$

Sedangkan:

$$
\mu_t,\Sigma_t
$$

adalah market-dependent quantities.

Jadi:

$$
\gamma,\beta
\notin
\mathcal F_t
$$

dalam arti yang sama seperti market state.

Mereka merupakan parameter yang dipilih untuk menghasilkan solusi dari:

$$
H_t.
$$

---

# Y.56. Dynamic Hamiltonian

Ini merupakan bagian yang sangat penting dari sistem kita.

Hamiltonian sebenarnya berubah terhadap waktu:

$$
\boxed{
\hat H_t
=
\hat H(
\hat\mu_t,
\hat\Sigma_t,
Risk_t,
Cost_t,
Constraints_t
).
}
$$

Jadi kita tidak mempunyai satu Hamiltonian permanen.

Kita memiliki:

$$
\hat H_1,\hat H_2,\ldots,\hat H_T.
$$

---

# Y.57. Dengan demikian trading loop menjadi:

$$
\boxed{
\hat H_t
\rightarrow
VQE/QAOA
\rightarrow
x_t^\star
\rightarrow
Trade_t
}
$$

kemudian market berubah:

$$
\boxed{
Market_{t+1}
\rightarrow
\hat H_{t+1}.
}
$$

Kemudian:

$$
x_t^\star
$$

tidak lagi dianggap optimal secara permanen.

---

# Y.58. Ini menjawab masalah "mengapa harus re-optimize?"

Karena:

$$
\hat H_{t+1}\neq\hat H_t.
$$

Perubahan dapat berasal dari:

$$
\Delta\mu,
\Delta\Sigma,
\Delta regime,
\Delta cost,
\Delta liquidity.
$$

Jadi:

$$
x_t^\star
$$

dapat menjadi suboptimal.

---

# Y.59. Re-optimization trigger

Kita tidak harus menjalankan optimizer setiap tick.

Definisikan:

$$
\Delta H_t
=
\|
H_t-H_{t-1}
\|.
$$

Re-optimize jika:

$$
\boxed{
\Delta H_t>\epsilon_H.
}
$$

Atau jika:

$$
|\Delta regime|=1.
$$

Atau:

$$
|\Delta\mu_i|>\epsilon_\mu.
$$

Atau:

$$
\Delta\sigma>\epsilon_\sigma.
$$

---

# Y.60. Jadi kita memiliki event-driven architecture

Optimizer aktif ketika:

$$
\boxed{
Event_t
=
\{
SignalChange,
RegimeChange,
RiskChange,
PositionChange,
LiquidityChange
\}.
}
$$

Ini jauh lebih efisien daripada:

$$
Optimize
$$

setiap saat tanpa alasan.

---

# Y.61. Full unified equation

Sekarang seluruh framework dapat diringkas:

$$
\boxed{
s_t
=
\left[
D_{0:t},
w_t,
q_t,
Risk_t
\right]
}
$$

kemudian:

$$
\boxed{
(\hat\mu_t,\hat\Sigma_t)
=
\Phi_\theta(s_t)
}
$$

kemudian:

$$
\boxed{
H_t(x)
=
-\hat\mu_t^\top x
+
\lambda_t x^\top\hat\Sigma_t x
+
C_t(x,x_{t-1})
+
P_t(x)
}
$$

kemudian:

$$
\boxed{
x_t^\star
=
\operatorname{Solve}(H_t)
}
$$

dengan:

$$
\operatorname{Solve}
\in
\{
Exact,
MILP,
Classical,
VQE,
QAOA
\}.
$$

Kemudian:

$$
\boxed{
w_t^\star
=
\Psi(x_t^\star,s_t)
}
$$

dan:

$$
\boxed{
q_t^\star
=
\min
\left[
q_t^{portfolio},
\frac{R_t}{\delta_t}
\right].
}
$$

Kemudian:

$$
\boxed{
O_t
=
\Omega(
w_t^\star,
q_t^\star,
OB_t,
SL_t,
TP_t
).
}
$$

Execution menghasilkan:

$$
\boxed{
s_{t+1}
=
F(s_t,O_t,\xi_{t+1}).
}
$$

---

# Y.62. Closed-loop formulation

Akhirnya:

$$
\boxed{
\begin{aligned}
\mathcal F_t
&\rightarrow s_t\\
&\rightarrow(\hat\mu_t,\hat\Sigma_t)\\
&\rightarrow H_t\\
&\rightarrow x_t^\star\\
&\rightarrow w_t^\star\\
&\rightarrow q_t^\star\\
&\rightarrow O_t\\
&\rightarrow E_{t+1}\\
&\rightarrow R_{t+1}\\
&\rightarrow s_{t+1}.
\end{aligned}
}
$$

Dan:

$$
s_{t+1}
$$

kembali masuk ke sistem.

Itulah feedback loop.

---

# Y.63. Formulasi sebagai constrained stochastic control

Kalau kita ingin menuliskannya dalam bentuk yang lebih formal:

$$
\boxed{
\begin{aligned}
\max_{\pi}
\quad&
\mathbb E^\pi
\left[
\sum_{t=0}^{T}
\gamma^t
U(s_t,a_t)
\right]\\
\text{s.t.}\quad
&
s_{t+1}=F(s_t,a_t,\xi_{t+1}),\\
&
a_t\in\mathcal A(s_t),\\
&
Risk_t\le R_t,\\
&
Turnover_t\le\tau_t,\\
&
Leverage_t\le L_t,\\
&
Liquidity_t\ge L_t^{min}.
\end{aligned}
}
$$

Ini adalah **master formulation**.

---

# Y.64. Tetapi ada dua level optimization

Ini menurut saya adalah desain paling penting dari seluruh framework kita:

$$
\boxed{
\textbf{Level 1 — Strategic / Policy}
}
$$

memilih bagaimana sistem mengambil keputusan.

Sedangkan:

$$
\boxed{
\textbf{Level 2 — Combinatorial Optimization}
}
$$

menentukan portfolio/order candidate pada state tertentu.

Secara diagram:

```text
                 POLICY
                   │
                   ▼
              MARKET STATE
                   │
                   ▼
           μ̂t , Σ̂t , Risk
                   │
                   ▼
          ┌─────────────────┐
          │ Combinatorial   │
          │ Optimization    │
          └─────────────────┘
             │    │    │
             ▼    ▼    ▼
           MILP  VQE  QAOA
             │    │    │
             └────┼────┘
                  ▼
             Portfolio
                  │
                  ▼
              Execution
                  │
                  ▼
                Market
                  │
                  └──────────► feedback
```

---

# Y.65. Mengapa desain ini bagus untuk proyek kita?

Karena kita **tidak memaksakan quantum computing untuk menyelesaikan seluruh trading problem**.

Quantum computing hanya digunakan di tempat yang memang natural:

$$
\boxed{
\text{discrete combinatorial optimization}.
}
$$

Sementara:

- factor estimation,
- covariance estimation,
- regime detection,
- risk management,
- execution,

tetap dapat menggunakan classical methods yang memang sesuai.

Ini jauh lebih defensible secara ilmiah daripada mencoba membuat "semua bagian trading menjadi quantum".

---

# Y.66. Dan ini juga membuka banyak jenis problem

Framework yang sama dapat menghasilkan:

### Portfolio selection

$$
\min_x H(x)
$$

### MaxCut

$$
\max_x
\sum_{ij}w_{ij}x_ix_j
$$

untuk clustering/exposure structure.

### TSP

Untuk routing order execution atau allocation scheduling tertentu:

$$
\min_{\pi}
\sum_{i,j}
d_{ij}x_{ij}.
$$

### Knapsack

Untuk capital allocation:

$$
\max_x
\sum_i v_ix_i
$$

subject to:

$$
\sum_i c_ix_i\le C.
$$

### Assignment

Untuk allocation capital/order capacity.

Dengan demikian:

$$
\boxed{
QAOA/VQE
}
$$

bukan terikat pada portfolio saja.

---

# Y.67. Dan akhirnya kita bisa melihat visi besar sistem

Sistem kita bukan:

> "bot yang membeli crypto."

Melainkan:

$$
\boxed{
\textbf{Adaptive Multi-Asset Quantitative Decision System}
}
$$

yang mengambil:

$$
\text{market}
+
\text{macro}
+
\text{cross-asset}
+
\text{risk}
+
\text{execution}
$$

dan menghasilkan:

$$
\text{discrete trading decisions}.
$$

---

# Y.68. Formulasi final yang saya sarankan kita "kunci"

Saya akan menjadikan persamaan berikut sebagai **central equation** dari seluruh proyek:

$$
\boxed{
x_t^\star
=
\arg\min_{x\in\mathcal X_t}
\left[
-\hat\mu_t^\top x
+
\lambda_t x^\top\hat\Sigma_t x
+
C_t(x,x_{t-1})
+
P_t(x)
\right]
}
$$

dengan:

$$
\boxed{
(\hat\mu_t,\hat\Sigma_t)
=
\Phi_\theta(
P_{0:t},
F_{0:t},
OB_{0:t},
z_t
)
}
$$

dan:

$$
\boxed{
q_t^\star
=
\min
\left(
q_t^{portfolio},
\frac{R_t}{\delta_t}
\right).
}
$$

Kemudian keputusan dieksekusi melalui:

$$
\boxed{
O_t
=
\Omega(
x_t^\star,q_t^\star,
OB_t,SL_t,TP_t
).
}
$$

Dan seluruh sistem berevolusi:

$$
\boxed{
s_{t+1}
=
F(s_t,O_t,\xi_{t+1}).
}
$$

---

# Y.69. Satu hal yang perlu kita luruskan

Ada perbedaan antara **model penelitian** dan **bot trading production**.

Untuk penelitian, kita ingin:

$$
\boxed{
\text{correctness}
>
\text{speed}.
}
$$

Kita harus memastikan:

- no leakage,
- valid mathematical formulation,
- correct QUBO,
- correct Ising mapping,
- correct execution simulation,
- robust OOS result.

Baru setelah itu:

$$
\boxed{
speed
\rightarrow
latency
\rightarrow
deployment.
}
$$

---

# Y.70. Posisi kita sekarang

Dengan Tahap Y, arsitektur kita sudah berubah dari sekadar:

$$
A\rightarrow B\rightarrow C\rightarrow\cdots
$$

menjadi satu persamaan besar:

$$
\boxed{
\mathcal F_t
\rightarrow
s_t
\rightarrow
\Phi_\theta
\rightarrow
(\mu_t,\Sigma_t)
\rightarrow
H_t
\rightarrow
\operatorname{Solve}
\rightarrow
x_t^\star
\rightarrow
w_t
\rightarrow
q_t
\rightarrow
Order
\rightarrow
Execution
\rightarrow
PnL
\rightarrow
s_{t+1}.
}
$$

Dan menurut saya, **Tahap Y adalah titik di mana proyek ini akhirnya memiliki "mathematical spine" yang jelas.**

Tahap berikutnya yang paling natural adalah **Tahap Z — Concrete Model Specification & Implementation Blueprint**: kita berhenti pada formulasi abstrak dan menentukan **persis** variabel apa yang digunakan, timeframe, asset universe, feature/factor matrix, estimasi $\mu_t$, estimasi $\Sigma_t$, regime model, bentuk QUBO final, encoding qubit, constraint, penalty coefficient, VQE/QAOA circuit, serta format data yang harus masuk dan keluar dari setiap modul. Dengan itu kita bisa mulai menerjemahkan formulasi Y menjadi arsitektur kode yang benar-benar dapat dibangun dan diuji.

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

## Prompt:
8/17/2026, 10:15:55 PM

lanjut Tahap AB

## Response:
8/17/2026, 10:15:56 PM

> **Remembering**
>
>
> ****
>
> 
>
> **Recalled trading architecture, decisions, risk rules, and Stage AB focus**
>
> 
>
> Worked for 6s

# Tahap AB — Mathematical Feature & Factor Engine

Baik. Pada **Tahap AA** kita sudah mengunci arsitektur data:

$$
\boxed{
\text{Raw Market Data}
\rightarrow
\mathcal F_t
\rightarrow
\text{Feature/Factor Engine}
\rightarrow
(\hat{\mu}_t,\hat{\Sigma}_t)
\rightarrow
\text{QUBO/Ising}
\rightarrow
\text{Trading Decision}
}
$$

Maka Tahap AB adalah tempat kita membangun bagian yang selama ini masih berupa kotak hitam:

$$
\boxed{
\text{Raw data}
\longrightarrow
\hat{\mu}_t,\hat{\Sigma}_t
}
$$

Dan saya ingin kita membuatnya **secara matematis**, bukan sekadar memasukkan indikator teknikal seperti RSI, MACD, dan sebagainya.

---

# AB.1. Tujuan Mathematical Feature Engine

Pada setiap waktu keputusan $t$, sistem memiliki informasi:

$$
\mathcal F_t.
$$

Dari informasi tersebut kita ingin membentuk feature vector:

$$
\boxed{
\mathbf{x}_{i,t}
=
f_i(\mathcal F_t)
}
$$

untuk setiap asset $i$.

Kemudian model forecast menghasilkan:

$$
\boxed{
\hat{\mu}_{i,t}
=
E[r_{i,t+1}\mid\mathcal F_t]
}
$$

dan covariance:

$$
\boxed{
\hat{\Sigma}_t
=
Cov(\mathbf r_{t+1}\mid\mathcal F_t).
}
$$

Jadi sebenarnya ada **dua mesin berbeda**:

$$
\boxed{
\text{Feature Engine}
\rightarrow
\text{Return Forecast}
}
$$

dan:

$$
\boxed{
\text{Feature/Factor Engine}
\rightarrow
\text{Risk Forecast}.
}
$$

Keduanya akhirnya bertemu di optimizer.

---

# AB.2. Return sebagai variabel fundamental

Kita mulai dari harga:

$$
P_{i,t}.
$$

Saya ingin menggunakan log-return:

$$
\boxed{
r_{i,t}
=
\ln
\frac{P_{i,t}}{P_{i,t-1}}
}
$$

karena memiliki sifat:

$$
r_{i,t}^{(H)}
=
\ln
\frac{P_{i,t}}{P_{i,t-H}}
=
\sum_{k=0}^{H-1}r_{i,t-k}.
$$

Ini sangat berguna untuk multi-horizon model.

---

# AB.3. Return vector

Untuk $N$ asset:

$$
\mathbf r_t
=
\begin{bmatrix}
r_{1,t}\\
r_{2,t}\\
\vdots\\
r_{N,t}
\end{bmatrix}.
$$

Untuk baseline kita:

$$
N=6
$$

dengan:

$$
\mathcal A_T
=
\{SOL,XRP,ADA,AVAX,LINK,DOGE\}.
$$

Maka:

$$
\mathbf r_t\in\mathbb R^6.
$$

---

# AB.4. Multi-horizon return

Satu return saja terlalu miskin.

Kita definisikan:

$$
\boxed{
R_{i,t}^{(H)}
=
\sum_{k=0}^{H-1}r_{i,t-k}.
}
$$

Kita dapat mengambil:

$$
H\in
\{1,3,6,12,24,72,168\}.
$$

Karena decision timeframe kita adalah 1 jam, maka:

- $H=1$: 1 jam,
- $H=3$: 3 jam,
- $H=6$: 6 jam,
- $H=12$: 12 jam,
- $H=24$: 1 hari,
- $H=72$: 3 hari,
- $H=168$: 1 minggu.

---

# AB.5. Momentum

Momentum sederhana:

$$
\boxed{
M_{i,t}^{(H)}
=
\sum_{k=0}^{H-1}r_{i,t-k}.
}
$$

Secara matematis sebenarnya sama dengan cumulative log-return.

Tetapi nanti kita dapat menggunakan beberapa transformasi:

$$
M_{i,t}^{(H)}
=
\ln
\frac{P_{i,t}}
{P_{i,t-H}}.
$$

---

# AB.6. Normalized momentum

Momentum absolut tidak dapat dibandingkan dengan baik antar-asset.

Maka kita normalisasi dengan volatility:

$$
\boxed{
Z_{i,t}^{(H)}
=
\frac{M_{i,t}^{(H)}}
{\hat{\sigma}_{i,t}^{(H)}+\epsilon}.
}
$$

Dengan:

$$
\epsilon>0
$$

untuk mencegah pembagian nol.

Sekarang $Z$ dapat dibandingkan antar asset.

---

# AB.7. Volatility

Volatility rolling:

$$
\boxed{
\hat{\sigma}_{i,t}^{(L)}
=
\sqrt{
\frac{1}{L-1}
\sum_{k=0}^{L-1}
(r_{i,t-k}-\bar r_{i,t})^2
}.
}
$$

Baseline kita:

$$
L=168.
$$

Jadi sistem mengetahui volatility satu minggu terakhir.

---

# AB.8. EWMA volatility

Volatility rolling memiliki kelemahan: semua observasi mendapat bobot sama.

Kita dapat menggunakan EWMA:

$$
\boxed{
\sigma_{i,t}^2
=
\lambda\sigma_{i,t-1}^2
+
(1-\lambda)r_{i,t-1}^2.
}
$$

Dengan:

$$
0<\lambda<1.
$$

Semakin besar $\lambda$, semakin lambat model bereaksi terhadap perubahan volatility.

---

# AB.9. Mengapa volatility penting?

Karena:

$$
\mu_i=1\%
$$

tidak berarti sama jika:

$$
\sigma_i=0.5\%
$$

dibanding:

$$
\sigma_i=5\%.
$$

Maka signal harus dipandang sebagai:

$$
\boxed{
\text{return relative to uncertainty}.
}
$$

---

# AB.10. Z-score return

Kita dapat membuat:

$$
\boxed{
Z_{i,t}
=
\frac{
r_{i,t}-\bar r_{i,t}^{(L)}
}{
\sigma_{i,t}^{(L)}+\epsilon
}.
}
$$

Ini memberi informasi apakah return saat ini abnormal relatif terhadap regime lokal.

---

# AB.11. Volume

Volume mentah juga tidak comparable.

Gunakan:

$$
\boxed{
VZ_{i,t}
=
\frac{
V_{i,t}-\bar V_{i,t}^{(L)}
}{
\sigma_{V_i,t}^{(L)}+\epsilon
}.
}
$$

Ini memberi:

> Apakah pergerakan harga sekarang terjadi dengan volume abnormal?

---

# AB.12. Dollar volume

Untuk likuiditas:

$$
\boxed{
DV_{i,t}
=
P_{i,t}V_{i,t}.
}
$$

Kemudian:

$$
ADV_{i,t}^{(L)}
=
\frac1L
\sum_{k=0}^{L-1}
DV_{i,t-k}.
$$

Ini akan digunakan juga pada execution/risk engine.

---

# AB.13. High-low range

Kita dapat mendefinisikan:

$$
\boxed{
Range_{i,t}
=
\frac{H_{i,t}-L_{i,t}}
{C_{i,t}}.
}
$$

Kemudian rolling average:

$$
\overline{Range}_{i,t}^{(L)}
=
\frac1L
\sum_{k=0}^{L-1}
Range_{i,t-k}.
$$

Ini merupakan proxy volatility intrabar.

---

# AB.14. Sekarang masuk ke bagian yang jauh lebih penting: cross-asset factors

Misalkan target kita adalah SOL.

Kita tidak hanya melihat:

$$
r_{SOL,t}.
$$

Kita melihat:

$$
\mathbf f_t
=
\begin{bmatrix}
r_{BTC,t}\\
r_{ETH,t}\\
r_{DXY,t}\\
r_{Gold,t}\\
r_{SPX,t}\\
r_{VIX,t}
\end{bmatrix}.
$$

Dengan:

$$
K=6.
$$

---

# AB.15. Factor model

Model dasar:

$$
\boxed{
\mathbf r_t
=
\boldsymbol\alpha
+
B\mathbf f_t
+
\boldsymbol\epsilon_t
}
$$

dengan:

$$
B\in\mathbb R^{N\times K}.
$$

Elemen:

$$
\beta_{ik}
$$

mengukur sensitivitas asset $i$ terhadap factor $k$.

---

# AB.16. Contoh interpretasi

Misalkan:

$$
\beta_{SOL,BTC}=1.4.
$$

Secara sederhana:

$$
\Delta SOL
\approx
1.4\Delta BTC
$$

untuk komponen pergerakan yang dijelaskan oleh factor tersebut.

Sedangkan:

$$
\beta_{SOL,DXY}=-0.3.
$$

Maka kenaikan DXY secara statistik berkaitan dengan tekanan terhadap SOL.

**Ini bukan klaim kausalitas.**

Kita hanya mengatakan:

$$
\text{conditional exposure}.
$$

---

# AB.17. Estimasi beta

Untuk setiap asset:

$$
\mathbf r_i
=
X\boldsymbol\beta_i
+
\epsilon_i.
$$

OLS:

$$
\boxed{
\hat{\boldsymbol\beta}_i
=
(X^\top X)^{-1}X^\top\mathbf r_i.
}
$$

Namun kita tidak akan menghitungnya menggunakan seluruh history.

---

# AB.18. Rolling beta

Pada waktu $t$:

$$
\boxed{
\hat B_t
=
\arg\min_B
\sum_{\tau=t-L+1}^{t}
\|
\mathbf r_\tau
-
\boldsymbol\alpha
-
B\mathbf f_\tau
\|^2.
}
$$

Jadi beta berubah:

$$
B_t\neq B_{t-1}.
$$

Ini jauh lebih masuk akal untuk short-term trading.

---

# AB.19. Mengapa beta harus berubah?

Karena hubungan pasar dapat berubah.

Misalnya:

### Regime 1

$$
\beta_{SOL,BTC}=1.2.
$$

### Regime 2

$$
\beta_{SOL,BTC}=2.0.
$$

Jika kita menggunakan beta jangka panjang:

$$
\beta=1.2
$$

maka model mungkin underestimate risiko SOL ketika BTC menjadi dominant driver.

---

# AB.20. Weighted regression

Kita dapat memberikan bobot lebih besar pada data terbaru:

$$
\boxed{
\min_B
\sum_{\tau=t-L+1}^{t}
w_{t-\tau}
\|
\mathbf r_\tau-B\mathbf f_\tau
\|^2.
}
$$

Misalnya:

$$
w_k=\lambda^k.
$$

Ini menghasilkan **exponentially weighted factor model**.

---

# AB.21. Residual return

Setelah factor exposure diketahui:

$$
\boxed{
\hat\epsilon_{i,t}
=
r_{i,t}
-
\hat\alpha_i
-
\hat\beta_i^\top\mathbf f_t.
}
$$

Ini sangat penting.

Karena kita sekarang dapat memisahkan:

$$
\boxed{
Total\ Return
=
Factor\ Return
+
Idiosyncratic\ Return.
}
$$

---

# AB.22. Residual momentum

Kita bahkan dapat menghitung momentum residual:

$$
\boxed{
RM_{i,t}^{(H)}
=
\sum_{k=0}^{H-1}
\hat\epsilon_{i,t-k}.
}
$$

Ini jauh lebih menarik daripada momentum harga biasa.

Misalnya:

$$
SOL
$$

naik karena:

$$
BTC
$$

naik.

Itu belum tentu merupakan alpha.

Tetapi jika:

$$
SOL
$$

mengungguli apa yang dijelaskan oleh BTC/ETH/macro factors:

$$
\hat\epsilon_{SOL}>0,
$$

maka terdapat **relative strength** yang lebih spesifik terhadap SOL.

---

# AB.23. Ini menghasilkan dua jenis momentum

### Market momentum

$$
M^{market}_{i,t}
$$

dan:

### Residual momentum

$$
M^{residual}_{i,t}.
$$

Kemudian feature vector dapat memiliki:

$$
\boxed{
x_{i,t}
=
[
M^{market},
M^{residual},
\sigma,
VZ,
\ldots
].
}
$$

---

# AB.24. Cross-asset lag

Sekarang kita masuk ke ide yang sebelumnya sudah kita tetapkan.

Model:

$$
r_{i,t+1}
=
\alpha_i
+
\sum_{k=0}^{K}
B_{i,k}f_{t-k}
+
\epsilon_{i,t+1}.
$$

Misalnya:

$$
r_{SOL,t+1}
=
\alpha
+
\beta_0r_{BTC,t}
+
\beta_1r_{BTC,t-1}
+
\beta_2r_{BTC,t-2}
+
\epsilon.
$$

---

# AB.25. Mengapa ini penting?

Bayangkan:

$$
BTC
$$

bergerak lebih dahulu.

Kemudian:

$$
SOL
$$

bereaksi beberapa jam kemudian.

Jika pola tersebut stabil, maka:

$$
BTC_{t}
$$

bisa menjadi **leading factor**.

Model kita tidak lagi sekadar bertanya:

> "Apa hubungan BTC dan SOL?"

tetapi:

> **"Apakah informasi BTC sekarang mengandung informasi tentang return SOL berikutnya?"**

---

# AB.26. Distributed-lag factor matrix

Kita dapat mendefinisikan:

$$
\mathbf F_t^{lag}
=
\begin{bmatrix}
\mathbf f_t\\
\mathbf f_{t-1}\\
\vdots\\
\mathbf f_{t-K}
\end{bmatrix}.
$$

Kemudian:

$$
\boxed{
r_{i,t+1}
=
\alpha_i
+
\Theta_i^\top
\mathbf F_t^{lag}
+
\epsilon_{i,t+1}.
}
$$

---

# AB.27. Jangan membuat $K$ terlalu besar

Jika:

$$
K=24
$$

dan factor:

$$
6,
$$

maka:

$$
6\times25=150
$$

coefficient per asset.

Dengan hanya:

$$
168
$$

observasi, kita mengalami masalah:

$$
\boxed{
p\approx n.
}
$$

Maka estimasi menjadi tidak stabil.

---

# AB.28. Regularisasi ridge

Kita dapat menggunakan:

$$
\boxed{
\hat\theta
=
\arg\min_\theta
\left[
\|y-X\theta\|^2
+
\lambda\|\theta\|_2^2
\right].
}
$$

Solusinya:

$$
\boxed{
\hat\theta
=
(X^\top X+\lambda I)^{-1}X^\top y.
}
$$

Ini sangat cocok untuk factor model kita.

---

# AB.29. Mengapa ridge lebih cocok daripada langsung memperbanyak feature?

Karena kita ingin:

$$
\text{predictive stability}
$$

bukan:

$$
\text{training fit}.
$$

Dalam trading:

$$
R^2_{train}
$$

yang tinggi tidak berarti:

$$
P\&L_{live}
$$

tinggi.

---

# AB.30. Factor interaction

Kita bahkan dapat memiliki:

$$
BTC\times DXY.
$$

Misalnya:

$$
x_t
=
r_{BTC,t}
r_{DXY,t}.
$$

Kemudian:

$$
r_{SOL,t+1}
=
\alpha
+
\beta_1BTC_t
+
\beta_2DXY_t
+
\beta_3(BTC_tDXY_t)
+
\epsilon.
$$

Ini memungkinkan hubungan non-additive.

---

# AB.31. Tetapi jangan terlalu cepat memasukkan interaction

Karena jumlah parameter bertambah.

Kita gunakan prinsip:

$$
\boxed{
complexity
\quad\text{harus dibayar dengan evidence}.
}
$$

Setiap feature tambahan harus melewati:

$$
walk-forward
$$

dan:

$$
ablation.
$$

---

# AB.32. Factor covariance

Sekarang bagian kedua yang sangat penting:

$$
\hat\Sigma_t.
$$

Dari:

$$
r_t
=
B_tf_t+\epsilon_t,
$$

kita mendapatkan:

$$
\boxed{
\Sigma_t
=
B_t\Sigma_{F,t}B_t^\top
+
\Sigma_{\epsilon,t}.
}
$$

Ini adalah **factor covariance model**.

---

# AB.33. Mengapa tidak langsung menghitung covariance asset?

Kita bisa:

$$
\hat\Sigma_{sample}
=
Cov(r).
$$

Tetapi jika:

$$
N
$$

besar dan:

$$
L
$$

relatif kecil, covariance sample menjadi noisy.

Factor model memberikan struktur:

$$
\boxed{
\text{common risk}
+
\text{idiosyncratic risk}.
}
$$

---

# AB.34. Factor covariance

Definisikan:

$$
\Sigma_{F,t}
=
Cov(f_t).
$$

Rolling estimate:

$$
\boxed{
\hat\Sigma_{F,t}
=
Cov
(
f_{t-L+1:t}
).
}
$$

Bisa juga EWMA.

---

# AB.35. Residual covariance

Residual:

$$
\epsilon_t
=
r_t-B_tf_t.
$$

Jika kita mengasumsikan residual relatif independent antar asset:

$$
\boxed{
\Sigma_{\epsilon,t}
\approx
diag(\sigma_{\epsilon,1}^2,\ldots,\sigma_{\epsilon,N}^2).
}
$$

Ini adalah **diagonal factor model**.

---

# AB.36. Mengapa asumsi diagonal menarik?

Karena:

$$
N(N-1)/2
$$

off-diagonal covariance harus diestimasi jika menggunakan covariance penuh.

Untuk:

$$
N=100,
$$

itu:

$$
4950
$$

parameter.

Factor model dapat mengurangi kompleksitas secara drastis.

---

# AB.37. Tetapi residual sebenarnya bisa berkorelasi

Misalnya:

$$
\epsilon_{SOL}
$$

dan:

$$
\epsilon_{AVAX}
$$

masih berkorelasi.

Maka nanti kita dapat menggunakan:

$$
\Sigma_\epsilon
=
D+
R.
$$

Tetapi baseline kita gunakan:

$$
\boxed{
\Sigma_\epsilon=D.
}
$$

---

# AB.38. Shrinkage covariance

Kita juga dapat melakukan shrinkage:

$$
\boxed{
\hat\Sigma
=
(1-\rho)\hat\Sigma_{sample}
+
\rho T.
}
$$

dengan $T$ target covariance.

Contoh:

$$
T=diag(\hat\Sigma_{sample}).
$$

Ini mengurangi estimation error.

---

# AB.39. EWMA covariance

Alternatif:

$$
\boxed{
\Sigma_t
=
\lambda\Sigma_{t-1}
+
(1-\lambda)
r_{t-1}r_{t-1}^\top.
}
$$

Secara online:

$$
\Sigma_t
$$

selalu diperbarui tanpa menghitung ulang seluruh history.

---

# AB.40. Kita sebenarnya akan menggunakan kombinasi

Untuk baseline:

$$
\boxed{
\Sigma_t
=
B_t\Sigma_{F,t}B_t^\top
+
D_{\epsilon,t}.
}
$$

Kemudian:

$$
\Sigma_{F,t}
$$

dapat menggunakan EWMA.

Dan:

$$
D_{\epsilon,t}
$$

juga dapat menggunakan EWMA residual volatility.

---

# AB.41. Sekarang expected return

Ini bagian yang akan menentukan:

$$
\hat\mu_t.
$$

Model paling sederhana:

$$
\boxed{
\hat\mu_t
=
\hat\alpha_t
+
\hat B_t\hat f_{t+1}.
}
$$

Masalahnya:

> kita tidak mengetahui $f_{t+1}$.

Maka kita perlu memprediksi factor.

---

# AB.42. Factor forecast

Misalnya:

$$
\boxed{
\hat f_{t+1}
=
E[f_{t+1}\mid\mathcal F_t].
}
$$

Kita dapat menggunakan model sederhana:

$$
\hat f_{t+1}
=
\phi f_t.
$$

atau:

$$
\hat f_{t+1}
=
\sum_{k=0}^{K}
A_kf_{t-k}.
$$

---

# AB.43. Namun ada pendekatan yang lebih konservatif

Untuk short-term trading, kita tidak harus mencoba memprediksi seluruh market.

Kita dapat memisahkan:

$$
\boxed{
\hat\mu_i
=
\hat\mu_i^{baseline}
+
\hat\mu_i^{factor}
+
\hat\mu_i^{residual}.
}
$$

Ini lebih fleksibel.

---

# AB.44. Baseline component

Misalnya:

$$
\hat\mu_i^{baseline}
=
\hat\alpha_i.
$$

Tetapi intercept saja biasanya terlalu lemah.

Maka kita dapat memasukkan momentum.

---

# AB.45. Momentum component

$$
\boxed{
\hat\mu_i^{mom}
=
\theta_{i}^{(1)}M_{i,t}^{(1)}
+
\theta_i^{(6)}M_{i,t}^{(6)}
+
\theta_i^{(24)}M_{i,t}^{(24)}.
}
$$

---

# AB.46. Factor component

$$
\boxed{
\hat\mu_i^{factor}
=
\hat B_{i,t}
\hat f_{t+1}.
}
$$

---

# AB.47. Residual component

Residual return dapat memiliki autocorrelation:

$$
\epsilon_{i,t}
=
\phi_i\epsilon_{i,t-1}
+
u_{i,t}.
$$

Maka:

$$
\boxed{
\hat\epsilon_{i,t+1}
=
\hat\phi_i\epsilon_{i,t}.
}
$$

---

# AB.48. Gabungan

Kita memperoleh:

$$
\boxed{
\hat\mu_{i,t}
=
\hat\alpha_i
+
\hat B_{i,t}\hat f_{t+1}
+
\hat\phi_i\hat\epsilon_{i,t}
+
\hat\mu_{i,t}^{mom}.
}
$$

Ini menjadi baseline forecast engine kita.

---

# AB.49. Tapi ada masalah penting

Kalau kita memasukkan terlalu banyak model:

$$
\hat\mu
=
\alpha
+
factor
+
momentum
+
residual
+
interaction
+
regime
+\cdots
$$

maka kita dapat mengalami:

$$
\boxed{
overfitting.
}
$$

Karena itu semua coefficient harus dipelajari **hanya dari training window**.

---

# AB.50. Regime conditioning

Kita sebelumnya telah menetapkan 3-state regime.

Misalkan:

$$
z_t\in
\{
1,2,3
\}.
$$

Contoh:

$$
1=\text{Calm}
$$

$$
2=\text{Normal}
$$

$$
3=\text{Stress}.
$$

Maka:

$$
\boxed{
\hat\mu_{i,t}
=
\hat\mu_i
(z_t).
}
$$

Dan:

$$
\boxed{
\hat\Sigma_t
=
\hat\Sigma(z_t).
}
$$

---

# AB.51. Mengapa regime mempengaruhi covariance?

Karena:

$$
Cov(r_t\mid z_t=1)
\neq
Cov(r_t\mid z_t=3).
$$

Saat stress:

$$
\sigma_i\uparrow
$$

dan sering:

$$
\rho_{ij}\uparrow.
$$

Jadi diversification dapat menjadi lebih lemah saat crash.

Ini sangat penting bagi optimizer.

---

# AB.52. Regime-conditioned factor beta

Kita bahkan dapat mendefinisikan:

$$
\boxed{
\beta_{i,k}^{(z)}
}
$$

sehingga:

$$
r_{i,t}
=
\alpha_i^{(z_t)}
+
B_i^{(z_t)}f_t
+
\epsilon_{i,t}.
$$

Tetapi untuk baseline kita **tidak langsung melakukan ini**, karena parameter akan terlalu banyak.

Kita mulai dengan:

$$
B_t
$$

rolling dan:

$$
z_t
$$

sebagai feature.

---

# AB.53. Feature vector final

Untuk asset $i$, baseline feature vector:

$$
\boxed{
\mathbf x_{i,t}
=
\begin{bmatrix}
M_i^{(1)}\\
M_i^{(6)}\\
M_i^{(24)}\\
M_i^{(168)}\\
Z_i^{(1)}\\
\sigma_i\\
VZ_i\\
Range_i\\
RM_i^{(24)}\\
\beta_{i,BTC}\\
\beta_{i,ETH}\\
\beta_{i,DXY}\\
\beta_{i,Gold}\\
\beta_{i,SPX}\\
\beta_{i,VIX}\\
\epsilon_{i,t}\\
z_t
\end{bmatrix}.
}
$$

Ini sudah cukup kaya.

---

# AB.54. Tetapi optimizer tidak menerima feature vector

Ini perbedaan penting.

Feature vector:

$$
\mathbf x_{i,t}
$$

masuk ke:

$$
Forecast\ Model.
$$

Outputnya:

$$
\boxed{
\hat\mu_{i,t}.
}
$$

Sementara covariance engine menghasilkan:

$$
\boxed{
\hat\Sigma_t.
}
$$

Barulah:

$$
(\hat\mu_t,\hat\Sigma_t)
$$

dikirim ke optimizer.

---

# AB.55. Pipeline matematis lengkap

Sekarang:

$$
\boxed{
P,V,OB,F
}
$$

menjadi:

$$
\downarrow
$$

$$
\boxed{
r,\sigma,M,VZ,OBI
}
$$

menjadi:

$$
\downarrow
$$

$$
\boxed{
B_t,\epsilon_t,\Sigma_F,\Sigma_\epsilon
}
$$

menjadi:

$$
\downarrow
$$

$$
\boxed{
\hat\mu_t,\hat\Sigma_t
}
$$

menjadi:

$$
\downarrow
$$

$$
\boxed{
QUBO_t
}
$$

menjadi:

$$
\downarrow
$$

$$
\boxed{
x_t^\star.
}
$$

---

# AB.56. Dari $(\mu,\Sigma)$ ke QUBO

Sekarang kita hubungkan langsung dengan penelitian quantum kita.

Misalkan binary:

$$
x_i\in\{0,1\}.
$$

Objective:

$$
\boxed{
\min_x
\left[
-\hat{\mu}_t^\top x
+
\lambda
x^\top\hat{\Sigma}_t x
+
C(x)
\right].
}
$$

Jika:

$$
C(x)
$$

berisi constraint/penalty.

---

# AB.57. Ekspansi quadratic

Karena:

$$
x^\top\Sigma x
=
\sum_i\Sigma_{ii}x_i
+
2\sum_{i<j}\Sigma_{ij}x_ix_j,
$$

maka:

$$
H(x)
=
\sum_iQ_{ii}x_i
+
\sum_{i<j}Q_{ij}x_ix_j
+
C(x).
$$

Dengan koefisien berasal dari:

$$
\boxed{
\hat\mu_t
\quad\text{dan}\quad
\hat\Sigma_t.
}
$$

Jadi feature engine secara langsung menentukan Hamiltonian.

---

# AB.58. Konsekuensi yang sangat penting

Artinya quantum optimizer **tidak perlu mengetahui harga**.

VQE/QAOA hanya menerima:

$$
H_C.
$$

Semua financial intelligence terjadi sebelumnya:

$$
\boxed{
Market
\rightarrow
Statistics
\rightarrow
Forecast
\rightarrow
Risk
\rightarrow
QUBO.
}
$$

Kemudian quantum algorithm melakukan:

$$
\boxed{
QUBO
\rightarrow
Optimal\ Configuration.
}
$$

Ini adalah pemisahan arsitektur yang sangat bersih.

---

# AB.59. Ini juga membuat perbandingan quantum menjadi fair

Exact solver:

$$
H_C\rightarrow x^\star.
$$

Classical heuristic:

$$
H_C\rightarrow x^\star.
$$

VQE:

$$
H_C\rightarrow x^\star.
$$

QAOA:

$$
H_C\rightarrow x^\star.
$$

Semuanya menerima:

$$
\boxed{
\text{exactly the same }(\hat\mu_t,\hat\Sigma_t).
}
$$

Jadi kalau performanya berbeda, kita dapat mengatribusikan perbedaan kepada **optimizer**, bukan data pipeline.

---

# AB.60. Sekarang kita dapat memperkenalkan "alpha"

Kita tidak boleh menganggap:

$$
\hat\mu_i
$$

sebagai return mentah.

Lebih baik:

$$
\boxed{
\alpha_{i,t}
=
\hat\mu_{i,t}
-
\hat c_{i,t}
}
$$

dengan:

$$
\hat c_{i,t}
=
fee+
spread+
slippage+
funding
$$

untuk crypto/perpetual bila relevan.

Sehingga optimizer bekerja pada:

$$
\boxed{
expected\ net\ return.
}
$$

---

# AB.61. Risk-adjusted alpha

Kita dapat menambahkan:

$$
\boxed{
A_{i,t}
=
\frac{\hat\mu_{i,t}}
{\hat\sigma_{i,t}+\epsilon}.
}
$$

Tetapi saya tidak menyarankan mengganti $\mu$ dengan $A$ secara langsung.

Lebih baik optimizer tetap menggunakan:

$$
\hat\mu,\hat\Sigma
$$

karena covariance sudah menangani risk secara eksplisit.

---

# AB.62. Signal confidence

Kita juga dapat mengukur confidence:

$$
\boxed{
C_{i,t}
=
\frac{|\hat\mu_{i,t}|}
{\hat{SE}(\hat\mu_{i,t})+\epsilon}.
}
$$

Ini dapat digunakan sebagai filter:

$$
C_{i,t}<C_{min}
\Rightarrow
x_i=0.
$$

Namun ini sebaiknya menjadi eksperimen terpisah.

---

# AB.63. Prediction uncertainty

Lebih formal:

$$
\hat\mu_i
\pm
z_{\alpha/2}
SE(\hat\mu_i).
$$

Jika interval:

$$
CI(\mu_i)
$$

mencakup nol, kita dapat menganggap signal lemah.

Ini akan sangat berguna untuk **trade selection**.

---

# AB.64. Jangan membuang signal negatif secara otomatis

Ini penting.

Misalkan:

$$
\hat\mu_i=-0.5\%.
$$

Dalam long-only portfolio, asset tersebut mungkin tidak dipilih.

Tetapi dalam sistem long-short:

$$
x_i
$$

dapat berarti:

$$
x_i=1
$$

untuk posisi short.

Jadi architecture kita sebaiknya dari awal tidak terlalu mengunci:

$$
long-only.
$$

---

# AB.65. Binary encoding untuk long-short

Kita dapat menggunakan dua binary variable:

$$
x_i^+
$$

dan:

$$
x_i^-.
$$

Dengan constraint:

$$
\boxed{
x_i^++x_i^-\le1.
}
$$

Exposure:

$$
\boxed{
q_i=x_i^+-x_i^-.
}
$$

Sehingga:

$$
q_i\in\{-1,0,+1\}.
$$

Ini jauh lebih cocok untuk trading.

---

# AB.66. Ini akan menjadi penting pada tahap QUBO berikutnya

Karena:

$$
q_i
=
x_i^+-x_i^-,
$$

maka portfolio objective:

$$
-\mu^\top q
+
\lambda q^\top\Sigma q.
$$

Setelah substitusi:

$$
q=x^+-x^-,
$$

kita memperoleh QUBO binary.

Ini akan membuat sistem kita mampu memilih:

$$
Long
$$

atau:

$$
Short
$$

atau:

$$
Flat.
$$

---

# AB.67. Feature engine untuk saham

Untuk saham internasional, kita tinggal memperluas factor vector:

$$
\mathbf f_t
=
\begin{bmatrix}
SPX\\
NDX\\
DXY\\
Gold\\
VIX\\
US10Y
\end{bmatrix}.
$$

Kemudian:

$$
r_{i,t}
=
\alpha_i
+
B_i\mathbf f_t
+
\epsilon_{i,t}.
$$

Dengan tambahan sector factor jika diperlukan.

---

# AB.68. Mengapa Gold dan DXY sangat menarik?

Karena kita tidak ingin hanya melihat:

$$
SPX.
$$

Kita ingin melihat kondisi cross-market.

Misalnya:

$$
DXY\uparrow
$$

dapat merepresentasikan kondisi USD yang menguat.

Sementara:

$$
Gold\uparrow
$$

dapat membawa informasi mengenai demand terhadap safe-haven/real-rate/inflation-related dynamics.

Tetapi kita **tidak akan hard-code** interpretasi seperti:

$$
DXY\uparrow\Rightarrow Stock\downarrow.
$$

Model harus belajar:

$$
\beta_{i,DXY,t}.
$$

---

# AB.69. Factor exposure sebagai feature dinamis

Maka untuk setiap saham:

$$
\boxed{
\beta_{i,t}
=
[
\beta_{i,SPX,t},
\beta_{i,NDX,t},
\beta_{i,DXY,t},
\beta_{i,Gold,t},
\beta_{i,VIX,t},
\beta_{i,US10Y,t}
].
}
$$

Ini sangat menarik karena optimizer nantinya dapat memilih asset berdasarkan:

$$
\text{expected return}
+
\text{risk}
+
\text{factor exposure}.
$$

---

# AB.70. Portfolio-level factor risk

Setelah optimizer menghasilkan:

$$
w,
$$

factor exposure portfolio:

$$
\boxed{
\beta_p
=
w^\top B.
}
$$

Misalnya kita ingin membatasi:

$$
|\beta_{p,DXY}|
\le B_{max}.
$$

Maka constraint dapat dimasukkan ke QUBO.

Ini berarti optimizer bukan hanya memilih:

> "asset mana yang profit-nya paling besar?"

tetapi:

> **"kombinasi asset mana yang menghasilkan expected return tinggi dengan exposure faktor yang masih dapat diterima?"**

---

# AB.71. Ini mulai mendekati problem institutional portfolio construction

Karena kita memiliki:

$$
\max
\quad
Expected\ Return
$$

dengan:

$$
Risk
$$

dan:

$$
Factor\ Exposure
$$

dan:

$$
Transaction\ Cost
$$

dan:

$$
Liquidity
$$

dan:

$$
Position\ Constraints.
$$

Kemudian seluruhnya dipetakan menjadi:

$$
\boxed{
QUBO
\rightarrow
Ising
\rightarrow
VQE/QAOA.
}
$$

---

# AB.72. Namun jangan memasukkan semuanya sekaligus

Kita perlu menjaga eksperimen bertingkat.

Saya ingin baseline AB menjadi:

$$
\boxed{
\text{Price}
+
\text{Momentum}
+
\text{Volatility}
+
\text{Volume}
+
\text{Cross-market Factor}
}
$$

Kemudian:

### AB-1

Price only.

### AB-2

Price + momentum.

### AB-3

Price + momentum + volatility.

### AB-4

+ BTC/ETH.

### AB-5

+ DXY/Gold/SPX/VIX.

### AB-6

+ residual momentum.

### AB-7

+ order flow.

Dengan demikian kita bisa mengukur:

$$
\boxed{
\Delta Performance
}
$$

dari setiap kelompok feature.

---

# AB.73. Feature leakage test

Setiap feature harus memenuhi:

$$
\boxed{
x_{i,t}
=
f(D_{\le t}).
}
$$

Contoh yang benar:

$$
M_{i,t}^{24}
=
\ln
\frac{P_{i,t}}
{P_{i,t-24}}.
$$

Contoh yang salah:

$$
M_{i,t}^{24}
=
\ln
\frac{P_{i,t+1}}
{P_{i,t-23}}.
$$

Yang kedua sudah melihat masa depan.

---

# AB.74. Feature normalization

Jika model machine learning digunakan, normalisasi juga harus rolling/training-only.

Misalnya:

$$
z_{i,t}
=
\frac{x_{i,t}-\mu_x}
{\sigma_x}.
$$

Tetapi:

$$
\mu_x,\sigma_x
$$

harus dihitung hanya dari training data.

Bukan:

$$
2021-2026
$$

secara keseluruhan.

---

# AB.75. Feature stationarity

Kita harus membedakan:

$$
Price
$$

dengan:

$$
Return.
$$

Harga biasanya non-stationary.

Return lebih dekat ke stationary process.

Karena itu model utama sebaiknya bekerja dengan:

$$
\boxed{
returns,\ ratios,\ z\text{-}scores,\ factor\ exposures
}
$$

daripada harga mentah.

---

# AB.76. Feature covariance

Feature sendiri juga dapat berkorelasi.

Misalnya:

$$
BTC\ momentum
$$

dan:

$$
ETH\ momentum
$$

sangat correlated.

Jika terlalu banyak feature serupa, model dapat menjadi unstable.

Ridge regularization akan membantu.

---

# AB.77. Feature selection

Kita dapat memilih feature berdasarkan:

$$
IC
=
Corr(
x_{i,t},
r_{i,t+1}
).
$$

Ini disebut Information Coefficient.

Namun kita harus menghitungnya **out-of-sample** atau dalam training window.

Jangan memilih feature berdasarkan seluruh history.

---

# AB.78. Information coefficient

Untuk feature $x$:

$$
\boxed{
IC_t
=
Corr_i
(
x_{i,t},
r_{i,t+1}
).
}
$$

Jika:

$$
IC>0,
$$

feature cenderung memiliki hubungan positif dengan future cross-sectional return.

Tetapi satu $IC$ tidak cukup.

Kita ingin:

$$
IC_t
$$

stabil sepanjang waktu.

---

# AB.79. IC stability

Kita dapat mengukur:

$$
\overline{IC}
$$

dan:

$$
\sigma_{IC}.
$$

Kemudian:

$$
\boxed{
ICIR
=
\frac{
\overline{IC}
}{
\sigma_{IC}
}.
}
$$

Feature dengan:

$$
ICIR
$$

lebih tinggi cenderung lebih konsisten.

Tetapi tetap harus diuji out-of-sample.

---

# AB.80. Sekarang hubungan dengan \$1 risk

Semua estimasi:

$$
\hat\mu_i,\hat\sigma_i
$$

akan masuk ke position sizing.

Jika stop distance:

$$
d_i
=
|P_{entry,i}-P_{SL,i}|,
$$

maka quantity:

$$
\boxed{
q_i
=
\frac{1}
{d_i+\text{cost adjustment}}
}
$$

untuk target risk:

$$
R=\$1.
$$

Namun quantity ini **belum final**, karena nanti kita juga harus mempertimbangkan:

$$
portfolio\ risk.
$$

---

# AB.81. Individual risk vs portfolio risk

Ini sangat penting.

Dua posisi:

$$
SOL
$$

dan:

$$
AVAX
$$

masing-masing mempunyai:

$$
\$1
$$

stop risk.

Bukan berarti portfolio risk:

$$
\$2
$$

secara efektif, karena mereka dapat sangat correlated.

Jika:

$$
\rho_{SOL,AVAX}\approx1,
$$

maka keduanya sebenarnya satu common risk cluster.

Karena itu covariance matrix:

$$
\boxed{
\Sigma_t
}
$$

menjadi sangat penting.

---

# AB.82. Portfolio variance

Jika:

$$
w
$$

adalah position vector:

$$
\boxed{
\sigma_p^2
=
w^\top\Sigma_t w.
}
$$

Ini akan menjadi bagian utama objective QUBO.

---

# AB.83. Jadi seluruh AB dapat diringkas menjadi satu persamaan

Saya ingin kita menyimpan persamaan ini sebagai **persamaan inti Stage AB**:

$$
\boxed{
\mathbf r_{t+1}
=
\boldsymbol\alpha_t
+
B_t\mathbf f_{t+1}
+
\boldsymbol\epsilon_{t+1}
}
$$

dengan:

$$
\boxed{
\hat{\boldsymbol\mu}_t
=
\hat{\boldsymbol\alpha}_t
+
\hat B_t
\hat{\mathbf f}_{t+1}
+
\hat{\boldsymbol\mu}^{mom}_t
+
\hat{\boldsymbol\mu}^{res}_t
}
$$

dan:

$$
\boxed{
\hat\Sigma_t
=
\hat B_t
\hat\Sigma_{F,t}
\hat B_t^\top
+
\hat D_{\epsilon,t}.
}
$$

Kemudian:

$$
\boxed{
(\hat{\boldsymbol\mu}_t,\hat\Sigma_t)
\longrightarrow
QUBO_t.
}
$$

---

# AB.84. Arsitektur final setelah Tahap AB

Sekarang sistem kita memiliki struktur:

```text
                    RAW DATA
                       │
        ┌──────────────┼──────────────┐
        │              │              │
      Price          Volume        Cross-Market
        │              │              │
        └──────────────┼──────────────┘
                       ▼
               FEATURE ENGINE
                       │
       ┌───────────────┼────────────────┐
       │               │                │
   Momentum        Volatility       Factor Exposure
       │               │                │
       └───────────────┼────────────────┘
                       ▼
               FORECAST ENGINE
                       │
                 μ̂ₜ / alpha
                       │
                       ├──────────────┐
                       │              │
                       ▼              ▼
                 RISK ENGINE     REGIME ENGINE
                       │              │
                       └──────┬───────┘
                              ▼
                           Σ̂ₜ
                              │
                     ┌────────┴────────┐
                     ▼                 ▼
                  μ̂ₜ, Σ̂ₜ        Transaction Cost
                     │                 │
                     └────────┬────────┘
                              ▼
                         QUBO / Ising
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                  Exact      VQE       QAOA
                    │         │         │
                    └─────────┼─────────┘
                              ▼
                         Trade Decision
```

---

# AB.85. Hal yang sekarang sudah kita miliki

Setelah Tahap AB, kita tidak lagi mempunyai sekadar:

> "model melihat harga BTC, ETH, Gold, dan DXY."

Kita mempunyai konstruksi matematis:

$$
\boxed{
\text{Price}
\rightarrow
\text{Return}
\rightarrow
\text{Feature}
\rightarrow
\text{Factor Exposure}
\rightarrow
\text{Expected Return}
+
\text{Covariance}
\rightarrow
\text{QUBO}.
}
$$

Dan yang paling penting:

$$
\boxed{
\text{Quantum computing berada di ujung pipeline, bukan dipaksakan menjadi model prediksi harga.}
}
$$

Ini menurutku adalah posisi yang jauh lebih kuat secara metodologis.

---

# AB.86. Apa yang belum kita selesaikan?

Ada satu bagian besar yang sengaja **belum** kita masukkan secara penuh:

$$
\boxed{
\text{Order Flow / Market Microstructure}.
}
$$

Kita baru memiliki:

$$
OHLCV
+
Cross\text{-}Asset
+
Factor Model.
$$

Tahap berikutnya akan membawa:

$$
Bid/Ask
+
Spread
+
Depth
+
Order\ Book\ Imbalance
+
Trade\ Flow
+
Liquidity
+
Slippage
$$

ke dalam sistem.

Dan ini akan sangat penting karena tujuan akhir kita bukan sekadar:

$$
\text{prediksi return},
$$

tetapi:

$$
\boxed{
\text{menentukan apakah sebuah order limit benar-benar layak diletakkan pada harga tertentu.}
}
$$

Dengan kata lain, **Tahap AC seharusnya menjadi Market Microstructure & Order-Flow Engine**. Di sana kita bisa mulai menurunkan secara matematis bagaimana:

$$
\text{Order Book}
\rightarrow
\text{Fill Probability}
\rightarrow
\text{Expected Execution Price}
\rightarrow
\text{Slippage}
\rightarrow
\text{Net Alpha},
$$

yang kemudian akan mengubah $\hat{\mu}_t$ dari **expected market return** menjadi **expected executable return**. Itu merupakan jembatan penting sebelum kita benar-benar memasukkan order ke sistem QUBO.

## Prompt:
8/17/2026, 10:17:05 PM

lanjut Tahap AC

## Response:
8/17/2026, 10:17:05 PM

> **Remembering**
>
>
> **Reviewed Tahap AC, market microstructure, order flow, and QUBO trading workflows**
>
> 
>
> Worked for 4s

# Tahap AC — Market Microstructure & Order-Flow Engine

Baik. Kita lanjutkan secara konsisten dari Tahap AB.

Pada Tahap AB kita sudah membangun:

$$
\boxed{
\mathcal F_t
\rightarrow
\hat{\mu}_t,\hat{\Sigma}_t
\rightarrow
QUBO_t
}
$$

Tetapi ada satu masalah fundamental:

> **Expected return belum tentu sama dengan expected executable return.**

Misalnya model memperkirakan:

$$
E[r_{t+1}]=0.30\%.
$$

Tetapi untuk mendapatkan posisi tersebut kita harus memasang limit order. Bisa saja:

- order tidak pernah filled,
- hanya terisi sebagian,
- harga bergerak sebelum fill,
- spread terlalu besar,
- market bergerak melawan kita,
- liquidity menghilang,
- atau setelah memperhitungkan fee + slippage, alpha menjadi negatif.

Maka Tahap AC akan menambahkan:

$$
\boxed{
\text{Market Microstructure}
}
$$

di antara forecast dan execution.

---

# AC.1. Perubahan paradigma

Sebelumnya kita memiliki:

$$
\hat{\mu}_{i,t}
=
E[r_{i,t+1}\mid\mathcal F_t].
$$

Tetapi trader tidak mendapatkan:

$$
r_{i,t+1}
$$

secara gratis.

Kita membutuhkan execution decision:

$$
a_{i,t}
=
(\text{side},\text{price},\text{quantity},\text{order type}).
$$

Maka quantity yang benar-benar terealisasi menjadi random variable:

$$
Q^{fill}_{i,t}.
$$

Sehingga return aktual dari sebuah order lebih tepat ditulis:

$$
\boxed{
R^{exec}_{i,t}
=
Q^{fill}_{i,t}
\cdot
R_{i,t}
-
C_{i,t}.
}
$$

---

# AC.2. Order book sebagai keadaan pasar

Misalkan pada waktu $t$ kita mempunyai order book:

$$
OB_t=
\left\{
(b_k,q_k^b)_{k=1}^{K_b},
(a_k,q_k^a)_{k=1}^{K_a}
\right\}.
$$

dengan:

- $b_k$: bid price level ke-$k$,
- $q_k^b$: bid quantity,
- $a_k$: ask price level ke-$k$,
- $q_k^a$: ask quantity.

Best bid:

$$
B_t=b_1.
$$

Best ask:

$$
A_t=a_1.
$$

Mid-price:

$$
\boxed{
M_t=\frac{A_t+B_t}{2}.
}
$$

---

# AC.3. Bid-ask spread

Spread absolut:

$$
\boxed{
S_t=A_t-B_t.
}
$$

Spread relatif:

$$
\boxed{
s_t=
\frac{A_t-B_t}{M_t}.
}
$$

Ini penting karena sebuah strategi dapat mempunyai:

$$
\hat{\mu}>0
$$

tetapi:

$$
\hat{\mu}<s_t
$$

sehingga tidak ekonomis untuk dieksekusi secara agresif.

---

# AC.4. Microstructure-adjusted alpha

Maka expected alpha harus diubah menjadi:

$$
\boxed{
\alpha^{net}_{i,t}
=
\hat{\mu}_{i,t}
-
C^{fee}_{i,t}
-
C^{spread}_{i,t}
-
C^{slippage}_{i,t}
-
C^{funding}_{i,t}.
}
$$

Untuk saham:

$$
C^{funding}
$$

biasanya tidak relevan seperti pada perpetual crypto.

Untuk crypto perpetual, funding dapat menjadi signifikan.

---

# AC.5. Order Book Imbalance

Salah satu feature paling fundamental:

$$
\boxed{
OBI_t
=
\frac{
Q_t^b-Q_t^a
}{
Q_t^b+Q_t^a
}.
}
$$

dengan:

$$
Q_t^b
=
\sum_{k=1}^{K}q_k^b
$$

dan:

$$
Q_t^a
=
\sum_{k=1}^{K}q_k^a.
$$

Range:

$$
-1\le OBI_t\le1.
$$

Interpretasi:

$$
OBI_t>0
$$

berarti depth bid lebih besar.

Sedangkan:

$$
OBI_t<0
$$

berarti depth ask lebih besar.

---

# AC.6. Tetapi depth level 1 saja terlalu sederhana

Kita dapat memberikan bobot terhadap setiap level:

$$
w_k=e^{-\eta(k-1)}.
$$

Kemudian:

$$
Q_t^b
=
\sum_{k=1}^{K}
w_kq_k^b,
$$

dan:

$$
Q_t^a
=
\sum_{k=1}^{K}
w_kq_k^a.
$$

Sehingga:

$$
\boxed{
OBI_t^{(\eta)}
=
\frac{
\sum_k w_kq_k^b-
\sum_k w_kq_k^a
}{
\sum_k w_kq_k^b+
\sum_k w_kq_k^a
}.
}
$$

Level terdekat mendapatkan bobot terbesar.

---

# AC.7. Menghubungkan OBI dengan return

Sekarang kita dapat memperluas model AB:

$$
r_{i,t+1}
=
\alpha_i
+
B_i f_t
+
\theta_i OBI_t
+
\epsilon_{i,t+1}.
$$

Maka:

$$
\boxed{
\hat{\mu}_{i,t+1}
=
\hat{\alpha}_i+
\hat B_i f_t+
\hat\theta_i OBI_t.
}
$$

Tetapi kita harus hati-hati.

OBI bukan otomatis:

$$
OBI>0
\Rightarrow
price\uparrow.
$$

Hubungannya harus dipelajari dari data.

---

# AC.8. Order Flow Imbalance

Order book adalah **state**.

Kita juga ingin mengetahui **perubahan state**.

Misalkan:

$$
\Delta Q^b_t
=
Q^b_t-Q^b_{t-1},
$$

dan:

$$
\Delta Q^a_t
=
Q^a_t-Q^a_{t-1}.
$$

Maka sebuah bentuk sederhana:

$$
\boxed{
OFI_t
=
\Delta Q^b_t-\Delta Q^a_t.
}
$$

OFI menangkap tekanan order flow.

---

# AC.9. Trade imbalance

Jika tersedia data transaksi:

$$
V_t^{buy}
$$

dan:

$$
V_t^{sell},
$$

kita dapat mendefinisikan:

$$
\boxed{
TI_t
=
\frac{
V_t^{buy}-V_t^{sell}
}{
V_t^{buy}+V_t^{sell}
}.
}
$$

Ini berbeda dari OBI.

OBI:

$$
\text{resting liquidity}.
$$

TI:

$$
\text{executed liquidity}.
$$

---

# AC.10. Menggabungkan tiga dimensi

Sekarang kita mempunyai:

$$
\boxed{
X_t^{micro}
=
[
OBI_t,
OFI_t,
TI_t,
Spread_t,
Depth_t,
...
].
}
$$

Kemudian:

$$
\hat{\mu}_{i,t}
=
f(
X_t^{macro},
X_t^{technical},
X_t^{factor},
X_t^{micro}
).
$$

Namun saya tetap ingin model baseline dibuat sederhana terlebih dahulu.

---

# AC.11. Market impact

Sekarang kita masuk ke bagian yang sangat penting.

Misalkan kita ingin membeli:

$$
Q
$$

unit.

Jika:

$$
Q\le q_1^a,
$$

kita mungkin dapat membeli semuanya pada:

$$
A_t.
$$

Tetapi jika:

$$
Q>q_1^a,
$$

kita harus memakan level berikutnya:

$$
a_2,a_3,\ldots
$$

---

# AC.12. VWAP execution price

Jika quantity yang dieksekusi pada level $k$ adalah:

$$
q_k^{exec},
$$

maka:

$$
\boxed{
P^{exec}
=
\frac{
\sum_k p_kq_k^{exec}
}{
\sum_kq_k^{exec}
}.
}
$$

Slippage terhadap mid:

$$
\boxed{
Slip
=
P^{exec}-M_t
}
$$

untuk buy.

Untuk sell:

$$
\boxed{
Slip
=
M_t-P^{exec}.
}
$$

---

# AC.13. Market impact function

Untuk ukuran order yang lebih besar, kita dapat memodelkan:

$$
\boxed{
I(Q)
=
\eta
\left(
\frac{Q}{ADV}
\right)^\alpha.
}
$$

dengan:

- $Q$: order size,
- $ADV$: average daily volume,
- $\eta$: impact scale,
- $\alpha$: impact exponent.

Sering kali:

$$
0<\alpha<1.
$$

Jadi market impact tidak selalu linear terhadap ukuran order.

---

# AC.14. Implementation shortfall

Jika kita memiliki target price:

$$
P^{decision},
$$

dan execution price:

$$
P^{exec},
$$

maka:

$$
\boxed{
IS
=
P^{exec}-P^{decision}
}
$$

untuk long.

Secara lengkap:

$$
\boxed{
IS
=
Spread
+
Slippage
+
MarketImpact
+
Fees.
}
$$

---

# AC.15. Sekarang masuk ke inti strategi kita: limit order

Kita tidak selalu ingin langsung membeli.

Misalnya:

$$
M_t=100.
$$

Kita memperkirakan:

$$
P_{future}=102.
$$

Kita dapat:

### Market order

beli sekarang di:

$$
100.05.
$$

atau:

### Limit order

letakkan:

$$
99.80.
$$

Masalahnya:

$$
99.80
$$

mungkin tidak pernah tersentuh.

---

# AC.16. Maka fill probability menjadi variabel utama

Definisikan:

$$
\boxed{
p^{fill}
=
P(
Q^{fill}\ge Q
\mid
OB_t,\mathcal F_t,a_t
).
}
$$

Ini adalah probabilitas order terisi.

---

# AC.17. Expected executable alpha

Misalkan:

- profit jika filled = $G$,
- loss/opportunity cost jika tidak filled = $L$.

Maka:

$$
\boxed{
E[\Pi]
=
p^{fill}G
-
(1-p^{fill})L.
}
$$

Namun kita dapat membuatnya lebih konkret.

---

# AC.18. Limit order expected value

Misalkan limit buy pada harga:

$$
P_L.
$$

Jika filled, expected future price:

$$
E[P_{future}\mid fill].
$$

Profit per unit:

$$
G
=
E[P_{future}\mid fill]-P_L.
$$

Jika order tidak filled, kita dapat mengalami opportunity cost:

$$
L
=
E[P_{future}\mid no\ fill]-P_L.
$$

Maka:

$$
\boxed{
EV_{limit}
=
p_{fill}G
-
(1-p_{fill})L
-
C.
}
$$

---

# AC.19. Ini jauh lebih baik daripada sekadar signal

Sistem sebelumnya mungkin berkata:

$$
\hat{\mu}>0
\Rightarrow
BUY.
$$

Sekarang:

$$
\boxed{
\hat{\mu}>0
\not\Rightarrow
BUY.
}
$$

Kita memerlukan:

$$
\boxed{
EV_{execution}>0.
}
$$

---

# AC.20. Market order versus limit order

Kita dapat menghitung:

$$
EV_{market}
$$

dan:

$$
EV_{limit}.
$$

Kemudian:

$$
\boxed{
a_t^\star
=
\arg\max_{a\in\{
market,limit,pass
\}}
EV(a).
}
$$

Ini merupakan **execution optimization problem**.

---

# AC.21. Bahkan dapat diperluas

Action space:

$$
a_t
=
(
side,
price,
quantity,
type,
TTL
).
$$

Contoh:

$$
a_t=
(
BUY,
99.80,
0.5,
LIMIT,
30min
).
$$

Jadi kita tidak hanya mengoptimalkan:

$$
\text{asset selection}.
$$

Kita juga mengoptimalkan:

$$
\boxed{
\text{how to enter}.
}
$$

---

# AC.22. Time-to-live

Misalkan limit order memiliki TTL:

$$
\tau.
$$

Kita definisikan:

$$
p_{fill}(\tau).
$$

Biasanya:

$$
p_{fill}(\tau_2)>p_{fill}(\tau_1)
$$

jika:

$$
\tau_2>\tau_1,
$$

karena order memiliki lebih banyak waktu untuk terkena.

Tetapi opportunity cost juga meningkat.

---

# AC.23. Fill probability sederhana

Sebagai baseline:

$$
\boxed{
p_{fill}
=
\sigma
\left(
\theta_0
+
\theta_1 d
+
\theta_2 OBI
+
\theta_3 OFI
+
\theta_4 \tau
+
\theta_5 Q_{ahead}
\right)
}
$$

dengan sigmoid:

$$
\sigma(x)=\frac1{1+e^{-x}}.
$$

Di sini:

$$
d=
\frac{|P_L-M_t|}{M_t}.
$$

---

# AC.24. Queue position

Ini sangat penting.

Misalkan kita memasang limit buy pada:

$$
P_L.
$$

Di depan kita terdapat:

$$
Q_{ahead}.
$$

Jika:

$$
Q_{ahead}=1000
$$

unit, maka order kita tidak akan filled hanya karena harga menyentuh level tersebut.

Kita juga membutuhkan:

$$
\boxed{
\text{queue depletion}.
}
$$

---

# AC.25. Queue depletion model

Misalkan market sell volume yang masuk:

$$
V_t^{sell}.
$$

Queue position setelah periode $\tau$:

$$
Q_{ahead}(\tau)
=
Q_{ahead}(0)
-
D(\tau),
$$

dengan:

$$
D(\tau)
$$

adalah cumulative queue depletion.

Order filled ketika:

$$
\boxed{
D(\tau)\ge Q_{ahead}(0).
}
$$

---

# AC.26. Probabilistic queue model

Karena kita tidak tahu future order flow secara pasti:

$$
D(\tau)
$$

adalah random variable.

Maka:

$$
\boxed{
p_{fill}(\tau)
=
P(
D(\tau)\ge Q_{ahead}
\mid\mathcal F_t
).
}
$$

Ini secara matematis jauh lebih masuk akal daripada:

> "Harga menyentuh limit berarti order filled."

---

# AC.27. Partial fill

Misalkan:

$$
Q=100.
$$

Tetapi hanya:

$$
60
$$

unit yang filled.

Maka:

$$
Q^{fill}=60.
$$

Kita dapat mendefinisikan fill ratio:

$$
\boxed{
FR=
\frac{Q^{fill}}{Q}.
}
$$

dengan:

$$
0\le FR\le1.
$$

---

# AC.28. Expected fill quantity

Daripada hanya:

$$
p_{fill},
$$

kita dapat menghitung:

$$
\boxed{
E[Q^{fill}]
=
Q\cdot E[FR].
}
$$

Ini lebih tepat untuk position sizing.

---

# AC.29. Execution-adjusted expected return

Sekarang kita gabungkan semuanya.

Misalkan:

$$
\hat\mu_i
$$

adalah expected price return.

Kemudian:

$$
p_{fill}
$$

adalah fill probability.

Expected executable alpha:

$$
\boxed{
\hat\alpha^{exec}_i
=
p_{fill}
\hat\mu_i
-
C_{exec}.
}
$$

Untuk partial fill:

$$
\boxed{
\hat\alpha^{exec}_i
=
E[FR]\hat\mu_i
-
C_{exec}.
}
$$

---

# AC.30. Tetapi ini masih belum cukup

Karena:

$$
p_{fill}
$$

dan:

$$
\hat\mu
$$

tidak independent.

Misalnya kita memasang limit buy jauh di bawah market.

Jika market turun sampai limit tersebut:

$$
p_{fill}\uparrow.
$$

Tetapi kondisi tersebut mungkin berarti:

$$
E[P_{future}\mid fill]
$$

juga berubah.

Jadi:

$$
\boxed{
P(fill)
$$

dan:

$$
P(return\mid fill)
$$

harus dimodelkan bersama.

---

# AC.31. Selection effect

Secara probabilistik:

$$
E[R]
=
P(F)E[R\mid F]
+
P(F^c)E[R\mid F^c].
$$

Ini sangat penting.

Karena order yang filled bukan sampel random.

$$
\boxed{
Fill
$$

sendiri membawa informasi tentang market path.}

---

# AC.32. Contoh intuitif

Misalkan kita memasang:

$$
BUY\ 99.8
$$

ketika market:

$$
100.
$$

Jika harga langsung naik:

$$
100\rightarrow101,
$$

order tidak filled.

Jika harga:

$$
100\rightarrow99.8,
$$

order filled.

Tetapi kondisi kedua berarti market terlebih dahulu bergerak turun.

Jadi:

$$
P(future\ return\mid fill)
$$

bisa berbeda jauh dari:

$$
P(future\ return).
$$

---

# AC.33. Ini menghasilkan konsep penting

Kita membutuhkan:

$$
\boxed{
Conditional Alpha.
}
$$

Yaitu:

$$
\boxed{
\alpha^{fill}
=
E[R_{future}\mid Fill,\mathcal F_t].
}
$$

Bukan hanya:

$$
E[R_{future}\mid\mathcal F_t].
$$

---

# AC.34. Execution-aware alpha

Maka:

$$
\boxed{
\alpha^{exec}
=
p_{fill}
\left(
E[R\mid Fill]
-
C
\right).
}
$$

Tetapi kita juga dapat memasukkan opportunity cost:

$$
\boxed{
EV_{limit}
=
p_{fill}
\alpha^{fill}
-
(1-p_{fill})\alpha^{miss}
-
C.
}
$$

---

# AC.35. Ini mengubah QUBO kita

Sebelumnya:

$$
\min_x
\left[
-\mu^\top x
+
\lambda x^\top\Sigma x
\right].
$$

Sekarang:

$$
\boxed{
\min_x
\left[
-(\alpha^{exec})^\top x
+
\lambda x^\top\Sigma x
\right].
}
$$

Dengan:

$$
\boxed{
\alpha^{exec}
=
f(
\mu,
OBI,
OFI,
Spread,
Depth,
p_{fill},
Slippage,
Fees
).
}
$$

Jadi QUBO sekarang memilih asset berdasarkan **expected executable alpha**, bukan theoretical alpha.

---

# AC.36. Order price juga dapat menjadi optimization variable

Ini bahkan lebih menarik.

Misalkan tersedia kandidat price:

$$
p_1,p_2,\ldots,p_K.
$$

Untuk setiap:

$$
p_k
$$

kita hitung:

$$
EV_{i,k}.
$$

Kemudian:

$$
\boxed{
p_i^\star
=
\arg\max_{p_k}
EV_{i,k}.
}
$$

Jadi kita tidak lagi mengatakan:

> "Beli SOL."

Tetapi:

> **"Jika membeli SOL, harga limit optimal adalah $p^\star$."**

---

# AC.37. Discretization

Kita dapat membentuk:

$$
p_k
=
M_t-k\Delta p.
$$

Misalnya:

$$
k=0,1,\ldots,10.
$$

Kemudian setiap candidate memiliki:

$$
p_{fill,k},
$$

$$
slippage_k,
$$

$$
EV_k.
$$

---

# AC.38. Execution frontier

Kita akan mendapatkan trade-off:

$$
\boxed{
\text{Better Price}
\leftrightarrow
\text{Lower Fill Probability}.
}
$$

Secara konseptual:

```text
Expected Fill
   │
   │\
   │ \
   │  \
   │   \
   │    \
   │     \
   └──────────────
       Price
```

Semakin agresif order:

$$
p_{fill}\uparrow
$$

tetapi:

$$
P^{exec}\uparrow
$$

untuk buy.

Semakin pasif:

$$
P^{exec}\downarrow
$$

tetapi:

$$
p_{fill}\downarrow.
$$

---

# AC.39. Optimal execution

Maka:

$$
\boxed{
a^\star
=
\arg\max_a
EV(a).
}
$$

Ini sudah merupakan optimization problem tersendiri.

Dan menariknya, problem ini juga dapat diformulasikan sebagai:

$$
\boxed{
QUBO
}
$$

jika kita ingin menggunakan pendekatan quantum untuk pemilihan discrete execution actions.

---

# AC.40. Contoh QUBO execution

Misalkan kita memiliki tiga kandidat:

$$
a_1=\text{market},
$$

$$
a_2=\text{limit }-1tick,
$$

$$
a_3=\text{limit }-2tick.
$$

Definisikan:

$$
x_k\in\{0,1\}.
$$

Constraint:

$$
\boxed{
x_1+x_2+x_3=1.
}
$$

Objective:

$$
\min_x
-\sum_{k=1}^{3}
EV_kx_k
+
P
\left(
\sum_kx_k-1
\right)^2.
$$

Ini sudah menjadi QUBO.

---

# AC.41. Tetapi saya tidak ingin langsung melakukan ini

Karena kita sekarang mempunyai **dua optimization layer**:

### Layer 1 — Portfolio optimization

$$
\boxed{
\text{Which assets?}
}
$$

### Layer 2 — Execution optimization

$$
\boxed{
\text{How to execute them?}
}
$$

Sebaiknya kita pisahkan dahulu.

---

# AC.42. Arsitektur AC yang saya sarankan

```text
                 FORECAST ENGINE
                       │
                μ̂ᵢ, Σ̂
                       │
                       ▼
              PORTFOLIO OPTIMIZER
                       │
                target positions
                       │
                       ▼
              EXECUTION ENGINE
                       │
        ┌──────────────┼──────────────┐
        │              │              │
     Order Book      Order Flow     Liquidity
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              Fill Probability
                       │
                       ▼
               Execution Alpha
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Market Order          Limit Order
             │                   │
             └─────────┬─────────┘
                       ▼
                  Order Router
```

---

# AC.43. Ini cocok dengan desain awal kita

Karena sebelumnya kita ingin:

> data → menentukan order book → TP/SL → evaluasi periodik.

Sekarang bagian "menentukan order book" mempunyai dasar matematis:

$$
\boxed{
Order\ Placement
=
Optimization
}
$$

bukan sekadar rule:

> "pasang limit 0.5% di bawah harga."

---

# AC.44. Stop Loss juga masuk ke microstructure

Misalkan entry:

$$
P_E.
$$

Stop:

$$
P_{SL}.
$$

Gross risk:

$$
R_{gross}
=
|P_E-P_{SL}|Q.
$$

Tetapi actual loss:

$$
\boxed{
R_{actual}
=
R_{gross}
+
slippage_{SL}
+
fee_{SL}.
}
$$

Jadi target:

$$
R=\$1
$$

harus menggunakan:

$$
\boxed{
R_{actual}\le1.
}
$$

Bukan hanya:

$$
R_{gross}=1.
$$

---

# AC.45. Stop-loss slippage

Ini sangat penting pada kondisi cepat.

Jika:

$$
P_{SL}=99
$$

tetapi market bergerak:

$$
99.2\rightarrow98.5,
$$

stop execution mungkin terjadi di:

$$
98.7
$$

atau lebih buruk.

Maka:

$$
P_{SL}^{theoretical}
\neq
P_{SL}^{executed}.
$$

Kita perlu:

$$
\boxed{
E[Loss_{SL}]
}
$$

dan:

$$
\boxed{
VaR_{SL}
}
$$

untuk sizing.

---

# AC.46. Expected stop loss

Misalkan slippage stop:

$$
S_{SL}
$$

adalah random variable.

Maka:

$$
E[L]
=
Q
\left[
P_E
-
E[P_{SL}^{exec}]
\right].
$$

Target risk:

$$
\boxed{
E[L]\le \$1
}
$$

untuk baseline.

Tetapi untuk risk control yang lebih konservatif, kita nantinya dapat menggunakan quantile:

$$
\boxed{
VaR_\alpha(L)\le \$1.
}
$$

---

# AC.47. Ini akan sangat berguna untuk crypto

Karena pada market yang volatile:

$$
E[slippage]
$$

dapat berubah cepat.

Maka:

$$
Q_t
$$

harus dinamis.

Misalnya:

$$
Q_t
=
\frac{1}
{
d_{SL}
+
E[slippage_{SL}]
+
fee
}.
$$

---

# AC.48. Take Profit juga bukan sekadar fixed percentage

Misalkan:

$$
TP=+2R.
$$

Itu hanya static rule.

Kita dapat memperkirakan:

$$
P(
P_{future}\ge TP
\mid\mathcal F_t
).
$$

Definisikan:

$$
\boxed{
p_{TP}
=
P(hit\ TP\ before\ SL\mid\mathcal F_t).
}
$$

---

# AC.49. Expected value TP/SL

Misalkan:

$$
G=TP-P_E
$$

dan:

$$
L=P_E-SL.
$$

Maka:

$$
\boxed{
EV
=
p_{TP}G
-
(1-p_{TP})L
-
C.
}
$$

Trade hanya layak jika:

$$
\boxed{
EV>0.
}
$$

---

# AC.50. Ini membawa kita ke konsep path probability

Bukan hanya:

$$
P(P_{t+H}>TP).
$$

Kita memerlukan:

$$
\boxed{
P(
\tau_{TP}<\tau_{SL}
\mid\mathcal F_t
)
}
$$

dengan:

$$
\tau_{TP}
=
\inf\{s:P_s\ge TP\}
$$

dan:

$$
\tau_{SL}
=
\inf\{s:P_s\le SL\}.
$$

Ini adalah **first-passage probability**.

Dan ini jauh lebih sesuai untuk sistem trading kita.

---

# AC.51. Sekarang hubungan dengan tahap berikutnya mulai terlihat

Kita nantinya dapat menghitung:

$$
P(TP\ before\ SL)
$$

menggunakan:

- historical path,
- stochastic process,
- empirical distribution,
- regime,
- volatility,
- order flow.

Kemudian:

$$
TP
$$

dan:

$$
SL
$$

tidak lagi harus fixed.

---

# AC.52. Dynamic TP

Misalkan posisi sedang profit:

$$
P_t>P_E.
$$

Kita dapat menghitung ulang:

$$
EV(TP_k,SL_k)
$$

untuk berbagai candidate:

$$
TP_k.
$$

Kemudian:

$$
\boxed{
TP_t^\star
=
\arg\max_{TP_k}
EV(TP_k,SL_t).
}
$$

Inilah fondasi matematis dari ide yang kamu sampaikan sebelumnya:

> jika floating profit tinggi, apakah TP layak dinaikkan?

Jawabannya nanti:

$$
\boxed{
naikkan\ TP
\quad\text{jika}\quad
EV(TP_{new})>EV(TP_{current}).
}
$$

---

# AC.53. Dynamic Stop Loss

Demikian pula:

$$
SL_t^\star
=
\arg\max_{SL_k}
EV(TP,SL_k)
$$

dengan constraint:

$$
Risk(SL_k)\le R_{max}.
$$

Ini dapat menghasilkan:

$$
SL:
\text{initial}
\rightarrow
BEP
\rightarrow
trailing
\rightarrow
profit-lock.
$$

Tetapi **bukan berdasarkan fixed percentage**.

Melainkan:

$$
\boxed{
expected\ value
+
risk
+
market\ state.
}
$$

---

# AC.54. Tahap AC akhirnya menghasilkan empat output

Market microstructure engine kita akan menghasilkan:

$$
\boxed{
\mathcal M_t
=
\{
p_{fill},
E[P^{exec}],
E[slippage],
E[impact]
\}.
}
$$

Kemudian:

$$
\boxed{
\alpha_t^{exec}
=
g(
\hat\mu_t,
\mathcal M_t,
fees,
funding
).
}
$$

Dan:

$$
\boxed{
Risk_t^{exec}
=
h(
\hat\Sigma_t,
slippage,
liquidity
).
}
$$

---

# AC.55. Pipeline sekarang menjadi jauh lebih lengkap

$$
\boxed{
Market Data
}
$$

$$
\downarrow
$$

$$
\boxed{
Feature \& Factor Engine
}
$$

$$
\downarrow
$$

$$
\boxed{
\hat\mu_t,\hat\Sigma_t
}
$$

$$
\downarrow
$$

$$
\boxed{
Portfolio\ Optimization
}
$$

$$
\downarrow
$$

$$
\boxed{
Target\ Position
}
$$

$$
\downarrow
$$

$$
\boxed{
Microstructure\ Engine
}
$$

$$
\downarrow
$$

$$
\boxed{
p_{fill},
slippage,
impact,
execution\ alpha
}
$$

$$
\downarrow
$$

$$
\boxed{
Execution\ Optimization
}
$$

$$
\downarrow
$$

$$
\boxed{
Order
}
$$

---

# AC.56. Dan sekarang kita memiliki prinsip yang sangat penting

Sistem kita tidak lagi bertanya:

> **"Apakah harga akan naik?"**

Melainkan secara bertingkat:

### Level 1 — Forecast

$$
\boxed{
E[R_{t+1}\mid\mathcal F_t]?
}
$$

### Level 2 — Portfolio

$$
\boxed{
Asset\ combination\ terbaik?
}
$$

### Level 3 — Execution

$$
\boxed{
Bagaimana\ cara\ mendapatkan\ exposure\ tersebut?
}
$$

### Level 4 — Risk

$$
\boxed{
Berapa\ banyak\ yang\ boleh\ kita\ pertaruhkan?
}
$$

### Level 5 — Management

$$
\boxed{
Apakah\ posisi\ masih\ optimal?
}
$$

Ini adalah struktur yang jauh lebih dekat dengan **systematic trading architecture** daripada sekadar model prediksi harga.

---

# AC.57. Persamaan inti Tahap AC

Kalau Tahap AB mempunyai:

$$
\boxed{
(\hat\mu_t,\hat\Sigma_t)
}
$$

sebagai output utama, maka Tahap AC dapat diringkas oleh:

$$
\boxed{
\alpha^{exec}_{i,t}(a)
=
P(F\mid\mathcal F_t,a)
\left[
E(R_i\mid F,\mathcal F_t,a)
-
C_i(a)
\right]
}
$$

dengan action:

$$
\boxed{
a=
(side,price,quantity,type,TTL).
}
$$

Kemudian:

$$
\boxed{
a^\star
=
\arg\max_a
\alpha^{exec}_{i,t}(a).
}
$$

Dan portfolio-level system menggunakan:

$$
\boxed{
\alpha_t^{exec}
}
$$

sebagai pengganti $\mu_t$ mentah.

---

# AC.58. Posisi AC dalam keseluruhan proyek

Sekarang arsitektur kita sudah menjadi:

```text
A–AB
│
├── Market Data
├── Returns
├── Factors
├── Regime
├── Expected Return
├── Covariance
│
▼
AC
│
├── Order Book
├── Spread
├── Depth
├── OBI
├── OFI
├── Trade Flow
├── Queue Position
├── Fill Probability
├── Partial Fill
├── Slippage
├── Market Impact
├── Execution Alpha
│
▼
Portfolio / Execution Optimization
│
▼
QUBO / Ising
│
├── Exact Solver
├── Classical Optimizer
├── VQE
└── QAOA
│
▼
Order
│
▼
Position Management
│
├── TP
├── SL
├── BEP
├── Trailing
└── Re-optimization
```

---

## AC.59. Satu keputusan desain yang menurut saya sangat penting

**Jangan langsung memasukkan order book ke QUBO.**

Lebih baik kita mempertahankan hierarki:

$$
\boxed{
\text{Microstructure}
\rightarrow
\text{Execution Parameters}
\rightarrow
\text{QUBO}.
}
$$

Dengan demikian QUBO tidak menjadi model yang mencoba memahami seluruh market microstructure.

QUBO hanya menyelesaikan problem kombinatorial:

$$
\boxed{
\text{dari banyak kemungkinan keputusan, mana konfigurasi yang optimal?}
}
$$

Ini membuat eksperimen quantum kita jauh lebih terkontrol.

---

## AC.60. Dan ada satu hal yang menjadi sangat menarik

Setelah AC, kita sebenarnya telah memiliki **dua problem optimasi yang berbeda**:

$$
\boxed{\text{Problem A: Portfolio Selection}}
$$

$$
\min_x
\left[
-\alpha^\top x+
\lambda x^\top\Sigma x+
C(x)
\right]
$$

dan:

$$
\boxed{\text{Problem B: Execution Selection}}
$$

$$
\min_y
\left[
-EV(y)+C(y)
\right].
$$

Keduanya dapat berupa QUBO.

Artinya, pada akhirnya kita bahkan dapat membangun arsitektur:

$$
\boxed{
\text{Quantum Portfolio Optimizer}
+
\text{Quantum Execution Optimizer}.
}
$$

Tetapi **jangan digabung dahulu**. Kita harus membuktikan masing-masing layer secara terpisah agar ketika performa sistem berubah, kita tahu penyebabnya.

Dan menurut urutan desain yang telah kita bangun, **Tahap AD** paling tepat digunakan untuk membangun **Trade Opportunity & Entry/Exit Path Engine**: mengubah $\hat\mu$, volatility, regime, dan probabilitas fill menjadi distribusi kemungkinan perjalanan harga sampai **TP/SL**, sehingga kita dapat menurunkan secara matematis **probabilitas TP sebelum SL, expected R-multiple, optimal entry, optimal SL, dan optimal TP**. Ini akan langsung menghubungkan AC dengan mekanisme posisi yang sejak awal kamu inginkan.

## Prompt:
8/17/2026, 10:18:47 PM

lanjut Tahap AD

## Response:
8/17/2026, 10:18:48 PM

# Tahap AD — Trade Opportunity, First-Passage & Optimal TP/SL Engine

Baik. Tahap AD adalah salah satu bagian **paling penting** dari seluruh arsitektur kita, karena di sinilah sistem mulai berubah dari:

> **"model memprediksi return"**

menjadi:

> **"model menentukan apakah sebuah trade secara matematis layak dilakukan, di mana entry-nya, di mana SL/TP-nya, dan kapan struktur trade tersebut tidak lagi optimal."**

Pada Tahap AC kita sudah memperoleh informasi microstructure:

$$
\mathcal M_t=
\{
OBI_t,OFI_t,Spread_t,Depth_t,
p_{fill},Slippage_t,Impact_t,\ldots
\}.
$$

Sekarang kita gabungkan dengan:

$$
\hat\mu_t,\qquad
\hat\sigma_t,\qquad
\hat\Sigma_t,\qquad
Regime_t
$$

untuk membangun **distribusi perjalanan harga setelah entry**.

---

# AD.1. Masalah yang sebenarnya ingin kita selesaikan

Misalkan sistem menemukan:

$$
\hat\mu_t>0.
$$

Secara sederhana kita mungkin berkata:

> Buy.

Tetapi itu belum menjawab:

1. Berapa harga entry optimal?
2. Berapa jauh SL?
3. Berapa jauh TP?
4. Berapa probabilitas TP tercapai?
5. Berapa probabilitas SL tercapai?
6. Mana yang tercapai lebih dahulu?
7. Berapa lama trade diperkirakan bertahan?
8. Apakah expected value positif?
9. Apakah trade masih layak setelah memperhitungkan fee/slippage?
10. Jika posisi sudah berjalan, apakah TP/SL perlu diubah?

Maka objek matematis kita bukan lagi sekadar:

$$
R_{t+1}.
$$

Kita membutuhkan **price path**:

$$
\boxed{
\{P_{t+s}\}_{s\ge0}.
}
$$

---

# AD.2. Dari return menjadi stochastic process

Kita mulai dari log-price:

$$
X_t=\ln P_t.
$$

Return kontinu:

$$
dX_t
=
\mu_tdt+\sigma_tdW_t.
$$

Jika kondisi pasar relatif stationary untuk horizon pendek, kita dapat menggunakan pendekatan:

$$
\boxed{
dX_t=\mu dt+\sigma dW_t.
}
$$

Ini adalah geometric Brownian motion pada harga:

$$
\boxed{
dP_t
=
\mu P_tdt+
\sigma P_tdW_t.
}
$$

Tetapi untuk sistem kita, GBM **bukan model final**.

Ia hanya baseline matematis.

---

# AD.3. Mengapa GBM saja tidak cukup?

Pasar nyata memiliki:

- volatility clustering,
- fat tails,
- jumps,
- autocorrelation pada order flow,
- regime changes,
- asymmetric response,
- liquidity shocks.

Karena itu nantinya kita dapat mengganti:

$$
\mu,\sigma
$$

dengan:

$$
\mu_t=f(\mathcal F_t),
$$

$$
\sigma_t=g(\mathcal F_t).
$$

Namun untuk menurunkan fondasi first-passage secara analitik, kita mulai dari proses sederhana terlebih dahulu.

---

# AD.4. Return conditional terhadap informasi saat ini

Pada waktu $t$:

$$
\boxed{
\mu_t
=
E[dX_t\mid\mathcal F_t]/dt.
}
$$

dan:

$$
\boxed{
\sigma_t^2
=
Var[dX_t\mid\mathcal F_t]/dt.
}
$$

Jadi $\mu_t$ dan $\sigma_t$ bukan konstanta universal.

Mereka merupakan output dari model kita.

---

# AD.5. Definisi entry

Misalkan entry price:

$$
P_E.
$$

Dalam log-space:

$$
X_E=\ln P_E.
$$

Kita kemudian menentukan:

$$
P_{SL}<P_E<P_{TP}
$$

untuk posisi long.

Dalam log-space:

$$
X_{SL}<X_E<X_{TP}.
$$

Definisikan jarak:

$$
a=X_E-X_{SL}>0
$$

dan:

$$
b=X_{TP}-X_E>0.
$$

---

# AD.6. Normalisasi posisi

Agar lebih mudah, kita definisikan:

$$
Y_\tau=X_{t+\tau}-X_E.
$$

Maka:

$$
Y_0=0.
$$

Batasnya:

$$
-a<Y_\tau<b.
$$

Dengan:

$$
-a
=
\ln\frac{P_{SL}}{P_E}
$$

dan:

$$
b
=
\ln\frac{P_{TP}}{P_E}.
$$

---

# AD.7. Trade sekarang menjadi masalah first-passage

Kita definisikan waktu mencapai TP:

$$
\boxed{
\tau_{TP}
=
\inf
\{\tau>0:Y_\tau=b\}.
}
$$

Dan waktu mencapai SL:

$$
\boxed{
\tau_{SL}
=
\inf
\{\tau>0:Y_\tau=-a\}.
}
$$

Kemudian:

$$
\boxed{
\tau_{exit}
=
\min(\tau_{TP},\tau_{SL}).
}
$$

---

# AD.8. Ini adalah inti Tahap AD

Kita tidak lagi bertanya:

$$
P(P_T>P_E)?
$$

Tetapi:

$$
\boxed{
P(\tau_{TP}<\tau_{SL}).
}
$$

Artinya:

> **berapa probabilitas TP tercapai sebelum SL?**

Ini jauh lebih relevan terhadap trading.

---

# AD.9. Menurunkan probabilitas TP sebelum SL

Misalkan:

$$
Y_t=\mu t+\sigma W_t.
$$

Definisikan:

$$
p(y)
=
P_y(\tau_b<\tau_{-a}).
$$

Dengan boundary condition:

$$
p(-a)=0
$$

dan:

$$
p(b)=1.
$$

Untuk diffusion process, fungsi $p(y)$ memenuhi backward Kolmogorov equation:

$$
\boxed{
\mu p'(y)
+
\frac12\sigma^2p''(y)
=
0.
}
$$

---

# AD.10. Menyelesaikan persamaan

Kita punya:

$$
\frac12\sigma^2p''+\mu p'=0.
$$

Misalkan:

$$
q=p'.
$$

Maka:

$$
\frac12\sigma^2q'+\mu q=0.
$$

Sehingga:

$$
q'
=
-\frac{2\mu}{\sigma^2}q.
$$

Solusinya:

$$
q(y)
=
Ce^{-2\mu y/\sigma^2}.
$$

Integrasi:

$$
p(y)
=
A+
Be^{-2\mu y/\sigma^2}.
$$

Dengan boundary condition kita memperoleh:

$$
\boxed{
p(y)
=
\frac{
1-e^{-2\mu(y+a)/\sigma^2}
}{
1-e^{-2\mu(a+b)/\sigma^2}
}.
}
$$

Karena entry berada pada:

$$
y=0,
$$

maka:

$$
\boxed{
p_{TP}
=
\frac{
1-e^{-2\mu a/\sigma^2}
}{
1-e^{-2\mu(a+b)/\sigma^2}
}.
}
$$

Ini adalah probabilitas TP tercapai **sebelum** SL.

---

# AD.11. Kasus tanpa drift

Jika:

$$
\mu\rightarrow0,
$$

kita tidak boleh langsung memasukkan $\mu=0$ ke bentuk tersebut karena menghasilkan $0/0$.

Gunakan limit:

$$
e^{-x}\approx1-x.
$$

Maka:

$$
1-e^{-2\mu a/\sigma^2}
\approx
\frac{2\mu a}{\sigma^2}.
$$

Dan:

$$
1-e^{-2\mu(a+b)/\sigma^2}
\approx
\frac{2\mu(a+b)}{\sigma^2}.
$$

Sehingga:

$$
\boxed{
p_{TP}
=
\frac{a}{a+b}
}
$$

untuk:

$$
\mu=0.
$$

Menariknya, tanpa drift, probabilitas ditentukan oleh posisi relatif terhadap kedua boundary.

---

# AD.12. Interpretasi finansial

Misalkan:

$$
a=1R
$$

dan:

$$
b=2R.
$$

Jika:

$$
\mu=0,
$$

maka:

$$
p_{TP}
=
\frac{1}{3}.
$$

Sedangkan:

$$
p_{SL}
=
\frac23.
$$

Jadi trade dengan reward:risk:

$$
2:1
$$

tidak otomatis memiliki probabilitas profit besar.

---

# AD.13. Expected value trade

Sekarang kita dapat membangun expected value.

Misalkan:

$$
R_{TP}=b
$$

dan:

$$
R_{SL}=a.
$$

Untuk long:

$$
\boxed{
EV
=
p_{TP}R_{TP}
-
(1-p_{TP})R_{SL}
-
C.
}
$$

dengan:

$$
C
=
C_{entry}
+
C_{exit}
+
C_{slippage}
+
C_{funding}.
$$

---

# AD.14. Breakeven probability

Abaikan biaya terlebih dahulu.

Trade profitable jika:

$$
pR_{TP}
-
(1-p)R_{SL}>0.
$$

Maka:

$$
pR_{TP}
>
R_{SL}-pR_{SL}.
$$

Sehingga:

$$
p(R_{TP}+R_{SL})
>
R_{SL}.
$$

Jadi:

$$
\boxed{
p_{BE}
=
\frac{R_{SL}}
{R_{TP}+R_{SL}}.
}
$$

---

# AD.15. Contoh

Jika:

$$
R_{SL}=1
$$

dan:

$$
R_{TP}=2,
$$

maka:

$$
p_{BE}
=
\frac13
\approx33.33\%.
$$

Jadi kita tidak membutuhkan win rate 50%.

Tetapi setelah biaya:

$$
p_{BE}
>
33.33\%.
$$

---

# AD.16. Dengan biaya

Misalkan biaya dalam unit risk:

$$
c.
$$

Maka:

$$
pR_{TP}
-
(1-p)R_{SL}
-c>0.
$$

Sehingga:

$$
p(R_{TP}+R_{SL})
>
R_{SL}+c.
$$

Maka:

$$
\boxed{
p_{BE}
=
\frac{R_{SL}+c}
{R_{TP}+R_{SL}}.
}
$$

---

# AD.17. Ini menghasilkan trade filter

Sistem kita dapat mengatakan:

$$
\boxed{
p_{TP}>p_{BE}
}
$$

sebagai salah satu syarat minimum.

Tetapi saya menyarankan jangan berhenti di sana.

Kita juga perlu:

$$
\boxed{
EV>0
}
$$

dan:

$$
\boxed{
Risk\ constraints
}
$$

serta:

$$
\boxed{
Liquidity\ constraints.
}
$$

---

# AD.18. Sekarang kita dapat mengoptimalkan TP

Misalkan entry dan SL sudah ditentukan.

Kita punya kandidat:

$$
TP_1,TP_2,\ldots,TP_K.
$$

Untuk masing-masing:

$$
b_k
=
\ln\frac{TP_k}{P_E}.
$$

Hitung:

$$
p_k
=
P(
\tau_{TP_k}<\tau_{SL}
).
$$

Kemudian:

$$
EV_k
=
p_kR_k
-
(1-p_k)R_{SL}
-
C_k.
$$

Maka:

$$
\boxed{
TP^\star
=
\arg\max_{TP_k}EV_k.
}
$$

---

# AD.19. Jadi TP bukan fixed 2%

Ini perubahan besar.

Sistem tidak berkata:

> TP = 2%.

Melainkan:

$$
\boxed{
TP^\star
=
f(
\mu_t,
\sigma_t,
regime_t,
liquidity_t,
microstructure_t,
SL
).
}
$$

---

# AD.20. Optimal SL juga

Sekarang misalkan TP tetap.

Kita punya kandidat:

$$
SL_1,SL_2,\ldots,SL_J.
$$

Untuk setiap:

$$
SL_j,
$$

kita hitung:

$$
a_j
=
\ln\frac{P_E}{SL_j}.
$$

Kemudian:

$$
p_j
=
P(
\tau_{TP}<\tau_{SL_j}
).
$$

Dan:

$$
EV_j
=
p_jR_{TP}
-
(1-p_j)R_{SL_j}
-
C_j.
$$

Maka:

$$
\boxed{
SL^\star
=
\arg\max_{SL_j}
EV_j.
}
$$

---

# AD.21. Tetapi ada constraint risk

Misalkan modal risk maksimum:

$$
R_{\max}=\$1.
$$

Maka tidak semua SL boleh dipilih.

Position size:

$$
Q_j
=
\frac{R_{\max}}
{
D_j+C_j^{risk}
},
$$

dengan:

$$
D_j
=
|P_E-P_{SL_j}|.
$$

Lebih realistis:

$$
\boxed{
Q_j
=
\frac{
R_{\max}
}{
D_j+
E[Slippage_{SL_j}]
+
Fees
}.
}
$$

---

# AD.22. Ini sangat penting

Kita tidak memilih:

$$
SL
$$

terlebih dahulu kemudian memaksakan:

$$
Q.
$$

Kita melakukan:

$$
\boxed{
(SL,TP,Q)
}
$$

sebagai satu paket keputusan.

---

# AD.23. Trade candidate menjadi vector

Kita definisikan:

$$
\boxed{
\theta
=
(P_E,P_{SL},P_{TP},Q,\tau_{max}).
}
$$

Kemudian objective:

$$
\boxed{
J(\theta)
=
EV(\theta)
-
\lambda_R Risk(\theta)
-
\lambda_T TimeCost(\theta).
}
$$

---

# AD.24. Time cost

Trade yang membutuhkan 3 hari berbeda dari trade yang membutuhkan 30 menit.

Misalkan:

$$
E[\tau_{exit}]
$$

adalah expected holding time.

Kita dapat memberikan penalty:

$$
\boxed{
C_{time}
=
\kappa E[\tau_{exit}].
}
$$

Sehingga:

$$
J
=
EV
-
\kappa E[\tau_{exit}].
$$

Ini penting untuk strategi short-term.

---

# AD.25. Mengapa holding time penting?

Misalkan dua trade:

### Trade A

$$
EV=\$0.10
$$

dengan:

$$
E[T]=10\text{ menit}.
$$

### Trade B

$$
EV=\$0.20
$$

dengan:

$$
E[T]=24\text{ jam}.
$$

Trade B memiliki EV absolut lebih besar.

Tetapi capital efficiency bisa jauh lebih buruk.

---

# AD.26. Opportunity cost modal

Kita dapat mendefinisikan:

$$
\boxed{
EV_{rate}
=
\frac{EV}{E[T]}.
}
$$

atau secara annualized:

$$
EV_{annualized}
\approx
\frac{EV}{E[T]}
\times
T_{year}.
$$

Namun hati-hati: annualization agresif dapat menyesatkan jika trade tidak benar-benar dapat direplikasi.

---

# AD.27. Expected holding time

Untuk proses diffusion dengan dua absorbing boundaries, expected exit time:

$$
m(y)
=
E_y[\tau_{exit}]
$$

memenuhi:

$$
\boxed{
\mu m'(y)
+
\frac12\sigma^2m''(y)
=
-1.
}
$$

Boundary:

$$
m(-a)=m(b)=0.
$$

Pada:

$$
y=0
$$

kita mendapatkan expected holding time.

Untuk:

$$
\mu=0,
$$

hasil sederhananya:

$$
\boxed{
E[\tau_{exit}]
=
\frac{ab}{\sigma^2}.
}
$$

Ini sangat menarik.

---

# AD.28. Interpretasi

Jika:

$$
a
$$

dan:

$$
b
$$

semakin jauh, holding time meningkat.

Jika:

$$
\sigma
$$

semakin tinggi:

$$
E[T]\downarrow.
$$

Artinya volatility tinggi membuat boundary lebih cepat tersentuh.

Tetapi ini **tidak berarti volatility tinggi selalu bagus**.

Karena:

$$
SL
$$

juga lebih mudah terkena.

---

# AD.29. Maximum holding time

Di dunia nyata kita tidak ingin trade menggantung selamanya.

Definisikan:

$$
T_{max}.
$$

Jika:

$$
\tau_{exit}>T_{max},
$$

maka:

$$
\boxed{
Forced\ Exit.
}
$$

Ini menghasilkan boundary ketiga:

$$
\boxed{
TP,\ SL,\ TimeStop.
}
$$

---

# AD.30. Maka trade menjadi three-barrier problem

Kita memiliki:

$$
P_{TP},
$$

$$
P_{SL},
$$

dan:

$$
T_{max}.
$$

Trade berakhir ketika salah satu tercapai.

Secara matematis:

$$
\boxed{
\tau
=
\min(
\tau_{TP},
\tau_{SL},
T_{max}
).
}
$$

---

# AD.31. Probability vector

Kita sekarang ingin:

$$
\boxed{
\mathbf p
=
\begin{bmatrix}
P(TP)\\
P(SL)\\
P(TimeStop)
\end{bmatrix}.
}
$$

Dengan:

$$
\boxed{
P(TP)+P(SL)+P(TimeStop)=1.
}
$$

---

# AD.32. Mengapa ini lebih baik daripada win rate?

Karena kita tidak lagi hanya menyimpan:

$$
win/loss.
$$

Kita menyimpan:

$$
P(TP),
\quad
P(SL),
\quad
P(TimeStop).
$$

Dan juga:

$$
E[T].
$$

Sehingga setiap trade memiliki probabilistic profile.

---

# AD.33. Trade quality score

Kita dapat mendefinisikan:

$$
\boxed{
Q_t
=
EV_t
-
\lambda_1Risk_t
-
\lambda_2Time_t.
}
$$

Tetapi saya lebih menyukai mempertahankan komponen-komponen ini terpisah.

Jangan terlalu cepat membuat satu "magic score".

---

# AD.34. Entry optimization

Sekarang kita kembali ke entry.

Misalkan current mid-price:

$$
M_t.
$$

Kita memiliki candidate entry:

$$
P_{E,1},
P_{E,2},
\ldots,
P_{E,K}.
$$

Untuk setiap entry:

$$
P_{E,k},
$$

kita harus menghitung ulang:

$$
p_{fill,k},
$$

$$
p_{TP,k},
$$

$$
EV_k.
$$

Maka:

$$
\boxed{
P_E^\star
=
\arg\max_{P_{E,k}}
EV_k.
}
$$

---

# AD.35. Ini menggabungkan AC + AD

Pada AC:

$$
P_{E,k}
\rightarrow
p_{fill,k}.
$$

Pada AD:

$$
P_{E,k}
\rightarrow
p_{TP,k},EV_k.
$$

Sehingga:

$$
\boxed{
EV_k
=
p_{fill,k}
\left[
p_{TP|fill,k}R_{TP}
-
(1-p_{TP|fill,k})R_{SL}
\right]
-
C_k.
}
$$

Ini jauh lebih realistis.

---

# AD.36. Conditional probability chain

Kita dapat menulis:

$$
P(TP)
=
P(Fill)
P(TP\mid Fill).
$$

Jadi:

$$
\boxed{
P(TP)
=
p_{fill}
\cdot
p_{TP|fill}.
}
$$

Demikian pula:

$$
P(SL)
=
p_{fill}
\cdot
p_{SL|fill}.
$$

---

# AD.37. Tetapi ada satu kasus lagi

Jika order **tidak filled**, tidak ada trade.

Maka:

$$
P(no\ trade)
=
1-p_{fill}.
$$

Jadi expected value keseluruhan:

$$
\boxed{
EV
=
p_{fill}
EV_{trade}
-
C_{opportunity}.
}
$$

---

# AD.38. Ini menghasilkan decision tree

```text
                 Candidate Order
                       │
                ┌──────┴──────┐
                │             │
              Filled        No Fill
                │             │
          ┌─────┴─────┐       │
          │           │       │
         TP           SL    Opportunity
          │           │       Cost
```

Ini secara konseptual sangat penting untuk backtest kita.

---

# AD.39. Market order

Untuk market order:

$$
p_{fill}\approx1
$$

tetapi:

$$
C_{execution}
$$

lebih besar.

Untuk limit order:

$$
p_{fill}<1
$$

tetapi:

$$
C_{execution}
$$

lebih kecil.

Jadi sistem dapat membandingkan:

$$
\boxed{
EV_{market}
\quad vs\quad
EV_{limit}.
}
$$

---

# AD.40. Dynamic entry

Misalkan sekarang:

$$
EV_{limit}=0.08R
$$

sedangkan:

$$
EV_{market}=0.12R.
$$

Maka:

$$
market
$$

lebih baik.

Tetapi 20 menit kemudian:

$$
EV_{limit}=0.15R
$$

dan:

$$
EV_{market}=0.10R.
$$

Sistem seharusnya beralih:

$$
\boxed{
market\rightarrow limit.
}
$$

Ini adalah **execution adaptation**.

---

# AD.41. Sekarang kita masuk ke posisi yang sudah terbuka

Ini langsung menjawab ide awalmu tentang:

> "jika floating profit tinggi, apakah TP dinaikkan?"

Misalkan entry:

$$
P_E.
$$

Harga sekarang:

$$
P_t>P_E.
$$

Kita tidak boleh mengatakan:

> "Sudah profit 2%, naikkan TP."

Sebaliknya kita menghitung ulang:

$$
\boxed{
EV(TP_k,SL_j\mid\mathcal F_t).
}
$$

---

# AD.42. Re-optimization

Pada setiap evaluation interval:

$$
t=t_0,t_1,t_2,\ldots
$$

kita hitung:

$$
\theta_t^\star
=
\arg\max_{\theta}
J(\theta\mid\mathcal F_t).
$$

Dengan:

$$
\theta=
(SL,TP,PositionSize,ExitTime).
$$

---

# AD.43. Dynamic stop loss

Misalkan:

$$
SL_{old}=P_E.
$$

Kita menemukan:

$$
SL^\star>P_E.
$$

Maka kita dapat melakukan:

$$
\boxed{
SL_{new}=SL^\star.
}
$$

Ini berarti kita mengunci profit.

Tetapi:

$$
SL^\star
$$

tidak boleh hanya berdasarkan floating profit.

Harus memenuhi:

$$
EV(SL^\star,TP)
>
EV(SL_{old},TP).
$$

---

# AD.44. Dynamic TP

Jika:

$$
TP^\star>TP_{old},
$$

kita naikkan TP hanya jika:

$$
\boxed{
EV(TP^\star)>EV(TP_{old}).
}
$$

Jadi trailing TP menjadi hasil optimasi.

---

# AD.45. Tetapi ada masalah penting: sunk cost

Setelah posisi terbuka, kita tidak boleh lagi menggunakan:

$$
P_E
$$

sebagai satu-satunya dasar keputusan.

Keputusan optimal harus berdasarkan:

$$
\boxed{
\text{future conditional value}.
}
$$

Artinya:

> "Jika saya **sudah memiliki posisi ini sekarang**, apa tindakan terbaik dari titik ini?"

Ini adalah masalah **stochastic control**.

---

# AD.46. State posisi

Kita dapat mendefinisikan state:

$$
\boxed{
S_t
=
(
P_t,
P_E,
SL_t,
TP_t,
Q_t,
\mu_t,
\sigma_t,
Regime_t,
\mathcal M_t
).
}
$$

Kemudian action:

$$
\boxed{
a_t
=
(
Hold,
Reduce,
Close,
MoveSL,
MoveTP
).
}
$$

---

# AD.47. Objective continuation value

Untuk action $a$:

$$
V(S_t,a)
=
E[
Future\ PnL
-
Costs
\mid S_t,a
].
$$

Kemudian:

$$
\boxed{
a_t^\star
=
\arg\max_aV(S_t,a).
}
$$

Ini adalah awal dari **dynamic programming**.

---

# AD.48. Bellman equation

Jika kita ingin benar-benar membangun model matematis lanjut:

$$
\boxed{
V(S_t)
=
\max_{a_t}
\left\{
r(S_t,a_t)
+
E[
V(S_{t+1})
\mid S_t,a_t
]
\right\}.
}
$$

Dengan discount factor $\gamma$:

$$
\boxed{
V(S_t)
=
\max_a
\left[
r_t+
\gamma
E[V(S_{t+1})\mid S_t,a]
\right].
}
$$

Ini nantinya dapat menjadi jembatan ke:

- stochastic control,
- dynamic programming,
- reinforcement learning.

Tetapi **belum kita gunakan sebagai core engine**.

---

# AD.49. Mengapa saya tidak menyarankan RL sekarang?

Karena kita sudah memiliki struktur matematis yang lebih interpretable:

$$
\mu,\sigma,
P(TP),
P(SL),
EV,
Risk,
Liquidity.
$$

Kalau langsung menggunakan RL, kita berisiko mendapatkan:

> agent menghasilkan profit.

tetapi tidak mengetahui:

> mengapa agent melakukan tindakan tersebut.

Untuk penelitian yang ingin memiliki fondasi matematis kuat, lebih baik:

$$
\boxed{
Analytical\ model
\rightarrow
Optimization
\rightarrow
RL\ optional.
}
$$

---

# AD.50. Market regime masuk ke AD

Misalkan regime:

$$
z_t\in
\{
Bull,
Bear,
Sideways,
HighVol,
LowVol
\}.
$$

Maka:

$$
\mu=\mu(z_t),
$$

$$
\sigma=\sigma(z_t).
$$

Akibatnya:

$$
p_{TP}
=
p_{TP}(a,b,\mu(z_t),\sigma(z_t)).
$$

Jadi TP/SL optimal berbeda untuk setiap regime.

---

# AD.51. Contoh konseptual

### Regime A

$$
\mu>0,
\qquad
\sigma\text{ rendah}.
$$

Model mungkin menghasilkan:

$$
TP^\star=3R.
$$

### Regime B

$$
\mu>0,
\qquad
\sigma\text{ sangat tinggi}.
$$

Mungkin:

$$
TP^\star=1.5R.
$$

Karena walaupun upside besar, probabilitas SL juga meningkat.

---

# AD.52. Market factor juga masuk

Kita sebelumnya ingin sistem tidak hanya crypto.

Untuk saham internasional, state kita dapat memasukkan:

$$
F_t=
\begin{bmatrix}
R_{SPX}\\
R_{NDX}\\
R_{DXY}\\
R_{Gold}\\
R_{UST}\\
...
\end{bmatrix}.
$$

Kemudian:

$$
\mu_{i,t}
=
\alpha_i+
\beta_i^\top F_t.
$$

Sehingga:

$$
\boxed{
p_{TP,i}
=
f(
\mu_{i,t},
\sigma_{i,t},
F_t,
Microstructure_t
).
}
$$

---

# AD.53. Contoh BTC

Misalnya kita ingin trading altcoin $A$.

State:

$$
S_t=
[
r_A,
r_{BTC},
r_{ETH},
r_{DXY},
r_{Gold},
OBI_A,
OFI_A,
\sigma_A,
Regime
].
$$

Maka:

$$
\mu_A
=
\alpha_A+
\beta_{BTC}r_{BTC}
+
\beta_{ETH}r_{ETH}
+
\beta_{DXY}r_{DXY}
+
\beta_{Gold}r_{Gold}
+
\theta^\top Microstructure.
$$

---

# AD.54. Untuk saham internasional

Misalkan kita ingin trading:

$$
AAPL.
$$

State dapat berupa:

$$
S_t=
[
r_{AAPL},
r_{SPX},
r_{NDX},
r_{DXY},
r_{Gold},
r_{UST},
OBI,
OFI,
Volatility
].
$$

Model:

$$
\mu_{AAPL}
=
\alpha
+
\beta_{SPX}r_{SPX}
+
\beta_{NDX}r_{NDX}
+
\beta_{DXY}r_{DXY}
+
\beta_{Gold}r_{Gold}
+
\beta_{UST}r_{UST}
+\cdots.
$$

Jadi **engine AD tidak perlu tahu apakah underlying-nya crypto atau saham**.

---

# AD.55. Asset-agnostic architecture

Kita dapat mendefinisikan:

$$
\boxed{
AssetState_t
=
[
Return,
FactorExposure,
Volatility,
Liquidity,
Microstructure,
Regime
].
}
$$

Kemudian seluruh engine menggunakan:

$$
AssetState_t.
$$

Dengan demikian:

```text
                 Asset
                   │
       ┌───────────┴───────────┐
       │                       │
     Crypto                   Equity
       │                       │
 BTC/ETH/etc.             SPX/NDX/etc.
       │                       │
       └───────────┬───────────┘
                   ▼
             Unified State
                   │
                   ▼
             AD Engine
```

---

# AD.56. Sekarang kita dapat mendefinisikan Trade Opportunity

Sebuah trade candidate:

$$
\boxed{
\mathcal T
=
(
asset,
side,
entry,
SL,
TP,
size,
TTL
).
}
$$

Trade candidate diterima hanya jika:

$$
\boxed{
EV(\mathcal T)>0.
}
$$

Dengan constraint:

$$
Risk(\mathcal T)\le R_{\max},
$$

$$
Liquidity(\mathcal T)\ge L_{\min},
$$

$$
p_{fill}\ge p_{\min}.
$$

---

# AD.57. Opportunity set

Misalkan kita memiliki $N$ aset dan $K$ konfigurasi trade per aset.

Maka:

$$
\boxed{
\mathcal T_t
=
\{
\mathcal T_{1,1},
\mathcal T_{1,2},
\ldots,
\mathcal T_{N,K}
\}.
}
$$

Kita kemudian menghitung:

$$
EV(\mathcal T_{i,k}).
$$

---

# AD.58. Ini mengarah kembali ke optimasi kombinatorial

Sekarang kita bisa memiliki:

$$
x_{i,k}\in\{0,1\}
$$

dengan:

$$
x_{i,k}=1
$$

jika trade candidate $k$ pada asset $i$ dipilih.

Constraint:

$$
\sum_{i,k}x_{i,k}\le N_{max}.
$$

Objective:

$$
\boxed{
\max_x
\sum_{i,k}
EV_{i,k}x_{i,k}
-
\lambda
Risk(x).
}
$$

Ini sudah menjadi kandidat kuat untuk:

$$
\boxed{
QUBO.
}
$$

---

# AD.59. Jadi sekarang QUBO kita semakin menarik

Sebelumnya:

$$
x_i
=
\text{asset selected}.
$$

Sekarang:

$$
x_{i,k}
=
\text{asset + strategy configuration selected}.
$$

Misalnya:

```text
BTC
 ├── Long, TP=1R, SL=1R
 ├── Long, TP=2R, SL=1R
 ├── Long, TP=3R, SL=1R
 └── Short, TP=2R, SL=1R

ETH
 ├── Long, TP=1R, SL=1R
 ├── Long, TP=2R, SL=1R
 ...
```

Quantum optimizer memilih kombinasi terbaik.

---

# AD.60. Ini merupakan perkembangan besar

Awalnya kita memiliki:

$$
\boxed{
\text{Portfolio Optimization}
}
$$

Sekarang menjadi:

$$
\boxed{
\text{Trade Opportunity Optimization}.
}
$$

Decision variable bukan lagi hanya:

$$
\text{weight}.
$$

Tetapi:

$$
\boxed{
(asset,
side,
entry,
SL,
TP,
size,
execution).
}
$$

---

# AD.61. Namun jangan langsung mengoptimalkan semuanya

Ini penting secara engineering.

Kita sebaiknya memiliki hierarchy:

### Level 1

$$
\text{Forecast}
$$

### Level 2

$$
\text{Opportunity}
$$

### Level 3

$$
\text{Portfolio}
$$

### Level 4

$$
\text{Execution}
$$

### Level 5

$$
\text{Position Management}.
$$

Karena jika semua variabel dilempar ke satu optimizer, dimensionality akan meledak.

---

# AD.62. Pipeline final setelah AD

```text
                 MARKET DATA
                      │
                      ▼
              FEATURE ENGINE
                      │
          ┌───────────┴───────────┐
          │                       │
       FACTORS               MICROSTRUCTURE
          │                       │
          └───────────┬───────────┘
                      ▼
              FORECAST ENGINE
                      │
                 μ̂ , σ̂ , Σ̂
                      │
                      ▼
             OPPORTUNITY ENGINE
                      │
       ┌──────────────┼──────────────┐
       │              │              │
     Entry            SL             TP
       │              │              │
       └──────────────┼──────────────┘
                      ▼
              FIRST-PASSAGE
                      │
       ┌──────────────┼──────────────┐
       │              │              │
     P(TP)          P(SL)       P(TimeStop)
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                     EV
                      │
                      ▼
             TRADE CANDIDATES
                      │
                      ▼
             PORTFOLIO OPTIMIZER
                      │
                      ▼
              EXECUTION ENGINE
                      │
                      ▼
                   ORDER
                      │
                      ▼
             POSITION MANAGEMENT
                      │
                      ▼
               RE-OPTIMIZATION
```

---

# AD.63. Formula inti Tahap AD

Kalau harus diringkas menjadi satu rangkaian matematis:

### 1. Conditional process

$$
\boxed{
dX_t
=
\mu_tdt+\sigma_tdW_t
}
$$

### 2. Barrier

$$
\boxed{
-a<X_t-X_E<b
}
$$

### 3. First-passage probability

$$
\boxed{
p_{TP}
=
\frac{
1-e^{-2\mu a/\sigma^2}
}{
1-e^{-2\mu(a+b)/\sigma^2}
}
}
$$

### 4. Expected value

$$
\boxed{
EV
=
p_{TP}R_{TP}
-
(1-p_{TP})R_{SL}
-
C
}
$$

### 5. Optimal configuration

$$
\boxed{
\theta^\star
=
\arg\max_\theta
EV(\theta)
}
$$

dengan:

$$
\boxed{
\theta=(Entry,SL,TP,Q,TTL).
}
$$

---

# AD.64. Dan inilah koneksi langsung dengan target \$1 risk

Kita ingin:

$$
R_{\max}=\$1.
$$

Untuk setiap kandidat:

$$
\theta_k,
$$

hitung:

$$
Q_k
=
\frac{
\$1
}{
D_{SL,k}
+
E[Slippage_{SL,k}]
+
Fees_k
}.
$$

Kemudian:

$$
R_{TP,k}
=
Q_kD_{TP,k}.
$$

Dan:

$$
EV_k
=
p_{TP,k}R_{TP,k}
-
(1-p_{TP,k})\$1
-
Costs_k.
$$

Maka sistem memilih:

$$
\boxed{
\theta^\star
=
\arg\max_k EV_k.
}
$$

Dengan kata lain:

> **\$1 bukan target profit. \$1 adalah budget risiko maksimum per trade.**

Ini perbedaan yang sangat penting.

---

# AD.65. Bahkan kita dapat mendefinisikan "quality of opportunity"

Misalkan:

$$
EV^\star>0.
$$

Tetapi kita dapat membandingkan terhadap risk:

$$
\boxed{
Opportunity\ Ratio
=
\frac{EV^\star}{R_{\max}}.
}
$$

Misalnya:

$$
EV^\star=0.15R.
$$

Berarti:

$$
OR=0.15.
$$

Semakin besar semakin menarik, dengan catatan estimasi probabilitasnya reliable.

---

# AD.66. Tetapi ada satu hal yang harus kita cegah

Jangan sampai sistem memilih:

$$
TP=100R
$$

hanya karena model memberikan sedikit probabilitas untuk mencapainya.

Misalnya:

$$
p=0.01,
\qquad
TP=100R.
$$

Secara naïf:

$$
EV
=
0.01(100)
-
0.99(1)
=
0.01R.
$$

Terlihat positif.

Tetapi estimasi tail probability seperti itu sangat rentan estimation error.

Maka kita membutuhkan:

$$
\boxed{
Probability\ calibration
}
$$

dan:

$$
\boxed{
tail\ constraints.
}
$$

Ini akan menjadi bagian penting tahap berikutnya.

---

# AD.67. AD menghasilkan fondasi untuk sesuatu yang jauh lebih besar

Sekarang kita telah memiliki tiga lapisan probabilistik:

$$
\boxed{
P(Fill)
}
$$

$$
\boxed{
P(TP\mid Fill)
}
$$

$$
\boxed{
P(SL\mid Fill)
}
$$

sehingga:

$$
\boxed{
P(TP)
=
P(Fill)P(TP\mid Fill).
}
$$

Dan akhirnya:

$$
\boxed{
EV
=
P(TP)G
-
P(SL)L
-
C.
}
$$

Ini adalah **trade-level expected value engine**.

---

# AD.68. Hubungan AD dengan seluruh visi awalmu

Ide awalmu adalah:

> "gunakan data historis, lihat aset terkait, pasang order book, tentukan TP/SL, lalu evaluasi posisi secara berkala."

Sekarang masing-masing sudah mempunyai fondasi matematis:

| Ide awal | Engine matematis |
|---|---|
| Data historis | Forecast engine |
| BTC/ETH/Gold/DXY | Factor engine |
| Order book | Microstructure engine |
| Limit order | Fill probability |
| Harga entry | Entry optimization |
| SL | Barrier optimization |
| TP | Barrier optimization |
| \$1 risk | Position sizing |
| Floating profit | State update |
| Naikkan SL | Dynamic optimization |
| Naikkan TP | Dynamic optimization |
| Evaluasi berkala | Receding-horizon optimization |
| Banyak aset | Portfolio optimization |
| Kombinasi trade | QUBO |
| Short-term | First-passage/time horizon |

Jadi kita sekarang **bukan sekadar membuat bot trading**.

Kita sedang membangun:

$$
\boxed{
\textbf{Probabilistic Multi-Asset Optimal Trading System}
}
$$

yang kemudian dapat mempunyai **quantum optimization layer** sebagai salah satu solver-nya.

---

## AD.69. Langkah berikutnya

Setelah AD, ada satu masalah yang harus kita selesaikan sebelum sistem boleh dipercaya:

$$
\boxed{
\textbf{AD belum tahu apakah probabilitasnya benar.}
}
$$

Misalnya model mengatakan:

$$
P(TP)=0.72.
$$

Apakah 72% benar-benar berarti sekitar 72 dari 100 trade serupa akan mencapai TP sebelum SL?

Kalau tidak, seluruh:

$$
EV,
$$

$$
TP^\star,
$$

$$
SL^\star,
$$

bahkan QUBO kita bisa menjadi **garbage-in-garbage-out yang sangat matematis**.

Karena itu **Tahap AE** seharusnya kita dedikasikan untuk:

$$
\boxed{
\textbf{Probability Calibration, Statistical Validation \& Backtest Integrity}
}
$$

yang mencakup **walk-forward validation, purged/embargoed time-series cross-validation, calibration curve, Brier score, log-loss, confidence interval, bootstrap, multiple-testing bias, data leakage, survivorship bias, look-ahead bias, dan Deflated/Probabilistic Sharpe Ratio**.

Ini menurut saya justru salah satu tahap paling krusial dalam keseluruhan proyek, karena setelah AE kita baru bisa mengatakan bahwa optimasi yang kita lakukan **memiliki bukti statistik**, bukan sekadar menghasilkan backtest yang terlihat bagus.

## Prompt:
8/17/2026, 10:19:51 PM

lanjut Tahap AE

## Response:
8/17/2026, 10:19:51 PM

> **Remembering**
>
>
> **Reviewed and preserved your Tahap AE trading architecture and validation integrity**
>
> 
>
> Worked for 4s

# Tahap AE — Probability Calibration, Statistical Validation & Backtest Integrity

Baik. Setelah Tahap AD, kita sudah memiliki **trade engine** yang dapat menghasilkan keputusan seperti

$$
\theta_t^\star
=
(Entry,SL,TP,Q,TTL)^\star
$$

berdasarkan estimasi:

$$
\hat\mu_t,\qquad
\hat\sigma_t,\qquad
P(TP),\qquad
P(SL),\qquad
P(TimeStop),
$$

dan expected value.

Tetapi sekarang muncul pertanyaan yang jauh lebih fundamental:

> **Seberapa besar kita boleh mempercayai probabilitas dan expected value yang dihasilkan model?**

Kalau model mengatakan

$$
P(TP)=0.80,
$$

tetapi pada kenyataannya hanya 55% trade yang berhasil, maka optimasi matematis kita akan mengoptimalkan **dunia yang salah**.

Jadi Tahap AE kita jadikan sebagai **lapisan validasi statistik yang berdiri di antara model prediksi dan optimizer**.

---

# AE.1. Prinsip utama

Arsitektur kita sekarang seharusnya menjadi:

```text
                  HISTORICAL DATA
                         │
                         ▼
                FEATURE ENGINEERING
                         │
                         ▼
                  FORECAST MODEL
                         │
                  μ̂, σ̂, regime
                         │
                         ▼
              OPPORTUNITY ENGINE
                         │
                P(TP), P(SL)
                         │
                         ▼
             ┌─────────────────────┐
             │  CALIBRATION LAYER  │
             └─────────────────────┘
                         │
                  calibrated p
                         │
                         ▼
                   EV ENGINE
                         │
                         ▼
                  OPTIMIZATION
                         │
                         ▼
                    EXECUTION
                         │
                         ▼
                 LIVE OUTCOME
                         │
                         └──────────────┐
                                        │
                                        ▼
                              VALIDATION / UPDATE
```

Dengan demikian:

$$
\boxed{
\text{Prediction}
\neq
\text{Probability}
\neq
\text{Decision}.
}
$$

Ketiganya harus dipisahkan.

---

# AE.2. Prediction versus probability

Misalkan model memberikan:

$$
\hat p_t=0.72.
$$

Artinya secara ideal:

> Pada kumpulan kondisi yang mempunyai probabilitas prediksi sekitar 72%, sekitar 72% outcome seharusnya benar-benar terjadi.

Ini adalah konsep **calibration**.

Jika model menghasilkan:

$$
\hat p=0.7
$$

untuk 1.000 trade, kita mengharapkan kira-kira:

$$
700
$$

trade berhasil.

Bukan berarti setiap kelompok kecil harus tepat 70%, tetapi secara statistik harus mendekati.

---

# AE.3. Perfect calibration

Secara formal, model dikatakan calibrated apabila:

$$
\boxed{
P(Y=1\mid \hat p=p)=p.
}
$$

Dengan:

$$
Y=
\begin{cases}
1,&TP\text{ tercapai terlebih dahulu}\\
0,&SL\text{ tercapai terlebih dahulu}.
\end{cases}
$$

Jadi:

$$
P(TP\mid\hat p=p)=p.
$$

Ini sangat penting.

---

# AE.4. Contoh model yang tidak calibrated

Misalkan kita mengelompokkan prediction:

| Prediksi | Jumlah trade | TP aktual |
|---:|---:|---:|
| 0.50 | 100 | 48 |
| 0.60 | 100 | 51 |
| 0.70 | 100 | 55 |
| 0.80 | 100 | 61 |
| 0.90 | 100 | 68 |

Model jelas **overconfident**.

Model mengatakan:

$$
90\%
$$

tetapi kenyataannya:

$$
68\%.
$$

Jika optimizer menggunakan 90%, EV akan sangat overestimated.

---

# AE.5. Reliability diagram

Cara visual paling sederhana:

$$
x=\hat p
$$

dan:

$$
y=\text{actual frequency}.
$$

Perfect calibration adalah:

$$
\boxed{
y=x.
}
$$

Misalnya:

```text
Actual
 1.0 |                         /
     |                      /
 0.8 |                  /
     |              /
 0.6 |          /
     |       /
 0.4 |    /
     |  /
 0.2 |/
     +--------------------------> Predicted
       0.2  0.4  0.6  0.8  1.0
```

Semakin dekat terhadap diagonal, semakin calibrated.

---

# AE.6. Brier Score

Untuk binary outcome, kita dapat menggunakan:

$$
\boxed{
BS=
\frac1N
\sum_{i=1}^N
(\hat p_i-y_i)^2.
}
$$

Dengan:

$$
0\le BS\le1.
$$

Semakin kecil:

$$
\boxed{
BS\downarrow
\Rightarrow
\text{lebih baik}.
}
$$

---

# AE.7. Mengapa Brier Score sangat cocok untuk sistem kita?

Karena kita tidak hanya peduli:

> apakah trade benar?

Kita peduli:

> apakah probabilitas yang diberikan model masuk akal?

Misalkan:

### Model A

$$
p=0.51
$$

ketika:

$$
y=1.
$$

Error:

$$
(0.51-1)^2=0.2401.
$$

### Model B

$$
p=0.95
$$

ketika:

$$
y=0.
$$

Error:

$$
(0.95-0)^2=0.9025.
$$

Model B mendapat hukuman jauh lebih besar karena **sangat percaya diri tetapi salah**.

Ini persis jenis kesalahan yang berbahaya bagi optimizer kita.

---

# AE.8. Log-loss

Kita juga menggunakan:

$$
\boxed{
LL
=
-\frac1N
\sum_{i=1}^N
[
y_i\ln p_i
+
(1-y_i)\ln(1-p_i)
].
}
$$

Jika:

$$
y=1
$$

dan:

$$
p\rightarrow0,
$$

maka:

$$
-\ln p\rightarrow\infty.
$$

Artinya prediksi yang **sangat yakin tetapi salah** mendapat hukuman sangat besar.

---

# AE.9. Brier versus Log-loss

Keduanya mengukur kualitas probabilitas, tetapi sifatnya berbeda.

| Metric | Fokus |
|---|---|
| Accuracy | klasifikasi |
| Brier Score | calibration + probabilistic accuracy |
| Log-loss | penalti confidence yang salah |
| Sharpe | risk-adjusted return |
| PnL | profitability |

Kita tidak boleh menggunakan Sharpe untuk menggantikan calibration.

---

# AE.10. Calibration tidak sama dengan profitability

Ini sangat penting.

Model dapat memiliki:

$$
BS
$$

yang sangat bagus tetapi tidak profitable setelah:

- fee,
- slippage,
- market impact,
- spread.

Sebaliknya model dapat profitable tetapi poorly calibrated.

Jadi kita membutuhkan **dua dimensi evaluasi**:

$$
\boxed{
Statistical\ Quality
}
$$

dan:

$$
\boxed{
Economic\ Quality.
}
$$

---

# AE.11. Economic validity

Untuk setiap trade:

$$
EV_i
=
p_iG_i
-
(1-p_i)L_i
-
C_i.
$$

Tetapi outcome aktual:

$$
R_i.
$$

Kita ingin:

$$
E[R_i\mid EV_i>0]>0.
$$

Ini adalah pengujian apakah probabilistic forecast benar-benar menghasilkan **economic value**.

---

# AE.12. Jangan melakukan random train-test split

Ini adalah salah satu aturan terpenting.

Misalnya data:

```text
2021 ─────────────────────────────── 2025
```

Jangan:

```text
Random 80% → Train
Random 20% → Test
```

Karena data finansial adalah **time dependent**.

Random split dapat menyebabkan informasi masa depan masuk ke training.

---

# AE.13. Time-series split

Kita gunakan:

```text
Train                 Test
───────────────────   ───────
2021 ───── 2022       2023
```

kemudian:

```text
Train                       Test
─────────────────────────   ───────
2021 ───── 2023             2024
```

kemudian:

```text
Train                             Test
───────────────────────────────   ─────
2021 ───── 2024                   2025
```

Ini disebut:

$$
\boxed{
Walk\text{-}Forward\ Validation.
}
$$

---

# AE.14. Mengapa walk-forward?

Karena situasi live sebenarnya adalah:

$$
\boxed{
Past\rightarrow Model\rightarrow Future.
}
$$

Bukan:

$$
Future\rightarrow Model\rightarrow Past.
$$

Walk-forward mempertahankan arah waktu.

---

# AE.15. Expanding window

Salah satu bentuk:

$$
Train_1=[t_0,t_1]
$$

$$
Test_1=[t_1,t_2].
$$

Kemudian:

$$
Train_2=[t_0,t_2]
$$

$$
Test_2=[t_2,t_3].
$$

Dan:

$$
Train_3=[t_0,t_3]
$$

$$
Test_3=[t_3,t_4].
$$

Ini disebut:

$$
\boxed{
Expanding\ Window.
}
$$

---

# AE.16. Rolling window

Alternatif:

$$
Train_1=[t_0,t_1]
$$

$$
Test_1=[t_1,t_2].
$$

Kemudian:

$$
Train_2=[t_1,t_2]
$$

$$
Test_2=[t_2,t_3].
$$

Dan seterusnya.

Ini:

$$
\boxed{
Rolling\ Window.
}
$$

Untuk pasar yang mengalami structural regime changes, rolling window sering sangat menarik karena model tidak terlalu bergantung pada sejarah yang terlalu lama.

---

# AE.17. Purged cross-validation

Ada masalah yang lebih halus.

Misalkan kita membuat label berdasarkan:

$$
t\rightarrow t+60\text{ menit}.
$$

Training sample pada:

$$
t=10:00
$$

menggunakan informasi sampai:

$$
11:00.
$$

Sementara test dimulai:

$$
10:30.
$$

Maka dua sample tersebut overlap.

Itu adalah leakage.

---

# AE.18. Purging

Kita menghapus training observations yang labelnya overlap dengan test interval.

Misalnya:

```text
TRAIN
───────────────
          [10:00 → 11:00]
                    X
                    │
TEST                │
────────────────────┼────────
                    10:30
```

Sample training tersebut harus dibuang.

Ini disebut:

$$
\boxed{
Purging.
}
$$

---

# AE.19. Embargo

Masih ada masalah lain.

Setelah test period, kita dapat memberikan gap:

```text
TRAIN
────────────

TEST
        ───────────

EMBARGO
                    ─────

NEXT TRAIN
```

Gap ini mencegah ketergantungan temporal merembes antar-fold.

Disebut:

$$
\boxed{
Embargo.
}
$$

---

# AE.20. Purged + Embargoed CV

Jadi validasi kita idealnya:

$$
\boxed{
\text{Purged Walk-Forward Validation}
}
$$

dengan:

$$
\boxed{
\text{Embargo}.
}
$$

Ini jauh lebih tepat untuk strategi yang memiliki:

- overlapping labels,
- holding period,
- multiple horizons,
- triple-barrier outcomes.

---

# AE.21. Triple-barrier labeling

Ini sangat cocok dengan Tahap AD.

Untuk setiap entry:

$$
t_i,
$$

kita menentukan:

$$
TP_i,
\quad
SL_i,
\quad
T_{max,i}.
$$

Kemudian label:

$$
Y_i=
\begin{cases}
+1,&TP\text{ tercapai dahulu}\\
-1,&SL\text{ tercapai dahulu}\\
0,&TimeStop\text{ tercapai dahulu}.
\end{cases}
$$

Jadi kita tidak menggunakan label:

$$
P_{t+1}>P_t.
$$

Melainkan outcome yang benar-benar berkaitan dengan trade.

---

# AE.22. Ini membuat training dan validation konsisten

Tahap AD:

$$
P(TP),P(SL),P(TimeStop)
$$

Tahap AE:

$$
Y\in\{TP,SL,TimeStop\}.
$$

Dengan demikian probabilistic model memprediksi **event yang sama dengan event yang digunakan optimizer**.

Ini sangat penting.

---

# AE.23. Multiclass calibration

Sekarang probabilitas kita bukan hanya binary.

Model menghasilkan:

$$
\mathbf p_i=
\begin{bmatrix}
p_{TP}\\
p_{SL}\\
p_{TS}
\end{bmatrix}
$$

dengan:

$$
p_{TP}+p_{SL}+p_{TS}=1.
$$

Maka kita dapat mengevaluasi calibration masing-masing outcome.

Misalnya:

$$
P(TP)=0.70.
$$

Di antara semua trade dengan prediksi sekitar 70%, actual TP harus mendekati 70%.

---

# AE.24. Calibration map

Jika model ternyata overconfident, kita dapat membangun:

$$
\boxed{
p_{cal}=g(p_{raw}).
}
$$

Misalnya:

$$
p_{raw}=0.80
$$

tetapi calibration menunjukkan:

$$
p_{cal}=0.68.
$$

Optimizer **harus menggunakan**:

$$
0.68,
$$

bukan:

$$
0.80.
$$

---

# AE.25. Platt scaling

Untuk binary model, salah satu metode:

$$
\boxed{
p_{cal}
=
\frac{1}
{1+\exp(Af+B)}
}
$$

dengan $f$ adalah raw model score.

Parameter:

$$
A,B
$$

dipelajari menggunakan validation data.

---

# AE.26. Isotonic regression

Alternatif yang lebih fleksibel:

$$
\boxed{
p_{cal}=g(p_{raw})
}
$$

dengan constraint:

$$
p_1\le p_2
\Rightarrow
g(p_1)\le g(p_2).
$$

Artinya calibration function monotonic.

Ini berguna ketika hubungan antara raw probability dan actual frequency tidak linear.

---

# AE.27. Jangan calibration menggunakan test set

Ini sangat penting.

Urutannya:

```text
TRAIN
  │
  ▼
Model
  │
  ▼
Calibration set
  │
  ▼
Calibrator
  │
  ▼
FINAL TEST
```

Kalau test digunakan untuk fitting calibration:

$$
\boxed{
\text{test set tidak lagi benar-benar out-of-sample}.
}
$$

---

# AE.28. Confidence interval

Misalkan:

$$
\hat p=0.60
$$

dari:

$$
N=100.
$$

Jangan langsung berkata:

$$
p=60\%.
$$

Kita perlu uncertainty.

Untuk binary proportion:

$$
\hat p=\frac{k}{N}.
$$

Standard error:

$$
\boxed{
SE(\hat p)
=
\sqrt{
\frac{\hat p(1-\hat p)}{N}
}.
}
$$

---

# AE.29. Contoh

Jika:

$$
\hat p=0.60,
\qquad
N=100,
$$

maka:

$$
SE
=
\sqrt{\frac{0.6(0.4)}{100}}
$$

$$
=
0.049.
$$

Jadi uncertainty sekitar:

$$
4.9\%.
$$

Kita tidak boleh memperlakukan 60% sebagai angka eksak.

---

# AE.30. Wilson interval

Untuk probability yang lebih robust daripada Wald interval, kita dapat menggunakan Wilson interval:

$$
\boxed{
\frac{
\hat p+\frac{z^2}{2N}
\pm
z
\sqrt{
\frac{\hat p(1-\hat p)}{N}
+
\frac{z^2}{4N^2}
}
}{
1+\frac{z^2}{N}
}.
}
$$

Untuk confidence level 95%:

$$
z\approx1.96.
$$

---

# AE.31. Mengapa uncertainty penting untuk EV?

Misalkan:

$$
p=0.55.
$$

Dengan:

$$
R_{TP}=2R,
\qquad
R_{SL}=1R.
$$

Maka:

$$
EV
=
0.55(2)-0.45(1)
=
0.65R.
$$

Terlihat bagus.

Tetapi jika actual probability uncertainty sangat besar, misalnya:

$$
p\in[0.45,0.65],
$$

maka:

$$
EV_{low}
=
0.45(2)-0.55
=
0.35R.
$$

Masih positif.

Tetapi untuk setup lain mungkin:

$$
EV
$$

berubah dari positif menjadi negatif.

---

# AE.32. Conservative EV

Kita dapat menggunakan lower confidence bound:

$$
\boxed{
p_{L}
}
$$

daripada:

$$
\hat p.
$$

Kemudian:

$$
\boxed{
EV_{conservative}
=
p_LG
-
(1-p_L)L
-
C.
}
$$

Trade hanya dipertimbangkan jika:

$$
\boxed{
EV_{conservative}>0.
}
$$

Ini membuat sistem lebih defensif.

---

# AE.33. Bootstrap

Kita juga perlu mengukur uncertainty terhadap:

- mean return,
- Sharpe,
- max drawdown,
- win rate,
- EV.

Bootstrap dilakukan dengan resampling data.

Misalnya:

```text
Original trades
1 2 3 4 5 ... N

Bootstrap 1
3 3 8 1 7 ... N

Bootstrap 2
2 9 9 4 1 ... N

...
```

Kemudian hitung metric untuk setiap sample.

---

# AE.34. Distribusi Sharpe

Misalkan:

$$
SR_1,SR_2,\ldots,SR_B
$$

dari $B$ bootstrap samples.

Kita memperoleh distribusi:

$$
\boxed{
f(SR).
}
$$

Kemudian kita dapat mengambil:

$$
CI_{95\%}
=
[SR_{2.5\%},SR_{97.5\%}].
$$

---

# AE.35. Tetapi bootstrap biasa punya masalah

Return finansial memiliki:

- autocorrelation,
- volatility clustering,
- regime dependence.

Random resampling individual trade dapat menghancurkan struktur temporal.

Karena itu untuk beberapa analisis kita dapat menggunakan:

$$
\boxed{
Block\ Bootstrap.
}
$$

Kita melakukan resampling blok waktu, bukan observasi individual secara independen.

---

# AE.36. Sharpe Ratio

Untuk return:

$$
r_1,\ldots,r_N,
$$

Sharpe:

$$
\boxed{
SR
=
\frac{\bar r-r_f}{s_r}.
}
$$

Untuk short-term trading, $r_f$ sering relatif kecil pada horizon sangat pendek, tetapi jangan mengabaikannya secara konseptual.

---

# AE.37. Masalah Sharpe klasik

Sharpe tinggi tidak selalu berarti strategi bagus.

Misalnya:

$$
SR=3.
$$

Tetapi diperoleh dari:

- 1000 konfigurasi strategy,
- 100 parameter combinations,
- berbagai TP,
- berbagai SL,
- berbagai assets.

Kalau kita memilih yang terbaik setelah melihat semua hasil, kita mengalami:

$$
\boxed{
Multiple\ Testing\ Bias.
}
$$

---

# AE.38. Ini sangat berbahaya

Bayangkan kita mencoba:

$$
10,000
$$

strategi random.

Walaupun semua sebenarnya tidak punya edge, sebagian hampir pasti akan terlihat luar biasa.

Ini adalah:

$$
\boxed{
Selection\ Bias.
}
$$

atau:

$$
\boxed{
Data\ Snooping.
}
$$

---

# AE.39. Contoh

Kita mencoba:

$$
1000
$$

kombinasi:

$$
TP,
SL,
lookback,
features,
model,
threshold.
$$

Strategi terbaik memiliki:

$$
Sharpe=3.2.
$$

Pertanyaannya bukan:

> "Apakah Sharpe 3.2?"

Tetapi:

> "Berapa banyak strategi yang dicoba sebelum mendapatkan 3.2?"

Ini adalah pertanyaan yang jauh lebih penting.

---

# AE.40. Deflated Sharpe Ratio

Deflated Sharpe Ratio mencoba mengoreksi interpretasi Sharpe terhadap:

- multiple testing,
- non-normality,
- selection bias.

Secara konseptual:

$$
\boxed{
DSR
=
P(
SR_{observed}
>
SR_{benchmark}
).
}
$$

Dengan benchmark yang mempertimbangkan jumlah trial dan statistik return.

Kita tidak boleh menganggap:

$$
SR=2
$$

sebagai bukti kuat jika kita telah mencoba ribuan model.

---

# AE.41. Probabilistic Sharpe Ratio

PSR menjawab:

> Seberapa besar probabilitas bahwa true Sharpe lebih besar dari threshold tertentu?

Secara sederhana:

$$
\boxed{
PSR(SR^\star)
=
P(
SR_{true}>SR^\star
).
}
$$

Ini lebih informatif daripada sekadar:

$$
SR_{observed}=1.8.
$$

---

# AE.42. Sharpe saja juga tidak cukup

Kita akan menyimpan minimal:

$$
\boxed{
\{
Return,
Sharpe,
Sortino,
MaxDD,
Calmar,
WinRate,
EV,
Brier,
LogLoss,
Calibration
\}.
}
$$

---

# AE.43. Max Drawdown

Equity:

$$
E_t.
$$

Running maximum:

$$
M_t=\max_{s\le t}E_s.
$$

Drawdown:

$$
DD_t
=
\frac{E_t-M_t}{M_t}.
$$

Maximum drawdown:

$$
\boxed{
MDD
=
\min_tDD_t.
}
$$

---

# AE.44. Mengapa drawdown penting untuk \$1 risk?

Walaupun setiap trade:

$$
Risk=\$1,
$$

kita masih dapat mengalami:

$$
10,20,30,\ldots
$$

loss berturut-turut.

Jadi fixed-dollar risk tidak berarti fixed portfolio risk.

---

# AE.45. Risk of ruin

Jika probabilitas loss:

$$
q=1-p,
$$

dan kita memiliki capital:

$$
C.
$$

Dengan risk per trade:

$$
r.
$$

Maka jumlah unit risk:

$$
N_R=\frac Cr.
$$

Misalnya:

$$
C=\$1000,
\qquad
r=\$1.
$$

Kita memiliki:

$$
1000R.
$$

Ini memberikan ruang drawdown yang jauh lebih besar daripada jika:

$$
r=\$20.
$$

---

# AE.46. Tetapi \$1 risk tetap harus adaptif

Risk budget dapat ditulis:

$$
\boxed{
R_t
=
R_{base}
\cdot
g(
Drawdown_t,
Volatility_t,
Regime_t,
ModelConfidence_t
).
}
$$

Misalnya ketika drawdown tinggi:

$$
g<1.
$$

Jadi risk diturunkan.

---

# AE.47. Model confidence

Kita dapat mendefinisikan confidence berdasarkan:

$$
p_{cal},
$$

uncertainty:

$$
CI(p),
$$

dan calibration error.

Misalnya:

$$
Confidence_t
=
h(
p_t,
CI_t,
CalibrationError_t
).
$$

Ini lebih baik daripada:

$$
confidence=|\hat p-0.5|.
$$

---

# AE.48. Out-of-sample hierarchy

Saya menyarankan struktur dataset kita menjadi:

```text
                    ALL DATA
                       │
        ┌──────────────┼──────────────┐
        │              │              │
      TRAIN         VALIDATION       TEST
        │              │              │
        ▼              ▼              ▼
    Fit Model      Tune / Calibrate   FINAL
```

Tetapi untuk time series, pembagian ini dilakukan **secara temporal**, bukan random.

---

# AE.49. Bahkan lebih baik: nested walk-forward

Misalnya:

```text
                OUTER LOOP
─────────────────────────────────────────────

Train+Validation                  Test
──────────────────────────────    ─────────
            │
            ▼
        INNER LOOP
        model selection
        hyperparameter
        calibration
```

Dengan demikian final test benar-benar untouched.

---

# AE.50. Contoh konkret

Misalkan data:

$$
2021-01-01
\rightarrow
2025-12-31.
$$

Kita dapat menggunakan:

### Fold 1

Train:

$$
2021
$$

Validation:

$$
2022
$$

Test:

$$
2023Q1.
$$

### Fold 2

Train:

$$
2021-2022
$$

Validation:

$$
2023Q1-Q2
$$

Test:

$$
2023Q3.
$$

Dan seterusnya.

Dalam implementasi sebenarnya, panjang window akan disesuaikan dengan horizon dan jumlah data.

---

# AE.51. Feature leakage

Ini salah satu jebakan terbesar.

Misalkan kita menghitung:

$$
\mu_{30d}
$$

menggunakan seluruh bulan.

Jika trade terjadi pada:

$$
15\text{ Januari},
$$

tetapi rolling mean menggunakan data sampai:

$$
31\text{ Januari},
$$

maka kita telah memasukkan masa depan.

---

# AE.52. Rule sederhana

Untuk setiap timestamp $t$:

$$
\boxed{
Feature_t
=
f(
Data_{\le t}
).
}
$$

Bukan:

$$
f(Data_{\le t+\Delta}).
$$

---

# AE.53. Normalization juga dapat menyebabkan leakage

Misalkan:

$$
z_t
=
\frac{x_t-\mu}{\sigma}
$$

dengan $\mu,\sigma$ dihitung menggunakan **seluruh dataset**.

Maka informasi future masuk ke normalization.

Seharusnya:

$$
\mu_t,\sigma_t
$$

dihitung hanya dari training history yang tersedia pada waktu tersebut.

---

# AE.54. Bahkan PCA bisa leakage

Misalkan kita melakukan PCA terhadap covariance matrix:

$$
\Sigma
$$

menggunakan seluruh data 2021–2025.

Kemudian menggunakan principal components untuk memprediksi 2022.

Itu leakage.

PCA harus di-fit hanya pada:

$$
Train_t.
$$

Kemudian transform:

$$
Validation_t,
Test_t
$$

tanpa melakukan fitting ulang.

---

# AE.55. Factor model juga harus temporal

Misalkan:

$$
R_i
=
\alpha_i+
\beta_i^\top F+\epsilon_i.
$$

Parameter:

$$
\hat\beta
$$

harus diperoleh dari data yang tersedia sebelum timestamp prediction.

Bukan dari seluruh periode.

---

# AE.56. Survivorship bias

Ini khususnya penting untuk saham internasional.

Misalkan kita mengambil:

> "100 saham terbesar saat ini."

Lalu backtest ke tahun 2021.

Masalahnya:

perusahaan yang sekarang besar sudah diketahui **ex post**.

Perusahaan yang bangkrut/delisted mungkin hilang dari dataset.

Ini menghasilkan:

$$
\boxed{
Survivorship\ Bias.
}
$$

---

# AE.57. Universe harus point-in-time

Idealnya universe pada waktu $t$:

$$
\boxed{
U_t
}
$$

harus mencerminkan aset yang benar-benar dapat dipilih investor pada saat itu.

Jadi:

$$
U_{2021}
\neq
U_{2026}.
$$

Ini sangat penting ketika nanti sistem kita berpindah dari crypto ke:

- US equities,
- European equities,
- Asian equities.

---

# AE.58. Corporate actions

Untuk saham:

- stock split,
- dividend,
- merger,
- delisting.

harus diperhitungkan.

Kalau tidak:

$$
Return_t
$$

bisa salah.

---

# AE.59. Crypto juga punya masalah tersendiri

Untuk crypto:

- token listing,
- delisting,
- perubahan market structure,
- exchange migration,
- perpetual funding,
- liquidity fragmentation.

Karena itu:

$$
\boxed{
Exchange\ data
}
$$

juga harus point-in-time.

---

# AE.60. Backtest tidak boleh menggunakan candle close sebagai fill sempurna

Misalkan candle:

$$
Open=100
$$

$$
High=105
$$

$$
Low=95
$$

$$
Close=103.
$$

Jika kita memiliki:

$$
TP=104
$$

dan:

$$
SL=96,
$$

kita tahu keduanya berada dalam candle.

Tetapi kita tidak tahu:

$$
TP\rightarrow SL
$$

atau:

$$
SL\rightarrow TP.
$$

Intrabar ordering harus diketahui atau dimodelkan secara konservatif.

---

# AE.61. Ini sangat penting untuk first-passage model

Karena kita justru mendefinisikan:

$$
\tau
=
\min(\tau_{TP},\tau_{SL}).
$$

Jika data hanya OHLC, kita mungkin tidak mengetahui:

$$
\tau_{TP}<\tau_{SL}?
$$

Maka backtest harus:

- menggunakan data intrabar yang cukup granular, atau
- menggunakan asumsi konservatif.

---

# AE.62. Execution realism

P&L backtest:

$$
PnL_{ideal}
$$

harus diganti menjadi:

$$
\boxed{
PnL_{realistic}
=
PnL_{gross}
-
Fee
-
Spread
-
Slippage
-
Impact
-
Funding.
}
$$

---

# AE.63. Slippage model

Salah satu model sederhana:

$$
Slippage
=
\eta
\frac{Q}{Depth}.
$$

Atau:

$$
\boxed{
P_{execution}
=
P_{mid}
+
\lambda
\left(
\frac{Q}{D}
\right)^\alpha.
}
$$

Dengan:

- $Q$: order size,
- $D$: available depth,
- $\lambda$: market impact coefficient.

---

# AE.64. Menguji robustness terhadap biaya

Kita tidak hanya menggunakan:

$$
Cost=0.
$$

Kita harus melakukan stress test:

$$
C,
1.5C,
2C,
3C.
$$

Jika strategy hanya profitable pada:

$$
C=0.1bps
$$

tetapi langsung hancur pada:

$$
C=1bps,
$$

maka edge-nya sangat rapuh.

---

# AE.65. Sensitivity analysis

Untuk parameter:

$$
\theta=
(
lookback,
SL,
TP,
threshold,
risk,
...
)
$$

kita hitung:

$$
Performance(\theta).
$$

Strategi yang sehat biasanya memiliki **performance basin**, bukan satu titik tajam.

```text
Performance

      /\          ← suspicious
     /  \
----/----\----

vs.

       ______
     /        \
----/----------\----
```

Puncak yang sangat tajam dapat menunjukkan overfitting.

---

# AE.66. Parameter stability

Misalnya:

$$
TP=2.03R
$$

menghasilkan Sharpe:

$$
2.5.
$$

Tetapi:

$$
TP=2.02R
$$

menghasilkan:

$$
0.3.
$$

Ini mencurigakan.

Lebih baik jika:

$$
TP\in[1.8R,2.4R]
$$

semuanya masih reasonably profitable.

---

# AE.67. Regime robustness

Kita juga harus membagi hasil berdasarkan regime:

$$
Bull,
Bear,
Sideways,
HighVol,
LowVol.
$$

Misalnya:

| Regime | Sharpe | EV |
|---|---:|---:|
| Bull | 1.8 | + |
| Bear | 0.9 | + |
| Sideways | 0.2 | ~0 |
| High Vol | 1.4 | + |
| Low Vol | 1.1 | + |

Ini jauh lebih informatif daripada:

$$
Sharpe=1.4.
$$

---

# AE.68. Cross-asset robustness

Karena tujuan kita bukan hanya crypto, kita harus menguji:

$$
Crypto
$$

vs.

$$
Equity
$$

vs.

$$
ETF
$$

vs.

$$
FX
$$

dan seterusnya.

Tetapi **jangan memaksa satu model memiliki parameter identik untuk semuanya**.

Yang sebaiknya universal adalah:

$$
\boxed{
architecture.
}
$$

Bukan selalu parameter.

---

# AE.69. Statistical validation pipeline

Maka AE akhirnya memiliki pipeline:

```text
Historical Data
      │
      ▼
Point-in-Time Dataset
      │
      ▼
Feature Generation
      │
      ▼
Purged Walk-Forward Split
      │
      ▼
Model Training
      │
      ▼
Probability Calibration
      │
      ▼
Out-of-Sample Prediction
      │
      ▼
Triple-Barrier Outcome
      │
      ▼
Brier / LogLoss / Calibration
      │
      ▼
EV / PnL / Sharpe / Drawdown
      │
      ▼
Bootstrap / Confidence Interval
      │
      ▼
Multiple-Testing Correction
      │
      ▼
Robustness Tests
      │
      ▼
FINAL ACCEPTANCE
```

---

# AE.70. Final acceptance criteria

Saya menyarankan kita **tidak** mendefinisikan:

> "Sharpe > 1 berarti strategi diterima."

Terlalu sederhana.

Sebaliknya, strategy candidate harus melewati beberapa layer.

### Statistical

$$
Calibration\ acceptable
$$

$$
Brier\ acceptable
$$

$$
LogLoss\ acceptable
$$

### Economic

$$
EV>0
$$

$$
Net\ PnL>0
$$

$$
MDD\ acceptable
$$

### Robustness

$$
Cost\ stress\ test
$$

$$
Parameter\ stability
$$

$$
Regime\ stability
$$

### Statistical significance

$$
PSR
$$

$$
DSR
$$

dan confidence interval yang masuk akal.

---

# AE.71. Decision gate

Kita akhirnya dapat membuat:

$$
\boxed{
TradeAllowed_t
=
I(
C_t>C_{min}
)
I(
EV_t>0
)
I(
Risk_t<R_{max}
)
I(
Liquidity_t>L_{min}
)
}
$$

Tetapi bahkan ini belum cukup.

Untuk live deployment kita dapat menambahkan:

$$
I(
ModelHealth_t=1
).
$$

Sehingga:

$$
\boxed{
TradeAllowed_t
=
I(
Calibration
\land
EV
\land
Risk
\land
Liquidity
\land
ModelHealth
).
}
$$

---

# AE.72. Model health

Model dapat mengalami degradation.

Misalnya:

Training:

$$
Brier=0.12.
$$

Live:

$$
Brier=0.25.
$$

Maka:

$$
\boxed{
ModelHealth\downarrow.
}
$$

Kita tidak boleh terus meningkatkan position size hanya karena historical backtest bagus.

---

# AE.73. Population Stability

Kita juga harus memeriksa apakah distribusi feature berubah.

Misalnya:

$$
X_{train}
$$

memiliki distribusi:

$$
P_{train}(X).
$$

Sedangkan live:

$$
P_{live}(X).
$$

Jika:

$$
P_{live}(X)\neq P_{train}(X),
$$

maka terjadi:

$$
\boxed{
Distribution\ Shift.
}
$$

---

# AE.74. Concept drift

Lebih buruk lagi:

$$
P(Y\mid X)
$$

sendiri dapat berubah.

Misalnya dulu:

$$
OBI>0.3
$$

berarti bullish.

Tetapi setelah market structure berubah:

$$
OBI>0.3
$$

tidak lagi memiliki predictive power yang sama.

Ini:

$$
\boxed{
Concept\ Drift.
}
$$

---

# AE.75. Maka sistem kita harus memiliki feedback loop

```text
               MODEL
                 │
                 ▼
              TRADES
                 │
                 ▼
              OUTCOMES
                 │
                 ▼
           CALIBRATION
                 │
                 ▼
          MODEL HEALTH
                 │
          ┌──────┴──────┐
          │             │
        Healthy      Degraded
          │             │
          ▼             ▼
       Continue      Retrain
```

Ini membuat sistem **adaptif tetapi tetap terkontrol**.

---

# AE.76. Dan ini mengubah definisi backtest

Backtest kita bukan:

> "Jalankan strategy pada data lalu lihat profit."

Tetapi:

$$
\boxed{
Backtest
=
Simulation
+
Statistical\ Validation
+
Execution\ Modeling
+
Uncertainty\ Quantification.
}
$$

---

# AE.77. Hierarki bukti

Saya ingin kita menggunakan hierarki berikut:

$$
\boxed{
Backtest
<
WalkForward
<
OutOfSample
<
PaperTrading
<
LiveSmallCapital
<
ScaledLive.
}
$$

Semakin ke kanan, semakin kuat bukti bahwa sistem benar-benar bekerja di dunia nyata.

Tidak ada backtest yang bisa membuktikan strategy akan selalu profitable.

---

# AE.78. Hubungan dengan quantum optimization kita

Ini juga penting untuk tujuan besar kita.

Quantum optimizer:

$$
QAOA/VQE
$$

tidak boleh diberi tugas:

> "cari parameter yang membuat backtest paling profitable."

Itu akan sangat mudah menghasilkan overfitting.

Sebaliknya:

$$
\boxed{
Statistical\ validation
}
$$

harus berada **di luar optimizer**.

Quantum/classical optimizer hanya menyelesaikan:

$$
\boxed{
\max_x
J(x\mid\text{validated estimates}).
}
$$

Validasi menentukan apakah:

$$
J
$$

layak dipercaya.

---

# AE.79. Arsitektur final sampai Tahap AE

Kita sekarang memiliki:

```text
                 MARKET
                   │
                   ▼
            DATA / FACTORS
                   │
                   ▼
          FORECAST ENGINE
                   │
          μ̂, σ̂, Σ̂, Regime
                   │
                   ▼
       MICROSTRUCTURE ENGINE
                   │
        Fill / Spread / Impact
                   │
                   ▼
         OPPORTUNITY ENGINE
                   │
          Entry / SL / TP
                   │
                   ▼
       FIRST-PASSAGE ENGINE
                   │
       P(TP), P(SL), P(Time)
                   │
                   ▼
        CALIBRATION ENGINE
                   │
           calibrated p
                   │
                   ▼
             EV ENGINE
                   │
                   ▼
        PORTFOLIO OPTIMIZER
          / Classical / QUBO
                   │
                   ▼
         EXECUTION ENGINE
                   │
                   ▼
             POSITION
                   │
                   ▼
       DYNAMIC MANAGEMENT
                   │
                   ▼
             OUTCOMES
                   │
                   ▼
       STATISTICAL VALIDATION
                   │
        ┌──────────┴──────────┐
        │                     │
     Healthy               Degraded
        │                     │
        ▼                     ▼
     Continue              Retrain
```

---

# AE.80. Persamaan "kontrak" antar-engine

Ini menurut saya merupakan salah satu hasil paling penting dari Tahap AE.

Forecast engine memberikan:

$$
\boxed{
(\hat\mu,\hat\sigma,\hat\Sigma)
}
$$

Opportunity engine mengubahnya menjadi:

$$
\boxed{
\hat{\mathbf p}
=
(
\hat p_{TP},
\hat p_{SL},
\hat p_{TS}
)
}
$$

Calibration engine menghasilkan:

$$
\boxed{
\tilde{\mathbf p}
=
Calibration(\hat{\mathbf p})
}
$$

EV engine:

$$
\boxed{
EV(\theta)
=
\tilde p_{TP}G
-
\tilde p_{SL}L
-
C
}
$$

Optimizer:

$$
\boxed{
\theta^\star
=
\arg\max_\theta
EV(\theta)
}
$$

dan validator kemudian menguji apakah:

$$
\boxed{
EV(\theta^\star)
}
$$

benar-benar terealisasi secara out-of-sample.

---

# AE.81. Prinsip yang harus kita pegang

Ada satu prinsip yang menurut saya harus menjadi **aturan fundamental proyek ini**:

$$
\boxed{
\textbf{Jangan mengoptimalkan sesuatu yang belum tervalidasi.}
}
$$

Dan bahkan lebih spesifik:

$$
\boxed{
\text{Prediction}
\rightarrow
\text{Calibration}
\rightarrow
\text{Validation}
\rightarrow
\text{Optimization}
\rightarrow
\text{Execution}.
}
$$

Bukan:

$$
\text{Data}
\rightarrow
\text{Optimization}
\rightarrow
\text{Backtest bagus}
\rightarrow
\text{Cari pembenaran}.
$$

Perbedaan tersebut sangat besar.

---

# AE.82. Posisi kita sekarang

Sampai Tahap AD kita sudah menjawab:

> **"Bagaimana menentukan trade terbaik?"**

Tahap AE menjawab:

> **"Bagaimana memastikan bahwa probabilitas dan edge yang digunakan untuk menentukan trade tersebut memang memiliki dasar statistik yang dapat dipercaya?"**

Dengan demikian kita sudah memiliki dua komponen:

$$
\boxed{
Decision\ Engine
}
$$

dan:

$$
\boxed{
Evidence\ Engine.
}
$$

Dan **Evidence Engine inilah yang mencegah seluruh sistem berubah menjadi overfit backtest yang sangat kompleks.**

---

## AE.83. Tahap berikutnya: AF

Setelah ini kita sudah bisa masuk ke bagian yang jauh lebih menarik: **AF — Portfolio-Level Trade Selection & Cross-Asset Risk Optimization**.

Di sana masalahnya berubah dari:

$$
\text{"Apakah trade A bagus?"}
$$

menjadi:

$$
\boxed{
\text{"Dari 500 trade opportunity yang muncul bersamaan,
kombinasi mana yang sebaiknya kita ambil?"}
}
$$

Karena misalnya pada pukul 10:00 sistem menemukan:

$$
20\text{ crypto trades}
+
100\text{ US stocks}
+
30\text{ ETFs}.
$$

Masing-masing mungkin memiliki:

$$
EV>0.
$$

Tetapi **kita tidak boleh mengambil semuanya**, karena exposure-nya bisa sangat berkorelasi.

Di sinilah:

$$
\Sigma,
$$

factor exposure,

$$
VaR/CVaR,
$$

drawdown constraint,

dan akhirnya **QUBO/Ising/QAOA** yang sejak awal menjadi tujuan kita mulai benar-benar bertemu dengan **short-term quantitative trading** secara natural.

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

## Prompt:
8/17/2026, 10:22:31 PM

lanjut Tahap AG

## Response:
8/17/2026, 10:22:32 PM

# Tahap AG — Mixed-Integer Portfolio Optimization: dari “Trade mana?” menjadi “Trade mana + seberapa besar?”

Tahap AG adalah kelanjutan langsung dari AF. Di AF kita sudah mempunyai variabel biner

$$
x_i\in\{0,1\},
$$

yang menjawab:

> **Apakah opportunity $i$ dipilih?**

Sekarang kita tambahkan variabel kontinu

$$
w_i\in\mathbb R,
$$

yang menjawab:

> **Jika dipilih, seberapa besar modal/risk yang dialokasikan?**

Maka sistem kita berubah dari **binary portfolio selection** menjadi:

$$
\boxed{
\text{Mixed-Integer Portfolio Optimization}
}
$$

dengan struktur fundamental:

$$
\boxed{
x_i\in\{0,1\},
\qquad
w_i\in\mathbb R.
}
$$

---

# AG.1. Dua variabel yang memiliki tugas berbeda

Untuk setiap opportunity $i$:

$$
x_i=
\begin{cases}
1,&\text{trade dipilih}\\
0,&\text{trade tidak dipilih}
\end{cases}
$$

sedangkan:

$$
w_i
$$

menyatakan exposure atau position weight.

Keduanya harus dihubungkan.

Jika:

$$
x_i=0,
$$

maka kita ingin:

$$
w_i=0.
$$

Jika:

$$
x_i=1,
$$

maka:

$$
w_i
$$

boleh mengambil nilai tertentu.

Secara matematis:

$$
\boxed{
|w_i|\le M_i x_i
}
$$

dengan $M_i$ sebagai maximum position size.

---

# AG.2. Mengapa constraint ini sangat penting?

Tanpa constraint:

$$
|w_i|\le M_i x_i,
$$

optimizer bisa menghasilkan:

$$
x_i=0,
\qquad
w_i\neq0.
$$

Artinya portfolio mengatakan:

> "Saya tidak memilih trade ini, tetapi tetap memiliki posisi di dalamnya."

Tidak masuk akal.

Constraint tersebut membuat:

$$
x_i=0
\Rightarrow
w_i=0.
$$

Sedangkan:

$$
x_i=1
\Rightarrow
|w_i|\le M_i.
$$

---

# AG.3. Portfolio return

Sekarang expected portfolio return menjadi:

$$
\boxed{
E[R_p]
=
\sum_iw_i\mu_i
}
$$

atau:

$$
\boxed{
E[R_p]
=
\mathbf w^\top\boldsymbol\mu.
}
$$

Berbeda dari AF.

Di AF:

$$
\mathbf x^\top\mu
$$

menganggap setiap trade mempunyai kontribusi binary.

Sekarang:

$$
w_i\mu_i
$$

memperhitungkan **berapa besar exposure** yang kita berikan.

---

# AG.4. Portfolio variance

Sekarang:

$$
\boxed{
\sigma_p^2
=
\mathbf w^\top\Sigma\mathbf w.
}
$$

Sehingga objective Markowitz:

$$
\boxed{
\max_{\mathbf w}
\left[
\mathbf w^\top\mu
-
\lambda
\mathbf w^\top\Sigma\mathbf w
\right].
}
$$

Tetapi sekarang kita juga mempunyai $x$.

Maka:

$$
\boxed{
\max_{\mathbf x,\mathbf w}
\left[
\mathbf w^\top\mu
-
\lambda\mathbf w^\top\Sigma\mathbf w
\right].
}
$$

subject to:

$$
|w_i|\le M_ix_i.
$$

---

# AG.5. Ini adalah inti mathematical architecture kita

Kita sekarang mempunyai:

$$
\boxed{
\begin{array}{ll}
x_i & \text{selection}\\
w_i & \text{sizing}
\end{array}
}
$$

sehingga:

$$
\boxed{
\text{Selection}
+
\text{Sizing}
+
\text{Risk}
}
$$

dapat dioptimalkan secara simultan.

---

# AG.6. Tetapi ada masalah besar

Bayangkan:

$$
N=1000.
$$

Kita memiliki:

$$
1000
$$

variabel binary dan:

$$
1000
$$

variabel continuous.

Maka problem menjadi jauh lebih sulit daripada QUBO biasa.

Secara umum:

$$
\boxed{
MIQP
=
Mixed\ Integer\ Quadratic\ Programming.
}
$$

---

# AG.7. Apakah kita harus langsung memasukkan semuanya ke QAOA?

Menurut saya:

$$
\boxed{\textbf{tidak.}}
$$

Ini keputusan desain yang penting.

Kita jangan memaksakan:

$$
\text{semua matematika}
\rightarrow
\text{quantum}.
$$

Justru kita gunakan paradigma hybrid:

$$
\boxed{
Quantum
+
Classical
}
$$

sesuai struktur masalah.

---

# AG.8. Hierarchical decomposition

Kita dapat memecahkan:

$$
(x,w)
$$

menjadi dua tahap:

### Tahap 1

Cari:

$$
x^\star.
$$

### Tahap 2

Diberikan $x^\star$, cari:

$$
w^\star.
$$

Secara matematis:

$$
\boxed{
x^\star
=
\arg\min_x H(x)
}
$$

kemudian:

$$
\boxed{
w^\star
=
\arg\min_w
f(w\mid x^\star).
}
$$

---

# AG.9. Mengapa pendekatan ini sangat masuk akal?

Karena discrete problem menjawab:

> "Apa yang kita percaya layak diperdagangkan?"

Sedangkan continuous problem menjawab:

> "Bagaimana kita mengalokasikan risk?"

Dua pertanyaan tersebut memang berbeda secara konseptual.

---

# AG.10. Position sizing berbasis stop-loss

Sekarang kita hubungkan dengan sistem $ \$1 $ risk yang kita desain sebelumnya.

Misalkan entry:

$$
P_i^{entry}
$$

dan stop-loss:

$$
P_i^{SL}.
$$

Distance:

$$
d_i=
|P_i^{entry}-P_i^{SL}|.
$$

Untuk satu unit posisi, maximum loss:

$$
L_i=d_iV_i,
$$

dengan $V_i$ adalah nilai moneter per unit perubahan harga.

Jika risk budget:

$$
R_i^{max}=\$1,
$$

maka:

$$
\boxed{
q_i^{max}
=
\frac{1}{d_iV_i}.
}
$$

---

# AG.11. Jika portfolio menggunakan risk unit

Lebih fleksibel jika kita mendefinisikan:

$$
r_i
$$

sebagai risk budget trade dalam satuan $R$.

Misalnya:

$$
r_i=1R.
$$

Kemudian:

$$
q_i
=
\frac{r_iR_{portfolio}}
{d_iV_i}.
$$

Jadi:

$$
\boxed{
Position\ Size
=
\frac{Risk\ Budget}
{Stop\ Distance\times Value\ per\ Unit}.
}
$$

Ini adalah fondasi risk-based position sizing.

---

# AG.12. Sekarang $w_i$ dapat kita definisikan dalam risk-space

Daripada:

$$
w_i=\frac{\text{notional}_i}{Capital},
$$

kita bisa mendefinisikan:

$$
\boxed{
w_i
=
\text{fraction of portfolio risk}.
}
$$

Misalnya:

$$
w_{BTC}=0.15
$$

berarti BTC menerima:

$$
15\%
$$

dari risk budget tertentu.

Ini jauh lebih konsisten dengan sistem trading kita daripada sekadar equal capital weighting.

---

# AG.13. Risk contribution

Untuk portfolio:

$$
\sigma_p
=
\sqrt{\mathbf w^\top\Sigma\mathbf w},
$$

marginal contribution to risk dari asset $i$:

$$
\boxed{
MCR_i
=
\frac{\partial\sigma_p}{\partial w_i}.
}
$$

Karena:

$$
\sigma_p
=
\sqrt{w^\top\Sigma w},
$$

maka:

$$
\frac{\partial\sigma_p}{\partial w_i}
=
\frac{(\Sigma w)_i}{\sigma_p}.
$$

Sehingga:

$$
\boxed{
MCR_i
=
\frac{(\Sigma w)_i}
{\sigma_p}.
}
$$

---

# AG.14. Total risk contribution

Risk contribution:

$$
RC_i
=
w_iMCR_i.
$$

Maka:

$$
\boxed{
RC_i
=
\frac{w_i(\Sigma w)_i}
{\sigma_p}.
}
$$

Dan:

$$
\sum_iRC_i=\sigma_p.
$$

Ini sangat berguna untuk mengetahui:

> Trade mana yang sebenarnya menyumbang risiko terbesar?

Karena position terbesar belum tentu mempunyai risk contribution terbesar.

---

# AG.15. Contoh

Misalkan:

$$
w_A=0.2
$$

dan:

$$
w_B=0.1.
$$

Tetapi A dan B sangat berkorelasi.

Mungkin:

$$
RC_A=0.15
$$

dan:

$$
RC_B=0.12.
$$

Jadi B yang hanya setengah posisi A ternyata menyumbang risiko hampir sama.

Inilah alasan:

$$
\boxed{
Position\ Weight
\neq
Risk\ Weight.
}
$$

---

# AG.16. Risk parity sebagai alternatif

Kita dapat meminta:

$$
RC_i\approx RC_j.
$$

Untuk seluruh trade:

$$
\boxed{
RC_i
\approx
\frac{\sigma_p}{N}.
}
$$

Ini disebut **risk parity**.

Tetapi untuk sistem kita, saya tidak menyarankan risk parity sebagai objective utama.

Lebih baik menjadikannya:

$$
\boxed{
optional\ regularizer.
}
$$

Karena kita tetap ingin mempertahankan expected edge.

---

# AG.17. Objective sizing yang lebih lengkap

Setelah $x^\star$ ditentukan:

$$
\boxed{
\max_w
\left[
w^\top\mu
-
\lambda w^\top\Sigma w
\right]
}
$$

subject to:

$$
|w_i|\le M_ix_i^\star,
$$

$$
\sum_i|w_i|\le L_{\max},
$$

dan:

$$
CVaR(w)\le C_{\max}.
$$

---

# AG.18. Leverage constraint

Jika portfolio mempunyai leverage maksimum:

$$
L_{\max},
$$

maka:

$$
\boxed{
\sum_i|w_i|
\le L_{\max}.
}
$$

Misalnya:

$$
L_{\max}=2.
$$

Maka total gross exposure tidak boleh melebihi:

$$
2\times
\text{capital}.
$$

---

# AG.19. Long-short portfolio

Untuk sistem yang mendukung short:

$$
w_i\in[-M_i,M_i].
$$

Kita dapat memecah:

$$
w_i=w_i^+-w_i^-,
$$

dengan:

$$
w_i^+\ge0,
$$

$$
w_i^-\ge0.
$$

Dan:

$$
|w_i|
=
w_i^++w_i^-.
$$

---

# AG.20. Constraint selection-sizing

Kita dapat menggunakan:

$$
w_i^++w_i^-
\le M_ix_i.
$$

Sehingga jika:

$$
x_i=0:
$$

$$
w_i^+=w_i^-=0.
$$

Jika:

$$
x_i=1:
$$

posisi dapat long atau short.

---

# AG.21. Factor neutrality

Misalkan:

$$
B
$$

adalah factor loading matrix.

Portfolio exposure:

$$
\boxed{
f=B^\top w.
}
$$

Jika kita ingin market-neutral:

$$
\boxed{
B_{market}^\top w=0.
}
$$

Jika kita ingin USD-neutral:

$$
\boxed{
B_{USD}^\top w=0.
}
$$

Atau hanya membatasi:

$$
|B_{USD}^\top w|
\le
\epsilon_{USD}.
$$

---

# AG.22. Ini sangat relevan dengan desain kita

Misalnya model menemukan:

$$
10
$$

saham yang semuanya bullish.

Tetapi ternyata semuanya mempunyai:

$$
\beta_{USD}<0.
$$

Artinya portfolio sebenarnya memiliki satu hidden macro bet:

$$
\boxed{
Short\ USD.
}
$$

Kita bisa mengontrolnya secara eksplisit.

---

# AG.23. Gold factor

Hal yang sama berlaku untuk gold.

Jika:

$$
B_{Gold}^\top w
$$

terlalu besar, berarti portfolio mempunyai exposure besar terhadap factor gold.

Kita bisa:

$$
B_{Gold}^\top w
\le
B_{Gold}^{max}.
$$

Atau bahkan:

$$
B_{Gold}^\top w
\approx0.
$$

---

# AG.24. Faktor bukan hanya untuk risk

Ini penting.

Factor exposure juga bisa menjadi **signal**.

Misalnya:

$$
F_{USD}\uparrow
$$

dan model kita memperkirakan aset tertentu akan underperform.

Maka:

$$
\mu_i
$$

dapat dibuat conditional:

$$
\boxed{
\mu_i
=
E[R_i\mid F_t].
}
$$

Dengan demikian factor model masuk ke:

$$
\boxed{
Prediction
}
$$

dan:

$$
\boxed{
Risk.
}
$$

---

# AG.25. Conditional covariance

Lebih lanjut:

$$
\Sigma_t
$$

juga tidak harus konstan.

Kita dapat memiliki:

$$
\boxed{
\Sigma_t
=
B_t\Sigma_{F,t}B_t^\top
+
D_t.
}
$$

Jadi ketika volatility regime berubah:

$$
\Sigma_{F,t}
$$

ikut berubah.

---

# AG.26. Regime-dependent optimization

Misalkan terdapat regime:

$$
z_t\in
\{
Bull,
Bear,
HighVol,
LowVol,
RiskOn,
RiskOff
\}.
$$

Maka:

$$
\mu_t=\mu(z_t)
$$

dan:

$$
\Sigma_t=\Sigma(z_t).
$$

Optimizer menjadi:

$$
\boxed{
w_t^\star
=
w^\star(z_t).
}
$$

---

# AG.27. Ini membuat sistem adaptif

Contohnya:

### Risk-on

$$
F_{crypto}>0
$$

$$
F_{equity}>0
$$

volatility rendah.

Optimizer mungkin memperbolehkan:

$$
higher\ gross\ exposure.
$$

### Risk-off

Volatility meningkat.

Optimizer mengurangi:

$$
\|w\|_1.
$$

---

# AG.28. Dynamic risk budget

Bahkan:

$$
R_{max}
$$

dapat dibuat fungsi regime:

$$
\boxed{
R_{max,t}
=
R_0g(z_t).
}
$$

Misalnya:

$$
g(z_t)<1
$$

ketika:

$$
volatility
$$

sangat tinggi.

Ini berarti sistem otomatis melakukan **risk compression**.

---

# AG.29. Sekarang kita kembali ke \$1 risk

Ada dua level:

### Trade level

$$
Risk_i\le \$1.
$$

### Portfolio level

$$
Risk_p\le R_{portfolio}^{max}.
$$

Keduanya harus dipertahankan.

Misalnya:

$$
R_i=\$1
$$

untuk setiap trade.

Jika:

$$
R_{portfolio}^{max}=\$5,
$$

maka sistem tidak boleh membuka 20 trade independen sekaligus jika aggregate risk melebihi budget.

---

# AG.30. Correlation-adjusted risk

Worst-case:

$$
R_p^{worst}
=
\sum_iR_i.
$$

Tetapi expected aggregate risk lebih kecil jika trade independen.

Secara sederhana:

$$
Var(L)
=
\sum_i\sigma_i^2
+
2\sum_{i<j}\rho_{ij}\sigma_i\sigma_j.
$$

Inilah alasan correlation matters.

---

# AG.31. Bahkan risk \$1 dapat dibuat adaptive

Tidak harus selalu:

$$
\$1.
$$

Kita dapat mendefinisikan:

$$
R_i(t)
=
R_0
g(
EV_i,
Vol_t,
Liquidity_t,
Drawdown_t
).
$$

Misalnya:

$$
R_i(t)
=
\$1
$$

dalam kondisi normal.

Tetapi ketika drawdown meningkat:

$$
R_i(t)<\$1.
$$

---

# AG.32. Drawdown-aware risk scaling

Misalkan equity:

$$
E_t.
$$

High-water mark:

$$
H_t=\max_{\tau\le t}E_\tau.
$$

Drawdown:

$$
\boxed{
DD_t
=
1-\frac{E_t}{H_t}.
}
$$

Kemudian:

$$
R_t
=
R_0f(DD_t).
$$

Contoh:

$$
f(DD)=
\max
\left(
f_{min},
1-kDD
\right).
$$

Jadi semakin besar drawdown:

$$
\boxed{
risk\ budget\downarrow.
}
$$

---

# AG.33. Ini merupakan feedback control

Kita sekarang memiliki:

$$
Market
\rightarrow
Signal
\rightarrow
Portfolio
\rightarrow
PnL
\rightarrow
Drawdown
\rightarrow
Risk\ Budget
\rightarrow
Portfolio.
$$

Dengan demikian sistem menjadi:

$$
\boxed{
closed\ loop.
}
$$

---

# AG.34. Transaction cost

Sizing tidak boleh mengabaikan biaya.

Misalkan:

$$
c_i
$$

adalah expected transaction cost per unit exposure.

Maka:

$$
Cost(w)
=
\sum_i c_i|w_i|.
$$

Objective:

$$
\boxed{
\max
\left[
w^\top\mu
-
\lambda w^\top\Sigma w
-
c^\top|w|
\right].
}
$$

---

# AG.35. Market impact

Untuk trade yang lebih besar, cost tidak lagi linear.

Model sederhana:

$$
Impact_i(q_i)
=
\eta_iq_i^2.
$$

Maka:

$$
Cost_i(q_i)
=
c_i|q_i|
+
\eta_iq_i^2.
$$

Ini membuat optimizer memperhitungkan liquidity.

---

# AG.36. Mengapa ini penting untuk short-term trading?

Karena pada horizon pendek:

$$
Expected\ Edge
$$

bisa sangat kecil.

Misalnya:

$$
EV=0.15R.
$$

Tetapi:

$$
Transaction\ Cost=0.08R.
$$

Maka net edge:

$$
0.07R.
$$

Jika slippage:

$$
0.10R,
$$

trade tersebut sebenarnya:

$$
EV_{net}<0.
$$

---

# AG.37. Maka expected value kita harus diperbaiki

Jangan menggunakan:

$$
EV_i^{gross}.
$$

Gunakan:

$$
\boxed{
EV_i^{net}
=
EV_i^{gross}
-
Cost_i
-
Slippage_i
-
Funding_i.
}
$$

Untuk crypto:

$$
Funding_i
$$

bisa penting.

Untuk saham:

$$
BorrowCost_i
$$

dapat relevan jika short.

---

# AG.38. Objective final sizing

Kita sekarang dapat menulis:

$$
\boxed{
\begin{aligned}
\max_{\mathbf w}
\quad
&
\mathbf w^\top\mu
-
\lambda
\mathbf w^\top\Sigma\mathbf w
\\
&
-
\mathbf c^\top|\mathbf w|
-
\mathbf w^\top M\mathbf w
\end{aligned}
}
$$

subject to:

$$
|w_i|\le M_ix_i^\star,
$$

$$
\sum_i|w_i|\le L_{\max},
$$

$$
B^\top w\in\mathcal F,
$$

$$
CVaR(w)\le C_{\max}.
$$

---

# AG.39. Interpretasi setiap term

$$
\mathbf w^\top\mu
$$

= expected profit.

$$
\lambda w^\top\Sigma w
$$

= portfolio risk.

$$
c^\top|w|
$$

= transaction cost.

$$
w^\top Mw
$$

= market impact.

Constraint:

$$
|w_i|\le M_ix_i
$$

= selection control.

Constraint:

$$
B^\top w\in\mathcal F
$$

= factor exposure control.

---

# AG.40. Sekarang kita mempunyai dua optimizer

### Optimizer A

$$
\boxed{
Discrete\ Optimizer
}
$$

memilih:

$$
x^\star.
$$

### Optimizer B

$$
\boxed{
Continuous\ Optimizer
}
$$

memilih:

$$
w^\star.
$$

---

# AG.41. Tetapi kita bisa melakukan sesuatu yang lebih menarik

Setelah mendapatkan:

$$
x^\star,
$$

kita dapat melakukan **iterative refinement**.

Pertama:

$$
x^{(0)}
\rightarrow
w^{(0)}.
$$

Kemudian hitung:

$$
Risk(w^{(0)}).
$$

Jika terlalu tinggi, kita kembali ke selection:

$$
x^{(1)}.
$$

Lalu:

$$
x^{(1)}
\rightarrow
w^{(1)}.
$$

Dan seterusnya.

---

# AG.42. Jadi bukan hanya pipeline

Bukan:

```text id="8w5y1p"
QUBO → Sizing → selesai
```

tetapi:

```text id="q5s2k0"
             ┌───────────────┐
             │ Opportunity   │
             └───────┬───────┘
                     ▼
               QUBO Selection
                     │
                     ▼
                Position Size
                     │
                     ▼
                 Risk Check
                     │
              ┌──────┴──────┐
              │             │
           PASS            FAIL
              │             │
              ▼             ▼
          Execute       Re-optimize
```

---

# AG.43. Ini merupakan decomposition algorithm

Secara konseptual:

$$
\boxed{
Discrete
\rightarrow
Continuous
\rightarrow
Risk
\rightarrow
Discrete
\rightarrow\cdots
}
$$

Kita bisa menggunakan pendekatan seperti:

- alternating optimization,
- Benders-style decomposition,
- coordinate refinement,
- heuristic local search.

Tidak semuanya harus quantum.

---

# AG.44. Peran QAOA menjadi semakin jelas

QAOA tidak perlu mengoptimalkan:

$$
w_i
$$

secara langsung.

Ia dapat mengoptimalkan:

$$
\boxed{
x_i.
}
$$

Kemudian classical optimizer menangani:

$$
\boxed{
w_i.
}
$$

Ini membuat penggunaan QAOA jauh lebih realistis.

---

# AG.45. Pipeline matematis Tahap AG

Sekarang sistem kita dapat dirumuskan:

$$
\boxed{
\text{Market Data}
}
$$

$$
\downarrow
$$

$$
\boxed{
\text{Feature/Factor Model}
}
$$

$$
\downarrow
$$

$$
\boxed{
\mu_i,\Sigma,B,C
}
$$

$$
\downarrow
$$

$$
\boxed{
QUBO(x)
}
$$

$$
\downarrow
$$

$$
\boxed{
x^\star
}
$$

$$
\downarrow
$$

$$
\boxed{
MIQP/Continuous\ Sizing
}
$$

$$
\downarrow
$$

$$
\boxed{
w^\star
}
$$

$$
\downarrow
$$

$$
\boxed{
Risk\ Engine
}
$$

$$
\downarrow
$$

$$
\boxed{
Execution.
}
$$

---

# AG.46. Contoh numerik kecil

Misalkan ada tiga trade:

$$
A,B,C.
$$

Expected return:

$$
\mu=
\begin{bmatrix}
0.12\\
0.10\\
0.08
\end{bmatrix}.
$$

Covariance:

$$
\Sigma=
\begin{bmatrix}
0.04&0.03&0.00\\
0.03&0.05&0.01\\
0.00&0.01&0.02
\end{bmatrix}.
$$

Misalkan optimizer memilih:

$$
x^\star=
\begin{bmatrix}
1\\
1\\
1
\end{bmatrix}.
$$

Kemudian sizing mencari:

$$
w^\star.
$$

Dengan constraint:

$$
w_A+w_B+w_C=1.
$$

dan:

$$
w_i\ge0.
$$

---

# AG.47. Unconstrained Markowitz

Tanpa constraint lain, problem:

$$
\max_w
\left[
w^\top\mu
-
\lambda w^\top\Sigma w
\right].
$$

First-order condition:

$$
\nabla
\left(
w^\top\mu
-
\lambda w^\top\Sigma w
\right)
=0.
$$

Karena:

$$
\nabla(w^\top\mu)=\mu
$$

dan:

$$
\nabla(w^\top\Sigma w)
=
2\Sigma w,
$$

maka:

$$
\mu-2\lambda\Sigma w=0.
$$

Sehingga:

$$
\boxed{
w^\star
=
\frac{1}{2\lambda}
\Sigma^{-1}\mu.
}
$$

Ini adalah solusi dasar Markowitz.

---

# AG.48. Tetapi constraint budget mengubahnya

Jika:

$$
\mathbf1^\top w=1,
$$

kita gunakan Lagrange multiplier:

$$
\mathcal L
=
w^\top\mu
-
\lambda w^\top\Sigma w
+
\nu(1-\mathbf1^\top w).
$$

FOC:

$$
\mu
-
2\lambda\Sigma w
-
\nu\mathbf1
=
0.
$$

Sehingga:

$$
\boxed{
w
=
\frac{1}{2\lambda}
\Sigma^{-1}
(\mu-\nu\mathbf1).
}
$$

$\nu$ kemudian ditentukan dari:

$$
\mathbf1^\top w=1.
$$

---

# AG.49. Kenapa derivasi ini penting?

Karena kita sekarang memiliki pembagian kerja:

### Quantum/discrete

Menentukan:

$$
x.
$$

### Classical analytical/numerical

Menentukan:

$$
w.
$$

Dengan demikian kita dapat menggunakan matematika yang sudah kamu pelajari dalam Markowitz secara langsung.

---

# AG.50. Tetapi untuk trading jangka pendek, Markowitz saja belum cukup

Karena:

$$
\mu_i
$$

sangat noisy.

Maka kita tidak boleh memperlakukan:

$$
\hat\mu_i
$$

seolah-olah exact.

Kita harus memperhitungkan uncertainty:

$$
\boxed{
\mu_i
=
\hat\mu_i+\epsilon_i.
}
$$

---

# AG.51. Robust optimization

Salah satu pendekatan:

$$
\mu_i\in\mathcal U_i.
$$

Kita tidak mengoptimalkan:

$$
\hat\mu_i
$$

saja, tetapi worst-case expected return:

$$
\boxed{
\max_w
\min_{\mu\in\mathcal U}
w^\top\mu
-
\lambda w^\top\Sigma w.
}
$$

Ini jauh lebih masuk akal untuk short-horizon prediction.

---

# AG.52. Confidence-adjusted expected return

Alternatif sederhana:

$$
\boxed{
\mu_i^{adj}
=
\hat\mu_i
-
\kappa s_i
}
$$

dengan:

$$
s_i
$$

sebagai uncertainty estimate.

Jadi:

$$
\text{high prediction uncertainty}
\Rightarrow
\mu_i^{adj}\downarrow.
$$

---

# AG.53. Ini sangat penting bagi sistem kita

Sebuah trade bisa memiliki:

$$
\hat\mu_i=0.20R
$$

tetapi uncertainty:

$$
s_i=0.30R.
$$

Trade tersebut sebenarnya kurang menarik dibanding trade:

$$
\hat\mu_j=0.15R,
\qquad
s_j=0.05R.
$$

Maka:

$$
\mu_i^{adj}
<
\mu_j^{adj}.
$$

---

# AG.54. Confidence masuk ke QUBO

Kita sekarang dapat mengganti:

$$
EV_i
$$

dengan:

$$
\boxed{
EV_i^{robust}.
}
$$

Sehingga QUBO memilih bukan:

> trade dengan predicted return terbesar,

tetapi:

> **trade dengan risk-adjusted, uncertainty-adjusted edge terbesar.**

---

# AG.55. Ini menghasilkan objective yang lebih matang

Discrete stage:

$$
\boxed{
\begin{aligned}
\min_x
\quad
&
-\sum_iEV_i^{robust}x_i
\\
&
+
\lambda x^\top\Sigma x
\\
&
+
\lambda_F R_F(x)
\\
&
+
\lambda_T T(x,x_{t-1})
\\
&
+
P_K(\mathbf1^\top x-K)^2.
\end{aligned}
}
$$

Continuous stage:

$$
\boxed{
\begin{aligned}
\max_w\quad
&
w^\top\mu^{robust}
-
\lambda w^\top\Sigma w
\\
&
-Cost(w)-Impact(w)
\end{aligned}
}
$$

subject to risk and exposure constraints.

---

# AG.56. Satu lagi masalah: turnover

Misalkan:

$$
w_{t-1}
$$

adalah portfolio sebelumnya.

Maka perubahan:

$$
\Delta w_t
=
w_t-w_{t-1}.
$$

Transaction cost:

$$
Cost_t
=
c^\top|\Delta w_t|.
$$

Jadi objective sebenarnya harus menggunakan:

$$
\boxed{
w_t^\top\mu_t
-
\lambda w_t^\top\Sigma_tw_t
-
c^\top|w_t-w_{t-1}|.
}
$$

Ini membuat portfolio **sticky**.

---

# AG.57. Ini sangat cocok dengan sistem evaluasi periodik kita

Kamu sebelumnya menginginkan:

> setiap jam atau periode tertentu posisi dievaluasi.

Sekarang kita punya formulasi matematisnya.

Pada waktu $t$:

$$
w_{t-1}
$$

adalah portfolio saat ini.

Model menghitung:

$$
w_t^\star.
$$

Kemudian:

$$
\Delta w_t
=
w_t^\star-w_{t-1}.
$$

Jika:

$$
|\Delta w_t|
$$

kecil, kita tidak perlu banyak melakukan perubahan.

---

# AG.58. Bahkan kita bisa membuat minimum improvement threshold

Misalkan:

$$
U(w_t^\star)-U(w_{t-1})
<
\epsilon.
$$

Maka:

$$
\boxed{
\text{Do not rebalance.}
}
$$

Ini sangat penting agar optimizer tidak overtrade.

---

# AG.59. Decision rule

Secara sederhana:

$$
\boxed{
\Delta U
=
U(w_t^\star)-U(w_{t-1}).
}
$$

Jika:

$$
\Delta U>\epsilon,
$$

rebalancing.

Jika:

$$
\Delta U\le\epsilon,
$$

pertahankan portfolio.

---

# AG.60. Ini menghubungkan AG dengan sistem position management sebelumnya

Kita sebelumnya membicarakan:

- floating loss,
- floating profit,
- BEP,
- trailing SL,
- TP extension.

Sekarang kita dapat melihatnya sebagai:

$$
\boxed{
Position\ Management
=
Local\ Optimization
}
$$

sedangkan:

$$
\boxed{
Portfolio\ Selection
=
Global\ Optimization.
}
$$

---

# AG.61. Dua skala optimisasi

### Global

$$
\text{Which trades?}
$$

$$
\rightarrow QUBO.
$$

### Local

$$
\text{How should each position evolve?}
$$

$$
\rightarrow
SL/TP/Trailing.
$$

Jangan dicampur menjadi satu optimizer raksasa.

---

# AG.62. Arsitektur akhirnya mulai terlihat

```text id="k4d6e2"
                MARKET
                   │
                   ▼
             Feature Engine
                   │
                   ▼
          Prediction / Forecast
                   │
                   ▼
          Expected Net Edge
                   │
          ┌────────┴────────┐
          ▼                 ▼
      Risk Model       Microstructure
          │                 │
          └────────┬────────┘
                   ▼
            QUBO / QAOA
                   │
                   ▼
             Trade Selection
                   │
                   ▼
         Continuous Position Sizing
                   │
                   ▼
              Risk Engine
                   │
                   ▼
                Orders
                   │
                   ▼
          Position Management
          ┌────────┼────────┐
          ▼        ▼        ▼
          SL       TP      Trailing
                   │
                   ▼
              PnL Feedback
                   │
                   ▼
            Next Optimization
```

---

# AG.63. Poin terpenting Tahap AG

Kita sekarang mempunyai **tiga lapisan optimisasi**:

$$
\boxed{
\begin{array}{lll}
\text{Layer 1} &:& \text{Opportunity Prediction}\\
\text{Layer 2} &:& \text{Discrete Portfolio Selection}\\
\text{Layer 3} &:& \text{Continuous Position Sizing}
\end{array}
}
$$

dan kemudian:

$$
\boxed{
\text{Layer 4: Dynamic Position Management}.
}
$$

---

# AG.64. Hubungan dengan TSP, Max-Cut, dan problem combinatorial lainnya

Sekarang menjadi lebih jelas mengapa kamu sejak awal tertarik pada:

- TSP,
- Max-Cut,
- portfolio optimization.

Mereka tidak harus menjadi tiga algoritma yang berdiri sendiri.

Mereka merupakan **primitive optimization structures**.

Misalnya:

$$
\boxed{
Portfolio\ Selection
\rightarrow QUBO
}
$$

$$
\boxed{
Diversification/Clustering
\rightarrow Graph/MaxCut
}
$$

dan untuk masalah execution:

$$
\boxed{
Order\ Routing
\rightarrow TSP/VRP
}
$$

---

# AG.65. Bahkan execution bisa menjadi optimization problem

Misalnya kita memiliki:

$$
N
$$

venue/order types.

Kita ingin menentukan:

$$
\text{order sequence}
$$

dengan:

- latency,
- fee,
- liquidity,
- slippage.

Maka kita dapat memiliki:

$$
\boxed{
Execution\ Optimization.
}
$$

Ini adalah layer yang berbeda dari portfolio selection.

---

# AG.66. Maka sistem besar kita mulai menjadi

$$
\boxed{
Prediction
\rightarrow
Portfolio
\rightarrow
Execution
\rightarrow
Position\ Management.
}
$$

Dengan berbagai mathematical optimization primitive:

$$
\boxed{
ML
+
QUBO
+
Ising
+
QAOA
+
Markowitz
+
Graph\ Optimization
+
Control.
}
$$

---

# AG.67. Dan ada prinsip desain yang sangat penting

Jangan menggunakan quantum algorithm hanya karena:

> "masalahnya bisa dibuat QUBO."

Pertanyaan yang benar adalah:

$$
\boxed{
\text{Apakah quantum optimizer memberikan keuntungan dibanding classical baseline?}
}
$$

Karena sistem kita harus mempunyai benchmark:

$$
QAOA
$$

vs.

$$
Simulated\ Annealing
$$

vs.

$$
MILP/MIQP
$$

vs.

$$
Greedy
$$

vs.

$$
Classical\ Markowitz.
$$

---

# AG.68. Ini nantinya akan menjadi eksperimen yang sangat kuat

Untuk setiap periode:

$$
t,
$$

kita dapat menjalankan:

$$
x_t^{QAOA}
$$

dan:

$$
x_t^{classical}.
$$

Kemudian bandingkan:

$$
EV,
$$

$$
Sharpe,
$$

$$
MaxDD,
$$

$$
CVaR,
$$

$$
Turnover,
$$

$$
Transaction\ Cost.
$$

Dengan demikian kita tidak mengatakan:

> "QAOA lebih bagus karena quantum."

Tetapi:

> **"Pada problem dan constraint tertentu, QAOA menghasilkan solusi dengan kualitas X dan computational characteristic Y dibanding baseline Z."**

Ini jauh lebih ilmiah.

---

# AG.69. Rumusan matematis AG yang paling lengkap

Untuk sekarang, saya akan menjadikan formulasi berikut sebagai **master formulation**:

$$
\boxed{
\begin{aligned}
\max_{\mathbf x,\mathbf w}\quad
&
\mathbf w^\top\mu_t^{robust}
-
\lambda
\mathbf w^\top\Sigma_t\mathbf w
\\
&
-
C_t(\mathbf w-\mathbf w_{t-1})
-
I_t(\mathbf w)
\\
&
-
\lambda_F
\|B_t^\top\mathbf w\|^2
\\[2mm]
\text{s.t.}\quad
&
|w_i|\le M_ix_i,
\\
&
x_i\in\{0,1\},
\\
&
\sum_i x_i\le K,
\\
&
\sum_i|w_i|\le L_{\max},
\\
&
CVaR_q(\mathbf w)\le C_{\max},
\\
&
B_t^\top\mathbf w\in\mathcal F,
\\
&
R_{portfolio}(\mathbf w)\le R_{\max,t}.
\end{aligned}
}
$$

Inilah problem yang secara konseptual sekarang ingin kita selesaikan.

---

# AG.70. Tetapi jangan langsung coding formulasi sebesar ini

Ini penting.

Kita sebaiknya membangun secara bertahap:

### AG-1

Binary selection:

$$
x_i.
$$

### AG-2

Selection + covariance:

$$
x^\top\Sigma x.
$$

### AG-3

Selection + factor exposure.

### AG-4

Continuous sizing:

$$
w_i.
$$

### AG-5

Transaction cost.

### AG-6

CVaR.

### AG-7

Dynamic rebalancing.

### AG-8

QAOA benchmark.

Dengan demikian setiap komponen dapat diuji secara independen.

---

# AG.71. Dan inilah keputusan desain yang saya sarankan

Untuk **versi pertama sistem nyata**, jangan langsung mencoba:

$$
1000\ assets.
$$

Mulai dengan:

$$
\boxed{
N=10-30
}
$$

opportunities.

Misalnya:

### Crypto

BTC, ETH + 8–15 altcoins.

### US equities

10–20 liquid stocks/ETFs.

### Macro

Gold + USD proxy + equity index.

Kemudian baru:

$$
N\rightarrow50\rightarrow100\rightarrow500.
$$

---

# AG.72. Mengapa?

Karena tujuan pertama bukan:

$$
\text{maximize profit}.
$$

Tujuan pertama adalah:

$$
\boxed{
\text{validate the mathematical architecture}.
}
$$

Kita harus bisa membuktikan:

$$
Prediction
\rightarrow
QUBO
\rightarrow
Selection
\rightarrow
Sizing
\rightarrow
Risk
\rightarrow
Execution
$$

benar-benar bekerja tanpa leakage dan tanpa bug.

---

# AG.73. Dan ada satu konsekuensi besar dari AG

Mulai tahap ini, **backtesting kita tidak boleh lagi hanya mengevaluasi signal**.

Kita harus melakukan:

$$
\boxed{
event-driven\ portfolio\ backtest.
}
$$

Karena keputusan sekarang bergantung pada:

$$
x_t,
w_t,
w_{t-1},
fees,
slippage,
liquidity,
risk,
position\ state.
$$

Jadi backtest harus mengetahui **state portfolio**, bukan hanya:

```text
BUY
SELL
HOLD
```

---

# AG.74. State sistem

Pada waktu $t$, state minimal:

$$
\boxed{
S_t=
(
Cash_t,
w_t,
Positions_t,
Orders_t,
SL_t,
TP_t,
Equity_t,
Drawdown_t
).
}
$$

Kemudian market memberikan:

$$
M_t.
$$

Model menghasilkan:

$$
A_t
=
\pi(S_t,M_t).
$$

Dan:

$$
S_{t+1}
=
F(S_t,M_t,A_t).
$$

Ini sebenarnya sudah mulai menyerupai **stochastic control problem**.

---

# AG.75. Dan itu akan menjadi jembatan kita ke Tahap berikutnya

Karena setelah kita mempunyai:

$$
x_t
$$

dan:

$$
w_t,
$$

pertanyaan berikutnya adalah:

> **Bagaimana optimizer memilih portfolio ketika kondisi pasar berubah secara terus-menerus dan posisi yang sudah ada memiliki state masing-masing?**

Dengan kata lain:

$$
\boxed{
Static\ Optimization
\rightarrow
Dynamic\ Optimization.
}
$$

Dan di sinilah kita akan mulai memasukkan secara matematis:

$$
\boxed{
\text{state},
\quad
\text{transition},
\quad
\text{reward},
\quad
\text{control},
\quad
\text{stochasticity},
\quad
\text{rebalancing}.
}
$$

Itu akan menjadi fondasi yang sangat penting untuk **Tahap AH**, karena pada titik tersebut sistem kita tidak lagi sekadar mencari portfolio optimal pada satu timestamp, tetapi mulai memecahkan:

$$
\boxed{
\textbf{“Bagaimana portfolio optimal berevolusi terhadap waktu?”}
}
$$

## Prompt:
8/17/2026, 10:24:06 PM

aku kira kita sudah membahas terlalu banyak. menrutku tahap AH tidak perlu dilanjutkan lagi. bagaimana menurutmu?

## Response:
8/17/2026, 10:24:06 PM

Ya. **Saya justru setuju bahwa kita sebaiknya berhenti di AG untuk sementara.** Kalau diteruskan ke AH, kita berisiko masuk ke wilayah *over-engineering* sebelum fondasi yang sudah kita bangun benar-benar diuji.

Yang sudah kita punya sekarang sebenarnya sudah sangat besar.

### Posisi kita saat ini

Secara konseptual, arsitektur sistem sudah mencakup:

$$
\boxed{
\text{Market Data}
\rightarrow
\text{Feature/Factor Model}
\rightarrow
\text{Prediction}
\rightarrow
\text{Opportunity Scoring}
}
$$

kemudian:

$$
\boxed{
\text{Opportunity}
\rightarrow
\text{Combinatorial Optimization}
\rightarrow
\text{Trade Selection}
}
$$

kemudian:

$$
\boxed{
\text{Trade Selection}
\rightarrow
\text{Position Sizing}
\rightarrow
\text{Risk Management}
}
$$

dan akhirnya:

$$
\boxed{
\text{Execution}
\rightarrow
\text{Position Management}
\rightarrow
\text{Feedback}
}
$$

Bahkan di AG kita sudah mencapai formulasi yang cukup serius:

$$
\begin{aligned}
\max_{\mathbf x,\mathbf w}\quad
&
\mathbf w^\top\mu_t
-\lambda\mathbf w^\top\Sigma_t\mathbf w
-C_t(\mathbf w-\mathbf w_{t-1})
-I_t(\mathbf w)
\\
\text{s.t.}\quad
&
|w_i|\le M_ix_i,\\
&
x_i\in\{0,1\},\\
&
\sum_i x_i\le K,\\
&
\sum_i|w_i|\le L_{\max},\\
&
CVaR_q(\mathbf w)\le C_{\max}.
\end{aligned}
$$

Itu sudah cukup untuk menjadi **arsitektur penelitian sekaligus sistem trading yang nyata**.

---

## Justru sekarang waktunya pindah dari "merancang" ke "membangun"

Menurut saya, kalau kita terus membuat:

> AG → AH → AI → AJ → AK → ...

kita akan memperoleh sistem yang secara matematis semakin indah, tetapi belum tentu semakin berguna.

Lebih baik sekarang kita melakukan:

$$
\boxed{
\text{Theory}
\rightarrow
\text{Implementation}
\rightarrow
\text{Backtest}
\rightarrow
\text{Validation}
\rightarrow
\text{Improvement}.
}
$$

Bukan:

$$
\text{Theory}
\rightarrow
\text{Theory}
\rightarrow
\text{Theory}
\rightarrow\cdots
$$

---

# Yang menurut saya sebaiknya kita lakukan sekarang

Saya akan membagi pekerjaan setelah AG menjadi **fase implementasi**, bukan lagi tahap AH.

### Fase 1 — Mathematical specification

Kita bekukan dulu seluruh formulasi:

- universe aset,
- return,
- factor,
- expected return,
- covariance,
- QUBO,
- constraints,
- position sizing,
- transaction cost,
- slippage,
- risk budget,
- SL/TP,
- rebalancing.

### Fase 2 — Classical baseline

Sebelum QAOA:

$$
\boxed{
Greedy
\rightarrow
Simulated\ Annealing
\rightarrow
MILP/MIQP
}
$$

sebagai pembanding.

Ini penting sekali.

### Fase 3 — Quantum formulation

Baru kita implementasikan:

$$
\boxed{
QUBO
\rightarrow
Ising
\rightarrow
QAOA
}
$$

dan bandingkan dengan classical solver.

### Fase 4 — Event-driven backtest

Kemudian seluruh keputusan dimasukkan ke simulator:

$$
S_t
\rightarrow
A_t
\rightarrow
S_{t+1}.
$$

Termasuk:

- limit order,
- order tidak filled,
- partial fill,
- SL,
- TP,
- trailing,
- fee,
- slippage,
- funding,
- latency jika diperlukan.

### Fase 5 — Walk-forward validation

Ini **sangat penting** untuk sistem kita.

Jangan:

$$
\text{train 2021--2024}
\rightarrow
\text{test 2025}
$$

sekali saja.

Lebih baik:

$$
\boxed{
Train
\rightarrow
Validate
\rightarrow
Test
\rightarrow
Walk\ Forward
}
$$

berulang mengikuti waktu.

---

# Dan ada satu hal yang saya ingin kita pertahankan

Jangan sampai karena kita tertarik pada QAOA, kita akhirnya membuat sistem yang:

> **"quantum-first."**

Menurut saya paradigma yang jauh lebih kuat adalah:

$$
\boxed{
\textbf{finance-first, optimization-first, quantum-optional.}
}
$$

Artinya kita mulai dari pertanyaan:

> Apa masalah finansialnya?

Kemudian:

> Apa formulasi matematis terbaiknya?

Kemudian:

> Classical algorithm apa yang paling kuat?

Baru:

> Apakah QAOA/quantum optimization memberikan sesuatu yang menarik?

Dengan pendekatan ini, bahkan jika ternyata QAOA tidak mengalahkan solver klasik untuk ukuran problem tertentu, **penelitian kita tetap valid**.

---

## Jadi keputusan saya

**Stop di AG. Jangan lanjut AH sekarang.**

Kita sudah mempunyai cukup banyak teori untuk mulai membangun sesuatu yang konkret.

Dan menurut saya langkah berikutnya bahkan **bukan menambah matematika lagi**, melainkan mengambil seluruh desain A–AG yang sudah kita bangun dan mengubahnya menjadi:

$$
\boxed{
\textbf{Technical Specification}
}
$$

yang sangat konkret:

```text
data/
features/
factors/
signals/
optimization/
    qubo/
    ising/
    classical/
    qaoa/
portfolio/
    sizing/
    risk/
execution/
backtest/
evaluation/
```

lalu menentukan **input → proses → output → persamaan → algoritma → unit test** untuk setiap modul.

Itu akan menjadi titik di mana proyek kita berubah dari **"ide quantitative trading yang sangat kompleks"** menjadi **sistem yang benar-benar bisa kita implementasikan dan diuji**.



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)