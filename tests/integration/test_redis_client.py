"""Integration tests for Redis client wrapper.

This test suite validates Redis connectivity through the remote proxy
and tests all client operations including caching, TTL, and batch operations.
"""

import pytest
import time
from mcp_scrt.integrations.redis_client import RedisClient


@pytest.fixture
def redis_client():
    """Create Redis client for testing."""
    client = RedisClient()
    yield client
    # Cleanup
    try:
        # Clean up test keys
        test_keys = client.keys("test:*")
        if test_keys:
            client.delete(*test_keys)
    finally:
        client.close()


def test_connection(redis_client):
    """Test basic Redis connection."""
    redis = redis_client.connect()
    assert redis is not None
    # Ping should succeed
    assert redis.ping() is True


def test_health_check(redis_client):
    """Test Redis health check."""
    health = redis_client.health_check()

    assert health["status"] == "healthy"
    assert health["ping"] is True
    assert "host" in health
    assert "port" in health
    assert "connected_clients" in health
    assert "used_memory_human" in health
    assert "total_keys" in health


def test_set_and_get_string(redis_client):
    """Test setting and getting string values."""
    key = "test:string"
    value = "Hello Redis"

    # Set value
    assert redis_client.set(key, value) is True

    # Get value
    retrieved = redis_client.get(key)
    assert retrieved == value

    # Cleanup
    redis_client.delete(key)


def test_set_and_get_json(redis_client):
    """Test setting and getting JSON objects."""
    key = "test:json"
    value = {"name": "test", "count": 42, "active": True}

    # Set JSON value
    assert redis_client.set(key, value) is True

    # Get JSON value (should be deserialized)
    retrieved = redis_client.get(key)
    assert retrieved == value
    assert isinstance(retrieved, dict)

    # Cleanup
    redis_client.delete(key)


def test_set_with_expiry(redis_client):
    """Test setting values with TTL."""
    key = "test:expiry"
    value = "temporary"

    # Set with 2 second expiry
    assert redis_client.set(key, value, ex=2) is True

    # Should exist immediately
    assert redis_client.exists(key) == 1
    assert redis_client.get(key) == value

    # Check TTL
    ttl = redis_client.ttl(key)
    assert 0 < ttl <= 2

    # Wait for expiry
    time.sleep(3)

    # Should be gone
    assert redis_client.exists(key) == 0
    assert redis_client.get(key) is None


def test_delete(redis_client):
    """Test deleting keys."""
    keys = ["test:delete1", "test:delete2", "test:delete3"]

    # Set multiple keys
    for key in keys:
        redis_client.set(key, "value")

    # Verify they exist
    assert redis_client.exists(*keys) == 3

    # Delete them
    deleted = redis_client.delete(*keys)
    assert deleted == 3

    # Verify they're gone
    assert redis_client.exists(*keys) == 0


def test_expire(redis_client):
    """Test setting expiry on existing keys."""
    key = "test:expire"

    # Set value without expiry
    redis_client.set(key, "value")
    assert redis_client.ttl(key) == -1  # No expiry

    # Set expiry
    assert redis_client.expire(key, 5) is True

    # Check TTL
    ttl = redis_client.ttl(key)
    assert 0 < ttl <= 5

    # Cleanup
    redis_client.delete(key)


def test_keys_pattern(redis_client):
    """Test finding keys by pattern."""
    # Create keys with pattern
    test_keys = {
        "test:pattern:1": "value1",
        "test:pattern:2": "value2",
        "test:pattern:3": "value3",
        "test:other": "other"
    }

    for key, value in test_keys.items():
        redis_client.set(key, value)

    # Find pattern keys
    pattern_keys = redis_client.keys("test:pattern:*")
    assert len(pattern_keys) == 3
    assert all(key.startswith("test:pattern:") for key in pattern_keys)

    # Cleanup
    redis_client.delete(*test_keys.keys())


def test_delete_pattern(redis_client):
    """Test deleting keys by pattern."""
    # Create keys with pattern
    for i in range(5):
        redis_client.set(f"test:batch:{i}", f"value{i}")

    # Verify they exist
    batch_keys = redis_client.keys("test:batch:*")
    assert len(batch_keys) == 5

    # Delete by pattern
    deleted = redis_client.delete_pattern("test:batch:*")
    assert deleted == 5

    # Verify they're gone
    assert len(redis_client.keys("test:batch:*")) == 0


def test_mget_mset(redis_client):
    """Test batch get and set operations."""
    # Batch set
    mapping = {
        "test:batch:a": "value_a",
        "test:batch:b": {"type": "json", "value": 123},
        "test:batch:c": "value_c"
    }

    assert redis_client.mset(mapping) is True

    # Batch get
    keys = list(mapping.keys())
    values = redis_client.mget(keys)

    assert len(values) == 3
    assert values[0] == "value_a"
    assert values[1] == {"type": "json", "value": 123}
    assert values[2] == "value_c"

    # Cleanup
    redis_client.delete(*keys)


def test_incr_decr(redis_client):
    """Test counter increment and decrement."""
    key = "test:counter"

    # Increment
    assert redis_client.incr(key) == 1
    assert redis_client.incr(key, 5) == 6

    # Decrement
    assert redis_client.decr(key) == 5
    assert redis_client.decr(key, 3) == 2

    # Cleanup
    redis_client.delete(key)


def test_hash_operations(redis_client):
    """Test hash field operations."""
    hash_name = "test:hash"

    # Set hash fields
    mapping = {
        "field1": "value1",
        "field2": {"nested": "json"},
        "field3": "value3"
    }

    added = redis_client.hset(hash_name, mapping)
    assert added >= 0  # Number of new fields added

    # Get single field
    value = redis_client.hget(hash_name, "field1")
    assert value == "value1"

    # Get all fields
    all_fields = redis_client.hgetall(hash_name)
    assert len(all_fields) == 3
    assert all_fields["field1"] == "value1"
    assert all_fields["field2"] == {"nested": "json"}

    # Increment hash field
    redis_client.hset(hash_name, {"counter": "0"})
    new_value = redis_client.hincrby(hash_name, "counter", 5)
    assert new_value == 5

    # Cleanup
    redis_client.delete(hash_name)


def test_connection_reuse(redis_client):
    """Test that connection is reused."""
    # First connection
    redis1 = redis_client.connect()

    # Second call should return same client
    redis2 = redis_client.connect()

    assert redis1 is redis2


def test_nx_xx_flags(redis_client):
    """Test NX (not exists) and XX (exists) flags."""
    key = "test:flags"

    # NX - set only if not exists
    assert redis_client.set(key, "value1", nx=True) is True
    assert redis_client.set(key, "value2", nx=True) is None  # Should fail

    # XX - set only if exists
    assert redis_client.set(key, "value3", xx=True) is True
    redis_client.delete(key)
    assert redis_client.set(key, "value4", xx=True) is None  # Should fail

    # Cleanup (if any)
    redis_client.delete(key)


def test_missing_key(redis_client):
    """Test getting non-existent keys."""
    key = "test:missing"

    # Ensure key doesn't exist
    redis_client.delete(key)

    # Get should return None
    assert redis_client.get(key) is None

    # TTL should return -2
    assert redis_client.ttl(key) == -2

    # Exists should return 0
    assert redis_client.exists(key) == 0
