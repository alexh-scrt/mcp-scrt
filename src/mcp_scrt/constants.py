"""Constants for Secret MCP Server.

This module contains all constant values used throughout the application,
including network endpoints, gas configuration, cache TTLs, security limits,
and validation patterns.
"""

from typing import Dict, List

from mcp_scrt.types import NetworkType, NetworkConfig

# Network endpoints
MAINNET_URL = "https://secret-4.api.trivium.network:1317"
TESTNET_URL = "https://pulsar.lcd.secretnodes.com"
MAINNET_CHAIN_ID = "secret-4"
TESTNET_CHAIN_ID = "pulsar-3"

# Gas configuration
DEFAULT_GAS_PRICES = "0.25uscrt"
DEFAULT_GAS_ADJUSTMENT = 1.0

# Gas prices by tier (in uscrt per gas unit)
GAS_PRICES: Dict[str, str] = {
    "DEFAULT": "0.25uscrt",
    "LOW": "0.1uscrt",
    "AVERAGE": "0.25uscrt",
    "HIGH": "0.5uscrt",
}

# Gas limits by operation type
GAS_LIMITS: Dict[str, int] = {
    "upload": 1_000_000,  # Contract upload
    "init": 500_000,  # Contract instantiation
    "exec": 200_000,  # Contract execution
    "send": 80_000,  # Token transfer
    "default": 200_000,  # Default operation
}

# Cache TTL (time-to-live) in seconds
CACHE_TTL: Dict[str, int] = {
    "validators": 300,  # 5 minutes - validators change rarely
    "balances": 30,  # 30 seconds - balances change frequently
    "contracts": 600,  # 10 minutes - contract info rarely changes
    "blocks": 10,  # 10 seconds - new blocks every ~6 seconds
    "accounts": 60,  # 60 seconds - account info changes moderately
    "tx_results": 3600,  # 1 hour - transaction results are immutable
}

# Security limits
DEFAULT_SPENDING_LIMIT = 10_000_000  # 10 SCRT in uscrt
CONFIRMATION_THRESHOLD = 1_000_000  # 1 SCRT in uscrt - require confirmation above this

# Retry configuration for network requests
MAX_RETRIES = 3  # Maximum number of retry attempts
RETRY_BACKOFF_BASE = 2  # Exponential backoff base (seconds)
RETRY_BACKOFF_MAX = 30  # Maximum backoff time (seconds)

# Connection pool configuration
MAX_CONNECTIONS = 10  # Maximum concurrent connections
IDLE_TIMEOUT = 300  # Idle connection timeout in seconds (5 minutes)
CONNECTION_KEEPALIVE = True  # Enable HTTP keep-alive

# Validation patterns (regex)
ADDRESS_PATTERN = r"^secret1[a-z0-9]{38,45}$"  # Secret Network account address (38-45 chars)
VALIDATOR_PATTERN = r"^secretvaloper1[a-z0-9]{38,45}$"  # Validator operator address
CONTRACT_PATTERN = r"^secret1[a-z0-9]{38,45}$"  # Smart contract address (same as account)

# Validation patterns dictionary for easy access
VALIDATION_PATTERNS: Dict[str, str] = {
    "address": ADDRESS_PATTERN,
    "validator": VALIDATOR_PATTERN,
    "contract": CONTRACT_PATTERN,
}

# Native denomination
NATIVE_DENOM = "uscrt"  # Micro SCRT
NATIVE_DENOM_DECIMALS = 6  # 1 SCRT = 10^6 uscrt

# Tool categories for organizing MCP tools
TOOL_CATEGORIES: List[str] = [
    "network",  # Network configuration and info
    "wallet",  # Wallet management
    "bank",  # Token operations
    "staking",  # Validator staking
    "rewards",  # Staking rewards
    "governance",  # On-chain governance
    "contracts",  # Smart contracts
    "ibc",  # Inter-blockchain communication
    "transactions",  # Transaction queries
    "blockchain",  # Blockchain queries
    "accounts",  # Account queries
]

# Network configurations
NETWORK_CONFIGS: Dict[NetworkType, NetworkConfig] = {
    NetworkType.MAINNET: NetworkConfig(
        network_type=NetworkType.MAINNET,
        lcd_url=MAINNET_URL,
        chain_id=MAINNET_CHAIN_ID,
        bech32_prefix="secret",
        coin_type=529,
        denom="uscrt",
        decimals=6,
        gas_prices="0.25uscrt",
        gas_adjustment=1.0,
    ),
    NetworkType.TESTNET: NetworkConfig(
        network_type=NetworkType.TESTNET,
        lcd_url=TESTNET_URL,
        chain_id=TESTNET_CHAIN_ID,
        bech32_prefix="secret",
        coin_type=529,
        denom="uscrt",
        decimals=6,
        gas_prices="0.25uscrt",
        gas_adjustment=1.0,
    ),
}
