# Dictionnaire de données

Ce document décrit les tables et les colonnes définies dans `script.sql`.

---

## Table `users`
- **id**: `UUID` — Clé primaire, `DEFAULT uuid_generate_v4()`, NON NULL.
- **last_name**: `TEXT` — Nom de famille, `NOT NULL`.
- **first_name**: `TEXT` — Prénom, `NOT NULL`.
- **phone**: `TEXT` — Numéro de téléphone, UNIQUE, peut être NULL si non renseigné.
- **birth_date**: `DATE` — Date de naissance, NULLABLE.
- **gender**: `TEXT` — Genre, `NOT NULL` (valeurs attendues non contraintes dans le SQL fourni mais idéalement `CHECK` ou enum).
- **weight**: `BIGINT` — Poids (unité à préciser, ex. grammes ou kg), NULLABLE.
- **height**: `BIGINT` — Taille (unité à préciser, ex. cm), NULLABLE.
- **registration_date**: `TIMESTAMP` — Date d'enregistrement, `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP`.
- **language**: `TEXT` — Langue préférée, `NOT NULL`, `DEFAULT 'fr'`, contrainte CHECK attendue `IN ('en','fr')`.

Remarques: la définition SQL fournie contenait une petite anomalie syntaxique (`AS, CHECK`). Le sens attendu est une contrainte de valeur pour `language`.

---

## Table `diseases`
- **id**: `UUID` — Clé primaire, `DEFAULT uuid_generate_v4()`.
- **name**: `TEXT` — Nom de la maladie, `NOT NULL`.
- **description**: `TEXT` — Description libre, NULLABLE.
- **severity_level**: `TEXT` — Niveau de sévérité, `CHECK (severity_level IN ('low','medium','high'))`, NULLABLE.
- **general_recommendations**: `TEXT` — Recommandations générales, NULLABLE.

---

## Table `allergens`
- **id**: `UUID` — Clé primaire, `DEFAULT uuid_generate_v4()`.
- **name**: `TEXT` — Nom de l'allergène, `NOT NULL`.
- **category**: `TEXT` — Catégorie (ex. "nut", "dairy"), NULLABLE.
- **danger_level**: `TEXT` — Niveau de danger, `CHECK (danger_level IN ('low','medium','high'))`, NULLABLE.

---

## Table `health_profiles`
- **id**: `UUID` — Clé primaire, `DEFAULT uuid_generate_v4()`.
- **user_id**: `UUID` — Référence vers `users(id)`, `ON DELETE CASCADE` (chaque profil appartient à un utilisateur).
- **intolerances**: `TEXT` — Champ libre listant des intolérances (format libre), NULLABLE.
- **physical_activity_level**: `TEXT` — Niveau d'activité physique, `CHECK (physical_activity_level IN ('sedentary','light','moderate','active','very_active'))`, NULLABLE.

Remarques: les relations many-to-many entre `health_profiles` et `diseases` / `allergens` sont maintenant modélisées via les tables d'association `health_profile_diseases` et `health_profile_allergens` (voir plus bas).

Remarques: les colonnes `chronic_diseases_ids` et `allergies_ids` sont des tableaux d'UUID — SQL standard ne supporte pas de FK direct sur les éléments d'un tableau. Pour assurer l'intégrité référentielle stricte, il est recommandé de remplacer ces tableaux par des tables d'association (`health_profile_diseases`, `health_profile_allergens`) contenant `health_profile_id` et `disease_id` / `allergen_id`.

---

