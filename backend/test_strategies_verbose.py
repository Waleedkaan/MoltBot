"""
Verbose Test for Strategies
"""
import sys
import os
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.historical_loader import HistoricalDataLoader
from strategies.strategy_manager import StrategyManager

def run_test():
    print("Initializing components...")
    loader = HistoricalDataLoader()
    manager = StrategyManager()
    
    print("Generating mock data...")
    data = {
        'timestamp': pd.date_range(start='2024-01-01', periods=200, freq='h'),
        'open': np.random.uniform(40000, 41000, 200),
        'high': np.random.uniform(41000, 42000, 200),
        'low': np.random.uniform(39000, 40000, 200),
        'close': np.random.uniform(40000, 41000, 200),
        'volume': np.random.uniform(100, 1000, 200)
    }
    df = pd.DataFrame(data)
    
    print("Adding technical indicators...")
    df_with_inds = loader.add_technical_indicators(df.copy())
    print(f"Columns after indicators: {df_with_inds.columns.tolist()}")
    print(f"Number of rows after dropna: {len(df_with_inds)}")
    
    if len(df_with_inds) == 0:
        print("ERROR: Resulting DataFrame is empty! Indicators might be all NaN.")
        return
        
    print("Calculating strategies...")
    result = manager.calculate_all(df_with_inds)
    print(f"Final Combined Signal: {result['signal']}")
    print(f"Final Combined Confidence: {result['avg_confidence']}%")
    
    print("\nIndividual Strategy Results:")
    for s in result['strategies']:
        print(f"  {s['strategy']}: {s['signal']} (Conf: {s['confidence']}%)")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
