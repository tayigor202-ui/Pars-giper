# OZON Parser - Flask Web Service

## Установка как Windows Service

Веб-интерфейс Flask работает как Windows Service, который:
- ✅ Запускается автоматически при загрузке Windows
- ✅ Работает в фоне постоянно
- ✅ Автоматически перезапускается при сбоях
- ✅ Записывает логи в `logs/` директорию

## Требования

Скачайте **NSSM** (Non-Sucking Service Manager):
1. Перейдите: https://nssm.cc/download
2. Скачайте последнюю версию
3. Извлеките `nssm.exe` (x64 версию) в папку `C:\Users\Kerher\Desktop\ParserProd\`

## Установка сервиса

1. **Запустите как Администратор**: `install_web_service.bat`
2. Скрипт автоматически:
   - Установит Flask как Windows Service
   - Настроит автозапуск при загрузке системы
   - Настроит автоперезапуск при сбоях (через 5 сек)
   - Создаст логи в `logs/web_service_*.log`

## Управление сервисом

### Через командную строку:
```cmd
# Запустить
nssm start OzonParserWeb

# Остановить
nssm stop OzonParserWeb

# Перезапустить
nssm restart OzonParserWeb

# Проверить статус
sc query OzonParserWeb
```

### Через Службы Windows:
1. Нажмите `Win+R` → введите `services.msc`
2. Найдите службу: **OZON Parser Web Dashboard**
3. ПКМ → Запустить/Остановить/Перезапустить

## Удаление сервиса

Запустите как Администратор: `uninstall_web_service.bat`

## Логи

Логи сохраняются в:
- `logs/web_service_stdout.log` - вывод приложения
- `logs/web_service_stderr.log` - ошибки

## Проверка работы

После установки откройте браузер:
- **URL**: http://localhost:3454
- **Логин**: admin
- **Пароль**: admin

## Устранение проблем

### Сервис не запускается:
1. Проверьте логи в `logs/web_service_stderr.log`
2. Убедитесь что Python установлен и доступен из командной строки
3. Проверьте что все зависимости установлены: `pip install -r requirements.txt`

### Порт 3454 занят:
1. Остановите сервис: `nssm stop OzonParserWeb`
2. Измените порт в `web_app.py` (строка с `app.run`)
3. Переустановите сервис

### После обновления кода:
```cmd
nssm restart OzonParserWeb
```
