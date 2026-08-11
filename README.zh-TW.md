# electron-live-i18n

> [English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)
>
> *Translations below were produced by this tool itself (`eli locales` / `eli tr`) and lightly reviewed. PRs welcome if a phrase reads wrong in your language.*

把**任何已經打包好的 Electron App** 介面即時翻成你看得懂的語言——不用重新編譯、不用原始碼、不用 API 金鑰。

市面上的 i18n 工具都假設你擁有這個 App、可以改它的語言檔。這個工具處理的是另一種情況：一個已經出貨、簽好章、包在 `app.asar` 裡的 Electron App，介面全是你看不懂的英文，而你今天就想把它變成中文。

做法是把一段**大約 900 位元組的載入器**寫進 `app.asar` 裡某一個現有檔案的位置（補白到與原檔完全同樣長度，再把完整性雜湊改掉），真正的翻譯層則由本機的小型 HTTP 伺服器提供。打完這一次補丁之後，你再也不用碰那個 App——改翻譯、加字典，按一下 ⌘R 就生效。

```
app.asar ──(載入器)──► http://127.0.0.1:7799/payload.js ──► DOM 掃描器 + 字典
```

## 實際操作長這樣

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
```

重開 App 之後，畫面上的英文會隨著出現被換掉，每一句新學到的都會寫進字典：

```console
$ cat mydict.json
{
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。",
  "Send a message to get started": "傳個訊息開始吧",
  "Settings saved successfully": "設定儲存成功"
}
```

覺得哪一句翻得爛？改那個檔，回到 App 按 ⌘R，立刻生效。

## 為什麼不直接改語言檔就好

- 很多 Electron App 的英文是寫死在 JSX/TSX 裡的，根本沒有語言檔可以改。
- App 已經編譯簽章完成，要重新編譯等於要把它整套開發環境裝起來。
- 你想要的是「以後它更新、出現新句子也能繼續翻」，而不是分叉一份自己維護。

如果你手上**真的有** JSON 語言檔，`eli locales` 也能翻那個。

## 安裝

```bash
pip install electron-live-i18n     # 或 pipx install electron-live-i18n
```

Python 3.9 以上，只用標準函式庫。沒有相依套件、不用金鑰、不用註冊帳號。

## 快速開始

```bash
# 1. 看看 App 裡面有什麼，挑一個放載入器的位置
eli inspect "/Applications/Some App.app"

# 2. 啟動翻譯伺服器（保持執行）
eli serve --target zh-TW --dict ./mydict.json &

# 3. 對 App 打一次補丁
eli patch "/Applications/Some App.app" --entry dist/vendor-analytics.js

# 4. 重開 App——你用到哪裡，哪裡就變中文
```

隨時可以還原：

```bash
eli revert "/Applications/Some App.app"
```

## 翻譯是怎麼發生的

1. `MutationObserver` 掃過所有文字節點，字典裡已經有的直接換掉——瞬間完成，不連網。
2. 字典裡沒有、而且看起來像外文的句子（英文字母 8 個以上、目標語言文字佔比低於 12%）送到本機伺服器。
3. 伺服器透過公開、免金鑰的 `translate.googleapis.com` 端點翻譯，結果存到磁碟快取，並附加到你的字典檔。

所以字典就是一份你可以手改的 JSON。機器翻譯幾秒鐘幫你完成 95%，剩下那十句彆扭的自己修一次，之後永遠是對的。

## 讓 AI 幫你做完整套

如果你在用可以在你電腦上執行指令、改檔案的助理——Claude Code、Cursor、Codex CLI、Cline、Windsurf、Copilot CLI——把下面這段貼給它，它會從頭做到尾，連挑哪個檔案打補丁都幫你決定：

```text
請用 https://github.com/dee0917/electron-live-i18n 把「<APP 路徑>」的介面翻成<語言>。

步驟：
1. pipx install electron-live-i18n（或 pip install electron-live-i18n）
2. 執行 `eli inspect "<APP 路徑>"`，挑一個夠大（超過 1 KB）而且不重要的前端 .js 檔
   （analytics、vendor 這類最適合）。告訴我你挑了哪個、為什麼。
