"""
ML Model Trainer
Trains machine learning models for price prediction
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
from typing import Dict, Tuple
from datetime import datetime
from data.historical_loader import HistoricalDataLoader
import structlog

logger = structlog.get_logger()


class MLModelTrainer:
    """Trains ML models for price prediction"""
    
    def __init__(self, model_dir: str = "./models"):
        """
        Initialize ML model trainer
        
        Args:
            model_dir: Directory to save trained models
        """
        self.model_dir = model_dir
        self.loader = HistoricalDataLoader()
        self.scaler = StandardScaler()
        
        # Create model directory
        os.makedirs(model_dir, exist_ok=True)
        
        logger.info("MLModelTrainer initialized", model_dir=model_dir)
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features and target from DataFrame
        
        Args:
            df: DataFrame with OHLCV and indicators
            
        Returns:
            Tuple of (X, y)
        """
        feature_cols = self.loader.get_feature_columns()
        
        # Ensure all columns exist
        available_cols = [col for col in feature_cols if col in df.columns]
        
        X = df[available_cols].values
        y = df['target'].values if 'target' in df.columns else None
        
        # Drop rows with NaN
        if y is not None:
            mask = ~np.isnan(X).any(axis=1) &  ~np.isnan(y)
            X = X[mask]
            y = y[mask]
        
        return X, y
    
    def train_logistic_regression(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        coin: str = "default",
        timeframe: str = "default"
    ) -> Dict:
        """Train Logistic Regression model"""
        try:
            logger.info("Training Logistic Regression...", coin=coin, timeframe=timeframe)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = LogisticRegression(max_iter=1000, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save model
            suffix = f"_{coin}_{timeframe}"
            joblib.dump(model, os.path.join(self.model_dir, f'logistic_regression{suffix}.pkl'))
            joblib.dump(scaler, os.path.join(self.model_dir, f'scaler_lr{suffix}.pkl'))
            
            logger.info("Logistic Regression trained", accuracy=accuracy)
            
            return {
                'model_name': 'logistic_regression',
                'accuracy': accuracy,
                'model': model,
                'scaler': scaler
            }
        
        except Exception as e:
            logger.error("Error training Logistic Regression", error=str(e))
            return None
    
    def train_random_forest(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        coin: str = "default",
        timeframe: str = "default"
    ) -> Dict:
        """Train Random Forest model"""
        try:
            logger.info("Training Random Forest...", coin=coin, timeframe=timeframe)
            
            # Train model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save model
            suffix = f"_{coin}_{timeframe}"
            joblib.dump(model, os.path.join(self.model_dir, f'random_forest{suffix}.pkl'))
            
            logger.info("Random Forest trained", accuracy=accuracy)
            
            return {
                'model_name': 'random_forest',
                'accuracy': accuracy,
                'model': model
            }
        
        except Exception as e:
            logger.error("Error training Random Forest", error=str(e))
            return None
    
    def train_xgboost(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        coin: str = "default",
        timeframe: str = "default"
    ) -> Dict:
        """Train XGBoost model"""
        try:
            logger.info("Training XGBoost...", coin=coin, timeframe=timeframe)
            
            # Train model
            model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save model
            suffix = f"_{coin}_{timeframe}"
            joblib.dump(model, os.path.join(self.model_dir, f'xgboost{suffix}.pkl'))
            
            logger.info("XGBoost trained", accuracy=accuracy)
            
            return {
                'model_name': 'xgboost',
                'accuracy': accuracy,
                'model': model
            }
        
        except Exception as e:
            logger.error("Error training XGBoost", error=str(e))
            return None
    
    def train_all_models(self, coin: str, timeframe: str) -> Dict:
        """
        Train all ML models for a coin/timeframe
        
        Args:
            coin: Coin symbol
            timeframe: Timeframe
            
        Returns:
            Dictionary of training results
        """
        logger.info("Training all models", coin=coin, timeframe=timeframe)
        
        # Load and prepare data
        train_df, test_df = self.loader.prepare_ml_dataset(coin, timeframe)
        
        if train_df is None or test_df is None:
            logger.error("Failed to prepare dataset")
            return None
        
        X_train, y_train = self.prepare_features(train_df)
        X_test, y_test = self.prepare_features(test_df)
        
        logger.info(
            "Dataset prepared",
            train_samples=len(X_train),
            test_samples=len(X_test),
            features=X_train.shape[1]
        )
        
        # Train models
        results = {}
        
        lr_result = self.train_logistic_regression(X_train, y_train, X_test, y_test, coin, timeframe)
        if lr_result:
            results['logistic_regression'] = lr_result
        
        rf_result = self.train_random_forest(X_train, y_train, X_test, y_test, coin, timeframe)
        if rf_result:
            results['random_forest'] = rf_result
        
        xgb_result = self.train_xgboost(X_train, y_train, X_test, y_test, coin, timeframe)
        if xgb_result:
            results['xgboost'] = xgb_result
        
        # Save metadata
        metadata = {
            'coin': coin,
            'timeframe': timeframe,
            'trained_at': datetime.now().isoformat(),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'models': {
                name: {'accuracy': res['accuracy']}
                for name, res in results.items()
            }
        }
        
        joblib.dump(metadata, os.path.join(self.model_dir, f'metadata_{coin}_{timeframe}.pkl'))
        
        logger.info("All models trained", models=len(results))
        return results


# Usage example
if __name__ == "__main__":
    trainer = MLModelTrainer()
    
    # Train models for BTC 1h
    results = trainer.train_all_models("BTC", "1h")
    
    if results:
        print(f"\n=== MODEL TRAINING RESULTS ===")
        for name, result in results.items():
            print(f"{name:20s} -> Accuracy: {result['accuracy']:.2%}")
