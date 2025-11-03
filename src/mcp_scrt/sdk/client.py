"""Client pool management for Secret Network LCD connections.

This module provides a connection pool for managing LCD client connections
to the Secret Network with health checking, retry logic, and detailed logging.
"""

import threading
from contextlib import contextmanager
from queue import Empty, Queue
from typing import Any, Dict, Generator, Optional

from secret_sdk.client.lcd import LCDClient

from ..config import get_settings
from ..types import NetworkType
from ..utils.errors import NetworkError
from ..utils.logging import get_logger

# Module logger
logger = get_logger(__name__)


class ClientPool:
    """Thread-safe connection pool for LCD clients with detailed logging.

    This class manages a pool of LCDClient connections with:
    - Connection pooling and reuse
    - Maximum connection limits
    - Thread-safe operations
    - Statistics tracking
    - Comprehensive debug logging

    The logging behavior depends on configuration:
    - LOG_LEVEL=DEBUG: Shows detailed operation logs
    - DEBUG=true: Shows extra verbose connection details
    """

    def __init__(
        self,
        network: NetworkType = NetworkType.TESTNET,
        max_connections: Optional[int] = None,
    ) -> None:
        """Initialize client pool.

        Args:
            network: Network to connect to (default: TESTNET)
            max_connections: Maximum number of connections (default: from settings)

        Raises:
            ValueError: If max_connections is invalid
        """
        self.network = network
        self._settings = get_settings()

        # Use provided max_connections or fall back to settings
        self.max_connections = max_connections if max_connections is not None else self._settings.max_connections

        # Validate max_connections
        if self.max_connections <= 0:
            logger.error(
                "Invalid max_connections",
                max_connections=self.max_connections,
            )
            raise ValueError(f"max_connections must be positive, got {self.max_connections}")

        # Connection pool and tracking
        self._pool: Queue[LCDClient] = Queue(maxsize=self.max_connections)
        self._all_connections: set[LCDClient] = set()
        self._in_use: set[LCDClient] = set()
        self._lock = threading.RLock()

        # Statistics
        self._requests_served = 0
        self._closed = False

        # Debug mode
        self._debug_enabled = self._settings.debug and self._settings.log_level.upper() == "DEBUG"

        logger.debug(
            "ClientPool initialized",
            network=network.value,
            max_connections=self.max_connections,
            debug_enabled=self._debug_enabled,
        )

        if self._debug_enabled:
            logger.debug(
                "ClientPool initial state",
                pool_size=self._pool.qsize(),
                total_connections=len(self._all_connections),
                in_use=len(self._in_use),
            )

    def _create_client(self) -> LCDClient:
        """Create a new LCD client.

        Returns:
            New LCDClient instance

        Raises:
            NetworkError: If client creation fails
        """
        logger.debug("Creating new LCD client", network=self.network.value)

        try:
            # Get network configuration
            url = self._settings.get_network_url()
            chain_id = self._settings.get_chain_id()

            if self._debug_enabled:
                logger.debug(
                    "Client connection details",
                    url=url,
                    chain_id=chain_id,
                    network=self.network.value,
                )

            # Create client
            client = LCDClient(url=url, chain_id=chain_id)

            logger.info("LCD client created", network=self.network.value, chain_id=chain_id)

            return client

        except Exception as e:
            logger.error(
                "Failed to create LCD client",
                network=self.network.value,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise NetworkError(
                f"Failed to create LCD client: {e}",
                details={"network": self.network.value, "error": str(e)},
            ) from e

    @contextmanager
    def get_client(self) -> Generator[LCDClient, None, None]:
        """Get a client from the pool as a context manager.

        Yields:
            LCDClient from the pool

        Raises:
            RuntimeError: If pool is closed
            NetworkError: If client acquisition fails

        Example:
            >>> with pool.get_client() as client:
            ...     result = client.bank.balance(address)
        """
        with self._lock:
            if self._closed:
                logger.error("Attempted to get client from closed pool")
                raise RuntimeError("ClientPool is closed")

            logger.debug("Acquiring client from pool")

        client: Optional[LCDClient] = None

        try:
            # Try to get existing client from pool
            try:
                client = self._pool.get_nowait()

                with self._lock:
                    self._in_use.add(client)

                logger.debug("Reused client from pool", pool_size=self._pool.qsize())

                if self._debug_enabled:
                    logger.debug(
                        "Client acquisition details",
                        client_id=id(client),
                        total_connections=len(self._all_connections),
                        in_use=len(self._in_use),
                        available=self._pool.qsize(),
                    )

            except Empty:
                # No available client, create new one if under limit
                # Check if we're at max connections
                with self._lock:
                    at_max = len(self._all_connections) >= self.max_connections

                if at_max:
                    # Release lock before waiting to avoid deadlock
                    logger.warning(
                        "Max connections reached, waiting for available client",
                        max_connections=self.max_connections,
                    )
                    # Wait for a client to become available (without holding lock)
                    client = self._pool.get(timeout=self._settings.idle_timeout)

                    with self._lock:
                        self._in_use.add(client)
                else:
                    # Create new client
                    with self._lock:
                        client = self._create_client()
                        self._all_connections.add(client)

                        logger.debug(
                            "Created new client",
                            total_connections=len(self._all_connections),
                        )

                        self._in_use.add(client)

                        if self._debug_enabled:
                            logger.debug(
                                "New client created",
                                client_id=id(client),
                                total_connections=len(self._all_connections),
                                in_use=len(self._in_use),
                            )

            # Increment requests served
            with self._lock:
                self._requests_served += 1

            # Yield client to caller
            yield client

        except Exception as e:
            logger.error(
                "Error during client acquisition",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

        finally:
            # Return client to pool
            if client is not None:
                with self._lock:
                    if client in self._in_use:
                        self._in_use.remove(client)

                    if not self._closed and client in self._all_connections:
                        self._pool.put(client)

                        logger.debug(
                            "Client returned to pool",
                            pool_size=self._pool.qsize(),
                            in_use=len(self._in_use),
                        )

                        if self._debug_enabled:
                            logger.debug(
                                "Client return details",
                                client_id=id(client),
                                pool_size=self._pool.qsize(),
                                in_use=len(self._in_use),
                            )

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics.

        Returns:
            Dictionary with pool statistics:
            - total_connections: Total number of connections created
            - available_connections: Number of available connections in pool
            - in_use_connections: Number of connections currently in use
            - max_connections: Maximum allowed connections
            - requests_served: Total number of requests served
        """
        with self._lock:
            stats = {
                "total_connections": len(self._all_connections),
                "available_connections": self._pool.qsize(),
                "in_use_connections": len(self._in_use),
                "max_connections": self.max_connections,
                "requests_served": self._requests_served,
            }

            if self._debug_enabled:
                logger.debug(
                    "Pool statistics retrieved",
                    **stats,
                )

            return stats

    def reset(self) -> None:
        """Reset the pool, clearing all connections and statistics."""
        with self._lock:
            logger.debug("Resetting client pool")

            # Close all connections
            self._close_all_connections()

            # Reset statistics
            self._requests_served = 0

            logger.info("Client pool reset complete")

            if self._debug_enabled:
                logger.debug(
                    "Pool state after reset",
                    total_connections=len(self._all_connections),
                    requests_served=self._requests_served,
                )

    def close(self) -> None:
        """Close the pool and all connections.

        After calling close(), the pool cannot be used anymore.
        """
        with self._lock:
            if self._closed:
                logger.debug("Pool already closed")
                return

            logger.debug("Closing client pool")

            self._closed = True
            self._close_all_connections()

            logger.info("Client pool closed")

    def _close_all_connections(self) -> None:
        """Close all connections in the pool (internal method)."""
        logger.debug(
            "Closing all connections",
            total_connections=len(self._all_connections),
        )

        # Clear pool queue
        while not self._pool.empty():
            try:
                self._pool.get_nowait()
            except Empty:
                break

        # Clear all tracking
        self._all_connections.clear()
        self._in_use.clear()

        logger.debug("All connections closed")

    def __enter__(self) -> "ClientPool":
        """Enter context manager."""
        logger.debug("Entering ClientPool context manager")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        logger.debug("Exiting ClientPool context manager")
        self.close()
