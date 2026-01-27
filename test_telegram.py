#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест подключения к Telegram
Проверяет корректность TG_BOT_TOKEN и TG_CHAT_ID
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')

print("="*70)
print("ПРОВЕРКА ПОДКЛЮЧЕНИЯ К TELEGRAM")
print("="*70)

# Проверка наличия переменных
print("\n1. Проверка переменных окружения:")
if TG_BOT_TOKEN:
    print(f"   ✅ TG_BOT_TOKEN: {TG_BOT_TOKEN[:20]}...")
else:
    print("   ❌ TG_BOT_TOKEN не установлен в .env")
    exit(1)

if TG_CHAT_ID:
    print(f"   ✅ TG_CHAT_ID: {TG_CHAT_ID}")
else:
    print("   ❌ TG_CHAT_ID не установлен в .env")
    exit(1)

# Проверка бота
print("\n2. Проверка бота (getMe):")
try:
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/getMe"
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('ok'):
            bot_info = result.get('result', {})
            print(f"   ✅ Бот активен!")
            print(f"      Имя: {bot_info.get('first_name')}")
            print(f"      Username: @{bot_info.get('username')}")
            print(f"      ID: {bot_info.get('id')}")
        else:
            print(f"   ❌ Ошибка: {result}")
            exit(1)
    else:
        print(f"   ❌ HTTP Error {response.status_code}: {response.text}")
        exit(1)
except Exception as e:
    print(f"   ❌ Ошибка подключения: {e}")
    exit(1)

# Проверка чата
print("\n3. Проверка доступа к чату:")
try:
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/getChat"
    params = {'chat_id': TG_CHAT_ID}
    response = requests.get(url, params=params, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('ok'):
            chat_info = result.get('result', {})
            print(f"   ✅ Чат найден!")
            print(f"      Тип: {chat_info.get('type')}")
            print(f"      Название: {chat_info.get('title', 'N/A')}")
            print(f"      ID: {chat_info.get('id')}")
        else:
            print(f"   ❌ Ошибка: {result.get('description')}")
            print("\n   📝 Возможные причины:")
            print("      1. Бот не добавлен в чат")
            print("      2. Неверный CHAT_ID")
            print("      3. Чат был удалён")
            exit(1)
    else:
        print(f"   ❌ HTTP Error {response.status_code}: {response.text}")
        exit(1)
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    exit(1)

# Тестовая отправка сообщения
print("\n4. Тестовая отправка сообщения:")
try:
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': TG_CHAT_ID,
        'text': '🧪 Тестовое сообщение от парсера\n\n✅ Подключение к Telegram работает корректно!'
    }
    response = requests.post(url, data=data, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('ok'):
            print("   ✅ Сообщение отправлено успешно!")
        else:
            print(f"   ❌ Ошибка: {result}")
    else:
        print(f"   ❌ HTTP Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("\n" + "="*70)
print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
print("="*70)
print("\n📌 Telegram настроен корректно и готов к отправке отчётов.")
