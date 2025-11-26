CREATE OR REPLACE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    last_name TEXT NOT NULL, 
    first_name TEXT NOT NULL, 
    email TEXT UNIQUE,
    hashed_password TEXT NOT NULL,
    birth_date DATE, 
    gender TEXT NOT NULL, 
    weight bigint, 
    height bigint,
    registration_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    language TEXT NOT NULL DEFAULT 'fr' CHECK (language IN ('en', 'fr'))
);

CREATE OR REPLACE TABLE diseases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    severity_level TEXT CHECK (severity_level IN ('low', 'medium', 'high')),
    general_recommendations TEXT
);

CREATE OR REPLACE TABLE allergens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    category TEXT,
    danger_level TEXT CHECK (danger_level IN ('low', 'medium', 'high'))
);

CREATE OR REPLACE TABLE health_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    intolerances TEXT,
    physical_activity_level TEXT CHECK (physical_activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active'))
);

CREATE OR REPLACE TABLE foods (
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

CREATE OR REPLACE TABLE ingredients (
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

CREATE OR REPLACE TABLE dishes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    meal_type TEXT CHECK (meal_type IN ('breakfast', 'lunch', 'dinner')),
    cuisine_origin TEXT
);

CREATE OR REPLACE TABLE dish_ingredients (
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

-- ============ TABLE DISEASES ============

-- Diabète Type 2
INSERT INTO diseases (id, name, description, severity_level, general_recommendations)
VALUES (
    uuid_generate_v4(),
    'Diabète Type 2',
    'Maladie métabolique caractérisée par une hyperglycémie chronique',
    'high',
    'Limiter glucides simples, privilégier IG bas (<55), portions contrôlées 45-60g glucides/repas, favoriser fibres (>5g/repas)'
);

-- Hypertension
INSERT INTO diseases (id, name, description, severity_level, general_recommendations)
VALUES (
    uuid_generate_v4(),
    'Hypertension artérielle',
    'Pression artérielle élevée chronique',
    'medium',
    'Limiter sodium <2000mg/jour, éviter sel de table, privilégier potassium, réduire graisses saturées'
);

-- Maladie hépatique
INSERT INTO diseases (id, name, description, severity_level, general_recommendations)
VALUES (
    uuid_generate_v4(),
    'Maladie hépatique chronique',
    'Atteinte du foie (cirrhose, stéatose, hépatite)',
    'high',
    'Limiter sodium <2000mg/jour, protéines modérées selon stade, éviter alcool, limiter graisses saturées'
);

-- Cancer (en traitement)
INSERT INTO diseases (id, name, description, severity_level, general_recommendations)
VALUES (
    uuid_generate_v4(),
    'Cancer (en traitement)',
    'Pathologie oncologique sous traitement actif',
    'high',
    'Besoins caloriques augmentés (+500kcal/jour), protéines 1.2-1.5g/kg, éviter ultra-transformés, privilégier anti-inflammatoires'
);

-- Insuffisance rénale
INSERT INTO diseases (id, name, description, severity_level, general_recommendations)
VALUES (
    uuid_generate_v4(),
    'Insuffisance rénale chronique',
    'Diminution progressive de la fonction rénale',
    'high',
    'Limiter sodium <2000mg/jour, limiter potassium <2000mg/jour, protéines contrôlées 0.8g/kg, limiter phosphore'
);


-- ============ TABLE ALLERGENS ============

-- Groupe 1 : Céréales à gluten
INSERT INTO allergens (id, name, category, danger_level)
VALUES 
    (uuid_generate_v4(), 'Gluten (blé)', 'cereals', 'high'),
    (uuid_generate_v4(), 'Gluten (seigle)', 'cereals', 'high'),
    (uuid_generate_v4(), 'Gluten (orge)', 'cereals', 'high'),
    (uuid_generate_v4(), 'Gluten (avoine)', 'cereals', 'medium');

-- Groupe 2 : Crustacés et mollusques
INSERT INTO allergens (id, name, category, danger_level)
VALUES 
    (uuid_generate_v4(), 'Crustacés', 'seafood', 'high'),
    (uuid_generate_v4(), 'Mollusques', 'seafood', 'high');

-- Groupe 3 : Œufs
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Œufs', 'eggs', 'high');

-- Groupe 4 : Poissons
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Poissons', 'fish', 'medium');

-- Groupe 5 : Arachides
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Arachides', 'nuts', 'high');

-- Groupe 6 : Soja
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Soja', 'legumes', 'medium');

-- Groupe 7 : Lait/Lactose
INSERT INTO allergens (id, name, category, danger_level)
VALUES 
    (uuid_generate_v4(), 'Lait (lactose)', 'dairy', 'medium'),
    (uuid_generate_v4(), 'Protéines de lait', 'dairy', 'high');

-- Groupe 8 : Fruits à coque
INSERT INTO allergens (id, name, category, danger_level)
VALUES 
    (uuid_generate_v4(), 'Amandes', 'nuts', 'high'),
    (uuid_generate_v4(), 'Noisettes', 'nuts', 'high'),
    (uuid_generate_v4(), 'Noix', 'nuts', 'high'),
    (uuid_generate_v4(), 'Noix de cajou', 'nuts', 'high'),
    (uuid_generate_v4(), 'Pistaches', 'nuts', 'high');

-- Groupe 9 : Céleri
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Céleri', 'vegetables', 'low');

-- Groupe 10 : Moutarde
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Moutarde', 'condiments', 'low');

-- Groupe 11 : Graines de sésame
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Sésame', 'seeds', 'medium');

-- Groupe 12 : Sulfites
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Sulfites (>10mg/kg)', 'additives', 'medium');

-- Groupe 13 : Lupin
INSERT INTO allergens (id, name, category, danger_level)
VALUES (uuid_generate_v4(), 'Lupin', 'legumes', 'low');


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