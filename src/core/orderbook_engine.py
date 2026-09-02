"""
Order Book & Market Microstructure Engine.
Implements Tahap P, U & Tahap AC from ChatGPT/MD_Source:
- Order Book Imbalance (OBI) calculation across depth levels.
- Effective Spread and Market Impact estimation.
- Optimal Limit Order placement within the bid-ask spread.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional

class OrderBookEngine:
    """
    Microstructure & Order Book Analytics.
    Provides liquidity analysis, Order Book Imbalance (OBI), and passive limit placement prices.
    """

    @staticmethod
    def calculate_order_book_imbalance(bids: List[List[float]], asks: List[List[float]], depth_levels: int = 10) -> float:
        """
        Calculates Order Book Imbalance (OBI) for top N depth levels:
        OBI = (Sum(V_bid) - Sum(V_ask)) / (Sum(V_bid) + Sum(V_ask))
        Returns float in [-1.0, +1.0], where +1.0 is pure bid pressure, -1.0 is pure ask pressure.
        """
        if not bids or not asks:
            return 0.0

        n_bids = min(len(bids), depth_levels)
        n_asks = min(len(asks), depth_levels)

        bid_vol = sum(float(b[1]) for b in bids[:n_bids])
        ask_vol = sum(float(a[1]) for a in asks[:n_asks])
        total_vol = bid_vol + ask_vol

        if total_vol < 1e-8:
            return 0.0

        obi = (bid_vol - ask_vol) / total_vol
        return float(np.clip(obi, -1.0, 1.0))

    @staticmethod
    def get_top_of_book(bids: List[List[float]], asks: List[List[float]]) -> Tuple[float, float, float]:
        """
        Returns: (best_bid, best_ask, spread_pct)
        """
        if not bids or not asks:
            return 0.0, 0.0, 0.0

        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        mid_price = (best_bid + best_ask) / 2.0

        spread_pct = ((best_ask - best_bid) / mid_price) if mid_price > 0 else 0.0
        return best_bid, best_ask, spread_pct

    @staticmethod
    def calculate_optimal_limit_price(
        direction: int,
        current_price: float,
        bids: Optional[List[List[float]]] = None,
        asks: Optional[List[List[float]]] = None,
        obi: float = 0.0,
        volatility: float = 0.01
    ) -> float:
        """
        Calculates optimal passive limit order price inside the spread to capture maker fees
        and avoid adverse selection (Tahap P & Tahap U).
        """
        if bids and asks and len(bids) > 0 and len(asks) > 0:
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            
            if direction > 0: # BUY Limit
                # Place near best bid, adjusted slightly by order book imbalance
                offset = (best_ask - best_bid) * (0.2 if obi > 0.2 else 0.1)
                return round(best_bid + offset, 2)
            else: # SELL Limit
                offset = (best_ask - best_bid) * (0.2 if obi < -0.2 else 0.1)
                return round(best_ask - offset, 2)
        else:
            # Fallback estimation based on volatility
            offset = current_price * (volatility * 0.1)
            if direction > 0:
                return round(current_price - offset, 2)
            else:
                return round(current_price + offset, 2)
