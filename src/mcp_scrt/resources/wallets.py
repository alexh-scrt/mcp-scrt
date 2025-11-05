"""Wallets list resource for MCP.

This module provides a resource that exposes the list of wallets in the session
with their IDs and addresses (but not private keys for security).
"""

from typing import Dict, Any, List

from mcp_scrt.core.session import Session


def get_wallets_list_resource(session: Session) -> Dict[str, Any]:
    """Get list of session wallets as a resource.

    Provides a list of all wallets loaded in the session, including their
    wallet IDs and addresses. Private keys are never exposed for security.

    Args:
        session: The active session instance

    Returns:
        Dictionary containing wallets list and metadata

    Example response:
        {
            "wallets": [
                {
                    "wallet_id": "wallet1",
                    "address": "secret1...",
                    "active": true
                },
                {
                    "wallet_id": "wallet2",
                    "address": "secret1...",
                    "active": false
                }
            ],
            "count": 2,
            "active_wallet": "wallet1"
        }
    """
    # Get active wallet info
    active_wallet_id = None
    try:
        wallet_info = session.get_wallet()
        if wallet_info:
            active_wallet_id = wallet_info.wallet_id
    except Exception:
        active_wallet_id = None

    # Get all wallets
    wallets_list: List[Dict[str, Any]] = []
    try:
        wallets = session.list_wallets()
        for wallet in wallets:
            wallets_list.append({
                "wallet_id": wallet.wallet_id,
                "address": wallet.address,
                "active": wallet.wallet_id == active_wallet_id,
            })
    except Exception:
        wallets_list = []

    # Build response
    response = {
        "wallets": wallets_list,
        "count": len(wallets_list),
        "active_wallet": active_wallet_id,
    }

    return response


def wallets_list_resource_function(session: Session):
    """Resource function that returns wallets list.

    This function is meant to be decorated with @mcp.resource in the server setup.
    It provides a JSON representation of all wallets in the session.

    Args:
        session: The session instance to query

    Returns:
        Dictionary with wallets list that will be JSON-serialized

    Usage:
        @mcp.resource("secret://wallets/list")
        def wallets_list():
            return wallets_list_resource_function(session_instance)
    """
    return get_wallets_list_resource(session)
