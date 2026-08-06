import redis
from app.core.config import settings
import json
from typing import Any

# Global redis connection pool
redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
redis_client = redis.Redis(connection_pool=redis_pool)

def get_cache(key: str) -> Any:
    """Retrieve value from cache"""
    try:
        val = redis_client.get(key)
        if val:
            return json.loads(val)
    except Exception as e:
        # Silently fail cache read so application continues
        print(f"Redis cache read error: {e}")
    return None

def set_cache(key: str, value: Any, expire_seconds: int = 3600) -> None:
    """Set value in cache with expiration"""
    try:
        redis_client.setex(key, expire_seconds, json.dumps(value))
    except Exception as e:
        # Silently fail cache write so application continues
        print(f"Redis cache write error: {e}")
