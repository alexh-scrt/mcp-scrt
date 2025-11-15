import pytest
from unittest.mock import Mock, AsyncMock, patch
from mcp_scrt.services.cache_service import CacheService, CacheStatistics


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = Mock()
    redis.get.return_value = None
    redis.set.return_value = True
    redis.delete.return_value = 1
    redis.keys.return_value = []
    redis.incr.return_value = 1
    redis.hincrby.return_value = 1
    redis.hgetall.return_value = {}
    redis.exists.return_value = 1
    redis.ttl.return_value = 300
    redis.flushdb.return_value = True
    redis.health_check.return_value = {
        "used_memory_human": "10MB",
        "total_keys": 100
    }
    return redis


@pytest.fixture
def cache_service(mock_redis):
    """Create cache service with mock Redis."""
    return CacheService(redis_client=mock_redis)


def test_initialization(cache_service):
    """Test service initialization."""
    assert cache_service.default_ttl == 300
    assert len(cache_service.patterns) > 0
    assert len(cache_service.invalidation_rules) > 0


def test_get_ttl_for_key(cache_service):
    """Test TTL determination based on key patterns."""
    # Exact match
    ttl = cache_service._get_ttl_for_key("gas_price")
    assert ttl == 30

    # Pattern match
    ttl = cache_service._get_ttl_for_key("balance:secret1abc")
    assert ttl == 30

    # No match - use default
    ttl = cache_service._get_ttl_for_key("unknown:key")
    assert ttl == 300


@pytest.mark.anyio
async def test_get_cache_hit(cache_service, mock_redis):
    """Test cache get with hit."""
    mock_redis.get.return_value = '{"balance": "1000"}'

    value = await cache_service.get("balance:secret1abc")

    assert value == {"balance": "1000"}
    mock_redis.get.assert_called_once_with("balance:secret1abc")


@pytest.mark.anyio
async def test_get_cache_miss(cache_service, mock_redis):
    """Test cache get with miss."""
    mock_redis.get.return_value = None

    value = await cache_service.get("balance:secret1abc", default=0)

    assert value == 0


@pytest.mark.anyio
async def test_set(cache_service, mock_redis):
    """Test cache set."""
    await cache_service.set("test:key", {"data": "value"})

    # Verify Redis set was called with TTL
    mock_redis.set.assert_called_once()
    args = mock_redis.set.call_args
    assert args[0][0] == "test:key"
    assert "ex" in args[1]  # TTL parameter


@pytest.mark.anyio
async def test_set_with_custom_ttl(cache_service, mock_redis):
    """Test cache set with custom TTL."""
    await cache_service.set("test:key", "value", ttl=600)

    args = mock_redis.set.call_args
    assert args[1]["ex"] == 600


@pytest.mark.anyio
async def test_delete(cache_service, mock_redis):
    """Test cache delete."""
    mock_redis.delete.return_value = 2

    deleted = await cache_service.delete("key1", "key2")

    assert deleted == 2
    mock_redis.delete.assert_called_once_with("key1", "key2")


@pytest.mark.anyio
async def test_get_or_fetch_cached(cache_service, mock_redis):
    """Test get_or_fetch with cached value."""
    mock_redis.get.return_value = '"cached_value"'

    fetch_fn = AsyncMock(return_value="fetched_value")

    value = await cache_service.get_or_fetch("test:key", fetch_fn)

    assert value == "cached_value"
    fetch_fn.assert_not_called()  # Should not fetch if cached


@pytest.mark.anyio
async def test_get_or_fetch_not_cached(cache_service, mock_redis):
    """Test get_or_fetch with cache miss."""
    mock_redis.get.return_value = None

    fetch_fn = AsyncMock(return_value="fetched_value")

    value = await cache_service.get_or_fetch("test:key", fetch_fn)

    assert value == "fetched_value"
    fetch_fn.assert_called_once()
    mock_redis.set.assert_called_once()  # Should cache result


@pytest.mark.anyio
async def test_invalidate_related(cache_service, mock_redis):
    """Test invalidating related cache keys."""
    mock_redis.keys.return_value = ["balance:secret1abc"]

    await cache_service.invalidate_related(
        operation="secret_send_tokens",
        params={
            "from_address": "secret1abc",
            "to_address": "secret1def"
        }
    )

    # Should delete keys for both addresses
    mock_redis.delete.assert_called()


@pytest.mark.anyio
async def test_invalidate_pattern(cache_service, mock_redis):
    """Test invalidating by pattern."""
    mock_redis.keys.return_value = ["balance:secret1abc", "balance:secret1def"]
    mock_redis.delete.return_value = 2

    deleted = await cache_service.invalidate_pattern("balance:*")

    assert deleted == 2
    mock_redis.keys.assert_called_with("balance:*")


@pytest.mark.anyio
async def test_get_statistics(cache_service, mock_redis):
    """Test getting cache statistics."""
    mock_redis.get.side_effect = [100, 20, 5]  # hits, misses, invalidations

    stats = await cache_service.get_statistics()

    assert isinstance(stats, CacheStatistics)
    assert stats.total_hits == 100
    assert stats.total_misses == 20
    assert stats.hit_rate > 0


@pytest.mark.anyio
async def test_warm_cache(cache_service, mock_redis):
    """Test cache warming."""
    mock_redis.get.return_value = None  # Not cached

    fetch_fn1 = AsyncMock(return_value="value1")
    fetch_fn2 = AsyncMock(return_value="value2")

    keys_and_fetchers = [
        ("key1", fetch_fn1, 300),
        ("key2", fetch_fn2, 600)
    ]

    await cache_service.warm_cache(keys_and_fetchers)

    fetch_fn1.assert_called_once()
    fetch_fn2.assert_called_once()
    assert mock_redis.set.call_count == 2


def test_get_cache_info(cache_service, mock_redis):
    """Test getting cache key info."""
    mock_redis.exists.return_value = 1
    mock_redis.ttl.return_value = 300
    mock_redis.get.return_value = "test_value"

    info = cache_service.get_cache_info("test:key")

    assert info["exists"] is True
    assert info["ttl"] == 300
    assert info["size_bytes"] > 0


@pytest.mark.anyio
async def test_clear_all(cache_service, mock_redis):
    """Test clearing all cache."""
    await cache_service.clear_all()

    mock_redis.flushdb.assert_called_once()
