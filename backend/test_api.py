"""
Simple API Tester
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(endpoint):
    url = f"{BASE_URL}{endpoint}"
    print(f"Testing {url}...")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response Sample:")
            print(json.dumps(data, indent=2)[:500] + "...")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

if __name__ == "__main__":
    endpoints = [
        "/api/coins",
        "/api/market-data/BTC/1h",
        "/api/prediction/BTC/1h"
    ]
    
    results = []
    for ep in endpoints:
        results.append(test_endpoint(ep))
        print("-" * 30)
    
    if all(results):
        print("🚀 API VERIFICATION SUCCESSFUL!")
    else:
        print("⚠️ API VERIFICATION FAILED")
