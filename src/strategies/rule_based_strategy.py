"""
Generic no-code strategy engine, driven entirely by a JSON rule config
produced by the Strategy Builder web UI (ui/pages/4_Strategy_Builder.py).

Unlike the other strategies in this folder (momentum.py,
vwap_rejection.py, etc.) which hardcode their signal logic in Python,
RuleBasedStrategy interprets a declarative config: a list of indicators to
compute, a list of comparison rules between those indicators (or raw
price fields), and how to combine them (AND / OR).

Config schema (see the Strategy Builder page for the form that produces
this, and custom_strategies.json for where it's stored):

{
  "enabled": true,
  "indicators": [
    {"id": "rsi14", "type": "RSI", "period": 14},
    {"id": "sma50", "type": "SMA", "period": 50}
  ],
  "entry_rules": [
    {"left": "rsi14", "op": "<", "right_type": "value", "right": 30},
    {"left": "close", "op": ">", "right_type": "indicator", "right": "sma50"}
  ],
  "combine_logic": "AND",       # or "OR"
  "direction": "long",          # or "short"
  "signal_strength": 2.0,       # magnitude returned when the rule set fires
  "risk_budget": 0.01
}

Supported indicator "type" values: SMA, EMA, RSI, MACD_HIST, BB_UPPER,
BB_MIDDLE, BB_LOWER, ATR, VWAP. Every indicator needs an "id" (used to
reference it from entry_rules) and a "period" (plus "num_std" for
Bollinger Bands, "fast"/"slow"/"signal" for MACD_HIST).

Supported "left"/"right" references in entry_rules: an indicator "id"
defined above, or a raw price field ("open", "high", "low", "close",
"volume").

Supported "op" values: ">", "<", ">=", "<=", "crosses_above",
"crosses_below".
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

from src.strategies.base_strategy import BaseStrategy

PRICE_FIELDS = {"open", "high", "low", "close", "volume"}


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Standard Wilder-style RSI (simple moving average version)."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def compute_indicator_series(df: pd.DataFrame, spec: Dict[str, Any]) -> pd.Series:
    """Computes a full indicator series (not just the last value) so that
    crosses_above/crosses_below rules can compare the current bar against
    the previous one."""
    itype = spec.get("type")

    if itype == "SMA":
        return df["close"].rolling(int(spec.get("period", 20))).mean()

    if itype == "EMA":
        return df["close"].ewm(span=int(spec.get("period", 20)), adjust=False).mean()

    if itype == "RSI":
        return _rsi(df["close"], int(spec.get("period", 14)))

    if itype == "MACD_HIST":
        fast = int(spec.get("fast", 12))
        slow = int(spec.get("slow", 26))
        signal = int(spec.get("signal", 9))
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        return macd_line - signal_line

    if itype in ("BB_UPPER", "BB_MIDDLE", "BB_LOWER"):
        period = int(spec.get("period", 20))
        num_std = float(spec.get("num_std", 2.0))
        mid = df["close"].rolling(period).mean()
        std = df["close"].rolling(period).std()
        if itype == "BB_UPPER":
            return mid + num_std * std
        if itype == "BB_LOWER":
            return mid - num_std * std
        return mid

    if itype == "ATR":
        period = int(spec.get("period", 14))
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    if itype == "VWAP":
        window = int(spec.get("period", 24))
        tp = (df["high"] + df["low"] + df["close"]) / 3.0
        pv = tp * df["volume"]
        vol_sum = df["volume"].rolling(window).sum().replace(0, np.nan)
        return pv.rolling(window).sum() / vol_sum

    raise ValueError(f"Unknown indicator type: {itype!r}")


class RuleBasedStrategy(BaseStrategy):
    """No-code strategy: evaluates a set of comparison rules against
    computed indicators and raw price fields, combined with AND/OR."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.indicators: List[Dict[str, Any]] = config.get("indicators", [])
        self.entry_rules: List[Dict[str, Any]] = config.get("entry_rules", [])
        self.combine_logic: str = str(config.get("combine_logic", "AND")).upper()
        self.direction: str = str(config.get("direction", "long")).lower()
        self.signal_strength: float = float(config.get("signal_strength", 2.0))

        # Determine minimum required bars for all indicators
        min_bars = 2
        for spec in self.indicators:
            period = int(spec.get("period", 20))
            if spec.get("type") == "MACD_HIST":
                period = int(spec.get("slow", 26)) + int(spec.get("signal", 9))
            min_bars = max(min_bars, period + 2)
        self._min_bars = min_bars

    def generate_signal(self, ohlcv_df: pd.DataFrame) -> float:
        if ohlcv_df is None or len(ohlcv_df) < self._min_bars:
            return 0.0
        if not self.entry_rules:
            return 0.0

        series_cache: Dict[str, pd.Series] = {}
        for spec in self.indicators:
            try:
                series_cache[spec["id"]] = compute_indicator_series(ohlcv_df, spec)
            except Exception:
                return 0.0

        def _resolve(key: str) -> pd.Series:
            if key in PRICE_FIELDS:
                return ohlcv_df[key]
            if key in series_cache:
                return series_cache[key]
            raise KeyError(f"Unknown indicator/field reference: {key!r}")

        results: List[bool] = []
        for rule in self.entry_rules:
            try:
                left_series = _resolve(rule["left"])
                op = rule.get("op", ">")
                if rule.get("right_type") == "indicator":
                    right_series = _resolve(rule["right"])
                else:
                    right_series = pd.Series(float(rule["right"]), index=ohlcv_df.index)

                cur_l, prev_l = left_series.iloc[-1], left_series.iloc[-2]
                cur_r, prev_r = right_series.iloc[-1], right_series.iloc[-2]

                if pd.isna(cur_l) or pd.isna(cur_r) or pd.isna(prev_l) or pd.isna(prev_r):
                    results.append(False)
                    continue

                if op == ">":
                    ok = cur_l > cur_r
                elif op == "<":
                    ok = cur_l < cur_r
                elif op == ">=":
                    ok = cur_l >= cur_r
                elif op == "<=":
                    ok = cur_l <= cur_r
                elif op == "crosses_above":
                    ok = (prev_l <= prev_r) and (cur_l > cur_r)
                elif op == "crosses_below":
                    ok = (prev_l >= prev_r) and (cur_l < cur_r)
                else:
                    ok = False

                results.append(bool(ok))
            except Exception:
                results.append(False)

        if not results:
            return 0.0

        triggered = all(results) if self.combine_logic == "AND" else any(results)
        if not triggered:
            return 0.0

        return self.signal_strength if self.direction == "long" else -self.signal_strength
