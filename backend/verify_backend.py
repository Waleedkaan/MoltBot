"""
Verification Script for MoltBot Backend
Tests imports, database, and core logic modules
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    print("\n--- Phase 1: Importing Modules ---")
    try:
        from data.market_data_collector import MarketDataCollector
        from data.historical_loader import HistoricalDataLoader
        from data.news_sentiment_fetcher import NewsSentimentFetcher
        from strategies.strategy_manager import StrategyManager
        from ml.model_predictor import MLModelPredictor
        from prediction.prediction_engine import PredictionEngine
        from models import SessionLocal, init_db
        print("[OK] All modules imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database():
    print("\n--- Phase 2: Database Connectivity ---")
    try:
        from models import SessionLocal, MarketData
        db = SessionLocal()
        # Try a simple query
        count = db.query(MarketData).count()
        print(f"[OK] Database connected. MarketData count: {count}")
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Database test failed: {str(e)}")
        return False

def test_market_data():
    print("\n--- Phase 3: Market Data Collection ---")
    try:
        from data.market_data_collector import MarketDataCollector
        collector = MarketDataCollector()
        # Test fetching BTC 1h data
        df = collector.get_ohlcv("BTC", "1h", limit=5)
        if df is not None and not df.empty:
            print(f"[OK] Successfully fetched data for BTC. Latest price: {df['close'].iloc[-1]}")
            return True
        else:
            print("[FAIL] Failed to fetch market data (Empty DataFrame)")
            return False
    except Exception as e:
        print(f"[FAIL] Market data test failed: {str(e)}")
        return False

def test_strategies():
    print("\n--- Phase 4: Strategy Calculation ---")
    try:
        from strategies.strategy_manager import StrategyManager
        # Create mock data
        data = {
            'timestamp': pd.date_range(start='2024-01-01', periods=100, freq='h'),
            'open': np.random.uniform(40000, 41000, 100),
            'high': np.random.uniform(41000, 42000, 100),
            'low': np.random.uniform(39000, 40000, 100),
            'close': np.random.uniform(40000, 41000, 100),
            'volume': np.random.uniform(100, 1000, 100)
        }
        df = pd.DataFrame(data)
        
        # We need technical indicators for strategies
        from data.historical_loader import HistoricalDataLoader
        loader = HistoricalDataLoader()
        df = loader.add_technical_indicators(df)
        
        manager = StrategyManager()
        result = manager.calculate_all(df)
        print(f"[OK] Strategy Manager result: {result['signal']} ({result['avg_confidence']:.2f}%)")
        return True
    except Exception as e:
        print(f"[FAIL] Strategy test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_prediction_engine():
    print("\n--- Phase 5: Prediction Engine ---")
    try:
        from prediction.prediction_engine import PredictionEngine
        engine = PredictionEngine()
        # This will use real market data but we can use a small limit
        prediction = engine.predict("BTC", "1h", min_confidence=10)
        print(f"[OK] Prediction Engine generated: {prediction['final']['signal']} ({prediction['final']['confidence']:.2f}%)")
        return True
    except Exception as e:
        print(f"[FAIL] Prediction Engine test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== MoltBot Backend Verification ===")
    
    steps = [
        test_imports,
        test_database,
        test_market_data,
        test_strategies,
        test_prediction_engine
    ]
    
    results = []
    for step in steps:
        results.append(step())
        
    print("\n" + "="*35)
    print(f"Final Result: {sum(results)}/{len(steps)} phases passed")
    if all(results):
        print("ALL SYSTEMS GO!")
        sys.exit(0)
    else:
        print("SOME SYSTEMS FAILED")
        sys.exit(1)
