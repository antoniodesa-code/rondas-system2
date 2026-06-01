import json

import redis.asyncio as aioredis

from app.core.config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def store_qr_session(session_id: str, data: dict, ttl: int = None) -> None:
    r = await get_redis()
    ttl = ttl or settings.QR_EXPIRATION_SECONDS
    await r.setex(f"qr:{session_id}", ttl, json.dumps(data))


async def get_qr_session(session_id: str) -> dict | None:
    r = await get_redis()
    raw = await r.get(f"qr:{session_id}")
    if raw is None:
        return None
    return json.loads(raw)


async def delete_qr_session(session_id: str) -> None:
    r = await get_redis()
    await r.delete(f"qr:{session_id}")
