#!/usr/bin/env python
"""Debug script using the ChromaDBClient wrapper."""

import logging
logging.basicConfig(level=logging.DEBUG)

from mcp_scrt.integrations.chromadb_client import ChromaDBClient

try:
    print("Creating ChromaDB client...")
    client = ChromaDBClient()

    print("Connecting to ChromaDB...")
    chroma = client.connect()
    print(f"✓ Connected: {chroma}")

    print("\nTesting heartbeat...")
    heartbeat = chroma.heartbeat()
    print(f"✓ Heartbeat: {heartbeat}")

    print("\nListing collections...")
    collections = chroma.list_collections()
    print(f"✓ Collections ({len(collections)}):")
    for col in collections:
        print(f"  - {col.name}")

    print("\n✅ Connection successful!")

    client.close()

except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()
