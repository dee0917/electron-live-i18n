# electron-live-i18n

> [English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)
>
> *Las traducciones a continuación fueron producidas por esta propia herramienta (`eli locales` / `eli tr`) y revisadas ligeramente. Los RP son bienvenidos si una frase se lee mal en su idioma.*

Traduce en vivo **cualquier aplicación Electron empaquetada**: sin reconstrucción, sin código fuente, sin clave API.

La mayoría de las herramientas de i18n asumen que usted es propietario de la aplicación y puede editar sus archivos locales. Este es para
el otro caso: una aplicación Electron enviada, firmada y llena de `app.asar` que muestra inglés
No puedo leer y solo lo quieres en tu idioma *hoy*.

Funciona escribiendo un **~cargador de 900 bytes** en una entrada existente dentro de `app.asar`
(rellenado al tamaño original exacto, hashes de integridad reescritos) y entregando el contenido real
capa de traducción desde un pequeño servidor HTTP local. Después de ese primer parche que nunca tocas
el paquete de aplicaciones nuevamente: itere en la capa de traducción y presione ⌘R.

```
app.asar ──(loader stub)──► http://127.0.0.1:7799/payload.js ──► DOM sweeper + dictionary
```

## Manifestación

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

Después del reinicio, el texto de la interfaz de usuario en inglés se reemplaza tal como aparece y cada cadena nueva
aterriza en `mydict.json`:

```console
$ cat mydict.json
{
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。",
  "Send a message to get started": "傳個訊息開始吧",
  "Settings saved successfully": "設定儲存成功"
}
```

¿Cambiaste de opinión acerca de una traducción? Edite ese archivo y presione ⌘R en la aplicación.

## ¿Por qué no simplemente editar los archivos locales?

- Muchas aplicaciones de Electron hard-code inglés en JSX/TSX; no hay ningún archivo local para editar.
- La aplicación ya está creada y firmada; reconstruir significa configurar toda su cadena de herramientas.
- Desea seguir traduciendo cadenas **nuevas** a medida que se actualiza la aplicación, no bifurcarla.

Si *tiene* archivos JSON locales, `eli locales` también los traduce.

## Instalar

```bash
pip install electron-live-i18n     # or: pipx install electron-live-i18n
```

Python 3.9+, biblioteca estándar únicamente. Sin dependencias, sin clave API, sin cuenta.

## Inicio rápido

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

Deshacer en cualquier momento:

```bash
eli revert "/Applications/Some App.app"
```

## como se traduce

1. Un `MutationObserver` recorre los nodos de texto y reemplaza cualquier cosa que ya esté en el diccionario: red instantánea y cero.
2. Las cadenas desconocidas que parecen extrañas (≥8 letras, <12% target-script caracteres) se envían al servidor local.
3. El servidor traduce a través del punto final público key-less `translate.googleapis.com`, almacena en caché el resultado en el disco y lo agrega a su archivo de diccionario.

Entonces el diccionario es un archivo JSON simple que puedes hand-edit. La traducción automática te ofrece el 95%
del camino en segundos; arregla las incómodas diez cuerdas a mano y permanecerán fijas.

```json
{
  "Send a message to get started": "傳個訊息開始吧",
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。"
}
```

## Deje que un agente de IA lo haga por usted

Si utiliza un asistente que puede ejecutar comandos y editar archivos en su máquina: Claude Code,
Cursor, Codex CLI, Cline, Windsurf, Copilot CLI: pegue esto y se encargará de todo
flujo, incluida la elección de la entrada para parchear:

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

Reemplace `<APP PATH>` (por ejemplo, `/Applications/Slack.app`, `C:\Users\me\AppData\Local\Slack`),
`<LANGUAGE>` y `<LANG CODE>` (`zh-TW`, `zh-CN`, `ja`, `ko`, `es`, `fr`, `de`, `pt`, `ru`, ...).

O conéctelo como un servidor MCP (ver más abajo) y simplemente diga
*"traducir la interfaz de usuario de esta aplicación al japonés"*.

## Elegir una entrada para parchear

`eli inspect` enumera las entradas front-end por tamaño. Elija uno que sea:

- **suficientemente grande**: el cargador tiene ~900 bytes y se rellena hasta el tamaño de la ranura.
- **cargado por el renderizador** — comprueba que `index.html` haga referencia a él,
- **non-critical**: los paquetes de telemetría/análisis son ideales; se reemplaza el contenido original.

