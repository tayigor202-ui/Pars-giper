@echo off
REM Quick service management commands

:menu
cls
echo.
echo ====================================================================
echo OZON Parser Web Service - Quick Menu
echo ====================================================================
echo.
echo 1. Start service
echo 2. Stop service
echo 3. Restart service
echo 4. Check status
echo 5. View logs (stdout)
echo 6. View logs (errors)
echo 7. Exit
echo.
choice /c 1234567 /n /m "Select option: "

set "NSSM=%~dp0nssm.exe"
set "SERVICE=OzonParserWeb"

if errorlevel 7 exit /b
if errorlevel 6 goto logs_err
if errorlevel 5 goto logs_out
if errorlevel 4 goto status
if errorlevel 3 goto restart
if errorlevel 2 goto stop
if errorlevel 1 goto start

:start
echo Starting service...
"%NSSM%" start "%SERVICE%"
timeout /t 2 /nobreak >nul
goto status

:stop
echo Stopping service...
"%NSSM%" stop "%SERVICE%"
timeout /t 2 /nobreak >nul
goto status

:restart
echo Restarting service...
"%NSSM%" restart "%SERVICE%"
timeout /t 3 /nobreak >nul
goto status

:status
echo.
sc query "%SERVICE%"
echo.
pause
goto menu

:logs_out
echo.
echo === Latest stdout log (last 30 lines) ===
echo.
powershell -Command "Get-Content '%~dp0logs\web_service_stdout.log' -Tail 30"
echo.
pause
goto menu

:logs_err
echo.
echo === Latest stderr log (last 30 lines) ===
echo.
powershell -Command "Get-Content '%~dp0logs\web_service_stderr.log' -Tail 30"
echo.
pause
goto menu
