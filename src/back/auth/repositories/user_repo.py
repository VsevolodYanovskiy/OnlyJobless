from typing import Optional, List
from ..models.user_auth import User
from sqlalchemy.orm import Session

class UserRepository:
    """Репозиторий для работы с данными пользователей в базе данных"""
    
    def __init__(self, db_session: Session):
        """Инициализация репозитория с сессией базы данных"""
        pass
    
    def create_user(self, user_data: dict) -> User:
        """Создает нового пользователя в базе данных"""
        pass
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Находит пользователя по email адресу"""
        pass
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Находит пользователя по его ID"""
        pass
    
    def update_user(self, user_id: int, update_data: dict) -> Optional[User]:
        """Обновляет данные пользователя"""
        pass
    
    def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя из базы данных"""
        pass
