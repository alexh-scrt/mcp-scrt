"""IBC (Inter-Blockchain Communication) tools for Secret Network.

This module provides tools for IBC operations including:
- IBC transfers
- IBC channel queries
- IBC denom trace queries
"""

from typing import Any, Dict

from mcp_scrt.tools.base import BaseTool, ToolCategory
from mcp_scrt.utils.errors import ValidationError, NetworkError, WalletError


# Helper function to create a signing client (placeholder for now)
async def create_signing_client(wallet_name: str, network: str):
    """Create a signing client for wallet operations.

    This is a placeholder that will be replaced with actual signing client implementation.
    """
    # This will be implemented with actual Secret Network signing client
    class MockSigningClient:
        async def ibc_transfer(
            self,
            channel_id: str,
            recipient: str,
            amount: Dict[str, str],
            timeout_height: str = None,
            timeout_timestamp: str = None,
            memo: str = "",
        ):
            return {"txhash": "mock_hash", "code": 0}

    return MockSigningClient()


class IBCTransferTool(BaseTool):
    """Transfer tokens via IBC.

    Performs cross-chain token transfers using the IBC protocol.
    """

    @property
    def name(self) -> str:
        return "ibc_transfer"

    @property
    def description(self) -> str:
        return (
            "Transfer tokens to another blockchain via IBC. "
            "Requires active wallet. Specify channel ID, recipient address, and amount."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.IBC

    @property
    def requires_wallet(self) -> bool:
        return True

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate IBC transfer parameters.

        Args:
            params: Tool parameters

        Raises:
            ValidationError: If parameters are invalid
        """
        if "channel_id" not in params:
            raise ValidationError(
                message="Missing required parameter: channel_id",
                details={"required_params": ["channel_id", "recipient", "amount"]},
                suggestions=[
                    "Provide 'channel_id' parameter",
                    "Example: {'channel_id': 'channel-0', 'recipient': 'cosmos1...', 'amount': '1000000'}",
                ],
            )

        if "recipient" not in params:
            raise ValidationError(
                message="Missing required parameter: recipient",
                details={"required_params": ["channel_id", "recipient", "amount"]},
                suggestions=[
                    "Provide 'recipient' parameter",
                    "Example: {'channel_id': 'channel-0', 'recipient': 'cosmos1...', 'amount': '1000000'}",
                ],
            )

        if "amount" not in params:
            raise ValidationError(
                message="Missing required parameter: amount",
                details={"required_params": ["channel_id", "recipient", "amount"]},
                suggestions=[
                    "Provide 'amount' parameter",
                    "Example: {'channel_id': 'channel-0', 'recipient': 'cosmos1...', 'amount': '1000000'}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute IBC transfer.

        Args:
            params: Tool parameters

        Returns:
            Transfer result with transaction hash

        Raises:
            WalletError: If no wallet is available
            NetworkError: If transfer fails
        """
        channel_id = params["channel_id"]
        recipient = params["recipient"]
        amount = params["amount"]
        denom = params.get("denom", "uscrt")
        timeout_height = params.get("timeout_height")
        timeout_timestamp = params.get("timeout_timestamp")
        memo = params.get("memo", "")

        # Get active wallet
        wallet_info = self.context.session.get_wallet()
        if not wallet_info:
            raise WalletError(
                message="No active wallet set",
                details={},
                suggestions=["Load a wallet using load_wallet"],
            )

        wallet_name = wallet_info.wallet_id
        sender = wallet_info.address

        try:
            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            # Prepare IBC transfer parameters
            transfer_params: Dict[str, Any] = {
                "channel_id": channel_id,
                "recipient": recipient,
                "amount": {"denom": denom, "amount": amount},
            }

            if timeout_height:
                transfer_params["timeout_height"] = timeout_height

            if timeout_timestamp:
                transfer_params["timeout_timestamp"] = timeout_timestamp

            if memo:
                transfer_params["memo"] = memo

            # Execute IBC transfer
            result = await signing_client.ibc_transfer(**transfer_params)

            return {
                "sender": sender,
                "recipient": recipient,
                "channel_id": channel_id,
                "amount": amount,
                "denom": denom,
                "txhash": result.get("txhash"),
                "message": f"Successfully transferred {amount} {denom} to {recipient} via {channel_id}",
            }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to execute IBC transfer: {str(e)}",
                details={
                    "sender": sender,
                    "recipient": recipient,
                    "channel_id": channel_id,
                    "amount": amount,
                    "error": str(e),
                },
                suggestions=[
                    "Verify the channel ID is correct and active",
                    "Ensure the recipient address is valid for the destination chain",
                    "Check that you have sufficient balance",
                    "Verify network connectivity",
                ],
            )


