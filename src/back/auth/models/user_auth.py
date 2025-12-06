from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime
from encryption import DataEncryptor
from ...config.security import get_security_settings
from .encryption import DataEncryptor


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
    email_encrypted = Column(String(512), unique=True, index=True, nullable=False)
    email_salt = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @property
    def email(self) -> str:
        """Получает расшифрованный email"""
        return encryptor.decrypt(self.email_encrypted, self.email_salt)

    @email.setter
    def email(self, value: str):
        """Устанавливает email с шифрованием"""
        encrypted_email, salt = encryptor.encrypt(value)
        self.email_encrypted = encrypted_email
        self.email_salt = salt

    def __init__(self, email: str = None, password_hash: str = None, **kwargs):
        """
        Инициализация пользователя с автоматическим шифрованием email.
        """
        super().__init__(**kwargs)
        if email:
            self.email = email
        if password_hash:
            self.password_hash = password_hash

    def to_dict(self, include_encrypted: bool = False) -> dict:
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
    def from_dict(cls, data: dict, encrypt_email: bool = True) -> 'User':
        """
        Создает объект пользователя из словаря.
        """
        user = cls()
        if 'email' in data:
            if encrypt_email:
                user.email = data['email']
            else:
                if 'email_encrypted' in data and 'email_salt' in data:
                    user.email_encrypted = data['email_encrypted']
                    user.email_salt = data['email_salt']
        if 'id' in data:
            user.id = data['id']
        if 'password_hash' in data:
            user.password_hash = data['password_hash']
        if 'created_at' in data and data['created_at']:
            if isinstance(data['created_at'], str):
                user.created_at = datetime.datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            else:
                user.created_at = data['created_at']
        if 'updated_at' in data and data['updated_at']:
            if isinstance(data['updated_at'], str):
                user.updated_at = datetime.datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
            else:
                user.updated_at = data['updated_at']
        return user

    def update_email(self, new_email: str):
        """Безопасно обновляет email с перешифровкой"""
        self.email = new_email
        self.updated_at = func.now()

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
        if not email or '@' not in email:
            return False
        return len(email) <= 255

    @staticmethod
    def mask_email(email: str) -> str:
        """Маскирует email для безопасного отображения"""
        if '@' not in email:
            return email
        local_part, domain = email.split('@', 1)
        if len(local_part) <= 2:
            masked_local = '*' * len(local_part)
        else:
            masked_local = local_part[0] + '*' * (len(local_part) - 2) + local_part[-1]
        return f"{masked_local}@{domain}"

    @staticmethod
    def users_to_dict_list(users: list, include_encrypted: bool = False) -> list:
        """
        Преобразует список пользователей в список словарей.
        """
        return [user.to_dict(include_encrypted=include_encrypted) for user in users]
