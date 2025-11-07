"""Governance tools for Secret Network governance operations.

This module provides tools for proposals, voting, and deposits.
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
        async def submit_proposal(self, content: dict, initial_deposit: list):
            return {"txhash": "mock_hash", "code": 0}

        async def deposit(self, proposal_id: int, amount: list):
            return {"txhash": "mock_hash", "code": 0}

        async def vote(self, proposal_id: int, option: str):
            return {"txhash": "mock_hash", "code": 0}

    return MockSigningClient()


class GetProposalsTool(BaseTool):
    """Get governance proposals.

    Query all governance proposals with optional status filter.
    """

    @property
    def name(self) -> str:
        return "get_proposals"

    @property
    def description(self) -> str:
        return (
            "Get all governance proposals. "
            "Optionally filter by status (voting, passed, rejected, deposit)."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.GOVERNANCE

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get proposals parameters.

        Args:
            params: Optionally contains 'status'

        Raises:
            ValidationError: If parameters are invalid
        """
        # Status is optional, but if provided should be valid
        if "status" in params:
            status = params["status"]
            valid_statuses = [
                "PROPOSAL_STATUS_DEPOSIT_PERIOD",
                "PROPOSAL_STATUS_VOTING_PERIOD",
                "PROPOSAL_STATUS_PASSED",
                "PROPOSAL_STATUS_REJECTED",
                "PROPOSAL_STATUS_FAILED",
            ]
            if status not in valid_statuses:
                raise ValidationError(
                    message=f"Invalid status: {status}",
                    details={"provided": status, "valid_values": valid_statuses},
                    suggestions=[
                        "Use one of: PROPOSAL_STATUS_DEPOSIT_PERIOD, PROPOSAL_STATUS_VOTING_PERIOD, "
                        "PROPOSAL_STATUS_PASSED, PROPOSAL_STATUS_REJECTED, PROPOSAL_STATUS_FAILED",
                    ],
                )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get proposals.

        Args:
            params: Parameters optionally including status

        Returns:
            List of proposals
        """
        status = params.get("status", "")

        try:
            # Query proposals using client pool
            with self.context.client_pool.get_client() as client:
                proposals_response = client.gov.proposals(
                    proposal_status=status
                )

                proposals = proposals_response.get("proposals", [])
                pagination = proposals_response.get("pagination", {})

                return {
                    "proposals": proposals,
                    "count": len(proposals),
                    "pagination": pagination,
                    "message": f"Retrieved {len(proposals)} proposal(s)",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get proposals: {str(e)}",
                details={"status": status, "error": str(e)},
                suggestions=[
                    "Verify network connectivity",
                    "Try again later",
                ],
            )


class GetProposalTool(BaseTool):
    """Get specific proposal.

    Query details for a specific proposal by ID.
    """

    @property
    def name(self) -> str:
        return "get_proposal"

    @property
    def description(self) -> str:
        return (
            "Get details for a specific proposal by ID. "
            "Returns proposal content, status, voting results, and timing."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.GOVERNANCE

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get proposal parameters.

        Args:
            params: Must contain 'proposal_id'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "proposal_id" not in params:
            raise ValidationError(
                message="Missing required parameter: proposal_id",
                details={"required_params": ["proposal_id"]},
                suggestions=[
                    "Provide 'proposal_id' parameter",
                    "Example: {'proposal_id': '1'}",
                ],
            )

        proposal_id = params["proposal_id"]
        if not isinstance(proposal_id, (str, int)):
            raise ValidationError(
                message="Invalid proposal_id: must be a string or integer",
                details={"provided": proposal_id},
                suggestions=[
                    "Provide a valid proposal ID",
                    "Example: {'proposal_id': '1'}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get proposal.

        Args:
            params: Parameters including proposal_id

        Returns:
            Proposal information
        """
        proposal_id = str(params["proposal_id"])

        try:
            # Query proposal using client pool
            with self.context.client_pool.get_client() as client:
                proposal_response = client.gov.proposal(proposal_id)

                proposal = proposal_response.get("proposal", {})

                return {
                    "proposal_id": proposal_id,
                    "proposal": proposal,
                    "message": f"Proposal {proposal_id} retrieved successfully",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get proposal: {str(e)}",
                details={"proposal_id": proposal_id, "error": str(e)},
                suggestions=[
                    "Check that the proposal ID is correct",
                    "Verify the proposal exists",
                    "Verify network connectivity",
                ],
            )


