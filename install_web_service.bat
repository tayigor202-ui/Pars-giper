@echo off
REM ====================================================================
REM Flask Web Dashboard - Windows Service Installation
REM Uses NSSM (Non-Sucking Service Manager) for reliable service
REM ====================================================================

echo.
echo ====================================================================
echo OZON Parser - Flask Web Service Installation
echo ====================================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Set paths
set "SCRIPT_DIR=%~dp0"
set "NSSM_PATH=%SCRIPT_DIR%nssm.exe"
set "PYTHON_EXE=python"
set "WEB_APP=%SCRIPT_DIR%web_app.py"
set "SERVICE_NAME=OzonParserWeb"

echo Current directory: %SCRIPT_DIR%
echo Python executable: %PYTHON_EXE%
echo Web app: %WEB_APP%
echo Service name: %SERVICE_NAME%
echo.

REM Check if NSSM exists
if not exist "%NSSM_PATH%" (
    echo ERROR: nssm.exe not found!
    echo.
    echo Please download NSSM from: https://nssm.cc/download
    echo Extract nssm.exe to: %SCRIPT_DIR%
    echo.
    pause
    exit /b 1
)

REM Check if service already exists
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo Service "%SERVICE_NAME%" already exists!
    echo Stopping and removing old service...
    "%NSSM_PATH%" stop "%SERVICE_NAME%"
    timeout /t 2 /nobreak >nul
    "%NSSM_PATH%" remove "%SERVICE_NAME%" confirm
    timeout /t 2 /nobreak >nul
)

echo.
echo Installing service "%SERVICE_NAME%"...
echo.

REM Install service
"%NSSM_PATH%" install "%SERVICE_NAME%" "%PYTHON_EXE%" "%WEB_APP%"

REM Set working directory
"%NSSM_PATH%" set "%SERVICE_NAME%" AppDirectory "%SCRIPT_DIR%"

REM Set display name and description
"%NSSM_PATH%" set "%SERVICE_NAME%" DisplayName "OZON Parser Web Dashboard"
"%NSSM_PATH%" set "%SERVICE_NAME%" Description "Web interface for OZON price parser with user management and scheduling"

REM Set startup type to automatic
"%NSSM_PATH%" set "%SERVICE_NAME%" Start SERVICE_AUTO_START

REM Set restart policy - auto restart on failure
"%NSSM_PATH%" set "%SERVICE_NAME%" AppExit Default Restart
"%NSSM_PATH%" set "%SERVICE_NAME%" AppRestartDelay 5000

REM Set stdout/stderr logging
"%NSSM_PATH%" set "%SERVICE_NAME%" AppStdout "%SCRIPT_DIR%logs\web_service_stdout.log"
"%NSSM_PATH%" set "%SERVICE_NAME%" AppStderr "%SCRIPT_DIR%logs\web_service_stderr.log"
"%NSSM_PATH%" set "%SERVICE_NAME%" AppStdoutCreationDisposition 4
"%NSSM_PATH%" set "%SERVICE_NAME%" AppStderrCreationDisposition 4

REM Create logs directory if not exists
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"

echo.
echo Service installed successfully!
echo.

REM Start service
echo Starting service...
"%NSSM_PATH%" start "%SERVICE_NAME%"

timeout /t 3 /nobreak >nul

REM Check service status
sc query "%SERVICE_NAME%" | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo.
    echo ====================================================================
    echo SUCCESS! Service is running!
    echo ====================================================================
    echo.
    echo Service Name: %SERVICE_NAME%
    echo Web URL: http://localhost:3454
    echo.
    echo Service will now:
    echo  - Run in background
    echo  - Auto-start on server reboot
    echo  - Auto-restart on failure (5 sec delay)
    echo.
    echo Logs location: %SCRIPT_DIR%logs\
    echo.
    echo To manage service:
    echo  - Start:   nssm start %SERVICE_NAME%
    echo  - Stop:    nssm stop %SERVICE_NAME%
    echo  - Restart: nssm restart %SERVICE_NAME%
    echo  - Remove:  nssm remove %SERVICE_NAME% confirm
    echo  - Or use:  services.msc
    echo.
    echo ====================================================================
) else (
    echo.
    echo WARNING: Service installed but failed to start!
    echo Check logs: %SCRIPT_DIR%logs\web_service_stderr.log
    echo.
)

pause
