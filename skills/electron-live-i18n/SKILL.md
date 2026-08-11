---
name: electron-live-i18n
description: Use when a packaged Electron app shows text in a language the user cannot read, when its UI needs translating without access to source code or a rebuild, or when JSON locale files need machine translation that preserves manual fixes.
---

# Translating a packaged Electron app

Use this when the app is already built and shipped: English hard-coded in the bundle,
no locale file to edit, and rebuilding is not an option.

## The shape of the solution

Write a ~900 byte loader into one entry inside `app.asar` **in place**, then serve the
real translation layer from a local HTTP server. Patch once, iterate forever.

```bash
eli inspect "/Applications/Some App.app"        # pick a large, non-critical .js entry
eli serve --target zh-TW --dict ./mydict.json & # keep running
eli patch "/Applications/Some App.app" --entry dist/vendor-analytics.js
# restart the app
eli revert "/Applications/Some App.app"         # undo anytime
```

If the app *does* ship JSON locale files, skip all of that:

```bash
eli locales locales/en.json locales/zh-TW.json --target zh-TW
```

## Rules that save hours

1. **Never repack the archive.** Pad the replacement payload to the exact original byte
   length, then rewrite the per-file SHA256 in the header and the `ElectronAsarIntegrity`
   hash in `Info.plist`. Fixed-length hex keeps every offset valid.
2. **Do not use `eval()`.** Electron's default CSP is `script-src 'self' blob:`; execute
   fetched code through a Blob URL.
3. **Chunk long text.** The free translation endpoint truncates long input silently and
   you will ship half-translated strings without noticing.
4. **Skip your own injected UI** with `--skip "#your-overlay"`, or it translates itself.
5. **Verify with a screenshot before declaring victory**, and test a narrow window —
   fixed-width overlays collapse into vertical text on small viewports.
6. Patching invalidates code signing. Unsigned/ad-hoc bundles keep working; a hardened
   notarized app may refuse to launch. Backups are automatic — use `eli revert`.

## As an MCP server

```json
{ "mcpServers": { "electron-live-i18n": { "type": "stdio", "command": "eli", "args": ["mcp"] } } }
```

Tools: `inspect_app`, `patch_app`, `revert_app`, `translate_text`, `translate_locale_file`.
