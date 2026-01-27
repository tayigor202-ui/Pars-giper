import json

# Тестируем прямое сохранение в config.json
CONFIG_FILE = 'config.json'

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# Загружаем текущий конфиг
current = load_config()
print("=== Текущий config.json ===")
print(f"OZON: {current.get('ozon_spreadsheet_url')}")
print(f"WB: {current.get('wb_spreadsheet_url')}")

# Обновляем WB URL
print("\n=== Обновляем WB URL ===")
current['wb_spreadsheet_url'] = "https://docs.google.com/spreadsheets/d/TEST_NEW_WB_URL/export?format=csv"
save_config(current)
print("✅ Сохранено!")

# Проверяем
updated = load_config()
print("\n=== Проверка после сохранения ===")
print(f"OZON: {updated.get('ozon_spreadsheet_url')}")
print(f"WB: {updated.get('wb_spreadsheet_url')}")

if updated['wb_spreadsheet_url'] == "https://docs.google.com/spreadsheets/d/TEST_NEW_WB_URL/export?format=csv":
    print("\n✅ УСПЕХ! Функция save_config работает корректно!")
else:
    print("\n❌ ОШИБКА! URL не обновился!")
