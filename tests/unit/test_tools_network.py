"""Tests for network tools.

This module tests the network tools for blockchain connectivity and information.
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, patch, AsyncMock

from mcp_scrt.tools.network import (
    ConfigureNetworkTool,
    GetNetworkInfoTool,
    GetGasPricesTool,
    HealthCheckTool,
)
from mcp_scrt.tools.base import ToolCategory, ToolExecutionContext
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.types import NetworkType
from mcp_scrt.utils.errors import ValidationError


class TestConfigureNetworkTool:
    """Test configure_network tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ConfigureNetworkTool(context)

        assert tool.name == "configure_network"
        assert "Configure network settings" in tool.description
        assert tool.category == ToolCategory.NETWORK
        assert tool.requires_wallet is False

    def test_validate_params_missing_network(self) -> None:
        """Test validation fails with missing network parameter."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ConfigureNetworkTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "network" in str(exc_info.value.message).lower()

    def test_validate_params_invalid_network(self) -> None:
        """Test validation fails with invalid network value."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ConfigureNetworkTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"network": "invalid"})

        assert "network" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_configure_testnet(self) -> None:
        """Test configuring network to testnet."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ConfigureNetworkTool(context)

        result = await tool.run({"network": "testnet"})

        assert result["success"] is True
        assert result["data"]["network"] == "testnet"
        assert "chain_id" in result["data"]
        assert "lcd_url" in result["data"]

    @pytest.mark.asyncio
    async def test_execute_configure_mainnet(self) -> None:
        """Test configuring network to mainnet."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ConfigureNetworkTool(context)

        result = await tool.run({"network": "mainnet"})

        assert result["success"] is True
        assert result["data"]["network"] == "mainnet"
        assert "chain_id" in result["data"]
        assert "lcd_url" in result["data"]


class TestGetNetworkInfoTool:
    """Test get_network_info tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetNetworkInfoTool(context)

        assert tool.name == "get_network_info"
        assert "network information" in tool.description.lower()
        assert tool.category == ToolCategory.NETWORK
        assert tool.requires_wallet is False

    def test_validate_params_no_params_required(self) -> None:
        """Test validation passes with no parameters."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetNetworkInfoTool(context)

        # Should not raise
        tool.validate_params({})

    @pytest.mark.asyncio
    async def test_execute_get_network_info(self) -> None:
        """Test getting network information."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetNetworkInfoTool(context)

        result = await tool.run({})

        assert result["success"] is True
        assert result["data"]["network"] == "testnet"
        assert "chain_id" in result["data"]
        assert "lcd_url" in result["data"]
        assert "bech32_prefix" in result["data"]


class TestGetGasPricesTool:
    """Test get_gas_prices tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetGasPricesTool(context)

        assert tool.name == "get_gas_prices"
        assert "gas prices" in tool.description.lower()
        assert tool.category == ToolCategory.NETWORK
        assert tool.requires_wallet is False

    def test_validate_params_no_params_required(self) -> None:
        """Test validation passes with no parameters."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetGasPricesTool(context)

        # Should not raise
        tool.validate_params({})

    @pytest.mark.asyncio
    async def test_execute_get_gas_prices(self) -> None:
        """Test getting gas prices."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetGasPricesTool(context)

        result = await tool.run({})

        assert result["success"] is True
        assert "gas_prices" in result["data"]
        assert "denom" in result["data"]
        assert result["data"]["denom"] == "uscrt"
        assert isinstance(result["data"]["gas_prices"], dict)


class TestHealthCheckTool:
    """Test health_check tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = HealthCheckTool(context)

        assert tool.name == "health_check"
        assert "health" in tool.description.lower()
        assert tool.category == ToolCategory.NETWORK
        assert tool.requires_wallet is False

    def test_validate_params_no_params_required(self) -> None:
        """Test validation passes with no parameters."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = HealthCheckTool(context)

        # Should not raise
        tool.validate_params({})

    @pytest.mark.asyncio
    async def test_execute_health_check_success(self) -> None:
        """Test successful health check."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = HealthCheckTool(context)

        # Mock the client pool to return a healthy response
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tendermint = Mock()
            mock_client.tendermint.node_info = AsyncMock(
                return_value={
                    "node_info": {"network": "pulsar-3"},
                    "application_version": {"version": "1.0.0"},
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({})

            assert result["success"] is True
            assert result["data"]["status"] == "healthy"
            assert result["data"]["network"] == "testnet"
            assert "node_connected" in result["data"]
            assert result["data"]["node_connected"] is True

    @pytest.mark.asyncio
    async def test_execute_health_check_failure(self) -> None:
        """Test health check with connection failure."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = HealthCheckTool(context)

        # Mock the client pool to raise an exception
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tendermint = Mock()
            mock_client.tendermint.node_info = AsyncMock(
                side_effect=Exception("Connection failed")
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({})

            assert result["success"] is True  # Health check doesn't fail, returns status
            assert result["data"]["status"] == "unhealthy"
            assert result["data"]["node_connected"] is False
            assert "error" in result["data"]


class TestNetworkToolsIntegration:
    """Test network tools working together."""

    @pytest.mark.asyncio
    async def test_configure_then_get_info(self) -> None:
        """Test configuring network then getting info."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Configure network
        configure_tool = ConfigureNetworkTool(context)
        config_result = await configure_tool.run({"network": "testnet"})

        assert config_result["success"] is True

        # Get network info
        info_tool = GetNetworkInfoTool(context)
        info_result = await info_tool.run({})

        assert info_result["success"] is True
        assert info_result["data"]["network"] == "testnet"

    @pytest.mark.asyncio
    async def test_all_network_tools(self) -> None:
        """Test all network tools can be instantiated and have correct metadata."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tools = [
            ConfigureNetworkTool(context),
            GetNetworkInfoTool(context),
            GetGasPricesTool(context),
            HealthCheckTool(context),
        ]

        # All tools should be NETWORK category
        for tool in tools:
            assert tool.category == ToolCategory.NETWORK
            assert tool.requires_wallet is False
            assert tool.name is not None
            assert tool.description is not None

        # All tool names should be unique
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))
