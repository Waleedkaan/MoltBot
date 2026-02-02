"""
Probability Combiner
Combines signals from strategies, ML, and news into final prediction
"""
from typing import Dict
from config import settings
import structlog

logger = structlog.get_logger()


class ProbabilityCombiner:
    """Combines signals from multiple sources with weighted scoring"""
    
    def __init__(
        self,
        strategy_weight: float = None,
        ml_weight: float = None,
        news_weight: float = None
    ):
        """
        Initialize probability combiner
        
        Args:
            strategy_weight: Weight for strategy signals (default 40%)
            ml_weight: Weight for ML predictions (default 35%)
            news_weight: Weight for news sentiment (default 25%)
        """
        self.strategy_weight = strategy_weight or settings.STRATEGY_WEIGHT
        self.ml_weight = ml_weight or settings.ML_WEIGHT
        self.news_weight = news_weight or settings.NEWS_WEIGHT
        
        # Ensure weights sum to 1
        total_weight = self.strategy_weight + self.ml_weight + self.news_weight
        self.strategy_weight /= total_weight
        self.ml_weight /= total_weight
        self.news_weight /= total_weight
        
        logger.info(
            "ProbabilityCombiner initialized",
            strategy_weight=f"{self.strategy_weight:.2%}",
            ml_weight=f"{self.ml_weight:.2%}",
            news_weight=f"{self.news_weight:.2%}"
        )
    
    def combine(
        self,
        strategy_result: Dict,
        ml_result: Dict,
        news_result: Dict
    ) -> Dict:
        """
        Combine signals from all sources
        
        Args:
            strategy_result: Strategy manager result
            ml_result: ML predictor result
            news_result: News sentiment result
            
        Returns:
            Combined prediction with final signal and confidence
        """
        # Extract signals and confidences
        strategy_signal = strategy_result.get('signal', 'NEUTRAL')
        strategy_confidence = strategy_result.get('avg_confidence', 0)
        
        ml_signal = ml_result.get('signal', 'NEUTRAL')
        ml_confidence = ml_result.get('avg_confidence', 0)
        
        news_signal = news_result.get('signal', 'NEUTRAL')
        news_confidence = news_result.get('confidence', 0)
        
        # Convert signals to numerical scores (-1 to 1)
        # BUY = 1, SELL = -1, NEUTRAL = 0
        signal_map = {'BUY': 1, 'SELL': -1, 'NEUTRAL': 0}
        
        strategy_score = signal_map.get(strategy_signal, 0)
        ml_score = signal_map.get(ml_signal, 0)
        news_score = signal_map.get(news_signal, 0)
        
        # Weight the scores by confidence
        strategy_weighted = strategy_score * (strategy_confidence / 100)
        ml_weighted = ml_score * (ml_confidence / 100)
        news_weighted = news_score * (news_confidence / 100)
        
        # Combine with source weights
        final_score = (
            strategy_weighted * self.strategy_weight +
            ml_weighted * self.ml_weight +
            news_weighted * self.news_weight
        )
        
        # Calculate final confidence (weighted average)
        final_confidence = (
            strategy_confidence * self.strategy_weight +
            ml_confidence * self.ml_weight +
            news_confidence * self.news_weight
        )
        
        # Determine final signal
        if final_score > 0.15:  # Threshold for BUY
            final_signal = 'BUY'
        elif final_score < -0.15:  # Threshold for SELL
            final_signal = 'SELL'
        else:
            final_signal = 'NEUTRAL'
        
        # Boost confidence if all sources agree
        all_buy = (strategy_signal == 'BUY' and ml_signal == 'BUY' and news_signal == 'BUY')
        all_sell = (strategy_signal == 'SELL' and ml_signal == 'SELL' and news_signal == 'SELL')
        
        if all_buy or all_sell:
            final_confidence = min(100, final_confidence + 15)  # +15% for full agreement
            logger.info("All sources agree", signal=final_signal)
        
        # Reduce confidence if sources strongly disagree
        if (strategy_signal == 'BUY' and ml_signal == 'SELL') or \
           (strategy_signal == 'SELL' and ml_signal == 'BUY'):
            final_confidence = max(0, final_confidence - 20)  # -20% for disagreement
            logger.info("Strategy and ML disagree")
        
        result = {
            'final_signal': final_signal,
            'final_confidence': round(final_confidence, 2),
            'final_score': round(final_score, 3),
            'breakdown': {
                'strategy': {
                    'signal': strategy_signal,
                    'confidence': strategy_confidence,
                    'weight': f"{self.strategy_weight:.0%}"
                },
                'ml': {
                    'signal': ml_signal,
                    'confidence': ml_confidence,
                    'weight': f"{self.ml_weight:.0%}"
                },
                'news': {
                    'signal': news_signal,
                    'confidence': news_confidence,
                    'weight': f"{self.news_weight:.0%}"
                }
            }
        }
        
        logger.info(
            "Combined prediction",
            signal=final_signal,
            confidence=final_confidence,
            score=final_score
        )
        
        return result


# Usage example
if __name__ == "__main__":
    combiner = ProbabilityCombiner()
    
    # Example signals
    strategy_result = {'signal': 'BUY', 'avg_confidence': 65}
    ml_result = {'signal': 'BUY', 'avg_confidence': 58}
    news_result = {'signal': 'NEUTRAL', 'confidence': 45}
    
    combined = combiner.combine(strategy_result, ml_result, news_result)
    
    print(f"\n═══ COMBINED PREDICTION ═══")
    print(f"Final Signal: {combined['final_signal']}")
    print(f"Final Confidence: {combined['final_confidence']}%")
    print(f"\nBreakdown:")
    for source, data in combined['breakdown'].items():
        print(f"  {source.upper():10s} → {data['signal']:8s} ({data['confidence']:.1f}%) | Weight: {data['weight']}")
