"""Pytest configuration and fixtures for Secret MCP Server tests."""

import pytest


@pytest.fixture
def sample_testnet_config():
    """Provide a sample testnet configuration."""
    from mcp_scrt.types import NetworkConfig, NetworkType

    return NetworkConfig(
        network_type=NetworkType.TESTNET,
        url="http://testnet.securesecrets.org:1317",
        chain_id="pulsar-2",
        gas_prices="0.25uscrt",
        gas_adjustment=1.0,
    )


@pytest.fixture
def sample_wallet_info():
    """Provide sample wallet information."""
    from mcp_scrt.types import WalletInfo

    return WalletInfo(
        wallet_id="test-wallet",
        address="secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
        account=0,
        index=0,
    )
