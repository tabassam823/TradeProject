"""
Forward Testing & Live Trading Engine for 5-Minute Solana Futures Scalping.
Integrates live market feeds, LightGBM inference, dynamic risk execution state machine,
and authenticated Binance Futures Testnet order execution.
"""
import os
import sys
import json
import time
import argparse
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add package root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crypto_futures_scalping.config import (
    DATA_DIR, OUTPUT_DIR, LGBM_PARAMS, LOOKBACK_DAYS,
    FORWARD_HORIZON_BARS, DEFAULT_FEE_RATE, DEFAULT_LEVERAGE, RISK_BUDGET_PCT
)
from crypto_futures_scalping.data_loader import load_scalping_market_data, fetch_5m_ohlcv
from crypto_futures_scalping.features import build_scalping_features, inject_cross_asset_lead_lag
from crypto_futures_scalping.binance_client import BinanceTestnetClient, load_env_file

STATE_FILE = OUTPUT_DIR / "forward_test_state.json"
TRADES_FILE = OUTPUT_DIR / "forward_test_trades.csv"
METRICS_FILE = OUTPUT_DIR / "scalping_metrics_summary.json"

# Load environment variables
load_env_file(PROJECT_ROOT / ".env")
load_env_file(CURRENT_DIR / ".env")

