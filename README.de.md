# electron-live-i18n

> [English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)
>
> *Die folgenden Übersetzungen wurden von diesem Tool selbst erstellt (`eli locales` / `eli tr`) und leicht überprüft. PRs sind willkommen, wenn sich ein Satz in Ihrer Sprache falsch liest.*

Live-Übersetzung **jeder gepackten Electron-App** – kein Neuaufbau, kein Quellcode, kein API-Schlüssel.

Bei den meisten i18n-Tools wird davon ausgegangen, dass Sie Eigentümer der App sind und deren Gebietsschemadateien bearbeiten können. Dieser ist für
der andere Fall: eine ausgelieferte, signierte, mit `app.asar` verpackte Electron-App, die Sie auf Englisch anzeigt
Sie können nicht lesen, und Sie möchten es einfach *heute* in Ihrer Sprache haben.

Es funktioniert, indem ein **~900-Byte-Loader** in einen vorhandenen Eintrag innerhalb von `app.asar` geschrieben wird
(auf die exakte Originalgröße aufgefüllt, Integritäts-Hashes neu geschrieben) und die tatsächliche Größe bereitstellen
Übersetzungsschicht von einem winzigen lokalen HTTP-Server. Nach diesem ersten Patch berühren Sie es nie mehr
erneut das App-Bundle – iterieren Sie auf der Übersetzungsebene und drücken Sie ⌘R.

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

Nach dem Neustart wird der englische UI-Text so ersetzt, wie er erscheint, und jede neue Zeichenfolge
landet in `mydict.json`:

```console
$ cat mydict.json
{
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。",
  "Send a message to get started": "傳個訊息開始吧",
  "Settings saved successfully": "設定儲存成功"
}
```

Haben Sie Ihre Meinung bezüglich einer Übersetzung geändert? Bearbeiten Sie diese Datei und drücken Sie in der App ⌘R.

## Warum nicht einfach die Locale-Dateien bearbeiten?

- Viele Electron-Apps hard-code Englisch in JSX/TSX; Es gibt keine zu bearbeitende Gebietsschemadatei.
- Die App ist bereits erstellt und signiert. Neuaufbau bedeutet, die gesamte Toolchain einzurichten.
- Sie möchten weiterhin **neue** Zeichenfolgen übersetzen, während die App aktualisiert wird, und sie nicht verzweigen.

Wenn Sie über lokale JSON-Dateien verfügen, übersetzt `eli locales` auch diese.

## Installieren

```bash
pip install electron-live-i18n     # or: pipx install electron-live-i18n
```

Python 3.9+, nur Standardbibliothek. Keine Abhängigkeiten, kein API-Schlüssel, kein Konto.

## Schnellstart

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

Jederzeit rückgängig machen:

```bash
eli revert "/Applications/Some App.app"
```

## Wie es übersetzt wird

1. Ein `MutationObserver` durchläuft Textknoten und ersetzt alles, was sich bereits im Wörterbuch befindet – sofort, kein Netzwerk.
2. Unbekannte Zeichenfolgen, die fremdartig aussehen (≥8 Buchstaben, <12 % target-script Zeichen) werden an den lokalen Server gesendet.
3. Der Server übersetzt über den öffentlichen Endpunkt key-less `translate.googleapis.com`, speichert das Ergebnis auf der Festplatte zwischen und hängt es an Ihre Wörterbuchdatei an.

Das Wörterbuch ist also eine einfache JSON-Datei, die Sie hand-edit können. Mit maschineller Übersetzung erreichen Sie 95 %
des Weges in Sekunden; Reparieren Sie die unangenehmen zehn Saiten von Hand und sie bleiben fixiert.

```json
{
  "Send a message to get started": "傳個訊息開始吧",
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。"
}
```

## Lassen Sie das von einem KI-Agenten für Sie erledigen

Wenn Sie einen Assistenten verwenden, der Befehle ausführen und Dateien auf Ihrem Computer bearbeiten kann – Claude Code,
Cursor, Codex CLI, Cline, Windsurf, Copilot CLI – fügen Sie dies ein und es wird das Ganze verwalten
Ablauf, einschließlich der Auswahl des zu patchenden Eintrags:

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

Ersetzen Sie `<APP PATH>` (z. B. `/Applications/Slack.app`, `C:\Users\me\AppData\Local\Slack`),
`<LANGUAGE>` und `<LANG CODE>` (`zh-TW`, `zh-CN`, `ja`, `ko`, `es`, `fr`, `de`, `pt`, `ru`, ...).

Oder verkabeln Sie es als MCP-Server (siehe unten) und sagen Sie es einfach
*"Übersetze die Benutzeroberfläche dieser App ins Japanische"*.

## Auswählen eines Eintrags zum Patchen

`eli inspect` listet front-end Einträge nach Größe auf. Wählen Sie eines aus:

- **groß genug** – der Loader ist ~900 Byte groß und wird auf die Slot-Größe aufgefüllt,
- **vom Renderer geladen** – prüfen Sie, ob `index.html` darauf verweist,
- **non-critical** – Telemetrie-/Analysepakete sind ideal; Der ursprüngliche Inhalt wird ersetzt.

