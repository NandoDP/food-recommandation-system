# 📚 Documentation Scientifique et Méthodologique

## Table des Matières

1. [Sources Scientifiques](#sources-scientifiques)
2. [Méthodologie de Calcul](#m%C3%A9thodologie-de-calcul)
3. [Documentation des Analyses](#documentation-des-analyses)
4. [Système de Recommandations](#syst%C3%A8me-de-recommandations)
5. [Algorithme d'Alternatives](#algorithme-dalternatives)

- - -

## 1. Sources Scientifiques

### 📖 Index Glycémique (IG)

**Références principales :**

1. **Jenkins, D.J., et al. (1981)**\
   _"Glycemic index of foods: a physiological basis for carbohydrate exchange"_\
   American Journal of Clinical Nutrition, 34(3), 362-366.\
   DOI: 10.1093/ajcn/34.3.362
2. **Atkinson, F.S., et al. (2008)**\
   _"International Tables of Glycemic Index and Glycemic Load Values: 2008"_\
   Diabetes Care, 31(12), 2281-2283.\
   DOI: 10.2337/dc08-1239
3. **OMS/FAO (1998)**\
   _"Carbohydrates in human nutrition"_\
   FAO Food and Nutrition Paper 66

**Classification utilisée :**

```
IG Bas     : < 55  (Recommandé pour diabétiques)
IG Moyen   : 55-70 (Modération)
IG Élevé   : > 70  (À éviter)
```

**Source de validation :** International GI Database (University of Sydney)

- - -

### 🧂 Apport en Sodium

**Références :**

1. **OMS (2012)**\
   _"Guideline: Sodium intake for adults and children"_\
   ISBN: 978-92-4-150483-6\
   Recommandation : **< 2000 mg/jour** (< 5g de sel)
2. **He, F.J., & MacGregor, G.A. (2015)**\
   _"Salt reduction lowers cardiovascular risk"_\
   The Lancet, 387(10025), 1213-1218.\
   DOI: 10.1016/S0140-6736(15)00879-2
3. **American Heart Association (2021)**\
   _"How much sodium should I eat per day?"_\
   Recommandation : **< 1500 mg/jour** pour hypertendus

**Calcul utilisé :**


```python
# Par repas (3 repas/jour)
sodium_max_per_meal = 2000 mg / 3 = 667 mg

# Seuils d'alerte
Vert (Safe)    : < 500 mg/repas
Orange (Caution): 500-667 mg/repas  
Rouge (Danger) : > 667 mg/repas
```

---

### 🍞 Glucides et Diabète

**Références :**

1. **American Diabetes Association (2023)**  
   *"Standards of Medical Care in Diabetes"*  
   Diabetes Care, 46(Supplement 1)  
   DOI: 10.2337/dc23-Sint

2. **Evert, A.B., et al. (2019)**  
   *"Nutrition Therapy for Adults With Diabetes or Prediabetes"*  
   Diabetes Care, 42(5), 731-754.  
   DOI: 10.2337/dci19-0014

**Recommandations appliquées :**
```
Glucides par repas : 45-60g (selon besoins individuels)
Fibres minimales   : 5g/repas (≥25-30g/jour)
Ratio glucides     : 45-50% des calories totales
```

**Formule de charge glycémique (CG) :**
```
CG = (IG × Quantité glucides en g) / 100

CG basse  : < 10
CG moyenne: 10-20
CG élevée : > 20
```

---

### 🫀 Maladies Cardiovasculaires et Graisses

**Références :**

1. **Sacks, F.M., et al. (2017)**  
   *"Dietary Fats and Cardiovascular Disease"*  
   Circulation, 136(3), e1-e23.  
   DOI: 10.1161/CIR.0000000000000510

2. **OMS (2018)**  
   *"Draft guidelines on saturated fatty acid and trans-fatty acid intake"*

**Recommandations :**
```
Graisses totales      : 20-35% des calories
Graisses saturées     : < 10% des calories
Graisses trans        : < 1% des calories
Oméga-3 (EPA+DHA)     : 250-500 mg/jour
```

- - -

### 🧬 Allergènes Majeurs

**Références :**

1. **Règlement UE n° 1169/2011**\
   _"Information des consommateurs sur les denrées alimentaires"_\
   Liste des 14 allergènes majeurs
2. **Muraro, A., et al. (2014)**\
   _"EAACI Food Allergy and Anaphylaxis Guidelines"_\
   Allergy, 69(8), 1008-1025.\
   DOI: 10.1111/all.12429

**Liste des 14 allergènes utilisés :**

1. Céréales contenant du gluten
2. Crustacés
3. Œufs
4. Poissons
5. Arachides
6. Soja
7. Lait
8. Fruits à coque
9. Céleri
10. Moutarde
11. Graines de sésame
12. Anhydride sulfureux et sulfites
13. Lupin
14. Mollusques

- - -

## 2. Méthodologie de Calcul

### 🎯 Système de Scoring (0-100)

#### **Formule Générale**

python

```python
Score_Final = (Score_Allergènes × 0.40) + 
              (Score_Maladies × 0.35) + 
              (Score_Nutrition × 0.25)
```

**Justification de la pondération :**

```
Critère	Poids	JustificationAllergènes	40%	Priorité absolue : risque vital immédiat (choc anaphylactique)
Maladies	35%	Critique : gestion à long terme des pathologies chroniques
Nutrition	25%	Important : équilibre nutritionnel général
```

**Source :** Adapté de Drewnowski, A. (2005). _"Concept of a nutritious food"_, Journal of the American College of Nutrition.

- - -

### 📊 Calcul du Score Allergènes

python

```python
def _check_allergens(dish_data, user_allergens, results):
    if not user_allergens:
        return 100.0  # Aucun allergène déclaré
    
    # Détection par mots-clés
    allergen_keywords = {
        'Arachides': ['arachide', 'peanut', 'cacahuète'],
        'Gluten': ['blé', 'wheat', 'farine', 'pain'],
        # ...
    }
    
    for allergen in user_allergens:
        if allergen_detected_in_dish:
            return 0.0  # Score nul si allergène présent
    
    return 100.0  # Pas d'allergène détecté
```

**Logique binaire :**

* ✅ **100 points** : Aucun allergène détecté
* ❌ **0 points** : Au moins 1 allergène détecté → Plat INTERDIT

**Niveau d'alerte :**

* `CRITICAL` : Allergène détecté (score = 0)

- - -

### 🏥 Calcul du Score Maladies

#### **Pour Diabète Type 2**

python

```python
def _check_diabetes(nutr, results):
    score = 100.0
    
    # 1. Index Glycémique (poids: 30%)
    gi = nutr['glycemic_index']
    
    if gi > 70:
        score -= 30
        alert = "DANGER"
    elif gi > 55:
        score -= 15
        alert = "CAUTION"
    
    # 2. Glucides (poids: 20%)
    carbs = nutr['carbohydrate_g']
    
    if carbs > 60:
        score -= 20
        alert = "DANGER"
    
    # 3. Fibres (poids: 10%)
    fiber = nutr['fiber_g']
    
    if fiber < 5:
        score -= 10
        recommendation = "Ajouter fibres"
    
    return max(0, score)
```

**Références :**

* Seuils IG : Atkinson et al. (2008)
* Seuils glucides : ADA Standards of Care (2023)
* Seuils fibres : OMS recommandations (25-30g/jour)

- - -

#### **Pour Hypertension**

python

```python
def _check_hypertension(nutr, results):
    score = 100.0
    
    sodium = nutr['sodium_mg']
    sodium_max = 667  # mg/repas (2000mg/3)
    
    if sodium > sodium_max:
        excess_ratio = sodium / sodium_max
        penalty = min(30, excess_ratio * 30)
        score -= penalty
        alert = "DANGER"
    
    elif sodium > sodium_max * 0.75:
        score -= 15
        alert = "CAUTION"
    
    return max(0, score)
```

**Source :** OMS (2012), He & MacGregor (2015)

**Calcul de pénalité progressive :**
```
Pénalité = min(30, (Sodium_Réel / Sodium_Max) × 30)

Exemple:
- 800mg : (800/667) × 30 = 36 → plafonné à 30 points
- 1200mg: (1200/667) × 30 = 54 → plafonné à 30 points
```

- - -

### 🥗 Calcul du Score Nutritionnel

python

```python
def _check_nutrition(dish_data, results):
    score = 100.0
    nutr = dish_data['nutritional_summary']
    
    protein = nutr['protein_g']
    fat = nutr['fat_g']
    carbs = nutr['carbohydrate_g']
    
    total_macros = protein + fat + carbs
    
    if total_macros == 0:
        return 50.0  # Données insuffisantes
    
    # Calculer % de calories (Atwater factors)
    total_kcal = (protein × 4) + (fat × 9) + (carbs × 4)
    
    protein_pct = (protein × 4 / total_kcal) × 100
    fat_pct = (fat × 9 / total_kcal) × 100
    
    # Protéines : 15-25% des calories
    if protein_pct < 10:
        score -= 15
    elif protein_pct > 35:
        score -= 10
    
    # Lipides : 25-35% des calories
    if fat_pct > 40:
        score -= 15
    
    return max(0, score)
```

**Références :**

* **Facteurs d'Atwater** :

  * Protéines : 4 kcal/g
  * Glucides : 4 kcal/g
  * Lipides : 9 kcal/g

* **Ratios recommandés** : Institute of Medicine (2005), _"Dietary Reference Intakes"_

- - -

### 🚦 Niveaux d'Alerte

python

```python
def _get_alert_level(score):
    if score >= 75:
        return "SAFE"      # 🟢 Vert
    elif score >= 50:
        return "CAUTION"   # 🟠 Orange
    elif score >= 25:
        return "DANGER"    # 🔴 Rouge
    else:
        return "CRITICAL"  # ⚫ Rouge foncé
```

**Justification des seuils :**

| Niveau | Score | Signification | Action recommandée |
|--------|-------|---------------|-------------------|
| SAFE | 75-100 | Compatible | Consommation libre |
| CAUTION | 50-74 | Acceptable avec précautions | Modération, surveiller portions |
| DANGER | 25-49 | Non recommandé | Éviter ou modifier fortement |
| CRITICAL | 0-24 | Interdit | Ne pas consommer (allergène présent) |

---

## 3. Documentation des Analyses

### 🔬 `/api/analyze-dish`

#### **Algorithme détaillé**
```
┌─────────────────────────────────────┐
│ 1. RÉCUPÉRATION DES DONNÉES        │
├─────────────────────────────────────┤
│ • Plat (nom, description)           │
│ • Ingrédients (liste complète)     │
│ • Profil santé utilisateur          │
│   - Maladies chroniques             │
│   - Allergies déclarées             │
│   - Poids corporel                  │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ 2. CALCUL NUTRITIONNEL              │
├─────────────────────────────────────┤
│ Pour chaque ingrédient:             │
│   qty_factor = quantité / 100       │
│                                     │
│   Calories += (food.kcal × factor)  │
│   Protéines += (food.prot × factor) │
│   Glucides += (food.carbs × factor) │
│   Sodium += (food.sodium × factor)  │
│                                     │
│ IG_plat = Σ(IG_ingredient × qty) / Σqty │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ 3. ANALYSE ALLERGÈNES (40%)         │
├─────────────────────────────────────┤
│ Pour chaque allergène utilisateur:  │
│   IF allergène IN plat:             │
│     RETURN Score = 0 (CRITICAL)     │
│   ELSE:                             │
│     Score = 100                     │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ 4. ANALYSE MALADIES (35%)           │
├─────────────────────────────────────┤
│ Pour chaque maladie:                │
│   • Diabète → check_diabetes()      │
│     - Vérifier IG                   │
│     - Vérifier glucides             │
│     - Vérifier fibres               │
│                                     │
│   • HTA → check_hypertension()      │
│     - Vérifier sodium               │
│     - Vérifier potassium            │
│                                     │
│   Score_maladie = moyenne(scores)   │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ 5. ANALYSE NUTRITIONNELLE (25%)     │
├─────────────────────────────────────┤
│ • Calculer ratios macronutriments   │
│ • Vérifier équilibre                │
│ • Pénaliser déséquilibres           │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ 6. SCORE FINAL PONDÉRÉ              │
├─────────────────────────────────────┤
│ Score = (Allergène×0.4) +           │
│         (Maladie×0.35) +            │
│         (Nutrition×0.25)            │
│                                     │
│ Alert_Level = f(Score)              │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ 7. GÉNÉRATION ALERTES & CONSEILS    │
├─────────────────────────────────────┤
│ • Alertes par niveau de gravité     │
│ • Recommandations personnalisées    │
│ • Alternatives si score < 50        │
└─────────────────────────────────────┘
```

#### **Exemple de calcul complet**

**Entrée :**

json

```json
{
  "dish": "Thiéboudienne",
  "ingredients": [
    {"name": "Riz blanc", "quantity": 300g},
    {"name": "Poisson thiof", "quantity": 200g},
    {"name": "Tomate", "quantity": 100g}
  ],
  "health_profile": {
    "diseases": ["Diabète Type 2", "Hypertension"],
    "allergens": [],
    "weight": 75kg
  }
}
```

**Étape 1 - Calcul nutritionnel :**
```
Riz blanc (300g) :
  - Énergie : 130 kcal/100g × 3 = 390 kcal
  - Protéines : 2.7g/100g × 3 = 8.1g
  - Glucides : 28g/100g × 3 = 84g
  - IG : 75

Poisson (200g) :
  - Énergie : 120 kcal/100g × 2 = 240 kcal
  - Protéines : 25g/100g × 2 = 50g
  - Glucides : 0g
  - IG : 0

Tomate (100g) :
  - Énergie : 18 kcal/100g × 1 = 18 kcal
  - Glucides : 4g/100g × 1 = 4g
  - IG : 38

TOTAL PLAT :
  - Énergie : 648 kcal
  - Protéines : 58.1g
  - Glucides : 88g
  - Sodium : 1200mg
  - IG moyen : (75×300 + 38×100) / 400 = 66
```

**Étape 2 - Score allergènes :**
```
Aucun allergène déclaré
→ Score_allergènes = 100
```

**Étape 3 - Score diabète :**
```
IG = 66 (> 55) → Pénalité -15 points
Glucides = 88g (> 60g) → Pénalité -20 points
Fibres = 4g (< 5g) → Pénalité -10 points

Score_diabète = 100 - 15 - 20 - 10 = 55
```

**Étape 4 - Score hypertension :**
```
Sodium = 1200mg (> 667mg/repas)
Excess = 1200 / 667 = 1.8
Pénalité = min(30, 1.8 × 30) = 30

Score_HTA = 100 - 30 = 70
```

**Étape 5 - Score maladies :**
```
Score_maladies = (55 + 70) / 2 = 62.5
```

**Étape 6 - Score nutritionnel :**
```
Total kcal = 648
Protéines % = (58.1×4 / 648) × 100 = 36% (> 35%)
→ Pénalité -10 points

Score_nutrition = 100 - 10 = 90
```

**Étape 7 - Score final :**
```
Score_final = (100 × 0.40) + (62.5 × 0.35) + (90 × 0.25)
            = 40 + 21.875 + 22.5
            = 84.375
            ≈ 84

Alert_level = SAFE (score ≥ 75)
```

**Mais avec les alertes :**

* IG modéré → CAUTION
* Glucides excessifs → DANGER
* Sodium excessif → DANGER

**Niveau d'alerte final = DANGER** (le plus restrictif l'emporte)

- - -

### 📝 `/api/analyze-menu` (Analyse textuelle)

#### **Algorithme NLP simplifié**

python

```python
def analyze_menu_text(menu_text, health_profile):
    # 1. Normalisation du texte
    text = menu_text.lower().strip()
    
    # 2. Détection de mots-clés
    keywords = {
        'riz': {'carbs': +20, 'gi': 75},
        'poisson': {'protein': +10},
        'légume': {'fiber': +3, 'gi': -10},
        'frit': {'fat': +15, 'energy': +150}
    }
    
    # 3. Estimation nutritionnelle de base
    nutr = {
        'energy_kcal': 600,  # baseline
        'protein_g': 25,
        'fat_g': 15,
        'carbohydrate_g': 80,
        'fiber_g': 4,
        'sodium_mg': 800,
        'glycemic_index': 70
    }
    
    # 4. Ajustements selon mots-clés
    for keyword, adjustments in keywords.items():
        if keyword in text:
            for nutrient, delta in adjustments.items():
                nutr[nutrient] += delta
    
    # 5. Analyse standard
    return NutritionEngine.analyze(dish_data, health_profile)
```

**⚠️ Limitations actuelles :**

* Estimation approximative (pas de NLP avancé)
* Basé sur mots-clés simples
* Recommandé : Intégrer Claude API ou GPT-4 pour extraction précise

**Roadmap amélioration :**

python

```python
# Version avancée avec Claude API
import anthropic

client = anthropic.Client(api_key="...")

prompt = f"""
Analyse ce menu et extrait:
1. Liste des ingrédients
2. Quantités estimées
3. Méthode de cuisson

Menu: {menu_text}

Retourne JSON structuré.
"""

response = client.messages.create(
    model="claude-3-sonnet-20240229",
    messages=[{"role": "user", "content": prompt}]
)

# Parser JSON et utiliser données structurées
```

---

## 4. Système de Recommandations

### 🎯 `/api/recommendations/{user_id}`

#### **Algorithme de Recommandation**
```
┌──────────────────────────────────────┐
│ 1. CHARGEMENT PROFIL UTILISATEUR    │
├──────────────────────────────────────┤
│ • Maladies chroniques                │
│ • Allergies                          │
│ • Poids corporel                     │
│ • Niveau activité physique           │
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│ 2. RÉCUPÉRATION PLATS DISPONIBLES   │
├──────────────────────────────────────┤
│ • Filtrage par meal_type (optionnel) │
│ • Tous les plats de la BDD           │
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│ 3. ANALYSE BATCH DE TOUS LES PLATS  │
├──────────────────────────────────────┤
│ FOR chaque plat:                     │
│   • Calculer nutrition               │
│   • Analyser compatibilité           │
│   • Générer score (0-100)            │
│                                      │
│   IF allergène_critique:             │
│     SKIP ce plat (exclusion)         │
│   ELSE:                              │
│     Ajouter à candidats              │
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│ 4. CLASSEMENT PAR SCORE              │
├──────────────────────────────────────┤
│ • Trier par score décroissant        │
│ • Garder top N (défaut: 5)           │
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│ 5. GÉNÉRATION EXPLICATIONS           │
├──────────────────────────────────────┤
│ Pour chaque plat recommandé:         │
│   • Raison personnalisée             │
│   • Highlights nutritionnels         │
│   • Modifications suggérées          │
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│ 6. CONSEILS PERSONNALISÉS            │
├──────────────────────────────────────┤
│ Selon maladies:                      │
│   • Diabète → IG bas, fibres         │
│   • HTA → Sodium, potassium          │
│   • Foie → Détoxifiants              │
└──────────────────────────────────────┘
```

#### **Génération de Raisons**

python

```python
def _generate_recommendation_reason(analysis, health_profile):
    score = analysis['score']
    diseases = health_profile['diseases']
    
    # Score excellent (85-100)
    if score >= 85:
        return "Excellent choix pour votre profil santé"
    
    # Score bon (75-84)
    elif score >= 75:
        reasons = []
        
        # Vérifier IG pour diabétiques
        if 'Diabète' in diseases:
            gi = analysis['nutritional_summary']['glycemic_index']
            if gi < 55:
                reasons.append("IG bas adapté au diabète")
        
        # Vérifier sodium pour HTA
        if 'Hypertension' in diseases:
            sodium = analysis['nutritional_summary']['sodium_mg']
            if sodium < 500:
                reasons.append("faible en sodium")
        
        if reasons:
            return "Bon choix : " + ", ".join(reasons)
        else:
            return "Compatible avec votre profil santé"
    
    # Score acceptable (60-74)
    elif score >= 60:
        return "Acceptable avec quelques précautions"
    
    # Score faible (< 60)
    else:
        return "À consommer avec modération"
```

#### **Highlights Nutritionnels**

python

```python
def _generate_nutritional_highlights(nutr, health_profile):
    highlights = []
    
    # 1. Fibres (≥5g = riche)
    fiber = nutr.get('fiber_g', 0)
    if fiber >= 5:
        highlights.append(f"Riche en fibres ({fiber:.1f}g)")
    
    # 2. Protéines (≥20g = bonne source)
    protein = nutr.get('protein_g', 0)
    if protein >= 20:
        highlights.append(f"Bonne source de protéines ({protein:.1f}g)")
    
    # 3. IG bas pour diabétiques
    if 'Diabète' in health_profile['diseases']:
        gi = nutr.get('glycemic_index', 0)
        if gi < 55:
            highlights.append(f"Index glycémique bas ({gi})")
    
    # 4. Faible sodium pour HTA
    if 'Hypertension' in health_profile['diseases']:
        sodium = nutr.get('sodium_mg', 0)
        if sodium < 400:
            highlights.append(f"Faible en sodium ({sodium:.0f}mg)")
    
    # 5. Énergie équilibrée (400-600 kcal)
    energy = nutr.get('energy_kcal', 0)
    if 400 <= energy <= 600:
        highlights.append("Apport calorique équilibré")
    
    return highlights if highlights else ["Plat équilibré"]
```

**Références :**

* **Fibres "riche"** : Règlement UE n°1924/2006 (≥6g/100g ou ≥3g/100kcal)
* **Protéines "source"** : ≥12% de l'apport énergétique
* **Sodium "faible"** : ≤120mg/100g (EU regulation)

- - -

### 💡 Conseils Personnalisés

python

```python
def _generate_personalized_tips(health_profile):
    tips = []
    diseases = health_profile['diseases']
    
    # Diabète
    if 'Diabète' in ' '.join(diseases):
        tips.extend([
            "💡 Privilégiez IG bas (<55)",
            "🥗 Légumes verts ralentissent absorption glucides"
        ])
    
    # Hypertension
    if 'Hypertension' in ' '.join(diseases):
        tips.extend([
            "🧂 Limitez sel, utilisez citron/épices",
            "🥑 Favorisez potassium (banane, avocat)"
        ])
    
    # Foie
    if 'Maladie hépatique' in ' '.join(diseases):
        tips.extend([
            "🍵 Hydratez-vous (1.5-2L/jour)",
            "🥦 Aliments détoxifiants (artichaut, citron)"
        ])
    
    # Conseils généraux si aucune maladie
    if not tips:
        tips.extend([
            "🍽️ Variété et équilibre alimentaire",
            "💧 Hydratation suffisante (1.5L/jour)"
        ])
    
    return tips
```

- - -

## 5. Algorithme d'Alternatives

### 🔄 `/api/alternatives/{dish_id}`

#### **Algorithme Complet**

```
┌──────────────────────────────────────────┐
│ 1. ANALYSE PLAT ORIGINAL                 │
├──────────────────────────────────────────┤
│ • Récupérer plat et ingrédients          │
│ • Calculer nutrition                     │
│ • Analyser avec profil utilisateur       │
│ • Score_original + Alertes               │
└──────────────────────────────────────────┘
            ↓
┌──────────────────────────────────────────┐
│ 2. IDENTIFICATION PROBLÈMES              │
├──────────────────────────────
```

Réessayer

N

Continuer

────────────┤ │ Extraire alertes DANGER/CRITICAL: │ │ • Allergènes détectés │ │ • IG trop élevé │ │ • Sodium excessif │ │ • Glucides trop élevés │ │ • Déséquilibre nutritionnel │ └──────────────────────────────────────────┘ ↓ ┌──────────────────────────────────────────┐ │ 3. RECHERCHE PLATS SIMILAIRES │ ├──────────────────────────────────────────┤ │ Critères de similarité: │ │ • Même meal\_type (breakfast/lunch/dinner)│ │ • Même cuisine\_origin (optionnel) │ │ • Exclure plat original │ │ │ │ Limite: 20 candidats │ └──────────────────────────────────────────┘ ↓ ┌──────────────────────────────────────────┐ │ 4. ANALYSE BATCH ALTERNATIVES │ ├──────────────────────────────────────────┤ │ FOR chaque plat candidat: │ │ • Analyser compatibilité │ │ • Calculer score │ │ │ │ IF score > score\_original: │ │ Ajouter à liste alternatives │ │ ELSE: │ │ Skip (pas mieux) │ └──────────────────────────────────────────┘ ↓ ┌──────────────────────────────────────────┐ │ 5. GÉNÉRATION EXPLICATIONS │ ├──────────────────────────────────────────┤ │ Pour chaque alternative: │ │ • Expliquer pourquoi meilleure │ │ • Comparer métriques clés │ │ • Suggérer modifications │ └──────────────────────────────────────────┘ ↓ ┌──────────────────────────────────────────┐ │ 6. SUBSTITUTIONS INGRÉDIENTS │ ├──────────────────────────────────────────┤ │ Proposer changements dans plat original: │ │ • Remplacer riz blanc → quinoa │ │ • Remplacer cube → épices naturelles │ │ • Augmenter portion légumes │ └──────────────────────────────────────────┘ ↓ ┌──────────────────────────────────────────┐ │ 7. CLASSEMENT & LIMITATION │ ├──────────────────────────────────────────┤ │ • Trier par score décroissant │ │ • Garder top N (défaut: 5) │ └──────────────────────────────────────────┘

```

#### **Comparaison et Explication**
```python
def _explain_why_better(orig_analysis, alt_analysis, 
                        orig_nutr, alt_nutr, hp):
    """
    Compare deux plats et explique les améliorations
    """
    reasons = []
    diseases = hp['diseases']
    
    # 1. Comparaison Index Glycémique
    if 'Diabète' in ' '.join(diseases):
        orig_gi = orig_nutr.get('glycemic_index', 0)
        alt_gi = alt_nutr.get('glycemic_index', 0)
        
        # Amélioration significative = -10 points IG
        if orig_gi and alt_gi and (alt_gi < orig_gi - 10):
            reasons.append(f"IG plus bas ({alt_gi} vs {orig_gi})")
    
    # 2. Comparaison Sodium
    if 'Hypertension' in ' '.join(diseases):
        orig_sodium = orig_nutr.get('sodium_mg', 0)
        alt_sodium = alt_nutr.get('sodium_mg', 0)
        
        # Amélioration significative = -30% sodium
        if orig_sodium and alt_sodium and (alt_sodium < orig_sodium * 0.7):
            diff = orig_sodium - alt_sodium
            reasons.append(f"{diff:.0f}mg moins de sodium")
    
    # 3. Comparaison Fibres
    orig_fiber = orig_nutr.get('fiber_g', 0)
    alt_fiber = alt_nutr.get('fiber_g', 0)
    
    # Amélioration significative = +30% fibres
    if orig_fiber and alt_fiber and (alt_fiber > orig_fiber * 1.3):
        reasons.append(f"plus riche en fibres ({alt_fiber:.1f}g)")
    
    # 4. Comparaison Glucides
    if 'Diabète' in ' '.join(diseases):
        orig_carbs = orig_nutr.get('carbohydrate_g', 0)
        alt_carbs = alt_nutr.get('carbohydrate_g', 0)
        
        if orig_carbs > 60 and alt_carbs <= 60:
            reasons.append(f"glucides dans limite recommandée ({alt_carbs:.1f}g)")
    
    # Retour
    if reasons:
        return "Meilleur car : " + ", ".join(reasons)
    else:
        return "Meilleur score de compatibilité global"
```

**Seuils de signification :**
- IG : Différence ≥ 10 points
- Sodium : Réduction ≥ 30%
- Fibres : Augmentation ≥ 30%
- Glucides : Passage sous seuil 60g

---

#### **Substitutions d'Ingrédients**
```python
def _generate_ingredient_substitutions(ingredients, problems, hp):
    """
    Propose substitutions basées sur problèmes identifiés
    """
    substitutions = []
    diseases = hp['diseases']
    allergens = hp['allergens']
    
    ingredient_names = [ing.name.lower() for ing in ingredients]
    
    # === DIABÈTE ===
    if 'Diabète' in ' '.join(diseases):
        
        # Riz blanc → Alternatives IG bas
        if any('riz blanc' in name for name in ingredient_names):
            substitutions.append(
                "Remplacer riz blanc par riz basmati (IG 58) ou quinoa (IG 53)"
            )
        
        # Pomme de terre → Patate douce
        if any('pomme de terre' in name for name in ingredient_names):
            substitutions.append(
                "Remplacer pomme de terre (IG 85) par patate douce (IG 70)"
            )
        
        # Pain blanc → Pain complet
        if any('pain blanc' in name for name in ingredient_names):
            substitutions.append(
                "Remplacer pain blanc par pain complet (IG 45)"
            )
    
    # === HYPERTENSION ===
    if 'Hypertension' in ' '.join(diseases):
        
        # Cube Maggi → Épices naturelles
        if any('cube' in name or 'maggi' in name for name in ingredient_names):
            substitutions.append(
                "Remplacer cube Maggi (1000mg sodium) par épices naturelles (0mg)"
            )
        
        # Sel de table → Herbes/citron
        if any('sel' in name for name in ingredient_names):
            substitutions.append(
                "Réduire ou éliminer sel, assaisonner avec citron, ail, oignon"
            )
    
    # === ALLERGÈNES ===
    
    # Arachides → Alternatives
    if 'Arachides' in allergens:
        if any('arachide' in name for name in ingredient_names):
            substitutions.append(
                "Remplacer huile arachide par huile olive/tournesol/canola"
            )
    
    # Lait → Alternatives sans lactose
    if 'Lait (lactose)' in allergens:
        if any('lait' in name for name in ingredient_names):
            substitutions.append(
                "Remplacer lait de vache par lait d'amande/soja/avoine sans lactose"
            )
    
    # Gluten → Alternatives sans gluten
    if 'Gluten' in ' '.join(allergens):
        if any('farine' in name or 'blé' in name for name in ingredient_names):
            substitutions.append(
                "Remplacer farine de blé par farine de riz/maïs/sarrasin (sans gluten)"
            )
    
    # === CONSEILS GÉNÉRAUX ===
    if not substitutions:
        substitutions.extend([
            "Augmenter portion de légumes verts (+50%)",
            "Réduire matières grasses de cuisson (-30%)",
            "Privilégier cuisson vapeur ou grill plutôt que friture"
        ])
    
    return substitutions
```

**Références substitutions :**
- **IG aliments** : International GI Database, University of Sydney
- **Sodium condiments** : Base USDA Food Composition Databases
- **Alternatives allergènes** : EAACI Guidelines (2014)

---

## 📚 Références Bibliographiques Complètes

### Articles Scientifiques

1. Atkinson, F.S., Foster-Powell, K., & Brand-Miller, J.C. (2008). International Tables of Glycemic Index and Glycemic Load Values: 2008. *Diabetes Care*, 31(12), 2281-2283.

2. Evert, A.B., et al. (2019). Nutrition Therapy for Adults With Diabetes or Prediabetes: A Consensus Report. *Diabetes Care*, 42(5), 731-754.

3. He, F.J., & MacGregor, G.A. (2015). Salt reduction lowers cardiovascular risk: meta-analysis. *The Lancet*, 387(10025), 1213-1218.

4. Jenkins, D.J., et al. (1981). Glycemic index of foods: a physiological basis for carbohydrate exchange. *American Journal of Clinical Nutrition*, 34(3), 362-366.

5. Muraro, A., et al. (2014). EAACI Food Allergy and Anaphylaxis Guidelines. *Allergy*, 69(8), 1008-1025.

6. Sacks, F.M., et al. (2017). Dietary Fats and Cardiovascular Disease: A Presidential Advisory From the American Heart Association. *Circulation*, 136(3), e1-e23.

### Organismes de Référence

1. **Organisation Mondiale de la Santé (OMS)**
   - Guidelines on Sodium Intake (2012)
   - Carbohydrates in Human Nutrition (1998)

2. **American Diabetes Association (ADA)**
   - Standards of Medical Care in Diabetes (2023)

3. **European Food Safety Authority (EFSA)**
   - Dietary Reference Values for Nutrients (2017)

4. **American Heart Association**
   - Dietary Guidelines for Sodium Reduction (2021)

### Bases de Données

1. **USDA Food Composition Databases**
   - https://fdc.nal.usda.gov/

2. **International GI Database**
   - University of Sydney
   - https://www.glycemicindex.com/

3. **FAO/INFOODS**
   - West African Food Composition Table (WAFCT 2019)

---

## 📝 Notes d'Implémentation

### Limitations Actuelles

1. **Analyse de menu textuel** : Estimation basique par mots-clés
   - **Solution future** : Intégration Claude API / GPT-4

2. **IG composite** : Moyenne pondérée simple
   - **Amélioration** : Prise en compte interactions aliments

3. **Portions individualisées** : Non adaptées au poids/taille
   - **Roadmap** : Calcul besoins énergétiques personnalisés

### Validation Clinique

**⚠️ Disclaimer Important :**

Ce système est un **outil d'aide à la décision** et ne remplace PAS :
- Une consultation médicale
- Les conseils d'un nutritionniste diplômé
- Un suivi médical personnalisé

**Recommandation :** Valider avec professionnels de santé avant déploiement à grande échelle.

---

**Version:** 1.0.0  
**Dernière mise à jour:** 26 novembre 2024  
**Auteur:** Système de Recommandation Alimentaire - Master 1
```

Réessayer

[Claude peut faire des erreurs.\
Assurez-vous de vérifier ses réponses.](https://support.anthropic.com/en/articles/8525154-claude-is-providing-incorrect-or-misleading-responses-what-s-going-on)