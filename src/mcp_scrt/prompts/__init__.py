"""MCP prompts for Secret Network guided operations.

This package contains prompt templates for helping users interact with
the Secret Network MCP server.
"""

from mcp_scrt.prompts.guide import secret_network_guide
from mcp_scrt.prompts.contracts import smart_contracts_guide

__all__ = [
    "secret_network_guide",
    "smart_contracts_guide",
]
