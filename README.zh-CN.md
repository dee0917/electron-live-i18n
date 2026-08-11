# electron-live-i18n

> [English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)
>
> *以下翻译由该工具本身生成（`eli locales` / `eli tr`）并经过轻微审查。如果某个短语在您的语言中读错了，欢迎 PR。*

实时翻译 **任何打包的 Electron 应用程序** — 无需重建，无需源代码，无需 API 密钥。

大多数 i18n 工具假设您拥有该应用程序并且可以编辑其区域设置文件。这个是为了
另一种情况：一个已发货、已签名、`app.asar` 包装的 Electron 应用程序，可以向您显示英语
无法阅读，而您*今天*只需要您的语言版本。

它的工作原理是将 **~900 字节加载器**写入 `app.asar` 内的一个现有条目中
（填充到确切的原始大小，重写完整性哈希），并提供实际的
来自小型本地 HTTP 服务器的转换层。在第一个补丁之后你就再也没有碰过
再次应用程序包 - 在翻译层上迭代并按 ⌘R。

```
app.asar ──(loader stub)──► http://127.0.0.1:7799/payload.js ──► DOM sweeper + dictionary
```

## 演示

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

重新启动后，英文 UI 文本将按原样替换，并且每个新字符串
落在 `mydict.json`：

```console
$ cat mydict.json
{
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。",
  "Send a message to get started": "傳個訊息開始吧",
  "Settings saved successfully": "設定儲存成功"
}
```

您改变了关于翻译的想法吗？编辑该文件并在应用程序中按 ⌘R。

## 为什么不直接编辑语言环境文件呢？

- 许多 Electron 应用程序 hard-code 英语采用 JSX/TSX；没有要编辑的区域设置文件。
- 该应用程序已经构建并签名；重建意味着建立整个工具链。
- 您希望在应用程序更新时继续翻译**新**字符串，而不是分叉它。

如果您*确实*有语言环境 JSON 文件，`eli locales` 也会翻译这些文件。

## 安装

```bash
pip install electron-live-i18n     # or: pipx install electron-live-i18n
```

Python 3.9+，仅限标准库。没有依赖项、没有 API 密钥、没有帐户。

## 快速启动

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

随时撤消：

```bash
eli revert "/Applications/Some App.app"
```

## 怎么翻译的

1. `MutationObserver` 遍历文本节点并替换字典中已有的任何内容 - 即时、零网络。
2. 看起来像是外国的未知字符串（≥8 个字母，<12% target-script 字符）被发送到本地服务器。
3. 服务器通过公共 key-less `translate.googleapis.com` 端点进行翻译，将结果缓存在磁盘上，并将其附加到字典文件中。

所以字典是一个普通的 JSON 文件，你可以hand-edit。机器翻译让你达到 95%
以秒为单位的路线；用手固定尴尬的十根弦，它们就保持固定。

```json
{
  "Send a message to get started": "傳個訊息開始吧",
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。"
}
```

## 让人工智能代理为您做这件事

如果您使用可以在计算机上运行命令和编辑文件的助手 - Claude Code，
Cursor、Codex CLI、Cline、Windsurf、Copilot CLI — 粘贴此内容，它将处理整个过程
流程，包括选择要修补的条目：

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

替换 `<APP PATH>`（例如 `/Applications/Slack.app`、`C:\Users\me\AppData\Local\Slack`），
`<LANGUAGE>` 和 `<LANG CODE>`（`zh-TW`、`zh-CN`、`ja`、`ko`、`es`、`fr`、`de`、`pt`、`ru`...）。

或者将其连接为 MCP 服务器（见下文），然后说
*“将此应用程序的用户界面翻译成日语”*。

## 选择要修补的条目

`eli inspect` 按大小列出 front-end 条目。选择一个是：

- **足够大** — 加载器约为 900 字节，并填充到插槽大小，
- **由渲染器加载** — 检查 `index.html` 引用它，
- **non-critical** — 遥测/分析包是理想的选择；原来的内容被替换了。