class ScalpingForwardTestEngine:
    def __init__(self, initial_capital: float = 1000.0, use_testnet_api: bool = False):
        self.state_file = STATE_FILE
        self.trades_file = TRADES_FILE
        self.load_optimal_config()
        self.load_or_init_state(initial_capital)
        self.model = None
        self.feature_cols = None
        
        # Binance Testnet Client Integration
        env_testnet = os.getenv("USE_BINANCE_TESTNET", "false").lower() in ("true", "1", "yes")
        self.use_testnet_api = use_testnet_api or env_testnet
        self.client = None
        
        if self.use_testnet_api:
            print("[ENGINE] Live Binance Testnet Mode ENABLED.")
            symbol = os.getenv("TRADING_SYMBOL", "SOLUSDT")
            leverage = int(os.getenv("LEVERAGE", str(int(self.config.get('leverage', DEFAULT_LEVERAGE)))))
            self.client = BinanceTestnetClient(symbol=symbol, leverage=leverage)
            if self.client.is_connected:
                live_balance = self.client.get_usdt_balance()
                if live_balance > 0:
                    self.state['capital'] = live_balance
                    self.save_state()
                    print(f"[ENGINE] Synchronized capital with Binance Testnet Wallet: ${live_balance:,.2f} USDT")
                
                # Check active testnet position
                pos = self.client.get_current_position()
                if pos['side'] != 'FLAT':
                    print(f"[ENGINE] Detected Active Testnet Position: {pos['side']} {pos['contracts']} SOL @ ${pos['entryPrice']:.2f}")
            else:
                print("[ENGINE WARNING] Could not connect to Binance Testnet API. Falling back to local paper simulation.")
                self.use_testnet_api = False
        else:
            print("[ENGINE] Local Paper Trading Mode (Simulated Execution).")

    def load_optimal_config(self):
        """Loads optimal parameters discovered by self-improvement engine."""
        if METRICS_FILE.exists():
            with open(METRICS_FILE, 'r') as f:
                data = json.load(f)
                self.config = data.get('best_hyperparameters', {})
                print(f"[CONFIG] Loaded optimized hyperparameters from {METRICS_FILE.name}")
        else:
            self.config = {
                'entry_z': 2.0,
                'exit_z': 0.0,
                'min_hold_bars': 6,
                'max_hold_bars': 24,
                'sl_atr_mult': 1.0,
                'tp_atr_mult': None,
                'trail_act_atr': 1.2,
                'trail_dist_atr': 0.8,
                'smooth_span': 3,
                'z_window': 288,
                'use_trend_filter': False,
                'use_vol_filter': False,
                'allow_short': False,
                'fee_rate': DEFAULT_FEE_RATE,
                'leverage': DEFAULT_LEVERAGE,
                'risk_pct': RISK_BUDGET_PCT
            }
            print("[CONFIG] Using default high-Sharpe scalper configuration.")

    def load_or_init_state(self, initial_capital: float):
        """Loads state or initializes fresh tracking dictionary."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
            print(f"[STATE] Loaded existing state (Equity: ${self.state['capital']:,.2f})")
        else:
            self.state = {
                'capital': initial_capital,
                'curr_pos': 0.0, # 1.0 for Long, -1.0 for Short, 0.0 for Flat
                'curr_units': 0.0,
                'entry_price': 0.0,
                'sl_price': 0.0,
                'tp_price': 0.0,
                'highest_price': 0.0,
                'lowest_price': 1e9,
                'holding_bars': 0,
                'consecutive_losses': 0,
                'cooldown_remaining': 0,
                'total_trades': 0,
                'total_fees_paid': 0.0,
                'last_update': datetime.now(timezone.utc).isoformat()
            }
            self.save_state()
            print(f"[STATE] Initialized state with ${initial_capital:,.2f}")

    def save_state(self):
        """Persists current state to JSON."""
        self.state['last_update'] = datetime.now(timezone.utc).isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=4)

    def train_latest_model(self):
        """Trains LightGBM model on the most recent 14-day 5m data."""
        print("[MODEL] Retraining LightGBM on latest 5m market features...")
        sol_raw, btc_raw = load_scalping_market_data(days=LOOKBACK_DAYS)
        sol_feat = build_scalping_features(sol_raw, horizon=FORWARD_HORIZON_BARS)
        sol_aligned, feature_cols = inject_cross_asset_lead_lag(sol_feat, btc_raw, horizon=FORWARD_HORIZON_BARS)
        
        self.feature_cols = feature_cols
        
        # Use last 14 days (4032 bars) for training
        train_window = 4032
        target_col = f'target_return_{FORWARD_HORIZON_BARS}bar'
        train_df = sol_aligned.iloc[-train_window - FORWARD_HORIZON_BARS : -FORWARD_HORIZON_BARS]
        
        X_train = train_df[feature_cols]
        y_train = train_df[target_col]
        
        import lightgbm as lgb
        self.model = lgb.LGBMRegressor(**LGBM_PARAMS)
        self.model.fit(X_train, y_train)
        
        # Calculate recent predictions to warm up rolling Z-Score
        recent_preds = self.model.predict(sol_aligned.iloc[-600:][feature_cols])
        pred_series = pd.Series(recent_preds, index=sol_aligned.iloc[-600:].index)
        smooth_pred = pred_series.ewm(span=self.config.get('smooth_span', 3), adjust=False).mean()
        roll_mean = smooth_pred.rolling(self.config.get('z_window', 288), min_periods=36).mean()
        roll_std = smooth_pred.rolling(self.config.get('z_window', 288), min_periods=36).std() + 1e-9
        self.last_z = float(((smooth_pred - roll_mean) / roll_std).iloc[-1])
        
        last_row = sol_aligned.iloc[-1]
        self.latest_close = float(last_row['close'])
        self.latest_atr = float(last_row['atr_14'])
        self.latest_sma = float(last_row['sma_200'])
        self.latest_vol_ratio = float(last_row.get('vol_ratio', 1.0))
        
        print(f"[MODEL OK] 5m Model Ready | Latest SOL: ${self.latest_close:.2f} | ATR: ${self.latest_atr:.2f} | Signal Z: {self.last_z:+.2f}")

    def evaluate_tick(self, live_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Executes one evaluation step of the live scalping risk state machine.
        """
        if self.model is None:
            self.train_latest_model()
            
        current_price = live_price if live_price is not None else self.latest_close
        atr = self.latest_atr
        sma = self.latest_sma
        z = self.last_z
        vol_ratio = self.latest_vol_ratio
        
        curr_pos = self.state['curr_pos']
        curr_units = self.state['curr_units']
        entry_price = self.state['entry_price']
        sl_price = self.state['sl_price']
        tp_price = self.state['tp_price']
        highest_price = self.state['highest_price']
        lowest_price = self.state['lowest_price']
        holding_bars = self.state['holding_bars']
        cooldown_remaining = self.state['cooldown_remaining']
        
        # Cooldown timer decrement
        if cooldown_remaining > 0:
            cooldown_remaining -= 1
            self.state['cooldown_remaining'] = cooldown_remaining
            in_cooldown = True
        else:
            in_cooldown = False
            
        action = 'HOLD'
        action_reason = None
        
        # 1. Evaluate Active Position Exit
        if curr_pos != 0.0:
            holding_bars += 1
            self.state['holding_bars'] = holding_bars
            exit_trade = False
            exit_reason = None
            
            trail_act_atr = self.config.get('trail_act_atr')
            trail_dist_atr = self.config.get('trail_dist_atr')
            tp_atr_mult = self.config.get('tp_atr_mult')
            min_hold_bars = self.config.get('min_hold_bars', 6)
            max_hold_bars = self.config.get('max_hold_bars', 24)
            entry_z = self.config.get('entry_z', 2.0)
            exit_z = self.config.get('exit_z', 0.0)
            
            if curr_pos == 1.0: # LONG
                highest_price = max(highest_price, current_price)
                self.state['highest_price'] = highest_price
                
                # Trailing Stop Calculation
                if trail_act_atr is not None and (highest_price - entry_price) >= trail_act_atr * atr:
                    trail_sl = highest_price - trail_dist_atr * atr
                    if trail_sl > sl_price:
                        sl_price = trail_sl
                        self.state['sl_price'] = sl_price
                        print(f"[TRAILING STOP UPDATED] New SL locked at: ${sl_price:,.2f}")
                        if self.use_testnet_api and self.client and self.client.is_connected:
                            self.client.update_stop_loss('LONG', sl_price)
                    
                if current_price <= sl_price:
                    exit_trade = True
                    exit_reason = 'STOP_LOSS'
                elif tp_atr_mult is not None and current_price >= tp_price:
                    exit_trade = True
                    exit_reason = 'TAKE_PROFIT'
                elif max_hold_bars is not None and holding_bars >= max_hold_bars:
                    exit_trade = True
                    exit_reason = 'TIME_STOP'
                elif holding_bars >= min_hold_bars:
                    if self.config.get('allow_short', False) and (z < -entry_z):
                        exit_trade = True
                        exit_reason = 'SIGNAL_REVERSAL'
                    elif z < exit_z:
                        exit_trade = True
                        exit_reason = 'SIGNAL_EXIT'
                        
            elif curr_pos == -1.0: # SHORT
                lowest_price = min(lowest_price, current_price)
                self.state['lowest_price'] = lowest_price
                
                if trail_act_atr is not None and (entry_price - lowest_price) >= trail_act_atr * atr:
                    trail_sl = lowest_price + trail_dist_atr * atr
                    if trail_sl < sl_price:
                        sl_price = trail_sl
                        self.state['sl_price'] = sl_price
                        print(f"[TRAILING STOP UPDATED] New SL locked at: ${sl_price:,.2f}")
                        if self.use_testnet_api and self.client and self.client.is_connected:
                            self.client.update_stop_loss('SHORT', sl_price)
                    
                if current_price >= sl_price:
                    exit_trade = True
                    exit_reason = 'STOP_LOSS'
                elif tp_atr_mult is not None and current_price <= tp_price:
                    exit_trade = True
                    exit_reason = 'TAKE_PROFIT'
                elif max_hold_bars is not None and holding_bars >= max_hold_bars:
                    exit_trade = True
                    exit_reason = 'TIME_STOP'
                elif holding_bars >= min_hold_bars:
                    if z > entry_z:
                        exit_trade = True
                        exit_reason = 'SIGNAL_REVERSAL'
                    elif z > -exit_z:
                        exit_trade = True
                        exit_reason = 'SIGNAL_EXIT'
                        
            if exit_trade:
                action = f'CLOSE_{"LONG" if curr_pos == 1.0 else "SHORT"}'
                action_reason = exit_reason
                
                # Execute Testnet Order if enabled
                if self.use_testnet_api and self.client and self.client.is_connected:
                    side_str = 'LONG' if curr_pos == 1.0 else 'SHORT'
                    self.client.close_position(side_str, curr_units)
                    
                trade_notional = curr_units * current_price
                fee = trade_notional * self.config.get('fee_rate', DEFAULT_FEE_RATE)
                
                if curr_pos == 1.0:
                    gross_pnl = curr_units * (current_price - entry_price)
                else:
                    gross_pnl = curr_units * (entry_price - current_price)
                    
                net_pnl = gross_pnl - fee
                self.state['capital'] += net_pnl
                self.state['total_fees_paid'] += fee
                self.state['total_trades'] += 1
                
                # Record Trade Log
                log_entry = {
                    'exit_time': datetime.now(timezone.utc).isoformat(),
                    'side': 'LONG' if curr_pos == 1.0 else 'SHORT',
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'units': curr_units,
                    'holding_bars': holding_bars,
                    'gross_pnl': gross_pnl,
                    'fee': fee,
                    'net_pnl': net_pnl,
                    'pnl_pct': (net_pnl / (curr_units * entry_price + 1e-9)) * 100.0,
                    'exit_reason': exit_reason,
                    'equity_after': self.state['capital']
                }
                
                # Append to CSV
                trades_df = pd.DataFrame([log_entry])
                if self.trades_file.exists():
                    trades_df.to_csv(self.trades_file, mode='a', header=False, index=False)
                else:
                    trades_df.to_csv(self.trades_file, mode='w', header=True, index=False)
                    
                # Loss streak & cooldown
                if net_pnl < 0:
                    self.state['consecutive_losses'] += 1
                    if self.state['consecutive_losses'] >= self.config.get('max_lose_streak', 3):
                        self.state['cooldown_remaining'] = self.config.get('cooldown_bars', 24)
                else:
                    self.state['consecutive_losses'] = 0
                    
                # Reset Position
                self.state['curr_pos'] = 0.0
                self.state['curr_units'] = 0.0
                self.state['entry_price'] = 0.0
                self.state['sl_price'] = 0.0
                self.state['tp_price'] = 0.0
                self.state['holding_bars'] = 0
                self.save_state()
                
                print(f"[TRADE CLOSED] {action} at ${current_price:.2f} ({exit_reason}) | Net PnL: ${net_pnl:+.2f} | Wallet: ${self.state['capital']:,.2f}")
                
        # 2. Evaluate New Position Entries (if Flat)
        elif self.state['curr_pos'] == 0.0 and not in_cooldown:
            entry_z = self.config.get('entry_z', 2.0)
            allow_short = self.config.get('allow_short', False)
            use_trend = self.config.get('use_trend_filter', False)
            use_vol = self.config.get('use_vol_filter', False)
            
            long_cond = (z > entry_z)
            short_cond = (z < -entry_z) if allow_short else False
            
            if use_trend:
                long_cond = long_cond and (current_price > sma)
                short_cond = short_cond and (current_price < sma)
                
            if use_vol:
                long_cond = long_cond and (vol_ratio >= 1.0)
                short_cond = short_cond and (vol_ratio >= 1.0)
                
            if long_cond or short_cond:
                side = 1.0 if long_cond else -1.0
                action = f'OPEN_{"LONG" if side == 1.0 else "SHORT"}'
                action_reason = f'Conviction Z ({z:+.2f}) > {entry_z}'
                
                # Volatility Stop Loss & Sizing
                sl_atr_mult = self.config.get('sl_atr_mult', 1.0)
                tp_atr_mult = self.config.get('tp_atr_mult')
                sl_dist = max(sl_atr_mult * atr, current_price * 0.003)
                
                if side == 1.0:
                    sl_price = current_price - sl_dist
                    tp_price = current_price + (tp_atr_mult * atr) if tp_atr_mult else 0.0
                else:
                    sl_price = current_price + sl_dist
                    tp_price = current_price - (tp_atr_mult * atr) if tp_atr_mult else 0.0
                    
                risk_pct = self.config.get('risk_pct', RISK_BUDGET_PCT)
                leverage = self.config.get('leverage', DEFAULT_LEVERAGE)
                capital = self.state['capital']
                
                risk_amount = capital * risk_pct
                sl_pct = sl_dist / current_price
                target_notional = risk_amount / (sl_pct + 1e-9)
                max_notional = capital * leverage
                actual_notional = min(target_notional, max_notional)
                units = actual_notional / current_price
                
                # Execute live testnet bracket order (Market Entry + On-Exchange TP + On-Exchange SL)
                if self.use_testnet_api and self.client and self.client.is_connected:
                    order_side = 'BUY' if side == 1.0 else 'SELL'
                    self.client.place_bracket_order(order_side, units, tp_price=tp_price, sl_price=sl_price)
                    
                fee = actual_notional * self.config.get('fee_rate', DEFAULT_FEE_RATE)
                self.state['capital'] -= fee
                self.state['total_fees_paid'] += fee
                
                self.state['curr_pos'] = side
                self.state['curr_units'] = units
                self.state['entry_price'] = current_price
                self.state['sl_price'] = sl_price
                self.state['tp_price'] = tp_price
                self.state['highest_price'] = current_price
                self.state['lowest_price'] = current_price
                self.state['holding_bars'] = 0
                self.save_state()
                
                print(f"[TRADE OPENED] {action} {units:.2f} SOL @ ${current_price:.2f} | SL: ${sl_price:.2f} | TP: ${tp_price:.2f} | Risk: ${risk_amount:.2f}")
                
        # Mark to market equity
        curr_pos = self.state['curr_pos']
        units = self.state['curr_units']
        entry = self.state['entry_price']
        if curr_pos == 1.0:
            unrealized = units * (current_price - entry)
        elif curr_pos == -1.0:
            unrealized = units * (entry - current_price)
        else:
            unrealized = 0.0
            
        equity = self.state['capital'] + unrealized
        
        status_info = {
            'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
            'price': current_price,
            'signal_z': z,
            'threshold_z': self.config.get('entry_z', 2.0),
            'action': action,
            'reason': action_reason,
            'position': 'LONG' if curr_pos == 1.0 else ('SHORT' if curr_pos == -1.0 else 'FLAT'),
            'units': units,
            'entry_price': entry,
            'sl_price': self.state['sl_price'],
            'unrealized_pnl': unrealized,
            'equity': equity,
            'wallet_capital': self.state['capital'],
            'total_trades': self.state['total_trades'],
            'holding_bars': self.state['holding_bars'],
            'cooldown_remaining': self.state['cooldown_remaining'],
            'testnet_mode': self.use_testnet_api
        }
        return status_info

