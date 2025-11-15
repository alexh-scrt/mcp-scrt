"""
Embedding Service with caching and batch support.

This module provides text embedding generation using ChromaDB's embedding functions
with Redis caching for improved performance.

Features:
- Text to vector embeddings using ChromaDB embedding functions
- Redis caching with TTL management
- Batch embedding generation
- Model lifecycle management
- Cache hit/miss metrics
"""

import hashlib
import logging
from typing import List, Optional, Dict, Any, Union
import numpy as np
from chromadb.utils import embedding_functions

from mcp_scrt.integrations.redis_client import RedisClient

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating and caching text embeddings.

    Features:
    - ChromaDB embedding function integration
    - Redis caching
    - Batch operations
    - Cache hit/miss tracking
    - Configurable TTL
    """

    def __init__(
        self,
        embedding_function: Optional[Any] = None,
        redis_client: Optional[RedisClient] = None,
        cache_ttl: int = 86400,  # 24 hours
        enable_cache: bool = True
    ):
        """
        Initialize Embedding Service.

        Args:
            embedding_function: ChromaDB embedding function (uses default if None)
            redis_client: Redis client instance (creates new if None)
            cache_ttl: Cache time-to-live in seconds (default: 24 hours)
            enable_cache: Enable/disable caching (default: True)

        Note:
            Default embedding function uses sentence-transformers
            'all-MiniLM-L6-v2' model (384-dimensional embeddings).
        """
        # Initialize embedding function
        if embedding_function is None:
            logger.info("Using ChromaDB DefaultEmbeddingFunction (all-MiniLM-L6-v2)")
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        else:
            self.embedding_function = embedding_function

        self.cache_ttl = cache_ttl
        self.enable_cache = enable_cache

        # Initialize Redis client
        self.redis_client = redis_client or RedisClient()

        # Metrics
        self._cache_hits = 0
        self._cache_misses = 0

        # Cache the embedding dimension to avoid affecting stats
        self._embedding_dim: Optional[int] = None

        logger.info(f"Initialized EmbeddingService with cache_enabled={enable_cache}")

    def _get_model_name(self) -> str:
        """Get model name for cache key generation."""
        # Try to extract model name from embedding function
        if hasattr(self.embedding_function, 'model_name'):
            return self.embedding_function.model_name
        elif hasattr(self.embedding_function, '_model_name'):
            return self.embedding_function._model_name
        else:
            # Default for ChromaDB's DefaultEmbeddingFunction
            return "all-MiniLM-L6-v2"

    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key for text.

        Args:
            text: Input text

        Returns:
            Cache key (hash of model + text)
        """
        # Include model name in hash to avoid conflicts when model changes
        model_name = self._get_model_name()
        content = f"{model_name}:{text}"
        hash_digest = hashlib.sha256(content.encode()).hexdigest()
        return f"embedding:{hash_digest}"

    def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """
        Retrieve embedding from cache.

        Args:
            text: Input text

        Returns:
            Cached embedding or None if not found
        """
        if not self.enable_cache:
            return None

        try:
            cache_key = self._get_cache_key(text)
            cached = self.redis_client.get(cache_key)

            if cached is not None:
                self._cache_hits += 1
                logger.debug(f"Cache hit for text: {text[:50]}...")
                return cached

            self._cache_misses += 1
            return None

        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            return None

    def _save_to_cache(self, text: str, embedding: List[float]):
        """
        Save embedding to cache.

        Args:
            text: Input text
            embedding: Generated embedding
        """
        if not self.enable_cache:
            return

        try:
            cache_key = self._get_cache_key(text)
            self.redis_client.set(cache_key, embedding, ex=self.cache_ttl)
            logger.debug(f"Cached embedding for text: {text[:50]}...")

        except Exception as e:
            logger.warning(f"Cache save failed: {e}")

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for single text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector as list of floats

        Example:
            >>> service = EmbeddingService()
            >>> embedding = service.embed("Hello world")
            >>> len(embedding)  # Default model produces 384-dim vectors
            384
        """
        # Check cache first
        cached = self._get_from_cache(text)
        if cached is not None:
            return cached

        # Generate embedding
        logger.debug(f"Generating embedding for: {text[:50]}...")

        # ChromaDB embedding functions expect lists
        embeddings = self.embedding_function([text])
        embedding = embeddings[0]

        # Convert numpy array to list if needed
        if hasattr(embedding, 'tolist'):
            embedding = embedding.tolist()
        elif isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()

        # Cache the result
        self._save_to_cache(text, embedding)

        return embedding

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing (default: 32)

        Returns:
            List of embedding vectors

        Note:
            This method checks cache for each text and only generates
            embeddings for cache misses, then processes them in batches.
        """
        if not texts:
            return []

        embeddings: List[Optional[List[float]]] = [None] * len(texts)
        texts_to_generate: List[tuple[int, str]] = []

        # Check cache for all texts
        for i, text in enumerate(texts):
            cached = self._get_from_cache(text)
            if cached is not None:
                embeddings[i] = cached
            else:
                texts_to_generate.append((i, text))

        # Generate embeddings for cache misses
        if texts_to_generate:
            logger.info(f"Generating {len(texts_to_generate)} embeddings")

            # Extract just the texts
            texts_only = [text for _, text in texts_to_generate]

            # Generate embeddings (ChromaDB functions handle batching internally)
            new_embeddings = self.embedding_function(texts_only)

            # Save to cache and store results
            for (original_idx, text), embedding in zip(texts_to_generate, new_embeddings):
                # Convert numpy array to list if needed
                if hasattr(embedding, 'tolist'):
                    embedding = embedding.tolist()
                elif isinstance(embedding, np.ndarray):
                    embedding = embedding.tolist()

                self._save_to_cache(text, embedding)
                embeddings[original_idx] = embedding

        # All embeddings should now be filled
        return embeddings  # type: ignore

    def get_embedding_dim(self) -> int:
        """
        Get embedding dimension for the current model.

        Returns:
            Embedding vector dimension
        """
        # Cache dimension to avoid affecting stats
        if self._embedding_dim is None:
            # Generate a test embedding to determine dimension (without affecting cache stats)
            saved_hits = self._cache_hits
            saved_misses = self._cache_misses

            test_embedding = self.embed("__dimension_test__")
            self._embedding_dim = len(test_embedding)

            # Restore stats
            self._cache_hits = saved_hits
            self._cache_misses = saved_misses

        return self._embedding_dim

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.

        Returns:
            Dict with cache hits, misses, and hit rate
        """
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0.0

        return {
            "cache_enabled": self.enable_cache,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_requests": total,
            "hit_rate": hit_rate,
            "model": self._get_model_name(),
            "dimension": self.get_embedding_dim() if total > 0 else None
        }

    def clear_cache(self, pattern: str = "embedding:*") -> int:
        """
        Clear embedding cache.

        Args:
            pattern: Redis key pattern to delete (default: all embeddings)

        Returns:
            Number of keys deleted
        """
        if not self.enable_cache:
            return 0

        deleted = self.redis_client.delete_pattern(pattern)
        logger.info(f"Cleared {deleted} cached embeddings")
        return deleted

    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Cosine similarity score (-1 to 1, typically 0 to 1 for embeddings)
        """
        emb1 = np.array(self.embed(text1))
        emb2 = np.array(self.embed(text2))

        # Cosine similarity
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def close(self):
        """Close resources and cleanup."""
        if self.redis_client:
            self.redis_client.close()

        # Log final stats
        stats = self.get_cache_stats()
        logger.info(f"EmbeddingService stats: {stats}")


# Export
__all__ = ["EmbeddingService"]
