#Requires -Version 5.1
$ErrorActionPreference = "Stop"

# -------------------- НАСТРОЙКИ --------------------
$Count       = 20              # сколько окон Chrome открыть
$ProxyStart  = 31280               # первый локальный порт (далее +1)
$Devtools0   = 9222                # первый порт DevTools (далее +1)

$ProfilesDir = "C:\Temp\chrome_profiles\ozon"
$CacheDir    = "C:\Temp\chrome_cache"
$LogsDir     = "C:\Users\Kerher\Desktop\ParserProd\logs"

$Upstreams   = Join-Path $PSScriptRoot "upstreams.txt"
$RotatorPy   = Join-Path $PSScriptRoot "auth_rotator.py"

# Автостарт парсера — запуск строго через venv Activate.ps1
$StartParser = $true

# -------------------- ПОДГОТОВКА --------------------
New-Item -ItemType Directory -Path $ProfilesDir -Force | Out-Null
New-Item -ItemType Directory -Path $CacheDir    -Force | Out-Null
New-Item -ItemType Directory -Path $LogsDir     -Force | Out-Null
try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding } catch {}

function Resolve-Chrome {
  $cands = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
  )
  foreach($c in $cands){ if(Test-Path $c){ return $c } }
  throw "Chrome not found"
}
function Resolve-Python {
  $cands = @(
    (Join-Path (Split-Path $PSScriptRoot -Parent) ".venv\Scripts\python.exe"),
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "python.exe"
  )
  foreach($c in $cands){ try { return (Get-Command $c -ErrorAction Stop).Source } catch {} }
  throw "python.exe not found"
}
function Resolve-Parser {
  $root = (Split-Path $PSScriptRoot -Parent)
  $cands = @(
    (Join-Path $root "Ozon3.py"),
    (Join-Path $root "price_parserOzon3.py"),
    (Join-Path $root "price_parserOzon.py"),
    (Join-Path $root "Ozon3.ps1"),
    (Join-Path $root "Start_Ozon_OneClick.bat")
  )
  foreach($c in $cands){ if(Test-Path $c){ return $c } }
  return $null
}
function Test-TcpOpen {
  param([string]$HostName,[int]$Port,[int]$TimeoutMs=600)
  try {
    $client = New-Object System.Net.Sockets.TcpClient
    $iar = $client.BeginConnect($HostName,$Port,$null,$null)
    if(-not $iar.AsyncWaitHandle.WaitOne($TimeoutMs)){ $client.Close(); return $false }
    $client.EndConnect($iar); $client.Close(); return $true
  } catch { return $false }
}

$chrome = Resolve-Chrome
$python = Resolve-Python
if(-not (Test-Path $Upstreams)){ throw "Файл upstreams.txt не найден: $Upstreams" }

Write-Host ("[*] Launch {0} Chrome windows via local proxies {1}..{2}" -f $Count, $ProxyStart, ($ProxyStart + $Count - 1))

