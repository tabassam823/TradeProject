"""
Paper Trading Engine (Multi-Strategy 24/7 Simulator).
Includes:
- 3-Tier Market Benchmark Ingestion (Tahap 3 & Tahap A)
- Order Book & Microstructure Ingestion (OBI & Spread)
- Regime-Adaptive Position Sizing (SL widening + Lot scaling)
- Anti-Whipsaw Trade Cooldown Engine (30 mins after SL)
- Regime Hard-Gate for Trend Strategies in Volatility Crisis
- Sequential Position Lifecycle Management (BEP & Trailing TP)
"""

import json
import os
import datetime
import time
from typing import Dict, Any, List, Optional, Tuple

from src.core.binance_client import BinanceClient
from src.core.openbb_client import OpenBBClient
from src.core.benchmark_provider import BenchmarkProvider
from src.core.position_sizer import VolatilityTargetPositionSizer
from src.core.orderbook_engine import OrderBookEngine
from src.core.position_lifecycle_manager import PositionLifecycleManager
from src.core.math_engine import MathEngine, MarketRegime

from src.strategies.momentum import MultiHorizonMomentumStrategy
from src.strategies.vwap_rejection import VWAPRejectionStrategy
from src.strategies.sentiment_trend import SentimentFilteredTrendStrategy
from src.strategies.factor_regime import FactorRegimeStrategy
from src.strategies.first_passage_value import FirstPassageValueStrategy

from src.strategies.qubo_portfolio_selector import QUBOPortfolioStrategy
from src.strategies.rule_based_strategy import RuleBasedStrategy  # <-- NEW

