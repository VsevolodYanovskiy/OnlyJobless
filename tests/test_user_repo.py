import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.back.auth.repositories.user_repo import UserRepository
from src.back.auth.models.user_auth import User


class TestUserRepository:
    """Тесты для репозитория пользователей"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Фикстура для мок-сессии БД"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = AsyncMock()
        return session
    
    @pytest.fixture
    def user_repository(self, mock_db_session):
        """Фикстура для репозитория"""
        return UserRepository(mock_db_session)
    
    @pytest.fixture
    def mock_user(self):
        """Фикстура для мок-пользователя"""
        user = MagicMock(spec=User)
        user.id = 1
        user.email_encrypted = "encrypted_email_123"
        user.email_salt = "salt_123"
        user.password_hash = "hashed_password_123"
        user.created_at = datetime(2024, 1, 1)
        user.updated_at = datetime(2024, 1, 1)
        user.email = "test@example.com"  # Свойство для дешифрованного email
        return user
    
    @pytest.fixture
    def mock_result(self, mock_user):
        """Фикстура для мок-результата запроса"""
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_user
        result.scalars.return_value.all.return_value = [mock_user]
        result.scalar.return_value = 1  # Для count
        return result
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repository, mock_db_session, mock_user):
        """Тест: успешное создание пользователя"""
        # Arrange
        mock_db_session.execute.return_value = MagicMock(scalar_one_or_none=AsyncMock(return_value=None))
        mock_db_session.commit.return_value = None
        
        user_data = {
            'email': 'test@example.com',
            'password_hash': 'hashed_password_123'
        }
        
        # Act
        result = await user_repository.create_user(user_data)
        
        # Assert
        assert result is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, user_repository):
        """Тест: создание пользователя с невалидным email"""
        # Arrange
        user_data = {
            'email': 'invalid-email',
            'password_hash': 'hashed_password_123'
        }
        
        # Act
        result = await user_repository.create_user(user_data)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_user_existing_email(self, user_repository, mock_db_session, mock_user):
        """Тест: создание пользователя с существующим email"""
        # Arrange
        # get_user_by_email возвращает существующего пользователя
        user_repository.get_user_by_email = AsyncMock(return_value=mock_user)
        
        user_data = {
            'email': 'existing@example.com',
            'password_hash': 'hashed_password_123'
        }
        
        # Act
        result = await user_repository.create_user(user_data)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_user_integrity_error(self, user_repository, mock_db_session):
        """Тест: обработка ошибки целостности при создании"""
        # Arrange
        mock_db_session.commit.side_effect = IntegrityError("test", "test", "test")
        mock_db_session.execute.return_value = MagicMock(scalar_one_or_none=AsyncMock(return_value=None))
        
        user_data = {
            'email': 'test@example.com',
            'password_hash': 'hashed_password_123'
        }
        
        # Act
        result = await user_repository.create_user(user_data)
        
        # Assert
        assert result is None
        mock_db_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_repository, mock_db_session, mock_result):
        """Тест: успешное получение пользователя по ID"""
        # Arrange
        mock_db_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.get_user_by_id(1)
        
        # Assert
        assert result is not None
        assert result.id == 1
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_repository, mock_db_session):
        """Тест: получение несуществующего пользователя по ID"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.get_user_by_id(999)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_repository, mock_db_session, mock_user):
        """Тест: успешное получение пользователя по email"""
        # Arrange - ПРАВИЛЬНОЕ async мокирование
        mock_scalars = MagicMock()
        mock_scalars.all = AsyncMock(return_value=[mock_user])
        
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        
        # Важно: execute должен возвращать результат, а не корутину
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await user_repository.get_user_by_email("test@example.com")
        
        # Assert
        assert result is not None
        assert result.id == 1
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_repository, mock_db_session):
        """Тест: получение пользователя по несуществующему email"""
        # Arrange
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        
        # Act
        result = await user_repository.get_user_by_email("nonexistent@example.com")
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_repository, mock_db_session, mock_user):
        """Тест: успешное обновление пользователя"""
        # Arrange
        user_repository.get_user_by_id = AsyncMock(return_value=mock_user)
        user_repository.get_user_by_email = AsyncMock(return_value=None)
        
        update_data = {
            'email': 'new@example.com',
            'password_hash': 'new_hash'
        }
        
        # Act
        result = await user_repository.update_user(1, update_data)
        
        # Assert
        assert result is not None
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_repository):
        """Тест: обновление несуществующего пользователя"""
        # Arrange
        user_repository.get_user_by_id = AsyncMock(return_value=None)
        
        # Act
        result = await user_repository.update_user(999, {})
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user_email_already_exists(self, user_repository, mock_user):
        """Тест: обновление email на уже существующий"""
        # Arrange
        user_repository.get_user_by_id = AsyncMock(return_value=mock_user)
        
        other_user = MagicMock(spec=User)
        other_user.id = 2
        user_repository.get_user_by_email = AsyncMock(return_value=other_user)
        
        # Act
        result = await user_repository.update_user(1, {'email': 'existing@example.com'})
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_repository, mock_db_session, mock_user):
        """Тест: успешное удаление пользователя"""
        # Arrange
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none = AsyncMock(return_value=mock_user)
        
        mock_db_session.execute = AsyncMock(return_value=mock_execute_result)
        
        # ВАЖНО: delete должен быть AsyncMock
        mock_db_session.delete = AsyncMock()
        
        # Act
        result = await user_repository.delete_user(1)
        
        # Assert
        assert result is True
        mock_db_session.delete.assert_awaited_once_with(mock_user)  # assert_awaited_once_with для async
        mock_db_session.commit.assert_awaited_once()

    @pytest.mark.asyncio  
    async def test_delete_user_not_found(self, user_repository, mock_db_session):
        """Тест: удаление несуществующего пользователя"""
        # Arrange
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none = AsyncMock(return_value=None)
        
        mock_db_session.execute = AsyncMock(return_value=mock_execute_result)
        
        # Act
        result = await user_repository.delete_user(999)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_all_users(self, user_repository, mock_db_session, mock_result):
        """Тест: получение всех пользователей"""
        # Arrange
        mock_db_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.get_all_users(limit=10, offset=0)
        
        # Assert
        assert len(result) == 1
        assert result[0].id == 1
    
    @pytest.mark.asyncio
    async def test_count_users(self, user_repository, mock_db_session):
        """Тест: подсчет пользователей"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.count_users()
        
        # Assert
        assert result == 5
