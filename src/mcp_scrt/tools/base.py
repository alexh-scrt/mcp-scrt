"""Base tool handler for MCP tools.

This module provides the base class and common infrastructure for all MCP tools.
"""

import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.types import NetworkType
from mcp_scrt.utils.errors import SecretMCPError, ValidationError, WalletError
from mcp_scrt.utils.logging import get_logger

# Module logger
logger = get_logger(__name__)


class ToolCategory(Enum):
    """Tool category classification."""

    NETWORK = "network"
    WALLET = "wallet"
    BANK = "bank"
    STAKING = "staking"
    REWARDS = "rewards"
    GOVERNANCE = "governance"
    CONTRACTS = "contracts"
    IBC = "ibc"
    TRANSACTIONS = "transactions"
    BLOCKCHAIN = "blockchain"
    ACCOUNTS = "accounts"


@dataclass
class ToolExecutionContext:
    """Context for tool execution.

    Provides access to session, client pool, and network configuration.
    """

    session: Session
    client_pool: ClientPool
    network: NetworkType
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """Base class for all MCP tools.

    All tools must inherit from this class and implement the required abstract methods.

    Example:
        class MyTool(BaseTool):
            @property
            def name(self) -> str:
                return "my_tool"

            @property
            def description(self) -> str:
                return "Does something useful"

            @property
            def category(self) -> ToolCategory:
                return ToolCategory.NETWORK

            @property
            def requires_wallet(self) -> bool:
                return False

            def validate_params(self, params: Dict[str, Any]) -> None:
                if "value" not in params:
                    raise ValidationError("Missing required parameter: value")

            async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
                return {"result": params["value"]}
    """

    def __init__(self, context: ToolExecutionContext):
        """Initialize tool with execution context.

        Args:
            context: Tool execution context
        """
        self.context = context
        self._logger = get_logger(f"{__name__}.{self.name}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Get tool name (must be unique).

        Returns:
            Tool name (e.g., "get_balance")
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get tool description.

        Returns:
            Human-readable description of what the tool does
        """
        pass

    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Get tool category.

        Returns:
            Tool category for organization
        """
        pass

    @property
    @abstractmethod
    def requires_wallet(self) -> bool:
        """Check if tool requires an active wallet.

        Returns:
            True if wallet is required, False otherwise
        """
        pass

    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate tool parameters.

        Args:
            params: Tool parameters to validate

        Raises:
            ValidationError: If parameters are invalid
        """
        pass

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool logic.

        Args:
            params: Validated tool parameters

        Returns:
            Tool execution result

        Raises:
            SecretMCPError: If execution fails
        """
        pass

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run the tool with error handling.

        This method orchestrates the complete tool execution:
        1. Check wallet requirement
        2. Validate parameters
        3. Execute tool logic
        4. Format response

        Args:
            params: Tool parameters

        Returns:
            Standardized tool response with success/error status
        """
        try:
            self._logger.debug("Tool execution started", tool=self.name, params=params)

            # Check if wallet is required
            if self.requires_wallet:
                if not self.context.session.has_wallet():
                    error_msg = (
                        f"Tool '{self.name}' requires an active wallet. "
                        "Please import or create a wallet first."
                    )
                    self._logger.error("No active wallet", tool=self.name)
                    return {
                        "success": False,
                        "error": {
                            "code": "WAL001",
                            "message": error_msg,
                            "details": {"tool": self.name, "requires_wallet": True},
                            "suggestions": [
                                "Use 'create_wallet' to create a new wallet",
                                "Use 'import_wallet' to import an existing wallet",
                            ],
                        },
                    }

            # Validate parameters
            self.validate_params(params)

            # Execute tool logic
            result = await self.execute(params)

            self._logger.info("Tool execution completed successfully", tool=self.name)

            return {
                "success": True,
                "data": result,
                "metadata": {
                    "tool": self.name,
                    "category": self.category.value,
                },
            }

        except ValidationError as e:
            self._logger.error(
                "Validation error",
                tool=self.name,
                error=str(e),
            )
            return {
                "success": False,
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details or {},
                    "suggestions": e.suggestions or [],
                },
            }

        except SecretMCPError as e:
            self._logger.error(
                "Tool execution error",
                tool=self.name,
                error=str(e),
            )
            return {
                "success": False,
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details or {},
                    "suggestions": e.suggestions or [],
                },
            }

        except Exception as e:
            self._logger.error(
                "Unexpected error",
                tool=self.name,
                error=str(e),
                traceback=traceback.format_exc(),
            )
            return {
                "success": False,
                "error": {
                    "code": "ERR001",
                    "message": f"Unexpected error: {str(e)}",
                    "details": {
                        "tool": self.name,
                        "error_type": type(e).__name__,
                    },
                    "suggestions": [
                        "Check the error details",
                        "Verify your parameters are correct",
                        "Try again or contact support if the issue persists",
                    ],
                },
            }

    def get_metadata(self) -> Dict[str, Any]:
        """Get tool metadata.

        Returns:
            Dictionary containing tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "requires_wallet": self.requires_wallet,
        }
