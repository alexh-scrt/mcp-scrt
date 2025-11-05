"""Rewards tools for Secret Network staking rewards and distribution.

This module provides tools for querying and withdrawing staking rewards.
"""

from typing import Any, Dict, Optional

from mcp_scrt.tools.base import BaseTool, ToolCategory
from mcp_scrt.utils.errors import ValidationError, NetworkError, WalletError
from mcp_scrt.core.validation import validate_address


# Helper function to create a signing client (placeholder for now)
async def create_signing_client(wallet_name: str, network: str):
    """Create a signing client for wallet operations.

    This is a placeholder that will be replaced with actual signing client implementation.
    """
    # This will be implemented with actual Secret Network signing client
    class MockSigningClient:
        async def withdraw_delegator_reward(self, validator_address: str):
            return {"txhash": "mock_hash", "code": 0}

        async def withdraw_all_rewards(self, validators: list):
            return {"txhash": "mock_hash", "code": 0}

        async def set_withdraw_address(self, withdraw_address: str):
            return {"txhash": "mock_hash", "code": 0}

    return MockSigningClient()


class GetRewardsTool(BaseTool):
    """Get staking rewards.

    Query staking rewards for a delegator address.
    """

    @property
    def name(self) -> str:
        return "get_rewards"

    @property
    def description(self) -> str:
        return (
            "Get staking rewards for a delegator address. "
            "Returns rewards per validator and total rewards."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.REWARDS

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get rewards parameters.

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
        """Execute get rewards.

        Args:
            params: Parameters including address

        Returns:
            Rewards information
        """
        address = params["address"]

        try:
            # Query rewards using client pool
            with self.context.client_pool.get_client() as client:
                rewards_response = await client.distribution.rewards(address)

                rewards = rewards_response.get("rewards", [])
                total = rewards_response.get("total", [])

                return {
                    "address": address,
                    "rewards": rewards,
                    "total": total,
                    "validators_count": len(rewards),
                    "message": f"Retrieved rewards for {address} from {len(rewards)} validator(s)",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get rewards: {str(e)}",
                details={"address": address, "error": str(e)},
                suggestions=[
                    "Check that the address is correct",
                    "Verify network connectivity",
                ],
            )


class WithdrawRewardsTool(BaseTool):
    """Withdraw staking rewards.

    Withdraw staking rewards from one or all validators.
    """

    @property
    def name(self) -> str:
        return "withdraw_rewards"

    @property
    def description(self) -> str:
        return (
            "Withdraw staking rewards from validators. "
            "Requires active wallet. Can withdraw from specific validator or all validators."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.REWARDS

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet to sign transaction

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate withdraw rewards parameters.

        Args:
            params: Optionally contains 'validator_address'

        Raises:
            ValidationError: If parameters are invalid
        """
        # validator_address is optional
        # If provided, validate it
        if "validator_address" in params:
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
        """Execute withdraw rewards.

        Args:
            params: Parameters optionally including validator_address

        Returns:
            Transaction result
        """
        validator_address = params.get("validator_address")

        # Get active wallet
        wallet_info = self.context.session.get_wallet()
        if not wallet_info:
            raise WalletError(
                message="No active wallet set",
                details={},
                suggestions=["Load a wallet using load_wallet"],
            )

        wallet_name = wallet_info.wallet_id
        delegator_address = wallet_info.address

        try:
            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            if validator_address:
                # Withdraw from specific validator
                result = await signing_client.withdraw_delegator_reward(
                    validator_address=validator_address
                )

                return {
                    "validator_address": validator_address,
                    "delegator_address": delegator_address,
                    "txhash": result.get("txhash"),
                    "message": f"Successfully withdrew rewards from {validator_address}",
                }
            else:
                # Withdraw from all validators
                # First get all delegations
                with self.context.client_pool.get_client() as client:
                    rewards_response = await client.distribution.rewards(
                        delegator_address
                    )
                    rewards = rewards_response.get("rewards", [])
                    validators = [r["validator_address"] for r in rewards if r.get("reward")]

                if not validators:
                    return {
                        "delegator_address": delegator_address,
                        "validators_count": 0,
                        "message": "No rewards to withdraw",
                    }

                # Withdraw from all validators
                result = await signing_client.withdraw_all_rewards(validators)

                return {
                    "delegator_address": delegator_address,
                    "validators_count": len(validators),
                    "txhash": result.get("txhash"),
                    "message": f"Successfully withdrew rewards from {len(validators)} validator(s)",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to withdraw rewards: {str(e)}",
                details={
                    "validator_address": validator_address,
                    "delegator_address": delegator_address,
                    "error": str(e),
                },
                suggestions=[
                    "Check that you have rewards to withdraw",
                    "Verify the validator address is correct (if specified)",
                    "Verify network connectivity",
                ],
            )


class SetWithdrawAddressTool(BaseTool):
    """Set withdraw address for rewards.

    Set a different address to receive staking rewards.
    """

    @property
    def name(self) -> str:
        return "set_withdraw_address"

    @property
    def description(self) -> str:
        return (
            "Set withdraw address for receiving staking rewards. "
            "Requires active wallet. Rewards will be sent to the specified address."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.REWARDS

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet to sign transaction

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate set withdraw address parameters.

        Args:
            params: Must contain 'withdraw_address'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "withdraw_address" not in params:
            raise ValidationError(
                message="Missing required parameter: withdraw_address",
                details={"required_params": ["withdraw_address"]},
                suggestions=[
                    "Provide 'withdraw_address' parameter",
                    "Example: {'withdraw_address': 'secret1...'}",
                ],
            )

        # Validate address format
        validate_address(params["withdraw_address"])

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute set withdraw address.

        Args:
            params: Parameters including withdraw_address

        Returns:
            Transaction result
        """
        withdraw_address = params["withdraw_address"]

        # Get active wallet
        wallet_info = self.context.session.get_wallet()
        if not wallet_info:
            raise WalletError(
                message="No active wallet set",
                details={},
                suggestions=["Load a wallet using load_wallet"],
            )

        wallet_name = wallet_info.wallet_id
        delegator_address = wallet_info.address

        try:
            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            # Set withdraw address
            result = await signing_client.set_withdraw_address(
                withdraw_address=withdraw_address
            )

            return {
                "delegator_address": delegator_address,
                "withdraw_address": withdraw_address,
                "txhash": result.get("txhash"),
                "message": f"Successfully set withdraw address to {withdraw_address}",
            }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to set withdraw address: {str(e)}",
                details={
                    "delegator_address": delegator_address,
                    "withdraw_address": withdraw_address,
                    "error": str(e),
                },
                suggestions=[
                    "Check that the withdraw address is valid",
                    "Verify network connectivity",
                ],
            )


class GetCommunityPoolTool(BaseTool):
    """Get community pool.

    Query the community pool balance.
    """

    @property
    def name(self) -> str:
        return "get_community_pool"

    @property
    def description(self) -> str:
        return (
            "Get community pool balance. "
            "Returns the current balance of the community pool."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.REWARDS

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get community pool parameters.

        Args:
            params: No parameters required

        Raises:
            ValidationError: If parameters are invalid
        """
        # No parameters required
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get community pool.

        Args:
            params: No parameters required

        Returns:
            Community pool balance
        """
        try:
            # Query community pool using client pool
            with self.context.client_pool.get_client() as client:
                pool_response = await client.distribution.community_pool()

                pool = pool_response.get("pool", [])

                return {
                    "pool": pool,
                    "message": f"Retrieved community pool with {len(pool)} denom(s)",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get community pool: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Verify network connectivity",
                    "Try again later",
                ],
            )
