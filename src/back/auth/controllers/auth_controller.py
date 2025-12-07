from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas.auth_schemas import UserRegister, UserLogin, UserResponse, TokenResponse
from ..services.auth_service import AuthService
from ..services.password_service import PasswordService
from ...database.database import get_db
from ...utilits.security import JWTService
from ...config.security import get_security_settings
from sqlalchemy.ext.asyncio import AsyncSession
import logging


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency для получения асинхронного сервиса аутентификации"""
    password_service = PasswordService()
    from ..repositories.user_repo import UserRepository
    user_repo = UserRepository(db)
    return AuthService(user_repo, password_service)


def get_jwt_service() -> JWTService:
    """Dependency для получения JWT сервиса"""
    security_settings = get_security_settings()
    return JWTService(security_settings)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Эндпоинт для регистрации нового пользователя"""
    strength_result = PasswordService.is_strong(user_data.password)
    if "ain't strong" in strength_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=strength_result
        )

    user = await auth_service.register_user(user_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось зарегистрировать пользователя. Возможно, email уже используется."
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
    jwt_service: JWTService = Depends(get_jwt_service)
):
    """Эндпоинт для аутентификации пользователя и получения токена"""
    user = await auth_service.authenticate_user(login_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = await jwt_service.create_access_token_async(
        data={"sub": str(user.id), "email": user.email}
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=jwt_service.settings.access_token_expire_minutes * 60
    )


@router.post("/logout")
async def logout():
    """Эндпоинт для выхода пользователя из системы"""
    return {"message": "Успешный выход из системы"}
