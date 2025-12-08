from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class AlertLevel(str, Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGER = "danger"
    CRITICAL = "critical"

# class AllergenAlert(BaseModel):
#     # type: str
#     allergen: str
#     level: AlertLevel
#     message: str
#     # details: Optional[Dict] = None

class Alert(BaseModel):
    name: str
    level: AlertLevel
    message: str
    
class DiseaseType(Enum):
    """Types de maladies supportées"""
    DIABETES = "Diabète Type 2"
    HYPERTENSION = "Hypertension artérielle"
    LIVER_DISEASE = "Maladie hépatique chronique"
    CANCER = "Cancer (en traitement)"
    KIDNEY_DISEASE = "Insuffisance rénale chronique"

class AnalysisResponse(BaseModel):
    score: int = Field(..., ge=0, le=100)
    name: str
    alert_level: AlertLevel
    allergen_alerts: List[Alert]
    disease_alerts: List[Alert]
    recommendations: List[str]
    alternatives: List[str]
    nutritional_summary: Dict[str, Any]
    detailed_breakdown: Dict[str, Any]

class DishAnalysisRequest(BaseModel):
    dish_id: str
    user_id: Optional[str] = None
    health_profile: Optional[Dict] = None

class MenuAnalysisRequest(BaseModel):
    menu_text: str
    user_id: Optional[str] = None
    health_profile: Optional[Dict] = None

class DishResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    meal_type: Optional[str]
    cuisine_origin: Optional[str]
    method: Optional[str]
    ingredients: List[str]
    ingredient_count: int

class FoodSearchResponse(BaseModel):
    id: str
    local_name: str
    category: Optional[str]
    glycemic_index: Optional[int]
    energy_kcal: Optional[float]


# ==================== RECOMMANDATIONS ====================

class RecommendedDish(BaseModel):
    dish_id: str
    dish_name: str
    score: int
    alert_level: AlertLevel
    meal_type: str
    reason: str
    nutritional_highlights: List[str]

class RecommendationsResponse(BaseModel):
    user_id: str
    recommendations: List[RecommendedDish]
    personalized_tips: List[str]
    count: int


# ==================== ALTERNATIVES ====================

class AlternativeDish(BaseModel):
    dish_id: str
    dish_name: str
    score: int
    alert_level: AlertLevel
    reason: str
    modifications: List[str]

class AlternativesResponse(BaseModel):
    original_dish_id: str
    original_dish_name: str
    original_score: int
    alternatives: List[AlternativeDish]
    substitution_suggestions: List[str]
