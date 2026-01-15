@echo off
REM Remove auto-start from Startup folder

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_NAME=OZON Parser Web.vbs"

echo Removing auto-start...
del "%STARTUP_FOLDER%\%SHORTCUT_NAME%" >nul 2>&1

if %errorLevel% equ 0 (
    echo Auto-start removed!
) else (
    echo File not found or already removed.
)

pause
