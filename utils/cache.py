"""
Cache management using Vercel KV (Redis).

Provides a wrapper around Redis for caching stock data, signals, and state.
Supports TTL, namespacing, and error handling.
"""

import os
import json
import logging
from datetime import timedelta
from typing import Any, Optional

try:
    import redis
except ImportError:
    redis = None

from utils.errors import CacheError

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis cache manager for Vercel KV.

    Handles:
    - Connection management
    - Namespacing to prevent key collisions
    - TTL (time-to-live) support
    - JSON serialization
    - Error handling with fallback
    """

    # Default TTL values (hours)
    TTL_STOCK_DATA = 1  # Real-time cache
    TTL_SIGNAL = 24  # Prevent re-ordering
    TTL_ORDER = 24  # Track orders
    TTL_CONFIG = 8760  # 1 year

    def __init__(self, namespace: str = "stock-scanner", enable_fallback: bool = True):
        """
        Initialize cache manager.

        Args:
            namespace: Namespace prefix for all keys
            enable_fallback: If True, use in-memory dict if Redis unavailable
        """
        self.namespace = namespace
        self.enable_fallback = enable_fallback
        self.redis_client = None
        self.fallback_cache = {} if enable_fallback else None

        self._connect()

    def _connect(self) -> None:
        """
        Establish Redis connection.

        Attempts to connect to Vercel KV using REST API.
        Falls back to in-memory cache if connection fails.
        """
        try:
            if not redis:
                raise ImportError("redis-py not installed")

            kv_url = os.getenv("KV_REST_API_URL")
            kv_token = os.getenv("KV_REST_API_TOKEN")

            if not kv_url or not kv_token:
                logger.warning("Redis credentials not configured, using fallback cache")
                return

            # Connect to Vercel KV
            self.redis_client = redis.from_url(
                kv_url,
                decode_responses=True,
                ssl_certreqs="required",
            )

            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Vercel KV Redis")

        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using fallback cache")
            self.redis_client = None

    def _make_key(self, key: str) -> str:
        """
        Create namespaced cache key.

        Args:
            key: Base key name

        Returns:
            Namespaced key in format: namespace:key
        """
        return f"{self.namespace}:{key}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found

        Raises:
            CacheError: If cache operation fails (with details)
        """
        try:
            full_key = self._make_key(key)

            if self.redis_client:
                # Try Redis first
                value = self.redis_client.get(full_key)
                if value:
                    return json.loads(value)
            elif self.fallback_cache is not None:
                # Use fallback cache
                if full_key in self.fallback_cache:
                    return self.fallback_cache[full_key]

            return None

        except json.JSONDecodeError as e:
            raise CacheError(
                f"Failed to deserialize cached value for key {key}",
                error_code="CACHE_DECODE_ERROR",
                details={"key": key, "error": str(e)},
            )
        except Exception as e:
            raise CacheError(
                f"Cache get operation failed for key {key}: {str(e)}",
                error_code="CACHE_GET_ERROR",
                details={"key": key, "error": str(e)},
            )

    def set(self, key: str, value: Any, ttl_hours: int = 1) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl_hours: Time-to-live in hours (default: 1)

        Returns:
            True if successful

        Raises:
            CacheError: If cache operation fails
        """
        try:
            full_key = self._make_key(key)
            json_value = json.dumps(value)
            ttl = timedelta(hours=ttl_hours)

            if self.redis_client:
                # Set in Redis with TTL
                self.redis_client.setex(full_key, ttl, json_value)
                logger.debug(f"Cached value for key {key} (TTL: {ttl_hours}h)")
            elif self.fallback_cache is not None:
                # Set in fallback cache
                self.fallback_cache[full_key] = value

            return True

        except Exception as e:
            raise CacheError(
                f"Cache set operation failed for key {key}: {str(e)}",
                error_code="CACHE_SET_ERROR",
                details={"key": key, "ttl_hours": ttl_hours, "error": str(e)},
            )

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful

        Raises:
            CacheError: If cache operation fails
        """
        try:
            full_key = self._make_key(key)

            if self.redis_client:
                self.redis_client.delete(full_key)
                logger.debug(f"Deleted cache key {key}")
            elif self.fallback_cache is not None and full_key in self.fallback_cache:
                del self.fallback_cache[full_key]

            return True

        except Exception as e:
            raise CacheError(
                f"Cache delete operation failed for key {key}: {str(e)}",
                error_code="CACHE_DELETE_ERROR",
                details={"key": key, "error": str(e)},
            )

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise

        Raises:
            CacheError: If cache operation fails
        """
        try:
            full_key = self._make_key(key)

            if self.redis_client:
                return self.redis_client.exists(full_key) > 0
            elif self.fallback_cache is not None:
                return full_key in self.fallback_cache

            return False

        except Exception as e:
            raise CacheError(
                f"Cache exists check failed for key {key}: {str(e)}",
                error_code="CACHE_EXISTS_ERROR",
                details={"key": key, "error": str(e)},
            )

    def clear(self, pattern: str = None) -> bool:
        """
        Clear cache entries.

        Args:
            pattern: Optional glob pattern to match keys (e.g., 'signal:*')
                    If None, clears entire namespace

        Returns:
            True if successful

        Raises:
            CacheError: If cache operation fails
        """
        try:
            if self.redis_client:
                if pattern:
                    search_pattern = self._make_key(pattern)
                    keys = self.redis_client.keys(search_pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                    logger.info(f"Cleared {len(keys)} cache entries matching {pattern}")
                else:
                    # Clear entire namespace
                    search_pattern = self._make_key("*")
                    keys = self.redis_client.keys(search_pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                    logger.info(f"Cleared entire cache namespace ({len(keys)} entries)")

            elif self.fallback_cache is not None:
                if pattern:
                    # Match pattern in fallback
                    import fnmatch

                    keys_to_delete = [
                        k for k in self.fallback_cache.keys() if fnmatch.fnmatch(k, self._make_key(pattern))
                    ]
                    for k in keys_to_delete:
                        del self.fallback_cache[k]
                else:
                    self.fallback_cache.clear()

            return True

        except Exception as e:
            raise CacheError(
                f"Cache clear operation failed: {str(e)}",
                error_code="CACHE_CLEAR_ERROR",
                details={"pattern": pattern, "error": str(e)},
            )

    def health(self) -> dict:
        """
        Check cache health status.

        Returns:
            Dictionary with health information:
            {
                'status': 'healthy'|'degraded'|'unhealthy',
                'connected': bool,
                'fallback_active': bool,
            }
        """
        try:
            if self.redis_client:
                self.redis_client.ping()
                return {
                    "status": "healthy",
                    "connected": True,
                    "fallback_active": False,
                    "backend": "redis",
                }
            elif self.fallback_cache is not None:
                return {
                    "status": "degraded",
                    "connected": False,
                    "fallback_active": True,
                    "backend": "memory",
                }
            else:
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "fallback_active": False,
                    "backend": "none",
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "fallback_active": self.fallback_cache is not None,
                "error": str(e),
            }


# Global cache instance
cache = CacheManager()