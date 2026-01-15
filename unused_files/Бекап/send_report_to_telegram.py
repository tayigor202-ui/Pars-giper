import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')

# Последний созданный отчёт
REPORT_FILE = "ozon_prices_report_20251121_210846.xlsx"

def send_to_telegram(filename):
    """Отправка отчёта в Telegram"""
    print(f"[TELEGRAM] 📤 Отправка отчета {filename} в Telegram...")
    
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("[TELEGRAM] ❌ Не указаны TG_BOT_TOKEN или TG_CHAT_ID в .env")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendDocument"
        
        with open(filename, 'rb') as f:
            files = {'document': f}
            data = {
                'chat_id': TG_CHAT_ID,
                'caption': f'📊 Отчёт по ценам Ozon\n\n✅ Файл: {filename}'
            }
            
            print(f"[TG] Sending to Telegram (chat_id: {TG_CHAT_ID})...")
            response = requests.post(url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("[TG] ✅ Report sent successfully")
                    return True
                else:
                    print(f"[TG] ❌ Error: {result}")
                    return False
            else:
                print(f"[TG] ❌ HTTP Error {response.status_code}: {response.text}")
                return False
                
    except FileNotFoundError:
        print(f"[TELEGRAM] ❌ Файл {filename} не найден")
        return False
    except Exception as e:
        print(f"[TELEGRAM] ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ОТПРАВКА ОТЧЁТА В TELEGRAM")
    print("=" * 60)
    
    if send_to_telegram(REPORT_FILE):
        print(f"\n✅ Отчёт {REPORT_FILE} успешно отправлен в Telegram!")
    else:
        print(f"\n❌ Не удалось отправить отчёт {REPORT_FILE}")
