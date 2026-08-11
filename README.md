# electron-live-i18n

> [English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)
>
> *Translations below were produced by this tool itself (`eli locales` / `eli tr`) and lightly reviewed. PRs welcome if a phrase reads wrong in your language.*

Live-translate **any packaged Electron app** — no rebuild, no source code, no API key.

Most i18n tooling assumes you own the app and can edit its locale files. This one is for
the other case: a shipped, signed, `app.asar`-packed Electron app that shows English you
cannot read, and you just want it in your language *today*.

It works by writing a **~900 byte loader** into one existing entry inside `app.asar`
(padded to the exact original size, integrity hashes rewritten), and serving the actual
translation layer from a tiny local HTTP server. After that first patch you never touch
the app bundle again — iterate on the translation layer and press ⌘R.

```
app.asar ──(loader stub)──► http://127.0.0.1:7799/payload.js ──► DOM sweeper + dictionary
```

## Demo

```console
$ eli inspect "/Applications/Some App.app"
archive : /Applications/Some App.app/Contents/Resources/app.asar
header  : 161743 bytes, data starts at 161760
plist   : /Applications/Some App.app/Contents/Info.plist
largest front-end entries (good loader slots):
    1284231  dist/assets/index-abc123.js
       7020  dist/vendor-analytics.js
        601  dist/index.html

$ eli serve --target zh-TW --dict ./mydict.json &
electron-live-i18n serving on http://127.0.0.1:7799 (dict: ./mydict.json)

$ eli patch "/Applications/Some App.app" --entry dist/vendor-analytics.js
{
  "patched": {
    "entry": "dist/vendor-analytics.js",
    "slot_size": 7020,
    "payload": 905,
    "file_hash": "401f5f19...",
    "header_hash": "6dc99001..."
  },
  "backups": [
    "./eli-backups/app.asar.bak-20260812-021132",
    "./eli-backups/Info.plist.bak-20260812-021132"
  ]
}

Restart the app. It will now pull the translation layer from http://127.0.0.1:7799/payload.js
```

After the restart, English UI text is replaced as it appears, and every new string
lands in `mydict.json`:

```console
$ cat mydict.json
{
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。",
  "Send a message to get started": "傳個訊息開始吧",
  "Settings saved successfully": "設定儲存成功"
}
```

Changed your mind about a translation? Edit that file and press ⌘R in the app.

## Why not just edit the locale files?

- Many Electron apps hard-code English in JSX/TSX; there is no locale file to edit.
- The app is already built and signed; rebuilding means setting up its whole toolchain.
- You want to keep translating **new** strings as the app updates, not fork it.

If you *do* have locale JSON files, `eli locales` translates those too.

## Install

```bash
pip install electron-live-i18n     # or: pipx install electron-live-i18n
```

Python 3.9+, standard library only. No dependencies, no API key, no account.

## Quick start

```bash
# 1. look inside the app and pick an entry to host the loader
eli inspect "/Applications/Some App.app"

#      1284231  dist/assets/index-abc123.js
#         7020  dist/vendor-analytics.js      <-- a good slot: big enough, non-critical
#          601  dist/index.html

# 2. start the translation server (keep it running)
eli serve --target zh-TW --dict ./mydict.json --skip "#my-own-overlay" &

# 3. patch the app once
eli patch "/Applications/Some App.app" --entry dist/vendor-analytics.js

# 4. restart the app — English turns into your language as you use it
```

Undo at any time:

```bash
eli revert "/Applications/Some App.app"
```

## How it translates

1. A `MutationObserver` walks text nodes and replaces anything already in the dictionary — instant, zero network.
2. Unknown strings that look foreign (≥8 letters, <12% target-script characters) are sent to the local server.
3. The server translates via the public, key-less `translate.googleapis.com` endpoint, caches the result on disk, and appends it to your dictionary file.

So the dictionary is a plain JSON file you can hand-edit. Machine translation gets you 95%
of the way in seconds; fix the awkward ten strings by hand and they stay fixed.

```json
{
  "Send a message to get started": "傳個訊息開始吧",
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。"
}
```

## Let an AI agent do it for you

If you use an assistant that can run commands and edit files on your machine — Claude Code,
Cursor, Codex CLI, Cline, Windsurf, Copilot CLI — paste this and it will handle the whole
flow, including picking the entry to patch:

