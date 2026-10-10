"""
Feature Engineering Module for Crypto Alpha & Options Volatility Signals.
Constructs strictly stationary technical indicators, volatility surfaces,
cross-asset momentum, and macroeconomic/micro news sentiment factors.
"""
import numpy as np
import pandas as pd
from typing import Tuple, List

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Standard Relative Strength Index calculation."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def build_asset_features(
    df_raw: pd.DataFrame,
    df_fng_input: pd.DataFrame,
    df_news_input: pd.DataFrame,
    horizon: int = 1
) -> pd.DataFrame:
    """
    Constructs comprehensive alpha & volatility feature table for an individual asset.
    Uses pd.merge_asof with backward direction to prevent future information leakage.
    """
    df = df_raw.copy()
    fng = df_fng_input.copy()
    news = df_news_input.copy()
    
    # Ensure compatible datetime index
    fng.index = fng.index.astype(df.index.dtype)
    news.index = news.index.astype(df.index.dtype)
    
    # 1. Asynchronous Merge Fear & Greed Index
    df = pd.merge_asof(df.sort_index(), fng.sort_index(), left_index=True, right_index=True, direction='backward')
    df['fng_value'] = df['fng_value'].ffill().bfill()
    df['fng_change_1d'] = df['fng_change_1d'].ffill().fillna(0.0)
    df['fng_regime_z'] = df['fng_regime_z'].ffill().fillna(0.0)
    
    # 2. Asynchronous Merge Hourly News Sentiment
    news['news_sentiment_ema_24h'] = news['news_sentiment_1h'].ewm(span=24, adjust=False).mean()
    news['news_sentiment_shock'] = news['news_sentiment_1h'] - news['news_sentiment_ema_24h']
    
    df = pd.merge_asof(df.sort_index(), news.sort_index(), left_index=True, right_index=True, direction='backward')
    df['news_sentiment_1h'] = df['news_sentiment_1h'].ffill().fillna(0.0)
    df['news_sentiment_ema_24h'] = df['news_sentiment_ema_24h'].ffill().fillna(0.0)
    df['news_sentiment_shock'] = df['news_sentiment_shock'].ffill().fillna(0.0)
    df['news_count_1h'] = df['news_count_1h'].ffill().fillna(0.0)
    
    # 3. Pure Stationary Price Returns
    for p in [1, 2, 3, 6, 12, 24, 48]:
        df[f'ret_{p}'] = df['close'].pct_change(p)
        df[f'log_ret_{p}'] = np.log(df['close'] / (df['close'].shift(p) + 1e-9))
        
    # 4. Moving Average Distances
    for ma in [7, 14, 25, 50, 100, 200]:
        sma_val = df['close'].rolling(ma).mean()
        df[f'dist_sma_{ma}'] = (df['close'] - sma_val) / (sma_val + 1e-9)
        
    # 5. Volatility & ATR
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift(1)).abs()
    tr3 = (df['low'] - df['close'].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr_14'] = tr.rolling(14).mean()
    df['natr_14'] = df['atr_14'] / (df['close'] + 1e-9)
    df['sma_200'] = df['close'].rolling(200).mean()
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # 6. Options Specific Volatility Metrics (Annualized Realized Volatilities)
    annualization_factor = np.sqrt(8760.0)  # 24 * 365 hours
    df['realized_vol_24h'] = df['log_ret_1'].rolling(24).std() * annualization_factor
    df['realized_vol_168h'] = df['log_ret_1'].rolling(168).std() * annualization_factor
    df['vol_term_ratio'] = df['realized_vol_24h'] / (df['realized_vol_168h'] + 1e-9)
    
    # Parkinson Volatility (High-Low range based)
    hl_ratio = np.log(df['high'] / (df['low'] + 1e-9)) ** 2
    df['parkinson_vol_24h'] = np.sqrt((1.0 / (4.0 * np.log(2.0))) * hl_ratio.rolling(24).mean()) * annualization_factor
    
    # Fill any initial missing volatility
    df['realized_vol_24h'] = df['realized_vol_24h'].bfill().fillna(0.60)
    df['realized_vol_168h'] = df['realized_vol_168h'].bfill().fillna(0.60)
    df['vol_term_ratio'] = df['vol_term_ratio'].bfill().fillna(1.0)
    df['parkinson_vol_24h'] = df['parkinson_vol_24h'].bfill().fillna(0.60)
    
    # Estimated Implied Volatility (IV = Realized + 8% Volatility Risk Premium)
    df['implied_vol'] = np.clip(df['realized_vol_24h'] + 0.08, 0.25, 2.50)
    
    # 7. Normalized MACD
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    raw_macd = ema12 - ema26
    raw_signal = raw_macd.ewm(span=9, adjust=False).mean()
    raw_hist = raw_macd - raw_signal
    df['norm_macd'] = raw_macd / (df['atr_14'] + 1e-9)
    df['norm_macd_signal'] = raw_signal / (df['atr_14'] + 1e-9)
    df['norm_macd_hist'] = raw_hist / (df['atr_14'] + 1e-9)
    
    # 8. Oscillators & Bollinger Bands
    df['rsi_14'] = calculate_rsi(df['close'], 14)
    df['rsi_28'] = calculate_rsi(df['close'], 28)
    
    rolling_std = df['close'].rolling(20).std()
    bb_mid = df['close'].rolling(20).mean()
    bb_up = bb_mid + 2 * rolling_std
    bb_low = bb_mid - 2 * rolling_std
    df['bb_pct'] = (df['close'] - bb_low) / (bb_up - bb_low + 1e-9)
    
    # 9. Volume Ratios and Bar Anatomy
    vol_sma = df['volume'].rolling(14).mean()
    df['vol_ratio'] = df['volume'] / (vol_sma + 1e-9)
    df['candle_body'] = (df['close'] - df['open']) / (df['open'] + 1e-9)
    df['candle_hl_range'] = (df['high'] - df['low']) / (df['close'] + 1e-9)
    
    # 10. Non-overlapping Future Targets
    df[f'target_return_{horizon}h'] = df['close'].shift(-horizon) / df['close'] - 1.0
    df['ret_next_1h'] = df['close'].shift(-1) / df['close'] - 1.0
    
    df = df.dropna()
    return df

def inject_cross_asset_features(
    target_feat: pd.DataFrame,
    lead_feat: pd.DataFrame
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Injects cross-asset leader signals (BTC momentum & volume) into target asset (SOL).
    """
    common_idx = target_feat.index.intersection(lead_feat.index)
    sol_df = target_feat.loc[common_idx].copy()
    btc_df = lead_feat.loc[common_idx]
    
    sol_df['btc_ret_1'] = btc_df['ret_1']
    sol_df['btc_ret_6'] = btc_df['ret_6']
    sol_df['btc_vol_ratio'] = btc_df['vol_ratio']
    sol_df['sol_btc_rel_strength'] = sol_df['ret_6'] - btc_df['ret_6']
    
    excluded_cols = [
        'open', 'high', 'low', 'close', 'volume',
        'target_return_1h', 'ret_next_1h', 'atr_14', 'sma_200', 'ema_50',
        'dominant_source', 'implied_vol'
    ]
    
    feature_cols = [
        c for c in sol_df.columns
        if c not in excluded_cols and not c.startswith('target_return_')
        and sol_df[c].dtype in [np.float64, np.float32, np.int64, np.int32, float, int]
    ]
    
    return sol_df, feature_cols
