"""
Prediction Engine
Main orchestrator that combines all prediction modules
"""
import pandas as pd
from typing import Dict
from data.market_data_collector import MarketDataCollector
from data.historical_loader import HistoricalDataLoader
from data.news_sentiment_fetcher import NewsSentimentFetcher
from strategies.strategy_manager import StrategyManager
from ml.model_predictor import MLModelPredictor
from prediction.probability_combiner import ProbabilityCombiner
from prediction.target_price_calculator import TargetPriceCalculator
from models import Prediction, SessionLocal
from datetime import datetime
import structlog

logger = structlog.get_logger()


class PredictionEngine:
    """Main prediction engine that orchestrates all components"""
    
    def __init__(self, enabled_strategies: Dict[str, bool] = None):
        """
        Initialize prediction engine
        
        Args:
            enabled_strategies: Dict of enabled strategies
        """
        self.market_collector = MarketDataCollector()
        self.historical_loader = HistoricalDataLoader()
        self.news_fetcher = NewsSentimentFetcher()
        self.strategy_manager = StrategyManager(enabled_strategies)
        self.ml_predictor = MLModelPredictor()
        self.probability_combiner = ProbabilityCombiner()
        self.target_calculator = TargetPriceCalculator()
        
        logger.info("PredictionEngine initialized")
    
    def predict(
        self,
        coin: str,
        timeframe: str,
        min_confidence: int = 60
    ) -> Dict:
        """
        Generate complete prediction for a coin/timeframe
        
        Args:
            coin: Coin symbol (e.g., 'BTC')
            timeframe: Timeframe (15m, 1h, 4h, 1d)
            min_confidence: Minimum confidence threshold
            
        Returns:
            Complete prediction dictionary
        """
        logger.info("Starting prediction", coin=coin, timeframe=timeframe)
        
        try:
            # 1. Get market data
            df = self.market_collector.get_ohlcv(coin, timeframe, limit=100)
            
            if df is None:
                logger.error("Failed to fetch market data")
                return self._empty_prediction(coin, timeframe)
            
            # 2. Add technical indicators
            df = self.historical_loader.add_technical_indicators(df)
            
            current_price = df['close'].iloc[-1]
            
            # 3. Get strategy signals
            strategy_result = self.strategy_manager.calculate_all(df)
            
            # 4. Get ML predictions
            ml_result = self.ml_predictor.predict_all(df, coin, timeframe)
            
            # 5. Get news sentiment
            news_result = self.news_fetcher.get_aggregated_sentiment(coin, hours=24)
            if news_result is None:
                news_result = {'signal': 'NEUTRAL', 'confidence': 0}
            
            # 6. Combine all signals
            combined = self.probability_combiner.combine(
                strategy_result,
                ml_result,
                news_result
            )
            
            final_signal = combined['final_signal']
            final_confidence = combined['final_confidence']
            
            # 7. Calculate target price
            target_result = self.target_calculator.calculate_target(
                df,
                final_signal,
                final_confidence,
                min_confidence
            )
            
            # 8. Build complete prediction
            prediction = {
                'coin': coin,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'current_price': round(current_price, 2),
                
                # Strategy results
                'strategy': {
                    'signal': strategy_result['signal'],
                    'confidence': strategy_result['avg_confidence'],
                    'details': strategy_result['strategies']
                },
                
                # ML results
                'ml': {
                    'signal': ml_result['signal'],
                    'confidence': ml_result['avg_confidence'],
                    'details': ml_result['models']
                },
                
                # News results
                'news': {
                    'signal': news_result['signal'],
                    'confidence': news_result['confidence']
                },
                
                # Final prediction
                'final': {
                    'signal': final_signal,
                    'confidence': final_confidence,
                    'target_price': target_result.get('target_price') if target_result else None,
                    'target_type': target_result.get('target_type') if target_result else None,
                    'meets_threshold': final_confidence >= min_confidence
                },
                
                # Breakdown
                'breakdown': combined['breakdown']
            }
            
            # 10. Clean prediction for serialization
            prediction = self._clean_for_serialization(prediction)
            
            # 11. Save prediction to database
            self._save_prediction(prediction)
            
            logger.info(
                "Prediction complete",
                coin=coin,
                signal=final_signal,
                confidence=final_confidence,
                target=prediction['final'].get('target_price')
            )
            
            return prediction
        
        except Exception as e:
            logger.error("Error generating prediction", coin=coin, error=str(e))
            import traceback
            logger.error(traceback.format_exc())
            return self._empty_prediction(coin, timeframe, error=str(e))
    
    def _clean_for_serialization(self, obj):
        """Recursively convert numpy/pandas types to python types for JSON serialization"""
        import numpy as np
        
        if isinstance(obj, dict):
            return {str(k): self._clean_for_serialization(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple, np.ndarray)):
            return [self._clean_for_serialization(i) for i in obj]
        elif isinstance(obj, pd.Series):
            return self._clean_for_serialization(obj.to_dict())
        elif isinstance(obj, pd.DataFrame):
            return self._clean_for_serialization(obj.to_dict('records'))
        elif hasattr(obj, 'item') and callable(getattr(obj, 'item')):
            return obj.item()
        type_str = str(type(obj))
        if 'Timestamp' in type_str or 'datetime' in type_str:
            return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
        elif 'numpy.int64' in type_str:
            return int(obj)
        elif 'numpy.float64' in type_str:
            return float(obj)
        import math
        if isinstance(obj, (float, int)) and (math.isnan(obj) or math.isinf(obj)):
            return None
        elif not isinstance(obj, (dict, list, str, bool, int, float)) and pd.isna(obj):
            return None
        return obj

    def _empty_prediction(self, coin: str, timeframe: str, error: str = None) -> Dict:
        """Return empty prediction on error"""
        return {
            'coin': coin,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'current_price': 0,
            'final': {
                'signal': 'NEUTRAL',
                'confidence': 0,
                'target_price': None,
                'target_type': None,
                'meets_threshold': False
            },
            'error': error
        }
    
    def _save_prediction(self, prediction: Dict):
        """Save prediction to database"""
        try:
            db = SessionLocal()
            
            pred_record = Prediction(
                coin=prediction['coin'],
                timeframe=prediction['timeframe'],
                current_price=prediction['current_price'],
                
                strategy_signal=prediction['strategy']['signal'],
                strategy_confidence=prediction['strategy']['confidence'],
                strategy_details=prediction['strategy']['details'],
                
                ml_signal=prediction['ml']['signal'],
                ml_confidence=prediction['ml']['confidence'],
                ml_details=prediction['ml']['details'],
                
                news_signal=prediction['news']['signal'],
                news_confidence=prediction['news']['confidence'],
                
                final_signal=prediction['final']['signal'],
                final_confidence=prediction['final']['confidence'],
                target_price=prediction['final']['target_price'],
                target_type=prediction['final']['target_type']
            )
            
            db.add(pred_record)
            db.commit()
            logger.info("Prediction saved to database")
        
        except Exception as e:
            logger.error("Error saving prediction", error=str(e))
            db.rollback()
        finally:
            db.close()


# Usage example
if __name__ == "__main__":
    engine = PredictionEngine()
    
    # Get prediction for BTC 1h
    prediction = engine.predict("BTC", "1h", min_confidence=60)
    
    print("-" * 50)
    print(f"  MOLTBOT PREDICTION - {prediction['coin']} ({prediction['timeframe']})")
    print("-" * 50)
    print(f"\nCurrent Price: ${prediction['current_price']:,.2f}")
    print(f"\n[ Signal Breakdown ]")
    print(f"| Strategy:  {prediction['strategy']['signal']:8s}  {prediction['strategy']['confidence']:5.1f}%  |")
    print(f"| ML:        {prediction['ml']['signal']:8s}  {prediction['ml']['confidence']:5.1f}%  |")
    print(f"| News:      {prediction['news']['signal']:8s}  {prediction['news']['confidence']:5.1f}%  |")
    print(f"------------------------------------------")
    print(f"\nFINAL: {prediction['final']['signal']} ({prediction['final']['confidence']:.1f}%)")
    
    if prediction['final']['target_price']:
        print(f"   Target {prediction['final']['target_type']}: ${prediction['final']['target_price']:,.2f}")
