@echo off
REM Запуск Python прокси-форвардера (вместо 3proxy)
REM Использует настройки из proxies_mango_rotating.txt

echo.
echo ════════════════════════════════════════════════════════════
echo  MANGO PROXY FORWARDER (Python)
echo ════════════════════════════════════════════════════════════
echo.

REM Проверяем наличие python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Ошибка: Python не найден!
    pause
    exit /b 1
)

echo ▶ Запуск прокси на 127.0.0.1:8118...
echo.

python proxies/auth_forwarder.py --config proxies_mango_rotating.txt --listen-start 8118

if errorlevel 1 (
    echo.
    echo ❌ Прокси завершился с ошибкой
    pause
)
