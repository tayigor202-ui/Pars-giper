import os, sys, time, random, json
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# Configuration
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROXY = "p2.mangoproxy.com:2333:xq85fh3lasn-zone-cis-region-ru:pq89ifo8re"

def get_cookies():
    proxy_parts = PROXY.split(':')
    proxy_host, proxy_port, proxy_user, proxy_pass = proxy_parts[0], proxy_parts[1], proxy_parts[2], proxy_parts[3]
    
    unique_id = "cookie_fetcher"
    profile = f"C:\\Temp\\chrome_profiles\\ozon\\tmp_{unique_id}"
    if os.path.exists(profile):
        import shutil
        shutil.rmtree(profile, ignore_errors=True)
    Path(profile).mkdir(parents=True, exist_ok=True)
    
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile}")
    options.add_argument(f"--proxy-server=http://{proxy_host}:{proxy_port}")
    options.add_argument("--lang=ru-RU")
    # Non-headless for maximum trust
    options.add_argument("--window-position=2000,2000")
    
    print("[INIT] Starting browser (Visible Mode) to fetch FULL cookies...")
    try:
        driver = uc.Chrome(options=options, browser_executable_path=CHROME_PATH)
        
        print("[W0] Navigating to Ozon Home...")
        driver.get("https://www.ozon.ru")
        time.sleep(15)
        
        if "доступ ограничен" in driver.title.lower():
            print("[WARN] Block detected, trying search...")
            driver.get("https://www.ozon.ru/search/?text=iphone")
            time.sleep(15)
            
        print("[CDP] Requesting all cookies...")
        cookies = driver.execute_cdp_cmd('Network.getCookies', {})['cookies']
        
        print("\n" + "="*50)
        print(" FULL CDP COOKIES FOUND ")
        print("="*50)
        print(json.dumps(cookies, indent=2))
        print("="*50 + "\n")
        
        with open("fresh_cookies_full.json", "w", encoding='utf-8') as f:
            json.dump(cookies, f, indent=2)
        print("[OK] Full cookies saved to fresh_cookies_full.json")
        
        driver.quit()
    except Exception as e:
        print(f"[ERROR] Failed to fetch cookies: {e}")

if __name__ == "__main__":
    get_cookies()
