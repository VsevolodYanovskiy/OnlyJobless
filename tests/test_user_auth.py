# test_user_auth.py
import pytest
from unittest.mock import Mock, patch, PropertyMock, MagicMock
from datetime import datetime
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем после добавления пути
from src.back.auth.models.user_auth import User, UserUtils, Base


class TestUserModel:
    """Тесты для модели User"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        # Создаем мок для encryptor
        self.encryptor_mock = Mock()
        self.encryptor_mock.encrypt.return_value = ('encrypted_email', 'test_salt')
        self.encryptor_mock.decrypt.return_value = 'test@example.com'
        
        # Патчим encryptor в модуле user_auth
        self.patcher = patch('src.back.auth.models.user_auth.encryptor', self.encryptor_mock)
        self.patcher.start()
        
        # Также нужно патчить encryptor внутри самого класса User
        User._encryptor = self.encryptor_mock
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        self.patcher.stop()
        # Восстанавливаем оригинальный encryptor если он есть
        if hasattr(User, '_original_encryptor'):
            User._encryptor = User._original_encryptor
    
    def test_user_initialization_with_email(self):
        """Тест инициализации пользователя с email"""
        user = User(email='test@example.com')
        
        assert user.email_encrypted == 'encrypted_email'
        assert user.email_salt == 'test_salt'
        self.encryptor_mock.encrypt.assert_called_once_with('test@example.com')
    
    def test_user_initialization_with_password_hash(self):
        """Тест инициализации пользователя с хэшем пароля"""
        password_hash = 'hashed_password_123'
        user = User(password_hash=password_hash)
        
        assert user.password_hash == password_hash
    
    def test_user_initialization_with_kwargs(self):
        """Тест инициализации с дополнительными параметрами"""
        now = datetime.now()
        user = User(email='test@example.com', password_hash='hash123', 
                    id=1, created_at=now)
        
        self.encryptor_mock.encrypt.assert_called_once_with('test@example.com')
        assert user.id == 1
        assert user.created_at == now
    
    def test_email_property_getter(self):
        """Тест получения email через property"""
        # Создаем пользователя без вызова __init__, чтобы избежать шифрования
        user = User.__new__(User)
        user.email_encrypted = 'encrypted_test'
        user.email_salt = 'salt_test'
        
        # Настраиваем мок для возврата конкретного значения
        self.encryptor_mock.decrypt.return_value = 'decrypted@test.com'
        
        email = user.email
        
        assert email == 'decrypted@test.com'
        self.encryptor_mock.decrypt.assert_called_once_with('encrypted_test', 'salt_test')
    
    def test_email_property_setter(self):
        """Тест установки email через property"""
        # Создаем пользователя без вызова __init__
        user = User.__new__(User)
        user.email = 'new@example.com'
        
        assert user.email_encrypted == 'encrypted_email'
        assert user.email_salt == 'test_salt'
        self.encryptor_mock.encrypt.assert_called_once_with('new@example.com')
    
    def test_to_dict_without_encrypted(self):
        """Тест преобразования в словарь без зашифрованных данных"""
        user = User.__new__(User)
        user.id = 1
        user.email_encrypted = 'encrypted_test'
        user.email_salt = 'salt_test'
        user.password_hash = 'hash_test'
        user.created_at = datetime(2023, 1, 1, 12, 0, 0)
        user.updated_at = datetime(2023, 1, 2, 12, 0, 0)
        
        # Настраиваем мок для свойства email
        self.encryptor_mock.decrypt.return_value = 'test@example.com'
        
        result = user.to_dict(include_encrypted=False)
        
        assert result['id'] == 1
        assert result['email'] == 'test@example.com'
        assert result['created_at'] == '2023-01-01T12:00:00'
        assert result['updated_at'] == '2023-01-02T12:00:00'
        assert 'email_encrypted' not in result
        assert 'email_salt' not in result
        assert 'password_hash' not in result
    
    def test_to_dict_with_encrypted(self):
        """Тест преобразования в словарь с зашифрованными данными"""
        user = User.__new__(User)
        user.id = 1
        user.email_encrypted = 'encrypted_test'
        user.email_salt = 'salt_test'
        user.password_hash = 'hash_test'
        user.created_at = datetime(2023, 1, 1, 12, 0, 0)
        
        # Настраиваем мок для свойства email
        self.encryptor_mock.decrypt.return_value = 'test@example.com'
        
        result = user.to_dict(include_encrypted=True)
        
        assert result['email_encrypted'] == 'encrypted_test'
        assert result['email_salt'] == 'salt_test'
        assert result['password_hash'] == 'hash_test'
        assert result['email'] == 'test@example.com'
    
    def test_from_dict_with_encryption(self):
        """Тест создания пользователя из словаря с шифрованием"""
        data = {
            'email': 'test@example.com',
            'password_hash': 'hashed_pass',
            'id': 42
        }
        
        user = User.from_dict(data, encrypt_email=True)
        
        assert user.email_encrypted == 'encrypted_email'
        assert user.email_salt == 'test_salt'
        assert user.password_hash == 'hashed_pass'
        assert user.id == 42
        self.encryptor_mock.encrypt.assert_called_once_with('test@example.com')
    
    def test_from_dict_without_encryption(self):
        """Тест создания пользователя из словаря без шифрования"""
        data = {
            'email_encrypted': 'already_encrypted',
            'email_salt': 'existing_salt',
            'password_hash': 'hashed_pass',
            'id': 42
        }
        
        user = User.from_dict(data, encrypt_email=False)
        
        assert user.email_encrypted == 'already_encrypted'
        assert user.email_salt == 'existing_salt'
        assert user.password_hash == 'hashed_pass'
        assert user.id == 42
        self.encryptor_mock.encrypt.assert_not_called()
    
    def test_from_dict_with_email_and_no_encryption(self):
        """Тест создания пользователя с email но без шифрования"""
        data = {
            'email': 'test@example.com',
            'id': 1
        }
        
        user = User.from_dict(data, encrypt_email=False)
        
        # При encrypt_email=False и наличии только email, email_encrypted должен быть None
        assert user.email_encrypted is None
        assert user.email_salt is None
        self.encryptor_mock.encrypt.assert_not_called()
    
    def test_from_dict_with_datetime_strings(self):
        """Тест создания пользователя со строками даты/времени"""
        data = {
            'created_at': '2023-01-01T12:00:00Z',
            'updated_at': '2023-01-02T12:00:00Z'
        }
        
        user = User.from_dict(data)
        
        assert user.created_at.year == 2023
        assert user.created_at.month == 1
        assert user.created_at.day == 1
        assert user.updated_at.year == 2023
        assert user.updated_at.month == 1
        assert user.updated_at.day == 2
    
    def test_from_dict_with_existing_datetime_objects(self):
        """Тест создания пользователя с существующими объектами datetime"""
        created = datetime(2023, 1, 1)
        updated = datetime(2023, 1, 2)
        data = {
            'created_at': created,
            'updated_at': updated
        }
        
        user = User.from_dict(data)
        
        assert user.created_at == created
        assert user.updated_at == updated
    
    def test_update_email(self):
        """Тест обновления email"""
        # Создаем пользователя без вызова __init__
        user = User.__new__(User)
        user.email_encrypted = 'old_encrypted'
        user.email_salt = 'old_salt'
        
        # Создаем мок для func.now()
        with patch('src.back.auth.models.user_auth.func.now') as mock_now:
            mock_now.return_value = datetime(2023, 1, 2, 12, 0, 0)
            
            user.update_email('new@example.com')
            
            assert user.email_encrypted == 'encrypted_email'
            assert user.email_salt == 'test_salt'
            assert user.updated_at == datetime(2023, 1, 2, 12, 0, 0)
            self.encryptor_mock.encrypt.assert_called_once_with('new@example.com')
    
    def test_verify_email(self):
        """Тест проверки email"""
        # Создаем пользователя без вызова __init__
        user = User.__new__(User)
        user.email_encrypted = 'encrypted_test'
        user.email_salt = 'salt_test'
        
        # Настраиваем decrypt для возврата разных значений
        decrypt_calls = []
        def side_effect(encrypted, salt):
            decrypt_calls.append((encrypted, salt))
            return 'test@example.com' if len(decrypt_calls) == 1 else 'wrong@example.com'
        
        self.encryptor_mock.decrypt.side_effect = side_effect
        
        # Совпадающий email
        assert user.verify_email('test@example.com') == True
        
        # Несовпадающий email (decrypt вернет другое значение при втором вызове)
        assert user.verify_email('wrong@example.com') == False
    
    def test_create_from_plain(self):
        """Тест создания пользователя из незашифрованных данных"""
        email = 'test@example.com'
        password_hash = 'hashed_password'
        
        user = User.create_from_plain(email, password_hash)
        
        assert user.email_encrypted == 'encrypted_email'
        assert user.email_salt == 'test_salt'
        assert user.password_hash == password_hash
        self.encryptor_mock.encrypt.assert_called_once_with(email)
    
    def test_init_without_encryption(self):
        """Тест инициализации без шифрования"""
        # Создаем пользователя без email
        user = User()
        
        assert user.email_encrypted is None
        assert user.email_salt is None
        self.encryptor_mock.encrypt.assert_not_called()


class TestUserUtils:
    """Тесты для вспомогательного класса UserUtils"""
    
    def test_validate_email_format_valid(self):
        """Тест проверки валидных email"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'a@b.c',
            'user+tag@example.com'
        ]
        
        for email in valid_emails:
            assert UserUtils.validate_email_format(email) == True
    
    def test_validate_email_format_invalid(self):
        """Тест проверки невалидных email"""
        invalid_emails = [
            '',  # пустая строка
            'invalid',  # нет @
            '@domain.com',  # нет локальной части
            'user@',  # нет домена
            'a' * 256 + '@example.com',  # слишком длинный
        ]
        
        for email in invalid_emails:
            assert UserUtils.validate_email_format(email) == False
        
        # None должен вызывать ошибку или возвращать False
        with pytest.raises((AttributeError, TypeError)):
            UserUtils.validate_email_format(None)
    
    def test_mask_email_normal(self):
        """Тест маскирования нормального email"""
        test_cases = [
            ('john.doe@example.com', 'j******e@example.com'),
            ('test@example.com', 't**t@example.com'),
            ('ab@example.com', '**@example.com'),
            ('a@example.com', '*@example.com'),
        ]
        
        for email, expected in test_cases:
            result = UserUtils.mask_email(email)
            assert result == expected
    
    def test_mask_email_short_local_part(self):
        """Тест маскирования email с короткой локальной частью"""
        emails = [
            ('ab@example.com', '**@example.com'),
            ('a@example.com', '*@example.com'),
            ('abc@example.com', 'a*c@example.com')
        ]
        
        for email, expected in emails:
            assert UserUtils.mask_email(email) == expected
    
    def test_mask_email_invalid_format(self):
        """Тест маскирования email с неправильным форматом"""
        # Для строк без @ функция должна вернуть исходную строку
        assert UserUtils.mask_email('not-an-email') == 'not-an-email'
        assert UserUtils.mask_email('') == ''
        
        # Для None ожидаем ошибку
        with pytest.raises((AttributeError, TypeError)):
            UserUtils.mask_email(None)
    
    def test_users_to_dict_list(self):
        """Тест преобразования списка пользователей"""
        # Создаем моки пользователей
        user1 = Mock()
        user1.to_dict.return_value = {'id': 1, 'email': 'user1@test.com'}
        
        user2 = Mock()
        user2.to_dict.return_value = {'id': 2, 'email': 'user2@test.com'}
        
        users = [user1, user2]
        
        result = UserUtils.users_to_dict_list(users, include_encrypted=False)
        
        assert len(result) == 2
        assert result[0]['id'] == 1
        assert result[1]['id'] == 2
        
        # Проверяем, что to_dict был вызван с правильными параметрами
        user1.to_dict.assert_called_once_with(include_encrypted=False)
        user2.to_dict.assert_called_once_with(include_encrypted=False)
    
    def test_users_to_dict_list_with_encrypted(self):
        """Тест преобразования списка пользователей с зашифрованными данными"""
        user = Mock()
        
        result = UserUtils.users_to_dict_list([user], include_encrypted=True)
        
        user.to_dict.assert_called_once_with(include_encrypted=True)
    
    def test_users_to_dict_list_empty(self):
        """Тест преобразования пустого списка пользователей"""
        result = UserUtils.users_to_dict_list([])
        assert result == []
    
    def test_validate_email_format_edge_cases(self):
        """Тест граничных случаев валидации email"""
        # Email ровно 255 символов должен быть валиден
        long_local = 'a' * 245
        long_email = f'{long_local}@example.com'
        assert len(long_email) == 255
        assert UserUtils.validate_email_format(long_email) == True
        
        # Email 256 символов должен быть невалиден
        too_long_local = 'a' * 246
        too_long_email = f'{too_long_local}@example.com'
        assert len(too_long_email) == 256
        assert UserUtils.validate_email_format(too_long_email) == False


