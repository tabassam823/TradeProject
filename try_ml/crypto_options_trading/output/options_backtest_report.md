# 📊 Solana Crypto Options ML Trading: Self-Improvement Report

## 1. Executive Summary & Performance Comparison

| Metrik | Baseline Options | Optimal Self-Improved Options | Futures (Week 3 Benchmark) | B&H Spot SOL |
| :--- | :--- | :--- | :--- | :--- |
| **Sharpe Ratio** | **-2.43** | **1.54** | 3.19 | -0.15 |
| **Net Return** | **-42.17%** | **+39.87%** | +225.71% | -10.88% |
| **Max Drawdown** | **-43.73%** | **-18.87%** | -24.83% | -55.20% |
| **Win Rate** | **34.6%** | **33.3%** | 54.8% | N/A |
| **Profit Factor** | **0.75** | **1.41** | 1.66 | N/A |
| **Total Trades** | **246** | **114** | 228 | 1 |
| **Total Fees Paid** | **$189.14** | **$137.87** | $1,130.76 | $0.00 |

## 2. Best Configuration Found

```json
{
  "strategy_type": "outright",
  "strike_moneyness": 1.0,
  "spread_width_pct": 0.05,
  "dte_hours": 72,
  "entry_z": 1.4,
  "exit_z": 0.0,
  "min_hold_hours": 12,
  "take_profit_pct": null,
  "stop_loss_pct": 0.4,
  "trail_act_pct": null,
  "trail_dist_pct": null,
  "smooth_span": 4,
  "z_window": 168,
  "use_sma_filter": true,
  "allow_bearish_puts": true,
  "use_cooldown": true,
  "max_lose_streak": 3,
  "cooldown_hours": 24
}
```

## 3. Structural Insights: Options vs Futures in Crypto Trading

1. **Asymmetric Downside Protection**:
   - Pada futures, risiko likuidasi dan gap-down loss bersifat linear.
   - Pada options (long call/put), kerugian maksimal dibatasi secara pasti pada *premium paid* (3% risiko modal per trade) tanpa risiko margin liquidation.

2. **Theta Decay vs Momentum Horizon**:
   - Tantangan utama options adalah *Theta decay* (penyusutan nilai waktu).
   - Strategi yang optimal menyeimbangkan DTE (Days to Expiration) dan ambang *Take-Profit pada premium* sebelum peluruhan waktu menggerus keuntungan.

3. **Top Feature Signals**:
- **candle_hl_range**: 74.49
- **btc_ret_1**: 70.81
- **ret_3**: 54.86
- **sol_btc_rel_strength**: 51.91
- **dist_sma_200**: 51.23
- **news_sentiment_ema_24h**: 51.19
- **ret_2**: 47.86
- **natr_14**: 46.98
- **btc_ret_6**: 45.72
- **news_sentiment_shock**: 44.93
