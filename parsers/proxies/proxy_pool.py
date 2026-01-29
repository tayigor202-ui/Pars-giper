import os, time, random, tempfile, shutil, json
from dataclasses import dataclass
from typing import List, Optional, Tuple

import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPSTREAMS = os.path.join(ROOT, "proxies", "upstreams.txt")

@dataclass
class Proxy:
    host: str
    port: int
    user: str
    pwd: str

    @property
    def server(self) -> str:
        return f"http://{self.host}:{self.port}"

    def as_requests(self) -> dict:
        auth = f"{self.user}:{self.pwd}@" if self.user and self.pwd else ""
        # requests прокси без встроенной авторизации — укажем отдельно:
        return {
            "http":  f"http://{self.host}:{self.port}",
            "https": f"http://{self.host}:{self.port}",
        }

class ProxyPool:
    def __init__(self, path: str = UPSTREAMS, healthcheck: bool = True, timeout=5.0, sample=None):
        self.path = path
        self.timeout = timeout
        self._proxies: List[Proxy] = self._load()
        if sample:
            self._proxies = self._proxies[:sample]
        if healthcheck:
            self._proxies = self._check_all(self._proxies)
            if not self._proxies:
                raise RuntimeError("No alive proxies after healthcheck")
        self._i = 0

    def _load(self) -> List[Proxy]:
        if not os.path.exists(self.path):
            print(f"[PROXY] Warning: {self.path} not found. Pool will be empty.")
            return []
        items: List[Proxy] = []
        with open(self.path, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith("#"):
                    continue
                parts = ln.split(":")
                if len(parts) >= 4:
                    host = parts[0].strip()
                    port = int(parts[1].strip())
                    user = parts[2].strip()
                    pwd  = ":".join(parts[3:]).strip()
                    items.append(Proxy(host, port, user, pwd))
                elif len(parts) == 2:
                    items.append(Proxy(parts[0].strip(), int(parts[1].strip()), "", ""))
        random.shuffle(items)
        return items

    def _check_all(self, items: List[Proxy]) -> List[Proxy]:
        alive = []
        for p in items:
            try:
                r = requests.get("https://httpbin.org/ip",
                                 proxies=p.as_requests(),
                                 timeout=self.timeout,
                                 auth=(p.user, p.pwd) if p.user and p.pwd else None)
                if r.ok:
                    alive.append(p)
            except Exception:
                pass
        return alive

    def next(self) -> Proxy:
        p = self._proxies[self._i % len(self._proxies)]
        self._i += 1
        return p

    # -------- Chrome proxy auth extension --------
    def build_chrome_auth_extension(self, proxy: Proxy) -> str:
        """
        Создаёт временное расширение для Chrome, которое внедряет
        логин/пароль на прокси через onAuthRequired.
        Возвращает путь к папке расширения.
        """
        temp_dir = tempfile.mkdtemp(prefix="chrome_proxy_ext_")
        manifest = {
          "version": "1.0.0",
          "manifest_version": 2,
          "name": "Chrome Proxy Auth",
          "permissions": [
            "proxy", "tabs", "unlimitedStorage", "storage", "<all_urls>", "webRequest", "webRequestBlocking"
          ],
          "background": {"scripts": ["background.js"]},
          "minimum_chrome_version":"22.0.0"
        }
        bg = f"""
var config = {{
    mode: "fixed_servers",
    rules: {{
      singleProxy: {{
        scheme: "http",
        host: "{proxy.host}",
        port: {proxy.port}
      }},
      bypassList: ["localhost"]
    }}
}};
chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{ }});
function callbackFn(details) {{
    return {{
        authCredentials: {{
            username: "{proxy.user}",
            password: "{proxy.pwd}"
        }}
    }};
}}
chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    {{urls: ["<all_urls>"]}},
    ['blocking']
);
        """.strip()

        with open(os.path.join(temp_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        with open(os.path.join(temp_dir, "background.js"), "w", encoding="utf-8") as f:
            f.write(bg)
        return temp_dir