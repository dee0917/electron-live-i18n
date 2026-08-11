"""Free, key-less translation with an on-disk cache.

Uses the public ``translate.googleapis.com/translate_a/single`` endpoint, the
same one browser extensions hit. No API key, no billing. Long text is split on
paragraph/sentence boundaries because that endpoint silently truncates long
input — a bug that is easy to miss and produces half-translated strings.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import re
import threading
import urllib.parse
import urllib.request

CJK = re.compile(r"[\u4e00-\u9fff]")


class Translator:
    def __init__(self, target: str = "zh-TW", cache_path: str | None = None,
                 workers: int = 8, chunk: int = 1200, timeout: int = 15):
        self.target = target
        self.cache_path = cache_path
        self.workers = workers
        self.chunk = chunk
        self.timeout = timeout
        self._lock = threading.Lock()
        self._cache: dict[str, str] = {}
        if cache_path and os.path.exists(cache_path):
            try:
                self._cache = json.load(open(cache_path, encoding="utf-8"))
            except Exception:
                self._cache = {}

    # -- heuristics ---------------------------------------------------
    def needs_translation(self, text: str, min_letters: int = 8) -> bool:
        if not text or len(text.strip()) < 4:
            return False
        letters = sum(1 for c in text if c.isalpha())
        if letters < min_letters:
            return False
        if self.target.startswith("zh"):
            return (len(CJK.findall(text)) / max(1, letters)) < 0.12
        return True

    # -- core ---------------------------------------------------------
    def _split(self, text: str) -> list[str]:
        parts, buf = [], ""
        for piece in re.split(r"(\n{1,})", text):
            if len(buf) + len(piece) <= self.chunk:
                buf += piece
                continue
            if buf:
                parts.append(buf)
                buf = ""
            while len(piece) > self.chunk:
                cut = max(piece.rfind("。", 0, self.chunk), piece.rfind(". ", 0, self.chunk),
                          piece.rfind(", ", 0, self.chunk), piece.rfind("，", 0, self.chunk))
                if cut < self.chunk // 3:
                    cut = self.chunk
                parts.append(piece[:cut + 1])
                piece = piece[cut + 1:]
            buf = piece
        if buf:
            parts.append(buf)
        return [p for p in parts if p.strip()]

    def _call(self, chunk: str) -> str:
        url = ("https://translate.googleapis.com/translate_a/single"
               f"?client=gtx&sl=auto&tl={self.target}&dt=t&q=" + urllib.parse.quote(chunk))
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        raw = urllib.request.urlopen(req, timeout=self.timeout).read().decode("utf-8")
        data = json.loads(raw)
        return "".join(seg[0] for seg in data[0] if seg and seg[0])

    def translate(self, text: str) -> str:
        key = hashlib.sha1((self.target + "\x00" + text).encode("utf-8")).hexdigest()
        with self._lock:
            hit = self._cache.get(key)
        if hit:
            return hit
        try:
            out = "".join(self._call(c) for c in self._split(text))
        except Exception:
            return text
        if not out:
            return text
        with self._lock:
            self._cache[key] = out
        return out

    def translate_many(self, texts: list[str]) -> list[str]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as ex:
            return list(ex.map(self.translate, texts))

    def save(self) -> None:
        if not self.cache_path:
            return
        os.makedirs(os.path.dirname(self.cache_path) or ".", exist_ok=True)
        tmp = self.cache_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False)
        os.replace(tmp, self.cache_path)
