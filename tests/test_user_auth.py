import pytest
import re
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from sqlalchemy import Column, Integer, String, DateTime
from src.back.auth.models.user_auth import User, UserUtils, Base
from src.back.auth.models.encryption import DataEncryptor


@pytest.fixture
def mock_encryptor():
    """Фикстура для мок-шифратора на уровне модуля"""
    encryptor = Mock(spec=DataEncryptor)
    encryptor.encrypt.return_value = ("encrypted_email", "test_salt")
    encryptor.decrypt.return_value = "test@example.com"
    return encryptor


class TestUserModel:
    """Тесты для модели пользователя"""
    
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
    
    def test_user_columns_nullable(self):
        """Тест: проверка nullable полей"""
        assert User.__table__.c.email_encrypted.nullable is True
        assert User.__table__.c.email_salt.nullable is True
        assert User.__table__.c.password_hash.nullable is True
        assert User.__table__.c.id.nullable is False
    
    def test_user_email_property_getter(self, mock_encryptor):
        """Тест: получение email через property"""
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = User()
            user.email_encrypted = "encrypted_email"
            user.email_salt = "test_salt"

            email = user.email

            mock_encryptor.decrypt.assert_called_once_with("encrypted_email", "test_salt")
            assert email == "test@example.com"
    
    def test_user_email_property_getter_none(self):
        """Тест: получение email когда поля пустые"""
        user = User()
        assert user.email is None
    
    def test_user_email_property_setter(self, mock_encryptor):
        """Тест: установка email через property"""
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = User()

            user.email = "new@example.com"

            mock_encryptor.encrypt.assert_called_once_with("new@example.com")
            assert user.email_encrypted == "encrypted_email"
            assert user.email_salt == "test_salt"
    
    def test_user_email_property_setter_none(self):
        """Тест: установка email в None"""
        user = User()
        user.email_encrypted = "encrypted"
        user.email_salt = "salt"
        
        user.email = None
        
        assert user.email_encrypted is None
        assert user.email_salt is None
    
    def test_user_initialization_with_email(self, mock_encryptor):
        """Тест: инициализация пользователя с email"""
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = User(email="test@example.com", password_hash="hash123")

            mock_encryptor.encrypt.assert_called_once_with("test@example.com")
            assert user.email_encrypted == "encrypted_email"
            assert user.email_salt == "test_salt"
            assert user.password_hash == "hash123"
    
    def test_user_initialization_without_email(self):
        """Тест: инициализация пользователя без email"""
        user = User()

        assert user.email_encrypted is None
        assert user.email_salt is None
        assert user.password_hash is None
    
    def test_user_initialization_with_kwargs(self):
        """Тест: инициализация пользователя с дополнительными параметрами"""
        user = User(id=1, created_at=datetime(2024, 1, 1))
        assert user.id == 1
        assert user.created_at == datetime(2024, 1, 1)
    
    def test_to_dict_without_encrypted(self, mock_encryptor):
        """Тест: преобразование в словарь без зашифрованных данных"""
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = User()
            user.id = 1
            user.email_encrypted = "encrypted"
            user.email_salt = "salt"
            user.password_hash = "hash"
            user.created_at = datetime(2024, 1, 1, 12, 0, 0)
            user.updated_at = datetime(2024, 1, 2, 12, 0, 0)

            # Используем PropertyMock для мока property
            with patch.object(User, 'email', new_callable=PropertyMock) as mock_email:
                mock_email.return_value = 'test@example.com'
                result = user.to_dict(include_encrypted=False)

            assert result == {
                'id': 1,
                'email': 'test@example.com',
                'created_at': '2024-01-01T12:00:00',
                'updated_at': '2024-01-02T12:00:00'
            }
            assert 'email_encrypted' not in result
            assert 'email_salt' not in result
            assert 'password_hash' not in result
    
    def test_to_dict_with_encrypted(self, mock_encryptor):
        """Тест: преобразование в словарь с зашифрованными данными"""
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = User()
            user.id = 1
            user.email_encrypted = "encrypted"
            user.email_salt = "salt"
            user.password_hash = "hash"
            user.created_at = datetime(2024, 1, 1, 12, 0, 0)
            user.updated_at = datetime(2024, 1, 2, 12, 0, 0)

            # Используем PropertyMock для мока property
            with patch.object(User, 'email', new_callable=PropertyMock) as mock_email:
                mock_email.return_value = 'test@example.com'
                result = user.to_dict(include_encrypted=True)

            assert result == {
                'id': 1,
                'email': 'test@example.com',
                'created_at': '2024-01-01T12:00:00',
                'updated_at': '2024-01-02T12:00:00',
                'email_encrypted': 'encrypted',
                'email_salt': 'salt',
                'password_hash': 'hash'
            }
    
    def test_to_dict_with_none_dates(self):
        """Тест: преобразование в словарь с None датами"""
        user = User()
        user.id = 1
        
        result = user.to_dict()
        
        assert result['id'] == 1
        assert result['email'] is None
        assert result['created_at'] is None
        assert result['updated_at'] is None
    
    def test_from_dict_with_encryption(self, mock_encryptor):
        """Тест: создание из словаря с шифрованием"""
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            data = {
                'email': 'test@example.com',
                'password_hash': 'hash123',
                'id': 1,
                'created_at': '2024-01-01T12:00:00',
                'updated_at': '2024-01-02T12:00:00'
            }

            user = User.from_dict(data, encrypt_email=True)

            mock_encryptor.encrypt.assert_called_once_with('test@example.com')
            assert user.email_encrypted == 'encrypted_email'
            assert user.email_salt == 'test_salt'
            assert user.password_hash == 'hash123'
            assert user.id == 1
            assert user.created_at == datetime(2024, 1, 1, 12, 0, 0)
            assert user.updated_at == datetime(2024, 1, 2, 12, 0, 0)
    
    def test_from_dict_without_encryption(self):
        """Тест: создание из словаря без шифрования"""
        data = {
            'email_encrypted': 'encrypted123',
            'email_salt': 'salt123',
            'password_hash': 'hash123',
            'id': 1
        }
        
        user = User.from_dict(data, encrypt_email=False)

        assert user.email_encrypted == 'encrypted123'
        assert user.email_salt == 'salt123'
        assert user.password_hash == 'hash123'
        assert user.id == 1
    
    def test_from_dict_only_email_encrypted(self):
        """Тест: создание из словаря только с email_encrypted"""
        data = {
            'email_encrypted': 'encrypted123',
            'id': 1
        }
        
        user = User.from_dict(data, encrypt_email=False)

        assert user.email_encrypted == 'encrypted123'
        assert user.email_salt is None  # Не было передано
        assert user.id == 1
    
    def test_from_dict_with_encrypted_data_directly(self):
        """Тест: создание из словаря с зашифрованными данными напрямую"""
        data = {
            'email_encrypted': 'encrypted123',
            'email_salt': 'salt123',
            'password_hash': 'hash123',
            'id': 1
        }
        
        # Не передаем 'email', только зашифрованные данные
        user = User.from_dict(data, encrypt_email=False)

        assert user.email_encrypted == 'encrypted123'
        assert user.email_salt == 'salt123'
        assert user.password_hash == 'hash123'
        assert user.id == 1
    
    def test_from_dict_with_datetime_objects(self):
        """Тест: создание из словаря с объектами datetime"""
        created = datetime(2024, 1, 1)
        updated = datetime(2024, 1, 2)
        data = {
            'id': 1,
            'created_at': created,
            'updated_at': updated
        }
        user = User.from_dict(data)
        assert user.id == 1
        assert user.created_at == created
        assert user.updated_at == updated
    
    def test_from_dict_empty(self):
        """Тест: создание из пустого словаря"""
        user = User.from_dict({})
        assert user.id is None
        assert user.email_encrypted is None
        assert user.email_salt is None
        assert user.password_hash is None
        assert user.created_at is None
        assert user.updated_at is None
    
    def test_update_email(self, mock_encryptor):
        """Тест: безопасное обновление email"""
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            with patch('src.back.auth.models.user_auth.datetime') as mock_datetime:
                mock_now = datetime(2024, 1, 3, 12, 0, 0)
                mock_datetime.datetime.utcnow.return_value = mock_now
                
                user = User()
                user.update_email('new@example.com')
                
                mock_encryptor.encrypt.assert_called_once_with('new@example.com')
                assert user.email_encrypted == 'encrypted_email'
                assert user.email_salt == 'test_salt'
                assert user.updated_at == mock_now
    
    def test_verify_email_correct(self):
        """Тест: проверка правильного email"""
        user = User()
        
        # Мокаем свойство email
        with patch.object(User, 'email', new_callable=PropertyMock) as mock_email:
            mock_email.return_value = 'test@example.com'
            result = user.verify_email('test@example.com')
            assert result is True
    
    def test_verify_email_incorrect(self):
        """Тест: проверка неправильного email"""
        user = User()
        
        # Мокаем свойство email
        with patch.object(User, 'email', new_callable=PropertyMock) as mock_email:
            mock_email.return_value = 'different@example.com'
            result = user.verify_email('test@example.com')
            assert result is False
    
    def test_verify_email_none(self):
        """Тест: проверка email когда email не установлен"""
        user = User()
        result = user.verify_email('test@example.com')
        assert result is False
    
    def test_create_from_plain(self, mock_encryptor):
        """Тест: создание пользователя из незашифрованных данных"""
        with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
            user = User.create_from_plain(
                email='test@example.com',
                password_hash='hash123'
            )
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
            'a@b.co',
            'user@sub.example.com',
            'user123@example.org',
            'first.last@example.co.uk'
        ]
        
        for email in valid_emails:
            assert UserUtils.validate_email_format(email) is True, f"Email '{email}' должен быть валидным"
    
    def test_validate_email_format_invalid(self):
        """Тест: валидация неправильного email"""
        invalid_emails = [
            '',  # пустой
            'invalid',  # нет @
            '@example.com',  # нет локальной части
            'test@',  # нет домена
            'test@.',  # некорректный домен
            'test@com',  # нет точки в домене
            '@',  # только @
            'test@example.',  # домен заканчивается точкой
            'test@.com',  # домен начинается с точки
            'user example.com',  # пробел вместо @
            'a' * 256 + '@example.com'  # слишком длинный
        ]
        
        for email in invalid_emails:
            assert UserUtils.validate_email_format(email) is False, f"Email '{email}' должен быть невалидным"
    
    def test_validate_email_format_edge_cases(self):
        """Тест: граничные случаи валидации email"""
        # Эти email должны быть валидными с текущей логикой
        assert UserUtils.validate_email_format('ab@example.com') is True
        assert UserUtils.validate_email_format('a@example.com') is True
        
        # Специальные символы в локальной части
        assert UserUtils.validate_email_format('user.name+tag@example.com') is True
        assert UserUtils.validate_email_format('user_name@example.com') is True
        assert UserUtils.validate_email_format('user-name@example.com') is True
        
        # Двойные точки в домене не допускаются
        assert UserUtils.validate_email_format('test@example..com') is False
    
    def test_mask_email_normal(self):
        """Тест: маскирование обычного email"""
        masked = UserUtils.mask_email('john.doe@example.com')
        # john.doe (8 символов) -> j + 6 звезд + e = j******e
        assert masked == 'j******e@example.com'
    
    def test_mask_email_short_local_part(self):
        """Тест: маскирование email с короткой локальной частью"""
        # 2 символа: ab -> a*
        masked = UserUtils.mask_email('ab@example.com')
        assert masked == 'a*@example.com'
    
    def test_mask_email_very_short_local_part(self):
        """Тест: маскирование email с очень короткой локальной частью"""
        # 1 символ: a -> *
        masked = UserUtils.mask_email('a@example.com')
        assert masked == '*@example.com'
    
    def test_mask_email_3_chars(self):
        """Тест: маскирование email с 3 символами в локальной части"""
        # abc -> a*c
        masked = UserUtils.mask_email('abc@example.com')
        assert masked == 'a*c@example.com'
    
    def test_mask_email_4_chars(self):
        """Тест: маскирование email с 4 символами в локальной части"""
        # abcd -> a**d
        masked = UserUtils.mask_email('abcd@example.com')
        assert masked == 'a**d@example.com'
    
    def test_mask_email_invalid_format(self):
        """Тест: маскирование некорректного email"""
        masked = UserUtils.mask_email('not-an-email')
        assert masked == 'not-an-email'
    
    def test_mask_email_empty(self):
        """Тест: маскирование пустого email"""
        masked = UserUtils.mask_email('')
        assert masked == ''
    
    def test_mask_email_none(self):
        """Тест: маскирование None - должно вернуть None"""
        masked = UserUtils.mask_email(None)
        assert masked is None
    
    def test_users_to_dict_list(self):
        """Тест: преобразование списка пользователей"""
        # Создаем мок-пользователей
        users = []
        for i in range(3):
            user = Mock(spec=User)
            user.to_dict.return_value = {'id': i, 'email': f'user{i}@example.com'}
            users.append(user)
        
        result = UserUtils.users_to_dict_list(users, include_encrypted=False)
        
        assert len(result) == 3
        for i in range(3):
            assert result[i] == {'id': i, 'email': f'user{i}@example.com'}
            users[i].to_dict.assert_called_once_with(include_encrypted=False)
    
    def test_users_to_dict_list_with_encrypted(self):
        """Тест: преобразование списка с зашифрованными данными"""
        user = Mock(spec=User)
        user.to_dict.return_value = {
            'id': 1, 
            'email': 'test@example.com', 
            'email_encrypted': 'enc'
        }
        
        result = UserUtils.users_to_dict_list([user], include_encrypted=True)
        
        user.to_dict.assert_called_once_with(include_encrypted=True)
        assert result == [{'id': 1, 'email': 'test@example.com', 'email_encrypted': 'enc'}]
    
    def test_users_to_dict_list_empty(self):
        """Тест: преобразование пустого списка пользователей"""
        result = UserUtils.users_to_dict_list([])
        assert result == []
    
    def test_users_to_dict_list_none(self):
        """Тест: преобразование None списка"""
        result = UserUtils.users_to_dict_list(None)
        assert result == []


