"""Network configuration resource for MCP.

This module provides a resource that exposes the current network configuration
including network type, RPC URL, chain ID, and gas prices.
"""

from typing import Dict, Any

from mcp_scrt.types import NetworkType
from mcp_scrt.constants import NETWORK_CONFIGS


def get_network_config_resource(network: NetworkType) -> Dict[str, Any]:
    """Get current network configuration as a resource.

    Provides comprehensive information about the configured network including
    its type, RPC endpoint, chain ID, and default gas prices.

    Args:
        network: The current network type

    Returns:
        Dictionary containing network configuration

    Example response:
        {
            "network_type": "testnet",
            "url": "https://lcd.testnet.secretsaturn.net",
            "chain_id": "pulsar-3",
            "gas_prices": {
                "denom": "uscrt",
                "amount": "0.25"
            },
            "is_testnet": true
        }
    """
    # Get network config
    config = NETWORK_CONFIGS.get(network)

    if not config:
        return {
            "network_type": str(network.value),
            "url": None,
            "chain_id": None,
            "gas_prices": None,
            "is_testnet": network == NetworkType.TESTNET,
            "error": "Network configuration not found",
        }

    # Build response
    response = {
        "network_type": str(network.value),
        "url": config.url,  # Using property alias
        "chain_id": config.chain_id,
        "gas_prices": config.gas_prices,
        "denom": config.denom,
        "decimals": config.decimals,
        "bech32_prefix": config.bech32_prefix,
        "is_testnet": network == NetworkType.TESTNET,
    }

    return response


def network_config_resource_function(network: NetworkType):
    """Resource function that returns network configuration.

    This function is meant to be decorated with @mcp.resource in the server setup.
    It provides a JSON representation of the current network configuration.

    Args:
        network: The current network type

    Returns:
        Dictionary with network config that will be JSON-serialized

    Usage:
        @mcp.resource("secret://network/config")
        def network_config():
            return network_config_resource_function(current_network)
    """
    return get_network_config_resource(network)
