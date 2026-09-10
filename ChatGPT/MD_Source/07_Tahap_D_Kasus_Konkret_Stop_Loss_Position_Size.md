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

