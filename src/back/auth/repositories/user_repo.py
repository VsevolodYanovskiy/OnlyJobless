import asyncio
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, or_
from sqlalchemy.exc import IntegrityError
import logging
from ..models.user_auth import User, UserUtils


logger = logging.getLogger(__name__)


class UserRepository:
    """Асинхронный репозиторий для работы с данными пользователей в базе данных"""
    def __init__(self, db_session: AsyncSession):
        """Инициализация репозитория с асинхронной сессией базы данных"""
        self.db_session = db_session

    async def create_user(self, user_data: dict) -> Optional[User]:
        """
        Создает нового пользователя в базе данных асинхронно.
        """
        try:
            email = user_data.get('email')
            if not email or not UserUtils.validate_email_format(email):
                logger.error(f"Некорректный формат email: {email}")
                return None
            existing_user = await self.get_user_by_email(email)
            if existing_user:
                logger.warning(f"Пользователь с email {email} уже существует")
                return None
            user = User.from_dict(user_data)
            self.db_session.add(user)
            await self.db_session.flush()
            await self.db_session.commit()
            logger.info(f"Создан пользователь с ID: {user.id}")
            return user
        except IntegrityError as e:
            await self.db_session.rollback()
            logger.error(f"Ошибка целостности при создании пользователя: {e}")
            return None
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Ошибка при создании пользователя: {e}")
            return None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Асинхронно находит пользователя по его ID.
        """
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка при поиске пользователя по ID {user_id}: {e}")
            return None

    async def update_user(self, user_id: int, update_data: dict) -> Optional[User]:
        """
        Асинхронно обновляет данные пользователя.
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                logger.warning(f"Пользователь с ID {user_id} не найден")
                return None
            if 'email' in update_data:
                email = update_data['email']
                if not UserUtils.validate_email_format(email):
                    logger.error(f"Некорректный формат email: {email}")
                    return None
                existing_user = await self.get_user_by_email(email)
                if existing_user and existing_user.id != user_id:
                    logger.warning(f"Email {email} уже используется другим пользователем")
                    return None
                user.update_email(email)
                del update_data['email']
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
                else:
                    logger.warning(f"Поле {key} не существует в модели User")
            user.updated_at = func.now() if hasattr(func, 'now') else datetime.datetime.utcnow()
            await self.db_session.commit()
            logger.info(f"Обновлен пользователь с ID: {user_id}")
            return user
        except IntegrityError as e:
            await self.db_session.rollback()
            logger.error(f"Ошибка целостности при обновлении пользователя {user_id}: {e}")
            return None
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Ошибка при обновлении пользователя {user_id}: {e}")
            return None

    async def delete_user(self, user_id: int) -> bool:
        """
        Асинхронно удаляет пользователя из базы данных.
        """
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.db_session.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                logger.warning(f"Пользователь с ID {user_id} не найден")
                return False
            await self.db_session.delete(user)
            await self.db_session.commit()
            logger.info(f"Удален пользователь с ID: {user_id}")
            return True
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Ошибка при удалении пользователя {user_id}: {e}")
            return False
