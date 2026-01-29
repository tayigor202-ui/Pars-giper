@echo off
:: No special characters at the top to prevent encoding crashes
echo ===================================================
echo    PARS-GIPER UNIVERSAL INSTALLER
echo ===================================================
echo.
echo DEBUG: Preparing environment...
pause

:: Ensure we are in the script directory
cd /d "%~dp0"

:: 1. CHECK FOR PYTHON
echo [1/3] Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python NOT found. Attempting auto-install...
    
    echo [SYSTEM] Downloading Python 3.11...
    set "PY_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    set "PY_EXE=python_setup.exe"
    
    :: Use curl (built-in Windows 10/11)
    curl -L -o %PY_EXE% %PY_URL%
    if %errorlevel% neq 0 (
        echo [ERROR] Download failed. Please install Python manually from python.org
        pause
        exit /b 1
    )
    
    echo [SYSTEM] Installing Python silently...
    echo PLEASE WAIT - This takes about 1-2 minutes.
    start /wait %PY_EXE% /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del %PY_EXE%
    
    echo.
    echo [SUCCESS] Python installed! 
    echo [IMPORTANT] YOU MUST RUN THIS SCRIPT ONE MORE TIME.
    echo.
    echo Press any key to exit, then launch install.bat again.
    pause
    exit /b 0
)

echo [OK] Python found.
python --version
echo.

:: 2. INSTALL LIBRARIES
echo [2/3] Installing libraries...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Normal install failed. Trying alternate...
    python -m pip install -r requirements.txt --user
)

:: 3. SETUP CONFIG
echo [3/3] Finalizing setup...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
    )
)

python setup\setup.py --silent
if %errorlevel% neq 0 (
    echo [!] Standard setup failed. Running database initialization...
    python setup\setup_database_and_users.py
)

echo.
echo ===================================================
echo        INSTALLATION FINISHED SUCCESSFULLY!
echo ===================================================
echo.
echo Next steps:
echo 1. Run start_web.bat to start the system
echo 2. Open http://localhost:3455
echo.
pause
