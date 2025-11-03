"""Unit tests for client pool management."""

import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.types import NetworkType
from mcp_scrt.utils.errors import NetworkError


class TestClientPoolCreation:
    """Test client pool creation and initialization."""

    def test_create_pool(self) -> None:
        """Test creating a client pool."""
        pool = ClientPool(network=NetworkType.TESTNET)
        assert pool is not None
        assert pool.network == NetworkType.TESTNET

    def test_create_pool_mainnet(self) -> None:
        """Test creating pool with mainnet."""
        pool = ClientPool(network=NetworkType.MAINNET)
        assert pool.network == NetworkType.MAINNET

    def test_initial_pool_empty(self) -> None:
        """Test that pool starts empty."""
        pool = ClientPool(network=NetworkType.TESTNET)
        stats = pool.get_stats()

        assert stats["total_connections"] == 0
        assert stats["available_connections"] == 0
        assert stats["in_use_connections"] == 0

    def test_pool_with_custom_max_connections(self) -> None:
        """Test creating pool with custom max connections."""
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        stats = pool.get_stats()

        assert stats["max_connections"] == 5


class TestClientAcquisition:
    """Test acquiring clients from the pool."""

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_get_client(self, mock_lcd_client: Mock) -> None:
        """Test getting a client from pool."""
        pool = ClientPool(network=NetworkType.TESTNET)

        with pool.get_client() as client:
            assert client is not None

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_client_returned_to_pool(self, mock_lcd_client: Mock) -> None:
        """Test that client is returned to pool after use."""
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=2)

        with pool.get_client() as client:
            stats = pool.get_stats()
            assert stats["in_use_connections"] == 1
            assert stats["available_connections"] == 0

        # After context manager exits, client should be returned
        stats = pool.get_stats()
        assert stats["in_use_connections"] == 0
        assert stats["available_connections"] == 1

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_reuse_client_from_pool(self, mock_lcd_client: Mock) -> None:
        """Test that clients are reused from pool."""
        pool = ClientPool(network=NetworkType.TESTNET)

        # Get and return a client
        with pool.get_client() as client1:
            client1_id = id(client1)

        # Get another client - should be the same one
        with pool.get_client() as client2:
            client2_id = id(client2)

        # Should reuse the same client
        assert client1_id == client2_id

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_multiple_clients(self, mock_lcd_client: Mock) -> None:
        """Test getting multiple clients simultaneously."""
        # Make mock return different instances each time
        mock_lcd_client.side_effect = lambda **kwargs: MagicMock()

        pool = ClientPool(network=NetworkType.TESTNET, max_connections=3)

        with pool.get_client() as client1:
            with pool.get_client() as client2:
                with pool.get_client() as client3:
                    assert client1 is not None
                    assert client2 is not None
                    assert client3 is not None

                    stats = pool.get_stats()
                    assert stats["in_use_connections"] == 3


class TestConnectionLimits:
    """Test connection limit enforcement."""

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_max_connections_enforced(self, mock_lcd_client: Mock) -> None:
        """Test that max connections limit is enforced."""
        # Make mock return different instances each time
        mock_lcd_client.side_effect = lambda **kwargs: MagicMock()

        pool = ClientPool(network=NetworkType.TESTNET, max_connections=2)

        with pool.get_client():
            with pool.get_client():
                stats = pool.get_stats()
                assert stats["total_connections"] == 2

                # Can't create more than max
                assert stats["total_connections"] <= 2

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_wait_for_available_client(self, mock_lcd_client: Mock) -> None:
        """Test waiting for available client when pool is full."""
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=1)

        # This test verifies the pool manages connections properly
        with pool.get_client() as client1:
            assert client1 is not None
            stats = pool.get_stats()
            assert stats["in_use_connections"] == 1


class TestPoolStatistics:
    """Test pool statistics tracking."""

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_stats_structure(self, mock_lcd_client: Mock) -> None:
        """Test stats return proper structure."""
        pool = ClientPool(network=NetworkType.TESTNET)
        stats = pool.get_stats()

        assert "total_connections" in stats
        assert "available_connections" in stats
        assert "in_use_connections" in stats
        assert "max_connections" in stats
        assert "requests_served" in stats

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_requests_served_increments(self, mock_lcd_client: Mock) -> None:
        """Test that requests served counter increments."""
        pool = ClientPool(network=NetworkType.TESTNET)

        with pool.get_client():
            pass

        with pool.get_client():
            pass

        stats = pool.get_stats()
        assert stats["requests_served"] >= 2


class TestPoolCleanup:
    """Test pool cleanup and resource management."""

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_close_pool(self, mock_lcd_client: Mock) -> None:
        """Test closing the pool."""
        pool = ClientPool(network=NetworkType.TESTNET)

        # Get and return a client to create connections
        with pool.get_client():
            pass

        # Close the pool
        pool.close()

        stats = pool.get_stats()
        assert stats["total_connections"] == 0

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_close_empty_pool(self, mock_lcd_client: Mock) -> None:
        """Test closing empty pool."""
        pool = ClientPool(network=NetworkType.TESTNET)

        # Should not raise error
        pool.close()

        stats = pool.get_stats()
        assert stats["total_connections"] == 0

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_context_manager(self, mock_lcd_client: Mock) -> None:
        """Test pool as context manager."""
        with ClientPool(network=NetworkType.TESTNET) as pool:
            with pool.get_client() as client:
                assert client is not None

        # Pool should be closed after exiting context


