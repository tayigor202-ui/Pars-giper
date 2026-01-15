@echo off
REM ====================================================================
REM Flask Web Dashboard - Auto-Start Setup (Task Scheduler)
REM No external dependencies required - uses built-in Windows Task Scheduler
REM ====================================================================

echo.
echo ====================================================================
echo OZON Parser - Auto-Start Setup
echo ====================================================================
echo.

REM Admin check not needed for ONLOGON tasks (run as current user)
REM Tasks will run when user logs in

set "SCRIPT_DIR=%~dp0"
set "TASK_NAME=OzonParserWebDashboard"
set "PYTHON_PATH=python"
set "WEB_APP=%SCRIPT_DIR%web_app.py"
set "LOG_FILE=%SCRIPT_DIR%logs\web_dashboard.log"

echo Script directory: %SCRIPT_DIR%
echo Task name: %TASK_NAME%
echo Web app: %WEB_APP%
echo.

REM Create logs directory
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"

REM Delete existing task if exists
echo Checking for existing task...
schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo Found existing task, deleting...
    schtasks /Delete /TN "%TASK_NAME%" /F
)

echo.
echo Creating scheduled task for auto-start...
echo.

REM Create task that runs at startup and stays running (as current user)
schtasks /Create /TN "%TASK_NAME%" /TR "\"%SCRIPT_DIR%start_flask_background.bat\"" /SC ONLOGON /F

if %errorLevel% equ 0 (
    echo.
    echo ====================================================================
    echo SUCCESS! Task created successfully!
    echo ====================================================================
    echo.
    echo Task Name: %TASK_NAME%
    echo Trigger: On system startup
    echo.
    echo Starting Flask now...
    echo.
    
    REM Start the task immediately
    schtasks /Run /TN "%TASK_NAME%"
    
    timeout /t 3 /nobreak >nul
    
    echo.
    echo ====================================================================
    echo Flask is now running in background!
    echo ====================================================================
    echo.
    echo Web URL: http://localhost:3454
    echo Logs: %SCRIPT_DIR%logs\web_dashboard.log
    echo.
    echo The dashboard will now:
    echo  - Run in background
    echo  - Auto-start on server reboot
    echo  - Keep running until stopped
    echo.
    echo To manage:
    echo  - View status:  schtasks /Query /TN "%TASK_NAME%"
    echo  - Stop:         schtasks /End /TN "%TASK_NAME%"
    echo  - Start:        schtasks /Run /TN "%TASK_NAME%"
    echo  - Remove:       schtasks /Delete /TN "%TASK_NAME%" /F
    echo  - Or use:       taskschd.msc
    echo.
    echo Quick management menu: manage_web_service.bat
    echo.
    echo ====================================================================
) else (
    echo.
    echo ERROR: Failed to create scheduled task!
    echo Please check permissions and try again.
    echo.
)

pause
