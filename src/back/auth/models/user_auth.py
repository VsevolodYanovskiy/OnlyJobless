from __future__ import annotations
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime
import re
from typing import Optional, Any, Dict, List
from src.back.config.security import get_security_settings
from src.back.auth.models.encryption import DataEncryptor


try:
    settings = get_security_settings()
    encryptor = DataEncryptor(encryption_key=settings.encryption_key)
except Exception as e:
    print(f"Внимание: Не удалось инициализировать шифратор: {e}")
    print("Установите переменную окружения ENCRYPTION_KEY")
    raise

Base = declarative_base()


class User(Base):
    """Модель пользователя с шифрованием персональных данных"""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email_encrypted = Column(String(512), unique=True, index=True, nullable=True)
    email_salt = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __init__(self, email: Optional[str] = None, password_hash: Optional[str] = None, **kwargs):
        """
        Инициализация пользователя с автоматическим шифрованием email.
        """
        super().__init__(**kwargs)
        if email:
            self.email = email
        if password_hash:
            self.password_hash = password_hash  # type: ignore

    @property
    def email(self) -> Optional[str]:
        """Получает расшифрованный email"""
        if not self.email_encrypted or not self.email_salt:
            return None
        return encryptor.decrypt(self.email_encrypted, self.email_salt)  # type: ignore

    @email.setter
    def email(self, value: str) -> None:
        """Устанавливает email с шифрованием"""
        if value is None:
            self.email_encrypted = None  # type: ignore
            self.email_salt = None  # type: ignore
        else:
            encrypted_email, salt = encryptor.encrypt(value)
            self.email_encrypted = encrypted_email  # type: ignore
            self.email_salt = salt  # type: ignore

    def to_dict(self, include_encrypted: bool = False) -> Dict[str, Any]:
        """
        Преобразует объект пользователя в словарь.
        """
        result = {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_encrypted:
            result.update({
                'email_encrypted': self.email_encrypted,
                'email_salt': self.email_salt,
                'password_hash': self.password_hash
            })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any], encrypt_email: bool = True) -> 'User':
        """
        Создает объект пользователя из словаря.
        """
        user = cls()
        if 'email' in data:
            if encrypt_email:
                user.email = data['email']
            else:
                user.email_encrypted = data.get('email_encrypted')  # type: ignore
                user.email_salt = data.get('email_salt')  # type: ignore
        else:
            if 'email_encrypted' in data and not encrypt_email:
                user.email_encrypted = data.get('email_encrypted')  # type: ignore
                user.email_salt = data.get('email_salt')  # type: ignore
        if 'id' in data:
            user.id = data['id']  # type: ignore
        if 'password_hash' in data:
            user.password_hash = data['password_hash']  # type: ignore
        if 'created_at' in data and data['created_at']:
            if isinstance(data['created_at'], str):
                user.created_at = datetime.datetime.fromisoformat(data['created_at'].replace('Z',
                                                                                             '+00:00'))  # type: ignore
            else:
                user.created_at = data['created_at']  # type: ignore
        if 'updated_at' in data and data['updated_at']:
            if isinstance(data['updated_at'], str):
                user.updated_at = datetime.datetime.fromisoformat(data['updated_at'].replace('Z',
                                                                                             '+00:00'))  # type: ignore
            else:
                user.updated_at = data['updated_at']  # type: ignore
        return user

    def update_email(self, new_email: str) -> None:
        """Безопасно обновляет email с перешифровкой"""
        self.email = new_email
        self.updated_at = datetime.datetime.utcnow()  # type: ignore

    def verify_email(self, email_to_verify: str) -> bool:
        """
        Проверяет, соответствует ли email сохраненному.
        """
        return self.email == email_to_verify

    @classmethod
    def create_from_plain(cls, email: str, password_hash: str) -> 'User':
        """
        Создает пользователя из незашифрованных данных.
        """
        return cls(email=email, password_hash=password_hash)


class UserUtils:
    """Вспомогательные функции для работы с пользователями"""

    @staticmethod
    def validate_email_format(email: str) -> bool:
        """Проверяет формат email"""
        if not email or len(email) > 255:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if '@' not in email:
            return False
        local_part, domain = email.split('@', 1)
        if not local_part:
            return False
        if not domain or '.' not in domain:
            return False
        return bool(re.match(pattern, email))

    @staticmethod
    def mask_email(email: Optional[str]) -> Optional[str]:
        """Маскирует email для безопасного отображения"""
        if email is None:
            return None
        if '@' not in email:
            return email
        local_part, domain = email.split('@', 1)
        if len(local_part) == 1:
            masked_local = '*'
        elif len(local_part) == 2:
            masked_local = local_part[0] + '*'
        else:
            masked_local = local_part[0] + '*' * (len(local_part) - 2) + local_part[-1]
        return f"{masked_local}@{domain}"

    @staticmethod
    def users_to_dict_list(users: List[User], include_encrypted: bool = False) -> List[Dict[str, Any]]:
        """
        Преобразует список пользователей в список словарей.
        """
        if users is None:
            return []
        return [user.to_dict(include_encrypted=include_encrypted) for user in users]
