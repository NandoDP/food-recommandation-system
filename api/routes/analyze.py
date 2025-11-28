"""
API BACKEND - SYSTÈME DE RECOMMANDATION ALIMENTAIRE
FastAPI + PostgreSQL + Moteur de règles métier
"""

from fastapi import HTTPException, Depends, APIRouter, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict
from api.core.database import Database
from api.models.analyze import (
    DishAnalysisRequest, MenuAnalysisRequest,
    AnalysisResponse, DishResponse, FoodSearchResponse,
    RecommendationsResponse, RecommendedDish,
    AlternativesResponse, AlertLevel, AlternativeDish, DiseaseType
)


# ==================== ANALYSE PLAT ====================
router = APIRouter(tags=["Menu Analysis"])

db_instance = Database()

class NutritionEngine:
    # """Moteur de règles métier"""
    
    # WEIGHTS = {'allergen': 0.40, 'disease': 0.35, 'nutrition': 0.25}
    
    # DIABETES_RULES = {
    #     'gi_max_safe': 55,
    #     'gi_max_moderate': 70,
    #     'carbs_max': 60,
    #     'fiber_min': 5
    # }
    
    # HYPERTENSION_RULES = {'sodium_max_per_meal': 667}
    
    """
    Moteur de règles nutritionnelles
    Calcule scores de compatibilité et génère alertes
    """
    
    # ========== RÈGLES DIABÈTE ==========
    DIABETES_RULES = {
        'gi_thresholds': {
            'low': 55,      # IG < 55 : favorable
            'medium': 70,   # IG 55-70 : modéré
            'high': 70      # IG > 70 : défavorable
        },
        'carbs_per_meal': {
            'min': 45,      # g
            'max': 60,      # g
            'optimal': 50   # g
        },
        'fiber_min': 5,     # g par repas minimum
        'forbidden_keywords': [   # aliments à éviter: TODO
            'sucre blanc', 'confiture', 'soda', 'bonbon', 
            'pâtisserie', 'pain blanc', 'riz blanc'
        ],
        'recommended_keywords': [   # aliments recommandés: TODO
            'légume', 'légumineuse', 'lentille', 'haricot',
            'quinoa', 'avoine', 'patate douce'
        ]
    }
    
    # ========== RÈGLES HYPERTENSION ==========
    HYPERTENSION_RULES = {
        'sodium_max': 2000,     # mg/jour
        'sodium_per_meal': 667, # mg/repas (2000/3)
        'potassium_min': 3500,  # mg/jour recommandé
        'forbidden_keywords': [   # aliments à éviter: TODO
            'sel', 'salé', 'cube maggi', 'bouillon cube',
            'charcuterie', 'fromage', 'anchois', 'olive'
        ],
        'recommended_keywords': [   # aliments recommandés: TODO
            'banane', 'avocat', 'épinard', 'patate douce',
            'haricot', 'tomate', 'orange'
        ]
    }
    
    # ========== RÈGLES MALADIE HÉPATIQUE ==========
    LIVER_RULES = {
        'sodium_max': 2000,         # mg/jour
        'protein_per_kg': {
            'normal': 1.0,           # g/kg poids corporel
            'decompensated': 0.8,    # stade décompensé
            'encephalopathy': 0.6    # encéphalopathie
        },
        'avoid_alcohol': True,
        'hepatotoxic_keywords': [     # aliments à éviter: TODO
            'alcool', 'paracétamol', 'champignon sauvage',
            'fructose élevé'
        ],
        'detox_keywords': [       # aliments recommandés: TODO
            'artichaut', 'radis noir', 'citron', 'curcuma',
            'ail', 'betterave', 'pomme'
        ]
    }
    
    # ========== RÈGLES CANCER ==========
    CANCER_RULES = {
        'calorie_increase': 500,    # kcal/jour supplémentaires: TODO
        'protein_per_kg': 1.5,      # g/kg (besoins augmentés)
        'avoid_keywords': [
            'ultra-transformé', 'charcuterie', 'viande rouge',
            'sucre raffiné', 'friture', 'barbecue'
        ],
        'anti_inflammatory_keywords': [
            'curcuma', 'gingembre', 'thé vert', 'baies',
            'poisson gras', 'noix', 'légume crucifère',
            'tomate', 'ail', 'oignon'
        ]
    }
    
    # ========== RÈGLES INSUFFISANCE RÉNALE ==========
    KIDNEY_RULES = {   # pour maladie rénale chronique: TODO
        'sodium_max': 2000,         # mg/jour
        'potassium_max': 2000,      # mg/jour
        'phosphorus_max': 1000,     # mg/jour
        'protein_per_kg': 0.8,      # g/kg
        'restrict_keywords': [
            'banane', 'avocat', 'orange', 'tomate',
            'produit laitier', 'noix', 'chocolat'
        ]
    }
    
    def __init__(self):
        """Initialisation du moteur"""
        self.weights = {
            'allergen': 0.40,      # 40% du score
            'disease': 0.35,       # 35% du score
            'nutrition': 0.25      # 25% du score
        }
    
    # ==================== ANALYSE PLAT ====================
    
    # @staticmethod
    def analyze(self, dish_data: Dict, health_profile: Dict) -> Dict:
        """Analyse complète d'un plat"""
        
        results = {
            'score': 100,
            'alert_level': AlertLevel.SAFE,
            'allergen_alerts': [],
            'disease_alerts': [],
            'recommendations': [],
            'alternatives': [],
            'nutritional_summary': dish_data.get('nutritional_summary', {}),
            'detailed_breakdown': {
                'allergen_score': 100,
                'disease_score': 100,
                'nutrition_score': 100
            }
        }
        
        # 1. Vérifier allergènes
        allergen_score = self._check_allergens(
            dish_data, 
            health_profile.get('allergens', []),
            results
        )
        results['detailed_breakdown']['allergen_score'] = allergen_score
        
        # 2. Vérifier maladies
        disease_score = self._check_diseases(
            dish_data,
            health_profile.get('diseases', []),
            health_profile.get('weight', 70),
            results
        )
        results['detailed_breakdown']['disease_score'] = disease_score
        
        # 3. Équilibre nutritionnel
        nutrition_score = self._check_nutrition(dish_data, results)
        results['detailed_breakdown']['nutrition_score'] = nutrition_score
        
        # 4. Score final pondéré
        final_score = (
            allergen_score * self.weights['allergen'] +
            disease_score * self.weights['disease'] +
            nutrition_score * self.weights['nutrition']
        )
        
        results['score'] = int(final_score)
        results['alert_level'] = self._get_alert_level(final_score)
        
        return results
    
    # ==================== VÉRIFICATION ALLERGÈNES ====================
    
    # @staticmethod
    def _check_allergens(self, dish_data: Dict, user_allergens: List[str], results: Dict) -> float:
        """Vérifie présence d'allergènes"""
        if not user_allergens:
            return 100.0
        
        dish_text = dish_data['name'].lower()
        for ing in dish_data.get('ingredients', []):
            dish_text += ' ' + ing.get('name', '').lower()
        
        allergen_keywords = {
            'Arachides': ['arachide', 'peanut', 'cacahuète'],
            'Crustacés': ['crustacé', 'crabe', 'crevette', 'shrimp'],
            'Gluten (blé)': ['blé', 'wheat', 'farine', 'pain', 'avoine', 'orge', 'couscous'],
            'Lait (lactose)': ['lait', 'milk', 'yaourt', 'fromage', 'beurre'],
            'Œufs': ['œuf', 'egg', 'oeuf'],
            'Poissons': ['poisson', 'fish', 'thiof', 'sardine', 'saumon', 'truite'],
            'Fruits à coque': ['noix', 'amande', 'noisette', 'pistache', 'cashew', 'walnut', 'cajou'],
            'Moutarde': ['moutarde', 'mustard', 'cornichon', 'bouillon-cube', 'mayonnaise'],
            'Soja': ['soja', 'soy', 'tofu'],
            'Sésame': ['sésame', 'sesame', 'tahini', 'gomasio'],
        }
        
        detected_allergens = []
        
        for allergen in user_allergens:
            keywords = allergen_keywords.get(allergen, [allergen.lower()])
            for keyword in keywords:
                if keyword in dish_text:
                    detected_allergens.append(allergen)
                    results['allergen_alerts'].append({
                        'name': allergen,
                        'level': AlertLevel.CRITICAL.value,
                        'message': f'⛔ ALLERGÈNE DÉTECTÉ : {allergen}'
                    })
                    break
        
        # Score : 0 si allergène trouvé, 100 sinon
        return 0.0 if detected_allergens else 100.0
    
    # ==================== VÉRIFICATION MALADIES ====================
    
    # @staticmethod
    def _check_diseases(self, dish_data: Dict, diseases: List[str], weight: float, results: Dict) -> float:
        """Vérifie compatibilité maladies"""
        if not diseases:
            return 100.0
        
        scores = []
        nutr = dish_data.get('nutritional_summary', {})
        
        for disease in diseases:
            if disease == DiseaseType.DIABETES.value:
                score = self._check_diabetes(nutr, results)
                scores.append(score)
            
            elif disease == DiseaseType.HYPERTENSION.value:
                score = self._check_hypertension(nutr, results)
                scores.append(score)
            
            elif disease == DiseaseType.LIVER_DISEASE.value:
                score = self._check_liver_disease(nutr, weight, results)
                scores.append(score)
            
            elif disease == DiseaseType.CANCER.value:
                score = self._check_cancer(nutr, results)
                scores.append(score)
            
            elif disease == DiseaseType.KIDNEY_DISEASE.value:
                score = self._check_kidney_disease(nutr, results)
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 100.0
    
    # @staticmethod
    def _check_diabetes(self, nutr: Dict, results: Dict) -> float:
        """Règles diabète"""
        score = 100.0
        
         # 1. Index glycémique
        gi = nutr.get('glycemic_index', 60)
        if gi > self.DIABETES_RULES['gi_thresholds']['high']:
            score -= 30
            results['disease_alerts'].append({
                'name': 'Diabète',
                'level': AlertLevel.DANGER.value,
                'message': f'🔴 IG élevé ({gi}) - Risque de pic glycémique'
            })
        elif gi > self.DIABETES_RULES['gi_thresholds']['medium']:
            score -= 15
            results['disease_alerts'].append({
                'name': 'Diabète',
                'level': AlertLevel.CAUTION.value,
                'message': f'🟠 IG modéré ({gi}) - Consommer avec modération'
            })
        
        # 2. Glucides
        carbs = nutr.get('carbohydrate_g', 0)
        max_carbs = self.DIABETES_RULES['carbs_per_meal']['max']
        if carbs > max_carbs:
            score -= 20
            results['disease_alerts'].append({
                'name': 'Diabète',
                'level': AlertLevel.DANGER.value,
                'message': f'🔴 Glucides excessifs ({carbs:.1f}g > {max_carbs}g)'
            })
        
        # 3. Fibres
        fiber = nutr.get('fiber_g', 0)
        if fiber < self.DIABETES_RULES['fiber_min']:
            score -= 10
            results['recommendations'].append(
                f'💡 Ajouter plus de fibres (actuel: {fiber:.1f}g, min: {self.DIABETES_RULES["fiber_min"]}g)'
            )
        
        return max(0, score)
    
    # @staticmethod
    def _check_hypertension(self, nutr: Dict, results: Dict) -> float:
        """Règles hypertension"""
        score = 100.0
        
        # Sodium
        sodium = nutr.get('sodium_mg', 0)
        max_sodium = self.HYPERTENSION_RULES['sodium_per_meal']
        
        if sodium > max_sodium:
            excess = sodium - max_sodium
            penalty = min(40, (excess / max_sodium) * 40)
            score -= penalty
            
            results['disease_alerts'].append({
                'name': 'Hypertension',
                'level': AlertLevel.DANGER.value,
                'message': f'🔴 Sodium excessif ({sodium:.0f}mg > {max_sodium}mg/repas)'
            })
        elif sodium > max_sodium * 0.75:
            score -= 15
            results['disease_alerts'].append({
                'name': 'Hypertension',
                'level': AlertLevel.CAUTION.value,
                'message': f'🟠 Sodium élevé ({sodium:.0f}mg)'
            })
        
        return max(0, score)
    
    def _check_liver_disease(self, dish: Dict, weight: float, results: Dict) -> float:
        """Règles maladie hépatique"""
        score = 100.0
        nutr = dish.get('nutritional_summary', {})
        
        # 1. Sodium (même règle qu'hypertension)
        sodium = nutr.get('sodium_mg', 0)
        if sodium > 667:  # 2000mg/3 repas
            score -= 25
            results['disease_alerts'].append({
                'name': 'Foie',
                'level': AlertLevel.DANGER.value,
                'message': f'🔴 Sodium excessif - Risque de rétention d\'eau'
            })
        
        # 2. Protéines (vérifier si excessif)
        protein = nutr.get('protein_g', 0)
        max_protein = weight * self.LIVER_RULES['protein_per_kg']['normal']
        if protein > max_protein / 3:  # Par repas
            score -= 15
            results['recommendations'].append(
                f'⚠️ Protéines à modérer selon stade hépatique'
            )
        
        return max(0, score)
    
    def _check_cancer(self, dish: Dict, results: Dict) -> float:
        """Règles cancer"""
        score = 100.0
        
        dish_text = dish['name'].lower()
        
        # Vérifier aliments à éviter
        for keyword in self.CANCER_RULES['avoid_keywords']:
            if keyword in dish_text:
                score -= 20
                results['disease_alerts'].append({
                    'name': 'Cancer',
                    'level': AlertLevel.CAUTION.value,
                    'message': f'🟠 Éviter : {keyword}'
                })
                break
        
        # Bonus pour anti-inflammatoires
        for keyword in self.CANCER_RULES['anti_inflammatory_keywords']:
            if keyword in dish_text:
                results['recommendations'].append(
                    f'✅ Contient {keyword} (anti-inflammatoire)'
                )
                break
        
        return max(0, score)
    
    def _check_kidney_disease(self, dish: Dict, results: Dict) -> float:
        """Règles insuffisance rénale"""
        score = 100.0
        nutr = dish.get('nutritional_summary', {})
        
        # Potassium
        potassium = nutr.get('potassium_mg', 0)
        if potassium > 667:  # 2000mg/3 repas
            score -= 30
            results['disease_alerts'].append({
                'name': 'Rein',
                'level': AlertLevel.DANGER.value,
                'message': f'🔴 Potassium excessif ({potassium:.0f}mg)'
            })
        
        # Sodium
        sodium = nutr.get('sodium_mg', 0)
        if sodium > 667:
            score -= 20
        
        return max(0, score)
    
    # ==================== ÉQUILIBRE NUTRITIONNEL ====================
    
    # @staticmethod
    def _check_nutrition(self, dish_data: Dict, results: Dict) -> float:
        """Équilibre nutritionnel"""
        score = 100.0
        nutr = dish_data.get('nutritional_summary', {})
        
        protein = nutr.get('protein_g', 0)
        fat = nutr.get('fat_g', 0)
        carbs = nutr.get('carbohydrate_g', 0)
        
        total = protein + fat + carbs
        if total == 0:
            return 50.0  # Pas assez de données
        
        # Ratios recommandés (% calories)
        protein_pct = (protein * 4) / ((protein * 4) + (fat * 9) + (carbs * 4)) * 100
        fat_pct = (fat * 9) / ((protein * 4) + (fat * 9) + (carbs * 4)) * 100
        
        # Protéines : 15-25%
        if protein_pct < 10:
            score -= 15
            results['recommendations'].append('💡 Augmenter apport en protéines')
        elif protein_pct > 35:
            score -= 10
        
        # Lipides : 25-35%
        if fat_pct > 40:
            score -= 15
            results['recommendations'].append('💡 Réduire matières grasses')
        
        return max(0, score)
    
    # ==================== NIVEAU D'ALERTE ====================
    
    # @staticmethod
    def _get_alert_level(self, score: float) -> AlertLevel:
        """Détermine niveau d'alerte"""
        if score >= 75:
            return AlertLevel.SAFE
        elif score >= 50:
            return AlertLevel.CAUTION
        elif score >= 25:
            return AlertLevel.DANGER
        else:
            return AlertLevel.CRITICAL

