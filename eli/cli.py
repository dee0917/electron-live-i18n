"""Command line interface."""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from .asar import backup, patch_entry, read_entry, read_header, restore, AsarError
from .locales import translate_json_file
from .server import serve
from .translate import Translator

HERE = os.path.dirname(os.path.abspath(__file__))


def _resolve_bundle(app: str) -> tuple[str, str | None]:
    """Accept either an .app bundle (macOS) or a direct path to app.asar."""
    if app.endswith(".asar"):
        return app, None
    asar = os.path.join(app, "Contents", "Resources", "app.asar")
    plist = os.path.join(app, "Contents", "Info.plist")
    if os.path.exists(asar):
        return asar, (plist if os.path.exists(plist) else None)
    raise SystemExit(f"could not find app.asar under {app}")


def cmd_inspect(a):
    asar, plist = _resolve_bundle(a.app)
    header, header_str, size, base = read_header(asar)

    def walk(node, prefix=""):
        for name, child in (node.get("files") or {}).items():
            path = f"{prefix}{name}"
            if "files" in child:
                yield from walk(child, path + "/")
            else:
                yield path, int(child.get("size", 0))

    entries = sorted(walk(header), key=lambda x: -x[1])
    print(f"archive : {asar}")
    print(f"header  : {size} bytes, data starts at {base}")
    print(f"plist   : {plist or '(none)'}")
    print("largest front-end entries (good loader slots):")
    for path, sz in entries[:20]:
        if path.endswith(".js") or path.endswith(".html"):
            print(f"  {sz:>9}  {path}")


def cmd_patch(a):
    asar, plist = _resolve_bundle(a.app)
    loader = open(os.path.join(HERE, "loader.js"), encoding="utf-8").read()
    loader = loader.replace("__ELI_URL__", a.url)
    saved = backup([p for p in (asar, plist) if p], a.backup_dir)
    try:
        info = patch_entry(asar, a.entry, loader.encode("utf-8"), info_plist=plist)
    except AsarError as e:
        raise SystemExit(f"patch failed: {e}\nbackups kept at: {saved}")
    print(json.dumps({"patched": info, "backups": saved}, ensure_ascii=False, indent=2))
    print("\nRestart the app. It will now pull the translation layer from", a.url)


def cmd_revert(a):
    asar, plist = _resolve_bundle(a.app)
    for target in [p for p in (asar, plist) if p]:
        name = os.path.basename(target)
        cands = sorted(f for f in os.listdir(a.backup_dir) if f.startswith(name + ".bak-"))
        if not cands:
            print(f"no backup found for {name}")
            continue
        src = os.path.join(a.backup_dir, cands[-1])
        restore(src, target)
        print(f"restored {name} from {cands[-1]}")


def cmd_show(a):
    asar, _ = _resolve_bundle(a.app)
    sys.stdout.write(read_entry(asar, a.entry).decode("utf-8", "replace"))


def cmd_serve(a):
    serve(port=a.port, dict_path=a.dict, target=a.target,
          skip_selectors=a.skip or [], extra_js=a.extra_js)


def cmd_locales(a):
    tr = Translator(target=a.target, cache_path=a.dict + ".cache")
    print(json.dumps(translate_json_file(a.src, a.dst, tr), ensure_ascii=False, indent=2))


def cmd_tr(a):
    tr = Translator(target=a.target, cache_path=a.dict + ".cache")
    print(tr.translate(a.text))
    tr.save()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="eli", description="Live-translate a packaged Electron app.")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("inspect", help="list asar entries and find a loader slot")
    p.add_argument("app")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("patch", help="write the tiny loader into app.asar (in place)")
    p.add_argument("app")
    p.add_argument("--entry", required=True, help="path inside the asar to overwrite, e.g. dist/vendor.js")
    p.add_argument("--url", default="http://127.0.0.1:7799/payload.js")
    p.add_argument("--backup-dir", default="./eli-backups")
    p.set_defaults(func=cmd_patch)

    p = sub.add_parser("revert", help="restore app.asar and Info.plist from backups")
    p.add_argument("app")
    p.add_argument("--backup-dir", default="./eli-backups")
    p.set_defaults(func=cmd_revert)

    p = sub.add_parser("show", help="print one entry from the archive")
    p.add_argument("app")
    p.add_argument("--entry", required=True)
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("serve", help="serve the runtime payload and /tr endpoint")
    p.add_argument("--port", type=int, default=7799)
    p.add_argument("--dict", default="eli-dict.json")
    p.add_argument("--target", default="zh-TW")
    p.add_argument("--skip", action="append", help="CSS selector to leave untouched (repeatable)")
    p.add_argument("--extra-js", help="extra JS file appended to the payload")
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("locales", help="translate a JSON locale file on disk")
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--target", default="zh-TW")
    p.add_argument("--dict", default="eli-dict.json")
    p.set_defaults(func=cmd_locales)

    p = sub.add_parser("tr", help="translate one string (handy for testing)")
    p.add_argument("text")
    p.add_argument("--target", default="zh-TW")
    p.add_argument("--dict", default="eli-dict.json")
    p.set_defaults(func=cmd_tr)

    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    main()
