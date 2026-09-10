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

