@echo off
chcp 65001 >nul
cd /d "F:\Pars-giper"

echo [SYSTEM] Настройка автозапуска...

REM Use PowerShell to get the correct user name even when elevated
for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "whoami"`) do set CURRENT_USER=%%a

echo Текущий пользователь: %CURRENT_USER%

if "%CURRENT_USER%"=="" (
    echo [ERROR] Не удалось определить пользователя.
    pause
    exit /b 1
)

REM Method 1: Task Scheduler (Best for background reliability)
echo [1/2] Регистрация в Планировщике задач...
schtasks /delete /tn "ParsGiper_WebServer" /f >nul 2>&1
schtasks /create /tn "ParsGiper_WebServer" /tr "wscript.exe F:\Pars-giper\start_persistently.vbs" /sc onlogon /ru "%CURRENT_USER%" /rl HIGHEST /f

if %errorlevel% equ 0 (
    echo [SUCCESS] Задание в Планировщике создано.
) else (
    echo [WARNING] Планировщик не принял задание (может требовать пароль).
)

REM Method 2: Startup Folder (Most reliable fallback)
echo [2/2] Создание ярлыка в папке Автозагрузка...
powershell -ExecutionPolicy Bypass -File "F:\Pars-giper\create_startup_shortcut.ps1"

echo.
echo ======================================================================
echo Настройка завершена! 
echo Если планировщик выдал ошибку, ярлык в "Автозагрузке" всё равно сработает.
echo ======================================================================
pause
