@echo off
REM ====================================================================
REM Simplest Auto-Start - Just copy bat to Startup folder
REM ====================================================================

echo.
echo ====================================================================
echo OZON Parser - Auto-Start Setup
echo ====================================================================
echo.

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SOURCE=%~dp0start_flask_background.bat"

echo Creating shortcut in Startup folder...
echo.

REM Create shortcut using PowerShell
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%STARTUP%\OZON Parser Web.lnk'); $SC.TargetPath = '%SOURCE%'; $SC.WorkingDirectory = '%~dp0'; $SC.WindowStyle = 7; $SC.Save()"

if %errorLevel% equ 0 (
    echo.
    echo ====================================================================
    echo SUCCESS! Auto-start configured!
    echo ====================================================================
    echo.
    echo Flask will start automatically on next login!
    echo.
    echo Starting Flask now ...
    start "" "%SOURCE%"
    
    timeout /t 2 /nobreak >nul
    
    echo.
    echo Web URL: http://localhost:3454
    echo.
    echo ====================================================================
) else (
    echo ERROR: Failed!
)

pause
