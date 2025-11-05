"""Tests for transaction tools.

This module tests the transaction tools for querying and simulating transactions.
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, patch, AsyncMock

from mcp_scrt.tools.transaction import (
    GetTransactionTool,
    SearchTransactionsTool,
    EstimateGasTool,
    SimulateTransactionTool,
    GetTransactionStatusTool,
)
from mcp_scrt.tools.base import ToolCategory, ToolExecutionContext
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.types import NetworkType
from mcp_scrt.utils.errors import ValidationError


class TestGetTransactionTool:
    """Test get_transaction tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetTransactionTool(context)

        assert tool.name == "get_transaction"
        assert "transaction" in tool.description.lower()
        assert tool.category == ToolCategory.TRANSACTIONS
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

        tool = GetTransactionTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "hash" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_transaction(self) -> None:
        """Test getting transaction by hash."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetTransactionTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tx = Mock()
            mock_client.tx.get_tx = AsyncMock(
                return_value={
                    "tx_response": {
                        "txhash": "ABC123",
                        "height": "12345",
                        "code": 0,
                        "raw_log": "success",
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"hash": "ABC123"})

            assert result["success"] is True
            assert "transaction" in result["data"]


class TestSearchTransactionsTool:
    """Test search_transactions tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SearchTransactionsTool(context)

        assert tool.name == "search_transactions"
        assert "search" in tool.description.lower()
        assert tool.category == ToolCategory.TRANSACTIONS
        assert tool.requires_wallet is False

    def test_validate_params_missing_query(self) -> None:
        """Test validation fails without query."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SearchTransactionsTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "query" in str(exc_info.value.message).lower()

    def test_validate_params_invalid_limit(self) -> None:
        """Test validation fails with invalid limit."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SearchTransactionsTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"query": "test", "limit": -1})

        assert "limit" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_search_transactions(self) -> None:
        """Test searching transactions."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SearchTransactionsTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tx = Mock()
            mock_client.tx.search = AsyncMock(
                return_value={
                    "txs": [{"txhash": "ABC123"}],
                    "total_count": "1",
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"query": "message.action='/cosmos.bank.v1beta1.MsgSend'"})

            assert result["success"] is True
            assert "transactions" in result["data"]


class TestEstimateGasTool:
    """Test estimate_gas tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = EstimateGasTool(context)

        assert tool.name == "estimate_gas"
        assert "gas" in tool.description.lower() or "estimate" in tool.description.lower()
        assert tool.category == ToolCategory.TRANSACTIONS
        assert tool.requires_wallet is False

    def test_validate_params_missing_messages(self) -> None:
        """Test validation fails without messages."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = EstimateGasTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "messages" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_estimate_gas(self) -> None:
        """Test estimating gas."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = EstimateGasTool(context)

        result = await tool.run({"messages": [{"type": "MsgSend"}]})

        assert result["success"] is True
        assert "gas_estimate" in result["data"]


class TestSimulateTransactionTool:
    """Test simulate_transaction tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SimulateTransactionTool(context)

        assert tool.name == "simulate_transaction"
        assert "simulate" in tool.description.lower()
        assert tool.category == ToolCategory.TRANSACTIONS
        assert tool.requires_wallet is False

    def test_validate_params_missing_messages(self) -> None:
        """Test validation fails without messages."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SimulateTransactionTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "messages" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_simulate_transaction(self) -> None:
        """Test simulating transaction."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SimulateTransactionTool(context)

        result = await tool.run({"messages": [{"type": "MsgSend"}]})

        assert result["success"] is True
        assert "simulation" in result["data"]


class TestGetTransactionStatusTool:
    """Test get_transaction_status tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetTransactionStatusTool(context)

        assert tool.name == "get_transaction_status"
        assert "status" in tool.description.lower()
        assert tool.category == ToolCategory.TRANSACTIONS
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

        tool = GetTransactionStatusTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "hash" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_transaction_status(self) -> None:
        """Test getting transaction status."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetTransactionStatusTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tx = Mock()
            mock_client.tx.get_tx = AsyncMock(
                return_value={
                    "tx_response": {
                        "txhash": "ABC123",
                        "code": 0,
                        "height": "12345",
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"hash": "ABC123"})

            assert result["success"] is True
            assert "status" in result["data"]
            assert result["data"]["status"] == "success"


class TestTransactionToolsIntegration:
    """Test transaction tools working together."""

    @pytest.mark.asyncio
    async def test_all_transaction_tools_have_correct_metadata(self) -> None:
        """Test all transaction tools can be instantiated and have correct metadata."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tools = [
            GetTransactionTool(context),
            SearchTransactionsTool(context),
            EstimateGasTool(context),
            SimulateTransactionTool(context),
            GetTransactionStatusTool(context),
        ]

        # All tools should be TRANSACTIONS category
        for tool in tools:
            assert tool.category == ToolCategory.TRANSACTIONS
            assert tool.name is not None
            assert tool.description is not None
            assert tool.requires_wallet is False

        # All tool names should be unique
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))