## Table `foods`
- **id**: `UUID` — Clé primaire, `DEFAULT uuid_generate_v4()`.
- **local_name**: `TEXT` — Nom local/usuel de l'aliment, `NOT NULL`.
- **scientific_name**: `TEXT` — Nom scientifique, NULLABLE.
- **category**: `TEXT` — Catégorie d'aliment (ex. "fruit", "vegetable"), NULLABLE.
- **nutritional_values**: `JSONB` — Objet JSON contenant les valeurs nutritionnelles (ex. kcal, lipids, proteins, carbs, vitamins...). Structure non normalisée dans le schéma actuel — documenter le format attendu ailleurs.
- **glycemic_index**: `INTEGER` — Index glycémique, NULLABLE.
- **sodium_content**: `INTEGER` — Teneur en sodium (unité à préciser, ex. mg/100g), NULLABLE.
- **potassium_content**: `INTEGER` — Teneur en potassium (unité à préciser), NULLABLE.
- **origin**: `TEXT` — Origine géographique, NULLABLE.

---

## Table `ingredients`
- **id**: `UUID` — Clé primaire, `DEFAULT uuid_generate_v4()`.
- **name**: `TEXT` — Nom de l'ingrédient, `NOT NULL`.
- **food_id**: `UUID` — Référence optionnelle vers `foods(id)`, `ON DELETE SET NULL` (lien vers l'aliment source si applicable).
- Les allergènes contenus pour un ingrédient sont maintenant stockés dans la table d'association `ingredient_allergens` (relation many-to-many vers `allergens`).

---

## Table `dishes`
- **id**: `UUID` — Clé primaire, `DEFAULT uuid_generate_v4()`.
- **name**: `TEXT` — Nom du plat, `NOT NULL`.
- **description**: `TEXT` — Description, NULLABLE.
- **meal_type**: `TEXT` — Type de repas, `CHECK (meal_type IN ('breakfast','lunch','dinner'))`, NULLABLE.
- **cuisine_origin**: `TEXT` — Origine/cuisine (ex. "french", "italian"), NULLABLE.

---

## Table `dish_ingredients`
- **dish_id**: `UUID` — Référence vers `dishes(id)`, `ON DELETE CASCADE`.
- **ingredient_id**: `UUID` — Référence vers `ingredients(id)`, `ON DELETE CASCADE`.
- **quantity**: `FLOAT` — Quantité de l'ingrédient pour le plat (unité indiquée dans `unit`), NULLABLE.
- **unit**: `TEXT` — Unité de la quantité (ex. "g", "ml", "cup"), NULLABLE.
- **PRIMARY KEY**: `(dish_id, ingredient_id)` — table d'association many-to-many entre `dishes` et `ingredients`.

---

## Indexes / Contraintes importantes
- `users.phone` : UNIQUE (empêche les doublons de numéro de téléphone).
- Plusieurs colonnes utilisent des `CHECK` pour limiter les valeurs (ex. `severity_level`, `danger_level`, `meal_type`, `physical_activity_level`). Assurez-vous que ces contraintes correspondent à vos besoins linguistiques/locales.

---

## Recommandations
- Pour l'intégrité référentielle, remplacer les tableaux `UUID[]` ou `TEXT[]` par des tables d'association (ex. `health_profile_diseases(health_profile_id, disease_id)`, `health_profile_allergens(health_profile_id, allergen_id)`, `ingredient_allergens(ingredient_id, allergen_id)` si nécessaire).
- Les tableaux ont été remplacés par des tables d'association :
	- `health_profile_diseases(health_profile_id, disease_id)`
	- `health_profile_allergens(health_profile_id, allergen_id)`
	- `ingredient_allergens(ingredient_id, allergen_id)`
- Normaliser l'objet `nutritional_values` (JSONB) en colonnes ou en table séparée si vous avez besoin de requêtes fréquentes sur des éléments individuels (ex. `calories`, `protein_g`).
- Clarifier les unités pour `weight`, `height`, `sodium_content`, `potassium_content` et documenter le format de `nutritional_values`.

---

Si vous voulez, je peux:
- Générer automatiquement les scripts de migration pour normaliser les relations `UUID[]` en tables d'association.
- Ajouter ces descriptions dans `docs.md` ou produire une version imprimable (PDF).
- Créer des exemples JSON pour le champ `nutritional_values`.

Indiquez la suite souhaitée.
