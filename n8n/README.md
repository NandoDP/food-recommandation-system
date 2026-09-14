# Service n8n — orchestration conversationnelle

Ce dossier contient tout ce qui accompagne le conteneur `n8n` défini dans
[`docker-compose.yml`](../docker-compose.yml) : le script de création de sa
base, et les workflows exportés et versionnés.

La cible, les workflows nœud par nœud et le plan de migration sont décrits dans
[`ARCHITECTURE_V2.md`](../ARCHITECTURE_V2.md) (§5, §8 et §9). Ce README ne
traite que de l'exploitation du service.

| Fichier | Rôle |
|---|---|
| [`../Dockerfile.n8n`](../Dockerfile.n8n) | Image n8n 2.39.5 + `ffmpeg` (conversion PCM → OGG/Opus pour `sendVoice`, phase 2) |
| [`init-n8n-db.sql`](init-n8n-db.sql) | Crée la base `n8n` dans le PostgreSQL du projet |
| `workflows/` | Workflows exportés en JSON, un fichier par workflow |

---

## 1. Premier démarrage

```bash
# 1. Renseigner les variables de la section N8N du .env
#    (voir .env.example : N8N_ENCRYPTION_KEY, INTERNAL_API_KEY, GEMINI_API_KEY…)
python -c "import secrets; print(secrets.token_urlsafe(32))"   # une clé par variable

# 2. Construire l'image (n8n + ffmpeg) et démarrer
docker compose build n8n
docker compose up -d db api n8n

# 3. Vérifier
docker compose ps n8n
curl -sf http://localhost:5678/healthz
```

L'éditeur est sur <http://localhost:5678>. Au premier accès, n8n demande de
créer le compte propriétaire : ces identifiants sont locaux à l'instance, ils
ne sont ni dans le dépôt ni dans le `.env`.

**Si le volume `postgres_data` existait déjà**, le script
`init-n8n-db.sql` n'a pas été exécuté (les scripts de
`/docker-entrypoint-initdb.d/` ne tournent que sur un volume neuf). Créer la
base à la main, sinon `n8n` redémarre en boucle :

```bash
docker compose exec db psql -U nutrisenegal -d nutrisenegal_db \
  -c "CREATE DATABASE n8n OWNER nutrisenegal;"
docker compose restart n8n
```

---

## 2. Exposer le webhook Telegram en HTTPS

Contrairement à l'ancien bot Python qui faisait du *long polling*, n8n reçoit
les updates par webhook : Telegram exige une URL **HTTPS publique**.

### En développement — cloudflared

```bash
cloudflared tunnel --url http://localhost:5678
# -> https://xxx-yyy-zzz.trycloudflare.com
```

Reporter cette URL dans `.env` puis recréer le conteneur (n8n construit l'URL
de webhook au démarrage, un `restart` ne suffit pas si la variable a changé) :

```bash
# .env
PUBLIC_HTTPS_URL=https://xxx-yyy-zzz.trycloudflare.com

docker compose up -d --force-recreate n8n
```

L'URL d'un tunnel gratuit change à chaque lancement : il faut refaire cette
étape, et réactiver le workflow `telegram-ingress` pour que n8n réenregistre
le webhook auprès de Telegram.

### En production

Reverse proxy TLS (nginx, Caddy, Traefik) devant `n8n:5678`, `PUBLIC_HTTPS_URL`
fixé au domaine, `N8N_PROXY_HOPS` égal au nombre de proxies traversés, et
`N8N_SECURE_COOKIE` remis à `true` dans le compose (il est à `false` pour
permettre la connexion en HTTP sur `localhost`).

### Vérifier l'enregistrement côté Telegram

```bash
curl -s "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

---

## 3. Credentials à créer dans l'éditeur

Les credentials sont chiffrés avec `N8N_ENCRYPTION_KEY` et stockés dans la base
`n8n` : ils ne sont **jamais** versionnés dans `workflows/`. À créer une fois
depuis l'interface :

| Credential | Type n8n | Valeur |
|---|---|---|
| `Telegram NutriSénégal (test)` | Telegram API | `TELEGRAM_TOKEN_N8N` — bot de test de la phase 1 |
| `Gemini NutriSénégal` | Google Gemini(PaLM) API | `GEMINI_API_KEY` |
| `Postgres NutriSénégal` | Postgres | hôte `db`, base `nutrisenegal_db`, user `nutrisenegal`, mot de passe `DB_PASSWORD` |

L'API FastAPI est appelée par des nœuds HTTP Request avec l'en-tête
`X-API-Key: {{ $env.INTERNAL_API_KEY }}` sur `{{ $env.INTERNAL_API_BASE_URL }}`
(soit `http://api:8000/api` depuis le réseau Docker) — pas de credential n8n
dédié.

> Le middleware qui **vérifie** cette clé côté FastAPI n'est pas encore écrit
> (ARCHITECTURE_V2.md §6.2) : l'en-tête est envoyé, il est ignoré pour l'instant.

---

## 4. Variables d'environnement lisibles dans les workflows

`N8N_BLOCK_ENV_ACCESS_IN_NODE=false` autorise `{{ $env.NOM }}` dans les nœuds.
Les identifiants de modèles ne sont donc jamais écrits en dur (les modèles TTS
sont en preview et seront renommés — ARCHITECTURE_V2.md §4.4) :

| Variable | Défaut | Usage |
|---|---|---|
| `INTERNAL_API_BASE_URL` | `http://api:8000/api` | Base des nœuds HTTP Request vers FastAPI |
| `INTERNAL_API_KEY` | — | En-tête `X-API-Key` |
| `GEMINI_API_KEY` | — | Credential Gemini (à recopier dans l'éditeur) |
| `GEMINI_LLM_MODEL` | `gemini-3.8-flash` | WF3 `nlu-router`, WF4 `reply-composer` |
| `GEMINI_ASR_MODEL` | `gemini-3.5-transcribe` | WF2 `speech-asr`, branches fr/en |
| `GEMINI_TTS_MODEL` | `gemini-2.5-flash-preview-tts` | WF5 `speech-tts` |
| `TELEGRAM_TOKEN_N8N` | — | Bot de test de la phase 1 |

Changer une de ces valeurs demande `docker compose up -d --force-recreate n8n`.

---

## 5. Versionner les workflows

Le dossier `workflows/` est monté sur `/workflows` dans le conteneur. Exporter
après chaque modification, et commiter :

```bash
# Export (un fichier JSON par workflow)
docker compose exec n8n n8n export:workflow --all --separate --output=/workflows

# Import (nouvelle machine, ou restauration)
docker compose exec n8n n8n import:workflow --separate --input=/workflows
```

Les workflows importés arrivent **désactivés** : les réactiver dans l'éditeur.
Un export contient les nœuds et leurs paramètres, mais seulement les
*références* aux credentials, pas leur contenu.

---

## 6. Dépannage

| Symptôme | Cause probable |
|---|---|
| `n8n` redémarre en boucle, log `database "n8n" does not exist` | Volume Postgres préexistant : créer la base à la main (§1) |
| Connexion à l'éditeur qui retombe sur l'écran de login | Cookie de session rejeté en HTTP : vérifier `N8N_SECURE_COOKIE=false` |
| Telegram ne déclenche rien | `PUBLIC_HTTPS_URL` périmée, ou workflow inactif : vérifier `getWebhookInfo` (§2) |
| `$env.X` vide dans un nœud | Variable absente du service `n8n` du compose, ou conteneur non recréé |
| Credentials illisibles après une remise à zéro | `N8N_ENCRYPTION_KEY` a changé : restaurer l'ancienne valeur ou recréer les credentials |
