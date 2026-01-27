@echo off
chcp 65001 >nul
echo ===============================================================
echo  ПЕРЕЗАПУСК ВЕБ-СЕРВИСА ПАРСЕРА
echo ===============================================================
echo.

echo [1/3] Остановка всех процессов pythonw...
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/3] Проверка порта 3454...
netstat -ano | findstr ":3454" >nul
if %ERRORLEVEL% EQU 0 (
    echo WARNING: Порт 3454 все еще занят
) else (
    echo OK: Порт 3454 свободен
)

echo [3/3] Запуск веб-приложения в фоновом режиме...
start /B pythonw web_app.py

timeout /t 3 /nobreak >nul

echo.
echo ===============================================================
echo  ЗАВЕРШЕНО!
echo ===============================================================
echo.
echo  URL: http://localhost:3454
echo  Логин: admin
echo  Пароль: admin
echo.
echo ===============================================================
pause
