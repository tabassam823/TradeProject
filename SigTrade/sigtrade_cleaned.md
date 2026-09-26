# Signature Trading: A Path-Dependent Extension of the Mean-Variance Framework with Exogenous Signals

**Owen Futter**$^1$, **Blanka Horvath**$^{2,3}$, and **Magnus Wiese**$^4$

$^1$ *Imperial College London, Department of Mathematics*  
$^2$ *University of Oxford, Mathematical Institute and Oxford-Man Institute*  
$^3$ *The Alan Turing Institute*  
$^4$ *University of Kaiserslautern, Department of Mathematics*  

**arXiv:** [2308.15135v2](https://arxiv.org/abs/2308.15135) [q-fin.PM] 30 Aug 2023

---

### Abstract

> In this article we introduce a portfolio optimisation framework, in which the use of rough path signatures [[Lyo98]](#ref-Lyons1998DifferentialSignals.) provides a novel method of incorporating path-dependencies in the joint signal-asset dynamics, naturally extending traditional factor models, while keeping the resulting formulas lightweight, tractable and easily interpretable. Specifically, we achieve this by representing a trading strategy as a linear functional applied to the signature of a path (which we refer to as "Signature Trading" or "Sig-Trading"). This allows the modeller to efficiently encode the evolution of past time-series observations into the optimisation problem. In particular, we derive a concise formulation of the dynamic mean-variance criterion alongside an explicit solution in our setting, which naturally incorporates a drawdown control in the optimal strategy over a finite time horizon. Secondly, we draw parallels between classical portfolio strategies and Sig-Trading strategies and explain how the latter leads to a pathwise extension of the classical setting via the "Signature Efficient Frontier". Finally, we give explicit examples when trading under an exogenous signal as well as examples for momentum and pair-trading strategies, demonstrated both on synthetic and market data. Our framework combines the best of both worlds between classical theory (whose appeal lies in clear and concise formulae) and between modern, flexible data-driven methods (usually represented by ML approaches) that can handle more realistic datasets. The advantage of the added flexibility of the latter is that one can bypass common issues such as the accumulation of heteroskedastic and asymmetric residuals during the optimisation phase. Overall, Sig-Trading combines the flexibility of data-driven methods without compromising on the clarity of the classical theory and our presented results provide a compelling toolbox that yields superior results for a large class of trading strategies.

**Keywords:** `Mean-Variance Optimisation` · `Signature Methods` · `Data-Driven Methods` · `Dynamic Trading Strategies` · `Path-Dependent Signals` · `Statistical Arbitrage` · `Momentum Strategies` · `Stochastic Filtering`

*Acknowledgements:* The authors would like to thank William F. Turner for helpful comments as well as Johannes Muhle-Karbe, Cristopher Salvi and Joseph Mulligan for fruitful discussions throughout the writing of this paper. OF and BH thankfully acknowledge the funding of this research by Atlantic House Investments & EPSRC Oxford-ICL Centre of Doctoral Studies in Mathematics of Random Systems.

---

## Table of Contents
- [1 Introduction](#1-introduction)
  - [1.1 Background and Motivation](#11-background-and-motivation)
  - [1.2 Summary of Contributions](#12-summary-of-contributions)
- [2 The Modelling Setup of the Sig-Factor Model](#2-the-modelling-setup-of-the-sig-factor-model)
  - [2.1 The Signature](#21-the-signature)
  - [2.2 Sig-Factor Model](#22-sig-factor-model)
- [3 Main Result](#3-main-result)
  - [3.1 Sig-Factor Model vs Classical Factor Model](#31-sig-factor-model-vs-classical-factor-model)
  - [3.2 Optimal Static Portfolio](#32-optimal-static-portfolio)
  - [3.3 Sig-Factor Model Efficient Frontier](#33-sig-factor-model-efficient-frontier)
- [4 Implementation](#4-implementation)
- [5 Numerical Results](#5-numerical-results)
  - [5.1 Synthetic Data](#51-synthetic-data)
    - [5.1.1 Pairs Trading](#511-pairs-trading)
    - [5.1.2 Incorporating Exogenous Signal](#512-incorporating-exogenous-signal)
  - [5.2 Learning Momentum as a Sig-Trading Strategy](#52-learning-momentum-as-a-sig-trading-strategy)
- [6 Conclusion](#6-conclusion)
- [Appendix A: Rough Path & Tensor Algebra Preliminaries](#appendix-a-rough-path--tensor-algebra-preliminaries)
  - [A.1 The Tensor Algebra](#a1-the-tensor-algebra)
  - [A.2 Rough Paths & The Signature](#a2-rough-paths--the-signature)
- [Appendix B: Proofs](#appendix-b-proofs)
  - [B.1 Proof of Theorem 2.11](#b1-proof-of-theorem-211)
- [References](#references)

---

## 1 Introduction

The design and construction of trading strategies is a fundamental aspect of finance and subsequently, has been extensively researched in the past decades. Creating a trading strategy can mainly be divided into two areas: extracting *alpha* and allocating the associated *risk*. Methods of extracting alpha depend on the trade horizon or trade frequency and are often achieved through statistical techniques, which can then be incorporated into a parametric model. Meanwhile, allocating the associated risk generally depends on your choice of model and objective criterion; conventionally, optimisation methods are deployed to find a transformation of the signal-asset dynamics that maximises the chosen utility function of the strategy PnL, with respect to the underlying model. The work ([[Mar52](#ref-Markowitz1952PortfolioSelection)]) of Markowitz introduced modern portfolio theory based on portfolio allocation determined by investors' preferences to risk and returns, resulting in a well-diversified portfolio. Classical methods consist of fixing a class of probabilistic parametric models and calibrating the model's parameters with respect to the empirical price process. Depending on the choice of parametric model and its corresponding parameters, the optimal portfolio will be different. In well-studied families of models it is possible to find closed-form expressions of the optimal portfolio given certain risk and return preferences, however in more complex parametric models or with more general utility functions, explicit solutions may not be attainable and so numerical techniques are used.

We can observe from the above blueprint, that the possible choices of model are vast - for example all possible ways of feature engineering, return prediction, or the choice of probabilistic model. The choice of optimisation technique will then be tailored to the choice of utility function and the model. While well-studied models provide a useful benchmark for practitioners, many of the assumptions made are restrictive. Several modelling assumptions do not reflect stylised facts in practice such as non-stationarity, heavy tails and path-dependent volatility ([[Fuk21](#ref-Fukasawa2021VolatilityRough); [Das22](#ref-Das2022RoughnessSignals); [GL22](#ref-Guyon2022VolatilityPath-Dependent); [MMB23](#ref-Morel2023PathMonte-Carlo)]) - all of which are exhibited by financial time-series data ([[Con01](#ref-Cont2001EmpiricalIssues)]). The latter considerations are even more relevant when working with multiple assets since dependence structures are highly non-linear, often with cross-sectional trend- and mean-reversion patterns occurring in practice. Recent research activity has brought modelling approaches to the forefront that are inherently data-driven and provide a highly flexible framework that is able to capture a broader set of asset dynamics than currently used classical stochastic models did. Data-driven techniques for trading have increased in recent years due to the rise of machine learning applications in finance, such as in [[ZZR20b](#ref-Zhang2020DeepTrading); [Wan19](#ref-Wang2019PortfolioLearning); [ZZR20a](#ref-Zhang2020DeepOptimization); [Jai+21](#ref-Jaimungal2021RobustLearning); [Van+21](#ref-VanStaden2021ACosts); [PZ22](#ref-Pretorius2022DeepManagement); [GPZ21](#ref-Guijarro-Ordonez2021DeepArbitrage); [CJC22](#ref-Coache2022ConditionallyLearning)], as well as in hedging applications in [[Büh+18](#ref-Buhler2018DeepHedging); [HTZ21](#ref-Horvath2021DeepVolatility); [LH23](#ref-Limmer2023RobustGANs)]. The requirement for complex and accurate synthetic data to train and test trading frameworks has also led to extensive research in developing market generators ([[Bue+21](#ref-Buehler2021GeneratingSignatures); [Wie+19](#ref-Wiese2019QuantSeries); [Ni+20](#ref-Ni2020ConditionalGenerationb); [Ni+21](#ref-Ni2021Sig-WassersteinGeneration); [Iss+23](#ref-Issa2023Non-adversarialScores)]). In this work, we go a step further than just modelling asset dynamics in a model-free way and take the approach of utilising rough path theory ([[Lyo14](#ref-Lyons2014RoughStreams); [FV10](#ref-Friz2010MultidimensionalPaths)]) also to develop a trading strategy that is determined by the expected signature of the joint signal-asset process. Since the aforementioned expected signature uniquely determines the law of the stochastic process ([[CL13](#ref-Chevyrev2013CharacteristicPaths)]), it is immediate to see how the techniques simplify to the classical case when applied to traditional stochastic models. By taking a pathwise approach to trading, this naturally alleviates probabilistic restrictions, resulting in a *model-free* or model-agnostic setup ([[CC23](#ref-Chiu2023AFinance)]). A pathwise setting has been used in [[PP16](#ref-Perkowski2016PathwiseFinance); [Rig16a](#ref-Riga2016ATrading); [Rig16b](#ref-Riga2016PathwiseFinance); [ACX23](#ref-Ananova2023Model-freeStrategies)], and has more recently been utilised to handle more general portfolios in [[All+21](#ref-Allan2021Model-freeApproach)], as well as in applications to derivative pricing and calibration in [[CGS22](#ref-Cuchiero2022Signature-basedCalibration)] and optimal stopping problems in [[Bay+21](#ref-Bayer2021OptimalSignatures)].

Inspired by the work of Perez et al. in [[Arr18](#ref-Arribas2018DerivativesPayoffs); [KLA20](#ref-Kalsi2020OptimalSignatures); [LNA19b](#ref-Lyons2019NumericalSignatures)], we adopt the idea of representing a trading strategy as a linear functional applied to the signature of a path and extend this to to incorporate exogenous market signals and multiple assets. We can think of a trading strategy as a decision made using the knowledge of the current state (e.g. the previous price path, plus some exogenous trading signal); in other words as a function from path space to some decision process. In practice, the true driving processes are most likely not (directly) observable and hidden by layers of noise. Hence the mapping from the previous price process to a trading strategy is often done first by removing noise in the system through stochastic filtering [[BC09](#ref-Bain2009FundamentalsFiltering); [CLO21](#ref-Crisan2021PathwiseProblem)] (i.e. an exponentially weighted moving average or Kalman filter) and then optimised based on the resulting prediction. Recently, the authors in [[Coh+23](#ref-Cohen2023NowcastingMethods)] prove how the Kalman filter can in fact be equivalently written as a linear regression on the signature. Work has also been conducted in [[DCS21](#ref-Dyer2021DeepModels); [Dye+22](#ref-Dyer2022ApproximateDiscrepancies)] with relation to approximate Bayesian computation using signatures. This naturally prompts the question - can the class of linear functionals on the signature be seen as a rich enough class of maps that represent such trading strategies? We will show that this is possible to due to signatures' capability to approximate continuous functions on paths. Also perhaps crucially, the Sig-Trading framework does not impose the restriction that the underlying asset or signal be Markovian, allowing the Sig-Trader to capture auto-correlation and mean-reverting behaviours within the process that perhaps some more classical methods are not able to exploit. This enables us to incorporate path-dependent considerations into our trading decisions, while still obtaining a closed-form solution, that is easy to compute and simple to analyse.

The paper is organised as follows: In Section [2](#sec:market_model) we introduce key foundations of Sig-Trading and the concept of the extension to classical factor models. In Section [3](#sec:original) we present our main result, an analytic solution to the dynamic mean-variance criterion for Sig-Trading and compare this to original factor models, whilst introducing a Sig-Trading version of the efficient frontier. Finally, in Section [4](#sec:implement) we discuss its implementation and in Section [5](#sec:results) we highlight the advantages of Sig-Trading, provide intuitive examples and demonstrate its possible use cases in practice, such as pairs trading, momentum, and trading under an exogenous signal.

### 1.1 Background and Motivation

### The Objective {#the-objective .unnumbered}

In this article, we are concerned with finding an optimal *systematic* and *dynamic* trading strategy such that the trader continuously updates their position as new information filters in. This is done with no discretion and is defined as a function of the market state, which continuously updates through time, leading to a new position for each time $t$.

We denote $T \in \mathbb{R}$ the terminal time. Let $(\Omega, \mathcal{F}, (\mathcal{F}_t)_{t \in [0,T]}, \mathbb{P})$ be a filtered probability space. Furthermore, denote by $X=(X_t)_{t \in [0,T]}$ a non-negative $\mathbb{R}^d$-valued stochastic process satisfying $X_0^m=1$ for $m \in \{1,\dots,d\}$. We are interested in finding an optimal, predictable dynamic trading strategy $(\xi)_{t \in [0,T]}$ that maximises the expected utility of the PnL 
<a id="eq:optimisation"></a>
$$
\begin{aligned}
\max_{\substack{(\xi_t)_{t \in [0,T]} \\ \text{s.t constraints}}} \mathbb{E}(U(V_T))
\end{aligned}
$$ where $V_T$ is the terminal value of the trading strategy (i.e the PnL) 
<a id="eq:PnL"></a>
$$
\begin{aligned}
V_T = \sum_{m=1}^d \int_0^T \xi_t^m dX_t^m.
\end{aligned}
$$ Here, the optimal strategy $\xi$ is a function of the market state (i.e filtration $\mathcal{F}$ at time $t$) and its optimality is with respect to the constraints and utility function that the trader chooses. In order to solve such an optimisation problem, commonly methods are constructed from the following structure:

1.  Fix a framework to model the underlying dynamics of $X$,

2.  Choose an objective criterion (utility and constraints),

3.  Optimisation with respect to (1) and (2).

Most likely, a trader may be trading under the presence of exogenous information $f$ to enrich the filtration $\mathcal{F}$ (and hence the model of the dynamics of $X$). Recently, extensive research in this direction has been conducted in optimal execution literature, e.g. in a more classical setting in [[LN19](#ref-Lehalle2019IncorporatingTrading); [For+22](#ref-Forde2022OptimalResilience); [SC22](#ref-Sanchez-Betancourt2022BrokersSignals); [CDM22](#ref-Cartea2022ExecutionMakers); [BCK23](#ref-Bank2023OptimalSignals); [CMN23](#ref-Cont2023FastInformation)] and with machine learning applications in [[BDG21](#ref-Bergault2021Multi-assetDynamics); [CDO23](#ref-Cartea2023BanditsSignals)]. In this work, we do not consider market impact, but refer the reader to [[KLA20](#ref-Kalsi2020OptimalSignatures); [CAS22](#ref-Cartea2022Double-ExecutionSignatures)] to work in this area involving signatures.

### Modelling Dynamics {#modelling-dynamics .unnumbered}

The choice of model in (1) often requires explicitly predicting asset returns through supervised learning techniques. Therefore, a large number of models tend to fall into the *predict-then-optimise* framework, where heavy assumptions are made on the asset returns/market factors that are input into any prediction, leaving the final solution exposed to asymmetric and compounded errors. Solutions to these problems are very well studied with specific assumptions and restrictions on the underlying asset process, however without these assumptions this can be much more difficult. In such stochastic control problems, the asset dynamics are explained by a diffusion process and dynamic programming can then be used to solve the Hamilton-Jacobi-Bellman (HJB) equation. In practice, the future expected returns (the drift of the process $X$), $\mu_{t+1}$, are often predicted via supervised learning methods, using trading signals or *factors* as statistical predictors which are embedded into the framework itself ([[CR83](#ref-Chamberlain1983ArbitrageMarkets); [NER92](#ref-Ng1992AReturns); [FF93](#ref-Fama1993CommonBonds); [FF15](#ref-Fama2015AModel); [SW10](#ref-Stock2010DynamicModels); [GP13](#ref-Garleanu2013DynamicCosts)]). A generic (linear) factor model models the asset returns at time $t$, as 
<a id="eq:factor_model_predict"></a>
$$
\begin{aligned}
\mu_{t+1} = \mathbb{E} [ r_{t+1} \vert \mathcal{F}_t ] = Bf_t + \varepsilon_{t+1}
\end{aligned}
$$ where $r$ is the $d$-dimensional asset returns, $B$ is a $d \times N$ matrix of factor coefficients, $f_t$ is a vector of $N$ factor returns and $\varepsilon$ is a vector of the $d$ assets' (unexplained) residuals returns. This is set up as a supervised linear regression on future returns, as a function of the trading signals/factors.

However, when working with financial data, there is generally a very low signal to noise ratio and the residual terms $\epsilon_t$ are badly behaved, violating many statistical assumptions. Due to autocorrelation, non-stationarity and path-dependent volatility in the underlying asset $X$ (and also the signal $f$), this framework can very quickly become problematic, and these asymmetric errors are then compounded in the optimisation phase. In order to capture some of the autocorrelation in the residuals, a trader could incorporate the path into the signal $f$ via stochastic filtering ([[BC09](#ref-Bain2009FundamentalsFiltering); [CLO21](#ref-Crisan2021PathwiseProblem)]). Traders may also scale returns for volatility in order to remove heteroskedasticity ([[Eng01](#ref-Engle2001GARCHEconometrics)]), log transform to remove asymmetricity or winsorise to remove fat tails; in [[Das22](#ref-Das2022RoughnessSignals)], the roughness of signals is also discussed. However, there still remains a large amount of discretion in such feature engineering and we will show that the signature can be used efficiently and robustly to tackle these issues in a data-driven manner. To avoid the accumulation of mis-specified error terms from the prediction phase, end-to-end (E2E) approaches using machine learning frameworks have been used in [[CI22](#ref-Costa2022DistributionallyConstruction)] and [[Zha+21](#ref-Zhang2021ALearning)] to ensure robustness by bypassing the prediction stage.

### Choice of Utility {#choice-of-utility .unnumbered}

Once we have a model that characterises the dynamics of the driving signal and the underlying asset, we can proceed to transforming this into a trading strategy position. How one does this depends on a variety of conditions such as the type of strategy, if we are trading multiple assets, risk preferences, trade frequency and investment horizon. Common objective criteria focus on a single trade-by-trade optimisation basis, overlooking the potential path that the trading strategy will take. However as alluded to previously, in practice signals and underlying assets can have strong temporal dependencies and so subsequent trading strategy positions will inherit autocorrelation structure.



<a id="fig:dynamic_strategy"></a>
<img src="images/mean_rev_strategy.png" />

*Comparison of the PnL profile through time of a mean-reverting strategy vs a non mean-reverting strategy.*



As a motivating example in Figure [1](#fig:dynamic_strategy), we consider the comparison between a strategy that is mean-reverting (has autocorrelation) vs one that doesn't. Both strategies yield identical daily PnL distributions (and hence Sharpe ratio), but have different distributions at a future time due to the temporal structure within the strategy over time. By optimising with respect to a future time horizon, we are inherently optimising for a dynamic criterion that is dependent on the path. This approach naturally integrates a drawdown control in the optimisation, since drawdowns are a path-dependent characteristic. Achieving a strategy with a small maximum drawdown either requires a strong trend-to-noise ratio (high Sharpe ratio) or relies on the strategy being mean-reverting during volatile periods ([[RSB17](#ref-Rej2017YouWorrying)] provides a neat analysis).

Mean-variance optimisation, perhaps the most widely known choice of utility function, was first introduced in Markowitz's thesis ([[Mar52](#ref-Markowitz1952PortfolioSelection)]). He demonstrated that it was natural to construct an objective function that rewarded positive returns while penalizing associated risk (via variance). Subsequently, this framework has been researched extensively in the literature, including the CAPM asset pricing framework ([[Sha64](#ref-Sharpe1964CapitalRisk)]). In this work, we extend this approach to integrate path-dependencies and optimise under a *dynamic* mean-variance criterion. We do so by simultaneously capturing path-dependent structure in the dynamics, while managing path-dependent variance through the lifetime of the trade. The general dynamic mean-variance optimisation can be framed as 
<a id="eq:mean_var_optimisation"></a>
$$
\begin{aligned}
\max_{(\xi_t)_{t \in [0,T]}} \mathbb{E} \left(\sum_{m=1}^d \int_0^T \xi_t^m dX_t^m \right) - \frac{\lambda}{2} \textup{ Var}\left(\sum_{m=1}^d\int_0^T \xi_t^m dX_t^m \right),
\end{aligned}
$$ where the quantity 
$$
\begin{align*}
V_T := \sum_{m=1}^d \int_0^T \xi_t^m dX_t^m
\end{align*}
$$ is the strategy PnL at some future time $T$.

### Optimisation {#optimisation .unnumbered}

Depending on the choice of underlying model, the optimisation method can be different - for example, reinforcement learning can in fact be used to simulataneously learn the model and the optimal strategy ([[WZ19](#ref-Wang2019Continuous-TimeFramework); [BT23](#ref-Brini2023DeepReturns); [Soo+23](#ref-Sood2023DeepOptimization)]). The authors in [[KEA19](#ref-Kalayci2019AOptimization)] provide an extensive overview of alternate formulations and methods for mean-variance optimisation. In the case of the predict-then-optimise framework, such as [eq:factor_model_predict](#eq:factor_model_predict), the mean-variance solution is given by 
<a id="eq:mean_var_sol"></a>
$$
\begin{aligned}
\xi_t^* = \frac{1}{\lambda} \Sigma_t^{-1} \mu_t
\end{aligned}
$$ where $\Sigma_t$ is the $d \times d$ covariance matrix of asset returns at time $t$ and $\mu_t$ is the $d \times 1$ vector of expected returns over the next time period $t \in [0,1]$. This solution is highly intuitive and tractable. The performance of such a trading strategy is then mostly reliant on the predictive power of the signal that goes into the model, as well as the well-posedness of the covariance structure, leaving flexibility and responsibility in the hands of the trader. However, as has been highlighted in decades of literature, this framework is highly restrictive, such as the assumption of normally distributed returns and stationarity in the factor signal.

### 1.2 Summary of Contributions {#section:our_approach}

Several stylised facts exhibited in asset prices are not represented in most classical dynamic optimisation frameworks. Many of these stylised facts, such as slow decaying autocorrelation and volatility clustering, are path-dependent properties and so it advantageous to incorporate path-dependence into any factor model. Due to such characteristics in financial time series data, the predict-then-optimise composition in classical factor models can be prone to asymmetric errors that are compounded through the optimisation process. Work from [[CI22](#ref-Costa2022DistributionallyConstruction)] and [[Zha+21](#ref-Zhang2021ALearning)] have provided robust machine learning approaches to help account for this issue by bypassing the direct prediction phase. Alternatively, we are able to exploit such dynamics in the signal and asset and incorporate these not only to increase expected return, but to dynamically reduce variance of PnL. Due to the powerful properties arising in rough path theory we are able to simultaneously incorporate such dynamics into both the modelling framework and the optimisation phase at the same time, bypassing any explicit prediction.

In summary, our contribution is to extend the existing signature trading strategy framework first presented in the thesis of Perez ([[Per20](#ref-PerezArribas2020SignaturesFinance)]), by deriving a closed form mean-variance optimal trading strategy for multiple assets that accounts for path-dependent dynamics between exogenous trading signals and the underlying assets, thereby providing a pathwise extension to classical factor models. Our framework is simple to implement and does not require heavy machinery while comparative machine learning methods may require extensive network building and hyperparameter tuning every time the trader wants to perform a new optimisation. This is possible due to the mathematical properties of the signature allowing us to linearise the objective function, meaning it is relatively straightforward to solve for an explicit closed-form solution. Sig-Trading is a one-model-fits-all type framework that is flexible enough to adapt to any type of underlying asset and market factor process. Once a linear functional $\ell$ is obtained from past data samples it is straightforward to unravel this into an implementable trading strategy characterised by the number of units to buy/sell at each time point $t \in [0,T]$. Since the strategy is dynamic, as new data arrives the Sig-Trader will continuously compute the signature and update their position accordingly.

#  The Modelling Setup of the Sig-Factor Model  {#sec:market_model}

Rough path theory has provided many valuable tools, such as the Signature of a path, to help shift the focus from probabilistic to pathwise approaches when working with streams of data. The concept of the signature was first introduced in [[Che57](#ref-Chen1957IntegrationFormula); [Che77](#ref-Chen1977IteratedIntegrals)] and has played a crucial role in rough path theory in [[Lyo98](#ref-Lyons1998DifferentialSignals.); [LCL07](#ref-Lyons2007DifferentialPaths); [FV10](#ref-Friz2010MultidimensionalPaths); [FH20](#ref-Friz2020AStructures)]. Recent mathematical finance literature has benefited immensely from its universality property, which states that linear functionals on the signature are dense in the space of continuous functions on compact sets of paths (Theorem [27](#eq:universal_approx)). This result allows to approximate a trading strategy as a linear functional on the terms of the signature. Incorporating higher order path-dependent characteristics via the signature allows us to capture stylised facts of financial time series data, without requiring or imposing an explicit probability distribution on the future returns. In this section, we discuss the notion of a $\textit{Signature Trading Strategy}$, first introduced in [[LNA19b](#ref-Lyons2019NumericalSignatures)], and how this is incorporated into a $\textit{model-free}$ setting, as well as under the presence of exogenous market signals.

### 2.1 The Signature {#sec:sig_intro}

In this section, we first recall definitons of path augmentations and how these are used in preceding results such as Theorem [10](#eq:hoff_converegence), which is crucial for our main result Theorem [13](#thm:orig_solution). Whilst we introduce fundamental definitions in Section [2.1](#sec:sig_intro), we have collected some basic concepts and definitions from rough path theory for convenience in Appendix [7](#sec:appx_rough_paths) as they may aide in understanding of notations and technicalities throughout the paper. For a more thorough introduction to signatures, see for example [[Gyu+13](#ref-Gyurko2013ExtractingStream); [CK16](#ref-Chevyrev2016ALearning); [LLN13](#ref-Levin2013LearningSystem); [Fer21](#ref-Fermanian2021EmbeddingSignatures); [LM22](#ref-Lyons2022SignatureLearning)] for excellent articles focusing on intuition and understanding in a practical setting. For specific applications of signatures in finance we refer the reader to [[Bon+19](#ref-Bonnier2019DeepTransforms); [KLA20](#ref-Kalsi2020OptimalSignatures); [ASS20](#ref-Arribas2020Sig-SDEsFinance); [Bay+21](#ref-Bayer2021OptimalSignatures); [CGS22](#ref-Cuchiero2022Signature-basedCalibration); [Ald+22](#ref-Alden2022Model-AgnosticSignatures); [DT23](#ref-Dupire2023FunctionalExpansions); [IH23](#ref-Issa2023Non-parametricStructures); [WKM23](#ref-Wiese2023Sig-Splines:Models)].

Unless stated otherwise, the process $(X_t)_{t \in [0,T]}$ is a continuous, stochastic process defined on a filtered probability space $(\Omega, \mathcal{F}, (\mathcal{F}_t)_{t \in [0,T]}, \mathbb{P})$. We often refer to the path trajectories of the process $(X_t)_{t \in [0,T]}$ as $X:[0,T] \to \mathbb{R}^d$, which we assume can be lifted to geometric rough paths (Definition [19](#defn:geom_rough_path)).



> **Definition 1**. *(Time reparameterisation). Let $X:[0,T] \to \mathbb{R}^d$, $\varphi:[0,T]\to[T_1, T_2]$ a non-decreasing surjection, then the re-parameterised path is denoted as $X \circ \varphi =: X^{\varphi} : [T_1, T_2] \to \mathbb{R}^d$.*





> **Definition 2**. *(Add-time process). Often, we may wish to preserve the temporal structure of a path and so we keep the time parameterisation of the path $X$ by defining a new process, $\hat{X}$. We denote the time-augmented process by $\hat{X}_t=(t, X_t), t \in [0,T]$ such that $(t,X_t) =: \hat{X}: [0,T] \to \mathbb{R}^{d+1}$.*





> **Definition 2.3** *(Hoff Lead-Lag Process, [[Hof06](#ref-Hoff2006ThePath)], [[FHL16](#ref-Flint2016DiscretelyProcess)]). Let $\hat{X}:[0,T] \to \mathbb{R}^{d+1}$ be the continuous time-augmented process of $X$, discretely sampled at $t=t_0,\dots,t_{2N}$. The *Hoff lead-lag transformed path* is defined as the piecewise linear interpolation $\hat{X}^{LL}:[0,T] \to \mathbb{R}^{2(d+1)}$ such that 
$$
(\hat{X}_{t_i}^{LL})^{2N}_{i=1} = (\hat{X}_{t_i}^{\textup{lead}}, \hat{X}_{t_i}^{\textup{lag}})^{2N}_{i=1}
$$ where 
$$
\hat{X}_{t}^{\textup{lead}} =
>     \begin{cases}
>         \hat{X}_{t_{k+1}}, & \quad \text{if } t \in [2k, 2k+1] \\
>         \hat{X}_{t_{k+1}} + 2(t-(2k+1))(X_{t_{k+2}} - X_{t_{k+1}}), & \quad \text{if } t \in [2k+1, 2k+\frac{3}{2}] \\
>         \hat{X}_{t_{k+2}}, & \quad \text{if } t \in [2k+\frac{3}{2}, 2k+2],
>     \end{cases}
$$ 
$$
\hat{X}_{t_j}^{\textup{lag}} =
>     \begin{cases}
>         \hat{X}_{t_i}, & \quad \text{if } t \in [2k, 2k+\frac{3}{2}] \\
>         \hat{X}_{t_{k+1}} + 2(t-(2k+\frac{3}{2}))(X_{t_{k+1}} - X_{t_{k}}), & \quad \text{if } t \in [2k+\frac{3}{2}, 2k+2].
>     \end{cases}
$$*





> **Remark 2.1**. *There also exists a more intuitive and straightforward definition of a lead-lag process, however we decide not to opt for this version and instead consider the so-called *Hoff process* ([[Hof06](#ref-Hoff2006ThePath)]), due to its fundamental properties in the case when we want to calculate the PnL of our trading strategy (Theorem [2.10](#eq:hoff_converegence)). This is due to the powerful, non-trivial result proven in [[FHL16](#ref-Flint2016DiscretelyProcess)] that states that the Itô integral of a function of a process $X$ against itself, can be recovered via the components of the Hoff lead-lag transformation. This will be made more precise in Section [2.2](#sec:sig_factor_model).*





<a id="fig:hoff_lead_lag"></a>
<img src="images/hoff_ll_three_plots.png" />

*SPY ETF sample price trajectory between 02/03/2020-30/04/2020 (LHS) and its respective Hoff lead-lag transformation (Centre) and the lead vs the lag component (RHS).*



**Notation:** We distinguish that any integral of the form $\int f \circ dx$ refers to Stratnovich integration, meanwhile $\int f  dx$ will refer to Itô integration.



> **Definition 4**. *(Signature Transform). Let $X:[0,T] \to \mathbb{R}^d \in C^{1-var}([0,T];\mathbb{R}^d)$ be a (piecewise) smooth path. Let us define the simplex $\Delta_T = \{(s,t) : 0 \leq s \leq t \leq T \}$. The signature of $X$ between fixed time $s$ and $t$ is a map 
> $$
> \begin{align*}
> \mathbb{X} : \Delta_T & \to T((\mathbb{R}^d)) \\
> (s,t) & \mapsto \mathbb{X}_{s,t} := (1, \mathbb{X}_{s,t}^1, \dots, \mathbb{X}_{s,t}^n, \dots )
> \end{align*}
> $$ where the $n$-th order of the signature is defined as 
> $$
> \begin{align*}
> \mathbb{X}_{s,t}^n := \int \dots \int_{s < u_1 < \dots < u_n < t} dX_{u_1} \otimes \dots \otimes dX_{u_n} \in (\mathbb{R}^d)^{\otimes n}.
> \end{align*}
> $$ The signature is a $T((\mathbb{R}^d))$-valued process, which can be viewed as 
> $$
> \begin{align*}
> \mathbb{X}^{< \infty}_{0,T} = \left( \underbrace{
> \begin{matrix}
> \text{ }
> \\
> \mathbb{X}_{0,T}^{\mathbf{\emptyset}} \\
> \text{ }
> \end{matrix}}_{\textstyle =1} \text{ } , \text{ }
> \underbrace{\begin{pmatrix}
> \mathbb{X}_{0,T}^{\mathbf{1}}   \\
> \vdots \\
> \mathbb{X}_{0,T}^{\mathbf{d}}
> \end{pmatrix}}_{\textstyle \mathbb{X}_{0,T}^1}
> \text{ } , \text{ }
> \underbrace{\begin{pmatrix}
> \mathbb{X}_{0,T}^{\mathbf{11}} & \dots &  \mathbb{X}_{0,T}^{\mathbf{1d}}   \\
> \vdots & \ddots & \vdots \\
> \mathbb{X}_{0,T}^{\mathbf{d1}} & \dots & \mathbb{X}_{0,T}^{\mathbf{dd}}
> \end{pmatrix}}_{\textstyle \mathbb{X}_{0,T}^2} \text{ } , \text{ } \dots
> \right).
> \end{align*}
> $$ The signature of a path can be truncated at any finite order $N \in \mathbb{N}$. We denote the truncated signature up to order $N$ as 
> $$
> \begin{align*}
> \mathbb{X}^{\leq N} : \Delta_T & \to T^{(N)}(\mathbb{R}^d) \\
> (s,t) & \mapsto \mathbb{X}_{s,t} := (1, \mathbb{X}_{s,t}^1, \dots, \mathbb{X}_{s,t}^N).
> \end{align*}
> $$*



**Notation:** Throughout, we refer to the (un-truncated) signature between time $0$ and time $T$ as $\mathbb{X}^{< \infty}_{0,T}$. We may refer to $\mathbb{X}_{0,T}^n$ as being the $n$-th *level* of the signature and $\mathbb{X}_{0,T}^{\leq N}$ as the $N$-th *order* truncated signature.

**Notation:** We will use bold blue for any word $\mathbf{w} \in \mathcal{W}(A_d)$. Words are the multi-indices that can be thought of as the different multi-indices inside the tensor algebra. By using a specific word $\mathbf{w}$, this will often equate to referring to the specific multi-index associated to that word.



> **Definition 5**. *(Linear functionals on the tensor algebra). Note that there is a natural pairing between the extended tensor algebra $T((\mathbb{R}^d))$ and its dual space $T((\mathbb{R}^d)^*)$, by which we denote 
> $$
> \begin{align*}
> \langle \cdot , \cdot \rangle : T((\mathbb{R}^d)^*) \times T((\mathbb{R}^d)) \to \mathbb{R}
> \end{align*}
> $$ and is given by 
$$
\langle \ell , \mathbb{X} \rangle = \sum_{\mathbf{w} \in \mathcal{W}(A_d)} \ell_{\mathbf{w}} \mathbb{X}^{\mathbf{w}}
$$ for $\ell \in T((\mathbb{R}^d)^*)$, $\mathbb{X} \in  T((\mathbb{R}^d)).$ We make clear that there exists a canonical isomorphism $(\mathbb{R}^d)^* \cong \mathbb{R}^d$ through the mapping $(\mathbb{R}^d)^* \ni \langle \ell , \cdot \rangle \mapsto \ell \in \mathbb{R}^d$.*



### 2.2 Sig-Factor Model {#sec:sig_factor_model}

In this section, we develop and collect the tools required in order to find optimal trading strategies with respect to a given objective criterion. The key ingredient is that we can approximate a trading strategy as a linear functional on the signature of the path, which is formulated in Theorem [8](#thm:sig_approx). Then, by embedding the *market factor process* (Definition [6](#defn:market_factor_process)) as a geometric rough path via the signature and using Theorem [2.10](#eq:hoff_converegence), we alleviate most probabilistic restrictions that classical methods may have. Theorem [11](#thm:int_sig) subsequently allows us to in fact bypass the Itô integral entirely and express the expected PnL as a linear functional on the expected Hoff lead-lag signature. Hence, all that remains to be done in order to optimise under a given criterion (i.e mean-variance), is to solve an optimisation problem - equating to solving a system of linear equations.

We consider the scenario, as is often the case in practice, that we observe a much larger market state than just the asset trajectories themselves, i.e we observe the natural filtration of a new process that consists of the original price trajectories, enriched with some new market factors $f_t = (f^1_t, \dots, f^N_t)$. A *market factor* can be any un-tradable characteristic, classified as a stochastic process $(f_t)_{t \in [0,T]}$ that may be used in tandem with our framework, in order to enrich the market state and provide predictability. In practice, factors are chosen and understood as a driving signal of the the underlying process. Unless stated otherwise, we assume the underlying asset process $(X_t)_{t \in [0,T]}$ is a continuous, stochastic process whose path trajectories can be lifted to geometric rough paths (Definition [19](#defn:geom_rough_path)). We note that, while our price process may be a semi-martingale, we do not require any restriction on the nature of the exogenous market signals, where as traditional factor models may require stationarity.



> **Definition 6**. *(Market factor process). Let $X=(X_t)_{t \in [0,T]}$ be a $d$-dimensional tradable underlying asset process and $\{f^i \}_{i=1}^N$ are $N$ un-tradable exogenous trading signals. Then we define the (time-augmented) *market factor process* as the $(1+d+N)$-dimensional process 
> $$
> \begin{align*}
> \hat{Z}_t := (t, X_t, f_t)
> \end{align*}
> $$ that induces the natural filtered probability sapce $(\Omega, \mathcal{F}^{Z}, (\mathcal{F}^{Z}_t)_{t \in [0,T]}, \mathbb{P})$, where the filtration of $X$ satisfies $\mathcal{F}^X \subseteq \mathcal{F}^Z$ such that $X$ is driven by $\{f^i \}_{i=1}^N$. Throughout the remainder of this paper, we maintain such assumptions on $\hat{Z}$. We define as the space of all *market factor trajectories* for given assets $X$ and factors $f$. 
$$
\mathcal{Z}^{f}_{0,T} := \{ \text{   } \hat{Z}_t = (t, X_t, f_t) \quad \vert \quad X:[0,T] \to \mathbb{R}^d,  \text{ and } f:[0,T] \to \mathbb{R}^N \text{ and } Z_0 = (0,1,1)  \text{   } \}
$$*





> **Definition 7**. *(Exogenous Signature Trading Strategy). Let $\hat{Z}$ be a market factor process as defined in Definition [6](#defn:market_factor_process). Let $\xi = (\xi)_{t \in [0,T]}$ be an adapted, $\mathcal{F}^Z_t$-predictable and integrable strategy such that $\int^T_0 \xi_s^2 ds < \infty$. If the strategy $\xi$ is then a function of the market state, that is $\xi_t = \phi(\hat{Z}_{0,t})$, a continuous function of the previous *market factor trajectory* up to time $t$. We can extend $\xi$ to be a *signature trading strategy*, such that 
> $$
> \begin{align*}
> \xi_t^m = \langle \ell_m, \hat{\mathbb{Z}}_{0,t} \rangle \approx \phi(t,Z_{0,t}), \quad \forall m = 1,\dots,d.
> \end{align*}
> $$ We define the space of all *exogenous signature trading strategies* with respect to market factors $f$ as 
$$
\mathcal{A}^{f, \text{sig}} := \left\{ (\xi)_{t \in [0,T]} = (\langle \ell, \hat{\mathbb{Z}}_{0,t} \rangle)_{t \in [0,T]} \quad \bigg\vert \quad \int^T_0 \xi_s^2 ds < \infty, \quad \forall \text{ } \hat{Z}_{0,T} \in \hat{\mathcal{Z}}^f_{0,T} \text{ and } \ell \in T((\mathbb{R}^{N+d+1})^*) \right\}.
$$*





> **Remark 2.2**. *If instead we wanted to trade *endogenously* without any trading signals, we would simply take the market factors to be the null-process $\emptyset$, such that $\hat{X} = \hat{Z}$, the results would still hold.*



Now that we have defined the framework required in order to trade a signature trading strategy embedded with market factors, we can state a key result in order to combine the importance of the Hoff process in Theorem [2.10](#eq:hoff_converegence), that allows us to explicitly state the PnL of the exogenous sig-trader without the need for an integral at all.



> **Lemma 2.9**. *Let $\mathcal{Z}^{f}_{0,T} \subset K \subset C^{1-var}([0,T],\mathbb{R}^d)$ be a compact set of market factor trajectories. Then for any exogenous signature trading strategy $\xi = \phi(\hat{Z}_{0,T})$ that acts on paths in $K$ and for every $\epsilon > 0$, there exists a linear functional $\ell \in T((\mathbb{R}^{N+d+1})^*)$, such that 
> $$
> \begin{align*}
> \sup_{Z \in K} \lVert \phi(\hat{Z}_{0,T}) - \langle \ell, \hat{\mathbb{Z}}_{0,T} \rangle \rVert < \epsilon.
> \end{align*}
> $$*



**Proof.** We can see that this result follows from the universal approximation of continuous functions on paths by linear functionals acting on the signature (Theorem [A.13](#eq:universal_approx)). $\square$



> **Definition 9**. *(Trading Strategy PnL). Let $\hat{Z} = (t,X_t, f_t)$ be a market factor process with $X$ a tradable underlying process and $f$ an untradable signal process. If $\xi \in \mathcal{A}^{f,\text{sig}}$ is a linear signature trading strategy such that $\xi_t^m = \langle \ell_m, \hat{\mathbb{Z}}_{0,t} \rangle$, for each asset $m=1,\dots,d$, then we define the PnL of the signature trading strategy between time $0$ and time $T$ as 
> <a id="eq:sig_pnl"></a>
> $$
> \begin{aligned}
> V_T = \sum_{m=1}^d \int^T_0 \langle \ell_m, \hat{\mathbb{Z}}_{0,t} \rangle dX_t^m
> \end{aligned}
> $$ where the integral is understood in the Itô sense.*



It is crucial to distinguish the difference between the Itô integral used in this definition versus the Stratonovich integral in (2) of Example [A.3](#eq:example_sigs). If that integral was in fact an Itô integral then we could describe the above definition of PnL directly in terms of the add-time signature $\hat{\mathbb{Z}}_{0,t}$, however this is unfortunately not the case! So in order to develop a more friendly version of $V_T$, we require the following theorem involving the *Hoff lead-lag process* as seen in Definition [2.3](#eq:hoff_defn).



> **Theorem 2.10** *(Recovery of Itô Integral using the Hoff process, (Theorem 5.1, [[FHL16](#ref-Flint2016DiscretelyProcess)])). Let $X=(X_t)_{t \in [0,T]}$ be a stochastic process on the filtered probability space $(\Omega, \mathcal{F}, (\mathcal{F}_t)_{t \in [0,T]}, \mathbb{P})$. Suppose we observe piecewise smooth streams of $X$ that are discretely sampled over a sequence of times $\{t_i\}^N_{i=0}$. Let $\hat{X}^{LL} = (\hat{X}_{t_i}^{\textup{lead}}, \hat{X}_{t_i}^{\textup{lag}})^{2N}_{i=1}$ be the associated observed *Hoff lead-lag transform* of $\hat{X}$ as defined in Definition [2.3](#eq:hoff_defn). Let $\phi = (\phi^1, \dots, \phi^d)$ be continuous functions acting on paths of $X$, then we have that 
> $$
> \begin{align*}
> \sum_{m=1}^d \int^T_0  \phi^m(\hat{X}_t^{\textup{lag}}) d\hat{X}_t^{m, \textup{lead}} \to \int^T_0 \phi(X_t) dX_t := & \sum_{m=1}^d \int^T_0 \phi^m(X_t) dX_t^m \\
> \text{as  } & \max_{t_i, t_{i+1}} \vert t_{i+1} - t_i \vert \to 0,
> \end{align*}
> $$ in either probability or $L^p$-norm.*



**Proof.** The basic idea of the proof is that the areas between the *lead* and *lag* components of the Hoff lead-lag process, (captured by $\hat{X}^{LL}$), introduce a correction factor in the stochastic integral limit, consequently allowing us to recover the Itô, not Stratonovich, integral. $\square$ This result allows us to show that applying a function to the observed lagged path, against the observed leading path, we recover the true Itô integral against the stochastic process $X$ as the mesh size goes to zero. In this sense, we see that we are able to approximate asymptotically the true Itô integral as instead an integral of the observed, Hoff lead-lag stream.



> **Remark 2.3**. *We can clearly see the analogy with Theorem [2.10](#eq:hoff_converegence) and our definition of PnL in Definition [2.10](#eq:pnl_defn). By transforming our asset price data via the Hoff lead-lag process, now regarded as a geometric rough path, the quadratic variation of the underlying process $X$ naturally arises. The path-dependent concept of volatility has been researched extensively ([[BCD98](#ref-Breidt1998TheVolatility); [GJR14](#ref-Gatheral2014VolatilityRough); [JL20](#ref-Jacquier2020Path-dependentModels); [GL22](#ref-Guyon2022VolatilityPath-Dependent)]) and this is explicitly embedded in the second order of the signature of the Hoff process. So not only does this result allow us to capture the path-dependency of volatility, which is mostly endogenous, we can enrich this with other path-dependent market factors.*





<a id="fig:true_vs_observed_v2"></a>
<img src="images/true_vs_observed.png" />

*Distinguishing between the true stochastic process <span class="math inline"><em>X</em></span> and the discretely sampled observed process for which we define the Hoff lead-lag process.*



We can see from Figure [3](#fig:true_vs_observed_v2) that in order for Theorem [10](#eq:hoff_converegence) to hold, we require frequent sampling such that the distance between observations is small. A natural next step is to consider the case where our strategy $\xi$ is in fact a *signature trading strategy*, i.e $\xi_t^m = \langle \ell_m , \hat{\mathbb{Z}}_{0,t} \rangle$ for each asset $m=1, \dots, d$. Moreover, how can we find an expression for the PnL $V_T$ in [eq:sig_pnl](#eq:sig_pnl), in the Itô integral sense, using Theorem [2.10](#eq:hoff_converegence)? We will in fact extend this idea to a much more powerful result, under the presence of exogenous market signals.



> **Theorem 2.11** *(PnL of a $d$-asset signature trading strategy under exogenous signal)*. *Let $\hat{Z} := (t, X_t, f_t)_{t \in [0,T]}$ be the *market factor process*, where $X$ is a $d$-dimensional tradable stochastic process and $f$ is a $N$-dimensional un-tradable factor process. Let $\ell_1, \dots, \ell_d \in T((\mathbb{R}^{N+d+1})^*)$ and define our trading strategy as $\xi_t^m =  \langle \ell_m, \hat{\mathbb{Z}}_{0,t}^{< \infty} \rangle$ for $m=1,\dots, d$. Then, we have that the PnL of the strategy between time $0$ and time $T$ can be represented as 
> <a id="eq:pnl_leadlag"></a>
> $$
> \begin{aligned}
> V_T = \sum_{m = 1}^d \int^T_0 \langle \ell_m, \hat{\mathbb{Z}}_{0,t}^{< \infty} \rangle dX_t^m \approx \sum_{m = 1}^d \int^T_0 \langle \ell_m, \hat{\mathbb{Z}}_{0,t}^{\textup{lag}, < \infty} \rangle dX_t^{m,\textup{lead}} = \sum_{m = 1}^d \langle \ell_m \mathbf{f}(m), \hat{\mathbb{Z}}^{LL,<\infty}_{0,T} \rangle
> \end{aligned}
> $$ where $\mathbf{f}(m): \{1, \dots, d\} \to \mathcal{W}(A_{2(N+d+1)})$ is a shift operator which is defined as $\mathbf{f}(m) = \pi(e^*_{m+N+d+2})$ where $\pi:T((\mathbb{R}^{2(N+d+1)})^*) \to \mathcal{W}(A_{2(N+d+1)})$ the canonical isomorphism between the dual space $T((\mathbb{R}^{2(N+d+1)})^*)$ and the space of all words $\mathcal{W}(A_{2(N+d+1)})$.*



Now, due to the linearity of expectation, we are able to represent the *expected PnL* at time $T$ as the following: 
<a id="eq:exp_lead_lag_pnl"></a>
$$
\begin{aligned}
\mathbb{E}(V_T) & =  \sum_{m =1 }^d \langle \ell_m \mathbf{f}(m), \mathbb{E}( \hat{\mathbb{Z}}^{LL,<\infty}_{0,T}) \rangle.
\end{aligned}
$$ where $\mathbb{E}( \hat{\mathbb{Z}}^{LL,<\infty}_{0,T})$ is the expected signature of the Hoff lead-lag transformation of $\hat{Z}$. **Proof.** Given in Appendix [8.1](#sec:proof_of_pnl_thm). $\square$



<a id="fig:hoff_lead_lag_integral"></a>
<img src="images/hoff_ll_integral_approx.png" />

*A comparison between different approximations of the true Itô PnL.*





> **Remark 2.4**. *This result allows us to express any integral of a linear functional on the signature of a time-augmented market factor path as a newly defined linear functional on the time-augmented lead-lag market factor path instead. We must note that the authors in ([[LNA19a](#ref-Lyons2019Non-parametricDerivatives)], Lemma 3.11), construct a version in the specific case when $d=1$, $f=\emptyset$ and so $\mathbf{f}(m) = \mathbf{4}$. Here, we extend this case to allow for any exogenous market information, as well as the multi dimensionsal case for $d>1$.*





> **Remark 2.5**. *Note that $\mathbf{f}(m): \{1,\dots,d\} \to \mathcal{W}(A_{2(N+d+1)})$ is simply just the shift operator that allows any multi-index $(j_1, \dots, j_n) \in \left\{1,\dots,d \right\}^n$ for the original signature terms to be transformed into a multi-index for the signature terms of the $2(N+d+1)$-dimensional time-augmented lead-lag process.*





> **Example 2.1**. *Define the $4$-dimensional market factor process $\hat{Z}:= (t, X^1, X^2, f^1)$ for two assets and one corresponding factor. Consider the case where our signature trading strategy is truncated at level $M=2$, then the truncated expected signature, $\mathbb{E}( \hat{\mathbb{Z}}^{LL,\leq M}_{0,T})$ will have 
$$
\vert \mathcal{W}_{d+N+1}^M \vert = \vert \mathcal{W}_{4}^{2} \vert = \sum^2_{k=0} 4^k = 21
$$ terms. Notably, the 21 *words* associated with these signature terms $\mathcal{W}_{4}^{2}$ are defined as: 
$$
\mathcal{W}_{4}^{2} = \left\{ \mathbf{\emptyset}, \mathbf{0}, \mathbf{1}, \mathbf{2}, \mathbf{3}, \mathbf{00}, \mathbf{01}, \mathbf{02}, \mathbf{03}, \mathbf{10}, \mathbf{11}, \mathbf{12}, \mathbf{13}, \mathbf{20}, \mathbf{21}, \mathbf{22}, \mathbf{23}, \mathbf{30}, \mathbf{31}, \mathbf{32}, \mathbf{33} \right\}
$$ and so any linear functional associated with the truncated expected signature, $\mathbb{E}( \hat{\mathbb{Z}}^{LL,\leq M}_{0,T})$, will have at most 21 non-zero terms. We can see that if we concatenate a linear functional $\ell$ with the letter $\mathbf{f}(m)$, then, it must be applied to the truncated signature $\hat{\mathbb{Z}}^{LL,\leq M+1}_{0,T}$ and the words associated with $\ell \mathbf{f}(m)$ will be $\mathbf{wf}(m)$ where $\mathbf{w} \in \mathcal{W}_{4}^{2}$. Throughout, we will refer to terms of the truncated signature via *words* such as $\mathbf{w}, \mathbf{v} \in W_{d+N+1}^M$.*





> **Lemma 12**. *(Variance of the PnL of a signature trading strategy under exogenous signal). Let $X$ be a $d$-dimensional tradable stochastic process and let $f$ be a $N$-dimensional un-tradable factor process. Define $\hat{Z}_t := (t, X_t, f_t)$ as the *market factor process* and $\ell_1, \dots, \ell_d \in T((\mathbb{R}^{N+d+1})^*)$ and define our trading strategy as $\langle \ell_m, \hat{\mathbb{Z}}_{0,s}^{< \infty} \rangle$ for $m=1,\dots, d$. Let the expected PnL of the strategy between time $0$ and time $T$ be defined as in ([eq:exp_lead_lag_pnl](#eq:exp_lead_lag_pnl)). Then the Variance of the PnL at time $T$ is defined as 
> <a id="eq:var_pnl"></a>
> $$
> \begin{align*}
> \textup{Var}(V_T) =\sum_{m =1}^d \sum_{n=1}^d \langle \ell_m \mathbf{f}(m) \mathbin{\sqcup\mkern-3mu\sqcup} \ell_n \mathbf{f}(n), \mathbb{E}( \hat{\mathbb{Z}}^{LL}_{0,T}) \rangle -  \langle \ell_m \mathbf{f}(m), \mathbb{E}( \hat{\mathbb{Z}}^{LL}_{0,T}) \rangle \langle \ell_n \mathbf{f}(n), \mathbb{E}( \hat{\mathbb{Z}}^{LL,}_{0,T}) \rangle.
> \end{align*}
> $$ where $\mathbin{\sqcup\mkern-3mu\sqcup}$ is the shuffle product defined in Definition [A.3](#defn:shuffle_product).*



**Proof.** This results follows simply from Theorem [2.11](#thm:int_sig) and the fact that variance of a random variable is defined as $\textup{Var}(V_T) = \mathbb{E} (V_T^2) - (\mathbb{E}(V_T))^2$, where $\mathbb{E}(V_T)$ is defined in ([eq:exp_lead_lag_pnl](#eq:exp_lead_lag_pnl)) and 
<a id="eq:exp_PnL2"></a>
<a id="eq:exp_PnL3"></a>
$$
\begin{aligned}
\mathbb{E} (V_T^2) = & \sum_{m =1}^d \sum_{n =1}^d \langle \ell_m \mathbf{f}(m) \mathbin{\sqcup\mkern-3mu\sqcup} \ell_n \mathbf{f}(n), \mathbb{E}( \hat{\mathbb{Z}}^{LL}_{0,T}) \rangle \\
\mathbb{E}(V_T)^2 = & \sum_{m =1}^d \sum_{n =1}^d \langle \ell_m \mathbf{f}(m), \mathbb{E}( \hat{\mathbb{Z}}^{LL}_{0,T}) \rangle \langle \ell_n \mathbf{f}(n), \mathbb{E}( \hat{\mathbb{Z}}^{LL}_{0,T}) \rangle.
\end{aligned}
$$ $\square$

## 3 Main Result  {#sec:original}

In this section we derive our main result, which is an explicit and concise expression for the optimal signature trading strategy in the presence of exogenous market signals considering a pathwise version of the classical mean-variance criterion. Using the trading strategy expected PnL and variance of PnL as defined in Chapter [2](#sec:market_model), we show that the path-dependent mean-variance optimisation problem is convex in the weights of the linear functionals $\ell_1, \dots, \ell_d$.



> **Theorem 3.1** *(Optimal Signature Trading Strategy)*. *Denote $T \in \mathbb{N}$ the terminal time. Let $X$ be a $d$-dimensional tradable stochastic process and let $f$ be a $N$-dimensional un-tradable factor process. Define $\hat{Z}_t := (t, X_t, f_t)$ as the *market factor process*. Define a signature trading strategy $\xi_t^m$ through a linear functional on the signature of the market factor process, i.e. $\xi_t^m = \langle \ell_m, \hat{\mathbb{Z}}_{0,t} \rangle$. Then, for a given truncation level $M$, the mean-variance optimal signature trading strategy $\ell^* = (\ell_1^*,\dots,\ell_d^*),$ $\ell_m^* \in T^{(M)}((\mathbb{R}^{N+d+1})^*)$, satisfies 
> <a id="eq:constrained_optimisation"></a>
> $$
> \begin{aligned}
> \ell_m^* :=\operatorname{argmax}_{\substack{\ell_m \in T^{(M)}((\mathbb{R}^{N+d+1})^*) \\ \text{Var}(V_T)\leq \Delta}}  \sum_{m =1 }^d  \left\langle \ell_m \mathbf{f}(m), \mathbb{E}( \hat{\mathbb{Z}}^{LL,< \infty}_{0,T}) \right\rangle, \quad \forall m \in \{1,\dots,d\}
> \end{aligned}
> $$ and is given by 
> $$
> \begin{align*}
> \langle \ell_m^*, e_{ \mathbf{w}} \rangle = \frac{((\Sigma^{\textup{sig}})^{-1} \mathbf{\mu}^{\textup{sig}} )_{\mathbf{wf}(m)}}{2\lambda}, \quad m \in \{1,\dots,d\}, \mathbf{w} \in \mathcal{W}^M_{N+d+1}
> \end{align*}
> $$ where the variance-scaling parameter $\lambda$ is given by 
> $$
> \begin{align*}
> \lambda = \frac{1}{2 \sqrt{\Delta}} \left( \sum_{m=1}^d \sum_{n=1}^d \sum_{ \mathbf{w} \in \mathcal{W}_{N+d+1}^M} \sum_{ \mathbf{v} \in \mathcal{W}_{N+d+1}^M} ((\Sigma^{\textup{sig}})^{-1} \mathbf{\mu}^{\textup{sig}})_{\mathbf{wf}(m)} ((\Sigma^{\textup{sig}})^{-1} \mu^{\textup{sig}})_{\mathbf{vf}(n)} \Sigma^{\textup{sig}}_{\mathbf{wf}(m), \mathbf{vf}(n)}   \right)^{\frac{1}{2}}.
> \end{align*}
> $$ We define the "Signature PnL attribution" as the $d \cdot \vert \mathcal{W}_{N+d+1}^M \vert$-length vector $\mu^{\textup{sig}} = (\mu^{\textup{sig}}_1, \dots, \mu^{\textup{sig}}_d)^\top$ as 
> <a id="eq:mu_sig"></a>
> $$
> \begin{aligned}
> \mu^{\textup{sig}}_{\mathbf{wf}(m)} = \left\langle \mathbf{wf}(m), \mathbb{E} (\hat{\mathbb{Z}}^{LL, < \infty}_{0,T}) \right\rangle, \quad & \forall \mathbf{w} \in \mathcal{W}_{N+d+1}^M,  m \in \{1,\dots,d\}
> \end{aligned}
> $$*
>
> *and the "Signature PnL covariances" as the $d \cdot \vert \mathcal{W}_{N+d+1}^M \vert \times d \cdot \vert \mathcal{W}_{N+d+1}^M \vert$ matrix $\Sigma^{\textup{sig}}$ as 
> <a id="eq:Sigma_sig"></a>
> $$
> \begin{aligned}
> \Sigma^{\textup{sig}}_{\mathbf{wf}(m),\mathbf{vf}(n)} = \left\langle \mathbf{wf}(m) \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{vf}(n), \mathbb{E} (\hat{\mathbb{Z}}^{LL, < \infty}_{0,T}) \right\rangle - \left\langle \mathbf{wf}(m), \mathbb{E} (\hat{\mathbb{Z}}^{LL, < \infty}_{0,T}) \right\rangle \left\langle \mathbf{vf}(n), \mathbb{E} (\hat{\mathbb{Z}}^{LL, < \infty}_{0,T}) \right\rangle
> \end{aligned}
> $$*
>
> *for all $\mathbf{w},\mathbf{v} \in \mathcal{W}_{N+d+1}^M$ and $m, n \in \{1,\dots,d\}$.*



**Proof.** In order to solve the constrained optimisation problem [eq:constrained_optimisation](#eq:constrained_optimisation), we can introduce the Lagrangian 
$$
\begin{align*}
\mathcal{L} (\ell_1, \dots, \ell_d, \lambda) = \mathbb{E} (V_T) - \lambda(\text{Var}(V_T)-\Delta)
\end{align*}
$$ and we are interested in finding saddle points $\ell_1^*, \dots, \ell_d^* \in T^{(M)}((\mathbb{R}^{N+d+1})^*), \lambda^0 \in \mathbb{R}$ that satisfy $\nabla \mathcal{L}(\ell_1^*, \dots, \ell_d^*, \lambda) = 0$. For this purpose recall Theorem [2.11](#thm:int_sig), where the expected terminal PnL is given by [eq:exp_lead_lag_pnl](#eq:exp_lead_lag_pnl). Furthermore, we can decompose the variance of the terminal PnL, given in equations ([eq:exp_PnL2](#eq:exp_PnL2)) and ([eq:exp_PnL2](#eq:exp_PnL2)). Next, we can compute for each asset $m \in \{1,\dots,d\}$ and each word $\mathbf{w} \in \mathcal{W}_{N+d+1}^M$, the gradients of [eq:exp_lead_lag_pnl](#eq:exp_lead_lag_pnl), [eq:exp_PnL2](#eq:exp_PnL2) and [eq:exp_PnL3](#eq:exp_PnL3) with respect to $\langle \ell_m, e_{\mathbf{w}} \rangle$ 
$$
\begin{align*}
\frac{\partial \mathbb{E} (V_T)}{\partial \langle \ell_m, e_{\mathbf{w}} \rangle}  & = \langle \mathbf{wf}(m), \mathbb{E} (\hat{\mathbb{Z}}^{LL,<\infty}_{0,T})\rangle \\
\frac{\partial \mathbb{E} (V_T^2)}{\partial \langle \ell_m, e_{\mathbf{w}} \rangle} & = 2 \sum_{n=1}^d \sum_{\mathbf{v} \in \mathcal{W}_{N+d+1}^M} \langle \ell_n, e_{\mathbf{v}} \rangle \langle \mathbf{wf}(m) \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{vf}(n), \mathbb{E} (\hat{\mathbb{Z}}^{LL,<\infty}_{0,T}) \rangle
\\
\frac{\partial \mathbb{E} (V_T)^2}{\partial \langle \ell_m, e_{\mathbf{w}} \rangle} & = 2 \sum_{n=1}^d \sum_{\mathbf{v} \in \mathcal{W}_{N+d+1}^M}  \langle \ell_n, e_{\mathbf{v}} \rangle \langle \mathbf{wf}(m), \mathbb{E} (\hat{\mathbb{Z}}^{LL,<\infty}_{0,T}) \rangle  \langle \mathbf{vf}(n), \mathbb{E} (\hat{\mathbb{Z}}^{LL,<\infty}_{0,T}) \rangle
\end{align*}
$$ Using these computed gradients, we can compute the gradient of the Lagrangian with respect to $\langle \ell_m, e_{\mathbf{w}} \rangle$ 
$$
\begin{align*}
\frac{\partial \mathcal{L} (\ell_1, \dots, \ell_d, \lambda)}{\partial \langle  \ell_m, e_{\mathbf{w}} \rangle} = \langle \mathbf{wf}(m), b \rangle - 2\lambda \sum_{n=1}^d \sum_{\mathbf{v} \in \mathcal{W}_{N+d+1}^M} \langle \ell_n, e_{\mathbf{v}} \rangle \Sigma^{\textup{sig}}_{\mathbf{wf}(m), \mathbf{vf}(n)}
\end{align*}
$$ where we define $\mu^{\textup{sig}} = (\mu^{\textup{sig}}_1, \dots, \mu^{\textup{sig}}_d)^\top$ as 
$$
\begin{align*}
\mu^{\textup{sig}}_{\mathbf{wf}(m)} = \langle \mathbf{wf}(m), \mathbb{E} (\hat{\mathbb{Z}}^{LL, < \infty}_{0,T}) \rangle, \quad & \forall \mathbf{w} \in \mathcal{W}_{N+d+1}^M,  m \in \{1,\dots,d\}
\end{align*}
$$ and the matrix $\Sigma^{\textup{sig}}$ as 
$$
\begin{align*}
\Sigma^{\textup{sig}}_{\mathbf{wf}(m),\mathbf{vf}(n)} = \langle \mathbf{wf}(m) \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{vf}(n), \mathbb{E} (\hat{\mathbb{Z}}^{LL, < \infty}_{0,T}) \rangle - \langle \mathbf{wf}(m), \mathbb{E} (\hat{\mathbb{Z}}^{LL, < \infty}_{0,T}) \rangle \langle \mathbf{vf}(n), \mathbb{E} (\hat{\mathbb{Z}}^{LL, < \infty}_{0,T}) \rangle
\end{align*}
$$ for all $\mathbf{w},\mathbf{v} \in \mathcal{W}_{N+d+1}^M$ and $m, n \in \{1,\dots,d\}$.

Using the first order conditions, observe that we obtain the system of linear equations 
<a id="eq:system"></a>
$$
\begin{aligned}
\mu^{\textup{sig}}_{\mathbf{wf}(m)} = 2 \lambda \sum_{n=1}^d \sum_{ \mathbf{v} \in \mathcal{W}_{N+d+1}^M} \langle \ell_n, e_{ \mathbf{v}} \rangle \Sigma^{\textup{sig}}_{\mathbf{wf}(m), \mathbf{vf}(n)}, m \in \{1,\dots,d \}, \mathbf{w} \in \mathcal{W}_{N+d+1}^M.
\end{aligned}
$$ Under truncation, we find that [eq:system](#eq:system) is a system of 
$$
\begin{align*}
d_M & = \vert I \vert \cdot \vert \mathcal{W}_{N+d+1}^M \vert \\
& = d \sum_{k=0}^M (N+d+1)^k \\
& =  (N+d+1)^{M+1} - 1
\end{align*}
$$ equations and $d_M$ unknowns. Hence, assuming that $\Sigma^{\textup{sig}}$ is invertible, we can solve [eq:system](#eq:system) and obtain for $m \in \{1,\dots,d \}, \mathbf{w} \in \mathcal{W}^M_{N+d+1}$ 
<a id="eq:solution"></a>
$$
\begin{aligned}
\langle \ell_m^*, e_{ \mathbf{w}} \rangle = \frac{((\Sigma^{\textup{sig}})^{-1} \mu^{\textup{sig}} )_{\mathbf{wf}(m)}}{2\lambda}
\end{aligned}
$$ where we assumed by complementary slackness (KKT) that $\lambda \neq 0$. We can then substitute [eq:solution](#eq:solution) into the variance constraint to obtain two solutions for $\lambda$ 
$$
\begin{align*}
\lambda_\pm = & \pm \frac{1}{2 \sqrt{\Delta}} \left( \sum_{m=1}^d \sum_{n=1}^d \sum_{ \mathbf{w} \in \mathcal{W}_{N+d+1}^M} \sum_{ \mathbf{v} \in \mathcal{W}_{N+d+1}^M} \langle \ell_m, e_{\mathbf{w}} \rangle \langle \ell_n, e_{\mathbf{v}} \rangle \Sigma^{\textup{sig}}_{\mathbf{wf}(m), \mathbf{vf}(n)}  \right)^{\frac{1}{2}} \\
= & \pm \frac{1}{2 \sqrt{\Delta}} \left( \sum_{m=1}^d \sum_{n=1}^d \sum_{ \mathbf{w} \in \mathcal{W}_{N+d+1}^M} \sum_{ \mathbf{v} \in \mathcal{W}_{N+d+1}^M} ((\Sigma^{\textup{sig}})^{-1} \mu^{\textup{sig}})_{\mathbf{wf}(m)} ((\Sigma^{\textup{sig}})^{-1} \mu^{\textup{sig}})_{\mathbf{vf}(n)} \Sigma^{\textup{sig}}_{\mathbf{wf}(m), \mathbf{vf}(n)}   \right)^{\frac{1}{2}}
\end{align*}
$$ Hence, we obtain the solution 
$$
\begin{align*}
\langle \ell_m^*, e_{\mathbf{w}} \rangle = \frac{(\Delta)^{\frac{1}{2}}((\Sigma^{\textup{sig}})^{-1} \mu^{\textup{sig}})_{\mathbf{wf}(m)}}{\left( \sum\limits_{m,n \in \{1,\dots,d\}} \sum\limits_{\mathbf{w},\mathbf{v} \in W_{N+d+1}^N} ((\Sigma^{\textup{sig}})^{-1} \mu^{\textup{sig}})_{\mathbf{wf}(m)} ((\Sigma^{\textup{sig}})^{-1} \mu^{\textup{sig}})_{\mathbf{vf}(n)} \Sigma^{\textup{sig}}_{\mathbf{wf}(m), \mathbf{vf}(n)} \right)^{\frac{1}{2}}}\text{ }
\end{align*}
$$ for $m \in \{ 1, \dots, d \}, \mathbf{w} \in \mathcal{W}^M_{N+d+1}$. $\square$ In the remainder of this section we first give an example how the main theorem can be used and then proceed to draw a parallel to the classical case and explain how our theorem extends classical formulas to the path-dependent case.



> **Remark 3.1**. *The matrix $\Sigma^{\textup{sig}}$ and vector $\mu^{\textup{sig}}$ are just placeholders for different terms and combinations of $\mathbb{E} (\hat{\mathbb{Z}}^{LL,<\infty}_{0,T})$. Hence, all we need in order to know what our optimal functional is, is the expected Hoff lead-lag signature, and this is straightforward to compute for reasonable orders of truncation and number of assets and factors. The following example aims to provide some practical intuition behind how the optimal strategy is calculated and the relation between the signature and words on the tensor algebra.*





> **Example 3.1**. *Let us consider the case of when we have two assets $X = (X^1, X^2)$, one factor $f$, such that $d=2$, $N=1$. Then we define the 4-dimensional market factor process $\hat{Z}:= (t,X,f)$.*
>
> *Let us fix the truncation level to be $M=2$. We remark that Example [1](#ex:word_example) is of the same form, and so the 2nd level truncated signature $\mathbb{Z}_{0,t}^{\leq 2}$ has $\vert \mathcal{W}^2_{4} \vert = 21$ terms, namely the associated words are: 
> <a id="eq:words_ex"></a>
> $$
> \begin{aligned}
> \mathcal{W}_{4}^{2} = \left\{ \mathbf{\emptyset}, \mathbf{0}, \mathbf{1}, \mathbf{2}, \mathbf{3}, \mathbf{00}, \mathbf{01}, \mathbf{02}, \mathbf{03}, \mathbf{10}, \mathbf{11}, \mathbf{12}, \mathbf{13}, \mathbf{20}, \mathbf{21}, \mathbf{22}, \mathbf{23}, \mathbf{30}, \mathbf{31}, \mathbf{32}, \mathbf{33} \right\}
> \end{aligned}
> $$*



Hence, the optimal linear signature trading strategy will correspond to two linear functionals (one for each asset) $\ell_1, \ell_2$, each of length 21, defined as 
$$
\begin{align*}
\xi_t^1 &= \langle \ell_1, \hat{\mathbb{Z}}_{0,t}^{\leq 2} \rangle \\
\xi_t^2 &= \langle \ell_2, \hat{\mathbb{Z}}_{0,t}^{\leq 2} \rangle
\end{align*}
$$

In the above theorem, we can see the vector $\mu^{\textup{sig}} = (\mu^{\textup{sig}}_1, \mu^{\textup{sig}}_2)$ will be defined as follows: 
$$
\mu^{\textup{sig}} := \left\{\mathbb{E} \left(\hat{\mathbb{Z}}_{\mathbf{w f}(m)}^{LL, \leq 3} \right)\right\}_{\mathbf{w} \in \mathcal{W}^2_{4}, m=1,2}.
$$ Hence, $\mu^{\textup{sig}}$ will be a $d \cdot \vert \mathcal{W}^M_{N+d+1} \vert = 2 \times 21 = 42$ length vector, containing elements of the expected lead-lag signature of order 3.

Recall that the shift operator $\mathbf{f}(m)$ is defined for each asset $m=1,2$ as: 
$$
\begin{align*}
\mathbf{f}(1) & = \mathbf{5} \\
\mathbf{f}(2) & = \mathbf{6}.
\end{align*}
$$ which correspond to the 5th and 6th dimensions of the lead-lag process. Hence, we see that $\mu^{\textup{sig}}_1$ contains the expected lead-lag signature terms corresponding to the index of words 
$$
I_1 := \left\{ \mathbf{5}, \mathbf{05}, \mathbf{15}, \mathbf{25}, \mathbf{35}, \mathbf{005}, \mathbf{015}, \mathbf{025}, \mathbf{035}, \mathbf{105}, \mathbf{115}, \mathbf{125}, \mathbf{135}, \mathbf{205}, \mathbf{215}, \mathbf{225}, \mathbf{235}, \mathbf{305}, \mathbf{315}, \mathbf{325}, \mathbf{335} \right\}
$$ and $\mu^{\textup{sig}}_2$ contains the expected lead-lag signature terms corresponding to the index of words 
$$
I_2 := \left\{ \mathbf{6}, \mathbf{06}, \mathbf{16}, \mathbf{26}, \mathbf{36}, \mathbf{006}, \mathbf{016}, \mathbf{026}, \mathbf{036}, \mathbf{106}, \mathbf{116}, \mathbf{126}, \mathbf{136}, \mathbf{206}, \mathbf{216}, \mathbf{226}, \mathbf{236}, \mathbf{306}, \mathbf{316}, \mathbf{326}, \mathbf{336} \right\},
$$ such that we have: 
$$
\begin{align*}
\mu^{\textup{sig}} =
\begin{bmatrix}
\left\langle \mathbf{5}, \mathbb{E} \left(\hat{\mathbb{Z}}^{LL, \leq 3} \right) \right\rangle \\
\vdots \\
\left\langle \mathbf{335}, \mathbb{E} \left(\hat{\mathbb{Z}}^{LL, \leq 3} \right) \right\rangle \\
\left\langle \mathbf{6}, \mathbb{E} \left(\hat{\mathbb{Z}}^{LL, \leq 3} \right) \right\rangle \\
\vdots \\
\left\langle \mathbf{336}, \mathbb{E} \left(\hat{\mathbb{Z}}^{LL, \leq 3} \right) \right\rangle
\end{bmatrix}
\Bigg\} \text{ 42 elements}
\end{align*}
$$ Intuitively, we can think of each element of $\mu^{\textup{sig}}$ as the expected *attribution* that each signature term has to a given assets future returns. For example, consider the term of the signature corresponding to the word $\mathbf{3}$, i.e $\langle \mathbf{3}, \hat{\mathbb{Z}}^{\leq 2} \rangle$, which corresponds to the increments of the factor signal, i.e 
$$
\langle \mathbf{3}, \hat{\mathbb{Z}}^{\leq 2}_{0,T} \rangle = \int^T_0 \circ dZ^3_t
$$ Then the expected *attribution* that this has on the increment of asset 1, can be defined as 
$$
\mathbb{E} \left( \int^T_0 \langle \mathbf{3}, \hat{\mathbb{Z}}^{\leq 2}_{0,t} \rangle dX^1_t \right) = \left \langle \mathbf{3f}(1), \mathbb{E} \left( \hat{\mathbb{Z}}^{LL,\leq 3}_{0,T} \right) \right\rangle = \left \langle \mathbf{35}, \mathbb{E} \left(  \hat{\mathbb{Z}}^{LL,\leq 3}_{0,T} \right) \right\rangle = \mu^{\textup{sig}}_{\mathbf{35}},
$$ therefore the vector $\mu^{\textup{sig}}$ consists of expected PnL attribution for each of the 21 terms of the signature of the factor process that we observe.

Now, we consider the $42 \times 42$ matrix $\Sigma^{\textup{sig}}$, defined element-wise as 
$$
\begin{align*}
\Sigma^{\textup{sig}}_{\mathbf{wf}(m),\mathbf{vf}(n)} = \left\langle \mathbf{wf}(m) \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{vf}(n), \mathbb{E} (\hat{\mathbb{Z}}^{LL, < \infty}_{0,T}) \right\rangle - \left\langle \mathbf{wf}(m), \mathbb{E} (\hat{\mathbb{Z}}^{LL, < \infty}_{0,T}) \right\rangle \left\langle \mathbf{vf}(n), \mathbb{E} (\hat{\mathbb{Z}}^{LL, < \infty}_{0,T}) \right\rangle
\end{align*}
$$ for all $\mathbf{w},\mathbf{v} \in \mathcal{W}_{4}^2$ and $m, n =1,2$.

Each element of this matrix represents a covariance term between the PnL *attributions* that we discussed previously. For example, let us observe an arbitrary element of $\Sigma^{\textup{sig}}$. Let $w = \mathbf{01}, \mathbf{v} = \mathbf{23}, m=1, n=2$. Then $\mathbf{wf}(m) = \mathbf{015}, \mathbf{vf}(n) = \mathbf{236}$ and the corresponding element in the matrix is given as 
$$
\Sigma^{\textup{sig}}_{\mathbf{015},\mathbf{236}} = \left\langle \mathbf{015} \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{236}, \mathbb{E} (\hat{\mathbb{Z}}^{LL, \leq 6}_{0,T}) \right\rangle - \left\langle \mathbf{015}, \mathbb{E} (\hat{\mathbb{Z}}^{LL, \leq 3}_{0,T}) \right\rangle \left\langle \mathbf{236}, \mathbb{E} (\hat{\mathbb{Z}}^{LL, \leq 3}_{0,T}) \right\rangle
$$ where $\mathbf{015} \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{236}$ is a sum of 20 different words in $\mathcal{W}_4^6$. We refer the reader also to Example [4](#ex:shuffle_ex) for another example of the shuffle product. It is evident that, while our linear functional is only applied to the second order truncated signature, we require the sixth order signature in order to compute the covariance matrix, which can cause a computational bottleneck in practice.

Piecing this altogether, to obtain our optimal solution $\ell^* = (\ell_1^*, \ell_2^*)$, we have 
$$
\begin{align*}
\ell^* = (\Sigma^{\textup{sig}})^{-1} \mu^{\textup{sig}}
\end{align*}
$$ of which we obtain a 42-dimensional vector $\ell^*$ consisting of two length 21 vectors $\ell_1^*, \ell_2^*$. We can then compute the trading strategy, for each time $t$, as 
$$
\begin{align*}
\xi_t^1 &= \langle \ell_1^*, \hat{\mathbb{Z}}_{0,t}^{\leq 2} \rangle \\
\xi_t^2 &= \langle \ell_2^*, \hat{\mathbb{Z}}_{0,t}^{\leq 2} \rangle.
\end{align*}
$$ Note also how we can explicitly calculate the expected PnL and variance of the portfolio explicitly in this framework. Let $\ell$ be the 42-length vector $\ell = (\ell_1^*, \ell_2^*)$, then we have 
$$
\begin{align*}
\mathbb{E}(V_T) &= \ell^\top \mu^{\textup{sig}} \\
\textup{Var}(V_T) &= \ell^\top \Sigma^{\textup{sig}} \ell.
\end{align*}
$$

### 2.2 Sig-Factor Model vs Classical Factor Model

Since $\hat{Z}$ is embedded with market factors $f$, the expected lead-lag signature $\mathbb{E} (\hat{\mathbb{Z}}^{LL,<\infty}_{0,T})$ will contain a wealth of path-dependent characteristics about our assets and how they are driven by the past price trajectory and the past trajectory of the market factors. At this point, we observe this solution is analogous is to the classical framing of an optimal factor model under the mean-variance framework, seen in [eq:factor_model_predict](#eq:factor_model_predict) and [eq:mean_var_sol](#eq:mean_var_sol). In the classical factor model framework, for $N$ factors $f = f^1, \dots, f^N$, to obtain the the $m$-th asset position at time $t$, $\pi_t^m$, we have 
<a id="eq:factor_lin_functional"></a>
$$
\begin{aligned}
\pi_t^m = &  \left\langle \frac{1}{\lambda} (\Sigma^{-1} B)_m , f_t \right\rangle \\
= &  \left\langle \beta_m , f_t \right\rangle
\end{aligned}
$$ where $(\Sigma^{-1} B)_m$ is the $m$-th row of the $d \times N$ matrix $\Sigma^{-1} B$. Therefore $\beta_m := \frac{1}{\lambda} (\Sigma_t^{-1} B)_m$ represents a risk-weighted transformation of the coefficients used in the prediction step. This sequence of $N$ coefficients are then applied to the factors via an inner product to obtain the position for the $m$-th asset, $\pi_t^m \in \mathbb{R}$. We can see just how similar this example is to the sig-factor model. 
<a id="eq:sig_factor_lin_functional"></a>
$$
\begin{align*}
\xi_t^m = & \left\langle \frac{1}{2\lambda} ((\Sigma^{\textup{sig}})^{-1} \mu^{\textup{sig}})_m, \hat{\mathbb{Z}}_{0,t} \right\rangle \\
= &  \left\langle \ell_m , \hat{\mathbb{Z}}_{0,t} \right\rangle
\end{align*}
$$ Here, we have that the vector $\mu^{\textup{sig}}$ consists of the expected lead-lag signature PnL terms, for all $\vert \mathcal{W}_{N+d+1}^M \vert$ terms in the $M$-th order truncated signature that end in the letter $\mathbf{f}(m)$, i.e.. 
$$
\mu^{\textup{sig}} = \left\{\mathbb{E} \left(\hat{\mathbb{Z}}_{\mathbf{w f}(m)}^{LL, <\infty} \right)\right\}_{\mathbf{w} \in \mathcal{W}^M_{N+d+1}, m\in \{1,\dots,d\}}.
$$ and so the linear functional $\ell_m$ is a risk-adjusted weighting of coefficients that are applied to the signature terms. A sensible question now to ask is - would we produce the same portfolio if the factors $f = f^1, \dots, f^N$ in [eq:factor_lin_functional](#eq:factor_lin_functional) were the terms of the signature? In this case, the answer is no. The sole reason for this is due to the *prediction* phase in the classical factor model which induces asymmetric errors that are compounded when applied to the covariance matrix, and subsequently observed factors at time $t$, meaning the linear functionals $\beta_m$ and $\ell_m$ would not be the same.



<a id="fig:classic_factor_model"></a>
<img src="images/classic_factor_model_architecture.png" />

*Classical Factor Model*





<a id="fig:sig_factor_model"></a>
<img src="images/sig_factor_model_architecture_v3.png" />

*Sig-Factor Model*



Due to powerful results from rough path theory, we are able able to bypass the prediction phase by lifting and projecting our market factor process into a much higher dimensional space. Using Theorem [eq:exp_lead_lag_pnl](#eq:exp_lead_lag_pnl), we can express the expected future PnL as a linear functional on the expected Hoff lead-lag signature and then perform the optimisation [eq:constrained_optimisation](#eq:constrained_optimisation) in this much higher-dimensional space, without inducing any errors originating from a least-squares regression.

### 3.2 Optimal Static Portfolio

By design, a *Signature Trading Strategy*, $\xi_t = \langle \ell, \hat{\mathbb{Z}}_{0,t} \rangle$, is a dynamic strategy that continuously updates its position at time $t$, depending on the value of $\hat{\mathbb{Z}}_{0,t}$. However, we recall that the signature is defined at each level as 
$$
\hat{\mathbb{Z}}_{0,t} = (1, \hat{\mathbb{Z}}_{0,t}^1, \dots, \hat{\mathbb{Z}}_{0,t}^N, \dots)
$$ where the $k$-th level has $d^k$ elements. We observe that in fact the zero-th level of the signature is equal to 1, and so if we choose to only trade depending on this level of the signature, any linear functional $\ell$ applied to 1, will just return a static position for all time $t \in [0,T]$. Therefore, for a $d$-asset portfolio, we obtain 
$$
\begin{align*}
\xi_t^1 & = \langle \ell_1, 1 \rangle = \ell_1 \in \mathbb{R}, \quad \forall t \in [0,T] \\
\vdots &  \\
\xi_t^d & = \langle \ell_d, 1 \rangle = \ell_d \in \mathbb{R}, \quad \forall t \in [0,T].
\end{align*}
$$ Using Theorem [13](#thm:orig_solution), we have that $\ell = (\ell_1, \dots, \ell_d) \in \mathbb{R}^d$, where 
$$
\ell = \frac{1}{2\lambda} (\Sigma^{\textup{sig}})^{-1} \mu^{\textup{sig}}.
$$ Since we are trading with respect to the zero-th order of the signature, then the only word $\mathbf{w}$ that we are interested in is $\mathbf{w} = \mathbf{\emptyset}$, therefore the number of words in our linear functional is $\vert \mathcal{W}_{N+d+1}^0 \vert = 1$. Hence, we can define the $d$-dimensional vector 
$$
\begin{align*}
\mu^{\textup{sig}}_{\mathbf{wf}(m)} & = \left\langle \mathbf{wf}(m), \mathbb{E} (\hat{\mathbb{Z}}^{LL, < \infty}_{0,T}) \right\rangle, \quad \forall \mathbf{w} \in \mathcal{W}_{N+d+1}^0,  m \in \{1,\dots,d\} \\
& = \left\langle \mathbf{f}(m), \mathbb{E} (\hat{\mathbb{Z}}^{LL, \leq 1}_{0,T})\right\rangle, \quad  m \in \{1,\dots,d\}.
\end{align*}
$$ We can observe that in fact, the elements of the $d$-dimensional vector $\mu^{\textup{sig}}$ are simply the expected returns of each asset, i.e. for element corresponding to the $m$-th asset, 
$$
\mu^{\textup{sig}}_m = \left\langle \mathbf{f}(m), \mathbb{E} (\hat{\mathbb{Z}}^{LL, \leq 1}_{0,T})\right\rangle = \mathbb{E} \left( \int^T_0 dX_t^m \right) = \mathbb{E}(X_T^m) - \mathbb{E}(X_0^m).
$$ Therefore, we have 
$$
\begin{align*}
\mu^{\textup{sig}} =
\begin{bmatrix}
\mathbb{E}(X_T^1) - \mathbb{E}(X_0^1) \\
\vdots \\
\mathbb{E}(X_T^d) - \mathbb{E}(X_0^d)
\end{bmatrix}
\end{align*}
$$ which corresponds to the expected returns vector. Likewise, we obtain the $d \times d$ matrix $\Sigma^{\textup{sig}}$ as 
$$
\begin{align*}
\Sigma^{\textup{sig}}_{m,n} = \left\langle \mathbf{f}(m) \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{f}(n), \mathbb{E} (\hat{\mathbb{Z}}^{LL, \leq 2}_{0,T}) \right\rangle - \left\langle \mathbf{f}(m), \mathbb{E} (\hat{\mathbb{Z}}^{LL,  \leq 1}_{0,T}) \right\rangle \left\langle \mathbf{f}(n), \mathbb{E} (\hat{\mathbb{Z}}^{LL,  \leq 1}_{0,T}) \right\rangle,
\end{align*}
$$ which naturally corresponds to the covariance matrix of the returns for each of the $d$ assets.

We can see how this solution will in fact yield us the same results as the classical Markowitz portfolio, provided we use the same historical period to calculate the expected returns and covariances, of which we provide further evidence by constructing the Sig-Factor Model extension of the efficient frontier.

### 2.2 Sig-Factor Model Efficient Frontier

In Modern Portfolio Theory (MPT), first introduced in [[Mar52](#ref-Markowitz1952PortfolioSelection)], the mean-variance optimal portfolio can be represented via the efficient frontier, which contains all portfolios that have the maximal Sharpe ratio. In the Sig-factor model, we can also obtain an efficient frontier that represents the relationship between expected returns and variance. For a given signature trading strategy $\xi_t^m = (\xi_t^1, \dots, \xi_t^d)$, where $\xi_t^m = \langle \ell_m, \hat{\mathbb{Z}}_{0,t} \rangle$, we can explicitly define the expected PnL and variance of our portfolio in terms of the matrix $\Sigma^{\textup{sig}}$ and vector $\mu^{\textup{sig}}$, as defined in Theorem [13](#thm:orig_solution), e.g we have 
$$
\begin{align*}
\mathbb{E}(V_T) &= \ell^\top \mu^{\textup{sig}} \\
\textup{Var}(V_T) &= \ell^\top \Sigma^{\textup{sig}} \ell.
\end{align*}
$$ Therefore, for any linear functional $\ell$, we can observe the expected PnL and variance corresponding to it.



<a id="fig:sig_frontier"></a>
<img src="images/sig_frontier_v2.png" />

*Sig-Factor Model Efficient Frontier for 3-asset portfolio of ETFs DBC/BND/VTI.*



In Figure [7](#fig:sig_frontier), the LHS represents the level-3 Sig-trader efficient frontier curve for a portfolio consisting of the ETFs DBC/BND/VTI. This demonstrates the relationship between portfolio returns and variance, just as Markowitz had posed. The orange circle corresponds to the mean-variance optimal sig-trading strategy $\ell^*$ for a given maximum variance $\Delta$, according to the solution provided in Theorem [13](#thm:orig_solution). Each of the smaller dots then represent different choices of linear functional $l$, that are perturbations of the original strategy. We clearly observe that the Sig-trader portfolio maximises the risk-adjusted return (Sharpe ratio), for a given level of risk, $\Delta$.

On the RHS, we observe the efficient frontier curve for different orders of Sig-trader, between levels 0 to 3. Firstly, as eluded to previously, we can observe that the zero-th order Sig-trader is in fact identical to the static Markowitz portfolio, meaning that their frontier curves are not distinguishable from one another. We can also observe the improvement that is made to our expected returns, as we introduce more levels of the signature. This shouldn't be a surprise, as we know that more information about the dynamics is explained as we increase the level of truncation, which suggests that non-linear dependency structures are drivers of the future asset returns.

## 4 Implementation {#sec:implement}

Throughout this work, we use the package [`signatory`](https://github.com/patrick-kidger/signatory) ([[KL21](#ref-Kidger2021Signatory:GPU)]), alongside `PyTorch` for calculating and performing functionality related to tensors and the signature transform. Other packages offering signature computation include [`esig`](https://github.com/datasig-ac-uk/esig) and [`iisignature`](https://github.com/bottler/iisignature). The mean-variance Sig-Trading framework is very simple to implement and does not require heavy machinery while comparative machine learning methods may require extensive network building and hyperparameter tuning for every time the user wants to perform a new optimisation. Signature-trading is a one-model-fits-all type framework that is flexible enough to adapt to different types of signal and underlying asset process. The algorithm to find an optimal trading strategy can be found in Algorithm [alg:algo1](#alg:algo1).

The method is also self-contained in the sense that it requires no user inputted assumptions such as expected returns or covariances and that they are inferred along with characteristics of the whole process within the algorithm itself. Once a linear functional $\ell$ is obtained from past data samples it is straightforward to unravel this into an implementable trading strategy characterised by the number of units to buy/sell at each time point $t \in [0,T]$. Since the strategy is dynamic, as new data arrives the Sig-Trader will continuously compute the signature and update their position accordingly.

Whilst Sig-Trading is data driven and does not require direct probabilistic assumptions on the underlying model, just like most frameworks, there is versatility when deploying Sig-Trading in practice as there does still remain quantities that need reliably estimating in the fitting procedure. The expected lead-lag signature could be noisy when calibrated through time and so we leave any questions of robustness (with respect to the fitting procedure) to future ongoing extensions of this project, as there remains question marks over how well defined such a solution is, especially in the context of rapidly changing regimes such as in financial markets. In step (4) of Algorithm [alg:algo1](#alg:algo1), we suggest taking a Monte Carlo approach by calculating the empirical expected lead-lag signature, such that $\mathbb{E} (\hat{\mathbb{Z}}^{LL,\leq N}) = \frac{1}{M} \sum_{i=1}^M \hat{\mathbb{Z}}^{LL,\leq N}_{t \in [0,T]}$. However, there remains a multitude of alternative ways to approach this for some given sample/fitting data, such as cross validation techniques, in order to ensure robustness out of sample. This paper does not directly discuss these approaches but we do point out that any traders favourite statistical estimation and training procedures can work in this setting. It may be that more recent training data is more important for fitting and this may be incorporated via a rolling fitted model - but this may lead to overfitting. Hence, in this paper we leave such statistical procedures directly to the discretion of the user and instead provide a framework in which such techniques can be ensembled.

Likewise, while signature trading strategies do a good job of drawdown control, we do not discuss extra practicalities such as vol-scaling positions in this paper. Due to the nested nature of filtrations in this work (i.e. we are in possession of strictly increasing amounts of information through time), this may impact performance of a trading strategy differently through the life of the trade, hence it would make practical sense to smoothe out Sig-Trading positions through time - this also can reduce any bias that may arise from the exact start date of the trade. We also suggest that, especially at higher frequencies, that we could replace time-augmentation with *volume-augmentation* since this is still a monotonically increasing channel in the process (ensuring the signature remains unique), but represents a new notion of time.

## 5 Numerical Results {#sec:results}

Throughout this section, we aim to demonstrate and highlight some of the capabilities of the Sig-Trading framework, incorporating path-dependencies and exogenous signals.

### 5.1 Synthetic Data

#### 5.1.1 Pairs Trading

First, we explore the scenario in which we have no exogenous trading signal to enrich our trading strategy but we only have access to the underlying time series of the asset process. The true advantage that data-driven methods have over classical parametric frameworks is that they can exploit the inefficiencies present in financial time series data, without specifying the explicit dynamics that they are trying to capture. In this toy example, we aim to isolate one specific aspect that is exhibited by time series data and highlight how the Sig-Trader exploits it. *Pairs Trading* is one of the most famous and original active trading strategies deployed by investors that focuses on trading the joint behaviour between two assets. The sentiment is that while both assets have their own dynamics, the difference (spread) between the prices of the two assets should hold some predictability on future (co-)movements. Classical literature focuses on modelling this relationship using a mean-reverting process such as an Ornstein-Uhlenbeck process. The strategy should then contain a *buy signal* when the spread falls below some threshold and a *sell signal* when the spread is above the threshold, in the anticipation that this spread should converge back to the threshold. More on mean-reversion strategies can be found in [[AD02](#ref-Alexander2002TheStrategies); [Vid04](#ref-Vidyamurthy2004PairsAnalysis); [MPW08](#ref-Mudchanatongsuk2008OptimalApproach); [CJ15](#ref-Cartea2015AlgorithmicAssets); [LL15](#ref-Leung2015OptimalExit)].

In this experiment we take two assets such that 
$$
\begin{align*}
dX_t & =  \sigma^X dW^X_t \\
dY_t & =  \kappa (X_t - Y_t) dt + \sigma^Y dW^Y_t
\end{align*}
$$ Where $X$ is a standard arithmetic Brownian motion with zero drift and volatility $\sigma^X$. $Y$ however is modelled as a mean-reverting process where its drift is proportional to the spread between $X$ and $Y$. We can clearly see in this toy example that the only exploitable *alpha* within the framework is the temporal dependence through mean-reversion in $Y$ since there is no long term drift in $X$ or $Y$.



<a id="fig:sim_pair_trade"></a>
<img src="images/toy_sharpes_frontier_v2.png" />

*Sharpe ratio distribution (LHS) and Sig-Trader strategy as a function of the spread between the two assets (RHS).*



If a trader was to deploy a static buy and hold strategy here, the PnL would be zero on average, however, for higher order Sig-Traders, it is possible to exploit the mean-reversion dynamics. In fact, this example demonstrates how the above-mentioned *alpha* is self-contained within the 1st level of the signature (which is the increment of the path, or the 'drift') and so orders of $N \geq 2$ do not contain any more predictive power on excess returns than that of $N=1$. However, on the right hand side (RHS) of Figure [8](#fig:sim_pair_trade), the signature efficient frontier illustrates that when trading with a weekly look-forward horizon, the ratio of return to variance of weekly PnL is greater as we increase the order of the Sig-Trader. This is due to the higher levels of the signature capturing non-linear path-dependencies that can help reduce variance in the weekly PnL distribution. We relate back to Figure [1](#fig:dynamic_strategy) to demonstrate that in fact higher order Sig-Traders are able to construct mean-reverting strategies that naturally limit drawdowns, which are an inherently path-dependent characteristic.

In this synthetic example, we compare the Sig-Trader strategy to that of the original factor model. The generic factor model is set up as a supervised linear regression on future returns, as a function of the current signature, 
$$
\begin{align*}
\mu_{t+1} = \mathbb{E} [ r_{t+1} \vert \mathcal{F}_t ] = B \mathcal{S}_t + \varepsilon_{t+1}
\end{align*}
$$ where $r$ is the $2$-dimensional asset returns, $B$ is a $2 \times N$ matrix of factor coefficients, $\mathcal{S}_t$ is a vector of the signature values of the and $\varepsilon$ is a vector of the $2$ assets' (unexplained) residuals returns. We can see that this model uses the same input as the Sig-Trader (the signature), with the same tools (applying a linear function).



<a id="fig:sim_pair_positions"></a>
<img src="images/synthetic_toy_positions_v2.png" />

*Comparison between the Markowitz Order 3 factor model positions and the corresponding Sig Trader positions, for orders 1,2,3.*



The key distinguishment is that the factor model is optimal for maximising the daily mean-variance PnL profile, which ignores any long term, pathwise dynamics of the strategy itself. Figure [9](#fig:sim_pair_positions) demonstrates the difference in nature between the Sig-Trader and the factor model. In the order 1 case, as described above, the exploitable alpha in terms of returns are captured by the 1st level of the signature and so we see a similar position profile for the Sig-Trader and the factor model. However, when the factor model tends to go more short (or long), the higher order Sig-Traders, e.g order 3, tends to reduce its position since this will be more beneficial to minimising the weekly variance of PnL. We can think of this behaviur as being similar to applying a sigmoid function to your position in search of robustness, or applying a stop-loss to avoid becoming too leveraged - which are common practices. By incorporating path-dependencies in the strategy, we have access to a more robust and intutive extension to classic factor models.

#### 5.1.2 Incorporating Exogenous Signal

We now consider the case when we are in possession of an exogenous signal that can be used to inform our trading decisions, rather than solely relying on raw asset time series data. Suppose the asset price process $X$ is driven by some function of the signal $\phi(t,f_{0,t})$, e.g 
$$
\begin{align*}
dX_t = \phi(t, f_{0,t}) dt + \sigma^{X} dW_t^{X}.
\end{align*}
$$ Since $\phi(t, f_{0,t})$ is a function of the past time series of $f$, it may be difficult for a trader to directly model the dynamics of this system directly if they do not know the explicit form of $\phi$. In practice, a trader may use a Kalman (or alternative) filter to capture the impact of a noisy signal; in fact, the authors in [[Coh+23](#ref-Cohen2023NowcastingMethods)] prove how the Kalman filter can be equivalently written as a linear regression on the signature. In this example, we propose the following system for the signal process $f$ and its consequent impact on the underlying asset $X$, 
$$
\begin{align*}
df_t & = -\kappa f_t + \sigma^{f} dW_t^{f} \\
Z_t & = \int^t_0 K (t-s) df_s \\
dX_t & = Z_t dt + \sigma^{X} dW_t^{X}.
\end{align*}
$$ We let the (observable) signal $f$ be a generic mean-reverting OU process with zero mean, while it has a path-dependent causal impact on some latent process $Z$ via a time-dependent kernel $K$ that we do not observe. This kernel could simply be a stochastic filter, for example if the kernel is exponential, we recover an exponentially weighted average of previous increments in the signal. In this example, we take the kernel to be $K(t,s) = \exp\{-\alpha(t-s)\}$, which can be understood to be a decaying impact of the signal on the process $Z$, i.e more recent observations of $f$ have a greater impact on the instantaneous drift. The asset price process $X$ then behaves like an arithmetic Brownian motion with long term zero drift, but short term temporal structure.



<a id="fig:synthetic_signal_example"></a>
<img src="images/signal_latent_asset.png" />

*An Example of Signal/Drift/Asset Trajectories.*



The underlying asset process $X$ does not have a long term drift, so we would expect a static strategy to have no long-term expected return, as seen in the left hand plot of Figure [11](#fig:synthetic_signal_sharpes). In fact, we notice that any excess return is marginal when the Sig-Trader trades endogenously without access to the signal, which can be seen in the light blue distributions in Figure [11](#fig:synthetic_signal_sharpes). The red distributions correspond to the simple factor model that takes the value of the signal at time $t$ and predicts the future (one-step) return, i.e 
<a id="eq:signal_factor"></a>
$$
\begin{aligned}
\mu_{t+1} = \mathbb{E} [r_{t+1} \vert \mathcal{F}_t ] = \beta f_t + \varepsilon_{t+1}
\end{aligned}
$$ where the position is then scaled according to the expected return $mu_{t+1}$. The dark blue Sharpe ratio distributions correspond to the Sig-Trader for different orders of truncation. Clearly, we see that for higher orders of truncation, the Sharpe ratio improves as the Sig-Trader can better approximate the non-linear relationship between the signal and the underlying asset process.



<a id="fig:synthetic_signal_sharpes"></a>
<img src="images/synthetic_signal_sharpes.png" />

*Sharpe ratio distributions for the Sig-Trader of truncation orders 0,1,2, compared to the factor model described in <a href="#eq:signal_factor" data-reference-type="eqref" data-reference="eq:signal_factor">[eq:signal_factor]</a>.*



In this system there are several layers of noise and complexities to sift through, including the path-dependent impact of the signal, as well as noise from the signal itself $\sigma^f$ and exogenous noise of the underlying asset, $\sigma^X$. In this simple system, this volatility of such randomness is constant through time, but in practice this is likely not the case and this is the type of scenario when the Sig-Trader can outperform the classic predict-then-optimise frameworks. The left hand side of Figure [12](#fig:synthetic_signal_noise_ratio) illustrates how the Sig-Trader can transform a signal of varying strengths, into a position that is able to produce strong risk-adjusted returns.



<a id="fig:synthetic_signal_noise_ratio"></a>
<img src="images/synthetic_signal_noise_sharpes.png" />

*Sharpe ratio against the signal to noise ratio (LHS). The mean PnL and variance of PnL through time (RHS).*



### 5.2 Learning Momentum as a Sig-Trading Strategy

As highlighted previously, the class of signature trading strategies, contains most common systematic trading strategies that are functions of the past market time-series. One of the most common and established forms of systematic trading strategy is trend following (and its multiple variants), which generally applies some function (i.e a filter) to the past market time series, to determine the strength and direction of the underlying asset trend. The trader then trades in this direction, adjusting their position according to the strength (alternatively, they may we want to trade the opposite direction, which would constitute a mean-reversion strategy). For a high-level overview of the design and mechanics of momentum strategies, we refer the reader to [[RD12](#ref-RichardJMartin2012MomentumMe); [RA12](#ref-RichardJMartin2012Non-linearStrategies)], which give a large discussion on both linear and non-linear momentum. For practical applications, see [[MOP12](#ref-Moskowitz2012TimeMomentum); [AMP13](#ref-Asness2013ValueEverywhere); [BK13](#ref-Baltas2013MomentumFunds); [BS15](#ref-Barroso2015MomentumMoments); [Lem+14](#ref-Lemperiere2014RiskReturns)].

Within the broader class of momentum strategies live several variants, and this is dependent on your choice of function that characterises the trend. Variants (and combinations thereof) include RSI indicators, Bollinger bands, MACD (moving average convergence divergence) or any other type of moving average crossover. The key observation is that all of the previous mentioned variants constitute alternative functions (filters) of the past time series, therefore a natural question to ask is what are the best (or in fact optimal) types of function or filter to apply to the past market time series, in order to capture the dynamics of the underlying asset? Since momentum strategies are contained within the space of signature trading strategies, we are able to find the linear functional corresponding to a given momentum strategy. To make this more precise, we focus on capturing the characteristics of a MACD momentum strategy. We recall that MACD$(t_1, t_2)$ is the difference between the (exponentially weighted) $t_1$-moving average (the fast signal) and the $t_2$-moving average (the slow signal), designed to indicate strength of trend. The general setup might look as follows:

This is a very general framework that takes a given filter (i.e the MACD), uses it to predict future returns, and then applies some normalisation (i.e a sigmoid function) in order to retrieve a final strategy position. We note that a momentum strategy should naturally result in a positive regression coefficient of $L$ since a positive MACD signal indicates that the asset is 'trending' (otherwise, if the coefficient was negative, this would imply mean-reversion). We can think of this whole framework as being one continuous function of the past path, i.e 
$$
\begin{align*}
\xi_t = \varphi(t, X_{0,t}) = \sigma(L(\phi(t, X_{0,t}))).
\end{align*}
$$ The goal is therefore to demonstrate that the function $\varphi$ can be captured via a signature trading strategy such that $\varphi(t, X_{0,t}) = \langle \ell, \hat{\mathbb{X}}_{0,t} \rangle$.

Figure [13](#fig:MACD_graph) displays the corresponding MACD filter, which we denote $\phi$, while Figure [14](#fig:learning_momentum) shows the improvement of learnt linear functionals $\ell$, as the order of truncation of the signature increases. We notice that the order 3 signature is able to approximate the function $\varphi$ with almost $90\%$ $R^2$ accuracy, even though both the filter $\phi$ and the normalisation function $\sigma$ are highly non-linear.

Given that we are able to approximate the momentum trading strategy via a Sig-Trading strategy, we can compare this strategy to the mean-variance optimal order 3 strategy. Using the learnt linear functional $\ell$, we are able to construct the efficient frontier via the expected terminal PnL and variance of terminal PnL, 
$$
\begin{align*}
\mathbb{E}(V_T) &= \ell^\top \mu^{\textup{sig}} \\
\textup{Var}(V_T) &= \ell^\top \Sigma^{\textup{sig}} \ell.
\end{align*}
$$ Figure [15](#fig:MACD_EF_convex) (LHS) demonstrates that the optimal order 3 Sig-Trader has a much better risk-return profile over the chosen trade horizon of 20 days (one month), than that of the learnt momentum trader. It is worth noting however that the Sig-Trader in this example has many similar characteristics to that of the momentum trader, however the optimal Sig-Trader was able to capture further



<a id="fig:MACD_graph"></a>
<img src="images/MACD_graph.png" />

*An example of the corresponding slow and fast moving averages of a MACD(10,20) signal on the TLT ETF during 2006 (LHS). The associated weight function <span class="math inline"><em>ϕ</em>(<em>t</em> − <em>s</em>)</span> with the MACD(10,20) filter (RHS).*





<a id="fig:learning_momentum"></a>
<img src="images/learning_MACD_momentum.png" />

*The learnt MACD momentum strategy as a linear functional on the signature for different orders of truncation.*





<a id="fig:MACD_EF_convex"></a>
<img src="images/MACD_EF_convex_profile.png" />

*Signature efficient frontier comparison for optimal Sig-Traders and the corresponding learnt 3rd order approximation of the MACD momentum strategy (LHS). The order 3 Sig-Trading strategy return profile compared to the underlying returns (RHS).*



characteristics about the underlying dynamics and factor in the pathwise optimisation to achieve a lower monthly variance. The convex return profile of the order 3 Sig-Trader (RHS of Figure [15](#fig:MACD_EF_convex)) is reminiscent of a trend following strategy that earns positive returns with high conviction in trending (upwards or downwards) markets. This example shows us that in fact, besides from focusing on an optimal Sig-Trading solution, by re-casting other strategies in the same format, it can inform us better on how our strategies work and the various exposures that may exist. It might be such that a given strategy is largely exposed to specific terms in the signature, which can explain more about its characteristics and associated risks. We can also analyse how 'far away' our strategies are to an optimal Sig-Trading solution and hence better optimise for dynamic risks.

## 6 Conclusion

Path dependencies such as non-Markovian data structures, or time series exhibiting temporal correlation are a frequent phenomenon in financial data. Momentum and mean-reversion (of assets or signals) are two of the purest features of time series' data that a trader can exploit, and these features are inherently reliant on the whole path. However, many traditional techniques used for portfolio oprimisation are too inflexible to handle such structural complexities of the data and signals. Signature trading strategies, first developed and covered in detail in the thesis of Perez ([[Per20](#ref-PerezArribas2020SignaturesFinance)]), are a versatile representation of any investment strategy, which have been demonstrated to be a powerful tool in the context of pricing, hedging, and optimal execution.

We observe that in fact their advantages can be carried over to more general portfolio optimisation problems as they encompass many common trading styles that are present in practice (including the before-mentioned momentum and mean-reversion). More specifically, in this paper we extend classical factor models into the Sig-Trading framework, obtaining a closed form solution to the optimal mean-variance Sig-Trading strategy and derive a clear intuition for portfolio managers to navigate and use this formula in a path-dependent context. Furthermore, by lifting the mean-variance optimisation into the lead-lag signature space (See Definition [2.3](#eq:hoff_defn)), we bypass the necessity for any explicit prediction of returns, which is commonly required in traditional settings. This alleviates the accumulation of asymmetric residuals from the prediction phase, which can often be difficult to control. Moreover, the Sig-Trading framework simultaneously captures the joint signal-asset dynamics, whilst performing a dynamic optimisation which naturally incorporates a drawdown control within the objective function.

In summary, the Sig-Trading framework provides an alternative to machine learning methods, in its ability to handle path-dependent, non-linear dynamics and signals in a portfolio opitmisation context. Unlike machine learning methods, our framework requires no training or gradient descent optimisation and provides a closed-form solution that is lightweight to work with in practice. Our closed-form solution is tractable, easily implementable and ensures interpretability of the derived optimal strategies. Overall, our results provide more intuition than ML-based methods and establish more discretion in the fitting procedure than classical methods, providing a malleable framework that still solves many challenges faced when working with financial data.



> ## Appendix A: Rough Path & Tensor Algebra Preliminaries {#sec:appx_rough_paths}
>
> We aim to keep this paper self-contained by recalling the concepts and definitions we explicitly use in this paper. In this appendix we recall necessary fundamental building blocks used in our derivations.
>
> ### A.1 The Tensor Algebra
>
> In this section, we define the space on which the signature is defined and introduce notations that are used throughout the paper.

 definition
**Definition 14**. *(Tensor Algebra). Let $d \geq 1$. We define the extended tensor algebra over $\mathbb{R}^d$ by 
$$
\begin{align*}
T((\mathbb{R}^d)) := \left\{ \text{  } \textbf{a} = (a_0, a_1, \dots, a_n, \dots) \text{  } \left| \text{  } a_n \in (\mathbb{R}^d)^{\otimes n} \text{  } \right\} \right.
\end{align*}
$$ Similarly, we define the truncated tensor algebra of order $N \in \mathbb{N}$ and the tensor algebra by $T^{(N)}(\mathbb{R}^d)$ and $T(\mathbb{R}^d)$ respectively, by 
$$
\begin{align*}
T^{(N)}(\mathbb{R}^d) := & \left\{ \text{  } \textbf{a} = (a_n)_{n=0}^\infty \text{  } \left|  \text{  } a_n \in (\mathbb{R}^d)^{\otimes n} \text{ and } a_n = 0 \text{  } \forall n \geq N  \text{  } \right\} \right. \subset T((\mathbb{R}^d)) \\
= & \bigoplus_{n = 0}^N (\mathbb{R}^d)^{\otimes n}, \\
T(\mathbb{R}^d) := & \bigoplus_{n = 0}^\infty (\mathbb{R}^d)^{\otimes n} \subset T((\mathbb{R}^d)).
\end{align*}
$$ Note that the truncated tensor algebra of order $N$ has dimension $\sum_{k=0}^N d^k = \frac{d^{N+1}-1}{d-1}$.*
	



 remark
**Remark 7**. *Intuitively, we have that the zero-th level of the tensor algebra, $(\mathbb{R}^d)^{\otimes 0}$, is simply the set of all scalars $a_0 \in \mathbb{R}$, with dimension $d^0 = 1$. At the first level, $(\mathbb{R}^d)^{\otimes 1}$ is the set of all $\mathbb{R}$-valued vectors of length $d$, with dimension $d^1$. Likewise, at the second level, $(\mathbb{R}^d)^{\otimes 2}$ is the set of all $\mathbb{R}$-valued $d \times d$ matrices. Then the truncated tensor algebra at order 2, $T^{(2)}(\mathbb{R}^d)$, has dimension $1 + d + d^2$ and contains all $\mathbb{R}^d$-valued tensors of order $0,1,2$.*




 definition
**Definition 15**. *(Dual Space of the Tensor Algebra). Let $\{ e_1, \dots , e_d \} \subset \mathbb{R}^d$ be a basis for $\mathbb{R}^d$, then it has a dual basis $\{ e_1^*, \dots , e_d^* \} \subset (\mathbb{R}^d)^*$ for $(\mathbb{R}^d)^*$, the dual space of $\mathbb{R}^d$. Recall that this dual space is the space of all linear functions $\mathbb{R}^d \to \mathbb{R}$. We may similarly define a basis for $T((\mathbb{R}^d))$ and its dual space $T((\mathbb{R}^d)^*)$.*

*We identify this dual space of the tensor algebra, $T((\mathbb{R}^d)^*)$, with the space of all words. Consider the following alphabet $A_d:=\{\mathbf{1},\dots,\mathbf{d} \}$, which consists of $d$ letters. In order to ease notations, we make the following identification: 
<a id="eq:word_functional"></a>
$$
\begin{aligned}
e_{i_1}^* \otimes \dots \otimes e_{i_n}^* \in T((\mathbb{R}^d)^*) \leftrightarrow \mathbf{i_1} \dots \mathbf{i_n} \in \mathcal{W}(A_d),
\end{aligned}
$$ where $\mathcal{W}(A_d)$ is the real vector space of all words with the alphabet $A_d$. The empty word will be denoted by . We then have the identification $T((\mathbb{R}^d)^*) = \mathcal{W}(A_d).$ That is, that any linear functional $\ell:T((\mathbb{R}^d)) \to \mathbb{R}$ can be identified via elements in $\mathcal{W}(A_d)$. Hence we can think of $\textit{words}$ as linear functions on the tensor algebra.*




 example
**Example 3**. *Let $\mathbb{X} \in T((\mathbb{R}^d))$ be an element of the tensor algebra. We can view $\mathbb{X}$ in terms of its elements within the tensor algebra and each multi-index corresponding to a word, e.g. 
$$
\begin{align*}
\mathbb{X} = \left( \underbrace{
\begin{matrix}
\text{ }
\\
\mathbb{X}^{\mathbf{\emptyset}} \\
\text{ }
\end{matrix}}_{\textstyle \in (\mathbb{R}^d)^{\otimes 0}} , \text{ }
\underbrace{\begin{pmatrix}
\mathbb{X}^{\mathbf{1}}   \\
\vdots \\
\mathbb{X}^{\mathbf{d}}
\end{pmatrix}}_{\textstyle  \in (\mathbb{R}^d)^{\otimes 1}}
\text{ } , \text{ }
\underbrace{\begin{pmatrix}
\mathbb{X}^{\mathbf{11}} & \dots &  \mathbb{X}^{\mathbf{1d}}   \\
\vdots & \ddots & \vdots \\
\mathbb{X}^{\mathbf{d1}} & \dots & \mathbb{X}^{\mathbf{dd}}
\end{pmatrix}}_{\textstyle \in (\mathbb{R}^d)^{\otimes 2}} \text{ } , \text{ } \dots
\right).
\end{align*}
$$ The space of all words is defined as 
$$
\begin{align*}
\mathcal{W}(A_d) = \{ \mathbf{\emptyset}, \mathbf{1}, \dots, \mathbf{d}, \mathbf{11}, \dots, \mathbf{dd}, \dots \}.
\end{align*}
$$*


> Two algebraic operations on $\mathcal{W}(A_d)$ are the sum and concatenation. The sum of two words $\mathbf{w}$ and $\mathbf{v}$ is just the formal sum $\mathbf{w} + \mathbf{v} \in \mathcal{W}(A_d)$. The concatenation of $\mathbf{w} = \mathbf{i_1} \dots \mathbf{i_n}$, $\mathbf{v} = \mathbf{j_1} \dots \mathbf{j_m} \in \mathcal{W}(A_d)$ is defined by 
> $$
> \begin{align*}
> \mathbf{wv} :=  \mathbf{i_1} \dots \mathbf{i_n}\mathbf{j_1} \dots \mathbf{j_m} \in \mathcal{W}(A_d).
> \end{align*}
> $$ With some abuse of notation, we will then use the concatenation on $\mathcal{W}(A_d)$ and $T((\mathbb{R}^d)^*)$ interchangeably, in the sense that we will sometimes write $\ell \mathbf{w}$ for $\ell \in T((\mathbb{R}^d)^*), \mathbf{w} \in \mathcal{W}(A_d)$.

 {#defn:shuffle_product .definition}
**Definition 16**. *(Shuffle Product). The shuffle product $\mathbin{\sqcup\mkern-3mu\sqcup} : \mathcal{W}(A_d) \times \mathcal{W}(A_d) \to \mathcal{W}(A_d)$ is defined inductively by*



> *$\mathbf{ua} \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{vb} = (\mathbf{u} \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{vb})\mathbf{a} + (\mathbf{ua} \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{v}) \mathbf{b}$*
>
> *$\mathbf{w} \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{\emptyset} = \mathbf{\emptyset} \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{w} = \mathbf{w}$*



*for all words $\mathbf{u}, \mathbf{v}$ and letters $\mathbf{a}, \mathbf{b} \in \mathcal{W}(A_d)$.*




 {#ex:shuffle_ex .example}
**Example 4**. *Let $\mathbf{w} = \mathbf{12}, \mathbf{v} = \mathbf{34}$, then $\mathbf{w} \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{v}$ is given by 
$$
\mathbf{12} \mathbin{\sqcup\mkern-3mu\sqcup} \mathbf{34} =  \mathbf{1234} + \mathbf{1324} + \mathbf{1342} + \mathbf{3124} + \mathbf{3142} + \mathbf{3412}
$$*




 remark
**Remark 8**. *We make extensive use of the fact that polynomials of linear functionals can be expressed as shuffle products of the linear functionals themselves.*


> ### A.2 Rough Paths & The Signature

 definition
**Definition 17**. *($p$-variation). Let $p \geq 1$ and $X:[t',T] \to \mathbb{R}^d$ be a $d$-dimensional continuous path. We say the $p$-variation of $X$ is denoted as the seminorm 
$$
\| X \|_p = \left( \sup_{\mathcal{P}} \sum_{[s,t] \in \mathcal{P}} \| X_t - X_s \|^p \right)^{\frac{1}{p}}
$$ where $\| \cdot \|$ is any norm on $\mathbb{R}^d$ and the supremum is taken over all partitions $\mathcal{P}$ of the interval $[t',T]$.*




 definition
**Definition 18**. *(Space of $p$-variation paths). We denote the space of all $\mathbb{R}$-valued $d$-dimensional paths of finite $p$-variation, to be $C^{p-var}([0,T];\mathbb{R}^d)$.*




 remark
**Remark 9**. *We refer to the paths of *bounded variation* as elements of the space $C^{1-var}([0,T];\mathbb{R}^d)$. Note that all continuous piecewise smooth paths $X_{0,T} \in C^{1-var}([0,T];\mathbb{R}^d)$.*




 {#defn:geom_rough_path .definition}
**Definition 19**. *(Geometric $p$-rough paths). We define the space of *geometric $p$-rough paths*, $G^{\lfloor p \rfloor}(\mathbb{R}^d)$, as the closure of the space of signatures of smooth paths, at order $\lfloor p \rfloor$, namely 
$$
G^{\lfloor p \rfloor}(\mathbb{R}^d) := \overline{ \left\{ \text{ } \mathbb{X}^{\leq N} : \Delta_T \to T^{(N)}(\mathbb{R}^d) \quad \big\vert \quad N = \lfloor p \rfloor \text{ } \right\} }^{d_{p-\textup{var}}}
$$ where the closure is with respect to the $p$-variation metric (defined in [[LCL07](#ref-Lyons2007DifferentialPaths)], Definition 1.5).*




 theorem
**Theorem 20**. *(Extension Theorem, [[LCL07](#ref-Lyons2007DifferentialPaths)], Theorem 3.7). Let $p>1$ be a real number and $\mathbb{X}^{\leq N}_{s,t} \in G^{\lfloor p \rfloor}(\mathbb{R}^d)$ be the truncated signature at level $N \in \mathbb{N}$ of the path $X_{s,t}\in \mathcal{X}^d_{s,t}$. Then for every $n \geq \lfloor p \rfloor + 1$, there exists a unique $\mathbb{X}^{n}_{s,t}$ such that 
$$
(s,t) \mapsto \mathbb{X}_{s,t} = (1, \mathbb{X}^{1}_{s,t}, \dots, \mathbb{X}^{\lfloor p \rfloor}_{s,t}, \dots, \mathbb{X}^{n}_{s,t}, \dots) \in T((\mathbb{R}^d))
$$ has finite $p$-variation. We denote $\mathbb{X}_{s,t}$ as the *extension* of $\mathbb{X}^{\leq N}_{s,t}$.*




 remark
**Remark 10**. *The signature of a (piecewise) smooth path $X_{0,T} \in \mathcal{X}^d_{0,T}$ is itself a geometric rough path, namely $\mathbb{X}_{0,T}^{<\infty} \in G^{\lfloor 1 \rfloor}(\mathbb{R}^d)$.*




 {#eq:shuffle_product_property .lemma}
**Lemma 21**. *(Shuffle product property).Let $\mathbb{X}^{< \infty}_{0,T} \in G^{[p]}(\mathbb{R}^d)$ be a geometric rough path and let $\ell_1, \ell_2 \in T((\mathbb{R}^d)^*)$ be elements of the dual space of the tensor algebra, then 
$$
\begin{align*}
\langle \ell_1, \mathbb{X}^{< \infty}_{0,T} \rangle \langle \ell_2, \mathbb{X}^{< \infty}_{0,T} \rangle = \langle \ell_1 \mathbin{\sqcup\mkern-3mu\sqcup} \ell_2 , \mathbb{X}^{< \infty}_{0,T} \rangle
\end{align*}
$$*




 remark
**Remark 11**. *The *shuffle product property* is heavily used in deriving an explicit representation of the variance of PnL in Section [3](#sec:original).*




 proposition
**Proposition 22**. *(Signature is point-seperating, ( [[HL10](#ref-Hambly2010UniquenessGroup)], [[Boe+16](#ref-Boedihardjo2016TheUniqueness)] )). Let $X: [0,T] \to \mathbb{R}^d$, then its signature $\mathbb{X}_{0,T}^{<\infty} \in G^{[p]}(\mathbb{R}^d)$ is unique up to tree like equivalence and translation.*




 {#eq:add_time .corollary}
**Corollary 23**. *Let $\hat{X} : [0,T] \to \mathbb{R}^{d+1}$ be the associated add-time process of $X$. Then its signature $\hat{\mathbb{X}}_{0,T}^{< \infty}$ uniquely determines $X$ up to translations.*




 definition
**Definition 24**. *(Probability measure on the space of paths). Let $(\Omega, \mathcal{F}, (\mathcal{F}_t)_{t \in [0,T]}, \mathbb{P})$ be a filtered probability space such that $\mathcal{F}=(\mathcal{F}_t)_{t \in [0,T]}$ is the filtration generated by the non-negative $\mathbb{R}^d$-valued stochastic process $X=(X_t)_{t \in [0,T]}$. We say its path trajectories $X_{0,T}$ are sampled under the probability measure $\mathbb{P}$ and we denote $\mathcal{P}(\mathcal{X}^d_{0,T})$ as the set of all such probability measures.*




 definition
**Definition 25**. *(Expected Signature). Let $X$ be defined as previous. Then for any such $\mathbb{R}^d$-valued random path $X_{0,T}$, we can see that taking its signature $\mathbb{X}_{0,T}$ is also a random variable under $\mathbb{P} \in \mathcal{P}(\mathcal{X}^d_{0,T})$ and so hence we can define the notion of an *expected signature* under $\mathbb{P}$ at each order as 
$$
\mathbb{E}^{\mathbb{P}} \left[ \mathbb{X}_{0,T}^n \right] := \mathbb{E}^{\mathbb{P}} \left[ \text{   } \int \dots \int_{s < u_1 < \dots < u_k < t} dX_{u_1} \otimes \dots \otimes dX_{u_k} \right] \in (\mathbb{R}^d)^{\otimes n}
$$ where we have 
$$
\mathbb{E}^{\mathbb{P}} \left[ \mathbb{X}^{< \infty}_{0,T} \right] := (1, \mathbb{E}^{\mathbb{P}}[\mathbb{X}_{0,T}^1] , \dots, \mathbb{E} ^{\mathbb{P}}[ \mathbb{X}_{0,T}^n ], \dots ) \in T((\mathbb{R}^d)).
$$*

*The map $\mathbb{P} \mapsto \mathbb{E}^{\mathbb{P}} \left[ \mathbb{X}_{0,T}^{< \infty} \right] \in T((\mathbb{R}^d))$, which maps the probability measure $\mathbb{P}$ to its expected truncated signature, is injective ([[CO22](#ref-Chevyrev2022SignatureProcesses)]).*




 remark
**Remark 12**. *The *expected signature* allows us to systematically characterize the empirical probability measure on the streams in a model-free sense. The expected signature of paths $X \sim \mathbb{P}$, i.e $\mathbb{E}^\mathbb{P} [ \mathbb{X}^{< \infty}_{0,T} ]$ can be thought of as the moment generating function of a path-valued random variables $X$. We must also note, however, that the assumption that the expected signature even exists at all is a strong assumption for all levels of the signature $N \in \mathbb{N}$. For example, the authors in [[Bay+21](#ref-Bayer2021OptimalSignatures)] highlight that this rules out many stochastic volatility models, such as the Heston model.*




 {#eq:factorial_decay .lemma}
**Lemma 26**. *(Factorial Decay).*

*The reason we are able to work with the truncated signature with sufficient confidence is due to the factorial decay of the terms of the signature. Let $X \in \mathcal{X}^d_{0,T} \subset C^{1-var}([0,T],\mathbb{R}^m)$ and $[s,t] \subset [0,T].$ Then $\forall n \geq 1$ 
$$
\begin{align*}
\lVert \mathbb{X}^n_{s,t} \rVert = \left\lVert \quad \int \dots \int_{t_0 < u_1 < \dots < u_n < t} dX_{u_1} \otimes \dots \otimes dX_{u_n} \right\rVert \leq \frac{(\lVert X \rVert_{1,[s,t]})^n}{n!}
\end{align*}
$$*




 {#eq:universal_approx .theorem}
**Theorem 27**. *(Universal Approximation, [[LLN13](#ref-Levin2013LearningSystem)], Theorem 3.1). Let $K \subset C^{1-var}([0,T],\mathbb{R}^d)$[^1] be a compact subset of paths. For any $\phi \in C(K,\mathbb{R})$, and for every $\epsilon>0$, there exists a linear functional $\ell \in T((\mathbb{R}^d))^*$ such that 
$$
\begin{align*}
\sup_{X \in K} \lVert \phi(X) - \langle \ell, \mathbb{X}^{< \infty}_{0,T} \rangle \rVert < \epsilon
\end{align*}
$$ where the choice of suitable candidate topology is discussed in [[CT22](#ref-Cass2022TopologiesSpace)].*




 remark
**Remark 13**. *If we imagine that the optimal adapted dynamic trading strategy $\xi_t$ is simply a function of the past path, i.e $\xi_t: X_{0,t} \mapsto \phi(X_{0,t})$ for some non-linear $\phi$, then Theorem [A.13](#eq:universal_approx) allows us to approximate the non-linear $\phi$ by $\phi(X_{0,t}) \approx \langle \ell , \mathbb{X}^{<\infty}_{0,t} \rangle$ where $\ell$ is linear. This will be made more precise in Section [2](#sec:market_model).*


> **Notation:** Throughout, we denote the time-augmented process by $\hat{X}_t=(t, X_t), t \in [0,T]$, the signature of $\hat{X}_{0,T}$ by $\hat{\mathbb{X}}^{<\infty}_{0,T}$ and the signature of the lead-lag process $\hat{\mathbb{X}}^{LL,<\infty}_{0,T}$.

 {#eq:example_sigs .example}
**Example 5**. *(Linear functional on the signature). Let $X=(X^{1}, \dots, X^{d}) : [0,T] \to \mathbb{R}^d$ be a $d$-dimensional path. We previously made the identification that any linear functional on the tensor algebra can be identified via elements in the space of all words. Take for example:*

1.  *Consider any signature term at the second level of the $i$-th and $j$-th component of $X$. 
$$
\begin{align*}
\mathbb{X}^{\mathbf{ij}}_{0,T} = \iint_{0<u_i < u_j <T}  \circ  dX_{u_i}^i  \circ dX_{u_j}^j = \int^T_0 (X_t^i - X_0^i)  \circ  dX_t^j = \langle  \mathbf{ij}, \hat{\mathbb{X}}^{<\infty}_{0,T} \rangle
\end{align*}
$$ where we can think of $\mathbf{ij}$ as a word in the space $\mathcal{W}(A_d)$, which can be identified as a linear functional on the tensor algebra, as shown in [eq:word_functional](#eq:word_functional).*

2.  *Consider an arbitrary linear functional $\ell \in T((\mathbb{R}^d)^*)$ on the signature, then its (Stratonovich) integral against the $i$-th component of the $d$-dimensional process $X$ is simply the linear functional concatenated with the letter $\mathbf{i}$, applied to the signature $\mathbb{X}^{<\infty}_{0,T}$, such as:*

    *
$$
\begin{align*}
\int^T_0 \langle \ell, \mathbb{X}^{<\infty}_{0,t} \rangle  \circ  dX_t^i = \langle \ell \mathbf{i} , \mathbb{X}^{<\infty}_{0,T} \rangle
\end{align*}
$$*

3.  *Let 
$$
\ell = \alpha_0 \mathbf{1} + \alpha_1 \mathbf{2} + \alpha_2 \mathbf{12}.
$$ When applied to the signature, we obtain 
$$
\langle \ell, \mathbb{X}^{<\infty}_{0,t} \rangle = \alpha_0 \mathbb{X}^{\mathbf{1}}_{0,t} + \alpha_1 \mathbb{X}^{\mathbf{2}}_{0,t} + \alpha_2 \mathbb{X}^{\mathbf{12}}_{0,t}
$$ and if we consider the concatenation $\ell \mathbf{34}$, then we have 
$$
\langle \ell \mathbf{34}, \mathbb{X}^{<\infty}_{0,t} \rangle = \alpha_0 \mathbb{X}^{\mathbf{134}}_{0,t} + \alpha_1 \mathbb{X}^{\mathbf{234}}_{0,t} + \alpha_2 \mathbb{X}^{\mathbf{1234}}_{0,t}.
$$*


> ## Appendix B: Proofs
>
> ## Proof of Theorem [11](#thm:int_sig) {#sec:proof_of_pnl_thm}
>
> **Proof.** Let $\hat{\mathbb{Z}}^{\leq M}$ be the $M$-th order signature of the (time-augmented) market factor process $\hat{Z}$ and define $\hat{Y}_t = (\hat{Z}_t, \hat{Z}_t)$ and its $M$-th order truncated signature as $\hat{\mathbb{Y}}^{\leq M}_t$. In order to prove this theorem, we first state some important results that we shall use as tools throughout. We denote the quadratic co-variation of 2 processes at time $t$ as $[ \cdot , \cdot ]_t$.
>
> 1.  $\int_0^T \langle l_m, \hat{\mathbb{Z}}^{\leq M}_{0,t} \rangle \circ dX_t^m = \langle l_m \mathbf{f}(m), \hat{\mathbb{Y}}^{\leq M+1}_{0,T} \rangle$
>
> 2.  $\int^T_0 Y dX = \int^T_0 Y \circ dX - \frac{1}{2} \left[ X,Y \right]$ for 2 stochastic processes $X, Y$.
>
> 3.  $\mathbb{Z}^{LL, \leq 2}_{0,T} = \hat{\mathbb{Y}}^{\leq 2}_{0,T} + \psi_{0,T}$ where 
> $$
> \psi_{0,T} =
> \begin{pmatrix}
> 0 & - \frac{1}{2} [ \hat{Y} ]_{0,T}  \\
> \frac{1}{2} [ \hat{Y} ]_{0,T} & 0 \\
> \end{pmatrix}
> $$
>
> 4.  $\mathbb{Z}^{LL, \leq M}_{0,T} = \int^T_0 \hat{\mathbb{Z}}^{\leq M-1}_{0,t} \otimes d \hat{Z}_t$
>
> 5.  $\langle  \mathbf{m} ,  \hat{\mathbb{Z}}^{\leq M}_{0,t}  \rangle = \langle \mathbf{f}(m),  \hat{\mathbb{Y}}^{\leq M}_{0,t} \rangle$
>
> 6.  $[ \int^T_0 \xi dX, Y] = \int^T_0 \xi d[X,Y]$
>
> First, we observe that the trading strategy PnL can be decomposed asset-wise such that $V_T = \sum_{m=1}^d V_T^m$ where $V_T^m$ is the PnL of the trading strategy of the $m$-th asset. Hence, all that needs to be shown is that for arbitrary asset $m$, 
> <a id="eq:pnl_by_asset"></a>
> $$
> \begin{aligned}
> V_T^m = \int^T_0 \langle l_m, \hat{\mathbb{Z}}_{0,t}^{< \infty} \rangle dX_t^m = \langle l_m \mathbf{f}(m), \hat{\mathbb{Z}}^{LL,<\infty}_{0,T} \rangle
> \end{aligned}
> $$ where the integral above is in the Itô sense. We also wish to show that this result holds for any truncation level $M \geq 1$ and for any number of market factors, $N$.
>
> Let us fix truncation level $M \geq 1$. By (2) we can decompose the Itô integral in [eq:pnl_by_asset](#eq:pnl_by_asset) into a Stratonovich integral and a quadratic variation correction term, i.e 
> <a id="eq:to_be_shown"></a>
> $$
> \begin{aligned}
> \int^T_0 \langle l_m, \hat{\mathbb{Z}}_{0,t}^{\leq M} \rangle dX_t^m & = \int^T_0  \langle l_m, \hat{\mathbb{Z}}_{0,t}^{\leq M} \rangle \circ dX_t^m - \frac{1}{2} \left[  \langle l_m, \hat{\mathbb{Z}}_{0,\cdot}^{\leq M} \rangle , X^m \right]_T \\
> & = \overbrace{\langle l_m \mathbf{f}(m), \hat{\mathbb{Y}}^{\leq M+1}_{0,T} \rangle }^{\textup{by } (1)} \quad \text{   } - \overbrace{\frac{1}{2} \left[ \left\langle l_m , \int^\cdot_0  \hat{\mathbb{Z}}_{0,t}^{\leq M-1} \otimes d \hat{Z}_t \right\rangle , X^m  \right]_T}^{\textup{by } (4)} \\
> & = \langle l_m \mathbf{f}(m), \hat{\mathbb{Y}}^{\leq M+1}_{0,T} \rangle  \quad \text{   } - \overbrace{ \frac{1}{2}
> \left[ \left\langle l_m \mathbf{f}(m) , \int^\cdot_0  \hat{\mathbb{Y}}_{0,t}^{\leq M-1} \otimes d \hat{Y}_t \right\rangle , X^m \right]_T}^{\text{by } (5)} \\
> & = \langle l_m \mathbf{f}(m), \hat{\mathbb{Y}}^{\leq M+1}_{0,T} \rangle  \quad \text{   } - \frac{1}{2}
> \left\langle l_m \mathbf{f}(m) , \left[  \int^\cdot_0  \hat{\mathbb{Y}}_{0,t}^{\leq M-1} \otimes d \hat{Y}_t , X^m \right]_T \right\rangle  \\
> & = \langle l_m \mathbf{f}(m), \hat{\mathbb{Y}}^{\leq M+1}_{0,T} \rangle  \quad \text{   } - \frac{1}{2}
> \left\langle l_m \mathbf{f}(m) , \overbrace{\int^\cdot_0  \hat{\mathbb{Y}}_{0,t}^{\leq M-1}  d \left[ \hat{Y}_t , X^m \right]_T}^{\text{by } (6)} \right\rangle  \\
> & = \langle l_m \mathbf{f}(m), \hat{\mathbb{Y}}^{\leq M+1}_{0,T} \rangle  \quad \text{   } -  \frac{1}{2} \left\langle l_m \mathbf{f}(m), \int^T_0 \hat{\mathbb{Y}}_{0,T}^{\leq M-1} \otimes d [\hat{Y}]_t \right\rangle  \\
> &  = \left\langle l_m \mathbf{f}(m), \hat{\mathbb{Y}}^{\leq M+1}_{0,T} - \frac{1}{2} \int^T_0 \hat{\mathbb{Y}}_{0,t}^{\leq M-1} \otimes d [\hat{Y}]_t \right\rangle.
> \end{aligned}
> $$ Hence, what remains to be shown is that the RHS of [eq:pnl_by_asset](#eq:pnl_by_asset) is equal to [eq:to_be_shown](#eq:to_be_shown), i.e that 
> <a id="eq:to_be_shown2"></a>
> $$
> \begin{aligned}
> \left\langle l_m \mathbf{f}(m), \hat{\mathbb{Z}}^{LL,\leq M+1}_{0,T} \right\rangle = \left\langle l_m \mathbf{f}(m) , \hat{\mathbb{Y}}^{\leq M+1}_{0,T} - \frac{1}{2} \int^T_0 \hat{\mathbb{Y}}_{0,t}^{\leq M-1} \otimes d [\hat{Y}]_t \right\rangle
> \end{aligned}
> $$ for any truncation level $M \geq 1$. For the case when $M=1$, we have that 
$$
\hat{\mathbb{Z}}^{LL,\leq 2}_{0,T} = \hat{\mathbb{Y}}^{\leq 2}_{0,T} + \psi_{0,T}
$$ as defined in (3), which is proven in [[FHL16](#ref-Flint2016DiscretelyProcess)], Theorem 4.1. Therefore, we can clearly see that 
> $$
> \begin{align*}
> \left\langle l_m \mathbf{f}(m), \hat{\mathbb{Z}}^{LL,\leq 2}_{0,T} \right\rangle = & \left\langle l_m \mathbf{f}(m),  \hat{\mathbb{Y}}^{\leq 2}_{0,T} + \psi_{0,T} \right\rangle \\
> = & \left\langle l_m \mathbf{f}(m),  \hat{\mathbb{Y}}^{\leq 2}_{0,T} - \frac{1}{2} [\hat{Y}]_T  \right\rangle \\
> = & \left\langle l_m \mathbf{f}(m),  \hat{\mathbb{Y}}^{\leq 2}_{0,T} - \frac{1}{2} \int^T_0 1 d [\hat{Y}]_t \right\rangle \\
> = & \left\langle l_m \mathbf{f}(m),  \hat{\mathbb{Y}}^{\leq 2}_{0,T} - \frac{1}{2} \int^T_0 \hat{\mathbb{Y}}^{\leq 0}_{0,T} \otimes  d [\hat{Y}]_t \right\rangle
> \end{align*}
> $$ Hence, the statement [eq:to_be_shown2](#eq:to_be_shown2) holds for $M=1$. By the same proof seen in Lemma 3.2.11 in [[Per20](#ref-PerezArribas2020SignaturesFinance)], the result follows for all $M \geq 1$ via induction, taking $I = \mathbf{i_1 i_2 \dots i_k} \in \{1 , \dots, d \}^k$ for the multi-dimensional result.
>
> We note here that by setting $Z = (t, X, f)$, we lose no strength in this argument, since we are still only integrating against $X^m$, for which the result then follows through $\mathbf{f}(m)$ for $m={1,\dots,d}$ and so any extra remaining exogenous factors embedded in $\mathbb{Z}$ do not change the result. Likewise, since out portfolio PnL is defined asset-wise, the result holds for all assets $m$ and so the overall trading strategy PnL is defined as 
> $$
> \begin{align*}
> V_T = \sum_{m = 1}^d \int^T_0 \langle l_m, \hat{\mathbb{Z}}_{0,s}^{< \infty} \rangle dX_s^m = \sum_{m = 1}^d \langle l_m \mathbf{f}(m), \hat{\mathbb{Z}}^{LL,<\infty}_{0,T} \rangle
> \end{align*}
> $$ $\square$



[^1]: *$K$ should be a subset of tree-reduced paths. However, as all of the paths we are concerned with are tree-reduced, this is not an issue.*


---

## References

- <a id="ref-Ananova2023Model-freeStrategies"></a>**[ACX23]** Anna Ananova, Rama Cont, Renyuan Xu (2023). *Model-free Analysis of Dynamic Trading Strategies*. SSRN Electronic Journal.

- <a id="ref-Alexander2002TheStrategies"></a>**[AD02]** Carol Alexander, Anca Dimitriu (2002). *The Cointegration Alpha: Enhanced Index Tracking and Long-Short Equity Market Neutral Strategies*. ISMA Finance Discussion Paper No. 2002-08.

- <a id="ref-Asness2013ValueEverywhere"></a>**[AMP13]** Clifford  S. Asness, Tobias  J. Moskowitz, Lasse  Heje Pedersen (2013). *Value and Momentum Everywhere*. Journal of Finance (Vol. 68, No. 3, pp. 929– 985).

- <a id="ref-Arribas2020Sig-SDEsFinance"></a>**[ASS20]** Imanol  Perez Arribas, Cristopher Salvi, Lukasz Szpruch (2020). *Sig-SDEs model for quantitative finance*. ICAIF 2020 - 1st ACM International Conference on AI in Finance.

- <a id="ref-Alden2022Model-AgnosticSignatures"></a>**[Ald+22]** Andrew Alden, Carmine Ventre, Blanka Horvath, Gordon Lee (2022). *Model-Agnostic Pricing of Exotic Derivatives Using Signatures*. Proceedings of the 3rd ACM International Conference on AI in Finance, ICAIF 2022 (pp. 96– 104).

- <a id="ref-Allan2021Model-freeApproach"></a>**[All+21]** Andrew  L. Allan, Christa Cuchiero, Chong Liu, David  J. Prömel (2021). *Model-free Portfolio Theory: A Rough Path Approach*. Mathematical Finance (Vol. 33, No. 3, pp. 709– 765).

- <a id="ref-Arribas2018DerivativesPayoffs"></a>**[Arr18]** Imanol  Perez Arribas (2018). *Derivatives pricing using signature payoffs*.

- <a id="ref-Bain2009FundamentalsFiltering"></a>**[BC09]** Alan Bain, Dan Crisan (2009). *Fundamentals of Stochastic Filtering*.

- <a id="ref-Breidt1998TheVolatility"></a>**[BCD98]** F.\bibnamedelimi Jay Breidt, Nuno Crato, Pedro De\bibnamedelima Lima (1998). *The detection and estimation of long memory in stochastic volatility*. Journal of Econometrics (Vol. 83, No. 1-2, pp. 325– 348).

- <a id="ref-Bank2023OptimalSignals"></a>**[BCK23]** Peter Bank, Álvaro Cartea, Laura Körber (2023). *Optimal execution and speculation with trade signals*.

- <a id="ref-Bergault2021Multi-assetDynamics"></a>**[BDG21]** Philippe Bergault, Fayçal Drissi, Olivier Guéant (2021). *Multi-asset optimal execution and statistical arbitrage strategies under Ornstein-Uhlenbeck dynamics*. SIAM Journal on Financial Mathematics (Vol. 13, No. 1).

- <a id="ref-Baltas2013MomentumFunds"></a>**[BK13]** Akindynos-Nikolaos Baltas, Robert Kosowski (2013). *Momentum Strategies in Futures Markets and Trend-following Funds*. SSRN Electronic Journal.

- <a id="ref-Barroso2015MomentumMoments"></a>**[BS15]** Pedro Barroso, Pedro Santa-Clara (2015). *Momentum has its moments*. Journal of Financial Economics (JFE) (Vol. 116, No. 1, pp. 111– 120).

- <a id="ref-Brini2023DeepReturns"></a>**[BT23]** Alessio Brini, Daniele Tantari (2023). *Deep Reinforcement Trading with Predictable Returns*.

- <a id="ref-Bayer2021OptimalSignatures"></a>**[Bay+21]** Christian Bayer, Paul Hager, Sebastian Riedel, John Schoenmakers (2021). *Optimal stopping with signatures*.

- <a id="ref-Boedihardjo2016TheUniqueness"></a>**[Boe+16]** Horatio Boedihardjo, Xi Geng, Terry Lyons, Danyu Yang (2016). *The signature of a rough path: Uniqueness*. Advances in Mathematics (Vol. 293, pp. 720– 737).

- <a id="ref-Bonnier2019DeepTransforms"></a>**[Bon+19]** Patric Bonnier, Patrick Kidger, Imanol  Perez Arribas, Cristopher Salvi, Terry Lyons (2019). *Deep Signature Transforms*. Advances in Neural Information Processing Systems (Vol. 32).

- <a id="ref-Buehler2021GeneratingSignatures"></a>**[Bue+21]** Hans Buehler, Blanka Horvath, Terry Lyons, Imanol Perez\bibnamedelima Arribas, Ben Wood (2021). *Generating Financial Markets With Signatures*. Risk.

- <a id="ref-Buhler2018DeepHedging"></a>**[Büh+18]** Hans Bühler, Lukas Gonon, Josef Teichmann, Ben Wood (2018). *Deep Hedging*.

- <a id="ref-Cartea2022Double-ExecutionSignatures"></a>**[CAS22]** Álvaro Cartea, Imanol  Pérez Arribas, Leandro Sánchez-Betancourt (2022). *Double-Execution Strategies Using Path Signatures*. https://doi.org/10.1137/21M1456467 (Vol. 13, No. 4, pp. 1379– 1417).

- <a id="ref-Chiu2023AFinance"></a>**[CC23]** Henry Chiu, Rama Cont (2023). *A model-free approach to continuous-time finance*. Mathematical Finance.

- <a id="ref-Cartea2022ExecutionMakers"></a>**[CDM22]** Alvaro Cartea, Fayçal Drissi, Marcello Monga (2022). *Execution and Statistical Arbitrage with Signals in Multiple Automated Market Makers*.

- <a id="ref-Cartea2023BanditsSignals"></a>**[CDO23]** Álvaro Cartea, Fayçal Drissi, Pierre Osselin (2023). *Bandits for Algorithmic Trading with Signals*. SSRN Electronic Journal.

- <a id="ref-Cuchiero2022Signature-basedCalibration"></a>**[CGS22]** Christa Cuchiero, Guido Gazzani, Sara Svaluto-Ferro (2022). *Signature-based models: theory and calibration*.

- <a id="ref-Costa2022DistributionallyConstruction"></a>**[CI22]** Giorgio Costa, Garud  N. Iyengar (2022). *Distributionally Robust End-to-End Portfolio Construction*.

- <a id="ref-Cartea2015AlgorithmicAssets"></a>**[CJ15]** Álvaro Cartea, Sebastian Jaimungal (2015). *Algorithmic Trading of Co-Integrated Assets*. SSRN Electronic Journal.

- <a id="ref-Coache2022ConditionallyLearning"></a>**[CJC22]** Anthony Coache, Sebastian Jaimungal, Alvaro Cartea (2022). *Conditionally Elicitable Dynamic Risk Measures for Deep Reinforcement Learning*.

- <a id="ref-Chevyrev2016ALearning"></a>**[CK16]** Ilya Chevyrev, Andrey Kormilitzin (2016). *A Primer on the Signature Method in Machine Learning*.

- <a id="ref-Chevyrev2013CharacteristicPaths"></a>**[CL13]** Ilya Chevyrev, Terry Lyons (2013). *Characteristic functions of measures on geometric rough paths*.

- <a id="ref-Crisan2021PathwiseProblem"></a>**[CLO21]** Dan Crisan, Alexander Lobbe, Salvador Ortiz-Latorre (2021). *Pathwise approximations for the solution of the non-linear filtering problem*.

- <a id="ref-Cont2023FastInformation"></a>**[CMN23]** Rama Cont, Alessandro Micheli, Eyal Neuman (2023). *Fast and Slow Optimal Trading with Exogenous Information*.

- <a id="ref-Chevyrev2022SignatureProcesses"></a>**[CO22]** Ilya Chevyrev, Harald Oberhauser (2022). *Signature Moments to Characterize Laws of Stochastic Processes*. Journal of Machine Learning Research (Vol. 23, pp. 1– 42).

- <a id="ref-Chamberlain1983ArbitrageMarkets"></a>**[CR83]** Gary Chamberlain, Michael Rothschild (1983). *Arbitrage, Factor Structure, and Mean-Variance Analysis on Large Asset Markets*. Econometrica (Vol. 51, No. 5, pp. 1281).

- <a id="ref-Cass2022TopologiesSpace"></a>**[CT22]** Thomas Cass, William  F. Turner (2022). *Topologies on unparameterised path space*.

- <a id="ref-Chen1957IntegrationFormula"></a>**[Che57]** Kuo-Tsai Chen (1957). *Integration of Paths, Geometric Invariants and a Generalized Baker- Hausdorff Formula*. The Annals of Mathematics (Vol. 65, No. 1, pp. 163).

- <a id="ref-Chen1977IteratedIntegrals"></a>**[Che77]** Kuo  Tsai Chen (1977). *Iterated path integrals*. Bulletin of the American Mathematical Society (Vol. 83, No. 5, pp. 831– 879).

- <a id="ref-Cohen2023NowcastingMethods"></a>**[Coh+23]** Samuel  N Cohen, Silvia Lui, Will Malpass, Giulia Mantoan, Lars Nesheim, ´ Aureo\bibnamedelimb De\bibnamedelima Paula, Andrew Reeves, Craig Scott, Emma Small, Lingyi Yang (2023). *Nowcasting with signature methods*.

- <a id="ref-Cont2001EmpiricalIssues"></a>**[Con01]** Rama Cont (2001). *Empirical properties of asset returns: stylized facts and statistical issues*.

- <a id="ref-Dyer2021DeepModels"></a>**[DCS21]** Joel Dyer, Patrick Cannon, Sebastian  M Schmon (2021). *Deep Signature Statistics for Likelihood-free Time-series Models*. ICML Workshop on Invertible Neural Networks, Normalizing Flows, and Explicit Likelihood Models.

- <a id="ref-Dupire2023FunctionalExpansions"></a>**[DT23]** Bruno Dupire, Valentin Tissot-Daguette (2023). *Functional Expansions*.

- <a id="ref-Das2022RoughnessSignals"></a>**[Das22]** Purba Das (2022). *Roughness properties of paths and signals*.

- <a id="ref-Dyer2022ApproximateDiscrepancies"></a>**[Dye+22]** Joel Dyer, John Fitzgerald, Bastian Rieck, Sebastian  M Schmon (2022). *Approximate Bayesian Computation for Panel Data with Signature Maximum Mean Discrepancies*. ICML Time-series Workshop.

- <a id="ref-Engle2001GARCHEconometrics"></a>**[Eng01]** Robert Engle (2001). *GARCH 101: The Use of ARCH/GARCH Models in Applied Econometrics*. Journal of Economic Perspectives (Vol. 15, No. 4, pp. 157– 168).

- <a id="ref-Fama2015AModel"></a>**[FF15]** Eugene  F. Fama, Kenneth  R. French (2015). *A five-factor asset pricing model*. Journal of Financial Economics (Vol. 116, No. 1, pp. 1– 22).

- <a id="ref-Fama1993CommonBonds"></a>**[FF93]** Eugene  F Fama, Kenneth  R French (1993). *Common risk factors in the returns on stocks and bonds*. Journal of Financial Economics (Vol. 33, pp. 3– 56).

- <a id="ref-Friz2020AStructures"></a>**[FH20]** Peter  K Friz, Martin Hairer (2020). *A Course on Rough Paths With an introduction to regularity structures*.

- <a id="ref-Flint2016DiscretelyProcess"></a>**[FHL16]** Guy Flint, Ben Hambly, Terry Lyons (2016). *Discretely sampled signals and the rough Hoff process*. Stochastic Processes and their Applications (Vol. 126, No. 9, pp. 2593– 2614).

- <a id="ref-Friz2010MultidimensionalPaths"></a>**[FV10]** Peter  K. Friz, Nicolas  B. Victoir (2010). *Multidimensional Stochastic Processes as Rough Paths*. Multidimensional Stochastic Processes as Rough Paths.

- <a id="ref-Fermanian2021EmbeddingSignatures"></a>**[Fer21]** Adeline Fermanian (2021). *Embedding and learning with signatures*. Computational Statistics {\& (Vol. 157, pp. 107148).

- <a id="ref-Forde2022OptimalResilience"></a>**[For+22]** Martin Forde, Leandro Sánchez-Betancourt, Benjamin Smith, Leandro Sánchez-betancourt, Maths Dept (2022). *Optimal trade execution for Gaussian signals with power-law resilience*. Quantitative Finance (Vol. 22, No. 3, pp. 585– 596).

- <a id="ref-Fukasawa2021VolatilityRough"></a>**[Fuk21]** Masaaki Fukasawa (2021). *Volatility has to be rough*. Quantitative Finance (Vol. 21, No. 1, pp. 1– 8).

- <a id="ref-Gatheral2014VolatilityRough"></a>**[GJR14]** Jim Gatheral, Thibault Jaisson, Mathieu Rosenbaum (2014). *Volatility is rough*. Quantitative Finance (Vol. 18, No. 6, pp. 933– 949).

- <a id="ref-Guyon2022VolatilityPath-Dependent"></a>**[GL22]** Julien Guyon, Jordan Lekeufack (2022). *Volatility Is (Mostly) Path-Dependent*.

- <a id="ref-Garleanu2013DynamicCosts"></a>**[GP13]** Nicolae Gârleanu, Lasse  Heje Pedersen (2013). *Dynamic Trading with Predictable Returns and Transaction Costs*. Journal of Finance (Vol. 68, No. 6, pp. 2309– 2340).

- <a id="ref-Guijarro-Ordonez2021DeepArbitrage"></a>**[GPZ21]** Jorge Guijarro-Ordonez, Markus Pelger, Greg Zanotti (2021). *Deep Learning Statistical Arbitrage*.

- <a id="ref-Gyurko2013ExtractingStream"></a>**[Gyu+13]** Lajos  Gergely Gyurkó, Terry Lyons, Mark Kontkowski, Jonathan Field (2013). *Extracting information from the signature of a financial data stream*.

- <a id="ref-Hambly2010UniquenessGroup"></a>**[HL10]** Ben Hambly, Terry Lyons (2010). *Uniqueness for the signature of a path of bounded variation and the reduced path group*. Annals of Mathematics (Vol. 171, No. 1, pp. 109– 167).

- <a id="ref-Horvath2021DeepVolatility"></a>**[HTZ21]** Blanka Horvath, Josef Teichmann, Zan Zuric (2021). *Deep Hedging under Rough Volatility*. Swiss Finance Institute Research Paper Series.

- <a id="ref-Hoff2006ThePath"></a>**[Hof06]** Ben Hoff (2006). *The Brownian Frame Process as a Rough Path*.

- <a id="ref-Issa2023Non-parametricStructures"></a>**[IH23]** Zacharia Issa, Blanka Horvath (2023). *Non-parametric online market regime detection and regime clustering for multidimensional and path-dependent data structures*.

- <a id="ref-Issa2023Non-adversarialScores"></a>**[Iss+23]** Zacharia Issa, Blanka Horvath, Maud Lemercier, Cristopher Salvi (2023). *Non-adversarial training of Neural SDEs with signature kernel scores*.

- <a id="ref-Jacquier2020Path-dependentModels"></a>**[JL20]** Antoine Jacquier, Chloé Lacombe (2020). *Path-dependent Volatility Models*.

- <a id="ref-Jaimungal2021RobustLearning"></a>**[Jai+21]** Sebastian Jaimungal, Silvana Pesenti, Ye  Sheng Wang, Hariom Tatsat (2021). *Robust Risk-Aware Reinforcement Learning*. SIAM Journal on Financial Mathematics (Vol. 13, pp. 213– 226).

- <a id="ref-Kalayci2019AOptimization"></a>**[KEA19]** Can  B Kalayci, Okkes Ertenlice, Anil Akbay (2019). *A comprehensive review of deterministic models and applications for mean-variance portfolio optimization*. Expert Systems With Applications (Vol. 125, pp. 345– 368).

- <a id="ref-Kidger2021Signatory:GPU"></a>**[KL21]** Patrick Kidger, Terry Lyons (2021). *Signatory: differentiable computations of the signature and logsignature transforms, on both CPU and GPU*. ICLR 2021 - 9th International Conference on Learning Representations.

- <a id="ref-Kalsi2020OptimalSignatures"></a>**[KLA20]** Jasdeep Kalsi, Terry Lyons, Imanol  Perez Arribas (2020). *Optimal execution with rough path signatures*. SIAM Journal on Financial Mathematics (Vol. 11, No. 2).

- <a id="ref-Lyons2007DifferentialPaths"></a>**[LCL07]** Terry  J. Lyons, Michael Caruana, Thierry Lévy (2007). *Differential Equations Driven by Rough Paths*.

- <a id="ref-Limmer2023RobustGANs"></a>**[LH23]** Yannick Limmer, Blanka Horvath (2023). *Robust Hedging GANs*.

- <a id="ref-Leung2015OptimalExit"></a>**[LL15]** Tim Leung, Xin Li (2015). *Optimal Mean Reversion Trading with Transaction Costs and Stop-Loss Exit*. International Journal of Theoretical and Applied Finance (Vol. 18, No. 3).

- <a id="ref-Levin2013LearningSystem"></a>**[LLN13]** Daniel Levin, Terry Lyons, Hao Ni (2013). *Learning from the past, predicting the statistics for the future, learning an evolving system*.

- <a id="ref-Lyons2022SignatureLearning"></a>**[LM22]** Terry Lyons, Andrew  D. McLeod (2022). *Signature Methods in Machine Learning*.

- <a id="ref-Lehalle2019IncorporatingTrading"></a>**[LN19]** Charles-Albert Lehalle, Eyal Neuman (2019). *Incorporating Signals into Optimal Trading*. Finance and Stochastics (Vol. 23, pp. 275– 311).

- <a id="ref-Lyons2019Non-parametricDerivatives"></a>**[LNA19a]** Terry Lyons, Sina Nejad, Imanol  Perez Arribas (2019). *Non-parametric Pricing and Hedging of Exotic Derivatives*. Applied Mathematical Finance (Vol. 27, pp. 457– 494).

- <a id="ref-Lyons2019NumericalSignatures"></a>**[LNA19b]** Terry Lyons, Sina Nejad, Imanol  Perez Arribas (2019). *Numerical method for model-free pricing of exotic derivatives using rough path signatures*.

- <a id="ref-Lemperiere2014RiskReturns"></a>**[Lem+14]** Yves Lemperiere, Cyril Deremble, Trung-Tu Nguyen, Marc Potters, Jean-Philippe Bouchaud (2014). *Risk Premia: Asymmetric Tail Risks and Excess Returns*. SSRN Electronic Journal.

- <a id="ref-Lyons2014RoughStreams"></a>**[Lyo14]** Terry Lyons (2014). *Rough paths, Signatures and the modelling of functions on streams*. Proceedings of the International Congress of Mathematicians, Korea.

- <a id="ref-Lyons1998DifferentialSignals."></a>**[Lyo98]** Terry  J. Lyons (1998). *Differential equations driven by rough signals.*. Revista Matemática Iberoamericana (Vol. 14, No. 2, pp. 215– 310).

- <a id="ref-Morel2023PathMonte-Carlo"></a>**[MMB23]** Rudy Morel, Stéphane Mallat, Jean-Philippe Bouchaud (2023). *Path Shadowing Monte-Carlo*.

- <a id="ref-Moskowitz2012TimeMomentum"></a>**[MOP12]** Tobias  J. Moskowitz, Yao  Hua Ooi, Lasse  Heje Pedersen (2012). *Time series momentum*. Journal of Financial Economics (Vol. 104, No. 2, pp. 228– 250).

- <a id="ref-Mudchanatongsuk2008OptimalApproach"></a>**[MPW08]** Supakorn Mudchanatongsuk, James  A. Primbs, Wilfred Wong (2008). *Optimal pairs trading: A stochastic control approach*. Proceedings of the American Control Conference (pp. 1035– 1039).

- <a id="ref-Markowitz1952PortfolioSelection"></a>**[Mar52]** Harry Markowitz (1952). *Portfolio Selection*. The Journal of Finance (Vol. 7, No. 1, pp. 77– 91).

- <a id="ref-Ng1992AReturns"></a>**[NER92]** Victor Ng, Robert  F Engle, Michael Rothschild (1992). *A multi-dynamic-factor model for stock returns*. Journal of Econometrics (Vol. 52, pp. 2455266).

- <a id="ref-Ni2020ConditionalGenerationb"></a>**[Ni+20]** Hao Ni, Lukasz Szpruch, Magnus Wiese, Shujian Liao, Baoren Xiao (2020). *Conditional Sig-Wasserstein GANs for Time Series Generation*.

- <a id="ref-Ni2021Sig-WassersteinGeneration"></a>**[Ni+21]** Hao Ni, Lukasz Szpruch, Marc Sabate-Vidales, Baoren Xiao, Magnus Wiese, Shujian Liao (2021). *Sig-Wasserstein GANs for Time Series Generation*. ICAIF 2021 - 2nd ACM International Conference on AI in Finance.

- <a id="ref-Perkowski2016PathwiseFinance"></a>**[PP16]** Nicolas Perkowski, David  J. Prömel (2016). *Pathwise stochastic integrals for model free finance*. Bernoulli (Vol. 22, No. 4, pp. 2486– 2520).

- <a id="ref-Pretorius2022DeepManagement"></a>**[PZ22]** Ruan Pretorius, Terence Zyl (2022). *Deep Reinforcement Learning and Convex Mean-Variance Optimisation for Portfolio Management*.

- <a id="ref-PerezArribas2020SignaturesFinance"></a>**[Per20]** Imanol Perez\bibnamedelima Arribas (2020). *Signatures in machine learning and finance*.

- <a id="ref-RichardJMartin2012Non-linearStrategies"></a>**[RA12]** Unknown (2012). *Non-linear momentum strategies*. Risk (Vol. 25, No. 11, pp. 60– 65).

- <a id="ref-RichardJMartin2012MomentumMe"></a>**[RD12]** Unknown (2012). *Momentum trading: ’skews me*. Risk (Vol. 25, No. 8, pp. 84– 89).

- <a id="ref-Rej2017YouWorrying"></a>**[RSB17]** Adam Rej, Philip Seager, Jean-Philippe Bouchaud (2017). *You are in a drawdown. When should you start worrying?*. Wilmott (Vol. 2018, No. 93, pp. 56– 59).

- <a id="ref-Riga2016ATrading"></a>**[Rig16a]** Candia Riga (2016). *A pathwise approach to continuous-time trading*.

- <a id="ref-Riga2016PathwiseFinance"></a>**[Rig16b]** Candia Riga (2016). *Pathwise functional calculus and applications to continuous-time finance*.

- <a id="ref-Sanchez-Betancourt2022BrokersSignals"></a>**[SC22]** Leandro Sánchez-Betancourt, Alvaro Cartea (2022). *Brokers and Informed Traders: dealing with toxic flow and extracting trading signals*.

- <a id="ref-Stock2010DynamicModels"></a>**[SW10]** James  H Stock, Mark  W Watson (2010). *Dynamic Factor Models*. Handbook of Macroeconomics (Vol. 2A).

- <a id="ref-Sharpe1964CapitalRisk"></a>**[Sha64]** William  F. Sharpe (1964). *Capital Asset Prices: A Theory of Market Equilibrium Under Conditions of Risk*. The Journal of Finance (Vol. 19, No. 3, pp. 425– 442).

- <a id="ref-Sood2023DeepOptimization"></a>**[Soo+23]** Srijan Sood, Kassiani Papasotiriou, Marius Vaiciulis, Tucker Balch, J  P Morgan, A  I Research (2023). *Deep Reinforcement Learning for Optimal Portfolio Allocation: A Comparative Study with Mean-Variance Optimization*.

- <a id="ref-VanStaden2021ACosts"></a>**[Van+21]** Pieter  M Van\bibnamedelima Staden, Yuying Li,  Peter, A Forsyth (2021). *A data-driven neural network approach to dynamic factor investing with transaction costs*.

- <a id="ref-Vidyamurthy2004PairsAnalysis"></a>**[Vid04]** Ganapathy. Vidyamurthy (2004). *Pairs trading: Quantitative Methods and Analysis*.

- <a id="ref-Wiese2023Sig-Splines:Models"></a>**[WKM23]** Magnus Wiese, Ralf Korn, Phillip Murray (2023). *Sig-Splines: universal approximation and convex calibration of time series generative models*.

- <a id="ref-Wang2019Continuous-TimeFramework"></a>**[WZ19]** Haoran Wang, Xun  Yu Zhou (2019). *Continuous-Time Mean-Variance Portfolio Selection: A Reinforcement Learning Framework*.

- <a id="ref-Wang2019PortfolioLearning"></a>**[Wan19]** Kewei Wang (2019). *Portfolio Optimisation under Rough Stochastic Volatility via Machine Learning*.

- <a id="ref-Wiese2019QuantSeries"></a>**[Wie+19]** Magnus Wiese, Robert Knobloch, Ralf Korn, Peter Kretschmer (2019). *Quant GANs: Deep Generation of Financial Time Series*. Quantitative Finance (Vol. 20, No. 9, pp. 1419– 1440).

- <a id="ref-Zhang2020DeepOptimization"></a>**[ZZR20a]** Zihao Zhang, Stefan Zohren, Stephen Roberts (2020). *Deep Learning for Portfolio Optimization*. The Journal of Financial Data Science (Vol. 2, No. 4, pp. 8– 20).

- <a id="ref-Zhang2020DeepTrading"></a>**[ZZR20b]** Zihao Zhang, Stefan Zohren, Stephen Roberts (2020). *Deep Reinforcement Learning for Trading*. The Journal of Financial Data Science (Vol. 2, No. 2, pp. 25– 40).

- <a id="ref-Zhang2021ALearning"></a>**[Zha+21]** Chao Zhang, Zihao Zhang, Mihai Cucuringu, Stefan Zohren (2021). *A Universal End-to-End Approach to Portfolio Optimization via Deep Learning*.
