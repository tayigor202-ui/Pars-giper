@echo off
REM Remove auto-start task

net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

set "TASK_NAME=OzonParserWebDashboard"

echo Stopping and removing auto-start task...
schtasks /End /TN "%TASK_NAME%" 2>nul
schtasks /Delete /TN "%TASK_NAME%" /F

echo.
echo Task removed!
echo.
pause
