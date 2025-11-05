"""Integration tests for staking workflow.

Tests the complete end-to-end staking workflow including:
1. Get validators list
2. Delegate to a validator
3. Check delegation
4. Query rewards
5. Withdraw rewards
6. Undelegate
7. Check unbonding
"""

import pytest
from unittest.mock import patch, AsyncMock

from mcp_scrt.tools.wallet import ImportWalletTool
from mcp_scrt.tools.staking import (
    GetValidatorsTool,
    GetValidatorTool,
    DelegateTool,
    UndelegateTool,
    RedelegateTool,
    GetDelegationsTool,
    GetUnbondingTool,
)
from mcp_scrt.tools.rewards import GetRewardsTool, WithdrawRewardsTool


class TestStakingWorkflow:
    """Integration tests for complete staking workflow."""

    @pytest.mark.asyncio
    async def test_complete_staking_workflow(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        mock_signing_client,
        mock_lcd_client,
    ):
        """Test complete staking lifecycle from delegation to unbonding.

        Workflow:
        1. Import wallet with funds
        2. Get list of validators
        3. Select a validator
        4. Delegate tokens
        5. Check delegation was successful
        6. Query rewards
        7. Withdraw rewards
        8. Undelegate tokens
        9. Check unbonding status
        """
        # Step 1: Import test wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Step 2: Get list of active validators
        validators_tool = GetValidatorsTool(tool_context)

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            validators_result = await validators_tool.run({
                "status": "BOND_STATUS_BONDED",
                "limit": 10,
            })

        assert validators_result["success"] is True
        validators = validators_result["data"]["validators"]
        assert len(validators) > 0

        # Step 3: Select the first validator (highest voting power in mock)
        selected_validator = validators[0]["operator_address"]
        validator_moniker = validators[0].get("moniker", "Test Validator")

        # Get specific validator details
        validator_tool = GetValidatorTool(tool_context)

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_lcd_client.staking.validator = AsyncMock(
                return_value={
                    "validator": validators[0]
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            validator_result = await validator_tool.run({
                "validator_address": selected_validator
            })

        assert validator_result["success"] is True
        assert validator_result["data"]["validator"]["operator_address"] == selected_validator

        # Step 4: Delegate tokens to the validator
        delegate_tool = DelegateTool(tool_context)
        delegation_amount = "10000000"  # 10 SCRT

        with patch("mcp_scrt.tools.staking.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            delegate_result = await delegate_tool.run({
                "validator_address": selected_validator,
                "amount": delegation_amount,
            })

        assert delegate_result["success"] is True
        assert "txhash" in delegate_result["data"]
        assert selected_validator in delegate_result["data"]["message"]

        # Step 5: Check delegation was successful
        delegations_tool = GetDelegationsTool(tool_context)

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_lcd_client.staking.delegations = AsyncMock(
                return_value={
                    "delegation_responses": [
                        {
                            "delegation": {
                                "delegator_address": test_wallet_with_funds.address,
                                "validator_address": selected_validator,
                                "shares": delegation_amount,
                            },
                            "balance": {
                                "denom": "uscrt",
                                "amount": delegation_amount,
                            }
                        }
                    ]
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            delegations_result = await delegations_tool.run({})

        assert delegations_result["success"] is True
        delegations = delegations_result["data"]["delegations"]
        assert len(delegations) > 0

        # Find our delegation
        our_delegation = next(
            (d for d in delegations if d["delegation"]["validator_address"] == selected_validator),
            None
        )
        assert our_delegation is not None
        assert our_delegation["balance"]["amount"] == delegation_amount

        # Step 6: Query rewards
        rewards_tool = GetRewardsTool(tool_context)

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_lcd_client.distribution.rewards = AsyncMock(
                return_value={
                    "rewards": [
                        {
                            "validator_address": selected_validator,
                            "reward": [
                                {"denom": "uscrt", "amount": "5000.50"}
                            ]
                        }
                    ],
                    "total": [
                        {"denom": "uscrt", "amount": "5000.50"}
                    ]
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            rewards_result = await rewards_tool.run({})

        assert rewards_result["success"] is True
        rewards = rewards_result["data"]["rewards"]
        assert len(rewards) > 0

        # Step 7: Withdraw rewards
        withdraw_tool = WithdrawRewardsTool(tool_context)

        with patch("mcp_scrt.tools.rewards.create_signing_client") as mock_create:
            mock_signing_client.withdraw_rewards = AsyncMock(
                return_value={
                    "txhash": "WITHDRAW_REWARDS_TXHASH",
                    "code": 0,
                }
            )
            mock_create.return_value = mock_signing_client

            withdraw_result = await withdraw_tool.run({
                "validator_address": selected_validator
            })

        assert withdraw_result["success"] is True
        assert "txhash" in withdraw_result["data"]

        # Step 8: Undelegate tokens
        undelegate_tool = UndelegateTool(tool_context)
        unbond_amount = "5000000"  # Undelegate 5 SCRT

        with patch("mcp_scrt.tools.staking.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            undelegate_result = await undelegate_tool.run({
                "validator_address": selected_validator,
                "amount": unbond_amount,
            })

        assert undelegate_result["success"] is True
        assert "txhash" in undelegate_result["data"]

        # Step 9: Check unbonding status
        unbonding_tool = GetUnbondingTool(tool_context)

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_lcd_client.staking.unbonding_delegations = AsyncMock(
                return_value={
                    "unbonding_responses": [
                        {
                            "delegator_address": test_wallet_with_funds.address,
                            "validator_address": selected_validator,
                            "entries": [
                                {
                                    "creation_height": "12345",
                                    "completion_time": "2025-11-25T00:00:00Z",
                                    "initial_balance": unbond_amount,
                                    "balance": unbond_amount,
                                }
                            ]
                        }
                    ]
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            unbonding_result = await unbonding_tool.run({})

        assert unbonding_result["success"] is True
        unbonding = unbonding_result["data"]["unbonding_delegations"]
        assert len(unbonding) > 0

        # Verify our unbonding entry
        our_unbonding = next(
            (u for u in unbonding if u["validator_address"] == selected_validator),
            None
        )
        assert our_unbonding is not None
        assert len(our_unbonding["entries"]) > 0
        assert our_unbonding["entries"][0]["balance"] == unbond_amount

    @pytest.mark.asyncio
    async def test_redelegate_workflow(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        mock_signing_client,
        mock_lcd_client,
    ):
        """Test redelegation from one validator to another."""
        # Import test wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Get validators
        validators_tool = GetValidatorsTool(tool_context)

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            # Mock two validators
            mock_lcd_client.staking.validators = AsyncMock(
                return_value={
                    "validators": [
                        {
                            "operator_address": "secretvaloper1validator1validator1validator1va",
                            "description": {"moniker": "Validator 1"},
                            "tokens": "2000000000000",
                            "status": "BOND_STATUS_BONDED",
                            "jailed": False,
                            "commission": {
                                "commission_rates": {
                                    "rate": "0.100000000000000000"
                                }
                            }
                        },
                        {
                            "operator_address": "secretvaloper1validator2validator2validator2va",
                            "description": {"moniker": "Validator 2"},
                            "tokens": "1000000000000",
                            "status": "BOND_STATUS_BONDED",
                            "jailed": False,
                            "commission": {
                                "commission_rates": {
                                    "rate": "0.050000000000000000"
                                }
                            }
                        }
                    ]
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            validators_result = await validators_tool.run({})

        assert validators_result["success"] is True
        validators = validators_result["data"]["validators"]
        assert len(validators) >= 2

        src_validator = validators[0]["operator_address"]
        dst_validator = validators[1]["operator_address"]

        # Redelegate from validator 1 to validator 2
        redelegate_tool = RedelegateTool(tool_context)
        redelegate_amount = "5000000"  # 5 SCRT

        with patch("mcp_scrt.tools.staking.create_signing_client") as mock_create:
            mock_signing_client.redelegate = AsyncMock(
                return_value={
                    "txhash": "REDELEGATE_TXHASH",
                    "code": 0,
                }
            )
            mock_create.return_value = mock_signing_client

            redelegate_result = await redelegate_tool.run({
                "src_validator": src_validator,
                "dst_validator": dst_validator,
                "amount": redelegate_amount,
            })

        assert redelegate_result["success"] is True
        assert "txhash" in redelegate_result["data"]
        assert src_validator in redelegate_result["data"]["message"]
        assert dst_validator in redelegate_result["data"]["message"]

    @pytest.mark.asyncio
    async def test_withdraw_all_rewards(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        mock_signing_client,
        mock_lcd_client,
    ):
        """Test withdrawing rewards from all validators at once."""
        # Import test wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Withdraw all rewards (no validator_address specified)
        withdraw_tool = WithdrawRewardsTool(tool_context)

        with patch("mcp_scrt.tools.rewards.create_signing_client") as mock_create:
            mock_signing_client.withdraw_all_rewards = AsyncMock(
                return_value={
                    "txhash": "WITHDRAW_ALL_REWARDS_TXHASH",
                    "code": 0,
                }
            )
            mock_create.return_value = mock_signing_client

            withdraw_result = await withdraw_tool.run({})

        assert withdraw_result["success"] is True
        assert "txhash" in withdraw_result["data"]
        assert "all validators" in withdraw_result["data"]["message"].lower()

    @pytest.mark.asyncio
    async def test_query_specific_delegator_rewards(
        self,
        tool_context,
        mock_lcd_client,
    ):
        """Test querying rewards for a specific delegator address."""
        rewards_tool = GetRewardsTool(tool_context)
        delegator_address = "secret1delegatordelegatordelegatordelegatordk"

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_lcd_client.distribution.rewards = AsyncMock(
                return_value={
                    "rewards": [
                        {
                            "validator_address": "secretvaloper1validatorvalidatorvalidatorvalida",
                            "reward": [
                                {"denom": "uscrt", "amount": "1234.56"}
                            ]
                        }
                    ],
                    "total": [
                        {"denom": "uscrt", "amount": "1234.56"}
                    ]
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            rewards_result = await rewards_tool.run({
                "delegator": delegator_address
            })

        assert rewards_result["success"] is True
        assert rewards_result["data"]["delegator"] == delegator_address
        assert "rewards" in rewards_result["data"]
