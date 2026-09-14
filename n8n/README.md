# Service n8n — orchestration conversationnelle

Ce dossier contient tout ce qui accompagne le conteneur `n8n` défini dans
[`docker-compose.yml`](../docker-compose.yml) : le script de création de sa
base, et les workflows exportés et versionnés.

La cible, les workflows nœud par nœud et le plan de migration sont décrits dans
[`ARCHITECTURE_V2.md`](../ARCHITECTURE_V2.md) (§5, §8 et §9). Ce README ne
traite que de l'exploitation du service.

| Fichier | Rôle |
|---|---|
| [`../Dockerfile.n8n`](../Dockerfile.n8n) | Image n8n 2.39.5 + binaire `ffmpeg` statique (conversion PCM → OGG/Opus pour `sendVoice`, phase 2) |
| [`init-n8n-db.sql`](init-n8n-db.sql) | Crée la base `n8n` dans le PostgreSQL du projet |
| `workflows/` | Workflows exportés en JSON, un fichier par workflow |
| [`../migrations/001_bot_tables.sql`](../migrations/001_bot_tables.sql) | Tables `bot_sessions`, `bot_processed_updates`, `bot_errors` |
| [`../migrations/002_users_language_wolof.sql`](../migrations/002_users_language_wolof.sql) | Autorise `wo` dans `users.language` (onboarding trilingue) |

| Workflow | Fichier | État |
|---|---|---|
| WF1 `telegram-ingress` | [`workflows/wf1-telegram-ingress.json`](workflows/wf1-telegram-ingress.json) | Point d'entrée complet ; appelle WF6, branches texte/vocal/callback en attente de WF3/WF2/WF7 |
| WF6 `onboarding` | [`workflows/wf6-onboarding.json`](workflows/wf6-onboarding.json) | Création de profil de bout en bout |

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
depuis l'interface, **avant d'importer les workflows** : l'import rattache les
nœuds à un credential par son nom, et ne peut le faire que si celui-ci existe
déjà. Les noms ci-dessous sont donc à respecter à la lettre — sinon les nœuds
arrivent sans credential et la publication échoue sur
« *Credential not configured* ». Renommer le credential et réimporter suffit à
réparer.

| Credential | Type n8n | Valeur |
|---|---|---|
| `Telegram NutriSénégal (test)` | Telegram API | `TELEGRAM_TOKEN_N8N` — bot de test de la phase 1 |
| `Gemini NutriSénégal` | Google Gemini(PaLM) API | `GEMINI_API_KEY` |
| `Postgres NutriSénégal` | Postgres | hôte `db` (**pas** `localhost` : depuis le conteneur n8n, `localhost` désigne n8n), base `nutrisenegal_db`, user `nutrisenegal`, mot de passe `DB_PASSWORD`, SSL `disable` |

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

## 5. WF1 `telegram-ingress`

Point d'entrée unique du bot (ARCHITECTURE_V2.md §5). Il normalise l'update
Telegram, écarte les doublons, charge le profil et la session, puis route selon
le type d'entrée. Les workflows d'aval n'existant pas encore, **chaque branche
répond un message de diagnostic** : c'est ce qui rend WF1 testable seul.

```
Telegram Trigger
  └─ Normaliser l'update        (Code : enveloppe plate, le format Telegram s'arrête ici)
     └─ Marquer l'update        (Postgres : INSERT ... ON CONFLICT DO NOTHING)
        └─ Update déjà traité ? ─ non ─▶ Doublon ignoré
           └─ Charger le contexte   (crée/rafraîchit bot_sessions, puis users + health_profiles, 1 ligne garantie)
              └─ Utilisateur connu ? ─ non ─▶ [WF6 onboarding]
                 └─ Type d'entrée ─┬─ texte    ─▶ [WF3 nlu-router]
                                   ├─ vocal    ─▶ [WF2 speech-asr]
                                   ├─ callback ─▶ Accuser le callback ─▶ [WF7 profile]
                                   └─ non géré
                                      └──────────▶ Répondre  ([WF4 reply-composer])
```

L'enveloppe produite par le nœud `Normaliser l'update` est le contrat que tous
les workflows suivants consomment : `kind` (`text` / `voice` / `callback` /
`other`), `telegram_id`, `chat_id`, `message_id`, `text`, `file_id`,
`duration`, `callback_data`, `callback_prefix`, `callback_query_id`, puis
`user_id`, `language` et `session_state` après chargement du contexte.

> Dans ce projet, l'identifiant Telegram **est** `users.id` (TEXT) : le bot
> Python enregistre `str(update.effective_user.id)`. `bot_sessions.telegram_id`
> suit la même convention.

### Mise en route

```bash
# 1. Tables de support (idempotent)
docker compose exec -T db psql -U nutrisenegal -d nutrisenegal_db   < migrations/001_bot_tables.sql

# 2. Import du workflow
docker compose exec -T n8n n8n import:workflow --separate --input=/workflows/

