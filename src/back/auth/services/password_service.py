import bcrypt
from typing import Union
import logging

ENCODING = 'utf-8'
SALT = bcrypt.gensalt()

class PasswordService:
    """Сервис для безопасного хэширования и проверки паролей"""
    
    @staticmethod
    def get_hash(password: str) -> str:
        """Создает безопасный хэш пароля с использованием bcrypt"""
        password = password.encode('utf-8')
        key = bcrypt.kdf(
            password=password,
            salt=SALT,
            desired_key_bytes=64,
            rounds=200
        )
        return key
    @staticmethod
    def is_strong(password: str) -> str:
        """Проверяет сложность пароля (длина, символы и т.д.)"""
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
    def verify(plain_password: str, hashed_password: str) -> bool:
        """Проверяет соответствие plain-text пароля его хэшу"""
        return get_hash(plain_password) == hashed_password

