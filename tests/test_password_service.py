import pytest
import bcrypt
from unittest.mock import patch, MagicMock
from src.back.auth.services.password_service import PasswordService


class TestPasswordService:
    """Тесты для сервиса работы с паролями"""

    def test_get_hash_returns_string(self):
        """Тест: хэширование возвращает строку"""
        # Arrange
        password = "TestPassword123!"
        
        # Act
        result = PasswordService.get_hash(password)
        
        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        # Проверяем что это bcrypt хэш
        assert result.startswith("$2b$") or result.startswith("$2a$") or result.startswith("$2y$")

    def test_get_hash_different_for_same_password(self):
        """Тест: разные вызовы дают разные хэши (из-за разной соли)"""
        # Arrange
        password = "TestPassword123!"
        
        # Act
        hash1 = PasswordService.get_hash(password)
        hash2 = PasswordService.get_hash(password)
        
        # Assert
        assert hash1 != hash2  # Разные соли = разные хэши
        assert len(hash1) == len(hash2)  # Но одинаковая длина

    @pytest.mark.parametrize("password,expected_message", [
        ("short", "This password ain't strong. Password may contain no less than 8 symbols. Try another one"),
        ("nouppercase1!", "This password ain't strong. Password may contain uppercase letters. Try another one"),
        ("NOLOWERCASE1!", "This password ain't strong. Password may contain lowercase letters. Try another one"),
        ("NoNumbers!", "This password ain't strong. Password may contain numbers. Try another one"),
        ("NoSpecial123", "This password ain't strong.\nPassword may contain at least one of the following special symbols: '! @ # $ % ^ & * ( ) - _ + = [ ]'.\nTry another one"),
        ("Another!123", "Your password is strong."),
        ("Test@123Pass", "Your password is strong."),
        ("Strong#2024", "Your password is strong."),
    ])
    def test_is_strong_various_passwords(self, password, expected_message):
        """Тест: проверка сложности пароля для разных случаев"""
        # Act
        result = PasswordService.is_strong(password)
        
        # Assert
        assert result == expected_message

    def test_is_strong_with_special_symbols(self):
        """Тест: проверка всех специальных символов"""
        special_chars = "!@#$%^&*()-_+=[]"
        
        for char in special_chars:
            password = f"Test123{char}pass"
            result = PasswordService.is_strong(password)
            assert result == "Your password is strong."

    def test_verify_correct_password(self):
        """Тест: проверка правильного пароля"""
        # Arrange
        plain_password = "TestPassword123!"
        hashed_password = PasswordService.get_hash(plain_password)
        
        # Act
        result = PasswordService.verify(plain_password, hashed_password)
        
        # Assert
        assert result is True

    def test_verify_incorrect_password(self):
        """Тест: проверка неправильного пароля"""
        # Arrange
        plain_password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed_password = PasswordService.get_hash(plain_password)
        
        # Act
        result = PasswordService.verify(wrong_password, hashed_password)
        
        # Assert
        assert result is False

    def test_verify_with_different_hash(self):
        """Тест: проверка с другим хэшем"""
        # Arrange
        password = "TestPassword123!"
        hash1 = PasswordService.get_hash(password)
        hash2 = PasswordService.get_hash(password)  # Другой хэш (другая соль)
        
        # Act & Assert
        assert PasswordService.verify(password, hash1) is True
        assert PasswordService.verify(password, hash2) is True

    def test_verify_empty_password(self):
        """Тест: проверка пустого пароля"""
        # Arrange
        plain_password = ""
        hashed_password = PasswordService.get_hash("somepassword")
        
        # Act
        result = PasswordService.verify(plain_password, hashed_password)
        
        # Assert
        assert result is False

    @patch('bcrypt.hashpw')
    def test_get_hash_bcrypt_error(self, mock_hashpw):
        """Тест: обработка ошибки bcrypt при хэшировании"""
        # Arrange
        mock_hashpw.side_effect = Exception("BCrypt error")
        
        # Act & Assert
        with pytest.raises(Exception):
            PasswordService.get_hash("TestPassword123!")

    @patch('src.back.auth.services.password_service.logger')
    @patch('bcrypt.checkpw')
    def test_verify_bcrypt_error(self, mock_checkpw, mock_logger):
        """Тест: обработка ошибки bcrypt при проверке"""
        # Arrange
        error_msg = "BCrypt check error"
        mock_checkpw.side_effect = Exception(error_msg)
        
        # Act
        result = PasswordService.verify("password", "hashed_password")
        
        # Assert
        assert result is False
        mock_logger.error.assert_called_once()

    def test_password_strength_edge_cases(self):
        """Тест: граничные случаи для проверки сложности"""
        # Минимально допустимый пароль
        min_password = "A1b!cdef"
        result = PasswordService.is_strong(min_password)
        assert result == "Your password is strong."
        
        # Пароль ровно 8 символов
        exactly_8 = "Ab1!defg"
        result = PasswordService.is_strong(exactly_8)
        assert result == "Your password is strong."

    def test_unicode_password(self):
        """Тест: пароль с Unicode символами"""
        # Arrange
        password = "Pässwörd123!Привет"
        hashed_password = PasswordService.get_hash(password)
        
        # Act & Assert
        assert PasswordService.verify(password, hashed_password) is True
        assert PasswordService.verify("wrong", hashed_password) is False

    def test_get_hash_with_bytes_input(self):
        """Тест: что метод работает только со строками"""
        # Act & Assert
        # Должно работать со строкой
        result = PasswordService.get_hash("string")
        assert isinstance(result, str)
        
        # Не должно работать с bytes (но это проверит сам Python)
        with pytest.raises(AttributeError):
            PasswordService.get_hash(b"bytes")  # .encode() вызовется на bytes

    def test_verify_with_invalid_hash_format(self):
        """Тест: проверка с некорректным форматом хэша"""
        # Arrange
        invalid_hashes = [
            "",  # пустой
            "invalid",  # не bcrypt
            "$2b$",  # неполный
        ]
        
        for invalid_hash in invalid_hashes:
            # Act
            result = PasswordService.verify("password", invalid_hash)
            
            # Assert - должно возвращать False при ошибке
            assert result is False

    @pytest.mark.parametrize("password", [
        "TEST123!",
        "test123!",
        "Testtest!",
        "TESTTEST!",
        "12345678!",
    ])
    def test_is_strong_negative_cases(self, password):
        """Тест: отрицательные случаи для проверки сложности"""
        result = PasswordService.is_strong(password)
        assert "ain't strong" in result

    def test_password_service_static_methods(self):
        """Тест: проверка что все методы статические"""
        # Act
        import inspect
        
        # Assert
        assert inspect.isfunction(PasswordService.get_hash)
        assert inspect.isfunction(PasswordService.is_strong)
        assert inspect.isfunction(PasswordService.verify)
        
        # Можно создать экземпляр, но методы остаются статическими
        service = PasswordService()
        assert service.get_hash("test") is not None

    def test_thread_pool_executor_initialized(self):
        """Тест: ThreadPoolExecutor инициализирован"""
        # Act
        from src.back.auth.services.password_service import executor
        
        # Assert
        assert executor is not None

    def test_verify_with_none_inputs(self):
        """Тест: проверка с None в качестве входных данных"""
        # Act & Assert
        # Все комбинации с None должны возвращать False
        assert PasswordService.verify(None, "hash") is False
        assert PasswordService.verify("password", None) is False
        assert PasswordService.verify(None, None) is False

    def test_password_exactly_72_bytes(self):
        """Тест: пароль ровно 72 байта (максимум для bcrypt)"""
        # Arrange
        # 72 символа 'A' = 72 байта в UTF-8
        max_length_password = "A" * 72
        
        # Act
        hashed = PasswordService.get_hash(max_length_password)
        result = PasswordService.verify(max_length_password, hashed)
        
        # Assert
        assert result is True

    def test_hash_verification_with_whitespace(self):
        """Тест: проверка пароля с пробелами"""
        # Arrange
        password_with_spaces = "  Test 123!  "
        hashed = PasswordService.get_hash(password_with_spaces)
        
        # Act & Assert
        assert PasswordService.verify(password_with_spaces, hashed) is True
        assert PasswordService.verify("Test 123!", hashed) is False  # Без внешних пробелов
    
    def test_special_characters_in_all_positions(self):
        """Тест: специальные символы в разных позициях пароля"""
        special_chars = "!@#$%^&*()-_+=[]"
        
        for char in special_chars:
            for position in [0, 5, -1]:  # Начало, середина, конец
                password = list("Test123pass")
                if position == -1:
                    position = len(password)
                if position <= len(password):
                    password.insert(position, char)
                    password_str = "".join(password)
                    
                    result = PasswordService.is_strong(password_str)
                    assert result == "Your password is strong."
