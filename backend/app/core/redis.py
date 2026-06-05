import json

import redis

from app.core.config import settings

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


def store_qr_session(session_id: str, data: dict, ttl: int = None) -> None:
    r = get_redis()
    ttl = ttl or settings.QR_EXPIRATION_SECONDS
    r.setex(f"qr:{session_id}", ttl, json.dumps(data))


def get_qr_session(session_id: str) -> dict | None:
    r = get_redis()
    raw = r.get(f"qr:{session_id}")
    if raw is None:
        return None
    return json.loads(raw)


def delete_qr_session(session_id: str) -> None:
    r = get_redis()
    r.delete(f"qr:{session_id}")
