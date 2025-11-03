"""Unit tests for cache functionality."""

import time
from typing import Any

import pytest

from mcp_scrt.core.cache import Cache


class TestCacheBasicOperations:
    """Test basic cache operations."""

    def test_create_cache(self) -> None:
        """Test creating a cache instance."""
        cache = Cache(default_ttl=60)
        assert cache is not None
        assert cache.default_ttl == 60

    def test_set_and_get(self) -> None:
        """Test setting and getting cache values."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1")

        result = cache.get("key1")
        assert result == "value1"

    def test_get_nonexistent_key(self) -> None:
        """Test getting a non-existent key returns None."""
        cache = Cache(default_ttl=60)
        result = cache.get("nonexistent")

        assert result is None

    def test_get_with_default(self) -> None:
        """Test getting with a default value."""
        cache = Cache(default_ttl=60)
        result = cache.get("nonexistent", default="default_value")

        assert result == "default_value"

    def test_set_with_custom_ttl(self) -> None:
        """Test setting a value with custom TTL."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1", ttl=30)

        result = cache.get("key1")
        assert result == "value1"

    def test_overwrite_existing_key(self) -> None:
        """Test overwriting an existing cache key."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1")
        cache.set("key1", "value2")

        result = cache.get("key1")
        assert result == "value2"

    def test_multiple_keys(self) -> None:
        """Test storing multiple keys."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_cache_different_types(self) -> None:
        """Test caching different data types."""
        cache = Cache(default_ttl=60)

        cache.set("string", "value")
        cache.set("int", 42)
        cache.set("float", 3.14)
        cache.set("list", [1, 2, 3])
        cache.set("dict", {"key": "value"})
        cache.set("none", None)

        assert cache.get("string") == "value"
        assert cache.get("int") == 42
        assert cache.get("float") == 3.14
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict") == {"key": "value"}
        assert cache.get("none") is None


class TestCacheTTL:
    """Test TTL (Time To Live) functionality."""

    def test_ttl_expiration(self) -> None:
        """Test that values expire after TTL."""
        cache = Cache(default_ttl=1)  # 1 second TTL
        cache.set("key1", "value1")

        # Value should exist immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Value should be expired
        assert cache.get("key1") is None

    def test_custom_ttl_expiration(self) -> None:
        """Test custom TTL expiration."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1", ttl=1)

        # Value should exist immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Value should be expired
        assert cache.get("key1") is None

    def test_different_ttls(self) -> None:
        """Test keys with different TTLs."""
        cache = Cache(default_ttl=60)
        cache.set("short", "value1", ttl=1)
        cache.set("long", "value2", ttl=60)

        # Both should exist initially
        assert cache.get("short") == "value1"
        assert cache.get("long") == "value2"

        # Wait for short TTL to expire
        time.sleep(1.1)

        # Short should be expired, long should still exist
        assert cache.get("short") is None
        assert cache.get("long") == "value2"

    def test_zero_ttl(self) -> None:
        """Test zero TTL (immediate expiration)."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1", ttl=0)

        # Should be immediately expired
        assert cache.get("key1") is None


class TestCacheInvalidation:
    """Test cache invalidation operations."""

    def test_delete_key(self) -> None:
        """Test deleting a single key."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.delete("key1")

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_delete_nonexistent_key(self) -> None:
        """Test deleting a non-existent key."""
        cache = Cache(default_ttl=60)

        # Should not raise error
        cache.delete("nonexistent")

    def test_clear_all(self) -> None:
        """Test clearing all cache entries."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

    def test_clear_pattern(self) -> None:
        """Test clearing keys matching a pattern."""
        cache = Cache(default_ttl=60)
        cache.set("user:1:name", "Alice")
        cache.set("user:2:name", "Bob")
        cache.set("post:1:title", "Title")

        cache.clear_pattern("user:*")

        assert cache.get("user:1:name") is None
        assert cache.get("user:2:name") is None
        assert cache.get("post:1:title") == "Title"

    def test_clear_pattern_no_matches(self) -> None:
        """Test clearing pattern with no matches."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1")

        cache.clear_pattern("nomatch:*")

        # Original key should still exist
        assert cache.get("key1") == "value1"


class TestCacheStatistics:
    """Test cache statistics tracking."""

    def test_hits_and_misses(self) -> None:
        """Test hit and miss tracking."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1")

        # Hit
        cache.get("key1")

        # Miss
        cache.get("nonexistent")

        stats = cache.get_stats()
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1

    def test_hit_rate(self) -> None:
        """Test hit rate calculation."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1")

        # 2 hits
        cache.get("key1")
        cache.get("key1")

        # 1 miss
        cache.get("nonexistent")

        stats = cache.get_stats()
        # Hit rate should be approximately 2/3 = 0.666...
        assert stats["hit_rate"] > 0.6
        assert stats["hit_rate"] < 0.7

    def test_size_tracking(self) -> None:
        """Test cache size tracking."""
        cache = Cache(default_ttl=60)

        stats = cache.get_stats()
        assert stats["size"] == 0

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        stats = cache.get_stats()
        assert stats["size"] == 2

    def test_reset_stats(self) -> None:
        """Test resetting statistics."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("nonexistent")

        cache.reset_stats()

        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        # Size should not be reset
        assert stats["size"] == 1


