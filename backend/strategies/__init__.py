"""
Strategies Package
"""
from .rsi_strategy import RSIStrategy
from .ema_crossover import EMACrossoverStrategy
from .macd_strategy import MACDStrategy
from .bollinger_bands import BollingerBandsStrategy
from .volume_spike import VolumeSpikeStrategy
from .support_resistance import SupportResistanceStrategy
from .strategy_manager import StrategyManager

__all__ = [
    'RSIStrategy',
    'EMACrossoverStrategy',
    'MACDStrategy',
    'BollingerBandsStrategy',
    'VolumeSpikeStrategy',
    'SupportResistanceStrategy',
    'StrategyManager'
]