如果您想保留原始代码，请从您自己的服务器托管它并将其附加到
有效负载为`eli serve --extra-js original.js`。这就是加载器间接的用途。

## 平台

|操作系统 |它寻找的捆绑布局 |完整性修复|
| --- | --- | --- |
| macOS | `Foo.app/Contents/Resources/app.asar` | `Info.plist` 中的存档标头哈希**和** `ElectronAsarIntegrity` |
|窗户| `Foo\resources\app.asar`，加上松鼠的`Foo\app-1.2.3\resources\app.asar` |存档头哈希 |
| Linux | `/opt/Foo/resources/app.asar` |存档头哈希 |

您始终可以直接传递 `app.asar` 路径而不是捆绑文件夹。

Windows 说明：以拥有安装目录的用户身份运行 shell（per-user 安装
`%LOCALAPPDATA%`以下无需加高； `Program Files` 是）。基于 Squirrel 的应用程序创建
更新时会出现一个新的 `app-<version>` 文件夹，因此升级后会出现 re-run `eli patch` —
字典和本地服务器保持不变。

## 这个项目的问题已经解决了

- **CSP** — Electron 的默认 `script-src 'self' blob:` 块 `eval()`。加载器通过 `Blob` URL 执行获取的代码。
- **Asar 完整性** — macOS 捆绑包在 `Info.plist` 中携带 `ElectronAsarIntegrity`，以及存档标头内的 per-file SHA256。两者都被重写，并且由于哈希值是 fixed-length 十六进制，标头大小永远不会改变，因此每个文件偏移量保持有效。
- **静默截断** — 自由翻译端点会悄悄地截断长输入。文本在段落/句子边界处分割并缝合在一起。
- **自翻译循环** — 为您自己注入的 UI 传递 `--skip` 选择器，这样它就不会自行翻译。

## 从 AI 代理 (MCP) 使用它

`eli mcp` 通过 stdio 讲模型上下文协议，因此助手可以检查
捆绑、修补、翻译字符串或语言环境文件并恢复 — 所有这一切都无需您离开
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

暴露工具：`inspect_app`、`patch_app`、`revert_app`、`translate_text`、
`translate_locale_file`。

对话示例：

> **你：** 这个应用程序的菜单是英文的，请将其设为繁体中文。
> **代理：** *（inspect_app → 选择一个 7 KB non-critical 包 → patch_app → 告诉您重新启动）*

## 磁盘上的语言环境文件

```bash
eli locales locales/en.json locales/zh-TW.json --target zh-TW
```

仅发送未翻译的字符串；目标文件 win 中的现有翻译，因此
您的手动修复仍然存在re-runs。写入是原子的（tmp 文件 + `os.replace`）。

## 翻译整个 Markdown 文档

```bash
eli md README.md README.ja.md --target ja
```

保留代码块、内联代码、URL 和表规则；仅翻译散文。
本存储库中的本地化自述文件就是通过这种方式生成的。

## 图书馆使用

```python
from eli.translate import Translator
from eli.asar import read_header, patch_entry

tr = Translator(target="ja", cache_path=".cache.json")
print(tr.translate("Settings saved successfully"))

header, header_str, size, base = read_header("/path/to/app.asar")
```

## 范围和诚实

- 在 macOS 上开发和测试。 Windows 和 Linux 捆绑包使用相同的 asar 布局，并且
  支持（参见平台）； `Info.plist` 步骤根本不适用。
- 修补已签名的包会使其签名失效。在 macOS 上，ad-hoc/未签名的应用程序会保留
  在职的;经过强化的、经过公证的应用程序可能会拒绝启动。测试一下，并保留备份。
- 这是一个用于**您自己的计算机和您自己的应用程序副本**的工具。尊重许可
  无论你正在翻译什么。

## 执照

MIT
