"""
OpenBB & Market Sentiment Provider with in-memory TTL caching.
"""

import os
import time
import requests
from typing import Dict, Any, List

class OpenBBClient:
    """
    Wrapper for OpenBB data & Live Financial News Sentiment Analysis with TTL Caching.
    """
    def __init__(self):
        self.has_openbb_sdk = False
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        self._sentiment_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._circuit_cache: Dict[str, Tuple[float, bool]] = {}
        self._cache_ttl = 60.0 # 60 seconds TTL

        try:
            from openbb import obb
            self.obb = obb
            self.has_openbb_sdk = True
        except Exception:
            pass

    def get_news_sentiment(self, symbol: str = "BTC") -> Dict[str, Any]:
        """Fetches news sentiment with 60-second in-memory TTL cache."""
        now = time.time()
        if symbol in self._sentiment_cache:
            ts, cached_val = self._sentiment_cache[symbol]
            if now - ts < self._cache_ttl:
                return cached_val

        bullish_keywords = ["bullish", "surge", "breakout", "rally", "gain", "adopt", "buy", "record", "high", "growth", "sec approval"]
        bearish_keywords = ["bearish", "crash", "drop", "hack", "ban", "dump", "lawsuit", "collapse", "plunge", "panic", "investigation"]

        try:
            url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
            response = requests.get(url, headers=self.headers, timeout=3)
            if response.status_code == 200:
                data = response.json()
                articles = data.get("Data", [])
                
                if articles:
                    total_score = 0.0
                    relevant_count = 0

                    for article in articles[:15]:
                        title = (article.get("title", "") + " " + article.get("body", "")).lower()
                        if symbol.lower() in title or "crypto" in title or "bitcoin" in title or "market" in title:
                            relevant_count += 1
                            bull_count = sum(title.count(kw) for kw in bullish_keywords)
                            bear_count = sum(title.count(kw) for kw in bearish_keywords)

                            if bull_count > bear_count:
                                total_score += 0.2
                            elif bear_count > bull_count:
                                total_score -= 0.3

                    avg_sentiment = total_score / max(relevant_count, 1)
                    avg_sentiment = max(min(avg_sentiment, 1.0), -1.0)

                    result = {
                        "symbol": symbol,
                        "sentiment_score": round(avg_sentiment, 3),
                        "news_count": relevant_count,
                        "status": "ok",
                        "provider": "cryptocompare_news_api"
                    }
                    self._sentiment_cache[symbol] = (now, result)
                    return result
        except Exception:
            pass

        fallback_result = {
            "symbol": symbol,
            "sentiment_score": 0.0,
            "status": "offline_fallback",
            "provider": "openbb_neutral"
        }
        self._sentiment_cache[symbol] = (now, fallback_result)
        return fallback_result

    def is_circuit_breaker_triggered(self, symbol: str = "BTC") -> bool:
        """Evaluates emergency news circuit breaker with TTL cache."""
        now = time.time()
        if symbol in self._circuit_cache:
            ts, val = self._circuit_cache[symbol]
            if now - ts < self._cache_ttl:
                return val

        sentiment = self.get_news_sentiment(symbol)
        score = sentiment.get("sentiment_score", 0.0)
        is_triggered = score <= -0.7
        self._circuit_cache[symbol] = (now, is_triggered)
        return is_triggered
