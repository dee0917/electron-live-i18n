"""A tiny MCP (Model Context Protocol) server exposing electron-live-i18n to AI agents.

Speaks JSON-RPC 2.0 over stdio using only the standard library, so an agent can
inspect an Electron bundle, patch it, translate strings or locale files, and revert —
without the user leaving their assistant.

Run:  eli mcp
"""

from __future__ import annotations

import json
import os
import sys
import traceback

from .asar import backup, patch_entry, read_header, restore, AsarError
from .locales import translate_json_file
from .translate import Translator

HERE = os.path.dirname(os.path.abspath(__file__))
PROTOCOL = "2025-06-18"

TOOLS = [
    {
        "name": "translate_text",
        "description": "Translate a string into a target language (key-less, cached on disk).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "target": {"type": "string", "default": "zh-TW"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "translate_locale_file",
        "description": "Translate a JSON locale file and write the result atomically. Existing translations in the destination are preserved.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "src": {"type": "string", "description": "source JSON file"},
                "dst": {"type": "string", "description": "destination JSON file"},
                "target": {"type": "string", "default": "zh-TW"},
            },
            "required": ["src", "dst"],
        },
    },
    {
        "name": "inspect_app",
        "description": "List front-end entries inside a packaged Electron app's app.asar, largest first, to pick a loader slot.",
        "inputSchema": {
            "type": "object",
            "properties": {"app": {"type": "string", "description": ".app bundle or app.asar path"}},
            "required": ["app"],
        },
    },
    {
        "name": "patch_app",
        "description": "Write the live-i18n loader into one asar entry in place (backs up app.asar and Info.plist first).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app": {"type": "string"},
                "entry": {"type": "string", "description": "path inside the archive to overwrite"},
                "url": {"type": "string", "default": "http://127.0.0.1:7799/payload.js"},
                "backup_dir": {"type": "string", "default": "./eli-backups"},
            },
            "required": ["app", "entry"],
        },
    },
    {
        "name": "revert_app",
        "description": "Restore app.asar and Info.plist from the most recent backup.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app": {"type": "string"},
                "backup_dir": {"type": "string", "default": "./eli-backups"},
            },
            "required": ["app"],
        },
    },
]


def _resolve(app: str):
    if app.endswith(".asar"):
        return app, None
    asar = os.path.join(app, "Contents", "Resources", "app.asar")
    plist = os.path.join(app, "Contents", "Info.plist")
    if not os.path.exists(asar):
        raise AsarError(f"no app.asar under {app}")
    return asar, (plist if os.path.exists(plist) else None)


def _entries(app: str):
    asar, plist = _resolve(app)
    header, _, size, base = read_header(asar)

    def walk(node, prefix=""):
        for name, child in (node.get("files") or {}).items():
            path = f"{prefix}{name}"
            if "files" in child:
                yield from walk(child, path + "/")
            else:
                yield path, int(child.get("size", 0))

    items = [(p, s) for p, s in walk(header) if p.endswith((".js", ".html", ".css"))]
    items.sort(key=lambda x: -x[1])
    return {"archive": asar, "info_plist": plist, "header_bytes": size,
            "data_offset": base,
            "entries": [{"path": p, "size": s} for p, s in items[:40]]}


def call_tool(name: str, args: dict) -> str:
    if name == "translate_text":
        tr = Translator(target=args.get("target", "zh-TW"), cache_path=".eli-cache.json")
        out = tr.translate(args["text"])
        tr.save()
        return out
    if name == "translate_locale_file":
        tr = Translator(target=args.get("target", "zh-TW"), cache_path=".eli-cache.json")
        return json.dumps(translate_json_file(args["src"], args["dst"], tr), ensure_ascii=False, indent=2)
    if name == "inspect_app":
        return json.dumps(_entries(args["app"]), ensure_ascii=False, indent=2)
    if name == "patch_app":
        asar, plist = _resolve(args["app"])
        loader = open(os.path.join(HERE, "loader.js"), encoding="utf-8").read()
        loader = loader.replace("__ELI_URL__", args.get("url", "http://127.0.0.1:7799/payload.js"))
        saved = backup([p for p in (asar, plist) if p], args.get("backup_dir", "./eli-backups"))
        info = patch_entry(asar, args["entry"], loader.encode("utf-8"), info_plist=plist)
        return json.dumps({"patched": info, "backups": saved,
                           "next": "restart the app; it will pull the translation layer from the URL"},
                          ensure_ascii=False, indent=2)
    if name == "revert_app":
        asar, plist = _resolve(args["app"])
        bdir = args.get("backup_dir", "./eli-backups")
        done = []
        for target in [p for p in (asar, plist) if p]:
            base = os.path.basename(target)
            cands = sorted(f for f in os.listdir(bdir) if f.startswith(base + ".bak-"))
            if cands:
                restore(os.path.join(bdir, cands[-1]), target)
                done.append(cands[-1])
        return json.dumps({"restored": done}, ensure_ascii=False)
    raise ValueError(f"unknown tool: {name}")


def _send(obj) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
        if method == "initialize":
            _send({"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "electron-live-i18n", "version": "0.1.0"},
            }})
        elif method == "tools/list":
            _send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}
            try:
                text = call_tool(name, args)
                _send({"jsonrpc": "2.0", "id": mid,
                       "result": {"content": [{"type": "text", "text": text}], "isError": False}})
            except Exception as e:
                _send({"jsonrpc": "2.0", "id": mid, "result": {
                    "content": [{"type": "text", "text": f"{type(e).__name__}: {e}\n{traceback.format_exc()}"}],
                    "isError": True}})
        elif method in ("ping",):
            _send({"jsonrpc": "2.0", "id": mid, "result": {}})
        elif mid is not None:
            _send({"jsonrpc": "2.0", "id": mid,
                   "error": {"code": -32601, "message": f"method not found: {method}"}})


if __name__ == "__main__":
    main()
