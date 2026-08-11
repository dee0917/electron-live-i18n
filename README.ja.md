# electron-live-i18n

> [English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)
>
> *以下の翻訳はこのツール自体 (`eli locales` / `eli tr`) によって作成され、軽くレビューされています。 PR は、フレーズがあなたの言語で間違って読まれても歓迎します。*

**パッケージ化された Electron アプリ** をライブ翻訳します。リビルド、ソース コード、API キーは必要ありません。

ほとんどの i18n ツールは、ユーザーがアプリを所有しており、そのロケール ファイルを編集できることを前提としています。これは、
もう 1 つのケース: 出荷され、署名され、`app.asar` がパックされた Electron アプリで、英語が表示されます。
読むことができないので、*今日*自分の言語で読みたいだけです。

**~900 バイト ローダー** を `app.asar` 内の 1 つの既存のエントリに書き込むことで機能します。
(正確な元のサイズにパディングされ、整合性ハッシュが書き換えられます)、実際の
小さなローカル HTTP サーバーからの翻訳層。最初のパッチの後は決して触れないでください
アプリバンドルを再度実行します。翻訳レイヤーを繰り返して、⌘R を押します。

```
app.asar ──(loader stub)──► http://127.0.0.1:7799/payload.js ──► DOM sweeper + dictionary
```

## デモ

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

再起動後、英語の UI テキストは表示どおりに置き換えられ、新しい文字列はすべて置き換えられます。
`mydict.json`に着陸します:

```console
$ cat mydict.json
{
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。",
  "Send a message to get started": "傳個訊息開始吧",
  "Settings saved successfully": "設定儲存成功"
}
```

翻訳について考えが変わりましたか?そのファイルを編集し、アプリ内で ⌘R を押します。

## ロケール ファイルを編集するだけではどうでしょうか?

- 多くの Electron アプリ hard-code JSX/TSX では英語。編集するロケール ファイルがありません。
- アプリはすでに構築され、署名されています。再構築とは、ツールチェーン全体をセットアップすることを意味します。
- アプリをフォークするのではなく、アプリの更新に応じて **新しい** 文字列を翻訳し続ける必要があります。

ロケール JSON ファイルがある場合、`eli locales` はそれらも翻訳します。

## インストール

```bash
pip install electron-live-i18n     # or: pipx install electron-live-i18n
```

Python 3.9 以降、標準ライブラリのみ。依存関係、API キー、アカウントはありません。

## クイックスタート

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

いつでも元に戻すことができます:

```bash
eli revert "/Applications/Some App.app"
```

## 翻訳方法

1. `MutationObserver` はテキスト ノードをたどり、辞書にすでにあるものをすべて置き換えます。インスタント、ゼロ ネットワークです。
2. 異質に見える未知の文字列 (8 文字以上、12% target-script 文字未満) がローカル サーバーに送信されます。
3. サーバーは、パブリック key-less `translate.googleapis.com` エンドポイントを介して翻訳し、結果をディスクにキャッシュし、辞書ファイルに追加します。

したがって、辞書はプレーンな JSON ファイルであり、hand-edit で使用できます。機械翻訳で 95% を実現
数秒で到着します。扱いにくい10本の弦を手で修正すると、固定されたままになります。

```json
{
  "Send a message to get started": "傳個訊息開始吧",
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。"
}
```

## AI エージェントに任せてください

マシン上でコマンドを実行してファイルを編集できるアシスタント (Claude Code) を使用している場合、
Cursor、Codex CLI、Cline、Windsurf、Copilot CLI — これを貼り付けると、全体が処理されます。
パッチを適用するエントリの選択を含むフロー:

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

`<APP PATH>` を置き換えます (例: `/Applications/Slack.app`、`C:\Users\me\AppData\Local\Slack`)。
`<LANGUAGE>` および `<LANG CODE>` (`zh-TW`、`zh-CN`、`ja`、`ko`、`es`、`fr`、`de`、`pt`、`ru`、...)。

または、MCP サーバーとして接続し (以下を参照)、次のように言うだけです。
*「このアプリのUIを日本語に翻訳します」*。

## パッチを適用するエントリの選択

`eli inspect` は、front-end エントリをサイズ別にリストします。次のいずれかを選択してください:

- **十分な大きさ** — ローダーは約 900 バイトで、スロット サイズまでパディングされます。
- **レンダラによってロード** — `index.html` がそれを参照していることを確認してください。
- **non-critical** — テレメトリ/分析バンドルが理想的です。元のコンテンツは置き換えられます。

