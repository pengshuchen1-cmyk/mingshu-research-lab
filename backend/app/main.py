from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from .cache import RedisClient
from .config import settings
from .database import DBSession
from .routers import admin, auth, me, pay

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
app.include_router(auth)
app.include_router(me)
app.include_router(admin)
app.include_router(pay)


@app.on_event("startup")
async def validate_production_settings():
    if settings.environment == "production":
        placeholder_markers = ("REPLACE_", "LOWERCASE_HEX", "development-secret")
        if len(settings.jwt_secret) < 32 or any(
            marker.lower() in settings.jwt_secret.lower() for marker in placeholder_markers
        ):
            raise RuntimeError(
                "JWT_SECRET must be replaced with a random value of at least 32 characters"
            )
        database_url = make_url(settings.database_url)
        if database_url.drivername != "mysql+asyncmy":
            raise RuntimeError("production DATABASE_URL must use mysql+asyncmy")
        if not database_url.password or any(
            marker.lower() in database_url.password.lower() for marker in placeholder_markers
        ):
            raise RuntimeError("production DATABASE_URL must contain a non-placeholder password")
        if not settings.redis_url:
            raise RuntimeError("production REDIS_URL is required")
        redis_url = make_url(settings.redis_url)
        if not redis_url.password or any(
            marker.lower() in redis_url.password.lower() for marker in placeholder_markers
        ):
            raise RuntimeError("production REDIS_URL must contain a non-placeholder password")


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
            raise RuntimeError("unexpected database readiness result")
    except (SQLAlchemyError, RuntimeError):
        # Do not leak connection strings or database errors through a public probe.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database is not ready",
        ) from None
    try:
        if cache is None or not await cache.ping():
            raise RuntimeError("unexpected Redis readiness result")
    except (RedisError, RuntimeError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="redis is not ready",
        ) from None
    return {"status": "ready"}
