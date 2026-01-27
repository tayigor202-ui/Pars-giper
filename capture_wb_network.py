import undetected_chromedriver as uc
import json
import time

sku = "504869177"
url = f"https://www.wildberries.ru/catalog/{sku}/detail.aspx"

options = uc.ChromeOptions()
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
# options.add_argument("--headless") # Disable headless to solve antibot

print(f"Opening {url} to capture network...")
driver = uc.Chrome(options=options)
driver.execute_cdp_cmd("Network.enable", {})
try:
    driver.get(url)
    time.sleep(10) # Wait for all API calls
    
    logs = driver.get_log("performance")
    for entry in logs:
        msg = json.loads(entry["message"])["message"]
        if "params" in msg and "request" in msg["params"]:
            req_url = msg["params"]["request"]["url"]
            req_id = msg["params"].get("requestId")
            if ("wb.ru" in req_url or "wildberries.ru" in req_url) and ("detail" in req_url or "product" in req_url):
                print(f"\nFOUND API CALL: {req_url}")
                # Note: Body might not be available for all requests immediately
                try:
                    body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": req_id})
                    print(f"  Response Body: {body['body'][:1000]}")
                except:
                    pass
except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()
