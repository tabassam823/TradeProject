from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class BaseStrategy(ABC):
    """
    Abstract Base Class for modular strategies in TradeProject.
    Every strategy must implement generate_signal() returning a signal score.
    """
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)

    @abstractmethod
    def generate_signal(self, ohlcv_df: pd.DataFrame) -> float:
        """
        Calculates signal score from OHLCV data.
        Returns a float score (typically -4.0 to +4.0, where + is Long, - is Short).
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Returns strategy metadata."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "config": self.config
        }
