"""
Configuration Module for Crypto ML Trading System.
Defines directories, trading pairs, model hyperparameters, and risk constraints.
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

# Assets and Data Feeds
DEFAULT_TICKERS = ["SOL-USD", "BTC-USD"]
TIMEFRAME = "1h"
LOOKBACK_DAYS = 365
BENCHMARK_TICKER = "SOL-USD"

# Exchange Simulation Parameters
DEFAULT_INITIAL_CAPITAL = 1000.0
DEFAULT_TAKER_FEE_RATE = 0.00075  # 0.075% Binance/Bybit VIP0 Taker Fee
DEFAULT_MAX_LEVERAGE = 2.0
RISK_BUDGET_PCT = 0.02           # 2% capital risk per trade

# Model Architecture Parameters
PURGED_TRAIN_DAYS = 60           # 60 days rolling train window
PURGED_TEST_DAYS = 7             # 7 days rolling test window
PURGE_GAP_HOURS = 1              # Zero look-ahead bias gap

LGBM_PARAMS = {
    'objective': 'regression',
    'metric': 'rmse',
    'boosting_type': 'gbdt',
    'n_estimators': 150,
    'learning_rate': 0.03,
    'num_leaves': 31,
    'max_depth': 5,
    'min_child_samples': 20,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': 42,
    'device': 'cpu',
    'n_jobs': -1,
    'verbose': -1
}

# Baseline Strategy Parameters (Week 3/4 unoptimized)
BASELINE_PARAMS = {
    'entry_z': 0.8,
    'exit_z': 0.2,
    'min_hold_hours': 6,
    'sl_atr_mult': 1.5,
    'tp_atr_mult': 3.0,
    'trail_act_atr': None,
    'trail_dist_atr': None,
    'smooth_span': 4,
    'z_window': 168,
    'use_sma_filter': True,
    'allow_short': True
}

# Minimum Required Performance
TARGET_SHARPE_RATIO = 1.5
