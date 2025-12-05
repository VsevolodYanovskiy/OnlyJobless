import bcrypt
from typing import Union
import logging

class PasswordService:
    """Сервис для безопасного хэширования и проверки паролей"""

    @staticmethod
    def get_hash(password: str) -> str:
        """Создает безопасный хэш пароля с использованием bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
