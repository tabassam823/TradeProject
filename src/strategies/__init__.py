"""Strategies Package for TradeProject."""
from src.strategies.base_strategy import BaseStrategy
from src.strategies.momentum import MultiHorizonMomentumStrategy
from src.strategies.vwap_rejection import VWAPRejectionStrategy
from src.strategies.sentiment_trend import SentimentFilteredTrendStrategy
from src.strategies.factor_regime import FactorRegimeStrategy
from src.strategies.first_passage_value import FirstPassageValueStrategy
from src.strategies.qubo_portfolio_selector import QUBOPortfolioStrategy
from src.strategies.signature_trading import SignatureTradingStrategy
from src.strategies.deep_sig_strategy import DeepSignatureTradingStrategy
from src.strategies.dual_thrust import DualThrustStrategy
from src.strategies.awesome_oscillator import AwesomeOscillatorStrategy
from src.strategies.bollinger_mean_reversion import BollingerMeanReversionStrategy
from src.strategies.heikin_ashi import HeikinAshiTrendStrategy

__all__ = [
    "BaseStrategy",
    "MultiHorizonMomentumStrategy",
    "VWAPRejectionStrategy",
    "SentimentFilteredTrendStrategy",
    "FactorRegimeStrategy",
    "FirstPassageValueStrategy",
    "QUBOPortfolioStrategy",
    "SignatureTradingStrategy",
    "DeepSignatureTradingStrategy",
    "DualThrustStrategy",
    "AwesomeOscillatorStrategy",
    "BollingerMeanReversionStrategy",
    "HeikinAshiTrendStrategy"
]
