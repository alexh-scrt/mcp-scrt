"""Unit tests for IBC tools."""

import pytest
from unittest.mock import AsyncMock, patch

from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.utils.errors import ValidationError, WalletError
from mcp_scrt.types import NetworkType, WalletInfo
from mcp_scrt.core.session import Session
from mcp_scrt.tools.base import ToolCategory, ToolExecutionContext
from mcp_scrt.tools.ibc import (
    IBCTransferTool,
    GetIBCChannelsTool,
    GetIBCChannelTool,
    GetIBCDenomTraceTool,
)


class TestIBCTransferTool:
    """Test ibc_transfer tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = IBCTransferTool(context)

        assert tool.name == "ibc_transfer"
        assert "ibc" in tool.description.lower()
        assert tool.category == ToolCategory.IBC
        assert tool.requires_wallet is True

    def test_validate_params_missing_channel_id(self) -> None:
        """Test validation fails without channel_id."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = IBCTransferTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "recipient": "cosmos1abc...",
                "amount": "1000000",
            })

        assert "channel_id" in str(exc_info.value.message).lower()

    def test_validate_params_missing_recipient(self) -> None:
        """Test validation fails without recipient."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = IBCTransferTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "channel_id": "channel-0",
                "amount": "1000000",
            })

        assert "recipient" in str(exc_info.value.message).lower()

    def test_validate_params_missing_amount(self) -> None:
        """Test validation fails without amount."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = IBCTransferTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "channel_id": "channel-0",
                "recipient": "cosmos1abc...",
            })

        assert "amount" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_ibc_transfer(self) -> None:
        """Test IBC transfer."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Start session and load wallet
        session.start()
        wallet = WalletInfo(
            wallet_id="test_wallet",
            address="secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
        )
        session.load_wallet(wallet)

        tool = IBCTransferTool(context)

        # Mock the signing client
        with patch("mcp_scrt.tools.ibc.create_signing_client") as mock_create:
            mock_signing = AsyncMock()
            mock_signing.ibc_transfer = AsyncMock(
                return_value={
                    "txhash": "ABC123",
                    "code": 0,
                }
            )
            mock_create.return_value = mock_signing

            result = await tool.run({
                "channel_id": "channel-0",
                "recipient": "cosmos1recipientrecipientrecipientrecipient",
                "amount": "1000000",
            })

            assert result["success"] is True
            assert "txhash" in result["data"]
            assert result["data"]["channel_id"] == "channel-0"

    @pytest.mark.asyncio
    async def test_execute_ibc_transfer_with_timeout(self) -> None:
        """Test IBC transfer with custom timeout."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Start session and load wallet
        session.start()
        wallet = WalletInfo(
            wallet_id="test_wallet",
            address="secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
        )
        session.load_wallet(wallet)

        tool = IBCTransferTool(context)

        # Mock the signing client
        with patch("mcp_scrt.tools.ibc.create_signing_client") as mock_create:
            mock_signing = AsyncMock()
            mock_signing.ibc_transfer = AsyncMock(
                return_value={
                    "txhash": "ABC123",
                    "code": 0,
                }
            )
            mock_create.return_value = mock_signing

            result = await tool.run({
                "channel_id": "channel-0",
                "recipient": "cosmos1recipientrecipientrecipientrecipient",
                "amount": "1000000",
                "timeout_height": "1000",
                "timeout_timestamp": "1700000000000000000",
            })

            assert result["success"] is True
            assert "txhash" in result["data"]


