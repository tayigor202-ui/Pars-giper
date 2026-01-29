$WshShell = New-Object -ComObject WScript.Shell
$ShortcutPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\ParsGiper.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "F:\Pars-giper\start_persistently.vbs"
$Shortcut.WorkingDirectory = "F:\Pars-giper"
$Shortcut.Save()
Write-Host "Shortcut created in Startup folder: $ShortcutPath"
