# electron-live-i18n

> [English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Русский](README.ru.md)
>
> *Les traductions ci-dessous ont été produites par cet outil lui-même (`eli locales` / `eli tr`) et légèrement révisées. Les PR sont les bienvenus si une phrase se lit mal dans votre langue.*

Traduisez en direct **n'importe quelle application Electron packagée** — pas de reconstruction, pas de code source, pas de clé API.

La plupart des outils i18n supposent que vous possédez l'application et que vous pouvez modifier ses fichiers de paramètres régionaux. Celui-ci est pour
l'autre cas : une application Electron expédiée, signée et remplie de `app.asar` qui vous montre l'anglais
je ne sais pas lire, et vous le voulez juste dans votre langue *aujourd'hui*.

Cela fonctionne en écrivant un **~900 chargeur d'octets** dans une entrée existante à l'intérieur de `app.asar`
(rembourré à la taille d'origine exacte, hachages d'intégrité réécrits) et servant le contenu réel
couche de traduction à partir d’un petit serveur HTTP local. Après ce premier patch, tu ne touches plus
le bundle d'applications à nouveau - parcourez la couche de traduction et appuyez sur ⌘R.

```
app.asar ──(loader stub)──► http://127.0.0.1:7799/payload.js ──► DOM sweeper + dictionary
```

## Démo

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

Après le redémarrage, le texte anglais de l'interface utilisateur est remplacé tel qu'il apparaît, et chaque nouvelle chaîne
atterrit en `mydict.json` :

```console
$ cat mydict.json
{
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。",
  "Send a message to get started": "傳個訊息開始吧",
  "Settings saved successfully": "設定儲存成功"
}
```

Vous avez changé d'avis à propos d'une traduction ? Modifiez ce fichier et appuyez sur ⌘R dans l'application.

## Pourquoi ne pas simplement modifier les fichiers de paramètres régionaux ?

- De nombreuses applications Electron hard-code Anglais en JSX/TSX ; il n'y a aucun fichier de paramètres régionaux à modifier.
- L'application est déjà construite et signée ; reconstruire signifie mettre en place toute sa chaîne d’outils.
- Vous souhaitez continuer à traduire les **nouvelles** chaînes à mesure que l'application est mise à jour, et non la duper.

Si vous *avez* des fichiers JSON de paramètres régionaux, `eli locales` les traduit également.

## Installer

```bash
pip install electron-live-i18n     # or: pipx install electron-live-i18n
```

Python 3.9+, bibliothèque standard uniquement. Pas de dépendances, pas de clé API, pas de compte.

## Démarrage rapide

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

Annuler à tout moment :

```bash
eli revert "/Applications/Some App.app"
```

## Comment ça se traduit

1. Un `MutationObserver` parcourt les nœuds de texte et remplace tout ce qui est déjà dans le dictionnaire – un réseau instantané et nul.
2. Les chaînes inconnues qui semblent étrangères (≥8 lettres, <12 % target-script caractères) sont envoyées au serveur local.
3. Le serveur traduit via le point de terminaison public key-less `translate.googleapis.com`, met en cache le résultat sur le disque et l'ajoute à votre fichier de dictionnaire.

Le dictionnaire est donc un simple fichier JSON que vous pouvez hand-edit. La traduction automatique vous rapporte 95 %
du chemin en quelques secondes ; réparez les dix cordes gênantes à la main et elles restent fixes.

```json
{
  "Send a message to get started": "傳個訊息開始吧",
  "Manager will assign tasks to the right agents.": "主管會把任務分派給對的員工。"
}
```

## Laissez un agent IA le faire pour vous

Si vous utilisez un assistant capable d'exécuter des commandes et de modifier des fichiers sur votre machine - Claude Code,
Curseur, Codex CLI, Cline, Windsurf, Copilot CLI — collez ceci et il gérera l'ensemble
flux, y compris la sélection de l’entrée à corriger :

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

Remplacez `<APP PATH>` (par exemple `/Applications/Slack.app`, `C:\Users\me\AppData\Local\Slack`),
`<LANGUAGE>` et `<LANG CODE>` (`zh-TW`, `zh-CN`, `ja`, `ko`, `es`, `fr`, `de`, `pt`, `ru`, ...).

Ou connectez-le en tant que serveur MCP (voir ci-dessous) et dites simplement
*"traduire l'interface utilisateur de cette application en japonais"*.

## Choisir une entrée à patcher

`eli inspect` répertorie les entrées front-end par taille. Choisissez-en un qui est :

