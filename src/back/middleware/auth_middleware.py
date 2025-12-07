from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..utilits.security import JWTService
from ..config.security import get_security_settings
from ..database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import logging


logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_service: JWTService = Depends(lambda: JWTService(get_security_settings())),
    db: AsyncSession = Depends(get_db)
):
    """Dependency для получения текущего пользователя из запроса"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Требуется аутентификация",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = await jwt_service.verify_token_async(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Недействительный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from ..auth.repositories.user_repo import UserRepository
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_id(int(user_id))

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def auth_middleware(request: Request, call_next):
    """Middleware для обязательной аутентификации запросов"""
    public_paths = ["/auth/login", "/auth/register", "/health", "/docs", "/openapi.json", "/favicon.ico"]
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Требуется аутентификация"}
        )
    return await call_next(request)


async def optional_auth_middleware(request: Request, call_next):
    """Middleware для опциональной аутентификации запросов"""
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            jwt_service = JWTService(get_security_settings())
            payload = await jwt_service.verify_token_async(token)

            if payload:
                request.state.user_id = payload.get("sub")
                request.state.user_email = payload.get("email")
    except Exception as e:
        logger.debug(f"Опциональная аутентификация не удалась: {e}")
    return await call_next(request)
