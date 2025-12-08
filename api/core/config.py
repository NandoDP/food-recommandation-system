from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # API Configuration
    APP_NAME: str = "Nutrition Westaf API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", None)
    
    # CORS
    ALLOWED_ORIGINS: list = ["*"]  # À restreindre en production
    
    SECRET_KEY: str = "your-very-secret-key"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 1000
    RATE_LIMIT_PERIOD: int = 3600  # 1 heure
    
    class Config:
        # env_file = None # En production sur Railway
        env_file = ".env"

settings = Settings()