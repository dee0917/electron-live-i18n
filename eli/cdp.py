"""Minimal Chrome DevTools Protocol client (stdlib only, no websocket deps)."""

import json, os, socket, base64, struct, urllib.request

def _ws_connect(url, timeout=10):
    # url: ws://127.0.0.1:9222/devtools/page/XXXX
    assert url.startswith("ws://")
    rest = url[5:]
    hostport, path = rest.split("/", 1)
    path = "/" + path
    host, port = hostport.split(":")
    s = socket.create_connection((host, int(port)), timeout=timeout)
    key = base64.b64encode(os.urandom(16)).decode()
    req = ("GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
           "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (path, hostport, key))
    s.sendall(req.encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = s.recv(4096)
        if not chunk:
            raise RuntimeError("handshake closed")
        buf += chunk
    if b"101" not in buf.split(b"\r\n")[0]:
        raise RuntimeError("handshake failed: %r" % buf[:200])
    return s

def _ws_send(s, payload: str):
    data = payload.encode()
    hdr = bytearray()
    hdr.append(0x81)
    mask = os.urandom(4)
    n = len(data)
    if n < 126:
        hdr.append(0x80 | n)
    elif n < 65536:
        hdr.append(0x80 | 126); hdr += struct.pack(">H", n)
    else:
        hdr.append(0x80 | 127); hdr += struct.pack(">Q", n)
    hdr += mask
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    s.sendall(bytes(hdr) + masked)

def _recv_exact(s, n):
    out = b""
    while len(out) < n:
        c = s.recv(n - len(out))
        if not c:
            raise RuntimeError("closed")
        out += c
    return out

def _ws_recv(s):
    b0, b1 = _recv_exact(s, 2)
    ln = b1 & 0x7F
    if ln == 126:
        ln = struct.unpack(">H", _recv_exact(s, 2))[0]
    elif ln == 127:
        ln = struct.unpack(">Q", _recv_exact(s, 8))[0]
    if b1 & 0x80:
        mask = _recv_exact(s, 4)
        data = bytearray(_recv_exact(s, ln))
        for i in range(ln):
            data[i] ^= mask[i % 4]
        data = bytes(data)
    else:
        data = _recv_exact(s, ln)
    return data.decode("utf-8", "replace")

def cdp_eval(expr, port=9222, title_hint="", timeout=15, await_promise=False):
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % port, timeout=5))
    page = None
    for t in tabs:
        if t.get("type") == "page" and title_hint.lower() in (t.get("title","") + t.get("url","")).lower():
            page = t; break
    if page is None:
        raise RuntimeError("no matching page")
    s = _ws_connect(page["webSocketDebuggerUrl"], timeout=timeout)
    s.settimeout(timeout)
    try:
        _ws_send(s, json.dumps({"id": 1, "method": "Runtime.evaluate",
                                "params": {"expression": expr, "returnByValue": True,
                                           "awaitPromise": await_promise}}))
        while True:
            msg = json.loads(_ws_recv(s))
            if msg.get("id") == 1:
                return msg
    finally:
        s.close()

def cdp_screenshot(path, port=9222, title_hint="", timeout=25):
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % port, timeout=5))
    page = [t for t in tabs if t.get("type") == "page" and title_hint.lower() in (t.get("title","")+t.get("url","")).lower()][0]
    s = _ws_connect(page["webSocketDebuggerUrl"], timeout=timeout); s.settimeout(timeout)
    try:
        _ws_send(s, json.dumps({"id": 2, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
        while True:
            msg = json.loads(_ws_recv(s))
            if msg.get("id") == 2:
                d = msg["result"]["data"]
                open(path, "wb").write(base64.b64decode(d))
                return path
    finally:
        s.close()


def cdp_call(method, params=None, port=9222, title_hint="", timeout=20):
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % port, timeout=5))
    page = [t for t in tabs if t.get("type") == "page" and title_hint.lower() in (t.get("title","")+t.get("url","")).lower()][0]
    s = _ws_connect(page["webSocketDebuggerUrl"], timeout=timeout); s.settimeout(timeout)
    try:
        _ws_send(s, json.dumps({"id": 7, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(_ws_recv(s))
            if msg.get("id") == 7:
                return msg
    finally:
        s.close()
