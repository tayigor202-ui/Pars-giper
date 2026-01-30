@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Ensure we are in the project directory
cd /d "%~dp0"

echo ======================================================================
echo            STARTING PARS-GIPER WEB SERVER
echo ======================================================================
echo.

:: 1. FIND PYTHON DYNAMICALLY
set PYTHON_CMD=python
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    set PYTHON_CMD=py
    !PYTHON_CMD! --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python not found! Please run install.bat first.
        pause
        exit /b 1
    )
)

echo [OK] Using command: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

:: 1.5 CHECK DATABASE CONNECTION
echo Checking Database Connection...
%PYTHON_CMD% -c "import psycopg2, os; from dotenv import load_dotenv; load_dotenv(); psycopg2.connect(os.getenv('DB_URL'))" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Could not connect to the database.
    echo Please make sure PostgreSQL is running and your .env is correct.
    echo Run install.bat if you haven't set up the database yet.
    echo.
    pause
    exit /b 1
)
echo [OK] Database is reachable.
echo.

:: 2. RUN WEB APP
echo [%DATE% %TIME%] Starting Web Server... >> startup_log.txt
echo Running web_app.py...

:: Run and capture both output and errors to log, but also show in console
%PYTHON_CMD% web_app.py

if errorlevel 1 (
    echo.
    echo [FATAL] Web server crashed or could not start.
    echo Check startup_log.txt for details.
    echo.
    pause
    exit /b 1
)

pause
