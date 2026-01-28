#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматическая установка и настройка проекта Ozon/WB Parser
Запуск: python setup.py
"""

import os
import sys
import subprocess
import platform
import json
import getpass
from pathlib import Path

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def run_command(cmd, description, check=True, shell=True):
    """Execute command with nice output"""
    print_info(f"{description}...")
    try:
        result = subprocess.run(cmd, shell=shell, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"{description} - завершено")
            return True
        else:
            print_error(f"{description} - ошибка: {result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        print_error(f"{description} - ошибка: {e.stderr}")
        return False
    except Exception as e:
        print_error(f"{description} - ошибка: {str(e)}")
        return False

def check_python_version():
    """Check Python version >= 3.8"""
    print_header("ПРОВЕРКА PYTHON")
    version = sys.version_info
    print_info(f"Python версия: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error("Требуется Python 3.8 или выше!")
        return False
    
    print_success("Python версия подходит")
    return True

def find_postgresql():
    """Try to find PostgreSQL executable in common paths"""
    # 1. Check PATH
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            return "psql"
    except:
        pass
    
    # 2. Check common Windows paths
    common_paths = [
        r"C:\Program Files\PostgreSQL\*\bin\psql.exe",
        r"C:\Program Files (x86)\PostgreSQL\*\bin\psql.exe"
    ]
    for path_pattern in common_paths:
        matches = glob.glob(path_pattern)
        if matches:
            # Get latest version
            matches.sort(reverse=True)
            return matches[0]
            
    return None

def check_postgresql():
    """Check if PostgreSQL is installed"""
    print_header("ПРОВЕРКА POSTGRESQL")
    
    psql_path = find_postgresql()
    if psql_path:
        print_success(f"PostgreSQL найден: {psql_path}")
        return True
    
    print_warning("PostgreSQL не найден в PATH или стандартных папках")
    print_info("Проект требует PostgreSQL для хранения данных.")
    print_info("Пожалуйста, установите его с официального сайта: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads")
    
    if os.environ.get('NON_INTERACTIVE'):
        return False
        
    response = input("\nPostgreSQL уже установлен? (y/n): ").lower()
    return response == 'y'

def install_python_dependencies():
    """Install Python packages from requirements.txt"""
    print_header("УСТАНОВКА PYTHON ЗАВИСИМОСТЕЙ")
    
    if not os.path.exists('requirements.txt'):
        print_error("Файл requirements.txt не найден!")
        return False
    
    # Upgrade pip first
    run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Обновление pip",
        check=False
    )
    
    # Install requirements
    success = run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Установка зависимостей из requirements.txt"
    )
    
    if success:
        print_success("Все Python зависимости установлены")
    
    return success

def create_env_file(interactive=True):
    """Create .env file automatically or with user input"""
    print_header("НАСТРОЙКА .ENV ФАЙЛА")
    
    if os.path.exists('.env') and interactive:
        response = input(".env файл уже существует. Перезаписать? (y/n): ").lower()
        if response != 'y':
            print_info("Пропускаем создание .env")
            return True
    
    env_data = {
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'DB_NAME': 'ozon_parser',
        'DB_USER': 'postgres',
        'DB_PASS': 'postgres' # Default common password
    }
    
    if interactive and not os.environ.get('NON_INTERACTIVE'):
        print_info("Введите параметры (Enter для значений по умолчанию):")
        env_data['DB_HOST'] = input(f"  DB_HOST [{env_data['DB_HOST']}]: ").strip() or env_data['DB_HOST']
        env_data['DB_PORT'] = input(f"  DB_PORT [{env_data['DB_PORT']}]: ").strip() or env_data['DB_PORT']
        env_data['DB_NAME'] = input(f"  DB_NAME [{env_data['DB_NAME']}]: ").strip() or env_data['DB_NAME']
        env_data['DB_USER'] = input(f"  DB_USER [{env_data['DB_USER']}]: ").strip() or env_data['DB_USER']
        env_data['DB_PASS'] = getpass.getpass(f"  DB_PASS (скрыто): ").strip() or env_data['DB_PASS']
    
    # Flask settings
    import secrets
    env_data['FLASK_SECRET_KEY'] = secrets.token_hex(32)
    
    # Write .env file
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write("# === AUTO-GENERATED CONFIG ===\n")
            f.write("# Database Settings\n")
            for key in ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASS']:
                f.write(f"{key}={env_data[key]}\n")
            
            f.write("\n# Flask Settings\n")
            f.write(f"FLASK_SECRET_KEY={env_data['FLASK_SECRET_KEY']}\n")
            
            f.write("\n# Telegram Settings (Configure via UI)\n")
            f.write(f"TG_BOT_TOKEN=\n")
            f.write(f"TG_CHAT_ID=\n")
            
            f.write("\n# Browser Settings\n")
            f.write(f"CHROME_PATH=\n")
        
        print_success(".env файл успешно создан")
        return True
    except Exception as e:
        print_error(f"Ошибка создания .env: {e}")
        return False

# create_database and create_database_tables functions are removed as per instructions
# and replaced by a direct call to setup_database_and_users.py in main().

def create_config_json():
    """Create config.json with default values"""
    print_header("СОЗДАНИЕ CONFIG.JSON")
    
    if os.path.exists('config.json'):
        print_warning("config.json уже существует")
        return True
    
    config = {
        "ozon_spreadsheet_url": "",
        "wb_spreadsheet_url": ""
    }
    
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print_success("config.json создан")
        print_info("Настройте URL Google Sheets через веб-интерфейс")
        return True
    except Exception as e:
        print_error(f"Ошибка создания config.json: {e}")
        return False

def print_final_instructions():
    """Print final instructions"""
    print_header("УСТАНОВКА ЗАВЕРШЕНА!")
    
    print_success("Проект успешно настроен!\n")
    
    print(f"{Colors.BOLD}Следующие шаги:{Colors.ENDC}\n")
    
    print("1. Запустите веб-интерфейс:")
    print(f"   {Colors.OKCYAN}python web_app.py{Colors.ENDC}\n")
    
    print("2. Откройте в браузере:")
    print(f"   {Colors.OKCYAN}http://localhost:3455{Colors.ENDC}\n")
    
    print("3. Войдите с учётными данными:")
    print(f"   Логин: {Colors.OKGREEN}admin{Colors.ENDC}")
    print(f"   Пароль: {Colors.OKGREEN}admin{Colors.ENDC}")
    print(f"   {Colors.WARNING}⚠ Смените пароль после первого входа!{Colors.ENDC}\n")
    
    print("4. Настройте в веб-интерфейсе:")
    print("   • URL Google Sheets (Ozon и Wildberries)")
    print("   • Telegram Bot Token и Chat ID")
    print("   • Расписание парсинга\n")
    
    print("5. Импортируйте данные:")
    print("   • Нажмите 'Импортировать OZON' в настройках")
    print("   • Нажмите 'Импортировать WB' в настройках\n")
    
    print(f"{Colors.BOLD}Полезные команды:{Colors.ENDC}\n")
    print(f"  Запуск парсера Ozon:       {Colors.OKCYAN}python ozon_parser_production_final.py{Colors.ENDC}")
    print(f"  Запуск парсера WB:         {Colors.OKCYAN}python wb_parser_production.py{Colors.ENDC}")
    print(f"  Генерация отчёта Ozon:     {Colors.OKCYAN}python generate_report.py{Colors.ENDC}")
    print(f"  Генерация отчёта WB:       {Colors.OKCYAN}python wb_reporting.py{Colors.ENDC}")
    print(f"  Тест Telegram:             {Colors.OKCYAN}python test_telegram.py{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Документация:{Colors.ENDC}")
    print("  • README.md - основная документация")
    print("  • WEB_README.md - веб-интерфейс")
    print("  • SERVICE_README.md - установка как сервис\n")

def main():
    """Main setup function"""
    interactive = not (len(sys.argv) > 1 and sys.argv[1] == '--silent')
    if not interactive:
        os.environ['NON_INTERACTIVE'] = '1'

    print_header("УСТАНОВКА OZON/WB PARSER")
    print_info("Автоматическая подготовка окружения...\n")
    
    # 1. Check Python
    if not check_python_version():
        sys.exit(1)
    
    # 2. Check PostgreSQL
    check_postgresql() # Don't exit, maybe user knows what they do
    
    # 3. Install dependencies
    if not install_python_dependencies():
        print_error("Критическая ошибка при установке зависимостей")
        # Continue anyway, some might be installed
    
    # 4. Create .env
    create_env_file(interactive=interactive)
    
    # 5. Create Database and Tables
    print_header("ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
    try:
        # Run the direct setup script
        setup_script = os.path.join(os.path.dirname(__file__), 'setup_database_and_users.py')
        if os.path.exists(setup_script):
            subprocess.run([sys.executable, setup_script], check=False)
        else:
            print_error("Файл setup_database_and_users.py не найден. База данных не инициализирована.")
    except Exception as e:
        print_error(f"Ошибка инициализации базы: {e}")
    
    # 6. Create config.json
    create_config_json()
    
    print_final_instructions()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Установка прервана пользователем{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
