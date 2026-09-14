-- ============================================
-- Schéma NutriSénégal — PostgreSQL
--
-- Rejouable : tables créées si absentes, données de référence insérées
-- si absentes. Appliqué automatiquement à la première initialisation du
-- volume Postgres (docker-entrypoint-initdb.d), ou à la main :
--   docker compose exec -T db psql -U nutrisenegal -d nutrisenegal_db < script.sql
-- ============================================

-- uuid_generate_v4() n'existe pas sans cette extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    -- id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id TEXT PRIMARY KEY,
    last_name TEXT NOT NULL, 
    first_name TEXT NOT NULL, 
    -- email TEXT UNIQUE,
    -- hashed_password TEXT NOT NULL,
    birth_date DATE, 
    gender TEXT, 
    weight bigint, 
    height bigint,
    registration_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    language TEXT NOT NULL DEFAULT 'fr' CHECK (language IN ('en', 'fr'))
);

CREATE TABLE IF NOT EXISTS diseases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    severity_level TEXT CHECK (severity_level IN ('low', 'medium', 'high')),
    general_recommendations TEXT
);

CREATE TABLE IF NOT EXISTS allergens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    category TEXT,
    danger_level TEXT CHECK (danger_level IN ('low', 'medium', 'high'))
);

CREATE TABLE IF NOT EXISTS health_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    intolerances TEXT,
    physical_activity_level TEXT CHECK (physical_activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active'))
);

CREATE TABLE IF NOT EXISTS foods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    local_name TEXT NOT NULL,
    scientific_name TEXT,
    category TEXT,
    nutritional_values JSONB,
    glycemic_index INTEGER,
    sodium_content INTEGER,
    potassium_content INTEGER,
    origin TEXT
);

CREATE TABLE IF NOT EXISTS ingredients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    food_id UUID REFERENCES foods(id) ON DELETE SET NULL
);

-- Association table linking health_profiles to diseases (many-to-many)
CREATE TABLE IF NOT EXISTS health_profile_diseases (
    health_profile_id UUID REFERENCES health_profiles(id) ON DELETE CASCADE,
    disease_id UUID REFERENCES diseases(id) ON DELETE CASCADE,
    PRIMARY KEY (health_profile_id, disease_id)
);

-- Association table linking health_profiles to allergens (many-to-many)
CREATE TABLE IF NOT EXISTS health_profile_allergens (
    health_profile_id UUID REFERENCES health_profiles(id) ON DELETE CASCADE,
    allergen_id UUID REFERENCES allergens(id) ON DELETE CASCADE,
    PRIMARY KEY (health_profile_id, allergen_id)
);

-- Association table linking ingredients to allergens (many-to-many)
CREATE TABLE IF NOT EXISTS ingredient_allergens (
    ingredient_id UUID REFERENCES ingredients(id) ON DELETE CASCADE,
    allergen_id UUID REFERENCES allergens(id) ON DELETE CASCADE,
    PRIMARY KEY (ingredient_id, allergen_id)
);

CREATE TABLE IF NOT EXISTS dishes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    method TEXT,
    meal_type TEXT CHECK (meal_type IN ('breakfast', 'lunch', 'dinner')),
    cuisine_origin TEXT
);

CREATE TABLE IF NOT EXISTS dish_ingredients (
    dish_id UUID REFERENCES dishes(id) ON DELETE CASCADE,
    ingredient_id UUID REFERENCES ingredients(id) ON DELETE CASCADE,
    quantity FLOAT,
    unit TEXT,
    PRIMARY KEY (dish_id, ingredient_id)
);






-- ============================================
-- PEUPLEMENT MALADIES ET ALLERGÈNES
-- Inclut règles métier de base
-- ============================================

