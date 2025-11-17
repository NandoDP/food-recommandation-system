CREATE OR REPLACE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    last_name TEXT NOT NULL, 
    first_name TEXT NOT NULL, 
    phone TEXT UNIQUE,
    birth_date DATE, 
    gender TEXT NOT NULL, 
    weight bigint, 
    height bigint,
    registration_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    language TEXT NOT NULL DEFAULT 'fr' AS, CHECK (language IN ('en', 'fr'))
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
    chronic_diseases TEXT[],
    allergies TEXT[],
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
    food_id UUID REFERENCES foods(id) ON DELETE SET NULL,
    allergens_contained TEXT[]
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