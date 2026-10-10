"""
Backtester and Performance Visualization Module.
Executes end-to-end backtest evaluations and outputs cumulative equity curves,
drawdown charts, and transaction log reports.
"""
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple
from .risk_engine import RiskExecutionEngine
from .config import OUTPUT_DIR

def run_backtest(
    pred_df: pd.DataFrame,
    engine_params: Dict[str, Any],
    asset_name: str = "SOL-USD"
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Instantiates the RiskExecutionEngine with provided parameters and evaluates strategy.
    """
    engine = RiskExecutionEngine(**engine_params)
    res_df, trades_df, metrics = engine.simulate(pred_df)
    return res_df, trades_df, metrics

def plot_equity_and_drawdown(
    eval_df: pd.DataFrame,
    metrics: Dict[str, Any],
    asset_name: str = "SOL-USD",
    output_filename: str = "equity_curve.png"
):
    """
    Generates and saves professional 2-panel chart:
    Panel 1: Equity Growth ($) vs Initial Capital
    Panel 2: Historical Dynamic Drawdown (%)
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True, gridspec_kw={'height_ratios': [2.5, 1]})
    
    init_cap = metrics['initial_capital']
    final_cap = metrics['final_equity']
    net_ret = metrics['total_net_return_pct']
    sharpe = metrics['sharpe_ratio']
    max_dd = metrics['max_drawdown_pct']
    
    # 1. Equity Plot
    ax1.plot(eval_df.index, eval_df['capital_equity'], label=f"{asset_name} Strategy (Final: ${final_cap:,.2f} | Return: {net_ret:+.2f}% | Sharpe: {sharpe:.2f})", color='#2ca02c', lw=2)
    ax1.axhline(init_cap, color='gray', linestyle='--', alpha=0.7, label=f'Initial Capital (${init_cap:,.0f})')
    
    # Buy & Hold Equivalent
    norm_bnh = (eval_df['close'] / eval_df['close'].iloc[0]) * init_cap
    ax1.plot(eval_df.index, norm_bnh, label=f"Buy & Hold {asset_name} ({metrics['buy_and_hold_return_pct']:+.2f}%)", color='#7f7f7f', linestyle=':', lw=1.5)
    
    ax1.set_title(f'Equity Curve & Dynamic Risk Performance: {asset_name}', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Portfolio Equity ($)', fontsize=11)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 2. Drawdown Plot
    roll_max = eval_df['capital_equity'].cummax()
    dd_series = (eval_df['capital_equity'] - roll_max) / roll_max * 100
    
    ax2.plot(dd_series.index, dd_series, label=f'Strategy Drawdown % (Max DD: {max_dd:.2f}%)', color='#d62728', lw=1.5)
    ax2.fill_between(dd_series.index, dd_series, 0, color='#d62728', alpha=0.2)
    ax2.set_title('Drawdown Profile (%)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Time', fontsize=11)
    ax2.set_ylabel('Drawdown (%)', fontsize=11)
    ax2.legend(loc='lower left')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_path = Path(OUTPUT_DIR) / output_filename
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[PLOT SAVED] Performance chart successfully saved to '{save_path}'")
