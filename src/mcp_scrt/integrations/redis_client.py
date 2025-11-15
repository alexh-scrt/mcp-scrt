"""
Redis client wrapper with connection pooling and caching utilities.

This module provides a clean interface to Redis with:
- Connection pooling
- Key pattern management
- TTL management
- Batch operations
- Health checks
"""

import os
import json
from typing import Any, Optional, List, Dict
import redis
from redis.connection import ConnectionPool
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Wrapper for Redis operations.

    Features:
    - Connection pooling
    - JSON serialization
    - TTL management
    - Pattern-based operations
    - Health checks
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        password: str = None,
        db: int = 0,
        decode_responses: bool = True,
        ssl: bool = None
    ):
        """
        Initialize Redis client.

        Args:
            host: Redis host (default: from env REDIS_HOST or 'localhost')
            port: Redis port (default: from env REDIS_PORT or 6379)
            password: Redis password (default: from env REDIS_PASSWORD)
            db: Database number (default: 0)
            decode_responses: Decode responses to strings
            ssl: Enable TLS/SSL (default: from env REDIS_SSL or False)

        Note:
            Redis uses native TCP protocol and cannot be proxied through HTTP.
            For production with TLS, set REDIS_HOST, REDIS_PASSWORD, and REDIS_SSL=true.
        """
        # Redis uses native TCP protocol, not HTTP, so it cannot go through Caddy proxy
        # For development, use REDIS_HOST if set, otherwise localhost
        # In production with direct Redis access, set REDIS_HOST explicitly
        default_host = os.getenv("REDIS_HOST", "localhost")

        # Remove protocol if present (in case someone sets it)
        if default_host.startswith("https://"):
            default_host = default_host.replace("https://", "")
        elif default_host.startswith("http://"):
            default_host = default_host.replace("http://", "")

        self.host = host or default_host
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.db = db
        self.decode_responses = decode_responses

        # SSL/TLS configuration
        if ssl is None:
            # Check env variable (convert string to bool)
            ssl_env = os.getenv("REDIS_SSL", "false").lower()
            self.ssl = ssl_env in ("true", "1", "yes")
        else:
            self.ssl = ssl

        self._client = None
        self._pool = None

    def connect(self) -> redis.Redis:
        """
        Establish connection to Redis.

        Returns:
            Redis client instance

        Raises:
            ConnectionError: If connection fails
        """
        if self._client is not None:
            return self._client

        try:
            # Create connection pool
            # Only include password if it's set (local Redis typically doesn't require password)
            pool_kwargs = {
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "decode_responses": self.decode_responses,
                "max_connections": 10
            }
            if self.password:
                pool_kwargs["password"] = self.password

            # For SSL connections, add SSL certificate verification settings
            if self.ssl:
                import ssl as ssl_module
                from redis.connection import SSLConnection

                # Use SSL connection class and configure SSL parameters
                pool_kwargs["connection_class"] = SSLConnection
                # Use CERT_NONE to skip client certificate requirement
                # (server still uses TLS but doesn't require client cert)
                pool_kwargs["ssl_cert_reqs"] = ssl_module.CERT_NONE
                pool_kwargs["ssl_check_hostname"] = False

            self._pool = ConnectionPool(**pool_kwargs)

            # Create client
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            self._client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")

            return self._client

        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Redis connection failed: {e}")

    def health_check(self) -> Dict[str, Any]:
        """
        Check Redis health status.

        Returns:
            Health status dict with status and metrics
        """
        try:
            client = self.connect()

            # Ping test
            ping = client.ping()

            # Get info
            info = client.info()

            return {
                "status": "healthy",
                "ping": ping,
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_keys": client.dbsize()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "host": self.host,
                "port": self.port
            }

    def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        Set a key-value pair.

        Args:
            key: Cache key
            value: Value (will be JSON serialized if not string)
            ex: Expiry in seconds
            px: Expiry in milliseconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists

        Returns:
            True if successful
        """
        client = self.connect()

        # Serialize value if needed
        if not isinstance(value, (str, bytes)):
            value = json.dumps(value)

        return client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)

    def get(self, key: str) -> Optional[Any]:
        """
        Get value by key.

        Args:
            key: Cache key

        Returns:
            Value (JSON deserialized if possible), or None if not found
        """
        client = self.connect()
        value = client.get(key)

        if value is None:
            return None

        # Try to deserialize JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.

        Args:
            keys: Keys to delete

        Returns:
            Number of keys deleted
        """
        client = self.connect()
        return client.delete(*keys)

    def exists(self, *keys: str) -> int:
        """
        Check if keys exist.

        Args:
            keys: Keys to check

        Returns:
            Number of keys that exist
        """
        client = self.connect()
        return client.exists(*keys)

    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiry on a key.

        Args:
            key: Key to set expiry on
            seconds: Seconds until expiry

        Returns:
            True if successful
        """
        client = self.connect()
        return client.expire(key, seconds)

    def ttl(self, key: str) -> int:
        """
        Get time to live for a key.

        Args:
            key: Key to check

        Returns:
            TTL in seconds, -1 if no expiry, -2 if key doesn't exist
        """
        client = self.connect()
        return client.ttl(key)

    def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching pattern.

        Args:
            pattern: Pattern to match (e.g., "balance:*")

        Returns:
            List of matching keys
        """
        client = self.connect()
        return client.keys(pattern)

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Pattern to match (e.g., "balance:*")

        Returns:
            Number of keys deleted
        """
        keys = self.keys(pattern)
        if keys:
            return self.delete(*keys)
        return 0

    def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """
        Get multiple values at once.

        Args:
            keys: List of keys

        Returns:
            List of values (None for missing keys)
        """
        client = self.connect()
        values = client.mget(keys)

        # Deserialize JSON values
        result = []
        for value in values:
            if value is None:
                result.append(None)
            else:
                try:
                    result.append(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    result.append(value)

        return result

    def mset(self, mapping: Dict[str, Any]) -> bool:
        """
        Set multiple key-value pairs at once.

        Args:
            mapping: Dict of key-value pairs

        Returns:
            True if successful
        """
        client = self.connect()

        # Serialize values
        serialized = {}
        for key, value in mapping.items():
            if not isinstance(value, (str, bytes)):
                serialized[key] = json.dumps(value)
            else:
                serialized[key] = value

        return client.mset(serialized)

    def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter.

        Args:
            key: Counter key
            amount: Amount to increment

        Returns:
            New value
        """
        client = self.connect()
        return client.incrby(key, amount)

    def decr(self, key: str, amount: int = 1) -> int:
        """
        Decrement a counter.

        Args:
            key: Counter key
            amount: Amount to decrement

        Returns:
            New value
        """
        client = self.connect()
        return client.decrby(key, amount)

    def hincrby(self, name: str, key: str, amount: int = 1) -> int:
        """
        Increment a hash field.

        Args:
            name: Hash name
            key: Field key
            amount: Amount to increment

        Returns:
            New value
        """
        client = self.connect()
        return client.hincrby(name, key, amount)

    def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """
        Set hash fields.

        Args:
            name: Hash name
            mapping: Field-value mapping

        Returns:
            Number of fields added
        """
        client = self.connect()

        # Serialize values
        serialized = {}
        for key, value in mapping.items():
            if not isinstance(value, (str, bytes)):
                serialized[key] = json.dumps(value)
            else:
                serialized[key] = value

        return client.hset(name, mapping=serialized)

    def hget(self, name: str, key: str) -> Optional[Any]:
        """
        Get hash field value.

        Args:
            name: Hash name
            key: Field key

        Returns:
            Field value or None
        """
        client = self.connect()
        value = client.hget(name, key)

        if value is None:
            return None

        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def hgetall(self, name: str) -> Dict[str, Any]:
        """
        Get all hash fields.

        Args:
            name: Hash name

        Returns:
            Dict of field-value pairs
        """
        client = self.connect()
        data = client.hgetall(name)

        # Deserialize values
        result = {}
        for key, value in data.items():
            try:
                result[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                result[key] = value

        return result

    def flushdb(self):
        """
        Clear current database.
        WARNING: Deletes all keys in current DB!
        """
        client = self.connect()
        client.flushdb()
        logger.warning(f"Flushed Redis database {self.db}")

    def close(self):
        """Close client connection."""
        if self._client:
            self._client.close()
            self._client = None
        if self._pool:
            self._pool.disconnect()
            self._pool = None
        logger.info("Redis client closed")


# Export
__all__ = ["RedisClient"]
