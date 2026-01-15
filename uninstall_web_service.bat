@echo off
REM ====================================================================
REM Uninstall Flask Web Service
REM ====================================================================

echo.
echo ====================================================================
echo OZON Parser - Flask Web Service Uninstallation
echo ====================================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    pause
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"
set "NSSM_PATH=%SCRIPT_DIR%nssm.exe"
set "SERVICE_NAME=OzonParserWeb"

if not exist "%NSSM_PATH%" (
    echo ERROR: nssm.exe not found!
    pause
    exit /b 1
)

echo Stopping service...
"%NSSM_PATH%" stop "%SERVICE_NAME%"

timeout /t 2 /nobreak >nul

echo Removing service...
"%NSSM_PATH%" remove "%SERVICE_NAME%" confirm

echo.
echo Service uninstalled!
echo.
pause