# 3. Redémarrer pour que l'éditeur voie le workflow importé
docker compose restart n8n
```

> **Sous Git Bash (Windows)**, préfixer les commandes contenant un chemin
> absolu du conteneur par `MSYS_NO_PATHCONV=1` : sinon `/workflows/` est
> réécrit en `C:/Program Files/Git/workflows/` et l'import annonce
> tranquillement « 0 workflows ». PowerShell et Linux ne sont pas concernés.

Puis dans l'éditeur :

1. Ouvrir **WF1 telegram-ingress** et vérifier que les trois nœuds Postgres et
   les deux nœuds Telegram pointent bien sur les credentials créés au §3
   (l'import les rattache par nom, mais il faut le confirmer).
2. **Settings → Error Workflow → WF1 telegram-ingress** pour activer la branche
   `Error Trigger` (§5.5 de l'architecture).
3. Activer le workflow (bascule **Active**). C'est ce geste qui enregistre le
   webhook auprès de Telegram : sans `PUBLIC_HTTPS_URL` valide, il échoue.

### Recette

| Envoi au bot de test | Réponse attendue |
|---|---|
| Un texte quelconque | Accusé listant `user_id`, `langue`, `session`, et le texte reçu |
| Un message vocal | Accusé avec la durée et le `file_id`, mention de la phase 2 |
| Une photo ou un sticker | « Ce type de message n'est pas encore géré » |
| Depuis un compte sans profil | Message d'accueil renvoyant vers l'ancien bot |
| Le même `update_id` rejoué | Aucune réponse, exécution arrêtée sur `Doublon ignoré` |
| N'importe lequel des envois ci-dessus | Une ligne apparaît dans `bot_sessions` avec le `chat_id` |

```sql
-- Vérifications en base après quelques messages
SELECT * FROM bot_processed_updates ORDER BY received_at DESC LIMIT 5;
SELECT telegram_id, chat_id, state, updated_at FROM bot_sessions;
SELECT occurred_at, node, message FROM bot_errors ORDER BY occurred_at DESC LIMIT 5;
```

Le nœud *Charger le contexte* crée la session au passage (`INSERT ... ON
CONFLICT DO UPDATE` dans une CTE) : `bot_sessions` est donc alimentée dès le
premier message, avant même l'inscription de l'utilisateur, ce dont WF6
onboarding aura besoin.

> **Prérequis** : la table `users` doit exister. `script.sql` la déclare avec
> `CREATE OR REPLACE TABLE`, syntaxe que PostgreSQL refuse — si la base a été
> initialisée uniquement par ce script, le nœud *Charger le contexte* échouera
> sur `relation "users" does not exist`.

---

## 6. WF6 `onboarding`

Remplace le `ConversationHandler` du bot Python. Appelé par WF1 dès qu'un
message arrive d'un compte sans profil, il mène la conversation jusqu'à la
création du profil santé :

```
IDLE → ASK_LANGUAGE → ASK_NAME → ASK_WEIGHT → ASK_DISEASES → ASK_ALLERGENS → DONE
```

L'état ne vit pas en mémoire mais dans `bot_sessions.state` et `.draft` : n8n
peut redémarrer au milieu d'un onboarding sans que l'utilisateur perde sa
progression. Les listes de maladies et d'allergènes sont lues sur
`/api/health-profiles/diseases` et `/allergens` — les UUID codés en dur de
`keyboads.py` disparaissent.

Trois choix de construction :

- **Toute la décision tient dans un nœud Code**, `Machine à états` : fonction
  pure, elle ne lit ni n'écrit rien, elle renvoie l'état suivant, le brouillon
  et le message Telegram à émettre. Les nœuds qui suivent exécutent. C'est ce
  qui rend l'enchaînement rejouable hors n8n et testable sans Telegram.
- **Les appels Telegram passent par des nœuds HTTP Request**, pas par le nœud
  Telegram : les claviers sont construits à partir des listes de l'API, et le
  nœud Telegram ne sait pas produire un clavier dynamique. Le token vient de
  `$env.TELEGRAM_TOKEN_N8N`.
- **Les deux nœuds de référentiel sont en « Execute Once »** : un nœud n8n
  s'exécute une fois **par item reçu**. Sans ce réglage, le nœud des allergènes
  reçoit les 5 maladies du nœud précédent, appelle l'API 5 fois et renvoie 110
  allergènes — le clavier dépasse alors la limite de ~10 ko de `reply_markup`
  et Telegram répond `Bad Request: reply markup is too long`.
- **La finalisation tolère le rejeu** : `register` et la création du profil
  acceptent un 400 « existe déjà », l'identifiant de profil est relu plutôt que
  déduit de la réponse de création, et `list_diseases` / `list_allergens`
  remplacent la sélection entière. Un utilisateur qui relance `/start` puis
  retermine ne crée pas de doublon.

> Le token apparaît dans l'URL des appels, donc dans les données d'exécution
> conservées par n8n. C'est acceptable pour le bot de test ; à revoir avant
> d'utiliser le token de production.

### Mise en route

```bash
# La langue wolof doit être acceptée par la base, sinon le choix « Wolof »
# fait échouer POST /api/users/register
docker compose exec -T db psql -U nutrisenegal -d nutrisenegal_db   < migrations/002_users_language_wolof.sql

