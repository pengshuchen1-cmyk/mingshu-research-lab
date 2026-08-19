from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from .config import settings
from .database import DBSession
from .models import User

bearer = HTTPBearer()
BearerCredentials = Annotated[HTTPAuthorizationCredentials, Depends(bearer)]


def token_for(user: User, typ="access"):
    ttl = settings.access_token_minutes if typ == "access" else settings.refresh_token_days * 1440
    return jwt.encode(
        {
            "sub": user.id,
            "role": user.role,
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
        raise HTTPException(401, "Invalid or expired token")
    if payload.get("typ") != "access":
        raise HTTPException(401, "Access token required")
    user = (await db.execute(select(User).where(User.id == payload["sub"]))).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(401, "User unavailable")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


async def admin_user(user: CurrentUser) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator role required")
    return user


AdminUser = Annotated[User, Depends(admin_user)]
