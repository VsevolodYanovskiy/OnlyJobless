from typing import Optional
from ..schemes.auth_schemes import UserRegister, UserLogin
from ..models.user_auth import User, UserUtils
import logging


logger = logging.getLogger(__name__)


class AuthService:
    """Сервис для управления аутентификацией и регистрацией пользователей"""

    def __init__(self, user_repository, password_service):
        """Инициализация сервиса с репозиторием пользователей и сервисом паролей"""
        self.user_repo = user_repository
        self.password_service = password_service

    async def register_user(self, register_data: UserRegister) -> Optional[User]:
        """Регистрирует нового пользователя в системе"""
        try:
            if not await self._validate_email_unique(register_data.email):
                logger.warning(f"Email {UserUtils.mask_email(register_data.email)} уже зарегистрирован")
                return None
            password_hash = self.password_service.get_hash(register_data.password)
            user = await self.user_repo.create_user({
                'email': register_data.email,
                'password_hash': password_hash
            })
            if user:
                logger.info(f"Зарегистрирован новый пользователь: {user.id}")
            return user
        except Exception as e:
            logger.error(f"Ошибка при регистрации пользователя: {e}")
            return None

    async def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        """Аутентифицирует пользователя по email и паролю"""
        try:
            user = await self.user_repo.get_user_by_email(login_data.email)
            if not user:
                logger.warning(f"Попытка входа с несуществующим email: {UserUtils.mask_email(login_data.email)}")
                return None
            if not self.password_service.verify(login_data.password, user.password_hash):
                logger.warning(f"Неверный пароль для пользователя {user.id}")
                return None
            logger.info(f"Успешная аутентификация пользователя {user.id}")
            return user
        except Exception as e:
            logger.error(f"Ошибка при аутентификации: {e}")
            return None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Возвращает пользователя по его ID"""
        try:
            return await self.user_repo.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя {user_id}: {e}")
            return None

    async def _validate_email_unique(self, email: str) -> bool:
        """Проверяет уникальность email в системе"""
        try:
            user = await self.user_repo.get_user_by_email(email)
            return user is None
        except Exception as e:
            logger.error(f"Ошибка при проверке уникальности email: {e}")
            return False
