# Pars-Giper Universal PowerShell Installer
$ErrorActionPreference = "Stop"

# Force ALL security protocols using numeric values for older PowerShell compatibility
# 3072 = TLS 1.2, 768 = TLS 1.1, 192 = TLS 1.0, 48 = SSL 3.0
[Net.ServicePointManager]::SecurityProtocol = 48 -bor 192 -bor 768 -bor 3072

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
    try {
        # Try Invoke-WebRequest first
        Invoke-WebRequest -Uri $url -OutFile $output -TimeoutSec 60
    }
    catch {
        Write-Host "[!] Standard download failed. Trying fallback method..." -ForegroundColor Magenta
        try {
            # Fallback to WebClient
            $webClient = New-Object System.Net.WebClient
            $webClient.DownloadFile($url, $output)
        }
        catch {
            Write-Host ""
            Write-Host "CRITICAL ERROR: Could not download Python automatically due to Windows SSL restrictions." -ForegroundColor Red
            Write-Host "PLEASE DO THIS MANUALLY:" -ForegroundColor White
            Write-Host "1. Download Python from: $url" -ForegroundColor Cyan
            Write-Host "2. Install it and CHECK THE BOX 'Add Python to PATH'" -ForegroundColor Cyan
            Write-Host "3. Then run this script again." -ForegroundColor White
            Write-Host ""
            Pause
            exit
        }
    }
    
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

# 2. Check PostgreSQL
Write-Host "[2/4] Checking PostgreSQL database..." -ForegroundColor Yellow
$pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue

if (!$pgService) {
    Write-Host "[!] PostgreSQL not found. Attempting automatic installation..." -ForegroundColor Red
    
    # Try direct download + silent install
    Write-Host "[SYSTEM] Downloading PostgreSQL installer (please wait)..." -ForegroundColor White
    $pgUrl = "https://sbp.enterprisedb.com/getinstaller.php?queryId=c18bc088031d9990df7f29013f99092d"
    $pgFile = Join-Path $env:TEMP "postgresql_installer.exe"
    
    try {
        Invoke-WebRequest -Uri $pgUrl -OutFile $pgFile -TimeoutSec 300
    }
    catch {
        try {
            $webClient = New-Object System.Net.WebClient
            $webClient.DownloadFile($pgUrl, $pgFile)
        }
        catch {
            Write-Host "[!] Automatic download failed. Please install manually." -ForegroundColor Red
            Write-Host "Link: $pgUrl"
            Pause
            exit
        }
    }

    Write-Host "[SYSTEM] Starting silent installation (2-4 mins)..." -ForegroundColor Yellow
    Write-Host "[WAIT] DO NOT CLOSE THIS WINDOW. Installs PostgreSQL and sets password to 'postgres'." -ForegroundColor Gray
    
    $args = "--mode unattended --unattendedmodeui none --superpassword postgres --serverport 5432"
    $p = Start-Process -FilePath $pgFile -ArgumentList $args -Wait -PassThru
    
    if ($p.ExitCode -ne 0) {
        Write-Host "[ERROR] Installation failed with exit code: $($p.ExitCode)" -ForegroundColor Red
        Pause
        exit
    }

    Remove-Item $pgFile
    Write-Host "[OK] PostgreSQL installed and service started." -ForegroundColor Green
}
else {
    Write-Host "[OK] PostgreSQL service found: $($pgService.DisplayName)" -ForegroundColor Green
}
Write-Host ""

# 3. Install Libraries
Write-Host "[3/4] Installing dependencies..." -ForegroundColor Yellow
& python -m pip install --upgrade pip
& python -m pip install -r requirements.txt
Write-Host "[OK] Libraries installed." -ForegroundColor Green
Write-Host ""

# 4. Setup Project
Write-Host "[4/4] Finalizing configuration..." -ForegroundColor Yellow
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
