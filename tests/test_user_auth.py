import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import Column, Integer, String, DateTime
from src.back.auth.models.user_auth import User, UserUtils, Base
from src.back.auth.models.encryption import DataEncryptor


class TestUserModel:
    """Тесты для модели пользователя"""
    
    @pytest.fixture
    def mock_encryptor(self):
        """Фикстура для мок-шифратора"""
        encryptor = Mock(spec=DataEncryptor)
        encryptor.encrypt.return_value = ("encrypted_email", "test_salt")
        encryptor.decrypt.return_value = "test@example.com"
        return encryptor
    
    @pytest.fixture
    def sample_user_data(self):
        """Фикстура с тестовыми данными пользователя"""
        return {
            'email': 'test@example.com',
            'password_hash': 'hashed_password_123'
        }
    
    def test_user_table_name(self):
        """Тест: имя таблицы пользователя"""
        assert User.__tablename__ == 'users'
    
    def test_user_columns_exist(self):
        """Тест: наличие всех колонок в модели"""
        columns = {col.name for col in User.__table__.columns}
        expected_columns = {
            'id', 'email_encrypted', 'email_salt', 
            'password_hash', 'created_at', 'updated_at'
        }
        assert columns == expected_columns
    
    def test_user_email_property_getter(self, mock_encryptor):
        """Тест: получение email через property"""
        # Arrange
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = User()
            user.email_encrypted = "encrypted_email"
            user.email_salt = "test_salt"
            
            # Act
            email = user.email
            
            # Assert
            mock_encryptor.decrypt.assert_called_once_with("encrypted_email", "test_salt")
            assert email == "test@example.com"
    
    def test_user_email_property_setter(self, mock_encryptor):
        """Тест: установка email через property"""
        # Arrange
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = User()
            
            # Act
            user.email = "new@example.com"
            
            # Assert
            mock_encryptor.encrypt.assert_called_once_with("new@example.com")
            assert user.email_encrypted == "encrypted_email"
            assert user.email_salt == "test_salt"
    
    def test_user_initialization_with_email(self, mock_encryptor):
        """Тест: инициализация пользователя с email"""
        # Arrange
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            # Act
            user = User(email="test@example.com", password_hash="hash123")
            
            # Assert
            mock_encryptor.encrypt.assert_called_once_with("test@example.com")
            assert user.email_encrypted == "encrypted_email"
            assert user.email_salt == "test_salt"
            assert user.password_hash == "hash123"
    
    def test_user_initialization_without_email(self):
        """Тест: инициализация пользователя без email"""
        # Act
        user = User()
        
        # Assert
        assert user.email_encrypted is None
        assert user.email_salt is None
        assert user.password_hash is None
    
    def test_to_dict_without_encrypted(self, mock_encryptor):
        """Тест: преобразование в словарь без зашифрованных данных"""
        # Arrange
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = User()
            user.id = 1
            user.email_encrypted = "encrypted"
            user.email_salt = "salt"
            user.password_hash = "hash"
            user.created_at = datetime(2024, 1, 1, 12, 0, 0)
            user.updated_at = datetime(2024, 1, 2, 12, 0, 0)
            
            # Act
            result = user.to_dict(include_encrypted=False)
            
            # Assert
            assert result == {
                'id': 1,
                'email': 'test@example.com',  # Декодируется
                'created_at': '2024-01-01T12:00:00',
                'updated_at': '2024-01-02T12:00:00'
            }
            assert 'email_encrypted' not in result
            assert 'email_salt' not in result
            assert 'password_hash' not in result
    
    def test_to_dict_with_encrypted(self, mock_encryptor):
        """Тест: преобразование в словарь с зашифрованными данными"""
        # Arrange
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = User()
            user.id = 1
            user.email_encrypted = "encrypted"
            user.email_salt = "salt"
            user.password_hash = "hash"
            user.created_at = datetime(2024, 1, 1, 12, 0, 0)
            user.updated_at = datetime(2024, 1, 2, 12, 0, 0)
            
            # Act
            result = user.to_dict(include_encrypted=True)
            
            # Assert
            assert result == {
                'id': 1,
                'email': 'test@example.com',
                'created_at': '2024-01-01T12:00:00',
                'updated_at': '2024-01-02T12:00:00',
                'email_encrypted': 'encrypted',
                'email_salt': 'salt',
                'password_hash': 'hash'
            }
    
    def test_from_dict_with_encryption(self, mock_encryptor):
        """Тест: создание из словаря с шифрованием"""
        # Arrange
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            data = {
                'email': 'test@example.com',
                'password_hash': 'hash123',
                'id': 1,
                'created_at': '2024-01-01T12:00:00',
                'updated_at': '2024-01-02T12:00:00'
            }
            
            # Act
            user = User.from_dict(data, encrypt_email=True)
            
            # Assert
            mock_encryptor.encrypt.assert_called_once_with('test@example.com')
            assert user.email_encrypted == 'encrypted_email'
            assert user.email_salt == 'test_salt'
            assert user.password_hash == 'hash123'
            assert user.id == 1
            assert user.created_at == datetime(2024, 1, 1, 12, 0, 0)
            assert user.updated_at == datetime(2024, 1, 2, 12, 0, 0)
    
    def test_from_dict_without_encryption(self):
        """Тест: создание из словаря без шифрования"""
        # Arrange
        data = {
            'email_encrypted': 'encrypted123',
            'email_salt': 'salt123',
            'password_hash': 'hash123',
            'id': 1
        }
        
        # Act
        user = User.from_dict(data, encrypt_email=False)
        
        # Assert
        assert user.email_encrypted == 'encrypted123'
        assert user.email_salt == 'salt123'
        assert user.password_hash == 'hash123'
        assert user.id == 1
    
    def test_from_dict_with_datetime_objects(self):
        """Тест: создание из словаря с объектами datetime"""
        # Arrange
        created = datetime(2024, 1, 1)
        updated = datetime(2024, 1, 2)
        data = {
            'id': 1,
            'created_at': created,
            'updated_at': updated
        }
        
        # Act
        user = User.from_dict(data)
        
        # Assert
        assert user.id == 1
        assert user.created_at == created
        assert user.updated_at == updated
    
    def test_update_email(self, mock_encryptor):
        """Тест: безопасное обновление email"""
        # Arrange
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = User()
            
            # Act
            user.update_email('new@example.com')
            
            # Assert
            mock_encryptor.encrypt.assert_called_once_with('new@example.com')
            assert user.email_encrypted == 'encrypted_email'
            assert user.email_salt == 'test_salt'
            # updated_at должен быть установлен, но мы не можем точно проверить значение
    
    def test_verify_email_correct(self, mock_encryptor):
        """Тест: проверка правильного email"""
        # Arrange
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = User()
            
            # Act
            result = user.verify_email('test@example.com')
            
            # Assert
            assert result is True
    
    def test_verify_email_incorrect(self, mock_encryptor):
        """Тест: проверка неправильного email"""
        # Arrange
        mock_encryptor.decrypt.return_value = 'different@example.com'
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = User()
            
            # Act
            result = user.verify_email('test@example.com')
            
            # Assert
            assert result is False
    
    def test_create_from_plain(self, mock_encryptor):
        """Тест: создание пользователя из незашифрованных данных"""
        # Arrange
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            # Act
            user = User.create_from_plain(
                email='test@example.com',
                password_hash='hash123'
            )
            
            # Assert
            mock_encryptor.encrypt.assert_called_once_with('test@example.com')
            assert user.email_encrypted == 'encrypted_email'
            assert user.email_salt == 'test_salt'
            assert user.password_hash == 'hash123'


