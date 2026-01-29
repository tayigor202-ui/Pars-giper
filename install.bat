@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ======================================================================
echo            АВТОМАТИЧЕСКАЯ УСТАНОВКА OZON/WB PARSER
echo ======================================================================
echo.

REM --- 1. ПРОВЕРКА PYTHON ---
echo [SYSTEM] Проверка наличия Python...

set PYTHON_CMD=python
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    set PYTHON_CMD=py
    !PYTHON_CMD! --version >nul 2>&1
    if errorlevel 1 (
        echo [ОШИБКА] Python не найден в системе!
        echo.
        echo Пожалуйста, установите Python 3.11 или выше:
        echo https://www.python.org/downloads/
        echo.
        echo ПРИ УСТАНОВКЕ ОБЯЗАТЕЛЬНО ОТМЕТЬТЕ ГАЛОЧКУ:
        echo "Add Python to PATH"
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Использование команды: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM --- 2. ЗАПУСК SETUP.PY ---
echo ======================================================================
echo Запуск основного сценария установки...
echo ======================================================================
echo.

if not exist "setup\setup.py" (
    echo [ОШИБКА] Файл setup\setup.py не найден! 
    echo Убедитесь, что вы запускаете install.bat из корня проекта.
    pause
    exit /b 1
)

%PYTHON_CMD% "setup\setup.py" %*

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Установка завершилась сбоем в Python-скрипте.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo                    УСТАНОВКА УСПЕШНО ЗАВЕРШЕНА!
echo ======================================================================
echo.
echo Для запуска веб-интерфейса выполните:
echo     start_web.bat
echo.
pause
