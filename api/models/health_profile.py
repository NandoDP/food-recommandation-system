from pydantic import BaseModel
from typing import List, Optional
# from uuid import UUID

class HealthProfileCreate(BaseModel):
    user_id: str
    intolerances: Optional[str] = None
    physical_activity_level: Optional[str] = None

class HealthProfileUpdate(BaseModel):
    intolerances: Optional[str] = None
    physical_activity_level: Optional[str] = None

class DiseaseAdd(BaseModel):
    disease_id: str

class AllergenAdd(BaseModel):
    allergen_id: str

class HealthProfileResponse(BaseModel):
    id: str
    user_id: str
    intolerances: Optional[str]
    physical_activity_level: Optional[str]
    diseases: List[str]
    allergens: List[str]

    class Config:
        orm_mode = True
