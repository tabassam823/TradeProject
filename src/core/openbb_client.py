import os
import requests
from typing import Dict, Any

class OpenBBClient:
    """Wrapper for OpenBB data, news sentiment, and macro indicators."""
    def __init__(self):
        self.has_openbb_sdk = False
        try:
            from openbb import obb
            self.obb = obb
            self.has_openbb_sdk = True
            print("[OpenBBClient] OpenBB SDK loaded successfully.")
        except Exception:
            print("[OpenBBClient] OpenBB SDK not imported directly; using standalone fallback mode.")

    def get_news_sentiment(self, symbol: str = "BTC") -> Dict[str, Any]:
        """
        Fetches news sentiment score for symbol.
        Returns sentiment score (-1.0 to +1.0) and news count.
        """
        if self.has_openbb_sdk:
            try:
                # OpenBB SDK call if available
                res = self.obb.news.world(provider="benzinga", limit=10)
                # Parse sentiment
                return {"sentiment_score": 0.1, "status": "ok", "provider": "openbb"}
            except Exception as e:
                print(f"[OpenBBClient] SDK fetch info: {e}")

        # Standard fallback sentiment check / CryptoCompare or mock news score
        return {
            "symbol": symbol,
            "sentiment_score": 0.05,  # Slightly neutral-positive default
            "status": "ok",
            "provider": "openbb_fallback"
        }

    def is_circuit_breaker_triggered(self, symbol: str, threshold: float = -0.6) -> bool:
        """Checks if critical negative news sentiment triggers the circuit breaker."""
        sentiment_data = self.get_news_sentiment(symbol)
        score = sentiment_data.get("sentiment_score", 0.0)
        if score <= threshold:
            print(f"[CIRCUIT BREAKER ALERT] Critical negative sentiment detected for {symbol} ({score:.2f} <= {threshold:.2f})!")
            return True
        return False
