"""Staking tools for Secret Network staking operations.

This module provides tools for validators, delegations, and staking operations.
"""

from typing import Any, Dict, Optional

from mcp_scrt.tools.base import BaseTool, ToolCategory
from mcp_scrt.utils.errors import ValidationError, NetworkError, WalletError
from mcp_scrt.core.validation import validate_address, validate_amount


# Helper function to create a signing client (placeholder for now)
async def create_signing_client(wallet_name: str, network: str):
    """Create a signing client for wallet operations.

    This is a placeholder that will be replaced with actual signing client implementation.
    """
    # This will be implemented with actual Secret Network signing client
    class MockSigningClient:
        async def delegate(self, validator_address: str, amount: Dict[str, str]):
            return {"txhash": "mock_hash", "code": 0}

        async def undelegate(self, validator_address: str, amount: Dict[str, str]):
            return {"txhash": "mock_hash", "code": 0}

        async def redelegate(
            self,
            src_validator: str,
            dst_validator: str,
            amount: Dict[str, str],
        ):
            return {"txhash": "mock_hash", "code": 0}

    return MockSigningClient()


class GetValidatorsTool(BaseTool):
    """Get all validators.

    Query all validators on the network with optional status filter.
    """

    @property
    def name(self) -> str:
        return "get_validators"

    @property
    def description(self) -> str:
        return (
            "Get all validators on Secret Network. "
            "Optionally filter by status (bonded, unbonded, unbonding)."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.STAKING

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get validators parameters.

        Args:
            params: Optionally contains 'status' and pagination params

        Raises:
            ValidationError: If parameters are invalid
        """
        # Status is optional, but if provided should be valid
        if "status" in params:
            status = params["status"]
            valid_statuses = [
                "BOND_STATUS_BONDED",
                "BOND_STATUS_UNBONDING",
                "BOND_STATUS_UNBONDED",
            ]
            if status not in valid_statuses:
                raise ValidationError(
                    message=f"Invalid status: {status}",
                    details={"provided": status, "valid_values": valid_statuses},
                    suggestions=[
                        "Use one of: BOND_STATUS_BONDED, BOND_STATUS_UNBONDING, BOND_STATUS_UNBONDED",
                    ],
                )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get validators.

        Args:
            params: Parameters including optional status

        Returns:
            List of validators
        """
        status = params.get("status", "")

        try:
            # Query validators using client pool
            with self.context.client_pool.get_client() as client:
                validators_response = client.staking.validators(status=status)

                validators = validators_response.get("validators", [])
                pagination = validators_response.get("pagination", {})

                return {
                    "validators": validators,
                    "count": len(validators),
                    "pagination": pagination,
                    "message": f"Retrieved {len(validators)} validator(s)",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get validators: {str(e)}",
                details={"status": status, "error": str(e)},
                suggestions=[
                    "Verify network connectivity",
                    "Try again later",
                ],
            )


class GetValidatorTool(BaseTool):
    """Get specific validator.

    Query details for a specific validator by address.
    """

    @property
    def name(self) -> str:
        return "get_validator"

    @property
    def description(self) -> str:
        return (
            "Get details for a specific validator by address. "
            "Returns validator information including commission, status, and voting power."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.STAKING

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get validator parameters.

        Args:
            params: Must contain 'validator_address'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "validator_address" not in params:
            raise ValidationError(
                message="Missing required parameter: validator_address",
                details={"required_params": ["validator_address"]},
                suggestions=[
                    "Provide 'validator_address' parameter",
                    "Example: {'validator_address': 'secretvaloper1...'}",
                ],
            )

        validator_address = params["validator_address"]
        if not isinstance(validator_address, str) or not validator_address:
            raise ValidationError(
                message="Invalid validator_address: must be a non-empty string",
                details={"provided": validator_address},
                suggestions=[
                    "Provide a valid validator address",
                    "Example: {'validator_address': 'secretvaloper1...'}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get validator.

        Args:
            params: Parameters including validator_address

        Returns:
            Validator information
        """
        validator_address = params["validator_address"]

        try:
            # Query validator using client pool
            with self.context.client_pool.get_client() as client:
                validator_response = client.staking.validator(validator_address)

                validator = validator_response.get("validator", {})

                return {
                    "validator_address": validator_address,
                    "validator": validator,
                    "message": f"Validator {validator_address} retrieved successfully",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get validator: {str(e)}",
                details={"validator_address": validator_address, "error": str(e)},
                suggestions=[
                    "Check that the validator address is correct",
                    "Verify the validator exists on the network",
                    "Verify network connectivity",
                ],
            )


class DelegateTool(BaseTool):
    """Delegate tokens to validator.

    Delegate tokens from your account to a validator.
    """

    @property
    def name(self) -> str:
        return "delegate"

    @property
    def description(self) -> str:
        return (
            "Delegate tokens to a validator. "
            "Requires active wallet. Tokens become bonded and earn staking rewards."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.STAKING

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet to sign transaction

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate delegate parameters.

        Args:
            params: Must contain 'validator_address' and 'amount'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "validator_address" not in params:
            raise ValidationError(
                message="Missing required parameter: validator_address",
                details={"required_params": ["validator_address", "amount"]},
                suggestions=[
                    "Provide 'validator_address' parameter",
                    "Example: {'validator_address': 'secretvaloper1...', 'amount': '1000000'}",
                ],
            )

        if "amount" not in params:
            raise ValidationError(
                message="Missing required parameter: amount",
                details={"required_params": ["validator_address", "amount"]},
                suggestions=[
                    "Provide 'amount' parameter",
                    "Example: {'validator_address': 'secretvaloper1...', 'amount': '1000000'}",
                ],
            )

        # Validate amount
        validate_amount(params["amount"], params.get("denom", "uscrt"))

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute delegate.

        Args:
            params: Parameters including validator_address, amount, optional denom

        Returns:
            Transaction result
        """
        validator_address = params["validator_address"]
        amount = params["amount"]
        denom = params.get("denom", "uscrt")

        # Get active wallet
        wallet_info = self.context.session.get_wallet()
        if not wallet_info:
            raise WalletError(
                message="No active wallet set",
                details={},
                suggestions=["Load a wallet using load_wallet"],
            )

        wallet_name = wallet_info.wallet_id

        try:
            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            # Delegate tokens
            result = await signing_client.delegate(
                validator_address=validator_address,
                amount={"denom": denom, "amount": amount},
            )

            return {
                "validator_address": validator_address,
                "amount": amount,
                "denom": denom,
                "txhash": result.get("txhash"),
                "message": f"Successfully delegated {amount} {denom} to {validator_address}",
            }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to delegate: {str(e)}",
                details={
                    "validator_address": validator_address,
                    "amount": amount,
                    "error": str(e),
                },
                suggestions=[
                    "Check that you have sufficient balance",
                    "Verify the validator address is correct",
                    "Verify network connectivity",
                ],
            )


class UndelegateTool(BaseTool):
    """Undelegate tokens from validator.

    Undelegate tokens from a validator. Tokens enter unbonding period.
    """

    @property
    def name(self) -> str:
        return "undelegate"

    @property
    def description(self) -> str:
        return (
            "Undelegate tokens from a validator. "
            "Requires active wallet. Tokens enter 21-day unbonding period."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.STAKING

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet to sign transaction

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate undelegate parameters.

        Args:
            params: Must contain 'validator_address' and 'amount'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "validator_address" not in params:
            raise ValidationError(
                message="Missing required parameter: validator_address",
                details={"required_params": ["validator_address", "amount"]},
                suggestions=[
                    "Provide 'validator_address' parameter",
                    "Example: {'validator_address': 'secretvaloper1...', 'amount': '1000000'}",
                ],
            )

        if "amount" not in params:
            raise ValidationError(
                message="Missing required parameter: amount",
                details={"required_params": ["validator_address", "amount"]},
                suggestions=[
                    "Provide 'amount' parameter",
                    "Example: {'validator_address': 'secretvaloper1...', 'amount': '1000000'}",
                ],
            )

        # Validate amount
        validate_amount(params["amount"], params.get("denom", "uscrt"))

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute undelegate.

        Args:
            params: Parameters including validator_address, amount, optional denom

        Returns:
            Transaction result
        """
        validator_address = params["validator_address"]
        amount = params["amount"]
        denom = params.get("denom", "uscrt")

        # Get active wallet
        wallet_info = self.context.session.get_wallet()
        if not wallet_info:
            raise WalletError(
                message="No active wallet set",
                details={},
                suggestions=["Load a wallet using load_wallet"],
            )

        wallet_name = wallet_info.wallet_id

        try:
            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            # Undelegate tokens
            result = await signing_client.undelegate(
                validator_address=validator_address,
                amount={"denom": denom, "amount": amount},
            )

            return {
                "validator_address": validator_address,
                "amount": amount,
                "denom": denom,
                "txhash": result.get("txhash"),
                "message": f"Successfully undelegated {amount} {denom} from {validator_address}",
            }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to undelegate: {str(e)}",
                details={
                    "validator_address": validator_address,
                    "amount": amount,
                    "error": str(e),
                },
                suggestions=[
                    "Check that you have sufficient delegated balance",
                    "Verify the validator address is correct",
                    "Verify network connectivity",
                ],
            )


class RedelegateTool(BaseTool):
    """Redelegate tokens between validators.

    Move delegated tokens from one validator to another without unbonding.
    """

    @property
    def name(self) -> str:
        return "redelegate"

    @property
    def description(self) -> str:
        return (
            "Redelegate tokens from one validator to another. "
            "Requires active wallet. No unbonding period, but limited frequency."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.STAKING

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet to sign transaction

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate redelegate parameters.

        Args:
            params: Must contain src_validator_address, dst_validator_address, amount

        Raises:
            ValidationError: If parameters are invalid
        """
        if "src_validator_address" not in params:
            raise ValidationError(
                message="Missing required parameter: src_validator_address",
                details={
                    "required_params": [
                        "src_validator_address",
                        "dst_validator_address",
                        "amount",
                    ]
                },
                suggestions=[
                    "Provide 'src_validator_address' parameter",
                    "Example: {'src_validator_address': 'secretvaloper1...', 'dst_validator_address': 'secretvaloper2...', 'amount': '1000000'}",
                ],
            )

        if "dst_validator_address" not in params:
            raise ValidationError(
                message="Missing required parameter: dst_validator_address",
                details={
                    "required_params": [
                        "src_validator_address",
                        "dst_validator_address",
                        "amount",
                    ]
                },
                suggestions=[
                    "Provide 'dst_validator_address' parameter",
                    "Example: {'src_validator_address': 'secretvaloper1...', 'dst_validator_address': 'secretvaloper2...', 'amount': '1000000'}",
                ],
            )

        if "amount" not in params:
            raise ValidationError(
                message="Missing required parameter: amount",
                details={
                    "required_params": [
                        "src_validator_address",
                        "dst_validator_address",
                        "amount",
                    ]
                },
                suggestions=[
                    "Provide 'amount' parameter",
                    "Example: {'src_validator_address': 'secretvaloper1...', 'dst_validator_address': 'secretvaloper2...', 'amount': '1000000'}",
                ],
            )

        # Validate amount
        validate_amount(params["amount"], params.get("denom", "uscrt"))

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute redelegate.

        Args:
            params: Parameters including src/dst validator addresses, amount, optional denom

        Returns:
            Transaction result
        """
        src_validator = params["src_validator_address"]
        dst_validator = params["dst_validator_address"]
        amount = params["amount"]
        denom = params.get("denom", "uscrt")

        # Get active wallet
        wallet_info = self.context.session.get_wallet()
        if not wallet_info:
            raise WalletError(
                message="No active wallet set",
                details={},
                suggestions=["Load a wallet using load_wallet"],
            )

        wallet_name = wallet_info.wallet_id

        try:
            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            # Redelegate tokens
            result = await signing_client.redelegate(
                src_validator=src_validator,
                dst_validator=dst_validator,
                amount={"denom": denom, "amount": amount},
            )

            return {
                "src_validator_address": src_validator,
                "dst_validator_address": dst_validator,
                "amount": amount,
                "denom": denom,
                "txhash": result.get("txhash"),
                "message": f"Successfully redelegated {amount} {denom} from {src_validator} to {dst_validator}",
            }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to redelegate: {str(e)}",
                details={
                    "src_validator": src_validator,
                    "dst_validator": dst_validator,
                    "amount": amount,
                    "error": str(e),
                },
                suggestions=[
                    "Check that you have sufficient delegated balance",
                    "Verify both validator addresses are correct",
                    "Note: You cannot redelegate to the same validator pair within 21 days",
                    "Verify network connectivity",
                ],
            )


class GetDelegationsTool(BaseTool):
    """Get delegations for address.

    Query all delegations for a specific address.
    """

    @property
    def name(self) -> str:
        return "get_delegations"

    @property
    def description(self) -> str:
        return (
            "Get all delegations for an address. "
            "Returns list of validators and delegated amounts."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.STAKING

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get delegations parameters.

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
        """Execute get delegations.

        Args:
            params: Parameters including address

        Returns:
            List of delegations
        """
        address = params["address"]

        try:
            # Query delegations using client pool
            with self.context.client_pool.get_client() as client:
                delegations_response = client.staking.delegations(address)

                delegation_responses = delegations_response.get(
                    "delegation_responses", []
                )
                pagination = delegations_response.get("pagination", {})

                return {
                    "address": address,
                    "delegations": delegation_responses,
                    "count": len(delegation_responses),
                    "pagination": pagination,
                    "message": f"Retrieved {len(delegation_responses)} delegation(s) for {address}",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get delegations: {str(e)}",
                details={"address": address, "error": str(e)},
                suggestions=[
                    "Check that the address is correct",
                    "Verify network connectivity",
                ],
            )


class GetUnbondingTool(BaseTool):
    """Get unbonding delegations.

    Query unbonding delegations for a specific address.
    """

    @property
    def name(self) -> str:
        return "get_unbonding"

    @property
    def description(self) -> str:
        return (
            "Get unbonding delegations for an address. "
            "Returns delegations currently in the unbonding period."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.STAKING

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get unbonding parameters.

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
        """Execute get unbonding.

        Args:
            params: Parameters including address

        Returns:
            List of unbonding delegations
        """
        address = params["address"]

        try:
            # Query unbonding delegations using client pool
            with self.context.client_pool.get_client() as client:
                unbonding_response = client.staking.unbonding_delegations(
                    address
                )

                unbonding_responses = unbonding_response.get("unbonding_responses", [])
                pagination = unbonding_response.get("pagination", {})

                return {
                    "address": address,
                    "unbonding_delegations": unbonding_responses,
                    "count": len(unbonding_responses),
                    "pagination": pagination,
                    "message": f"Retrieved {len(unbonding_responses)} unbonding delegation(s) for {address}",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get unbonding delegations: {str(e)}",
                details={"address": address, "error": str(e)},
                suggestions=[
                    "Check that the address is correct",
                    "Verify network connectivity",
                ],
            )


class GetRedelegationsTool(BaseTool):
    """Get redelegations.

    Query redelegations for a specific address.
    """

    @property
    def name(self) -> str:
        return "get_redelegations"

    @property
    def description(self) -> str:
        return (
            "Get redelegations for an address. "
            "Returns active redelegation records."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.STAKING

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get redelegations parameters.

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
        """Execute get redelegations.

        Args:
            params: Parameters including address

        Returns:
            List of redelegations
        """
        address = params["address"]

        try:
            # Query redelegations using client pool
            with self.context.client_pool.get_client() as client:
                redelegations_response = client.staking.redelegations(
                    delegator_addr=address
                )

                redelegation_responses = redelegations_response.get(
                    "redelegation_responses", []
                )
                pagination = redelegations_response.get("pagination", {})

                return {
                    "address": address,
                    "redelegations": redelegation_responses,
                    "count": len(redelegation_responses),
                    "pagination": pagination,
                    "message": f"Retrieved {len(redelegation_responses)} redelegation(s) for {address}",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get redelegations: {str(e)}",
                details={"address": address, "error": str(e)},
                suggestions=[
                    "Check that the address is correct",
                    "Verify network connectivity",
                ],
            )
