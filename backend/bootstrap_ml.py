"""
Bootstrap ML Models
"""
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml.model_trainer import MLModelTrainer

def bootstrap():
    print("Starting ML Model Bootstrapping...")
    trainer = MLModelTrainer(model_dir="./models")
    
    coins = ["BTC", "ETH", "SOL"]
    timeframe = "1h"
    
    for coin in coins:
        print(f"\n--- Training {coin} {timeframe} ---")
        try:
            results = trainer.train_all_models(coin, timeframe)
            if results:
                print(f"[OK] {coin} training complete.")
                for name, res in results.items():
                    print(f"  - {name}: {res['accuracy']:.2%} accuracy")
            else:
                print(f"[FAIL] {coin} training failed.")
        except Exception as e:
            print(f"[ERROR] Exception during {coin} training: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    bootstrap()
