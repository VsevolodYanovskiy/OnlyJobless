from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import AsyncGenerator
import os


Base = declarative_base()


class Database:
    """Класс для управления подключением к базе данных и сессиями"""
    def __init__(self, database_url: str):
        """Инициализация подключения к базе данных"""
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            echo=bool(os.getenv("SQL_ECHO", False)),
            future=True,
            pool_pre_ping=True,
            pool_recycle=300
        )
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Возвращает новую асинхронную сессию базы данных"""

        async with self.async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    async def create_tables(self):
        """Создает все таблицы в базе данных"""
        async with self.engine.begin() as conn:
            from ..auth.models.user_auth import Base as AuthBase
            await conn.run_sync(AuthBase.metadata.create_all)

    async def close_connection(self):
        """Закрывает соединение с базой данных"""
        if self.engine:
            await self.engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для FastAPI, предоставляющая асинхронную сессию базы данных"""
    from . import database_instance
    async for session in database_instance.get_session():
        yield session

database_instance = None

async def init_database(database_url: str) -> Database:
    """Инициализирует базу данных"""
    global database_instance
    database_instance = Database(database_url)
    await database_instance.create_tables()
    return database_instance
