@echo off
chcp 65001 >nul

echo Проверка и запуск прокси...

REM Проверяем запущен ли прокси на порту 8118
netstat -an | findstr ":8118" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Прокси уже работает на порту 8118
) else (
    echo Запуск прокси в фоновом режиме...
    start /B "" python "C:\Users\Kerher\Desktop\ParserProd\proxies\auth_forwarder.py" --config "C:\Users\Kerher\Desktop\ParserProd\upstreams.txt" --listen-start 8118
    timeout /t 5 /nobreak >nul
    echo Прокси запущен
)

echo.
echo Запуск парсера Ozon...
echo.

python "C:\Users\Kerher\Desktop\ParserProd\ozon_parser_production_final.py"

echo.
echo Парсер завершил работу
