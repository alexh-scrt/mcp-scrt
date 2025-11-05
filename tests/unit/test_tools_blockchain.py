"""Tests for blockchain tools.

This module tests the blockchain tools for querying blockchain state.
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, patch, AsyncMock

from mcp_scrt.tools.blockchain import (
    GetBlockTool,
    GetLatestBlockTool,
    GetBlockByHashTool,
    GetNodeInfoTool,
    GetSyncingStatusTool,
)
from mcp_scrt.tools.base import ToolCategory, ToolExecutionContext
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.types import NetworkType
from mcp_scrt.utils.errors import ValidationError


class TestGetBlockTool:
    """Test get_block tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetBlockTool(context)

        assert tool.name == "get_block"
        assert "block" in tool.description.lower()
        assert tool.category == ToolCategory.BLOCKCHAIN
        assert tool.requires_wallet is False

    def test_validate_params_missing_height(self) -> None:
        """Test validation fails without height."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetBlockTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "height" in str(exc_info.value.message).lower()

    def test_validate_params_invalid_height(self) -> None:
        """Test validation fails with invalid height."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetBlockTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"height": -1})

        assert "height" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_block(self) -> None:
        """Test getting block by height."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetBlockTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tendermint = Mock()
            mock_client.tendermint.block = AsyncMock(
                return_value={
                    "block": {
                        "header": {
                            "height": "12345",
                            "time": "2023-01-01T00:00:00Z",
                            "chain_id": "pulsar-2"
                        },
                        "data": {"txs": []},
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"height": 12345})

            assert result["success"] is True
            assert "block" in result["data"]
            assert result["data"]["height"] == 12345


class TestGetLatestBlockTool:
    """Test get_latest_block tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetLatestBlockTool(context)

        assert tool.name == "get_latest_block"
        assert "latest" in tool.description.lower() or "current" in tool.description.lower()
        assert tool.category == ToolCategory.BLOCKCHAIN
        assert tool.requires_wallet is False

    @pytest.mark.asyncio
    async def test_execute_get_latest_block(self) -> None:
        """Test getting latest block."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetLatestBlockTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tendermint = Mock()
            mock_client.tendermint.block_info = AsyncMock(
                return_value={
                    "block": {
                        "header": {
                            "height": "99999",
                            "time": "2023-01-01T00:00:00Z",
                            "chain_id": "pulsar-2"
                        },
                        "data": {"txs": []},
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({})

            assert result["success"] is True
            assert "block" in result["data"]


class TestGetBlockByHashTool:
    """Test get_block_by_hash tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetBlockByHashTool(context)

        assert tool.name == "get_block_by_hash"
        assert "hash" in tool.description.lower()
        assert tool.category == ToolCategory.BLOCKCHAIN
        assert tool.requires_wallet is False

    def test_validate_params_missing_hash(self) -> None:
        """Test validation fails without hash."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetBlockByHashTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "hash" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_block_by_hash(self) -> None:
        """Test getting block by hash."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetBlockByHashTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tendermint = Mock()
            mock_client.tendermint.block_by_hash = AsyncMock(
                return_value={
                    "block": {
                        "header": {
                            "height": "12345",
                            "time": "2023-01-01T00:00:00Z",
                            "chain_id": "pulsar-2"
                        },
                        "data": {"txs": []},
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"hash": "ABCDEF1234567890"})

            assert result["success"] is True
            assert "block" in result["data"]


class TestGetNodeInfoTool:
    """Test get_node_info tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetNodeInfoTool(context)

        assert tool.name == "get_node_info"
        assert "node" in tool.description.lower()
        assert tool.category == ToolCategory.BLOCKCHAIN
        assert tool.requires_wallet is False

    @pytest.mark.asyncio
    async def test_execute_get_node_info(self) -> None:
        """Test getting node info."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetNodeInfoTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tendermint = Mock()
            mock_client.tendermint.node_info = AsyncMock(
                return_value={
                    "node_info": {
                        "protocol_version": {"p2p": "8", "block": "11", "app": "0"},
                        "id": "node123",
                        "network": "pulsar-2",
                        "version": "0.34.24",
                        "moniker": "testnode",
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({})

            assert result["success"] is True
            assert "node_info" in result["data"]
            assert result["data"]["node_info"]["network"] == "pulsar-2"


class TestGetSyncingStatusTool:
    """Test get_syncing_status tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetSyncingStatusTool(context)

        assert tool.name == "get_syncing_status"
        assert "sync" in tool.description.lower()
        assert tool.category == ToolCategory.BLOCKCHAIN
        assert tool.requires_wallet is False

    @pytest.mark.asyncio
    async def test_execute_get_syncing_status(self) -> None:
        """Test getting syncing status."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetSyncingStatusTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tendermint = Mock()
            mock_client.tendermint.syncing = AsyncMock(
                return_value={
                    "syncing": False
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({})

            assert result["success"] is True
            assert "syncing" in result["data"]
            assert result["data"]["syncing"] is False


class TestBlockchainToolsIntegration:
    """Test blockchain tools working together."""

    @pytest.mark.asyncio
    async def test_all_blockchain_tools_have_correct_metadata(self) -> None:
        """Test all blockchain tools can be instantiated and have correct metadata."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tools = [
            GetBlockTool(context),
            GetLatestBlockTool(context),
            GetBlockByHashTool(context),
            GetNodeInfoTool(context),
            GetSyncingStatusTool(context),
        ]

        # All tools should be BLOCKCHAIN category
        for tool in tools:
            assert tool.category == ToolCategory.BLOCKCHAIN
            assert tool.name is not None
            assert tool.description is not None
            assert tool.requires_wallet is False

        # All tool names should be unique
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))