- **assez grand** — le chargeur fait environ 900 octets et est complété jusqu'à la taille de l'emplacement,
- **chargé par le moteur de rendu** — vérifiez que `index.html` y fait référence,
- **non-critical** — les offres groupées de télémétrie/analyse sont idéales ; le contenu original est remplacé.

Si vous souhaitez conserver le code original, hébergez-le depuis votre propre serveur et ajoutez-le au
charge utile avec `eli serve --extra-js original.js`. C'est à cela que sert l'indirection du chargeur.

## Plateformes

| Système d'exploitation | Disposition du bundle qu'il recherche | Correction de l'intégrité |
| --- | --- | --- |
| macOS | `Foo.app/Contents/Resources/app.asar` | hachage d'en-tête d'archive **et** `ElectronAsarIntegrity` dans `Info.plist` |
| Fenêtres | `Foo\resources\app.asar`, plus `Foo\app-1.2.3\resources\app.asar` de l'écureuil | hachage d'en-tête d'archive |
| Linux | `/opt/Foo/resources/app.asar` | hachage d'en-tête d'archive |

Vous pouvez toujours transmettre le chemin `app.asar` directement au lieu du dossier du bundle.

Notes Windows : exécutez le shell en tant qu'utilisateur propriétaire du répertoire d'installation (per-user installe
en dessous de `%LOCALAPPDATA%`, aucune élévation n’est nécessaire ; `Program Files` fait). Création d'applications basées sur les écureuils
un nouveau dossier `app-<version>` lors de la mise à jour, donc re-run `eli patch` après une mise à niveau — le
le dictionnaire et le serveur local sont intacts.

## Gotchas, ce projet est déjà résolu

- **CSP** — Le `script-src 'self' blob:` par défaut d'Electron bloque `eval()`. Le chargeur exécute à la place le code récupéré via une URL `Blob`.
- **Intégrité Asar** — Les bundles macOS contiennent `ElectronAsarIntegrity` dans `Info.plist`, plus un per-file SHA256 dans l'en-tête de l'archive. Les deux sont réécrits et, comme les hachages sont fixed-length hex, la taille de l'en-tête ne change jamais, donc chaque décalage de fichier reste valide.
- **Troncation silencieuse** : le point de terminaison de traduction gratuite coupe silencieusement les entrées longues. Le texte est divisé selon les limites des paragraphes/phrases et recousu.
- **Boucles d'auto-traduction** — passez les sélecteurs `--skip` pour votre propre interface utilisateur injectée afin qu'elle ne se traduise pas.

## Utilisez-le depuis un agent IA (MCP)

`eli mcp` parle le protocole de contexte de modèle sur stdio, afin qu'un assistant puisse inspecter un
regroupez, corrigez-le, traduisez des chaînes ou des fichiers de paramètres régionaux et rétablissez-le, le tout sans que vous quittiez
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

Outils exposés : `inspect_app`, `patch_app`, `revert_app`, `translate_text`,
`translate_locale_file`.

Exemple de conversation :

> **Vous :** Le menu de cette application est en anglais, faites-en du chinois traditionnel.
> **Agent :** *(inspect_app → sélectionne un bundle de 7 Ko non-critical → patch_app → vous demande de redémarrer)*

## Fichiers de paramètres régionaux sur le disque

```bash
eli locales locales/en.json locales/zh-TW.json --target zh-TW
```

Seules les chaînes non traduites sont envoyées ; les traductions existantes dans le fichier de destination gagnent, donc
vos correctifs manuels survivent à re-runs. Les écritures sont atomiques (fichier tmp + `os.replace`).

## Traduire des documents Markdown entiers

```bash
eli md README.md README.ja.md --target ja
```

Les blocs de code, le code en ligne, les URL et les règles de table sont préservés ; seule la prose est traduite.
Les README localisés dans ce dépôt ont été produits de cette façon.

## Utilisation de la bibliothèque

```python
from eli.translate import Translator
from eli.asar import read_header, patch_entry

tr = Translator(target="ja", cache_path=".cache.json")
print(tr.translate("Settings saved successfully"))

header, header_str, size, base = read_header("/path/to/app.asar")
```

## Portée et honnêteté

- Développé et testé sur macOS. Les bundles Windows et Linux utilisent la même présentation asar et sont
  pris en charge (voir Plateformes); l'étape `Info.plist` ne s'applique tout simplement pas ici.
- Appliquer un correctif à un bundle signé invalide sa signature. Sur macOS, une application ad-hoc/non signée conserve
  fonctionnement; a hardened, notarized app may refuse to launch. Test, and keep the backup.
- Il s'agit d'un outil pour **votre propre machine et votre propre copie** d'une application. Respecter le permis
  de tout ce que vous traduisez.

## Licence

MIT
