from pydantic_settings import BaseSettings
from typing import List
import os


class SecuritySettings(BaseSettings):
    """Настройки безопасности приложения (JWT, CORS и т.д.)"""
    secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "")


    class Config:
        env_file = ".env"


def get_security_settings() -> SecuritySettings:
    """Возвращает настройки безопасности из переменных окружения"""
    return SecuritySettings()
