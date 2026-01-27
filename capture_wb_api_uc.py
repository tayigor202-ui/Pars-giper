import os, sys, time, json, re
import undetected_chromedriver as uc
from dotenv import load_dotenv

load_dotenv()

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def capture_api_logs_detailed():
    options = uc.ChromeOptions()
    options.binary_location = CHROME_PATH
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Using mobile proxy to match production environment
    proxy_host = os.getenv('MOBILE_PROXY_HOST')
    proxy_port = os.getenv('MOBILE_PROXY_PORT')
    proxy_user = os.getenv('MOBILE_PROXY_USERNAME')
    proxy_pass = os.getenv('MOBILE_PROXY_PASSWORD')
    
    # We won't use the extension for this quick test, just try direct or standard auth if possible
    # Actually, better to run without proxy first to see the URL names, then apply proxy
    
    driver = None
    try:
        print("[CAPTURE] Starting browser...")
        driver = uc.Chrome(options=options, browser_executable_path=CHROME_PATH)
        
        sku = "504869177"
        url = f"https://www.wildberries.ru/catalog/{sku}/detail.aspx"
        
        print(f"[CAPTURE] Opening {url}...")
        driver.get(url)
        time.sleep(15) 
        
        print("[CAPTURE] Extracting logs and session data...")
        logs = driver.get_log('performance')
        cookies = driver.get_cookies()
        ua = driver.execute_script("return navigator.userAgent")
        
        session_data = {
            'cookies': {c['name']: c['value'] for c in cookies},
            'ua': ua
        }
        with open("session_data.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=4)
        
        print(f"[CAPTURE] Saved session data to session_data.json")
        
        # Filtering for known WB data domains
        data_apis = [u for u in all_urls if any(x in u for x in ['wb.ru', 'wildberries.ru']) and 'detail' in u.lower()]
        print("\n[CANDIDATES]:")
        for u in set(data_apis):
            print(f" - {u}")
                
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    capture_api_logs_detailed()
