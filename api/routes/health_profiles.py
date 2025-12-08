from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
# from uuid import UUID

from api.schemas.users import HealthProfile, Disease, Allergen, User
from api.core.database import Database

from api.models.health_profile import (
    HealthProfileCreate,
    HealthProfileUpdate,
    DiseaseAdd,
    AllergenAdd,
)

db_instance = Database()

router = APIRouter(prefix="/health-profiles", tags=["Health Profiles"])

@router.get("/diseases")
def list_diseases(db: Session = Depends(db_instance.get_db)):
    diseases = db.query(Disease).all()
    return [{"id": d.id, "name": d.name, "description": d.description} for d in diseases]

@router.get("/allergens")
def list_allergens(db: Session = Depends(db_instance.get_db)):
    allergens = db.query(Allergen).all()
    return [{"id": a.id, "name": a.name, "category": a.category} for a in allergens]

@router.post("/", status_code=201)
def create_health_profile(payload: HealthProfileCreate, db: Session = Depends(db_instance.get_db)):
    # vérifier si l'utilisateur existe
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Vérifier si profil existe déjà
    existing = db.query(HealthProfile).filter(HealthProfile.user_id == payload.user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Health profile already exists for this user")

    profile = HealthProfile(
        user_id=payload.user_id,
        # intolerances = payload.intolerances,
        physical_activity_level = payload.physical_activity_level
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {"message": "Health profile created", "id": str(profile.id)}



@router.get("/{user_id}")
def get_health_profile(user_id: str, db: Session = Depends(db_instance.get_db)):
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")

    return {
        "id": profile.id,
        "user_id": profile.user_id,
        # "intolerances": profile.intolerances,
        "physical_activity_level": profile.physical_activity_level,
        "diseases": [d.name for d in profile.diseases],
        "allergens": [a.name for a in profile.allergens]
    }


@router.put("/{id}")
def update_health_profile(id: str, payload: HealthProfileUpdate, db: Session = Depends(db_instance.get_db)):
    profile = db.query(HealthProfile).filter(HealthProfile.id == id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")

    # if payload.intolerances is not None:
    #     profile.intolerances = payload.intolerances

    if payload.physical_activity_level is not None:
        profile.physical_activity_level = payload.physical_activity_level

    db.commit()
    db.refresh(profile)

    return {"message": "Health profile updated"}


@router.post("/{id}/diseases")
def add_disease(id: str, payload: DiseaseAdd, db: Session = Depends(db_instance.get_db)):
    profile = db.query(HealthProfile).filter(HealthProfile.id == id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")

    disease = db.query(Disease).filter(Disease.id == payload.disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found")

    # éviter doublon
    if disease in profile.diseases:
        return {"message": "Disease already assigned"}

    profile.diseases.append(disease)
    db.commit()

    return {"message": "Disease added"}


@router.post("/{id}/list_diseases")
def add_list_diseases(id: str, payload: list[DiseaseAdd], db: Session = Depends(db_instance.get_db)):
    profile = db.query(HealthProfile).filter(HealthProfile.id == id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")
    
    profile.diseases.clear()

    for item in payload:
        disease = db.query(Disease).filter(Disease.id == item.disease_id).first()
        if not disease:
            raise HTTPException(status_code=404, detail="Disease not found")

        profile.diseases.append(disease)
        db.commit()

    return {"message": "Diseases added"}


@router.post("/{id}/allergens")
def add_allergen(id: str, payload: AllergenAdd, db: Session = Depends(db_instance.get_db)):
    profile = db.query(HealthProfile).filter(HealthProfile.id == id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")

    allergen = db.query(Allergen).filter(Allergen.id == payload.allergen_id).first()
    if not allergen:
        raise HTTPException(status_code=404, detail="Allergen not found")

    if allergen in profile.allergens:
        return {"message": "Allergen already assigned"}

    profile.allergens.append(allergen)
    db.commit()

    return {"message": "Allergen added"}

@router.post("/{id}/list_allergens")
def add_list_allergens(id: str, payload: list[AllergenAdd], db: Session = Depends(db_instance.get_db)):
    profile = db.query(HealthProfile).filter(HealthProfile.id == id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")

    profile.allergens.clear()
    
    for item in payload:
        allergen = db.query(Allergen).filter(Allergen.id == item.allergen_id).first()
        if not allergen:
            raise HTTPException(status_code=404, detail="Allergen not found")

        profile.allergens.append(allergen)
        db.commit()

    return {"message": "Allergens added"}


@router.delete("/{id}/diseases/{disease_id}")
def remove_disease(id: str, disease_id: str, db: Session = Depends(db_instance.get_db)):
    profile = db.query(HealthProfile).filter(HealthProfile.id == id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")

    disease = db.query(Disease).filter(Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found")

    if disease not in profile.diseases:
        raise HTTPException(status_code=400, detail="Disease not assigned to profile")

    profile.diseases.remove(disease)
    db.commit()

    return {"message": "Disease removed"}

