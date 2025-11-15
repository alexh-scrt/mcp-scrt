import pytest
from unittest.mock import Mock, MagicMock
import time
from mcp_scrt.middleware.telemetry import TelemetryMiddleware, ExecutionMetrics


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = Mock()
    redis.redis = Mock()
    redis.redis.lpush = Mock()
    redis.redis.ltrim = Mock()
    redis.redis.zadd = Mock()
    redis.redis.zrange = Mock(return_value=[])
    redis.redis.zremrangebyrank = Mock()
    redis.redis.lrange = Mock(return_value=[])
    redis.hincrby = Mock()
    redis.hget = Mock(return_value=0)
    redis.hgetall = Mock(return_value={})
    return redis


@pytest.fixture
def middleware(mock_redis):
    """Create telemetry middleware with mock Redis."""
    return TelemetryMiddleware(redis_client=mock_redis)


def test_before_execute(middleware):
    """Test before_execute records context."""
    context = middleware.before_execute(
        "test_tool",
        {"param1": "value1"}
    )

    assert "tool_name" in context
    assert "start_time" in context
    assert "params_size" in context
    assert context["tool_name"] == "test_tool"


@pytest.mark.anyio
async def test_after_execute_success(middleware, mock_redis):
    """Test after_execute records successful execution."""
    context = {
        "tool_name": "test_tool",
        "start_time": time.time() - 0.1,  # 100ms ago
        "params_size": 50
    }

    await middleware.after_execute(
        tool_name="test_tool",
        params={},
        result={"success": True},
        context=context,
        error=None
    )

    # Verify metrics were stored
    mock_redis.redis.lpush.assert_called()
    mock_redis.hincrby.assert_called()


@pytest.mark.anyio
async def test_after_execute_failure(middleware, mock_redis):
    """Test after_execute records failed execution."""
    context = {
        "tool_name": "test_tool",
        "start_time": time.time(),
        "params_size": 50
    }

    await middleware.after_execute(
        tool_name="test_tool",
        params={},
        result=None,
        context=context,
        error=ValueError("Test error")
    )

    # Verify failure was recorded
    mock_redis.hincrby.assert_any_call(
        "telemetry:stats:failed",
        "test_tool",
        1
    )


@pytest.mark.anyio
async def test_get_tool_statistics(middleware, mock_redis):
    """Test getting tool statistics."""
    mock_redis.hget.side_effect = [100, 90, 10]  # total, successful, failed
    mock_redis.redis.zrange.return_value = [100.0, 200.0, 150.0]

    stats = await middleware.get_tool_statistics("test_tool")

    assert stats is not None
    assert stats.total_executions == 100
    assert stats.successful_executions == 90
    assert stats.failed_executions == 10
    assert stats.success_rate == 90.0
