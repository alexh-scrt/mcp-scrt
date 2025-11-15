"""Integration tests for Embedding Service.

This test suite validates the EmbeddingService functionality including:
- Embedding generation
- Redis caching
- Batch operations
- Cache statistics
- Similarity calculation
"""

import pytest
from mcp_scrt.services.embedding_service import EmbeddingService
from mcp_scrt.integrations.redis_client import RedisClient


@pytest.fixture
def redis_client():
    """Create Redis client for testing."""
    client = RedisClient()
    client.connect()
    yield client
    # Cleanup test keys
    try:
        client.delete_pattern("embedding:*")
    finally:
        client.close()


@pytest.fixture
def embedding_service(redis_client):
    """Create EmbeddingService for testing."""
    service = EmbeddingService(redis_client=redis_client, enable_cache=True)
    yield service
    # Cleanup
    service.clear_cache()
    service.close()


@pytest.fixture
def embedding_service_no_cache():
    """Create EmbeddingService without caching for testing."""
    service = EmbeddingService(enable_cache=False)
    yield service
    service.close()


def test_embed_single_text(embedding_service):
    """Test embedding a single text."""
    text = "Hello, world!"

    embedding = embedding_service.embed(text)

    # Check embedding is a list of floats
    assert isinstance(embedding, list)
    assert all(isinstance(x, float) for x in embedding)

    # Default model should produce 384-dimensional embeddings
    assert len(embedding) == 384


def test_embed_caching(embedding_service):
    """Test that embeddings are cached correctly."""
    text = "Test caching"

    # First call - should miss cache
    embedding1 = embedding_service.embed(text)
    stats1 = embedding_service.get_cache_stats()
    assert stats1["cache_misses"] == 1
    assert stats1["cache_hits"] == 0

    # Second call - should hit cache
    embedding2 = embedding_service.embed(text)
    stats2 = embedding_service.get_cache_stats()
    assert stats2["cache_misses"] == 1  # Still 1
    assert stats2["cache_hits"] == 1  # Now 1

    # Embeddings should be identical
    assert embedding1 == embedding2


def test_embed_no_cache(embedding_service_no_cache):
    """Test embedding without cache."""
    text = "Test no cache"

    # Generate embedding
    embedding = embedding_service_no_cache.embed(text)

    # Check it works
    assert isinstance(embedding, list)
    assert len(embedding) == 384

    # Stats should show cache disabled
    stats = embedding_service_no_cache.get_cache_stats()
    assert stats["cache_enabled"] is False
    assert stats["cache_hits"] == 0
    assert stats["cache_misses"] == 0


def test_embed_batch(embedding_service):
    """Test batch embedding generation."""
    texts = [
        "First text",
        "Second text",
        "Third text"
    ]

    # Generate batch embeddings
    embeddings = embedding_service.embed_batch(texts)

    # Check results
    assert len(embeddings) == 3
    assert all(isinstance(emb, list) for emb in embeddings)
    assert all(len(emb) == 384 for emb in embeddings)

    # All three should be different
    assert embeddings[0] != embeddings[1]
    assert embeddings[1] != embeddings[2]


def test_embed_batch_with_cache(embedding_service):
    """Test batch embedding with partial cache hits."""
    texts = [
        "Cached text 1",
        "Cached text 2",
        "New text"
    ]

    # Pre-cache first two texts
    embedding_service.embed(texts[0])
    embedding_service.embed(texts[1])

    # Reset stats
    embedding_service._cache_hits = 0
    embedding_service._cache_misses = 0

    # Now generate batch (should hit cache for first two, miss for third)
    embeddings = embedding_service.embed_batch(texts)

    # Check all embeddings generated
    assert len(embeddings) == 3

    # Check cache stats
    stats = embedding_service.get_cache_stats()
    assert stats["cache_hits"] == 2
    assert stats["cache_misses"] == 1


