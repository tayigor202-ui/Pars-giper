import requests
import os

def test_direct():
    print("Testing DIRECT connection to Wildberries...")
    try:
        url = "https://www.wildberries.ru/__internal/u-card/cards/v4/detail"
        params = {"nm": "504869177"}
        headers = {
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
             "Accept": "*/*"
        }
        res = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text[:200]}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_direct()
