from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    APP_NAME: str = "Knowledge Ingestion Platform"
    DEBUG: bool = False
    MONGO_URI: str
    MONGO_DATABASE: str
    ALLOWED_ORIGINS: List[str] = ["*"]
    API_PREFIX: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env.example",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