def run_cli():
    parser = argparse.ArgumentParser(description="Forward Testing & Live Execution Engine for 5m Futures Scalping.")
    parser.add_argument("--mode", choices=["once", "loop", "daemon"], default="once", help="Execution mode")
    parser.add_argument("--interval", type=int, default=60, help="Polling interval in seconds for loop mode")
    parser.add_argument("--testnet", action="store_true", help="Force Binance Testnet API execution")
    parser.add_argument("--capital", type=float, default=1000.0, help="Initial paper capital")
    args = parser.parse_args()
    
    engine = ScalpingForwardTestEngine(initial_capital=args.capital, use_testnet_api=args.testnet)
    
    if args.mode == "once":
        # Fetch live ticker price if connected to testnet
        live_price = None
        if engine.client and engine.client.is_connected:
            p = engine.client.get_ticker_price()
            if p > 0:
                live_price = p
                print(f"[LIVE TESTNET PRICE] SOLUSDT = ${live_price:.2f}")
                
        status = engine.evaluate_tick(live_price=live_price)
        print("\n" + "=" * 70)
        print("⚡ SCALPING FORWARD TEST STATUS (5M TICK EVALUATION)")
        print("=" * 70)
        for k, v in status.items():
            if isinstance(v, float):
                print(f"  {k:<20}: {v:,.2f}")
            else:
                print(f"  {k:<20}: {v}")
        print("=" * 70)
        
    elif args.mode in ("loop", "daemon"):
        print(f"\n[DAEMON] Starting Scalping Live Forward Test Loop (Interval: {args.interval}s)...")
        print("Press Ctrl+C to terminate.")
        try:
            while True:
                live_price = None
                if engine.client and engine.client.is_connected:
                    p = engine.client.get_ticker_price()
                    if p > 0:
                        live_price = p
                status = engine.evaluate_tick(live_price=live_price)
                print(
                    f"[{status['timestamp']}] Price: ${status['price']:.2f} | "
                    f"Z-Score: {status['signal_z']:+.2f} | Pos: {status['position']} | "
                    f"Equity: ${status['equity']:,.2f} | Action: {status['action']}"
                )
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[DAEMON] Forward test loop stopped by user.")

if __name__ == '__main__':
    run_cli()