class GetIBCChannelsTool(BaseTool):
    """Get all IBC channels.

    Query all IBC channels on the network.
    """

    @property
    def name(self) -> str:
        return "get_ibc_channels"

    @property
    def description(self) -> str:
        return (
            "Get all IBC channels on the network. "
            "Returns list of channels with their states and counterparties."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.IBC

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters.

        Args:
            params: Tool parameters
        """
        # No required parameters - all are optional
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get IBC channels.

        Args:
            params: Tool parameters

        Returns:
            List of IBC channels

        Raises:
            NetworkError: If query fails
        """
        pagination_limit = params.get("pagination_limit")
        pagination_offset = params.get("pagination_offset")
        pagination_key = params.get("pagination_key")

        try:
            with self.context.client_pool.get_client() as client:
                # Prepare query parameters
                query_params: Dict[str, Any] = {}

                if pagination_limit:
                    query_params["pagination_limit"] = pagination_limit

                if pagination_offset:
                    query_params["pagination_offset"] = pagination_offset

                if pagination_key:
                    query_params["pagination_key"] = pagination_key

                # Query IBC channels
                response = await client.ibc.channels(**query_params)

                channels = response.get("channels", [])
                pagination = response.get("pagination", {})

                return {
                    "channels": channels,
                    "pagination": pagination,
                    "count": len(channels),
                    "message": f"Found {len(channels)} IBC channel(s)",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to query IBC channels: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Verify network connectivity",
                    "Ensure the node supports IBC queries",
                ],
            )


class GetIBCChannelTool(BaseTool):
    """Get specific IBC channel.

    Query details of a specific IBC channel.
    """

    @property
    def name(self) -> str:
        return "get_ibc_channel"

    @property
    def description(self) -> str:
        return (
            "Get a specific IBC channel by ID. "
            "Returns channel details including state, counterparty, and connection info."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.IBC

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get IBC channel parameters.

        Args:
            params: Tool parameters

        Raises:
            ValidationError: If parameters are invalid
        """
        if "channel_id" not in params:
            raise ValidationError(
                message="Missing required parameter: channel_id",
                details={"required_params": ["channel_id"]},
                suggestions=[
                    "Provide 'channel_id' parameter",
                    "Example: {'channel_id': 'channel-0'}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get IBC channel.

        Args:
            params: Tool parameters

        Returns:
            IBC channel details

        Raises:
            NetworkError: If query fails
        """
        channel_id = params["channel_id"]
        port_id = params.get("port_id", "transfer")

        try:
            with self.context.client_pool.get_client() as client:
                # Query IBC channel
                response = await client.ibc.channel(
                    channel_id=channel_id,
                    port_id=port_id,
                )

                channel = response.get("channel", {})

                return {
                    "channel": channel,
                    "channel_id": channel_id,
                    "port_id": port_id,
                    "message": f"Retrieved IBC channel {channel_id}",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to query IBC channel: {str(e)}",
                details={
                    "channel_id": channel_id,
                    "port_id": port_id,
                    "error": str(e),
                },
                suggestions=[
                    "Verify the channel ID is correct",
                    "Check that the port ID is correct (default: 'transfer')",
                    "Verify network connectivity",
                ],
            )


class GetIBCDenomTraceTool(BaseTool):
    """Get IBC denom trace.

    Query the origin information of an IBC denomination.
    """

    @property
    def name(self) -> str:
        return "get_ibc_denom_trace"

    @property
    def description(self) -> str:
        return (
            "Get the trace of an IBC denomination. "
            "Returns the path and base denomination for an IBC token hash."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.IBC

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get IBC denom trace parameters.

        Args:
            params: Tool parameters

        Raises:
            ValidationError: If parameters are invalid
        """
        if "hash" not in params:
            raise ValidationError(
                message="Missing required parameter: hash",
                details={"required_params": ["hash"]},
                suggestions=[
                    "Provide 'hash' parameter",
                    "Example: {'hash': '27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2'}",
                    "The hash is the SHA256 of the IBC denomination path",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get IBC denom trace.

        Args:
            params: Tool parameters

        Returns:
            IBC denom trace information

        Raises:
            NetworkError: If query fails
        """
        denom_hash = params["hash"]

        try:
            with self.context.client_pool.get_client() as client:
                # Query IBC denom trace
                response = await client.ibc.denom_trace(hash=denom_hash)

                denom_trace = response.get("denom_trace", {})
                path = denom_trace.get("path", "")
                base_denom = denom_trace.get("base_denom", "")

                return {
                    "denom_trace": denom_trace,
                    "hash": denom_hash,
                    "path": path,
                    "base_denom": base_denom,
                    "message": f"Retrieved denom trace for hash {denom_hash}",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to query IBC denom trace: {str(e)}",
                details={
                    "hash": denom_hash,
                    "error": str(e),
                },
                suggestions=[
                    "Verify the hash is correct",
                    "Ensure the denomination exists on this chain",
                    "Verify network connectivity",
                ],
            )
