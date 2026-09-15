-- ============================================================================
-- Architecture v2 — le wolof devient une langue d'interface
-- ARCHITECTURE_V2.md §6.1
--
-- WF6 pose la première question en trilingue (fr / wo / en) : sans cette
-- migration, choisir le wolof fait échouer POST /api/users/register sur la
-- contrainte users_language_check.
--
-- Idempotent.
--   docker compose exec -T db psql -U nutrisenegal -d nutrisenegal_db \
--     < migrations/002_users_language_wolof.sql
-- ============================================================================

ALTER TABLE users DROP CONSTRAINT IF EXISTS users_language_check;
ALTER TABLE users ADD CONSTRAINT users_language_check
    CHECK (language IN ('fr', 'wo', 'en'));
