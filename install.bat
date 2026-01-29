@echo off
echo ==========================================
echo    PARS-GIPER INSTALLER (DEBUG MODE)
echo ==========================================
echo.
echo DEBUG: Script started. Early pause incoming...
pause

cd /d "%~dp0"
echo DEBUG: Current directory: %cd%

REM Check Python
echo DEBUG: Checking Python (python)...
python --version
if errorlevel 1 (
    echo DEBUG: python failed, checking (py)...
    py --version
    if errorlevel 1 (
        echo ERROR: No python found! Stop.
        pause
        exit /b 1
    )
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

echo DEBUG: Using command: %PYTHON_CMD%
pause

echo DEBUG: Starting setup.py...
%PYTHON_CMD% "setup\setup.py"
if errorlevel 1 (
    echo ERROR: setup.py failed!
    pause
    exit /b 1
)

echo.
echo SUCCESS: Installation finished.
pause
