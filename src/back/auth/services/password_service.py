import bcrypt
import asyncio
from typing import Optional
import logging
from concurrent.futures import ThreadPoolExecutor


logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=4)

BCRYPT_MAX_LENGTH = 72


class PasswordService:
    """Асинхронный сервис для безопасного хэширования и проверки паролей"""

    @staticmethod
    def _validate_password_length(password: str) -> None:
        """Проверяет длину пароля для bcrypt"""
        if password is None:
            raise ValueError("Password cannot be None")
        # Проверяем длину в байтах (bcrypt ограничивает 72 байтами)
        byte_length = len(password.encode('utf-8'))
        if byte_length > BCRYPT_MAX_LENGTH:
            raise ValueError(
                f"password cannot be longer than {BCRYPT_MAX_LENGTH} bytes, "
                f"got {byte_length} bytes. Password will be truncated by bcrypt. "
                f"Consider using a shorter password or hash the password first."
            )

    @staticmethod
    def get_hash(password: str) -> str:
        """Создает безопасный хэш пароля с использованием bcrypt"""
        PasswordService._validate_password_length(password)
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    async def get_hash_async(password: str) -> str:
        """Асинхронно создает безопасный хэш пароля"""
        PasswordService._validate_password_length(password)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor, 
            lambda: bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        )

    @staticmethod
    def is_strong(password: str) -> str:
        """Синхронно проверяет сложность пароля"""
        if password is None:
            return "This password ain't strong. Password may contain no less than 8 symbols. Try another one"
        # Проверяем длину в символах (не байтах)
        if len(password) < 8:
            return "This password ain't strong. Password may contain no less than 8 symbols. Try another one"
        if not any(char in "0123456789" for char in password):
            return "This password ain't strong. Password may contain numbers. Try another one"
        if not any(char in "abcdefghijklmnopqrstuvwxyz" for char in password):
            return "This password ain't strong. Password may contain lowercase letters. Try another one"
        if not any(char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" for char in password):
            return "This password ain't strong. Password may contain uppercase letters. Try another one"
        if not any(char in "!@#$%^&*()-_+=[]" for char in password):
            return "This password ain't strong.\n Password may contain at least one of the following special symbols: '! @ # $ % ^ & * ( ) - _ + = [ ]'.\n Try another one"
        return "Your password is strong."

    @staticmethod
    async def is_strong_async(password: str) -> str:
        """Асинхронно проверяет сложность пароля"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, lambda: PasswordService.is_strong(password))

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """Синхронно проверяет соответствие пароля его хэшу"""
        if plain_password is None or hashed_password is None:
            logger.warning("Попытка проверки пароля с None значениями")
            return False
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Ошибка при проверке пароля: {e}")
            return False

    @staticmethod
    async def verify_async(plain_password: str, hashed_password: str) -> bool:
        """Асинхронно проверяет соответствие пароля его хэшу"""
        if plain_password is None or hashed_password is None:
            logger.warning("Попытка проверки пароля с None значениями (async)")
            return False
        
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                executor,
                lambda: bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
            )
        except Exception as e:
            logger.error(f"Ошибка при проверке пароля (async): {e}")
            return False
