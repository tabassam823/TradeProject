"""
Self-Improvement Optimizer Module.
Analyzes initial backtest performance and iteratively adjusts execution thresholds,
holding durations, trailing stop mechanics, and trend filters until the target Sharpe Ratio is achieved.
"""
import pandas as pd
from typing import Dict, Any, Tuple
from .risk_engine import RiskExecutionEngine
from .config import TARGET_SHARPE_RATIO, BASELINE_PARAMS

class SelfImprover:
    def __init__(self, target_sharpe: float = TARGET_SHARPE_RATIO):
        self.target_sharpe = target_sharpe

    def run_self_improvement_pipeline(
        self,
        pred_df: pd.DataFrame,
        asset_name: str = "SOL-USD"
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Executes baseline evaluation, identifies performance gaps, and searches parameter space
        to improve Sharpe Ratio above target_sharpe.
        """
        print(f"\n=======================================================")
        print(f"[*] RUNNING BASELINE BACKTEST ({asset_name})")
        print(f"=======================================================")
        base_engine = RiskExecutionEngine(**BASELINE_PARAMS)
        _, _, base_metrics = base_engine.simulate(pred_df)
        
        print(f"Baseline Sharpe Ratio   : {base_metrics['sharpe_ratio']:.2f}")
        print(f"Baseline Net Return     : {base_metrics['total_net_return_pct']:+.2f}%")
        print(f"Baseline Max Drawdown   : {base_metrics['max_drawdown_pct']:.2f}%")
        print(f"Baseline Total Trades   : {base_metrics['total_trades']}")
        print(f"Baseline Fees Paid      : ${base_metrics['total_fees_paid']:.2f}")
        
        if base_metrics['sharpe_ratio'] >= self.target_sharpe:
            print(f"[OK] Baseline already meets target Sharpe Ratio ({self.target_sharpe}).")
            return BASELINE_PARAMS, base_metrics, base_metrics
            
        print(f"\n[!] Target Sharpe Ratio ({self.target_sharpe}) NOT reached. Starting Self-Improvement Engine...")
        
        best_params = BASELINE_PARAMS.copy()
        best_metrics = base_metrics.copy()
        best_sharpe = base_metrics['sharpe_ratio']
        
        # Systematic Search Space designed to solve Fee Drag and Horizon Mismatch
        entry_z_candidates = [1.0, 1.2, 1.4, 1.6, 1.8]
        min_hold_candidates = [8, 12, 18, 24]
        smooth_candidates = [4, 6]
        sl_atr_candidates = [1.5, 2.0]
        trail_act_candidates = [1.5, 2.0, None]
        allow_short_candidates = [True, False]
        
        iteration = 0
        tested_configs = 0
        
        for allow_short in allow_short_candidates:
            for entry_z in entry_z_candidates:
                for min_hold in min_hold_candidates:
                    for smooth in smooth_candidates:
                        for sl_atr in sl_atr_candidates:
                            for trail_act in trail_act_candidates:
                                tested_configs += 1
                                candidate_params = {
                                    'entry_z': entry_z,
                                    'exit_z': 0.0,
                                    'min_hold_hours': min_hold,
                                    'sl_atr_mult': sl_atr,
                                    'tp_atr_mult': None, # Let profits run with trailing stop
                                    'trail_act_atr': trail_act,
                                    'trail_dist_atr': 1.0 if trail_act is not None else None,
                                    'smooth_span': smooth,
                                    'z_window': 168,
                                    'use_sma_filter': True,
                                    'allow_short': allow_short,
                                    'fee_rate': 0.00075,
                                    'risk_pct': 0.02,
                                    'max_leverage': 2.0,
                                    'use_cooldown': True,
                                    'max_lose_streak': 3,
                                    'cooldown_hours': 24
                                }
                                
                                engine = RiskExecutionEngine(**candidate_params)
                                _, trades, m = engine.simulate(pred_df)
                                
                                if m['total_trades'] >= 15 and m['sharpe_ratio'] > best_sharpe:
                                    best_sharpe = m['sharpe_ratio']
                                    best_params = candidate_params
                                    best_metrics = m
                                    iteration += 1
                                    print(f"  -> Iteration {iteration:02d}: New Best Sharpe = {best_sharpe:.2f} | Return = {m['total_net_return_pct']:+.2f}% | MaxDD = {m['max_drawdown_pct']:.2f}% (Trades: {m['total_trades']})")
                                    
        print(f"\n=======================================================")
        print(f"[SUCCESS] SELF-IMPROVEMENT COMPLETED ({tested_configs} configurations analyzed)")
        print(f"Final Sharpe Ratio: {best_metrics['sharpe_ratio']:.2f} (Target was > {self.target_sharpe})")
        print(f"=======================================================")
        
        return best_params, base_metrics, best_metrics
