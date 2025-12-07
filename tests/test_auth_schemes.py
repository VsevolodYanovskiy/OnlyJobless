import pytest
from datetime import datetime
from pydantic import ValidationError
from src.back.schemes.auth_schemes import (
    UserRegister, 
    UserLogin, 
    UserResponse, 
    TokenResponse
)


class TestAuthSchemas:
    """Тесты для схем аутентификации"""
    
    def test_user_register_valid(self):
        """Тест: валидные данные для регистрации"""
        # Act
        user = UserRegister(
            email="test@example.com",
            password="StrongPass123!",
            password_confirm="StrongPass123!"
        )
        
        # Assert
        assert user.email == "test@example.com"
        assert user.password == "StrongPass123!"
        assert user.password_confirm == "StrongPass123!"
    
    def test_user_register_invalid_email(self):
        """Тест: невалидный email при регистрации"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="invalid-email",
                password="StrongPass123!",
                password_confirm="StrongPass123!"
            )
        
        assert "email" in str(exc_info.value)
    
    def test_user_register_passwords_mismatch(self):
        """Тест: несовпадающие пароли при регистрации"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="StrongPass123!",
                password_confirm="DifferentPass456!"
            )
        
        assert "passwords_match" in str(exc_info.value)
    
    def test_user_register_missing_fields(self):
        """Тест: отсутствие обязательных полей"""
        with pytest.raises(ValidationError):
            UserRegister(
                email="test@example.com",
                # Пропущены password и password_confirm
            )
    
    def test_user_login_valid(self):
        """Тест: валидные данные для входа"""
        # Act
        login = UserLogin(
            email="test@example.com",
            password="StrongPass123!"
        )
        
        # Assert
        assert login.email == "test@example.com"
        assert login.password == "StrongPass123!"
    
    def test_user_login_invalid_email(self):
        """Тест: невалидный email при входе"""
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(
                email="invalid-email",
                password="StrongPass123!"
            )
        
        assert "email" in str(exc_info.value)
    
    def test_user_response_valid(self):
        """Тест: валидные данные ответа пользователя"""
        # Arrange
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        
        # Act
        response = UserResponse(
            id=1,
            email="test@example.com",
            created_at=created_at
        )
        
        # Assert
        assert response.id == 1
        assert response.email == "test@example.com"
        assert response.created_at == created_at
    
    def test_user_response_from_orm(self):
        """Тест: создание ответа из ORM объекта"""
        # Arrange
        class MockUser:
            def __init__(self):
                self.id = 1
                self.email = "test@example.com"
                self.created_at = datetime(2024, 1, 1, 12, 0, 0)
        
        mock_user = MockUser()
        
        # Act
        response = UserResponse.model_validate(mock_user)
        
        # Assert
        assert response.id == 1
        assert response.email == "test@example.com"
        assert response.created_at == mock_user.created_at
    
    def test_token_response_valid(self):
        """Тест: валидные данные токена"""
        # Act
        token = TokenResponse(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            token_type="bearer",
            expires_in=1800
        )
        
        # Assert
        assert token.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert token.token_type == "bearer"
        assert token.expires_in == 1800
    
    def test_token_response_default_token_type(self):
        """Тест: токен с дефолтным типом"""
        # Act
        token = TokenResponse(
            access_token="token123",
            expires_in=1800
        )
        
        # Assert
        assert token.token_type == "bearer"  # Дефолтное значение
        assert token.expires_in == 1800
    
    def test_user_register_email_normalization(self):
        """Тест: нормализация email при регистрации"""
        # Pydantic автоматически нормализует email
        # Act
        user = UserRegister(
            email="TEST@EXAMPLE.COM",
            password="StrongPass123!",
            password_confirm="StrongPass123!"
        )
        
        # Assert
        assert user.email == "TEST@EXAMPLE.COM"  # Pydantic не меняет case для локальной части
    
    def test_user_login_email_normalization(self):
        """Тест: нормализация email при входе"""
        # Act
        login = UserLogin(
            email="TEST@EXAMPLE.COM",
            password="StrongPass123!"
        )
        
        # Assert
        assert login.email == "test@example.com"
    
    @pytest.mark.parametrize("email", [
        "user@example.com",
        "user.name@example.com",
        "user+tag@example.com",
        "user@sub.example.com",
        "user@example.co.uk",
        "123@example.com",
        "user@123.com",
    ])
    def test_valid_email_formats(self, email):
        """Тест: различные валидные форматы email"""
        # Act & Assert
        UserRegister(
            email=email,
            password="StrongPass123!",
            password_confirm="StrongPass123!"
        )
        # Не должно быть исключения
    
    @pytest.mark.parametrize("email", [
        "invalid",
        "@example.com",
        "user@",
        "user@.com",
        "user@example.",
        "user example.com",
        "user@example..com",
    ])
    def test_invalid_email_formats(self, email):
        """Тест: различные невалидные форматы email"""
        with pytest.raises(ValidationError):
            UserRegister(
                email=email,
                password="StrongPass123!",
                password_confirm="StrongPass123!"
            )
    
    def test_schema_configs(self):
        """Тест: конфигурации схем"""
        # Проверяем что у UserResponse включен orm_mode
        assert UserResponse.Config.orm_mode is True
        
        # Проверяем что у TokenResponse есть дефолты
        token = TokenResponse(access_token="test", expires_in=3600)
        assert token.token_type == "bearer"  # Из дефолта
    
    def test_serialization(self):
        """Тест: сериализация схем"""
        # Arrange
        user_response = UserResponse(
            id=1,
            email="test@example.com",
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        # Act
        json_str = user_response.json()
        
        # Assert
        assert "test@example.com" in json_str
        assert '"id": 1' in json_str
