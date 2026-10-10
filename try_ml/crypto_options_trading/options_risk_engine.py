"""
Options Risk Management & Execution Engine Module.
Simulates continuous mark-to-market options holding, dynamic Greeks exposure,
volatility repricing, premium-based stop-loss/take-profit, trailing stops,
expiration settlement, and Deribit fee/slippage structures.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
from .options_pricer import BlackScholesPricer
from .config import (
    INITIAL_CAPITAL, RISK_PER_TRADE_PCT, RISK_FREE_RATE,
    OPTION_FEE_UNDERLYING_PCT, OPTION_FEE_MAX_PREMIUM_PCT, OPTION_SLIPPAGE_PREMIUM_PCT
)

class OptionsExecutionEngine:
    def __init__(
        self,
        initial_capital: float = INITIAL_CAPITAL,
        risk_pct: float = RISK_PER_TRADE_PCT,
        strategy_type: str = 'outright',  # 'outright' or 'spread'
        strike_moneyness: float = 1.0,     # 1.0 = ATM, 1.02 = 2% OTM
        spread_width_pct: float = 0.05,    # 5% width for vertical spread
        dte_hours: int = 48,               # Days to expiration in hours
        entry_z: float = 1.0,
        exit_z: float = 0.0,
        min_hold_hours: int = 6,
        take_profit_pct: Optional[float] = 1.0,  # e.g. +100% gain on premium
        stop_loss_pct: Optional[float] = 0.50,   # e.g. -50% loss on premium
        trail_act_pct: Optional[float] = None,   # e.g. activates when premium up +50%
        trail_dist_pct: Optional[float] = None,  # e.g. 25% from peak premium
        smooth_span: int = 4,
        z_window: int = 168,
        use_sma_filter: bool = True,
        allow_bearish_puts: bool = True,
        use_cooldown: bool = True,
        max_lose_streak: int = 3,
        cooldown_hours: int = 24,
        fee_underlying_pct: float = OPTION_FEE_UNDERLYING_PCT,
        slippage_pct: float = OPTION_SLIPPAGE_PREMIUM_PCT
    ):
        self.initial_capital = initial_capital
        self.risk_pct = risk_pct
        self.strategy_type = strategy_type
        self.strike_moneyness = strike_moneyness
        self.spread_width_pct = spread_width_pct
        self.dte_hours = dte_hours
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.min_hold_hours = min_hold_hours
        self.take_profit_pct = take_profit_pct
        self.stop_loss_pct = stop_loss_pct
        self.trail_act_pct = trail_act_pct
        self.trail_dist_pct = trail_dist_pct
        self.smooth_span = smooth_span
        self.z_window = z_window
        self.use_sma_filter = use_sma_filter
        self.allow_bearish_puts = allow_bearish_puts
        self.use_cooldown = use_cooldown
        self.max_lose_streak = max_lose_streak
        self.cooldown_hours = cooldown_hours
        self.fee_underlying_pct = fee_underlying_pct
        self.slippage_pct = slippage_pct
        
        self.pricer = BlackScholesPricer(risk_free_rate=RISK_FREE_RATE)

    def _calc_contract_price(self, spot: float, strike: float, time_years: float, iv: float, option_type: str) -> float:
        if self.strategy_type == 'outright':
            if option_type == 'call':
                return self.pricer.price_call(spot, strike, time_years, iv)
            else:
                return self.pricer.price_put(spot, strike, time_years, iv)
        else:
            # Vertical spread
            if option_type == 'call':
                strike2 = strike * (1.0 + self.spread_width_pct)
                p1 = self.pricer.price_call(spot, strike, time_years, iv)
                p2 = self.pricer.price_call(spot, strike2, time_years, iv)
                return max(0.01, p1 - p2)
            else:
                strike2 = strike * (1.0 - self.spread_width_pct)
                p1 = self.pricer.price_put(spot, strike, time_years, iv)
                p2 = self.pricer.price_put(spot, strike2, time_years, iv)
                return max(0.01, p1 - p2)

    def simulate(self, df_input: pd.DataFrame, pred_col: str = 'pred_return') -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Executes bar-by-bar options backtest simulation.
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
        iv_vals = df['implied_vol'].fillna(0.65).values if 'implied_vol' in df.columns else np.full(n, 0.65)
        sma_vals = df['sma_200'].fillna(df['close']).values if 'sma_200' in df.columns else df['close'].values
        
        capital = self.initial_capital
        active_pos = None  # Dict storing active option position
        consecutive_losses = 0
        cooldown_timer = 0
        fees_paid_total = 0.0
        
        capital_curve = []
        equity_curve = []
        positions = []
        trade_logs = []
        greeks_history = []
        
        for i in range(n):
            current_close = close_vals[i]
            current_iv = iv_vals[i]
            sma = sma_vals[i]
            z = z_vals[i]
            
            # Cooldown logic
            if cooldown_timer > 0:
                cooldown_timer -= 1
                in_cooldown = True
            else:
                in_cooldown = False
                
            current_greeks = {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0}
            
            # --- 1. Evaluate Active Position ---
            if active_pos is not None:
                active_pos['holding_hours'] += 1
                h = active_pos['holding_hours']
                rem_hours = max(0, self.dte_hours - h)
                rem_t_years = rem_hours / 8760.0
                
                # Re-price option mark-to-market
                curr_price = self._calc_contract_price(
                    current_close, active_pos['strike'], rem_t_years, current_iv, active_pos['type']
                )
                
                # Calculate active Greeks
                g_dict = self.pricer.calculate_greeks(
                    current_close, active_pos['strike'], rem_t_years, current_iv, active_pos['type']
                )
                current_greeks = {
                    'delta': g_dict['delta'] * active_pos['units'],
                    'gamma': g_dict['gamma'] * active_pos['units'],
                    'theta': g_dict['theta_per_day'] * active_pos['units'],
                    'vega': g_dict['vega_1pct'] * active_pos['units']
                }
                
                # Premium return from entry
                entry_premium = active_pos['entry_premium']
                premium_return = (curr_price - entry_premium) / (entry_premium + 1e-9)
                active_pos['peak_price'] = max(active_pos['peak_price'], curr_price)
                
                exit_trade = False
                exit_reason = None
                exit_price = curr_price
                
                # Check Expiration
                if rem_hours == 0:
                    exit_trade = True
                    exit_reason = 'EXPIRATION'
                    # Cash settlement at expiration intrinsic value
                    if active_pos['type'] == 'call':
                        intrinsic = max(0.0, current_close - active_pos['strike'])
                        if self.strategy_type == 'spread':
                            strike2 = active_pos['strike'] * (1.0 + self.spread_width_pct)
                            intrinsic = min(intrinsic, strike2 - active_pos['strike'])
                    else:
                        intrinsic = max(0.0, active_pos['strike'] - current_close)
                        if self.strategy_type == 'spread':
                            strike2 = active_pos['strike'] * (1.0 - self.spread_width_pct)
                            intrinsic = min(intrinsic, active_pos['strike'] - strike2)
                    exit_price = intrinsic
                    
                # Check Stop Loss on Premium
                elif self.stop_loss_pct is not None and premium_return <= -self.stop_loss_pct:
                    exit_trade = True
                    exit_reason = 'STOP_LOSS_PREMIUM'
                    exit_price = entry_premium * (1.0 - self.stop_loss_pct)
                    
                # Check Take Profit on Premium
                elif self.take_profit_pct is not None and premium_return >= self.take_profit_pct:
                    exit_trade = True
                    exit_reason = 'TAKE_PROFIT_PREMIUM'
                    exit_price = entry_premium * (1.0 + self.take_profit_pct)
                    
                # Check Trailing Stop
                elif self.trail_act_pct is not None and (active_pos['peak_price'] - entry_premium) / entry_premium >= self.trail_act_pct:
                    trail_threshold = active_pos['peak_price'] * (1.0 - self.trail_dist_pct)
                    if curr_price <= trail_threshold:
                        exit_trade = True
                        exit_reason = 'TRAILING_STOP'
                        exit_price = trail_threshold
                        
                # Check Signal Exit / Reversal after minimum holding hours
                elif h >= self.min_hold_hours:
                    if active_pos['type'] == 'call':
                        if self.allow_bearish_puts and (z < -self.entry_z):
                            exit_trade = True
                            exit_reason = 'SIGNAL_REVERSAL'
                        elif z < self.exit_z:
                            exit_trade = True
                            exit_reason = 'SIGNAL_EXIT'
                    elif active_pos['type'] == 'put':
                        if z > self.entry_z:
                            exit_trade = True
                            exit_reason = 'SIGNAL_REVERSAL'
                        elif z > -self.exit_z:
                            exit_trade = True
                            exit_reason = 'SIGNAL_EXIT'
                            
                # Process Exit
                if exit_trade:
                    # Apply slippage on exit premium
                    net_exit_price = max(0.0, exit_price * (1.0 - self.slippage_pct))
                    gross_pnl = (net_exit_price - entry_premium) * active_pos['units']
                    
                    # Exit fee (no fee if expired out-of-the-money)
                    exit_fee = 0.0
                    if net_exit_price > 0.01:
                        exit_fee = self.pricer.calculate_deribit_fee(
                            current_close, net_exit_price, self.fee_underlying_pct
                        ) * active_pos['units']
                        
                    net_pnl = gross_pnl - exit_fee
                    capital += net_pnl
                    fees_paid_total += exit_fee
                    
                    if net_pnl < 0:
                        consecutive_losses += 1
                        if self.use_cooldown and consecutive_losses >= self.max_lose_streak:
                            cooldown_timer = self.cooldown_hours
                    else:
                        consecutive_losses = 0
                        
                    trade_logs.append({
                        'timestamp': df.index[i],
                        'type': active_pos['type'].upper(),
                        'strategy': self.strategy_type,
                        'strike': active_pos['strike'],
                        'spot_entry': active_pos['spot_entry'],
                        'spot_exit': current_close,
                        'entry_premium': entry_premium,
                        'exit_premium': exit_price,
                        'units': active_pos['units'],
                        'gross_pnl': gross_pnl,
                        'net_pnl': net_pnl,
                        'exit_fee': exit_fee,
                        'return_pct': (net_pnl / active_pos['risk_budget']) * 100.0,
                        'reason': exit_reason,
                        'holding_hours': h
                    })
                    active_pos = None
                    
            # --- 2. Evaluate New Entry Condition ---
            if active_pos is None and not (self.use_cooldown and in_cooldown):
                sma_long_ok = (current_close > sma) if self.use_sma_filter else True
                sma_short_ok = (current_close < sma) if self.use_sma_filter else True
                
                signal_type = None
                if z > self.entry_z and sma_long_ok:
                    signal_type = 'call'
                elif self.allow_bearish_puts and (z < -self.entry_z) and sma_short_ok:
                    signal_type = 'put'
                    
                if signal_type is not None:
                    # Strike selection
                    if signal_type == 'call':
                        strike = current_close * self.strike_moneyness
                    else:
                        strike = current_close * (2.0 - self.strike_moneyness) if self.strike_moneyness != 1.0 else current_close
                        
                    t_entry_years = self.dte_hours / 8760.0
                    raw_premium = self._calc_contract_price(
                        current_close, strike, t_entry_years, current_iv, signal_type
                    )
                    
                    # Entry premium with slippage (pay ask)
                    effective_entry_premium = raw_premium * (1.0 + self.slippage_pct)
                    
                    if effective_entry_premium > 0.05:
                        risk_budget = max(5.0, self.risk_pct * capital)
                        units = risk_budget / effective_entry_premium
                        
                        entry_fee = self.pricer.calculate_deribit_fee(
                            current_close, effective_entry_premium, self.fee_underlying_pct
                        ) * units
                        
                        # Deduct entry fee immediately
                        capital -= entry_fee
                        fees_paid_total += entry_fee
                        
                        active_pos = {
                            'type': signal_type,
                            'strike': strike,
                            'spot_entry': current_close,
                            'entry_premium': effective_entry_premium,
                            'peak_price': effective_entry_premium,
                            'units': units,
                            'risk_budget': risk_budget,
                            'holding_hours': 0
                        }
                        
            # Mark-to-market equity
            unrealized_pnl = 0.0
            if active_pos is not None:
                rem_h = max(0, self.dte_hours - active_pos['holding_hours'])
                curr_p = self._calc_contract_price(
                    current_close, active_pos['strike'], rem_h / 8760.0, current_iv, active_pos['type']
                )
                unrealized_pnl = (curr_p - active_pos['entry_premium']) * active_pos['units']
                
            equity = capital + unrealized_pnl
            capital_curve.append(capital)
            equity_curve.append(equity)
            positions.append(1 if (active_pos and active_pos['type'] == 'call') else (-1 if (active_pos and active_pos['type'] == 'put') else 0))
            greeks_history.append(current_greeks)
            
        # Assemble simulation results DataFrame
        df['capital'] = capital_curve
        df['equity'] = equity_curve
        df['position'] = positions
        df['delta'] = [g['delta'] for g in greeks_history]
        df['gamma'] = [g['gamma'] for g in greeks_history]
        df['theta'] = [g['theta'] for g in greeks_history]
        df['vega'] = [g['vega'] for g in greeks_history]
        
        trades_df = pd.DataFrame(trade_logs) if trade_logs else pd.DataFrame(columns=[
            'timestamp', 'type', 'strategy', 'strike', 'spot_entry', 'spot_exit',
            'entry_premium', 'exit_premium', 'units', 'gross_pnl', 'net_pnl',
            'exit_fee', 'return_pct', 'reason', 'holding_hours'
        ])
        
        # Calculate summary metrics
        metrics = self._calculate_metrics(df, trades_df, fees_paid_total)
        return df, trades_df, metrics

    def _calculate_metrics(self, df: pd.DataFrame, trades: pd.DataFrame, total_fees: float) -> Dict[str, Any]:
        equity_series = df['equity']
        returns = equity_series.pct_change().fillna(0.0)
        
        # Annualized Sharpe Ratio (hourly bars)
        std_ret = returns.std()
        if std_ret > 1e-9:
            sharpe = (returns.mean() / std_ret) * np.sqrt(8760.0)
        else:
            sharpe = 0.0
            
        # Cumulative returns and drawdown
        cum_ret = equity_series / self.initial_capital
        rolling_max = cum_ret.cummax()
        drawdown = (cum_ret - rolling_max) / rolling_max
        max_drawdown_pct = float(drawdown.min() * 100.0)
        
        total_net_return_pct = float(((equity_series.iloc[-1] / self.initial_capital) - 1.0) * 100.0)
        buy_hold_ret_pct = float(((df['close'].iloc[-1] / df['close'].iloc[0]) - 1.0) * 100.0)
        
        n_trades = len(trades)
        if n_trades > 0:
            winning_trades = trades[trades['net_pnl'] > 0]
            losing_trades = trades[trades['net_pnl'] < 0]
            win_rate_pct = float((len(winning_trades) / n_trades) * 100.0)
            
            gross_profit = float(winning_trades['net_pnl'].sum()) if len(winning_trades) > 0 else 0.0
            gross_loss = float(abs(losing_trades['net_pnl'].sum())) if len(losing_trades) > 0 else 1e-9
            profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else float('nan')
            avg_return_per_trade_pct = float(trades['return_pct'].mean())
        else:
            win_rate_pct = 0.0
            profit_factor = 0.0
            avg_return_per_trade_pct = 0.0
            
        return {
            'initial_capital': self.initial_capital,
            'final_equity': float(equity_series.iloc[-1]),
            'total_net_return_pct': total_net_return_pct,
            'buy_and_hold_return_pct': buy_hold_ret_pct,
            'sharpe_ratio': float(sharpe),
            'max_drawdown_pct': max_drawdown_pct,
            'total_trades': float(n_trades),
            'win_rate_pct': win_rate_pct,
            'profit_factor': profit_factor,
            'avg_return_per_trade_pct': avg_return_per_trade_pct,
            'total_fees_paid': float(total_fees)
        }
