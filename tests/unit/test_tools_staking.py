"""Tests for staking tools.

This module tests the staking tools for validators and delegation operations.
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, patch, AsyncMock

from mcp_scrt.tools.staking import (
    GetValidatorsTool,
    GetValidatorTool,
    DelegateTool,
    UndelegateTool,
    RedelegateTool,
    GetDelegationsTool,
    GetUnbondingTool,
    GetRedelegationsTool,
)
from mcp_scrt.tools.base import ToolCategory, ToolExecutionContext
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.types import NetworkType, WalletInfo
from mcp_scrt.utils.errors import ValidationError


class TestGetValidatorsTool:
    """Test get_validators tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetValidatorsTool(context)

        assert tool.name == "get_validators"
        assert "validators" in tool.description.lower()
        assert tool.category == ToolCategory.STAKING
        assert tool.requires_wallet is False

    def test_validate_params_optional_status(self) -> None:
        """Test validation with optional status parameter."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetValidatorsTool(context)

        # Should not raise with no params
        tool.validate_params({})

        # Should not raise with valid status
        tool.validate_params({"status": "BOND_STATUS_BONDED"})

    @pytest.mark.asyncio
    async def test_execute_get_validators(self) -> None:
        """Test getting validators."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetValidatorsTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.staking = Mock()
            mock_client.staking.validators = AsyncMock(
                return_value={
                    "validators": [
                        {
                            "operator_address": "secretvaloper1...",
                            "consensus_pubkey": {"@type": "...", "key": "..."},
                            "jailed": False,
                            "status": "BOND_STATUS_BONDED",
                            "tokens": "1000000000000",
                            "delegator_shares": "1000000000000",
                            "description": {
                                "moniker": "Test Validator",
                                "identity": "",
                                "website": "",
                                "security_contact": "",
                                "details": "",
                            },
                            "commission": {
                                "commission_rates": {
                                    "rate": "0.100000000000000000",
                                    "max_rate": "0.200000000000000000",
                                    "max_change_rate": "0.010000000000000000",
                                },
                                "update_time": "2021-01-01T00:00:00Z",
                            },
                        }
                    ],
                    "pagination": {"next_key": None, "total": "1"},
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({})

            assert result["success"] is True
            assert "validators" in result["data"]
            assert result["data"]["count"] == 1


class TestGetValidatorTool:
    """Test get_validator tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetValidatorTool(context)

        assert tool.name == "get_validator"
        assert "validator" in tool.description.lower()
        assert tool.category == ToolCategory.STAKING
        assert tool.requires_wallet is False

    def test_validate_params_missing_validator_address(self) -> None:
        """Test validation fails without validator_address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetValidatorTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "validator_address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_validator(self) -> None:
        """Test getting a specific validator."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetValidatorTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.staking = Mock()
            mock_client.staking.validator = AsyncMock(
                return_value={
                    "validator": {
                        "operator_address": "secretvaloper1abc",
                        "consensus_pubkey": {"@type": "...", "key": "..."},
                        "jailed": False,
                        "status": "BOND_STATUS_BONDED",
                        "tokens": "1000000000000",
                        "delegator_shares": "1000000000000",
                        "description": {"moniker": "Test Validator"},
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"validator_address": "secretvaloper1abc"})

            assert result["success"] is True
            assert "validator" in result["data"]


class TestDelegateTool:
    """Test delegate tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = DelegateTool(context)

        assert tool.name == "delegate"
        assert "delegate" in tool.description.lower()
        assert tool.category == ToolCategory.STAKING
        assert tool.requires_wallet is True

    def test_validate_params_missing_validator_address(self) -> None:
        """Test validation fails without validator_address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = DelegateTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"amount": "1000000"})

        assert "validator_address" in str(exc_info.value.message).lower()

    def test_validate_params_missing_amount(self) -> None:
        """Test validation fails without amount."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = DelegateTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"validator_address": "secretvaloper1abc"})

        assert "amount" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_delegate(self) -> None:
        """Test delegating tokens."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Start session and load wallet
        session.start()
        wallet = WalletInfo(
            wallet_id="test_wallet",
            address="secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
        )
        session.load_wallet(wallet)

        tool = DelegateTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tx = Mock()
            mock_client.tx.broadcast = AsyncMock(
                return_value={
                    "tx_response": {
                        "txhash": "ABC123",
                        "code": 0,
                        "height": "12345",
                        "raw_log": "success",
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            # Mock the signing client
            with patch("mcp_scrt.tools.staking.create_signing_client") as mock_create:
                mock_signing = AsyncMock()
                mock_signing.delegate = AsyncMock(
                    return_value={
                        "txhash": "ABC123",
                        "code": 0,
                    }
                )
                mock_create.return_value = mock_signing

                result = await tool.run({
                    "validator_address": "secretvaloper1abc",
                    "amount": "1000000",
                })

                assert result["success"] is True
                assert "txhash" in result["data"]


class TestUndelegateTool:
    """Test undelegate tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = UndelegateTool(context)

        assert tool.name == "undelegate"
        assert "undelegate" in tool.description.lower()
        assert tool.category == ToolCategory.STAKING
        assert tool.requires_wallet is True

    def test_validate_params_missing_validator_address(self) -> None:
        """Test validation fails without validator_address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = UndelegateTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"amount": "1000000"})

        assert "validator_address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_undelegate(self) -> None:
        """Test undelegating tokens."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Start session and load wallet
        session.start()
        wallet = WalletInfo(
            wallet_id="test_wallet",
            address="secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
        )
        session.load_wallet(wallet)

        tool = UndelegateTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tx = Mock()
            mock_client.tx.broadcast = AsyncMock(
                return_value={
                    "tx_response": {
                        "txhash": "ABC123",
                        "code": 0,
                        "height": "12345",
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            # Mock the signing client
            with patch("mcp_scrt.tools.staking.create_signing_client") as mock_create:
                mock_signing = AsyncMock()
                mock_signing.undelegate = AsyncMock(
                    return_value={
                        "txhash": "ABC123",
                        "code": 0,
                    }
                )
                mock_create.return_value = mock_signing

                result = await tool.run({
                    "validator_address": "secretvaloper1abc",
                    "amount": "1000000",
                })

                assert result["success"] is True


class TestRedelegateTool:
    """Test redelegate tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = RedelegateTool(context)

        assert tool.name == "redelegate"
        assert "redelegate" in tool.description.lower()
        assert tool.category == ToolCategory.STAKING
        assert tool.requires_wallet is True

    def test_validate_params_missing_src_validator(self) -> None:
        """Test validation fails without src_validator_address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = RedelegateTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "dst_validator_address": "secretvaloper1xyz",
                "amount": "1000000",
            })

        assert "src_validator_address" in str(exc_info.value.message).lower()

    def test_validate_params_missing_dst_validator(self) -> None:
        """Test validation fails without dst_validator_address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = RedelegateTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "src_validator_address": "secretvaloper1abc",
                "amount": "1000000",
            })

        assert "dst_validator_address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_redelegate(self) -> None:
        """Test redelegating tokens."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Start session and load wallet
        session.start()
        wallet = WalletInfo(
            wallet_id="test_wallet",
            address="secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
        )
        session.load_wallet(wallet)

        tool = RedelegateTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.tx = Mock()
            mock_client.tx.broadcast = AsyncMock(
                return_value={
                    "tx_response": {
                        "txhash": "ABC123",
                        "code": 0,
                        "height": "12345",
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            # Mock the signing client
            with patch("mcp_scrt.tools.staking.create_signing_client") as mock_create:
                mock_signing = AsyncMock()
                mock_signing.redelegate = AsyncMock(
                    return_value={
                        "txhash": "ABC123",
                        "code": 0,
                    }
                )
                mock_create.return_value = mock_signing

                result = await tool.run({
                    "src_validator_address": "secretvaloper1abc",
                    "dst_validator_address": "secretvaloper1xyz",
                    "amount": "1000000",
                })

                assert result["success"] is True


class TestGetDelegationsTool:
    """Test get_delegations tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetDelegationsTool(context)

        assert tool.name == "get_delegations"
        assert "delegation" in tool.description.lower()
        assert tool.category == ToolCategory.STAKING
        assert tool.requires_wallet is False

    def test_validate_params_missing_address(self) -> None:
        """Test validation fails without address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetDelegationsTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_delegations(self) -> None:
        """Test getting delegations."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetDelegationsTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.staking = Mock()
            mock_client.staking.delegations = AsyncMock(
                return_value={
                    "delegation_responses": [
                        {
                            "delegation": {
                                "delegator_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
                                "validator_address": "secretvaloper1abc",
                                "shares": "1000000000000",
                            },
                            "balance": {"denom": "uscrt", "amount": "1000000000000"},
                        }
                    ],
                    "pagination": {"next_key": None, "total": "1"},
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"})

            assert result["success"] is True
            assert "delegations" in result["data"]


class TestGetUnbondingTool:
    """Test get_unbonding tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetUnbondingTool(context)

        assert tool.name == "get_unbonding"
        assert "unbonding" in tool.description.lower()
        assert tool.category == ToolCategory.STAKING
        assert tool.requires_wallet is False

    def test_validate_params_missing_address(self) -> None:
        """Test validation fails without address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetUnbondingTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_unbonding(self) -> None:
        """Test getting unbonding delegations."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetUnbondingTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.staking = Mock()
            mock_client.staking.unbonding_delegations = AsyncMock(
                return_value={
                    "unbonding_responses": [
                        {
                            "delegator_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
                            "validator_address": "secretvaloper1abc",
                            "entries": [
                                {
                                    "creation_height": "12345",
                                    "completion_time": "2024-01-01T00:00:00Z",
                                    "initial_balance": "1000000",
                                    "balance": "1000000",
                                }
                            ],
                        }
                    ],
                    "pagination": {"next_key": None, "total": "1"},
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"})

            assert result["success"] is True
            assert "unbonding_delegations" in result["data"]


class TestGetRedelegationsTool:
    """Test get_redelegations tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetRedelegationsTool(context)

        assert tool.name == "get_redelegations"
        assert "redelegation" in tool.description.lower()
        assert tool.category == ToolCategory.STAKING
        assert tool.requires_wallet is False

    def test_validate_params_missing_address(self) -> None:
        """Test validation fails without address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetRedelegationsTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_redelegations(self) -> None:
        """Test getting redelegations."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetRedelegationsTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.staking = Mock()
            mock_client.staking.redelegations = AsyncMock(
                return_value={
                    "redelegation_responses": [
                        {
                            "redelegation": {
                                "delegator_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
                                "validator_src_address": "secretvaloper1abc",
                                "validator_dst_address": "secretvaloper1xyz",
                                "entries": [],
                            },
                            "entries": [
                                {
                                    "redelegation_entry": {
                                        "creation_height": 12345,
                                        "completion_time": "2024-01-01T00:00:00Z",
                                        "initial_balance": "1000000",
                                        "shares_dst": "1000000",
                                    },
                                    "balance": "1000000",
                                }
                            ],
                        }
                    ],
                    "pagination": {"next_key": None, "total": "1"},
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"})

            assert result["success"] is True
            assert "redelegations" in result["data"]


class TestStakingToolsIntegration:
    """Test staking tools working together."""

    @pytest.mark.asyncio
    async def test_all_staking_tools_have_correct_metadata(self) -> None:
        """Test all staking tools can be instantiated and have correct metadata."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tools = [
            GetValidatorsTool(context),
            GetValidatorTool(context),
            DelegateTool(context),
            UndelegateTool(context),
            RedelegateTool(context),
            GetDelegationsTool(context),
            GetUnbondingTool(context),
            GetRedelegationsTool(context),
        ]

        # All tools should be STAKING category
        for tool in tools:
            assert tool.category == ToolCategory.STAKING
            assert tool.name is not None
            assert tool.description is not None

        # All tool names should be unique
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))

        # Check which tools require wallet
        wallet_required = [tool for tool in tools if tool.requires_wallet]
        wallet_not_required = [tool for tool in tools if not tool.requires_wallet]

        # Delegate, undelegate, redelegate should require wallet
        assert len(wallet_required) == 3
        assert len(wallet_not_required) == 5
