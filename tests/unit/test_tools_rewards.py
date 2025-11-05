"""Tests for rewards tools.

This module tests the rewards tools for staking rewards and distribution operations.
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, patch, AsyncMock

from mcp_scrt.tools.rewards import (
    GetRewardsTool,
    WithdrawRewardsTool,
    SetWithdrawAddressTool,
    GetCommunityPoolTool,
)
from mcp_scrt.tools.base import ToolCategory, ToolExecutionContext
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.types import NetworkType, WalletInfo
from mcp_scrt.utils.errors import ValidationError


class TestGetRewardsTool:
    """Test get_rewards tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetRewardsTool(context)

        assert tool.name == "get_rewards"
        assert "rewards" in tool.description.lower()
        assert tool.category == ToolCategory.REWARDS
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

        tool = GetRewardsTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_rewards(self) -> None:
        """Test getting rewards."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetRewardsTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.distribution = Mock()
            mock_client.distribution.rewards = AsyncMock(
                return_value={
                    "rewards": [
                        {
                            "validator_address": "secretvaloper1abc",
                            "reward": [
                                {"denom": "uscrt", "amount": "1000000"},
                            ],
                        }
                    ],
                    "total": [
                        {"denom": "uscrt", "amount": "1000000"},
                    ],
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"})

            assert result["success"] is True
            assert "rewards" in result["data"]
            assert "total" in result["data"]


class TestWithdrawRewardsTool:
    """Test withdraw_rewards tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = WithdrawRewardsTool(context)

        assert tool.name == "withdraw_rewards"
        assert "withdraw" in tool.description.lower()
        assert tool.category == ToolCategory.REWARDS
        assert tool.requires_wallet is True

    def test_validate_params_optional_validator(self) -> None:
        """Test validation with optional validator_address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = WithdrawRewardsTool(context)

        # Should not raise with no params (withdraw from all validators)
        tool.validate_params({})

        # Should not raise with validator_address
        tool.validate_params({"validator_address": "secretvaloper1abc"})

    @pytest.mark.asyncio
    async def test_execute_withdraw_rewards_from_validator(self) -> None:
        """Test withdrawing rewards from specific validator."""
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

        tool = WithdrawRewardsTool(context)

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
            with patch("mcp_scrt.tools.rewards.create_signing_client") as mock_create:
                mock_signing = AsyncMock()
                mock_signing.withdraw_delegator_reward = AsyncMock(
                    return_value={
                        "txhash": "ABC123",
                        "code": 0,
                    }
                )
                mock_create.return_value = mock_signing

                result = await tool.run({"validator_address": "secretvaloper1abc"})

                assert result["success"] is True
                assert "txhash" in result["data"]

    @pytest.mark.asyncio
    async def test_execute_withdraw_rewards_from_all(self) -> None:
        """Test withdrawing rewards from all validators."""
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

        tool = WithdrawRewardsTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.distribution = Mock()
            mock_client.distribution.rewards = AsyncMock(
                return_value={
                    "rewards": [
                        {
                            "validator_address": "secretvaloper1abc",
                            "reward": [{"denom": "uscrt", "amount": "1000000"}],
                        },
                        {
                            "validator_address": "secretvaloper1xyz",
                            "reward": [{"denom": "uscrt", "amount": "2000000"}],
                        },
                    ],
                    "total": [{"denom": "uscrt", "amount": "3000000"}],
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            # Mock the signing client
            with patch("mcp_scrt.tools.rewards.create_signing_client") as mock_create:
                mock_signing = AsyncMock()
                mock_signing.withdraw_all_rewards = AsyncMock(
                    return_value={
                        "txhash": "ABC123",
                        "code": 0,
                    }
                )
                mock_create.return_value = mock_signing

                result = await tool.run({})

                assert result["success"] is True
                assert "txhash" in result["data"]
                assert result["data"]["validators_count"] == 2


class TestSetWithdrawAddressTool:
    """Test set_withdraw_address tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SetWithdrawAddressTool(context)

        assert tool.name == "set_withdraw_address"
        assert "withdraw" in tool.description.lower() and "address" in tool.description.lower()
        assert tool.category == ToolCategory.REWARDS
        assert tool.requires_wallet is True

    def test_validate_params_missing_withdraw_address(self) -> None:
        """Test validation fails without withdraw_address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SetWithdrawAddressTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "withdraw_address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_set_withdraw_address(self) -> None:
        """Test setting withdraw address."""
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

        tool = SetWithdrawAddressTool(context)

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
            with patch("mcp_scrt.tools.rewards.create_signing_client") as mock_create:
                mock_signing = AsyncMock()
                mock_signing.set_withdraw_address = AsyncMock(
                    return_value={
                        "txhash": "ABC123",
                        "code": 0,
                    }
                )
                mock_create.return_value = mock_signing

                result = await tool.run({
                    "withdraw_address": "secret1xyz123xyz123xyz123xyz123xyz123xyz123xyz"
                })

                assert result["success"] is True
                assert "txhash" in result["data"]


class TestGetCommunityPoolTool:
    """Test get_community_pool tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetCommunityPoolTool(context)

        assert tool.name == "get_community_pool"
        assert "community pool" in tool.description.lower()
        assert tool.category == ToolCategory.REWARDS
        assert tool.requires_wallet is False

    def test_validate_params_no_params_required(self) -> None:
        """Test validation with no params required."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetCommunityPoolTool(context)

        # Should not raise with no params
        tool.validate_params({})

    @pytest.mark.asyncio
    async def test_execute_get_community_pool(self) -> None:
        """Test getting community pool."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetCommunityPoolTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.distribution = Mock()
            mock_client.distribution.community_pool = AsyncMock(
                return_value={
                    "pool": [
                        {"denom": "uscrt", "amount": "1000000000000.123456789"},
                    ]
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({})

            assert result["success"] is True
            assert "pool" in result["data"]


class TestRewardsToolsIntegration:
    """Test rewards tools working together."""

    @pytest.mark.asyncio
    async def test_all_rewards_tools_have_correct_metadata(self) -> None:
        """Test all rewards tools can be instantiated and have correct metadata."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tools = [
            GetRewardsTool(context),
            WithdrawRewardsTool(context),
            SetWithdrawAddressTool(context),
            GetCommunityPoolTool(context),
        ]

        # All tools should be REWARDS category
        for tool in tools:
            assert tool.category == ToolCategory.REWARDS
            assert tool.name is not None
            assert tool.description is not None

        # All tool names should be unique
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))

        # Check which tools require wallet
        wallet_required = [tool for tool in tools if tool.requires_wallet]
        wallet_not_required = [tool for tool in tools if not tool.requires_wallet]

        # withdraw_rewards and set_withdraw_address should require wallet
        assert len(wallet_required) == 2
        assert len(wallet_not_required) == 2