class TestBaseModel:
    """Тесты базовой модели SQLAlchemy"""
    
    def test_base_is_declarative_base(self):
        """Тест: Base является declarative_base"""
        assert Base.__class__.__name__ == 'DeclarativeMeta'
    
    def test_base_has_metadata(self):
        """Тест: Base имеет метаданные"""
        assert hasattr(Base, 'metadata')
        assert Base.metadata is not None
    
    def test_base_metadata_tables(self):
        """Тест: метаданные содержат таблицы"""
        # Проверяем, что User таблица зарегистрирована в metadata
        assert 'users' in Base.metadata.tables


def test_user_model_integration():
    """Интеграционный тест: создание и использование пользователя"""
    user = User()
    assert user is not None
    assert hasattr(user, 'id')
    
    # Проверяем, что есть property email
    assert hasattr(type(user), 'email')
    assert isinstance(type(user).email, property)
    
    # Проверяем наличие всех атрибутов
    assert hasattr(user, 'email_encrypted')
    assert hasattr(user, 'email_salt')
    assert hasattr(user, 'password_hash')
    assert hasattr(user, 'created_at')
    assert hasattr(user, 'updated_at')
    
    # Проверяем методы
    assert hasattr(user, 'to_dict')
    assert hasattr(user, 'update_email')
    assert hasattr(user, 'verify_email')
    
    # Проверяем classmethod
    assert hasattr(User, 'from_dict')
    assert hasattr(User, 'create_from_plain')


