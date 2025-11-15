"""
Cache service for intelligent data caching.

This service provides:
- Smart cache key generation
- TTL management by data type
- Pattern-based invalidation
- Cache statistics and monitoring
- Multi-layer caching strategy
"""

import hashlib
import json
from typing import Any, Optional, Callable, Dict, List, Awaitable
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheStatistics:
    """Cache performance statistics."""
    total_hits: int
    total_misses: int
    hit_rate: float
    total_keys: int
    memory_used: str
    top_keys: List[Dict[str, Any]]
    invalidations: int


# Cache key patterns with default TTLs (in seconds)
CACHE_PATTERNS = {
    # Rapidly changing data (30 seconds)
    "balance:{address}": 30,
    "gas_price": 30,
    "block:latest": 30,
    "account:{address}:sequence": 30,

    # Moderately changing data (5 minutes)
    "validator:{address}": 300,
    "delegations:{address}": 300,
    "rewards:{address}": 300,
    "account:{address}:info": 300,
    "tx:status:{hash}": 300,

    # Slowly changing data (1 hour)
    "validators:all": 3600,
    "proposals:all": 3600,
    "proposal:{id}": 3600,
    "code_info:{code_id}": 3600,
    "contract_info:{address}": 3600,
    "ibc:channels": 3600,

    # Static data (24 hours)
    "block:{height}": 86400,
    "tx:{hash}": 86400,
    "contract_code:{code_id}": 86400,

    # Knowledge base (1 hour)
    "knowledge:query:*": 3600,
    "embedding:*": 86400,

    # Graph analysis (5 minutes)
    "graph:*": 300,
}

# Invalidation rules: operation -> patterns to invalidate
INVALIDATION_RULES = {
    # Bank operations
    "secret_send_tokens": [
        "balance:{from_address}",
        "balance:{to_address}",
        "account:{from_address}:info",
    ],
    "secret_multi_send": [
        "balance:*",  # Invalidate all balances (multiple recipients)
    ],

    # Staking operations
    "secret_delegate": [
        "balance:{delegator}",
        "delegations:{delegator}",
        "validator:{validator}",
        "validators:all",
        "rewards:{delegator}",
    ],
    "secret_undelegate": [
        "balance:{delegator}",
        "delegations:{delegator}",
        "validator:{validator}",
        "validators:all",
    ],
    "secret_redelegate": [
        "delegations:{delegator}",
        "validator:{from_validator}",
        "validator:{to_validator}",
        "validators:all",
    ],
    "secret_withdraw_rewards": [
        "balance:{delegator}",
        "rewards:{delegator}",
        "delegations:{delegator}",
    ],

    # Governance operations
    "secret_submit_proposal": [
        "proposals:all",
        "balance:{proposer}",
    ],
    "secret_vote_proposal": [
        "proposal:{proposal_id}",
        "account:{voter}:info",
    ],
    "secret_deposit_proposal": [
        "proposal:{proposal_id}",
        "balance:{depositor}",
    ],

    # Contract operations
    "secret_instantiate_contract": [
        "balance:{sender}",
        "account:{sender}:info",
    ],
    "secret_execute_contract": [
        "balance:{sender}",
        "contract_info:{contract_address}",
    ],

    # Knowledge operations
    "knowledge_add_document": [
        "knowledge:query:*",
    ],
    "knowledge_update_document": [
        "knowledge:query:*",
    ],
    "knowledge_delete_document": [
        "knowledge:query:*",
    ],
}


