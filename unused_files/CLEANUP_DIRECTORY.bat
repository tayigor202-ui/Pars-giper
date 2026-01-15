@echo off
chcp 65001 >nul
echo ========================================
echo   ОЧИСТКА ДИРЕКТОРИИ ПАРСЕРА ОТ МУСОРА
echo ========================================
echo.
echo ВНИМАНИЕ: Этот скрипт удалит ВСЕ ненужные файлы!
echo Рабочий парсер НЕ будет затронут.
echo.
echo Будут сохранены ТОЛЬКО:
echo - ozon_parser_production_final.py
echo - .env
echo - proxies_mango_rotating.txt
echo - start_3proxy.bat
echo - proxies/auth_forwarder.py
echo - requirements_pars.txt
echo.
pause
echo.
echo Начинаю очистку...
echo.

REM Удаление старых парсеров Python
echo [1/10] Удаление старых парсеров...
del /Q "Pars*.py" 2>nul
del /Q "Ozon*.py" 2>nul
del /Q "WB.py" 2>nul
del /Q "*_parser*.py" 2>nul
del /Q "ozon_parser_production_final.py.backup" 2>nul

REM Сохраняем рабочий парсер (восстанавливаем если удалили)
echo [ЗАЩИТА] Проверка рабочего парсера...
if not exist "ozon_parser_production_final.py" (
    echo ОШИБКА: Рабочий парсер был удален! Остановка.
    pause
    exit /b 1
)

REM Удаление тестовых скриптов
echo [2/10] Удаление тестовых скриптов...
del /Q "test_*.py" 2>nul
del /Q "*_test.py" 2>nul

REM Удаление вспомогательных скриптов
echo [3/10] Удаление вспомогательных скриптов...
del /Q "advanced_*.py" 2>nul
del /Q "aggressive_*.py" 2>nul
del /Q "human_*.py" 2>nul
del /Q "ultra_*.py" 2>nul
del /Q "session_*.py" 2>nul
del /Q "sync_*.py" 2>nul
del /Q "playwright_*.py" 2>nul
del /Q "visible_*.py" 2>nul
del /Q "simple_*.py" 2>nul
del /Q "parallel_*.py" 2>nul
del /Q "final_parser*.py" 2>nul
del /Q "working_*.py" 2>nul
del /Q "run_*.py" 2>nul
del /Q "api_server.py" 2>nul
del /Q "browser_profiles*.py" 2>nul
del /Q "check_*.py" 2>nul
del /Q "clean_*.py" 2>nul
del /Q "convert_*.py" 2>nul
del /Q "db_init.py" 2>nul
del /Q "driver_manager.py" 2>nul
del /Q "exel.py" 2>nul
del /Q "export_*.py" 2>nul
del /Q "generate_*.py" 2>nul
del /Q "init_db.py" 2>nul
del /Q "install_*.py" 2>nul
del /Q "local_proxy*.py" 2>nul
del /Q "proxy_auth_extension.py" 2>nul
del /Q "setup_*.py" 2>nul
del /Q "start_with_browsers.py" 2>nul
del /Q "tg*.py" 2>nul
del /Q "update_*.py" 2>nul
del /Q "verify_*.py" 2>nul
del /Q "xls_*.py" 2>nul
del /Q "ym_*.py" 2>nul

REM Удаление debug HTML файлов
echo [4/10] Удаление debug HTML файлов...
del /Q "debug_*.html" 2>nul
del /Q "debug_*.csv" 2>nul

REM Удаление логов
echo [5/10] Удаление логов...
del /Q "*.log" 2>nul
del /Q "chrome_log_*.txt" 2>nul
del /Q "parser_*.log" 2>nul
del /Q "parser_*.txt" 2>nul
del /Q "parser_*.err" 2>nul
del /Q "parser_*.out" 2>nul
del /Q "output.txt" 2>nul
del /Q "test_output.txt" 2>nul

REM Удаление результатов парсинга
echo [6/10] Удаление старых результатов...
del /Q "*.json" 2>nul
del /Q "*.xlsx" 2>nul
del /Q "products.txt" 2>nul

REM Удаление документации
echo [7/10] Удаление документации...
del /Q "*.md" 2>nul
del /Q "*.txt" 2>nul

REM Сохраняем важные файлы (восстанавливаем если удалили)
echo [ЗАЩИТА] Проверка важных файлов...
if not exist "proxies_mango_rotating.txt" (
    echo ОШИБКА: Конфигурация прокси была удалена!
    pause
    exit /b 1
)

REM Удаление bat файлов (кроме рабочих)
echo [8/10] Удаление лишних bat файлов...
del /Q "CHECK_*.bat" 2>nul
del /Q "CLEANUP_DB.bat" 2>nul
del /Q "INSTALL_*.bat" 2>nul
del /Q "ParserOzonKerher.bat" 2>nul
del /Q "SEND_*.bat" 2>nul
del /Q "START_PARSER*.bat" 2>nul
del /Q "START_SIMPLE.bat" 2>nul
del /Q "TEST_*.bat" 2>nul
del /Q "start_playwright_parser.bat" 2>nul

REM Удаление старых прокси конфигураций
echo [9/10] Удаление старых прокси конфигураций...
del /Q "proxies_http.txt" 2>nul
del /Q "proxies_mango.txt" 2>nul
del /Q "proxies_mango_converted.txt" 2>nul
del /Q "3proxy.cfg" 2>nul
del /Q "3proxy.log.*" 2>nul

REM Удаление DLL файлов 3proxy
echo [10/10] Удаление DLL файлов...
del /Q "*.dll" 2>nul
del /Q "*.exe" 2>nul

REM Удаление директорий
echo.
echo Удаление директорий...
rmdir /S /Q "__pycache__" 2>nul
rmdir /S /Q ".venv" 2>nul
rmdir /S /Q ".vscode" 2>nul
rmdir /S /Q "137" 2>nul
rmdir /S /Q "ParserOzon" 2>nul
rmdir /S /Q "ParserOzon_Production" 2>nul
rmdir /S /Q "ParserYM" 2>nul
rmdir /S /Q "browser_profiles" 2>nul
rmdir /S /Q "db" 2>nul
rmdir /S /Q "debug_html_antibot" 2>nul
rmdir /S /Q "dev" 2>nul
rmdir /S /Q "error_logs" 2>nul
rmdir /S /Q "legacy" 2>nul
rmdir /S /Q "local_proxy" 2>nul
rmdir /S /Q "logs" 2>nul
rmdir /S /Q "output" 2>nul
rmdir /S /Q "p3" 2>nul
rmdir /S /Q "prod" 2>nul
rmdir /S /Q "project_structure" 2>nul
rmdir /S /Q "proxy_auth_extension" 2>nul
rmdir /S /Q "proxy_extension" 2>nul
rmdir /S /Q "tmp_proxy_ext" 2>nul
rmdir /S /Q "tools" 2>nul

echo.
echo ========================================
echo   ОЧИСТКА ЗАВЕРШЕНА!
echo ========================================
echo.
echo Сохранены только рабочие файлы:
dir /B "ozon_parser_production_final.py" 2>nul
dir /B ".env" 2>nul
dir /B "proxies_mango_rotating.txt" 2>nul
dir /B "start_3proxy.bat" 2>nul
dir /B "proxies\auth_forwarder.py" 2>nul
dir /B "requirements_pars.txt" 2>nul
echo.
pause
