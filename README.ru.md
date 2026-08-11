# electron-live-i18n

> [English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)
>
> *Приведенные ниже переводы были выполнены самим этим инструментом (`eli locales` / `eli tr`) и слегка проверены. Пиарщики приветствуются, если фраза неправильно читается на вашем языке.*

Live-перевод **любого упакованного приложения Electron** — без пересборки, без исходного кода, без ключа API.

Большинство инструментов i18n предполагают, что вы являетесь владельцем приложения и можете редактировать его файлы локали. Это для
другой случай: отправленное, подписанное и упакованное `app.asar` приложение Electron, которое показывает вам английский язык.
не умею читать, и ты просто хочешь, чтобы это было на твоем языке *сегодня*.

Это работает путем записи **~900-байтового загрузчика** в одну существующую запись внутри `app.asar`.
(дополнен до точного исходного размера, хеши целостности переписаны) и обслуживает фактические
уровень трансляции с крошечного локального HTTP-сервера. После этого первого патча ты никогда не трогаешь
снова пакет приложения — пройдитесь по уровню перевода и нажмите ⌘R.

```
app.asar ──(loader stub)──► http://127.0.0.1:7799/payload.js ──► DOM sweeper + dictionary
```

## Демо

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

После перезапуска текст пользовательского интерфейса на английском языке заменяется по мере его появления, и каждая новая строка
земли в `mydict.json`:

```console
$ cat mydict.json
{
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。",
  "Send a message to get started": "傳個訊息開始吧",
  "Settings saved successfully": "設定儲存成功"
}
```

Передумали переводить? Отредактируйте этот файл и нажмите ⌘R в приложении.

## Почему бы просто не отредактировать файлы локали?

- Многие приложения Electron hard-code английский в JSX/TSX; нет файла локали для редактирования.
- Приложение уже создано и подписано; перестройка означает настройку всей цепочки инструментов.
- Вы хотите продолжать переводить **новые** строки по мере обновления приложения, а не создавать его форки.

Если у вас *есть* есть файлы JSON локали, `eli locales` переводит и их.

## Установить

```bash
pip install electron-live-i18n     # or: pipx install electron-live-i18n
```

Python 3.9+, только стандартная библиотека. Никаких зависимостей, никакого ключа API, никакой учетной записи.

## Быстрый старт

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

Отменить в любой момент:

```bash
eli revert "/Applications/Some App.app"
```

## Как это переводится

1. `MutationObserver` проходит по текстовым узлам и заменяет все, что уже есть в словаре — мгновенно, нулевая сеть.
2. Неизвестные строки, которые выглядят как иностранные (≥8 букв, <12% target-script символов), отправляются на локальный сервер.
3. Сервер переводит через общедоступную конечную точку key-less `translate.googleapis.com`, кэширует результат на диске и добавляет его в файл словаря.

Итак, словарь представляет собой простой файл JSON, который вы можете hand-edit. Машинный перевод поможет вам на 95 %
путь за секунды; почините неуклюжие десять струн вручную, и они останутся зафиксированными.

```json
{
  "Send a message to get started": "傳個訊息開始吧",
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。"
}
```

## Позвольте ИИ-агенту сделать это за вас

Если вы используете помощника, который может запускать команды и редактировать файлы на вашем компьютере — Claude Code,
Курсор, Codex CLI, Cline, Windsurf, Copilot CLI — вставьте это, и оно справится со всем
поток, включая выбор записи для исправления:

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

Замените `<APP PATH>` (например, `/Applications/Slack.app`, `C:\Users\me\AppData\Local\Slack`),
`<LANGUAGE>` и `<LANG CODE>` (`zh-TW`, `zh-CN`, `ja`, `ko`, `es`, `fr`, `de`, `pt`, `ru`, ...).

Или подключите его как сервер MCP (см. ниже) и просто скажите:
*"перевести пользовательский интерфейс этого приложения на японский язык"*.

## Выбор записи для исправления

`eli inspect` перечисляет front-end записей по размеру. Выберите тот, который:

- **достаточно большой** — размер загрузчика составляет ~900 байт и дополняется до размера слота,
- **загружается средством рендеринга** — убедитесь, что `index.html` ссылается на него,
- **non-critical** — пакеты телеметрии/аналитики идеальны; исходное содержимое заменяется.