def test_user_utils_static_methods():
    """Тест: статические методы UserUtils"""
    # Проверяем, что методы статические
    assert UserUtils.validate_email_format('test@example.com') is True
    assert UserUtils.mask_email('test@example.com') == 't**t@example.com'
    
    # Проверяем метод users_to_dict_list с пустым списком
    assert UserUtils.users_to_dict_list([]) == []


@pytest.mark.parametrize("email,expected", [
    ('test@example.com', True),
    ('user.name@example.com', True),
    ('user+tag@example.com', True),
    ('a@b.co', True),
    ('', False),
    ('invalid', False),
    ('@example.com', False),
    ('test@', False),
])
def test_validate_email_format_parametrized(email, expected):
    """Параметризованный тест валидации email"""
    assert UserUtils.validate_email_format(email) == expected


@pytest.mark.parametrize("email,expected", [
    ('a@example.com', '*@example.com'),
    ('ab@example.com', 'a*@example.com'),
    ('abc@example.com', 'a*c@example.com'),
    ('abcd@example.com', 'a**d@example.com'),
    ('abcde@example.com', 'a***e@example.com'),
    ('john.doe@example.com', 'j******e@example.com'),
    ('not-an-email', 'not-an-email'),
    ('', ''),
])
def test_mask_email_parametrized(email, expected):
    """Параметризованный тест маскирования email"""
    assert UserUtils.mask_email(email) == expected


