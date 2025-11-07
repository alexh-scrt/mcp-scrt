"""Type definitions for Secret MCP Server."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class NetworkType(str, Enum):
    """Supported network types."""

    MAINNET = "mainnet"
    TESTNET = "testnet"
    CUSTOM = "custom"


class ToolCategory(str, Enum):
    """Tool categories for organizing MCP tools."""

    NETWORK = "network"
    WALLET = "wallet"
    BANK = "bank"
    STAKING = "staking"
    REWARDS = "rewards"
    GOVERNANCE = "governance"
    CONTRACTS = "contracts"
    IBC = "ibc"
    TRANSACTIONS = "transactions"
    BLOCKCHAIN = "blockchain"
    ACCOUNTS = "accounts"


@dataclass
class NetworkConfig:
    """Network configuration for Secret Network connection."""

    network_type: NetworkType
    lcd_url: str  # LCD REST endpoint
    chain_id: str
    bech32_prefix: str = "secret"
    coin_type: int = 529  # SLIP-0044 coin type for Secret Network
    denom: str = "uscrt"
    decimals: int = 6
    gas_prices: str = "0.25uscrt"
    gas_adjustment: float = 1.0

    @property
    def url(self) -> str:
        """Alias for lcd_url for backward compatibility."""
        return self.lcd_url


@dataclass
class WalletInfo:
    """Wallet information including address and derivation path."""

    wallet_id: str
    address: str
    account: int = 0
    index: int = 0
    hd_wallet: Optional[Any] = None  # HDWallet instance for signing (stored in-memory only)


class ToolRequest(BaseModel):
    """Tool request model for MCP tool invocations."""

    tool_name: str
    parameters: Dict[str, Any]
    request_id: Optional[str] = None

    @field_validator("tool_name")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """Validate tool name is not empty."""
        if not v or not v.strip():
            raise ValueError("Tool name cannot be empty")
        return v


class ToolResponse(BaseModel):
    """Tool response model for MCP tool results."""

    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response model with detailed error information."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    suggestions: List[str] = Field(default_factory=list)


class CacheEntry(BaseModel):
    """Cache entry model for storing cached data with TTL."""

    key: str
    value: Any
    timestamp: float
    ttl: int  # seconds

    @field_validator("ttl")
    @classmethod
    def validate_ttl(cls, v: int) -> int:
        """Validate TTL is positive."""
        if v < 0:
            raise ValueError("TTL must be non-negative")
        return v


@dataclass
class TransactionResult:
    """Transaction result information."""

    txhash: str
    success: bool
    height: Optional[int] = None
    gas_used: Optional[int] = None
    gas_wanted: Optional[int] = None
    raw_log: Optional[str] = None
    events: Optional[List[Dict[str, Any]]] = field(default_factory=lambda: None)