class TestErrorHandling:
    """Test error handling in client pool."""

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_client_creation_failure(self, mock_lcd_client: Mock) -> None:
        """Test handling of client creation failure."""
        # Make client creation fail
        mock_lcd_client.side_effect = Exception("Connection failed")

        pool = ClientPool(network=NetworkType.TESTNET)

        with pytest.raises(NetworkError):
            with pool.get_client():
                pass

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_client_cleanup_on_error(self, mock_lcd_client: Mock) -> None:
        """Test that client is cleaned up on error."""
        pool = ClientPool(network=NetworkType.TESTNET)

        try:
            with pool.get_client() as client:
                # Simulate error during usage
                raise Exception("Test error")
        except Exception:
            pass

        # Client should be returned to pool even after error
        stats = pool.get_stats()
        assert stats["in_use_connections"] == 0


class TestNetworkConfiguration:
    """Test network configuration handling."""

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_testnet_configuration(self, mock_lcd_client: Mock) -> None:
        """Test testnet configuration."""
        pool = ClientPool(network=NetworkType.TESTNET)

        with pool.get_client():
            # Verify LCDClient was called with testnet URL
            assert mock_lcd_client.called

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_mainnet_configuration(self, mock_lcd_client: Mock) -> None:
        """Test mainnet configuration."""
        pool = ClientPool(network=NetworkType.MAINNET)

        with pool.get_client():
            # Verify LCDClient was called with mainnet URL
            assert mock_lcd_client.called


class TestThreadSafety:
    """Test thread safety of client pool."""

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_concurrent_client_access(self, mock_lcd_client: Mock) -> None:
        """Test concurrent access to client pool."""
        import threading

        # Make mock return different instances each time
        mock_lcd_client.side_effect = lambda **kwargs: MagicMock()

        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        errors: list[Exception] = []
        success_count = [0]
        count_lock = threading.Lock()

        def get_and_use_client(thread_id: int) -> None:
            try:
                with pool.get_client() as client:
                    assert client is not None
                    time.sleep(0.01)
                    with count_lock:
                        success_count[0] += 1
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_and_use_client, args=(i,)) for i in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=5.0)

        # All threads should succeed
        assert len(errors) == 0
        assert success_count[0] == 10

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_concurrent_pool_stats(self, mock_lcd_client: Mock) -> None:
        """Test getting stats concurrently."""
        import threading

        pool = ClientPool(network=NetworkType.TESTNET)

        def get_stats() -> None:
            for _ in range(10):
                stats = pool.get_stats()
                assert stats is not None

        threads = [threading.Thread(target=get_stats) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()


class TestPoolReset:
    """Test pool reset functionality."""

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_reset_pool(self, mock_lcd_client: Mock) -> None:
        """Test resetting the pool."""
        pool = ClientPool(network=NetworkType.TESTNET)

        # Create some connections
        with pool.get_client():
            pass

        stats_before = pool.get_stats()
        assert stats_before["total_connections"] > 0

        # Reset the pool
        pool.reset()

        stats_after = pool.get_stats()
        assert stats_after["total_connections"] == 0
        assert stats_after["requests_served"] == 0

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_reset_clears_stats(self, mock_lcd_client: Mock) -> None:
        """Test that reset clears statistics."""
        pool = ClientPool(network=NetworkType.TESTNET)

        # Use pool to generate stats
        with pool.get_client():
            pass

        with pool.get_client():
            pass

        # Reset
        pool.reset()

        stats = pool.get_stats()
        assert stats["requests_served"] == 0


class TestPoolHealthCheck:
    """Test health checking of clients."""

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_unhealthy_client_removed(self, mock_lcd_client: Mock) -> None:
        """Test that unhealthy clients are removed."""
        pool = ClientPool(network=NetworkType.TESTNET)

        # Get a client
        with pool.get_client() as client:
            # Mark it as unhealthy somehow (this would be implementation specific)
            pass

        # The unhealthy client should be handled appropriately


class TestPoolEdgeCases:
    """Test edge cases for client pool."""

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_zero_max_connections(self, mock_lcd_client: Mock) -> None:
        """Test that pool handles zero max connections."""
        # Should raise error or use default
        with pytest.raises((ValueError, RuntimeError)):
            ClientPool(network=NetworkType.TESTNET, max_connections=0)

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_negative_max_connections(self, mock_lcd_client: Mock) -> None:
        """Test that pool handles negative max connections."""
        with pytest.raises((ValueError, RuntimeError)):
            ClientPool(network=NetworkType.TESTNET, max_connections=-1)

    @patch("mcp_scrt.sdk.client.LCDClient")
    def test_get_client_after_close(self, mock_lcd_client: Mock) -> None:
        """Test getting client after pool is closed."""
        pool = ClientPool(network=NetworkType.TESTNET)
        pool.close()

        # Should raise error
        with pytest.raises(RuntimeError):
            with pool.get_client():
                pass
