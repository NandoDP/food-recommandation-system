from config import settings
import requests
import logging

# ==================== CONFIGURATION ====================

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def call_api(endpoint: str, method: str = 'GET', data: dict = None):
    """
    Appel générique à l'API backend.
    
    Args:
        endpoint (str): Endpoint de l'API (ex: '/health-profiles/{user_id}')
        method (str): Méthode HTTP ('GET', 'POST', 'PUT', 'DELETE')
        data (dict, optional): Données à envoyer dans la requête
        
    Returns:
        dict: Réponse JSON de l'API ou None en cas d'erreur
    """
    url = f"{settings.API_BASE_URL}{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, params=data, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        elif method == 'PUT':
            response = requests.put(url, json=data, timeout=10)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ API Error: {e}")
        return None

def get_user_profile(user_id: str):
    """Récupère le profil santé d'un utilisateur"""
    return call_api(f'/health-profiles/{user_id}', 'GET')

def create_user_profile(profile_data: dict):
    """
    Crée un profil santé complet pour un utilisateur.
    
    Args:
        profile_data (dict): Données du profil incluant user_id, first_name, last_name,
                           weight, physical_activity_level, diseases, allergens
                           
    Returns:
        dict: Profil créé ou None en cas d'erreur
    """
    user_data = {
        'id': profile_data['user_id'],
        'first_name': profile_data.get('first_name', ''),
        'last_name': profile_data.get('last_name', ''),
        'weight': profile_data.get('weight', None)
    }
    
    try:
        call_api('/users/register', 'POST', user_data)
        profile = call_api('/health-profiles', 'POST', {
            'user_id': profile_data['user_id'],
            'physical_activity_level': profile_data.get('physical_activity_level', 'moderate'),
        })
        
        for disease in profile_data.get('diseases', []):
            call_api(f'/health-profiles/{profile["id"]}/diseases', 'POST', {'disease_id': disease})
        for allergen in profile_data.get('allergens', []):
            call_api(f'/health-profiles/{profile["id"]}/allergens', 'POST', {'allergen_id': allergen})
        
        return profile
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        return None

def analyze_dish(dish_id: str, user_id: str):
    """Analyse un plat"""
    return call_api('/analyze-dish', 'POST', {
        'dish_id': dish_id,
        'user_id': user_id
    })

def analyze_menu_text(menu_text: str, user_id: str):
    """Analyse un menu depuis texte"""
    return call_api('/analyze-menu', 'POST', {
        'menu_text': menu_text,
        'user_id': user_id
    })

def get_recommendations(user_id: str, meal_type: str = None):
    """Obtient des recommandations"""
    params = {'limit': 5}
    if meal_type:
        params['meal_type'] = meal_type
    
    return call_api(f'/recommendations/{user_id}', 'GET', params)

def get_alternatives(dish_id: str, user_id: str):
    """Obtient alternatives pour un plat"""
    return call_api(f'/alternatives/{dish_id}', 'POST', {
        'user_id': user_id
    })

def get_dishes(meal_type: str = None, limit: int = 10):
    """Liste des plats disponibles"""
    params = {'limit': limit}
    if meal_type:
        params['meal_type'] = meal_type
    
    return call_api('/dishes', 'GET', params)

def get_dish_details(dish_id: str):
    """Détails d'un plat"""
    return call_api(f'/{dish_id}/dish_details', 'GET')

def get_alternatives(dish_id: str, user_id: str):
    """Obtient alternatives pour un plat"""
    return call_api(f'/alternatives/{dish_id}', 'POST', {
        'user_id': user_id
    })

def add_list_allergens_to_profile(user_id: str, allergens: list):
    """Ajoute une liste d'allergènes à un profil santé"""
    return call_api(f'/health-profiles/{user_id}/list_allergens', 'POST', allergens)

def delete_user_profile(user_id: str):
    """Supprime un profil santé"""
    return call_api(f'/users/{user_id}/health-profile', 'DELETE')