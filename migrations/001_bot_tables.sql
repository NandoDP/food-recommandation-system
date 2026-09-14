-- ============================================================================
-- Architecture v2 — tables de support du bot orchestré par n8n
-- ARCHITECTURE_V2.md §6.1 et §7
--
-- Idempotent : ré-exécutable sans effet de bord.
-- Application :
--   docker compose exec -T db psql -U nutrisenegal -d nutrisenegal_db \
--     < migrations/001_bot_tables.sql
--
-- Note de schéma : dans ce projet, l'identifiant Telegram EST `users.id`
-- (TEXT) — voir api/routes/users.py, le bot enregistre str(effective_user.id).
-- `bot_sessions.telegram_id` référence donc `users.id`, mais sans clé
-- étrangère : une session existe dès le premier message, avant l'inscription.
-- ============================================================================

-- État conversationnel, remplace le ConversationHandler python-telegram-bot
CREATE TABLE IF NOT EXISTS bot_sessions (
    telegram_id   TEXT PRIMARY KEY,
    chat_id       BIGINT,                        -- pour réémettre un message hors requête
    state         TEXT NOT NULL DEFAULT 'IDLE',  -- IDLE, ASK_LANGUAGE, ASK_NAME, ...
    draft         JSONB NOT NULL DEFAULT '{}',   -- données d'onboarding en cours
    history       JSONB NOT NULL DEFAULT '[]',   -- derniers tours {role, text, lang}
    last_lang     TEXT,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Déduplication des updates Telegram : le webhook peut rejouer un update
-- non acquitté, et un doublon relancerait l'analyse (et sa facturation LLM).
CREATE TABLE IF NOT EXISTS bot_processed_updates (
    update_id     BIGINT PRIMARY KEY,
    received_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Purge : garder cette table petite, l'historique n'a pas de valeur au-delà
-- de quelques jours.
--   DELETE FROM bot_processed_updates WHERE received_at < NOW() - INTERVAL '7 days';
CREATE INDEX IF NOT EXISTS idx_bot_processed_updates_received_at
    ON bot_processed_updates (received_at);

-- Journal des erreurs de workflow (Error Trigger de WF1, §5.5)
CREATE TABLE IF NOT EXISTS bot_errors (
    id            BIGSERIAL PRIMARY KEY,
    occurred_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    workflow      TEXT,
    node          TEXT,
    message       TEXT,
    execution_url TEXT,
    payload       JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_bot_errors_occurred_at
    ON bot_errors (occurred_at DESC);
