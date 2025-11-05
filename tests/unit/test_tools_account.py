"""Tests for account tools.

This module tests the account tools for querying account information and transactions.
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, patch, AsyncMock

from mcp_scrt.tools.account import (
    GetAccountTool,
    GetAccountTransactionsTool,
    GetAccountTxCountTool,
)
from mcp_scrt.tools.base import ToolCategory, ToolExecutionContext
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.types import NetworkType
from mcp_scrt.utils.errors import ValidationError


class TestGetAccountTool:
    """Test get_account tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetAccountTool(context)

        assert tool.name == "get_account"
        assert "account" in tool.description.lower()
        assert tool.category == ToolCategory.ACCOUNTS
        assert tool.requires_wallet is False

    def test_validate_params_missing_address(self) -> None:
        """Test validation fails without address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetAccountTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "address" in str(exc_info.value.message).lower()

    def test_validate_params_invalid_address(self) -> None:
        """Test validation fails with invalid address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetAccountTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"address": "invalid"})

        assert "address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_account(self) -> None:
        """Test getting account information."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetAccountTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.auth = Mock()
            mock_client.auth.account = AsyncMock(
                return_value={
                    "account": {
                        "address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
                        "pub_key": None,
                        "account_number": "12345",
                        "sequence": "42",
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"})

            assert result["success"] is True
            assert "account" in result["data"]
            assert result["data"]["address"] == "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"


class TestGetAccountTransactionsTool:
    """Test get_account_transactions tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetAccountTransactionsTool(context)

        assert tool.name == "get_account_transactions"
        assert "transaction" in tool.description.lower()
        assert tool.category == ToolCategory.ACCOUNTS
        assert tool.requires_wallet is False

    def test_validate_params_missing_address(self) -> None:
        """Test validation fails without address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetAccountTransactionsTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "address" in str(exc_info.value.message).lower()

    def test_validate_params_invalid_limit(self) -> None:
        """Test validation fails with invalid limit."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetAccountTransactionsTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
                "limit": -1
            })

        assert "limit" in str(exc_info.value.message).lower()

    def test_validate_params_invalid_offset(self) -> None:
        """Test validation fails with invalid offset."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetAccountTransactionsTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
                "offset": -1
            })

        assert "offset" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_account_transactions(self) -> None:
        """Test getting account transactions."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetAccountTransactionsTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tx = Mock()
            mock_client.tx.search = AsyncMock(
                return_value={
                    "txs": [
                        {
                            "txhash": "ABC123",
                            "height": "12345",
                            "tx": {"body": {"messages": []}},
                        }
                    ],
                    "total_count": "1",
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"})

            assert result["success"] is True
            assert "transactions" in result["data"]
            assert result["data"]["count"] == 1


class TestGetAccountTxCountTool:
    """Test get_account_tx_count tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetAccountTxCountTool(context)

        assert tool.name == "get_account_tx_count"
        assert "count" in tool.description.lower() or "transaction" in tool.description.lower()
        assert tool.category == ToolCategory.ACCOUNTS
        assert tool.requires_wallet is False

    def test_validate_params_missing_address(self) -> None:
        """Test validation fails without address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetAccountTxCountTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_account_tx_count(self) -> None:
        """Test getting account transaction count."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetAccountTxCountTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tx = Mock()
            mock_client.tx.search = AsyncMock(
                return_value={
                    "txs": [],
                    "total_count": "42",
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"})

            assert result["success"] is True
            assert "count" in result["data"]
            assert result["data"]["count"] == 42


class TestAccountToolsIntegration:
    """Test account tools working together."""

    @pytest.mark.asyncio
    async def test_all_account_tools_have_correct_metadata(self) -> None:
        """Test all account tools can be instantiated and have correct metadata."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tools = [
            GetAccountTool(context),
            GetAccountTransactionsTool(context),
            GetAccountTxCountTool(context),
        ]

        # All tools should be ACCOUNTS category
        for tool in tools:
            assert tool.category == ToolCategory.ACCOUNTS
            assert tool.name is not None
            assert tool.description is not None
            assert tool.requires_wallet is False

        # All tool names should be unique
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))
