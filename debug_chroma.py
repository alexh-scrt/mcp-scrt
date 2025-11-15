#!/usr/bin/env python
"""Debug script to test ChromaDB connection through proxy."""

import os
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

# Load environment
load_dotenv()

# Parse config
raw_host = os.getenv("REMOTE_HOST", "localhost")
if raw_host.startswith("https://"):
    host = raw_host.replace("https://", "")
    use_ssl = True
elif raw_host.startswith("http://"):
    host = raw_host.replace("http://", "")
    use_ssl = False
else:
    host = raw_host
    use_ssl = True

port = int(os.getenv("REMOTE_PORT", "8000"))
api_key = os.getenv("API_KEY")

print(f"Configuration:")
print(f"  Host: {host}")
print(f"  Port: {port}")
print(f"  SSL: {use_ssl}")
print(f"  API Key: {api_key[:20]}..." if api_key else "  API Key: None")
print()

# Test connection
headers = {}
if api_key:
    headers["Authorization"] = f"Bearer {api_key}"
    headers["X-API-Key"] = api_key

print("Headers:")
for k, v in headers.items():
    print(f"  {k}: {v[:20]}..." if len(v) > 20 else f"  {k}: {v}")
print()

settings = Settings(
    anonymized_telemetry=False,
    allow_reset=True,
    chroma_server_api_default_path="/chroma"
)

try:
    print("Creating ChromaDB client...")
    client = chromadb.HttpClient(
        host=host,
        port=port,
        ssl=use_ssl,
        headers=headers,
        settings=settings
    )

    print("Testing heartbeat...")
    heartbeat = client.heartbeat()
    print(f"✓ Heartbeat: {heartbeat}")

    print("\nListing collections...")
    collections = client.list_collections()
    print(f"✓ Collections ({len(collections)}):")
    for col in collections:
        print(f"  - {col.name}")

    print("\n✅ Connection successful!")

except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()