Если вы хотите сохранить исходный код, разместите его на своем сервере и добавьте в файл
полезная нагрузка с `eli serve --extra-js original.js`. Для этого и нужна косвенность загрузчика.

## Платформы

| ОС | Макет пакета, который он ищет | Исправление целостности |
| --- | --- | --- |
| macOS | `Foo.app/Contents/Resources/app.asar` | хеш заголовка архива **и** `ElectronAsarIntegrity` в `Info.plist` |
| Окна | `Foo\resources\app.asar`, плюс Белка `Foo\app-1.2.3\resources\app.asar` | хеш заголовка архива |
| Линукс | `/opt/Foo/resources/app.asar` | хеш заголовка архива |

Вы всегда можете передать путь `app.asar` напрямую вместо папки пакета.

Примечания для Windows: запускайте оболочку от имени пользователя, которому принадлежит каталог установки (per-user устанавливает
ниже `%LOCALAPPDATA%` возвышение не требуется; `Program Files` да). Приложения на основе Squirrel создают
новая папка `app-<version>` при обновлении, поэтому re-run `eli patch` после обновления —
словарь и локальный сервер не затронуты.

## Попался, этот проект уже решен

- **CSP** — `script-src 'self' blob:` по умолчанию в Electron блокирует `eval()`. Вместо этого загрузчик выполняет полученный код через URL-адрес `Blob`.
- **Целостность Asar** — пакеты macOS содержат `ElectronAsarIntegrity` в `Info.plist`, а также per-file SHA256 внутри заголовка архива. Оба переписаны, и поскольку хеши имеют шестнадцатеричный формат fixed-length, размер заголовка никогда не меняется, поэтому каждое смещение файла остается действительным.
- **Тихое усечение** — конечная точка бесплатного перевода незаметно обрезает длинный ввод. Текст разделяется по границам абзаца/предложения и сшивается обратно.
- **Циклы самоперевода** — передайте селекторы `--skip` для вашего собственного внедренного пользовательского интерфейса, чтобы он не переводил сам себя.

## Используйте его от агента ИИ (MCP)

`eli mcp` передает протокол контекста модели через stdio, поэтому помощник может проверить
собирать пакеты, исправлять их, переводить строки или файлы локали и выполнять возврат — и все это без вашего участия
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

Открытые инструменты: `inspect_app`, `patch_app`, `revert_app`, `translate_text`,
`translate_locale_file`.

Пример разговора:

> **Вы:** Меню этого приложения на английском языке, сделайте его традиционным китайским.
> **Агент:** *(inspect_app → выбирает пакет non-critical размером 7 КБ → patch_app → предлагает перезапустить)*

## Файлы локали на диске

```bash
eli locales locales/en.json locales/zh-TW.json --target zh-TW
```

Отправляются только непереведенные строки; существующие переводы в целевом файле выигрывают, поэтому
ваши ручные исправления сохраняются re-runs. Запись является атомарной (файл tmp + `os.replace`).

## Перевод всей документации Markdown

```bash
eli md README.md README.ja.md --target ja
```

Блоки кода, встроенный код, URL-адреса и правила таблиц сохраняются; переводится только проза.
Локализованные файлы README в этом репозитории были созданы таким образом.

## Использование библиотеки

```python
from eli.translate import Translator
from eli.asar import read_header, patch_entry

tr = Translator(target="ja", cache_path=".cache.json")
print(tr.translate("Settings saved successfully"))

header, header_str, size, base = read_header("/path/to/app.asar")
```

## Объем и честность

- Разработано и протестировано на macOS. Пакеты Windows и Linux используют одинаковую структуру asar и
  поддерживается (см. Платформы); шаг `Info.plist` здесь просто неприменим.
- Исправление подписанного пакета делает его подпись недействительной. В macOS приложение ad-hoc/неподписанное сохраняет
  работающий; защищенное нотариально заверенное приложение может отказаться запускаться. Протестируйте и сохраните резервную копию.
- Это инструмент для **вашего компьютера и вашей собственной копии** приложения. Уважайте лицензию
  того, что вы переводите.

## Лицензия

MIT
