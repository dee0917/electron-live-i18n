# electron-live-i18n

> [English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)
>
> *아래 번역은 본 툴 자체(`eli locales` / `eli tr`)로 제작되었으며, 가볍게 리뷰한 것입니다. 귀하의 언어에서 문구가 잘못 읽힌다면 PR을 환영합니다.*

**모든 패키지 Electron 앱**을 실시간 번역하세요. 다시 빌드할 필요도, 소스 코드도, API 키도 필요하지 않습니다.

대부분의 i18n 도구는 사용자가 앱을 소유하고 해당 로케일 파일을 편집할 수 있다고 가정합니다. 이것은
다른 경우: 배송되고 서명되었으며 `app.asar`로 포장된 Electron 앱으로 영어를 보여줍니다.
읽을 수는 없지만 *오늘* 당신의 언어로 번역되기를 원합니다.

`app.asar` 내부의 기존 항목 하나에 **~900바이트 로더**를 작성하여 작동합니다.
(정확한 원본 크기로 패딩되고 무결성 해시가 다시 작성됨) 실제
작은 로컬 HTTP 서버의 번역 레이어. 첫 번째 패치 이후에는 절대 만지지 마세요
앱 번들을 다시 실행하세요. 번역 레이어를 반복하고 ⌘R을 누르세요.

```
app.asar ──(loader stub)──► http://127.0.0.1:7799/payload.js ──► DOM sweeper + dictionary
```

## 데모

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

다시 시작하면 영어 UI 텍스트가 표시된 대로 바뀌고 모든 새 문자열이
`mydict.json`에 토지:

```console
$ cat mydict.json
{
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。",
  "Send a message to get started": "傳個訊息開始吧",
  "Settings saved successfully": "設定儲存成功"
}
```

번역에 대한 마음이 바뀌셨나요? 해당 파일을 편집하고 앱에서 ⌘R을 누르세요.

## 로케일 파일만 편집하면 되지 않나요?

- 많은 Electron 앱 hard-code JSX/TSX의 영어; 편집할 로케일 파일이 없습니다.
- 앱이 이미 구축되고 서명되었습니다. 재구축은 전체 툴체인을 설정하는 것을 의미합니다.
- 앱이 업데이트될 때 **새** 문자열을 포크하는 것이 아니라 계속 번역하고 싶습니다.

로케일 JSON 파일이 *있는 경우* `eli locales`는 해당 파일도 번역합니다.

## 설치하다

```bash
pip install electron-live-i18n     # or: pipx install electron-live-i18n
```

Python 3.9+, 표준 라이브러리 전용. 종속성, API 키, 계정이 없습니다.

## 빠른 시작

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

언제든지 실행취소하세요.

```bash
eli revert "/Applications/Some App.app"
```

## 번역 방법

1. `MutationObserver`는 텍스트 노드를 탐색하고 이미 사전에 있는 모든 항목을 대체합니다. 즉각적이고 네트워크가 필요하지 않습니다.
2. 외부처럼 보이는 알 수 없는 문자열(≥8자, <12% target-script 문자)은 로컬 서버로 전송됩니다.
3. 서버는 공용 key-less `translate.googleapis.com` 엔드포인트를 통해 변환하고 결과를 디스크에 캐시한 후 사전 파일에 추가합니다.

따라서 사전은 hand-edit할 수 있는 일반 JSON 파일입니다. 기계 번역으로 95%를 얻을 수 있습니다
몇 초 만에; 어색한 10개의 줄을 손으로 고치면 고정된 상태로 유지됩니다.

```json
{
  "Send a message to get started": "傳個訊息開始吧",
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。"
}
```

## AI 에이전트에게 맡기세요

컴퓨터에서 명령을 실행하고 파일을 편집할 수 있는 도우미(Claude Code)를 사용하는 경우
커서, Codex CLI, Cline, Windsurf, Copilot CLI — 이것을 붙여넣으면 전체를 처리합니다.
패치할 항목 선택을 포함한 흐름:

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

`<APP PATH>` 교체(예: `/Applications/Slack.app`, `C:\Users\me\AppData\Local\Slack`),
`<LANGUAGE>` 및 `<LANG CODE>` (`zh-TW`, `zh-CN`, `ja`, `ko`, `es`, `fr`, `de`, `pt`, `ru`, ...).

또는 MCP 서버로 연결하고(아래 참조) 다음과 같이 말합니다.
*"이 앱의 UI를 일본어로 번역합니다"*.

## 패치할 항목 선택

`eli inspect`는 front-end 항목을 크기별로 나열합니다. 다음 중 하나를 선택하세요.

- **충분히 크다** — 로더는 ~900바이트이고 슬롯 크기까지 채워집니다.
- **렌더러에 의해 로드됨** — `index.html`가 이를 참조하는지 확인하세요.
- **non-critical** — 원격 측정/분석 번들이 이상적입니다. 원본 콘텐츠가 대체됩니다.

