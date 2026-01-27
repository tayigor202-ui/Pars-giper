import requests
import json

# Обновляем WB URL через временный эндпоинт
wb_url = "https://docs.google.com/spreadsheets/d/13MFilmBi8yVyB0-IVzJM6oHdZg5aMjx5wySPgv5cEKE/export?format=csv"

print("=== Обновление URL Wildberries ===")
response = requests.post(
    "http://localhost:3455/api/config/force_update",
    json={"wb_spreadsheet_url": wb_url}
)

print(f"Статус: {response.status_code}")
result = response.json()
print(f"Ответ: {result}")

if result.get('status') == 'success':
    print("\n✅ URL успешно обновлён!")
    print(f"WB URL: {result['config']['wb_spreadsheet_url']}")
else:
    print(f"\n❌ Ошибка: {result.get('message')}")
