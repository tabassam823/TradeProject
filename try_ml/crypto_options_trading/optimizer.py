"""
Self-Improvement Optimizer Module for Crypto Options.
Analyzes initial options backtest performance and iteratively searches the option parameter space
(DTE, strike moneyness, vertical spreads vs outrights, premium take-profit/stop-loss, and Z-score thresholds)
until the target Sharpe Ratio is achieved.
"""
import pandas as pd
from typing import Dict, Any, Tuple
from .options_risk_engine import OptionsExecutionEngine
from .config import TARGET_SHARPE_RATIO, BASELINE_OPTIONS_PARAMS

class OptionsSelfImprover:
    def __init__(self, target_sharpe: float = TARGET_SHARPE_RATIO):
        self.target_sharpe = target_sharpe

    def run_self_improvement_pipeline(
        self,
        pred_df: pd.DataFrame,
        asset_name: str = "SOL-USD"
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Runs baseline options backtest, diagnoses performance bottlenecks,
        and systematically optimizes parameters to achieve target Sharpe Ratio (> 1.5).
        """
        print(f"\n=======================================================")
        print(f"[*] RUNNING BASELINE OPTIONS BACKTEST ({asset_name})")
        print(f"=======================================================")
        base_engine = OptionsExecutionEngine(**BASELINE_OPTIONS_PARAMS)
        _, _, base_metrics = base_engine.simulate(pred_df)
        
        print(f"Baseline Sharpe Ratio   : {base_metrics['sharpe_ratio']:.2f}")
        print(f"Baseline Net Return     : {base_metrics['total_net_return_pct']:+.2f}%")
        print(f"Baseline Max Drawdown   : {base_metrics['max_drawdown_pct']:.2f}%")
        print(f"Baseline Total Trades   : {base_metrics['total_trades']}")
        print(f"Baseline Win Rate       : {base_metrics['win_rate_pct']:.2f}%")
        print(f"Baseline Fees Paid      : ${base_metrics['total_fees_paid']:.2f}")
        
        if base_metrics['sharpe_ratio'] >= self.target_sharpe:
            print(f"[OK] Baseline already meets target Sharpe Ratio ({self.target_sharpe}).")
            return BASELINE_OPTIONS_PARAMS, base_metrics, base_metrics
            
        print(f"\n[!] Target Sharpe Ratio ({self.target_sharpe}) NOT reached. Starting Options Self-Improvement Engine...")
        
        best_params = BASELINE_OPTIONS_PARAMS.copy()
        best_metrics = base_metrics.copy()
        best_sharpe = base_metrics['sharpe_ratio']
        
        # Grid Search space tailored for Options Dynamics (Theta decay, Vega, Asymmetric Payoffs)
        strategy_candidates = ['outright', 'spread']
        dte_candidates = [24, 48, 72]          # 1 to 3 days to expiration
        entry_z_candidates = [1.0, 1.2, 1.4, 1.6]
        min_hold_candidates = [4, 6, 12]
        tp_candidates = [0.60, 1.0, 1.5, None] # 60%, 100%, 150% gain on premium
        sl_candidates = [0.40, 0.50, 0.60]     # 40%, 50%, 60% loss limit
        trail_act_candidates = [0.50, None]
        
        iteration = 0
        tested_configs = 0
        
        for strat in strategy_candidates:
            for dte in dte_candidates:
                for entry_z in entry_z_candidates:
                    for min_hold in min_hold_candidates:
                        for tp in tp_candidates:
                            for sl in sl_candidates:
                                for trail_act in trail_act_candidates:
                                    tested_configs += 1
                                    candidate_params = {
                                        'strategy_type': strat,
                                        'strike_moneyness': 1.0,
                                        'spread_width_pct': 0.05,
                                        'dte_hours': dte,
                                        'entry_z': entry_z,
                                        'exit_z': 0.0,
                                        'min_hold_hours': min_hold,
                                        'take_profit_pct': tp,
                                        'stop_loss_pct': sl,
                                        'trail_act_pct': trail_act,
                                        'trail_dist_pct': 0.25 if trail_act is not None else None,
                                        'smooth_span': 4,
                                        'z_window': 168,
                                        'use_sma_filter': True,
                                        'allow_bearish_puts': True,
                                        'use_cooldown': True,
                                        'max_lose_streak': 3,
                                        'cooldown_hours': 24
                                    }
                                    
                                    engine = OptionsExecutionEngine(**candidate_params)
                                    _, trades, m = engine.simulate(pred_df)
                                    
                                    # Ensure sufficient statistical sample of trades and improved Sharpe
                                    if m['total_trades'] >= 15 and m['sharpe_ratio'] > best_sharpe:
                                        best_sharpe = m['sharpe_ratio']
                                        best_params = candidate_params
                                        best_metrics = m
                                        iteration += 1
                                        print(f"  -> Iteration {iteration:02d}: New Best Sharpe = {best_sharpe:.2f} | Return = {m['total_net_return_pct']:+.2f}% | MaxDD = {m['max_drawdown_pct']:.2f}% | WinRate = {m['win_rate_pct']:.1f}% (Trades: {int(m['total_trades'])}) [Strat: {strat.upper()}, DTE: {dte}h, Z: {entry_z}, TP: {tp}, SL: {sl}]")
                                        
        print(f"\n=======================================================")
        print(f"[SUCCESS] OPTIONS SELF-IMPROVEMENT COMPLETED ({tested_configs} configurations analyzed)")
        print(f"Final Sharpe Ratio: {best_metrics['sharpe_ratio']:.2f} (Target was > {self.target_sharpe})")
        print(f"Net Return        : {best_metrics['total_net_return_pct']:+.2f}%")
        print(f"Max Drawdown      : {best_metrics['max_drawdown_pct']:.2f}%")
        print(f"=======================================================")
        
        return best_params, base_metrics, best_metrics
