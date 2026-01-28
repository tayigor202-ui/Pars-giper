@echo off
echo ======================================================================
echo          ПЕРЕЗАПУСК ПРИЛОЖЕНИЯ ПОСЛЕ ОБНОВЛЕНИЯ...
echo ======================================================================
echo.

timeout /t 5 /nobreak >nul

echo Остановка старых процессов...
taskkill /F /IM python.exe /T >nul 2>&1

echo Запуск новой версии...
cd /d "%~dp0"
start python web_app.py

echo Перезапуск успешно инициирован!
timeout /t 3 /nobreak >nul
exit
