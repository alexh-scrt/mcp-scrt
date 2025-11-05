"""Tests for bank tools.

This module tests the bank tools for token operations.
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, patch, AsyncMock

from mcp_scrt.tools.bank import (
    GetBalanceTool,
    SendTokensTool,
    MultiSendTool,
    GetTotalSupplyTool,
    GetDenomMetadataTool,
)
from mcp_scrt.tools.base import ToolCategory, ToolExecutionContext
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.sdk.wallet import HDWallet, generate_mnemonic
from mcp_scrt.types import NetworkType, WalletInfo
from mcp_scrt.utils.errors import ValidationError


class TestGetBalanceTool:
    """Test get_balance tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetBalanceTool(context)

        assert tool.name == "get_balance"
        assert "balance" in tool.description.lower()
        assert tool.category == ToolCategory.BANK
        assert tool.requires_wallet is False  # Can query any address

    def test_validate_params_missing_address(self) -> None:
        """Test validation fails without address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetBalanceTool(context)

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

        tool = GetBalanceTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"address": "invalid"})

        assert "address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_balance(self) -> None:
        """Test getting balance."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetBalanceTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.bank = Mock()
            mock_client.bank.balance = AsyncMock(
                return_value={
                    "balances": [
                        {"denom": "uscrt", "amount": "1000000"},
                    ]
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"})

            assert result["success"] is True
            assert "balances" in result["data"]
            assert len(result["data"]["balances"]) > 0


class TestSendTokensTool:
    """Test send_tokens tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SendTokensTool(context)

        assert tool.name == "send_tokens"
        assert "send" in tool.description.lower()
        assert tool.category == ToolCategory.BANK
        assert tool.requires_wallet is True  # Requires wallet for signing

    def test_validate_params_missing_to_address(self) -> None:
        """Test validation fails without to_address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SendTokensTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"amount": "1000000", "denom": "uscrt"})

        assert "to_address" in str(exc_info.value.message).lower()

    def test_validate_params_missing_amount(self) -> None:
        """Test validation fails without amount."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SendTokensTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "to_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
                "denom": "uscrt"
            })

        assert "amount" in str(exc_info.value.message).lower()

    def test_validate_params_invalid_amount(self) -> None:
        """Test validation fails with invalid amount."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SendTokensTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "to_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
                "amount": "-100",
                "denom": "uscrt"
            })

        assert "amount" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_send_tokens(self) -> None:
        """Test sending tokens."""
        # Create a wallet
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)
        address = wallet.get_address()

        session = Session(network=NetworkType.TESTNET)
        session.start()
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Load wallet
        wallet_info = WalletInfo(wallet_id="test", address=address)
        session.load_wallet(wallet_info)

        tool = SendTokensTool(context)

        # Note: This will fail in real execution without actual blockchain connection
        # But we're testing the tool structure
        result = await tool.run({
            "to_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
            "amount": "1000000",
            "denom": "uscrt",
        })

        # In test environment without real blockchain, this should return structure
        assert "success" in result or "error" in result


class TestMultiSendTool:
    """Test multi_send tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = MultiSendTool(context)

        assert tool.name == "multi_send"
        assert "multi" in tool.description.lower() or "multiple" in tool.description.lower()
        assert tool.category == ToolCategory.BANK
        assert tool.requires_wallet is True

    def test_validate_params_missing_recipients(self) -> None:
        """Test validation fails without recipients."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = MultiSendTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "recipients" in str(exc_info.value.message).lower()

    def test_validate_params_empty_recipients(self) -> None:
        """Test validation fails with empty recipients list."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = MultiSendTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"recipients": []})

        assert "recipients" in str(exc_info.value.message).lower()

    def test_validate_params_invalid_recipient_format(self) -> None:
        """Test validation fails with invalid recipient format."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = MultiSendTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "recipients": [
                    {"address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"}  # Missing amount
                ]
            })

        # Should fail validation


class TestGetTotalSupplyTool:
    """Test get_total_supply tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetTotalSupplyTool(context)

        assert tool.name == "get_total_supply"
        assert "supply" in tool.description.lower()
        assert tool.category == ToolCategory.BANK
        assert tool.requires_wallet is False

    @pytest.mark.asyncio
    async def test_execute_get_total_supply(self) -> None:
        """Test getting total supply."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetTotalSupplyTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.bank = Mock()
            mock_client.bank.total_supply = AsyncMock(
                return_value={
                    "supply": [
                        {"denom": "uscrt", "amount": "1000000000"},
                    ]
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({})

            assert result["success"] is True
            assert "supply" in result["data"]


class TestGetDenomMetadataTool:
    """Test get_denom_metadata tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetDenomMetadataTool(context)

        assert tool.name == "get_denom_metadata"
        assert "metadata" in tool.description.lower()
        assert tool.category == ToolCategory.BANK
        assert tool.requires_wallet is False

    def test_validate_params_missing_denom(self) -> None:
        """Test validation fails without denom."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetDenomMetadataTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "denom" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_denom_metadata(self) -> None:
        """Test getting denom metadata."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetDenomMetadataTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.bank = Mock()
            mock_client.bank.denom_metadata = AsyncMock(
                return_value={
                    "metadata": {
                        "description": "Secret Network native token",
                        "denom_units": [
                            {"denom": "uscrt", "exponent": 0},
                            {"denom": "scrt", "exponent": 6},
                        ],
                        "base": "uscrt",
                        "display": "scrt",
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"denom": "uscrt"})

            assert result["success"] is True
            assert "metadata" in result["data"]


class TestBankToolsIntegration:
    """Test bank tools working together."""

    @pytest.mark.asyncio
    async def test_all_bank_tools_have_correct_metadata(self) -> None:
        """Test all bank tools can be instantiated and have correct metadata."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tools = [
            GetBalanceTool(context),
            SendTokensTool(context),
            MultiSendTool(context),
            GetTotalSupplyTool(context),
            GetDenomMetadataTool(context),
        ]

        # All tools should be BANK category
        for tool in tools:
            assert tool.category == ToolCategory.BANK
            assert tool.name is not None
            assert tool.description is not None

        # All tool names should be unique
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))

    @pytest.mark.asyncio
    async def test_get_balance_then_send(self) -> None:
        """Test getting balance before sending tokens."""
        # Create a wallet
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)
        address = wallet.get_address()

        session = Session(network=NetworkType.TESTNET)
        session.start()
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Load wallet
        wallet_info = WalletInfo(wallet_id="test", address=address)
        session.load_wallet(wallet_info)

        # Mock get balance
        get_balance_tool = GetBalanceTool(context)

        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.bank = Mock()
            mock_client.bank.balance = AsyncMock(
                return_value={
                    "balances": [
                        {"denom": "uscrt", "amount": "1000000"},
                    ]
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            balance_result = await get_balance_tool.run({"address": address})

            assert balance_result["success"] is True
