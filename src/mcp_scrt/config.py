"""Configuration management for Secret MCP Server.

This module provides centralized configuration management using pydantic-settings,
loading settings from environment variables and .env files.
"""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import (
    DEFAULT_GAS_ADJUSTMENT,
    DEFAULT_GAS_PRICES,
    DEFAULT_SPENDING_LIMIT,
    MAINNET_CHAIN_ID,
    MAINNET_URL,
    TESTNET_CHAIN_ID,
    TESTNET_URL,
)
from .types import NetworkType


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables with the same name
    (case-insensitive). Settings are loaded in this order:
    1. Default values
    2. .env file (if present)
    3. Environment variables
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Network configuration
    secret_network: NetworkType = Field(
        default=NetworkType.TESTNET,
        description="Network to connect to (testnet, mainnet, custom)",
    )

    secret_mainnet_url: str = Field(
        default=MAINNET_URL,
        description="Mainnet LCD endpoint URL",
    )

    secret_testnet_url: str = Field(
        default=TESTNET_URL,
        description="Testnet LCD endpoint URL",
    )

    secret_mainnet_chain_id: str = Field(
        default=MAINNET_CHAIN_ID,
        description="Mainnet chain identifier",
    )

    secret_testnet_chain_id: str = Field(
        default=TESTNET_CHAIN_ID,
        description="Testnet chain identifier",
    )

    secret_custom_url: Optional[str] = Field(
        default=None,
        description="Custom network LCD endpoint URL",
    )

    secret_custom_chain_id: Optional[str] = Field(
        default=None,
        description="Custom network chain identifier",
    )

    # Gas configuration
    default_gas_price: str = Field(
        default=DEFAULT_GAS_PRICES,
        description="Default gas price (e.g., '0.25uscrt')",
    )

    gas_adjustment: float = Field(
        default=DEFAULT_GAS_ADJUSTMENT,
        description="Gas adjustment multiplier for estimation",
    )

    # Cache configuration (TTL in seconds)
    cache_ttl_validators: int = Field(
        default=300,
        description="Validators cache TTL (seconds)",
    )

    cache_ttl_balances: int = Field(
        default=30,
        description="Balances cache TTL (seconds)",
    )

    cache_ttl_contracts: int = Field(
        default=600,
        description="Contracts cache TTL (seconds)",
    )

    cache_ttl_blocks: int = Field(
        default=10,
        description="Blocks cache TTL (seconds)",
    )

    cache_ttl_accounts: int = Field(
        default=60,
        description="Accounts cache TTL (seconds)",
    )

    # Security configuration
    spending_limit_uscrt: int = Field(
        default=DEFAULT_SPENDING_LIMIT,
        description="Maximum spending limit per transaction (uscrt)",
    )

    require_confirmation_above_uscrt: int = Field(
        default=1_000_000,
        description="Require user confirmation for amounts above this (uscrt)",
    )

    # Wallet persistence
    wallet_storage_enabled: bool = Field(
        default=True,
        description="Enable encrypted wallet persistence to disk",
    )

    wallet_storage_path: str = Field(
        default="~/.secret-mcp/wallets",
        description="Directory for encrypted wallet storage",
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    log_format: str = Field(
        default="json",
        description="Log output format (json or console)",
    )

    debug: bool = Field(
        default=False,
        description="Enable extra debug logging (requires LOG_LEVEL=DEBUG)",
    )

    # Connection pool configuration
    max_connections: int = Field(
        default=10,
        description="Maximum concurrent connections to blockchain",
    )

    idle_timeout: int = Field(
        default=300,
        description="Idle connection timeout (seconds)",
    )

    connection_keepalive: bool = Field(
        default=True,
        description="Enable HTTP keep-alive for connections",
    )

    # Retry configuration
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for failed requests",
    )

    retry_backoff_base: int = Field(
        default=2,
        description="Exponential backoff base multiplier (seconds)",
    )

    retry_backoff_max: int = Field(
        default=30,
        description="Maximum backoff time between retries (seconds)",
    )

    def get_network_url(self) -> str:
        """Get LCD endpoint URL for the configured network.

        Returns:
            LCD endpoint URL

        Raises:
            ValueError: If custom network is selected but URL is not configured
        """
        if self.secret_network == NetworkType.MAINNET:
            return self.secret_mainnet_url
        elif self.secret_network == NetworkType.TESTNET:
            return self.secret_testnet_url
        elif self.secret_network == NetworkType.CUSTOM:
            if not self.secret_custom_url:
                raise ValueError(
                    "Invalid network configuration: Custom network requires SECRET_CUSTOM_URL"
                )
            return self.secret_custom_url
        else:
            raise ValueError(f"Invalid network configuration: {self.secret_network}")

    def get_chain_id(self) -> str:
        """Get chain ID for the configured network.

        Returns:
            Chain identifier

        Raises:
            ValueError: If custom network is selected but chain ID is not configured
        """
        if self.secret_network == NetworkType.MAINNET:
            return self.secret_mainnet_chain_id
        elif self.secret_network == NetworkType.TESTNET:
            return self.secret_testnet_chain_id
        elif self.secret_network == NetworkType.CUSTOM:
            if not self.secret_custom_chain_id:
                raise ValueError(
                    "Invalid network configuration: Custom network requires SECRET_CUSTOM_CHAIN_ID"
                )
            return self.secret_custom_chain_id
        else:
            raise ValueError(f"Invalid network configuration: {self.secret_network}")


# Global settings instance (singleton pattern)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance.

    This function implements a singleton pattern for settings,
    ensuring the same instance is reused throughout the application.

    Returns:
        Global Settings instance
    """
    global _settings

    if _settings is None:
        # Load .env file if it exists
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)

        _settings = Settings()

    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment variables.

    This forces recreation of the global settings instance,
    picking up any changes to environment variables.

    Returns:
        New Settings instance with current environment values
    """
    global _settings

    # Clear the current instance
    _settings = None

    # Create and return new instance
    return get_settings()
