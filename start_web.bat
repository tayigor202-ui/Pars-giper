@echo off
chcp 65001 >nul
echo ======================================================================
echo              ЗАПУСК ВЕБ-ИНТЕРФЕЙСА OZON/WB PARSER
echo ======================================================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo [ОШИБКА] Файл .env не найден!
    echo.
    echo Сначала выполните установку:
    echo     install.bat
    echo.
    echo Или:
    echo     python setup.py
    echo.
    pause
    exit /b 1
)

echo Проверка обновлений в репозитории Git...
git pull origin main
echo.

echo Запуск веб-серера...
echo.
echo Веб-интерфейс будет доступен по адресу:
echo     http://localhost:3455
echo.
echo Для остановки нажмите Ctrl+C
echo.
echo ======================================================================
echo.

python web_app.py

pause
