import pytest
import os
import sys
import asyncio
from typing import Generator, AsyncGenerator

# Добавляем src в путь импорта для тестов
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Импортируем после добавления пути
try:
    from back.main import app
    from back.database.database import Base, get_db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
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
    AsyncSession = None

# Конфигурация тестовой БД
TEST_DATABASE_URL = "sqlite:///:memory:"
TEST_ASYNC_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Создание event loop для асинхронных тестов
@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для асинхронных тестов"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

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
        "DEBUG": "True",
        "ENCRYPTION_KEY": "test-encryption-key-32-chars-long-for-tests",
        "JWT_SECRET_KEY": "test-jwt-secret-key-for-tests-only",
        "CORS_ORIGINS": "http://localhost:3000"
    })
    yield

@pytest.fixture(scope="session")
def engine():
    """Фикстура для синхронного движка БД"""
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

@pytest.fixture(scope="session")
async def async_engine():
    """Фикстура для асинхронного движка БД"""
    if not HAS_DEPS or Base is None:
        pytest.skip("Database dependencies not available")
    
    engine = create_async_engine(
        TEST_ASYNC_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Очищаем
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Фикстура для синхронной сессии БД"""
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
async def async_db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для асинхронной сессии БД"""
    if not HAS_DEPS:
        pytest.skip("Database dependencies not available")
    
    async_session = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await session.close()

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
    config.addinivalue_line("markers", "async: async tests")
    config.addinivalue_line("markers", "encryption: encryption tests")

