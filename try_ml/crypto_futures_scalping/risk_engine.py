"""
Risk Management and Execution State Machine Module for Futures Scalping.
Simulates bar-by-bar futures trading execution with exchange taker fees, slippage,
dynamic ATR stop loss/take profit, trailing stop lock-in, time-stops, and drawdown protections.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional

class ScalpingRiskEngine:
    def __init__(
        self,
        initial_capital: float = 1000.0,
        risk_pct: float = 0.015,
        entry_z: float = 1.6,
        exit_z: float = 0.0,
        min_hold_bars: int = 2,       # Minimum 10 minutes
        max_hold_bars: int = 18,      # Max 90 minutes time-stop
        sl_atr_mult: float = 1.5,
        tp_atr_mult: Optional[float] = 2.5,
        trail_act_atr: Optional[float] = 1.2,
        trail_dist_atr: Optional[float] = 0.8,
        smooth_span: int = 3,
        z_window: int = 288,          # 24h rolling z-score window (288 5m bars)
        fee_rate: float = 0.0006,      # 0.05% taker + 0.01% slippage
        leverage: float = 3.0,
        use_trend_filter: bool = True,
        use_vol_filter: bool = False,
        allow_short: bool = True,
        use_cooldown: bool = True,
        max_lose_streak: int = 3,
        cooldown_bars: int = 24       # 2 hours cooldown
    ):
        self.initial_capital = initial_capital
        self.risk_pct = risk_pct
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.min_hold_bars = min_hold_bars
        self.max_hold_bars = max_hold_bars
        self.sl_atr_mult = sl_atr_mult
        self.tp_atr_mult = tp_atr_mult
        self.trail_act_atr = trail_act_atr
        self.trail_dist_atr = trail_dist_atr
        self.smooth_span = smooth_span
        self.z_window = z_window
        self.fee_rate = fee_rate
        self.leverage = leverage
        self.use_trend_filter = use_trend_filter
        self.use_vol_filter = use_vol_filter
        self.allow_short = allow_short
        self.use_cooldown = use_cooldown
        self.max_lose_streak = max_lose_streak
        self.cooldown_bars = cooldown_bars

    def simulate(self, df_input: pd.DataFrame, pred_col: str = 'pred_return') -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Executes the iterative 5-minute bar-by-bar scalping backtest simulation.
        """
        df = df_input.copy()
        
        # 1. Smooth prediction signal & calculate Rolling Z-Score
        df['smooth_pred'] = df[pred_col].ewm(span=self.smooth_span, adjust=False).mean()
        roll_mean = df['smooth_pred'].rolling(self.z_window, min_periods=36).mean()
        roll_std = df['smooth_pred'].rolling(self.z_window, min_periods=36).std() + 1e-9
        df['pred_z'] = (df['smooth_pred'] - roll_mean) / roll_std
        
        n = len(df)
        z_vals = df['pred_z'].fillna(0.0).values
        close_vals = df['close'].values
        atr_vals = df['atr_14'].fillna(df['close'] * 0.005).values
        sma_vals = df['sma_200'].fillna(df['close']).values
        vol_ratio_vals = df['vol_ratio'].fillna(1.0).values if 'vol_ratio' in df.columns else np.ones(n)
        
        capital = self.initial_capital
        curr_pos = 0.0       # +1 for Long, -1 for Short, 0 for Flat
        curr_units = 0.0
        entry_price = 0.0
        sl_price = 0.0
        tp_price = 0.0
        holding_bars = 0
        highest_price = 0.0
        lowest_price = 1e9
        fees_paid_total = 0.0
        
        consecutive_losses = 0
        cooldown_timer = 0
        
        capital_curve = []
        positions = []
        trade_logs = []
        
        for i in range(n):
            current_close = close_vals[i]
            atr = atr_vals[i]
            sma = sma_vals[i]
            z = z_vals[i]
            vol_ratio = vol_ratio_vals[i]
            
            # Cooldown Management
            if cooldown_timer > 0:
                cooldown_timer -= 1
                in_cooldown = True
            else:
                in_cooldown = False
                
            # 1. Evaluate Active Position Exits
            if curr_pos != 0.0:
                holding_bars += 1
                exit_trade = False
                exit_reason = None
                exit_price = current_close
                
                if curr_pos == 1.0:
                    highest_price = max(highest_price, current_close)
                    # Trailing Stop calculation
                    if self.trail_act_atr is not None and (highest_price - entry_price) >= self.trail_act_atr * atr:
                        trail_sl = highest_price - self.trail_dist_atr * atr
                        sl_price = max(sl_price, trail_sl)
                        
                    if current_close <= sl_price:
                        exit_trade = True
                        exit_reason = 'STOP_LOSS'
                        exit_price = sl_price
                    elif self.tp_atr_mult is not None and current_close >= tp_price:
                        exit_trade = True
                        exit_reason = 'TAKE_PROFIT'
                        exit_price = tp_price
                    elif self.max_hold_bars is not None and holding_bars >= self.max_hold_bars:
                        exit_trade = True
                        exit_reason = 'TIME_STOP'
                    elif holding_bars >= self.min_hold_bars:
                        if self.allow_short and (z < -self.entry_z):
                            exit_trade = True
                            exit_reason = 'SIGNAL_REVERSAL'
                        elif z < self.exit_z:
                            exit_trade = True
                            exit_reason = 'SIGNAL_EXIT'
                            
                elif curr_pos == -1.0:
                    lowest_price = min(lowest_price, current_close)
                    # Trailing Stop for Short
                    if self.trail_act_atr is not None and (entry_price - lowest_price) >= self.trail_act_atr * atr:
                        trail_sl = lowest_price + self.trail_dist_atr * atr
                        sl_price = min(sl_price, trail_sl)
                        
                    if current_close >= sl_price:
                        exit_trade = True
                        exit_reason = 'STOP_LOSS'
                        exit_price = sl_price
                    elif self.tp_atr_mult is not None and current_close <= tp_price:
                        exit_trade = True
                        exit_reason = 'TAKE_PROFIT'
                        exit_price = tp_price
                    elif self.max_hold_bars is not None and holding_bars >= self.max_hold_bars:
                        exit_trade = True
                        exit_reason = 'TIME_STOP'
                    elif holding_bars >= self.min_hold_bars:
                        if z > self.entry_z:
                            exit_trade = True
                            exit_reason = 'SIGNAL_REVERSAL'
                        elif z > -self.exit_z:
                            exit_trade = True
                            exit_reason = 'SIGNAL_EXIT'
                            
                if exit_trade:
                    # Calculate Gross and Net PnL
                    trade_notional_exit = curr_units * exit_price
                    exit_fee = trade_notional_exit * self.fee_rate
                    fees_paid_total += exit_fee
                    
                    if curr_pos == 1.0:
                        gross_pnl = curr_units * (exit_price - entry_price)
                    else:
                        gross_pnl = curr_units * (entry_price - exit_price)
                        
                    net_pnl = gross_pnl - exit_fee
                    capital += net_pnl
                    
                    # Record Trade Log
                    pnl_pct = (net_pnl / (curr_units * entry_price + 1e-9)) * 100
                    trade_logs.append({
                        'exit_time': df.index[i],
                        'side': 'LONG' if curr_pos == 1.0 else 'SHORT',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'units': curr_units,
                        'holding_bars': holding_bars,
                        'gross_pnl': gross_pnl,
                        'exit_fee': exit_fee,
                        'net_pnl': net_pnl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': exit_reason,
                        'equity_after': capital
                    })
                    
                    # Update streak / cooldown
                    if net_pnl < 0:
                        consecutive_losses += 1
                        if self.use_cooldown and consecutive_losses >= self.max_lose_streak:
                            cooldown_timer = self.cooldown_bars
                    else:
                        consecutive_losses = 0
                        
                    curr_pos = 0.0
                    curr_units = 0.0
                    
            # 2. Evaluate New Position Entries (if Flat and not in Cooldown)
            if curr_pos == 0.0 and not in_cooldown and i < n - 1:
                long_cond = (z > self.entry_z)
                short_cond = (z < -self.entry_z) if self.allow_short else False
                
                # Trend Alignment Filter
                if self.use_trend_filter:
                    long_cond = long_cond and (current_close > sma)
                    short_cond = short_cond and (current_close < sma)
                    
                # Volatility / Volume Surge Filter
                if self.use_vol_filter:
                    long_cond = long_cond and (vol_ratio >= 1.0)
                    short_cond = short_cond and (vol_ratio >= 1.0)
                    
                if long_cond or short_cond:
                    curr_pos = 1.0 if long_cond else -1.0
                    entry_price = current_close
                    highest_price = current_close
                    lowest_price = current_close
                    holding_bars = 0
                    
                    # Volatility-Based Stop Loss & Sizing
                    sl_dist = max(self.sl_atr_mult * atr, current_close * 0.003)
                    
                    if curr_pos == 1.0:
                        sl_price = entry_price - sl_dist
                        tp_price = entry_price + (self.tp_atr_mult * atr) if self.tp_atr_mult else None
                    else:
                        sl_price = entry_price + sl_dist
                        tp_price = entry_price - (self.tp_atr_mult * atr) if self.tp_atr_mult else None
                        
                    # Risk-Budget Position Sizing with Leverage Cap
                    risk_amount = capital * self.risk_pct
                    sl_pct = sl_dist / entry_price
                    target_notional = risk_amount / (sl_pct + 1e-9)
                    max_notional = capital * self.leverage
                    actual_notional = min(target_notional, max_notional)
                    
                    curr_units = actual_notional / entry_price
                    
                    # Deduct Entry Fee
                    entry_fee = actual_notional * self.fee_rate
                    capital -= entry_fee
                    fees_paid_total += entry_fee
                    
            # Mark-to-Market Equity Tracking
            if curr_pos == 1.0:
                unrealized_pnl = curr_units * (current_close - entry_price)
            elif curr_pos == -1.0:
                unrealized_pnl = curr_units * (entry_price - current_close)
            else:
                unrealized_pnl = 0.0
                
            current_equity = capital + unrealized_pnl
            capital_curve.append(current_equity)
            positions.append(curr_pos)
            
        # Compile Simulation Results DataFrame
        df['capital_equity'] = capital_curve
        df['position'] = positions
        
        trades_df = pd.DataFrame(trade_logs)
        metrics = self._calculate_metrics(df, trades_df, fees_paid_total)
        return df, trades_df, metrics

    def _calculate_metrics(self, df: pd.DataFrame, trades_df: pd.DataFrame, total_fees: float) -> Dict[str, Any]:
        """
        Computes institutional-grade trading performance metrics.
        """
        initial_cap = self.initial_capital
        final_equity = df['capital_equity'].iloc[-1]
        net_return_pct = ((final_equity - initial_cap) / initial_cap) * 100.0
        
        # 5m Returns (288 bars per day * 365 = 105,120 periods/year)
        equity_series = df['capital_equity']
        bar_returns = equity_series.pct_change().dropna()
        
        annual_factor = 288 * 365
        ret_mean = bar_returns.mean()
        ret_std = bar_returns.std()
        sharpe = (ret_mean / (ret_std + 1e-9)) * np.sqrt(annual_factor) if ret_std > 0 else 0.0
        
        # Sortino Ratio (Downside deviation only)
        downside_returns = bar_returns[bar_returns < 0]
        downside_std = downside_returns.std()
        sortino = (ret_mean / (downside_std + 1e-9)) * np.sqrt(annual_factor) if downside_std > 0 else 0.0
        
        # Drawdown Metrics
        cummax = equity_series.cummax()
        drawdowns = (equity_series - cummax) / cummax * 100.0
        max_dd = drawdowns.min()
        
        # Calmar Ratio (Annualized Return / Max Drawdown)
        total_days = len(df) / 288.0
        annualized_return_pct = (((final_equity / initial_cap) ** (365.0 / max(total_days, 1.0))) - 1.0) * 100.0
        calmar = (annualized_return_pct / (abs(max_dd) + 1e-9)) if abs(max_dd) > 0 else 0.0
        
        # Trade Statistics
        total_trades = len(trades_df)
        if total_trades > 0:
            winning_trades = trades_df[trades_df['net_pnl'] > 0]
            losing_trades = trades_df[trades_df['net_pnl'] <= 0]
            win_rate = (len(winning_trades) / total_trades) * 100.0
            
            gross_profit = winning_trades['gross_pnl'].sum() if len(winning_trades) > 0 else 0.0
            gross_loss = abs(losing_trades['gross_pnl'].sum()) if len(losing_trades) > 0 else 0.0
            profit_factor = (gross_profit / (gross_loss + 1e-9)) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0.0)
            avg_win = winning_trades['net_pnl'].mean() if len(winning_trades) > 0 else 0.0
            avg_loss = losing_trades['net_pnl'].mean() if len(losing_trades) > 0 else 0.0
            avg_holding = trades_df['holding_bars'].mean() * 5.0 # in minutes
        else:
            win_rate = 0.0
            profit_factor = 0.0
            avg_win = 0.0
            avg_loss = 0.0
            avg_holding = 0.0
            
        # Buy & Hold Benchmark Return
        bnh_return_pct = ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100.0
        
        return {
            'initial_capital': initial_cap,
            'final_equity': final_equity,
            'total_net_return_pct': net_return_pct,
            'annualized_return_pct': annualized_return_pct,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'max_drawdown_pct': max_dd,
            'total_trades': total_trades,
            'win_rate_pct': win_rate,
            'profit_factor': profit_factor,
            'avg_win_dollars': avg_win,
            'avg_loss_dollars': avg_loss,
            'avg_holding_minutes': avg_holding,
            'total_fees_paid': total_fees,
            'buy_and_hold_return_pct': bnh_return_pct
        }
