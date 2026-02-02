"""
MACD Strategy
Moving Average Convergence Divergence strategy
"""
import pandas as pd
import pandas_ta as ta
from typing import Dict
from config import settings
import structlog

logger = structlog.get_logger()


class MACDStrategy:
    """MACD trading strategy"""
    
    def __init__(self, fast: int = None, slow: int = None, signal: int = None):
        """
        Initialize MACD strategy
        
        Args:
            fast: Fast period (default 12)
            slow: Slow period (default 26)
            signal: Signal period (default 9)
        """
        self.fast = fast or settings.MACD_FAST
        self.slow = slow or settings.MACD_SLOW
        self.signal_period = signal or settings.MACD_SIGNAL
        self.name = "MACD"
        logger.info("MACD Strategy initialized", fast=self.fast, slow=self.slow, signal=self.signal_period)
    
    def calculate(self, df: pd.DataFrame) -> Dict:
        """
        Calculate MACD signal
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with signal and confidence
        """
        try:
            # Calculate MACD
            macd_result = ta.macd(
                df['close'],
                fast=self.fast,
                slow=self.slow,
                signal=self.signal_period
            )
            
            macd_line = macd_result[f'MACD_{self.fast}_{self.slow}_{self.signal_period}']
            signal_line = macd_result[f'MACDs_{self.fast}_{self.slow}_{self.signal_period}']
            histogram = macd_result[f'MACDh_{self.fast}_{self.slow}_{self.signal_period}']
            
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_hist = histogram.iloc[-1]
            
            # Previous values for crossover
            prev_macd = macd_line.iloc[-2]
            prev_signal = signal_line.iloc[-2]
            
            # Detect crossover
            bullish_cross = prev_macd <= prev_signal and current_macd > current_signal
            bearish_cross = prev_macd >= prev_signal and current_macd < current_signal
            
            # Histogram strength
            hist_strength = abs(current_hist)
            
            if bullish_cross or (current_macd > current_signal and current_hist > 0):
                signal = "BUY"
                # Confidence based on histogram strength
                confidence = min(100, 50 + hist_strength * 5)
            elif bearish_cross or (current_macd < current_signal and current_hist < 0):
                signal = "SELL"
                confidence = min(100, 50 + hist_strength * 5)
            else:
                signal = "NEUTRAL"
                confidence = max(20, 40 - hist_strength * 2)
            
            result = {
                'strategy': self.name,
                'signal': signal,
                'confidence': round(confidence, 2),
                'macd': round(current_macd, 2),
                'signal_line': round(current_signal, 2),
                'histogram': round(current_hist, 2),
                'bullish_cross': bullish_cross,
                'bearish_cross': bearish_cross
            }
            
            logger.debug("MACD calculated", **result)
            return result
        
        except Exception as e:
            logger.error("Error calculating MACD", error=str(e))
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
        strategy = MACDStrategy()
        result = strategy.calculate(df)
        print(f"\nMACD Strategy Result:")
        print(f"  Signal: {result['signal']}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  MACD: {result['macd']}")
        print(f"  Signal Line: {result['signal_line']}")
        print(f"  Histogram: {result['histogram']}")
