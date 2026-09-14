"""
API BACKEND - SYSTÈME DE RECOMMANDATION ALIMENTAIRE
FastAPI + PostgreSQL + Moteur de règles métier
"""

from fastapi import HTTPException, Depends, APIRouter, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict
from api.core.database import Database
from api.core.nutrition_engine import NutritionEngine
from api.core.menu_parser import WestAfricanMenuParser
from api.core.nutrition_calculator import calculate_dish_nutrition_from_items
from api.models.analyze import (
    DishAnalysisRequest, MenuAnalysisRequest,
    AnalysisResponse, DishResponse, FoodSearchResponse,
    RecommendationsResponse, RecommendedDish,
    AlternativesResponse, AlertLevel, AlternativeDish, DiseaseType
)


# ==================== ANALYSE PLAT ====================
router = APIRouter(tags=["Menu Analysis"])

db_instance = Database()


# Dans ton endpoint ou chatbot WhatsApp

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
        profile = get_user_health_profile(payload.user_id, db)
        health_profile = {
            'diseases': profile.get('diseases', []),
            'allergens': profile.get('allergens', []),
            'weight': profile.get('weight', 70)
        }
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
    
    from api.schemas.analyze import Ingredient
    
    menu_text = payload.menu_text.lower()
    
    # Récupérer profil santé
    if payload.health_profile:
        health_profile = payload.health_profile
    elif payload.user_id:
        profile = get_user_health_profile(payload.user_id, db)
        health_profile = {
            'diseases': profile.get('diseases', []),
            'allergens': profile.get('allergens', []),
            'weight': profile.get('weight', 70)
        }
    else:
        health_profile = {'diseases': [], 'allergens': [], 'weight': 70}
    
    parser = WestAfricanMenuParser(db_instance.get_db())
    items = parser.parse_menu_text(menu_text)
    
    # Conversion en dish_ingredients (prêt pour NutritionEngine)
    dish_data = {
        "name": "Menu détecté",
        "ingredients": [
            {"name": db.query(Ingredient).get(it["ingredient_id"]).name}
            for it in items
        ],
        "nutritional_summary": calculate_dish_nutrition_from_items(items, db, portion_size_g=500)
    }
    
    engine = NutritionEngine()
    analysis = engine.analyze(dish_data, health_profile)
    
    return AnalysisResponse(**analysis)


@router.get("/{dish_id}/dish_details")
def get_dish_details(dish_id: str, db: Session = Depends(db_instance.get_db)):
    """
    Récupère les détails d'un plat spécifique
    
    Args:
        dish_id: UUID du plat
    
    Returns:
        Détails du plat avec ingrédients
    """
    from api.schemas.analyze import Dish, DishIngredient, Ingredient
    
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    # Récupérer ingrédients avec quantités et unités
    ingredients = []
    dish_ingredients = db.query(DishIngredient).filter(DishIngredient.dish_id == dish_id).all()
    for di in dish_ingredients:
        ingredient = db.query(Ingredient).filter(Ingredient.id == di.ingredient_id).first()
        if ingredient:
            ingredients.append({
                'id': str(ingredient.id),
                'name': ingredient.name,
                'quantity': di.quantity,
                'unit': di.unit
            })
    
    return {
        'id': str(dish.id),
        'name': dish.name,
        'description': dish.description,
        'meal_type': dish.meal_type,
        'cuisine_origin': dish.cuisine_origin,
        'method': dish.method,
        'ingredients': ingredients
    }

