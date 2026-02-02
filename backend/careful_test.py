import asyncio
import websockets
import json
import requests
import time
import pandas as pd
import numpy as np

# Configuration
API_BASE = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/market"

class MoltBotTester:
    def __init__(self):
        self.results = []

    def log_test(self, name, status, details=""):
        self.results.append({"name": name, "status": status, "details": details})
        icon = "[OK]" if status == "PASS" else "[FAIL]"
        print(f"{icon} {name}: {details}")

    async def test_rest_api_market_data(self):
        print("\n--- Testing REST API Market Data ---")
        try:
            # Test 1h with indicators
            url = f"{API_BASE}/api/market-data/BTC/1h?limit=100&include_indicators=true"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                candles = data.get('data', [])
                if candles and 'ema_fast' in candles[0] and 'bollinger_upper' in candles[0]:
                    self.log_test("REST Market Data (1h)", "PASS", f"Received {len(candles)} candles with indicators")
                else:
                    self.log_test("REST Market Data (1h)", "FAIL", "Missing indicators in response")
            else:
                self.log_test("REST Market Data (1h)", "FAIL", f"Status {r.status_code}")

            # Test 1s timeframe
            url = f"{API_BASE}/api/market-data/BTC/1s?limit=10"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                self.log_test("REST Market Data (1s)", "PASS", "Successfully fetched granular 1s data")
            else:
                self.log_test("REST Market Data (1s)", "FAIL", f"Status {r.status_code}")
        except Exception as e:
            self.log_test("REST API Tests", "FAIL", str(e))

    async def test_websocket_stream(self):
        print("\n--- Testing WebSocket Real-Time Stream ---")
        try:
            async with websockets.connect(WS_URL) as websocket:
                # 1. Test Subscription
                sub_msg = {"coin": "ETH", "timeframe": "1m"}
                await websocket.send(json.dumps(sub_msg))
                
                # 2. Wait for full_update
                response = await asyncio.wait_for(websocket.recv(), timeout=15)
                data = json.loads(response)
                
                if data.get('type') == 'full_update' and data.get('coin') == 'ETH':
                    details = f"Received live update for {data['coin']} {data['timeframe']}"
                    prediction = data.get('prediction', {})
                    market_data = data.get('market_data', [])
                    
                    if prediction and market_data:
                        self.log_test("WebSocket Stream", "PASS", f"{details} (Data points: {len(market_data)})")
                    else:
                        self.log_test("WebSocket Stream", "FAIL", "Incomplete payload received")
                else:
                    self.log_test("WebSocket Stream", "FAIL", f"Unexpected response type: {data.get('type')}")
        except Exception as e:
            self.log_test("WebSocket Tests", "FAIL", str(e))

    async def test_indicator_validity(self):
        print("\n--- Testing Indicator Validity ---")
        try:
            url = f"{API_BASE}/api/market-data/BTC/1h?limit=100&include_indicators=true"
            data = requests.get(url).json()['data']
            df = pd.DataFrame(data)
            
            # Check for NaNs in processed data (should be None/null in JSON)
            # Since our serialization converts NaN to None, we check for presence
            total = len(df)
            valid_rsi = df['rsi'].count()
            valid_ema = df['ema_fast'].count()
            
            if valid_rsi > 0 and valid_ema > 0:
                self.log_test("Indicator Calculation", "PASS", f"Valid indicators mapped: RSI({valid_rsi}/{total}), EMA({valid_ema}/{total})")
            else:
                self.log_test("Indicator Calculation", "FAIL", "Indicators returned all nulls")
        except Exception as e:
            self.log_test("Indicator Tests", "FAIL", str(e))

    async def run_all(self):
        print("Starting MoltBot Careful Verification Suite...")
        await self.test_rest_api_market_data()
        await self.test_indicator_validity()
        await self.test_websocket_stream()
        
        print("\n" + "="*40)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        print(f"CARE ME TEST RESULTS:")
        print(f"  TOTAL:  {len(self.results)}")
        print(f"  PASSED: {passed}")
        print(f"  FAILED: {failed}")
        
        if failed > 0:
            print("\nFailures:")
            for r in self.results:
                if r['status'] == 'FAIL':
                    print(f"  - {r['name']}: {r['details']}")
        print("="*40)

if __name__ == "__main__":
    tester = MoltBotTester()
    asyncio.run(tester.run_all())