class SubmitProposalTool(BaseTool):
    """Submit governance proposal.

    Submit a new governance proposal.
    """

    @property
    def name(self) -> str:
        return "submit_proposal"

    @property
    def description(self) -> str:
        return (
            "Submit a new governance proposal. "
            "Requires active wallet. Must include initial deposit."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.GOVERNANCE

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet to sign transaction

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate submit proposal parameters.

        Args:
            params: Must contain 'title', 'description', 'initial_deposit'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "title" not in params:
            raise ValidationError(
                message="Missing required parameter: title",
                details={
                    "required_params": ["title", "description", "initial_deposit"]
                },
                suggestions=[
                    "Provide 'title' parameter",
                    "Example: {'title': 'My Proposal', 'description': '...', 'initial_deposit': '1000000'}",
                ],
            )

        if "description" not in params:
            raise ValidationError(
                message="Missing required parameter: description",
                details={
                    "required_params": ["title", "description", "initial_deposit"]
                },
                suggestions=[
                    "Provide 'description' parameter",
                    "Example: {'title': 'My Proposal', 'description': '...', 'initial_deposit': '1000000'}",
                ],
            )

        if "initial_deposit" not in params:
            raise ValidationError(
                message="Missing required parameter: initial_deposit",
                details={
                    "required_params": ["title", "description", "initial_deposit"]
                },
                suggestions=[
                    "Provide 'initial_deposit' parameter",
                    "Example: {'title': 'My Proposal', 'description': '...', 'initial_deposit': '1000000'}",
                ],
            )

        # Validate initial deposit
        validate_amount(params["initial_deposit"], params.get("denom", "uscrt"))

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute submit proposal.

        Args:
            params: Parameters including title, description, initial_deposit

        Returns:
            Transaction result
        """
        title = params["title"]
        description = params["description"]
        initial_deposit = params["initial_deposit"]
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
        proposer = wallet_info.address

        try:
            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            # Create proposal content
            content = {
                "@type": "/cosmos.gov.v1beta1.TextProposal",
                "title": title,
                "description": description,
            }

            # Submit proposal
            result = await signing_client.submit_proposal(
                content=content,
                initial_deposit=[{"denom": denom, "amount": initial_deposit}],
            )

            return {
                "title": title,
                "proposer": proposer,
                "initial_deposit": initial_deposit,
                "denom": denom,
                "txhash": result.get("txhash"),
                "message": f"Successfully submitted proposal: {title}",
            }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to submit proposal: {str(e)}",
                details={
                    "title": title,
                    "proposer": proposer,
                    "error": str(e),
                },
                suggestions=[
                    "Check that you have sufficient balance for the deposit",
                    "Verify network connectivity",
                ],
            )


class DepositProposalTool(BaseTool):
    """Deposit to proposal.

    Deposit tokens to a governance proposal.
    """

    @property
    def name(self) -> str:
        return "deposit_proposal"

    @property
    def description(self) -> str:
        return (
            "Deposit tokens to a governance proposal. "
            "Requires active wallet. Helps proposal reach minimum deposit."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.GOVERNANCE

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet to sign transaction

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate deposit proposal parameters.

        Args:
            params: Must contain 'proposal_id' and 'amount'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "proposal_id" not in params:
            raise ValidationError(
                message="Missing required parameter: proposal_id",
                details={"required_params": ["proposal_id", "amount"]},
                suggestions=[
                    "Provide 'proposal_id' parameter",
                    "Example: {'proposal_id': '1', 'amount': '1000000'}",
                ],
            )

        if "amount" not in params:
            raise ValidationError(
                message="Missing required parameter: amount",
                details={"required_params": ["proposal_id", "amount"]},
                suggestions=[
                    "Provide 'amount' parameter",
                    "Example: {'proposal_id': '1', 'amount': '1000000'}",
                ],
            )

        # Validate amount
        validate_amount(params["amount"], params.get("denom", "uscrt"))

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deposit proposal.

        Args:
            params: Parameters including proposal_id, amount, optional denom

        Returns:
            Transaction result
        """
        proposal_id = int(params["proposal_id"])
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
        depositor = wallet_info.address

        try:
            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            # Deposit to proposal
            result = await signing_client.deposit(
                proposal_id=proposal_id,
                amount=[{"denom": denom, "amount": amount}],
            )

            return {
                "proposal_id": proposal_id,
                "depositor": depositor,
                "amount": amount,
                "denom": denom,
                "txhash": result.get("txhash"),
                "message": f"Successfully deposited {amount} {denom} to proposal {proposal_id}",
            }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to deposit to proposal: {str(e)}",
                details={
                    "proposal_id": proposal_id,
                    "depositor": depositor,
                    "amount": amount,
                    "error": str(e),
                },
                suggestions=[
                    "Check that you have sufficient balance",
                    "Verify the proposal exists and is in deposit period",
                    "Verify network connectivity",
                ],
            )


