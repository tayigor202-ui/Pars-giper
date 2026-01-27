import requests
import json

# Тест API с сессией (как браузер)
session = requests.Session()

# 1. Логин
login_url = "http://localhost:3455/login"
login_data = {
    "username": "admin",
    "password": "admin"
}

print("=== Шаг 1: Логин ===")
response = session.post(login_url, data=login_data)
print(f"Статус: {response.status_code}")
print(f"Редирект на: {response.url}")

# 2. Получаем текущий конфиг
print("\n=== Шаг 2: Получаем текущий конфиг ===")
response = session.get("http://localhost:3455/api/config")
print(f"Статус: {response.status_code}")
if response.status_code == 200:
    config = response.json()
    print(f"OZON URL: {config.get('ozon_spreadsheet_url', 'НЕТ')[:80]}...")
    print(f"WB URL: {config.get('wb_spreadsheet_url', 'НЕТ')[:80]}...")
else:
    print(f"Ошибка: {response.text}")

# 3. Сохраняем новый WB URL
print("\n=== Шаг 3: Сохраняем новый WB URL ===")
new_wb_url = "https://docs.google.com/spreadsheets/d/TEST_FROM_SCRIPT/export?format=csv"
response = session.post(
    "http://localhost:3455/api/config",
    json={"wb_spreadsheet_url": new_wb_url},
    headers={"Content-Type": "application/json"}
)
print(f"Статус: {response.status_code}")
print(f"Ответ: {response.text}")

# 4. Проверяем, что сохранилось
print("\n=== Шаг 4: Проверяем config.json ===")
with open('config.json', 'r') as f:
    config = json.load(f)
    print(f"WB URL в файле: {config.get('wb_spreadsheet_url')}")
    
if config.get('wb_spreadsheet_url') == new_wb_url:
    print("\n✅ УСПЕХ! URL сохранился!")
else:
    print("\n❌ ОШИБКА! URL не изменился!")