def test_embed_batch_empty(embedding_service):
    """Test batch embedding with empty list."""
    embeddings = embedding_service.embed_batch([])
    assert embeddings == []


def test_get_embedding_dim(embedding_service):
    """Test getting embedding dimension."""
    dim = embedding_service.get_embedding_dim()
    assert dim == 384  # Default model dimension


def test_cache_stats(embedding_service):
    """Test cache statistics."""
    # Generate some embeddings
    embedding_service.embed("text1")
    embedding_service.embed("text2")
    embedding_service.embed("text1")  # Cache hit

    stats = embedding_service.get_cache_stats()

    assert stats["cache_enabled"] is True
    assert stats["cache_hits"] == 1
    assert stats["cache_misses"] == 2
    assert stats["total_requests"] == 3
    assert stats["hit_rate"] == pytest.approx(1/3)
    assert stats["model"] == "all-MiniLM-L6-v2"
    assert stats["dimension"] == 384


def test_clear_cache(embedding_service):
    """Test clearing the cache."""
    # Generate and cache some embeddings
    embedding_service.embed("text1")
    embedding_service.embed("text2")
    embedding_service.embed("text3")

    # Clear cache
    deleted = embedding_service.clear_cache()

    # Should have deleted 3 keys
    assert deleted == 3

    # Reset stats
    embedding_service._cache_hits = 0
    embedding_service._cache_misses = 0

    # Re-embedding should miss cache
    embedding_service.embed("text1")
    stats = embedding_service.get_cache_stats()
    assert stats["cache_hits"] == 0
    assert stats["cache_misses"] == 1


def test_similarity(embedding_service):
    """Test cosine similarity calculation."""
    # Similar texts
    text1 = "The cat sat on the mat"
    text2 = "A cat was sitting on a mat"

    # Different text
    text3 = "Python programming language"

    # Calculate similarities
    sim_similar = embedding_service.similarity(text1, text2)
    sim_different = embedding_service.similarity(text1, text3)

    # Similar texts should have higher similarity
    assert 0 <= sim_similar <= 1
    assert 0 <= sim_different <= 1
    assert sim_similar > sim_different

    # Identical text should have similarity of 1
    sim_identical = embedding_service.similarity(text1, text1)
    assert sim_identical == pytest.approx(1.0, abs=1e-6)


def test_embedding_consistency(embedding_service):
    """Test that same text always produces same embedding."""
    text = "Consistency test"

    # Generate embedding multiple times
    embedding1 = embedding_service.embed(text)
    embedding2 = embedding_service.embed(text)
    embedding3 = embedding_service.embed(text)

    # All should be identical (due to caching)
    assert embedding1 == embedding2
    assert embedding2 == embedding3


def test_different_texts_different_embeddings(embedding_service):
    """Test that different texts produce different embeddings."""
    text1 = "First unique text"
    text2 = "Second unique text"

    embedding1 = embedding_service.embed(text1)
    embedding2 = embedding_service.embed(text2)

    # Embeddings should be different
    assert embedding1 != embedding2


def test_cache_key_generation(embedding_service):
    """Test that cache keys are generated consistently."""
    text = "Cache key test"

    # Generate cache key directly
    key1 = embedding_service._get_cache_key(text)
    key2 = embedding_service._get_cache_key(text)

    # Same text should generate same key
    assert key1 == key2

    # Different text should generate different key
    key3 = embedding_service._get_cache_key("Different text")
    assert key1 != key3


def test_large_batch(embedding_service):
    """Test embedding a large batch of texts."""
    # Create 100 unique texts
    texts = [f"Text number {i}" for i in range(100)]

    # Generate embeddings
    embeddings = embedding_service.embed_batch(texts)

    # Check all generated
    assert len(embeddings) == 100
    assert all(len(emb) == 384 for emb in embeddings)

    # Check they're all different (with high probability)
    unique_embeddings = set(tuple(emb) for emb in embeddings)
    assert len(unique_embeddings) == 100  # All unique
