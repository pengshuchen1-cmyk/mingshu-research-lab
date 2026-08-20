from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from .config import settings
from .database import DBSession
from .errors import APIError, Errors
from .models import User

bearer = HTTPBearer()
BearerCredentials = Annotated[HTTPAuthorizationCredentials, Depends(bearer)]


def token_for(user: User, typ="access"):
    ttl = settings.access_token_minutes if typ == "access" else settings.refresh_token_days * 1440
    return jwt.encode(
        {
            "sub": user.id,
            "role": user.role,
            "ver": user.auth_version,
            "typ": typ,
            "iss": settings.jwt_issuer,
            "exp": datetime.now(UTC) + timedelta(minutes=ttl),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


async def current_user(
    c: BearerCredentials,
    db: DBSession,
) -> User:
    try:
        payload = jwt.decode(
            c.credentials, settings.jwt_secret, algorithms=["HS256"], issuer=settings.jwt_issuer
        )
    except jwt.PyJWTError:
        raise APIError(Errors.INVALID_OR_EXPIRED_TOKEN)
    if payload.get("typ") != "access":
        raise APIError(Errors.ACCESS_TOKEN_REQUIRED)
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise APIError(Errors.INVALID_OR_EXPIRED_TOKEN)
    user = (await db.execute(select(User).where(User.id == subject))).scalar_one_or_none()
    if not user or not user.is_active:
        raise APIError(Errors.USER_UNAVAILABLE)
    if payload.get("ver", 0) != user.auth_version:
        raise APIError(Errors.INVALID_OR_EXPIRED_TOKEN)
    return user


CurrentUser = Annotated[User, Depends(current_user)]


async def admin_user(user: CurrentUser) -> User:
    if user.role != "admin":
        raise APIError(Errors.ADMINISTRATOR_REQUIRED)
    return user


AdminUser = Annotated[User, Depends(admin_user)]
