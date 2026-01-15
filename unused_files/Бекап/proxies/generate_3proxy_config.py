#!/usr/bin/env python3
"""
Генератор конфига 3proxy из upstreams.txt
Автоматически создает конфиг со всеми прокси и ротацией
"""
import sys
from pathlib import Path

# Читаем upstreams.txt
upstreams_file = Path(__file__).parent / "upstreams.txt"
if not upstreams_file.exists():
    print(f"❌ Файл не найден: {upstreams_file}")
    sys.exit(1)

proxies = []
with open(upstreams_file, "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) >= 4:
            host, port, user, passwd = parts[0], parts[1], parts[2], parts[3]
            proxies.append({
                "host": host,
                "port": port,
                "user": user,
                "pass": passwd
            })

if not proxies:
    print("❌ Не найдено прокси в upstreams.txt")
    sys.exit(1)

print(f"✅ Загружено {len(proxies)} прокси")

# Генерируем конфиг
config_lines = [
    "# 3proxy AUTO-GENERATED CONFIG — binds local ports for Ozon parser with proxy rotation",
    "daemon",
    "maxconn 1000",
    "nscache 65536",
    "timeouts 1 5 30 60 180 1800 15 60",
    "",
    "# Логирование",
    "log /var/log/3proxy/3proxy.log D",
    'logformat "L%Y-%m-%d %H:%M:%S %U %C %R %Q %T %J %z %Z %E"',
    "",
    "# Без авторизации для локального доступа",
    "auth none",
    "",
    "# ═══════════════════════════════════════════════════════════════",
    "# UPSTREAM PARENTS (все прокси из upstreams.txt)",
    "# ═══════════════════════════════════════════════════════════════",
]

# Добавляем все upstream прокси
for idx, proxy in enumerate(proxies):
    parent_id = 1000 + idx
    config_lines.append(f"parent {parent_id} http {proxy['host']} {proxy['port']} {proxy['user']} {proxy['pass']}")

config_lines.extend([
    "",
    "# ═══════════════════════════════════════════════════════════════",
    "# LOCAL PROXY INSTANCES (31280+) — выбирают parent round-robin",
    "# ═══════════════════════════════════════════════════════════════",
])

# Генерируем локальные прокси инстансы (31280-31380 = 101 инстанс = для ~100 браузеров)
num_local_proxies = min(len(proxies) * 3, 150)  # 3 порта на каждый upstream (макс 150)
for local_idx in range(num_local_proxies):
    local_port = 31280 + local_idx
    upstream_idx = local_idx % len(proxies)
    parent_id = 1000 + upstream_idx
    config_lines.extend([
        f"proxy -n -a -p{local_port}",
        f"parent {parent_id}",
    ])

config_lines.extend([
    "",
    "# ═══════════════════════════════════════════════════════════════",
    "# HTTP API для ротации (доступно на localhost:3128/rotate и т.д.)",
    "# ═══════════════════════════════════════════════════════════════",
    "# listen 0.0.0.0:3128",
    "# admin",
    "",
    "# Очистка кэша",
    "flush",
    "",
])

# Записываем конфиг с UTF-8
config_file = Path(__file__).parent / "3proxy.cfg"
with open(config_file, "w", encoding="utf-8") as f:
    f.write("\n".join(config_lines))

print(f"✅ Конфиг сгенерирован: {config_file}")
print(f"   • Upstream прокси: {len(proxies)}")
print(f"   • Локальные порты: 31280-{31280 + num_local_proxies - 1} ({num_local_proxies} портов)")
print(f"   • Каждый браузер может использовать port 31280+N")
print(f"\n Для запуска 3proxy:")
print(f"   cd {Path(__file__).parent}")
print(f"   ./3proxy 3proxy.cfg")
