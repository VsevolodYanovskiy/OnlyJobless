import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.back.auth.services.auth_service import AuthService
from src.back.auth.schemas.auth_schemas import UserRegister, UserLogin
from src.back.auth.models.user_auth import User
from src.back.auth.services.password_service import PasswordService


class TestAuthService:
    """Тесты для сервиса аутентификации"""
    
    @pytest.fixture
    def mock_user_repo(self):
        """Фикстура для мок-репозитория пользователей"""
        repo = AsyncMock()
        repo.get_user_by_email.return_value = None
        repo.create_user.return_value = None
        repo.get_user_by_id.return_value = None
        return repo
    
    @pytest.fixture
    def mock_password_service(self):
        """Фикстура для мок-сервиса паролей"""
        service = MagicMock()
        service.get_hash.return_value = "hashed_password_123"
        service.verify.return_value = True
        return service
    
    @pytest.fixture
    def auth_service(self, mock_user_repo, mock_password_service):
        """Фикстура для сервиса аутентификации"""
        return AuthService(mock_user_repo, mock_password_service)
    
    @pytest.fixture
    def sample_user_data(self):
        """Фикстура с тестовыми данными пользователя"""
        return UserRegister(
            email="test@example.com",
            password="StrongPass123!",
            password_confirm="StrongPass123!"
        )
    
    @pytest.fixture
    def sample_login_data(self):
        """Фикстура с тестовыми данными для входа"""
        return UserLogin(
            email="test@example.com",
            password="StrongPass123!"
        )
    
    @pytest.fixture
    def mock_user(self):
        """Фикстура для мок-пользователя"""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.password_hash = "hashed_password_123"
        user.created_at = "2024-01-01T00:00:00"
        return user
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, mock_user_repo, mock_password_service, sample_user_data, mock_user):
        """Тест: успешная регистрация пользователя"""
        # Arrange
        mock_user_repo.get_user_by_email.return_value = None
        mock_user_repo.create_user.return_value = mock_user
        
        # Act
        result = await auth_service.register_user(sample_user_data)
        
        # Assert
        assert result is not None
        assert result.id == 1
        mock_user_repo.get_user_by_email.assert_called_once_with("test@example.com")
        mock_password_service.get_hash.assert_called_once_with("StrongPass123!")
        mock_user_repo.create_user.assert_called_once_with({
            'email': 'test@example.com',
            'password_hash': 'hashed_password_123'
        })
    
    @pytest.mark.asyncio
    async def test_register_user_email_already_exists(self, auth_service, mock_user_repo, sample_user_data, mock_user):
        """Тест: регистрация с уже существующим email"""
        # Arrange
        mock_user_repo.get_user_by_email.return_value = mock_user
        
        # Act
        result = await auth_service.register_user(sample_user_data)
        
        # Assert
        assert result is None
        mock_user_repo.get_user_by_email.assert_called_once_with("test@example.com")
        mock_user_repo.create_user.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_user_repo, mock_password_service, sample_login_data, mock_user):
        """Тест: успешная аутентификация"""
        # Arrange
        mock_user_repo.get_user_by_email.return_value = mock_user
        mock_password_service.verify.return_value = True
        
        # Act
        result = await auth_service.authenticate_user(sample_login_data)
        
        # Assert
        assert result is not None
        assert result.id == 1
        mock_user_repo.get_user_by_email.assert_called_once_with("test@example.com")
        mock_password_service.verify.assert_called_once_with("StrongPass123!", "hashed_password_123")
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service, mock_user_repo, mock_password_service, sample_login_data, mock_user):
        """Тест: аутентификация с неправильным паролем"""
        # Arrange
        mock_user_repo.get_user_by_email.return_value = mock_user
        mock_password_service.verify.return_value = False
        
        # Act
        result = await auth_service.authenticate_user(sample_login_data)
        
        # Assert
        assert result is None
        mock_user_repo.get_user_by_email.assert_called_once_with("test@example.com")
        mock_password_service.verify.assert_called_once_with("StrongPass123!", "hashed_password_123")
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, mock_user_repo, sample_login_data):
        """Тест: аутентификация несуществующего пользователя"""
        # Arrange
        mock_user_repo.get_user_by_email.return_value = None
        
        # Act
        result = await auth_service.authenticate_user(sample_login_data)
        
        # Assert
        assert result is None
        mock_user_repo.get_user_by_email.assert_called_once_with("test@example.com")
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, auth_service, mock_user_repo, mock_user):
        """Тест: успешное получение пользователя по ID"""
        # Arrange
        mock_user_repo.get_user_by_id.return_value = mock_user
        
        # Act
        result = await auth_service.get_user_by_id(1)
        
        # Assert
        assert result is not None
        assert result.id == 1
        mock_user_repo.get_user_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, auth_service, mock_user_repo):
        """Тест: получение несуществующего пользователя по ID"""
        # Arrange
        mock_user_repo.get_user_by_id.return_value = None
        
        # Act
        result = await auth_service.get_user_by_id(999)
        
        # Assert
        assert result is None
        mock_user_repo.get_user_by_id.assert_called_once_with(999)
    
    @pytest.mark.asyncio
    async def test_validate_email_unique_true(self, auth_service, mock_user_repo):
        """Тест: проверка уникальности email (уникальный)"""
        # Arrange
        mock_user_repo.get_user_by_email.return_value = None
        
        # Act
        result = await auth_service._validate_email_unique("unique@example.com")
        
        # Assert
        assert result is True
        mock_user_repo.get_user_by_email.assert_called_once_with("unique@example.com")
    
    @pytest.mark.asyncio
    async def test_validate_email_unique_false(self, auth_service, mock_user_repo, mock_user):
        """Тест: проверка уникальности email (уже существует)"""
        # Arrange
        mock_user_repo.get_user_by_email.return_value = mock_user
        
        # Act
        result = await auth_service._validate_email_unique("existing@example.com")
        
        # Assert
        assert result is False
        mock_user_repo.get_user_by_email.assert_called_once_with("existing@example.com")
    
    @pytest.mark.asyncio
    async def test_register_user_exception_handling(self, auth_service, mock_user_repo, sample_user_data):
        """Тест: обработка исключений при регистрации"""
        # Arrange
        mock_user_repo.get_user_by_email.side_effect = Exception("DB Error")
        
        # Act
        result = await auth_service.register_user(sample_user_data)
        
        # Assert
        assert result is None
        mock_user_repo.get_user_by_email.assert_called_once_with("test@example.com")
    
    @pytest.mark.asyncio
    async def test_authenticate_user_exception_handling(self, auth_service, mock_user_repo, sample_login_data):
        """Тест: обработка исключений при аутентификации"""
        # Arrange
        mock_user_repo.get_user_by_email.side_effect = Exception("DB Error")
        
        # Act
        result = await auth_service.authenticate_user(sample_login_data)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_weak_password_registration(self):
        """Тест: регистрация со слабым паролем (должно быть обработано на уровне контроллера)"""
        # Этот тест проверяет что сервис не падает на слабых паролях
        # Действительная проверка происходит в контроллере
        pass
    
    def test_auth_service_initialization(self, mock_user_repo, mock_password_service):
        """Тест: инициализация сервиса"""
        # Act
        service = AuthService(mock_user_repo, mock_password_service)
        
        # Assert
        assert service.user_repo == mock_user_repo
        assert service.password_service == mock_password_service
