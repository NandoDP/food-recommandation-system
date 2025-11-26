from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from api.core.database import Database

# Create a single Database instance to provide a bound `get_db` dependency
db_instance = Database()
from api.core.security import security
from api.models.users import User

basic_scheme = HTTPBasic()

def get_current_user(
    credentials: HTTPBasicCredentials = Depends(basic_scheme),
    db: Session = Depends(db_instance.get_db)
) -> User:
    """Obtenir l'utilisateur actuel via email/mot de passe (authentification basique)"""
    user = db.query(User).filter(User.email == credentials.username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    if not security.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Vérifier que l'utilisateur est admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user