from typing import List, Dict
from api.models.analyze import AlertLevel, DiseaseType


class NutritionEngine:    
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
        'forbidden_keywords': [   # aliments à éviter: IG élevé, sucres rapides
            'sucre blanc', 'confiture', 'soda', 'bonbon', 
            'pâtisserie', 'pain blanc', 'riz blanc', 'pâtes blanches',
            'pommes de terre frites', 'gâteaux', 'viennoiseries',
            'fruits secs sucrés', 'cerises', 'mangue', 'banane mûre',
            'jus de fruits', 'sirop de glucose-fructose', 'sodas sucrés'
        ],
        'recommended_keywords': [   # aliments recommandés: IG bas, fibres
            'légume', 'légumineuse', 'lentille', 'haricot',
            'quinoa', 'avoine', 'patate douce', 'céréales complètes',
            'riz complet', 'brocoli', 'courgette', 'tofu',
            'baies', 'fraises', 'framboises', 'myrtilles'
        ]
    }
    
    # ========== RÈGLES HYPERTENSION ==========
    HYPERTENSION_RULES = {
        'sodium_max': 2000,     # mg/jour
        'sodium_per_meal': 667, # mg/repas (2000/3)
        'potassium_min': 3500,  # mg/jour recommandé
        'forbidden_keywords': [   # aliments à éviter: riches en sodium
            'sel', 'salé', 'cube maggi', 'bouillon cube',
            'charcuterie', 'fromage', 'anchois', 'olive',
            'poisson fumé', 'conserves', 'plats préparés',
            'chips', 'biscuits salés', 'sauce soja',
            'jambon industriel', 'saucisses', 'pizzas surgelées'
        ],
        'recommended_keywords': [   # aliments recommandés: riches en potassium
            'banane', 'avocat', 'épinard', 'patate douce',
            'haricot', 'tomate', 'orange', 'poisson gras',
            'huile d\'olive', 'noix', 'légumes verts',
            'fruits frais', 'céréales complètes'
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
        'hepatotoxic_keywords': [     # aliments à éviter: graisses, fructose, toxiques
            'alcool', 'paracétamol', 'champignon sauvage',
            'fructose élevé', 'viandes grasses', 'fritures',
            'sodas', 'jus sucrés', 'fruits secs sucrés',
            'graisses saturées', 'huile de palme', 'pâtés'
        ],
        'detox_keywords': [       # aliments recommandés: détoxifiants
            'artichaut', 'radis noir', 'citron', 'curcuma',
            'ail', 'betterave', 'pomme', 'chardon-marie',
            'oignon', 'thé vert', 'légumes crucifères',
            'poisson gras', 'noix'
        ]
    }
    
    # ========== RÈGLES CANCER ==========
    CANCER_RULES = {
        'calorie_increase': 500,    # kcal/jour supplémentaires
        'protein_per_kg': 1.5,      # g/kg (besoins augmentés)
        'avoid_keywords': [
            'ultra-transformé', 'charcuterie', 'viande rouge',
            'sucre raffiné', 'friture', 'barbecue',
            'alcool', 'sodas', 'viandes transformées',
            'saucisses', 'bacon', 'pizzas surgelées',
            'biscuits', 'gâteaux industriels'
        ],
        'anti_inflammatory_keywords': [
            'curcuma', 'gingembre', 'thé vert', 'baies',
            'poisson gras', 'noix', 'légume crucifère',
            'tomate', 'ail', 'oignon', 'fruits rouges',
            'légumes verts', 'épinards', 'brocoli'
        ]
    }
    
    # ========== RÈGLES INSUFFISANCE RÉNALE ==========
    KIDNEY_RULES = {   # pour maladie rénale chronique
        'sodium_max': 2000,         # mg/jour
        'potassium_max': 2000,      # mg/jour
        'phosphorus_max': 1000,     # mg/jour
        'protein_per_kg': 0.8,      # g/kg
        'restrict_keywords': [
            'banane', 'avocat', 'orange', 'tomate',
            'produit laitier', 'noix', 'chocolat',
            'pommes de terre', 'légumes secs', 'poisson fumé',
            'fromages', 'sodas', 'charcuterie'
        ]
    }
    
    # ========== INITIALISATION ==========
    def __init__(self):
        """Initialisation du moteur"""
        self.weights = {
            'allergen': 0.40,      # 40% du score
            'disease': 0.35,       # 35% du score
            'nutrition': 0.25      # 25% du score
        }
    
    # ==================== ANALYSE PLAT ====================
    
    def analyze(self, dish_data: Dict, health_profile: Dict) -> Dict:
        """Analyse complète d'un plat"""
        
        results = {
            'name': dish_data.get('name', 'Plat inconnu'),
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
            'Gluten (blé)': ['blé', 'wheat', 'farine', 'pain', 'avoine', 'orge', 'couscous', 'spaghetti'],
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
    
    def _check_diseases(self, dish_data: Dict, diseases: List[str], weight: float, results: Dict) -> float:
        """Vérifie compatibilité maladies"""
        if not diseases:
            return 100.0
        
        scores = []
        nutr = dish_data.get('nutritional_summary', {})
        dish_text = dish_data['name'].lower()  # Pour scan mots-clés
        
        for disease in diseases:
            if disease == DiseaseType.DIABETES.value:
                score = self._check_diabetes(nutr, dish_text, results)
                scores.append(score)
            
            elif disease == DiseaseType.HYPERTENSION.value:
                score = self._check_hypertension(nutr, dish_text, results)
                scores.append(score)
            
            elif disease == DiseaseType.LIVER_DISEASE.value:
                score = self._check_liver_disease(dish_data, weight, dish_text, results)
                scores.append(score)
            
            elif disease == DiseaseType.CANCER.value:
                score = self._check_cancer(dish_data, dish_text, results)
                scores.append(score)
            
            elif disease == DiseaseType.KIDNEY_DISEASE.value:
                score = self._check_kidney_disease(dish_data, dish_text, results)
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 100.0
    
    def _check_diabetes(self, nutr: Dict, dish_text: str, results: Dict) -> float:
        """Règles diabète - inclut scan mots-clés"""
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
        
        # 4. Scan mots-clés forbidden
        for keyword in self.DIABETES_RULES['forbidden_keywords']:
            if keyword in dish_text:
                score -= 15
                results['disease_alerts'].append({
                    'name': 'Diabète',
                    'level': AlertLevel.CAUTION.value,
                    'message': f'🟠 Aliment à IG élevé détecté: {keyword}'
                })
                break  # Pénalité une fois par plat
        
        return max(0, score)
    
    def _check_hypertension(self, nutr: Dict, dish_text: str, results: Dict) -> float:
        """Règles hypertension - inclut scan mots-clés"""
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
        
        # Scan mots-clés forbidden
        for keyword in self.HYPERTENSION_RULES['forbidden_keywords']:
            if keyword in dish_text:
                score -= 20
                results['disease_alerts'].append({
                    'name': 'Hypertension',
                    'level': AlertLevel.DANGER.value,
                    'message': f'🔴 Aliment riche en sodium détecté: {keyword}'
                })
                break
        
        return max(0, score)
    
    def _check_liver_disease(self, dish: Dict, weight: float, dish_text: str, results: Dict) -> float:
        """Règles maladie hépatique - inclut scan mots-clés"""
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
        
        # Scan mots-clés hepatotoxiques
        for keyword in self.LIVER_RULES['hepatotoxic_keywords']:
            if keyword in dish_text:
                score -= 25
                results['disease_alerts'].append({
                    'name': 'Foie',
                    'level': AlertLevel.DANGER.value,
                    'message': f'🔴 Aliment hépatotoxique détecté: {keyword}'
                })
                break
        
        return max(0, score)
    
    def _check_cancer(self, dish: Dict, dish_text: str, results: Dict) -> float:
        """Règles cancer - inclut scan mots-clés"""
        score = 100.0
        
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
                score += 10  # Bonus mineur
                break
        
        return max(0, score)
    
    def _check_kidney_disease(self, dish: Dict, dish_text: str, results: Dict) -> float:
        """Règles insuffisance rénale - inclut scan mots-clés"""
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
        
        # Scan mots-clés restrictifs (phosphore, potassium)
        for keyword in self.KIDNEY_RULES['restrict_keywords']:
            if keyword in dish_text:
                score -= 25
                results['disease_alerts'].append({
                    'name': 'Rein',
                    'level': AlertLevel.DANGER.value,
                    'message': f'🔴 Aliment restrictif détecté: {keyword} (riche en K/P)'
                })
                break
        
        return max(0, score)
    
    # ==================== ÉQUILIBRE NUTRITIONNEL ====================
    
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











# from sqlalchemy.orm import Session, joinedload
# from typing import List, Dict
# from api.models.analyze import AlertLevel, DiseaseType


# class NutritionEngine:    
#     """
#     Moteur de règles nutritionnelles
#     Calcule scores de compatibilité et génère alertes
#     """
    
#     # ========== RÈGLES DIABÈTE ==========
#     DIABETES_RULES = {
#         'gi_thresholds': {
#             'low': 55,      # IG < 55 : favorable
#             'medium': 70,   # IG 55-70 : modéré
#             'high': 70      # IG > 70 : défavorable
#         },
#         'carbs_per_meal': {
#             'min': 45,      # g
#             'max': 60,      # g
#             'optimal': 50   # g
#         },
#         'fiber_min': 5,     # g par repas minimum
#         'forbidden_keywords': [   # aliments à éviter: TODO
#             'sucre blanc', 'confiture', 'soda', 'bonbon', 
#             'pâtisserie', 'pain blanc', 'riz blanc'
#         ],
#         'recommended_keywords': [   # aliments recommandés: TODO
#             'légume', 'légumineuse', 'lentille', 'haricot',
#             'quinoa', 'avoine', 'patate douce'
#         ]
#     }
    
#     # ========== RÈGLES HYPERTENSION ==========
#     HYPERTENSION_RULES = {
#         'sodium_max': 2000,     # mg/jour
#         'sodium_per_meal': 667, # mg/repas (2000/3)
#         'potassium_min': 3500,  # mg/jour recommandé
#         'forbidden_keywords': [   # aliments à éviter: TODO
#             'sel', 'salé', 'cube maggi', 'bouillon cube',
#             'charcuterie', 'fromage', 'anchois', 'olive'
#         ],
#         'recommended_keywords': [   # aliments recommandés: TODO
#             'banane', 'avocat', 'épinard', 'patate douce',
#             'haricot', 'tomate', 'orange'
#         ]
#     }
    
#     # ========== RÈGLES MALADIE HÉPATIQUE ==========
#     LIVER_RULES = {
#         'sodium_max': 2000,         # mg/jour
#         'protein_per_kg': {
#             'normal': 1.0,           # g/kg poids corporel
#             'decompensated': 0.8,    # stade décompensé
#             'encephalopathy': 0.6    # encéphalopathie
#         },
#         'avoid_alcohol': True,
#         'hepatotoxic_keywords': [     # aliments à éviter: TODO
#             'alcool', 'paracétamol', 'champignon sauvage',
#             'fructose élevé'
#         ],
#         'detox_keywords': [       # aliments recommandés: TODO
#             'artichaut', 'radis noir', 'citron', 'curcuma',
#             'ail', 'betterave', 'pomme'
#         ]
#     }
    
#     # ========== RÈGLES CANCER ==========
#     CANCER_RULES = {
#         'calorie_increase': 500,    # kcal/jour supplémentaires: TODO
#         'protein_per_kg': 1.5,      # g/kg (besoins augmentés)
#         'avoid_keywords': [
#             'ultra-transformé', 'charcuterie', 'viande rouge',
#             'sucre raffiné', 'friture', 'barbecue'
#         ],
#         'anti_inflammatory_keywords': [
#             'curcuma', 'gingembre', 'thé vert', 'baies',
#             'poisson gras', 'noix', 'légume crucifère',
#             'tomate', 'ail', 'oignon'
#         ]
#     }
    
#     # ========== RÈGLES INSUFFISANCE RÉNALE ==========
#     KIDNEY_RULES = {   # pour maladie rénale chronique: TODO
#         'sodium_max': 2000,         # mg/jour
#         'potassium_max': 2000,      # mg/jour
#         'phosphorus_max': 1000,     # mg/jour
#         'protein_per_kg': 0.8,      # g/kg
#         'restrict_keywords': [
#             'banane', 'avocat', 'orange', 'tomate',
#             'produit laitier', 'noix', 'chocolat'
#         ]
#     }
    
#     # ========== INITIALISATION ==========
#     def __init__(self):
#         """Initialisation du moteur"""
#         self.weights = {
#             'allergen': 0.40,      # 40% du score
#             'disease': 0.35,       # 35% du score
#             'nutrition': 0.25      # 25% du score
#         }
    
#     # ==================== ANALYSE PLAT ====================
    
#     def analyze(self, dish_data: Dict, health_profile: Dict) -> Dict:
#         """Analyse complète d'un plat"""
        
#         results = {
#             'name': dish_data.get('name', 'Plat inconnu'),
#             'score': 100,
#             'alert_level': AlertLevel.SAFE,
#             'allergen_alerts': [],
#             'disease_alerts': [],
#             'recommendations': [],
#             'alternatives': [],
#             'nutritional_summary': dish_data.get('nutritional_summary', {}),
#             'detailed_breakdown': {
#                 'allergen_score': 100,
#                 'disease_score': 100,
#                 'nutrition_score': 100
#             }
#         }
        
#         # 1. Vérifier allergènes
#         allergen_score = self._check_allergens(
#             dish_data, 
#             health_profile.get('allergens', []),
#             results
#         )
#         results['detailed_breakdown']['allergen_score'] = allergen_score
        
#         # 2. Vérifier maladies
#         disease_score = self._check_diseases(
#             dish_data,
#             health_profile.get('diseases', []),
#             health_profile.get('weight', 70),
#             results
#         )
#         results['detailed_breakdown']['disease_score'] = disease_score
        
#         # 3. Équilibre nutritionnel
#         nutrition_score = self._check_nutrition(dish_data, results)
#         results['detailed_breakdown']['nutrition_score'] = nutrition_score
        
#         # 4. Score final pondéré
#         final_score = (
#             allergen_score * self.weights['allergen'] +
#             disease_score * self.weights['disease'] +
#             nutrition_score * self.weights['nutrition']
#         )
        
#         results['score'] = int(final_score)
#         results['alert_level'] = self._get_alert_level(final_score)
        
#         return results
    
#     # ==================== VÉRIFICATION ALLERGÈNES ====================
    
#     def _check_allergens(self, dish_data: Dict, user_allergens: List[str], results: Dict) -> float:
#         """Vérifie présence d'allergènes"""
#         if not user_allergens:
#             return 100.0
        
#         dish_text = dish_data['name'].lower()
#         for ing in dish_data.get('ingredients', []):
#             dish_text += ' ' + ing.get('name', '').lower()
        
#         allergen_keywords = {
#             'Arachides': ['arachide', 'peanut', 'cacahuète'],
#             'Crustacés': ['crustacé', 'crabe', 'crevette', 'shrimp'],
#             'Gluten (blé)': ['blé', 'wheat', 'farine', 'pain', 'avoine', 'orge', 'couscous', 'spaghetti'],
#             'Lait (lactose)': ['lait', 'milk', 'yaourt', 'fromage', 'beurre'],
#             'Œufs': ['œuf', 'egg', 'oeuf'],
#             'Poissons': ['poisson', 'fish', 'thiof', 'sardine', 'saumon', 'truite'],
#             'Fruits à coque': ['noix', 'amande', 'noisette', 'pistache', 'cashew', 'walnut', 'cajou'],
#             'Moutarde': ['moutarde', 'mustard', 'cornichon', 'bouillon-cube', 'mayonnaise'],
#             'Soja': ['soja', 'soy', 'tofu'],
#             'Sésame': ['sésame', 'sesame', 'tahini', 'gomasio'],
#         }
        
#         detected_allergens = []
        
#         for allergen in user_allergens:
#             keywords = allergen_keywords.get(allergen, [allergen.lower()])
#             for keyword in keywords:
#                 if keyword in dish_text:
#                     detected_allergens.append(allergen)
#                     results['allergen_alerts'].append({
#                         'name': allergen,
#                         'level': AlertLevel.CRITICAL.value,
#                         'message': f'⛔ ALLERGÈNE DÉTECTÉ : {allergen}'
#                     })
#                     break
        
#         # Score : 0 si allergène trouvé, 100 sinon
#         return 0.0 if detected_allergens else 100.0
    
#     # ==================== VÉRIFICATION MALADIES ====================
    
#     def _check_diseases(self, dish_data: Dict, diseases: List[str], weight: float, results: Dict) -> float:
#         """Vérifie compatibilité maladies"""
#         if not diseases:
#             return 100.0
        
#         scores = []
#         nutr = dish_data.get('nutritional_summary', {})
        
#         for disease in diseases:
#             if disease == DiseaseType.DIABETES.value:
#                 score = self._check_diabetes(nutr, results)
#                 scores.append(score)
            
#             elif disease == DiseaseType.HYPERTENSION.value:
#                 score = self._check_hypertension(nutr, results)
#                 scores.append(score)
            
#             elif disease == DiseaseType.LIVER_DISEASE.value:
#                 score = self._check_liver_disease(nutr, weight, results)
#                 scores.append(score)
            
#             elif disease == DiseaseType.CANCER.value:
#                 score = self._check_cancer(nutr, results)
#                 scores.append(score)
            
#             elif disease == DiseaseType.KIDNEY_DISEASE.value:
#                 score = self._check_kidney_disease(nutr, results)
#                 scores.append(score)
        
#         return sum(scores) / len(scores) if scores else 100.0
    
#     def _check_diabetes(self, nutr: Dict, results: Dict) -> float:
#         """Règles diabète"""
#         score = 100.0
        
#          # 1. Index glycémique
#         gi = nutr.get('glycemic_index', 60)
#         if gi > self.DIABETES_RULES['gi_thresholds']['high']:
#             score -= 30
#             results['disease_alerts'].append({
#                 'name': 'Diabète',
#                 'level': AlertLevel.DANGER.value,
#                 'message': f'🔴 IG élevé ({gi}) - Risque de pic glycémique'
#             })
#         elif gi > self.DIABETES_RULES['gi_thresholds']['medium']:
#             score -= 15
#             results['disease_alerts'].append({
#                 'name': 'Diabète',
#                 'level': AlertLevel.CAUTION.value,
#                 'message': f'🟠 IG modéré ({gi}) - Consommer avec modération'
#             })
        
#         # 2. Glucides
#         carbs = nutr.get('carbohydrate_g', 0)
#         max_carbs = self.DIABETES_RULES['carbs_per_meal']['max']
#         if carbs > max_carbs:
#             score -= 20
#             results['disease_alerts'].append({
#                 'name': 'Diabète',
#                 'level': AlertLevel.DANGER.value,
#                 'message': f'🔴 Glucides excessifs ({carbs:.1f}g > {max_carbs}g)'
#             })
        
#         # 3. Fibres
#         fiber = nutr.get('fiber_g', 0)
#         if fiber < self.DIABETES_RULES['fiber_min']:
#             score -= 10
#             results['recommendations'].append(
#                 f'💡 Ajouter plus de fibres (actuel: {fiber:.1f}g, min: {self.DIABETES_RULES["fiber_min"]}g)'
#             )
        
#         return max(0, score)
    
#     def _check_hypertension(self, nutr: Dict, results: Dict) -> float:
#         """Règles hypertension"""
#         score = 100.0
        
#         # Sodium
#         sodium = nutr.get('sodium_mg', 0)
#         max_sodium = self.HYPERTENSION_RULES['sodium_per_meal']
        
#         if sodium > max_sodium:
#             excess = sodium - max_sodium
#             penalty = min(40, (excess / max_sodium) * 40)
#             score -= penalty
            
#             results['disease_alerts'].append({
#                 'name': 'Hypertension',
#                 'level': AlertLevel.DANGER.value,
#                 'message': f'🔴 Sodium excessif ({sodium:.0f}mg > {max_sodium}mg/repas)'
#             })
#         elif sodium > max_sodium * 0.75:
#             score -= 15
#             results['disease_alerts'].append({
#                 'name': 'Hypertension',
#                 'level': AlertLevel.CAUTION.value,
#                 'message': f'🟠 Sodium élevé ({sodium:.0f}mg)'
#             })
        
#         return max(0, score)
    
#     def _check_liver_disease(self, dish: Dict, weight: float, results: Dict) -> float:
#         """Règles maladie hépatique"""
#         score = 100.0
#         nutr = dish.get('nutritional_summary', {})
        
#         # 1. Sodium (même règle qu'hypertension)
#         sodium = nutr.get('sodium_mg', 0)
#         if sodium > 667:  # 2000mg/3 repas
#             score -= 25
#             results['disease_alerts'].append({
#                 'name': 'Foie',
#                 'level': AlertLevel.DANGER.value,
#                 'message': f'🔴 Sodium excessif - Risque de rétention d\'eau'
#             })
        
#         # 2. Protéines (vérifier si excessif)
#         protein = nutr.get('protein_g', 0)
#         max_protein = weight * self.LIVER_RULES['protein_per_kg']['normal']
#         if protein > max_protein / 3:  # Par repas
#             score -= 15
#             results['recommendations'].append(
#                 f'⚠️ Protéines à modérer selon stade hépatique'
#             )
        
#         return max(0, score)
    
#     def _check_cancer(self, dish: Dict, results: Dict) -> float:
#         """Règles cancer"""
#         score = 100.0
        
#         dish_text = dish['name'].lower()
        
#         # Vérifier aliments à éviter
#         for keyword in self.CANCER_RULES['avoid_keywords']:
#             if keyword in dish_text:
#                 score -= 20
#                 results['disease_alerts'].append({
#                     'name': 'Cancer',
#                     'level': AlertLevel.CAUTION.value,
#                     'message': f'🟠 Éviter : {keyword}'
#                 })
#                 break
        
#         # Bonus pour anti-inflammatoires
#         for keyword in self.CANCER_RULES['anti_inflammatory_keywords']:
#             if keyword in dish_text:
#                 results['recommendations'].append(
#                     f'✅ Contient {keyword} (anti-inflammatoire)'
#                 )
#                 break
        
#         return max(0, score)
    
#     def _check_kidney_disease(self, dish: Dict, results: Dict) -> float:
#         """Règles insuffisance rénale"""
#         score = 100.0
#         nutr = dish.get('nutritional_summary', {})
        
#         # Potassium
#         potassium = nutr.get('potassium_mg', 0)
#         if potassium > 667:  # 2000mg/3 repas
#             score -= 30
#             results['disease_alerts'].append({
#                 'name': 'Rein',
#                 'level': AlertLevel.DANGER.value,
#                 'message': f'🔴 Potassium excessif ({potassium:.0f}mg)'
#             })
        
#         # Sodium
#         sodium = nutr.get('sodium_mg', 0)
#         if sodium > 667:
#             score -= 20
        
#         return max(0, score)
    
#     # ==================== ÉQUILIBRE NUTRITIONNEL ====================
    
#     def _check_nutrition(self, dish_data: Dict, results: Dict) -> float:
#         """Équilibre nutritionnel"""
#         score = 100.0
#         nutr = dish_data.get('nutritional_summary', {})
        
#         protein = nutr.get('protein_g', 0)
#         fat = nutr.get('fat_g', 0)
#         carbs = nutr.get('carbohydrate_g', 0)
        
#         total = protein + fat + carbs
#         if total == 0:
#             return 50.0  # Pas assez de données
        
#         # Ratios recommandés (% calories)
#         protein_pct = (protein * 4) / ((protein * 4) + (fat * 9) + (carbs * 4)) * 100
#         fat_pct = (fat * 9) / ((protein * 4) + (fat * 9) + (carbs * 4)) * 100
        
#         # Protéines : 15-25%
#         if protein_pct < 10:
#             score -= 15
#             results['recommendations'].append('💡 Augmenter apport en protéines')
#         elif protein_pct > 35:
#             score -= 10
        
#         # Lipides : 25-35%
#         if fat_pct > 40:
#             score -= 15
#             results['recommendations'].append('💡 Réduire matières grasses')
        
#         return max(0, score)
    
#     # ==================== NIVEAU D'ALERTE ====================
    
#     def _get_alert_level(self, score: float) -> AlertLevel:
#         """Détermine niveau d'alerte"""
#         if score >= 75:
#             return AlertLevel.SAFE
#         elif score >= 50:
#             return AlertLevel.CAUTION
#         elif score >= 25:
#             return AlertLevel.DANGER
#         else:
#             return AlertLevel.CRITICAL

# # ==================== HELPER FUNCTIONS ====================

# def get_user_health_profile(user_id: str, db: Session) -> Dict:
#     """Récupère le profil santé complet d'un utilisateur"""
#     from api.routes.users import get_user_profile
    
#     profile = get_user_profile(user_id, db)
#     health_profile = profile['health']
#     health_profile['weight'] = profile.get("user").get('weight', 70)
    
#     return health_profile

# def calculate_dish_nutrition(dish_id: str, db: Session) -> Dict:
#     """Calcule le résumé nutritionnel d'un plat à partir de ses ingrédients"""
#     from api.schemas.analyze import DishIngredient, Ingredient, Food
    
#     # Récupérer ingrédients avec foods
#     dish_ingredients = db.query(DishIngredient).options(
#         joinedload(DishIngredient.ingredient).joinedload(Ingredient.food)
#     ).filter(DishIngredient.dish_id == dish_id).all()
    
#     nutritional_summary = {
#         'energy_kcal': 0,
#         'protein_g': 0,
#         'fat_g': 0,
#         'carbohydrate_g': 0,
#         'fiber_g': 0,
#         'sodium_mg': 0,
#         'potassium_mg': 0,
#         'glycemic_index': None
#     }
    
#     gi_values = []
    
#     for di in dish_ingredients:
#         if di.ingredient and di.ingredient.food:
#             food = di.ingredient.food
#             nutr_values = food.nutritional_values or {}
            
#             # Facteur de quantité (normaliser à 100g)
#             qty_factor = (di.quantity or 100) / 100
            
#             # Cumuler les nutriments
#             nutritional_summary['energy_kcal'] += (nutr_values.get('energy_kcal', 0) or 0) * qty_factor
#             nutritional_summary['protein_g'] += (nutr_values.get('protein_g', 0) or 0) * qty_factor
#             nutritional_summary['fat_g'] += (nutr_values.get('fat_g', 0) or 0) * qty_factor
#             nutritional_summary['carbohydrate_g'] += (nutr_values.get('carbohydrate_g', 0) or 0) * qty_factor
#             nutritional_summary['fiber_g'] += (nutr_values.get('fiber_g', 0) or 0) * qty_factor
#             nutritional_summary['sodium_mg'] += (nutr_values.get('sodium_mg', 0) or 0) * qty_factor
#             nutritional_summary['potassium_mg'] += (nutr_values.get('potassium_mg', 0) or 0) * qty_factor
            
#             # Collecter IG pour moyenne pondérée
#             if food.glycemic_index:
#                 gi_values.append((food.glycemic_index, di.quantity or 100))
    
#     # Calculer IG moyen pondéré
#     if gi_values:
#         total_qty = sum(qty for gi, qty in gi_values)
#         weighted_gi = sum(gi * qty for gi, qty in gi_values) / total_qty
#         nutritional_summary['glycemic_index'] = int(weighted_gi)
#     else:
#         nutritional_summary['glycemic_index'] = 65  # Valeur par défaut
    
#     return nutritional_summary
