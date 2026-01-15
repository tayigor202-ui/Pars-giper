@echo off
chcp 65001 >nul
echo ========================================
echo   БЕЗОПАСНАЯ ОЧИСТКА ДИРЕКТОРИИ
echo ========================================
echo.

REM Удаление конкретных старых парсеров (БЕЗ МАСОК!)
echo [1/8] Удаление старых парсеров...
del /Q "Pars.py" 2>nul
del /Q "Pars_async.py" 2>nul
del /Q "Pars_multi.py" 2>nul
del /Q "Pars_simple.py" 2>nul
del /Q "WB.py" 2>nul
del /Q "Ozon3.py.BROKEN_BACKUP" 2>nul
del /Q "Ozon3.py.bak_20251112_082625" 2>nul
del /Q "advanced_bypass_parser.py" 2>nul
del /Q "advanced_parser_antibot.py" 2>nul
del /Q "aggressive_ozon_parser.py" 2>nul
del /Q "aggressive_retry_parser.py" 2>nul
del /Q "human_behavior_parser_v4.py" 2>nul
del /Q "ozon_cdp_parser.py" 2>nul
del /Q "ozon_fast_parser.py" 2>nul
del /Q "ozon_final_with_extension.py" 2>nul
del /Q "ozon_final_with_local_proxy.py" 2>nul
del /Q "ozon_http_parser.py" 2>nul
del /Q "ozon_parser_final.py" 2>nul
del /Q "ozon_parser_with_seleniumwire.py" 2>nul
del /Q "ozon_simple_parser.py" 2>nul
del /Q "ozon_visible_parser.py" 2>nul
del /Q "parallel_mega_parser.py" 2>nul
del /Q "parser_proxy_auth_correct.py" 2>nul
del /Q "playwright_driver.py" 2>nul
del /Q "playwright_parallel_parser.py" 2>nul
del /Q "playwright_simple_5.py" 2>nul
del /Q "playwright_simple_parser.py" 2>nul
del /Q "session_aware_parser_v3.py" 2>nul
del /Q "simple_parser_5.py" 2>nul
del /Q "sync_parser_v5.py" 2>nul
del /Q "sync_playwright_adapter.py" 2>nul
del /Q "ultra_bypass_parser.py" 2>nul
del /Q "visible_browsers_parser.py" 2>nul
del /Q "visible_parser_final.py" 2>nul
del /Q "visible_parser_with_auth.py" 2>nul
del /Q "working_parser_attach.py" 2>nul
del /Q "final_parser_auto_close.py" 2>nul
del /Q "final_parser_clean.py" 2>nul
del /Q "final_parser_fixed.py" 2>nul
del /Q "final_parser_proxy_auth_fixed.py" 2>nul

REM Удаление тестовых скриптов
echo [2/8] Удаление тестовых скриптов...
for %%f in (test_*.py) do del /Q "%%f" 2>nul

REM Удаление вспомогательных скриптов
echo [3/8] Удаление вспомогательных скриптов...
del /Q "api_server.py" 2>nul
del /Q "browser_profiles.py" 2>nul
del /Q "browser_profiles_manager.py" 2>nul
del /Q "check_browsers.py" 2>nul
del /Q "check_db_cols.py" 2>nul
del /Q "check_db_structure.py" 2>nul
del /Q "check_parallel_results.py" 2>nul
del /Q "check_prices.py" 2>nul
del /Q "check_update_stats.py" 2>nul
del /Q "clean_chrome_profiles.py" 2>nul
del /Q "convert_mango_proxies.py" 2>nul
del /Q "convert_proxies.py" 2>nul
del /Q "db_init.py" 2>nul
del /Q "driver_manager.py" 2>nul
del /Q "exel.py" 2>nul
del /Q "export_all_prices.py" 2>nul
del /Q "export_prices.py" 2>nul
del /Q "generate_mango_proxies.py" 2>nul
del /Q "generate_report_and_send.py" 2>nul
del /Q "init_db.py" 2>nul
del /Q "install_playwright_browsers.py" 2>nul
del /Q "local_proxy_manager.py" 2>nul
del /Q "local_proxy_server.py" 2>nul
del /Q "ozon_price_updater.py" 2>nul
del /Q "proxy_auth_extension.py" 2>nul
del /Q "run_high_perf_system.py" 2>nul
del /Q "run_parser.py" 2>nul
del /Q "run_price.py" 2>nul
del /Q "run_production_parser.py" 2>nul
del /Q "run_production_system.py" 2>nul
del /Q "run_with_proxy.py" 2>nul
del /Q "setup_privoxy.py" 2>nul
del /Q "setup_system_proxy.py" 2>nul
del /Q "start_with_browsers.py" 2>nul
del /Q "tg.py" 2>nul
del /Q "tg_bot.py" 2>nul
del /Q "update_db_from_visible_parser.py" 2>nul
del /Q "update_from_csv.py" 2>nul
del /Q "update_from_google_sheets.py" 2>nul
del /Q "update_prices_with_variation.py" 2>nul
del /Q "verify_proxy_ip.py" 2>nul
del /Q "xls_loader_kerher.py" 2>nul
del /Q "xls_loader_kerher_wb.py" 2>nul
del /Q "ym_products.py" 2>nul