class VoteProposalTool(BaseTool):
    """Vote on proposal.

    Vote on a governance proposal.
    """

    @property
    def name(self) -> str:
        return "vote_proposal"

    @property
    def description(self) -> str:
        return (
            "Vote on a governance proposal. "
            "Requires active wallet. Options: YES, NO, ABSTAIN, NO_WITH_VETO."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.GOVERNANCE

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet to sign transaction

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate vote proposal parameters.

        Args:
            params: Must contain 'proposal_id' and 'option'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "proposal_id" not in params:
            raise ValidationError(
                message="Missing required parameter: proposal_id",
                details={"required_params": ["proposal_id", "option"]},
                suggestions=[
                    "Provide 'proposal_id' parameter",
                    "Example: {'proposal_id': '1', 'option': 'VOTE_OPTION_YES'}",
                ],
            )

        if "option" not in params:
            raise ValidationError(
                message="Missing required parameter: option",
                details={"required_params": ["proposal_id", "option"]},
                suggestions=[
                    "Provide 'option' parameter",
                    "Example: {'proposal_id': '1', 'option': 'VOTE_OPTION_YES'}",
                ],
            )

        # Validate vote option
        option = params["option"]
        valid_options = [
            "VOTE_OPTION_YES",
            "VOTE_OPTION_NO",
            "VOTE_OPTION_ABSTAIN",
            "VOTE_OPTION_NO_WITH_VETO",
        ]
        if option not in valid_options:
            raise ValidationError(
                message=f"Invalid option: {option}",
                details={"provided": option, "valid_values": valid_options},
                suggestions=[
                    "Use one of: VOTE_OPTION_YES, VOTE_OPTION_NO, VOTE_OPTION_ABSTAIN, VOTE_OPTION_NO_WITH_VETO",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute vote proposal.

        Args:
            params: Parameters including proposal_id and option

        Returns:
            Transaction result
        """
        proposal_id = int(params["proposal_id"])
        option = params["option"]

        # Get active wallet
        wallet_info = self.context.session.get_wallet()
        if not wallet_info:
            raise WalletError(
                message="No active wallet set",
                details={},
                suggestions=["Load a wallet using load_wallet"],
            )

        wallet_name = wallet_info.wallet_id
        voter = wallet_info.address

        try:
            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            # Vote on proposal
            result = await signing_client.vote(
                proposal_id=proposal_id, option=option
            )

            return {
                "proposal_id": proposal_id,
                "voter": voter,
                "option": option,
                "txhash": result.get("txhash"),
                "message": f"Successfully voted {option} on proposal {proposal_id}",
            }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to vote on proposal: {str(e)}",
                details={
                    "proposal_id": proposal_id,
                    "voter": voter,
                    "option": option,
                    "error": str(e),
                },
                suggestions=[
                    "Verify the proposal exists and is in voting period",
                    "Check that you haven't already voted",
                    "Verify network connectivity",
                ],
            )


class GetVoteTool(BaseTool):
    """Get vote.

    Query a specific vote for a proposal.
    """

    @property
    def name(self) -> str:
        return "get_vote"

    @property
    def description(self) -> str:
        return (
            "Get a vote for a specific proposal and voter. "
            "Returns the vote option if the voter has voted."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.GOVERNANCE

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get vote parameters.

        Args:
            params: Must contain 'proposal_id' and 'voter'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "proposal_id" not in params:
            raise ValidationError(
                message="Missing required parameter: proposal_id",
                details={"required_params": ["proposal_id", "voter"]},
                suggestions=[
                    "Provide 'proposal_id' parameter",
                    "Example: {'proposal_id': '1', 'voter': 'secret1...'}",
                ],
            )

        if "voter" not in params:
            raise ValidationError(
                message="Missing required parameter: voter",
                details={"required_params": ["proposal_id", "voter"]},
                suggestions=[
                    "Provide 'voter' parameter",
                    "Example: {'proposal_id': '1', 'voter': 'secret1...'}",
                ],
            )

        # Validate voter address
        validate_address(params["voter"])

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get vote.

        Args:
            params: Parameters including proposal_id and voter

        Returns:
            Vote information
        """
        proposal_id = str(params["proposal_id"])
        voter = params["voter"]

        try:
            # Query vote using client pool
            with self.context.client_pool.get_client() as client:
                vote_response = client.gov.vote(
                    proposal_id=proposal_id, voter=voter
                )

                vote = vote_response.get("vote", {})

                return {
                    "proposal_id": proposal_id,
                    "voter": voter,
                    "vote": vote,
                    "message": f"Retrieved vote for proposal {proposal_id} by {voter}",
                }

        except Exception as e:
            # If vote not found, return appropriate message
            error_msg = str(e).lower()
            if "not found" in error_msg or "does not exist" in error_msg:
                return {
                    "proposal_id": proposal_id,
                    "voter": voter,
                    "vote": None,
                    "message": f"No vote found for proposal {proposal_id} by {voter}",
                }

            raise NetworkError(
                message=f"Failed to get vote: {str(e)}",
                details={"proposal_id": proposal_id, "voter": voter, "error": str(e)},
                suggestions=[
                    "Check that the proposal ID is correct",
                    "Verify the voter address is valid",
                    "Verify network connectivity",
                ],
            )
