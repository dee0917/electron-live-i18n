"""Translate locale files on disk (JSON / nested JSON), writing back atomically."""

from __future__ import annotations

import json
import os
from typing import Any

from .translate import Translator


def _walk(node: Any, out: list[tuple[list, str]], path: list) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            _walk(v, out, path + [k])
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk(v, out, path + [i])
    elif isinstance(node, str):
        out.append((path, node))


def _set(node: Any, path: list, value: str) -> None:
    for p in path[:-1]:
        node = node[p]
    node[path[-1]] = value


def translate_json_file(src: str, dst: str, tr: Translator, only_missing: bool = True) -> dict:
    data = json.load(open(src, encoding="utf-8"))
    existing = {}
    if only_missing and os.path.exists(dst):
        try:
            existing = json.load(open(dst, encoding="utf-8"))
        except Exception:
            existing = {}
    items: list[tuple[list, str]] = []
    _walk(data, items, [])
    todo = [(p, s) for p, s in items if tr.needs_translation(s)]
    outs = tr.translate_many([s for _, s in todo])
    result = json.loads(json.dumps(data, ensure_ascii=False))
    for (path, _), new in zip(todo, outs):
        _set(result, path, new)
    if existing:
        result = {**result, **{k: v for k, v in existing.items() if isinstance(v, str) and v}}
    tmp = dst + ".tmp"
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, dst)
    tr.save()
    return {"strings": len(items), "translated": len(todo), "out": dst}
