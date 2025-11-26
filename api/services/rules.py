"""
MOTEUR DE RÈGLES MÉTIER - SYSTÈME DE RECOMMANDATION ALIMENTAIRE
Implémente scoring, restrictions et alertes pour chaque maladie
"""

from typing import Dict, List, Tuple
from enum import Enum
import json

class AlertLevel(Enum):
    """Niveaux d'alerte"""
    SAFE = "safe"           # Vert
    CAUTION = "caution"     # Orange
    DANGER = "danger"       # Rouge
    CRITICAL = "critical"   # Rouge foncé

class DiseaseType(Enum):
    """Types de maladies supportées"""
    DIABETES = "Diabète Type 2"
    HYPERTENSION = "Hypertension artérielle"
    LIVER_DISEASE = "Maladie hépatique chronique"
    CANCER = "Cancer (en traitement)"
    KIDNEY_DISEASE = "Insuffisance rénale chronique"


class NutritionRulesEngine:
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
        'forbidden_keywords': [
            'sucre blanc', 'confiture', 'soda', 'bonbon', 
            'pâtisserie', 'pain blanc', 'riz blanc'
        ],
        'recommended_keywords': [
            'légume', 'légumineuse', 'lentille', 'haricot',
            'quinoa', 'avoine', 'patate douce'
        ]
    }
    
    # ========== RÈGLES HYPERTENSION ==========
    HYPERTENSION_RULES = {
        'sodium_max': 2000,     # mg/jour
        'sodium_per_meal': 667, # mg/repas (2000/3)
        'potassium_min': 3500,  # mg/jour recommandé
        'forbidden_keywords': [
            'sel', 'salé', 'cube maggi', 'bouillon cube',
            'charcuterie', 'fromage', 'anchois', 'olive'
        ],
        'recommended_keywords': [
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
        'hepatotoxic_keywords': [
            'alcool', 'paracétamol', 'champignon sauvage',
            'fructose élevé'
        ],
        'detox_keywords': [
            'artichaut', 'radis noir', 'citron', 'curcuma',
            'ail', 'betterave', 'pomme'
        ]
    }
    
    # ========== RÈGLES CANCER ==========
    CANCER_RULES = {
        'calorie_increase': 500,    # kcal/jour supplémentaires
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
    KIDNEY_RULES = {
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
    
    def analyze_dish(self, dish: Dict, health_profile: Dict) -> Dict:
        """
        Analyse complète d'un plat pour un profil santé
        
        Args:
            dish: {
                'name': str,
                'ingredients': [{'name': str, 'food_id': uuid, 'quantity': float}],
                'nutritional_summary': {...}  # calculé depuis ingredients
            }
            health_profile: {
                'diseases': [str],  # noms des maladies
                'allergens': [str], # noms des allergènes
                'weight': float,    # kg
                'activity_level': str
            }
        
        Returns:
            {
                'score': int (0-100),
                'alert_level': AlertLevel,
                'allergen_alerts': [...],
                'disease_alerts': [...],
                'recommendations': [str],
                'alternatives': [str]
            }
        """
        
        results = {
            'score': 100,
            'alert_level': AlertLevel.SAFE,
            'allergen_alerts': [],
            'disease_alerts': [],
            'recommendations': [],
            'alternatives': []
        }
        
        # 1. Vérifier allergènes
        allergen_score = self._check_allergens(
            dish, 
            health_profile.get('allergens', []), 
            results
        )
        
        # 2. Vérifier maladies
        disease_score = self._check_diseases(
            dish,
            health_profile.get('diseases', []),
            health_profile.get('weight', 70),
            results
        )
        
        # 3. Score nutritionnel général
        nutrition_score = self._check_nutrition_balance(dish, results)
        
        # 4. Calcul score final pondéré
        final_score = (
            allergen_score * self.weights['allergen'] +
            disease_score * self.weights['disease'] +
            nutrition_score * self.weights['nutrition']
        )
        
        results['score'] = int(final_score)
        results['alert_level'] = self._determine_alert_level(final_score)
        
        return results
    
    # ==================== VÉRIFICATION ALLERGÈNES ====================
    
    def _check_allergens(self, dish: Dict, user_allergens: List[str], 
                        results: Dict) -> float:
        """
        Vérifie présence d'allergènes
        Returns: score 0-100 (100 = aucun allergène)
        """
        
        if not user_allergens:
            return 100.0
        
        dish_ingredients = [ing['name'].lower() for ing in dish.get('ingredients', [])]
        dish_text = ' '.join(dish_ingredients + [dish['name'].lower()])
        
        # Mapping allergènes → mots-clés
        allergen_keywords = {
            'Arachides': ['arachide', 'peanut', 'cacahuète'],
            'Gluten (blé)': ['blé', 'wheat', 'farine', 'pain', 'couscous'],
            'Lait (lactose)': ['lait', 'milk', 'yaourt', 'fromage', 'beurre'],
            'Œufs': ['œuf', 'egg', 'oeuf'],
            'Poissons': ['poisson', 'fish', 'thiof', 'sardine'],
            'Crustacés': ['crustacé', 'crevette', 'crabe'],
            'Soja': ['soja', 'soy', 'tofu'],
            'Fruits à coque': ['noix', 'amande', 'cajou', 'noisette']
        }
        
        detected_allergens = []
        
        for allergen in user_allergens:
            keywords = allergen_keywords.get(allergen, [allergen.lower()])
            for keyword in keywords:
                if keyword in dish_text:
                    detected_allergens.append(allergen)
                    results['allergen_alerts'].append({
                        'allergen': allergen,
                        'level': AlertLevel.CRITICAL.value,
                        'message': f'⛔ ALLERGÈNE DÉTECTÉ : {allergen}'
                    })
                    break
        
        # Score : 0 si allergène trouvé, 100 sinon
        return 0.0 if detected_allergens else 100.0
    
    # ==================== VÉRIFICATION MALADIES ====================
    
    def _check_diseases(self, dish: Dict, user_diseases: List[str], 
                       weight: float, results: Dict) -> float:
        """
        Vérifie compatibilité avec maladies
        Returns: score moyen 0-100
        """
        
        if not user_diseases:
            return 100.0
        
        scores = []
        
        for disease in user_diseases:
            if disease == DiseaseType.DIABETES.value:
                score = self._check_diabetes(dish, results)
                scores.append(score)
            
            elif disease == DiseaseType.HYPERTENSION.value:
                score = self._check_hypertension(dish, results)
                scores.append(score)
            
            elif disease == DiseaseType.LIVER_DISEASE.value:
                score = self._check_liver_disease(dish, weight, results)
                scores.append(score)
            
            elif disease == DiseaseType.CANCER.value:
                score = self._check_cancer(dish, results)
                scores.append(score)
            
            elif disease == DiseaseType.KIDNEY_DISEASE.value:
                score = self._check_kidney_disease(dish, results)
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 100.0
    
    def _check_diabetes(self, dish: Dict, results: Dict) -> float:
        """Règles diabète"""
        score = 100.0
        nutr = dish.get('nutritional_summary', {})
        
        # 1. Index glycémique
        gi = nutr.get('glycemic_index', 60)
        if gi > self.DIABETES_RULES['gi_thresholds']['high']:
            score -= 30
            results['disease_alerts'].append({
                'disease': 'Diabète',
                'level': AlertLevel.DANGER.value,
                'message': f'🔴 IG élevé ({gi}) - Risque de pic glycémique'
            })
        elif gi > self.DIABETES_RULES['gi_thresholds']['medium']:
            score -= 15
            results['disease_alerts'].append({
                'disease': 'Diabète',
                'level': AlertLevel.CAUTION.value,
                'message': f'🟠 IG modéré ({gi}) - Consommer avec modération'
            })
        
        # 2. Glucides
        carbs = nutr.get('carbohydrate_g', 0)
        max_carbs = self.DIABETES_RULES['carbs_per_meal']['max']
        if carbs > max_carbs:
            score -= 20
            results['disease_alerts'].append({
                'disease': 'Diabète',
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
    
    def _check_hypertension(self, dish: Dict, results: Dict) -> float:
        """Règles hypertension"""
        score = 100.0
        nutr = dish.get('nutritional_summary', {})
        
        # Sodium
        sodium = nutr.get('sodium_mg', 0)
        max_sodium = self.HYPERTENSION_RULES['sodium_per_meal']
        
        if sodium > max_sodium:
            excess = sodium - max_sodium
            penalty = min(40, (excess / max_sodium) * 40)
            score -= penalty
            
            results['disease_alerts'].append({
                'disease': 'Hypertension',
                'level': AlertLevel.DANGER.value,
                'message': f'🔴 Sodium excessif ({sodium:.0f}mg > {max_sodium}mg/repas)'
            })
        elif sodium > max_sodium * 0.75:
            score -= 15
            results['disease_alerts'].append({
                'disease': 'Hypertension',
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
                'disease': 'Foie',
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
                    'disease': 'Cancer',
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
                'disease': 'Rein',
                'level': AlertLevel.DANGER.value,
                'message': f'🔴 Potassium excessif ({potassium:.0f}mg)'
            })
        
        # Sodium
        sodium = nutr.get('sodium_mg', 0)
        if sodium > 667:
            score -= 20
        
        return max(0, score)
    
    # ==================== ÉQUILIBRE NUTRITIONNEL ====================
    
    def _check_nutrition_balance(self, dish: Dict, results: Dict) -> float:
        """Évalue équilibre nutritionnel global"""
        score = 100.0
        nutr = dish.get('nutritional_summary', {})
        
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
    
    def _determine_alert_level(self, score: float) -> AlertLevel:
        """Détermine niveau d'alerte selon score"""
        if score >= 75:
            return AlertLevel.SAFE      # Vert
        elif score >= 50:
            return AlertLevel.CAUTION   # Orange
        elif score >= 25:
            return AlertLevel.DANGER    # Rouge
        else:
            return AlertLevel.CRITICAL  # Rouge foncé
    
    # ==================== GÉNÉRATION ALTERNATIVES ====================
    
    def suggest_alternatives(self, dish: Dict, health_profile: Dict) -> List[str]:
        """Suggère alternatives selon restrictions"""
        alternatives = []
        
        diseases = health_profile.get('diseases', [])
        
        if DiseaseType.DIABETES.value in diseases:
            alternatives.append("Remplacer riz blanc par quinoa ou riz basmati")
            alternatives.append("Ajouter légumes verts pour réduire IG")
        
        if DiseaseType.HYPERTENSION.value in diseases:
            alternatives.append("Cuisiner sans sel, assaisonner avec citron/herbes")
            alternatives.append("Éviter bouillon cube, utiliser épices naturelles")
        
        return alternatives


# ==================== EXEMPLE D'UTILISATION ====================

if __name__ == "__main__":
    # Initialisation
    engine = NutritionRulesEngine()
    
    # Exemple de plat
    dish = {
        'name': 'Thiéboudienne',
        'ingredients': [
            {'name': 'Riz blanc', 'quantity': 300},
            {'name': 'Poisson thiof', 'quantity': 200},
            {'name': 'Tomate', 'quantity': 100},
        ],
        'nutritional_summary': {
            'energy_kcal': 650,
            'protein_g': 35,
            'fat_g': 15,
            'carbohydrate_g': 85,
            'fiber_g': 4,
            'sodium_mg': 1200,
            'potassium_mg': 800,
            'glycemic_index': 75
        }
    }
    
    # Exemple de profil santé
    health_profile = {
        'diseases': ['Diabète Type 2', 'Hypertension artérielle'],
        'allergens': ['Arachides'],
        'weight': 75,
        'activity_level': 'moderate'
    }
    
    # Analyse
    results = engine.analyze_dish(dish, health_profile)
    
    # Affichage
    print("="*60)
    print(f"ANALYSE : {dish['name']}")
    print("="*60)
    print(f"\n🎯 Score de compatibilité : {results['score']}/100")
    print(f"🚦 Niveau d'alerte : {results['alert_level'].value.upper()}")
    
    if results['allergen_alerts']:
        print("\n⚠️ ALERTES ALLERGÈNES :")
        for alert in results['allergen_alerts']:
            print(f"   {alert['message']}")
    
    if results['disease_alerts']:
        print("\n🏥 ALERTES MALADIES :")
        for alert in results['disease_alerts']:
            print(f"   {alert['message']}")
    
    if results['recommendations']:
        print("\n💡 RECOMMANDATIONS :")
        for rec in results['recommendations']:
            print(f"   {rec}")