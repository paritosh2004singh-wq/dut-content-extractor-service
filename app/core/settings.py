from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    APP_NAME: str = "Knowledge Ingestion Platform"
    DEBUG: bool = False
    MONGO_URI: str
    MONGO_DATABASE: str
    ALLOWED_ORIGINS: List[str] = ["*"]
    API_PREFIX: str = "/api/v1"
    # Providers
    
    MISTRAL_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
