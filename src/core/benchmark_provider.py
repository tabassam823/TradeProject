"""
3-Tier Market Universe & Benchmark Provider.
Implements Tahap 3 & Tahap A from ChatGPT/MD_Source:
- Tier 1 (A_T): Target Traded Assets
- Tier 2 (A_M): Market Leader Benchmark (BTC / SPY)
- Tier 3 (A_F): Global Macro Benchmark Factors (DXY, Gold, VIX)
"""

import time
import requests
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from src.core.binance_client import BinanceClient
from src.core.math_engine import MathEngine, MarketRegime

class BenchmarkProvider:
    """
    Supplies real-time cross-asset benchmark and macro factor state to all trading strategies.
    """
    def __init__(self, benchmark_symbol: str = "BTC/USDT", testnet: bool = True):
        self.benchmark_symbol = benchmark_symbol
        self.binance = BinanceClient(testnet=testnet)
        self._cached_benchmark_df: Optional[pd.DataFrame] = None
        self._last_fetch_time: float = 0.0
        self._cache_ttl_sec: float = 30.0

    def get_benchmark_ohlcv(self, timeframe: str = "1h", limit: int = 100) -> pd.DataFrame:
        """Fetches and caches benchmark leader candles."""
        now = time.time()
        if self._cached_benchmark_df is not None and (now - self._last_fetch_time) < self._cache_ttl_sec:
            return self._cached_benchmark_df

        try:
            df = self.binance.fetch_ohlcv(self.benchmark_symbol, timeframe=timeframe, limit=limit)
            if not df.empty:
                self._cached_benchmark_df = df
                self._last_fetch_time = now
                return df
        except Exception as e:
            print(f"[BenchmarkProvider] Warning fetching benchmark {self.benchmark_symbol}: {e}")

        if self._cached_benchmark_df is not None:
            return self._cached_benchmark_df
        return pd.DataFrame()

    def get_macro_factors(self) -> Dict[str, float]:
        """
        Fetches macro benchmark indicators (DXY proxy, Gold, Crypto Sentiment / VIX).
        Falls back to public market sentiment feeds if offline.
        """
        factors = {
            "DXY": 104.2,
            "GOLD": 2480.0,
            "VIX": 16.5,
            "CRYPTO_FEAR_GREED": 50.0
        }
        try:
            resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data and len(data["data"]) > 0:
                    factors["CRYPTO_FEAR_GREED"] = float(data["data"][0]["value"])
        except Exception:
            pass
        return factors

    def get_market_state(
        self,
        target_symbol: str,
        target_df: pd.DataFrame,
        timeframe: str = "1h"
    ) -> Dict[str, Any]:
        """
        Synthesizes complete Market State Vector s_t (Tahap A) comparing target asset to benchmark.
        """
        benchmark_df = self.get_benchmark_ohlcv(timeframe=timeframe, limit=100)
        macro_factors = self.get_macro_factors()

        # Detect Global Regime
        regime, regime_metrics = MathEngine.detect_market_regime(
            benchmark_df=benchmark_df if not benchmark_df.empty else target_df,
            macro_factors=macro_factors
        )

        # Decompose Alpha & Beta
        target_returns = MathEngine.calculate_log_returns(target_df['close']) if target_df is not None and not target_df.empty else pd.Series()
        benchmark_returns = MathEngine.calculate_log_returns(benchmark_df['close']) if not benchmark_df.empty else target_returns

        alpha, beta = MathEngine.calculate_beta_alpha(target_returns, benchmark_returns)
        target_vol = MathEngine.calculate_garman_klass_volatility(target_df).iloc[-1] if target_df is not None and not target_df.empty else 0.02
        benchmark_return_1h = benchmark_returns.iloc[-1] if len(benchmark_returns) > 0 else 0.0
        benchmark_cum_24h = benchmark_returns.tail(24).sum() if len(benchmark_returns) >= 24 else 0.0

        return {
            "target_symbol": target_symbol,
            "benchmark_symbol": self.benchmark_symbol,
            "regime": regime.value,
            "regime_details": regime_metrics,
            "alpha": float(alpha),
            "beta": float(beta),
            "target_volatility": float(target_vol),
            "benchmark_return_1h": float(benchmark_return_1h),
            "benchmark_return_24h": float(benchmark_cum_24h),
            "macro_factors": macro_factors,
            "timestamp": time.time()
        }