# -------------------- СТАРТ РОТАТОРА --------------------
$needPorts = 0..($ProxyCount-1) | ForEach-Object { $ProxyStart + $_ }
$alive = ($needPorts | Where-Object { Test-TcpOpen -HostName "127.0.0.1" -Port $_ }).Count
if($alive -lt $Count){
  Write-Host "[*] Starting auth_rotator.py (round-robin + health + rotation)"
  $env:LP_START   = "$ProxyStart"
  $env:LP_COUNT   = "$Count"
  $env:UPSTREAMS  = $Upstreams
  $env:ROTATE_SEC = "600"
  $env:HEALTH_SEC = "30"
  $env:PYTHONIOENCODING = "utf-8"

  $rotLog = Join-Path $LogsDir ("rotator_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName  = $python
  $psi.Arguments = "`"$RotatorPy`""
  $psi.WorkingDirectory = $PSScriptRoot
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
# -------------------- Windows per proxy (новое) --------------------
$envWpp = $env:WINDOWS_PER_PROXY
if(-not $envWpp){ $WindowsPerProxy = 10 } else { try { $WindowsPerProxy = [int]$envWpp } catch { $WindowsPerProxy = 10 } }
if($WindowsPerProxy -lt 1){ $WindowsPerProxy = 10 }

# сколько локальных proxy-портов потребуется
$ProxyCount = [int][math]::Ceiling($Count / $WindowsPerProxy)

  $psi.RedirectStandardError  = $true
  $proc = [System.Diagnostics.Process]::Start($psi)
  $w = [System.IO.StreamWriter]::new($rotLog,$true,[System.Text.UTF8Encoding]::new())
  $proc.add_OutputDataReceived({ param($s,$e) if($e.Data){ $w.WriteLine($e.Data) } })
  $proc.add_ErrorDataReceived( { param($s,$e) if($e.Data){ $w.WriteLine($e.Data) } })
  $proc.BeginOutputReadLine(); $proc.BeginErrorReadLine()

  $deadline = (Get-Date).AddSeconds(25)
  $env:LP_COUNT   = "$ProxyCount"
  do {
    Start-Sleep -Milliseconds 300
    $ok = 0
    foreach($p in $needPorts){ if(Test-TcpOpen -HostName "127.0.0.1" -Port $p){ $ok++ } }
    if($ok -eq $needPorts.Count){ break }
  } while((Get-Date) -lt $deadline)
  if($ok -lt $needPorts.Count){ Write-Host ("[!] Поднято {0}/{1} proxy-портов. Лог: {2}" -f $ok,$needPorts.Count,$rotLog) -ForegroundColor Yellow }
  else { Write-Host "[*] Ротатор готов: все локальные proxy-порты подняты." }
} else { Write-Host "[*] Локальные прокси уже подняты." }

# -------------------- СТАРТ ОКОН CHROME --------------------
# УБРАН --host-resolver-rules. Явно задаём прокси для http/https.
$spawned = @()
for($i=0;$i -lt $Count;$i++){
  $devtools = $Devtools0 + $i
  # one local proxy per $WindowsPerProxy windows
  $lport    = $ProxyStart + [int][math]::Floor($i / $WindowsPerProxy)
  $prof     = Join-Path $ProfilesDir ("p{0}" -f ($i+1))
  if(-not (Test-Path $prof)){ New-Item -ItemType Directory -Path $prof -Force | Out-Null }

  $chromeArgs = @(
    "--remote-debugging-port=$devtools",
    "--user-data-dir=$prof",
    "--disk-cache-dir=$CacheDir",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-features=TranslateUI",
    "--proxy-server=http=127.0.0.1:$lport;https=127.0.0.1:$lport",
    "--proxy-bypass-list=<-loopback>",
    "https://www.ozon.ru/"
  )

  Start-Process -FilePath $chrome -ArgumentList $chromeArgs -WindowStyle Normal | Out-Null
  $spawned += $devtools
  Start-Sleep -Milliseconds (600 + (Get-Random -Minimum 0 -Maximum 300))
  if((($i+1) % 10) -eq 0){ Start-Sleep -Seconds 2 }
}

# -------------------- ПРОВЕРКА И ДОЗАПУСК --------------------
Start-Sleep -Seconds 3
$failDev = @()
for($i=0;$i -lt $Count;$i++){
  $dev = $Devtools0 + $i
  if(-not (Test-TcpOpen -HostName "127.0.0.1" -Port $dev)){ $failDev += $i }
}
if($failDev.Count -gt 0){
  Write-Host ("[i] DevTools не поднялись у окон: {0} — перезапускаю" -f (($failDev | ForEach-Object {$_+1}) -join ", "))
  foreach($i in $failDev){
    $devtools = $Devtools0 + $i
    $lport    = $ProxyStart + $i
    $prof     = Join-Path $ProfilesDir ("p{0}" -f ($i+1))
    $chromeArgs = @(
      "--remote-debugging-port=$devtools",
      "--user-data-dir=$prof",
      "--disk-cache-dir=$CacheDir",
      "--no-first-run",
      "--no-default-browser-check",
      "--disable-background-networking",
      "--disable-component-update",
      "--disable-features=TranslateUI",
      "--proxy-server=http=127.0.0.1:$lport;https=127.0.0.1:$lport",
      "--proxy-bypass-list=<-loopback>",
      "https://www.ozon.ru/"
    )
    Start-Process -FilePath $chrome -ArgumentList $chromeArgs -WindowStyle Normal | Out-Null
    Start-Sleep -Milliseconds 900
  }
}

# -------------------- ИТОГОВАЯ ТАБЛИЦА --------------------
$rows = @()
for($i=0;$i -lt $Count;$i++){
  $dev = $Devtools0 + $i
  $lpr = $ProxyStart + $i
  $okDev = Test-TcpOpen -HostName "127.0.0.1" -Port $dev
  $okPrx = Test-TcpOpen -HostName "127.0.0.1" -Port $lpr
  $rows += [PSCustomObject]@{
    idx          = $i+1
    chrome_port  = $dev
    devtools     = if($okDev){"OK"} else {"FAIL"}
    local_proxy  = ("127.0.0.1:{0}" -f $lpr)
    proxy_status = if($okPrx){"OK"} else {"FAIL"}
    profile      = (Join-Path $ProfilesDir ("p{0}" -f ($i+1)))
  }
}
$rows | Format-Table -AutoSize

# -------------------- СТАРТ Ozon3 ЧЕРЕЗ ACTIVATE.PS1 --------------------
if($StartParser){
  $projectRoot   = (Split-Path $PSScriptRoot -Parent)
  $venvActivate  = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"
  $parserPath    = Resolve-Parser
  if((Test-Path $venvActivate) -and $parserPath){
    Write-Host ("[*] Запускаю Ozon3 через venv: {0}" -f $parserPath)
    $ext = [System.IO.Path]::GetExtension($parserPath).ToLowerInvariant()
    switch ($ext) {
      ".py" {
        $cmd = @"
& { Set-Location '$projectRoot'; . '$venvActivate'; python '$parserPath' }
"@
        Start-Process -FilePath "powershell.exe" -ArgumentList "-NoLogo -NoProfile -ExecutionPolicy Bypass -Command $cmd" -WindowStyle Minimized
      }
      ".ps1" {
        $cmd = @"
& { Set-Location '$projectRoot'; . '$venvActivate'; . '$parserPath' }
"@
        Start-Process -FilePath "powershell.exe" -ArgumentList "-NoLogo -NoProfile -ExecutionPolicy Bypass -Command $cmd" -WindowStyle Minimized
      }
      ".bat" {
        $cmd = @"
& { Set-Location '$projectRoot'; . '$venvActivate'; & cmd.exe /c `"$parserPath`" }
"@
        Start-Process -FilePath "powershell.exe" -ArgumentList "-NoLogo -NoProfile -ExecutionPolicy Bypass -Command $cmd" -WindowStyle Minimized
      }
      default { Write-Host "[!] Неизвестный формат парсера: $ext" -ForegroundColor Yellow }
    }
  } else {
    Write-Host "[!] Не найден Activate.ps1 или Ozon3.* — автозапуск пропущен." -ForegroundColor Yellow
  }
}