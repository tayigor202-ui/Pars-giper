def test_production_extract():
    import os, time, json, random
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    import psycopg2
    from dotenv import load_dotenv
    import re
    
    load_dotenv()
    DB_URL=f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    CHROME_PATH=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    API_ENDPOINT = 'https://www.ozon.ru/api/composer-api.bx/page/json/v2'

    def clean_price(price_str):
        if not price_str: return None
        cleaned = re.sub(r'[^\d]', '', str(price_str))
        return int(cleaned) if cleaned else None

    # Importing extract_prices logic from the updated file
    from ozon_parser_production_final import extract_prices, save_batch_to_db
    
    options = uc.ChromeOptions()
    options.binary_location = CHROME_PATH
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    print("[TEST] Starting browser...")
    driver = uc.Chrome(options=options)
    
    test_skus = ['1076148283', '33069284'] # OOS item and In Stock item
    batch = []
    
    try:
        for sku in test_skus:
            print(f"[TEST] Processing {sku}...")
            driver.get(f"https://www.ozon.ru/product/{sku}/")
            res = extract_prices(driver, sku, "TEST")
            res['sku'] = sku
            res['competitor_name'] = 'TEST_RUN'
            batch.append(res)
            
        print("[TEST] Saving to DB...")
        saved = save_batch_to_db(batch)
        print(f"[TEST] Saved {saved} items.")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_production_extract()