Si desea conservar el código original, alójelo desde su propio servidor y añádalo al
carga útil con `eli serve --extra-js original.js`. Para eso está la dirección indirecta del cargador.

## Plataformas

| SO | Diseño del paquete que busca | Reparación de integridad |
| --- | --- | --- |
| MacOS | `Foo.app/Contents/Resources/app.asar` | hash del encabezado del archivo **y** `ElectronAsarIntegrity` en `Info.plist` |
| Ventanas | `Foo\resources\app.asar`, más `Foo\app-1.2.3\resources\app.asar` de Ardilla | hash de encabezado de archivo |
| Linux | `/opt/Foo/resources/app.asar` | hash de encabezado de archivo |

Siempre puedes pasar la ruta `app.asar` directamente en lugar de la carpeta del paquete.

Notas de Windows: ejecute el shell como el usuario propietario del directorio de instalación (per-user installs
por debajo de `%LOCALAPPDATA%` no necesita elevación; `Program Files` lo hace). Se crean aplicaciones basadas en ardillas
una nueva carpeta `app-<version>` en la actualización, por lo que re-run `eli patch` después de una actualización, la
El diccionario y el servidor local no se modifican.

## Tengo este proyecto ya resuelto.

- **CSP**: el valor predeterminado de Electron `script-src 'self' blob:` bloquea `eval()`. En su lugar, el cargador ejecuta el código recuperado a través de una URL `Blob`.
- **Integridad de Asar**: los paquetes de macOS llevan `ElectronAsarIntegrity` en `Info.plist`, más un per-file SHA256 dentro del encabezado del archivo. Ambos se reescriben y, como los hashes son fixed-length hexadecimales, el tamaño del encabezado nunca cambia, por lo que cada desplazamiento de archivo sigue siendo válido.
- **Truncado silencioso**: el punto final de traducción gratuita corta silenciosamente la entrada larga. El texto se divide en los límites del párrafo/oración y se vuelve a unir.
- **Bucles de autotraducción**: pase los selectores `--skip` para su propia interfaz de usuario inyectada para que no se traduzca sola.

## Úselo desde un agente de IA (MCP)

`eli mcp` habla el protocolo de contexto del modelo a través de stdio, para que un asistente pueda inspeccionar un
agrupar, parchear, traducir cadenas o archivos locales y revertir, todo sin tener que salir
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

Herramientas expuestas: `inspect_app`, `patch_app`, `revert_app`, `translate_text`,
`translate_locale_file`.

Ejemplo de conversación:

> **Tú:** El menú de esta aplicación está en inglés, conviértelo en chino tradicional.
> **Agente:** *(inspect_app → elige un paquete non-critical de 7 KB → patch_app → le indica que reinicie)*

## Archivos locales en el disco

```bash
eli locales locales/en.json locales/zh-TW.json --target zh-TW
```

Sólo se envían cadenas sin traducir; las traducciones existentes en el archivo de destino ganan, por lo que
sus correcciones manuales sobreviven re-runs. Las escrituras son atómicas (archivo tmp + `os.replace`).

## Traducir documentos completos de Markdown

```bash
eli md README.md README.ja.md --target ja
```

Se conservan los bloques de código, el código en línea, las URL y las reglas de las tablas; sólo se traduce la prosa.
Los archivos README localizados en este repositorio se produjeron de esta manera.

## Uso de la biblioteca

```python
from eli.translate import Translator
from eli.asar import read_header, patch_entry

tr = Translator(target="ja", cache_path=".cache.json")
print(tr.translate("Settings saved successfully"))

header, header_str, size, base = read_header("/path/to/app.asar")
```

## Alcance y honestidad

- Desarrollado y probado en macOS. Los paquetes de Windows y Linux utilizan el mismo diseño asar y son
  compatible (ver Plataformas); el paso `Info.plist` simplemente no se aplica allí.
- Parchar un paquete firmado invalida su firma. En macOS se mantiene una aplicación ad-hoc/sin firmar
  laboral; una aplicación reforzada y certificada ante notario puede negarse a iniciarse. Pruebe y conserve la copia de seguridad.
- Esta es una herramienta para **tu propia máquina y tu propia copia** de una aplicación. respetar la licencia
  de lo que sea que estés traduciendo.

## Licencia

MIT
