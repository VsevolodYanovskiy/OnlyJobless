from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os


class DataEncryptor:
    """
    Шифратор данных с использованием ключа и соли.
    Ключ должен храниться отдельно от кода (в переменных окружения, secrets manager и т.д.)
    """
    def __init__(self, encryption_key: str = None):
        """
        Инициализация шифратора.
        """
        self.encryption_key = encryption_key or os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key:
            raise ValueError(
                "Ключ шифрования не найден. "
                "Укажите его в параметре или установите переменную окружения ENCRYPTION_KEY"
            )

    def _generate_salt(self) -> bytes:
        """Генерирует случайную соль для шифрования."""
        return os.urandom(16)

    def _get_fernet_key(self, salt: bytes) -> bytes:
        """
        Создает ключ Fernet из основного ключа и соли.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(self.encryption_key.encode())
        )
        return key

    def encrypt(self, data: str) -> tuple[str, str]:
        """
        Шифрует строку данных (email, username).
        """
        salt = self._generate_salt()
        fernet_key = self._get_fernet_key(salt)
        cipher = Fernet(fernet_key)
        encrypted_bytes = cipher.encrypt(data.encode('utf-8'))
        encrypted_base64 = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        salt_base64 = base64.urlsafe_b64encode(salt).decode('utf-8')
        return encrypted_base64, salt_base64

    def decrypt(self, encrypted_data: str, salt_base64: str) -> str:
        """
        Дешифрует данные.
        """
        salt = base64.urlsafe_b64decode(salt_base64.encode('utf-8'))
        fernet_key = self._get_fernet_key(salt)
        cipher = Fernet(fernet_key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        return decrypted_bytes.decode('utf-8')
