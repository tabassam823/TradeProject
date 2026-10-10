"""
Alpha Feature Engineering Module for 5-Minute Futures Scalping.
Constructs strictly stationary micro-momentum, order flow proxies, volatility estimators,
volume surge dynamics, and cross-asset lead-lag signals with zero look-ahead bias.
"""
import numpy as np
import pandas as pd
from typing import Tuple, List
from .config import FORWARD_HORIZON_BARS

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Standard Relative Strength Index (RSI).
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def build_scalping_features(df_raw: pd.DataFrame, horizon: int = FORWARD_HORIZON_BARS) -> pd.DataFrame:
    """
    Constructs high-frequency scalping alpha features for 5m OHLCV bars.
    """
    df = df_raw.copy().sort_index()
    
    # 1. Stationary Returns & Log Returns
    for p in [1, 2, 3, 6, 12, 24, 48]:
        df[f'ret_{p}'] = df['close'].pct_change(p)
        df[f'log_ret_{p}'] = np.log(df['close'] / (df['close'].shift(p) + 1e-9))
        
    # 2. Price Acceleration (2nd derivative of price movement)
    df['accel_1'] = df['ret_1'] - df['ret_1'].shift(1)
    df['accel_3'] = df['ret_3'] - df['ret_3'].shift(3)
    
    # 3. Micro-Momentum & Oscillators
    df['rsi_7'] = calculate_rsi(df['close'], period=7)
    df['rsi_14'] = calculate_rsi(df['close'], period=14)
    df['rsi_36'] = calculate_rsi(df['close'], period=36)
    
    # Stochastic Oscillator
    low_14 = df['low'].rolling(14).min()
    high_14 = df['high'].rolling(14).max()
    df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14 + 1e-9))
    df['stoch_d'] = df['stoch_k'].rolling(3).mean()
    
    # Normalized MACD (Fast & Standard)
    # ATR 14
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift(1)).abs()
    tr3 = (df['low'] - df['close'].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr_14'] = tr.rolling(14).mean()
    df['natr_14'] = df['atr_14'] / (df['close'] + 1e-9)
    df['atr_36'] = tr.rolling(36).mean()
    
    # Fast MACD (6, 13, 5)
    ema6 = df['close'].ewm(span=6, adjust=False).mean()
    ema13 = df['close'].ewm(span=13, adjust=False).mean()
    fast_macd = ema6 - ema13
    fast_signal = fast_macd.ewm(span=5, adjust=False).mean()
    df['norm_fast_macd'] = fast_macd / (df['atr_14'] + 1e-9)
    df['norm_fast_macd_hist'] = (fast_macd - fast_signal) / (df['atr_14'] + 1e-9)
    
    # Standard MACD (12, 26, 9)
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    df['norm_macd'] = macd / (df['atr_14'] + 1e-9)
    df['norm_macd_hist'] = (macd - macd_signal) / (df['atr_14'] + 1e-9)
    
    # 4. Moving Average Distances & Slopes
    for span in [9, 21, 50, 200]:
        ema_val = df['close'].ewm(span=span, adjust=False).mean()
        df[f'ema_{span}'] = ema_val
        df[f'dist_ema_{span}'] = (df['close'] - ema_val) / (ema_val + 1e-9)
    
    df['ema_50_slope'] = (df['ema_50'] - df['ema_50'].shift(6)) / (df['ema_50'].shift(6) + 1e-9)
    df['sma_200'] = df['close'].rolling(200).mean()
    df['dist_sma_200'] = (df['close'] - df['sma_200']) / (df['sma_200'] + 1e-9)
    
    # 5. Volatility & Bollinger Band Squeeze
    bb_mid = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    bb_up = bb_mid + 2 * bb_std
    bb_low = bb_mid - 2 * bb_std
    df['bb_pct'] = (df['close'] - bb_low) / (bb_up - bb_low + 1e-9)
    df['bb_width'] = (bb_up - bb_low) / (bb_mid + 1e-9)
    
    # Parkinson High-Low Volatility
    hl_ratio = np.log(df['high'] / (df['low'] + 1e-9))
    df['parkinson_vol'] = np.sqrt((hl_ratio ** 2) / (4 * np.log(2)))
    
    # 6. Microstructure & Order Flow Proxies
    hl_range = df['high'] - df['low'] + 1e-9
    df['buying_pressure'] = (df['close'] - df['low']) / hl_range
    df['candle_body_ratio'] = (df['close'] - df['open']).abs() / hl_range
    df['upper_shadow_ratio'] = (df['high'] - df[['open', 'close']].max(axis=1)) / hl_range
    df['lower_shadow_ratio'] = (df[['open', 'close']].min(axis=1) - df['low']) / hl_range
    
    # Volume Dynamics & Signed Volume Flow
    vol_sma_20 = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / (vol_sma_20 + 1e-9)
    df['signed_vol_flow'] = np.sign(df['close'] - df['open']) * df['vol_ratio']
    
    # Rolling 24h VWAP Proxy (288 5m bars)
    pv = ((df['high'] + df['low'] + df['close']) / 3.0) * df['volume']
    rolling_pv = pv.rolling(288, min_periods=24).sum()
    rolling_v = df['volume'].rolling(288, min_periods=24).sum()
    df['vwap_24h'] = rolling_pv / (rolling_v + 1e-9)
    df['dist_vwap_24h'] = (df['close'] - df['vwap_24h']) / (df['vwap_24h'] + 1e-9)
    
    # 7. Non-overlapping Future Forward Return Target
    df[f'target_return_{horizon}bar'] = df['close'].shift(-horizon) / df['close'] - 1.0
    df['ret_next_1bar'] = df['close'].shift(-1) / df['close'] - 1.0
    
    df = df.dropna()
    return df

def inject_cross_asset_lead_lag(
    sol_features: pd.DataFrame,
    btc_raw: pd.DataFrame,
    horizon: int = FORWARD_HORIZON_BARS
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Injects Bitcoin 5m lead-lag signals (momentum, volatility, relative strength) into Solana.
    """
    btc_feat = build_scalping_features(btc_raw, horizon=horizon)
    common_idx = sol_features.index.intersection(btc_feat.index)
    
    sol_df = sol_features.loc[common_idx].copy()
    btc_df = btc_feat.loc[common_idx]
    
    # Cross-asset leader features
    sol_df['btc_ret_1'] = btc_df['ret_1']
    sol_df['btc_ret_3'] = btc_df['ret_3']
    sol_df['btc_ret_6'] = btc_df['ret_6']
    sol_df['btc_vol_ratio'] = btc_df['vol_ratio']
    sol_df['btc_buying_pressure'] = btc_df['buying_pressure']
    sol_df['btc_norm_fast_macd'] = btc_df['norm_fast_macd']
    
    # Relative strength (SOL vs BTC momentum)
    sol_df['sol_btc_rel_mom_3'] = sol_df['ret_3'] - btc_df['ret_3']
    sol_df['sol_btc_rel_mom_6'] = sol_df['ret_6'] - btc_df['ret_6']
    
    excluded_cols = [
        'open', 'high', 'low', 'close', 'volume',
        f'target_return_{horizon}bar', 'ret_next_1bar',
        'atr_14', 'atr_36', 'ema_9', 'ema_21', 'ema_50', 'ema_200', 'sma_200', 'vwap_24h'
    ]
    
    feature_cols = [
        c for c in sol_df.columns
        if c not in excluded_cols and not c.startswith('target_return_')
        and sol_df[c].dtype in [np.float64, np.float32, np.int64, np.int32, float, int]
    ]
    
    return sol_df, feature_cols
