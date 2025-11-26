from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import Database
from api.core.security import security
from api.models.users import User
from api.models.users import HealthProfile
from api.schemas.auth import UserLogin, UserRegister, UserResponse
from api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])
db_instance = Database()

@router.post("/register")


def register_user(user_data: UserRegister, db: Session = Depends(db_instance.get_db)):
    """Inscription d'un nouvel utilisateur avec clé API automatique"""
    # Vérifier si l'utilisateur existe
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Créer l'utilisateur
    hashed_password = security.hash_password(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        last_name=user_data.last_name,
        first_name=user_data.first_name,
        birth_date=user_data.birth_date,
        gender=user_data.gender,
        weight=user_data.weight,
        height=user_data.height,
        registration_date=user_data.registration_date,
        language=user_data.language
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"message": "User registered successfully", "user_id": db_user.id}

@router.post("/login")
def login_user(credentials: UserLogin, db: Session = Depends(db_instance.get_db)):
    """Connexion utilisateur avec information de clé API"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not security.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    return {"message": "Login successful", "user_id": user.id}

@router.get("/{id}/profile")
def get_user_profile(id: str, db: Session = Depends(db_instance.get_db)):
    """Obtenir le profil d'un utilisateur par ID"""

    user = db.query(User).filter(User.id == id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Récupérer le health profile associé
    health_profile = (
        db.query(HealthProfile)
        .filter(HealthProfile.user_id == user.id)
        .first()
    )

    # Si pas encore de profil santé → renvoyer une structure vide
    if not health_profile:
        return {
            "user": {
                "id": str(user.id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "gender": user.gender,
                "weight": user.weight,
                "height": user.height,
            },
            "health": {
                "diseases": [],
                "allergens": [],
                "intolerances": None,
                "physical_activity_level": None
            }
        }

    # Récupérer maladies
    diseases = [d.name for d in health_profile.diseases]

    # Récupérer allergies
    allergens = [a.name for a in health_profile.allergens]

    # Construire la réponse finale
    return {
        "user": {
            "id": str(user.id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "gender": user.gender,
            "weight": user.weight,
            "height": user.height,
        },
        "health": {
            "diseases": diseases,
            "allergens": allergens,
            "physical_activity_level": health_profile.physical_activity_level,
        }
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Obtenir les informations de l'utilisateur connecté"""
    return current_user