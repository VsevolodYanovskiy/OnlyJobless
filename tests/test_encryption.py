import pytest
import base64
import os
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet, InvalidToken
from src.back.auth.models.encryption import DataEncryptor


class TestEncryption:
    """Тесты для шифрования данных"""
    
    @pytest.fixture
    def encryption_key(self):
        """Фикстура с тестовым ключом шифрования"""
        return "test-encryption-key-min-32-chars-long-here"
    
    @pytest.fixture
    def encryptor(self, encryption_key):
        """Фикстура для шифратора"""
        return DataEncryptor(encryption_key=encryption_key)
    
    def test_initialization_with_key(self, encryption_key):
        """Тест: инициализация с ключом"""

        encryptor = DataEncryptor(encryption_key=encryption_key)

        assert encryptor.encryption_key == encryption_key
    
    def test_initialization_with_env_var(self, encryption_key):
        """Тест: инициализация с переменной окружения"""
        with patch.dict(os.environ, {"ENCRYPTION_KEY": encryption_key}):

            encryptor = DataEncryptor()

            assert encryptor.encryption_key == encryption_key
    
    def test_initialization_without_key(self):
        """Тест: инициализация без ключа (должна вызывать ошибку)"""

        with patch.dict(os.environ, {}, clear=True):

            with pytest.raises(ValueError) as exc_info:
                DataEncryptor()
            
            assert "Ключ шифрования не найден" in str(exc_info.value)
    
    def test_encrypt_decrypt_string(self, encryptor):
        """Тест: шифрование и дешифрование строки"""

        original_data = "test@example.com"

        encrypted_data, salt = encryptor.encrypt(original_data)
        decrypted_data = encryptor.decrypt(encrypted_data, salt)

        assert isinstance(encrypted_data, str)
        assert isinstance(salt, str)
        assert len(encrypted_data) > 0
        assert len(salt) > 0
        assert decrypted_data == original_data

        assert encrypted_data != original_data

        try:
            base64.urlsafe_b64decode(encrypted_data.encode())
            base64.urlsafe_b64decode(salt.encode())
        except Exception:
            pytest.fail("Невалидный base64 формат")
    
    def test_encrypt_different_salts(self, encryptor):
        """Тест: разные вызовы шифрования дают разные результаты"""

        data = "test@example.com"

        encrypted1, salt1 = encryptor.encrypt(data)
        encrypted2, salt2 = encryptor.encrypt(data)

        assert encrypted1 != encrypted2
        assert salt1 != salt2
    
    def test_decrypt_with_wrong_salt(self, encryptor):
        """Тест: дешифрование с неправильной солью"""

        data = "test@example.com"
        encrypted, salt = encryptor.encrypt(data)

        wrong_salt = base64.urlsafe_b64encode(b"wrong-salt-123456").decode()

        with pytest.raises(InvalidToken):
            encryptor.decrypt(encrypted, wrong_salt)
    
    def test_decrypt_tampered_data(self, encryptor):
        """Тест: дешифрование измененных данных"""

        data = "test@example.com"
        encrypted, salt = encryptor.encrypt(data)

        tampered = encrypted[:-1] + ("a" if encrypted[-1] != "a" else "b")

        with pytest.raises(InvalidToken):
            encryptor.decrypt(tampered, salt)
    
    def test_encrypt_empty_string(self, encryptor):
        """Тест: шифрование пустой строки"""

        encrypted, salt = encryptor.encrypt("")
        decrypted = encryptor.decrypt(encrypted, salt)

        assert decrypted == ""
    
    def test_encrypt_special_characters(self, encryptor):
        """Тест: шифрование строк со специальными символами"""
        test_cases = [
            "test@example.com",
            "имя@домен.рф",
            "user+tag@example.com",
            "1234567890",
            "!@#$%^&*()",
            " ",
            "\t\n\r",
            "a" * 1000,
        ]
        
        for original in test_cases:
            encrypted, salt = encryptor.encrypt(original)
            decrypted = encryptor.decrypt(encrypted, salt)
            
            assert decrypted == original, f"Не удалось для: {original[:20]}"
    
    def test_encrypt_decrypt_bytes(self):
        """Тест: что методы работают только со строками"""
        encryptor = DataEncryptor(encryption_key="test-key-32-chars-long-here-12345")

        encrypted, salt = encryptor.encrypt("string")
        assert isinstance(encrypted, str)
        assert isinstance(salt, str)

        with pytest.raises(AttributeError):
            encryptor.encrypt(b"bytes")
    
    def test_generate_salt_randomness(self, encryptor):
        """Тест: случайность генерации соли"""
        salts = set()

        for _ in range(10):
            salt = encryptor._generate_salt()

        assert len(salts) == 10
    
    def test_get_fernet_key_consistency(self, encryptor):
        """Тест: консистентность генерации ключа Fernet"""

        salt = encryptor._generate_salt()

        key1 = encryptor._get_fernet_key(salt)
        key2 = encryptor._get_fernet_key(salt)

        assert key1 == key2
    
    def test_encrypt_large_data(self, encryptor):
        """Тест: шифрование больших данных"""

        large_data = "x" * 10000

        encrypted, salt = encryptor.encrypt(large_data)
        decrypted = encryptor.decrypt(encrypted, salt)

        assert decrypted == large_data
    
    def test_encrypt_with_different_keys(self):
        """Тест: шифрование с разными ключами"""
        key1 = "first-encryption-key-32-chars-long-here"
        key2 = "second-encryption-key-32-chars-long-here"
        encryptor1 = DataEncryptor(encryption_key=key1)
        encryptor2 = DataEncryptor(encryption_key=key2)
        data = "test@example.com"
        encrypted1, salt1 = encryptor1.encrypt(data)
        encrypted2, salt2 = encryptor2.encrypt(data)
        assert encrypted1 != encrypted2
        assert encryptor1.decrypt(encrypted1, salt1) == data
        assert encryptor2.decrypt(encrypted2, salt2) == data
        with pytest.raises(InvalidToken):
            encryptor1.decrypt(encrypted2, salt2)
    
    def test_encryption_stability(self, encryptor):
        """Тест: стабильность шифрования/дешифрования"""
        test_data = [
            ("test1@example.com", "password123"),
            ("user@domain.com", "пароль123!"),
            ("admin@test.ru", "P@ssw0rd"),
        ]
        
        for email, password in test_data:
            for _ in range(5):
                encrypted, salt = encryptor.encrypt(email)
                decrypted = encryptor.decrypt(encrypted, salt)
                assert decrypted == email