class CacheService:
    """
    High-level caching service with smart invalidation.

    Features:
    - Automatic TTL based on data type
    - Pattern-based invalidation
    - Cache-aside pattern support
    - Performance analytics
    - Multi-layer caching
    """

    def __init__(
        self,
        redis_client,
        default_ttl: int = 300  # 5 minutes
    ):
        """
        Initialize cache service.

        Args:
            redis_client: Redis client
            default_ttl: Default TTL in seconds
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.patterns = CACHE_PATTERNS
        self.invalidation_rules = INVALIDATION_RULES

        logger.info("Initialized CacheService")

    def _get_ttl_for_key(self, key: str) -> int:
        """
        Determine TTL for a cache key based on patterns.

        Args:
            key: Cache key

        Returns:
            TTL in seconds
        """
        # Check if key matches any pattern
        for pattern, ttl in self.patterns.items():
            # Handle wildcard patterns (e.g., "embedding:*")
            if "*" in pattern:
                prefix = pattern.split("*")[0]
                if key.startswith(prefix):
                    return ttl
            # Handle template patterns (e.g., "balance:{address}")
            elif "{" in pattern:
                # Extract the prefix before the template variable
                prefix = pattern.split("{")[0]
                if key.startswith(prefix):
                    return ttl
            # Handle exact match
            elif pattern == key:
                return ttl

        # Default TTL
        return self.default_ttl

    def _normalize_value(self, value: Any) -> str:
        """
        Normalize value for caching (convert to JSON string).

        Args:
            value: Value to cache

        Returns:
            JSON string
        """
        if isinstance(value, str):
            return value
        return json.dumps(value, default=str)

    def _denormalize_value(self, value: Optional[str]) -> Any:
        """
        Denormalize cached value (parse JSON string).

        Args:
            value: Cached string value

        Returns:
            Parsed value or None
        """
        if value is None:
            return None

        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        value = self.redis.get(key)

        if value is not None:
            # Record cache hit
            await self._record_hit(key)
            logger.debug(f"Cache hit: {key}")
            return self._denormalize_value(value)

        # Record cache miss
        await self._record_miss(key)
        logger.debug(f"Cache miss: {key}")
        return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL (uses pattern-based if not provided)

        Returns:
            True if successful
        """
        # Determine TTL
        if ttl is None:
            ttl = self._get_ttl_for_key(key)

        # Normalize value
        normalized = self._normalize_value(value)

        # Set in Redis with TTL
        success = self.redis.set(key, normalized, ex=ttl)

        if success:
            logger.debug(f"Cached: {key} (TTL: {ttl}s)")

        return success

    async def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.

        Args:
            keys: Keys to delete

        Returns:
            Number of keys deleted
        """
        if not keys:
            return 0

        deleted = self.redis.delete(*keys)
        logger.debug(f"Deleted {deleted} cache keys")
        return deleted

    async def get_or_fetch(
        self,
        key: str,
        fetch_fn: Callable[[], Awaitable[Any]],
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get from cache or fetch from source (cache-aside pattern).

        Args:
            key: Cache key
            fetch_fn: Async function to fetch data if not cached
            ttl: Optional TTL

        Returns:
            Cached or fetched value
        """
        # Try cache first
        cached = await self.get(key)
        if cached is not None:
            return cached

        # Fetch from source
        logger.debug(f"Fetching data for cache key: {key}")
        data = await fetch_fn()

        # Cache the result
        if data is not None:
            await self.set(key, data, ttl=ttl)

        return data

    async def invalidate_related(
        self,
        operation: str,
        params: Dict[str, Any]
    ):
        """
        Invalidate cache keys related to an operation.

        Args:
            operation: Operation name (e.g., "secret_delegate")
            params: Operation parameters
        """
        if operation not in self.invalidation_rules:
            logger.debug(f"No invalidation rules for operation: {operation}")
            return

        patterns = self.invalidation_rules[operation]
        keys_to_delete = []

        for pattern in patterns:
            try:
                # Format pattern with parameters
                formatted_key = pattern.format(**params)

                # Handle wildcard patterns
                if "*" in formatted_key:
                    # Delete all matching keys
                    matching_keys = self.redis.keys(formatted_key)
                    keys_to_delete.extend(matching_keys)
                else:
                    keys_to_delete.append(formatted_key)

            except KeyError as e:
                # Parameter not provided, skip this pattern
                logger.debug(f"Skipping pattern {pattern}: missing parameter {e}")
                continue

        # Delete all collected keys
        if keys_to_delete:
            deleted = await self.delete(*keys_to_delete)
            await self._record_invalidation(operation, deleted)
            logger.info(f"Invalidated {deleted} cache keys for operation: {operation}")

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "balance:*")

        Returns:
            Number of keys deleted
        """
        keys = self.redis.keys(pattern)

        if keys:
            deleted = self.redis.delete(*keys)
            logger.info(f"Invalidated {deleted} keys matching pattern: {pattern}")
            return deleted

        return 0

    async def _record_hit(self, key: str):
        """Record a cache hit for statistics."""
        self.redis.incr("cache:stats:hits")
        self.redis.hincrby("cache:stats:keys", key, 1)

    async def _record_miss(self, key: str):
        """Record a cache miss for statistics."""
        self.redis.incr("cache:stats:misses")

    async def _record_invalidation(self, operation: str, count: int):
        """Record cache invalidations for statistics."""
        self.redis.incr("cache:stats:invalidations", count)
        self.redis.hincrby("cache:stats:operations", operation, count)

    async def get_statistics(self) -> CacheStatistics:
        """
        Get cache performance statistics.

        Returns:
            Cache statistics
        """
        hits = int(self.redis.get("cache:stats:hits") or 0)
        misses = int(self.redis.get("cache:stats:misses") or 0)
        invalidations = int(self.redis.get("cache:stats:invalidations") or 0)

        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0.0

        # Get memory info from Redis
        info = self.redis.health_check()
        memory_used = info.get("used_memory_human", "unknown")
        total_keys = info.get("total_keys", 0)

        # Get top cached keys
        top_keys_data = self.redis.hgetall("cache:stats:keys")
        top_keys = [
            {"key": k, "hits": v}
            for k, v in sorted(
                top_keys_data.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        ]

        return CacheStatistics(
            total_hits=hits,
            total_misses=misses,
            hit_rate=hit_rate,
            total_keys=total_keys,
            memory_used=memory_used,
            top_keys=top_keys,
            invalidations=invalidations
        )

    async def reset_statistics(self):
        """Reset cache statistics."""
        self.redis.delete(
            "cache:stats:hits",
            "cache:stats:misses",
            "cache:stats:invalidations"
        )
        self.redis.delete("cache:stats:keys")
        self.redis.delete("cache:stats:operations")
        logger.info("Cache statistics reset")

    async def warm_cache(
        self,
        keys_and_fetchers: List[tuple]
    ):
        """
        Warm cache with pre-fetched data.

        Args:
            keys_and_fetchers: List of (key, fetch_fn, ttl) tuples
        """
        logger.info(f"Warming cache with {len(keys_and_fetchers)} items")

        for item in keys_and_fetchers:
            if len(item) == 2:
                key, fetch_fn = item
                ttl = None
            else:
                key, fetch_fn, ttl = item

            try:
                # Check if already cached
                if await self.get(key) is not None:
                    logger.debug(f"Key already cached: {key}")
                    continue

                # Fetch and cache
                data = await fetch_fn()
                if data is not None:
                    await self.set(key, data, ttl=ttl)
                    logger.debug(f"Warmed cache: {key}")

            except Exception as e:
                logger.warning(f"Failed to warm cache for {key}: {e}")
                continue

    async def clear_all(self):
        """
        Clear all cache data.
        WARNING: This deletes all keys in the Redis database!
        """
        self.redis.flushdb()
        logger.warning("All cache data cleared")

    def get_cache_info(self, key: str) -> Dict[str, Any]:
        """
        Get information about a cached key.

        Args:
            key: Cache key

        Returns:
            Info dict with TTL, size, etc.
        """
        exists = self.redis.exists(key)

        if not exists:
            return {"exists": False}

        ttl = self.redis.ttl(key)
        value = self.redis.get(key)
        size = len(value) if value else 0

        return {
            "exists": True,
            "ttl": ttl,
            "size_bytes": size,
            "expires_at": datetime.utcnow().timestamp() + ttl if ttl > 0 else None
        }


# Export
__all__ = ["CacheService", "CacheStatistics", "CACHE_PATTERNS", "INVALIDATION_RULES"]
