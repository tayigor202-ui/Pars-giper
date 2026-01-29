@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

:: Ensure we are in the script directory
cd /d "%~dp0"

echo ======================================================================
echo            UNIVERSAL ONE-CLICK INSTALLER : PARS-GIPER
echo ======================================================================
echo.

:: 1. CHECK FOR PYTHON
echo [1/4] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python not found. Starting automatic bootstrap...
    
    :: Try winget first (Standard on Win 10/11)
    echo [SYSTEM] Attempting to install Python via winget...
    winget install --id Python.Python.3.11 --exact --no-upgrade --accept-source-agreements --accept-package-agreements --silent
    
    if errorlevel 1 (
        echo [SYSTEM] Winget failed or not available. Downloading Python installer manually...
        set "PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
        set "INSTALLER_EXE=python_installer.exe"
        
        curl -L -o !INSTALLER_EXE! !PYTHON_URL!
        if errorlevel 1 (
            echo [FATAL] Failed to download Python. Please check internet connection.
            pause
            exit /b 1
        )
        
        echo [SYSTEM] Running silent installation (this may take a minute)...
        start /wait !INSTALLER_EXE! /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        del !INSTALLER_EXE!
    )
    
    echo.
    echo [OK] Python installed successfully! 
    echo [IMPORTANT] I need to RESTART this script to see the new Python path.
    echo Please press any key, and then run install.bat AGAIN.
    pause
    exit /b 0
)

echo [OK] Python found: 
python --version
echo.

:: 2. INSTALL DEPENDENCIES
echo [2/4] Installing project libraries (requirements.txt)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Some libraries failed to install. Retrying...
    python -m pip install -r requirements.txt --user
)

:: 3. SETUP DATABASE AND CONFIG
echo [3/4] Initializing Database and Configuration...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo [OK] Created .env from example.
    )
)

python setup\setup.py --silent
if errorlevel 1 (
    echo [!] Setup script encountered issues. Attempting repair...
    python setup\setup_database_and_users.py
)

:: 4. FINALIZE
echo.
echo ======================================================================
echo                    INSTALLATION COMPLETE!
echo ======================================================================
echo.
echo You can now start the web interface using:
echo     start_web.bat
echo.
echo Also, you can set up autostart (Run as Admin):
echo     add_to_startup.bat
echo.
pause
