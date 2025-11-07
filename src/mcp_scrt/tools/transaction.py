"""Transaction tools for Secret Network transaction operations.

This module provides tools for querying, searching, and simulating transactions.
"""

from typing import Any, Dict, List

from mcp_scrt.tools.base import BaseTool, ToolCategory
from mcp_scrt.utils.errors import ValidationError, NetworkError


class GetTransactionTool(BaseTool):
    """Get transaction by hash.

    Query transaction details using its hash.
    """

    @property
    def name(self) -> str:
        return "get_transaction"

    @property
    def description(self) -> str:
        return (
            "Get transaction details by transaction hash. "
            "Returns complete transaction information including result and logs."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.TRANSACTIONS

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get transaction parameters.

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
                    "Example: {'hash': 'ABC123...'}",
                ],
            )

        # Validate hash is a non-empty string
        tx_hash = params["hash"]
        if not isinstance(tx_hash, str) or not tx_hash:
            raise ValidationError(
                message="Invalid hash: must be a non-empty string",
                details={"provided": tx_hash},
                suggestions=[
                    "Provide a valid transaction hash",
                    "Example: {'hash': 'ABC123...'}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get transaction.

        Args:
            params: Parameters including hash

        Returns:
            Transaction details
        """
        tx_hash = params["hash"]

        try:
            # Query transaction using client pool
            with self.context.client_pool.get_client() as client:
                tx_response = client.tx.get_tx(hash=tx_hash)

                tx_data = tx_response.get("tx_response", {})

                return {
                    "hash": tx_hash,
                    "transaction": tx_data,
                    "height": tx_data.get("height"),
                    "code": tx_data.get("code"),
                    "message": f"Transaction {tx_hash[:8]}... retrieved successfully",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get transaction: {str(e)}",
                details={"hash": tx_hash, "error": str(e)},
                suggestions=[
                    "Check that the transaction hash is correct",
                    "Verify the transaction exists on the network",
                    "Verify network connectivity",
                    "Try again later",
                ],
            )


class SearchTransactionsTool(BaseTool):
    """Search transactions by criteria.

    Search for transactions using query parameters.
    """

    @property
    def name(self) -> str:
        return "search_transactions"

    @property
    def description(self) -> str:
        return (
            "Search for transactions using query criteria. "
            "Supports filtering by message type, sender, recipient, and more."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.TRANSACTIONS

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate search transactions parameters.

        Args:
            params: Must contain 'query', optionally 'limit' and 'page'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "query" not in params:
            raise ValidationError(
                message="Missing required parameter: query",
                details={"required_params": ["query"]},
                suggestions=[
                    "Provide 'query' parameter",
                    "Example: {'query': \"message.action='/cosmos.bank.v1beta1.MsgSend'\"}",
                ],
            )

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

        # Validate page if provided
        if "page" in params:
            page = params["page"]
            if not isinstance(page, int) or page < 1:
                raise ValidationError(
                    message=f"Invalid page: {page}",
                    details={"provided": page},
                    suggestions=[
                        "Page must be a positive integer",
                        "Example: {'page': 1}",
                    ],
                )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search transactions.

        Args:
            params: Parameters including query, limit, page

        Returns:
            Search results
        """
        query = params["query"]
        limit = params.get("limit", 100)
        page = params.get("page", 1)

        try:
            # Search transactions using client pool
            with self.context.client_pool.get_client() as client:
                search_response = client.tx.search(
                    query=query,
                    page=page,
                    limit=limit,
                )

                txs = search_response.get("txs", [])
                total_count = int(search_response.get("total_count", 0))

                return {
                    "query": query,
                    "transactions": txs,
                    "count": len(txs),
                    "total_count": total_count,
                    "page": page,
                    "limit": limit,
                    "message": f"Found {total_count} transaction(s) matching query",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to search transactions: {str(e)}",
                details={"query": query, "error": str(e)},
                suggestions=[
                    "Check that the query syntax is correct",
                    "Verify network connectivity",
                    "Try again later",
                ],
            )


class EstimateGasTool(BaseTool):
    """Estimate gas for transaction.

    Estimate the gas required for a transaction.
    """

    @property
    def name(self) -> str:
        return "estimate_gas"

    @property
    def description(self) -> str:
        return (
            "Estimate gas required for a transaction. "
            "Returns estimated gas units needed."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.TRANSACTIONS

    @property
    def requires_wallet(self) -> bool:
        return False  # Estimation doesn't require wallet

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate estimate gas parameters.

        Args:
            params: Must contain 'messages'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "messages" not in params:
            raise ValidationError(
                message="Missing required parameter: messages",
                details={"required_params": ["messages"]},
                suggestions=[
                    "Provide 'messages' parameter as a list",
                    "Example: {'messages': [{'type': 'MsgSend', ...}]}",
                ],
            )

        messages = params["messages"]
        if not isinstance(messages, list) or len(messages) == 0:
            raise ValidationError(
                message="Messages must be a non-empty list",
                details={"provided_type": type(messages).__name__},
                suggestions=[
                    "Provide at least one message",
                    "Example: {'messages': [{'type': 'MsgSend'}]}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute estimate gas.

        Args:
            params: Parameters including messages

        Returns:
            Gas estimation
        """
        messages = params["messages"]

        # For now, provide a simple gas estimation
        # In a full implementation, this would simulate the transaction
        base_gas = 100000
        per_message_gas = 50000
        estimated_gas = base_gas + (len(messages) * per_message_gas)

        return {
            "messages_count": len(messages),
            "gas_estimate": estimated_gas,
            "message": f"Estimated gas: {estimated_gas} units for {len(messages)} message(s)",
            "note": "This is a simplified estimation. For accurate gas estimation, use simulate_transaction.",
        }


class SimulateTransactionTool(BaseTool):
    """Simulate transaction execution.

    Simulate a transaction to check if it will succeed and estimate gas.
    """

    @property
    def name(self) -> str:
        return "simulate_transaction"

    @property
    def description(self) -> str:
        return (
            "Simulate transaction execution without broadcasting. "
            "Returns simulation result, gas used, and logs."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.TRANSACTIONS

    @property
    def requires_wallet(self) -> bool:
        return False  # Simulation doesn't require wallet

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate simulate transaction parameters.

        Args:
            params: Must contain 'messages'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "messages" not in params:
            raise ValidationError(
                message="Missing required parameter: messages",
                details={"required_params": ["messages"]},
                suggestions=[
                    "Provide 'messages' parameter as a list",
                    "Example: {'messages': [{'type': 'MsgSend', ...}]}",
                ],
            )

        messages = params["messages"]
        if not isinstance(messages, list) or len(messages) == 0:
            raise ValidationError(
                message="Messages must be a non-empty list",
                details={"provided_type": type(messages).__name__},
                suggestions=[
                    "Provide at least one message",
                    "Example: {'messages': [{'type': 'MsgSend'}]}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute simulate transaction.

        Args:
            params: Parameters including messages

        Returns:
            Simulation result
        """
        messages = params["messages"]

        # For now, provide a mock simulation result
        # In a full implementation, this would use the LCD client to simulate
        base_gas = 100000
        per_message_gas = 50000
        gas_used = base_gas + (len(messages) * per_message_gas)

        return {
            "simulation": {
                "success": True,
                "gas_used": gas_used,
                "gas_wanted": int(gas_used * 1.2),  # Add 20% buffer
                "logs": [],
            },
            "messages_count": len(messages),
            "message": "Transaction simulation successful",
            "note": "This is a test implementation. Real simulation requires full SDK integration.",
        }


class GetTransactionStatusTool(BaseTool):
    """Get transaction status.

    Query the status of a transaction (success/failure/pending).
    """

    @property
    def name(self) -> str:
        return "get_transaction_status"

    @property
    def description(self) -> str:
        return (
            "Get the status of a transaction by hash. "
            "Returns whether the transaction succeeded, failed, or is pending."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.TRANSACTIONS

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get transaction status parameters.

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
                    "Example: {'hash': 'ABC123...'}",
                ],
            )

        # Validate hash is a non-empty string
        tx_hash = params["hash"]
        if not isinstance(tx_hash, str) or not tx_hash:
            raise ValidationError(
                message="Invalid hash: must be a non-empty string",
                details={"provided": tx_hash},
                suggestions=[
                    "Provide a valid transaction hash",
                    "Example: {'hash': 'ABC123...'}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get transaction status.

        Args:
            params: Parameters including hash

        Returns:
            Transaction status
        """
        tx_hash = params["hash"]

        try:
            # Query transaction using client pool
            with self.context.client_pool.get_client() as client:
                tx_response = client.tx.get_tx(hash=tx_hash)

                tx_data = tx_response.get("tx_response", {})
                code = tx_data.get("code", 0)
                height = tx_data.get("height")

                # Determine status based on code
                if code == 0:
                    status = "success"
                    status_message = "Transaction executed successfully"
                else:
                    status = "failed"
                    status_message = f"Transaction failed with code {code}"

                return {
                    "hash": tx_hash,
                    "status": status,
                    "code": code,
                    "height": height,
                    "message": status_message,
                }

        except Exception as e:
            # If transaction not found, it might be pending or invalid
            error_msg = str(e).lower()
            if "not found" in error_msg or "does not exist" in error_msg:
                return {
                    "hash": tx_hash,
                    "status": "not_found",
                    "message": "Transaction not found. It may be pending or the hash is invalid.",
                }

            raise NetworkError(
                message=f"Failed to get transaction status: {str(e)}",
                details={"hash": tx_hash, "error": str(e)},
                suggestions=[
                    "Check that the transaction hash is correct",
                    "Verify network connectivity",
                    "Try again later",
                ],
            )