class TestCacheMaxSize:
    """Test cache maximum size handling."""

    def test_max_size_enforcement(self) -> None:
        """Test that cache respects max size."""
        cache = Cache(default_ttl=60, max_size=2)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        stats = cache.get_stats()
        # Should not exceed max size
        assert stats["size"] <= 2

    def test_eviction_policy(self) -> None:
        """Test LRU eviction when max size is reached."""
        cache = Cache(default_ttl=60, max_size=2)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Access key1 to make it more recently used
        cache.get("key1")

        # Add key3, should evict key2 (least recently used)
        cache.set("key3", "value3")

        assert cache.get("key1") == "value1"
        assert cache.get("key3") == "value3"
        # key2 should be evicted
        assert cache.get("key2") is None


class TestCacheContains:
    """Test cache membership operations."""

    def test_contains_existing_key(self) -> None:
        """Test checking if key exists."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1")

        assert cache.contains("key1") is True

    def test_contains_nonexistent_key(self) -> None:
        """Test checking if non-existent key exists."""
        cache = Cache(default_ttl=60)

        assert cache.contains("nonexistent") is False

    def test_contains_expired_key(self) -> None:
        """Test checking if expired key exists."""
        cache = Cache(default_ttl=1)
        cache.set("key1", "value1")

        time.sleep(1.1)

        assert cache.contains("key1") is False


class TestCacheEdgeCases:
    """Test cache edge cases."""

    def test_empty_string_key(self) -> None:
        """Test using empty string as key."""
        cache = Cache(default_ttl=60)
        cache.set("", "value")

        assert cache.get("") == "value"

    def test_none_value(self) -> None:
        """Test storing None as value."""
        cache = Cache(default_ttl=60)
        cache.set("key1", None)

        # Should be able to distinguish between stored None and missing key
        assert cache.contains("key1") is True
        assert cache.get("key1") is None

    def test_large_value(self) -> None:
        """Test storing large value."""
        cache = Cache(default_ttl=60)
        large_value = "x" * 10000

        cache.set("large", large_value)
        assert cache.get("large") == large_value

    def test_negative_ttl(self) -> None:
        """Test negative TTL (should use default or treat as 0)."""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1", ttl=-1)

        # Should either use default TTL or expire immediately
        result = cache.get("key1")
        assert result is None or result == "value1"

    def test_unicode_keys_and_values(self) -> None:
        """Test unicode in keys and values."""
        cache = Cache(default_ttl=60)
        cache.set("键", "值")
        cache.set("🔑", "🎁")

        assert cache.get("键") == "值"
        assert cache.get("🔑") == "🎁"


class TestCacheThreadSafety:
    """Test cache thread safety."""

    def test_concurrent_access(self) -> None:
        """Test concurrent access from multiple threads."""
        import threading

        cache = Cache(default_ttl=60)
        errors: list[Exception] = []

        def worker(thread_id: int) -> None:
            try:
                for i in range(10):
                    key = f"thread{thread_id}:key{i}"
                    cache.set(key, f"value{i}")
                    result = cache.get(key)
                    assert result == f"value{i}"
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # No errors should occur
        assert len(errors) == 0

    def test_concurrent_modifications(self) -> None:
        """Test concurrent modifications to same key."""
        import threading

        cache = Cache(default_ttl=60)

        def writer(value: str) -> None:
            for _ in range(20):
                cache.set("shared_key", value)
                time.sleep(0.001)

        threads = [
            threading.Thread(target=writer, args=("value1",)),
            threading.Thread(target=writer, args=("value2",)),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have one of the values, not corrupted
        result = cache.get("shared_key")
        assert result in ["value1", "value2"]
