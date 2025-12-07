from pydantic_settings import BaseModel, EmailStr, field_validator
from typing import Optional
import datetime


class UserRegister(BaseModel):
    """Схема для регистрации нового пользователя"""
    email: EmailStr
    password: str
    password_confirm: str
    @field_validator('password_confirm')
    def passwords_match(cls, v, values):
        """Валидатор для проверки совпадения паролей"""
        if 'password' in values and v != values['password']:
            raise ValueError('Пароли не совпадают')
        return v


class UserLogin(BaseModel):
    """Схема для входа пользователя в систему"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя (без чувствительной информации)"""
    id: int
    email: str
    created_at: datetime.datetime
    
    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    """Схема ответа с JWT токенами"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
