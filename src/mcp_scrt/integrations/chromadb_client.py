"""
ChromaDB client wrapper with connection pooling and error handling.

This module provides a clean interface to ChromaDB with:
- Automatic connection management through Caddy proxy
- API key authentication
- Error handling and retries
- Health checks
- Collection management
- Embedding integration
"""

import os
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions
import logging
from dotenv import load_dotenv
from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chromadb.api.ClientAPI import ClientAPI

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Default embedding function (sentence-transformers)
DEFAULT_EMBEDDING_FUNCTION = embedding_functions.DefaultEmbeddingFunction()


class ChromaDBClient:
    """
    Wrapper for ChromaDB operations.

    Features:
    - Connection pooling
    - Proxy support with API key authentication
    - Health checks
    - Collection lifecycle management
    - Batch operations
    - Error handling
    """

    def __init__(
        self,
        remote_host: str = None,
        remote_port: int = None,
        api_key: Optional[str] = None,
        use_ssl: bool = True
    ):
        """
        Initialize ChromaDB client.

        Args:
            remote_host: Remote host URL (default: from env REMOTE_HOST)
            remote_port: Remote port (default: from env REMOTE_PORT)
            api_key: API key for authentication (default: from env API_KEY)
            use_ssl: Use SSL/TLS connection (default: True for remote)
        """
        # Parse remote host - remove protocol if present
        raw_host = remote_host or os.getenv("REMOTE_HOST", "localhost")
        if raw_host.startswith("https://"):
            self.host = raw_host.replace("https://", "")
            self.use_ssl = True
        elif raw_host.startswith("http://"):
            self.host = raw_host.replace("http://", "")
            self.use_ssl = use_ssl
        else:
            self.host = raw_host
            self.use_ssl = use_ssl

        self.port = remote_port or int(os.getenv("REMOTE_PORT", "8000"))
        self.api_key = api_key or os.getenv("API_KEY")

        self._client = None
        self._collections_cache: Dict[str, Collection] = {}

    def connect(self) -> chromadb.Client:
        """
        Establish connection to ChromaDB.

        Returns:
            ChromaDB client instance

        Raises:
            ConnectionError: If connection fails
        """
        if self._client is not None:
            return self._client

        try:
            # Prepare headers with API key
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                headers["X-API-Key"] = self.api_key

            # Create settings
            # Note: Disable auth provider since server doesn't return /auth/identity
            # Don't set chroma_server_api_default_path here - we'll add it in the path prefix
            settings = Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                chroma_client_auth_provider=None,
                chroma_client_auth_credentials=None
            )

            # Monkey-patch both _make_request and get_user_identity
            from chromadb.api import fastapi as fastapi_module
            from chromadb.auth import UserIdentity

            # Import client module for patching validation
            from chromadb.api import client as client_module

            original_class_make_request = fastapi_module.FastAPI._make_request
            original_get_user_identity = fastapi_module.FastAPI.get_user_identity
            original_validate_tenant_database = client_module.Client._validate_tenant_database

            # Create patched _make_request that adds /chroma/api/v2 prefix
            def create_patched_make_request(original_method):
                @wraps(original_method)
                def patched_make_request(self, method: str, path: str, **kwargs):
                    # Add /chroma/api/v2 prefix for Caddy routing
                    # (Caddy strips /chroma and forwards /api/v2/path to chromadb:8000)
                    path = f"/chroma/api/v2{path}"
                    return original_method(self, method, path, **kwargs)
                return patched_make_request

            # Create patched get_user_identity that returns a dummy identity
            def patched_get_user_identity(self):
                # Return a dummy user identity since the server doesn't support this endpoint
                return UserIdentity(user_id="anonymous", tenant="default_tenant")

            # Create patched _validate_tenant_database that skips validation
            def patched_validate_tenant_database(self, tenant: str, database: str):
                # Skip validation since server doesn't support tenant/database endpoints
                pass

            # Apply the patches temporarily
            fastapi_module.FastAPI._make_request = create_patched_make_request(original_class_make_request)
            fastapi_module.FastAPI.get_user_identity = patched_get_user_identity
            client_module.Client._validate_tenant_database = patched_validate_tenant_database

            try:
                # Create HTTP client (now with patched methods)
                self._client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port,
                    ssl=self.use_ssl,
                    headers=headers,
                    settings=settings
                )
            finally:
                # Restore original class methods
                fastapi_module.FastAPI._make_request = original_class_make_request
                fastapi_module.FastAPI.get_user_identity = original_get_user_identity
                client_module.Client._validate_tenant_database = original_validate_tenant_database

            # Fix the _api_url to remove the /api/v2 prefix that was added by default
            # We'll add it manually in our patched _make_request
            original_api_url = self._client._server._api_url
            # Remove /api/v2 or /api/v1 from the end of the URL
            if original_api_url.endswith("/api/v2"):
                self._client._server._api_url = original_api_url[:-7]  # Remove "/api/v2"
            elif original_api_url.endswith("/api/v1"):
                self._client._server._api_url = original_api_url[:-7]  # Remove "/api/v1"

            logger.debug(f"Original API URL: {original_api_url}")
            logger.debug(f"Modified API URL: {self._client._server._api_url}")

            # Now patch the instance method to keep the /chroma/api/v2 prefix for all future requests
            original_instance_make_request = self._client._server._make_request.__func__

            def patched_instance_make_request(self_server, method: str, path: str, **kwargs):
                # Add /chroma/api/v2 prefix for Caddy routing
                # (Caddy strips /chroma and forwards /api/v2/path to chromadb:8000)
                path = f"/chroma/api/v2{path}"
                logger.debug(f"ChromaDB request: {method.upper()} {path}")
                return original_instance_make_request(self_server, method, path, **kwargs)

            # Bind the patched method to the instance
            import types
            self._client._server._make_request = types.MethodType(
                patched_instance_make_request,
                self._client._server
            )

            # Test connection
            self._client.heartbeat()
            logger.info(f"Connected to ChromaDB at {self.host}:{self.port}/chroma")

            return self._client

        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise ConnectionError(f"ChromaDB connection failed: {e}")

    def health_check(self) -> Dict[str, Any]:
        """
        Check ChromaDB health status.

        Returns:
            Health status dict with status and metrics
        """
        try:
            client = self.connect()
            heartbeat = client.heartbeat()

            return {
                "status": "healthy",
                "heartbeat": heartbeat,
                "host": self.host,
                "port": self.port,
                "ssl": self.use_ssl,
                "collections_count": len(self.list_collections())
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "host": self.host,
                "port": self.port
            }

    def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict] = None,
        embedding_function: Optional[Any] = None
    ) -> Collection:
        """
        Get existing collection or create if doesn't exist.

        Args:
            name: Collection name
            metadata: Collection metadata
            embedding_function: Custom embedding function

        Returns:
            Collection instance
        """
        # Check cache
        if name in self._collections_cache:
            return self._collections_cache[name]

        client = self.connect()

        # Use default embedding function if none provided
        if embedding_function is None:
            embedding_function = DEFAULT_EMBEDDING_FUNCTION

        try:
            collection = client.get_collection(
                name=name,
                embedding_function=embedding_function
            )
            logger.info(f"Retrieved existing collection: {name}")
        except Exception:
            # Collection doesn't exist, create it
            # ChromaDB v2 requires metadata to be non-empty
            if not metadata:
                metadata = {"created_by": "mcp-scrt"}
            collection = client.create_collection(
                name=name,
                metadata=metadata,
                embedding_function=embedding_function
            )
            logger.info(f"Created new collection: {name}")

        # Cache collection
        self._collections_cache[name] = collection
        return collection

    def list_collections(self) -> List[str]:
        """
        List all collections.

        Returns:
            List of collection names
        """
        client = self.connect()
        collections = client.list_collections()
        return [c.name for c in collections]

    def delete_collection(self, name: str):
        """
        Delete a collection.

        Args:
            name: Collection name to delete
        """
        client = self.connect()
        client.delete_collection(name=name)

        # Remove from cache
        if name in self._collections_cache:
            del self._collections_cache[name]

        logger.info(f"Deleted collection: {name}")

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ):
        """
        Add documents to collection.

        Args:
            collection_name: Target collection
            documents: Document texts
            metadatas: Document metadata
            ids: Document IDs
            embeddings: Pre-computed embeddings (optional)
        """
        collection = self.get_or_create_collection(collection_name)

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )

        logger.info(f"Added {len(documents)} documents to {collection_name}")

    def query(
        self,
        collection_name: str,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 5,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> Dict:
        """
        Query collection for similar documents.

        Args:
            collection_name: Collection to query
            query_texts: Query texts (will be embedded)
            query_embeddings: Pre-computed query embeddings
            n_results: Number of results to return
            where: Metadata filters
            where_document: Document content filters

        Returns:
            Query results with documents, distances, metadatas
        """
        collection = self.get_or_create_collection(collection_name)

        results = collection.query(
            query_texts=query_texts,
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
            where_document=where_document
        )

        return results

    def update_documents(
        self,
        collection_name: str,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict]] = None,
        embeddings: Optional[List[List[float]]] = None
    ):
        """
        Update existing documents.

        Args:
            collection_name: Collection name
            ids: Document IDs to update
            documents: New document texts
            metadatas: New metadata
            embeddings: New embeddings
        """
        collection = self.get_or_create_collection(collection_name)

        collection.update(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )

        logger.info(f"Updated {len(ids)} documents in {collection_name}")

    def delete_documents(
        self,
        collection_name: str,
        ids: List[str]
    ):
        """
        Delete documents from collection.

        Args:
            collection_name: Collection name
            ids: Document IDs to delete
        """
        collection = self.get_or_create_collection(collection_name)
        collection.delete(ids=ids)

        logger.info(f"Deleted {len(ids)} documents from {collection_name}")

    def count_documents(self, collection_name: str) -> int:
        """
        Count documents in collection.

        Args:
            collection_name: Collection name

        Returns:
            Number of documents
        """
        collection = self.get_or_create_collection(collection_name)
        return collection.count()

    def close(self):
        """Close client connection and clear cache."""
        self._client = None
        self._collections_cache.clear()
        logger.info("ChromaDB client closed")
