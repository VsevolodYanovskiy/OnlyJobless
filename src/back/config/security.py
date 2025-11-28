from pydantic import BaseSettings
from typing import Optional
import os

class SecuritySettings(BaseSettings):
    """Настройки безопасности приложения (JWT, CORS и т.д.)"""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: list = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

def get_security_settings() -> SecuritySettings:
    """Возвращает настройки безопасности из переменных окружения"""
    pass
