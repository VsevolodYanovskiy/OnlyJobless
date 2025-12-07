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
        session.delete = MagicMock()
        
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
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
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_result(self, mock_user):
        """Фикстура для мок-результата запроса"""
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_user
        result.scalars.return_value.all.return_value = [mock_user]
        result.scalar.return_value = 1
        return result
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repository, mock_db_session, mock_user):
        """Тест: успешное создание пользователя"""

        mock_db_session.execute.return_value = MagicMock(scalar_one_or_none=AsyncMock(return_value=None))
        mock_db_session.commit.return_value = None
        
        user_data = {
            'email': 'test@example.com',
            'password_hash': 'hashed_password_123'
        }

        result = await user_repository.create_user(user_data)

        assert result is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, user_repository):
        """Тест: создание пользователя с невалидным email"""

        user_data = {
            'email': 'invalid-email',
            'password_hash': 'hashed_password_123'
        }

        result = await user_repository.create_user(user_data)

        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_user_existing_email(self, user_repository, mock_db_session, mock_user):
        """Тест: создание пользователя с существующим email"""
        user_repository.get_user_by_email = AsyncMock(return_value=mock_user)
        
        user_data = {
            'email': 'existing@example.com',
            'password_hash': 'hashed_password_123'
        }
        
        result = await user_repository.create_user(user_data)

        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_user_integrity_error(self, user_repository, mock_db_session):
        """Тест: обработка ошибки целостности при создании"""

        mock_db_session.commit.side_effect = IntegrityError("test", "test", "test")
        mock_db_session.execute.return_value = MagicMock(scalar_one_or_none=AsyncMock(return_value=None))
        
        user_data = {
            'email': 'test@example.com',
            'password_hash': 'hashed_password_123'
        }

        result = await user_repository.create_user(user_data)

        assert result is None
        mock_db_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_repository, mock_db_session, mock_result):
        """Тест: успешное получение пользователя по ID"""

        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_user_by_id(1)

        assert result is not None
        assert result.id == 1
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_repository, mock_db_session):
        """Тест: получение несуществующего пользователя по ID"""

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_user_by_id(999)

        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_repository, mock_db_session, mock_user):
        """Тест: успешное получение пользователя по email"""
        mock_user.email = "test@example.com"
        mock_scalar_result = MagicMock()
        mock_scalar_result.all = MagicMock(return_value=[mock_user])  # ← НЕ AsyncMock!
        
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_scalar_result)
        
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        result = await user_repository.get_user_by_email("test@example.com")
        assert result is not None
        assert result.id == 1
        assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_repository, mock_db_session):
        """Тест: получение пользователя по несуществующему email"""
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        result = await user_repository.get_user_by_email("nonexistent@example.com")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_repository, mock_db_session, mock_user):
        """Тест: успешное обновление пользователя"""
        user_repository.get_user_by_id = AsyncMock(return_value=mock_user)
        user_repository.get_user_by_email = AsyncMock(return_value=None)
        
        update_data = {
            'email': 'new@example.com',
            'password_hash': 'new_hash'
        }
        result = await user_repository.update_user(1, update_data)
        assert result is not None
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_repository):
        """Тест: обновление несуществующего пользователя"""
        user_repository.get_user_by_id = AsyncMock(return_value=None)
        result = await user_repository.update_user(999, {})
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user_email_already_exists(self, user_repository, mock_user):
        """Тест: обновление email на уже существующий"""
        user_repository.get_user_by_id = AsyncMock(return_value=mock_user)
        
        other_user = MagicMock(spec=User)
        other_user.id = 2
        user_repository.get_user_by_email = AsyncMock(return_value=other_user)
        result = await user_repository.update_user(1, {'email': 'existing@example.com'})
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_repository, mock_db_session, mock_user):
        """Тест: успешное удаление пользователя"""
        user_repository.get_user_by_id = AsyncMock(return_value=mock_user)
        mock_db_session.delete = AsyncMock()
        mock_db_session.commit = AsyncMock()
        result = await user_repository.delete_user(1)
        assert result is True
        mock_db_session.delete.assert_called_once_with(mock_user)
        mock_db_session.commit.assert_awaited_once()

    @pytest.mark.asyncio  
    async def test_delete_user_not_found(self, user_repository, mock_db_session):
        """Тест: удаление несуществующего пользователя"""
        user_repository.get_user_by_id = AsyncMock(return_value=None)
        result = await user_repository.delete_user(999)
        assert result is False
        mock_db_session.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_all_users(self, user_repository, mock_db_session, mock_result):
        """Тест: получение всех пользователей"""
        mock_db_session.execute.return_value = mock_result
        result = await user_repository.get_all_users(limit=10, offset=0)
        assert len(result) == 1
        assert result[0].id == 1
    
    @pytest.mark.asyncio
    async def test_count_users(self, user_repository, mock_db_session):
        """Тест: подсчет пользователей"""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db_session.execute.return_value = mock_result
        result = await user_repository.count_users()
        assert result == 5