def test_user_encryption_integration(mock_encryptor):
    """Интеграционный тест шифрования email"""
    with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
        # Создание пользователя
        user = User(email='test@example.com', password_hash='hash123')
        
        # Проверка шифрования при создании
        mock_encryptor.encrypt.assert_called_once_with('test@example.com')
        
        # Проверка получения email
        email = user.email
        mock_encryptor.decrypt.assert_called_once()
        
        # Обновление email
        user.update_email('new@example.com')
        assert mock_encryptor.encrypt.call_count == 2
        mock_encryptor.encrypt.assert_called_with('new@example.com')


def test_user_serialization_cycle(mock_encryptor):
    """Тест полного цикла сериализации/десериализации"""
    with patch('src.back.auth.models.user_auth.encryptor', mock_encryptor):
        # Создаем пользователя
        original_user = User(
            email='test@example.com',
            password_hash='hash123'
        )
        original_user.id = 1
        original_user.created_at = datetime(2024, 1, 1)
        original_user.updated_at = datetime(2024, 1, 2)
        
        # Сериализуем в словарь
        user_dict = original_user.to_dict(include_encrypted=True)
        
        # Десериализуем обратно
        restored_user = User.from_dict(user_dict, encrypt_email=False)
        
        # Проверяем, что данные совпадают
        assert restored_user.id == original_user.id
        assert restored_user.email_encrypted == original_user.email_encrypted
        assert restored_user.email_salt == original_user.email_salt
        assert restored_user.password_hash == original_user.password_hash
        assert restored_user.created_at == original_user.created_at
        assert restored_user.updated_at == original_user.updated_at
