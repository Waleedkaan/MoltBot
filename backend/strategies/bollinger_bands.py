"""
Bollinger Bands Strategy
Price position relative to Bollinger Bands
"""
import pandas as pd
import pandas_ta as ta
from typing import Dict
from config import settings
import structlog

logger = structlog.get_logger()


class BollingerBandsStrategy:
    """Bollinger Bands trading strategy"""
    
    def __init__(self, period: int = None, std: int = None):
        """
        Initialize Bollinger Bands strategy
        
        Args:
            period: Period for moving average (default 20)
            std: Standard deviations (default 2)
        """
        self.period = period or settings.BOLLINGER_PERIOD
        self.std = std or settings.BOLLINGER_STD
        self.name = "Bollinger Bands"
        logger.info("Bollinger Bands Strategy initialized", period=self.period, std=self.std)
    
    def calculate(self, df: pd.DataFrame) -> Dict:
        """
        Calculate Bollinger Bands signal
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with signal and confidence
        """
        try:
            # Calculate Bollinger Bands
            bbands = ta.bbands(df['close'], length=self.period, std=self.std)
            
            upper = bbands[f'BBU_{self.period}_{self.std}.0']
            middle = bbands[f'BBM_{self.period}_{self.std}.0']
            lower = bbands[f'BBL_{self.period}_{self.std}.0']
            
            current_price = df['close'].iloc[-1]
            current_upper = upper.iloc[-1]
            current_middle = middle.iloc[-1]
            current_lower = lower.iloc[-1]
            
            # Band width (for squeeze detection)
            band_width = ((current_upper - current_lower) / current_middle) * 100
            
            # Calculate position within bands (0 to 1)
            if current_upper != current_lower:
                position = (current_price - current_lower) / (current_upper - current_lower)
            else:
                position = 0.5
            
            # Determine signal
            if current_price <= current_lower:
                signal = "BUY"
                # Confidence based on how far below lower band
                below_pct = ((current_lower - current_price) / current_lower) * 100
                confidence = min(100, 60 + below_pct * 20)
            elif current_price >= current_upper:
                signal = "SELL"
                # Confidence based on how far above upper band
                above_pct = ((current_price - current_upper) / current_upper) * 100
                confidence = min(100, 60 + above_pct * 20)
            elif current_price < current_middle and position < 0.3:
                signal = "BUY"
                confidence = 40 + (0.3 - position) * 50
            elif current_price > current_middle and position > 0.7:
                signal = "SELL"
                confidence = 40 + (position - 0.7) * 50
            else:
                signal = "NEUTRAL"
                confidence = max(20, 40 - abs(position - 0.5) * 40)
            
            result = {
                'strategy': self.name,
                'signal': signal,
                'confidence': round(confidence, 2),
                'price': round(current_price, 2),
                'upper': round(current_upper, 2),
                'middle': round(current_middle, 2),
                'lower': round(current_lower, 2),
                'position': round(position, 3),
                'band_width': round(band_width, 2)
            }
            
            logger.debug("Bollinger Bands calculated", **result)
            return result
        
        except Exception as e:
            logger.error("Error calculating Bollinger Bands", error=str(e))
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
        strategy = BollingerBandsStrategy()
        result = strategy.calculate(df)
        print(f"\nBollinger Bands Strategy Result:")
        print(f"  Signal: {result['signal']}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Price: ${result['price']:,.2f}")
        print(f"  Upper: ${result['upper']:,.2f}")
        print(f"  Middle: ${result['middle']:,.2f}")
        print(f"  Lower: ${result['lower']:,.2f}")
