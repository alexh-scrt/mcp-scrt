#!/usr/bin/env python
"""Debug script to test Redis connection through proxy."""

import os
import sys
from dotenv import load_dotenv
import redis

# Load environment
load_dotenv()

# Parse remote config
raw_host = os.getenv("REMOTE_HOST", "localhost")
if raw_host.startswith("https://"):
    remote_host = raw_host.replace("https://", "")
elif raw_host.startswith("http://"):
    remote_host = raw_host.replace("http://", "")
else:
    remote_host = raw_host

# Try different configurations
configs = [
    {"name": "Local Redis (no password)", "host": "localhost", "port": 6379, "password": None},
    {"name": "Local Redis (with password)", "host": "localhost", "port": 6379, "password": os.getenv("REDIS_PASSWORD")},
    {"name": "Remote Redis (port 6379)", "host": remote_host, "port": 6379, "password": os.getenv("REDIS_PASSWORD")},
    {"name": "Remote Redis (port 18343)", "host": remote_host, "port": 18343, "password": os.getenv("REDIS_PASSWORD")},
]

for config in configs:
    print(f"\n{'='*60}")
    print(f"Testing: {config['name']}")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  Password: {'***' if config['password'] else 'None'}")
    print(f"{'='*60}")

    try:
        client = redis.Redis(
            host=config['host'],
            port=config['port'],
            password=config['password'],
            db=0,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )

        result = client.ping()
        print(f"✓ Ping successful: {result}")

        # Try a simple operation
        client.set("test:debug", "Hello!")
        value = client.get("test:debug")
        print(f"✓ Set/Get works: {value}")
        client.delete("test:debug")

        info = client.info()
        print(f"✓ Redis version: {info.get('redis_version')}")
        print(f"\n✅ SUCCESS with this configuration!")
        sys.exit(0)

    except redis.ConnectionError as e:
        print(f"❌ Connection failed: {e}")
    except redis.TimeoutError as e:
        print(f"❌ Timeout: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

print(f"\n{'='*60}")
print("❌ All connection attempts failed")
print(f"{'='*60}")
sys.exit(1)
