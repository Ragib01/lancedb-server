"""
Redis client management for LanceDB Server
"""

import redis.asyncio as redis
import structlog
from typing import Optional

from .config import settings

logger = structlog.get_logger()

# Global Redis client
redis_client: Optional[redis.Redis] = None


async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    
    try:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test connection
        await redis_client.ping()
        logger.info("Redis connection established")
        
    except Exception as e:
        logger.error("Failed to initialize Redis", error=str(e))
        raise


async def get_redis():
    """Get Redis client"""
    if redis_client is None:
        await init_redis()
    return redis_client


async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


class CacheManager:
    """Redis cache manager for common operations"""
    
    def __init__(self):
        self.default_ttl = 3600  # 1 hour
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        client = await get_redis()
        return await client.get(key)
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        client = await get_redis()
        ttl = ttl or self.default_ttl
        return await client.setex(key, ttl, value)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        client = await get_redis()
        return bool(await client.delete(key))
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        client = await get_redis()
        return bool(await client.exists(key))
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        client = await get_redis()
        return await client.incrby(key, amount)
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        client = await get_redis()
        return await client.expire(key, ttl)


# Global cache manager instance
cache = CacheManager() 