```text
Install and use https://github.com/dee0917/electron-live-i18n to translate the UI of
"<APP PATH>" into <LANGUAGE>.

Steps:
1. pipx install electron-live-i18n   (or: pip install electron-live-i18n)
2. Run `eli inspect "<APP PATH>"` and pick a front-end .js entry that is large enough
   (> 1 KB) and non-critical — analytics/vendor bundles are ideal. Tell me which one you
   picked and why.
3. Start `eli serve --target <LANG CODE> --dict ./mydict.json` in the background.
4. Run `eli patch "<APP PATH>" --entry <THE ENTRY>`, then restart the app.
5. Confirm the backups exist, and remind me that `eli revert "<APP PATH>"` undoes everything.
```

Replace `<APP PATH>` (e.g. `/Applications/Slack.app`, `C:\Users\me\AppData\Local\Slack`),
`<LANGUAGE>` and `<LANG CODE>` (`zh-TW`, `zh-CN`, `ja`, `ko`, `es`, `fr`, `de`, `pt`, `ru`, ...).

Or wire it up as an MCP server (see below) and just say
*"translate this app's UI into Japanese"*.

## Choosing an entry to patch

`eli inspect` lists front-end entries by size. Pick one that is:

- **large enough** — the loader is ~900 bytes and gets padded up to the slot size,
- **loaded by the renderer** — check that `index.html` references it,
- **non-critical** — telemetry/analytics bundles are ideal; the original content is replaced.

If you want to keep the original code, host it from your own server and append it to the
payload with `eli serve --extra-js original.js`. That is what the loader indirection is for.

## Platforms

| OS | Bundle layout it looks for | Integrity fixup |
| --- | --- | --- |
| macOS | `Foo.app/Contents/Resources/app.asar` | archive header hash **and** `ElectronAsarIntegrity` in `Info.plist` |
| Windows | `Foo\resources\app.asar`, plus Squirrel's `Foo\app-1.2.3\resources\app.asar` | archive header hash |
| Linux | `/opt/Foo/resources/app.asar` | archive header hash |

You can always pass the `app.asar` path directly instead of the bundle folder.

Windows notes: run the shell as the user who owns the install directory (per-user installs
under `%LOCALAPPDATA%` need no elevation; `Program Files` does). Squirrel-based apps create
a new `app-<version>` folder on update, so re-run `eli patch` after an upgrade — the
dictionary and the local server are untouched.

## Gotchas this project already solved

- **CSP** — Electron's default `script-src 'self' blob:` blocks `eval()`. The loader executes fetched code through a `Blob` URL instead.
- **Asar integrity** — macOS bundles carry `ElectronAsarIntegrity` in `Info.plist`, plus a per-file SHA256 inside the archive header. Both are rewritten, and because hashes are fixed-length hex the header size never changes, so every file offset stays valid.
- **Silent truncation** — the free translate endpoint quietly cuts long input. Text is split on paragraph/sentence boundaries and stitched back together.
- **Self-translation loops** — pass `--skip` selectors for your own injected UI so it does not translate itself.

## Use it from an AI agent (MCP)

`eli mcp` speaks the Model Context Protocol over stdio, so an assistant can inspect a
bundle, patch it, translate strings or locale files and revert — all without you leaving
the chat.

```json
{
  "mcpServers": {
    "electron-live-i18n": {
      "type": "stdio",
      "command": "eli",
      "args": ["mcp"]
    }
  }
}
```

Tools exposed: `inspect_app`, `patch_app`, `revert_app`, `translate_text`,
`translate_locale_file`.

Example conversation:

> **You:** This app's menu is in English, make it Traditional Chinese.
> **Agent:** *(inspect_app → picks a 7 KB non-critical bundle → patch_app → tells you to restart)*

## Locale files on disk

```bash
eli locales locales/en.json locales/zh-TW.json --target zh-TW
```

Only untranslated strings are sent; existing translations in the destination file win, so
your manual fixes survive re-runs. Writes are atomic (tmp file + `os.replace`).

## Translating whole Markdown docs

```bash
eli md README.md README.ja.md --target ja
```

Code blocks, inline code, URLs and table rules are preserved; only prose is translated.
The localized READMEs in this repo were produced this way.

## Library use

```python
from eli.translate import Translator
from eli.asar import read_header, patch_entry

tr = Translator(target="ja", cache_path=".cache.json")
print(tr.translate("Settings saved successfully"))

header, header_str, size, base = read_header("/path/to/app.asar")
```

## Scope and honesty

- Developed and tested on macOS. Windows and Linux bundles use the same asar layout and are
  supported (see Platforms); the `Info.plist` step simply does not apply there.
- Patching a signed bundle invalidates its signature. On macOS an ad-hoc/unsigned app keeps
  working; a hardened, notarized app may refuse to launch. Test, and keep the backup.
- This is a tool for **your own machine and your own copy** of an app. Respect the licence
  of whatever you are translating.

## Licence

MIT
