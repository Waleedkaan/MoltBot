"""
RSI Strategy
Relative Strength Index trading strategy
"""
import pandas as pd
import pandas_ta as ta
from typing import Dict
from config import settings
import structlog

logger = structlog.get_logger()


class RSIStrategy:
    """RSI-based trading strategy"""
    
    def __init__(
        self,
        period: int = None,
        overbought: int = None,
        oversold: int = None
    ):
        """
        Initialize RSI strategy
        
        Args:
            period: RSI period (default from settings)
            overbought: Overbought threshold (default 70)
            oversold: Oversold threshold (default 30)
        """
        self.period = period or settings.RSI_PERIOD
        self.overbought = overbought or settings.RSI_OVERBOUGHT
        self.oversold = oversold or settings.RSI_OVERSOLD
        self.name = "RSI"
        logger.info("RSI Strategy initialized", period=self.period)
    
    def calculate(self, df: pd.DataFrame) -> Dict:
        """
        Calculate RSI signal
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with signal and confidence
        """
        try:
            # Calculate RSI
            rsi = ta.rsi(df['close'], length=self.period)
            current_rsi = rsi.iloc[-1]
            
            # Determine signal
            if current_rsi <= self.oversold:
                signal = "BUY"
                # Confidence increases the further we are below oversold
                confidence = min(100, 50 + (self.oversold - current_rsi) * 2)
            elif current_rsi >= self.overbought:
                signal = "SELL"
                # Confidence increases the further we are above overbought
                confidence = min(100, 50 + (current_rsi - self.overbought) * 2)
            else:
                signal = "NEUTRAL"
                # Confidence decreases as we approach middle (50)
                distance_from_neutral = abs(current_rsi - 50)
                confidence = max(20, distance_from_neutral)
            
            result = {
                'strategy': self.name,
                'signal': signal,
                'confidence': round(confidence, 2),
                'value': round(current_rsi, 2),
                'overbought': self.overbought,
                'oversold': self.oversold
            }
            
            logger.debug("RSI calculated", **result)
            return result
        
        except Exception as e:
            logger.error("Error calculating RSI", error=str(e))
            return {
                'strategy': self.name,
                'signal': 'NEUTRAL',
                'confidence': 0,
                'value': 0,
                'error': str(e)
            }


# Usage example
if __name__ == "__main__":
    from data.market_data_collector import MarketDataCollector
    
    collector = MarketDataCollector()
    df = collector.get_ohlcv("BTC", "1h", limit=100)
    
    if df is not None:
        strategy = RSIStrategy()
        result = strategy.calculate(df)
        print(f"\nRSI Strategy Result:")
        print(f"  Signal: {result['signal']}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  RSI Value: {result['value']}")
