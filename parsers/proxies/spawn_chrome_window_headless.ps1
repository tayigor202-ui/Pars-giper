param([int]$dev,[int]$lproxy,[string]$prof)
if(-not $dev -or -not $lproxy -or -not $prof){ Write-Error "Usage: spawn_chrome_window_headless.ps1 <dev> <lproxy> <prof>"; exit 2 }

$chrome=(Get-Command chrome.exe -ErrorAction SilentlyContinue).Source
if(-not $chrome){
    $c='C:\Program Files\Google\Chrome\Application\chrome.exe'
    if(Test-Path $c){ $chrome=$c }
    else {
        $c2="$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
        if(Test-Path $c2){ $chrome=$c2 }
        else { Write-Error 'Chrome not found'; exit 3 }
    }
}
if(-not (Test-Path $prof)){ New-Item -ItemType Directory -Path $prof -Force | Out-Null }
$argsList=@(
    "--headless",
    "--remote-debugging-port=$dev",
    "--user-data-dir=$prof",
    "--no-first-run",
    "--no-default-browser-check",
    "--proxy-server=http=127.0.0.1:$lproxy;https=127.0.0.1:$lproxy",
    "https://www.ozon.ru/"
)
Start-Process -FilePath $chrome -ArgumentList $argsList -WindowStyle Hidden | Out-Null
Write-Host "[*] spawn_chrome_window_headless: started devtools=$dev local_proxy=$lproxy profile=$prof (headless mode)"
