# Diagramme Entité-Relations

Ce fichier contient le diagramme Entité-Relations (ER) généré à partir de `script.sql`.

- Fichier source analysé : `script.sql`

## Diagramme (Mermaid)

Collez le bloc ci-dessous dans un visualiseur Mermaid (VS Code extension "Markdown Preview Mermaid Support" ou la prévisualisation GitHub si prise en charge) pour voir le diagramme.

```mermaid
erDiagram
    USERS {
        UUID id PK
        TEXT last_name
        TEXT first_name
        TEXT phone
        DATE birth_date
        TEXT gender
        BIGINT weight
        BIGINT height
        TIMESTAMP registration_date
        TEXT language
    }
    DISEASES {
        UUID id PK
        TEXT name
        TEXT description
        TEXT severity_level
        TEXT general_recommendations
    }

    ALLERGENS {
        UUID id PK
        TEXT name
        TEXT category
        TEXT danger_level
    }

    HEALTH_PROFILES {
        UUID id PK
        UUID user_id FK
        TEXT intolerances
        TEXT physical_activity_level
    }

        HEALTH_PROFILE_DISEASES {
            UUID health_profile_id FK
            UUID disease_id FK
        }

        HEALTH_PROFILE_ALLERGENS {
            UUID health_profile_id FK
            UUID allergen_id FK
        }

    FOODS {
        UUID id PK
        TEXT local_name
        TEXT scientific_name
        TEXT category
        JSONB nutritional_values
        INTEGER glycemic_index
        INTEGER sodium_content
        INTEGER potassium_content
        TEXT origin
    }

    INGREDIENTS {
        UUID id PK
        TEXT name
        UUID food_id FK
        TEXT[] allergens_contained
    }

    DISHES {
        UUID id PK
        TEXT name
        TEXT description
        TEXT meal_type
        TEXT cuisine_origin
    }

    DISH_INGREDIENTS {
        UUID dish_id FK
        UUID ingredient_id FK
        FLOAT quantity
        TEXT unit
    }

    %% Relations
    USERS ||--o{ HEALTH_PROFILES : "has"
    FOODS ||--o{ INGREDIENTS : "is_source_for"
    DISHES ||--o{ DISH_INGREDIENTS : "contains"
    INGREDIENTS ||--o{ DISH_INGREDIENTS : "used_in"

    %% Explicitly show that health_profiles stores arrays of IDs referencing diseases and allergens
        %% Explicitly show new association tables for many-to-many relations
        HEALTH_PROFILES ||--o{ HEALTH_PROFILE_DISEASES : "has"
        DISEASES ||--o{ HEALTH_PROFILE_DISEASES : "referenced_by"
        HEALTH_PROFILES ||--o{ HEALTH_PROFILE_ALLERGENS : "has"
        ALLERGENS ||--o{ HEALTH_PROFILE_ALLERGENS : "referenced_by"

        INGREDIENTS ||--o{ INGREDIENT_ALLERGENS : "has"
        ALLERGENS ||--o{ INGREDIENT_ALLERGENS : "referenced_by"

    %% Notes: `chronic_diseases_ids` and `allergies_ids` are arrays of UUIDs referencing `diseases(id)` and `allergens(id)` respectively.

``` 

## Observations / Remarques

- `health_profiles.user_id` référence `users(id)` avec `ON DELETE CASCADE` : chaque profil appartient à un utilisateur (relation un-à-plusieurs possible selon la conception).
- `dish_ingredients` est une table d'association (many-to-many) entre `dishes` et `ingredients` (clé primaire composite `dish_id, ingredient_id`).
- `ingredients.food_id` référence `foods(id)` avec `ON DELETE SET NULL`.
- Les colonnes `chronic_diseases` et `allergies` dans `health_profiles` sont des tableaux de texte (référence indirecte aux tables `diseases` et `allergens` — aucun FK explicite dans le SQL fourni).