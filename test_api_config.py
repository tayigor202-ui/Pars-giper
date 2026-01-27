import requests
import json

# Тестируем сохранение URL для WB
url = "http://localhost:3455/api/config"
payload = {
    "wb_spreadsheet_url": "https://docs.google.com/spreadsheets/d/TEST_WB_ID/export?format=csv"
}

print("Отправляем тестовый запрос на сохранение URL WB...")
print(f"Payload: {payload}")

try:
    response = requests.post(url, json=payload, auth=('admin', 'admin'))
    print(f"\nОтвет сервера: {response.status_code}")
    print(f"Содержимое: {response.json()}")
    
    # Проверяем, что сохранилось
    print("\n--- Проверка config.json ---")
    with open('config.json', 'r') as f:
        config = json.load(f)
        print(f"OZON URL: {config.get('ozon_spreadsheet_url')}")
        print(f"WB URL: {config.get('wb_spreadsheet_url')}")
        
except Exception as e:
    print(f"Ошибка: {e}")