REM Удаление debug HTML файлов
echo [4/8] Удаление debug HTML файлов...
for %%f in (debug_*.html debug_*.csv) do del /Q "%%f" 2>nul

REM Удаление логов
echo [5/8] Удаление логов...
for %%f in (*.log chrome_log_*.txt parser_*.txt parser_*.err parser_*.out) do del /Q "%%f" 2>nul
del /Q "output.txt" 2>nul
del /Q "test_output.txt" 2>nul
del /Q "local_proxy_manager.log" 2>nul
del /Q "3proxy.log.*" 2>nul

REM Удаление результатов парсинга
echo [6/8] Удаление старых результатов...
for %%f in (*.json *.xlsx) do del /Q "%%f" 2>nul
del /Q "products.txt" 2>nul
del /Q "debug_google_sheet.csv" 2>nul

REM Удаление документации
echo [7/8] Удаление документации...
for %%f in (*.md) do del /Q "%%f" 2>nul
for %%f in (00_*.txt 3PROXY_*.txt AGENTS.md ANTI_*.txt ARCHITECTURE_*.txt BROWSER_*.txt CHANGELOG*.txt CHANGES_*.txt CODE_*.txt DELETE_*.txt DOCUMENTATION_*.txt DO_IT_*.txt ERROR_*.txt EXAMPLE_*.txt FILES_*.txt FINAL_*.txt FLOW_*.txt HEADLESS_*.txt HIGH_*.txt IP_*.txt ITERATION_*.txt LOCAL_*.txt MIGRATION_*.txt PARSER_*.txt PLAYWRIGHT_*.txt PRE_*.txt PRODUCTION_*.txt PROJECT_*.txt PROXY_*.txt QUICK_*.txt README_*.txt RELEASE_*.txt SEND_*.txt SESSION_*.txt SETUP_*.txt SOLUTION_*.txt START_*.txt TLDR_*.txt UPDATE_*.txt VERIFICATION_*.txt) do del /Q "%%f" 2>nul

REM Удаление bat файлов (кроме рабочих)
echo [8/8] Удаление лишних bat файлов...
del /Q "CHECK_3PROXY_STATUS.bat" 2>nul
del /Q "CLEANUP_DB.bat" 2>nul
del /Q "INSTALL_3PROXY.bat" 2>nul
del /Q "ParserOzonKerher.bat" 2>nul
del /Q "SEND_REPORT_NOW.bat" 2>nul
del /Q "START_PARSER_FINAL.bat" 2>nul
del /Q "START_PARSER_ONECLICK.bat" 2>nul
del /Q "START_SIMPLE.bat" 2>nul
del /Q "TEST_COMPONENTS.bat" 2>nul
del /Q "start_playwright_parser.bat" 2>nul

REM Удаление старых прокси конфигураций
del /Q "proxies_http.txt" 2>nul
del /Q "proxies_mango.txt" 2>nul
del /Q "proxies_mango_converted.txt" 2>nul
del /Q "3proxy.cfg" 2>nul

REM Удаление DLL и EXE файлов
for %%f in (*.dll 3proxy.exe mycrypt.exe) do del /Q "%%f" 2>nul

REM Удаление директорий
echo.
echo Удаление директорий...
for %%d in (__pycache__ .venv .vscode 137 ParserOzon ParserOzon_Production ParserYM browser_profiles db debug_html_antibot dev error_logs legacy local_proxy logs output p3 prod project_structure proxy_auth_extension proxy_extension tmp_proxy_ext tools) do (
    if exist "%%d" rmdir /S /Q "%%d" 2>nul
)

echo.
echo ========================================
echo   ОЧИСТКА ЗАВЕРШЕНА!
echo ========================================
echo.
dir /B
echo.
pause
