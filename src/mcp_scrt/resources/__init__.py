"""MCP resources for Secret Network state and configuration.

This package contains resource handlers that expose read-only data
to MCP clients, including session state, wallet list, network config,
and validator information.
"""

from mcp_scrt.resources.session import (
    get_session_state_resource,
    session_state_resource_function,
)
from mcp_scrt.resources.wallets import (
    get_wallets_list_resource,
    wallets_list_resource_function,
)
from mcp_scrt.resources.network import (
    get_network_config_resource,
    network_config_resource_function,
)
from mcp_scrt.resources.validators import (
    get_top_validators_resource,
    top_validators_resource_function,
)

__all__ = [
    # Session resources
    "get_session_state_resource",
    "session_state_resource_function",
    # Wallets resources
    "get_wallets_list_resource",
    "wallets_list_resource_function",
    # Network resources
    "get_network_config_resource",
    "network_config_resource_function",
    # Validators resources
    "get_top_validators_resource",
    "top_validators_resource_function",
]
