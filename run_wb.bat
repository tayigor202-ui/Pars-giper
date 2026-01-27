@echo off
chcp 65001 >nul
echo ════════════════════════════════════════════════════════════
echo  ЗАПУСК ПАРСЕРА WILDBERRIES
echo ════════════════════════════════════════════════════════════
echo.

echo [1/2] Проверка зависимостей...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Ошибка: Python не найден!
    pause
    exit /b 1
)

echo [2/2] Запускаем парсер Wildberries...
echo.
python "C:\Users\Kerher\Desktop\ParserProd\wb_parser_production.py"

echo.
echo ✅ Парсер WB завершил работу. Терминал закроется через 3 секунды...
timeout /t 3 /nobreak >nul
exit
