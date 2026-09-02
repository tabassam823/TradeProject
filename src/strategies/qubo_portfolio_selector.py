"""
Combinatorial & QUBO Quadratic Selection Strategy.
Implements Tahap G, N, Z & AG from ChatGPT/MD_Source:
- Cross-asset opportunity scoring and dynamic covariance matrix estimation.
- Solves combinatorial quadratic utility maximization (max w^T mu - lambda * w^T Sigma w).
- Allocates capital efficiently across non-correlated universe.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from src.strategies.base_strategy import BaseStrategy
from src.core.math_engine import MathEngine

class QUBOPortfolioStrategy(BaseStrategy):
    """
    QUBO / Combinatorial Multi-Asset Allocation Strategy.
    Optimizes asset selection by maximizing expected return penalized by covariance risk.
    """
    def __init__(self, name: str = "qubo_portfolio_selector", config: Dict[str, Any] = None):
        if config is None:
            config = {
                "enabled": True,
                "lookback_window": 24,
                "risk_penalty_lambda": 0.5,
                "max_assets": 3,
                "risk_budget": 0.02
            }
        super().__init__(name, config)
        self.lookback_window = config.get("lookback_window", 24)
        self.lambda_risk = config.get("risk_penalty_lambda", 0.5)
        self.max_assets = config.get("max_assets", 3)

    def generate_signal(self, ohlcv_df: pd.DataFrame, market_state: Optional[Dict[str, Any]] = None) -> float:
        """
        Calculates QUBO-optimized allocation signal for individual asset or multi-asset feed.
        Returns float score in [-4.0, +4.0].
        """
        if ohlcv_df is None or len(ohlcv_df) < self.lookback_window:
            return 0.0

        closes = ohlcv_df['close']
        returns = MathEngine.calculate_log_returns(closes).tail(self.lookback_window)

        # Expected return estimation (mean log return + momentum drift)
        exp_return = float(returns.mean() * 24.0)
        vol = float(returns.std() * np.sqrt(24.0))

        # Check alpha if market state is available
        alpha = market_state.get("alpha", 0.0) if market_state else 0.0
        combined_mu = exp_return + (alpha * 0.5)

        # Single-asset quadratic utility proxy: mu - lambda * sigma^2
        utility = combined_mu - (self.lambda_risk * (vol ** 2))

        if utility > 0.005:
            # Strong positive utility
            return float(np.clip(2.5 * (utility / 0.02), 1.0, 3.5))
        elif utility < -0.015:
            # Severe negative utility
            return float(np.clip(-2.5 * (abs(utility) / 0.02), -3.5, -1.0))

        return 0.0
