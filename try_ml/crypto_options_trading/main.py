"""
Main Orchestration Pipeline for Crypto Options ML Trading System.
Executes end-to-end data ingestion, alpha & volatility feature engineering,
purged walk-forward model retraining, baseline options backtesting,
options self-improvement optimization, and comprehensive reporting.
"""
import os
import sys
import json
import pandas as pd
from pathlib import Path

# Add project root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crypto_options_trading.config import (
    OUTPUT_DIR, BASELINE_OPTIONS_PARAMS, TARGET_SHARPE_RATIO,
    LOOKBACK_DAYS, PURGED_TRAIN_DAYS, PURGED_TEST_DAYS
)
from crypto_options_trading.data_loader import load_all_market_data
from crypto_options_trading.features import build_asset_features, inject_cross_asset_features
from crypto_options_trading.model import run_purged_walk_forward_retraining
from crypto_options_trading.options_risk_engine import OptionsExecutionEngine
from crypto_options_trading.backtester import plot_options_performance
from crypto_options_trading.optimizer import OptionsSelfImprover

def run_pipeline():
    print("=" * 80)
    print("⚡ SOLANA CRYPTO OPTIONS ML TRADING SYSTEM: WALK-FORWARD & SELF-IMPROVEMENT")
    print("=" * 80)
    print(f"Output Directory: {OUTPUT_DIR}")
    
    # 1. Ingestion
    print("\n--- 1. Ingesting Market Data & Sentiment Feeds ---")
    btc_raw, sol_raw, fng_raw, news_raw = load_all_market_data(days=LOOKBACK_DAYS)
    print(f"-> SOL Candles: {len(sol_raw)} | BTC Candles: {len(btc_raw)} | FNG: {len(fng_raw)} | News: {len(news_raw)}")
    
    # 2. Feature Engineering
    print("\n--- 2. Engineering Stationary Alpha & Options Volatility Features ---")
    feat_btc = build_asset_features(btc_raw, fng_raw, news_raw, horizon=1)
    feat_sol = build_asset_features(sol_raw, fng_raw, news_raw, horizon=1)
    feat_sol_aligned, feature_cols = inject_cross_asset_features(feat_sol, feat_btc)
    print(f"-> Total Engineered Features: {len(feature_cols)}")
    print(f"-> Sample Features: {feature_cols[:8]}")
    
    # 3. Model Training
    print("\n--- 3. Purged Rolling Walk-Forward Retraining (Zero Look-Ahead Bias) ---")
    sol_pred_df, feat_importance = run_purged_walk_forward_retraining(
        feat_sol_aligned,
        feature_cols,
        target_col='target_return_1h',
        horizon=1,
        train_days=PURGED_TRAIN_DAYS,
        test_days=PURGED_TEST_DAYS
    )
    
    # 4. Self-Improvement Engine for Options
    print("\n--- 4. Evaluating Baseline Options Strategy & Running Self-Improvement ---")
    improver = OptionsSelfImprover(target_sharpe=TARGET_SHARPE_RATIO)
    best_params, base_metrics, improved_metrics = improver.run_self_improvement_pipeline(
        sol_pred_df, asset_name="SOL-USD"
    )
    
    # 5. Final Evaluation with Optimal Parameters
    print("\n--- 5. Generating Final Options Backtest Artifacts ---")
    final_engine = OptionsExecutionEngine(**best_params)
    final_df, final_trades, final_metrics = final_engine.simulate(sol_pred_df)
    
    # Export Plot
    plot_options_performance(
        final_df,
        final_metrics,
        asset_name="SOL-USD",
        output_filename="sol_options_equity_curve.png"
    )
    
    # Export Trade Logs
    trades_csv_path = OUTPUT_DIR / "sol_options_trade_logs.csv"
    final_trades.to_csv(trades_csv_path, index=False)
    print(f"[EXPORT] Trade logs saved to '{trades_csv_path}'")
    
    # Export Metrics Summary JSON
    summary_data = {
        'asset': 'SOL-USD',
        'instrument': 'Options (Black-Scholes Simulated)',
        'target_sharpe': TARGET_SHARPE_RATIO,
        'baseline_metrics': {k: (float(v) if hasattr(v, '__float__') else v) for k, v in base_metrics.items()},
        'improved_metrics': {k: (float(v) if hasattr(v, '__float__') else v) for k, v in final_metrics.items()},
        'best_hyperparameters': best_params,
        'top_features': feat_importance.head(10).to_dict(orient='records')
    }
    
    json_path = OUTPUT_DIR / "options_metrics_summary.json"
    with open(json_path, 'w') as f:
        json.dump(summary_data, f, indent=4)
    print(f"[EXPORT] Metrics summary saved to '{json_path}'")
    
    # Export Markdown Report
    report_path = OUTPUT_DIR / "options_backtest_report.md"
    with open(report_path, 'w') as f:
        f.write("# 📊 Solana Crypto Options ML Trading: Self-Improvement Report\n\n")
        f.write("## 1. Executive Summary & Performance Comparison\n\n")
        f.write("| Metrik | Baseline Options | Optimal Self-Improved Options | Futures (Week 3 Benchmark) | B&H Spot SOL |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        f.write(f"| **Sharpe Ratio** | **{base_metrics['sharpe_ratio']:.2f}** | **{final_metrics['sharpe_ratio']:.2f}** | 3.19 | -0.15 |\n")
        f.write(f"| **Net Return** | **{base_metrics['total_net_return_pct']:+.2f}%** | **{final_metrics['total_net_return_pct']:+.2f}%** | +225.71% | {final_metrics['buy_and_hold_return_pct']:+.2f}% |\n")
        f.write(f"| **Max Drawdown** | **{base_metrics['max_drawdown_pct']:.2f}%** | **{final_metrics['max_drawdown_pct']:.2f}%** | -24.83% | -55.20% |\n")
        f.write(f"| **Win Rate** | **{base_metrics['win_rate_pct']:.1f}%** | **{final_metrics['win_rate_pct']:.1f}%** | 54.8% | N/A |\n")
        f.write(f"| **Profit Factor** | **{base_metrics['profit_factor']:.2f}** | **{final_metrics['profit_factor']:.2f}** | 1.66 | N/A |\n")
        f.write(f"| **Total Trades** | **{int(base_metrics['total_trades'])}** | **{int(final_metrics['total_trades'])}** | 228 | 1 |\n")
        f.write(f"| **Total Fees Paid** | **${base_metrics['total_fees_paid']:.2f}** | **${final_metrics['total_fees_paid']:.2f}** | $1,130.76 | $0.00 |\n\n")
        
        f.write("## 2. Best Configuration Found\n\n")
        f.write("```json\n")
        f.write(json.dumps(best_params, indent=2))
        f.write("\n```\n\n")
        
        f.write("## 3. Structural Insights: Options vs Futures in Crypto Trading\n\n")
        f.write("1. **Asymmetric Downside Protection**:\n")
        f.write("   - Pada futures, risiko likuidasi dan gap-down loss bersifat linear.\n")
        f.write("   - Pada options (long call/put), kerugian maksimal dibatasi secara pasti pada *premium paid* (3% risiko modal per trade) tanpa risiko margin liquidation.\n\n")
        f.write("2. **Theta Decay vs Momentum Horizon**:\n")
        f.write("   - Tantangan utama options adalah *Theta decay* (penyusutan nilai waktu).\n")
        f.write("   - Strategi yang optimal menyeimbangkan DTE (Days to Expiration) dan ambang *Take-Profit pada premium* sebelum peluruhan waktu menggerus keuntungan.\n\n")
        f.write("3. **Top Feature Signals**:\n")
        for i, row in feat_importance.head(10).iterrows():
            f.write(f"- **{row['feature']}**: {row['importance']:.2f}\n")
            
    print(f"[EXPORT] Backtest report saved to '{report_path}'")
    print("\n🎉 Pipeline Execution Completed Successfully!")

if __name__ == "__main__":
    run_pipeline()
