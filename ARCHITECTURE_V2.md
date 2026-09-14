# Architecture v2 — NutriSénégal : orchestration n8n, voix et wolof via Gemini

> Proposition de refonte, rédigée le 14 septembre 2026. Elle part de l'état
> actuel du dépôt (FastAPI + PostgreSQL + bot Telegram Python) et décrit la
> cible, les workflows n8n, les changements minimaux côté API, et un plan de
> migration par phases. Les identifiants de modèles Gemini cités ont été
> vérifiés sur la documentation officielle à la date de rédaction. Les quatre
> arbitrages laissés ouverts ont été tranchés le même jour : ils sont récapitulés
> au §11 et déjà intégrés dans les sections ci-dessous.

---

## 1. Objectifs

1. **Sortir la logique conversationnelle du code Python** : le bot Telegram
   (`telegram_bot/`, ~1 000 lignes de handlers, claviers et formatage) devient
   un ensemble de workflows n8n éditables sans redéploiement.
2. **Ajouter la voix** : l'utilisateur peut envoyer un message vocal et
   recevoir une réponse audio.
3. **Ajouter le wolof** : compréhension (texte et voix) et réponse (texte, puis
   voix) en wolof, en plus du français.
4. **Ne pas toucher au cœur métier** : le moteur de règles nutritionnelles
   reste déterministe, en Python, testé. Le LLM reformule, il ne calcule pas.

---

## 2. Ce qui reste, ce qui part, ce qui arrive

