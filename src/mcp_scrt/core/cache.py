"""Cache implementation with TTL support.

This module provides a thread-safe caching layer with TTL (Time To Live) support,
pattern-based invalidation, and statistics tracking.
"""

import fnmatch
import threading
import time
from typing import Any, Dict, Optional

from cachetools import TTLCache


class Cache:
    """Thread-safe cache with TTL support and statistics tracking.

    This cache provides:
    - TTL-based expiration for cache entries
    - Thread-safe operations using locks
    - Pattern-based cache invalidation
    - Hit/miss statistics tracking
    - Configurable maximum size with LRU eviction
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 1000) -> None:
        """Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds (default: 300)
            max_size: Maximum number of entries (default: 1000)
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: TTLCache[str, Any] = TTLCache(maxsize=max_size, ttl=default_ttl)
        self._lock = threading.RLock()

        # Statistics
        self._hits = 0
        self._misses = 0

        # Store custom TTLs for each key
        self._ttls: Dict[str, float] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default if not found/expired
        """
        with self._lock:
            # Check if key has custom TTL and if it's expired
            if key in self._ttls:
                if time.time() > self._ttls[key]:
                    # Expired, remove it
                    self._cache.pop(key, None)
                    self._ttls.pop(key, None)
                    self._misses += 1
                    return default

            try:
                value = self._cache[key]
                self._hits += 1
                return value
            except KeyError:
                self._misses += 1
                return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        with self._lock:
            # Handle zero or negative TTL
            if ttl is not None and ttl <= 0:
                # Don't cache or remove immediately
                self._cache.pop(key, None)
                self._ttls.pop(key, None)
                return

            self._cache[key] = value

            # Store custom TTL expiration time
            if ttl is not None and ttl != self.default_ttl:
                self._ttls[key] = time.time() + ttl
            else:
                # Remove custom TTL if using default
                self._ttls.pop(key, None)

    def delete(self, key: str) -> None:
        """Delete a key from cache.

        Args:
            key: Cache key to delete
        """
        with self._lock:
            self._cache.pop(key, None)
            self._ttls.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._ttls.clear()

    def clear_pattern(self, pattern: str) -> None:
        """Clear cache entries matching a pattern.

        Args:
            pattern: Pattern to match (supports wildcards like 'user:*')
        """
        with self._lock:
            # Get keys matching pattern
            keys_to_delete = [key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)]

            # Delete matching keys
            for key in keys_to_delete:
                self._cache.pop(key, None)
                self._ttls.pop(key, None)

    def contains(self, key: str) -> bool:
        """Check if key exists in cache and is not expired.

        Args:
            key: Cache key to check

        Returns:
            True if key exists and not expired, False otherwise
        """
        with self._lock:
            # Check custom TTL expiration
            if key in self._ttls:
                if time.time() > self._ttls[key]:
                    # Expired
                    self._cache.pop(key, None)
                    self._ttls.pop(key, None)
                    return False

            return key in self._cache

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics:
            - hits: Number of cache hits
            - misses: Number of cache misses
            - size: Current cache size
            - hit_rate: Cache hit rate (0.0 to 1.0)
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0

            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._cache),
                "hit_rate": hit_rate,
            }

    def reset_stats(self) -> None:
        """Reset cache statistics (does not clear cache)."""
        with self._lock:
            self._hits = 0
            self._misses = 0
