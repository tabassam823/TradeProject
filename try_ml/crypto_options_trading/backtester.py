"""
Backtester and Performance Visualization Module for Options Trading.
Generates multi-panel performance plots (Equity Curve, Drawdown Profile, and Greeks Exposure)
and exports trade records.
"""
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple
from .options_risk_engine import OptionsExecutionEngine
from .config import OUTPUT_DIR

def run_backtest(
    pred_df: pd.DataFrame,
    engine_params: Dict[str, Any]
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Instantiates the OptionsExecutionEngine with provided parameters and evaluates strategy.
    """
    engine = OptionsExecutionEngine(**engine_params)
    res_df, trades_df, metrics = engine.simulate(pred_df)
    return res_df, trades_df, metrics

def plot_options_performance(
    eval_df: pd.DataFrame,
    metrics: Dict[str, Any],
    asset_name: str = "SOL-USD",
    output_filename: str = "sol_options_equity_curve.png"
):
    """
    Generates and saves professional 3-panel options performance chart:
    Panel 1: Portfolio Equity Growth ($) vs Buy & Hold
    Panel 2: Dynamic Drawdown Profile (%)
    Panel 3: Greeks Exposure (Net Delta & Theta per Day)
    """
    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(14, 12), sharex=True, gridspec_kw={'height_ratios': [2.5, 1.2, 1.3]}
    )
    
    init_cap = metrics['initial_capital']
    final_cap = metrics['final_equity']
    net_ret = metrics['total_net_return_pct']
    sharpe = metrics['sharpe_ratio']
    max_dd = metrics['max_drawdown_pct']
    win_rate = metrics['win_rate_pct']
    pf = metrics['profit_factor']
    
    # 1. Equity Plot
    ax1.plot(
        eval_df.index, eval_df['equity'],
        label=f"{asset_name} Options Strategy (Final: ${final_cap:,.2f} | Net: {net_ret:+.2f}% | Sharpe: {sharpe:.2f} | WinRate: {win_rate:.1f}%)",
        color='#1f77b4', lw=2.2
    )
    ax1.axhline(init_cap, color='gray', linestyle='--', alpha=0.7, label=f'Initial Capital (${init_cap:,.0f})')
    
    # Buy & Hold Equivalent
    norm_bnh = (eval_df['close'] / eval_df['close'].iloc[0]) * init_cap
    ax1.plot(
        eval_df.index, norm_bnh,
        label=f"Buy & Hold {asset_name} Spot ({metrics['buy_and_hold_return_pct']:+.2f}%)",
        color='#7f7f7f', linestyle=':', lw=1.5
    )
    
    ax1.set_title(f'Solana Systematic Options Trading Strategy (Black-Scholes & Machine Learning)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Portfolio Equity ($)', fontsize=11)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 2. Drawdown Plot
    roll_max = eval_df['equity'].cummax()
    dd_series = (eval_df['equity'] - roll_max) / roll_max * 100
    
    ax2.plot(dd_series.index, dd_series, label=f'Options Strategy Drawdown % (Max DD: {max_dd:.2f}%)', color='#d62728', lw=1.5)
    ax2.fill_between(dd_series.index, dd_series, 0, color='#d62728', alpha=0.25)
    ax2.set_title('Drawdown Profile (%)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Drawdown (%)', fontsize=11)
    ax2.legend(loc='lower left')
    ax2.grid(True, alpha=0.3)
    
    # 3. Greeks Exposure (Delta & Theta)
    ax3.plot(eval_df.index, eval_df['delta'], label='Net Position Delta', color='#2ca02c', lw=1.2, alpha=0.85)
    ax3_twin = ax3.twinx()
    ax3_twin.plot(eval_df.index, eval_df['theta'], label='Net Theta Decay ($/Day)', color='#ff7f0e', linestyle='--', lw=1.2, alpha=0.85)
    
    ax3.axhline(0, color='black', lw=0.8, alpha=0.5)
    ax3.set_title('Dynamic Options Risk Exposure (Delta & Theta)', fontsize=11, fontweight='bold')
    ax3.set_xlabel('Timestamp', fontsize=11)
    ax3.set_ylabel('Delta Exposure (SOL)', fontsize=10, color='#2ca02c')
    ax3_twin.set_ylabel('Theta Decay ($/Day)', fontsize=10, color='#ff7f0e')
    
    lines_1, labels_1 = ax3.get_legend_handles_labels()
    lines_2, labels_2 = ax3_twin.get_legend_handles_labels()
    ax3.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_path = Path(OUTPUT_DIR) / output_filename
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[PLOT SAVED] Options performance chart successfully saved to '{save_path}'")
