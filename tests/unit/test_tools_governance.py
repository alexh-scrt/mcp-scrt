"""Tests for governance tools.

This module tests the governance tools for proposals, voting, and deposits.
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, patch, AsyncMock

from mcp_scrt.tools.governance import (
    GetProposalsTool,
    GetProposalTool,
    SubmitProposalTool,
    DepositProposalTool,
    VoteProposalTool,
    GetVoteTool,
)
from mcp_scrt.tools.base import ToolCategory, ToolExecutionContext
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.types import NetworkType, WalletInfo
from mcp_scrt.utils.errors import ValidationError


class TestGetProposalsTool:
    """Test get_proposals tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetProposalsTool(context)

        assert tool.name == "get_proposals"
        assert "proposals" in tool.description.lower()
        assert tool.category == ToolCategory.GOVERNANCE
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

        tool = GetProposalsTool(context)

        # Should not raise with no params
        tool.validate_params({})

        # Should not raise with valid status
        tool.validate_params({"status": "PROPOSAL_STATUS_VOTING_PERIOD"})

    @pytest.mark.asyncio
    async def test_execute_get_proposals(self) -> None:
        """Test getting proposals."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetProposalsTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.gov = Mock()
            mock_client.gov.proposals = AsyncMock(
                return_value={
                    "proposals": [
                        {
                            "proposal_id": "1",
                            "content": {
                                "@type": "/cosmos.gov.v1beta1.TextProposal",
                                "title": "Test Proposal",
                                "description": "Test Description",
                            },
                            "status": "PROPOSAL_STATUS_VOTING_PERIOD",
                            "final_tally_result": {
                                "yes": "0",
                                "abstain": "0",
                                "no": "0",
                                "no_with_veto": "0",
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
            assert "proposals" in result["data"]
            assert result["data"]["count"] == 1


class TestGetProposalTool:
    """Test get_proposal tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetProposalTool(context)

        assert tool.name == "get_proposal"
        assert "proposal" in tool.description.lower()
        assert tool.category == ToolCategory.GOVERNANCE
        assert tool.requires_wallet is False

    def test_validate_params_missing_proposal_id(self) -> None:
        """Test validation fails without proposal_id."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetProposalTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "proposal_id" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_proposal(self) -> None:
        """Test getting a specific proposal."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetProposalTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.gov = Mock()
            mock_client.gov.proposal = AsyncMock(
                return_value={
                    "proposal": {
                        "proposal_id": "1",
                        "content": {
                            "@type": "/cosmos.gov.v1beta1.TextProposal",
                            "title": "Test Proposal",
                            "description": "Test Description",
                        },
                        "status": "PROPOSAL_STATUS_VOTING_PERIOD",
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"proposal_id": "1"})

            assert result["success"] is True
            assert "proposal" in result["data"]


class TestSubmitProposalTool:
    """Test submit_proposal tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SubmitProposalTool(context)

        assert tool.name == "submit_proposal"
        assert "submit" in tool.description.lower()
        assert tool.category == ToolCategory.GOVERNANCE
        assert tool.requires_wallet is True

    def test_validate_params_missing_title(self) -> None:
        """Test validation fails without title."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SubmitProposalTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "description": "Test",
                "initial_deposit": "1000000",
            })

        assert "title" in str(exc_info.value.message).lower()

    def test_validate_params_missing_description(self) -> None:
        """Test validation fails without description."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = SubmitProposalTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "title": "Test",
                "initial_deposit": "1000000",
            })

        assert "description" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_submit_proposal(self) -> None:
        """Test submitting a proposal."""
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

        tool = SubmitProposalTool(context)

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
            with patch("mcp_scrt.tools.governance.create_signing_client") as mock_create:
                mock_signing = AsyncMock()
                mock_signing.submit_proposal = AsyncMock(
                    return_value={
                        "txhash": "ABC123",
                        "code": 0,
                    }
                )
                mock_create.return_value = mock_signing

                result = await tool.run({
                    "title": "Test Proposal",
                    "description": "Test Description",
                    "initial_deposit": "1000000",
                })

                assert result["success"] is True
                assert "txhash" in result["data"]


class TestDepositProposalTool:
    """Test deposit_proposal tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = DepositProposalTool(context)

        assert tool.name == "deposit_proposal"
        assert "deposit" in tool.description.lower()
        assert tool.category == ToolCategory.GOVERNANCE
        assert tool.requires_wallet is True

    def test_validate_params_missing_proposal_id(self) -> None:
        """Test validation fails without proposal_id."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = DepositProposalTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"amount": "1000000"})

        assert "proposal_id" in str(exc_info.value.message).lower()

    def test_validate_params_missing_amount(self) -> None:
        """Test validation fails without amount."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = DepositProposalTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"proposal_id": "1"})

        assert "amount" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_deposit_proposal(self) -> None:
        """Test depositing to a proposal."""
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

        tool = DepositProposalTool(context)

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
            with patch("mcp_scrt.tools.governance.create_signing_client") as mock_create:
                mock_signing = AsyncMock()
                mock_signing.deposit = AsyncMock(
                    return_value={
                        "txhash": "ABC123",
                        "code": 0,
                    }
                )
                mock_create.return_value = mock_signing

                result = await tool.run({
                    "proposal_id": "1",
                    "amount": "1000000",
                })

                assert result["success"] is True
                assert "txhash" in result["data"]


