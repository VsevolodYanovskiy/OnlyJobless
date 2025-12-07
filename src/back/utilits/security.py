from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
from ...config.security import SecuritySettings


executor = ThreadPoolExecutor(max_workers=2)


class JWTService:
    """Асинхронный сервис для работы с JWT токенами"""
    def __init__(self, security_settings: SecuritySettings):
        """Инициализация сервиса с настройками безопасности"""
        self.settings = security_settings

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Синхронно создает JWT токен доступа"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.settings.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        return jwt.encode(
            to_encode,
            self.settings.secret_key,
            algorithm=self.settings.algorithm
        )

    async def create_access_token_async(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Асинхронно создает JWT токен доступа"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            lambda: self.create_access_token(data, expires_delta)
        )

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Синхронно проверяет валидность JWT токена"""
        try:
            return jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm]
            )
        except JWTError:
            return None

    async def verify_token_async(self, token: str) -> Optional[Dict[str, Any]]:
        """Асинхронно проверяет валидность JWT токена"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, lambda: self.verify_token(token))

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Синхронно декодирует JWT токен без проверки подписи"""
        try:
            return jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm],
                options={"verify_signature": False}
            )
        except JWTError:
            return None
    async def decode_token_async(self, token: str) -> Optional[Dict[str, Any]]:
        """Асинхронно декодирует JWT токен без проверки подписи"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, lambda: self.decode_token(token))