docker compose exec -T n8n n8n import:workflow --separate --input=/workflows/
docker compose restart n8n
```

WF6 est un sous-workflow : **il n'a pas à être activé**, WF1 l'appelle. En
revanche l'import **désactive** les workflows importés, WF1 compris — il faut
le republier et redémarrer, sinon le webhook Telegram n'est plus enregistré :

```bash
docker compose exec -T n8n n8n publish:workflow --id=wf1-telegram-ingress
docker compose restart n8n
curl -s "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

### Recette

| Envoi au bot de test, depuis un compte sans profil | Réponse attendue |
|---|---|
| `/start` | Message d'accueil et trois boutons de langue |
| Bouton « Français » | Le message est **édité** (pas de nouveau message) et demande le nom |
| Un prénom, ou le bouton « Utiliser … » | Demande le poids |
| `abc` puis `800` | Deux refus, la question du poids reste posée |
| `72,4` | Clavier des 5 maladies, avec « Aucune » et « Valider » |
| Cocher / décocher | Le clavier se met à jour, la case bascule |
| Valider | Clavier des 22 allergènes (24 boutons, ~2,3 ko) |
| Terminer | Récapitulatif, et le profil existe en base |

```sql
SELECT state, draft FROM bot_sessions WHERE telegram_id = '<ton id>';
SELECT id, first_name, weight, language FROM users;
SELECT hp.id, array_agg(d.name) FROM health_profiles hp
  LEFT JOIN health_profile_diseases hpd ON hpd.health_profile_id = hp.id
  LEFT JOIN diseases d ON d.id = hpd.disease_id GROUP BY hp.id;
```

Une fois le profil créé, `is_known_user` devient vrai dans WF1 : les messages
suivants ne passent plus par WF6 mais par le routage texte / vocal / callback.

---

## 7. Versionner les workflows

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

## 8. Dépannage

| Symptôme | Cause probable |
|---|---|
| `n8n` redémarre en boucle, log `database "n8n" does not exist` | Volume Postgres préexistant : créer la base à la main (§1) |
| Connexion à l'éditeur qui retombe sur l'écran de login | Cookie de session rejeté en HTTP : vérifier `N8N_SECURE_COOKIE=false` |
| Telegram ne déclenche rien | `PUBLIC_HTTPS_URL` périmée, ou workflow inactif : vérifier `getWebhookInfo` (§2) |
| `$env.X` vide dans un nœud | Variable absente du service `n8n` du compose, ou conteneur non recréé |
| Credentials illisibles après une remise à zéro | `N8N_ENCRYPTION_KEY` a changé : restaurer l'ancienne valeur ou recréer les credentials |
| WF1 : `relation "bot_processed_updates" does not exist` | Migration `001_bot_tables.sql` non appliquée (§5) |
| `Importing 0 workflows` | Chemin réécrit par Git Bash : voir l'encadré du §5 |
| `Postgres <version> is not supported` au démarrage | n8n 2.x demande PostgreSQL 16 ou plus ; le compose est en 17 |
| `password authentication failed for user "nutrisenegal"` | `DB_PASSWORD` a été modifié dans `.env` **après** la création du volume : `POSTGRES_PASSWORD` n'agit qu'à l'initialisation, le rôle garde l'ancien mot de passe. Réaligner sans perdre les données : `docker compose exec -T db psql -U nutrisenegal -d nutrisenegal_db -c "ALTER USER nutrisenegal WITH PASSWORD '<nouveau>';"` puis `docker compose up -d --force-recreate db api n8n` |
| `Credential not configured` à la publication | Workflow importé avant la création des credentials : créer ceux du §3 avec les noms exacts, puis réimporter |
| Le bot ne répond plus après un import | L'import désactive les workflows : republier WF1 et redémarrer n8n (§6) |
| WF6 : `violates check constraint "users_language_check"` | Migration `002_users_language_wolof.sql` non appliquée |
| `Bad Request: reply markup is too long` | Un clavier dépasse ~10 ko. Vérifier que les nœuds de référentiel sont bien en **Execute Once** : sinon ils tournent une fois par item reçu et multiplient les listes |
| Un nœud renvoie N fois trop de données | Même cause : en n8n un nœud s'exécute une fois par item d'entrée. `Execute Once` dans les réglages du nœud |
| WF1 : le bouton Telegram tourne indéfiniment | Le nœud *Accuser le callback* n'a pas été exécuté : vérifier la branche `callback` du Switch |
