import pandas as pd
from typing import Dict, Any
from src.strategies.base_strategy import BaseStrategy
from src.core.openbb_client import OpenBBClient

class SentimentFilteredTrendStrategy(BaseStrategy):
    """
    Combines Moving Average trend filter with OpenBB News Sentiment analysis.
    Only enters trend positions when sentiment alignment supports the technical trend.
    """
    def __init__(self, name: str = "sentiment_filtered_trend", config: Dict[str, Any] = None):
        if config is None:
            config = {
                "enabled": True,
                "trend_fast": 10,
                "trend_slow": 30,
                "min_sentiment_score": -0.2
            }
        super().__init__(name, config)
        self.fast_period = config.get("trend_fast", 10)
        self.slow_period = config.get("trend_slow", 30)
        self.min_sentiment = config.get("min_sentiment_score", -0.2)
        self.openbb_client = OpenBBClient()

    def generate_signal(self, ohlcv_df: pd.DataFrame) -> float:
        """Calculates sentiment-filtered trend signal score."""
        if ohlcv_df is None or len(ohlcv_df) < self.slow_period:
            return 0.0

        close = ohlcv_df['close']
        fast_ema = close.ewm(span=self.fast_period, adjust=False).mean()
        slow_ema = close.ewm(span=self.slow_period, adjust=False).mean()

        current_fast = fast_ema.iloc[-1]
        current_slow = slow_ema.iloc[-1]

        sentiment_info = self.openbb_client.get_news_sentiment("BTC")
        sentiment_score = sentiment_info.get("sentiment_score", 0.0)

        # Bullish crossover + non-bearish sentiment -> Long (+3.0)
        if current_fast > current_slow and sentiment_score >= self.min_sentiment:
            return 3.0
            
        # Bearish crossover + non-bullish sentiment -> Short (-3.0)
        if current_fast < current_slow and sentiment_score <= -self.min_sentiment:
            return -3.0

        return 0.0
