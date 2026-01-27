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

def check_postgresql():
    """Check if PostgreSQL is installed"""
    print_header("ПРОВЕРКА POSTGRESQL")
    
    # Try to find psql
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print_success(f"PostgreSQL установлен: {result.stdout.strip()}")
            return True
    except:
        pass
    
    print_warning("PostgreSQL не найден в PATH")
    print_info("Пожалуйста, установите PostgreSQL:")
    print_info("  Windows: https://www.postgresql.org/download/windows/")
    print_info("  Linux: sudo apt-get install postgresql postgresql-contrib")
    print_info("  macOS: brew install postgresql")
    
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

def create_env_file():
    """Create .env file with user input"""
    print_header("НАСТРОЙКА .ENV ФАЙЛА")
    
    if os.path.exists('.env'):
        response = input(".env файл уже существует. Перезаписать? (y/n): ").lower()
        if response != 'y':
            print_info("Пропускаем создание .env")
            return True
    
    print_info("Введите параметры подключения к PostgreSQL:")
    
    env_data = {}
    
    # Database settings
    env_data['DB_HOST'] = input("  DB_HOST [localhost]: ").strip() or 'localhost'
    env_data['DB_PORT'] = input("  DB_PORT [5432]: ").strip() or '5432'
    env_data['DB_NAME'] = input("  DB_NAME [ozon_parser]: ").strip() or 'ozon_parser'
    env_data['DB_USER'] = input("  DB_USER [postgres]: ").strip() or 'postgres'
    env_data['DB_PASS'] = getpass.getpass("  DB_PASS: ").strip()
    
    # Flask settings
    print_info("\nНастройки Flask:")
    env_data['FLASK_SECRET_KEY'] = input("  FLASK_SECRET_KEY [auto-generated]: ").strip()
    if not env_data['FLASK_SECRET_KEY']:
        import secrets
        env_data['FLASK_SECRET_KEY'] = secrets.token_hex(32)
        print_info(f"  Сгенерирован ключ: {env_data['FLASK_SECRET_KEY'][:20]}...")
    
    # Telegram settings (optional)
    print_info("\nНастройки Telegram (можно оставить пустыми и настроить позже через UI):")
    env_data['TG_BOT_TOKEN'] = input("  TG_BOT_TOKEN [пусто]: ").strip() or ''
    env_data['TG_CHAT_ID'] = input("  TG_CHAT_ID [пусто]: ").strip() or ''
    
    # Write .env file
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            for key, value in env_data.items():
                f.write(f"{key}={value}\n")
        
        print_success(".env файл создан")
        return True
    except Exception as e:
        print_error(f"Ошибка создания .env: {e}")
        return False

def create_database():
    """Create PostgreSQL database"""
    print_header("СОЗДАНИЕ БАЗЫ ДАННЫХ")
    
    # Load .env
    from dotenv import load_dotenv
    load_dotenv()
    
    db_name = os.getenv('DB_NAME', 'ozon_parser')
    db_user = os.getenv('DB_USER', 'postgres')
    db_pass = os.getenv('DB_PASS', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    
    print_info(f"Создание базы данных: {db_name}")
    
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Connect to postgres database to create new database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_pass,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if exists:
            print_warning(f"База данных {db_name} уже существует")
            response = input("Пересоздать базу данных? (y/n): ").lower()
            if response == 'y':
                cursor.execute(f"DROP DATABASE {db_name}")
                print_info(f"База данных {db_name} удалена")
                cursor.execute(f"CREATE DATABASE {db_name}")
                print_success(f"База данных {db_name} создана")
            else:
                print_info("Используем существующую базу данных")
        else:
            cursor.execute(f"CREATE DATABASE {db_name}")
            print_success(f"База данных {db_name} создана")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Ошибка создания базы данных: {e}")
        print_warning("Попробуйте создать базу данных вручную:")
        print_info(f"  psql -U {db_user} -c 'CREATE DATABASE {db_name};'")
        return False

def create_database_tables():
    """Create all database tables"""
    print_header("СОЗДАНИЕ ТАБЛИЦ БАЗЫ ДАННЫХ")
    
    # Check if setup_database_and_users.py exists
    if os.path.exists('setup_database_and_users.py'):
        print_info("Запуск setup_database_and_users.py...")
        success = run_command(
            f"{sys.executable} setup_database_and_users.py",
            "Создание таблиц и пользователей"
        )
        if success:
            print_success("Таблицы и пользователи созданы")
            return True
    
    print_error("Файл setup_database_and_users.py не найден")
    return False

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
    print_header("УСТАНОВКА OZON/WB PARSER")
    print_info("Этот скрипт автоматически настроит проект\n")
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Check PostgreSQL
    if not check_postgresql():
        print_error("PostgreSQL требуется для работы проекта")
        sys.exit(1)
    
    # Step 3: Install Python dependencies
    if not install_python_dependencies():
        print_error("Не удалось установить зависимости")
        sys.exit(1)
    
    # Step 4: Create .env file
    if not create_env_file():
        print_error("Не удалось создать .env файл")
        sys.exit(1)
    
    # Step 5: Create database
    if not create_database():
        print_warning("База данных не создана, но можно продолжить")
    
    # Step 6: Create database tables
    if not create_database_tables():
        print_warning("Таблицы не созданы, создайте их вручную")
    
    # Step 7: Create config.json
    create_config_json()
    
    # Final instructions
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
