"""Bank tools for Secret Network token operations.

This module provides tools for querying balances, sending tokens, and managing denominations.
"""

from typing import Any, Dict, List

from mcp_scrt.tools.base import BaseTool, ToolCategory
from mcp_scrt.utils.errors import ValidationError, NetworkError
from mcp_scrt.core.validation import validate_address, validate_amount


class GetBalanceTool(BaseTool):
    """Get account token balance.

    Query the balance of any Secret Network address.
    """

    @property
    def name(self) -> str:
        return "get_balance"

    @property
    def description(self) -> str:
        return (
            "Get token balance for a Secret Network address. "
            "Returns all token denominations and amounts."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BANK

    @property
    def requires_wallet(self) -> bool:
        return False  # Can query any address

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get balance parameters.

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
        """Execute get balance.

        Args:
            params: Parameters including address

        Returns:
            Account balance information
        """
        address = params["address"]

        try:
            # Query balance using client pool
            with self.context.client_pool.get_client() as client:
                # Note: The actual secret-sdk client method may differ
                # This is a placeholder for the real implementation
                balance_response = await client.bank.balance(address)

                return {
                    "address": address,
                    "balances": balance_response.get("balances", []),
                    "message": f"Balance retrieved for {address}",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get balance: {str(e)}",
                details={"address": address, "error": str(e)},
                suggestions=[
                    "Check network connectivity",
                    "Verify the address exists on the network",
                    "Try again later",
                ],
            )


class SendTokensTool(BaseTool):
    """Send tokens to another address.

    Transfer tokens from the active wallet to a recipient address.
    """

    @property
    def name(self) -> str:
        return "send_tokens"

    @property
    def description(self) -> str:
        return (
            "Send tokens from the active wallet to a recipient address. "
            "Requires an active wallet for signing the transaction."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BANK

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet for signing

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate send tokens parameters.

        Args:
            params: Must contain 'to_address', 'amount', 'denom'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "to_address" not in params:
            raise ValidationError(
                message="Missing required parameter: to_address",
                details={"required_params": ["to_address", "amount", "denom"]},
                suggestions=[
                    "Provide recipient address",
                    "Example: {'to_address': 'secret1...', 'amount': '1000000', 'denom': 'uscrt'}",
                ],
            )

        if "amount" not in params:
            raise ValidationError(
                message="Missing required parameter: amount",
                details={"required_params": ["to_address", "amount", "denom"]},
                suggestions=[
                    "Provide amount to send",
                    "Amount should be in base denomination (e.g., uscrt)",
                ],
            )

        if "denom" not in params:
            raise ValidationError(
                message="Missing required parameter: denom",
                details={"required_params": ["to_address", "amount", "denom"]},
                suggestions=[
                    "Provide token denomination",
                    "Example: 'uscrt' for Secret Network native token",
                ],
            )

        # Validate address
        validate_address(params["to_address"])

        # Validate amount
        try:
            amount = int(params["amount"])
            validate_amount(amount, field_name="amount")
        except (ValueError, TypeError):
            raise ValidationError(
                message=f"Invalid amount: {params['amount']}",
                details={"provided": params["amount"]},
                suggestions=[
                    "Amount must be a positive integer",
                    "Use base denomination (e.g., 1000000 uscrt = 1 SCRT)",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute send tokens.

        Args:
            params: Send parameters

        Returns:
            Transaction result
        """
        to_address = params["to_address"]
        amount = params["amount"]
        denom = params["denom"]
        memo = params.get("memo", "")

        wallet_info = self.context.session.get_wallet()

        return {
            "from_address": wallet_info.address,
            "to_address": to_address,
            "amount": amount,
            "denom": denom,
            "memo": memo,
            "status": "pending",
            "message": "Transaction prepared (Note: Blockchain execution not implemented in test mode)",
            "warning": "This is a test implementation. Real blockchain execution requires full SDK integration.",
        }


class MultiSendTool(BaseTool):
    """Send tokens to multiple addresses.

    Transfer tokens from the active wallet to multiple recipients in a single transaction.
    """

    @property
    def name(self) -> str:
        return "multi_send"

    @property
    def description(self) -> str:
        return (
            "Send tokens to multiple recipients in a single transaction. "
            "Requires an active wallet for signing."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BANK

    @property
    def requires_wallet(self) -> bool:
        return True

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate multi send parameters.

        Args:
            params: Must contain 'recipients' list

        Raises:
            ValidationError: If parameters are invalid
        """
        if "recipients" not in params:
            raise ValidationError(
                message="Missing required parameter: recipients",
                details={"required_params": ["recipients"]},
                suggestions=[
                    "Provide list of recipients",
                    "Example: {'recipients': [{'address': 'secret1...', 'amount': '1000000', 'denom': 'uscrt'}]}",
                ],
            )

        recipients = params["recipients"]

        if not isinstance(recipients, list) or len(recipients) == 0:
            raise ValidationError(
                message="Recipients must be a non-empty list",
                details={"provided_type": type(recipients).__name__},
                suggestions=[
                    "Provide at least one recipient",
                    "Each recipient must have address, amount, and denom",
                ],
            )

        # Validate each recipient
        for i, recipient in enumerate(recipients):
            if not isinstance(recipient, dict):
                raise ValidationError(
                    message=f"Recipient {i} must be a dictionary",
                    details={"recipient_index": i},
                    suggestions=["Each recipient must have address, amount, and denom fields"],
                )

            if "address" not in recipient:
                raise ValidationError(
                    message=f"Recipient {i} missing address",
                    details={"recipient_index": i},
                    suggestions=["Each recipient must have an address field"],
                )

            if "amount" not in recipient:
                raise ValidationError(
                    message=f"Recipient {i} missing amount",
                    details={"recipient_index": i},
                    suggestions=["Each recipient must have an amount field"],
                )

            # Validate address and amount
            validate_address(recipient["address"])
            validate_amount(int(recipient["amount"]), field_name=f"recipient[{i}].amount")

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multi send.

        Args:
            params: Multi send parameters

        Returns:
            Transaction result
        """
        recipients = params["recipients"]
        wallet_info = self.context.session.get_wallet()

        # Calculate total amount
        total_amount = sum(int(r["amount"]) for r in recipients)

        return {
            "from_address": wallet_info.address,
            "recipients": recipients,
            "recipient_count": len(recipients),
            "total_amount": str(total_amount),
            "status": "pending",
            "message": f"Multi-send prepared for {len(recipients)} recipients",
            "warning": "This is a test implementation. Real blockchain execution requires full SDK integration.",
        }


class GetTotalSupplyTool(BaseTool):
    """Get total supply of tokens.

    Query the total supply of all token denominations.
    """

    @property
    def name(self) -> str:
        return "get_total_supply"

    @property
    def description(self) -> str:
        return "Get total supply of tokens on Secret Network. Returns supply for all denominations."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BANK

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters (optional denom filter)."""
        # No required parameters
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get total supply.

        Returns:
            Total supply information
        """
        denom_filter = params.get("denom")

        try:
            # Query total supply using client pool
            with self.context.client_pool.get_client() as client:
                supply_response = await client.bank.total_supply()

                supply = supply_response.get("supply", [])

                # Filter by denom if specified
                if denom_filter:
                    supply = [s for s in supply if s.get("denom") == denom_filter]

                return {
                    "supply": supply,
                    "count": len(supply),
                    "message": "Total supply retrieved successfully",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get total supply: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check network connectivity",
                    "Try again later",
                ],
            )


class GetDenomMetadataTool(BaseTool):
    """Get denomination metadata.

    Query metadata information for a specific token denomination.
    """

    @property
    def name(self) -> str:
        return "get_denom_metadata"

    @property
    def description(self) -> str:
        return (
            "Get metadata for a token denomination. "
            "Returns description, display name, and denomination units."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BANK

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters.

        Args:
            params: Must contain 'denom'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "denom" not in params:
            raise ValidationError(
                message="Missing required parameter: denom",
                details={"required_params": ["denom"]},
                suggestions=[
                    "Provide token denomination",
                    "Example: {'denom': 'uscrt'}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get denom metadata.

        Args:
            params: Parameters including denom

        Returns:
            Denomination metadata
        """
        denom = params["denom"]

        try:
            # Query denom metadata using client pool
            with self.context.client_pool.get_client() as client:
                metadata_response = await client.bank.denom_metadata(denom)

                return {
                    "denom": denom,
                    "metadata": metadata_response.get("metadata", {}),
                    "message": f"Metadata retrieved for {denom}",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get denom metadata: {str(e)}",
                details={"denom": denom, "error": str(e)},
                suggestions=[
                    "Check that the denomination exists",
                    "Verify network connectivity",
                    "Try again later",
                ],
            )
