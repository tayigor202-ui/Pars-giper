try {
  [System.Management.Automation.Language.Parser]::ParseFile('C:\Users\Kerher\Desktop\ParserProd\proxies\spawn_chrome_window.ps1',[ref]$null,[ref]$null)
  Write-Output 'OK'
} catch {
  Write-Output ("ERROR: " + $_.Exception.Message)
  exit 1
}