class TestVoteProposalTool:
    """Test vote_proposal tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = VoteProposalTool(context)

        assert tool.name == "vote_proposal"
        assert "vote" in tool.description.lower()
        assert tool.category == ToolCategory.GOVERNANCE
        assert tool.requires_wallet is True

    def test_validate_params_missing_proposal_id(self) -> None:
        """Test validation fails without proposal_id."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = VoteProposalTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"option": "VOTE_OPTION_YES"})

        assert "proposal_id" in str(exc_info.value.message).lower()

    def test_validate_params_missing_option(self) -> None:
        """Test validation fails without option."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = VoteProposalTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"proposal_id": "1"})

        assert "option" in str(exc_info.value.message).lower()

    def test_validate_params_invalid_option(self) -> None:
        """Test validation fails with invalid option."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = VoteProposalTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "proposal_id": "1",
                "option": "INVALID_OPTION",
            })

        assert "option" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_vote_proposal(self) -> None:
        """Test voting on a proposal."""
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

        tool = VoteProposalTool(context)

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
            with patch("mcp_scrt.tools.governance.create_signing_client") as mock_create:
                mock_signing = AsyncMock()
                mock_signing.vote = AsyncMock(
                    return_value={
                        "txhash": "ABC123",
                        "code": 0,
                    }
                )
                mock_create.return_value = mock_signing

                result = await tool.run({
                    "proposal_id": "1",
                    "option": "VOTE_OPTION_YES",
                })

                assert result["success"] is True
                assert "txhash" in result["data"]


class TestGetVoteTool:
    """Test get_vote tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetVoteTool(context)

        assert tool.name == "get_vote"
        assert "vote" in tool.description.lower()
        assert tool.category == ToolCategory.GOVERNANCE
        assert tool.requires_wallet is False

    def test_validate_params_missing_proposal_id(self) -> None:
        """Test validation fails without proposal_id."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetVoteTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"voter": "secret1..."})

        assert "proposal_id" in str(exc_info.value.message).lower()

    def test_validate_params_missing_voter(self) -> None:
        """Test validation fails without voter."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetVoteTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"proposal_id": "1"})

        assert "voter" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_vote(self) -> None:
        """Test getting a vote."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetVoteTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.gov = Mock()
            mock_client.gov.vote = AsyncMock(
                return_value={
                    "vote": {
                        "proposal_id": "1",
                        "voter": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
                        "option": "VOTE_OPTION_YES",
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({
                "proposal_id": "1",
                "voter": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
            })

            assert result["success"] is True
            assert "vote" in result["data"]


class TestGovernanceToolsIntegration:
    """Test governance tools working together."""

    @pytest.mark.asyncio
    async def test_all_governance_tools_have_correct_metadata(self) -> None:
        """Test all governance tools can be instantiated and have correct metadata."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tools = [
            GetProposalsTool(context),
            GetProposalTool(context),
            SubmitProposalTool(context),
            DepositProposalTool(context),
            VoteProposalTool(context),
            GetVoteTool(context),
        ]

        # All tools should be GOVERNANCE category
        for tool in tools:
            assert tool.category == ToolCategory.GOVERNANCE
            assert tool.name is not None
            assert tool.description is not None

        # All tool names should be unique
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))

        # Check which tools require wallet
        wallet_required = [tool for tool in tools if tool.requires_wallet]
        wallet_not_required = [tool for tool in tools if not tool.requires_wallet]

        # submit_proposal, deposit_proposal, vote_proposal should require wallet
        assert len(wallet_required) == 3
        assert len(wallet_not_required) == 3
