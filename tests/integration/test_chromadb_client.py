"""Integration tests for ChromaDB client.

These tests require:
1. ChromaDB service running (via docker-compose)
2. Access through Caddy proxy
3. API_KEY authentication configured in .env
"""

import pytest
from mcp_scrt.integrations.chromadb_client import ChromaDBClient


@pytest.fixture
def chroma_client():
    """Fixture for ChromaDB client.

    Reads configuration from .env:
    - REMOTE_HOST
    - REMOTE_PORT
    - API_KEY
    """
    client = ChromaDBClient()
    yield client
    client.close()


def test_connection(chroma_client):
    """Test basic connection through proxy."""
    client_instance = chroma_client.connect()
    assert client_instance is not None


def test_health_check(chroma_client):
    """Test health check."""
    health = chroma_client.health_check()
    assert health["status"] == "healthy"
    assert "heartbeat" in health
    assert health["ssl"] is True  # Should be using SSL for remote connection


def test_collection_lifecycle(chroma_client):
    """Test collection CRUD operations."""
    test_collection_name = "test_collection"

    # Clean up any existing test collection
    try:
        chroma_client.delete_collection(test_collection_name)
    except Exception:
        pass  # Collection might not exist

    # Create collection
    collection = chroma_client.get_or_create_collection(test_collection_name)
    assert collection is not None

    # List collections
    collections = chroma_client.list_collections()
    assert test_collection_name in collections

    # Delete collection
    chroma_client.delete_collection(test_collection_name)
    collections = chroma_client.list_collections()
    assert test_collection_name not in collections


def test_add_and_query_documents(chroma_client):
    """Test adding and querying documents."""
    collection_name = "test_docs"

    # Clean up
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass

    # Add documents
    chroma_client.add_documents(
        collection_name=collection_name,
        documents=["Secret Network is a blockchain", "Privacy is important"],
        metadatas=[{"source": "test1"}, {"source": "test2"}],
        ids=["doc1", "doc2"]
    )

    # Verify documents were added
    count = chroma_client.count_documents(collection_name)
    assert count == 2

    # Query
    results = chroma_client.query(
        collection_name=collection_name,
        query_texts=["blockchain privacy"],
        n_results=2
    )

    assert len(results["ids"][0]) == 2
    assert "doc1" in results["ids"][0] or "doc2" in results["ids"][0]

    # Cleanup
    chroma_client.delete_collection(collection_name)


def test_update_documents(chroma_client):
    """Test document updates."""
    collection_name = "test_updates"

    # Clean up
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass

    # Add initial documents
    chroma_client.add_documents(
        collection_name=collection_name,
        documents=["Original text"],
        metadatas=[{"version": 1}],
        ids=["doc1"]
    )

    # Update
    chroma_client.update_documents(
        collection_name=collection_name,
        ids=["doc1"],
        documents=["Updated text"],
        metadatas=[{"version": 2}]
    )

    # Verify update
    results = chroma_client.query(
        collection_name=collection_name,
        query_texts=["Updated text"],
        n_results=1
    )

    assert results["metadatas"][0][0]["version"] == 2

    # Cleanup
    chroma_client.delete_collection(collection_name)


def test_delete_documents(chroma_client):
    """Test document deletion."""
    collection_name = "test_delete_docs"

    # Clean up
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass

    # Add documents
    chroma_client.add_documents(
        collection_name=collection_name,
        documents=["Doc 1", "Doc 2", "Doc 3"],
        metadatas=[{"id": 1}, {"id": 2}, {"id": 3}],
        ids=["doc1", "doc2", "doc3"]
    )

    # Verify count
    count = chroma_client.count_documents(collection_name)
    assert count == 3

    # Delete one document
    chroma_client.delete_documents(collection_name, ids=["doc2"])

    # Verify count decreased
    count = chroma_client.count_documents(collection_name)
    assert count == 2

    # Cleanup
    chroma_client.delete_collection(collection_name)


def test_query_with_filters(chroma_client):
    """Test querying with metadata filters."""
    collection_name = "test_filters"

    # Clean up
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass

    # Add documents with different metadata
    chroma_client.add_documents(
        collection_name=collection_name,
        documents=[
            "Secret Network blockchain",
            "Privacy technology",
            "Decentralized network"
        ],
        metadatas=[
            {"category": "blockchain", "priority": "high"},
            {"category": "privacy", "priority": "high"},
            {"category": "network", "priority": "low"}
        ],
        ids=["doc1", "doc2", "doc3"]
    )

    # Query with filter
    results = chroma_client.query(
        collection_name=collection_name,
        query_texts=["technology"],
        n_results=5,
        where={"priority": "high"}
    )

    # Should only return high priority documents
    assert len(results["ids"][0]) <= 2
    for metadata in results["metadatas"][0]:
        assert metadata["priority"] == "high"

    # Cleanup
    chroma_client.delete_collection(collection_name)


def test_multiple_queries_cached_collection(chroma_client):
    """Test that collection caching works properly."""
    collection_name = "test_cache"

    # Clean up
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass

    # Add documents
    chroma_client.add_documents(
        collection_name=collection_name,
        documents=["Test document"],
        metadatas=[{"test": True}],
        ids=["doc1"]
    )

    # Multiple queries should use cached collection
    for i in range(3):
        results = chroma_client.query(
            collection_name=collection_name,
            query_texts=["document"],
            n_results=1
        )
        assert len(results["ids"][0]) == 1

    # Cleanup
    chroma_client.delete_collection(collection_name)


@pytest.mark.parametrize("n_docs", [1, 5, 10])
def test_batch_operations(chroma_client, n_docs):
    """Test batch operations with different document counts."""
    collection_name = f"test_batch_{n_docs}"

    # Clean up
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass

    # Create batch data
    documents = [f"Document {i}" for i in range(n_docs)]
    metadatas = [{"index": i} for i in range(n_docs)]
    ids = [f"doc{i}" for i in range(n_docs)]

    # Add batch
    chroma_client.add_documents(
        collection_name=collection_name,
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    # Verify count
    count = chroma_client.count_documents(collection_name)
    assert count == n_docs

    # Cleanup
    chroma_client.delete_collection(collection_name)
