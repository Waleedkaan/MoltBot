"""
Debug Prediction Logic
"""
import sys
import os
import traceback
import pandas as pd

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prediction.prediction_engine import PredictionEngine

def debug():
    print("Initializing PredictionEngine...")
    try:
        engine = PredictionEngine()
        print("Initialised. Running predict('BTC', '1h')...")
        
        prediction = engine.predict('BTC', '1h', min_confidence=10)
        
        print("\n--- PREDICTION RESULT ---")
        import json
        # Try to serialize to see if it's a serialization error
        try:
            print(json.dumps(prediction, indent=2))
        except TypeError as te:
            print(f"SERIALIZATION ERROR: {str(te)}")
            # Try to find which key is failing
            for k, v in prediction.items():
                try:
                    json.dumps(v)
                except:
                    print(f"  Failing key: {k} (type: {type(v)})")
                    if isinstance(v, dict):
                        for k2, v2 in v.items():
                            try:
                                json.dumps(v2)
                            except:
                                print(f"    Failing sub-key: {k2} (type: {type(v2)})")
                                
    except Exception as e:
        print("\n--- EXCEPTION CAUGHT ---")
        traceback.print_exc()

if __name__ == "__main__":
    debug()
