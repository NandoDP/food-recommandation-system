from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class HealthProfileCreate(BaseModel):
    user_id: UUID
    intolerances: Optional[str] = None
    physical_activity_level: Optional[str] = None

class HealthProfileUpdate(BaseModel):
    intolerances: Optional[str] = None
    physical_activity_level: Optional[str] = None

class DiseaseAdd(BaseModel):
    disease_id: UUID

class AllergenAdd(BaseModel):
    allergen_id: UUID

class HealthProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    intolerances: Optional[str]
    physical_activity_level: Optional[str]
    diseases: List[str]
    allergens: List[str]

    class Config:
        orm_mode = True
