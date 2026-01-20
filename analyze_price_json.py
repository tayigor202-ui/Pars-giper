import json
import re

def clean_price(price_str):
    if not price_str:
        return None
    # Remove currency symbol, non-breaking spaces, etc.
    return re.sub(r'[^\d]', '', price_str)

def analyze_json():
    with open("debug_api_1067025156.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    widget_states = data.get("widgetStates", {})
    
    # Search for webPrice widget
    for key, value in widget_states.items():
        if "webPrice" in key:
            print(f"Found webPrice widget: {key}")
            state = json.loads(value)
            print(f"Keys in webPrice state: {list(state.keys())}")
            print(f"Full state: {json.dumps(state, indent=2, ensure_ascii=False)}")
            break
            
    print(f"Extracted Prices: {price_data}")

if __name__ == "__main__":
    analyze_json()
