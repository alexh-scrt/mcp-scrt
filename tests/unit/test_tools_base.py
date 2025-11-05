"""Tests for base tool handler.

This module tests the base tool handler that all MCP tools inherit from.
"""

import pytest
from typing import Any, Dict, Optional
from unittest.mock import Mock, patch

from mcp_scrt.tools.base import BaseTool, ToolCategory, ToolExecutionContext
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.types import NetworkType
from mcp_scrt.utils.errors import ValidationError, SecretMCPError


class TestToolCategory:
    """Test tool category enum."""

    def test_tool_category_values(self) -> None:
        """Test that all expected tool categories exist."""
        expected_categories = [
            "network",
            "wallet",
            "bank",
            "staking",
            "rewards",
            "governance",
            "contracts",
            "ibc",
            "transactions",
            "blockchain",
            "accounts",
        ]

        for category in expected_categories:
            assert hasattr(ToolCategory, category.upper())
            assert ToolCategory[category.upper()].value == category


class TestToolExecutionContext:
    """Test tool execution context."""

    def test_context_creation(self) -> None:
        """Test creating execution context."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)

        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        assert context.session == session
        assert context.client_pool == pool
        assert context.network == NetworkType.TESTNET

    def test_context_with_metadata(self) -> None:
        """Test context with additional metadata."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)

        metadata = {"request_id": "test-123", "user": "test-user"}
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
            metadata=metadata,
        )

        assert context.metadata == metadata
        assert context.metadata["request_id"] == "test-123"


