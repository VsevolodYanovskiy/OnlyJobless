from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from ...config.security import SecuritySettings

class JWTService:
    """Сервис для работы с JWT токенами"""
    
    def __init__(self, security_settings: SecuritySettings):
        """Инициализация сервиса с настройками безопасности"""
        pass
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создает JWT токен доступа с указанными данными"""
        pass
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверяет валидность JWT токена и возвращает его payload"""
        pass
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Декодирует JWT токен без проверки подписи (для отладки)"""
        pass