-- Unicité supposée par les modèles (api/schemas/users.py) et requise par
-- les ON CONFLICT ci-dessous
CREATE UNIQUE INDEX IF NOT EXISTS idx_diseases_name  ON diseases (name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_allergens_name ON allergens (name);

-- ============ TABLE DISEASES ============

-- Diabète Type 2
INSERT INTO diseases (id, name, description, severity_level, general_recommendations)
VALUES (
    uuid_generate_v4(),
    'Diabète Type 2',
    'Maladie métabolique caractérisée par une hyperglycémie chronique',
    'high',
    'Limiter glucides simples, privilégier IG bas (<55), portions contrôlées 45-60g glucides/repas, favoriser fibres (>5g/repas)'
)
ON CONFLICT (name) DO NOTHING;

-- Hypertension
INSERT INTO diseases (id, name, description, severity_level, general_recommendations)
VALUES (
    uuid_generate_v4(),
    'Hypertension artérielle',
    'Pression artérielle élevée chronique',
    'medium',
    'Limiter sodium <2000mg/jour, éviter sel de table, privilégier potassium, réduire graisses saturées'
)
ON CONFLICT (name) DO NOTHING;

-- Maladie hépatique
INSERT INTO diseases (id, name, description, severity_level, general_recommendations)
VALUES (
    uuid_generate_v4(),
    'Maladie hépatique chronique',
    'Atteinte du foie (cirrhose, stéatose, hépatite)',
    'high',
    'Limiter sodium <2000mg/jour, protéines modérées selon stade, éviter alcool, limiter graisses saturées'
)
ON CONFLICT (name) DO NOTHING;

-- Cancer (en traitement)
INSERT INTO diseases (id, name, description, severity_level, general_recommendations)
VALUES (
    uuid_generate_v4(),
    'Cancer (en traitement)',
    'Pathologie oncologique sous traitement actif',
    'high',
    'Besoins caloriques augmentés (+500kcal/jour), protéines 1.2-1.5g/kg, éviter ultra-transformés, privilégier anti-inflammatoires'
)
ON CONFLICT (name) DO NOTHING;

-- Insuffisance rénale
INSERT INTO diseases (id, name, description, severity_level, general_recommendations)
VALUES (
    uuid_generate_v4(),
    'Insuffisance rénale chronique',
    'Diminution progressive de la fonction rénale',
    'high',
    'Limiter sodium <2000mg/jour, limiter potassium <2000mg/jour, protéines contrôlées 0.8g/kg, limiter phosphore'
)
ON CONFLICT (name) DO NOTHING;


-- ============ TABLE ALLERGENS ============

-- Groupe 1 : Céréales à gluten
INSERT INTO allergens (id, name, category, danger_level)
VALUES 
    (uuid_generate_v4(), 'Gluten (blé)', 'cereals', 'high'),
    (uuid_generate_v4(), 'Gluten (seigle)', 'cereals', 'high'),
    (uuid_generate_v4(), 'Gluten (orge)', 'cereals', 'high'),
    (uuid_generate_v4(), 'Gluten (avoine)', 'cereals', 'medium')
ON CONFLICT (name) DO NOTHING;

-- Groupe 2 : Crustacés et mollusques
INSERT INTO allergens (id, name, category, danger_level)
VALUES 
    (uuid_generate_v4(), 'Crustacés', 'seafood', 'high'),
    (uuid_generate_v4(), 'Mollusques', 'seafood', 'high')
ON CONFLICT (name) DO NOTHING;

-- Groupe 3 : Œufs
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Œufs', 'eggs', 'high')
ON CONFLICT (name) DO NOTHING;

-- Groupe 4 : Poissons
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Poissons', 'fish', 'medium')
ON CONFLICT (name) DO NOTHING;

-- Groupe 5 : Arachides
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Arachides', 'nuts', 'high')
ON CONFLICT (name) DO NOTHING;

-- Groupe 6 : Soja
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Soja', 'legumes', 'medium')
ON CONFLICT (name) DO NOTHING;

-- Groupe 7 : Lait/Lactose
INSERT INTO allergens (id, name, category, danger_level)
VALUES 
    (uuid_generate_v4(), 'Lait (lactose)', 'dairy', 'medium'),
    (uuid_generate_v4(), 'Protéines de lait', 'dairy', 'high')
ON CONFLICT (name) DO NOTHING;

-- Groupe 8 : Fruits à coque
INSERT INTO allergens (id, name, category, danger_level)
VALUES 
    (uuid_generate_v4(), 'Amandes', 'nuts', 'high'),
    (uuid_generate_v4(), 'Noisettes', 'nuts', 'high'),
    (uuid_generate_v4(), 'Noix', 'nuts', 'high'),
    (uuid_generate_v4(), 'Noix de cajou', 'nuts', 'high'),
    (uuid_generate_v4(), 'Pistaches', 'nuts', 'high')
ON CONFLICT (name) DO NOTHING;

-- Groupe 9 : Céleri
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Céleri', 'vegetables', 'low')
ON CONFLICT (name) DO NOTHING;

-- Groupe 10 : Moutarde
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Moutarde', 'condiments', 'low')
ON CONFLICT (name) DO NOTHING;

-- Groupe 11 : Graines de sésame
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Sésame', 'seeds', 'medium')
ON CONFLICT (name) DO NOTHING;

-- Groupe 12 : Sulfites
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Sulfites (>10mg/kg)', 'additives', 'medium')
ON CONFLICT (name) DO NOTHING;

-- Groupe 13 : Lupin
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Lupin', 'legumes', 'low')
ON CONFLICT (name) DO NOTHING;


-- ============ ALLERGIES CROISÉES (documentation) ============
-- Note : À implémenter via une table dédiée si nécessaire

/*
ALLERGIES CROISÉES PRINCIPALES :
1. Latex → Banane, Avocat, Kiwi, Châtaigne
2. Bouleau (pollen) → Pomme, Poire, Cerise, Noisette
3. Arachide → Lupin, Soja, Pois
4. Lait de vache → Lait de chèvre, Bœuf
5. Œuf de poule → Viande de poulet
6. Crustacés → Mollusques, Acariens
*/


-- ============ VÉRIFICATION ============
SELECT 'Diseases count:' as info, COUNT(*) as count FROM diseases
UNION ALL
SELECT 'Allergens count:', COUNT(*) FROM allergens;