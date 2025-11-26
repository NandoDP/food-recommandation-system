import bcrypt
import secrets
import hashlib
from api.core.config import settings

class SecurityManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
    
    # Password Management
    def hash_password(self, password: str) -> str:
        """Hasher un mot de passe avec bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Vérifier un mot de passe"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    # API Key Management
    def generate_api_key(self, prefix: str = "tk") -> str:
        """Générer une clé API sécurisée"""
        # Format: tk-proj_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}-proj_{random_part}"
    
    def hash_api_key(self, api_key: str) -> str:
        """Hasher une clé API avec SHA-256"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key_format(self, api_key: str) -> bool:
        """Vérifier le format d'une clé API"""
        return api_key.startswith("tk-proj_") and len(api_key) >= 40

security = SecurityManager(settings.SECRET_KEY)