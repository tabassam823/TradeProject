"""
Risk Management and Execution State Machine Module.
Implements Dynamic Risk Budgeting, Volatility Stop Loss/Take Profit,
Dynamic Trailing Stop, SMA-200 Trend Validation, and Circuit Breaker Cooldowns.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional

class RiskExecutionEngine:
    def __init__(
        self,
        initial_capital: float = 1000.0,
        risk_pct: float = 0.02,
        entry_z: float = 1.4,
        exit_z: float = 0.0,
        min_hold_hours: int = 12,
        sl_atr_mult: float = 1.5,
        tp_atr_mult: Optional[float] = None,
        trail_act_atr: Optional[float] = 1.5,
        trail_dist_atr: Optional[float] = 1.0,
        smooth_span: int = 4,
        z_window: int = 168,
        fee_rate: float = 0.00075,
        max_leverage: float = 2.0,
        use_sma_filter: bool = True,
        allow_short: bool = True,
        use_cooldown: bool = True,
        max_lose_streak: int = 3,
        cooldown_hours: int = 24
    ):
        self.initial_capital = initial_capital
        self.risk_pct = risk_pct
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.min_hold_hours = min_hold_hours
        self.sl_atr_mult = sl_atr_mult
        self.tp_atr_mult = tp_atr_mult
        self.trail_act_atr = trail_act_atr
        self.trail_dist_atr = trail_dist_atr
        self.smooth_span = smooth_span
        self.z_window = z_window
        self.fee_rate = fee_rate
        self.max_leverage = max_leverage
        self.use_sma_filter = use_sma_filter
        self.allow_short = allow_short
        self.use_cooldown = use_cooldown
        self.max_lose_streak = max_lose_streak
        self.cooldown_hours = cooldown_hours

    def simulate(self, df_input: pd.DataFrame, pred_col: str = 'pred_return') -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Executes the iterative bar-by-bar backtest simulation.
        """
        df = df_input.copy()
        
        # 1. Smooth signal & Rolling Z-Score
        df['smooth_pred'] = df[pred_col].ewm(span=self.smooth_span, adjust=False).mean()
        roll_mean = df['smooth_pred'].rolling(self.z_window, min_periods=24).mean()
        roll_std = df['smooth_pred'].rolling(self.z_window, min_periods=24).std() + 1e-9
        df['pred_z'] = (df['smooth_pred'] - roll_mean) / roll_std
        
        n = len(df)
        z_vals = df['pred_z'].fillna(0.0).values
        close_vals = df['close'].values
        atr_vals = df['atr_14'].fillna(df['close'] * 0.01).values
        sma_vals = df['sma_200'].fillna(df['close']).values
        
        capital = self.initial_capital
        curr_pos = 0.0
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
        cooldown_status = []
        
        for i in range(n):
            current_close = close_vals[i]
            atr = atr_vals[i]
            sma = sma_vals[i]
            z = z_vals[i]
            
            # Cooldown check
            if cooldown_timer > 0:
                cooldown_timer -= 1
                in_cooldown = True
            else:
                in_cooldown = False
            cooldown_status.append(1 if in_cooldown else 0)
            
            # 1. Evaluate Active Position Exit
            if curr_pos != 0.0:
                holding_bars += 1
                exit_trade = False
                exit_reason = None
                exit_price = current_close
                
                if curr_pos == 1.0:
                    highest_price = max(highest_price, current_close)
                    # Trailing Stop logic
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
                    elif holding_bars >= self.min_hold_hours:
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
                    elif holding_bars >= self.min_hold_hours:
                        if z > self.entry_z:
                            exit_trade = True
                            exit_reason = 'SIGNAL_REVERSAL'
                        elif z > -self.exit_z:
                            exit_trade = True
                            exit_reason = 'SIGNAL_EXIT'
                            
                if exit_trade:
                    gross_pnl = (exit_price - entry_price) * curr_units * curr_pos
                    exit_fee = exit_price * curr_units * self.fee_rate
                    net_pnl = gross_pnl - exit_fee
                    capital += net_pnl
                    fees_paid_total += exit_fee
                    
                    # Update consecutive loss tracker
                    if net_pnl < 0:
                        consecutive_losses += 1
                        if self.use_cooldown and consecutive_losses >= self.max_lose_streak:
                            cooldown_timer = self.cooldown_hours
                    else:
                        consecutive_losses = 0
                        
                    trade_logs.append({
                        'timestamp': df.index[i],
                        'side': 'LONG' if curr_pos == 1.0 else 'SHORT',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'units': curr_units,
                        'gross_pnl': gross_pnl,
                        'net_pnl': net_pnl,
                        'exit_fee': exit_fee,
                        'reason': exit_reason,
                        'holding_hours': holding_bars
                    })
                    curr_pos = 0.0
                    curr_units = 0.0
                    holding_bars = 0
                    
            # 2. Evaluate Flat Entry Condition
            if curr_pos == 0.0 and not (self.use_cooldown and in_cooldown):
                risk_dollar = max(1.0, self.risk_pct * capital)
                sl_dist = max(self.sl_atr_mult * atr, current_close * 0.005)
                max_units = (capital * self.max_leverage) / current_close
                target_units = min(risk_dollar / sl_dist, max_units)
                
                sma_long_ok = (current_close > sma) if self.use_sma_filter else True
                if z > self.entry_z and sma_long_ok:
                    curr_pos = 1.0
                    curr_units = target_units
                    entry_price = current_close
                    sl_price = entry_price - sl_dist
                    tp_price = entry_price + (self.tp_atr_mult * atr) if self.tp_atr_mult is not None else 0.0
                    highest_price = entry_price
                    entry_fee = entry_price * curr_units * self.fee_rate
                    capital -= entry_fee
                    fees_paid_total += entry_fee
                    holding_bars = 0
                elif self.allow_short:
                    sma_short_ok = (current_close < sma) if self.use_sma_filter else True
                    if z < -self.entry_z and sma_short_ok:
                        curr_pos = -1.0
                        curr_units = target_units
                        entry_price = current_close
                        sl_price = entry_price + sl_dist
                        tp_price = entry_price - (self.tp_atr_mult * atr) if self.tp_atr_mult is not None else 0.0
                        lowest_price = entry_price
                        entry_fee = entry_price * curr_units * self.fee_rate
                        capital -= entry_fee
                        fees_paid_total += entry_fee
                        holding_bars = 0
                        
            unrealized = (current_close - entry_price) * curr_units * curr_pos if curr_pos != 0 else 0.0
            current_equity = capital + unrealized
            capital_curve.append(current_equity)
            positions.append(curr_pos)
            
        df['capital_equity'] = capital_curve
        df['strategy_pos'] = positions
        df['cooldown_active'] = cooldown_status
        df['returns'] = df['capital_equity'].pct_change().fillna(0.0)
        
        trades_df = pd.DataFrame(trade_logs)
        metrics = self._calculate_metrics(df, trades_df, fees_paid_total)
        return df, trades_df, metrics

    def _calculate_metrics(self, df: pd.DataFrame, trades_df: pd.DataFrame, fees_paid_total: float) -> Dict[str, Any]:
        """
        Calculates annualized financial performance metrics.
        """
        initial = self.initial_capital
        final = df['capital_equity'].iloc[-1]
        net_ret = (final / initial) - 1.0
        
        bnh_ret = (df['close'].iloc[-1] / df['close'].iloc[0]) - 1.0
        
        roll_max = df['capital_equity'].cummax()
        drawdowns = (df['capital_equity'] - roll_max) / roll_max
        max_dd = drawdowns.min()
        
        mean_ret = df['returns'].mean()
        std_ret = df['returns'].std()
        sharpe = (mean_ret / (std_ret + 1e-9)) * np.sqrt(8760)
        
        n_trades = len(trades_df)
        win_rate = (trades_df['net_pnl'] > 0).mean() * 100 if n_trades > 0 else 0.0
        
        tot_gain = trades_df[trades_df['net_pnl'] > 0]['net_pnl'].sum() if n_trades > 0 else 0.0
        tot_loss = trades_df[trades_df['net_pnl'] < 0]['net_pnl'].abs().sum() if n_trades > 0 else 1.0
        profit_factor = (tot_gain / (tot_loss + 1e-9)) if tot_loss > 0 else 0.0
        
        return {
            'initial_capital': initial,
            'final_equity': final,
            'total_net_return_pct': net_ret * 100,
            'buy_and_hold_return_pct': bnh_ret * 100,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_dd * 100,
            'total_trades': n_trades,
            'win_rate_pct': win_rate,
            'profit_factor': profit_factor,
            'total_fees_paid': fees_paid_total
        }
