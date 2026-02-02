"""
Strategy Manager
Orchestrates all trading strategies and combines signals
"""
from typing import Dict, List
import pandas as pd
from strategies.rsi_strategy import RSIStrategy
from strategies.ema_crossover import EMACrossoverStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bollinger_bands import BollingerBandsStrategy
from strategies.volume_spike import VolumeSpikeStrategy
from strategies.support_resistance import SupportResistanceStrategy
import structlog

logger = structlog.get_logger()


class StrategyManager:
    """Manages and combines multiple trading strategies"""
    
    def __init__(self, enabled_strategies: Dict[str, bool] = None):
        """
        Initialize strategy manager
        
        Args:
            enabled_strategies: Dict of strategy_name -> enabled (default all True)
        """
        # Initialize all strategies
        self.strategies = {
            'rsi': RSIStrategy(),
            'ema_crossover': EMACrossoverStrategy(),
            'macd': MACDStrategy(),
            'bollinger': BollingerBandsStrategy(),
            'volume_spike': VolumeSpikeStrategy(),
            'support_resistance': SupportResistanceStrategy()
        }
        
        # Set enabled strategies
        if enabled_strategies is None:
            self.enabled_strategies = {name: True for name in self.strategies.keys()}
        else:
            self.enabled_strategies = enabled_strategies
        
        logger.info("StrategyManager initialized", strategies=list(self.strategies.keys()))
    
    def calculate_all(self, df: pd.DataFrame) -> Dict:
        """
        Calculate signals from all enabled strategies
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Combined strategy results
        """
        results = []
        
        # Calculate each enabled strategy
        for name, strategy in self.strategies.items():
            if self.enabled_strategies.get(name, True):
                try:
                    result = strategy.calculate(df)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in strategy {name}", error=str(e))
        
        # Combine results
        combined = self._combine_strategies(results)
        
        logger.info(
            "All strategies calculated",
            total=len(results),
            signal=combined['signal'],
            confidence=combined['avg_confidence']
        )
        
        return combined
    
    def _combine_strategies(self, results: List[Dict]) -> Dict:
        """
        Combine strategy signals into aggregated result
        
        Args:
            results: List of strategy results
            
        Returns:
            Combined result with overall signal and confidence
        """
        if not results:
            return {
                'signal': 'NEUTRAL',
                'avg_confidence': 0,
                'strategies': [],
                'buy_count': 0,
                'sell_count': 0,
                'neutral_count': 0
            }
        
        # Count signals
        buy_count = sum(1 for r in results if r['signal'] == 'BUY')
        sell_count = sum(1 for r in results if r['signal'] == 'SELL')
        neutral_count = sum(1 for r in results if r['signal'] == 'NEUTRAL')
        
        # Weighted average confidence
        total_confidence = sum(r['confidence'] for r in results)
        avg_confidence = total_confidence / len(results) if results else 0
        
        # Determine overall signal
        if buy_count > sell_count and buy_count > neutral_count:
            signal = 'BUY'
            # Higher confidence if more strategies agree
            agreement_boost = (buy_count / len(results)) * 20
            avg_confidence = min(100, avg_confidence + agreement_boost)
        elif sell_count > buy_count and sell_count > neutral_count:
            signal = 'SELL'
            agreement_boost = (sell_count / len(results)) * 20
            avg_confidence = min(100, avg_confidence + agreement_boost)
        else:
            signal = 'NEUTRAL'
            # Lower confidence when strategies disagree
            max_count = max(buy_count, sell_count, neutral_count)
            disagreement_penalty = (1 - max_count / len(results)) * 30
            avg_confidence = max(0, avg_confidence - disagreement_penalty)
        
        return {
            'signal': signal,
            'avg_confidence': round(avg_confidence, 2),
            'strategies': results,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'neutral_count': neutral_count,
            'total_strategies': len(results)
        }
    
    def set_enabled_strategies(self, enabled: Dict[str, bool]):
        """
        Update enabled strategies
        
        Args:
            enabled: Dict of strategy_name -> enabled
        """
        self.enabled_strategies.update(enabled)
        logger.info("Updated enabled strategies", enabled=self.enabled_strategies)
    
    def get_strategy_list(self) -> List[str]:
        """Get list of all available strategies"""
        return list(self.strategies.keys())


# Usage example
if __name__ == "__main__":
    from data.market_data_collector import MarketDataCollector
    
    collector = MarketDataCollector()
    df = collector.get_ohlcv("BTC", "1h", limit=100)
    
    if df is not None:
        manager = StrategyManager()
        combined = manager.calculate_all(df)
        
        print(f"\n═══ COMBINED STRATEGY RESULT ═══")
        print(f"Signal: {combined['signal']}")
        print(f"Confidence: {combined['avg_confidence']}%")
        print(f"BUY: {combined['buy_count']} | SELL: {combined['sell_count']} | NEUTRAL: {combined['neutral_count']}")
        print(f"\n─── Individual Strategies ───")
        for strategy in combined['strategies']:
            print(f"  {strategy['strategy']:20s} → {strategy['signal']:8s} ({strategy['confidence']:.1f}%)")
