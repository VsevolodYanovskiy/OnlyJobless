from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import datetime

class UserRegister(BaseModel):
    """Схема для регистрации нового пользователя"""
    email: EmailStr
    password: str
    password_confirm: str
    
    @validator('password_confirm')
    def passwords_match(cls, v, values):
        """Валидатор для проверки совпадения паролей"""
        pass

class UserLogin(BaseModel):
    """Схема для входа пользователя в систему"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Схема ответа с данными пользователя (без чувствительной информации)"""
    id: int
    email: str
    created_at: datetime.datetime

class TokenResponse(BaseModel):
    """Схема ответа с JWT токенами"""
    access_token: str
    token_type: str
    expires_in: int
