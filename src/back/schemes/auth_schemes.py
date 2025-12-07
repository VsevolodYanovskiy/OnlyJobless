from pydantic import BaseModel, EmailStr, field_validator
import datetime
from pydantic import ValidationInfo
import ConfigDict


class UserRegister(BaseModel):
    """Схема для регистрации нового пользователя"""
    email: EmailStr
    password: str
    password_confirm: str
    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v, info: ValidationInfo):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Пароли не совпадают')
        return v
    @field_validator('email')
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserLogin(BaseModel):
    """Схема для входа пользователя в систему"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя (без чувствительной информации)"""
    id: int
    email: str
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)
    def to_json(self) -> str:
        return self.model_dump_json()


class TokenResponse(BaseModel):
    """Схема ответа с JWT токенами"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