元のコードを保持したい場合は、独自のサーバーからホストして、
`eli serve --extra-js original.js` のペイロード。これがローダーの間接参照の目的です。

## プラットフォーム

| OS |検索するバンドル レイアウト |整合性の修正 |
| --- | --- | --- |
| macOS | `Foo.app/Contents/Resources/app.asar` |アーカイブ ヘッダー ハッシュ ** と ** `Info.plist` の `ElectronAsarIntegrity` |
|ウィンドウズ | `Foo\resources\app.asar`、プラスリスの `Foo\app-1.2.3\resources\app.asar` |アーカイブヘッダーハッシュ |
|リナックス | `/opt/Foo/resources/app.asar` |アーカイブヘッダーハッシュ |

バンドル フォルダーの代わりに、いつでも `app.asar` パスを直接渡すことができます。

Windows の注意事項: インストール ディレクトリ (per-user インストール) を所有するユーザーとしてシェルを実行します。
`%LOCALAPPDATA%` 未満では上昇する必要はありません。 `Program Files` はそうします）。 Squirrel ベースのアプリの作成
更新時に新しい `app-<version>` フォルダーが作成されるため、アップグレード後は re-run `eli patch` になります。
辞書とローカルサーバーはそのままです。

## このプロジェクトはすでに解決されているようです

- **CSP** — Electron のデフォルトの `script-src 'self' blob:` は `eval()` をブロックします。ローダーは、代わりに `Blob` URL を通じてフェッチされたコードを実行します。
- **Asar の整合性** — macOS バンドルでは、`Info.plist` に `ElectronAsarIntegrity` が含まれており、さらにアーカイブ ヘッダー内に per-file SHA256 が含まれています。両方とも書き換えられ、ハッシュは fixed-length 16 進数であるため、ヘッダー サイズは決して変更されず、すべてのファイル オフセットは有効なままになります。
- **サイレントトランケーション** — 無料の翻訳エンドポイントは長い入力を静かにカットします。テキストは段落/文の境界で分割され、再びつなぎ合わされます。
- **自己翻訳ループ** — 独自に挿入された UI に `--skip` セレクターを渡し、それ自体が翻訳されないようにします。

## AIエージェント（MCP）から利用する

`eli mcp` は標準入出力を介してモデル コンテキスト プロトコルを話すため、アシスタントは
バンドル、パッチ適用、文字列またはロケール ファイルの翻訳、元に戻す - すべてを離れることなく実行できます。
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

公開されたツール: `inspect_app`、`patch_app`、`revert_app`、`translate_text`、
`translate_locale_file`。

会話例:

> **あなた:** このアプリのメニューは英語なので、繁体字中国語にします。
> **エージェント:** *(inspect_app → 7 KB non-critical バンドルを選択 → patch_app → 再起動するように指示)*

## ディスク上のロケール ファイル

```bash
eli locales locales/en.json locales/zh-TW.json --target zh-TW
```

未翻訳の文字列のみが送信されます。宛先ファイル内の既存の翻訳が優先されるため、
手動による修正は re-runs まで残ります。書き込みはアトミックです (tmp ファイル + `os.replace`)。

## Markdown ドキュメント全体を翻訳する

```bash
eli md README.md README.ja.md --target ja
```

コード ブロック、インライン コード、URL、テーブル ルールは保持されます。散文のみが翻訳されます。
このリポジトリのローカライズされた README はこの方法で作成されました。

## 図書館の利用

```python
from eli.translate import Translator
from eli.asar import read_header, patch_entry

tr = Translator(target="ja", cache_path=".cache.json")
print(tr.translate("Settings saved successfully"))

header, header_str, size, base = read_header("/path/to/app.asar")
```

## 範囲と誠実さ

- macOS 上で開発およびテストされました。 Windows と Linux のバンドルは同じ asar レイアウトを使用しており、
  サポートされています (「プラットフォーム」を参照)。 `Info.plist` ステップは単にそこには適用されません。
- 署名付きバンドルにパッチを適用すると、その署名が無効になります。 macOS では、ad-hoc/未署名のアプリが保持されます
  働く;強化され、公証されたアプリは起動を拒否する場合があります。テストしてバックアップを保管してください。
- これは、**自分のマシンと自分のアプリのコピー**用のツールです。ライセンスを尊重する
  あなたが翻訳しているものは何でも。

## ライセンス

MIT
