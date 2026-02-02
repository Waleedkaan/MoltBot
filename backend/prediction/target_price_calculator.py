"""
Target Price Calculator
Calculates predicted HIGH/LOW price based on volatility and confidence
"""
import pandas as pd
import pandas_ta as ta
from typing import Dict, Optional
import structlog

logger = structlog.get_logger()


class TargetPriceCalculator:
    """Calculates target price for BUY/SELL signals"""
    
    def __init__(self, atr_period: int = 14):
        """
        Initialize target price calculator
        
        Args:
            atr_period: Period for ATR calculation (default 14)
        """
        self.atr_period = atr_period
        logger.info("TargetPriceCalculator initialized", atr_period=atr_period)
    
    def calculate_target(
        self,
        df: pd.DataFrame,
        signal: str,
        confidence: float,
        min_confidence: int = 60
    ) -> Optional[Dict]:
        """
        Calculate target price for a signal
        
        Args:
            df: DataFrame with OHLCV data
            signal: BUY/SELL/NEUTRAL
            confidence: Confidence percentage
            min_confidence: Minimum confidence to calculate target
            
        Returns:
            Dictionary with target price and type, or None if below threshold
        """
        try:
            # No target if confidence too low
            if confidence < min_confidence:
                logger.info("Confidence too low for target", confidence=confidence)
                return {
                    'target_price': None,
                    'target_type': None,
                    'current_price': df['close'].iloc[-1],
                    'reason': f'Confidence below threshold ({min_confidence}%)'
                }
            
            # No target for NEUTRAL
            if signal == 'NEUTRAL':
                return {
                    'target_price': None,
                    'target_type': None,
                    'current_price': df['close'].iloc[-1],
                    'reason': 'Signal is NEUTRAL'
                }
            
            # Calculate ATR for volatility
            atr = ta.atr(df['high'], df['low'], df['close'], length=self.atr_period)
            current_atr = atr.iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Confidence factor (higher confidence = larger target)
            # Scale from 0.5x to 2.0x ATR based on confidence
            confidence_factor = 0.5 + (confidence / 100) * 1.5
            
            # Calculate price movement
            price_movement = current_atr * confidence_factor
            
            if signal == 'BUY':
                # Target is HIGH price (current + movement)
                target_price = current_price + price_movement
                target_type = 'HIGH'
            else:  # SELL
                # Target is LOW price (current - movement)
                target_price = current_price - price_movement
                target_type = 'LOW'
            
            # Calculate percentage move
            pct_move = ((target_price - current_price) / current_price) * 100
            
            result = {
                'target_price': round(target_price, 2),
                'target_type': target_type,
                'current_price': round(current_price, 2),
                'atr': round(current_atr, 2),
                'confidence_factor': round(confidence_factor, 2),
                'price_movement': round(price_movement, 2),
                'pct_move': round(pct_move, 2)
            }
            
            logger.info(
                "Target price calculated",
                signal=signal,
                target_price=target_price,
                pct_move=pct_move
            )
            
            return result
        
        except Exception as e:
            logger.error("Error calculating target price", error=str(e))
            return None
    
    def calculate_stop_loss(
        self,
        current_price: float,
        signal: str,
        atr: float,
        risk_pct: float = 3.0
    ) -> float:
        """
        Calculate stop loss price
        
        Args:
            current_price: Current price
            signal: BUY or SELL
            atr: Average True Range
            risk_pct: Risk percentage (default 3%)
            
        Returns:
            Stop loss price
        """
        # Stop loss at 1.5x ATR or risk_pct, whichever is smaller
        atr_stop = current_price - (atr * 1.5)
        pct_stop = current_price * (1 - risk_pct / 100)
        
        if signal == 'BUY':
            stop_loss = max(atr_stop, pct_stop)  # Use tighter stop
        else:  # SELL
            atr_stop = current_price + (atr * 1.5)
            pct_stop = current_price * (1 + risk_pct / 100)
            stop_loss = min(atr_stop, pct_stop)  # Use tighter stop
        
        return round(stop_loss, 2)


# Usage example
if __name__ == "__main__":
    from data.market_data_collector import MarketDataCollector
    
    collector = MarketDataCollector()
    df = collector.get_ohlcv("BTC", "1h", limit=100)
    
    if df is not None:
        calculator = TargetPriceCalculator()
        
        # Calculate target for BUY signal with 65% confidence
        target = calculator.calculate_target(df, 'BUY', 65)
        
        if target and target['target_price']:
            print(f"\n═══ TARGET PRICE ═══")
            print(f"Signal: BUY")
            print(f"Current Price: ${target['current_price']:,.2f}")
            print(f"Target {target['target_type']}: ${target['target_price']:,.2f}")
            print(f"Move: {target['pct_move']:.2f}%")
            print(f"ATR: ${target['atr']:,.2f}")
