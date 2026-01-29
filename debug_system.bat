@echo off
echo === SYSTEM DIAGNOSTICS ===
echo.
echo 1. Current User:
whoami
echo.
echo 2. Current Directory:
cd
echo.
echo 3. Python Check:
where python
python --version
echo.
echo 4. Py Launcher Check:
where py
py --version
echo.
echo 5. .env File Check:
if exist .env (echo [.env exists]) else (echo [.env missing])
echo.
echo 6. Path Variable:
echo %PATH%
echo.
echo === DIAGNOSTICS COMPLETE ===
pause