Wenn Sie den Originalcode behalten möchten, hosten Sie ihn auf Ihrem eigenen Server und hängen Sie ihn an den an
Nutzlast mit `eli serve --extra-js original.js`. Dafür gibt es die Loader-Indirektion.

## Plattformen

| Betriebssystem | Bundle-Layout, nach dem gesucht wird | Integritätskorrektur |
| --- | --- | --- |
| macOS | `Foo.app/Contents/Resources/app.asar` | Archiv-Header-Hash **und** `ElectronAsarIntegrity` in `Info.plist` |
| Windows | `Foo\resources\app.asar`, plus Eichhörnchens `Foo\app-1.2.3\resources\app.asar` | Archiv-Header-Hash |
| Linux | `/opt/Foo/resources/app.asar` | Archiv-Header-Hash |

Sie können den Pfad `app.asar` jederzeit direkt anstelle des Bundle-Ordners übergeben.

Windows-Hinweise: Führen Sie die Shell als Benutzer aus, der Eigentümer des Installationsverzeichnisses ist (per-user).
unter `%LOCALAPPDATA%` ist keine Erhöhung erforderlich; `Program Files` tut). Eichhörnchenbasierte Apps erstellen
ein neuer Ordner `app-<version>` beim Update, also re-run `eli patch` nach einem Upgrade – der
Wörterbuch und der lokale Server bleiben unberührt.

## Die Probleme dieses Projekts sind bereits gelöst

- **CSP** – Electrons Standard-`script-src 'self' blob:` blockiert `eval()`. Der Loader führt den abgerufenen Code stattdessen über eine `Blob`-URL aus.
- **Asar-Integrität** – macOS-Bundles tragen `ElectronAsarIntegrity` in `Info.plist` sowie einen per-file SHA256 im Archiv-Header. Beide werden neu geschrieben, und da Hashes fixed-length hexadezimal sind, ändert sich die Headergröße nie, sodass jeder Dateioffset gültig bleibt.
- **Stille Kürzung** – der kostenlose Übersetzungsendpunkt schneidet lange Eingaben stillschweigend ab. Der Text wird an Absatz-/Satzgrenzen aufgeteilt und wieder zusammengefügt.
- **Selbstübersetzungsschleifen** – Übergeben Sie `--skip`-Selektoren für Ihre eigene injizierte Benutzeroberfläche, damit diese sich nicht selbst übersetzt.

## Verwenden Sie es von einem KI-Agenten (MCP)

`eli mcp` spricht das Model Context Protocol über stdio, sodass ein Assistent a überprüfen kann
Bündeln, patchen, Strings oder Gebietsschemadateien übersetzen und wiederherstellen – alles, ohne dass Sie gehen müssen
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

Freiliegende Werkzeuge: `inspect_app`, `patch_app`, `revert_app`, `translate_text`,
`translate_locale_file`.

Beispielgespräch:

> **Sie:** Das Menü dieser App ist auf Englisch, also auf traditionelles Chinesisch.
> **Agent:** *(inspect_app → wählt ein 7 KB non-critical-Bundle aus → patch_app → fordert Sie auf, neu zu starten)*

## Gebietsschemadateien auf der Festplatte

```bash
eli locales locales/en.json locales/zh-TW.json --target zh-TW
```

Es werden nur unübersetzte Zeichenfolgen gesendet; vorhandene Übersetzungen in der Zieldatei gewinnen, also
Ihre manuellen Korrekturen überleben re-runs. Schreibvorgänge sind atomar (tmp-Datei + `os.replace`).

## Übersetzen ganzer Markdown-Dokumente

```bash
eli md README.md README.ja.md --target ja
```

Codeblöcke, Inline-Code, URLs und Tabellenregeln bleiben erhalten; Es wird nur Prosa übersetzt.
Die lokalisierten READMEs in diesem Repo wurden auf diese Weise erstellt.

## Bibliotheksnutzung

```python
from eli.translate import Translator
from eli.asar import read_header, patch_entry

tr = Translator(target="ja", cache_path=".cache.json")
print(tr.translate("Settings saved successfully"))

header, header_str, size, base = read_header("/path/to/app.asar")
```

## Umfang und Ehrlichkeit

- Entwickelt und getestet auf macOS. Windows- und Linux-Bundles verwenden dasselbe Asar-Layout und sind es auch
  unterstützt (siehe Plattformen); der `Info.plist`-Schritt gilt dort einfach nicht.
- Durch das Patchen eines signierten Bundles wird dessen Signatur ungültig. Unter macOS bleibt eine ad-hoc/unsigned-App erhalten
  Arbeiten; Eine gehärtete, notariell beglaubigte App kann den Start verweigern. Testen Sie und bewahren Sie das Backup auf.
- Dies ist ein Tool für **Ihren eigenen Computer und Ihre eigene Kopie** einer App. Respektieren Sie die Lizenz
  von dem, was Sie übersetzen.

## Lizenz

MIT
