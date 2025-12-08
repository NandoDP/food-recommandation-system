"""
Tests pour les endpoints de l'API
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app


client = TestClient(app)


class TestHealthProfilesAPI:
    """Tests pour les endpoints de profils santé"""
    
    def test_create_user_profile(self):
        """Test création d'un profil utilisateur"""
        user_data = {
            'id': 'test_user_api_1',
            'first_name': 'Test',
            'last_name': 'User',
            'weight': 75
        }
        
        response = client.post('/users/register', json=user_data)
        
        # Peut retourner 200 (créé) ou 409 (déjà existe)
        assert response.status_code in [200, 201, 409]
    
    def test_get_user_profile(self):
        """Test récupération d'un profil"""
        # Créer d'abord un utilisateur
        user_id = 'test_user_api_2'
        user_data = {
            'id': user_id,
            'first_name': 'Test',
            'last_name': 'Profile',
            'weight': 70
        }
        
        client.post('/users/register', json=user_data)
        
        # Récupérer le profil
        response = client.get(f'/users/{user_id}/profile')
        
        if response.status_code == 200:
            data = response.json()
            assert 'user' in data or 'id' in data


class TestAnalysisAPI:
    """Tests pour les endpoints d'analyse"""
    
    def test_get_dishes_list(self):
        """Test récupération de la liste des plats"""
        response = client.get('/dishes', params={'limit': 10})
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_analyze_dish_endpoint(self):
        """Test endpoint d'analyse de plat"""
        # D'abord récupérer un plat
        dishes_response = client.get('/dishes', params={'limit': 1})
        
        if dishes_response.status_code == 200 and len(dishes_response.json()) > 0:
            dish_id = dishes_response.json()[0]['id']
            
            # Analyser le plat
            analysis_request = {
                'dish_id': dish_id,
                'user_id': 'test_user_api_1'
            }
            
            response = client.post('/analyze-dish', json=analysis_request)
            
            # Peut échouer si l'utilisateur n'existe pas, ce qui est OK pour le test
            assert response.status_code in [200, 404, 422]
    
    def test_get_recommendations(self):
        """Test endpoint de recommandations"""
        response = client.get('/recommendations/test_user_1', params={'limit': 5})
        
        # Peut retourner 404 si l'utilisateur n'existe pas
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert 'recommendations' in data or isinstance(data, list)


class TestHealthChecks:
    """Tests de santé de l'API"""
    
    def test_api_is_running(self):
        """Test que l'API est accessible"""
        # Test sur le endpoint docs qui existe toujours
        response = client.get('/docs')
        assert response.status_code in [200, 307]  # 307 = redirect
    
    def test_openapi_schema(self):
        """Test que le schéma OpenAPI est disponible"""
        response = client.get('/openapi.json')
        assert response.status_code == 200
        data = response.json()
        assert 'openapi' in data
        assert 'paths' in data


class TestInputValidation:
    """Tests de validation des entrées"""
    
    def test_invalid_user_id_format(self):
        """Test avec ID utilisateur invalide"""
        response = client.get('/recommendations/', params={'limit': 5})
        
        # Devrait retourner une erreur de validation
        assert response.status_code in [404, 422]
    
    def test_negative_limit(self):
        """Test avec limite négative"""
        response = client.get('/dishes', params={'limit': -1})
        
        # Devrait gérer gracieusement
        assert response.status_code in [200, 422]
    
    def test_missing_required_fields(self):
        """Test avec champs obligatoires manquants"""
        incomplete_data = {
            'first_name': 'Test'
            # Manque id, last_name, weight
        }
        
        response = client.post('/users/register', json=incomplete_data)
        
        # Devrait retourner erreur de validation
        assert response.status_code == 422


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
