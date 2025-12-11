"""
Rate limiting utilities for API endpoints.
Uses Redis for distributed rate limiting in production and in-memory for development.
"""
import time
import asyncio
from typing import Optional, Dict, Any, Callable, Awaitable
from functools import wraps
import logging
import aioredis
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from config import settings

logger = logging.getLogger(__name__)

# In-memory rate limit storage for development
_rate_limit_store = {}
_rate_limit_locks = {}

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Try again in {retry_after} seconds.")

class RateLimiter:
    """
    Rate limiter for API endpoints.
    
    Args:
        key_prefix: Prefix for rate limit keys
        limit: Maximum number of requests allowed in the time window
        window: Time window in seconds
    """
    def __init__(
        self, 
        key_prefix: str = "rate_limit",
        limit: int = 60,
        window: int = 60
    ):
        self.key_prefix = key_prefix
        self.limit = limit
        self.window = window
        self.redis = None
        self._initialized = False
    
    async def init_redis(self):
        """Initialize Redis connection if not already initialized"""
        if not self._initialized and settings.REDIS_URL:
            try:
                self.redis = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                self._initialized = True
                logger.info("Redis rate limiter initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {str(e)}")
                self.redis = None
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        if settings.TRUSTED_PROXIES:
            # Get the right-most IP in the X-Forwarded-For header
            x_forwarded_for = request.headers.get("X-Forwarded-For")
            if x_forwarded_for:
                return x_forwarded_for.split(",")[-1].strip()
        
        # Fall back to the request's client host
        return request.client.host if request.client else "unknown"
    
    async def get_rate_limit_key(self, request: Request, key: str) -> str:
        """Generate a rate limit key based on the request and provided key"""
        client_ip = self.get_client_ip(request)
        return f"{self.key_prefix}:{key}:{client_ip}"
    
    async def is_rate_limited(self, request: Request, key: str) -> bool:
        """Check if the request exceeds the rate limit"""
        if not self.redis and not settings.REDIS_URL:
            # Use in-memory rate limiting in development
            return await self._is_rate_limited_in_memory(request, key)
        
        # Use Redis for rate limiting in production
        await self.init_redis()
        
        if not self.redis:
            logger.warning("Redis not available, falling back to in-memory rate limiting")
            return await self._is_rate_limited_in_memory(request, key)
        
        rate_key = await self.get_rate_limit_key(request, key)
        
        try:
            # Use Redis pipeline for atomic operations
            async with self.redis.pipeline() as pipe:
                current = await pipe.incr(rate_key).execute()
                
                # Set expiration if this is the first request in the window
                if current == 1:
                    await pipe.expire(rate_key, self.window).execute()
                
                return current > self.limit
                
        except Exception as e:
            logger.error(f"Redis error in rate limiting: {str(e)}")
            return False  # Fail open to avoid blocking requests
    
    async def _is_rate_limited_in_memory(self, request: Request, key: str) -> bool:
        """In-memory rate limiting for development"""
        rate_key = await self.get_rate_limit_key(request, key)
        current_time = time.time()
        
        # Initialize rate limit data if it doesn't exist
        if rate_key not in _rate_limit_store:
            _rate_limit_store[rate_key] = {
                'count': 0,
                'window_start': current_time
            }
        
        # Reset the window if it has expired
        if current_time - _rate_limit_store[rate_key]['window_start'] > self.window:
            _rate_limit_store[rate_key] = {
                'count': 0,
                'window_start': current_time
            }
        
        # Check if rate limit is exceeded
        _rate_limit_store[rate_key]['count'] += 1
        return _rate_limit_store[rate_key]['count'] > self.limit
    
    async def get_retry_after(self, request: Request, key: str) -> int:
        """Get the number of seconds until the rate limit resets"""
        if not self.redis and not settings.REDIS_URL:
            # For in-memory rate limiting, return the remaining window
            rate_key = await self.get_rate_limit_key(request, key)
            if rate_key in _rate_limit_store:
                elapsed = time.time() - _rate_limit_store[rate_key]['window_start']
                return max(0, int(self.window - elapsed))
            return 0
        
        # For Redis, get the TTL of the key
        if self.redis:
            rate_key = await self.get_rate_limit_key(request, key)
            ttl = await self.redis.ttl(rate_key)
            return max(0, ttl) if ttl > 0 else 0
        
        return 0

# Global rate limiter instance
rate_limiter = RateLimiter(
    key_prefix="api_rate_limit",
    limit=settings.RATE_LIMIT_PER_MINUTE,
    window=60  # 1 minute window
)

def rate_limit(
    key: str,
    limit: Optional[int] = None,
    window: Optional[int] = None
):
    """
    Decorator to apply rate limiting to a route.
    
    Args:
        key: Unique identifier for the rate limit (e.g., 'login', 'register')
        limit: Maximum number of requests allowed in the time window
        window: Time window in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Create a rate limiter instance with custom settings if provided
            limiter = rate_limiter
            if limit is not None or window is not None:
                limiter = RateLimiter(
                    key_prefix=f"rate_limit_{key}",
                    limit=limit or rate_limiter.limit,
                    window=window or rate_limiter.window
                )
            
            # Check rate limit
            is_limited = await limiter.is_rate_limited(request, key)
            if is_limited:
                retry_after = await limiter.get_retry_after(request, key)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "message": "Too many requests",
                        "retry_after": retry_after
                    },
                    headers={"Retry-After": str(retry_after)}
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