class TestBaseTool:
    """Test base tool handler."""

    def test_base_tool_cannot_be_instantiated(self) -> None:
        """Test that BaseTool is abstract and cannot be instantiated directly."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        with pytest.raises(TypeError):
            # BaseTool has abstract methods and cannot be instantiated
            BaseTool(context)  # type: ignore

    def test_concrete_tool_implementation(self) -> None:
        """Test creating a concrete tool implementation."""

        class TestTool(BaseTool):
            """Test tool for validation."""

            @property
            def name(self) -> str:
                return "test_tool"

            @property
            def description(self) -> str:
                return "A test tool"

            @property
            def category(self) -> ToolCategory:
                return ToolCategory.NETWORK

            @property
            def requires_wallet(self) -> bool:
                return False

            def validate_params(self, params: Dict[str, Any]) -> None:
                """Validate parameters."""
                pass

            async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
                """Execute the tool."""
                return {"result": "success"}

        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = TestTool(context)

        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.category == ToolCategory.NETWORK
        assert tool.requires_wallet is False

    @pytest.mark.asyncio
    async def test_tool_execution_flow(self) -> None:
        """Test complete tool execution flow with validation."""

        class TestTool(BaseTool):
            """Test tool for execution flow."""

            @property
            def name(self) -> str:
                return "test_tool"

            @property
            def description(self) -> str:
                return "A test tool"

            @property
            def category(self) -> ToolCategory:
                return ToolCategory.NETWORK

            @property
            def requires_wallet(self) -> bool:
                return False

            def validate_params(self, params: Dict[str, Any]) -> None:
                """Validate parameters."""
                if "value" not in params:
                    raise ValidationError("Missing required parameter: value")

            async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
                """Execute the tool."""
                return {"value": params["value"] * 2}

        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = TestTool(context)

        # Test successful execution
        result = await tool.run({"value": 5})
        assert result["success"] is True
        assert result["data"]["value"] == 10
        assert "error" not in result

        # Test validation error
        result = await tool.run({})
        assert result["success"] is False
        assert "error" in result
        assert "Missing required parameter" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_tool_requires_wallet_check(self) -> None:
        """Test that tools requiring wallet check for active wallet."""

        class WalletTool(BaseTool):
            """Tool that requires a wallet."""

            @property
            def name(self) -> str:
                return "wallet_tool"

            @property
            def description(self) -> str:
                return "A tool requiring wallet"

            @property
            def category(self) -> ToolCategory:
                return ToolCategory.WALLET

            @property
            def requires_wallet(self) -> bool:
                return True

            def validate_params(self, params: Dict[str, Any]) -> None:
                """Validate parameters."""
                pass

            async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
                """Execute the tool."""
                return {"result": "success"}

        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = WalletTool(context)

        # Without active wallet, should fail
        result = await tool.run({})
        assert result["success"] is False
        assert "requires an active wallet" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_tool_error_handling(self) -> None:
        """Test that tool errors are properly handled and formatted."""

        class ErrorTool(BaseTool):
            """Tool that raises an error."""

            @property
            def name(self) -> str:
                return "error_tool"

            @property
            def description(self) -> str:
                return "A tool that errors"

            @property
            def category(self) -> ToolCategory:
                return ToolCategory.NETWORK

            @property
            def requires_wallet(self) -> bool:
                return False

            def validate_params(self, params: Dict[str, Any]) -> None:
                """Validate parameters."""
                pass

            async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
                """Execute the tool."""
                raise ValueError("Something went wrong")

        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ErrorTool(context)

        result = await tool.run({})
        assert result["success"] is False
        assert "error" in result
        assert "Something went wrong" in result["error"]["message"]

    def test_tool_metadata(self) -> None:
        """Test tool metadata properties."""

        class TestTool(BaseTool):
            """Test tool with metadata."""

            @property
            def name(self) -> str:
                return "test_tool"

            @property
            def description(self) -> str:
                return "A test tool"

            @property
            def category(self) -> ToolCategory:
                return ToolCategory.BANK

            @property
            def requires_wallet(self) -> bool:
                return True

            def validate_params(self, params: Dict[str, Any]) -> None:
                """Validate parameters."""
                pass

            async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
                """Execute the tool."""
                return {}

        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = TestTool(context)

        metadata = tool.get_metadata()

        assert metadata["name"] == "test_tool"
        assert metadata["description"] == "A test tool"
        assert metadata["category"] == "bank"
        assert metadata["requires_wallet"] is True

    @pytest.mark.asyncio
    async def test_tool_with_client_pool(self) -> None:
        """Test tool that uses client pool."""

        class ClientTool(BaseTool):
            """Tool that uses client pool."""

            @property
            def name(self) -> str:
                return "client_tool"

            @property
            def description(self) -> str:
                return "A tool using client pool"

            @property
            def category(self) -> ToolCategory:
                return ToolCategory.BLOCKCHAIN

            @property
            def requires_wallet(self) -> bool:
                return False

            def validate_params(self, params: Dict[str, Any]) -> None:
                """Validate parameters."""
                pass

            async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
                """Execute the tool."""
                # Verify we have access to client pool
                assert self.context.client_pool is not None
                return {"pool_available": True}

        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ClientTool(context)

        result = await tool.run({})
        assert result["success"] is True
        assert result["data"]["pool_available"] is True


class TestToolRegistry:
    """Test tool registry patterns."""

    def test_multiple_tools_registration(self) -> None:
        """Test that multiple tools can be created with same context."""

        class Tool1(BaseTool):
            @property
            def name(self) -> str:
                return "tool1"

            @property
            def description(self) -> str:
                return "Tool 1"

            @property
            def category(self) -> ToolCategory:
                return ToolCategory.NETWORK

            @property
            def requires_wallet(self) -> bool:
                return False

            def validate_params(self, params: Dict[str, Any]) -> None:
                pass

            async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
                return {"tool": "1"}

        class Tool2(BaseTool):
            @property
            def name(self) -> str:
                return "tool2"

            @property
            def description(self) -> str:
                return "Tool 2"

            @property
            def category(self) -> ToolCategory:
                return ToolCategory.WALLET

            @property
            def requires_wallet(self) -> bool:
                return True

            def validate_params(self, params: Dict[str, Any]) -> None:
                pass

            async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
                return {"tool": "2"}

        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool1 = Tool1(context)
        tool2 = Tool2(context)

        assert tool1.name == "tool1"
        assert tool2.name == "tool2"
        assert tool1.category == ToolCategory.NETWORK
        assert tool2.category == ToolCategory.WALLET
        assert tool1.requires_wallet is False
        assert tool2.requires_wallet is True
