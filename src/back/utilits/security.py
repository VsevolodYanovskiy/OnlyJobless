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
        self.settings = security_settings

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создает JWT токен доступа"""
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

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создает JWT refresh токен"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.settings.refresh_token_expire_days)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        return jwt.encode(
            to_encode,
            self.settings.refresh_secret_key,
            algorithm=self.settings.algorithm
        )

    async def create_access_token_async(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Асинхронно создает JWT токен доступа"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            lambda: self.create_access_token(data, expires_delta)
        )

    async def create_refresh_token_async(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Асинхронно создает JWT refresh токен"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            lambda: self.create_refresh_token(data, expires_delta)
        )

    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверяет валидность access токена"""
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm]
            )
            if payload.get("type") != "access":
                return None
            return payload
        except JWTError:
            return None

    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверяет валидность refresh токена"""
        try:
            payload = jwt.decode(
                token,
                self.settings.refresh_secret_key,
                algorithms=[self.settings.algorithm]
            )
            if payload.get("type") != "refresh":
                return None
            return payload
        except JWTError:
            return None

    async def verify_access_token_async(self, token: str) -> Optional[Dict[str, Any]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, lambda: self.verify_access_token(token))

    async def verify_refresh_token_async(self, token: str) -> Optional[Dict[str, Any]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, lambda: self.verify_refresh_token(token))
