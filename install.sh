#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================================================"
echo "          АВТОМАТИЧЕСКАЯ УСТАНОВКА OZON/WB PARSER"
echo "======================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ОШИБКА] Python3 не найден!${NC}"
    echo ""
    echo "Установите Python 3.8 или выше:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "  macOS: brew install python3"
    echo ""
    exit 1
fi

echo -e "${GREEN}[OK] Python найден${NC}"
python3 --version
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}[ПРЕДУПРЕЖДЕНИЕ] PostgreSQL не найден${NC}"
    echo ""
    echo "Установите PostgreSQL:"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "  macOS: brew install postgresql"
    echo ""
    read -p "Продолжить установку? (y/n): " continue
    if [ "$continue" != "y" ]; then
        exit 1
    fi
else
    echo -e "${GREEN}[OK] PostgreSQL найден${NC}"
    psql --version
fi

echo ""
echo "======================================================================"
echo "Запуск автоматической установки..."
echo "======================================================================"
echo ""

# Run setup.py
python3 setup.py

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}[ОШИБКА] Установка завершилась с ошибкой${NC}"
    exit 1
fi

echo ""
echo "======================================================================"
echo "                  УСТАНОВКА ЗАВЕРШЕНА!"
echo "======================================================================"
echo ""
echo "Для запуска веб-интерфейса выполните:"
echo "    python3 web_app.py"
echo ""
echo "Или используйте:"
echo "    ./start_web.sh"
echo ""