class TestUserUtils:
    """Тесты для вспомогательных функций пользователя"""
    
    def test_validate_email_format_valid(self):
        """Тест: валидация правильного email"""
        valid_emails = [
            'test@example.com',
            'user.name@example.com',
            'user+tag@example.com',
            'a@b.co'
        ]
        
        for email in valid_emails:
            assert UserUtils.validate_email_format(email) is True
    
    def test_validate_email_format_invalid(self):
        """Тест: валидация неправильного email"""
        invalid_emails = [
            '',  # Пустой
            'invalid',  # Нет @
            '@example.com',  # Нет локальной части
            'test@',  # Нет домена
            'a' * 256 + '@example.com'  # Слишком длинный
        ]
        
        for email in invalid_emails:
            assert UserUtils.validate_email_format(email) is False
    
    def test_mask_email_normal(self):
        """Тест: маскирование обычного email"""
        # Act
        masked = UserUtils.mask_email('john.doe@example.com')
        
        # Assert
        assert masked == 'j*********e@example.com'
    
    def test_mask_email_short_local_part(self):
        """Тест: маскирование email с короткой локальной частью"""
        # Act
        masked = UserUtils.mask_email('ab@example.com')
        
        # Assert
        assert masked == '**@example.com'
    
    def test_mask_email_very_short_local_part(self):
        """Тест: маскирование email с очень короткой локальной частью"""
        # Act
        masked = UserUtils.mask_email('a@example.com')
        
        # Assert
        assert masked == '*@example.com'
    
    def test_mask_email_invalid_format(self):
        """Тест: маскирование некорректного email"""
        # Act
        masked = UserUtils.mask_email('not-an-email')
        
        # Assert
        assert masked == 'not-an-email'
    
    def test_users_to_dict_list(self, mock_encryptor):
        """Тест: преобразование списка пользователей"""
        # Arrange
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            users = []
            for i in range(3):
                user = Mock(spec=User)
                user.to_dict.return_value = {'id': i, 'email': f'user{i}@example.com'}
                users.append(user)
            
            # Act
            result = UserUtils.users_to_dict_list(users, include_encrypted=False)
            
            # Assert
            assert len(result) == 3
            for i in range(3):
                assert result[i] == {'id': i, 'email': f'user{i}@example.com'}
                users[i].to_dict.assert_called_once_with(include_encrypted=False)
    
    def test_users_to_dict_list_with_encrypted(self, mock_encryptor):
        """Тест: преобразование списка с зашифрованными данными"""
        # Arrange
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = Mock(spec=User)
            user.to_dict.return_value = {'id': 1, 'email': 'test@example.com', 'email_encrypted': 'enc'}
            
            # Act
            result = UserUtils.users_to_dict_list([user], include_encrypted=True)
            
            # Assert
            user.to_dict.assert_called_once_with(include_encrypted=True)
            assert result == [{'id': 1, 'email': 'test@example.com', 'email_encrypted': 'enc'}]


class TestBaseModel:
    """Тесты базовой модели SQLAlchemy"""
    
    def test_base_is_declarative_base(self):
        """Тест: Base является declarative_base"""
        assert Base.__class__.__name__ == 'DeclarativeMeta'
    
    def test_base_has_metadata(self):
        """Тест: Base имеет метаданные"""
        assert hasattr(Base, 'metadata')
        assert Base.metadata is not None


@pytest.mark.asyncio
async def test_user_model_integration():
    """Интеграционный тест: создание и использование пользователя"""
    # Этот тест можно расширить для проверки реального шифрования
    # Пока просто проверяем что модель вообще работает
    user = User()
    assert user is not None
    assert hasattr(user, 'id')
    assert hasattr(user, 'email')
