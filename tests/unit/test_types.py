"""Unit tests for type definitions."""

import pytest
from pydantic import ValidationError

from mcp_scrt.types import (
    NetworkType,
    ToolCategory,
    NetworkConfig,
    WalletInfo,
    ToolRequest,
    ToolResponse,
    ErrorResponse,
    CacheEntry,
    TransactionResult,
)


class TestNetworkType:
    """Test NetworkType enum."""

    def test_network_types(self) -> None:
        """Test network type values."""
        assert NetworkType.MAINNET == "mainnet"
        assert NetworkType.TESTNET == "testnet"
        assert NetworkType.CUSTOM == "custom"

    def test_network_type_from_string(self) -> None:
        """Test creating network type from string."""
        assert NetworkType("mainnet") == NetworkType.MAINNET
        assert NetworkType("testnet") == NetworkType.TESTNET


class TestToolCategory:
    """Test ToolCategory enum."""

    def test_tool_categories(self) -> None:
        """Test tool category values."""
        assert ToolCategory.NETWORK == "network"
        assert ToolCategory.WALLET == "wallet"
        assert ToolCategory.BANK == "bank"
        assert ToolCategory.TRANSACTIONS == "transactions"

    def test_all_categories_exist(self) -> None:
        """Test all expected categories exist."""
        expected = [
            "network",
            "wallet",
            "bank",
            "staking",
            "rewards",
            "governance",
            "contracts",
            "ibc",
            "transactions",
            "blockchain",
            "accounts",
        ]
        actual = [cat.value for cat in ToolCategory]
        for exp in expected:
            assert exp in actual


class TestNetworkConfig:
    """Test NetworkConfig dataclass."""

    def test_create_network_config(self) -> None:
        """Test creating network configuration."""
        config = NetworkConfig(
            network_type=NetworkType.TESTNET,
            lcd_url="http://testnet.example.com:1317",
            chain_id="pulsar-2",
        )
        assert config.network_type == NetworkType.TESTNET
        assert config.lcd_url == "http://testnet.example.com:1317"
        assert config.url == "http://testnet.example.com:1317"  # Test property alias
        assert config.chain_id == "pulsar-2"
        assert config.gas_prices == "0.25uscrt"  # Default
        assert config.gas_adjustment == 1.0  # Default

    def test_network_config_with_custom_gas(self) -> None:
        """Test network config with custom gas settings."""
        config = NetworkConfig(
            network_type=NetworkType.MAINNET,
            lcd_url="https://mainnet.example.com:1317",
            chain_id="secret-4",
            gas_prices="0.5uscrt",
            gas_adjustment=1.5,
        )
        assert config.gas_prices == "0.5uscrt"
        assert config.gas_adjustment == 1.5


class TestWalletInfo:
    """Test WalletInfo dataclass."""

    def test_create_wallet_info(self) -> None:
        """Test creating wallet information."""
        wallet = WalletInfo(
            wallet_id="test-wallet-1",
            address="secret1abcdef1234567890",
        )
        assert wallet.wallet_id == "test-wallet-1"
        assert wallet.address == "secret1abcdef1234567890"
        assert wallet.account == 0  # Default
        assert wallet.index == 0  # Default

    def test_wallet_info_with_hd_path(self) -> None:
        """Test wallet info with HD derivation path."""
        wallet = WalletInfo(
            wallet_id="test-wallet-2",
            address="secret1xyz",
            account=1,
            index=5,
        )
        assert wallet.account == 1
        assert wallet.index == 5


