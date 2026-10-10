"""
Options Pricing & Greeks Engine Module.
Implements Black-Scholes-Merton continuous pricing for crypto options,
dynamic implied volatility modeling with Volatility Risk Premium (VRP),
Greeks calculations (Delta, Gamma, Theta, Vega), and Deribit fee/slippage structures.
"""
import numpy as np
from scipy.stats import norm
from typing import Dict, Any, Tuple

class BlackScholesPricer:
    """
    Continuous Black-Scholes-Merton Options Engine for Crypto Assets.
    """
    def __init__(self, risk_free_rate: float = 0.05, vrp: float = 0.08):
        self.r = risk_free_rate
        self.vrp = vrp  # Volatility Risk Premium (Crypto IV typically trades above RV)

    @staticmethod
    def _d1_d2(S: float, K: float, T: float, r: float, sigma: float) -> Tuple[float, float]:
        if T <= 1e-6 or sigma <= 1e-6:
            return 0.0, 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return d1, d2

    def price_call(self, S: float, K: float, T: float, sigma: float) -> float:
        """
        Calculates Call Option price.
        T is in years (e.g. hours / 8760).
        """
        if T <= 1e-6:
            return max(0.0, S - K)
        sigma = max(1e-4, sigma)
        d1, d2 = self._d1_d2(S, K, T, self.r, sigma)
        call = S * norm.cdf(d1) - K * np.exp(-self.r * T) * norm.cdf(d2)
        return max(0.0, float(call))

    def price_put(self, S: float, K: float, T: float, sigma: float) -> float:
        """
        Calculates Put Option price.
        T is in years.
        """
        if T <= 1e-6:
            return max(0.0, K - S)
        sigma = max(1e-4, sigma)
        d1, d2 = self._d1_d2(S, K, T, self.r, sigma)
        put = K * np.exp(-self.r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return max(0.0, float(put))

    def calculate_greeks(self, S: float, K: float, T: float, sigma: float, option_type: str = 'call') -> Dict[str, float]:
        """
        Calculates Delta, Gamma, Theta (per day), and Vega (per 1% IV move).
        """
        if T <= 1e-6:
            if option_type == 'call':
                delta = 1.0 if S > K else 0.0
            else:
                delta = -1.0 if S < K else 0.0
            return {'delta': delta, 'gamma': 0.0, 'theta_per_day': 0.0, 'vega_1pct': 0.0}

        sigma = max(1e-4, sigma)
        d1, d2 = self._d1_d2(S, K, T, self.r, sigma)
        pdf_d1 = norm.pdf(d1)
        sqrt_T = np.sqrt(T)

        gamma = pdf_d1 / (S * sigma * sqrt_T + 1e-9)
        vega_annual = S * sqrt_T * pdf_d1
        vega_1pct = vega_annual * 0.01

        if option_type == 'call':
            delta = norm.cdf(d1)
            theta_annual = -(S * pdf_d1 * sigma) / (2 * sqrt_T) - self.r * K * np.exp(-self.r * T) * norm.cdf(d2)
        else:
            delta = norm.cdf(d1) - 1.0
            theta_annual = -(S * pdf_d1 * sigma) / (2 * sqrt_T) + self.r * K * np.exp(-self.r * T) * norm.cdf(-d2)

        theta_per_day = theta_annual / 365.0
        return {
            'delta': float(delta),
            'gamma': float(gamma),
            'theta_per_day': float(theta_per_day),
            'vega_1pct': float(vega_1pct)
        }

    def estimate_implied_volatility(self, realized_vol_24h: float) -> float:
        """
        Estimates market Implied Volatility by adding the Volatility Risk Premium (VRP).
        """
        return max(0.15, realized_vol_24h + self.vrp)

    @staticmethod
    def calculate_deribit_fee(spot_price: float, option_premium: float, fee_underlying_pct: float = 0.0003, max_cap_pct: float = 0.125) -> float:
        """
        Computes standard Deribit crypto options fee:
        0.03% of underlying spot, capped at 12.5% of option premium.
        """
        base_fee = spot_price * fee_underlying_pct
        max_fee = option_premium * max_cap_pct
        return min(base_fee, max_fee)
