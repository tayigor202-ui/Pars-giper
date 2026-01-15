# proxies/auth_rotator.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64, os, socket, sys, threading, time, selectors
from pathlib import Path
from typing import List, Tuple

LISTEN_HOST      = "127.0.0.1"
LISTEN_START     = int(os.getenv("LP_START", "31280"))   # первый локальный порт
LISTEN_COUNT     = int(os.getenv("LP_COUNT", "40"))      # сколько локальных портов поднять
UPSTREAMS_FILE   = os.getenv("UPSTREAMS") or str((Path(__file__).parent / "upstreams.txt").resolve())
ROTATE_SEC       = int(os.getenv("ROTATE_SEC", "600"))   # каждые N сек сдвигать соответствия local_port → upstream
HEALTH_EVERY_SEC = int(os.getenv("HEALTH_SEC", "30"))    # как часто проверять апстримы
CONNECT_TIMEOUT  = float(os.getenv("CONNECT_TIMEOUT", "7.0"))
BUF              = 65536

print("[cfg] LP_START=%d LP_COUNT=%d ROTATE_SEC=%d HEALTH_SEC=%d" %
      (LISTEN_START, LISTEN_COUNT, ROTATE_SEC, HEALTH_EVERY_SEC))
print("[cfg] UPSTREAMS=%s" % UPSTREAMS_FILE)

# ── Загрузка апстримов ──────────────────────────────────────────────────────────
def load_upstreams(path: str) -> List[Tuple[str,int,str,str]]:
    p = Path(path)
    if not p.is_file():
        print("[err] upstreams file not found: %s" % path); sys.exit(2)
    rows = []
    for raw in p.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"): continue
        host, port, user, pw = s.split(":", 3)
        rows.append((host, int(port), user, pw))
    if not rows:
        print("[err] upstreams file is empty: %s" % path); sys.exit(2)
    return rows

UPSTREAMS = load_upstreams(UPSTREAMS_FILE)
U_N = len(UPSTREAMS)
print("[cfg] upstreams: %d" % U_N)

# ── Healthcheck ────────────────────────────────────────────────────────────────
_up_health = [True]*U_N
_up_lock = threading.Lock()

def _test_connect(idx: int) -> bool:
    host, port, user, pw = UPSTREAMS[idx]
    try:
        s = socket.create_connection((host, port), timeout=CONNECT_TIMEOUT)
        s.settimeout(CONNECT_TIMEOUT)
        token = base64.b64encode(("%s:%s" % (user, pw)).encode()).decode()
        req = ("CONNECT httpbin.org:443 HTTP/1.1\r\n"
               "Host: httpbin.org:443\r\n"
               "Proxy-Authorization: Basic %s\r\n"
               "Proxy-Connection: keep-alive\r\n\r\n") % token
        s.sendall(req.encode())
        resp = s.recv(4096)
        ok = (b" 200 " in resp) or (b"200 Connection established" in resp) or (b"200 Connection Established" in resp)
        s.close()
        return ok
    except Exception:
        return False

def health_loop():
    while True:
        for i in range(U_N):
            ok = _test_connect(i)
            with _up_lock:
                _up_health[i] = ok
        time.sleep(HEALTH_EVERY_SEC)

# ── Назначение апстримов локальным портам ──────────────────────────────────────
_bind_offset = 0
_bind_lock = threading.Lock()

def choose_upstream_for_local(local_idx: int) -> int:
    # round-robin + учёт health
    with _bind_lock:
        base = (local_idx + _bind_offset) % U_N
    with _up_lock:
        for k in range(U_N):
            j = (base + k) % U_N
            if _up_health[j]:
                return j
    return base

def rotate_bindings():
    global _bind_offset
    while True:
        time.sleep(ROTATE_SEC)
        with _bind_lock:
            _bind_offset = (_bind_offset + 1) % U_N
        print("[rotate] offset=%d" % _bind_offset)

