from sqlalchemy import text, MetaData, Table, Column, Integer, String, DateTime
from sqlalchemy.sql import func


def create_users_table(engine):
    """Создает таблицу пользователей в базе данных"""
    metadata = MetaData()
    Table(
        'users',
        metadata,
        Column('id', Integer, primary_key=True, index=True),
        Column('email_encrypted', String(512), unique=True, index=True, nullable=False),
        Column('email_salt', String(255), nullable=False),
        Column('password_hash', String(255), nullable=False),
        Column('created_at', DateTime, default=func.now()),
        Column('updated_at', DateTime, default=func.now(), onupdate=func.now())
    )
    metadata.create_all(engine)
    print("Таблица 'users' создана успешно")


def drop_users_table(engine):
    """Удаляет таблицу пользователей из базы данных"""
    with engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS users"))
        print("Таблица 'users' удалена успешно")
