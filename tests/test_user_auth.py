# test_user_auth.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sqlalchemy

from src.back.auth.models.user_auth import User, UserUtils, Base, encryptor


class TestUserModel:
    """Тесты для модели User"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        # Создаем мок для encryptor чтобы изолировать тесты от реального шифрования
        self.encryptor_mock = Mock()
        self.encryptor_mock.encrypt.return_value = ('encrypted_email', 'test_salt')
        self.encryptor_mock.decrypt.return_value = 'test@example.com'
        
        # Сохраняем оригинальный encryptor и подменяем его моком
        self.original_encryptor = encryptor
        # Временная подмена через патчинг класса User
        User._encryptor = self.encryptor_mock
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        # Восстанавливаем оригинальный encryptor
        if hasattr(self, 'original_encryptor'):
            User._encryptor = self.original_encryptor
    
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
        user = User(email='test@example.com', password_hash='hash123', 
                    id=1, created_at=datetime.now())
        
        assert user.id == 1
        assert user.created_at is not None
    
    def test_email_property_getter(self):
        """Тест получения email через property"""
        user = User()
        user.email_encrypted = 'encrypted_test'
        user.email_salt = 'salt_test'
        
        # Настраиваем мок для возврата конкретного значения
        self.encryptor_mock.decrypt.return_value = 'decrypted@test.com'
        
        email = user.email
        
        assert email == 'decrypted@test.com'
        self.encryptor_mock.decrypt.assert_called_once_with('encrypted_test', 'salt_test')
    
    def test_email_property_setter(self):
        """Тест установки email через property"""
        user = User()
        
        user.email = 'new@example.com'
        
        assert user.email_encrypted == 'encrypted_email'
        assert user.email_salt == 'test_salt'
        self.encryptor_mock.encrypt.assert_called_once_with('new@example.com')
    
    def test_to_dict_without_encrypted(self):
        """Тест преобразования в словарь без зашифрованных данных"""
        user = User(id=1, email='test@example.com')
        user.created_at = datetime(2023, 1, 1, 12, 0, 0)
        user.updated_at = datetime(2023, 1, 2, 12, 0, 0)
        
        # Мокаем свойство email
        with patch.object(User, 'email', 'test@example.com'):
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
        user = User(id=1)
        user.email_encrypted = 'encrypted_test'
        user.email_salt = 'salt_test'
        user.password_hash = 'hash_test'
        user.created_at = datetime(2023, 1, 1, 12, 0, 0)
        
        # Мокаем свойство email
        with patch.object(User, 'email', 'test@example.com'):
            result = user.to_dict(include_encrypted=True)
        
        assert result['email_encrypted'] == 'encrypted_test'
        assert result['email_salt'] == 'salt_test'
        assert result['password_hash'] == 'hash_test'
    
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
        user = User(email='old@example.com')
        
        with patch.object(User, 'email', new_callable=PropertyMock) as mock_email_prop:
            with patch('src.back.auth.models.user_auth.func.now') as mock_now:
                mock_now.return_value = datetime(2023, 1, 2)
                
                user.update_email('new@example.com')
                
                # Проверяем, что сеттер email был вызван
                assert mock_email_prop.called
                # Проверяем, что updated_at был обновлен
                assert user.updated_at == datetime(2023, 1, 2)
    
    def test_verify_email(self):
        """Тест проверки email"""
        user = User(email='test@example.com')
        
        # Мокаем свойство email
        with patch.object(User, 'email', 'test@example.com'):
            # Совпадающий email
            assert user.verify_email('test@example.com') == True
            # Несовпадающий email
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
            None  # None
        ]
        
        for email in invalid_emails:
            assert UserUtils.validate_email_format(email) == False
    
    def test_mask_email_normal(self):
        """Тест маскирования нормального email"""
        email = 'john.doe@example.com'
        masked = UserUtils.mask_email(email)
        
        assert masked.startswith('j')
        assert '*' in masked
        assert masked.endswith('@example.com')
        assert len(masked.split('@')[0]) == len('john.doe')
    
    def test_mask_email_short_local_part(self):
        """Тест маскирования email с короткой локальной частью"""
        emails = [
            ('ab@example.com', '**@example.com'),
            ('a@example.com', '*@example.com')
        ]
        
        for email, expected in emails:
            assert UserUtils.mask_email(email) == expected
    
    def test_mask_email_invalid_format(self):
        """Тест маскирования email с неправильным форматом"""
        invalid_emails = [
            'not-an-email',
            '',
            None
        ]
        
        for email in invalid_emails:
            # Проверяем, что функция не падает и возвращает исходное значение
            result = UserUtils.mask_email(email)
            assert result == email or (email is None and result is None)
    
    def test_users_to_dict_list(self):
        """Тест преобразования списка пользователей"""
        users = []
        
        for i in range(3):
            user = Mock(spec=User)
            user.to_dict.return_value = {'id': i, 'email': f'user{i}@test.com'}
            users.append(user)
        
        result = UserUtils.users_to_dict_list(users, include_encrypted=False)
        
        assert len(result) == 3
        assert result[0]['id'] == 0
        assert result[1]['id'] == 1
        assert result[2]['id'] == 2
        
        # Проверяем, что to_dict был вызван с правильными параметрами
        for user in users:
            user.to_dict.assert_called_once_with(include_encrypted=False)
    
    def test_users_to_dict_list_with_encrypted(self):
        """Тест преобразования списка пользователей с зашифрованными данными"""
        user = Mock(spec=User)
        
        result = UserUtils.users_to_dict_list([user], include_encrypted=True)
        
        user.to_dict.assert_called_once_with(include_encrypted=True)


class TestEncryptorInitialization:
    """Тесты инициализации шифратора"""
    
    @patch('src.back.auth.models.user_auth.get_security_settings')
    @patch('src.back.auth.models.user_auth.DataEncryptor')
    def test_encryptor_initialization_success(self, mock_encryptor_class, mock_get_settings):
        """Тест успешной инициализации шифратора"""
        # Перезагружаем модуль для тестирования инициализации
        import importlib
        import src.back.auth.models.user_auth
        
        mock_settings = Mock()
        mock_settings.encryption_key = 'test_key'
        mock_get_settings.return_value = mock_settings
        
        # Имитируем успешную инициализацию
        mock_encryptor_instance = Mock()
        mock_encryptor_class.return_value = mock_encryptor_instance
        
        # Перезагружаем модуль для срабатывания инициализации
        importlib.reload(src.back.auth.models.user_auth)
        
        mock_get_settings.assert_called_once()
        mock_encryptor_class.assert_called_once_with(encryption_key='test_key')
    
    @patch('src.back.auth.models.user_auth.get_security_settings')
    def test_encryptor_initialization_failure(self, mock_get_settings):
        """Тест неудачной инициализации шифратора"""
        # Мокаем исключение при инициализации
        mock_get_settings.side_effect = Exception("Settings error")
        
        # Перезагружаем модуль и проверяем, что исключение пробрасывается
        import importlib
        import src.back.auth.models.user_auth
        
        with pytest.raises(Exception, match="Settings error"):
            importlib.reload(src.back.auth.models.user_auth)


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
            assert isinstance(getattr(User, column).property, sqlalchemy.orm.ColumnProperty)
    
    def test_base_inheritance(self):
        """Тест наследования от Base"""
        assert issubclass(User, Base)


# Вспомогательный мок для Property
class PropertyMock:
    def __init__(self):
        self.called = False
        self.value = None
    
    def __call__(self):
        self.called = True
        return self.value
    
    def __get__(self, obj, objtype=None):
        return self
    
    def __set__(self, obj, value):
        self.called = True
        self.value = value
