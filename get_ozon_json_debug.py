import json
import time
import os
from curl_cffi.requests import Session as CffiSession
import undetected_chromedriver as uc

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROXY_SERVER = "127.0.0.1:8118"
API_ENDPOINT = "https://www.ozon.ru/api/composer-api.bx/page/json/v2"

def get_debug_json(sku="1067025156"):
    options = uc.ChromeOptions()
    options.binary_location = CHROME_PATH
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=ru-RU")
    
    driver = None
    try:
        print(f"[DEBUG] Warming up for SKU {sku}...")
        driver = uc.Chrome(options=options, browser_executable_path=CHROME_PATH)
        driver.get(f"https://www.ozon.ru/product/{sku}/")
        time.sleep(10)
        
        cookies_dict = {c['name']: c['value'] for c in driver.get_cookies()}
        user_agent = driver.execute_script("return navigator.userAgent;")
        driver.quit()
        
        session = CffiSession(impersonate="chrome124")
        headers = {
            "authority": "www.ozon.ru",
            "accept": "application/json",
            "user-agent": user_agent,
            "x-o3-app-name": "entrypoint-api",
            "referer": f"https://www.ozon.ru/product/{sku}/"
        }
        
        response = session.get(API_ENDPOINT, params={"url": f"/product/{sku}/"}, headers=headers, cookies=cookies_dict)
        
        if response.status_code == 200:
            data = response.json()
            with open(f"debug_api_{sku}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[DEBUG] JSON saved to debug_api_{sku}.json")
        else:
            print(f"[DEBUG] Error {response.status_code}")
            
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")

def analyze_json(sku="1401683802"):
    with open(f"debug_api_{sku}.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    widget_states = data.get("widgetStates", {})
    
    # Search for webPrice widget
    for key, value in widget_states.items():
        if "webPrice" in key:
            print(f"Found webPrice widget: {key}")
            state = json.loads(value)
            print(f"Full state for {sku}: {json.dumps(state, indent=2, ensure_ascii=False)}")
            break

if __name__ == "__main__":
    analyze_json("1401683802")
