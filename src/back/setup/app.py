from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from ..database.database import init_database
from ..config.security import get_security_settings
from ..middleware.auth_middleware import optional_auth_middleware
from ..auth.controllers.auth_controller import router as auth_router


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan для управления событиями запуска и остановки"""
    logger.info("Запуск приложения...")
    settings = get_security_settings()
    database_url = settings.database_url if hasattr(settings, 'database_url') else "sqlite+aiosqlite:///./app.db"
    try:
        await init_database(database_url)
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
    yield
    logger.info("Остановка приложения...")


def create_application() -> FastAPI:
    """Фабрика для создания и настройки FastAPI приложения"""
    settings = get_security_settings()
    app = FastAPI(
        title="Auth API",
        description="API для аутентификации и регистрации пользователей",
        version="1.0.0",
        lifespan=lifespan
    )
    setup_middleware(app, settings)
    setup_routes(app)
    return app


def setup_middleware(app: FastAPI, settings):
    """Настраивает middleware приложения"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(optional_auth_middleware)


def setup_routes(app: FastAPI):
    """Регистрирует все роуты приложения"""
    app.include_router(auth_router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "auth-api"}
