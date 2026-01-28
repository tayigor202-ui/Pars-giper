#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, pathlib, itertools

HERE = pathlib.Path(__file__).resolve().parent
PROXIES_TXT = HERE / "proxies.txt"
CFG_OUT = HERE / "3proxy.cfg"
PORTS_OUT = HERE / "ports.txt"

LOCAL_START = 24001
LOCAL_COUNT = 80          # сколько локальных портов под Chrome
DEBUG_START = 9222        # remote-debugging-port для первого окна

def parse_proxies(lines):
    res = []
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#"): 
            continue
        parts = ln.split(":")
        if len(parts) != 4:
            raise SystemExit(f"Bad proxy line (need host:port:login:password): {ln}")
        host, port, user, pwd = parts
        res.append((host, int(port), user, pwd))
    if not res:
        raise SystemExit("proxies.txt is empty")
    return res

def gen_cfg(proxies):
    # Общие параметры 3proxy
    head = []
    head.append("daemon")
    head.append("nscache 65536")
    head.append("timeouts 1 5 30 60 180 1800 15 60")
    head.append("auth none")
    head.append("")  # пустая строка

    blocks = []
    # Циклично раздаём апстримы на 24001..24080
    for i in range(LOCAL_COUNT):
        local_port = LOCAL_START + i
        host, port, user, pwd = proxies[i % len(proxies)]
        blocks.append(f"# === listener {i+1} | local {local_port} -> {host}:{port} ({user}) ===")
        # parent: <weight> <type> <user> <password> <server> <port>
        blocks.append(f"parent 1000 http {user} {pwd} {host} {port}")
        # локальный http-прокси на нужном порту
        blocks.append(f"proxy -n -a -p{local_port} -i0.0.0.0 -e0.0.0.0")
        blocks.append("flush")
        blocks.append("")

    return "\n".join(head + blocks)

def main():
    lines = PROXIES_TXT.read_text(encoding="utf-8").splitlines()
    proxies = parse_proxies(lines)

    # 1) 3proxy.cfg
    CFG_OUT.write_text(gen_cfg(proxies), encoding="utf-8")
    print(f"[OK] generated {CFG_OUT}")

    # 2) ports.txt (local_port,debug_port)
    #    80 строк: 24001..24080 и 9222..9301
    with PORTS_OUT.open("w", encoding="utf-8") as f:
        for i in range(LOCAL_COUNT):
            local = LOCAL_START + i
            debug = DEBUG_START + i
            f.write(f"{local},{debug}\n")
    print(f"[OK] generated {PORTS_OUT}")

if __name__ == "__main__":
    main()