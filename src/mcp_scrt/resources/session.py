"""Session state resource for MCP.

This module provides a resource that exposes the current session state
including network configuration, active wallet, and wallet count.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from mcp_scrt.core.session import Session


def get_session_state_resource(session: Session) -> Dict[str, Any]:
    """Get current session state as a resource.

    Provides comprehensive information about the current MCP session state
    including network configuration, active wallet, wallet count, and metadata.

    Args:
        session: The active session instance

    Returns:
        Dictionary containing session state information

    Example response:
        {
            "network": "testnet",
            "active_wallet": {
                "wallet_id": "my_wallet",
                "address": "secret1..."
            },
            "wallet_count": 3,
            "metadata": {
                "session_active": true,
                "timestamp": "2025-11-04T..."
            }
        }
    """
    # Get active wallet info
    active_wallet: Optional[Dict[str, str]] = None
    try:
        wallet_info = session.get_wallet()
        if wallet_info:
            active_wallet = {
                "wallet_id": wallet_info.wallet_id,
                "address": wallet_info.address,
            }
    except Exception:
        # No active wallet or session not started
        active_wallet = None

    # Get wallet count
    wallet_count = 0
    try:
        wallets = session.list_wallets()
        wallet_count = len(wallets)
    except Exception:
        wallet_count = 0

    # Build state response
    state = {
        "network": str(session.network.value) if hasattr(session, "network") else "unknown",
        "active_wallet": active_wallet,
        "wallet_count": wallet_count,
        "metadata": {
            "session_active": session.is_active if hasattr(session, "is_active") else False,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }

    return state


def session_state_resource_function(session: Session):
    """Resource function that returns session state.

    This function is meant to be decorated with @mcp.resource in the server setup.
    It provides a JSON representation of the current session state.

    Args:
        session: The session instance to query

    Returns:
        Dictionary with session state that will be JSON-serialized

    Usage:
        @mcp.resource("secret://session/state")
        def session_state():
            return session_state_resource_function(session_instance)
    """
    return get_session_state_resource(session)
