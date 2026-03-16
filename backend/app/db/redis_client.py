import redis.asyncio as aioredis
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_redis_client = None

async def get_redis_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("Redis cloud client initialized")
    return _redis_client

async def close_redis_client():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")