"""Network tools for Secret Network blockchain interaction.

This module provides tools for network configuration and information.
"""

from typing import Any, Dict

from mcp_scrt.tools.base import BaseTool, ToolCategory
from mcp_scrt.types import NetworkType
from mcp_scrt.utils.errors import ValidationError, NetworkError
from mcp_scrt.config import get_settings
from mcp_scrt.constants import GAS_PRICES, NETWORK_CONFIGS


class ConfigureNetworkTool(BaseTool):
    """Configure network settings (testnet/mainnet/custom).

    This tool allows switching between different Secret Network networks.
    """

    @property
    def name(self) -> str:
        return "configure_network"

    @property
    def description(self) -> str:
        return (
            "Configure network settings for Secret Network. "
            "Switch between testnet, mainnet, or configure a custom network."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.NETWORK

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate network configuration parameters.

        Args:
            params: Must contain 'network' (testnet/mainnet/custom)

        Raises:
            ValidationError: If parameters are invalid
        """
        if "network" not in params:
            raise ValidationError(
                message="Missing required parameter: network",
                details={"required_params": ["network"]},
                suggestions=[
                    "Provide 'network' parameter with value: testnet, mainnet, or custom",
                    "Example: {'network': 'testnet'}",
                ],
            )

        network = params["network"].lower()
        valid_networks = ["testnet", "mainnet", "custom"]

        if network not in valid_networks:
            raise ValidationError(
                message=f"Invalid network: {network}",
                details={
                    "provided": network,
                    "valid_networks": valid_networks,
                },
                suggestions=[
                    f"Use one of: {', '.join(valid_networks)}",
                    "testnet: Secret Network testnet (pulsar-3)",
                    "mainnet: Secret Network mainnet (secret-4)",
                ],
            )

        # If custom, validate URL and chain_id
        if network == "custom":
            if "lcd_url" not in params:
                raise ValidationError(
                    message="Custom network requires 'lcd_url' parameter",
                    details={"required_for_custom": ["lcd_url", "chain_id"]},
                    suggestions=[
                        "Provide LCD endpoint URL",
                        "Example: {'network': 'custom', 'lcd_url': 'https://lcd.example.com', 'chain_id': 'secret-custom-1'}",
                    ],
                )

            if "chain_id" not in params:
                raise ValidationError(
                    message="Custom network requires 'chain_id' parameter",
                    details={"required_for_custom": ["lcd_url", "chain_id"]},
                    suggestions=[
                        "Provide chain ID",
                        "Example: {'network': 'custom', 'lcd_url': 'https://lcd.example.com', 'chain_id': 'secret-custom-1'}",
                    ],
                )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute network configuration.

        Args:
            params: Network configuration parameters

        Returns:
            Configured network information
        """
        network = params["network"].lower()
        settings = get_settings()

        if network == "custom":
            lcd_url = params["lcd_url"]
            chain_id = params["chain_id"]

            return {
                "network": "custom",
                "lcd_url": lcd_url,
                "chain_id": chain_id,
                "status": "configured",
                "message": f"Custom network configured: {chain_id}",
            }

        # Get network configuration
        network_type = NetworkType.TESTNET if network == "testnet" else NetworkType.MAINNET
        config = NETWORK_CONFIGS[network_type]

        return {
            "network": network,
            "lcd_url": config.lcd_url,
            "chain_id": config.chain_id,
            "status": "configured",
            "message": f"Network configured: {network} ({config.chain_id})",
        }


class GetNetworkInfoTool(BaseTool):
    """Get current network information.

    This tool returns information about the currently configured network.
    """

    @property
    def name(self) -> str:
        return "get_network_info"

    @property
    def description(self) -> str:
        return (
            "Get current network information including network type, "
            "chain ID, LCD URL, and configuration details."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.NETWORK

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters (no parameters required)."""
        # No parameters required for this tool
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get network info.

        Returns:
            Current network information
        """
        network = self.context.network
        config = NETWORK_CONFIGS[network]
        settings = get_settings()

        return {
            "network": network.value,
            "chain_id": config.chain_id,
            "lcd_url": config.lcd_url,
            "bech32_prefix": config.bech32_prefix,
            "coin_type": config.coin_type,
            "denom": config.denom,
            "decimals": config.decimals,
            "description": f"Secret Network {network.value}",
        }


class GetGasPricesTool(BaseTool):
    """Get current gas prices.

    This tool returns the current gas prices for transactions.
    """

    @property
    def name(self) -> str:
        return "get_gas_prices"

    @property
    def description(self) -> str:
        return (
            "Get current gas prices for Secret Network transactions. "
            "Returns default, low, average, and high gas price options."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.NETWORK

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters (no parameters required)."""
        # No parameters required for this tool
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get gas prices.

        Returns:
            Current gas prices
        """
        network = self.context.network
        config = NETWORK_CONFIGS[network]

        return {
            "denom": config.denom,
            "gas_prices": {
                "default": GAS_PRICES["DEFAULT"],
                "low": GAS_PRICES["LOW"],
                "average": GAS_PRICES["AVERAGE"],
                "high": GAS_PRICES["HIGH"],
            },
            "description": "Gas prices in uscrt per gas unit",
            "recommendation": "Use 'average' for normal transactions, 'high' for urgent transactions",
        }


class HealthCheckTool(BaseTool):
    """Check network connectivity and health.

    This tool performs a health check on the network connection.
    """

    @property
    def name(self) -> str:
        return "health_check"

    @property
    def description(self) -> str:
        return (
            "Check Secret Network connectivity and health. "
            "Verifies connection to LCD endpoint and node availability."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.NETWORK

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters (no parameters required)."""
        # No parameters required for this tool
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute health check.

        Returns:
            Network health status
        """
        network = self.context.network
        config = NETWORK_CONFIGS[network]

        try:
            # Try to get node info from the client pool
            with self.context.client_pool.get_client() as client:
                node_info = await client.tendermint.node_info()

                return {
                    "status": "healthy",
                    "network": network.value,
                    "lcd_url": config.lcd_url,
                    "chain_id": config.chain_id,
                    "node_connected": True,
                    "node_info": {
                        "network": node_info.get("node_info", {}).get("network"),
                        "version": node_info.get("application_version", {}).get("version"),
                    },
                    "message": "Network is healthy and responsive",
                }

        except Exception as e:
            # Health check should not fail completely, just report unhealthy
            self._logger.warning(
                "Health check failed",
                error=str(e),
                network=network.value,
            )

            return {
                "status": "unhealthy",
                "network": network.value,
                "lcd_url": config.lcd_url,
                "chain_id": config.chain_id,
                "node_connected": False,
                "error": str(e),
                "message": "Unable to connect to network",
                "suggestions": [
                    "Check your internet connection",
                    "Verify the LCD endpoint is accessible",
                    "Try switching to a different network",
                ],
            }
