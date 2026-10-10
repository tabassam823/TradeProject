"""
Model Training & Walk-Forward Engine Module.
Implements Purged Rolling Walk-Forward Retraining with LightGBM and strict purge gaps
to eliminate look-ahead bias in financial time series.
"""
import time
import numpy as np
import pandas as pd
import lightgbm as lgb
from typing import Tuple, List, Dict, Any
from .config import LGBM_PARAMS, PURGED_TRAIN_DAYS, PURGED_TEST_DAYS, PURGE_GAP_HOURS

def run_purged_walk_forward_retraining(
    df_features: pd.DataFrame,
    feature_cols: List[str],
    target_col: str = 'target_return_1h',
    horizon: int = 1,
    train_days: int = PURGED_TRAIN_DAYS,
    test_days: int = PURGED_TEST_DAYS,
    lgb_params: Dict[str, Any] = None,
    verbose: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Executes Purged Rolling Walk-Forward Retraining fold-by-fold.
    Guarantees out-of-sample evaluation with no data leakage.
    """
    if lgb_params is None:
        lgb_params = LGBM_PARAMS.copy()
        
    candles_per_day = 24
    train_size = train_days * candles_per_day
    test_size = test_days * candles_per_day
    step_size = test_size
    n_rows = len(df_features)
    
    predictions = []
    feature_importances = []
    
    start_idx = 0
    fold = 1
    start_time_all = time.time()
    
    if verbose:
        print(f"Starting Purged Rolling Walk-Forward Retraining...")
        print(f"Train Window: {train_days}d ({train_size} bars) | Purge Gap: {horizon} bar(s) | Test Window: {test_days}d ({test_size} bars)")
        
    while start_idx + train_size < n_rows:
        train_end_idx = start_idx + train_size
        test_end_idx = min(train_end_idx + test_size, n_rows)
        
        # Purge Gap prevents target label overlap leakage
        train_df = df_features.iloc[start_idx : train_end_idx - horizon]
        test_df = df_features.iloc[train_end_idx : test_end_idx]
        
        if len(test_df) == 0:
            break
            
        X_train, y_train = train_df[feature_cols], train_df[target_col]
        X_test, y_test = test_df[feature_cols], test_df[target_col]
        
        model = lgb.LGBMRegressor(**lgb_params)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        
        test_res = test_df[['close', 'ret_next_1h', 'atr_14', 'sma_200', 'ema_50']].copy()
        test_res['pred_return'] = y_pred
        test_res['fold'] = fold
        predictions.append(test_res)
        
        feature_importances.append(model.feature_importances_)
        
        if verbose and (fold % 10 == 1 or test_end_idx == n_rows):
            train_start_str = train_df.index[0].strftime('%Y-%m-%d')
            train_end_str = train_df.index[-1].strftime('%Y-%m-%d')
            test_start_str = test_df.index[0].strftime('%Y-%m-%d')
            test_end_str = test_df.index[-1].strftime('%Y-%m-%d')
            print(f"  Fold {fold:02d}: Train [{train_start_str} -> {train_end_str}] | Test [{test_start_str} -> {test_end_str}] (N={len(test_df)})")
            
        start_idx += step_size
        fold += 1
        
    total_duration = time.time() - start_time_all
    results_df = pd.concat(predictions).sort_index()
    
    avg_importance = np.mean(feature_importances, axis=0)
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': avg_importance
    }).sort_values('importance', ascending=False)
    
    if verbose:
        print(f"[SUCCESS] {fold-1} walk-forward folds completed in {total_duration:.2f} seconds.")
        
    return results_df, importance_df