# ==================== HELPER FUNCTIONS ====================

def get_user_health_profile(user_id: str, db: Session) -> Dict:
    """Récupère le profil santé complet d'un utilisateur"""
    from api.routes.users import get_user_profile
    
    profile = get_user_profile(user_id, db)
    health_profile = profile['health']
    health_profile['weight'] = profile.get("user").get('weight', 70)
    
    return health_profile

def calculate_dish_nutrition(dish_id: str, db: Session) -> Dict:
    """Calcule le résumé nutritionnel d'un plat à partir de ses ingrédients"""
    from api.schemas.analyze import DishIngredient, Ingredient, Food
    
    # Récupérer ingrédients avec foods
    dish_ingredients = db.query(DishIngredient).options(
        joinedload(DishIngredient.ingredient).joinedload(Ingredient.food)
    ).filter(DishIngredient.dish_id == dish_id).all()
    
    nutritional_summary = {
        'energy_kcal': 0,
        'protein_g': 0,
        'fat_g': 0,
        'carbohydrate_g': 0,
        'fiber_g': 0,
        'sodium_mg': 0,
        'potassium_mg': 0,
        'glycemic_index': None
    }
    
    gi_values = []
    
    for di in dish_ingredients:
        if di.ingredient and di.ingredient.food:
            food = di.ingredient.food
            nutr_values = food.nutritional_values or {}
            
            # Facteur de quantité (normaliser à 100g)
            qty_factor = (di.quantity or 100) / 100
            
            # Cumuler les nutriments
            nutritional_summary['energy_kcal'] += (nutr_values.get('energy_kcal', 0) or 0) * qty_factor
            nutritional_summary['protein_g'] += (nutr_values.get('protein_g', 0) or 0) * qty_factor
            nutritional_summary['fat_g'] += (nutr_values.get('fat_g', 0) or 0) * qty_factor
            nutritional_summary['carbohydrate_g'] += (nutr_values.get('carbohydrate_g', 0) or 0) * qty_factor
            nutritional_summary['fiber_g'] += (nutr_values.get('fiber_g', 0) or 0) * qty_factor
            nutritional_summary['sodium_mg'] += (nutr_values.get('sodium_mg', 0) or 0) * qty_factor
            nutritional_summary['potassium_mg'] += (nutr_values.get('potassium_mg', 0) or 0) * qty_factor
            
            # Collecter IG pour moyenne pondérée
            if food.glycemic_index:
                gi_values.append((food.glycemic_index, di.quantity or 100))
    
    # Calculer IG moyen pondéré
    if gi_values:
        total_qty = sum(qty for gi, qty in gi_values)
        weighted_gi = sum(gi * qty for gi, qty in gi_values) / total_qty
        nutritional_summary['glycemic_index'] = int(weighted_gi)
    else:
        nutritional_summary['glycemic_index'] = 65  # Valeur par défaut
    
    return nutritional_summary