class TestToolRequest:
    """Test ToolRequest model."""

    def test_create_tool_request(self) -> None:
        """Test creating tool request."""
        request = ToolRequest(
            tool_name="secret_get_balance",
            parameters={"address": "secret1abc"},
        )
        assert request.tool_name == "secret_get_balance"
        assert request.parameters == {"address": "secret1abc"}
        assert request.request_id is None

    def test_tool_request_with_id(self) -> None:
        """Test tool request with request ID."""
        request = ToolRequest(
            tool_name="secret_send_tokens",
            parameters={"to": "secret1xyz", "amount": "1000000"},
            request_id="req-123",
        )
        assert request.request_id == "req-123"

    def test_tool_request_validation(self) -> None:
        """Test tool request validation."""
        with pytest.raises(ValidationError):
            ToolRequest(tool_name="", parameters={})  # Empty tool name


class TestToolResponse:
    """Test ToolResponse model."""

    def test_successful_response(self) -> None:
        """Test creating successful response."""
        response = ToolResponse(
            success=True,
            data={"balance": "1000000uscrt"},
            metadata={"cached": False},
        )
        assert response.success is True
        assert response.data == {"balance": "1000000uscrt"}
        assert response.error is None
        assert response.metadata == {"cached": False}

    def test_error_response(self) -> None:
        """Test creating error response."""
        response = ToolResponse(
            success=False,
            error={"code": "NETWORK_ERROR", "message": "Connection failed"},
        )
        assert response.success is False
        assert response.data is None
        assert response.error == {"code": "NETWORK_ERROR", "message": "Connection failed"}

    def test_response_defaults(self) -> None:
        """Test response default values."""
        response = ToolResponse(success=True)
        assert response.data is None
        assert response.error is None
        assert response.metadata == {}


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_create_error_response(self) -> None:
        """Test creating error response."""
        error = ErrorResponse(
            code="VALIDATION_ERROR",
            message="Invalid address format",
        )
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Invalid address format"
        assert error.details is None
        assert error.suggestions == []

    def test_error_with_details_and_suggestions(self) -> None:
        """Test error with details and suggestions."""
        error = ErrorResponse(
            code="INSUFFICIENT_FUNDS",
            message="Not enough balance",
            details={"required": 1000000, "available": 500000},
            suggestions=[
                "Check your account balance",
                "Reduce the transfer amount",
            ],
        )
        assert error.details == {"required": 1000000, "available": 500000}
        assert len(error.suggestions) == 2


class TestCacheEntry:
    """Test CacheEntry model."""

    def test_create_cache_entry(self) -> None:
        """Test creating cache entry."""
        entry = CacheEntry(
            key="balance:secret1abc",
            value={"amount": "1000000uscrt"},
            timestamp=1234567890.0,
            ttl=30,
        )
        assert entry.key == "balance:secret1abc"
        assert entry.value == {"amount": "1000000uscrt"}
        assert entry.timestamp == 1234567890.0
        assert entry.ttl == 30

    def test_cache_entry_validation(self) -> None:
        """Test cache entry validation."""
        with pytest.raises(ValidationError):
            CacheEntry(key="", value={}, timestamp=0.0, ttl=-1)  # Invalid TTL


class TestTransactionResult:
    """Test TransactionResult dataclass."""

    def test_create_transaction_result(self) -> None:
        """Test creating transaction result."""
        result = TransactionResult(
            txhash="ABCD1234567890",
            success=True,
        )
        assert result.txhash == "ABCD1234567890"
        assert result.success is True
        assert result.height is None
        assert result.gas_used is None

    def test_complete_transaction_result(self) -> None:
        """Test complete transaction result."""
        result = TransactionResult(
            txhash="XYZ123",
            success=True,
            height=12345,
            gas_used=100000,
            gas_wanted=150000,
            raw_log="success",
            events=[{"type": "transfer", "attributes": []}],
        )
        assert result.height == 12345
        assert result.gas_used == 100000
        assert result.gas_wanted == 150000
        assert result.raw_log == "success"
        assert len(result.events) == 1

    def test_failed_transaction_result(self) -> None:
        """Test failed transaction result."""
        result = TransactionResult(
            txhash="FAIL123",
            success=False,
            raw_log="insufficient funds",
        )
        assert result.success is False
        assert result.raw_log == "insufficient funds"
