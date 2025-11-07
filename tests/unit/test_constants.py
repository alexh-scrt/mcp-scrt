"""Unit tests for constants."""

import re

import pytest

from mcp_scrt.constants import (
    ADDRESS_PATTERN,
    CACHE_TTL,
    CONFIRMATION_THRESHOLD,
    CONNECTION_KEEPALIVE,
    CONTRACT_PATTERN,
    DEFAULT_GAS_ADJUSTMENT,
    DEFAULT_GAS_PRICES,
    DEFAULT_SPENDING_LIMIT,
    GAS_LIMITS,
    IDLE_TIMEOUT,
    MAINNET_CHAIN_ID,
    MAINNET_URL,
    MAX_CONNECTIONS,
    MAX_RETRIES,
    NATIVE_DENOM,
    NATIVE_DENOM_DECIMALS,
    RETRY_BACKOFF_BASE,
    RETRY_BACKOFF_MAX,
    TESTNET_CHAIN_ID,
    TESTNET_URL,
    TOOL_CATEGORIES,
    VALIDATOR_PATTERN,
)


class TestNetworkConstants:
    """Test network-related constants."""

    def test_mainnet_url(self) -> None:
        """Test mainnet URL."""
        assert MAINNET_URL == "https://secret-4.api.trivium.network:1317"
        assert MAINNET_URL.startswith("https://")

    def test_testnet_url(self) -> None:
        """Test testnet URL."""
        assert TESTNET_URL == "https://pulsar.lcd.secretnodes.com"
        assert TESTNET_URL.startswith("http://")

    def test_mainnet_chain_id(self) -> None:
        """Test mainnet chain ID."""
        assert MAINNET_CHAIN_ID == "secret-4"

    def test_testnet_chain_id(self) -> None:
        """Test testnet chain ID."""
        assert TESTNET_CHAIN_ID == "pulsar-3"


class TestGasConstants:
    """Test gas-related constants."""

    def test_default_gas_prices(self) -> None:
        """Test default gas prices."""
        assert DEFAULT_GAS_PRICES == "0.25uscrt"

    def test_default_gas_adjustment(self) -> None:
        """Test default gas adjustment."""
        assert DEFAULT_GAS_ADJUSTMENT == 1.0
        assert isinstance(DEFAULT_GAS_ADJUSTMENT, float)

    def test_gas_limits(self) -> None:
        """Test gas limits configuration."""
        assert isinstance(GAS_LIMITS, dict)
        assert "upload" in GAS_LIMITS
        assert "init" in GAS_LIMITS
        assert "exec" in GAS_LIMITS
        assert "send" in GAS_LIMITS
        assert "default" in GAS_LIMITS

        # Verify reasonable values
        assert GAS_LIMITS["upload"] == 1_000_000
        assert GAS_LIMITS["init"] == 500_000
        assert GAS_LIMITS["exec"] == 200_000
        assert GAS_LIMITS["send"] == 80_000
        assert GAS_LIMITS["default"] == 200_000


class TestCacheConstants:
    """Test cache-related constants."""

    def test_cache_ttl_structure(self) -> None:
        """Test cache TTL structure."""
        assert isinstance(CACHE_TTL, dict)
        assert "validators" in CACHE_TTL
        assert "balances" in CACHE_TTL
        assert "contracts" in CACHE_TTL
        assert "blocks" in CACHE_TTL
        assert "accounts" in CACHE_TTL

    def test_cache_ttl_values(self) -> None:
        """Test cache TTL values are reasonable."""
        assert CACHE_TTL["validators"] == 300  # 5 minutes
        assert CACHE_TTL["balances"] == 30  # 30 seconds
        assert CACHE_TTL["contracts"] == 600  # 10 minutes
        assert CACHE_TTL["blocks"] == 10  # 10 seconds
        assert CACHE_TTL["accounts"] == 60  # 60 seconds

        # All values should be positive
        for ttl_value in CACHE_TTL.values():
            assert ttl_value > 0


class TestSecurityConstants:
    """Test security-related constants."""

    def test_default_spending_limit(self) -> None:
        """Test default spending limit."""
        assert DEFAULT_SPENDING_LIMIT == 10_000_000  # 10 SCRT
        assert isinstance(DEFAULT_SPENDING_LIMIT, int)

    def test_confirmation_threshold(self) -> None:
        """Test confirmation threshold."""
        assert CONFIRMATION_THRESHOLD == 1_000_000  # 1 SCRT
        assert isinstance(CONFIRMATION_THRESHOLD, int)
        assert CONFIRMATION_THRESHOLD < DEFAULT_SPENDING_LIMIT


