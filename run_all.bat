@echo off
chcp 65001 >nul
echo ════════════════════════════════════════════════════════════
echo  ЗАПУСК ВСЕЙ СИСТЕМЫ (ПРОКСИ + ПАРСЕР)
echo ════════════════════════════════════════════════════════════
echo.

echo [1/2] Запускаем прокси-сервер в отдельном окне...
start "Proxy Server" cmd /c "C:\Users\Kerher\Desktop\ParserProd\start_3proxy.bat"

echo.
echo ⏳ Ждем 5 секунд для инициализации прокси...
timeout /t 5 /nobreak >nul

echo.
echo [2/2] Запускаем парсер Ozon...
echo.
python "C:\Users\Kerher\Desktop\ParserProd\ozon_parser_production_final.py"

echo.
echo ✅ Парсер завершил работу. Терминал закроется через 3 секунды...
timeout /t 3 /nobreak >nul
exit
