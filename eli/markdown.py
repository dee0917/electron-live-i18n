"""Translate a Markdown document while leaving code, links and tables intact."""

from __future__ import annotations

import os
import re

from .translate import Translator

FENCE = re.compile(r"^(```|~~~)")
LINKLINE = re.compile(r"^\s*>?\s*\[[^\]]+\]\([^)]+\)(\s*\|\s*\[[^\]]+\]\([^)]+\))+\s*$")
TABLE_SEP = re.compile(r"^\s*\|?[\s:\-|]+\|[\s:\-|]*$")
INLINE_CODE = re.compile(r"`[^`]*`")
URL = re.compile(r"https?://\S+")
KEBAB = re.compile(r"\b[a-z0-9]+(?:-[a-z0-9]+){1,}\b")   # package names like electron-live-i18n


def _protect(text: str) -> tuple[str, list[str]]:
    """Replace inline code and URLs with placeholders so the engine cannot mangle them."""
    store: list[str] = []

    def keep(m):
        store.append(m.group(0))
        return f"\u2402{len(store) - 1}\u2403"

    text = INLINE_CODE.sub(keep, text)
    text = URL.sub(keep, text)
    text = KEBAB.sub(keep, text)
    return text, store


def _restore(text: str, store: list[str]) -> str:
    for i, original in enumerate(store):
        text = text.replace(f"\u2402{i}\u2403", original)
        text = text.replace(f"\u2402 {i} \u2403", original)
    return text


def translate_markdown(src: str, dst: str, tr: Translator) -> dict:
    lines = open(src, encoding="utf-8").read().split("\n")
    out: list[str] = []
    in_fence = False
    translated = 0

    for line in lines:
        if FENCE.match(line.strip()):
            in_fence = not in_fence
            out.append(line)
            continue
        stripped = line.strip()
        if (in_fence or not stripped or stripped.startswith(("    ", "\t"))
                or TABLE_SEP.match(line) or LINKLINE.match(line)
                or stripped.startswith("<!--")):
            out.append(line)
            continue

        # keep markdown structure markers, translate only the prose part
        m = re.match(r"^(\s*(?:[-*+]\s+|\d+\.\s+|#{1,6}\s+|>\s?)*)(.*)$", line)
        prefix, body = m.group(1), m.group(2)
        is_heading = prefix.lstrip().startswith("#")
        if not body.strip() or not tr.needs_translation(body, min_letters=3 if is_heading else 8):
            out.append(line)
            continue
        protected, store = _protect(body)
        result = _restore(tr.translate(protected), store)
        out.append(prefix + result)
        translated += 1

    tmp = dst + ".tmp"
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    os.replace(tmp, dst)
    tr.save()
    return {"lines": len(lines), "translated": translated, "out": dst}
