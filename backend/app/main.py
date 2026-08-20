from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from .api.v1 import router as api_v1_router
from .cache import RedisClient
from .config import settings
from .database import DBSession
from .errors import APIError, Errors, SystemErrorMessages

app = FastAPI(
    title="Mingshu Backend API", version="0.1.0", openapi_url="/openapi.json", docs_url="/docs"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_v1_router)


@app.on_event("startup")
async def validate_production_settings():
    if settings.environment == "production":
        placeholder_markers = ("REPLACE_", "LOWERCASE_HEX", "development-secret")
        if len(settings.jwt_secret) < 32 or any(
            marker.lower() in settings.jwt_secret.lower() for marker in placeholder_markers
        ):
            raise RuntimeError(SystemErrorMessages.JWT_SECRET_INSECURE)
        database_url = make_url(settings.database_url)
        if database_url.drivername != "mysql+asyncmy":
            raise RuntimeError(SystemErrorMessages.PRODUCTION_DATABASE_DRIVER_INVALID)
        if not database_url.password or any(
            marker.lower() in database_url.password.lower() for marker in placeholder_markers
        ):
            raise RuntimeError(SystemErrorMessages.PRODUCTION_DATABASE_PASSWORD_INVALID)
        if not settings.redis_url:
            raise RuntimeError(SystemErrorMessages.PRODUCTION_REDIS_REQUIRED)
        redis_url = make_url(settings.redis_url)
        if not redis_url.password or any(
            marker.lower() in redis_url.password.lower() for marker in placeholder_markers
        ):
            raise RuntimeError(SystemErrorMessages.PRODUCTION_REDIS_PASSWORD_INVALID)


@app.get("/healthz", tags=["operations"])
async def health():
    """进程存活探针：API 进程可响应时返回成功，不检查外部依赖。"""
    return {"status": "ok"}


@app.get("/readyz", tags=["operations"])
async def readiness(
    db: DBSession,
    cache: RedisClient,
):
    """服务就绪探针：仅在 MySQL 和 Redis 均可正常响应时返回成功。"""
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar_one() != 1:
            raise RuntimeError(SystemErrorMessages.DATABASE_READINESS_UNEXPECTED)
    except (SQLAlchemyError, RuntimeError):
        # Do not leak connection strings or database errors through a public probe.
        raise APIError(Errors.DATABASE_NOT_READY) from None
    try:
        if cache is None or not await cache.ping():
            raise RuntimeError(SystemErrorMessages.REDIS_READINESS_UNEXPECTED)
    except (RedisError, RuntimeError):
        raise APIError(Errors.REDIS_NOT_READY) from None
    return {"status": "ready"}
