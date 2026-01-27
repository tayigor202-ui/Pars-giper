@echo off
set "PYTHONW_PATH=C:\Users\Kerher\AppData\Local\Programs\Python\Python311\pythonw.exe"
cd /d "%~dp0"
echo Starting Ozon Parser Web UI in background...
start "" "%PYTHONW_PATH%" web_app.py
echo Web UI started in background on http://localhost:3455
pause
