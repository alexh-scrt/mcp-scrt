#!/usr/bin/env python
"""Debug script using the RedisClient wrapper with remote TLS."""

import logging
logging.basicConfig(level=logging.DEBUG)

from mcp_scrt.integrations.redis_client import RedisClient

try:
    print("Creating Redis client...")
    client = RedisClient()

    print(f"Configuration:")
    print(f"  Host: {client.host}")
    print(f"  Port: {client.port}")
    print(f"  SSL: {client.ssl}")
    print(f"  Password: {'***' if client.password else 'None'}")
    print()

    print("Connecting to Redis...")
    redis = client.connect()
    print(f"✓ Connected: {redis}")

    print("\nTesting health check...")
    health = client.health_check()
    print(f"✓ Health: {health}")

    print("\nTesting set/get...")
    client.set("test:remote", "Hello from remote!")
    value = client.get("test:remote")
    print(f"✓ Set/Get: {value}")

    print("\nCleaning up...")
    client.delete("test:remote")

    print("\n✅ Remote Redis connection successful!")

    client.close()

except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()
