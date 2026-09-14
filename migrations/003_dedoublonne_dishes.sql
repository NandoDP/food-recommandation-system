-- ============================================================================
-- Déduplication de la table dishes
--
-- L'extraction WAFCT a été rejouée sans garde-fou : 201 plats pour 100 noms
-- distincts, chaque plat étant présent 2 à 6 fois. Les recommandations
-- proposaient donc le même plat plusieurs fois.
--
-- Les exemplaires d'un même nom se sont révélés identiques en substance : même
-- description, même composition, seules quelques méthodes diffèrent par des
-- broutilles de texte. On garde le plus complet et on reporte ses liaisons.
--
-- Idempotent : rejouer ne supprime rien de plus.
--   docker compose exec -T db psql -v ON_ERROR_STOP=1 -U nutrisenegal \
--     -d nutrisenegal_db < migrations/003_dedoublonne_dishes.sql
-- ============================================================================

BEGIN;

\echo 'Avant :'
SELECT COUNT(*) AS plats, COUNT(DISTINCT name) AS noms_distincts,
       (SELECT COUNT(*) FROM dish_ingredients) AS liaisons
FROM dishes;

-- 1. Élire un exemplaire par nom : le mieux garni, puis le plus documenté,
--    puis le plus petit identifiant pour que le choix soit déterministe.
CREATE TEMP TABLE classement ON COMMIT DROP AS
SELECT d.id,
       d.name,
       (SELECT COUNT(*) FROM dish_ingredients di WHERE di.dish_id = d.id) AS nb_ingredients,
       length(COALESCE(d.description, '')) + length(COALESCE(d.method, '')) AS richesse
FROM dishes d;

CREATE TEMP TABLE gardes ON COMMIT DROP AS
SELECT DISTINCT ON (name) name, id AS garde_id
FROM classement
ORDER BY name, nb_ingredients DESC, richesse DESC, id;

-- 2. Reporter sur l'exemplaire gardé les ingrédients que lui seul n'aurait pas.
INSERT INTO dish_ingredients (dish_id, ingredient_id, quantity, unit)
SELECT g.garde_id, di.ingredient_id, di.quantity, di.unit
FROM dish_ingredients di
JOIN dishes d ON d.id = di.dish_id
JOIN gardes g ON g.name = d.name
WHERE di.dish_id <> g.garde_id
ON CONFLICT (dish_id, ingredient_id) DO NOTHING;

-- 3. Supprimer les doublons ; leurs liaisons partent en cascade.
DELETE FROM dishes d
USING gardes g
WHERE d.name = g.name AND d.id <> g.garde_id;

-- 4. Empêcher la récidive : un nom, un plat.
CREATE UNIQUE INDEX IF NOT EXISTS idx_dishes_name ON dishes (name);

\echo 'Après :'
SELECT COUNT(*) AS plats, COUNT(DISTINCT name) AS noms_distincts,
       (SELECT COUNT(*) FROM dish_ingredients) AS liaisons
FROM dishes;

\echo 'Plats sans aucun ingrédient (doivent rester rares) :'
SELECT COUNT(*) FROM dishes d
WHERE NOT EXISTS (SELECT 1 FROM dish_ingredients di WHERE di.dish_id = d.id);

COMMIT;
