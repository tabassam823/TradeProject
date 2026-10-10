"""
Forward Testing & Live Trading Engine for SOL-USD.
Connects real-time Binance public market data, trained LightGBM models,
dynamic risk management state machine, and optional Binance Futures Testnet API execution.
"""
import os
import sys
import json
import time
import argparse
import asyncio
import aiohttp
import websockets
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add package root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crypto_ml_trading.config import (
    DATA_DIR, OUTPUT_DIR, LGBM_PARAMS, LOOKBACK_DAYS
)
from crypto_ml_trading.data_loader import load_all_market_data, fetch_yfinance_ohlcv
from crypto_ml_trading.features import build_asset_features, inject_cross_asset_features
from crypto_ml_trading.binance_client import BinanceTestnetClient, load_env_file

STATE_FILE = OUTPUT_DIR / "forward_test_state.json"
TRADES_FILE = OUTPUT_DIR / "forward_test_trades.csv"
METRICS_FILE = OUTPUT_DIR / "metrics_summary.json"

# Load environment variables from .env
load_env_file(PROJECT_ROOT / ".env")
load_env_file(CURRENT_DIR / ".env")

class ForwardTestEngine:
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
            symbol = os.getenv("TRADING_SYMBOL", "SOL/USDT:USDT")
            leverage = int(os.getenv("LEVERAGE", "2"))
            self.client = BinanceTestnetClient(symbol=symbol, leverage=leverage)
            if self.client.is_connected:
                live_balance = self.client.get_usdt_balance()
                if live_balance > 0:
                    self.state['capital'] = live_balance
                    self.save_state()
                    print(f"[ENGINE] Synchronized capital with Binance Testnet Wallet: ${live_balance:,.2f}")
            else:
                print("[ENGINE WARNING] Could not connect to Binance Testnet API. Falling back to local paper simulation.")
                self.use_testnet_api = False
        else:
            print("[ENGINE] Local Paper Trading Mode (Simulated Execution).")
        
    def load_optimal_config(self):
        """Load best hyperparameters from metrics_summary.json if available."""
        if METRICS_FILE.exists():
            with open(METRICS_FILE, 'r') as f:
                data = json.load(f)
                self.config = data.get('best_hyperparameters', {})
                print(f"[CONFIG] Loaded optimized hyperparameters from {METRICS_FILE.name}")
        else:
            self.config = {
                'entry_z': 1.0,
                'exit_z': 0.0,
                'min_hold_hours': 24,
                'sl_atr_mult': 1.5,
                'tp_atr_mult': None,
                'trail_act_atr': 1.5,
                'trail_dist_atr': 1.0,
                'smooth_span': 4,
                'z_window': 168,
                'use_sma_filter': True,
                'allow_short': True,
                'fee_rate': 0.00075,
                'risk_pct': 0.02,
                'max_leverage': 2.0
            }
            print("[CONFIG] Using default high-Sharpe configuration.")

    def load_or_init_state(self, initial_capital: float):
        """Loads paper trading state or initializes a new account."""
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
                'holding_hours': 0,
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
        """Trains LightGBM model on the most recent 60-day window."""
        print("[MODEL] Retraining LightGBM on latest market features...")
        btc_raw, sol_raw, fng_raw, news_raw = load_all_market_data(days=LOOKBACK_DAYS)
        feat_btc = build_asset_features(btc_raw, fng_raw, news_raw, horizon=1)
        feat_sol = build_asset_features(sol_raw, fng_raw, news_raw, horizon=1)
        feat_sol_aligned, feature_cols = inject_cross_asset_features(feat_sol, feat_btc)
        
        self.feature_cols = feature_cols
        
        train_window = 1440 # 60 days
        train_df = feat_sol_aligned.iloc[-train_window:-1] # 1 bar purge
        X_train = train_df[feature_cols]
        y_train = train_df['target_return_1h']
        
        import lightgbm as lgb
        self.model = lgb.LGBMRegressor(**LGBM_PARAMS)
        self.model.fit(X_train, y_train)
        
        # Calculate recent historical predictions to warm up rolling Z-score
        recent_preds = self.model.predict(feat_sol_aligned.iloc[-300:][feature_cols])
        pred_series = pd.Series(recent_preds, index=feat_sol_aligned.iloc[-300:].index)
        smooth_pred = pred_series.ewm(span=self.config.get('smooth_span', 4), adjust=False).mean()
        roll_mean = smooth_pred.rolling(self.config.get('z_window', 168), min_periods=24).mean()
        roll_std = smooth_pred.rolling(self.config.get('z_window', 168), min_periods=24).std() + 1e-9
        self.last_z = float(((smooth_pred - roll_mean) / roll_std).iloc[-1])
        
        last_row = feat_sol_aligned.iloc[-1]
        self.latest_close = float(last_row['close'])
        self.latest_atr = float(last_row['atr_14'])
        self.latest_sma = float(last_row['sma_200'])
        
        print(f"[MODEL] Model ready. Latest Close: ${self.latest_close:.2f} | Current Z-Score: {self.last_z:+.3f}")

    def evaluate_step(self, current_price: float = None):
        """
        Executes one forward-test evaluation cycle against current market state.
        """
        self.train_latest_model()
            
        if current_price is None and self.client and self.client.is_connected:
            try:
                ticker = self.client.client.futures_symbol_ticker(symbol=self.client.symbol)
                current_price = float(ticker['price'])
            except Exception:
                current_price = self.latest_close
        elif current_price is None:
            current_price = self.latest_close
            
        atr = self.latest_atr
        sma = self.latest_sma
        z = self.last_z
        cfg = self.config
        fee_rate = cfg.get('fee_rate', 0.00075)
        
        curr_pos = self.state['curr_pos']
        curr_units = self.state['curr_units']
        entry_price = self.state['entry_price']
        sl_price = self.state['sl_price']
        tp_price = self.state['tp_price']
        capital = self.state['capital']
        holding_bars = self.state['holding_hours']
        
        print("\n" + "=" * 65)
        print(f"📡 FORWARD TEST CYCLE: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        mode_str = "BINANCE TESTNET API (LIVE)" if (self.use_testnet_api and self.client and self.client.is_connected) else "LOCAL PAPER SIMULATION"
        print(f"Mode Execution   : {mode_str}")
        print("=" * 65)
        print(f"SOL Market Price : ${current_price:,.2f}")
        print(f"Model Signal Z   : {z:+.3f} (Entry Threshold: ±{cfg['entry_z']:.2f})")
        print(f"Macro Trend (SMA): ${sma:,.2f} -> {'BULLISH' if current_price > sma else 'BEARISH'}")
        print(f"Volatility (ATR) : ${atr:,.2f}")
        
        # 1. Evaluate Exit if In Position
        if curr_pos != 0.0:
            holding_bars += 1
            self.state['holding_hours'] = holding_bars
            exit_trade = False
            exit_reason = None
            exit_exec_price = current_price
            
            if curr_pos == 1.0: # Long
                self.state['highest_price'] = max(self.state['highest_price'], current_price)
                if cfg.get('trail_act_atr') and (self.state['highest_price'] - entry_price) >= cfg['trail_act_atr'] * atr:
                    new_sl = self.state['highest_price'] - cfg['trail_dist_atr'] * atr
                    if new_sl > sl_price:
                        sl_price = new_sl
                        self.state['sl_price'] = sl_price
                        print(f"[TRAILING STOP UPDATED] New SL locked at: ${sl_price:,.2f}")
                        if self.use_testnet_api and self.client and self.client.is_connected:
                            self.client.update_stop_loss('LONG', sl_price)
                        
                if current_price <= sl_price:
                    exit_trade = True
                    exit_reason = 'STOP_LOSS'
                    exit_exec_price = sl_price
                elif holding_bars >= cfg['min_hold_hours']:
                    if cfg['allow_short'] and (z < -cfg['entry_z']):
                        exit_trade = True
                        exit_reason = 'SIGNAL_REVERSAL'
                    elif z < cfg['exit_z']:
                        exit_trade = True
                        exit_reason = 'SIGNAL_EXIT'
                        
            elif curr_pos == -1.0: # Short
                self.state['lowest_price'] = min(self.state['lowest_price'], current_price)
                if cfg.get('trail_act_atr') and (entry_price - self.state['lowest_price']) >= cfg['trail_act_atr'] * atr:
                    new_sl = self.state['lowest_price'] + cfg['trail_dist_atr'] * atr
                    if new_sl < sl_price:
                        sl_price = new_sl
                        self.state['sl_price'] = sl_price
                        print(f"[TRAILING STOP UPDATED] New SL locked at: ${sl_price:,.2f}")
                        if self.use_testnet_api and self.client and self.client.is_connected:
                            self.client.update_stop_loss('SHORT', sl_price)
                        
                if current_price >= sl_price:
                    exit_trade = True
                    exit_reason = 'STOP_LOSS'
                    exit_exec_price = sl_price
                elif holding_bars >= cfg['min_hold_hours']:
                    if z > cfg['entry_z']:
                        exit_trade = True
                        exit_reason = 'SIGNAL_REVERSAL'
                    elif z > -cfg['exit_z']:
                        exit_trade = True
                        exit_reason = 'SIGNAL_EXIT'
                        
            if exit_trade:
                gross_pnl = (exit_exec_price - entry_price) * curr_units * curr_pos
                exit_fee = exit_exec_price * curr_units * fee_rate
                net_pnl = gross_pnl - exit_fee
                capital += net_pnl
                self.state['capital'] = capital
                self.state['total_fees_paid'] += exit_fee
                self.state['total_trades'] += 1
                
                print(f"🚨 [TRADE CLOSED] {exit_reason} at ${exit_exec_price:,.2f}")
                print(f"   Gross PnL: ${gross_pnl:+.2f} | Fee: ${exit_fee:.2f} | Net PnL: ${net_pnl:+.2f}")
                
                # Close live position on Binance Testnet if connected
                if self.use_testnet_api and self.client and self.client.is_connected:
                    side_str = 'LONG' if curr_pos == 1.0 else 'SHORT'
                    self.client.close_position(side_str, curr_units)
                    
                self._log_trade({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'side': 'LONG' if curr_pos == 1.0 else 'SHORT',
                    'entry_price': entry_price,
                    'exit_price': exit_exec_price,
                    'units': curr_units,
                    'net_pnl': net_pnl,
                    'reason': exit_reason,
                    'holding_hours': holding_bars
                })
                
                self.state['curr_pos'] = 0.0
                self.state['curr_units'] = 0.0
                self.state['holding_hours'] = 0
                curr_pos = 0.0
                
        # 2. Evaluate Entry if Flat
        if curr_pos == 0.0:
            risk_dollar = max(1.0, cfg['risk_pct'] * capital)
            sl_dist = max(cfg['sl_atr_mult'] * atr, current_price * 0.005)
            max_units = (capital * cfg['max_leverage']) / current_price
            target_units = min(risk_dollar / sl_dist, max_units)
            
            sma_long_ok = (current_price > sma) if cfg['use_sma_filter'] else True
            sma_short_ok = (current_price < sma) if cfg['use_sma_filter'] else True
            
            if z > cfg['entry_z'] and sma_long_ok:
                curr_pos = 1.0
                curr_units = target_units
                entry_price = current_price
                sl_price = entry_price - sl_dist
                tp_price = entry_price + (cfg['tp_atr_mult'] * atr) if cfg.get('tp_atr_mult') else 0.0
                highest_price = entry_price
                entry_fee = entry_price * curr_units * fee_rate
                capital -= entry_fee
                
                self.state['curr_pos'] = 1.0
                self.state['curr_units'] = curr_units
                self.state['entry_price'] = entry_price
                self.state['sl_price'] = sl_price
                self.state['tp_price'] = tp_price
                self.state['highest_price'] = entry_price
                self.state['capital'] = capital
                self.state['total_fees_paid'] += entry_fee
                self.state['holding_hours'] = 0
                
                print(f"🟢 [NEW ORDER] LONG ENTERED at ${entry_price:,.2f}")
                print(f"   Units: {curr_units:.4f} | Size: ${entry_price * curr_units:,.2f} | SL: ${sl_price:,.2f} | TP: ${tp_price:,.2f} | Fee: ${entry_fee:.2f}")
                
                # Execute live testnet bracket order (Market + TP + SL on-exchange)
                if self.use_testnet_api and self.client and self.client.is_connected:
                    self.client.place_bracket_order('BUY', curr_units, tp_price=tp_price, sl_price=sl_price)
                
            elif cfg['allow_short'] and z < -cfg['entry_z'] and sma_short_ok:
                curr_pos = -1.0
                curr_units = target_units
                entry_price = current_price
                sl_price = entry_price + sl_dist
                tp_price = entry_price - (cfg['tp_atr_mult'] * atr) if cfg.get('tp_atr_mult') else 0.0
                lowest_price = entry_price
                entry_fee = entry_price * curr_units * fee_rate
                capital -= entry_fee
                
                self.state['curr_pos'] = -1.0
                self.state['curr_units'] = curr_units
                self.state['entry_price'] = entry_price
                self.state['sl_price'] = sl_price
                self.state['tp_price'] = tp_price
                self.state['lowest_price'] = entry_price
                self.state['capital'] = capital
                self.state['total_fees_paid'] += entry_fee
                self.state['holding_hours'] = 0
                
                print(f"🔴 [NEW ORDER] SHORT ENTERED at ${entry_price:,.2f}")
                print(f"   Units: {curr_units:.4f} | Size: ${entry_price * curr_units:,.2f} | SL: ${sl_price:,.2f} | TP: ${tp_price:,.2f} | Fee: ${entry_fee:.2f}")
                
                # Execute live testnet bracket order (Market + TP + SL on-exchange)
                if self.use_testnet_api and self.client and self.client.is_connected:
                    self.client.place_bracket_order('SELL', curr_units, tp_price=tp_price, sl_price=sl_price)
            else:
                print(f"⚪ [POSITION FLAT] No trigger. Waiting for high-conviction Z-signal.")
                
        # 3. Print Portfolio State
        unrealized = (current_price - self.state['entry_price']) * self.state['curr_units'] * self.state['curr_pos'] if self.state['curr_pos'] != 0 else 0.0
        equity = self.state['capital'] + unrealized
        
        pos_label = "FLAT"
        if self.state['curr_pos'] == 1.0:
            pos_label = f"LONG ({self.state['curr_units']:.4f} SOL @ ${self.state['entry_price']:,.2f} | Unrealized: ${unrealized:+.2f})"
        elif self.state['curr_pos'] == -1.0:
            pos_label = f"SHORT ({self.state['curr_units']:.4f} SOL @ ${self.state['entry_price']:,.2f} | Unrealized: ${unrealized:+.2f})"
            
        print("-" * 65)
        print(f"Current Position : {pos_label}")
        print(f"Cash Balance     : ${self.state['capital']:,.2f}")
        print(f"Total Equity     : ${equity:,.2f}")
        print(f"Total Trades     : {self.state['total_trades']} closed trades")
        print("=" * 65)
        
        self.save_state()

    def _log_trade(self, record: dict):
        df_new = pd.DataFrame([record])
        if self.trades_file.exists():
            df_new.to_csv(self.trades_file, mode='a', header=False, index=False)
        else:
            df_new.to_csv(self.trades_file, index=False)

def run_continuous_loop(engine: ForwardTestEngine):
    """
    Runs the forward test engine indefinitely, evaluating exactly on every hourly candle close.
    """
    print("\n" + "=" * 65)
    print("🔄 STARTING CONTINUOUS HOURLY FORWARD TEST DAEMON")
    print("=" * 65)
    print("Press Ctrl+C to terminate cleanly at any time.\n")
    
    while True:
        try:
            # 1. Run evaluation cycle
            engine.evaluate_step()
            
            # 2. Calculate sleep time until next hour (:01 minute past the hour)
            now = datetime.now(timezone.utc)
            next_hour = (now + timedelta(hours=1)).replace(minute=1, second=0, microsecond=0)
            sleep_seconds = max(10, int((next_hour - now).total_seconds()))
            
            print(f"\n💤 Sleeping {sleep_seconds // 60}m {sleep_seconds % 60}s until next candle close ({next_hour.strftime('%H:%M:%S UTC')})...\n")
            time.sleep(sleep_seconds)
            
        except KeyboardInterrupt:
            print("\n[STOPPED] Continuous daemon safely halted by user.")
            break
        except Exception as e:
            print(f"\n[LOOP ERROR] Error in evaluation loop: {e}. Retrying in 60s...")
            time.sleep(60)

async def stream_live_market(engine: ForwardTestEngine, duration_seconds: int = 30):
    """
    Connects to Binance Public Futures WebSocket and monitors live ticks.
    """
    ws_url = "wss://stream.binancefuture.com/stream?streams=solusdt@ticker/btcusdt@ticker"
    print(f"\n[STREAM] Connecting to Binance Live Futures WebSocket for {duration_seconds}s...")
    
    start_time = time.time()
    try:
        async with websockets.connect(ws_url, open_timeout=10) as ws:
            while time.time() - start_time < duration_seconds:
                msg = await ws.recv()
                data = json.loads(msg).get('data', {})
                symbol = data.get('s')
                price = float(data.get('c', 0.0))
                change = float(data.get('P', 0.0))
                ts = datetime.now(timezone.utc).strftime('%H:%M:%S')
                print(f"  ⚡ [{ts} UTC] {symbol:<8} | Live Price: ${price:>9.2f} | 24h: {change:>+6.2f}%")
                await asyncio.sleep(1)
    except Exception as e:
        print(f"[STREAM ERROR] {e}")

def main():
    parser = argparse.ArgumentParser(description="Forward Testing & Live Trading Engine for SOL-USD")
    parser.add_argument("--step", action="store_true", help="Execute one forward test evaluation cycle")
    parser.add_argument("--status", action="store_true", help="Display current forward test position and portfolio status")
    parser.add_argument("--stream", type=int, default=0, help="Stream live market prices via WebSocket for N seconds")
    parser.add_argument("--loop", action="store_true", help="Run continuously every hour on candle close (daemon mode)")
    parser.add_argument("--live-testnet", action="store_true", help="Force execute live orders on Binance Futures Testnet")
    args = parser.parse_args()
    
    engine = ForwardTestEngine(use_testnet_api=args.live_testnet)
    
    if args.status:
        pos = engine.state['curr_pos']
        pos_str = "FLAT"
        if pos == 1.0:
            pos_str = f"LONG ({engine.state['curr_units']:.4f} SOL @ ${engine.state['entry_price']:,.2f})"
        elif pos == -1.0:
            pos_str = f"SHORT ({engine.state['curr_units']:.4f} SOL @ ${engine.state['entry_price']:,.2f})"
        print("\n" + "=" * 55)
        print("💼 FORWARD TEST PORTFOLIO STATUS")
        print("=" * 55)
        print(f"Execution Mode     : {'BINANCE TESTNET API' if (engine.use_testnet_api and engine.client and engine.client.is_connected) else 'LOCAL PAPER TRADING'}")
        print(f"Current Position   : {pos_str}")
        print(f"Cash Capital       : ${engine.state['capital']:,.2f}")
        print(f"Holding Time       : {engine.state['holding_hours']} hours")
        print(f"Stop Loss Price    : ${engine.state['sl_price']:,.2f}")
        print(f"Total Closed Trades: {engine.state['total_trades']}")
        print(f"Total Fees Paid    : ${engine.state['total_fees_paid']:,.2f}")
        print(f"State File Path    : {STATE_FILE}")
        print("=" * 55)
        return
        
    if args.loop:
        run_continuous_loop(engine)
        return
        
    # Default is running 1 step
    engine.evaluate_step()
    
    if args.stream > 0:
        asyncio.run(stream_live_market(engine, duration_seconds=args.stream))

if __name__ == '__main__':
    main()
