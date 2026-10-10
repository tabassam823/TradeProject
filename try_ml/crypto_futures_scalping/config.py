"""
Configuration Module for Crypto Futures Scalping ML Trading System.
Defines parameters for 5-minute Solana (SOL) futures scalping, exchange frictions,
purged walk-forward training windows, and risk management constraints.
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Assets and High-Frequency Scalping Data
TARGET_TICKER = "SOL-USD"
LEAD_TICKER = "BTC-USD"
TIMEFRAME = "5m"
LOOKBACK_DAYS = 60  # 60 days of 5m data (~17,200 bars)
FORWARD_HORIZON_BARS = 3  # 3 bars = 15 minutes prediction horizon

# Exchange Friction & Futures Simulation Parameters
DEFAULT_INITIAL_CAPITAL = 1000.0
# Binance VIP0 Futures Taker Fee (0.05%) + Execution Slippage (0.01%) = 0.06% (0.0006)
DEFAULT_FEE_RATE = 0.0006
DEFAULT_LEVERAGE = 3.0
RISK_BUDGET_PCT = 0.015  # 1.5% capital risk per trade

# Purged Walk-Forward Retraining Parameters (5m bars)
# 288 bars/day -> 14 days = 4,032 bars train, 2 days = 576 bars test
PURGED_TRAIN_DAYS = 14
PURGED_TEST_DAYS = 2
PURGE_GAP_BARS = 3

# LightGBM Hyperparameters for High-Frequency Scalping
LGBM_PARAMS = {
    'objective': 'regression',
    'metric': 'rmse',
    'boosting_type': 'gbdt',
    'n_estimators': 180,
    'learning_rate': 0.035,
    'num_leaves': 31,
    'max_depth': 6,
    'min_child_samples': 30,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': 42,
    'device': 'cpu',
    'n_jobs': -1,
    'verbose': -1
}

# Baseline Strategy Parameters (Unoptimized High-Frequency Scalper)
BASELINE_SCALPER_PARAMS = {
    'entry_z': 0.8,
    'exit_z': 0.1,
    'min_hold_bars': 2,        # 10 minutes
    'max_hold_bars': 24,       # 2 hours max
    'sl_atr_mult': 1.5,
    'tp_atr_mult': 2.0,
    'trail_act_atr': None,
    'trail_dist_atr': None,
    'smooth_span': 3,
    'z_window': 288,           # 24 hours rolling window (288 5m bars)
    'use_trend_filter': False,
    'use_vol_filter': False,
    'allow_short': True,
    'fee_rate': DEFAULT_FEE_RATE,
    'leverage': DEFAULT_LEVERAGE,
    'risk_pct': RISK_BUDGET_PCT
}

# Target Optimization Metrics
TARGET_SHARPE_RATIO = 1.50
