"""Tests for wallet tools.

This module tests the wallet tools for wallet management operations.
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, patch, MagicMock

from mcp_scrt.tools.wallet import (
    CreateWalletTool,
    ImportWalletTool,
    SetActiveWalletTool,
    GetActiveWalletTool,
    ListWalletsTool,
    RemoveWalletTool,
)
from mcp_scrt.tools.base import ToolCategory, ToolExecutionContext
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.sdk.wallet import HDWallet, generate_mnemonic
from mcp_scrt.types import NetworkType, WalletInfo
from mcp_scrt.utils.errors import ValidationError


class TestCreateWalletTool:
    """Test create_wallet tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = CreateWalletTool(context)

        assert tool.name == "create_wallet"
        assert "create" in tool.description.lower()
        assert "wallet" in tool.description.lower()
        assert tool.category == ToolCategory.WALLET
        assert tool.requires_wallet is False  # Creating wallet doesn't require existing wallet

    def test_validate_params_with_no_params(self) -> None:
        """Test validation passes with no parameters (generates mnemonic)."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = CreateWalletTool(context)

        # Should not raise - mnemonic will be generated
        tool.validate_params({})

    def test_validate_params_with_word_count(self) -> None:
        """Test validation with word_count parameter."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = CreateWalletTool(context)

        # Valid word counts
        tool.validate_params({"word_count": 12})
        tool.validate_params({"word_count": 24})

        # Invalid word count
        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"word_count": 15})

        assert "word_count" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_create_wallet(self) -> None:
        """Test creating a new wallet."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = CreateWalletTool(context)

        result = await tool.run({})

        assert result["success"] is True
        assert "address" in result["data"]
        assert "mnemonic" in result["data"]
        assert "wallet_id" in result["data"]
        assert result["data"]["address"].startswith("secret1")
        assert len(result["data"]["mnemonic"].split()) == 24  # Default 24 words

    @pytest.mark.asyncio
    async def test_execute_create_wallet_with_word_count(self) -> None:
        """Test creating wallet with specific word count."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = CreateWalletTool(context)

        result = await tool.run({"word_count": 12})

        assert result["success"] is True
        assert len(result["data"]["mnemonic"].split()) == 12


class TestImportWalletTool:
    """Test import_wallet tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ImportWalletTool(context)

        assert tool.name == "import_wallet"
        assert "import" in tool.description.lower()
        assert tool.category == ToolCategory.WALLET
        assert tool.requires_wallet is False

    def test_validate_params_missing_mnemonic(self) -> None:
        """Test validation fails without mnemonic."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ImportWalletTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "mnemonic" in str(exc_info.value.message).lower()

    def test_validate_params_invalid_mnemonic(self) -> None:
        """Test validation fails with invalid mnemonic."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ImportWalletTool(context)

        # Too short
        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"mnemonic": "word1 word2 word3"})

        assert "mnemonic" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_import_wallet(self) -> None:
        """Test importing a wallet from mnemonic."""
        # Generate a valid mnemonic
        mnemonic = generate_mnemonic(word_count=24)

        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ImportWalletTool(context)

        result = await tool.run({"mnemonic": mnemonic})

        assert result["success"] is True
        assert "address" in result["data"]
        assert "wallet_id" in result["data"]
        assert result["data"]["address"].startswith("secret1")


class TestSetActiveWalletTool:
    """Test set_active_wallet tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SetActiveWalletTool(context)

        assert tool.name == "set_active_wallet"
        assert tool.category == ToolCategory.WALLET
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

        tool = SetActiveWalletTool(context)

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

        tool = SetActiveWalletTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"address": "invalid"})

        assert "address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_set_active_wallet(self) -> None:
        """Test setting active wallet."""
        # Create a wallet first
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)
        address = wallet.get_address()

        session = Session(network=NetworkType.TESTNET)
        session.start()  # Start session before loading wallet
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Load wallet into session
        wallet_info = WalletInfo(wallet_id="test-wallet", address=address)
        session.load_wallet(wallet_info)

        tool = SetActiveWalletTool(context)

        result = await tool.run({"address": address})

        assert result["success"] is True
        assert result["data"]["address"] == address
        assert result["data"]["status"] == "active"


