@echo off
chcp 65001 >nul
echo ======================================================================
echo            АВТОМАТИЧЕСКАЯ УСТАНОВКА OZON/WB PARSER
echo ======================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo.
    echo Пожалуйста, установите Python 3.8 или выше:
    echo https://www.python.org/downloads/
    echo.
    echo Убедитесь, что отметили "Add Python to PATH" при установке
    pause
    exit /b 1
)

echo [OK] Python найден
python --version
echo.

echo ======================================================================
echo Запуск автоматической установки (Zero-Touch Deployment)
echo ======================================================================
echo.

REM Run setup.py - you can add --silent here if you want it completely non-iREM Run setup.py
python setup\setup.py %*

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Установка завершилась с ошибкой
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo                    УСТАНОВКА ЗАВЕРШЕНА!
echo ======================================================================
echo.
echo Для запуска веб-интерфейса выполните:
echo     python web_app.py
echo.
echo Или используйте:
echo     start_web.bat
echo.
pause
