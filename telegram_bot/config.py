from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # API Configuration
    APP_NAME: str = "Nutrition Westaf API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", None)
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
    
    class Config:
        # env_file = None # En production sur Railway
        env_file = ".env"

settings = Settings()