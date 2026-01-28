@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [SYSTEM] Запуск всего проекта в фоновом режиме...

REM Проверка наличия .env
if not exist ".env" (
    echo [ERROR] .env не найден. Запустите сначала install.bat
    pause
    exit /b 1
)

REM Запуск через тихий загрузчик
wscript.exe run_hidden.vbs "python web_app.py"

echo [SUCCESS] Приложение запущено скрытно.
echo Веб-интерфейс: http://localhost:3455
echo Никаких окон консоли не останется.
timeout /t 5
exit