원본 코드를 유지하려면 자체 서버에서 호스팅하고
`eli serve --extra-js original.js`의 페이로드. 이것이 바로 로더 간접 참조의 목적입니다.

## 플랫폼

| OS | 찾는 번들 레이아웃 | 무결성 수정 |
| --- | --- | --- |
| macOS | `Foo.app/Contents/Resources/app.asar` | 아카이브 헤더 해시 **및** `Info.plist`의 `ElectronAsarIntegrity` |
| 윈도우 | `Foo\resources\app.asar`, 다람쥐의 `Foo\app-1.2.3\resources\app.asar` | 아카이브 헤더 해시 |
| 리눅스 | `/opt/Foo/resources/app.asar` | 아카이브 헤더 해시 |

번들 폴더 대신 언제든지 `app.asar` 경로를 직접 전달할 수 있습니다.

Windows 참고 사항: 설치 디렉터리를 소유한 사용자로 셸을 실행합니다(per-user 설치
`%LOCALAPPDATA%` 미만에서는 고도가 필요하지 않습니다. `Program Files` 그렇습니다). 다람쥐 기반 앱 생성
업데이트 시 새로운 `app-<version>` 폴더가 생성되므로 업그레이드 후 re-run `eli patch` —
사전과 로컬 서버는 그대로 유지됩니다.

## 이 프로젝트는 이미 해결되었습니다.

- **CSP** — Electron의 기본 `script-src 'self' blob:` 블록 `eval()`. 대신 로더는 `Blob` URL을 통해 가져온 코드를 실행합니다.
- **Asar 무결성** — macOS 번들은 `Info.plist`에 `ElectronAsarIntegrity`를 포함하고 아카이브 헤더 내부에 per-file SHA256을 포함합니다. 둘 다 다시 작성되며 해시가 fixed-length 16진수이므로 헤더 크기가 변경되지 않으므로 모든 파일 오프셋이 유효하게 유지됩니다.
- **자동 잘림** — 무료 번역 엔드포인트는 긴 입력을 조용히 자릅니다. 텍스트는 단락/문장 경계에서 분할되어 다시 연결됩니다.
- **자체 번역 루프** — 자체적으로 번역되지 않도록 삽입된 UI에 대해 `--skip` 선택기를 전달합니다.

## AI 에이전트(MCP)에서 사용

`eli mcp`는 stdio를 통해 Model Context Protocol을 말하므로 어시스턴트가
번들링, 패치, 문자열 또는 로케일 파일 번역 및 되돌리기 — 모두 떠나지 않고도 가능합니다.
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

노출된 도구: `inspect_app`, `patch_app`, `revert_app`, `translate_text`,
`translate_locale_file`.

대화 예시:

> **당신:** 이 앱의 메뉴는 영어로 되어 있습니다. 중국어 번체로 만드세요.
> **에이전트:** *(inspect_app → 7KB non-critical 번들 선택 → patch_app → 다시 시작하라는 메시지 표시)*

## 디스크의 로케일 파일

```bash
eli locales locales/en.json locales/zh-TW.json --target zh-TW
```

번역되지 않은 문자열만 전송됩니다. 대상 파일의 기존 번역이 승리하므로
수동 수정은 re-runs 유지됩니다. 쓰기는 원자성입니다(tmp 파일 + `os.replace`).

## 전체 Markdown 문서 번역하기

```bash
eli md README.md README.ja.md --target ja
```

코드 블록, 인라인 코드, URL 및 테이블 규칙은 보존됩니다. 산문만 번역되었습니다.
이 저장소의 현지화된 README는 이러한 방식으로 생성되었습니다.

## 도서관 이용

```python
from eli.translate import Translator
from eli.asar import read_header, patch_entry

tr = Translator(target="ja", cache_path=".cache.json")
print(tr.translate("Settings saved successfully"))

header, header_str, size, base = read_header("/path/to/app.asar")
```

## 범위와 정직성

- macOS에서 개발 및 테스트되었습니다. Windows 및 Linux 번들은 동일한 asar 레이아웃을 사용하며
  지원됨(플랫폼 참조) `Info.plist` 단계는 거기에 적용되지 않습니다.
- 서명된 번들을 패치하면 서명이 무효화됩니다. macOS에서는 ad-hoc/unsigned 앱이 다음을 유지합니다.
  일하고 있는; 강화되고 공증된 앱은 출시를 거부할 수 있습니다. 테스트하고 백업을 유지하십시오.
- 이것은 **자신의 컴퓨터와 앱의 사본**을 위한 도구입니다. 라이센스를 존중하세요
  당신이 번역하는 모든 것.

## 특허

MIT
