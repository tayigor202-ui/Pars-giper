@echo off
REM Quick Flask management

:menu
cls
echo.
echo ====================================================================
echo OZON Parser Web Dashboard - Management
echo ====================================================================
echo.
echo Current status:
tasklist | findstr pythonw.exe >nul 2>&1 && echo Flask running (pythonw.exe) || echo Flask stopped
echo.
echo 1. Start Flask
echo 2. Stop Flask
echo 3. Restart Flask
echo 4. View logs (last 30 lines)
echo 5. Open in browser
echo 6. Exit
echo.
choice /c 123456 /n /m "Select option: "

set "TASK=OzonParserWebDashboard"

if errorlevel 6 exit /b
if errorlevel 5 goto browser
if errorlevel 4 goto logs
if errorlevel 3 goto restart
if errorlevel 2 goto stop
if errorlevel 1 goto start

:start
echo Starting Flask...
start "" "%~dp0start_flask_background.bat"
timeout /t 2 /nobreak >nul
echo.
echo Flask started in background! Check http://localhost:3454
pause
goto menu

:stop
echo Stopping Flask...
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 1 /nobreak >nul
echo.
echo Flask stopped!
pause
goto menu

:restart
echo Restarting Flask...
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 2 /nobreak >nul
start "" "%~dp0start_flask_background.bat"
timeout /t 2 /nobreak >nul
echo.
echo Flask restarted!
pause
goto menu

:logs
echo.
echo === Last 30 lines of log ===
echo.
powershell -Command "Get-Content '%~dp0logs\web_dashboard.log' -Tail 30 -ErrorAction SilentlyContinue"
echo.
pause
goto menu

:browser
echo Opening browser...
start http://localhost:3454
goto menu
