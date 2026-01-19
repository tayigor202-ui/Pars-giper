# proxies/auth_forwarder.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket, base64, threading, selectors, time, argparse, pathlib

BUF = 65536
CONNECT_TIMEOUT = 20
IDLE_TIMEOUT = 180

def log(msg):
    try:
        with open("proxy_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except: pass

def parse_config(path):
    rows = []
    for raw in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"): continue
        host, port, user, pw = s.split(":", 3)
        rows.append((host, int(port), user, pw))
    return rows

import random, string



def read_headers(sock, maxlen=65536):
    """Читает до \r\n\r\n и ВЫЧИТЫВАЕТ из буфера (без PEEK)."""
    data = b""
    sock.settimeout(CONNECT_TIMEOUT)
    while b"\r\n\r\n" not in data and len(data) < maxlen:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    return data

def pump(a, b):
    sel = selectors.DefaultSelector()
    a.setblocking(False); b.setblocking(False)
    sel.register(a, selectors.EVENT_READ)
    sel.register(b, selectors.EVENT_READ)
    last = time.time()
    try:
        while True:
            events = sel.select(1.0)
            if time.time() - last > IDLE_TIMEOUT:
                return
            for key, _ in events:
                src = key.fileobj
                dst = b if src is a else a
                try:
                    buf = src.recv(BUF)
                except BlockingIOError:
                    continue
                if not buf:
                    return
                dst.sendall(buf)
                last = time.time()
    finally:
        for s in (a, b):
            try: s.shutdown(socket.SHUT_RDWR)
            except: pass
            try: s.close()
            except: pass

def handle_client(cli, up_host, up_port, user, pw):
    # читаем ПОЛНОСТЬЮ стартовые заголовки клиента
    first = read_headers(cli)
    if not first:
        cli.close(); return

    first_line = first.split(b"\r\n", 1)[0].decode(errors="ignore")
    log(f"Request: {first_line}")
    
    is_connect = first_line.upper().startswith("CONNECT ")

    # коннект к апстриму
    try:
        ups = socket.create_connection((up_host, up_port), CONNECT_TIMEOUT)
    except Exception as e:
        log(f"Upstream connect error: {e}")
        cli.close(); return

    # уменьшаем залипания
    for s in (cli, ups):
        try: s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except: pass

    if is_connect:
        # host:port из CONNECT
        try:
            _, target, _ = first_line.split(" ", 2)
        except ValueError:
            cli.close(); ups.close(); return

        # отправляем свой CONNECT (с auth)
        req = (
            f"CONNECT {target} HTTP/1.1\r\n"
            f"Host: {target}\r\n"
            f"{auth_hdr(user, pw)}"
            "Proxy-Connection: keep-alive\r\n"
            "Connection: keep-alive\r\n"
            "\r\n"
        ).encode()
        ups.sendall(req)

        # читаем ответ апстрима ДО \r\n\r\n
        resp = read_headers(ups)
        
        # Разделяем заголовки и возможное тело (если считали лишнее)
        parts = resp.split(b"\r\n\r\n", 1)
        head = parts[0]
        extra = parts[1] if len(parts) > 1 else b""
        
        log(f"Upstream response: {head.decode(errors='ignore')}")
        
        if b" 200 " not in head:
            try: cli.sendall(resp)
            except: pass
            cli.close(); ups.close(); return

        # даём клиенту чистое 200 (без хвостов)
        try:
            cli.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            # Если считали кусок тела (handshake и т.д.), отдаём клиенту
            if extra:
                log(f"Forwarding {len(extra)} bytes of extra data")
                cli.sendall(extra)
        except:
            cli.close(); ups.close(); return

        # запускаем чистый туннель
        pump(cli, ups)

    else:
        # это обычный HTTP-запрос. Вставляем Proxy-Authorization (если не было) и пробрасываем.
        if b"Proxy-Authorization:" not in first:
            # вставим сразу после первой строки
            p = first.find(b"\r\n")
            first = first[:p+2] + auth_hdr(user, pw).encode() + first[p+2:]
        ups.sendall(first)
        pump(cli, ups)

def serve(listener, up_host, up_port, user, pw):
    while True:
        try:
            cli, _ = listener.accept()
        except OSError:
            return
        threading.Thread(target=handle_client, args=(cli, up_host, up_port, user, pw), daemon=True).start()

def auth_hdr(user, pw):
    # Base encoding for the user as provided (which may already have a session)
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return f"Proxy-Authorization: Basic {token}\r\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--listen-start", type=int, required=True)
    ap.add_argument("--count", type=int, default=1, help="Number of ports to open for sessions")
    args = ap.parse_args()

    entries = parse_config(args.config)
    if not entries:
        print("[!] No entries in config")
        return

    listeners = []
    
    # We will open 'count' ports for EACH entry in upstreams
    # Default count is 1, but we can increase it for workers
    for idx, (h, p, u, w) in enumerate(entries):
        for offset in range(args.count):
            lp = args.listen_start + (idx * args.count) + offset
            
            # Generate a STICKY session for this specific port
            # This ensures that all requests through port LP use the same exit IP
            sticky_user = u
            if "-session-" not in sticky_user:
                session_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
                sticky_user = f"{sticky_user}-session-{session_id}"
            
            ls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                ls.bind(("0.0.0.0", lp))
                ls.listen(256)
                threading.Thread(target=serve, args=(ls, h, p, sticky_user, w), daemon=True).start()
                listeners.append(ls)
                print(f"[L] 0.0.0.0:{lp} -> {h}:{p} (Sticky session: ...{sticky_user[-8:]})")
            except Exception as e:
                print(f"[!] Failed to bind port {lp}: {e}")

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        for ls in listeners:
            try: ls.close()
            except: pass

if __name__ == "__main__":
    main()