class TestGetIBCChannelsTool:
    """Test get_ibc_channels tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetIBCChannelsTool(context)

        assert tool.name == "get_ibc_channels"
        assert "channels" in tool.description.lower()
        assert tool.category == ToolCategory.IBC
        assert tool.requires_wallet is False

    @pytest.mark.asyncio
    async def test_execute_get_ibc_channels(self) -> None:
        """Test getting IBC channels."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetIBCChannelsTool(context)

        # Mock the client
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.ibc.channels = AsyncMock(
                return_value={
                    "channels": [
                        {
                            "channel_id": "channel-0",
                            "port_id": "transfer",
                            "state": "STATE_OPEN",
                            "counterparty": {
                                "channel_id": "channel-1",
                                "port_id": "transfer",
                            },
                        },
                        {
                            "channel_id": "channel-1",
                            "port_id": "transfer",
                            "state": "STATE_OPEN",
                            "counterparty": {
                                "channel_id": "channel-2",
                                "port_id": "transfer",
                            },
                        },
                    ],
                    "pagination": {},
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_client

            result = await tool.run({})

            assert result["success"] is True
            assert "channels" in result["data"]
            assert len(result["data"]["channels"]) == 2

    @pytest.mark.asyncio
    async def test_execute_get_ibc_channels_with_pagination(self) -> None:
        """Test getting IBC channels with pagination."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetIBCChannelsTool(context)

        # Mock the client
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.ibc.channels = AsyncMock(
                return_value={
                    "channels": [
                        {
                            "channel_id": "channel-0",
                            "port_id": "transfer",
                            "state": "STATE_OPEN",
                        },
                    ],
                    "pagination": {"next_key": "abc123"},
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_client

            result = await tool.run({
                "pagination_limit": "10",
                "pagination_offset": "5",
            })

            assert result["success"] is True
            assert "channels" in result["data"]


class TestGetIBCChannelTool:
    """Test get_ibc_channel tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetIBCChannelTool(context)

        assert tool.name == "get_ibc_channel"
        assert "channel" in tool.description.lower()
        assert tool.category == ToolCategory.IBC
        assert tool.requires_wallet is False

    def test_validate_params_missing_channel_id(self) -> None:
        """Test validation fails without channel_id."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetIBCChannelTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "channel_id" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_ibc_channel(self) -> None:
        """Test getting a specific IBC channel."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetIBCChannelTool(context)

        # Mock the client
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.ibc.channel = AsyncMock(
                return_value={
                    "channel": {
                        "channel_id": "channel-0",
                        "port_id": "transfer",
                        "state": "STATE_OPEN",
                        "ordering": "ORDER_UNORDERED",
                        "counterparty": {
                            "channel_id": "channel-1",
                            "port_id": "transfer",
                        },
                        "connection_hops": ["connection-0"],
                        "version": "ics20-1",
                    },
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_client

            result = await tool.run({
                "channel_id": "channel-0",
            })

            assert result["success"] is True
            assert "channel" in result["data"]
            assert result["data"]["channel"]["channel_id"] == "channel-0"

    @pytest.mark.asyncio
    async def test_execute_get_ibc_channel_with_port(self) -> None:
        """Test getting a specific IBC channel with custom port."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetIBCChannelTool(context)

        # Mock the client
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.ibc.channel = AsyncMock(
                return_value={
                    "channel": {
                        "channel_id": "channel-0",
                        "port_id": "wasm.secret1contract...",
                        "state": "STATE_OPEN",
                    },
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_client

            result = await tool.run({
                "channel_id": "channel-0",
                "port_id": "wasm.secret1contractcontractcontractcontractcontra",
            })

            assert result["success"] is True
            assert "channel" in result["data"]


class TestGetIBCDenomTraceTool:
    """Test get_ibc_denom_trace tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetIBCDenomTraceTool(context)

        assert tool.name == "get_ibc_denom_trace"
        assert "denom" in tool.description.lower()
        assert tool.category == ToolCategory.IBC
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

        tool = GetIBCDenomTraceTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "hash" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_ibc_denom_trace(self) -> None:
        """Test getting IBC denom trace."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetIBCDenomTraceTool(context)

        # Mock the client
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.ibc.denom_trace = AsyncMock(
                return_value={
                    "denom_trace": {
                        "path": "transfer/channel-0",
                        "base_denom": "uatom",
                    },
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_client

            result = await tool.run({
                "hash": "27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2",
            })

            assert result["success"] is True
            assert "denom_trace" in result["data"]
            assert result["data"]["denom_trace"]["base_denom"] == "uatom"


class TestIBCToolsIntegration:
    """Integration tests for IBC tools."""

    def test_all_ibc_tools_have_correct_metadata(self) -> None:
        """Test all IBC tools have correct metadata."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tools = [
            IBCTransferTool(context),
            GetIBCChannelsTool(context),
            GetIBCChannelTool(context),
            GetIBCDenomTraceTool(context),
        ]

        for tool in tools:
            assert tool.name is not None
            assert tool.description is not None
            assert tool.category == ToolCategory.IBC
            assert isinstance(tool.requires_wallet, bool)
