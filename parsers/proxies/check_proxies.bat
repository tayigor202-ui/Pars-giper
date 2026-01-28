@echo off
REM Проверка что 3proxy работает и прокси функциональны
REM Usage: check_proxies.bat [кол-во проверок] [интервал сек]

setlocal enabledelayedexpansion

set CHECKS=%1
if "%CHECKS%"=="" set CHECKS=5

set INTERVAL=%2
if "%INTERVAL%"=="" set INTERVAL=2

set PROXY_PORT=31280
set TEST_URL=http://ipinfo.io/ip

echo.
echo ════════════════════════════════════════════════════════════
echo  Проверка прокси портов 31280-31290
echo  Проверок: %CHECKS%, Интервал: %INTERVAL% сек
echo ════════════════════════════════════════════════════════════
echo.

REM Проверяем 31280-31289 (10 портов)
for /L %%P in (0, 1, 9) do (
    set /A PORT=31280+%%P
    set /A CHECK=0
    
    :retry
    set /A CHECK+=1
    
    if !CHECK! leq %CHECKS% (
        echo [!PORT!] попытка !CHECK!/%CHECKS% ...
        
        REM Пытаемся получить IP
        for /f %%A in ('curl -s -x http://127.0.0.1:!PORT! %TEST_URL% 2^>nul') do (
            if not "%%A"=="" (
                echo   ✅ Ответ: %%A
                goto next_port
            )
        )
        
        echo   ⏳ Жду %INTERVAL% сек...
        timeout /t %INTERVAL% /nobreak > nul
        goto retry
    )
    
    echo   ❌ ОШИБКА: нет ответа
    
    :next_port
)

echo.
echo ════════════════════════════════════════════════════════════
echo  Проверка завершена
echo ════════════════════════════════════════════════════════════
echo.
echo Примечания:
echo   • Каждый порт должен вернуть разный IP
echo   • Если получается один IP - прокси может быть неправильно настроен
echo   • Если нет ответа - 3proxy не запущен или порт заблокирован
echo.

pause
