"""
Configuration Module for Crypto Options ML Trading System.
Defines parameters for Black-Scholes options pricing, Deribit-like fee structure,
machine learning walk-forward validation, and options risk management.
"""
from pathlib import Path

# Directories
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = BASE_DIR / "output"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Assets
ASSET_NAME = "SOL-USD"
DEFAULT_TICKERS = ["SOL-USD", "BTC-USD"]
TIMEFRAME = "1h"
LOOKBACK_DAYS = 365

# Options Market Simulation Parameters
INITIAL_CAPITAL = 1000.0
RISK_PER_TRADE_PCT = 0.03        # 3% of current capital risked in option premium per trade
RISK_FREE_RATE = 0.05            # 5% annual risk-free rate
VOLATILITY_RISK_PREMIUM = 0.08   # Crypto IV premium over realized vol (8% annualized)

# Deribit-style Fee Structure for Crypto Options
# 0.03% of underlying asset price, capped at 12.5% of option premium
OPTION_FEE_UNDERLYING_PCT = 0.0003
OPTION_FEE_MAX_PREMIUM_PCT = 0.125
OPTION_SLIPPAGE_PREMIUM_PCT = 0.015  # 1.5% slippage on premium due to wider option bid-ask spreads

# Model Training Parameters (Purged Walk-Forward Retraining)
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

# Baseline Strategy Parameters for Solana Options
BASELINE_OPTIONS_PARAMS = {
    'strategy_type': 'outright',     # 'outright' (Long Call / Long Put) or 'spread' (Vertical Spread)
    'strike_moneyness': 1.0,         # ATM (1.0 = Spot)
    'dte_hours': 48,                 # 48 hours to expiration
    'entry_z': 0.8,
    'exit_z': 0.2,
    'min_hold_hours': 6,
    'take_profit_pct': 1.0,          # +100% gain on premium
    'stop_loss_pct': 0.5,            # -50% loss on premium
    'trail_act_pct': None,           # Trailing stop activation on premium return
    'trail_dist_pct': None,          # Trailing stop distance
    'smooth_span': 4,
    'z_window': 168,
    'use_sma_filter': True,
    'allow_bearish_puts': True
}

# Performance Target
TARGET_SHARPE_RATIO = 1.5
