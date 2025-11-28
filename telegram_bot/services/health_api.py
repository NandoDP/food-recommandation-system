import requests
from ..config import FLASK_API_URL

def get_user_health_profile(user_id):
    url = f"{FLASK_API_URL}/health-profiles/{user_id}"
    r = requests.get(url)

    if r.status_code == 200:
        return r.json()
    return None

def get_nutritional_recommendations(user_id, food_name):
    url = f"{FLASK_API_URL}/nutrition/recommend"
    r = requests.post(url, json={"user_id": user_id, "food": food_name})

    if r.status_code == 200:
        return r.json()
    return {"message": "Impossible de récupérer la recommandation."}
