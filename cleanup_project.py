#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для удаления отладочных и временных файлов из проекта
"""

import os
import sys

# Файлы для удаления (отладочные, тестовые, временные)
FILES_TO_DELETE = [
    # Debug scripts
    'debug_api_response.py',
    'debug_db_content.py',
    'debug_proxy_creds.py',
    'debug_report_data.py',
    'debug_wb_db.py',
    'debug_wb_sheet.py',
    
    # Check/analyze scripts (диагностические)
    'analyze_price_json.py',
    'analyze_report.py',
    'analyze_wb_html.py',
    'check_all_prices.py',
    'check_both_tables.py',
    'check_competitors.py',
    'check_current_db_state.py',
    'check_database.py',
    'check_db_stats.py',
    'check_db_time.py',
    'check_db_types.py',
    'check_db_users.py',
    'check_distribution.py',
    'check_names.py',
    'check_null.py',
    'check_orphans.py',
    'check_others.py',
    'check_ozon.py',
    'check_sellers.py',
    'check_sku_content.py',
    'check_sp_counts.py',
    'check_sp_grouping.py',
    'check_sp_stats.py',
    'check_table_structure.py',
    'check_violations.py',
    'check_wb_data.py',
    'check_wb_detailed.py',
    
    # Capture/fetch scripts
    'capture_wb_api_uc.py',
    'capture_wb_network.py',
    'fetch_ozon_cookies.py',
    'get_ozon_json_debug.py',
    'get_wb_sku.py',
    
    # Clean/fix scripts (одноразовые)
    'add_column.py',
    'add_sp_code.py',
    'clean_database.py',
    'clean_invalid_names.py',
    'clean_null_sellers.py',
    'cleanup_test.py',
    'clear_database.py',
    'delete_null.py',
    'delete_test_data.py',
    'fix_competitor_names.py',
    'fix_indent.py',
    'fix_tail.py',
    'fix_wb_table.py',
    
    # Diagnose scripts
    'diagnose_csv.py',
    'diagnose_missing_names.py',
    
    # Find/verify scripts
    'find_skus_in_db.py',
    'verify_skus.py',
    'verify_wb_sql.py',
    
    # Load/import test scripts
    'load_all_products_from_sheet.py',
    'load_test_products.py',
    
    # Old/deprecated parsers
    'ozon_api_parser.py',
    'ozon_api_parser_reliable.py',
    'ozon_hybrid_batch.py',
    'ozon_hybrid_batch_fast.py',
    'ozon_hybrid_parser.py',
    'parser_runner.py',
    
    # Test scripts
    'test_api_config.py',
    'test_api_minimal.py',
    'test_api_with_session.py',
    'test_internal_api.py',
    'test_name_fill.py',
    'test_name_fix.py',
    'test_new_report_format.py',
    'test_pivot.py',
    'test_production_logic.py',
    'test_proxy_api.py',
    'test_proxy_api_cffi.py',
    'test_proxy_auth.py',
    'test_regex.py',
    'test_report_layout.py',
    'test_save_config.py',
    'test_sheet.py',
    'test_warmup.py',
    'test_wb_cffi.py',
    'test_wb_endpoints.py',
    'test_wb_exhaustive.py',
    'test_wb_final.py',
    'test_wb_fixed.py',
    
    # Temporary/one-time scripts
    'create_admin.py',  # Заменён на create_admin_user.py
    'fix_admin.py',  # Одноразовый
    'fix_admin_permissions.py',  # Одноразовый
    'init_users.py',  # Одноразовый
    'migrate_platform.py',  # Одноразовый
    'run_report_only.py',  # Временный
    'setup_wb_table.py',  # Одноразовый
    'truncate_database.py',  # Опасный, лучше удалить
    'update_wb_url.py',  # Одноразовый
    
    # SQL files (если есть одноразовые)
    'check_users.sql',
]

# Файлы которые ОСТАВЛЯЕМ (важные для проекта)
KEEP_FILES = [
    # Core application
    'web_app.py',
    'scheduler.py',
    'user_management.py',
    
    # Production parsers
    'ozon_parser_production_final.py',
    'wb_parser_production.py',
    'wb_silent_parser.py',
    
    # Reporting
    'generate_report.py',
    'wb_reporting.py',
    'send_report_to_telegram.py',
    
    # Import scripts
    'import_from_sheets.py',
    'import_from_wb_sheets.py',
    'import_wb_from_sheets.py',
    
    # Setup/Installation
    'setup.py',
    'setup_database_and_users.py',
    'create_admin_user.py',
    
    # Utilities (полезные)
    'check_db_stats_full.py',  # Полезная статистика
    'check_users.py',  # Управление пользователями
    'clear_all_data.py',  # Полезная утилита
    'test_db_connection.py',  # Диагностика подключения
    'test_telegram.py',  # Диагностика Telegram
]

def main():
    print("=" * 70)
    print("ОЧИСТКА ПРОЕКТА ОТ ОТЛАДОЧНЫХ СКРИПТОВ")
    print("=" * 70)
    print()
    
    # Проверяем, что мы в правильной директории
    if not os.path.exists('web_app.py'):
        print("❌ Ошибка: запустите скрипт из корневой директории проекта")
        sys.exit(1)
    
    deleted_count = 0
    not_found_count = 0
    
    print(f"Файлов для удаления: {len(FILES_TO_DELETE)}")
    print()
    
    # Показываем список файлов
    print("Файлы для удаления:")
    for filename in FILES_TO_DELETE:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"  - {filename} ({size} bytes)")
        else:
            print(f"  - {filename} (не найден)")
    
    print()
    response = input("Продолжить удаление? (yes/no): ").lower()
    
    if response != 'yes':
        print("Отменено пользователем")
        sys.exit(0)
    
    print()
    print("Удаление файлов...")
    print()
    
    for filename in FILES_TO_DELETE:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"✓ Удалён: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"✗ Ошибка при удалении {filename}: {e}")
        else:
            not_found_count += 1
    
    print()
    print("=" * 70)
    print(f"✅ Удалено файлов: {deleted_count}")
    print(f"⚠️  Не найдено: {not_found_count}")
    print("=" * 70)
    print()
    print("Проект очищен!")
    print()
    print("Важные файлы сохранены:")
    for filename in KEEP_FILES:
        if os.path.exists(filename):
            print(f"  ✓ {filename}")

if __name__ == "__main__":
    main()