# ── Вспомогательные ────────────────────────────────────────────────────────────
def with_proxy_auth(raw_headers: bytes, idx: int) -> bytes:
    host, port, user, pw = UPSTREAMS[idx]
    token = base64.b64encode(("%s:%s" % (user, pw)).encode()).decode()
    if b"Proxy-Authorization:" in raw_headers:
        return raw_headers
    # вставляем перед пустой строкой
    return raw_headers.replace(b"\r\n\r\n",
                               ("\\r\\nProxy-Authorization: Basic %s\\r\\n\\r\\n" % token)
                               .encode().decode("unicode_escape").encode())

def pump(a: socket.socket, b: socket.socket):
    sel = selectors.DefaultSelector()
    a.setblocking(False); b.setblocking(False)
    sel.register(a, selectors.EVENT_READ, data=b)
    sel.register(b, selectors.EVENT_READ, data=a)
    try:
        while True:
            for key, _ in sel.select(timeout=30):
                src = key.fileobj
                dst = key.data
                try:
                    buf = src.recv(BUF)
                    if not buf:
                        return
                    dst.sendall(buf)
                except Exception:
                    return
    finally:
        try: sel.close()
        except: pass
        for s in (a,b):
            try: s.shutdown(socket.SHUT_RDWR)
            except: pass
            try: s.close()
            except: pass

def handle_client(client: socket.socket, local_idx: int):
    client.settimeout(CONNECT_TIMEOUT)
    try:
        req = b""
        while b"\r\n\r\n" not in req and len(req) < 65536:
            chunk = client.recv(4096)
            if not chunk:
                client.close(); return
            req += chunk
    except Exception:
        try: client.close()
        except: pass
        return

    try:
        first = req.split(b"\r\n",1)[0]
        method, target, _ = first.split(b" ", 2)
    except Exception:
        try: client.close()
        except: pass
        return

    up_idx = choose_upstream_for_local(local_idx)
    host, port, user, pw = UPSTREAMS[up_idx]

    try:
        upstream = socket.create_connection((host, port), timeout=CONNECT_TIMEOUT)
        upstream.settimeout(CONNECT_TIMEOUT)
    except Exception:
        try: client.close()
        except: pass
        return

    try:
        if method == b"CONNECT":
            token = base64.b64encode(("%s:%s" % (user, pw)).encode()).decode()
            msg = (b"CONNECT " + target + b" HTTP/1.1\r\n"
                   b"Host: " + target + b"\r\n"
                   b"Proxy-Authorization: Basic " + token.encode() + b"\r\n"
                   b"Proxy-Connection: keep-alive\r\n\r\n")
            upstream.sendall(msg)
            resp = upstream.recv(4096)
            if b" 200 " not in resp:
                try: client.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                except: pass
                upstream.close(); client.close(); return
            try: client.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            except Exception: pass
            pump(client, upstream)
        else:
            upstream.sendall(with_proxy_auth(req, up_idx))
            pump(client, upstream)
    except Exception:
        try: upstream.close()
        except: pass
        try: client.close()
        except: pass

class Listener(threading.Thread):
    def __init__(self, idx: int):
        super().__init__(daemon=True)
        self.idx = idx
        self.port = LISTEN_START + idx
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((LISTEN_HOST, self.port))
        self.sock.listen(256)

    def run(self):
        print("[L] listen %s:%d" % (LISTEN_HOST, self.port))
        while True:
            try:
                c, _ = self.sock.accept()
                threading.Thread(target=handle_client, args=(c, self.idx), daemon=True).start()
            except Exception:
                time.sleep(0.05)

def main():
    threading.Thread(target=health_loop, daemon=True).start()
    threading.Thread(target=rotate_bindings, daemon=True).start()
    listeners = [Listener(i) for i in range(LISTEN_COUNT)]
    for L in listeners: L.start()
    try:
        while True:
            with _bind_lock: off = _bind_offset
            with _up_lock: health = "".join(["." if h else "x" for h in _up_health])
            print("[status] offset=%d health[%d]=%s" % (off, U_N, health))
            time.sleep(20)
    except KeyboardInterrupt:
        print("bye")

if __name__ == "__main__":
    main()