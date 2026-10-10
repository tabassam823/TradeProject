"""
Backtester and Visualization Module for Crypto Futures Scalping.
Generates publication-quality charts and detailed performance evaluations.
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple
from .risk_engine import ScalpingRiskEngine
from .config import OUTPUT_DIR

def run_scalping_backtest(
    pred_df: pd.DataFrame,
    engine_params: Dict[str, Any],
    asset_name: str = "SOL-USD"
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Executes scalping backtest simulation with specified parameter configuration.
    """
    engine = ScalpingRiskEngine(**engine_params)
    res_df, trades_df, metrics = engine.simulate(pred_df)
    return res_df, trades_df, metrics

def plot_scalping_performance(
    eval_df: pd.DataFrame,
    trades_df: pd.DataFrame,
    metrics: Dict[str, Any],
    asset_name: str = "SOL-USD",
    output_filename: str = "sol_scalping_equity_curve.png"
):
    """
    Generates institutional 3-panel visualization:
    Panel 1: Cumulative Equity vs Buy & Hold Benchmark
    Panel 2: Portfolio Drawdown Profile (%)
    Panel 3: Trade Net Return (%) Distribution
    """
    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(14, 11),
        gridspec_kw={'height_ratios': [2.2, 1.0, 1.0]}
    )
    
    init_cap = metrics['initial_capital']
    final_cap = metrics['final_equity']
    net_ret = metrics['total_net_return_pct']
    sharpe = metrics['sharpe_ratio']
    max_dd = metrics['max_drawdown_pct']
    win_rate = metrics['win_rate_pct']
    trades_count = metrics['total_trades']
    
    # --- Panel 1: Equity Curve vs Buy & Hold ---
    ax1.plot(
        eval_df.index, eval_df['capital_equity'],
        label=f"Scalping ML Strategy (Final: ${final_cap:,.2f} | Net: {net_ret:+.2f}% | Sharpe: {sharpe:.2f})",
        color='#00c853', lw=2
    )
    ax1.axhline(init_cap, color='gray', linestyle='--', alpha=0.7, label=f'Initial Capital (${init_cap:,.0f})')
    
    # Buy & Hold normalized
    norm_bnh = (eval_df['close'] / eval_df['close'].iloc[0]) * init_cap
    ax1.plot(
        eval_df.index, norm_bnh,
        label=f"Buy & Hold {asset_name} ({metrics['buy_and_hold_return_pct']:+.2f}%)",
        color='#9e9e9e', linestyle=':', lw=1.5
    )
    
    ax1.set_title(
        f'⚡ High-Frequency Futures Scalping ML (5m) Performance: {asset_name}\n'
        f'Trades: {trades_count} | Win Rate: {win_rate:.1f}% | Profit Factor: {metrics["profit_factor"]:.2f} | Max DD: {max_dd:.2f}%',
        fontsize=13, fontweight='bold'
    )
    ax1.set_ylabel('Portfolio Equity ($)', fontsize=10)
    ax1.legend(loc='upper left', frameon=True)
    ax1.grid(True, alpha=0.3)
    
    # --- Panel 2: Drawdown Profile ---
    roll_max = eval_df['capital_equity'].cummax()
    dd_series = (eval_df['capital_equity'] - roll_max) / roll_max * 100.0
    
    ax2.plot(dd_series.index, dd_series, label=f'Drawdown % (Max DD: {max_dd:.2f}%)', color='#d50000', lw=1.2)
    ax2.fill_between(dd_series.index, dd_series, 0, color='#d50000', alpha=0.25)
    ax2.set_ylabel('Drawdown (%)', fontsize=10)
    ax2.set_ylim(bottom=min(max_dd * 1.25, -5.0), top=1.0)
    ax2.legend(loc='lower left')
    ax2.grid(True, alpha=0.3)
    
    # --- Panel 3: Trade PnL Distribution ---
    if len(trades_df) > 0:
        win_pnl = trades_df[trades_df['net_pnl'] > 0]['pnl_pct']
        loss_pnl = trades_df[trades_df['net_pnl'] <= 0]['pnl_pct']
        
        bins = np.linspace(trades_df['pnl_pct'].min() - 0.5, trades_df['pnl_pct'].max() + 0.5, 35)
        ax3.hist(win_pnl, bins=bins, color='#00c853', alpha=0.7, label=f'Winning Trades ({len(win_pnl)})')
        ax3.hist(loss_pnl, bins=bins, color='#d50000', alpha=0.7, label=f'Losing Trades ({len(loss_pnl)})')
        ax3.axvline(0, color='black', linestyle='--', lw=1)
        ax3.set_xlabel('Trade Net Return (%) per Execution', fontsize=10)
        ax3.set_ylabel('Frequency', fontsize=10)
        ax3.set_title('Trade PnL % Distribution (After Taker Fees & Slippage)', fontsize=11, fontweight='bold')
        ax3.legend(loc='upper right')
        ax3.grid(True, alpha=0.3)
    else:
        ax3.text(0.5, 0.5, 'No Closed Trades', horizontalalignment='center', verticalalignment='center')
        
    plt.tight_layout()
    save_path = Path(OUTPUT_DIR) / output_filename
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[PLOT SAVED] Scalping performance chart saved to '{save_path}'")