# ==================== ENDPOINTS ====================

@router.post("/analyze-dish", response_model=AnalysisResponse)
def analyze_dish(payload: DishAnalysisRequest, db: Session = Depends(db_instance.get_db)):
    """
    Analyse un plat spécifique pour un utilisateur
    
    Args:
        dish_id: UUID du plat
        user_id: UUID de l'utilisateur (optionnel)
        health_profile: Profil santé direct (optionnel, prioritaire sur user_id)
    
    Returns:
        Score, alertes, recommandations
    """
    from api.schemas.analyze import Dish, DishIngredient, Ingredient
    
    # 1. Vérifier que le plat existe
    dish = db.query(Dish).filter(Dish.id == payload.dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    # 2. Récupérer ingrédients
    ingredients = db.query(Ingredient).join(
        DishIngredient,
        DishIngredient.ingredient_id == Ingredient.id
    ).filter(DishIngredient.dish_id == payload.dish_id).all()
    
    ingredient_list = [{'name': ing.name} for ing in ingredients]
    
    # 3. Calculer résumé nutritionnel
    nutritional_summary = calculate_dish_nutrition(payload.dish_id, db)
    
    # 4. Récupérer profil santé
    if payload.health_profile:
        health_profile = payload.health_profile
    elif payload.user_id:
        health_profile = get_user_health_profile(payload.user_id, db)
    else:
        health_profile = {'diseases': [], 'allergens': [], 'weight': 70}
    
    # 5. Analyse avec moteur de règles
    dish_data = {
        'name': dish.name,
        'ingredients': ingredient_list,
        'nutritional_summary': nutritional_summary
    }
    
    engine = NutritionEngine()
    analysis = engine.analyze(dish_data, health_profile)
    
    return AnalysisResponse(**analysis)


@router.post("/analyze-menu", response_model=AnalysisResponse)
def analyze_menu(payload: MenuAnalysisRequest, db: Session = Depends(db_instance.get_db)):
    """
    Analyse un menu depuis une description textuelle
    
    Args:
        menu_text: Description du menu (ex: "Thiéboudienne avec riz et poisson")
        user_id: UUID de l'utilisateur (optionnel)
        health_profile: Profil santé direct (optionnel)
    
    Returns:
        Score, alertes, recommandations
    
    Note: Pour une version avancée, intégrer Claude API pour extraction NLP
    """
    
    menu_text = payload.menu_text.lower()
    
    # Estimation simple basée sur mots-clés
    nutritional_summary = {
        'energy_kcal': 600,
        'protein_g': 25,
        'fat_g': 15,
        'carbohydrate_g': 80,
        'fiber_g': 4,
        'sodium_mg': 800,
        'potassium_mg': 600,
        'glycemic_index': 70
    }
    
    # Ajustements basés sur mots-clés
    if 'riz' in menu_text or 'rice' in menu_text:
        nutritional_summary['carbohydrate_g'] += 20
        nutritional_summary['glycemic_index'] = 75
    
    if 'poisson' in menu_text or 'fish' in menu_text:
        nutritional_summary['protein_g'] += 10
    
    if 'légume' in menu_text or 'vegetable' in menu_text:
        nutritional_summary['fiber_g'] += 3
        nutritional_summary['glycemic_index'] -= 10
    
    if 'frit' in menu_text or 'fried' in menu_text:
        nutritional_summary['fat_g'] += 15
        nutritional_summary['energy_kcal'] += 150
    
    # Récupérer profil santé
    if payload.health_profile:
        health_profile = payload.health_profile
    elif payload.user_id:
        health_profile = get_user_health_profile(payload.user_id, db)
    else:
        health_profile = {'diseases': [], 'allergens': [], 'weight': 70}
    
    # Analyse
    dish_data = {
        'name': payload.menu_text,
        'ingredients': [],
        'nutritional_summary': nutritional_summary
    }
    
    engine = NutritionEngine()
    analysis = engine.analyze(dish_data, health_profile)
    
    return AnalysisResponse(**analysis)


@router.get("/dishes", response_model=List[DishResponse])
def list_dishes(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    meal_type: Optional[str] = Query(None, regex="^(breakfast|lunch|dinner)$"),
    db: Session = Depends(db_instance.get_db)
):
    """
    Liste les plats disponibles avec filtrage optionnel
    
    Args:
        limit: Nombre max de résultats (défaut: 20)
        offset: Décalage pour pagination (défaut: 0)
        meal_type: Filtrer par type de repas (optionnel)
    
    Returns:
        Liste de plats avec nombre d'ingrédients
    """
    from api.models.analyze import Dish, DishIngredient
    from sqlalchemy import func
    
    # Requête de base avec comptage d'ingrédients
    query = db.query(
        Dish.id,
        Dish.name,
        Dish.description,
        Dish.meal_type,
        Dish.cuisine_origin,
        func.count(DishIngredient.ingredient_id).label('ingredient_count')
    ).outerjoin(
        DishIngredient,
        DishIngredient.dish_id == Dish.id
    ).group_by(
        Dish.id,
        Dish.name,
        Dish.description,
        Dish.meal_type,
        Dish.cuisine_origin
    )
    
    # Filtrage par meal_type si spécifié
    if meal_type:
        query = query.filter(Dish.meal_type == meal_type)
    
    # Pagination
    dishes = query.order_by(Dish.name).limit(limit).offset(offset).all()
    
    # Convertir en DishResponse
    return [
        DishResponse(
            id=str(d.id),
            name=d.name,
            description=d.description,
            meal_type=d.meal_type,
            cuisine_origin=d.cuisine_origin,
            ingredient_count=d.ingredient_count
        )
        for d in dishes
    ]


@router.get("/foods/search", response_model=List[FoodSearchResponse])
def search_foods(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(db_instance.get_db)
):
    """
    Recherche d'aliments par nom
    
    Args:
        q: Terme de recherche (min 2 caractères)
        limit: Nombre max de résultats (défaut: 10)
    
    Returns:
        Liste d'aliments correspondants
    """
    from api.models.analyze import Food
    
    # Recherche insensible à la casse avec ILIKE
    foods = db.query(Food).filter(
        Food.local_name.ilike(f'%{q}%')
    ).order_by(Food.local_name).limit(limit).all()
    
    # Convertir en FoodSearchResponse
    return [
        FoodSearchResponse(
            id=str(f.id),
            local_name=f.local_name,
            category=f.category,
            glycemic_index=f.glycemic_index,
            energy_kcal=f.nutritional_values.get('energy_kcal') if f.nutritional_values else None
        )
        for f in foods
    ]
    


# ==================== RECOMMANDATIONS ====================

@router.get("/recommendations/{user_id}")
def get_recommendations(
    user_id: str,
    meal_type: Optional[str] = Query(None, regex="^(breakfast|lunch|dinner)$"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(db_instance.get_db)
):
    """
    Obtient des recommandations de plats personnalisées pour un utilisateur
    
    Args:
        user_id: UUID de l'utilisateur
        meal_type: Filtrer par type de repas (optionnel)
        limit: Nombre de recommandations (défaut: 5)
    
    Returns:
        Liste de plats recommandés avec scores et raisons
    
    Logique:
        1. Récupère le profil santé de l'utilisateur
        2. Analyse tous les plats disponibles
        3. Filtre et classe par score de compatibilité
        4. Retourne les meilleurs plats avec explications
    """
    from api.schemas.analyze import Dish, DishIngredient, Ingredient
    
    # 1. Récupérer profil santé
    health_profile = get_user_health_profile(user_id, db)
    
    # 2. Récupérer plats disponibles
    query = db.query(Dish)
    
    if meal_type:
        query = query.filter(Dish.meal_type == meal_type)
    
    dishes = query.all()
    
    if not dishes:
        raise HTTPException(status_code=404, detail="No dishes available")
    
    # 3. Analyser chaque plat et scorer
    scored_dishes = []
    
    for dish in dishes:
        # Récupérer ingrédients
        ingredients = db.query(Ingredient).join(
            DishIngredient,
            DishIngredient.ingredient_id == Ingredient.id
        ).filter(DishIngredient.dish_id == dish.id).all()
        
        ingredient_list = [{'name': ing.name} for ing in ingredients]
        
        # Calculer nutrition
        nutritional_summary = calculate_dish_nutrition(str(dish.id), db)
        
        # Analyser
        dish_data = {
            'name': dish.name,
            'ingredients': ingredient_list,
            'nutritional_summary': nutritional_summary
        }
        
        engine = NutritionEngine()
        analysis = engine.analyze(dish_data, health_profile)
        
        # Ne garder que les plats sans allergènes critiques
        has_critical_allergen = any(
            alert['level'] == AlertLevel.CRITICAL 
            for alert in analysis['allergen_alerts']
        )
        
        if not has_critical_allergen:
            # Générer raison de recommandation
            reason = _generate_recommendation_reason(analysis, health_profile)
            
            # Highlights nutritionnels
            highlights = _generate_nutritional_highlights(nutritional_summary, health_profile)
            
            scored_dishes.append({
                'dish_id': str(dish.id),
                'dish_name': dish.name,
                'score': analysis['score'],
                'alert_level': analysis['alert_level'],
                'meal_type': dish.meal_type or 'lunch',
                'reason': reason,
                'nutritional_highlights': highlights
            })
    
    # 4. Trier par score décroissant
    scored_dishes.sort(key=lambda x: x['score'], reverse=True)
    
    # 5. Limiter résultats
    top_recommendations = scored_dishes[:limit]
    
    # 6. Générer conseils personnalisés
    personalized_tips = _generate_personalized_tips(health_profile)
    
    # return RecommendationsResponse(
    #     user_id=user_id,
    #     recommendations=[RecommendedDish(**dish) for dish in top_recommendations],
    #     personalized_tips=personalized_tips,
    #     count=len(top_recommendations)
    # )
    return {
        'user_id': user_id,
        'recommendations': top_recommendations,
        'personalized_tips': personalized_tips,
        'count': len(top_recommendations)
    }


def _generate_recommendation_reason(analysis: Dict, health_profile: Dict) -> str:
    """Génère une raison de recommandation basée sur l'analyse"""
    
    score = analysis['score']
    diseases = health_profile.get('diseases', [])
    
    if score >= 85:
        return "Excellent choix pour votre profil santé"
    elif score >= 75:
        reasons = []
        
        if 'Diabète' in ' '.join(diseases):
            gi = analysis['nutritional_summary'].get('glycemic_index', 0)
            if gi and gi < 55:
                reasons.append("IG bas adapté au diabète")
        
        if 'Hypertension' in ' '.join(diseases):
            sodium = analysis['nutritional_summary'].get('sodium_mg', 0)
            if sodium and sodium < 500:
                reasons.append("faible en sodium")
        
        if reasons:
            return "Bon choix : " + ", ".join(reasons)
        else:
            return "Compatible avec votre profil santé"
    
    elif score >= 60:
        return "Acceptable avec quelques précautions"
    else:
        return "À consommer avec modération"


def _generate_nutritional_highlights(nutr: Dict, health_profile: Dict) -> List[str]:
    """Génère les points forts nutritionnels du plat"""
    
    highlights = []
    diseases = health_profile.get('diseases', [])
    
    # Fibres
    fiber = nutr.get('fiber_g', 0)
    if fiber and fiber >= 5:
        highlights.append(f"Riche en fibres ({fiber:.1f}g)")
    
    # Protéines
    protein = nutr.get('protein_g', 0)
    if protein and protein >= 20:
        highlights.append(f"Bonne source de protéines ({protein:.1f}g)")
    
    # IG bas pour diabétiques
    if 'Diabète' in ' '.join(diseases):
        gi = nutr.get('glycemic_index', 0)
        if gi and gi < 55:
            highlights.append(f"Index glycémique bas ({gi})")
    
    # Faible sodium pour HTA
    if 'Hypertension' in ' '.join(diseases):
        sodium = nutr.get('sodium_mg', 0)
        if sodium and sodium < 400:
            highlights.append(f"Faible en sodium ({sodium:.0f}mg)")
    
    # Énergie modérée
    energy = nutr.get('energy_kcal', 0)
    if energy and 400 <= energy <= 600:
        highlights.append("Apport calorique équilibré")
    
    if not highlights:
        highlights.append("Plat équilibré")
    
    return highlights


def _generate_personalized_tips(health_profile: Dict) -> List[str]:
    """Génère des conseils personnalisés selon le profil"""
    
    tips = []
    diseases = health_profile.get('diseases', [])
    
    if 'Diabète' in ' '.join(diseases):
        tips.append("💡 Privilégiez les aliments à index glycémique bas (<55)")
        tips.append("🥗 Ajoutez des légumes verts pour ralentir l'absorption des glucides")
    
    if 'Hypertension' in ' '.join(diseases):
        tips.append("🧂 Limitez le sel, utilisez citron et épices pour assaisonner")
        tips.append("🥑 Favorisez les aliments riches en potassium")
    
    if 'Maladie hépatique' in ' '.join(diseases):
        tips.append("🍵 Hydratez-vous suffisamment tout au long de la journée")
        tips.append("🥦 Privilégiez les aliments détoxifiants (artichaut, citron)")
    
    if not tips:
        tips.append("🍽️ Privilégiez la variété et l'équilibre dans vos repas")
        tips.append("💧 Buvez au moins 1.5L d'eau par jour")
    
    return tips


# ==================== ALTERNATIVES ====================

@router.post("/alternatives/{dish_id}", response_model=AlternativesResponse)
def suggest_alternatives(
    dish_id: str,
    user_id: Optional[str] = None,
    health_profile: Optional[Dict] = None,
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(db_instance.get_db)
):
    """
    Suggère des plats alternatifs pour un plat donné
    
    Args:
        dish_id: UUID du plat problématique
        user_id: UUID de l'utilisateur (optionnel)
        health_profile: Profil santé direct (optionnel)
        limit: Nombre d'alternatives (défaut: 5)
    
    Returns:
        Liste de plats alternatifs plus adaptés au profil santé
    
    Logique:
        1. Analyse le plat original
        2. Identifie les problèmes (allergènes, IG élevé, sodium...)
        3. Cherche des plats similaires mais plus adaptés
        4. Propose des substitutions d'ingrédients
    """
    from api.models.analyze import Dish, DishIngredient, Ingredient
    
    # 1. Vérifier que le plat existe
    original_dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not original_dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    # 2. Récupérer profil santé
    if health_profile:
        hp = health_profile
    elif user_id:
        hp = get_user_health_profile(user_id, db)
    else:
        hp = {'diseases': [], 'allergens': [], 'weight': 70}
    
    # 3. Analyser le plat original
    original_ingredients = db.query(Ingredient).join(
        DishIngredient,
        DishIngredient.ingredient_id == Ingredient.id
    ).filter(DishIngredient.dish_id == dish_id).all()
    
    original_nutr = calculate_dish_nutrition(dish_id, db)
    
    engine = NutritionEngine()
    original_analysis = NutritionEngine.analyze(
        {
            'name': original_dish.name,
            'ingredients': [{'name': ing.name} for ing in original_ingredients],
            'nutritional_summary': original_nutr
        },
        hp
    )
    
    # 4. Identifier les problèmes
    problems = []
    for alert in original_analysis['allergen_alerts']:
        if alert['level'] in [AlertLevel.DANGER, AlertLevel.CRITICAL]:
            problems.append('allergen')
            break
    for alert in original_analysis['disease_alerts']:
        if alert['level'] in [AlertLevel.DANGER, AlertLevel.CRITICAL]:
            problems.append('disease')
            break
    
    # 5. Chercher plats alternatifs du même type de repas
    alternative_dishes = db.query(Dish).filter(
        Dish.meal_type == original_dish.meal_type,
        Dish.id != dish_id
    ).limit(20).all()
    
    # 6. Analyser et scorer les alternatives
    scored_alternatives = []
    
    engine = NutritionEngine()
    for alt_dish in alternative_dishes:
        alt_ingredients = db.query(Ingredient).join(
            DishIngredient,
            DishIngredient.ingredient_id == Ingredient.id
        ).filter(DishIngredient.dish_id == alt_dish.id).all()
        
        alt_nutr = calculate_dish_nutrition(str(alt_dish.id), db)
        
        alt_analysis = engine.analyze(
            {
                'name': alt_dish.name,
                'ingredients': [{'name': ing.name} for ing in alt_ingredients],
                'nutritional_summary': alt_nutr
            },
            hp
        )
        
        # Ne proposer que si score meilleur
        if alt_analysis['score'] > original_analysis['score']:
            # Expliquer pourquoi c'est mieux
            reason = _explain_why_better(
                original_analysis, 
                alt_analysis, 
                original_nutr, 
                alt_nutr,
                hp
            )
            
            # Modifications suggérées
            modifications = _generate_modifications(alt_nutr, hp)
            
            scored_alternatives.append({
                'dish_id': str(alt_dish.id),
                'dish_name': alt_dish.name,
                'score': alt_analysis['score'],
                'alert_level': alt_analysis['alert_level'],
                'reason': reason,
                'modifications': modifications
            })
    
    # 7. Trier par score décroissant
    scored_alternatives.sort(key=lambda x: x['score'], reverse=True)
    
    # 8. Limiter résultats
    top_alternatives = scored_alternatives[:limit]
    
    # 9. Générer suggestions de substitution pour le plat original
    substitutions = _generate_ingredient_substitutions(
        original_ingredients, 
        problems,
        hp
    )
    
    return AlternativesResponse(
        original_dish_id=str(original_dish.id),
        original_dish_name=original_dish.name,
        original_score=original_analysis['score'],
        alternatives=[AlternativeDish(**alt) for alt in top_alternatives],
        substitution_suggestions=substitutions
    )


def _explain_why_better(orig_analysis: Dict, alt_analysis: Dict, 
                        orig_nutr: Dict, alt_nutr: Dict, hp: Dict) -> str:
    """Explique pourquoi l'alternative est meilleure"""
    
    reasons = []
    diseases = hp.get('diseases', [])
    
    # Comparaison IG
    if 'Diabète' in ' '.join(diseases):
        orig_gi = orig_nutr.get('glycemic_index', 0)
        alt_gi = alt_nutr.get('glycemic_index', 0)
        
        if orig_gi and alt_gi and alt_gi < orig_gi - 10:
            reasons.append(f"IG plus bas ({alt_gi} vs {orig_gi})")
    
    # Comparaison sodium
    if 'Hypertension' in ' '.join(diseases):
        orig_sodium = orig_nutr.get('sodium_mg', 0)
        alt_sodium = alt_nutr.get('sodium_mg', 0)
        
        if orig_sodium and alt_sodium and alt_sodium < orig_sodium * 0.7:
            diff = orig_sodium - alt_sodium
            reasons.append(f"{diff:.0f}mg moins de sodium")
    
    # Fibres
    orig_fiber = orig_nutr.get('fiber_g', 0)
    alt_fiber = alt_nutr.get('fiber_g', 0)
    
    if orig_fiber and alt_fiber and alt_fiber > orig_fiber * 1.3:
        reasons.append(f"plus riche en fibres ({alt_fiber:.1f}g)")
    
    if reasons:
        return "Meilleur car : " + ", ".join(reasons)
    else:
        return "Meilleur score de compatibilité global"


def _generate_modifications(nutr: Dict, hp: Dict) -> List[str]:
    """Génère des suggestions de modification pour le plat"""
    
    modifications = []
    diseases = hp.get('diseases', [])
    
    if 'Diabète' in ' '.join(diseases):
        modifications.append("Ajouter des légumes verts pour baisser l'IG")
        modifications.append("Préférer riz basmati au riz blanc")
    
    if 'Hypertension' in ' '.join(diseases):
        modifications.append("Cuisiner sans sel ajouté")
        modifications.append("Assaisonner avec citron et herbes")
    
    return modifications


def _generate_ingredient_substitutions(ingredients: List, problems: List[str], hp: Dict) -> List[str]:
    """Génère des suggestions de substitution d'ingrédients"""
    
    substitutions = []
    diseases = hp.get('diseases', [])
    allergens = hp.get('allergens', [])
    
    ingredient_names = [ing.name.lower() for ing in ingredients]
    
    # Substitutions pour diabète
    if 'Diabète' in ' '.join(diseases):
        if any('riz blanc' in name for name in ingredient_names):
            substitutions.append("Remplacer riz blanc par riz basmati ou quinoa")
        
        if any('pomme de terre' in name for name in ingredient_names):
            substitutions.append("Remplacer pomme de terre par patate douce")
    
    # Substitutions pour hypertension
    if 'Hypertension' in ' '.join(diseases):
        if any('bouillon cube' in name or 'cube' in name for name in ingredient_names):
            substitutions.append("Remplacer cube Maggi par épices naturelles")
    
    # Substitutions pour allergènes
    if 'Arachides' in allergens:
        if any('arachide' in name for name in ingredient_names):
            substitutions.append("Remplacer huile d'arachide par huile d'olive ou tournesol")
    
    if 'Lait (lactose)' in allergens:
        if any('lait' in name for name in ingredient_names):
            substitutions.append("Remplacer lait de vache par lait d'amande ou lait sans lactose")
    
    if not substitutions:
        substitutions.append("Augmenter la portion de légumes")
        substitutions.append("Réduire les matières grasses")
    
    return substitutions