| Composant actuel | Décision | Remplacé par / remarque |
|---|---|---|
| PostgreSQL (11 tables, `script.sql`) | **Conservé** | Ajout de colonnes de traduction et d'une table de session bot |
| `api/core/nutrition_engine.py`, `nutrition_calculator.py` | **Conservé** | Source de vérité pour scores, alertes, alternatives |
| `api/routes/analyze.py`, `health_profiles.py`, `users.py` | **Conservé** | Ajout d'un endpoint d'analyse par ingrédients structurés et d'une clé API interne |
| `api/core/menu_parser.py` (spaCy + rapidfuzz) | **Rétrogradé en fallback** | Extraction d'ingrédients par Gemini (sortie JSON contrainte), spaCy sert de repli hors ligne et de validation des noms |
| `telegram_bot/bot.py`, `action_handles.py` | **Supprimé** | Workflows n8n `telegram-ingress`, `onboarding`, `profile` |
| `telegram_bot/services/health_api.py` | **Supprimé** | Nœuds HTTP Request n8n vers FastAPI |
| `telegram_bot/services/formatters.py` | **Supprimé** | Gemini génère le message final dans la langue de l'utilisateur, à partir du JSON de l'API |
| `telegram_bot/services/keyboads.py` | **Supprimé** | Claviers inline construits dans un nœud Code n8n (les UUID codés en dur sont remplacés par un appel à `/api/health-profiles/diseases` et `/allergens`) |
| `ConversationHandler` (états d'onboarding) | **Supprimé** | Table `bot_sessions` en PostgreSQL, lue/écrite par n8n |
| `Dockerfile.bot`, service `bot` du compose | **Supprimé** | Service `n8n` |
| — | **Nouveau** | Couche voix : ASR (Gemini 3.5 Transcribe en fr/en, Gemini multimodal en wolof) et TTS Gemini 2.5 (fr/en uniquement) |
| — | **Nouveau** | Langue `wo` dans `users.language`, alias wolof des ingrédients et plats |

---

## 3. Architecture cible

```
┌──────────────────────────────────────────────────────────────────────────┐
│  TELEGRAM (webhook HTTPS)                                                │
│  texte · vocal (OGG/Opus) · callback_query                               │
└───────────────────────────────┬──────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  n8n — ORCHESTRATION CONVERSATIONNELLE                                   │
│                                                                          │
│  WF1 telegram-ingress ─┬─ voix ──▶ WF2 speech-asr ──┐                    │
│                        ├─ texte ─────────────────────┼─▶ WF3 nlu-router  │
│                        └─ callback ──▶ WF6/WF7 (onboarding, profil)      │
│                                                      │                   │
│  WF3 : Gemini LLM (JSON strict) → intent + ingrédients + langue           │
│        → HTTP Request vers FastAPI                                        │
│                                                      ▼                   │
│  WF4 reply-composer : Gemini reformule le JSON API dans la langue        │
│        → Telegram sendMessage (+ clavier inline)                          │
│        → si entrée vocale ou préférence audio : WF5 speech-tts           │
│                                                                          │
│  Sous-workflows fournisseurs (interchangeables) :                        │
│    WF2 speech-asr  : fr/en → gemini-3.5-transcribe                       │
│                      wo    → Gemini multimodal (Chirp 3 en secours)      │
│    WF5 speech-tts  : fr/en → gemini-2.5-flash-preview-tts                │
│                      wo    → texte wolof + audio français (§4.3)         │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │ HTTP + X-API-Key
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  FASTAPI — MOTEUR MÉTIER (inchangé dans son cœur)                        │
│  /analyze-dish · /analyze-ingredients (nouveau) · /recommendations       │
│  /alternatives · /health-profiles · /users                               │
│  nutrition_engine (règles) · nutrition_calculator · menu_parser (repli)  │
└───────────────────────────────┬──────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  POSTGRESQL                                                              │
│  tables existantes + bot_sessions + traductions (JSONB) + aliases wolof  │
└──────────────────────────────────────────────────────────────────────────┘
```

Principe de séparation : **n8n orchestre, Gemini comprend et reformule,
FastAPI décide.** Aucun score, aucune alerte, aucune alternative ne sort du
LLM. Il reçoit le JSON de l'API et le met en mots.

---

## 4. Stratégie langue et voix : ce que Gemini fait vraiment

### 4.1 Modèles disponibles (vérifié le 14/09/2026)

| Rôle | Modèle | Statut | Point d'attention wolof |
|---|---|---|---|
| ASR fichier fr/en | `gemini-3.5-transcribe` | GA (août 2026), 85+ langues, jusqu'à 1 h par requête | **Le wolof n'est pas dans la liste officielle** |
| ASR streaming | `gemini-3.5-transcribe-live` | GA | Inutile ici : Telegram envoie des fichiers, pas un flux |
| **ASR wolof — retenu** | `gemini-3.8-flash` (ou `gemini-2.5-flash`) via `generateContent`, audio en entrée | GA | Compréhension audio générique : OGG/Opus accepté, 32 tokens par seconde d'audio, 20 Mo en inline. Wolof en « meilleur effort », **non documenté** |
| ASR wolof — porte de sortie | Google Cloud Speech-to-Text `chirp_3`, `wo-SN` (région `eu`) | GA | Seule option Google qui liste explicitement le wolof. Branche construite mais désactivée, activée si la phase 0 échoue |
| ASR wolof — autre piste | ElevenLabs Scribe | GA | Wolof listé, mais WER annoncé de 40,7 % sur FLEURS (qualité « modérée ») |
| TTS | `gemini-2.5-flash-preview-tts`, `gemini-2.5-pro-preview-tts`, `gemini-3.1-flash-tts-preview` | Preview, 80+ langues, 30 voix, sortie PCM 16 bits 24 kHz mono | **Le wolof n'est pas dans la liste officielle** ; la langue est auto-détectée |
| TTS wolof open source | `galsenai/xTTS-v2-wolof` (Hugging Face) | Communautaire | 7 Go, GPU recommandé, pauses aléatoires, gère mal les chiffres et le code-mixing |
| LLM | `gemini-3.8-flash` (GA sept. 2026) ; `gemini-2.5-flash` en alternative stable | GA | Compréhension du wolof écrit correcte mais à évaluer sur le vocabulaire culinaire |

Conséquence directe : la demande initiale « ASR Gemini 3.5, TTS Gemini 2.5,
LLM Gemini » fonctionne telle quelle pour le **français** et l'**anglais**.
Pour le **wolof**, il faut soit accepter un mode « meilleur effort » non
documenté, soit brancher un fournisseur qui le supporte officiellement.

**Arbitrage retenu** : on tente d'abord Gemini multimodal sur le wolof
(décision 1), avec un seuil chiffré en phase 0 pour décider de basculer ou non
vers Chirp 3. Côté restitution, pas de synthèse vocale wolof : le texte est en
wolof, l'audio en français, et on l'annonce à l'utilisateur (décision 2). Le
design ci-dessous garde ces deux choix réversibles.

### 4.2 Pipeline de compréhension (entrée)

```
audio Telegram
   │
   ├─ langue du profil connue (users.language) ?
   │     fr / en ─▶ gemini-3.5-transcribe ─▶ texte
   │     wo      ─▶ gemini-3.8-flash (audio en entrée)      ◀ décision 1
   │                prompt : « Transcris fidèlement en wolof, puis donne
   │                la traduction française. Réponds en JSON. »
   │                └─ si phase 0 sous le seuil ─▶ bascule Chirp 3 wo-SN
   │                   (branche du Switch, construite et désactivée)
   │
   └─ langue inconnue (premier contact) ─▶ gemini-3.8-flash (audio)
         prompt : détecte la langue parmi {fr, wo, en}, transcris, traduis
                                    │
                                    ▼
                          WF3 nlu-router (texte)
   Gemini LLM, sortie JSON contrainte :
   {
     "language": "wo" | "fr" | "en",
     "intent": "analyze_dish" | "recommend" | "alternatives" |
               "dish_details" | "update_profile" | "help" | "other",
     "dish_name": "ceebu jën",
     "ingredients": [{"name_fr": "riz", "name_raw": "ceeb", "quantity": null}],
     "meal_type": "lunch" | null,
     "confidence": 0.0-1.0
   }
```

Règles :

- Le LLM **normalise toujours vers le français** (`name_fr`) car la base de
  données et le moteur de règles sont en français. Les alias wolof stockés en
  base (`ingredients.aliases`) servent de liste fermée fournie dans le prompt
  pour ancrer la normalisation.
- Si `confidence < 0.6` ou si un ingrédient normalisé n'existe pas en base,
  n8n appelle `/api/analyze-menu` (spaCy + rapidfuzz) en repli, puis demande
  confirmation à l'utilisateur avec un clavier inline plutôt que de deviner.
- Température 0.2, `responseMimeType: application/json`, `responseSchema`
  fourni. Pas de texte libre à cette étape.

### 4.3 Pipeline de réponse (sortie)

```
JSON FastAPI (score, alert_level, alerts, recommendations, alternatives)
   │
   ▼
WF4 reply-composer — Gemini LLM
   system : « Tu es NutriSénégal. Tu reçois un résultat d'analyse calculé.
             Tu le restitues en {language} sans modifier aucun chiffre,
             aucun niveau d'alerte, aucun nom de plat. Tu n'ajoutes aucune
             recommandation médicale. Tu termines par le rappel : consulter
             un professionnel de santé. »
   → texte Markdown Telegram (fr ou wo)
   │
   ├─▶ Telegram sendMessage + clavier inline
   │
   └─▶ si message entrant vocal OU users.audio_reply = true
         ▼
       WF5 speech-tts
         fr / en ─▶ gemini-2.5-flash-preview-tts (voix « Kore » ou « Zephyr »)
                   PCM 24 kHz ─▶ conversion ─▶ OGG/Opus ─▶ sendVoice
         wo      ─▶ texte en WOLOF + audio en FRANÇAIS       ◀ décision 2
                   Gemini produit deux sorties : le message wolof envoyé en
                   texte, et sa version française envoyée au TTS. L'audio est
                   précédé de l'annonce ci-dessous.
                   Piste ultérieure, hors périmètre : microservice `wolof-tts`
                   (xTTS-v2-wolof) derrière la même interface qu'au §4.4.
```

**Annonce à l'utilisateur wolof.** Tant qu'il n'existe pas de synthèse vocale
en wolof, l'utilisateur doit comprendre pourquoi il lit du wolof et entend du
français. Message affiché une fois à l'activation de la réponse audio, puis
rappelé en une ligne au premier vocal de chaque session :

> 🔊 Baat bi ci farañse la, ndax masin bi mënagul wax wolof ba léegi.
> Bataaxal bi nekk na ci wolof.
> *(L'audio est en français : la synthèse vocale wolof n'est pas encore
> disponible. Le texte, lui, reste en wolof.)*

Ce libellé est un **gabarit fixe à faire relire par un locuteur**, pas une
génération du LLM (§7). Si l'utilisateur désactive `audio_reply`, l'annonce
disparaît avec l'audio.

Conversion audio : Telegram `sendVoice` exige de l'OGG/Opus. Le TTS Gemini
sort du PCM brut. Deux options :

1. Image n8n personnalisée avec `ffmpeg`, nœud Execute Command :
   `ffmpeg -f s16le -ar 24000 -ac 1 -i in.pcm -c:a libopus out.ogg`
   (recommandé, ~50 ms).
2. Nœud Code qui préfixe un en-tête WAV et envoie via `sendAudio` en
   document. Plus simple, mais rendu « fichier » et non « message vocal ».

### 4.4 Abstraction fournisseur

`speech-asr` et `speech-tts` sont des **sous-workflows** appelés par
Execute Workflow avec un contrat fixe :

```json
// entrée ASR                         // sortie ASR
{ "audio": <binary>, "lang_hint": "wo" }   { "text": "...", "lang": "wo", "provider": "chirp3", "confidence": 0.82 }

// entrée TTS                         // sortie TTS
{ "text": "...", "lang": "fr" }            { "audio": <binary ogg>, "provider": "gemini-2.5-flash-preview-tts" }
```

Changer de fournisseur wolof (Gemini → Chirp 3 → ElevenLabs → modèle local)
revient à modifier une branche d'un Switch dans un seul sous-workflow. Les
identifiants de modèles sont des **variables n8n** (`GEMINI_LLM_MODEL`,
`GEMINI_ASR_MODEL`, `GEMINI_TTS_MODEL`), jamais codés dans les nœuds, car
les modèles TTS sont en preview et seront renommés.

---

## 5. Workflows n8n, nœud par nœud

### WF1 `telegram-ingress` (point d'entrée unique)

1. **Telegram Trigger** (updates : `message`, `callback_query`). Webhook
   HTTPS obligatoire : `cloudflared` ou `ngrok` en dev, domaine + TLS en prod.
2. **Code : idempotence** — lit `update_id`, l'insère dans
   `bot_processed_updates` ; si déjà présent, stop (Telegram renvoie les
   updates non acquittés).
3. **Postgres : charger contexte** — `users` + `health_profiles` +
   `bot_sessions` par `telegram_id`. Si absent → WF6 onboarding.
4. **Switch : type d'update**
   - `message.voice` ou `message.audio` → Telegram Get File → WF2 → WF3
   - `message.text` → WF3
   - `callback_query` → Switch sur préfixe (`action_`, `dish_`, `alt_`,
     `disease_`, `allergen_`, `meal_`) → WF7 ou appel API direct → WF4
5. **Error Trigger** global → message d'excuse dans la langue de l'utilisateur
   + log dans `bot_errors`.

### WF2 `speech-asr` — voir §4.2

Nœuds : Switch langue → **Google Gemini node, ressource Audio, opération
Transcribe** (fr/en) | **Google Gemini node, Message a Model** avec l'audio en
`inlineData` et un `responseSchema`
`{transcript_wo, transcript_fr, confidence}` (wo) → Set sortie.

La branche Chirp 3 (HTTP Request vers Speech-to-Text v2 `recognize`,
`model: chirp_3`, `languageCodes: ["wo-SN"]`, endpoint régional `eu`) est
**construite mais désactivée** dans le Switch. Elle ne s'active que si la
phase 0 passe sous le seuil défini au §9.

### WF3 `nlu-router`

1. **Google Gemini node, Message a Model** avec `responseSchema` (§4.2) et
   le contexte : profil santé résumé, liste des alias wolof connus, 5 derniers
   échanges depuis `bot_sessions.history`.
2. **Switch intent** :
   - `analyze_dish` → `POST /api/analyze-ingredients` (nouveau, §6) ou
     `POST /api/analyze-dish` si `dish_name` correspond à un plat en base
     (`GET /api/dishes?search=`)
   - `recommend` → `GET /api/recommendations/{user_id}?meal_type=`
   - `alternatives` → `POST /api/alternatives/{dish_id}`
   - `dish_details` → `GET /api/{dish_id}/dish_details`
   - `update_profile` → WF7
   - `help` / `other` → WF4 avec texte d'aide statique traduit
3. **Postgres : mettre à jour `bot_sessions`** (historique court, intent,
   dernière langue détectée ; si la langue détectée diffère de
   `users.language` trois fois de suite, proposer de changer la préférence).

### WF4 `reply-composer` — voir §4.3

### WF5 `speech-tts` — voir §4.3

### WF6 `onboarding` (remplace le `ConversationHandler`)

Machine à états stockée dans `bot_sessions.state` :
`ASK_LANGUAGE → ASK_NAME → ASK_WEIGHT → ASK_DISEASES → ASK_ALLERGENS → DONE`.
Première question posée en trilingue (fr / wo / en) avec trois boutons ; la
langue choisie fixe `users.language`. Les listes de maladies et d'allergènes
viennent de `/api/health-profiles/diseases` et `/allergens` (fin des UUID
codés en dur dans `keyboads.py`). Chaque étape accepte texte **ou** vocal :
un message vocal passe par WF2 puis par un petit prompt Gemini d'extraction
(« extrais un poids en kg », « extrais des noms de maladies parmi cette
liste »). À `DONE` : `POST /api/users/register` puis
`POST /api/health-profiles/` + `list_diseases` + `list_allergens`.

### WF7 `profile-management`

Toggles maladies / allergènes (mêmes endpoints qu'aujourd'hui), changement de
langue, activation de la réponse audio (`users.audio_reply`), suppression du
profil.

---

## 6. Changements côté FastAPI et base de données

Volontairement minimaux.

### 6.1 Schéma

```sql
-- langue
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_language_check;
ALTER TABLE users ADD CONSTRAINT users_language_check
  CHECK (language IN ('fr', 'wo', 'en'));
ALTER TABLE users ADD COLUMN IF NOT EXISTS audio_reply BOOLEAN NOT NULL DEFAULT false;

-- alias multilingues (déjà anticipé par WestAfricanMenuParser._get_aliases)
ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS aliases JSONB DEFAULT '[]';
ALTER TABLE dishes      ADD COLUMN IF NOT EXISTS translations JSONB DEFAULT '{}';
ALTER TABLE diseases    ADD COLUMN IF NOT EXISTS translations JSONB DEFAULT '{}';
ALTER TABLE allergens   ADD COLUMN IF NOT EXISTS translations JSONB DEFAULT '{}';
-- ex. dishes.translations = {"wo": "Ceebu jën", "en": "Fish and rice"}

-- état conversationnel (remplace ConversationHandler)
CREATE TABLE IF NOT EXISTS bot_sessions (
  telegram_id   TEXT PRIMARY KEY,
  state         TEXT NOT NULL DEFAULT 'IDLE',
  draft         JSONB NOT NULL DEFAULT '{}',   -- données d'onboarding en cours
  history       JSONB NOT NULL DEFAULT '[]',   -- 5 derniers tours {role, text, lang}
  last_lang     TEXT,
  updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bot_processed_updates (
  update_id     BIGINT PRIMARY KEY,
  received_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Amorçage des alias wolof pour les ingrédients les plus fréquents : `ceeb`
(riz), `jën` (poisson), `yàpp` (viande), `ginaar` (poulet), `soble` (oignon),
`ñebbe` (haricot), `gerte` (arachide), `tamaate` (tomate), `diw` (huile),
`xorom` (sel), `suukar` (sucre), `meew` (lait), `mburu` (pain), `dugub`
(mil), `ñambi` (manioc), `batañse` (aubergine), `kaani` (piment). Cette liste
est à valider avec un locuteur : l'orthographe wolof varie fortement et le LLM
la rencontrera sous plusieurs formes.

### 6.2 Endpoints

| Endpoint | Changement |
|---|---|
| `POST /api/analyze-ingredients` | **Nouveau.** Reçoit `{"user_id", "ingredients": [{"name", "quantity", "unit"}], "dish_name"}` déjà normalisés par Gemini, appelle `nutrition_calculator` + `nutrition_engine` sans passer par spaCy. Factoriser le corps de `analyze_menu` pour que les deux routes partagent la même fonction interne |
| `POST /api/analyze-menu` | **Conservé durablement** (décision 4) : repli hors ligne quand l'API Gemini est indisponible ou quand la confiance NLU est basse. Reste couvert par `tests/test_menu_parser.py` |
| `GET /api/dishes` | Ajouter `?search=` avec correspondance sur `name` et `translations` |
| `GET /api/health-profiles/diseases`, `/allergens` | Renvoyer `translations` pour que n8n construise les claviers dans la bonne langue |
| Tous | Middleware `X-API-Key` : l'API n'est plus appelée uniquement depuis le réseau Docker interne par un bot maison mais depuis n8n ; la clé est une variable d'environnement partagée. Le `TrustedHostMiddleware(allowed_hosts=["*"])` de `api/main.py` est à restreindre à `api` et `localhost` |

### 6.3 Ce qui ne bouge pas

`nutrition_engine.py`, `nutrition_calculator.py`, la pondération 40/35/25,
l'exclusion des allergènes des alternatives (couverte par
`tests/test_alternatives_filter.py`). Les tests existants restent valides.

---

## 7. Garde-fous santé et qualité

- **Ancrage strict** : le prompt de WF4 reçoit le JSON de l'API et la
  consigne de ne rien recalculer. Un nœud Code vérifie après génération que
  le score numérique et le niveau d'alerte présents dans le texte
  correspondent au JSON (regex) ; sinon on renvoie un gabarit fixe traduit.
- **Pas de conseil médical inventé** : `recommendations` viennent de
  `_generate_personalized_tips` et consorts, pas du LLM. Rappel systématique
  de consulter un professionnel, dans les trois langues.
- **Confirmation avant analyse** quand la confiance NLU est basse ou que
  l'entrée est vocale en wolof (WER élevé attendu) : « J'ai compris : riz,
  poisson, huile. C'est bien ça ? » avec boutons Oui / Corriger.
- **Jeu de test wolof** : 30 phrases écrites + 30 clips audio (locuteurs
  variés, bruit de fond de marché) versionnés dans `tests/wolof/`. Mesurer WER
  (ASR) et exactitude d'intention + d'ingrédients (NLU) à chaque changement de
  modèle. C'est ce jeu qui tranche entre Chirp 3, Gemini multimodal et
  ElevenLabs, pas la documentation marketing.
- **Journalisation** : chaque tour (langue, provider ASR, texte transcrit,
  JSON NLU, endpoint appelé, latence) dans une table `bot_turns` pour analyse
  dans les notebooks existants.
- **Données personnelles** : les audios sont supprimés après transcription
  (pas de persistance du binaire) ; seul le texte est conservé.

---

## 8. Déploiement cible

```yaml
# docker-compose.yml (extrait cible)
services:
  db:      # inchangé (+ migrations §6.1 dans script.sql)
  api:     # inchangé, + INTERNAL_API_KEY, + TrustedHost restreint
  n8n:
    build: { context: ., dockerfile: Dockerfile.n8n }   # n8nio/n8n:2.39.5 + ffmpeg
    environment:
      N8N_ENCRYPTION_KEY: ${N8N_ENCRYPTION_KEY}
      N8N_WEBHOOK_URL: ${PUBLIC_HTTPS_URL}   # Telegram exige HTTPS ; `WEBHOOK_URL` est déprécié depuis n8n 2.35
      N8N_BLOCK_ENV_ACCESS_IN_NODE: "false"  # autorise {{ $env.GEMINI_* }} dans les nœuds (§4.4)
      DB_TYPE: postgresdb                    # n8n stocke ses workflows dans le même Postgres (base séparée)
      DB_POSTGRESDB_HOST: db
      DB_POSTGRESDB_DATABASE: n8n
      GENERIC_TIMEZONE: Africa/Dakar
    ports: ["5678:5678"]
    volumes: ["n8n_data:/home/node/.n8n", "./n8n/workflows:/workflows"]
    depends_on: [db, api]
  # optionnel, phase 4 :
  # wolof-tts:  image GPU exposant POST /synthesize (xTTS-v2-wolof)
```

n8n est **auto-hébergé dans le compose** (décision 3) : pas d'abonnement, et
workflows comme identifiants restent sur ton infrastructure. En contrepartie,
le webhook Telegram doit être joignable en HTTPS depuis Internet —
`cloudflared` en développement, reverse proxy TLS en production.

Variables d'environnement nouvelles : `GEMINI_API_KEY`, `N8N_ENCRYPTION_KEY`,
`PUBLIC_HTTPS_URL`, `INTERNAL_API_KEY` (voir `n8n/README.md` pour la mise en
route du service et l'exposition du webhook). `GOOGLE_APPLICATION_CREDENTIALS`
n'est **pas** nécessaire au départ : la décision 1 retient Gemini multimodal
pour le wolof, donc une seule clé API suffit. Le service `bot` et
`Dockerfile.bot` disparaissent. Les workflows n8n sont exportés en JSON dans
`n8n/workflows/` et versionnés dans le dépôt.

---

## 9. Plan de migration

| Phase | Contenu | Critère de sortie |
|---|---|---|
| **0. Validation de Gemini sur le wolof** | Constituer `tests/wolof/` (30 clips audio + 30 phrases écrites). Mesurer **Gemini multimodal seul** : WER de transcription, et surtout exactitude d'extraction des ingrédients. Chirp 3 et ElevenLabs ne sont mesurés qu'en cas d'échec | **Go** si l'extraction d'ingrédients atteint 75 % sur les 30 clips. **No-go** → activer la branche Chirp 3 `wo-SN` et refaire la mesure |
| **1. n8n texte français** | Service n8n, WF1/WF3/WF4/WF6/WF7 avec un **second token de bot** de test. L'ancien bot Python reste en production. `POST /api/analyze-ingredients`, `bot_sessions`, `X-API-Key` | Parité fonctionnelle avec le bot Python sur les 7 actions du menu principal |
| **2. Voix français** | WF2 + WF5, image n8n avec ffmpeg, `audio_reply` | Aller-retour vocal fr < 8 s en médiane |
| **3. Wolof texte** | `language='wo'`, alias wolof, `translations`, onboarding trilingue, prompts WF3/WF4 en wolof, jeu de test écrit | Exactitude intention ≥ 90 % et ingrédients ≥ 85 % sur le jeu écrit |
| **4. Wolof voix** | Branche wo de WF2 (Gemini multimodal, ou Chirp 3 si la phase 0 l'a imposé) ; réponse = texte wolof + audio français avec l'annonce du §4.3 | Confirmation utilisateur **obligatoire** avant toute analyse issue d'un vocal wolof ; WER mesuré et publié dans le README |
| **5. Décommission** | Basculer le token principal sur n8n, supprimer `telegram_bot/`, `Dockerfile.bot`, mettre à jour README, CHANGELOG 2.0.0 | Aucun appel API en provenance de l'ancien bot pendant 7 jours |

Phases 1 et 0 sont indépendantes et peuvent être menées en parallèle.

---

## 10. Risques et coûts

- **Wolof non officiellement supporté par Gemini (ASR et TTS)**. C'est le
  risque principal du projet, et la décision 1 l'assume délibérément : on parie
  sur un comportement non documenté, donc susceptible de se dégrader sans
  préavis à chaque mise à jour de modèle. Trois mitigations : la branche
  Chirp 3 reste construite et testable (§4.4), la phase 0 fixe un seuil de
  bascule chiffré, et le jeu de test wolof est rejoué à chaque changement de
  modèle. Ne rien communiquer sur la voix wolof avant les chiffres de la
  phase 0.
- **Modèles TTS en preview** : identifiants susceptibles de changer. Variables
  n8n centralisées, jamais en dur.
- **Latence** : vocal → ASR → LLM → API → LLM → TTS → conversion. Compter
  5 à 10 s. Envoyer un accusé « 🎧 Je t'écoute… » dès la réception, puis
  éditer le message.
- **Coût** : audio facturé environ 32 tokens par seconde côté Gemini ; un
  vocal de 15 s et deux appels LLM courts restent dans l'ordre du centime.
  Chirp 3 et ElevenLabs sont facturés à la minute ou à l'heure d'audio.
  Le quota gratuit Gemini suffit pour le développement, pas pour un pilote
  avec plusieurs dizaines d'utilisateurs actifs.
- **Webhook HTTPS** : contrairement au polling actuel, n8n doit être
  joignable depuis Internet. En dev, tunnel ; en prod, reverse proxy TLS.
- **Dépendance à n8n** pour la logique métier conversationnelle : garder la
  logique nutritionnelle dans FastAPI (c'est le but) et exporter les workflows
  dans le dépôt à chaque changement.
- **Qualité du wolof généré par le LLM** : le wolof écrit de Gemini peut être
  francisé ou incohérent dans l'orthographe. Faire relire les gabarits fixes
  (aide, onboarding, disclaimer) par un locuteur et les stocker en dur plutôt
  que de les générer.

---

## 11. Décisions prises (14 septembre 2026)

| # | Question | Décision | Implication |
|---|---|---|---|
| 1 | Fournisseur ASR wolof | **Gemini multimodal** (`gemini-3.8-flash`, audio en entrée). Chirp 3 `wo-SN` gardé en porte de sortie | Une seule clé API au départ, pas de compte de service Google Cloud à créer. En contrepartie on dépend d'un comportement non documenté : la confirmation utilisateur devient obligatoire sur le vocal wolof, et la phase 0 fixe le seuil de bascule (§9) |
| 2 | Restitution vocale en wolof | **Texte en wolof, audio en français**, annoncé explicitement à l'utilisateur (§4.3) | Pas de GPU ni de microservice supplémentaire. L'annonce est un gabarit fixe à faire relire par un locuteur, pas une génération du LLM |
| 3 | Hébergement de n8n | **Auto-hébergé** dans `docker-compose.yml` | Coût nul et contrôle des données. Il faut exposer le webhook Telegram en HTTPS : `cloudflared` en développement, reverse proxy TLS en production |
| 4 | `/api/analyze-menu` (spaCy) | **Conservé durablement** comme repli hors ligne | Le parser spaCy et `tests/test_menu_parser.py` restent maintenus. Il prend le relais quand Gemini est indisponible ou quand la confiance NLU est basse |

Ces quatre choix sont réversibles par construction : les trois premiers se
concentrent dans les sous-workflows `speech-asr` et `speech-tts` (§4.4) et dans
le compose, le quatrième dans une route FastAPI isolée.

Points encore ouverts, à trancher au fil des phases plutôt que maintenant :

- la voix Gemini retenue pour le français (« Kore », ferme, ou « Zephyr ») ;
- la profondeur d'historique conservée dans `bot_sessions.history` (5 tours
  proposés, à ajuster selon le coût en tokens observé) ;
- le moment exact de décommissionner le bot Python (phase 5), qui dépend de la
  parité fonctionnelle constatée en phase 1.

---

## Sources vérifiées

- Modèles Gemini : https://ai.google.dev/gemini-api/docs/models
- Gemini 3.5 Transcribe : https://ai.google.dev/gemini-api/docs/models/gemini-3.5-transcribe
- Génération vocale Gemini (TTS) : https://ai.google.dev/gemini-api/docs/speech-generation
- Compréhension audio Gemini : https://ai.google.dev/gemini-api/docs/audio
- Journal des versions Gemini : https://ai.google.dev/gemini-api/docs/changelog
- Langues Cloud Speech-to-Text (Chirp 3, `wo-SN`) : https://docs.cloud.google.com/speech-to-text/docs/speech-to-text-supported-languages
- Nœud Google Gemini de n8n : https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-langchain.googlegemini/
- ElevenLabs Scribe wolof : https://elevenlabs.io/speech-to-text/wolof
- TTS wolof open source : https://huggingface.co/galsenai/xTTS-v2-wolof
