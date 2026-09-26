"""
mfe_mae_analyzer.py
Maximum Favorable Excursion (MFE) & Maximum Adverse Excursion (MAE) Trade Execution Analyzer.
Adapted and enhanced from Quant-Analysis-Toolkit (mfe_mae_analyzer.py).

Answers the key institutional execution questions:
1. "How much money was on the table during each trade, and how much did we actually capture?"
2. "Are our stop losses placed too close (choking trades that would have won) or too wide?"
3. "Are our profit targets leaving excessive gains on the table?"
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd


def compute_trade_mfe_mae(
    trades: List[Dict[str, Any]],
    ohlcv_df: pd.DataFrame,
    time_col: str = "timestamp",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close"
) -> pd.DataFrame:
    """
    Computes MFE, MAE, and Exit Efficiency for each closed trade against high-resolution OHLCV data.

    Parameters:
    -----------
    trades : List[Dict[str, Any]]
        List of trades. Each trade should have:
        - 'entry_time': datetime or timestamp
        - 'exit_time': datetime or timestamp
        - 'entry_price': float
        - 'exit_price': float
        - 'side': 'BUY'/'LONG' or 'SELL'/'SHORT'
        - 'pnl' (optional): float
    ohlcv_df : pd.DataFrame
        Candlestick price history covering the trade periods.

    Returns:
    --------
    pd.DataFrame: Analysis dataframe with columns:
        - trade_id, side, entry_time, exit_time, entry_price, exit_price
        - mfe_price, mae_price
        - mfe_pct, mae_pct
        - realized_ret_pct
        - exit_efficiency (realized_ret / mfe)
        - left_on_table_pct (mfe - realized_ret)
    """
    df = ohlcv_df.copy()
    if not isinstance(df.index, pd.DatetimeIndex) and time_col in df.columns:
        df[time_col] = pd.to_datetime(df[time_col])
        df = df.set_index(time_col)
    df = df.sort_index()

    records = []

    for idx, tr in enumerate(trades):
        entry_t = pd.to_datetime(tr.get("entry_time"))
        exit_t = pd.to_datetime(tr.get("exit_time"))
        entry_p = float(tr.get("entry_price", 0.0))
        exit_p = float(tr.get("exit_price", 0.0))
        side = str(tr.get("side", "LONG")).upper()
        is_long = "BUY" in side or "LONG" in side

        if entry_p <= 0 or exit_p <= 0:
            continue

        # Extract intrabar slice during trade holding period
        mask = (df.index >= entry_t) & (df.index <= exit_t)
        sub_df = df.loc[mask]

        if sub_df.empty:
            # Fallback to entry/exit prices if no intermediate bars
            highest = max(entry_p, exit_p)
            lowest = min(entry_p, exit_p)
        else:
            highest = float(sub_df[high_col].max())
            lowest = float(sub_df[low_col].min())

        if is_long:
            # For LONG:
            # MFE is peak price above entry
            mfe_price = max(highest, exit_p)
            mfe_pct = max(0.0, (mfe_price - entry_p) / entry_p) * 100.0

            # MAE is worst drawdown below entry
            mae_price = min(lowest, exit_p)
            mae_pct = max(0.0, (entry_p - mae_price) / entry_p) * 100.0

            # Realized return
            realized_ret_pct = ((exit_p - entry_p) / entry_p) * 100.0
        else:
            # For SHORT:
            # MFE is lowest price below entry
            mfe_price = min(lowest, exit_p)
            mfe_pct = max(0.0, (entry_p - mfe_price) / entry_p) * 100.0

            # MAE is peak price above entry
            mae_price = max(highest, exit_p)
            mae_pct = max(0.0, (mae_price - entry_p) / entry_p) * 100.0

            # Realized return
            realized_ret_pct = ((entry_p - exit_p) / entry_p) * 100.0

        # Efficiency & Left on table
        if mfe_pct > 1e-6:
            exit_efficiency = realized_ret_pct / mfe_pct
        else:
            exit_efficiency = 1.0 if realized_ret_pct >= 0 else -1.0

        left_on_table_pct = max(0.0, mfe_pct - realized_ret_pct)

        records.append({
            "trade_id": tr.get("id", idx + 1),
            "symbol": tr.get("symbol", "N/A"),
            "side": "LONG" if is_long else "SHORT",
            "entry_time": entry_t,
            "exit_time": exit_t,
            "entry_price": entry_p,
            "exit_price": exit_p,
            "mfe_price": mfe_price,
            "mae_price": mae_price,
            "mfe_pct": round(mfe_pct, 2),
            "mae_pct": round(mae_pct, 2),
            "realized_ret_pct": round(realized_ret_pct, 2),
            "exit_efficiency": round(exit_efficiency, 2),
            "left_on_table_pct": round(left_on_table_pct, 2)
        })

    return pd.DataFrame(records)


def analyze_execution_quality(mfe_mae_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes aggregate metrics and diagnostic recommendations on trade execution quality.
    """
    if mfe_mae_df.empty:
        return {}

    wins = mfe_mae_df[mfe_mae_df["realized_ret_pct"] > 0]
    losses = mfe_mae_df[mfe_mae_df["realized_ret_pct"] <= 0]

    avg_mfe = mfe_mae_df["mfe_pct"].mean()
    avg_mae = mfe_mae_df["mae_pct"].mean()
    avg_eff = mfe_mae_df["exit_efficiency"].mean()
    avg_left_on_table = mfe_mae_df["left_on_table_pct"].mean()

    # Winning trade characteristics
    win_avg_mfe = wins["mfe_pct"].mean() if not wins.empty else 0.0
    win_avg_mae = wins["mae_pct"].mean() if not wins.empty else 0.0
    win_avg_eff = wins["exit_efficiency"].mean() if not wins.empty else 0.0

    # Losing trade characteristics
    loss_avg_mfe = losses["mfe_pct"].mean() if not losses.empty else 0.0
    loss_avg_mae = losses["mae_pct"].mean() if not losses.empty else 0.0

    # Diagnostic insights
    recommendations = []
    if win_avg_eff < 0.40 and not wins.empty:
        recommendations.append("⚠️ Winning trades give back over 60% of their peak profit. Consider trailing stop or earlier partial take-profit.")
    if loss_avg_mfe > 1.5 and not losses.empty:
        recommendations.append("⚠️ Multiple losing trades were significantly profitable (MFE > 1.5%) before reversing into losses. Implement Break-Even stops (BEP).")
    if win_avg_mae < (avg_mae * 0.4) and not wins.empty:
        recommendations.append("✅ Winning trades show low adverse excursion (MAE). Stop loss can safely be tightened to reduce risk.")

    return {
        "total_trades": len(mfe_mae_df),
        "win_rate_pct": round(len(wins) / len(mfe_mae_df) * 100.0, 1),
        "avg_mfe_pct": round(avg_mfe, 2),
        "avg_mae_pct": round(avg_mae, 2),
        "avg_efficiency": round(avg_eff, 2),
        "avg_left_on_table_pct": round(avg_left_on_table, 2),
        "win_avg_mfe_pct": round(win_avg_mfe, 2),
        "win_avg_mae_pct": round(win_avg_mae, 2),
        "win_avg_eff": round(win_avg_eff, 2),
        "loss_avg_mfe_pct": round(loss_avg_mfe, 2),
        "loss_avg_mae_pct": round(loss_avg_mae, 2),
        "recommendations": recommendations
    }