class TestGetActiveWalletTool:
    """Test get_active_wallet tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetActiveWalletTool(context)

        assert tool.name == "get_active_wallet"
        assert tool.category == ToolCategory.WALLET
        assert tool.requires_wallet is True  # Requires active wallet

    @pytest.mark.asyncio
    async def test_execute_get_active_wallet_with_wallet(self) -> None:
        """Test getting active wallet when wallet is loaded."""
        # Create a wallet
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)
        address = wallet.get_address()

        session = Session(network=NetworkType.TESTNET)
        session.start()  # Start session before loading wallet
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Load wallet into session
        wallet_info = WalletInfo(wallet_id="test-wallet", address=address)
        session.load_wallet(wallet_info)

        tool = GetActiveWalletTool(context)

        result = await tool.run({})

        assert result["success"] is True
        assert result["data"]["address"] == address
        assert result["data"]["wallet_id"] == "test-wallet"

    @pytest.mark.asyncio
    async def test_execute_get_active_wallet_without_wallet(self) -> None:
        """Test getting active wallet when no wallet is loaded."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetActiveWalletTool(context)

        result = await tool.run({})

        # Should fail because requires_wallet is True and no wallet is active
        assert result["success"] is False
        assert "requires an active wallet" in result["error"]["message"]


class TestListWalletsTool:
    """Test list_wallets tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ListWalletsTool(context)

        assert tool.name == "list_wallets"
        assert tool.category == ToolCategory.WALLET
        assert tool.requires_wallet is False

    @pytest.mark.asyncio
    async def test_execute_list_wallets_empty(self) -> None:
        """Test listing wallets when none exist."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ListWalletsTool(context)

        result = await tool.run({})

        assert result["success"] is True
        assert "wallets" in result["data"]
        assert isinstance(result["data"]["wallets"], list)
        assert result["data"]["count"] == 0

    @pytest.mark.asyncio
    async def test_execute_list_wallets_with_wallet(self) -> None:
        """Test listing wallets with active wallet."""
        # Create a wallet
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)
        address = wallet.get_address()

        session = Session(network=NetworkType.TESTNET)
        session.start()  # Start session before loading wallet
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Load wallet into session
        wallet_info = WalletInfo(wallet_id="test-wallet", address=address)
        session.load_wallet(wallet_info)

        tool = ListWalletsTool(context)

        result = await tool.run({})

        assert result["success"] is True
        assert result["data"]["count"] >= 1
        assert any(w["address"] == address for w in result["data"]["wallets"])


class TestRemoveWalletTool:
    """Test remove_wallet tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = RemoveWalletTool(context)

        assert tool.name == "remove_wallet"
        assert tool.category == ToolCategory.WALLET
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

        tool = RemoveWalletTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_remove_wallet(self) -> None:
        """Test removing a wallet."""
        # Create a wallet
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)
        address = wallet.get_address()

        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = RemoveWalletTool(context)

        result = await tool.run({"address": address})

        assert result["success"] is True
        assert result["data"]["address"] == address
        assert result["data"]["status"] == "removed"


class TestWalletToolsIntegration:
    """Test wallet tools working together."""

    @pytest.mark.asyncio
    async def test_create_and_list_wallets(self) -> None:
        """Test creating wallet then listing."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Create wallet
        create_tool = CreateWalletTool(context)
        create_result = await create_tool.run({})

        assert create_result["success"] is True
        address = create_result["data"]["address"]

        # List wallets
        list_tool = ListWalletsTool(context)
        list_result = await list_tool.run({})

        assert list_result["success"] is True
        # Note: Listing might show the wallet if session stores it

    @pytest.mark.asyncio
    async def test_full_wallet_lifecycle(self) -> None:
        """Test complete wallet lifecycle: create, set active, get, remove."""
        session = Session(network=NetworkType.TESTNET)
        session.start()  # Start session before loading wallet
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Create wallet
        create_tool = CreateWalletTool(context)
        create_result = await create_tool.run({})
        address = create_result["data"]["address"]

        # Set as active
        set_tool = SetActiveWalletTool(context)
        # First load wallet info into session
        wallet_info = WalletInfo(wallet_id=create_result["data"]["wallet_id"], address=address)
        session.load_wallet(wallet_info)
        set_result = await set_tool.run({"address": address})

        assert set_result["success"] is True

        # Get active
        get_tool = GetActiveWalletTool(context)
        get_result = await get_tool.run({})

        assert get_result["success"] is True
        assert get_result["data"]["address"] == address

        # Remove
        remove_tool = RemoveWalletTool(context)
        remove_result = await remove_tool.run({"address": address})

        assert remove_result["success"] is True

    @pytest.mark.asyncio
    async def test_all_wallet_tools_have_correct_metadata(self) -> None:
        """Test all wallet tools can be instantiated and have correct metadata."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tools = [
            CreateWalletTool(context),
            ImportWalletTool(context),
            SetActiveWalletTool(context),
            GetActiveWalletTool(context),
            ListWalletsTool(context),
            RemoveWalletTool(context),
        ]

        # All tools should be WALLET category
        for tool in tools:
            assert tool.category == ToolCategory.WALLET
            assert tool.name is not None
            assert tool.description is not None

        # All tool names should be unique
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))
