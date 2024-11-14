"""
Redis client utility for caching.
"""

from typing import Optional, Any, Union
import json
from redis.asyncio import Redis
from app.core.config import settings

class RedisClient:
    _instance = None
    _redis = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance

    async def init(self):
        """Initialize Redis connection."""
        if self._redis is None:
            self._redis = Redis.from_url(
                settings.redis.REDIS_URL,
                db=settings.redis.REDIS_DB,
                password=settings.redis.REDIS_PASSWORD,
                encoding="utf-8",
                decode_responses=False  # Changed to False to handle raw bytes
            )

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        if not self._redis:
            await self.init()
        
        try:
            value = await self._redis.get(key)
            if value:
                try:
                    return json.loads(value.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Redis decode error: {e}")
                    return None
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in Redis with optional TTL."""
        if not self._redis:
            await self.init()
        
        try:
            serialized = json.dumps(value).encode('utf-8')
            if ttl:
                await self._redis.setex(key, ttl, serialized)
            else:
                await self._redis.set(key, serialized)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self._redis:
            await self.init()
        
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self._redis:
            await self.init()
        
        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False

    async def clear_cache(self, pattern: str = "*") -> bool:
        """Clear cache entries matching pattern."""
        if not self._redis:
            await self.init()
        
        try:
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern)
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break
            return True
        except Exception as e:
            print(f"Redis clear cache error: {e}")
            return False

# Create singleton instance
redis_client = RedisClient()
