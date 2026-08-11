# electron-live-i18n

> [English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)
>
> *As traduções abaixo foram produzidas pela própria ferramenta (`eli locales` / `eli tr`) e levemente revisadas. PRs são bem-vindos se uma frase estiver errada em seu idioma.*

Traduza ao vivo **qualquer aplicativo Electron empacotado** — sem reconstrução, sem código-fonte, sem chave de API.

A maioria das ferramentas i18n pressupõe que você possui o aplicativo e pode editar seus arquivos de localidade. Este é para
o outro caso: um aplicativo Electron enviado, assinado e embalado com `app.asar` que mostra em inglês você
não consegue ler, e você só quer isso em seu idioma *hoje*.

Funciona escrevendo um carregador de **~900 bytes** em uma entrada existente dentro de `app.asar`
(preenchido no tamanho original exato, hashes de integridade reescritos) e servindo o real
camada de tradução de um pequeno servidor HTTP local. Depois daquele primeiro patch você nunca mais toca
o pacote de aplicativos novamente – itere na camada de tradução e pressione ⌘R.

```
app.asar ──(loader stub)──► http://127.0.0.1:7799/payload.js ──► DOM sweeper + dictionary
```

## Demonstração

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

Após a reinicialização, o texto da IU em inglês é substituído conforme aparece e cada nova string
pousa em `mydict.json`:

```console
$ cat mydict.json
{
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。",
  "Send a message to get started": "傳個訊息開始吧",
  "Settings saved successfully": "設定儲存成功"
}
```

Mudou de ideia sobre uma tradução? Edite esse arquivo e pressione ⌘R no aplicativo.

## Por que não apenas editar os arquivos de localidade?

- Muitos aplicativos Electron hard-code Inglês em JSX/TSX; não há arquivo de localidade para editar.
- O aplicativo já está construído e assinado; reconstruir significa configurar todo o seu conjunto de ferramentas.
- Você deseja continuar traduzindo **novas** strings à medida que o aplicativo é atualizado, e não bifurcá-lo.

Se você *tem* arquivos JSON de localidade, `eli locales` os traduz também.

## Instalar

```bash
pip install electron-live-i18n     # or: pipx install electron-live-i18n
```

Python 3.9+, apenas biblioteca padrão. Sem dependências, sem chave de API, sem conta.

## Início rápido

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

Desfazer a qualquer momento:

```bash
eli revert "/Applications/Some App.app"
```

## Como isso se traduz

1. Um `MutationObserver` percorre os nós de texto e substitui qualquer coisa que já esteja no dicionário - rede instantânea e zero.
2. Sequências desconhecidas que parecem estrangeiras (≥8 letras, <12% target-script caracteres) são enviadas ao servidor local.
3. O servidor traduz por meio do endpoint público key-less `translate.googleapis.com`, armazena em cache o resultado no disco e o anexa ao seu arquivo de dicionário.

Portanto, o dicionário é um arquivo JSON simples que você pode hand-edit. A tradução automática oferece 95%
do caminho em segundos; conserte as dez cordas estranhas com a mão e elas permanecerão fixas.

```json
{
  "Send a message to get started": "傳個訊息開始吧",
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。"
}
```

## Deixe um agente de IA fazer isso por você

Se você usa um assistente que pode executar comandos e editar arquivos em sua máquina – Claude Code,
Cursor, Codex CLI, Cline, Windsurf, Copilot CLI – cole isto e ele cuidará de tudo
fluxo, incluindo a escolha da entrada para corrigir:

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

Substitua `<APP PATH>` (por exemplo, `/Applications/Slack.app`, `C:\Users\me\AppData\Local\Slack`),
`<LANGUAGE>` e `<LANG CODE>` (`zh-TW`, `zh-CN`, `ja`, `ko`, `es`, `fr`, `de`, `pt`, `ru`, ...).

Ou conecte-o como um servidor MCP (veja abaixo) e apenas diga
*"traduzir a UI deste aplicativo para o japonês"*.

## Escolhendo uma entrada para corrigir

`eli inspect` lista front-end entradas por tamanho. Escolha um que seja:

- **grande o suficiente** — o carregador tem aproximadamente 900 bytes e é preenchido até o tamanho do slot,
- **carregado pelo renderizador** — verifique se `index.html` faz referência a ele,
- **non-critical** — pacotes de telemetria/análise são ideais; o conteúdo original é substituído.

