-- Base dédiée à n8n (workflows, credentials chiffrés, historique d'exécution).
-- Elle est séparée de `nutrisenegal_db` : n8n gère son propre schéma par
-- migrations, il ne doit pas cohabiter avec les tables métier.
--
-- Ce fichier est monté dans /docker-entrypoint-initdb.d/ et n'est donc exécuté
-- QUE lors de la toute première initialisation du volume postgres_data.
-- Sur une base déjà existante, créer la base à la main :
--   docker compose exec db psql -U nutrisenegal -d nutrisenegal_db \
--     -c "CREATE DATABASE n8n OWNER nutrisenegal;"
CREATE DATABASE n8n OWNER nutrisenegal;
