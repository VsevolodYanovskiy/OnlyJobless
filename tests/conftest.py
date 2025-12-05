import pytest
import os
import sys
from typing import Generator

# Добавляем src в путь импорта для тестов
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Импортируем после добавления пути
try:
    from back.main import app
    from back.database.database import Base, get_db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.pool import StaticPool
    from fastapi.testclient import TestClient
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    # Если зависимости не установлены, используем заглушки
    app = None
    Base = None
    get_db = None
    create_engine = None
    sessionmaker = None
    Session = None
    StaticPool = None
    TestClient = None

# Конфигурация тестовой БД
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Настройка тестового окружения"""
    # Устанавливаем переменные окружения
    os.environ.update({
        "SECRET_KEY": "test-secret-key-for-tests-only",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "DATABASE_URL": TEST_DATABASE_URL,
        "ENVIRONMENT": "test",
        "DEBUG": "True"
    })
    yield

@pytest.fixture(scope="session")
def engine():
    """Фикстура для движка БД"""
    if not HAS_DEPS or Base is None:
        pytest.skip("Database dependencies not available")
    
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)
    yield engine
    
    # Очищаем
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Фикстура для сессии БД"""
    if not HAS_DEPS:
        pytest.skip("Database dependencies not available")
    
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Фикстура для тестового клиента FastAPI"""
    if not HAS_DEPS or app is None:
        pytest.skip("FastAPI app not available")
    
    # Временно переопределяем зависимость БД
    original_override = None
    if hasattr(app, 'dependency_overrides'):
        original_override = app.dependency_overrides.get(get_db)
    
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Восстанавливаем
    if original_override:
        app.dependency_overrides[get_db] = original_override
    elif get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]

# Регистрация кастомных маркеров pytest
def pytest_configure(config):
    """Регистрация маркеров"""
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "slow: slow running tests")
    config.addinivalue_line("markers", "auth: authentication tests")
    config.addinivalue_line("markers", "db: database tests")

def pytest_collection_modifyitems(config, items):
    """Автоматически помечать тесты по их расположению"""
    for item in items:
        # Тесты в integration/ помечаем как интеграционные
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        # Тесты с базой данных
        if any(keyword in item.nodeid for keyword in ["db", "database", "sql"]):
            item.add_marker(pytest.mark.db)