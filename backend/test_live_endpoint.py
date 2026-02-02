import requests
import json

def test_live_data():
    url = "http://127.0.0.1:8001/api/market-data/BTC/1s?limit=100&include_indicators=true"
    print(f"Testing URL: {url}")
    try:
        r = requests.get(url)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Candles received: {len(data['data'])}")
            if len(data['data']) > 0:
                first_candle = data['data'][0]
                indicators = ['rsi', 'ema_fast', 'ema_slow', 'bollinger_upper', 'bollinger_lower']
                print("\nIndicators check:")
                for ind in indicators:
                    val = first_candle.get(ind)
                    print(f"  - {ind}: {val} (type: {type(val)})")
        else:
            print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_live_data()
