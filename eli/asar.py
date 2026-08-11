"""In-place patching of a packaged Electron ``app.asar``.

The trick this project relies on: an entry inside ``app.asar`` can be rewritten
**without repacking the whole archive**, as long as the replacement payload is
padded to the exact original byte length. Then we only have to fix up two
integrity hashes:

1. the per-file SHA256 inside the asar header (``hash`` + ``blocks[0]``), and
2. the SHA256 of the header itself, stored in ``Info.plist`` under
   ``ElectronAsarIntegrity`` (macOS bundles).

Both hashes are fixed-length hex, so the header length never changes and every
file offset stays valid.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import time
from typing import Any


class AsarError(RuntimeError):
    pass


def read_header(asar_path: str) -> tuple[dict[str, Any], str, int, int]:
    """Return ``(header_dict, header_str, header_size, data_base_offset)``."""
    with open(asar_path, "rb") as f:
        head = f.read(16)
        if len(head) < 16:
            raise AsarError("not an asar file (too short)")
        _, size2, _, size4 = struct.unpack("<4I", head)
        if not (0 < size4 < 64 * 1024 * 1024):
            raise AsarError("not an asar archive (implausible header size)")
        try:
            header_str = f.read(size4).decode("utf-8")
            header = json.loads(header_str)
        except (UnicodeDecodeError, ValueError) as e:
            raise AsarError(f"not an asar archive (header is not valid JSON: {e})")
    return header, header_str, size4, 8 + size2


def find_entry(header: dict[str, Any], rel_path: str) -> dict[str, Any]:
    node = header
    for part in rel_path.split("/"):
        files = node.get("files")
        if not files or part not in files:
            raise AsarError(f"{rel_path!r} not found inside archive")
        node = files[part]
    if "offset" not in node:
        raise AsarError(f"{rel_path!r} is not a regular file")
    return node


def read_entry(asar_path: str, rel_path: str) -> bytes:
    header, _, _, base = read_header(asar_path)
    entry = find_entry(header, rel_path)
    with open(asar_path, "rb") as f:
        f.seek(base + int(entry["offset"]))
        return f.read(int(entry["size"]))


def backup(paths: list[str], backup_dir: str) -> list[str]:
    os.makedirs(backup_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out = []
    for p in paths:
        dst = os.path.join(backup_dir, f"{os.path.basename(p)}.bak-{stamp}")
        shutil.copy2(p, dst)
        out.append(dst)
    return out


def patch_entry(asar_path: str, rel_path: str, payload: bytes,
                info_plist: str | None = None, pad_byte: bytes = b" ") -> dict[str, Any]:
    """Overwrite one entry in place. ``payload`` must fit in the original size."""
    header, header_str, header_size, base = read_header(asar_path)
    entry = find_entry(header, rel_path)
    size = int(entry["size"])
    if len(payload) > size:
        raise AsarError(
            f"payload is {len(payload)} bytes but the slot only holds {size}. "
            "Shrink the payload (a small loader that fetches the real code works well)."
        )
    padded = payload + b"\n" + pad_byte * (size - len(payload) - 1) if len(payload) < size else payload
    if len(padded) != size:
        raise AsarError("padding failed")

    old_hash = (entry.get("integrity") or {}).get("hash")
    new_hash = hashlib.sha256(padded).hexdigest()
    new_header_str = header_str
    if old_hash:
        if len(old_hash) != len(new_hash):
            raise AsarError("unexpected hash length")
        new_header_str = header_str.replace(old_hash, new_hash)
        if len(new_header_str.encode()) != header_size:
            raise AsarError("header length changed, refusing to write")

    with open(asar_path, "r+b") as f:
        if old_hash:
            f.seek(16)
            f.write(new_header_str.encode("utf-8"))
        f.seek(base + int(entry["offset"]))
        f.write(padded)

    result = {"entry": rel_path, "slot_size": size, "payload": len(payload),
              "file_hash": new_hash, "header_hash": None}

    if info_plist and old_hash:
        old_header_hash = hashlib.sha256(header_str.encode("utf-8")).hexdigest()
        new_header_hash = hashlib.sha256(new_header_str.encode("utf-8")).hexdigest()
        text = open(info_plist, encoding="utf-8").read()
        if old_header_hash in text:
            tmp = info_plist + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text.replace(old_header_hash, new_header_hash))
            os.replace(tmp, info_plist)
            result["header_hash"] = new_header_hash
    return result


def restore(backup_path: str, target: str) -> None:
    shutil.copy2(backup_path, target)
