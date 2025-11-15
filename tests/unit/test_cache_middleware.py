import pytest
from unittest.mock import Mock, AsyncMock
from mcp_scrt.middleware.cache_middleware import CacheMiddleware, CacheContext


@pytest.fixture
def mock_cache_service():
    """Mock cache service."""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.invalidate_related = AsyncMock()
    return cache


@pytest.fixture
def middleware(mock_cache_service):
    """Create cache middleware with mock cache service."""
    return CacheMiddleware(cache_service=mock_cache_service)


def test_should_cache_tool(middleware):
    """Test determining if tool should be cached."""
    # Read operation - should cache
    assert middleware._should_cache_tool("secret_get_balance") is True

    # Write operation - should not cache
    assert middleware._should_cache_tool("secret_send_tokens") is False

    # Wallet operation - should not cache
    assert middleware._should_cache_tool("secret_create_wallet") is False


def test_generate_cache_key_with_pattern(middleware):
    """Test cache key generation with predefined pattern."""
    key = middleware._generate_cache_key(
        "secret_get_balance",
        {"address": "secret1abc123"}
    )

    assert key == "balance:secret1abc123"


def test_generate_cache_key_without_pattern(middleware):
    """Test cache key generation without pattern (hash-based)."""
    key = middleware._generate_cache_key(
        "unknown_tool",
        {"param1": "value1", "param2": "value2"}
    )

    assert key.startswith("tool:unknown_tool:")
    assert len(key) > len("tool:unknown_tool:")


def test_generate_cache_key_consistency(middleware):
    """Test that same parameters generate same key."""
    params = {"address": "secret1abc", "height": 100}

    key1 = middleware._generate_cache_key("test_tool", params)
    key2 = middleware._generate_cache_key("test_tool", params)

    assert key1 == key2


@pytest.mark.anyio
async def test_before_execute_cache_hit(middleware, mock_cache_service):
    """Test before_execute with cache hit."""
    mock_cache_service.get.return_value = {"balance": "1000"}

    context = await middleware.before_execute(
        "secret_get_balance",
        {"address": "secret1abc"}
    )

    assert context.cache_hit is True
    assert context.cache_key == "balance:secret1abc"


@pytest.mark.anyio
async def test_before_execute_cache_miss(middleware, mock_cache_service):
    """Test before_execute with cache miss."""
    mock_cache_service.get.return_value = None

    context = await middleware.before_execute(
        "secret_get_balance",
        {"address": "secret1abc"}
    )

    assert context.cache_hit is False
    assert context.cache_key is not None


@pytest.mark.anyio
async def test_before_execute_uncacheable(middleware):
    """Test before_execute with uncacheable tool."""
    context = await middleware.before_execute(
        "secret_send_tokens",
        {"recipient": "secret1def", "amount": "1000"}
    )

    assert context.should_cache is False


@pytest.mark.anyio
async def test_after_execute_caches_result(middleware, mock_cache_service):
    """Test after_execute caches successful result."""
    context = CacheContext(
        cache_key="test:key",
        should_cache=True
    )

    await middleware.after_execute(
        tool_name="secret_get_balance",
        params={"address": "secret1abc"},
        result={"balance": "1000"},
        context=context,
        error=None
    )

    mock_cache_service.set.assert_called_once()


@pytest.mark.anyio
async def test_after_execute_skips_on_error(middleware, mock_cache_service):
    """Test after_execute doesn't cache on error."""
    context = CacheContext(
        cache_key="test:key",
        should_cache=True
    )

    await middleware.after_execute(
        tool_name="secret_get_balance",
        params={"address": "secret1abc"},
        result=None,
        context=context,
        error=Exception("Test error")
    )

    mock_cache_service.set.assert_not_called()


@pytest.mark.anyio
async def test_after_execute_invalidates_on_write(middleware, mock_cache_service):
    """Test after_execute invalidates cache for write operations."""
    context = CacheContext(should_cache=False)

    await middleware.after_execute(
        tool_name="secret_send_tokens",
        params={"from_address": "secret1abc", "to_address": "secret1def"},
        result={"tx_hash": "ABC123"},
        context=context,
        error=None
    )

    mock_cache_service.invalidate_related.assert_called_once()
