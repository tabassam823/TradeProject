"""
Advanced Position Sizer for Binance Futures.
Replaces position_sizer.py with futures contract size mapping.

Key Changes:
- Maps symbol to Binance Futures contract size
- Calculates lot units in CONTRACTS, not raw units
- Supports leverage-adjusted position sizing
- Futures-specific minimum order quantity handling
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from src.core.binance_client_wds import FUTURES_CONTRACT_SIZES


class VolatilityTargetPositionSizer:
    """
    Futures-Ready Position Sizing Engine.
    
    Calculates exact CONTRACT QUANTITY (not raw units) for Binance Futures USDT-M.
    
    Key Formula:
        contracts = risk_dollar / (|P_entry - P_SL| * contract_size)
    
    Where:
        - contract_size: How much base asset per 1 contract (e.g., 0.001 BTC for BTCUSDT)
        - This ensures proper lot sizing on Binance Futures
    """

    # Binance Futures minimum notional value varies by symbol
    # Default minimum: $5 (most USDT-M perpetuals)
    MIN_NOTIONAL_USD = 5.0
    
    # Binance Futures maximum leverage by symbol
    MAX_LEVERAGES = {
        "BTC/USDT": 125,
        "ETH/USDT": 100,
        "SOL/USDT": 50,
        "BNB/USDT": 50,
        "AVAX/USDT": 50,
        "XRP/USDT": 100,
        "DOGE/USDT": 100,
        "ADA/USDT": 100,
        "DOT/USDT": 50,
        "LINK/USDT": 50,
    }

    def __init__(self, max_risk_per_trade: float = 0.02, min_volatility: float = 0.005):
        self.max_risk_per_trade = max_risk_per_trade
        self.min_volatility = min_volatility

    def get_contract_size(self, symbol: str) -> float:
        """
        Returns the contract size for a symbol.
        E.g., BTC/USDT → 0.001 (1 contract = 0.001 BTC)
        """
        clean_sym = symbol.replace("/", "").replace(":", "")
        
        # Direct match
        if clean_sym in FUTURES_CONTRACT_SIZES:
            return FUTURES_CONTRACT_SIZES[clean_sym]
        
        # Try reverse look-up
        for key, size in FUTURES_CONTRACT_SIZES.items():
            if key.replace("/", "") == clean_sym:
                return size
        
        # Fallback
        print(f"[PositionSizer] Warning: Contract size for {symbol} not found. Using 1.0")
        return 1.0

    def calculate_volatility(self, ohlcv_df: pd.DataFrame, window: int = 21) -> float:
        """Calculates rolling volatility of returns."""
        if ohlcv_df is None or len(ohlcv_df) < window:
            return 0.02
        returns = ohlcv_df['close'].pct_change().dropna()
        vol = returns.tail(window).std()
        if pd.isna(vol) or vol < self.min_volatility:
            vol = self.min_volatility
        return float(vol)

    def calculate_tiered_risk_dollar(self, capital: float) -> float:
        """
        Tiered Risk Budgeting:
        - Capital <= $100: Risk fixed $1.00 per trade.
        - Capital > $100: Risk 1% of capital per trade.
        """
        if capital <= 100.0:
            return 1.00
        else:
            return capital * 0.01

    def calculate_sl_tp_levels(
        self,
        entry_price: float,
        direction: int,
        volatility: float,
        rr_ratio: float = 2.5,
        regime: Optional[str] = None
    ) -> Tuple[float, float, float]:
        """
        Calculates Stop Loss and Take Profit levels with Regime Adaptation.
        In HIGH_VOLATILITY_CRISIS or MEAN_REVERSION_CHOP, scales SL distance up to 2.8x.
        """
        # Regime-adaptive scaling multiplier
        if regime in ["HIGH_VOLATILITY_CRISIS", "MEAN_REVERSION_CHOP"]:
            sl_multiplier = 2.8
            min_sl_distance_pct = 0.025  # 2.5% minimum breathing room
        else:
            sl_multiplier = 1.5
            min_sl_distance_pct = 0.010  # 1.0% minimum breathing room

        sl_pct = max(volatility * sl_multiplier, min_sl_distance_pct)
        tp_pct = sl_pct * rr_ratio

        if direction > 0:  # Long
            sl_price = entry_price * (1.0 - sl_pct)
            tp_price = entry_price * (1.0 + tp_pct)
        else:  # Short
            sl_price = entry_price * (1.0 + sl_pct)
            tp_price = entry_price * (1.0 - tp_pct)

        return round(sl_price, 4), round(tp_price, 4), sl_pct

    def calculate_exact_contract_units(
        self,
        entry_price: float,
        sl_price: float,
        risk_dollar: float,
        symbol: str = "BTC/USDT"
    ) -> float:
        """
        Calculates exact CONTRACT QUANTITY for Binance Futures.
        
        Formula:
            contracts = risk_dollar / (|P_entry - P_SL| * contract_size)
        
        Where:
            contract_size = amount of base asset per 1 contract
                            (e.g., 0.001 BTC means 1 BTCUSDT contract = 0.001 BTC)
        
        This ensures the position is sized correctly on Binance Futures.
        
        Example:
            Entry: $50,000, SL: $49,000, Risk: $100, BTC/USDT (contract_size=0.001)
            contracts = 100 / (1000 * 0.001) = 100 / 1 = 100 contracts
            Each contract = 0.001 BTC, so 100 contracts = 0.1 BTC position
            Risk: 0.1 BTC * $1000 = $100 ✓
        """
        sl_distance = abs(entry_price - sl_price)
        contract_size = self.get_contract_size(symbol)
        
        if sl_distance <= 1e-6:
            return 0.0
        
        # contracts = risk_dollar / (price_distance * contract_size)
        contracts = risk_dollar / (sl_distance * contract_size)
        
        # Round to minimum lot size for the symbol
        min_lot = 1.0  # Minimum 1 contract
        contracts = max(contracts, min_lot)
        
        return contracts

    def calculate_position_size(
        self,
        current_price: float,
        capital: float,
        score: float,
        volatility: float,
        risk_budget_ratio: float = 0.01,
        is_circuit_broken: bool = False,
        regime: Optional[str] = None,
        symbol: str = "BTC/USDT",
        leverage: int = 20
    ) -> Dict[str, Any]:
        """
        Synthesizes futures position direction, target value, and exact contract units.
        
        Returns:
            Dict with direction, target_value, contracts, sl_price, tp_price, risk_dollar, sl_pct
        """
        if is_circuit_broken or abs(score) < 0.5 or current_price <= 0:
            return {
                "direction": 0,
                "target_value": 0.0,
                "contracts": 0.0,
                "sl_price": 0.0,
                "tp_price": 0.0,
                "risk_dollar": 0.0
            }

        direction = 1 if score > 0 else -1
        conviction = min(abs(score) / 4.0, 1.0)

        # Risk dollar allocation
        base_risk_dollar = self.calculate_tiered_risk_dollar(capital)
        trade_risk_dollar = base_risk_dollar * conviction

        sl_price, tp_price, sl_pct = self.calculate_sl_tp_levels(
            entry_price=current_price,
            direction=direction,
            volatility=volatility,
            rr_ratio=2.5,
            regime=regime
        )

        # Calculate exact CONTRACT quantity for Binance Futures
        contracts = self.calculate_exact_contract_units(
            entry_price=current_price,
            sl_price=sl_price,
            risk_dollar=trade_risk_dollar,
            symbol=symbol
        )

        # Calculate notional value in USDT
        contract_size = self.get_contract_size(symbol)
        target_value = contracts * contract_size * current_price

        # Apply leverage cap: max position value = capital * leverage
        max_position_value = capital * leverage
        if target_value > max_position_value:
            target_value = max_position_value
            contracts = target_value / (contract_size * current_price)
            # Ensure at least 1 contract if direction is valid
            contracts = max(contracts, 1.0) if direction != 0 else 0.0

        # Ensure minimum notional ($5 on Binance Futures)
        if target_value < self.MIN_NOTIONAL_USD and direction != 0:
            # Adjust contracts to meet minimum
            min_contracts = self.MIN_NOTIONAL_USD / (contract_size * current_price)
            contracts = max(contracts, min_contracts)
            target_value = contracts * contract_size * current_price

        return {
            "direction": direction,
            "target_value": float(target_value),
            "contracts": float(contracts),
            "sl_price": float(sl_price),
            "tp_price": float(tp_price),
            "risk_dollar": float(trade_risk_dollar),
            "sl_pct": float(sl_pct),
            "symbol": symbol,
            "contract_size": contract_size
        }

    def calculate_leverage_required(
        self,
        capital: float,
        contracts: float,
        symbol: str,
        entry_price: float
    ) -> int:
        """
        Calculates the minimum leverage required for a position.
        """
        contract_size = self.get_contract_size(symbol)
        position_value = contracts * contract_size * entry_price
        
        if position_value <= 0:
            return 1
        
        # leverage = position_value / capital
        leverage_needed = position_value / capital
        return int(np.ceil(leverage_needed))

    def validate_order_on_binance(
        self,
        symbol: str,
        contracts: float,
        side: str,
        current_price: float,
        leverage: int = 20
    ) -> Dict[str, Any]:
        """
        Validates if an order will meet Binance Futures requirements:
        - Minimum notional value ($5)
        - Maximum position size
        - Leverage constraints
        
        Returns:
            Dict with validation results.
        """
        contract_size = self.get_contract_size(symbol)
        notional = contracts * contract_size * current_price
        
        # Check minimum notional
        if notional < self.MIN_NOTIONAL_USD:
            return {
                "valid": False,
                "reason": f"Notional ${notional:.2f} below minimum ${self.MIN_NOTIONAL_USD}",
                "notional": notional
            }
        
        # Check maximum position size (50x leverage max)
        max_notional = contract_size * current_price * leverage
        if notional > max_notional:
            return {
                "valid": False,
                "reason": f"Notional ${notional:.2f} exceeds max position at {leverage}x",
                "notional": notional,
                "max_allowed": max_notional
            }
        
        return {
            "valid": True,
            "notional": notional,
            "leverage": leverage,
            "contract_size": contract_size
        }
