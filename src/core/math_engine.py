"""
Mathematical & Quantitative Core Engine.
Implements specifications from ChatGPT/MD_Source (Tahap A through Tahap Z/AG):
- Market State Vector s_t (Tahap A)
- Factor & Benchmark Decomposition (Tahap 3 & Tahap B)
- 4-State Global Market Regime Identification (Tahap B & Tahap M)
- Asymmetric Expected Value E[X] (Tahap C, D & strategy.md)
- Combinatorial / QUBO Quadratic Portfolio Optimizer (Tahap G, N, Z & AG)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum

class MarketRegime(Enum):
    BULL_TREND = "BULL_TREND"
    BEAR_TREND = "BEAR_TREND"
    MEAN_REVERSION_CHOP = "MEAN_REVERSION_CHOP"
    HIGH_VOLATILITY_CRISIS = "HIGH_VOLATILITY_CRISIS"

class MathEngine:
    """
    Asset-Agnostic Quantitative Mathematical Engine.
    All calculations operate on dimensionless normalized series.
    """

    @staticmethod
    def calculate_log_returns(prices: pd.Series) -> pd.Series:
        """Calculates log returns: r_t = ln(P_t / P_{t-1})."""
        arr = prices.values
        if len(arr) < 2:
            return pd.Series(0.0, index=prices.index)
        ret = np.zeros(len(arr))
        ret[1:] = np.log(arr[1:] / (arr[:-1] + 1e-8))
        return pd.Series(ret, index=prices.index)

    @staticmethod
    def calculate_garman_klass_volatility(df: pd.DataFrame, window: int = 14) -> pd.Series:
        """
        Calculates Garman-Klass high-low-open-close volatility estimator.
        sigma_GK^2 = 0.5 * (ln(H/L))^2 - (2*ln(2) - 1) * (ln(C/O))^2
        """
        sub_df = df.tail(window * 2) if len(df) > window * 2 else df
        h = sub_df['high'].values
        l = sub_df['low'].values
        c = sub_df['close'].values
        o = sub_df['open'].values

        log_hl = np.log(h / (l + 1e-8))
        log_co = np.log(c / (o + 1e-8))
        
        rs = 0.5 * (log_hl ** 2) - (2 * np.log(2) - 1) * (log_co ** 2)
        if len(rs) >= window:
            vol_val = np.sqrt(np.mean(rs[-window:]))
        else:
            vol_val = np.sqrt(np.mean(rs)) if len(rs) > 0 else 0.01
        
        return pd.Series([vol_val], index=[sub_df.index[-1]])

    @staticmethod
    def calculate_beta_alpha(asset_returns: pd.Series, benchmark_returns: pd.Series) -> Tuple[float, float]:
        """
        Decomposes asset return into Alpha and Beta relative to market benchmark.
        r_i,t = alpha_i + beta_i * r_M,t + epsilon_i
        """
        r_i = asset_returns.values if hasattr(asset_returns, 'values') else np.array(asset_returns)
        r_m = benchmark_returns.values if hasattr(benchmark_returns, 'values') else np.array(benchmark_returns)

        min_len = min(len(r_i), len(r_m))
        if min_len < 5:
            return 0.0, 1.0

        r_i = r_i[-min_len:]
        r_m = r_m[-min_len:]

        var_m = np.var(r_m, ddof=1)
        if var_m < 1e-8:
            return 0.0, 1.0

        cov_im = np.cov(r_i, r_m, ddof=1)[0, 1]
        beta = float(cov_im / var_m)
        alpha = float(np.mean(r_i) - beta * np.mean(r_m))
        return alpha, beta

    @staticmethod
    def calculate_vwap_bands(df: pd.DataFrame, window: int = 24, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Calculates Volume-Weighted Average Price and Gaussian Standard Deviation Bands.
        Returns: (vwap, upper_band, lower_band, z_score_distance)
        """
        sub_df = df.tail(window)
        h = sub_df['high'].values
        l = sub_df['low'].values
        c = sub_df['close'].values
        vol = sub_df['volume'].values

        tp = (h + l + c) / 3.0
        tot_vol = np.sum(vol) + 1e-8
        vwap_val = np.sum(tp * vol) / tot_vol

        variance = np.sum(((tp - vwap_val) ** 2) * vol) / tot_vol
        std_val = np.sqrt(max(variance, 1e-8))

        upper_val = vwap_val + (num_std * std_val)
        lower_val = vwap_val - (num_std * std_val)
        
        current_close = float(c[-1])
        z_dist = (current_close - vwap_val) / std_val

        idx = sub_df.index
        return pd.Series([vwap_val], index=[idx[-1]]), pd.Series([upper_val], index=[idx[-1]]), pd.Series([lower_val], index=[idx[-1]]), z_dist

    @staticmethod
    def detect_market_regime(
        benchmark_df: pd.DataFrame,
        macro_factors: Optional[Dict[str, float]] = None,
        vol_lookback: int = 24
    ) -> Tuple[MarketRegime, Dict[str, Any]]:
        """
        Identifies Global Market Regime (Tahap B & Tahap M).
        """
        if benchmark_df is None or len(benchmark_df) < 5:
            return MarketRegime.MEAN_REVERSION_CHOP, {"reason": "Insufficient data"}

        closes = benchmark_df['close'].values
        lookback = min(vol_lookback, len(closes) - 1)
        if lookback < 2:
            return MarketRegime.MEAN_REVERSION_CHOP, {"reason": "Insufficient data"}

        tail_closes = closes[-lookback:]
        log_rets = np.log(tail_closes[1:] / (tail_closes[:-1] + 1e-8))
        
        cum_return = float(np.sum(log_rets))
        current_vol = float(np.std(log_rets) * np.sqrt(365 * 24))

        sma_fast = float(np.mean(closes[-min(12, len(closes)):]))
        sma_slow = float(np.mean(tail_closes))
        trend_direction = 1 if sma_fast > sma_slow else -1

        macro_stress = False
        if macro_factors:
            dxy = macro_factors.get("DXY", 100.0)
            vix = macro_factors.get("VIX", 20.0)
            if vix > 30.0 or dxy > 108.0:
                macro_stress = True

        if current_vol > 0.60 or macro_stress:
            regime = MarketRegime.HIGH_VOLATILITY_CRISIS
            reason = f"Volatility spike ({current_vol:.1%}) or Macro stress."
        elif cum_return > 0.015 and trend_direction > 0:
            regime = MarketRegime.BULL_TREND
            reason = f"Positive drift (+{cum_return:.2%})."
        elif cum_return < -0.015 and trend_direction < 0:
            regime = MarketRegime.BEAR_TREND
            reason = f"Negative drift ({cum_return:.2%})."
        else:
            regime = MarketRegime.MEAN_REVERSION_CHOP
            reason = f"Sideways returns ({cum_return:.2%})."

        metrics = {
            "regime": regime.value,
            "reason": reason,
            "cum_return": cum_return,
            "annualized_vol": current_vol,
            "trend_direction": trend_direction
        }
        return regime, metrics

    @staticmethod
    def calculate_expected_value(win_rate: float, reward_r: float, risk_r: float = 1.0) -> float:
        """
        Calculates expected value E[X] = (P_win * R_reward) - (P_loss * R_risk).
        """
        p_win = np.clip(win_rate, 0.0, 1.0)
        p_loss = 1.0 - p_win
        return float((p_win * reward_r) - (p_loss * risk_r))

    @staticmethod
    def solve_qubo_portfolio(
        mu: np.ndarray,
        sigma: np.ndarray,
        lambda_risk: float = 0.5,
        max_assets: int = 3
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Solves combinatorial asset selection & weighting.
        """
        n = len(mu)
        if n == 0:
            return np.array([]), np.array([])
        if n <= max_assets:
            x_best = np.ones(n, dtype=int)
            w_best = np.ones(n) / n
            return x_best, w_best

        best_score = -1e9
        x_best = np.zeros(n, dtype=int)
        w_best = np.zeros(n)

        from itertools import combinations
        for k in range(1, max_assets + 1):
            for combo in combinations(range(n), k):
                x_cand = np.zeros(n, dtype=int)
                x_cand[list(combo)] = 1
                
                sub_sigma = sigma[np.ix_(combo, combo)]
                sub_mu = mu[list(combo)]
                
                inv_diag = 1.0 / (np.diag(sub_sigma) + 1e-6)
                sub_w = inv_diag / np.sum(inv_diag)
                
                port_return = np.dot(sub_w, sub_mu)
                port_var = np.dot(sub_w, np.dot(sub_sigma, sub_w))
                
                utility = port_return - (lambda_risk * port_var)
                if utility > best_score:
                    best_score = utility
                    x_best = x_cand
                    w_full = np.zeros(n)
                    w_full[list(combo)] = sub_w
                    w_best = w_full

        return x_best, w_best
