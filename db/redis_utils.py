# db/redis_utils.py
import json
import logging
from typing import Optional, Any, Dict
from functools import wraps
import redis.asyncio as redis
from fastapi import HTTPException, status
import asyncio

from config.settings import settings

logger = logging.getLogger(__name__)

class RedisManager:
    _instance = None
    _redis: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
        return cls._instance

    async def get_redis(self) -> Optional[redis.Redis]:
        """Get or create a Redis connection."""
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2,  # 2 seconds timeout
                    socket_timeout=2,
                    retry_on_timeout=False
                )
                # Test the connection
                await self._redis.ping()
                # Test the connection
                await self._redis.ping()
            except Exception as e:
                logger.warning(f" Could not connect to Redis: {e}")
                logger.warning(" Running without Redis cache. Some features may be limited.")
                self._redis = None  # Ensure _redis is None if connection fails
        return self._redis

    async def close(self):
        """Close the Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

# Global Redis manager instance
redis_manager = RedisManager()

async def get_redis() -> Optional[redis.Redis]:
    """Dependency to get Redis client. Returns None if Redis is not available."""
    try:
        return await redis_manager.get_redis()
    except Exception as e:
        logger.warning(f" Redis error: {e}")
        return None

async def get_cached_data(key: str) -> Optional[Dict[str, Any]]:
    """
    Get JSON data from Redis cache.
    """
    try:
        redis_client = await get_redis()
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Error getting cached data for key {key}: {str(e)}")
        return None

async def set_cached_data(key: str, data: Any, ttl: int = settings.REDIS_TTL) -> bool:
    """
    Store JSON data in Redis cache.
    """
    try:
        redis_client = await get_redis()
        await redis_client.set(
            key,
            json.dumps(data, default=str),
            ex=ttl
        )
        return True
    except Exception as e:
        logger.error(f"Error setting cached data for key {key}: {str(e)}")
        return False

async def delete_cached_data(key: str) -> bool:
    """
    Delete data from Redis cache.
    """
    try:
        redis_client = await get_redis()
        if '*' in key:
            # Handle pattern matching for wildcard deletes
            keys = await redis_client.keys(key)
            if keys:
                await redis_client.delete(*keys)
        else:
            await redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Error deleting cached data for key {key}: {str(e)}")
        return False

def cache_key(prefix: str, *args) -> str:
    """Generate a consistent cache key."""
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"

def cache_org_data(ttl: int = settings.REDIS_TTL):
    """
    Decorator to cache organization data.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Generate cache key from function name and args
            org_name = kwargs.get('organization_name') or (args[0] if args else None)
            if not org_name:
                return await func(self, *args, **kwargs)
                
            cache_key = f"org:{org_name}"
            
            # Try to get from cache
            if not kwargs.get('skip_cache', False):
                cached_data = await get_cached_data(cache_key)
                if cached_data is not None:
                    return cached_data
                
            # If not in cache, call the original function
            result = await func(self, *args, **kwargs)
            
            # Cache the result if successful
            if result is not None:
                await set_cached_data(cache_key, result, ttl)
                
            return result
        return wrapper
    return decorator