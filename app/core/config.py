from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Taxi 2.0"
    DEBUG: bool = True
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/taxi_db"

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]

    ADMIN_LOGIN: str = "Alexander"
    ADMIN_PASSWORD: str = "123"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