class TestRetryConstants:
    """Test retry-related constants."""

    def test_max_retries(self) -> None:
        """Test max retries."""
        assert MAX_RETRIES == 3
        assert isinstance(MAX_RETRIES, int)
        assert MAX_RETRIES > 0

    def test_retry_backoff_base(self) -> None:
        """Test retry backoff base."""
        assert RETRY_BACKOFF_BASE == 2
        assert isinstance(RETRY_BACKOFF_BASE, int)

    def test_retry_backoff_max(self) -> None:
        """Test retry backoff max."""
        assert RETRY_BACKOFF_MAX == 30
        assert isinstance(RETRY_BACKOFF_MAX, int)
        assert RETRY_BACKOFF_MAX > RETRY_BACKOFF_BASE


class TestConnectionConstants:
    """Test connection pool constants."""

    def test_max_connections(self) -> None:
        """Test max connections."""
        assert MAX_CONNECTIONS == 10
        assert isinstance(MAX_CONNECTIONS, int)
        assert MAX_CONNECTIONS > 0

    def test_idle_timeout(self) -> None:
        """Test idle timeout."""
        assert IDLE_TIMEOUT == 300  # 5 minutes
        assert isinstance(IDLE_TIMEOUT, int)
        assert IDLE_TIMEOUT > 0

    def test_connection_keepalive(self) -> None:
        """Test connection keepalive."""
        assert CONNECTION_KEEPALIVE is True
        assert isinstance(CONNECTION_KEEPALIVE, bool)


class TestValidationPatterns:
    """Test validation pattern constants."""

    def test_address_pattern(self) -> None:
        """Test address pattern."""
        assert ADDRESS_PATTERN == r"^secret1[a-z0-9]{38,45}$"

        # Test pattern matches valid addresses
        valid_address = "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"
        assert re.match(ADDRESS_PATTERN, valid_address)

        # Test pattern rejects invalid addresses
        assert not re.match(ADDRESS_PATTERN, "cosmos1abc")
        assert not re.match(ADDRESS_PATTERN, "secret1")
        assert not re.match(ADDRESS_PATTERN, "SECRET1abc")  # uppercase

    def test_validator_pattern(self) -> None:
        """Test validator pattern."""
        assert VALIDATOR_PATTERN == r"^secretvaloper1[a-z0-9]{38,45}$"

        # Test pattern matches valid validator addresses
        valid_validator = "secretvaloper1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"
        assert re.match(VALIDATOR_PATTERN, valid_validator)

        # Test pattern rejects invalid validator addresses
        assert not re.match(VALIDATOR_PATTERN, "secret1abc")
        assert not re.match(VALIDATOR_PATTERN, "secretvaloper1")

    def test_contract_pattern(self) -> None:
        """Test contract pattern."""
        assert CONTRACT_PATTERN == r"^secret1[a-z0-9]{38,45}$"

        # Contract pattern should be same as address pattern
        assert CONTRACT_PATTERN == ADDRESS_PATTERN


class TestDenominationConstants:
    """Test denomination constants."""

    def test_native_denom(self) -> None:
        """Test native denomination."""
        assert NATIVE_DENOM == "uscrt"

    def test_native_denom_decimals(self) -> None:
        """Test native denomination decimals."""
        assert NATIVE_DENOM_DECIMALS == 6
        assert isinstance(NATIVE_DENOM_DECIMALS, int)

    def test_denom_conversion(self) -> None:
        """Test denomination conversion factor."""
        # 1 SCRT = 10^6 uscrt
        scrt_to_uscrt = 10 ** NATIVE_DENOM_DECIMALS
        assert scrt_to_uscrt == 1_000_000


class TestToolCategories:
    """Test tool categories constants."""

    def test_tool_categories_list(self) -> None:
        """Test tool categories list."""
        assert isinstance(TOOL_CATEGORIES, list)
        assert len(TOOL_CATEGORIES) == 11

    def test_tool_categories_content(self) -> None:
        """Test tool categories contain expected values."""
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
        assert TOOL_CATEGORIES == expected

    def test_tool_categories_unique(self) -> None:
        """Test tool categories are unique."""
        assert len(TOOL_CATEGORIES) == len(set(TOOL_CATEGORIES))

    def test_tool_categories_lowercase(self) -> None:
        """Test all tool categories are lowercase."""
        for category in TOOL_CATEGORIES:
            assert category.islower()
            assert category.isalpha()