class PaperTrader:
    """
    Asset-Agnostic Multi-Strategy Paper Trading Engine with Order Book, Anti-Whipsaw Cooldown & Regime Gate.
    """
    def __init__(self, config_path: str = "config.json", strategy_config_path: str = "strategy_config.json"):
        with open(config_path, "r") as f:
            self.config = json.load(f)
        with open(strategy_config_path, "r") as f:
            self.strategy_config = json.load(f)

        self.binance = BinanceClient(testnet=self.config.get("BINANCE_SANDBOX", True))
        self.openbb = OpenBBClient()
        
        benchmark_sym = self.strategy_config.get("benchmark", {}).get("market_symbol", "BTC/USDT")
        self.benchmark_provider = BenchmarkProvider(benchmark_symbol=benchmark_sym, testnet=self.config.get("BINANCE_SANDBOX", True))

        self.position_sizer = VolatilityTargetPositionSizer(
            max_risk_per_trade=self.config["RISK_LIMITS"]["max_risk_per_trade"]
        )
        
        self.pairs = self.config.get("TRADING_PAIRS", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
        self.timeframe = self.config.get("TIMEFRAME", "1h")
        self.initial_capital = self.config.get("INITIAL_CAPITAL", 10000.0)
        self.ledger_file = "logs/paper_ledger.json"
        
        # In-memory cooldown tracker: (strategy_name, symbol) -> expire_unix_timestamp
        self.symbol_cooldowns: Dict[Tuple[str, str], float] = {}

        # Instantiate all configured strategies
        self.strategies = []
        strat_configs = self.strategy_config.get("strategies", {})

        if strat_configs.get("momentum_multi_horizon", {}).get("enabled", True):
            self.strategies.append(MultiHorizonMomentumStrategy(config=strat_configs["momentum_multi_horizon"]))
            
        if strat_configs.get("vwap_mean_reversion", {}).get("enabled", True):
            self.strategies.append(VWAPRejectionStrategy(config=strat_configs["vwap_mean_reversion"]))
            
        if strat_configs.get("sentiment_filtered_trend", {}).get("enabled", True):
            self.strategies.append(SentimentFilteredTrendStrategy(config=strat_configs["sentiment_filtered_trend"]))

        if strat_configs.get("factor_regime_adaptive", {}).get("enabled", True):
            self.strategies.append(FactorRegimeStrategy(config=strat_configs["factor_regime_adaptive"]))


        if strat_configs.get("qubo_portfolio_selector", {}).get("enabled", True):
            self.strategies.append(QUBOPortfolioStrategy(config=strat_configs["qubo_portfolio_selector"]))


        # --- Custom no-code strategies created via the Strategy Builder web UI ---
        custom_strategies_path = "custom_strategies.json"
        if os.path.exists(custom_strategies_path):
            try:
                with open(custom_strategies_path, "r") as f:
                    custom_configs = json.load(f)
                for custom_name, custom_cfg in custom_configs.items():
                    if custom_cfg.get("enabled", True):
                        self.strategies.append(RuleBasedStrategy(name=custom_name, config=custom_cfg))
            except (json.JSONDecodeError, OSError) as e:
                print(f"[PaperTrader] Warning: failed to load custom_strategies.json: {e}")

        self.ledger = self._load_ledger()

    def _load_ledger(self) -> Dict[str, Any]:
        """Loads or initializes paper trading ledger."""
        os.makedirs("logs", exist_ok=True)
        if os.path.exists(self.ledger_file):
            try:
                with open(self.ledger_file, "r") as f:
                    data = json.load(f)
                    for strategy in self.strategies:
                        if strategy.name not in data:
                            data[strategy.name] = {
                                "capital": self.initial_capital,
                                "equity_curve": [{"timestamp": str(datetime.datetime.now()), "equity": self.initial_capital}],
                                "pending_orders": {},
                                "open_positions": {},
                                "closed_trades": [],
                                "bep_events": 0,
                                "trailing_tp_events": 0
                            }
                    return data
            except Exception as e:
                print(f"[PaperTrader] Warning loading ledger: {e}")

        initial_ledger = {}
        for strategy in self.strategies:
            initial_ledger[strategy.name] = {
                "capital": self.initial_capital,
                "equity_curve": [{"timestamp": str(datetime.datetime.now()), "equity": self.initial_capital}],
                "pending_orders": {},
                "open_positions": {},
                "closed_trades": [],
                "bep_events": 0,
                "trailing_tp_events": 0
            }
        return initial_ledger

    def _save_ledger(self, benchmark_state: Optional[Dict[str, Any]] = None):
        """Saves current paper trading ledger to file."""
        os.makedirs("logs", exist_ok=True)
        if benchmark_state:
            self.ledger["_benchmark_meta"] = benchmark_state
        with open(self.ledger_file, "w") as f:
            json.dump(self.ledger, f, indent=2)

    def run_tick(self):
        """Executes a single paper trading evaluation tick with anti-whipsaw controls."""
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        now_ts = time.time()
        print(f"\n[PAPER TRADER TICK] Executing tick at {now_str}...")

        # Ingest benchmark state
        sample_df = self.binance.fetch_ohlcv(self.pairs[0], timeframe=self.timeframe, limit=100)
        benchmark_state = self.benchmark_provider.get_market_state(
            target_symbol=self.pairs[0],
            target_df=sample_df,
            timeframe=self.timeframe
        )
        current_regime = benchmark_state.get("regime", MarketRegime.MEAN_REVERSION_CHOP.value)
        print(f"[Market State] Regime: {current_regime} | Benchmark ({benchmark_state.get('benchmark_symbol')} 24h): {benchmark_state.get('benchmark_return_24h'):+.2%}")

        for symbol in self.pairs:
            # Fetch latest candles & synthetic/real orderbook
            df = self.binance.fetch_ohlcv(symbol, timeframe=self.timeframe, limit=100)
            if df.empty or len(df) < 50:
                print(f"[PaperTrader] Skipping {symbol} (insufficient candles).")
                continue

            current_price = df['close'].iloc[-1]
            volatility = self.position_sizer.calculate_volatility(df)
            
            # Order book microstructure state
            bids = [[current_price * (1.0 - 0.0005 * i), 10.0 + 5.0 * i] for i in range(1, 11)]
            asks = [[current_price * (1.0 + 0.0005 * i), 10.0 + 5.0 * i] for i in range(1, 11)]
            obi = OrderBookEngine.calculate_order_book_imbalance(bids, asks)

            # Circuit Breaker check
            base_coin = symbol.split('/')[0]
            is_circuit_broken = self.openbb.is_circuit_breaker_triggered(base_coin)

            market_state = self.benchmark_provider.get_market_state(symbol, df, timeframe=self.timeframe)
            market_state["obi"] = obi

            for strategy in self.strategies:
                strat_name = strategy.name
                strat_ledger = self.ledger.get(strat_name, {
                    "capital": self.initial_capital,
                    "pending_orders": {},
                    "open_positions": {},
                    "closed_trades": [],
                    "equity_curve": [],
                    "bep_events": 0,
                    "trailing_tp_events": 0
                })
                
                if "pending_orders" not in strat_ledger:
                    strat_ledger["pending_orders"] = {}

                # 1. EVALUATE PENDING ORDERS (Unfilled Lifecycle - 60 ticks patience window)
                pending_order = strat_ledger["pending_orders"].get(symbol)
                try:
                    score = strategy.generate_signal(df, market_state=market_state)
                except TypeError:
                    score = strategy.generate_signal(df)

                if pending_order is not None:
                    order_status, pos_data, reason = PositionLifecycleManager.evaluate_pending_order(
                        order=pending_order,
                        current_price=current_price,
                        current_score=score,
                        max_pending_ticks=60
                    )
                    if order_status == "FILLED" and pos_data:
                        strat_ledger["open_positions"][symbol] = pos_data
                        del strat_ledger["pending_orders"][symbol]
                        print(f"  [{strat_name}] ⚡ ORDER FILLED on {symbol} @ ${pos_data['entry_price']:.2f} (Units: {pos_data['units']:.4f})")
                    elif order_status == "CANCELLED":
                        del strat_ledger["pending_orders"][symbol]
                        print(f"  [{strat_name}] ❌ PENDING ORDER CANCELLED on {symbol} ({reason})")

                # 2. EVALUATE ACTIVE POSITIONS (Filled Lifecycle: BEP, Trailing TP, SL Exit)
                active_pos = strat_ledger["open_positions"].get(symbol)
                if active_pos is not None:
                    action, updated_pos, closed_trade = PositionLifecycleManager.evaluate_active_position(
                        position=active_pos,
                        current_price=current_price
                    )

                    if action == "MOVED_BEP":
                        strat_ledger["open_positions"][symbol] = updated_pos
                        strat_ledger["bep_events"] = strat_ledger.get("bep_events", 0) + 1
                        print(f"  [{strat_name}] 🛡️ BEP ACTIVATED on {symbol}: SL moved to Break-Even (${updated_pos['current_sl_price']:.2f})")

                    elif action == "TRAILED_TP":
                        strat_ledger["open_positions"][symbol] = updated_pos
                        strat_ledger["trailing_tp_events"] = strat_ledger.get("trailing_tp_events", 0) + 1
                        print(f"  [{strat_name}] 🚀 TRAILING TP ELEVATED on {symbol}: TP elevated to ${updated_pos['current_tp_price']:.2f}")

                    elif action == "CLOSED" and closed_trade:
                        strat_ledger["capital"] += closed_trade["net_pnl"]
                        strat_ledger["closed_trades"].append(closed_trade)
                        del strat_ledger["open_positions"][symbol]
                        pnl_tag = "+PROFIT" if closed_trade["net_pnl"] > 0 else "-LOSS"
                        print(f"  [{strat_name}] 🏁 POSITION CLOSED on {symbol} @ ${closed_trade['exit_price']:.2f} | {pnl_tag} Net PnL: ${closed_trade['net_pnl']:+.2f} ({closed_trade['exit_reason']})")
                        
                        # If stopped out, trigger 30-minute anti-whipsaw cooldown on this symbol
                        if "STOP_LOSS" in closed_trade["exit_reason"]:
                            self.symbol_cooldowns[(strat_name, symbol)] = now_ts + 1800.0
                            print(f"  [{strat_name}] ⏳ COOLDOWN INITIATED on {symbol} (30 mins protection against whipsaw)")

                # 3. EVALUATE NEW ORDER PLACEMENT (Only if no open pos, no pending order, and not in cooldown)
                if symbol not in strat_ledger["open_positions"] and symbol not in strat_ledger["pending_orders"]:
                    # Check Cooldown
                    cooldown_expiry = self.symbol_cooldowns.get((strat_name, symbol), 0.0)
                    if now_ts < cooldown_expiry:
                        rem_mins = (cooldown_expiry - now_ts) / 60.0
                        continue

                    # Regime Hard-Gate: In Crisis or Chop, prevent aggressive trend following entries
                    is_trend_strat = strat_name in ["sentiment_filtered_trend", "momentum_multi_horizon"]
                    if is_trend_strat and current_regime in ["HIGH_VOLATILITY_CRISIS", "MEAN_REVERSION_CHOP"]:
                        continue

                    sizing = self.position_sizer.calculate_position_size(
                        current_price=current_price,
                        capital=strat_ledger["capital"],
                        score=score,
                        volatility=volatility,
                        risk_budget_ratio=strategy.config.get("risk_budget", 0.01),
                        is_circuit_broken=is_circuit_broken,
                        regime=current_regime
                    )

                    if sizing["direction"] != 0:
                        limit_price = OrderBookEngine.calculate_optimal_limit_price(
                            direction=sizing["direction"],
                            current_price=current_price,
                            bids=bids,
                            asks=asks,
                            obi=obi,
                            volatility=volatility
                        )

                        order_record = {
                            "symbol": symbol,
                            "direction": sizing["direction"],
                            "limit_price": limit_price,
                            "units": sizing["units"],
                            "sl_price": sizing["sl_price"],
                            "tp_price": sizing["tp_price"],
                            "risk_dollar": sizing["risk_dollar"],
                            "created_time": now_str,
                            "score": score,
                            "ticks_alive": 0,
                            "strategy_name": strat_name
                        }
                        
                        strat_ledger["pending_orders"][symbol] = order_record
                        dir_str = "BUY LIMIT" if sizing["direction"] > 0 else "SELL LIMIT"
                        print(f"  [{strat_name}] 📥 PLACED {dir_str} on {symbol} @ ${limit_price:.2f} | SL: ${sizing['sl_price']:.2f} ({(abs(limit_price-sizing['sl_price'])/limit_price):.2%}) | TP: ${sizing['tp_price']:.2f} | Risk: ${sizing['risk_dollar']:.2f}")

                # Record equity snapshot
                strat_ledger["equity_curve"].append({
                    "timestamp": now_str,
                    "equity": strat_ledger["capital"]
                })
                
                self.ledger[strat_name] = strat_ledger

        self._save_ledger(benchmark_state=benchmark_state)
        print(f"[PaperTrader] Tick completed successfully. Sub-ledgers updated.\n")

    def run_continuous(self, interval_seconds: int = 30, max_ticks: Optional[int] = None):
        """Runs continuous paper trading loop."""
        print(f"Starting continuous paper trading (Interval: {interval_seconds}s)... Press Ctrl+C to stop.")
        ticks = 0
        try:
            while True:
                self.run_tick()
                ticks += 1
                if max_ticks and ticks >= max_ticks:
                    break
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\nContinuous paper trading stopped by operator.")

if __name__ == "__main__":
    trader = PaperTrader()
    trader.run_tick()
