"""
Self-Improvement Optimizer Module for High-Frequency Scalping.
Evaluates baseline execution, isolates performance bottlenecks (fee drag, choppy whipsaws, horizon mismatch),
and systematically searches parameter space to maximize Sharpe Ratio and control Drawdown.
"""
import pandas as pd
from typing import Dict, Any, Tuple
from .risk_engine import ScalpingRiskEngine
from .config import TARGET_SHARPE_RATIO, BASELINE_SCALPER_PARAMS, DEFAULT_FEE_RATE, DEFAULT_LEVERAGE, RISK_BUDGET_PCT

class ScalpingSelfImprover:
    def __init__(self, target_sharpe: float = TARGET_SHARPE_RATIO):
        self.target_sharpe = target_sharpe

    def run_self_improvement_pipeline(
        self,
        pred_df: pd.DataFrame,
        asset_name: str = "SOL-USD"
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Executes baseline scalper evaluation and iteratively searches for optimal configurations.
        """
        print(f"\n=======================================================")
        print(f"[*] RUNNING BASELINE SCALPER BACKTEST ({asset_name})")
        print(f"=======================================================")
        base_engine = ScalpingRiskEngine(**BASELINE_SCALPER_PARAMS)
        _, _, base_metrics = base_engine.simulate(pred_df)
        
        print(f"Baseline Sharpe Ratio   : {base_metrics['sharpe_ratio']:.2f}")
        print(f"Baseline Net Return     : {base_metrics['total_net_return_pct']:+.2f}%")
        print(f"Baseline Max Drawdown   : {base_metrics['max_drawdown_pct']:.2f}%")
        print(f"Baseline Total Trades   : {base_metrics['total_trades']}")
        print(f"Baseline Win Rate       : {base_metrics['win_rate_pct']:.2f}%")
        print(f"Baseline Fees Paid      : ${base_metrics['total_fees_paid']:.2f}")
        
        print(f"\n[!] Initiating Systematic Self-Improvement Optimization...")
        
        best_params = BASELINE_SCALPER_PARAMS.copy()
        best_metrics = base_metrics.copy()
        best_sharpe = base_metrics['sharpe_ratio']
        
        # Candidate parameter grid tailored for 5m crypto futures scalping
        entry_z_candidates = [1.2, 1.5, 1.8, 2.0]
        min_hold_candidates = [2, 4, 6]            # 10m, 20m, 30m
        max_hold_candidates = [12, 18, 24]         # 1h, 1.5h, 2h
        sl_atr_candidates = [1.0, 1.5]
        tp_atr_candidates = [2.0, 3.0, None]
        trail_act_candidates = [1.2, 1.6, None]
        use_trend_candidates = [True, False]
        use_vol_candidates = [True, False]
        allow_short_candidates = [True, False]
        
        iteration = 0
        tested_configs = 0
        
        # Intelligent layered grid search
        for allow_short in allow_short_candidates:
            for use_trend in use_trend_candidates:
                for entry_z in entry_z_candidates:
                    for min_hold in min_hold_candidates:
                        for max_hold in max_hold_candidates:
                            for sl_atr in sl_atr_candidates:
                                for tp_atr in tp_atr_candidates:
                                    for trail_act in trail_act_candidates:
                                        for use_vol in use_vol_candidates:
                                            tested_configs += 1
                                            
                                            candidate_params = {
                                                'entry_z': entry_z,
                                                'exit_z': 0.0,
                                                'min_hold_bars': min_hold,
                                                'max_hold_bars': max_hold,
                                                'sl_atr_mult': sl_atr,
                                                'tp_atr_mult': tp_atr,
                                                'trail_act_atr': trail_act,
                                                'trail_dist_atr': 0.8 if trail_act is not None else None,
                                                'smooth_span': 3,
                                                'z_window': 288,
                                                'use_trend_filter': use_trend,
                                                'use_vol_filter': use_vol,
                                                'allow_short': allow_short,
                                                'fee_rate': DEFAULT_FEE_RATE,
                                                'leverage': DEFAULT_LEVERAGE,
                                                'risk_pct': RISK_BUDGET_PCT,
                                                'use_cooldown': True,
                                                'max_lose_streak': 3,
                                                'cooldown_bars': 24
                                            }
                                            
                                            engine = ScalpingRiskEngine(**candidate_params)
                                            _, _, m = engine.simulate(pred_df)
                                            
                                            # Quality filter: minimum 20 trades for statistical confidence
                                            if m['total_trades'] >= 20 and m['sharpe_ratio'] > best_sharpe:
                                                best_sharpe = m['sharpe_ratio']
                                                best_params = candidate_params
                                                best_metrics = m
                                                iteration += 1
                                                print(
                                                    f"  -> Iteration {iteration:02d}: New Best Sharpe = {best_sharpe:.2f} | "
                                                    f"Return = {m['total_net_return_pct']:+.2f}% | MaxDD = {m['max_drawdown_pct']:.2f}% | "
                                                    f"Trades: {m['total_trades']} | WinRate: {m['win_rate_pct']:.1f}%"
                                                )
                                                
        print(f"\n=======================================================")
        print(f"[SUCCESS] SELF-IMPROVEMENT COMPLETED ({tested_configs} configurations explored)")
        print(f"Final Sharpe Ratio: {best_metrics['sharpe_ratio']:.2f} (Target > {self.target_sharpe})")
        print(f"=======================================================")
        
        return best_params, base_metrics, best_metrics
