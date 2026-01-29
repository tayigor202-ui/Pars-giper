# Pars-Giper Universal PowerShell Installer
$ErrorActionPreference = "Stop"

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   PARS-GIPER UNIVERSAL INSTALLER (PS MODE)    " -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
Write-Host "[1/3] Checking Python environment..." -ForegroundColor Yellow
$pythonPath = Get-Command python -ErrorAction SilentlyContinue

if (!$pythonPath) {
    Write-Host "[!] Python not found. Starting automatic bootstrap..." -ForegroundColor Red
    
    $url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $output = Join-Path $env:TEMP "python_setup.exe"
    
    Write-Host "[SYSTEM] Downloading Python 3.11..." -ForegroundColor Gray
    Invoke-WebRequest -Uri $url -OutFile $output
    
    Write-Host "[SYSTEM] Installing Python silently (1-2 mins)..." -ForegroundColor Gray
    $process = Start-Process -FilePath $output -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait -PassThru
    
    Remove-Item $output
    
    Write-Host ""
    Write-Host "[SUCCESS] Python installed!" -ForegroundColor Green
    Write-Host "[IMPORTANT] You MUST restart this script to apply changes." -ForegroundColor White
    Write-Host "Press any key to exit, then run install_ps.bat again."
    $null = [System.Console]::ReadKey()
    exit
}

Write-Host "[OK] Python is ready." -ForegroundColor Green
python --version
Write-Host ""

# 2. Install Libraries
Write-Host "[2/3] Installing dependencies..." -ForegroundColor Yellow
& python -m pip install --upgrade pip
& python -m pip install -r requirements.txt
Write-Host "[OK] Libraries installed." -ForegroundColor Green
Write-Host ""

# 3. Setup Project
Write-Host "[3/3] Finalizing configuration..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
    }
}

& python setup/setup.py --silent
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "       INSTALLATION FINISHED SUCCESSFULLY!     " -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Run start_web.bat to start the system"
Write-Host "2. Open http://localhost:3455"
Write-Host ""
Write-Host "Press any key to close..."
$null = [System.Console]::ReadKey()
