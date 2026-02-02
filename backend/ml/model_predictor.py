"""
ML Model Predictor
Loads trained models and makes predictions
"""
import pandas as pd
import numpy as np
import joblib
import os
from typing import Dict, List, Optional
from data.historical_loader import HistoricalDataLoader
import structlog

logger = structlog.get_logger()


class MLModelPredictor:
    """Makes predictions using trained ML models"""
    
    def __init__(self, model_dir: str = "./models"):
        """
        Initialize ML model predictor
        
        Args:
            model_dir: Directory containing trained models
        """
        self.model_dir = model_dir
        self.loader = HistoricalDataLoader()
        self.models = {}
        self.scalers = {}
        
        logger.info("MLModelPredictor initialized")
    
    def load_model(self, model_name: str, coin: str = None, timeframe: str = None) -> bool:
        """
        Load a trained model
        
        Args:
            model_name: Name of model to load (e.g., 'logistic_regression')
            coin: Optional coin symbol
            timeframe: Optional timeframe
            
        Returns:
            True if successful
        """
        try:
            suffix = f"_{coin}_{timeframe}" if coin and timeframe else ""
            key = f"{model_name}{suffix}"
            
            # Cache check
            if key in self.models:
                return True
                
            model_path = os.path.join(self.model_dir, f'{model_name}{suffix}.pkl')
            
            # Fallback to generic if specific not found
            if not os.path.exists(model_path):
                model_path = os.path.join(self.model_dir, f'{model_name}.pkl')
            
            if not os.path.exists(model_path):
                logger.warning(f"Model not found: {model_name}{suffix}")
                return False
            
            # Load and cache
            self.models[key] = joblib.load(model_path)
            
            # Load scaler if exists
            scaler_name = 'scaler_lr' if model_name == 'logistic_regression' else f'scaler_{model_name}'
            scaler_path = os.path.join(self.model_dir, f'{scaler_name}{suffix}.pkl')
            
            if not os.path.exists(scaler_path):
                scaler_path = os.path.join(self.model_dir, f'{scaler_name}.pkl')
                
            if os.path.exists(scaler_path):
                self.scalers[key] = joblib.load(scaler_path)
            
            logger.info(f"Loaded model: {key}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading model {model_name}{suffix}", error=str(e))
            return False
    
    def load_all_models(self, coin: str = None, timeframe: str = None):
        """Load all available models for a specific coin/timeframe"""
        model_names = ['logistic_regression', 'random_forest', 'xgboost']
        
        for name in model_names:
            self.load_model(name, coin, timeframe)
        
        logger.info(f"Loaded {len(self.models)} models")
    
    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Prepare features from DataFrame
        
        Args:
            df: DataFrame with OHLCV and indicators
            
        Returns:
            Feature array
        """
        feature_cols = self.loader.get_feature_columns()
        available_cols = [col for col in feature_cols if col in df.columns]
        
        X = df[available_cols].values
        
        # Get last row only (for real-time prediction)
        if len(X.shape) > 1:
            X = X[-1:, :]
        
        return X
    
    def predict_single_model(
        self,
        model_key: str,
        features: np.ndarray
    ) -> Optional[Dict]:
        """
        Make prediction with a single model
        
        Args:
            model_key: Key of model in self.models
            features: Feature array
            
        Returns:
            Prediction result
        """
        if model_key not in self.models:
            logger.warning(f"Model not loaded: {model_key}")
            return None
        
        try:
            model = self.models[model_key]
            
            # Scale features if needed
            if model_key in self.scalers:
                features = self.scalers[model_key].transform(features)
            
            # Predict
            prediction = model.predict(features)[0]  # 0 = DOWN, 1 = UP
            
            # Get probability if available
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(features)[0]
                confidence = max(proba) * 100  # Confidence in %
            else:
                confidence = 60  # Default confidence
            
            # Determine signal
            signal = "BUY" if prediction == 1 else "SELL"
            
            result = {
                'model': model_key,
                'signal': signal,
                'confidence': round(confidence, 2),
                'prediction': int(prediction)
            }
            
            logger.debug(f"Prediction from {model_key}", **result)
            return result
        
        except Exception as e:
            logger.error(f"Error predicting with {model_key}", error=str(e))
            return None
    
    def predict_all(self, df: pd.DataFrame, coin: str = None, timeframe: str = None) -> Dict:
        """
        Make predictions with all available models
        
        Args:
            df: DataFrame with OHLCV and indicators
            coin: Optional coin symbol
            timeframe: Optional timeframe
            
        Returns:
            Combined predictions
        """
        # Load specific/generic models for this request
        self.load_all_models(coin, timeframe)
        
        # Prepare features
        features = self.prepare_features(df)
        
        # Get predictions from models that match this coin/timeframe (or are generic)
        predictions = []
        suffix = f"_{coin}_{timeframe}" if coin and timeframe else ""
        
        for key in self.models.keys():
            # Only use models that match the requested suffix or are generic
            if key.endswith(suffix) or "_" not in key:
                pred = self.predict_single_model(key, features)
                if pred:
                    predictions.append(pred)
        
        # Combine predictions
        combined = self._combine_predictions(predictions)
        
        logger.info(
            "ML predictions complete",
            coin=coin,
            models=len(predictions),
            signal=combined['signal'],
            confidence=combined['avg_confidence']
        )
        
        return combined
    
    def _combine_predictions(self, predictions: List[Dict]) -> Dict:
        """
        Combine predictions from multiple models
        
        Args:
            predictions: List of prediction dicts
            
        Returns:
            Combined prediction
        """
        if not predictions:
            return {
                'signal': 'NEUTRAL',
                'avg_confidence': 0,
                'models': [],
                'buy_count': 0,
                'sell_count': 0
            }
        
        # Count signals
        buy_count = sum(1 for p in predictions if p['signal'] == 'BUY')
        sell_count = sum(1 for p in predictions if p['signal'] == 'SELL')
        
        # Weighted average confidence
        total_confidence = sum(p['confidence'] for p in predictions)
        avg_confidence = total_confidence / len(predictions) if predictions else 0
        
        # Determine overall signal
        if buy_count > sell_count:
            signal = 'BUY'
            # Boost confidence with agreement
            agreement_boost = (buy_count / len(predictions)) * 15
            avg_confidence = min(100, avg_confidence + agreement_boost)
        elif sell_count > buy_count:
            signal = 'SELL'
            agreement_boost = (sell_count / len(predictions)) * 15
            avg_confidence = min(100, avg_confidence + agreement_boost)
        else:
            signal = 'NEUTRAL'
            # Penalize for disagreement
            avg_confidence = max(20, avg_confidence - 20)
        
        return {
            'signal': signal,
            'avg_confidence': round(avg_confidence, 2),
            'models': predictions,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'total_models': len(predictions)
        }


# Usage example
if __name__ == "__main__":
    from data.market_data_collector import MarketDataCollector
    from data.historical_loader import HistoricalDataLoader
    
    # Get data
    collector = MarketDataCollector()
    loader = HistoricalDataLoader()
    
    df = collector.get_ohlcv("BTC", "1h", limit=100)
    df = loader.add_technical_indicators(df)
    
    # Predict
    predictor = MLModelPredictor()
    predictions = predictor.predict_all(df)
    
    print(f"\n═══ ML PREDICTIONS ═══")
    print(f"Signal: {predictions['signal']}")
    print(f"Confidence: {predictions['avg_confidence']}%")
    print(f"BUY: {predictions['buy_count']} | SELL: {predictions['sell_count']}")
    print(f"\n─── Individual Models ───")
    for pred in predictions['models']:
        print(f"  {pred['model']:20s} → {pred['signal']:8s} ({pred['confidence']:.1f}%)")
