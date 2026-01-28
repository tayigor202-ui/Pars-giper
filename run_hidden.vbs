Set WshShell = CreateObject("WScript.Shell")
Dim args, i
args = ""
For i = 0 to WScript.Arguments.Count - 1
   args = args & " " & chr(34) & WScript.Arguments(i) & chr(34)
Next
WshShell.Run "cmd /c" & args, 0, False
