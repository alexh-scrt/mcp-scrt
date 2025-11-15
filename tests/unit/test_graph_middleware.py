import pytest
from unittest.mock import Mock, AsyncMock
from mcp_scrt.middleware.graph_middleware import GraphMiddleware


@pytest.fixture
def mock_graph_service():
    """Mock graph service."""
    graph = Mock()
    graph.record_delegation = AsyncMock()
    graph.record_transfer = AsyncMock()
    graph.record_vote = AsyncMock()
    graph.record_contract_execution = AsyncMock()
    return graph


@pytest.fixture
def middleware(mock_graph_service):
    """Create graph middleware with mock graph service."""
    return GraphMiddleware(graph_service=mock_graph_service, async_mode=False)


def test_should_record(middleware):
    """Test determining if operation should be recorded."""
    # Should record
    assert middleware._should_record("secret_delegate") is True
    assert middleware._should_record("secret_send_tokens") is True

    # Should not record
    assert middleware._should_record("secret_get_balance") is False
    assert middleware._should_record("secret_create_wallet") is False


@pytest.mark.anyio
async def test_after_execute_skips_on_error(middleware, mock_graph_service):
    """Test after_execute doesn't record on error."""
    await middleware.after_execute(
        tool_name="secret_delegate",
        params={},
        result={},
        error=Exception("Test error")
    )

    mock_graph_service.record_delegation.assert_not_called()


@pytest.mark.anyio
async def test_after_execute_skips_non_graph_operations(middleware, mock_graph_service):
    """Test after_execute skips non-graph operations."""
    await middleware.after_execute(
        tool_name="secret_get_balance",
        params={},
        result={},
        error=None
    )

    mock_graph_service.record_delegation.assert_not_called()


@pytest.mark.anyio
async def test_record_delegation(middleware, mock_graph_service):
    """Test recording a delegation."""
    await middleware.after_execute(
        tool_name="secret_delegate",
        params={
            "address": "secret1abc",
            "validator_address": "secretvaloper1xyz",
            "amount": "1000000"
        },
        result={"tx_hash": "ABC123"},
        error=None
    )

    mock_graph_service.record_delegation.assert_called_once()
    call_args = mock_graph_service.record_delegation.call_args[1]
    assert call_args["delegator_address"] == "secret1abc"
    assert call_args["validator_address"] == "secretvaloper1xyz"
    assert call_args["tx_hash"] == "ABC123"


@pytest.mark.anyio
async def test_record_transfer(middleware, mock_graph_service):
    """Test recording a transfer."""
    await middleware.after_execute(
        tool_name="secret_send_tokens",
        params={
            "address": "secret1abc",
            "recipient": "secret1def",
            "amount": "500000"
        },
        result={"tx_hash": "XYZ789"},
        error=None
    )

    mock_graph_service.record_transfer.assert_called_once()
    call_args = mock_graph_service.record_transfer.call_args[1]
    assert call_args["from_address"] == "secret1abc"
    assert call_args["to_address"] == "secret1def"
    assert call_args["tx_hash"] == "XYZ789"


@pytest.mark.anyio
async def test_record_vote(middleware, mock_graph_service):
    """Test recording a vote."""
    await middleware.after_execute(
        tool_name="secret_vote_proposal",
        params={
            "address": "secret1abc",
            "proposal_id": 42,
            "vote_option": "YES"
        },
        result={"tx_hash": "VOTE123"},
        error=None
    )

    mock_graph_service.record_vote.assert_called_once()
    call_args = mock_graph_service.record_vote.call_args[1]
    assert call_args["voter_address"] == "secret1abc"
    assert call_args["proposal_id"] == 42
    assert call_args["vote_option"] == "YES"


@pytest.mark.anyio
async def test_record_contract_execution(middleware, mock_graph_service):
    """Test recording a contract execution."""
    await middleware.after_execute(
        tool_name="secret_execute_contract",
        params={
            "address": "secret1abc",
            "contract_address": "secret1contract",
            "execute_msg": {"method": "transfer"}
        },
        result={"tx_hash": "CONTRACT123"},
        error=None
    )

    mock_graph_service.record_contract_execution.assert_called_once()
    call_args = mock_graph_service.record_contract_execution.call_args[1]
    assert call_args["executor_address"] == "secret1abc"
    assert call_args["contract_address"] == "secret1contract"


@pytest.mark.anyio
async def test_error_isolation(middleware, mock_graph_service):
    """Test that graph errors don't propagate."""
    # Make graph service raise an error
    mock_graph_service.record_delegation.side_effect = Exception("Graph error")

    # Should not raise exception
    await middleware.after_execute(
        tool_name="secret_delegate",
        params={
            "address": "secret1abc",
            "validator_address": "secretvaloper1xyz",
            "amount": "1000000"
        },
        result={"tx_hash": "ABC123"},
        error=None
    )

    # Error should be logged but not raised
    mock_graph_service.record_delegation.assert_called_once()
