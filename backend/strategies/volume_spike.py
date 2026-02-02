"""
Volume Spike Strategy
Detects unusual volume spikes combined with price direction
"""
import pandas as pd
import pandas_ta as ta
from typing import Dict
from config import settings
import structlog

logger = structlog.get_logger()


class VolumeSpikeStrategy:
    """Volume spike detection strategy"""
    
    def __init__(self, multiplier: float = None, period: int = 20):
        """
        Initialize Volume Spike strategy
        
        Args:
            multiplier: Volume spike multiplier (default 2.0)
            period: Period for volume average (default 20)
        """
        self.multiplier = multiplier or settings.VOLUME_SPIKE_MULTIPLIER
        self.period = period
        self.name = "Volume Spike"
        logger.info("Volume Spike Strategy initialized", multiplier=self.multiplier)
    
    def calculate(self, df: pd.DataFrame) -> Dict:
        """
        Calculate volume spike signal
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with signal and confidence
        """
        try:
            # Calculate volume SMA
            volume_sma = ta.sma(df['volume'], length=self.period)
            
            current_volume = df['volume'].iloc[-1]
            avg_volume = volume_sma.iloc[-1]
            
            # Price change
            current_close = df['close'].iloc[-1]
            prev_close = df['close'].iloc[-2]
            price_change_pct = ((current_close - prev_close) / prev_close) * 100
            
            # Volume spike ratio
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
            else:
                volume_ratio = 1.0
            
            # Detect spike
            is_spike = volume_ratio >= self.multiplier
            
            if is_spike:
                if price_change_pct > 1.0:  # Price up with volume spike
                    signal = "BUY"
                    # Confidence based on volume ratio and price change
                    confidence = min(100, 50 + (volume_ratio - self.multiplier) * 15 + abs(price_change_pct) * 3)
                elif price_change_pct < -1.0:  # Price down with volume spike
                    signal = "SELL"
                    confidence = min(100, 50 + (volume_ratio - self.multiplier) * 15 + abs(price_change_pct) * 3)
                else:
                    signal = "NEUTRAL"
                    confidence = 30
            else:
                # No spike or minor spike
                if volume_ratio > 1.2 and abs(price_change_pct) > 0.5:
                    signal = "BUY" if price_change_pct > 0 else "SELL"
                    confidence = max(20, 30 + (volume_ratio - 1) * 20)
                else:
                    signal = "NEUTRAL"
                    confidence = max(10, 25 - abs(1 - volume_ratio) * 10)
            
            result = {
                'strategy': self.name,
                'signal': signal,
                'confidence': round(confidence, 2),
                'current_volume': int(current_volume),
                'avg_volume': int(avg_volume),
                'volume_ratio': round(volume_ratio, 2),
                'price_change_pct': round(price_change_pct, 2),
                'is_spike': is_spike
            }
            
            logger.debug("Volume Spike calculated", **result)
            return result
        
        except Exception as e:
            logger.error("Error calculating Volume Spike", error=str(e))
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
        strategy = VolumeSpikeStrategy()
        result = strategy.calculate(df)
        print(f"\nVolume Spike Strategy Result:")
        print(f"  Signal: {result['signal']}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Volume Ratio: {result['volume_ratio']}x")
        print(f"  Price Change: {result['price_change_pct']}%")
        print(f"  Is Spike: {result['is_spike']}")
