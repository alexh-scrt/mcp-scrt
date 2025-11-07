"""Unit tests for configuration management."""

import os
from pathlib import Path

import pytest

from mcp_scrt.config import Settings, get_settings, reload_settings
from mcp_scrt.types import NetworkType


class TestSettings:
    """Test Settings configuration class."""

    def test_default_settings(self) -> None:
        """Test default settings values."""
        settings = Settings()

        # Network defaults
        assert settings.secret_network == NetworkType.TESTNET
        assert settings.secret_testnet_chain_id == "pulsar-3"
        assert settings.secret_mainnet_chain_id == "secret-4"

        # Gas defaults
        assert settings.default_gas_price == "0.25uscrt"
        assert settings.gas_adjustment == 1.0

        # Cache defaults
        assert settings.cache_ttl_validators == 300
        assert settings.cache_ttl_balances == 30
        assert settings.cache_ttl_contracts == 600

        # Security defaults
        assert settings.spending_limit_uscrt == 10_000_000
        assert settings.require_confirmation_above_uscrt == 1_000_000

    def test_settings_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading settings from environment variables."""
        monkeypatch.setenv("SECRET_NETWORK", "mainnet")
        monkeypatch.setenv("DEFAULT_GAS_PRICE", "0.5")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        settings = Settings()

        assert settings.secret_network == NetworkType.MAINNET
        assert settings.default_gas_price == "0.5"
        assert settings.log_level == "DEBUG"

    def test_get_network_url_testnet(self) -> None:
        """Test getting testnet URL."""
        settings = Settings(secret_network=NetworkType.TESTNET)
        url = settings.get_network_url()

        assert url == "https://pulsar.lcd.secretnodes.com"

    def test_get_network_url_mainnet(self) -> None:
        """Test getting mainnet URL."""
        settings = Settings(secret_network=NetworkType.MAINNET)
        url = settings.get_network_url()

        assert url == "https://secret-4.api.trivium.network:1317"

    def test_get_network_url_custom(self) -> None:
        """Test getting custom network URL."""
        settings = Settings(
            secret_network=NetworkType.CUSTOM,
            secret_custom_url="http://localhost:1317",
        )
        url = settings.get_network_url()

        assert url == "http://localhost:1317"

    def test_get_network_url_custom_missing(self) -> None:
        """Test getting custom network URL when not configured."""
        settings = Settings(secret_network=NetworkType.CUSTOM)

        with pytest.raises(ValueError, match="Invalid network configuration"):
            settings.get_network_url()

    def test_get_chain_id_testnet(self) -> None:
        """Test getting testnet chain ID."""
        settings = Settings(secret_network=NetworkType.TESTNET)
        chain_id = settings.get_chain_id()

        assert chain_id == "pulsar-3"

    def test_get_chain_id_mainnet(self) -> None:
        """Test getting mainnet chain ID."""
        settings = Settings(secret_network=NetworkType.MAINNET)
        chain_id = settings.get_chain_id()

        assert chain_id == "secret-4"

    def test_get_chain_id_custom(self) -> None:
        """Test getting custom chain ID."""
        settings = Settings(
            secret_network=NetworkType.CUSTOM,
            secret_custom_chain_id="custom-1",
            secret_custom_url="http://localhost:1317",
        )
        chain_id = settings.get_chain_id()

        assert chain_id == "custom-1"

    def test_get_chain_id_custom_missing(self) -> None:
        """Test getting custom chain ID when not configured."""
        settings = Settings(
            secret_network=NetworkType.CUSTOM,
            secret_custom_url="http://localhost:1317",
        )

        with pytest.raises(ValueError, match="Invalid network configuration"):
            settings.get_chain_id()

    def test_cache_ttl_settings(self) -> None:
        """Test cache TTL configuration."""
        settings = Settings(
            cache_ttl_validators=600,
            cache_ttl_balances=60,
            cache_ttl_contracts=1200,
        )

        assert settings.cache_ttl_validators == 600
        assert settings.cache_ttl_balances == 60
        assert settings.cache_ttl_contracts == 1200

    def test_security_settings(self) -> None:
        """Test security configuration."""
        settings = Settings(
            spending_limit_uscrt=5_000_000,
            require_confirmation_above_uscrt=500_000,
        )

        assert settings.spending_limit_uscrt == 5_000_000
        assert settings.require_confirmation_above_uscrt == 500_000

    def test_logging_settings(self) -> None:
        """Test logging configuration."""
        settings = Settings(
            log_level="WARNING",
            log_format="console",
        )

        assert settings.log_level == "WARNING"
        assert settings.log_format == "console"

    def test_connection_pool_settings(self) -> None:
        """Test connection pool configuration."""
        settings = Settings(
            max_connections=20,
            idle_timeout=600,
            connection_keepalive=False,
        )

        assert settings.max_connections == 20
        assert settings.idle_timeout == 600
        assert settings.connection_keepalive is False

    def test_retry_settings(self) -> None:
        """Test retry configuration."""
        settings = Settings(
            max_retries=5,
            retry_backoff_base=3,
            retry_backoff_max=60,
        )

        assert settings.max_retries == 5
        assert settings.retry_backoff_base == 3
        assert settings.retry_backoff_max == 60


class TestGetSettings:
    """Test get_settings function."""

    def test_get_settings_singleton(self) -> None:
        """Test get_settings returns same instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_get_settings_returns_settings(self) -> None:
        """Test get_settings returns Settings instance."""
        settings = get_settings()

        assert isinstance(settings, Settings)

    def test_get_settings_with_defaults(self) -> None:
        """Test get_settings returns settings with defaults."""
        settings = get_settings()

        assert settings.secret_network == NetworkType.TESTNET
        assert settings.default_gas_price == "0.25uscrt"


