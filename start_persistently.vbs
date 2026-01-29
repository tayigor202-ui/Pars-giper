Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "F:\Pars-giper"
WshShell.Run "cmd /c start_web.bat", 0, False
