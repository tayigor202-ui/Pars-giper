@echo off
REM ====================================================================
REM Simple Auto-Start via Windows Startup Folder
REM No admin rights required!
REM ====================================================================

echo.
echo ====================================================================
echo OZON Parser - Simple Auto-Start Setup
echo ====================================================================
echo.

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_NAME=OZON Parser Web.vbs"
set "TARGET_BAT=%~dp0start_flask_background.bat"

echo Creating auto-start shortcut...
echo Target: %TARGET_BAT%
echo Startup folder: %STARTUP_FOLDER%
echo.

REM Create VBS script to run Flask silently (no console window)
echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\run_flask.vbs"
echo WshShell.Run chr(34) ^& "%TARGET_BAT%" ^& Chr(34), 0 >> "%TEMP%\run_flask.vbs"
echo Set WshShell = Nothing >> "%TEMP%\run_flask.vbs"

REM Copy VBS to Startup folder
copy "%TEMP%\run_flask.vbs" "%STARTUP_FOLDER%\%SHORTCUT_NAME%" >nul 2>&1

if %errorLevel% equ 0 (
    echo.
    echo ====================================================================
    echo SUCCESS! Auto-start configured!
    echo ====================================================================
    echo.
    echo Flask will now start automatically when you log in to Windows!
    echo.
    echo The web dashboard will run in background (no visible window)
    echo.
    echo Starting Flask now...
    echo.
    
    REM Start Flask now
    start "" "%TARGET_BAT%"
    
    timeout /t 3 /nobreak >nul
    
    echo.
    echo ====================================================================
    echo Flask is running!
    echo ====================================================================
    echo.
    echo Web URL: http://localhost:3454
    echo.
    echo To remove auto-start, run: remove_autostart_simple.bat
    echo.
    echo ====================================================================
) else (
    echo.
    echo ERROR: Failed to create shortcut!
    echo.
)

pause