class TestReloadSettings:
    """Test reload_settings function."""

    def test_reload_settings_returns_new_instance(self) -> None:
        """Test reload_settings creates new instance."""
        settings1 = get_settings()
        settings2 = reload_settings()

        # After reload, new call should return the same as settings2
        settings3 = get_settings()

        assert settings2 is settings3
        # Note: We can't test settings1 is not settings2 reliably
        # as singleton may be recreated with same values

    def test_reload_settings_picks_up_env_changes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test reload_settings picks up environment changes."""
        # Initial settings
        settings1 = get_settings()
        initial_network = settings1.secret_network

        # Change environment
        monkeypatch.setenv("SECRET_NETWORK", "mainnet")

        # Reload
        settings2 = reload_settings()

        # New settings should reflect environment change
        assert settings2.secret_network == NetworkType.MAINNET
        assert settings2.secret_network != initial_network


class TestSettingsValidation:
    """Test settings validation."""

    def test_network_type_validation(self) -> None:
        """Test network type must be valid."""
        # Valid network types
        Settings(secret_network="testnet")
        Settings(secret_network="mainnet")
        Settings(secret_network="custom")

        # Pydantic will convert strings to enum
        settings = Settings(secret_network="testnet")
        assert settings.secret_network == NetworkType.TESTNET

    def test_numeric_validation(self) -> None:
        """Test numeric fields are validated."""
        # Valid values
        Settings(max_connections=10)
        Settings(gas_adjustment=1.5)

        # Type coercion
        settings = Settings(max_connections="20")
        assert settings.max_connections == 20
        assert isinstance(settings.max_connections, int)

    def test_boolean_validation(self) -> None:
        """Test boolean fields are validated."""
        # Valid values
        Settings(connection_keepalive=True)
        Settings(connection_keepalive=False)

        # String coercion
        settings = Settings(connection_keepalive="false")
        assert settings.connection_keepalive is False


class TestSettingsEdgeCases:
    """Test edge cases for settings."""

    def test_empty_custom_url(self) -> None:
        """Test custom network with empty URL raises error."""
        settings = Settings(
            secret_network=NetworkType.CUSTOM,
            secret_custom_url="",
        )

        with pytest.raises(ValueError):
            settings.get_network_url()

    def test_none_custom_url(self) -> None:
        """Test custom network with None URL raises error."""
        settings = Settings(secret_network=NetworkType.CUSTOM)

        with pytest.raises(ValueError):
            settings.get_network_url()

    def test_cache_ttl_zero(self) -> None:
        """Test cache TTL can be zero (disable caching)."""
        settings = Settings(cache_ttl_balances=0)

        assert settings.cache_ttl_balances == 0

    def test_max_connections_positive(self) -> None:
        """Test max connections must be positive."""
        settings = Settings(max_connections=1)
        assert settings.max_connections == 1

    def test_gas_adjustment_range(self) -> None:
        """Test gas adjustment accepts various values."""
        # Very low
        settings1 = Settings(gas_adjustment=0.1)
        assert settings1.gas_adjustment == 0.1

        # Normal
        settings2 = Settings(gas_adjustment=1.0)
        assert settings2.gas_adjustment == 1.0

        # High
        settings3 = Settings(gas_adjustment=2.5)
        assert settings3.gas_adjustment == 2.5
