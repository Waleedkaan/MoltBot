"""
EMA Crossover Strategy
Fast EMA vs Slow EMA crossover strategy
"""
import pandas as pd
import pandas_ta as ta
from typing import Dict
from config import settings
import structlog

logger = structlog.get_logger()


class EMACrossoverStrategy:
    """EMA crossover trading strategy"""
    
    def __init__(self, fast: int = None, slow: int = None):
        """
        Initialize EMA crossover strategy
        
        Args:
            fast: Fast EMA period (default 9)
            slow: Slow EMA period (default 21)
        """
        self.fast = fast or settings.EMA_FAST
        self.slow = slow or settings.EMA_SLOW
        self.name = "EMA Crossover"
        logger.info("EMA Crossover Strategy initialized", fast=self.fast, slow=self.slow)
    
    def calculate(self, df: pd.DataFrame) -> Dict:
        """
        Calculate EMA crossover signal
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with signal and confidence
        """
        try:
            # Calculate EMAs
            ema_fast = ta.ema(df['close'], length=self.fast)
            ema_slow = ta.ema(df['close'], length=self.slow)
            
            current_fast = ema_fast.iloc[-1]
            current_slow = ema_slow.iloc[-1]
            
            # Previous values for crossover detection
            prev_fast = ema_fast.iloc[-2]
            prev_slow = ema_slow.iloc[-2]
            
            # Calculate crossover strength (% difference)
            diff_percent = ((current_fast - current_slow) / current_slow) * 100
            
            # Detect crossover
            golden_cross = prev_fast <= prev_slow and current_fast > current_slow
            death_cross = prev_fast >= prev_slow and current_fast < current_slow
            
            if golden_cross or (current_fast > current_slow and abs(diff_percent) > 0.5):
                signal = "BUY"
                # Higher confidence with stronger crossover
                confidence = min(100, 50 + abs(diff_percent) * 10)
            elif death_cross or (current_fast < current_slow and abs(diff_percent) > 0.5):
                signal = "SELL"
                confidence = min(100, 50 + abs(diff_percent) * 10)
            else:
                signal = "NEUTRAL"
                confidence = max(20, 40 - abs(diff_percent) * 5)
            
            result = {
                'strategy': self.name,
                'signal': signal,
                'confidence': round(confidence, 2),
                'ema_fast': round(current_fast, 2),
                'ema_slow': round(current_slow, 2),
                'diff_percent': round(diff_percent, 3),
                'golden_cross': golden_cross,
                'death_cross': death_cross
            }
            
            logger.debug("EMA Crossover calculated", **result)
            return result
        
        except Exception as e:
            logger.error("Error calculating EMA Crossover", error=str(e))
            return {
                'strategy': self.name,
                'signal': 'NEUTRAL',
                'confidence': 0,
                'error': str(e)
            }


# Usage example
if __name__ == "__main__":
    from data.market_data_collector import MarketDataCollector
    
    collector = MarketDataCollector()
    df = collector.get_ohlcv("BTC", "1h", limit=100)
    
    if df is not None:
        strategy = EMACrossoverStrategy()
        result = strategy.calculate(df)
        print(f"\nEMA Crossover Strategy Result:")
        print(f"  Signal: {result['signal']}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Fast EMA: ${result['ema_fast']:,.2f}")
        print(f"  Slow EMA: ${result['ema_slow']:,.2f}")
