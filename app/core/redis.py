"""
Enhanced Redis client utility for caching with improved error handling and logging.
"""

from typing import Optional, Any, Union, List
import json
import logging
from redis.asyncio import Redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClientError(Exception):
    """Custom exception for Redis client errors."""
    pass

class RedisClient:
    _instance = None
    _redis = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance

    async def init(self):
        """Initialize Redis connection with comprehensive error handling."""
        try:
            if self._redis is None:
                self._redis = Redis.from_url(
                    settings.redis.REDIS_URL,
                    db=settings.redis.REDIS_DB,
                    password=settings.redis.REDIS_PASSWORD,
                    encoding="utf-8",
                    decode_responses=False
                )
                logger.info("Redis connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            raise RedisClientError(f"Redis initialization failed: {e}")

    async def close(self):
        """Close Redis connection with error handling."""
        try:
            if self._redis:
                await self._redis.close()
                self._redis = None
                logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis with enhanced error handling and logging.
        
        Args:
            key (str): Redis key to retrieve
        
        Returns:
            Deserialized value or None
        
        Raises:
            RedisClientError for critical failures
        """
        if not self._redis:
            await self.init()
        
        try:
            value = await self._redis.get(key)
            if value is None:
                logger.debug(f"No value found for key: {key}")
                return None
            
            try:
                decoded_value = value.decode('utf-8')
                return json.loads(decoded_value)
            except (json.JSONDecodeError, UnicodeDecodeError) as decode_error:
                logger.warning(
                    f"Decoding error for key {key}: {decode_error}. "
                    f"Raw value: {value}"
                )
                return None
        
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            raise RedisClientError(f"Failed to retrieve key {key}: {e}")

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        force_overwrite: bool = False
    ) -> bool:
        """
        Set value in Redis with advanced features.
        
        Args:
            key (str): Redis key to set
            value (Any): Value to store
            ttl (Optional[int]): Time-to-live in seconds
            force_overwrite (bool): Override existing key
        
        Returns:
            Boolean indicating success
        
        Raises:
            RedisClientError for critical failures
        """
        if not self._redis:
            await self.init()
        
        try:
            # Check if key exists and overwrite is not forced
            if not force_overwrite and await self.exists(key):
                logger.warning(f"Key {key} already exists. Use force_overwrite=True to override.")
                return False
            
            serialized = json.dumps(value).encode('utf-8')
            
            if ttl:
                await self._redis.setex(key, ttl, serialized)
            else:
                await self._redis.set(key, serialized)
            
            logger.debug(f"Successfully set key {key} with TTL {ttl}")
            return True
        
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            raise RedisClientError(f"Failed to set key {key}: {e}")

    async def delete(self, key: str) -> bool:
        """Delete key from Redis with logging."""
        if not self._redis:
            await self.init()
        
        try:
            result = await self._redis.delete(key)
            if result:
                logger.info(f"Deleted key: {key}")
            else:
                logger.debug(f"No key found to delete: {key}")
            return bool(result)
        
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            raise RedisClientError(f"Failed to delete key {key}: {e}")

    async def exists(self, key: str) -> bool:
        """Check key existence with error handling."""
        if not self._redis:
            await self.init()
        
        try:
            return await self._redis.exists(key) > 0
        
        except Exception as e:
            logger.error(f"Redis exists check error for key {key}: {e}")
            raise RedisClientError(f"Failed to check key existence {key}: {e}")

    async def clear_search_results_cache(self, results_prefix: str = "search_results:") -> int:
        """
        Clear all search result cache entries.
        
        Args:
            results_prefix (str): Prefix for search result keys
        
        Returns:
            Number of keys deleted
        """
        if not self._redis:
            await self.init()
        
        try:
            cursor = 0
            total_deleted = 0
            
            while True:
                cursor, keys = await self._redis.scan(
                    cursor, 
                    match=f"{results_prefix}*", 
                    count=1000
                )
                
                if keys:
                    deleted = await self._redis.delete(*keys)
                    total_deleted += deleted
                    logger.info(f"Deleted {deleted} search result cache keys")
                
                if cursor == 0:
                    break
            
            logger.info(f"Total search result cache keys deleted: {total_deleted}")
            return total_deleted
        
        except Exception as e:
            logger.error(f"Error clearing search results cache: {e}")
            raise RedisClientError(f"Failed to clear search results cache: {e}")

# Create singleton instance
redis_client = RedisClient()
