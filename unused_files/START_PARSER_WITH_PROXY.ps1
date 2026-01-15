#!/usr/bin/env pwsh
# OZON PARSER WITH LOCAL PROXY SERVER

Set-Location $PSScriptRoot

Write-Host ""
Write-Host "Starting Local Proxy Server..." -ForegroundColor Cyan
Write-Host ""

# Start local proxy in background
$proxyProcess = Start-Process -NoNewWindow -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "start_local_proxy.py" -PassThru

Write-Host "Proxy started (PID: $($proxyProcess.Id))" -ForegroundColor Green
Write-Host "Waiting 3 seconds for initialization..." -ForegroundColor Yellow

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Starting OZON PARSER with 20 browsers..." -ForegroundColor Cyan
Write-Host ""

# Run parser
& .\.venv\Scripts\python.exe ParserOzon_Production\core\Ozon3.py

Write-Host ""
Write-Host "Parser finished" -ForegroundColor Green
Write-Host "Stopping proxy server (PID: $($proxyProcess.Id))" -ForegroundColor Yellow

# Stop proxy
$proxyProcess | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1
Write-Host "Proxy stopped" -ForegroundColor Green
