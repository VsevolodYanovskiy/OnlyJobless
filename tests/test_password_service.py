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
        ("NoSpecial123", "This password ain't strong.\n Password may contain at least one of the following special symbols: '! @ # $ % ^ & * ( ) - _ + = [ ]'.\n Try another one"),
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
        mock_logger.error.assert_called_once_with(f"Ошибка при проверке пароля: {error_msg}")

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
            b"bytes_hash",  # bytes вместо строки
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
        assert inspect.isfunction(PasswordService.get_hash_async)
        assert inspect.isfunction(PasswordService.is_strong_async)
        assert inspect.isfunction(PasswordService.verify_async)
        
        # Можно создать экземпляр, но методы остаются статическими
        service = PasswordService()
        assert service.get_hash("test") is not None

    @pytest.mark.asyncio
    async def test_get_hash_async_success(self):
        """Тест: асинхронное хэширование успешно"""
        # Arrange
        password = "TestPassword123!"
        
        # Act
        result = await PasswordService.get_hash_async(password)
        
        # Assert
        assert isinstance(result, str)
        assert result.startswith("$2b$") or result.startswith("$2a$") or result.startswith("$2y$")
    
    @pytest.mark.asyncio
    async def test_is_strong_async_success(self):
        """Тест: асинхронная проверка сложности пароля"""
        # Arrange
        strong_password = "StrongPass123!"
        weak_password = "weak"
        
        # Act & Assert
        strong_result = await PasswordService.is_strong_async(strong_password)
        weak_result = await PasswordService.is_strong_async(weak_password)
        
        assert strong_result == "Your password is strong."
        assert "ain't strong" in weak_result
    
    @pytest.mark.asyncio
    async def test_verify_async_success(self):
        """Тест: асинхронная проверка пароля"""
        # Arrange
        password = "TestPassword123!"
        hashed_password = PasswordService.get_hash(password)
        
        # Act
        result = await PasswordService.verify_async(password, hashed_password)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_async_wrong_password(self):
        """Тест: асинхронная проверка неправильного пароля"""
        # Arrange
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed_password = PasswordService.get_hash(password)
        
        # Act
        result = await PasswordService.verify_async(wrong_password, hashed_password)
        
        # Assert
        assert result is False
    
    @patch('bcrypt.hashpw')
    @pytest.mark.asyncio
    async def test_get_hash_async_bcrypt_error(self, mock_hashpw):
        """Тест: обработка ошибки bcrypt при асинхронном хэшировании"""
        # Arrange
        mock_hashpw.side_effect = Exception("BCrypt error")
        
        # Act & Assert
        with pytest.raises(Exception):
            await PasswordService.get_hash_async("TestPassword123!")
    
    @patch('src.back.auth.services.password_service.logger')
    @patch('bcrypt.checkpw')
    @pytest.mark.asyncio
    async def test_verify_async_bcrypt_error(self, mock_checkpw, mock_logger):
        """Тест: обработка ошибки bcrypt при асинхронной проверке"""
        # Arrange
        error_msg = "BCrypt check error"
        mock_checkpw.side_effect = Exception(error_msg)
        
        # Act
        result = await PasswordService.verify_async("password", "hashed_password")
        
        # Assert
        assert result is False
        mock_logger.error.assert_called_once()
        # Проверяем что лог содержит сообщение об ошибке
        call_args = mock_logger.error.call_args[0][0]
        assert "Ошибка при проверке пароля" in call_args
    
    def test_verify_with_none_inputs(self):
        """Тест: проверка с None в качестве входных данных"""
        # Act & Assert
        # Все комбинации с None должны возвращать False
        assert PasswordService.verify(None, "hash") is False
        assert PasswordService.verify("password", None) is False
        assert PasswordService.verify(None, None) is False
    
    @pytest.mark.asyncio
    async def test_async_methods_with_none_inputs(self):
        """Тест: асинхронные методы с None в качестве входных данных"""
        # Act & Assert
        result = await PasswordService.verify_async(None, "hash")
        assert result is False
    
    def test_password_too_long(self):
        """Тест: пароль слишком длинный для bcrypt"""
        # bcrypt имеет ограничение на длину пароля (72 байта)
        # UTF-8 символы могут быть больше 1 байта
        # Arrange
        very_long_password = "A" * 100  # 100 символов 'A' - это 100 байт в UTF-8
        
        # Act & Assert
        # get_hash должен упасть с ValueError
        with pytest.raises(ValueError, match="password cannot be longer than 72 bytes"):
            PasswordService.get_hash(very_long_password)
    
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
