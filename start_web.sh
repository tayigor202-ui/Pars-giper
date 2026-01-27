#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================================================"
echo "            ЗАПУСК ВЕБ-ИНТЕРФЕЙСА OZON/WB PARSER"
echo "======================================================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}[ОШИБКА] Файл .env не найден!${NC}"
    echo ""
    echo "Сначала выполните установку:"
    echo "    ./install.sh"
    echo ""
    echo "Или:"
    echo "    python3 setup.py"
    echo ""
    exit 1
fi

echo "Запуск веб-сервера..."
echo ""
echo "Веб-интерфейс будет доступен по адресу:"
echo -e "    ${BLUE}http://localhost:3455${NC}"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""
echo "======================================================================"
echo ""

python3 web_app.py