@router.get("/dishes")
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
    from api.schemas.analyze import Dish, DishIngredient
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
    # Prendre 10 plats au hasard pour diversité
    dishes = query.order_by(func.random()).limit(limit).offset(offset).all()
    
    # Convertir en DishResponse
    return [
        {
            'id': str(d.id),
            'name': d.name,
            # 'description': d.description,
            # 'meal_type': d.meal_type,
            # 'ingredient_count': d.ingredient_count
        }
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
    from api.schemas.analyze import Food
    
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
    profile = get_user_health_profile(user_id, db)
    health_profile = {
        'diseases': profile.get('diseases', []),
        'allergens': profile.get('allergens', []),
        'weight': profile.get('weight', 70)
    }
    
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
    nutr = analysis['nutritional_summary']
    
    if score >= 85:
        reasons = ["Excellent choix pour votre profil santé (HAS/WCRF)"]
        
        if DiseaseType.DIABETES.value in diseases:
            gi = nutr.get('glycemic_index', 0)
            if gi < 55:
                reasons.append("IG bas (<55) adapté au diabète – ralentit l'absorption des glucides (HAS 2024)")
        
        if DiseaseType.HYPERTENSION.value in diseases:
            sodium = nutr.get('sodium_mg', 0)
            if sodium < 500:
                reasons.append("Faible en sodium (<500mg) – conforme au régime DASH (FRHTA)")
        
        if DiseaseType.LIVER_DISEASE.value in diseases:
            fiber = nutr.get('fiber_g', 0)
            if fiber >= 5:
                reasons.append("Riche en fibres pour détox hépatique – régime méditerranéen recommandé (AFE F)")
        
        if DiseaseType.CANCER.value in diseases:
            # Vérifier présence anti-inflammatoires (basé sur scan keywords dans engine)
            if any("anti_inflammatory" in str(analysis) for _ in [1]):  # Placeholder ; étendre engine si besoin
                reasons.append("Contient anti-inflammatoires (ex. curcuma) – réduit risque (WCRF)")
        
        if DiseaseType.KIDNEY_DISEASE.value in diseases:
            potassium = nutr.get('potassium_mg', 0)
            if potassium < 667:
                reasons.append("Faible en potassium (<667mg) – protège les reins (HAS)")
        
        return " ; ".join(reasons)
    
    elif score >= 75:
        reasons = ["Bon choix compatible"]
        # Ajouts similaires mais modérés
        if DiseaseType.DIABETES.value in diseases and nutr.get('glycemic_index', 0) < 70:
            reasons.append("IG modéré – avec légumes verts pour équilibre (HAS)")
        return " ; ".join(reasons)
    
    elif score >= 60:
        return "Acceptable avec précautions (réduire portions, ajouter légumes)"
    else:
        return "À consommer avec modération – consulter diététicien"


def _generate_nutritional_highlights(nutr: Dict, health_profile: Dict) -> List[str]:
    """Génère les points forts nutritionnels du plat"""
    
    highlights = []
    diseases = health_profile.get('diseases', [])
    
    # Fibres (général et hépatique/cancer)
    fiber = nutr.get('fiber_g', 0)
    if fiber >= 5:
        highlights.append(f"Riche en fibres ({fiber:.1f}g) – aide digestion et contrôle glycémique (HAS/WCRF)")
    
    # Protéines (rénal modéré)
    protein = nutr.get('protein_g', 0)
    weight = health_profile.get('weight', 70)
    if 0.6 * weight / 3 <= protein <= 0.8 * weight / 3:  # Par repas, adapté rénal
        highlights.append(f"Protéines modérées ({protein:.1f}g) – adapté aux reins (HAS)")
    elif protein >= 20:
        highlights.append(f"Bonne source de protéines ({protein:.1f}g) – pour énergie sans excès")
    
    # IG bas pour diabète
    if DiseaseType.DIABETES.value in diseases:
        gi = nutr.get('glycemic_index', 0)
        if gi < 55:
            highlights.append(f"Index glycémique bas ({gi}) – prévient pics glycémiques (HAS 2024)")
    
    # Faible sodium pour HTA/rénal/hépatique
    if DiseaseType.HYPERTENSION.value in diseases or DiseaseType.KIDNEY_DISEASE.value in diseases or DiseaseType.LIVER_DISEASE.value in diseases:
        sodium = nutr.get('sodium_mg', 0)
        if sodium < 400:
            highlights.append(f"Faible en sodium ({sodium:.0f}mg) – réduit rétention d'eau (DASH/HAS)")
    
    # Potassium équilibré pour HTA/rénal
    if DiseaseType.HYPERTENSION.value in diseases:
        potassium = nutr.get('potassium_mg', 0)
        if 800 <= potassium <= 1000:  # Apport modéré/jour divisé
            highlights.append(f"Bon potassium ({potassium:.0f}mg) – équilibre Na/K (FRHTA)")
    elif DiseaseType.KIDNEY_DISEASE.value in diseases and potassium < 667:
        highlights.append(f"Contrôlé en potassium ({potassium:.0f}mg) – sûr pour reins (Ameli)")
    
    # Énergie modérée (général/cancer)
    energy = nutr.get('energy_kcal', 0)
    if 400 <= energy <= 600:
        highlights.append("Apport calorique équilibré – idéal pour maintien poids (WCRF)")
    
    if DiseaseType.CANCER.value in diseases:
        # Anti-inflamm (basé sur nutr ou keywords)
        if nutr.get('fat_g', 0) > 10 and "oméga-3" in str(nutr):  # Placeholder
            highlights.append("Oméga-3 pour anti-inflammatoire – soutien immunitaire (INSERM)")
    
    if not highlights:
        highlights.append("Plat équilibré – varie les repas pour nutriments complets")
    
    return highlights


def _generate_personalized_tips(health_profile: Dict) -> List[str]:
    """Génère des conseils personnalisés selon le profil"""
    
    tips = []
    diseases = health_profile.get('diseases', [])
    allergens = health_profile.get('allergens', [])
    
    if DiseaseType.DIABETES.value in diseases:
        tips.append("💡 Privilégiez IG bas (<55) et légumes verts pour ralentir absorption glucides (HAS 2024)")
        tips.append("🏃‍♂️ Associez à 30 min activité physique/jour pour sensibilité insuline")
    
    if DiseaseType.HYPERTENSION.value in diseases:
        tips.append("🧂 Limitez sel <5-6g/jour ; utilisez citron/épices (DASH/FRHTA)")
        tips.append("🥑 Augmentez potassium (banane, épinards) pour équilibre Na/K")
    
    if DiseaseType.LIVER_DISEASE.value in diseases:
        tips.append("🍵 Hydratez 1.5-2L/jour ; régime méditerranéen riche fibres (AFE F)")
        tips.append("🥦 Privilégiez détox (artichaut, curcuma) ; évitez alcool/fructose")
    
    if DiseaseType.CANCER.value in diseases:
        tips.append("🥗 Limitez ultra-transformés/viande rouge ; + fibres/fruits (WCRF)")
        tips.append("🫐 Anti-inflamm : baies, curcuma, oméga-3 pour soutien (INSERM)")
    
    if DiseaseType.KIDNEY_DISEASE.value in diseases:
        tips.append("🍗 Protéines 0.6-0.8g/kg/jour ; faible P/K (HAS/Ameli)")
        tips.append("🌿 Alimentation alcalinisante (légumes) pour ralentir déclin rénal")
    
    if allergens:
        tips.append(f"⚠️ Éviction stricte allergènes ({', '.join(allergens)}) ; variez pour éviter carences (HAS)")
        tips.append("📋 Consultez diététicien pour équilibre nutritionnel")
    
    if not tips:
        tips.append("🍽️ Variété/équilibre : + fruits/légumes, activité physique (PNNS)")
        tips.append("💧 1.5-2L eau/jour pour santé générale")
    
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
    from api.schemas.analyze import Dish, DishIngredient, Ingredient
    
    # 1. Vérifier que le plat existe
    original_dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not original_dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    # 2. Récupérer profil santé
    if health_profile:
        hp = health_profile
    elif user_id:
        profile = get_user_health_profile(user_id, db)
        hp = {
            'diseases': profile.get('diseases', []),
            'allergens': profile.get('allergens', []),
            'weight': profile.get('weight', 70)
        }
    else:
        hp = {'diseases': [], 'allergens': [], 'weight': 70}
    
    # 3. Analyser le plat original
    original_ingredients = db.query(Ingredient).join(
        DishIngredient,
        DishIngredient.ingredient_id == Ingredient.id
    ).filter(DishIngredient.dish_id == dish_id).all()
    
    original_nutr = calculate_dish_nutrition(dish_id, db)
    
    engine = NutritionEngine()
    original_analysis = engine.analyze(
        {
            'name': original_dish.name,
            'ingredients': [{'name': ing.name} for ing in original_ingredients],
            'nutritional_summary': original_nutr
        },
        hp
    )
    
    # 4. Identifier les problèmes
    problems = []
    if _has_blocking_alert(original_analysis['allergen_alerts']):
        problems.append('allergen')
    if _has_blocking_alert(original_analysis['disease_alerts']):
        problems.append('disease')
    
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
        
        # Sécurité : un allergène du profil est une contre-indication absolue.
        # L'alternative est écartée quel que soit son score, y compris quand
        # celui-ci dépasse celui du plat d'origine.
        if _has_blocking_alert(alt_analysis['allergen_alerts']):
            continue

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


BLOCKING_ALERT_LEVELS = (AlertLevel.DANGER, AlertLevel.CRITICAL)


def _has_blocking_alert(alerts: List[Dict]) -> bool:
    """Vrai si au moins une alerte atteint un niveau bloquant (danger/critique).

    Les alertes produites par NutritionEngine stockent le niveau sous forme de
    chaîne ; AlertLevel hérite de str, la comparaison reste donc valide dans les
    deux sens.
    """
    return any(
        alert.get('level') in BLOCKING_ALERT_LEVELS
        for alert in alerts or []
    )


def _explain_why_better(orig_analysis: Dict, alt_analysis: Dict, 
                        orig_nutr: Dict, alt_nutr: Dict, hp: Dict) -> str:
    """Explique pourquoi l'alternative est meilleure"""
    
    reasons = []
    diseases = hp.get('diseases', [])
    
    # Comparaison IG (diabète)
    if DiseaseType.DIABETES.value in diseases:
        orig_gi = orig_nutr.get('glycemic_index', 0)
        alt_gi = alt_nutr.get('glycemic_index', 0)
        
        if orig_gi and alt_gi and alt_gi < orig_gi - 10:
            reasons.append(f"IG plus bas ({alt_gi} vs {orig_gi}) – prévient pics (HAS)")
    
    # Comparaison sodium (HTA/rénal/hépatique)
    if any(d in diseases for d in [DiseaseType.HYPERTENSION.value, DiseaseType.KIDNEY_DISEASE.value, DiseaseType.LIVER_DISEASE.value]):
        orig_sodium = orig_nutr.get('sodium_mg', 0)
        alt_sodium = alt_nutr.get('sodium_mg', 0)
        
        if orig_sodium and alt_sodium and alt_sodium < orig_sodium * 0.7:
            diff = orig_sodium - alt_sodium
            reasons.append(f"{diff:.0f}mg moins de sodium – réduit risques CV/rénaux (DASH/HAS)")
    
    # Fibres (hépatique/cancer/diabète)
    orig_fiber = orig_nutr.get('fiber_g', 0)
    alt_fiber = alt_nutr.get('fiber_g', 0)
    
    if orig_fiber and alt_fiber and alt_fiber > orig_fiber * 1.3:
        reasons.append(f"Plus riche en fibres ({alt_fiber:.1f}g) – détox et anti-cancer (WCRF)")
    
    # Potassium (HTA vs rénal)
    if DiseaseType.HYPERTENSION.value in diseases:
        orig_k = orig_nutr.get('potassium_mg', 0)
        alt_k = alt_nutr.get('potassium_mg', 0)
        if alt_k > orig_k + 200:
            reasons.append(f"+ potassium ({alt_k - orig_k:.0f}mg) – équilibre tension (FRHTA)")
    elif DiseaseType.KIDNEY_DISEASE.value in diseases and alt_nutr.get('potassium_mg', 0) < orig_nutr.get('potassium_mg', 0):
        reasons.append("Moins de potassium – protège reins (Ameli)")
    
    if reasons:
        return "Meilleur car : " + " ; ".join(reasons)
    else:
        return "Meilleur score global – plus équilibré (PNNS/WCRF)"


def _generate_modifications(nutr: Dict, hp: Dict) -> List[str]:
    """Génère des suggestions de modification pour le plat"""
    
    modifications = []
    diseases = hp.get('diseases', [])
    
    if DiseaseType.DIABETES.value in diseases:
        modifications.append("Ajouter légumes verts (brocoli) pour baisser IG effectif (HAS)")
        modifications.append("Remplacer féculents par quinoa/avoine – IG bas")
    
    if DiseaseType.HYPERTENSION.value in diseases:
        modifications.append("Cuisiner sans sel ; + herbes/citron pour saveur (DASH)")
        modifications.append("Ajouter avocat/banane pour potassium naturel")
    
    if DiseaseType.LIVER_DISEASE.value in diseases:
        modifications.append("Inclure artichaut/curcuma pour détox hépatique (AFE F)")
        modifications.append("Réduire graisses saturées ; + oméga-3 (poisson)")
    
    if DiseaseType.CANCER.value in diseases:
        modifications.append("Ajouter baies/tomates pour antioxydants (WCRF)")
        modifications.append("Éviter fritures ; opter vapeur/grill")
    
    if DiseaseType.KIDNEY_DISEASE.value in diseases:
        modifications.append("Limiter phosphore : - chocolat/fromages (HAS)")
        modifications.append("+ légumes alcalins (carottes) pour équilibre acide-base")
    
    return modifications if modifications else ["Adapter portions à besoins ; consulter diététicien"]


def _generate_ingredient_substitutions(ingredients: List, problems: List[str], hp: Dict) -> List[str]:
    """Génère des suggestions de substitution d'ingrédients"""
    
    substitutions = []
    diseases = hp.get('diseases', [])
    allergens = hp.get('allergens', [])
    
    ingredient_names = [ing.name.lower() for ing in ingredients]
    
    # Substitutions pour diabète
    if DiseaseType.DIABETES.value in diseases:
        if any('riz blanc' in name for name in ingredient_names):
            substitutions.append("Remplacer riz blanc par riz complet/quinoa – IG bas (HAS)")
        
        if any('pomme de terre' in name for name in ingredient_names):
            substitutions.append("Remplacer pomme de terre par patate douce – fibres + (HAS)")
    
    # Substitutions pour hypertension
    if DiseaseType.HYPERTENSION.value in diseases:
        if any('bouillon cube' in name or 'cube' in name for name in ingredient_names):
            substitutions.append("Remplacer cube Maggi par épices/herbes – réduit Na (DASH)")
        
        if any('sel' in name for name in ingredient_names):
            substitutions.append("Omettre sel ; + citron pour goût")
    
    # Substitutions pour hépatique
    if DiseaseType.LIVER_DISEASE.value in diseases:
        if any('huile palme' in name or 'graisse saturée' in name for name in ingredient_names):
            substitutions.append("Remplacer par huile olive – oméga-9 protecteur (méditerranéen)")
        
        if any('alcool' in name for name in ingredient_names):
            substitutions.append("Éviter alcool ; + thé vert détox")
    
    # Substitutions pour cancer
    if DiseaseType.CANCER.value in diseases:
        if any('viande rouge' in name for name in ingredient_names):
            substitutions.append("Remplacer par poisson/tofu – limite risque (WCRF)")
        
        if any('friture' in name for name in ingredient_names):
            substitutions.append("Opter bouilli/vapeur ; + curcuma anti-inflamm")
    
    # Substitutions pour rénal
    if DiseaseType.KIDNEY_DISEASE.value in diseases:
        if any('banane' in name or 'tomate' in name for name in ingredient_names):
            substitutions.append("Remplacer par pommes/poires – faible K (HAS)")
        
        if any('fromage' in name for name in ingredient_names):
            substitutions.append("Choisir versions faible P ; + protéines végétales modérées")
    
    # Substitutions pour allergènes
    if 'Arachides' in allergens:
        if any('arachide' in name for name in ingredient_names):
            substitutions.append("Remplacer huile arachide par olive/tournesol – éviction stricte (HAS)")
    
    if 'Lait (lactose)' in allergens:
        if any('lait' in name for name in ingredient_names):
            substitutions.append("Remplacer lait vache par amande/avoine sans additifs – variété nutriments")
    
    if 'Gluten (blé)' in allergens:
        if any('blé' in name or 'pain' in name for name in ingredient_names):
            substitutions.append("Remplacer par sarrasin/quinoa – sans gluten")
    
    if not substitutions:
        substitutions.append("Augmenter légumes ; réduire graisses pour équilibre général")
        substitutions.append("Variez sources protéines pour nutriments complets")
    
    return substitutions[:5]  # Limiter à 5 pour concision