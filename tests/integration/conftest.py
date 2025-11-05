"""Pytest configuration and fixtures for integration tests.

Provides common fixtures for integration testing including test wallets,
session setup, and cleanup utilities.
"""

import pytest
from unittest.mock import AsyncMock, patch

from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.tools.base import ToolExecutionContext
from mcp_scrt.types import NetworkType, WalletInfo


@pytest.fixture
def test_network():
    """Provide testnet network type for integration tests."""
    return NetworkType.TESTNET


@pytest.fixture
def session(test_network):
    """Create a session for integration tests."""
    session = Session(network=test_network)
    session.start()
    yield session
    # Cleanup: end session
    if session.is_active:
        session.end()


@pytest.fixture
def client_pool(test_network):
    """Create a client pool for integration tests."""
    pool = ClientPool(network=test_network, max_connections=5)
    yield pool
    # Cleanup: close pool connections
    pool.close()


@pytest.fixture
def tool_context(session, client_pool, test_network):
    """Create a tool execution context for integration tests."""
    return ToolExecutionContext(
        session=session,
        client_pool=client_pool,
        network=test_network,
    )


@pytest.fixture
def test_wallet():
    """Provide a test wallet for integration tests.

    Note: This is a mock wallet for testing. In real integration tests,
    you would use a real testnet wallet with test funds.
    """
    return WalletInfo(
        wallet_id="integration_test_wallet",
        address="secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
    )


@pytest.fixture
def test_wallet_with_funds():
    """Provide a test wallet that has testnet funds.

    Note: This is a mock wallet. In real integration tests, you would
    load a real wallet with testnet funds from a faucet.
    """
    return WalletInfo(
        wallet_id="funded_test_wallet",
        address="secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
    )


@pytest.fixture
def recipient_address():
    """Provide a recipient address for transfer tests."""
    return "secret1recipientrecipientrecipientrecipientrecip"


@pytest.fixture
def mock_signing_client():
    """Provide a mock signing client for integration tests.

    This mocks blockchain transactions without actually broadcasting them.
    """
    mock_client = AsyncMock()

    # Mock send transaction
    mock_client.send = AsyncMock(
        return_value={
            "txhash": "INTEGRATION_TEST_TXHASH_SEND",
            "code": 0,
            "height": 12345,
        }
    )

    # Mock delegate transaction
    mock_client.delegate = AsyncMock(
        return_value={
            "txhash": "INTEGRATION_TEST_TXHASH_DELEGATE",
            "code": 0,
            "height": 12346,
        }
    )

    # Mock undelegate transaction
    mock_client.undelegate = AsyncMock(
        return_value={
            "txhash": "INTEGRATION_TEST_TXHASH_UNDELEGATE",
            "code": 0,
            "height": 12347,
        }
    )

    # Mock contract upload
    mock_client.upload = AsyncMock(
        return_value={
            "txhash": "INTEGRATION_TEST_TXHASH_UPLOAD",
            "code": 0,
            "code_id": 999,
        }
    )

    # Mock contract instantiate
    mock_client.instantiate = AsyncMock(
        return_value={
            "txhash": "INTEGRATION_TEST_TXHASH_INSTANTIATE",
            "code": 0,
            "contract_address": "secret1contractcontractcontractcontractcontra",
        }
    )

    # Mock contract execute
    mock_client.execute = AsyncMock(
        return_value={
            "txhash": "INTEGRATION_TEST_TXHASH_EXECUTE",
            "code": 0,
        }
    )

    return mock_client


@pytest.fixture
def mock_lcd_client():
    """Provide a mock LCD client for query operations.

    This mocks blockchain queries without actually hitting the network.
    """
    mock_client = AsyncMock()

    # Mock bank balance query
    mock_client.bank.balance = AsyncMock(
        return_value={
            "balances": [
                {"denom": "uscrt", "amount": "1000000000"}
            ]
        }
    )

    # Mock validators query
    mock_client.staking.validators = AsyncMock(
        return_value={
            "validators": [
                {
                    "operator_address": "secretvaloper1validatorvalidatorvalidatorvalida",
                    "description": {"moniker": "Test Validator"},
                    "tokens": "1000000000000",
                    "status": "BOND_STATUS_BONDED",
                    "jailed": False,
                    "commission": {
                        "commission_rates": {
                            "rate": "0.100000000000000000"
                        }
                    }
                }
            ]
        }
    )

    # Mock transaction query
    mock_client.tx.transaction = AsyncMock(
        return_value={
            "txhash": "TEST_TXHASH",
            "code": 0,
            "height": 12345,
            "tx": {},
            "logs": [],
        }
    )

    # Mock contract query
    mock_client.wasm.contract_query = AsyncMock(
        return_value={"count": 42}
    )

    return mock_client


@pytest.fixture(autouse=True)
def cleanup_test_wallets(session):
    """Automatically cleanup test wallets after each test."""
    yield
    # Remove any test wallets created during the test
    try:
        wallets = session.list_wallets()
        for wallet in wallets:
            if wallet.wallet_id.startswith("integration_test_") or wallet.wallet_id.startswith("test_"):
                session.remove_wallet(wallet.wallet_id)
    except Exception:
        # Session might not be active, ignore
        pass
