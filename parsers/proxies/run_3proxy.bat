@echo off
REM Запуск 3proxy с конфигом для парсера
REM Загружает все 40 прокси из upstreams.txt
REM Слушает на локальных портах 31280-31399

echo.
echo ════════════════════════════════════════════════════════════
echo  3proxy LAUNCHER - Ozon Parser Proxy Pool
echo ════════════════════════════════════════════════════════════
echo.
echo Загруженные параметры:
echo   • Upstream прокси: 40
echo   • Локальные порты: 31280-31399 (120 инстансов)
echo   • Каждый браузер использует port 31280 + INDEX
echo.

REM Проверяем наличие 3proxy.exe
if not exist "3proxy.exe" (
    echo ❌ Ошибка: 3proxy.exe не найден в текущей папке
    echo Скачайте с https://3proxy.org/ или распакуйте архив
    echo.
    pause
    exit /b 1
)

REM Проверяем наличие конфига
if not exist "3proxy.cfg" (
    echo ❌ Ошибка: 3proxy.cfg не найден
    echo Запустите сначала: python generate_3proxy_config.py
    echo.
    pause
    exit /b 1
)

echo ▶ Запуск 3proxy с конфигом...
echo.

REM Запускаем 3proxy
3proxy.exe 3proxy.cfg

if errorlevel 1 (
    echo.
    echo ❌ 3proxy завершился с ошибкой
    pause
    exit /b 1
)