Se você quiser manter o código original, hospede-o em seu próprio servidor e anexe-o ao
carga útil com `eli serve --extra-js original.js`. É para isso que serve a indireção do carregador.

## Plataformas

| SO | Layout do pacote que procura | Correção de integridade |
| --- | --- | --- |
| macOS | `Foo.app/Contents/Resources/app.asar` | hash de cabeçalho de arquivo **e** `ElectronAsarIntegrity` em `Info.plist` |
| Janelas | `Foo\resources\app.asar`, mais `Foo\app-1.2.3\resources\app.asar` do esquilo | hash de cabeçalho de arquivo |
| Linux | `/opt/Foo/resources/app.asar` | hash de cabeçalho de arquivo |

Você sempre pode passar o caminho `app.asar` diretamente em vez da pasta do pacote configurável.

Notas do Windows: execute o shell como o usuário que possui o diretório de instalação (per-user instala
abaixo de `%LOCALAPPDATA%` não precisa de elevação; `Program Files` faz). Aplicativos baseados em esquilo criam
uma nova pasta `app-<version>` na atualização, então re-run `eli patch` após uma atualização — o
o dicionário e o servidor local permanecem intactos.

## Peguei esse projeto já resolvido

- **CSP** — O padrão `script-src 'self' blob:` do Electron bloqueia `eval()`. O carregador executa o código obtido por meio de uma URL `Blob`.
- **Integridade Asar** — os pacotes macOS carregam `ElectronAsarIntegrity` em `Info.plist`, mais um per-file SHA256 dentro do cabeçalho do arquivo. Ambos são reescritos e, como os hashes são fixed-length hexadecimais, o tamanho do cabeçalho nunca muda, portanto, cada deslocamento de arquivo permanece válido.
- **Truncamento silencioso** — o endpoint de tradução livre corta silenciosamente entradas longas. O texto é dividido nos limites do parágrafo/frase e costurado novamente.
- **Loops de autotradução** — passe seletores `--skip` para sua própria UI injetada para que ela não se traduza.

## Use-o de um agente de IA (MCP)

`eli mcp` fala o Protocolo de Contexto do Modelo por stdio, para que um assistente possa inspecionar um
agrupar, corrigir, traduzir strings ou arquivos de localidade e reverter - tudo sem você sair
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

Ferramentas expostas: `inspect_app`, `patch_app`, `revert_app`, `translate_text`,
`translate_locale_file`.

Exemplo de conversa:

> **Você:** O menu deste aplicativo está em inglês, torne-o em chinês tradicional.
> **Agente:** *(inspect_app → escolhe um pacote de 7 KB non-critical → patch_app → diz para você reiniciar)*

## Arquivos de localidade no disco

```bash
eli locales locales/en.json locales/zh-TW.json --target zh-TW
```

Somente strings não traduzidas são enviadas; as traduções existentes no arquivo de destino vencem, então
suas correções manuais sobrevivem a re-runs. As gravações são atômicas (arquivo tmp + `os.replace`).

## Traduzindo documentos inteiros do Markdown

```bash
eli md README.md README.ja.md --target ja
```

Blocos de código, código embutido, URLs e regras de tabela são preservados; apenas a prosa é traduzida.
Os READMEs localizados neste repositório foram produzidos desta forma.

## Uso da biblioteca

```python
from eli.translate import Translator
from eli.asar import read_header, patch_entry

tr = Translator(target="ja", cache_path=".cache.json")
print(tr.translate("Settings saved successfully"))

header, header_str, size, base = read_header("/path/to/app.asar")
```

## Escopo e honestidade

- Desenvolvido e testado em macOS. Os pacotes Windows e Linux usam o mesmo layout asar e são
  suportado (ver Plataformas); a etapa `Info.plist` simplesmente não se aplica aqui.
- A correção de um pacote assinado invalida sua assinatura. No macOS, um aplicativo ad-hoc/não assinado mantém
  trabalhando; um aplicativo robusto e autenticado pode se recusar a iniciar. Teste e mantenha o backup.
- Esta é uma ferramenta para **sua própria máquina e sua própria cópia** de um aplicativo. Respeite a licença
  de tudo o que você está traduzindo.

## Licença

MIT
