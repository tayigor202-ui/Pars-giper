# Быстрая установка Pars-Giper

Этот документ описывает процесс установки проекта на чистой машине.

## Требования

- **Windows 10/11** или **Linux**
- **Python 3.11+** (рекомендуется 3.11, так как все зависимости уже установлены для этой версии)
- **PostgreSQL 12+**
- **Git**
- **Google Chrome** (для парсеров)

## Установка за 3 шага

### 1. Клонирование репозитория

```bash
git clone https://github.com/tayigor202-ui/Pars-giper.git
cd Pars-giper
```

### 2. Автоматическая установка

**Windows:**
```bash
install.bat
```

**Linux/Mac:**
```bash
python setup/setup.py
```

Скрипт автоматически:
- ✅ Проверит версию Python (требуется 3.8+)
- ✅ Проверит наличие PostgreSQL
- ✅ Установит все Python зависимости из `requirements.txt`
- ✅ Создаст файл `.env` с настройками базы данных
- ✅ Создаст базу данных `ozon_parser` (если её нет)
- ✅ Создаст все необходимые таблицы
- ✅ Создаст пользователя `admin` с паролем `admin`
- ✅ Создаст файл `config.json`

### 3. Запуск веб-интерфейса

```bash
# Обычный запуск (с видимым окном)
start_web.bat

# Или фоновый запуск (без окна)
start_persistently.vbs
```

Откройте в браузере: **http://localhost:3455**

**Логин:** `admin`  
**Пароль:** `admin`

⚠️ **Обязательно смените пароль после первого входа!**

## Настройка после установки

### 1. Базовые настройки (через веб-интерфейс)

1. Перейдите в раздел **Настройки**
2. Укажите:
   - URL Google Sheets для Ozon
   - URL Google Sheets для Wildberries
   - URL Google Sheets для Lemana Pro (если используется)
3. Сохраните изменения

### 2. Telegram (опционально)

1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Получите Bot Token
3. Добавьте бота в ваш чат/канал
4. Получите Chat ID через [@userinfobot](https://t.me/userinfobot)
5. Введите Token и Chat ID в разделе **Настройки → Telegram**

### 3. Импорт данных

1. Перейдите в раздел **Настройки**
2. Нажмите **"Импортировать OZON"**
3. Нажмите **"Импортировать WB"**
4. Нажмите **"Импортировать Lemana"** (если используется)

### 4. Автозапуск при старте Windows (опционально)

**Запустите от имени Администратора:**
```bash
add_to_startup.bat
```

Теперь веб-сервер будет автоматически запускаться при входе в Windows в фоновом режиме.

## Проверка установки

### 1. Проверка веб-интерфейса

- Откройте http://localhost:3455
- Вы должны увидеть страницу входа
- Войдите с учётными данными `admin / admin`

### 2. Проверка базы данных

```bash
python check_tables.py
```

Должны быть созданы таблицы:
- `prices` (Ozon)
- `wb_prices` (Wildberries)
- `lemana_prices` (Lemana Pro)
- `users` (пользователи)

### 3. Проверка парсеров

**Ozon:**
```bash
cd parsers
python ozon_parser_production_final.py
```

**Wildberries:**
```bash
cd parsers
python wb_parser_production.py
```

**Lemana Pro:**
```bash
cd parsers
python lemana_parser_production.py
```

## Устранение проблем

### PostgreSQL не найден

**Windows:**
1. Скачайте PostgreSQL с https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
2. Установите (запомните пароль для пользователя `postgres`)
3. Добавьте в PATH: `C:\Program Files\PostgreSQL\15\bin`

**Linux:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

### Python не найден

**Windows:**
1. Скачайте Python 3.11 с https://www.python.org/downloads/
2. При установке **обязательно** отметьте "Add Python to PATH"

**Linux:**
```bash
sudo apt-get install python3.11 python3.11-pip
```

### Ошибка подключения к базе данных

1. Убедитесь, что PostgreSQL запущен:
   ```bash
   # Windows
   pg_ctl status
   
   # Linux
   sudo systemctl status postgresql
   ```

2. Проверьте файл `.env`:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=ozon_parser
   DB_USER=postgres
   DB_PASS=ваш_пароль
   ```

3. Попробуйте подключиться вручную:
   ```bash
   psql -U postgres -h localhost
   ```

### Ошибки при установке зависимостей

```bash
# Обновите pip
python -m pip install --upgrade pip

# Переустановите зависимости
pip install -r requirements.txt --force-reinstall
```

### Chrome не найден

Парсеры требуют установленный Google Chrome:
- **Windows:** https://www.google.com/chrome/
- **Linux:** `sudo apt-get install google-chrome-stable`

## Дополнительные команды

### Обновление проекта

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Очистка данных

```bash
# Очистить все цены
python scripts/clear_all_data.py

# Пересоздать таблицы
python setup/setup_database_and_users.py
```

### Просмотр логов

```bash
# Логи веб-сервера
type startup_log.txt

# Логи парсеров (в консоли при запуске)
```

## Структура проекта

```
Pars-Giper/
├── install.bat                      # Автоустановка (Windows)
├── start_web.bat                    # Запуск веб-сервера
├── start_persistently.vbs           # Фоновый запуск
├── add_to_startup.bat               # Настройка автозапуска
├── web_app.py                       # Веб-интерфейс
├── .env                             # Конфигурация (создаётся при установке)
├── config.json                      # Настройки (создаётся при установке)
├── requirements.txt                 # Python зависимости
├── setup/
│   ├── setup.py                     # Скрипт установки
│   └── setup_database_and_users.py  # Настройка БД
├── parsers/
│   ├── ozon_parser_production_final.py
│   ├── wb_parser_production.py
│   └── lemana_parser_production.py
├── scripts/
│   ├── import_ozon_from_sheets.py
│   ├── import_wb_from_sheets.py
│   ├── import_lemana_from_sheets.py
│   ├── wb_reporting.py
│   └── lemana_reporting.py
├── core/
│   ├── scheduler.py                 # Планировщик задач
│   ├── user_management.py           # Управление пользователями
│   └── lemana_utils.py              # Утилиты Lemana
└── templates/                       # HTML шаблоны
```

## Следующие шаги

После успешной установки:

1. ✅ Настройте Google Sheets URLs
2. ✅ Импортируйте данные
3. ✅ Настройте Telegram (опционально)
4. ✅ Настройте расписание парсинга
5. ✅ Настройте автозапуск (опционально)

Готово! Система полностью настроена и готова к работе.
