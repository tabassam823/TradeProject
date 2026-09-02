"""
Factor & Market Regime Conditioned Strategy.
Implements Tahap A & Tahap B from ChatGPT/MD_Source:
- Multi-factor signal decomposition (Alpha vs Beta, Normalized Momentum, Volatility state).
- Dynamic weighting conditioned on Global Market Regime.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from src.strategies.base_strategy import BaseStrategy
from src.core.math_engine import MathEngine, MarketRegime

class FactorRegimeStrategy(BaseStrategy):
    """
    Factor-Regime Adaptive Strategy.
    Generates alpha-driven signals conditioned on whether the macro market is in
    BULL_TREND, BEAR_TREND, MEAN_REVERSION_CHOP, or HIGH_VOLATILITY_CRISIS.
    """
    def __init__(self, name: str = "factor_regime_adaptive", config: Dict[str, Any] = None):
        if config is None:
            config = {
                "enabled": True,
                "fast_lookback": 12,
                "slow_lookback": 36,
                "min_alpha_threshold": 0.0005,
                "risk_budget": 0.015
            }
        super().__init__(name, config)
        self.fast_lookback = config.get("fast_lookback", 12)
        self.slow_lookback = config.get("slow_lookback", 36)
        self.min_alpha = config.get("min_alpha_threshold", 0.0005)

    def generate_signal(self, ohlcv_df: pd.DataFrame, market_state: Optional[Dict[str, Any]] = None) -> float:
        """
        Calculates regime-conditioned factor signal.
        Returns float score in [-4.0, +4.0].
        """
        if ohlcv_df is None or len(ohlcv_df) < self.slow_lookback:
            return 0.0

        closes = ohlcv_df['close']
        returns = MathEngine.calculate_log_returns(closes)

        # Factor 1: Normalized Momentum Factor
        fast_ret = returns.tail(self.fast_lookback).sum()
        slow_ret = returns.tail(self.slow_lookback).sum()
        mom_factor = (fast_ret - (slow_ret * (self.fast_lookback / self.slow_lookback)))

        # Factor 2: Idiosyncratic Alpha (if market_state provided)
        alpha = market_state.get("alpha", 0.0) if market_state else 0.0
        regime_str = market_state.get("regime", MarketRegime.MEAN_REVERSION_CHOP.value) if market_state else MarketRegime.MEAN_REVERSION_CHOP.value

        # Factor 3: Volatility Penalty / Scaling
        vol = MathEngine.calculate_garman_klass_volatility(ohlcv_df).iloc[-1]
        vol_scalar = 1.0 / (vol + 1e-4)
        vol_norm = np.clip(vol_scalar / 50.0, 0.5, 2.0)

        # Condition signals on Global Regime (Tahap B & Tahap M)
        if regime_str == MarketRegime.BULL_TREND.value:
            # Long trend continuation with alpha preference
            base_score = (2.0 if mom_factor > 0 else 0.0) + (1.5 if alpha > self.min_alpha else 0.0)
            return float(np.clip(base_score * vol_norm, -4.0, 4.0))

        elif regime_str == MarketRegime.BEAR_TREND.value:
            # Defensive / Short bias if idiosyncratic alpha is negative
            base_score = (-2.0 if mom_factor < 0 else 0.0) + (-1.5 if alpha < -self.min_alpha else 0.0)
            return float(np.clip(base_score * vol_norm, -4.0, 4.0))

        elif regime_str == MarketRegime.HIGH_VOLATILITY_CRISIS.value:
            # Crisis regime: scale down signals heavily / preserve capital
            return 0.0

        else: # MEAN_REVERSION_CHOP
            # Light counter-trend fade
            if fast_ret > 0.03:
                return -1.5
            elif fast_ret < -0.03:
                return 1.5
            return 0.0
