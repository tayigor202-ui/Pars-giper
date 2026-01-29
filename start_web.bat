@echo off
chcp 65001 >nul
cd /d "F:\Pars-giper"

echo [%DATE% %TIME%] Starting Web Server (Python 3.11)... >> startup_log.txt

"C:\Users\Kerher\AppData\Local\Programs\Python\Python311\python.exe" web_app.py >> startup_log.txt 2>&1