3. 在背景執行 `eli serve --target <語言代碼> --dict ./mydict.json`。
4. 執行 `eli patch "<APP 路徑>" --entry <你挑的那個檔>`，然後重開 App。
5. 確認備份檔存在，並提醒我 `eli revert "<APP 路徑>"` 可以完全還原。
```

把 `<APP 路徑>`（例如 `/Applications/Slack.app`、`C:\Users\me\AppData\Local\Slack`）、
`<語言>` 與 `<語言代碼>`（`zh-TW`、`zh-CN`、`ja`、`ko`、`es`、`fr`、`de`、`pt`、`ru`…）換成你的。

或者把它接成 MCP 伺服器（見下面），然後直接說一句
「把這個 App 的介面翻成日文」。

## 該挑哪個檔案打補丁

`eli inspect` 會照大小列出前端檔案。挑一個：

- **夠大**——載入器約 900 位元組，會補白到該檔原本的大小，
- **是渲染程序會載入的**——確認 `index.html` 有引用它，
- **不重要的**——遙測、分析類的檔案最理想，因為原本的內容會被取代。

如果你想保留原本的程式碼，把它放到自己的伺服器上，用 `eli serve --extra-js original.js`
一起送出去。載入器這一層間接就是為了這個而存在。

## 支援的平台

| 系統 | 會去找的位置 | 完整性修補 |
| --- | --- | --- |
| macOS | `Foo.app/Contents/Resources/app.asar` | 封存標頭雜湊**加上** `Info.plist` 裡的 `ElectronAsarIntegrity` |
| Windows | `Foo\resources\app.asar`，以及 Squirrel 的 `Foo\app-1.2.3\resources\app.asar` | 封存標頭雜湊 |
| Linux | `/opt/Foo/resources/app.asar` | 封存標頭雜湊 |

你也可以直接給 `app.asar` 的路徑，不一定要給資料夾。

Windows 補充：用擁有該安裝目錄的使用者身分開終端機（裝在 `%LOCALAPPDATA%` 的每使用者安裝不需要提權，`Program Files` 則需要）。Squirrel 類型的 App 每次更新會建一個新的 `app-<版本>` 資料夾，所以更新之後要重跑一次 `eli patch`——字典跟本機伺服器都不受影響。

## 這個專案已經替你踩過的坑

- **CSP**——Electron 預設的 `script-src 'self' blob:` 會擋掉 `eval()`。載入器改用 `Blob` URL 執行抓回來的程式碼。
- **asar 完整性驗證**——macOS 的 App 除了封存標頭裡的單檔 SHA256，還會在 `Info.plist` 帶一份 `ElectronAsarIntegrity`。兩個都要改；因為雜湊是固定長度的十六進位字串，標頭長度不會變，所有檔案位移也就都還有效。
- **靜默截斷**——免費的翻譯端點對長文會直接切掉一段而且不告訴你。所以文字要照段落與句子邊界切塊，翻完再接回去。
- **自己翻自己**——用 `--skip` 指定你自己注入的 UI 選擇器，不然它會把自己的介面也翻一遍。

## 給 AI 代理使用（MCP）

`eli mcp` 走 stdio 講 Model Context Protocol，所以助理可以直接看 App 內容、打補丁、翻字串或語言檔、還原，你完全不用離開對話。

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

提供的工具：`inspect_app`、`patch_app`、`revert_app`、`translate_text`、`translate_locale_file`。

## 磁碟上的語言檔

```bash
eli locales locales/en.json locales/zh-TW.json --target zh-TW
```

只會送出還沒翻的字串；目的檔裡已經存在的翻譯優先保留，所以你手動修過的內容重跑也不會被蓋掉。寫檔是原子的（暫存檔 + `os.replace`）。

## 翻整份 Markdown 文件

```bash
eli md README.md README.ja.md --target ja
```

程式碼區塊、行內程式碼、網址與表格框線都會原樣保留，只翻文字。這個 repo 的各語言版本就是這樣產生的。

## 當函式庫用

```python
from eli.translate import Translator
from eli.asar import read_header, patch_entry

tr = Translator(target="ja", cache_path=".cache.json")
print(tr.translate("Settings saved successfully"))

header, header_str, size, base = read_header("/path/to/app.asar")
```

## 誠實說明範圍

- 開發與測試主要在 macOS 上。Windows 與 Linux 的 asar 結構相同，也支援（見「支援的平台」），只是 `Info.plist` 那一步用不到。
- 打補丁會讓程式碼簽章失效。未簽章／ad-hoc 簽章的 App 照常運作；經過 hardened runtime 與公證的 App 可能會拒絕啟動。請先測試，並保留備份。
- 這是給**你自己的電腦、你自己那份 App** 用的工具。請尊重你所翻譯的軟體的授權條款。

## 授權

MIT
