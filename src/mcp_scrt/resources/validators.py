"""Top validators resource for MCP.

This module provides a resource that exposes the top validators by voting power
with caching for performance.
"""

from typing import Dict, Any, List
import asyncio

from mcp_scrt.sdk.client import ClientPool


async def get_top_validators_resource(client_pool: ClientPool, limit: int = 10) -> Dict[str, Any]:
    """Get top validators by voting power as a resource.

    Provides information about the top validators sorted by voting power,
    including their operator address, moniker, voting power, and commission rates.

    This resource should be cached for 5 minutes to reduce network load.

    Args:
        client_pool: The client pool for making API calls
        limit: Maximum number of validators to return (default: 10)

    Returns:
        Dictionary containing top validators list

    Example response:
        {
            "validators": [
                {
                    "operator_address": "secretvaloper1...",
                    "moniker": "Validator Name",
                    "voting_power": "1000000",
                    "commission": "0.10",
                    "status": "BOND_STATUS_BONDED"
                }
            ],
            "count": 10,
            "total_voting_power": "50000000"
        }
    """
    try:
        with client_pool.get_client() as client:
            # Query validators
            response = await client.staking.validators(
                status="BOND_STATUS_BONDED",
                pagination_limit=limit,
            )

            validators_data = response.get("validators", [])

            # Extract relevant validator information
            validators_list: List[Dict[str, Any]] = []
            total_voting_power = 0

            for validator in validators_data:
                # Extract voting power (tokens delegated)
                voting_power = int(validator.get("tokens", "0"))
                total_voting_power += voting_power

                # Extract commission rate
                commission_rates = validator.get("commission", {}).get("commission_rates", {})
                commission_rate = commission_rates.get("rate", "0")

                validators_list.append({
                    "operator_address": validator.get("operator_address", ""),
                    "moniker": validator.get("description", {}).get("moniker", "Unknown"),
                    "voting_power": str(voting_power),
                    "commission": commission_rate,
                    "status": validator.get("status", ""),
                    "jailed": validator.get("jailed", False),
                })

            # Sort by voting power (descending)
            validators_list.sort(key=lambda v: int(v["voting_power"]), reverse=True)

            return {
                "validators": validators_list,
                "count": len(validators_list),
                "total_voting_power": str(total_voting_power),
            }

    except Exception as e:
        return {
            "validators": [],
            "count": 0,
            "total_voting_power": "0",
            "error": f"Failed to fetch validators: {str(e)}",
        }


def top_validators_resource_function(client_pool: ClientPool, limit: int = 10):
    """Resource function that returns top validators.

    This function is meant to be decorated with @mcp.resource in the server setup.
    It provides a JSON representation of the top validators by voting power.

    Note: This should be cached for ~5 minutes to reduce network load.

    Args:
        client_pool: The client pool for API calls
        limit: Maximum number of validators to return

    Returns:
        Dictionary with validators list that will be JSON-serialized

    Usage:
        @mcp.resource("secret://validators/top")
        async def top_validators():
            return await top_validators_resource_function(client_pool_instance)
    """
    # Since this is async, we need to run it in an event loop
    return asyncio.run(get_top_validators_resource(client_pool, limit))
