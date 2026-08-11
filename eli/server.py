"""Local HTTP server that feeds the runtime bundle and on-demand translations."""

from __future__ import annotations

import http.server
import json
import os
import threading
import urllib.parse

from .translate import Translator

HERE = os.path.dirname(os.path.abspath(__file__))


def build_bundle(dict_path: str | None, api: str, skip_selectors: list[str]) -> str:
    runtime = open(os.path.join(HERE, "runtime.js"), encoding="utf-8").read()
    dictionary = {}
    if dict_path and os.path.exists(dict_path):
        try:
            dictionary = json.load(open(dict_path, encoding="utf-8"))
        except Exception:
            dictionary = {}
    cfg = {"api": api, "skipSelectors": skip_selectors, "dict": dictionary}
    return "window.__ELI_CONFIG = " + json.dumps(cfg, ensure_ascii=False) + ";\n" + runtime


def serve(port: int = 7799, dict_path: str = "eli-dict.json", target: str = "zh-TW",
          skip_selectors: list[str] | None = None, extra_js: str | None = None) -> None:
    skip_selectors = skip_selectors or []
    tr = Translator(target=target, cache_path=dict_path + ".cache")
    lock = threading.Lock()

    def remember(src: str, out: str) -> None:
        with lock:
            data = {}
            if os.path.exists(dict_path):
                try:
                    data = json.load(open(dict_path, encoding="utf-8"))
                except Exception:
                    data = {}
            if data.get(src) == out:
                return
            data[src] = out
            tmp = dict_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
            os.replace(tmp, dict_path)

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, body: bytes, ctype: str) -> None:
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            p = urllib.parse.urlparse(self.path)
            if p.path == "/payload.js":
                js = build_bundle(dict_path, f"http://127.0.0.1:{port}", skip_selectors)
                if extra_js and os.path.exists(extra_js):
                    js += "\n" + open(extra_js, encoding="utf-8").read()
                self._send(js.encode("utf-8"), "application/javascript; charset=utf-8")
            elif p.path == "/tr":
                q = urllib.parse.parse_qs(p.query).get("q", [""])[0]
                out = tr.translate(q) if tr.needs_translation(q) else q
                if out != q:
                    remember(q, out)
                    tr.save()
                self._send(json.dumps({"t": out}, ensure_ascii=False).encode("utf-8"),
                           "application/json; charset=utf-8")
            elif p.path == "/health":
                self._send(b'{"ok":true}', "application/json")
            else:
                self.send_error(404)

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"electron-live-i18n serving on http://127.0.0.1:{port} (dict: {dict_path})")
    httpd.serve_forever()
