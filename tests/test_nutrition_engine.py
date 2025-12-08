"""
Tests unitaires pour le moteur de règles nutritionnelles
"""
import pytest
from api.core.nutrition_engine import NutritionEngine


class TestNutritionEngine:
    """Tests pour le moteur de règles nutritionnelles"""
    
    @pytest.fixture
    def engine(self):
        """Fixture pour créer une instance du moteur"""
        return NutritionEngine()
    
    @pytest.fixture
    def sample_nutrition(self):
        """Données nutritionnelles d'exemple"""
        return {
            'energy_kcal': 250,
            'protein_g': 15,
            'fat_g': 8,
            'carbohydrate_g': 30,
            'fiber_g': 5,
            'sodium_mg': 400,
            'potassium_mg': 600,
            'glycemic_index': 55
        }
    
    @pytest.fixture
    def diabetic_profile(self):
        """Profil santé diabétique"""
        return {
            'user_id': 'test_user_1',
            'weight': 75,
            'physical_activity_level': 'moderate',
            'diseases': [{'name': 'diabetes_type2'}],
            'allergens': []
        }
    
    @pytest.fixture
    def hypertension_profile(self):
        """Profil santé hypertendu"""
        return {
            'user_id': 'test_user_2',
            'weight': 80,
            'physical_activity_level': 'light',
            'diseases': [{'name': 'hypertension'}],
            'allergens': []
        }
    
    def test_score_calculation_healthy_profile(self, engine, sample_nutrition):
        """Test calcul de score pour profil sain"""
        healthy_profile = {
            'user_id': 'test_user_3',
            'weight': 70,
            'physical_activity_level': 'moderate',
            'diseases': [],
            'allergens': []
        }
        
        result = engine.analyze(sample_nutrition, healthy_profile)
        
        assert 'score' in result
        assert 0 <= result['score'] <= 100
        assert result['alert_level'] in ['SAFE', 'WARNING', 'DANGER']
    
    def test_diabetic_low_gi_bonus(self, engine, diabetic_profile):
        """Test bonus pour IG bas chez diabétique"""
        low_gi_nutrition = {
            'energy_kcal': 200,
            'protein_g': 10,
            'fat_g': 5,
            'carbohydrate_g': 25,
            'fiber_g': 6,
            'sodium_mg': 300,
            'potassium_mg': 500,
            'glycemic_index': 40  # IG bas
        }
        
        result = engine.analyze(low_gi_nutrition, diabetic_profile)
        
        assert result['score'] >= 70  # Devrait être dans la zone safe
        assert any('glycémique' in p.lower() for p in result.get('positive_points', []))
    
    def test_diabetic_high_gi_penalty(self, engine, diabetic_profile):
        """Test pénalité pour IG élevé chez diabétique"""
        high_gi_nutrition = {
            'energy_kcal': 250,
            'protein_g': 8,
            'fat_g': 3,
            'carbohydrate_g': 50,
            'fiber_g': 2,
            'sodium_mg': 300,
            'potassium_mg': 400,
            'glycemic_index': 85  # IG élevé
        }
        
        result = engine.analyze(high_gi_nutrition, diabetic_profile)
        
        assert result['alert_level'] in ['WARNING', 'DANGER']
        assert any('glycémique' in p.lower() for p in result.get('problems', []))
    
    def test_hypertension_high_sodium_penalty(self, engine, hypertension_profile):
        """Test pénalité pour sodium élevé chez hypertendu"""
        high_sodium_nutrition = {
            'energy_kcal': 200,
            'protein_g': 12,
            'fat_g': 6,
            'carbohydrate_g': 20,
            'fiber_g': 4,
            'sodium_mg': 1200,  # Sodium très élevé
            'potassium_mg': 300,
            'glycemic_index': 50
        }
        
        result = engine.analyze(high_sodium_nutrition, hypertension_profile)
        
        assert result['alert_level'] in ['WARNING', 'DANGER']
        assert any('sodium' in p.lower() or 'sel' in p.lower() for p in result.get('problems', []))
    
    def test_hypertension_good_k_na_ratio(self, engine, hypertension_profile):
        """Test bonus pour bon ratio K/Na chez hypertendu"""
        good_ratio_nutrition = {
            'energy_kcal': 180,
            'protein_g': 10,
            'fat_g': 5,
            'carbohydrate_g': 20,
            'fiber_g': 5,
            'sodium_mg': 200,
            'potassium_mg': 800,  # Bon ratio K/Na
            'glycemic_index': 50
        }
        
        result = engine.analyze(good_ratio_nutrition, hypertension_profile)
        
        assert result['score'] >= 70
    
    def test_fiber_bonus(self, engine, sample_nutrition, diabetic_profile):
        """Test bonus pour fibres élevées"""
        high_fiber = sample_nutrition.copy()
        high_fiber['fiber_g'] = 10  # Fibres élevées
        
        result = engine.analyze(high_fiber, diabetic_profile)
        
        # Les fibres devraient améliorer le score
        assert any('fibre' in p.lower() for p in result.get('positive_points', []))
    
    def test_allergen_detection(self, engine, sample_nutrition):
        """Test détection d'allergènes"""
        profile_with_allergen = {
            'user_id': 'test_user_4',
            'weight': 70,
            'physical_activity_level': 'moderate',
            'diseases': [],
            'allergens': [{'name': 'peanuts'}]
        }
        
        # Simuler un plat avec allergène
        ingredients = [{'name': 'peanut butter'}]
        
        result = engine.analyze(sample_nutrition, profile_with_allergen, ingredients)
        
        # Devrait détecter l'allergène
        assert result['alert_level'] == 'DANGER'
        assert any('allergen' in p.lower() or 'allergène' in p.lower() for p in result.get('problems', []))
    
    def test_score_boundaries(self, engine, sample_nutrition, diabetic_profile):
        """Test que le score reste dans les limites 0-100"""
        result = engine.analyze(sample_nutrition, diabetic_profile)
        
        assert 0 <= result['score'] <= 100
    
    def test_alert_level_consistency(self, engine, sample_nutrition, diabetic_profile):
        """Test cohérence entre score et niveau d'alerte"""
        result = engine.analyze(sample_nutrition, diabetic_profile)
        
        score = result['score']
        alert_level = result['alert_level']
        
        if score >= 70:
            assert alert_level == 'SAFE'
        elif score >= 50:
            assert alert_level == 'WARNING'
        else:
            assert alert_level == 'DANGER'
    
    def test_multiple_diseases(self, engine, sample_nutrition):
        """Test avec profil ayant plusieurs maladies"""
        multi_disease_profile = {
            'user_id': 'test_user_5',
            'weight': 85,
            'physical_activity_level': 'light',
            'diseases': [
                {'name': 'diabetes_type2'},
                {'name': 'hypertension'}
            ],
            'allergens': []
        }
        
        result = engine.analyze(sample_nutrition, multi_disease_profile)
        
        # Devrait prendre en compte les deux maladies
        assert 'score' in result
        assert len(result.get('problems', [])) > 0 or len(result.get('warnings', [])) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