class TestSqlAlchemyIntegration:
    """Тесты интеграции с SQLAlchemy"""
    
    def test_table_definition(self):
        """Тест определения таблицы"""
        assert hasattr(User, '__tablename__')
        assert User.__tablename__ == 'users'
        
        # Проверяем наличие всех колонок
        columns = ['id', 'email_encrypted', 'email_salt', 'password_hash', 
                   'created_at', 'updated_at']
        
        for column in columns:
            assert hasattr(User, column)
    
    def test_base_inheritance(self):
        """Тест наследования от Base"""
        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base()
        assert isinstance(User.__bases__[0], type(Base))


# Тесты для инициализации модуля с моками
class TestModuleInitialization:
    """Тесты инициализации модуля с моками зависимостей"""
    
    @patch.dict('os.environ', {'ENCRYPTION_KEY': 'test_key_12345'})
    @patch('src.back.auth.models.user_auth.get_security_settings')
    @patch('src.back.auth.models.user_auth.DataEncryptor')
    def test_module_initialization_with_mocks(self, mock_encryptor_class, mock_get_settings):
        """Тест инициализации модуля с замоканными зависимостями"""
        # Создаем моки
        mock_settings = Mock()
        mock_settings.encryption_key = 'test_key'
        mock_get_settings.return_value = mock_settings
        
        mock_encryptor_instance = Mock()
        mock_encryptor_class.return_value = mock_encryptor_instance
        
        # Перезагружаем модуль
        import importlib
        import src.back.auth.models.user_auth as user_auth_module
        
        # Сохраняем текущий encryptor
        original_encryptor = getattr(user_auth_module, 'encryptor', None)
        
        # Перезагружаем модуль
        importlib.reload(user_auth_module)
        
        # Проверяем, что зависимости были вызваны
        mock_get_settings.assert_called_once()
        mock_encryptor_class.assert_called_once_with(encryption_key='test_key')
        
        # Восстанавливаем оригинальный encryptor
        if original_encryptor:
            user_auth_module.encryptor = original_encryptor


# Основные исправления для conftest.py
@pytest.fixture(autouse=True)
def mock_dependencies():
    """Автоматический мок для всех зависимостей"""
    # Мокаем encryptor
    with patch('src.back.auth.models.user_auth.encryptor') as mock_encryptor:
        mock_encryptor.encrypt.return_value = ('mocked_encrypted', 'mocked_salt')
        mock_encryptor.decrypt.return_value = 'mocked@email.com'
        yield mock_encryptor
