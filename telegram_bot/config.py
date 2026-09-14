from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    """Configuration settings for Telegram Bot"""
    
    # API Configuration
    APP_NAME: str = "NutriSénégal Bot"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Telegram Bot
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    
    # API Backend URL
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000/api")
    
    # Configuration Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore les champs supplémentaires du .env
        case_sensitive=False
    )

settings = Settings()