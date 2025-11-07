"""Blockchain tools for Secret Network blockchain queries.

This module provides tools for querying blockchain state, blocks, and node information.
"""

from typing import Any, Dict

from mcp_scrt.tools.base import BaseTool, ToolCategory
from mcp_scrt.utils.errors import ValidationError, NetworkError


class GetBlockTool(BaseTool):
    """Get block by height.

    Query blockchain block at a specific height.
    """

    @property
    def name(self) -> str:
        return "get_block"

    @property
    def description(self) -> str:
        return (
            "Get block information by height. "
            "Returns block header, transactions, and metadata."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BLOCKCHAIN

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get block parameters.

        Args:
            params: Must contain 'height' (positive integer)

        Raises:
            ValidationError: If parameters are invalid
        """
        if "height" not in params:
            raise ValidationError(
                message="Missing required parameter: height",
                details={"required_params": ["height"]},
                suggestions=[
                    "Provide 'height' parameter",
                    "Example: {'height': 12345}",
                ],
            )

        # Validate height is a positive integer
        height = params["height"]
        if not isinstance(height, int) or height < 0:
            raise ValidationError(
                message=f"Invalid height: {height}",
                details={"provided": height},
                suggestions=[
                    "Height must be a non-negative integer",
                    "Example: {'height': 12345}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get block.

        Args:
            params: Parameters including height

        Returns:
            Block information
        """
        height = params["height"]

        try:
            # Query block using client pool
            with self.context.client_pool.get_client() as client:
                block_response = client.tendermint.block(height=height)

                return {
                    "height": height,
                    "block": block_response.get("block", {}),
                    "message": f"Block {height} retrieved successfully",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get block: {str(e)}",
                details={"height": height, "error": str(e)},
                suggestions=[
                    "Check that the height exists on the blockchain",
                    "Verify network connectivity",
                    "Try again later",
                ],
            )


class GetLatestBlockTool(BaseTool):
    """Get latest block.

    Query the most recent blockchain block.
    """

    @property
    def name(self) -> str:
        return "get_latest_block"

    @property
    def description(self) -> str:
        return (
            "Get the latest (current) block on the blockchain. "
            "Returns the most recent block header, transactions, and metadata."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BLOCKCHAIN

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters (no parameters required)."""
        # No parameters needed
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get latest block.

        Returns:
            Latest block information
        """
        try:
            # Query latest block using client pool
            with self.context.client_pool.get_client() as client:
                block_response = client.tendermint.block_info()

                block = block_response.get("block", {})
                header = block.get("header", {})
                height = header.get("height", "unknown")

                return {
                    "block": block,
                    "height": height,
                    "message": f"Latest block retrieved (height: {height})",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get latest block: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Verify network connectivity",
                    "Check that the node is synced",
                    "Try again later",
                ],
            )


class GetBlockByHashTool(BaseTool):
    """Get block by hash.

    Query blockchain block by its hash.
    """

    @property
    def name(self) -> str:
        return "get_block_by_hash"

    @property
    def description(self) -> str:
        return (
            "Get block information by block hash. "
            "Returns block header, transactions, and metadata."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BLOCKCHAIN

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get block by hash parameters.

        Args:
            params: Must contain 'hash'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "hash" not in params:
            raise ValidationError(
                message="Missing required parameter: hash",
                details={"required_params": ["hash"]},
                suggestions=[
                    "Provide 'hash' parameter",
                    "Example: {'hash': 'ABCDEF1234567890'}",
                ],
            )

        # Validate hash is a non-empty string
        block_hash = params["hash"]
        if not isinstance(block_hash, str) or not block_hash:
            raise ValidationError(
                message="Invalid hash: must be a non-empty string",
                details={"provided": block_hash},
                suggestions=[
                    "Provide a valid block hash as a string",
                    "Example: {'hash': 'ABCDEF1234567890'}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get block by hash.

        Args:
            params: Parameters including hash

        Returns:
            Block information
        """
        block_hash = params["hash"]

        try:
            # Query block by hash using client pool
            with self.context.client_pool.get_client() as client:
                block_response = client.tendermint.block_by_hash(hash=block_hash)

                block = block_response.get("block", {})
                header = block.get("header", {})
                height = header.get("height", "unknown")

                return {
                    "hash": block_hash,
                    "block": block,
                    "height": height,
                    "message": f"Block retrieved (hash: {block_hash[:8]}..., height: {height})",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get block by hash: {str(e)}",
                details={"hash": block_hash, "error": str(e)},
                suggestions=[
                    "Check that the hash exists on the blockchain",
                    "Verify the hash format is correct",
                    "Verify network connectivity",
                    "Try again later",
                ],
            )


class GetNodeInfoTool(BaseTool):
    """Get node information.

    Query information about the connected blockchain node.
    """

    @property
    def name(self) -> str:
        return "get_node_info"

    @property
    def description(self) -> str:
        return (
            "Get information about the connected blockchain node. "
            "Returns node ID, network, version, and protocol information."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BLOCKCHAIN

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters (no parameters required)."""
        # No parameters needed
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get node info.

        Returns:
            Node information
        """
        try:
            # Query node info using client pool
            with self.context.client_pool.get_client() as client:
                info_response = client.tendermint.node_info()

                node_info = info_response.get("node_info", {})
                network = node_info.get("network", "unknown")
                version = node_info.get("version", "unknown")

                return {
                    "node_info": node_info,
                    "network": network,
                    "version": version,
                    "message": f"Node info retrieved (network: {network}, version: {version})",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get node info: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Verify network connectivity",
                    "Check that the LCD endpoint is accessible",
                    "Try again later",
                ],
            )


class GetSyncingStatusTool(BaseTool):
    """Get node syncing status.

    Query whether the node is currently syncing with the network.
    """

    @property
    def name(self) -> str:
        return "get_syncing_status"

    @property
    def description(self) -> str:
        return (
            "Get the syncing status of the connected node. "
            "Returns whether the node is currently syncing or fully synced."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BLOCKCHAIN

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters (no parameters required)."""
        # No parameters needed
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get syncing status.

        Returns:
            Syncing status
        """
        try:
            # Query syncing status using client pool
            with self.context.client_pool.get_client() as client:
                sync_response = client.tendermint.syncing()

                syncing = sync_response.get("syncing", False)
                status = "syncing" if syncing else "synced"

                return {
                    "syncing": syncing,
                    "status": status,
                    "message": f"Node is {status}",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get syncing status: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Verify network connectivity",
                    "Check that the LCD endpoint is accessible",
                    "Try again later",
                ],
            )
