"""
Data loading utilities for the TradeProject Streamlit dashboard.

Reads the JSON files written by the trading worker (run_scheduler.py) and
turns them into pandas DataFrames / dicts that are easy to display in
Streamlit. This module is READ-ONLY: it never writes to the ledger and
never touches the trading engine.

Files it reads (relative to the project root, where `streamlit run` is
launched from):
  - config.json               -> INITIAL_CAPITAL, trading pairs, etc.
  - logs/paper_ledger.json    -> raw per-strategy state (capital, trades,
                                  equity curve), written by
                                  src/paper_trader.py
  - logs/leaderboard.json     -> pre-computed performance metrics per
                                  strategy, written by src/leaderboard.py
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

CONFIG_PATH = "config.json"
LEDGER_PATH = os.path.join("logs", "paper_ledger.json")
LEADERBOARD_PATH = os.path.join("logs", "leaderboard.json")

DEFAULT_INITIAL_CAPITAL = 10000.0


def _safe_read_json(path: str, retries: int = 3, delay: float = 0.15) -> Optional[Dict[str, Any]]:
    """Read a JSON file, retrying briefly in case the worker process is
    writing to it at the exact same moment. Returns None if the file does
    not exist yet or cannot be read after all retries."""
    if not os.path.exists(path):
        return None

    last_error: Optional[Exception] = None
    for _ in range(retries):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            last_error = e
            time.sleep(delay)

    print(f"[data_loader] Failed to read {path} after {retries} attempts: {last_error}")
    return None


@st.cache_data(ttl=30, show_spinner=False)
def load_config() -> Dict[str, Any]:
    """Load config.json (not the strategy_config.json)."""
    return _safe_read_json(CONFIG_PATH) or {}


@st.cache_data(ttl=10, show_spinner=False)
def load_ledger() -> Dict[str, Any]:
    """Load logs/paper_ledger.json. Returns {} if missing/unreadable."""
    return _safe_read_json(LEDGER_PATH) or {}


@st.cache_data(ttl=10, show_spinner=False)
def load_leaderboard() -> Dict[str, Any]:
    """Load logs/leaderboard.json. Returns {} if missing/unreadable."""
    return _safe_read_json(LEADERBOARD_PATH) or {}


def get_initial_capital() -> float:
    """Reads INITIAL_CAPITAL from config.json so PnL numbers on the
    dashboard match what the engine is actually using, instead of assuming
    a hardcoded $10,000 (note: src/leaderboard.py currently hardcodes
    10000.0 internally -- keep that in mind if the two disagree)."""
    cfg = load_config()
    return float(cfg.get("INITIAL_CAPITAL", DEFAULT_INITIAL_CAPITAL))


def get_strategy_names(ledger: Dict[str, Any]) -> List[str]:
    """Strategy entries are plain top-level keys; metadata keys are
    prefixed with an underscore (e.g. `_benchmark_meta`)."""
    return [k for k in ledger.keys() if not k.startswith("_")]


def get_benchmark_meta(ledger: Dict[str, Any]) -> Dict[str, Any]:
    return ledger.get("_benchmark_meta", {})


def get_equity_curve_df(ledger: Dict[str, Any], strategy_name: str) -> pd.DataFrame:
    """Returns a DataFrame with columns [timestamp, equity, drawdown_pct]
    for a single strategy. Empty DataFrame if there's no equity curve yet
    (e.g. the worker hasn't completed a tick for this strategy)."""
    strat = ledger.get(strategy_name, {})
    curve = strat.get("equity_curve", [])
    if not curve:
        return pd.DataFrame(columns=["timestamp", "equity", "drawdown_pct"])

    df = pd.DataFrame(curve)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    else:
        df["timestamp"] = pd.RangeIndex(len(df))

    if "equity" not in df.columns:
        df["equity"] = strat.get("capital", get_initial_capital())

    df = df.sort_values("timestamp").reset_index(drop=True)
    running_peak = df["equity"].cummax()
    df["drawdown_pct"] = ((df["equity"] - running_peak) / running_peak.replace(0, pd.NA)) * 100.0
    df["drawdown_pct"] = df["drawdown_pct"].fillna(0.0)
    return df


def get_trades_df(ledger: Dict[str, Any], strategy_name: str) -> pd.DataFrame:
    """Returns closed trades for one strategy as a DataFrame (empty if
    none yet). Actual fields written by
    src/core/position_lifecycle_manager.py are: symbol, direction (1/-1),
    entry_price, exit_price, net_pnl, return_pct, entry_time, exit_time,
    exit_reason -- NOT open_time/close_time."""
    strat = ledger.get(strategy_name, {})
    trades = strat.get("closed_trades", [])
    if not trades:
        return pd.DataFrame()

    df = pd.DataFrame(trades)
    for col in ("entry_time", "exit_time"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    if "direction" in df.columns:
        df["side"] = df["direction"].map({1: "Long", -1: "Short"}).fillna("Unknown")
    return df


def get_all_trades_df(ledger: Dict[str, Any]) -> pd.DataFrame:
    """Returns closed trades across ALL strategies, with a `strategy`
    column added, concatenated into one DataFrame. Empty DataFrame if no
    trades exist anywhere yet."""
    frames = []
    for name in get_strategy_names(ledger):
        df = get_trades_df(ledger, name)
        if df.empty:
            continue
        df = df.copy()
        df.insert(0, "strategy", name)
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    if "exit_time" in combined.columns:
        combined = combined.sort_values("exit_time", ascending=False).reset_index(drop=True)
    return combined


def get_strategy_summary_rows(ledger: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Quick per-strategy summary for the Overview page (uses raw ledger
    data, not the pre-computed leaderboard metrics -- see leaderboard page
    for Sharpe/win-rate/etc.)."""
    initial_capital = get_initial_capital()
    rows = []
    for name in get_strategy_names(ledger):
        strat = ledger[name]
        capital = strat.get("capital", initial_capital)
        rows.append({
            "Strategi": name,
            "Equity": capital,
            "PnL": capital - initial_capital,
            "Trades": len(strat.get("closed_trades", [])),
            "Posisi Terbuka": len(strat.get("open_positions", {})),
            "Order Pending": len(strat.get("pending_orders", {})),
        })
    return rows


def get_overview_metrics(ledger: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate quick numbers across all strategies for the Overview
    page's top metric cards."""
    rows = get_strategy_summary_rows(ledger)
    return {
        "num_strategies": len(rows),
        "total_equity": sum(r["Equity"] for r in rows),
        "total_pnl": sum(r["PnL"] for r in rows),
        "total_open_positions": sum(r["Posisi Terbuka"] for r in rows),
        "total_trades": sum(r["Trades"] for r in rows),
    }
