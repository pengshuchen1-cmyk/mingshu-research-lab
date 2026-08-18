from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from .config import settings


async def get_redis() -> AsyncIterator[Redis]:
    """Provide a request-scoped Redis client from the required REDIS_URL."""
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


RedisClient = Annotated[Redis, Depends(get_redis)]
