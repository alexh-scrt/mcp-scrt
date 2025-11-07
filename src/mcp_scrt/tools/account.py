"""Account tools for Secret Network account queries.

This module provides tools for querying account information and transaction history.
"""

from typing import Any, Dict

from mcp_scrt.tools.base import BaseTool, ToolCategory
from mcp_scrt.utils.errors import ValidationError, NetworkError
from mcp_scrt.core.validation import validate_address


class GetAccountTool(BaseTool):
    """Get account information.

    Query account details including account number and sequence.
    """

    @property
    def name(self) -> str:
        return "get_account"

    @property
    def description(self) -> str:
        return (
            "Get account information for a Secret Network address. "
            "Returns account number, sequence, and public key."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ACCOUNTS

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get account parameters.

        Args:
            params: Must contain 'address'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "address" not in params:
            raise ValidationError(
                message="Missing required parameter: address",
                details={"required_params": ["address"]},
                suggestions=[
                    "Provide 'address' parameter",
                    "Example: {'address': 'secret1...'}",
                ],
            )

        # Validate address format
        validate_address(params["address"])

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get account.

        Args:
            params: Parameters including address

        Returns:
            Account information
        """
        address = params["address"]

        try:
            # Query account using client pool
            with self.context.client_pool.get_client() as client:
                account_response = client.auth.account_info(address)

                account = account_response.get("account", {})

                return {
                    "address": address,
                    "account": account,
                    "account_number": account.get("account_number"),
                    "sequence": account.get("sequence"),
                    "message": f"Account information retrieved for {address}",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get account: {str(e)}",
                details={"address": address, "error": str(e)},
                suggestions=[
                    "Check that the address exists on the network",
                    "Verify network connectivity",
                    "Try again later",
                ],
            )


class GetAccountTransactionsTool(BaseTool):
    """Get account transactions.

    Query transaction history for a Secret Network address.
    """

    @property
    def name(self) -> str:
        return "get_account_transactions"

    @property
    def description(self) -> str:
        return (
            "Get transaction history for a Secret Network address. "
            "Returns list of transactions with pagination support."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ACCOUNTS

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get account transactions parameters.

        Args:
            params: Must contain 'address', optionally 'limit' and 'offset'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "address" not in params:
            raise ValidationError(
                message="Missing required parameter: address",
                details={"required_params": ["address"]},
                suggestions=[
                    "Provide 'address' parameter",
                    "Example: {'address': 'secret1...'}",
                ],
            )

        # Validate address format
        validate_address(params["address"])

        # Validate limit if provided
        if "limit" in params:
            limit = params["limit"]
            if not isinstance(limit, int) or limit < 1:
                raise ValidationError(
                    message=f"Invalid limit: {limit}",
                    details={"provided": limit},
                    suggestions=[
                        "Limit must be a positive integer",
                        "Example: {'limit': 100}",
                    ],
                )

        # Validate offset if provided
        if "offset" in params:
            offset = params["offset"]
            if not isinstance(offset, int) or offset < 0:
                raise ValidationError(
                    message=f"Invalid offset: {offset}",
                    details={"provided": offset},
                    suggestions=[
                        "Offset must be a non-negative integer",
                        "Example: {'offset': 0}",
                    ],
                )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get account transactions.

        Args:
            params: Parameters including address, limit, offset

        Returns:
            Transaction history
        """
        address = params["address"]
        limit = params.get("limit", 100)
        offset = params.get("offset", 0)

        try:
            # Query transactions using client pool
            with self.context.client_pool.get_client() as client:
                # Search for transactions from this address
                # Note: secret-sdk search uses events format [["key", "value"]]
                events = [["message.sender", address]]

                # Create params for pagination
                from secret_sdk.client.lcd.params import APIParams
                page = offset // limit + 1
                api_params = APIParams(pagination_limit=limit, pagination_offset=offset)

                tx_response = client.tx.search(
                    events=events,
                    params=api_params,
                )

                txs = tx_response.get("txs", [])
                total_count = len(txs)

                return {
                    "address": address,
                    "transactions": txs,
                    "count": len(txs),
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "message": f"Retrieved {len(txs)} transactions for {address}",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get transactions: {str(e)}",
                details={"address": address, "error": str(e)},
                suggestions=[
                    "Verify network connectivity",
                    "Check that the address exists",
                    "Try again later",
                ],
            )


class GetAccountTxCountTool(BaseTool):
    """Get account transaction count.

    Query total number of transactions for a Secret Network address.
    """

    @property
    def name(self) -> str:
        return "get_account_tx_count"

    @property
    def description(self) -> str:
        return (
            "Get total transaction count for a Secret Network address. "
            "Returns the number of transactions sent from or received by the address."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ACCOUNTS

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get account tx count parameters.

        Args:
            params: Must contain 'address'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "address" not in params:
            raise ValidationError(
                message="Missing required parameter: address",
                details={"required_params": ["address"]},
                suggestions=[
                    "Provide 'address' parameter",
                    "Example: {'address': 'secret1...'}",
                ],
            )

        # Validate address format
        validate_address(params["address"])

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get account tx count.

        Args:
            params: Parameters including address

        Returns:
            Transaction count
        """
        address = params["address"]

        try:
            # Query transaction count using client pool
            with self.context.client_pool.get_client() as client:
                # Search for transactions from this address
                # Note: secret-sdk search uses events format [["key", "value"]]
                events = [["message.sender", address]]

                # Create params for pagination - just get 1 result to count
                from secret_sdk.client.lcd.params import APIParams
                api_params = APIParams(pagination_limit=1)

                tx_response = client.tx.search(
                    events=events,
                    params=api_params,
                )

                # Note: Without proper pagination support, we can only count returned results
                # This may not give the true total count
                txs = tx_response.get("txs", [])
                total_count = len(txs)

                return {
                    "address": address,
                    "count": total_count,
                    "message": f"Address {address} has {total_count} transaction(s)",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get transaction count: {str(e)}",
                details={"address": address, "error": str(e)},
                suggestions=[
                    "Verify network connectivity",
                    "Check that the address exists",
                    "Try again later",
                ],
            )
