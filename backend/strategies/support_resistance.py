"""
Support & Resistance Strategy
Dynamic support and resistance level detection
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import structlog

logger = structlog.get_logger()


class SupportResistanceStrategy:
    """Support and Resistance trading strategy"""
    
    def __init__(self, lookback: int = 50, threshold: float = 0.02):
        """
        Initialize S/R strategy
        
        Args:
            lookback: Number of candles to look back
            threshold: Price threshold for level clustering (2%)
        """
        self.lookback = lookback
        self.threshold = threshold 
        self.name = "Support/Resistance"
        logger.info("S/R Strategy initialized", lookback=self.lookback)
    
    def _find_pivots(self, df: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """
        Find pivot highs and lows
        
        Returns:
            Tuple of (support_levels, resistance_levels)
        """
        highs = []
        lows = []
        
        # Look for local highs and lows
        for i in range(2, len(df) - 2):
            # Pivot high (resistance)
            if (df['high'].iloc[i] > df['high'].iloc[i-1] and 
                df['high'].iloc[i] > df['high'].iloc[i-2] and
                df['high'].iloc[i] > df['high'].iloc[i+1] and 
                df['high'].iloc[i] > df['high'].iloc[i+2]):
                highs.append(df['high'].iloc[i])
            
            # Pivot low (support)
            if (df['low'].iloc[i] < df['low'].iloc[i-1] and 
                df['low'].iloc[i] < df['low'].iloc[i-2] and
                df['low'].iloc[i] < df['low'].iloc[i+1] and 
                df['low'].iloc[i] < df['low'].iloc[i+2]):
                lows.append(df['low'].iloc[i])
        
        return lows, highs
    
    def _cluster_levels(self, levels: List[float]) -> List[float]:
        """
        Cluster nearby price levels
        
        Args:
            levels: List of price levels
            
        Returns:
            List of clustered levels
        """
        if not levels:
            return []
        
        levels = sorted(levels)
        clustered = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            # If within threshold, add to current cluster
            if (level - current_cluster[-1]) / current_cluster[-1] <= self.threshold:
                current_cluster.append(level)
            else:
                # Save cluster average and start new cluster
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]
        
        # Add last cluster
        if current_cluster:
            clustered.append(np.mean(current_cluster))
        
        return clustered
    
    def calculate(self, df: pd.DataFrame) -> Dict:
        """
        Calculate S/R signal
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with signal and confidence
        """
        try:
            # Use last N candles
            df_lookback = df.tail(self.lookback).copy().reset_index(drop=True)
            
            # Find pivots
            support_levels, resistance_levels = self._find_pivots(df_lookback)
            
            # Cluster levels
            support_levels = self._cluster_levels(support_levels)
            resistance_levels = self._cluster_levels(resistance_levels)
            
            current_price = df['close'].iloc[-1]
            
            # Find nearest support and resistance
            nearest_support = None
            nearest_resistance = None
            
            for level in support_levels:
                if level < current_price:
                    if nearest_support is None or level > nearest_support:
                        nearest_support = level
            
            for level in resistance_levels:
                if level > current_price:
                    if nearest_resistance is None or level < nearest_resistance:
                        nearest_resistance = level
            
            # Calculate distances
            support_distance = None
            resistance_distance = None
            
            if nearest_support:
                support_distance = ((current_price - nearest_support) / current_price) * 100
            
            if nearest_resistance:
                resistance_distance = ((nearest_resistance - current_price) / current_price) * 100
            
            # Determine signal
            signal = "NEUTRAL"
            confidence = 30
            
            # Near support = potential bounce = BUY
            if support_distance is not None and support_distance < 1.0:
                signal = "BUY"
                confidence = min(100, 60 + (1.0 - support_distance) * 30)
            
            # Near resistance = potential rejection = SELL
            elif resistance_distance is not None and resistance_distance < 1.0:
                signal = "SELL"
                confidence = min(100, 60 + (1.0 - resistance_distance) * 30)
            
            # Breakout above resistance = BUY
            elif nearest_resistance and current_price > nearest_resistance:
                signal = "BUY"
                breakout_strength = ((current_price - nearest_resistance) / nearest_resistance) * 100
                confidence = min(100, 50 + breakout_strength * 20)
            
            # Breakdown below support = SELL
            elif nearest_support and current_price < nearest_support:
                signal = "SELL"
                breakdown_strength = ((nearest_support - current_price) / nearest_support) * 100
                confidence = min(100, 50 + breakdown_strength * 20)
            
            result = {
                'strategy': self.name,
                'signal': signal,
                'confidence': round(confidence, 2),
                'current_price': round(current_price, 2),
                'nearest_support': round(nearest_support, 2) if nearest_support else None,
                'nearest_resistance': round(nearest_resistance, 2) if nearest_resistance else None,
                'support_distance': round(support_distance, 2) if support_distance else None,
                'resistance_distance': round(resistance_distance, 2) if resistance_distance else None,
                'num_support_levels': len(support_levels),
                'num_resistance_levels': len(resistance_levels)
            }
            
            logger.debug("S/R calculated", **result)
            return result
        
        except Exception as e:
            logger.error("Error calculating S/R", error=str(e))
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
        strategy = SupportResistanceStrategy()
        result = strategy.calculate(df)
        print(f"\nSupport/Resistance Strategy Result:")
        print(f"  Signal: {result['signal']}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Current Price: ${result['current_price']:,.2f}")
        if result['nearest_support']:
            print(f"  Nearest Support: ${result['nearest_support']:,.2f}")
        if result['nearest_resistance']:
            print(f"  Nearest Resistance: ${result['nearest_resistance']:,.2f}")
