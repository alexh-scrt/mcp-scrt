"""Unit tests for custom exceptions."""

import pytest

from mcp_scrt.utils.errors import (
    AuthenticationError,
    CacheError,
    ConfigurationError,
    ContractError,
    InsufficientFundsError,
    NetworkError,
    SecretMCPError,
    TransactionError,
    ValidationError,
    WalletError,
)


class TestSecretMCPError:
    """Test base SecretMCPError exception."""

    def test_create_basic_error(self) -> None:
        """Test creating basic error."""
        error = SecretMCPError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.code == "UNKNOWN_ERROR"
        assert error.details == {}
        assert error.suggestions == []

    def test_create_error_with_code(self) -> None:
        """Test creating error with custom code."""
        error = SecretMCPError("Error occurred", code="CUSTOM_ERROR")
        assert error.code == "CUSTOM_ERROR"
        assert error.message == "Error occurred"

    def test_create_error_with_details(self) -> None:
        """Test creating error with details."""
        details = {"key": "value", "count": 42}
        error = SecretMCPError("Error", details=details)
        assert error.details == details

    def test_create_error_with_suggestions(self) -> None:
        """Test creating error with suggestions."""
        suggestions = ["Try this", "Or try that"]
        error = SecretMCPError("Error", suggestions=suggestions)
        assert error.suggestions == suggestions
        assert len(error.suggestions) == 2

    def test_error_to_dict(self) -> None:
        """Test converting error to dictionary."""
        error = SecretMCPError(
            message="Test error",
            code="TEST_ERROR",
            details={"field": "value"},
            suggestions=["Suggestion 1", "Suggestion 2"],
        )
        error_dict = error.to_dict()

        assert error_dict["code"] == "TEST_ERROR"
        assert error_dict["message"] == "Test error"
        assert error_dict["details"] == {"field": "value"}
        assert error_dict["suggestions"] == ["Suggestion 1", "Suggestion 2"]


class TestNetworkError:
    """Test NetworkError exception."""

    def test_network_error_code(self) -> None:
        """Test network error has correct code."""
        error = NetworkError("Connection failed")
        assert error.code == "NETWORK_ERROR"
        assert error.message == "Connection failed"

    def test_network_error_inheritance(self) -> None:
        """Test network error inherits from base error."""
        error = NetworkError("Test")
        assert isinstance(error, SecretMCPError)
        assert isinstance(error, Exception)


class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_code(self) -> None:
        """Test validation error has correct code."""
        error = ValidationError("Invalid input")
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Invalid input"

    def test_validation_error_with_details(self) -> None:
        """Test validation error with field details."""
        error = ValidationError(
            "Invalid address",
            details={"field": "address", "value": "invalid"},
        )
        assert error.details["field"] == "address"


class TestAuthenticationError:
    """Test AuthenticationError exception."""

    def test_authentication_error_code(self) -> None:
        """Test authentication error has correct code."""
        error = AuthenticationError("No wallet configured")
        assert error.code == "AUTHENTICATION_ERROR"


class TestWalletError:
    """Test WalletError exception."""

    def test_wallet_error_code(self) -> None:
        """Test wallet error has correct code."""
        error = WalletError("Wallet not found")
        assert error.code == "WALLET_ERROR"
        assert error.message == "Wallet not found"

    def test_wallet_error_with_suggestions(self) -> None:
        """Test wallet error with suggestions."""
        error = WalletError(
            "No active wallet",
            suggestions=["Import a wallet", "Create a new wallet"],
        )
        assert len(error.suggestions) == 2


class TestTransactionError:
    """Test TransactionError exception."""

    def test_transaction_error_code(self) -> None:
        """Test transaction error has correct code."""
        error = TransactionError("Transaction failed")
        assert error.code == "TRANSACTION_ERROR"


class TestInsufficientFundsError:
    """Test InsufficientFundsError exception."""

    def test_insufficient_funds_error(self) -> None:
        """Test insufficient funds error."""
        error = InsufficientFundsError(required=1000000, available=500000)
        assert error.code == "TRANSACTION_ERROR"
        assert "required 1000000 uscrt" in error.message
        assert "available 500000 uscrt" in error.message

    def test_insufficient_funds_error_details(self) -> None:
        """Test insufficient funds error has details."""
        error = InsufficientFundsError(required=2000000, available=1000000)
        assert error.details["required"] == 2000000
        assert error.details["available"] == 1000000

    def test_insufficient_funds_error_suggestions(self) -> None:
        """Test insufficient funds error has suggestions."""
        error = InsufficientFundsError(required=1000000, available=500000)
        assert len(error.suggestions) > 0
        assert any("balance" in s.lower() for s in error.suggestions)

    def test_insufficient_funds_error_inheritance(self) -> None:
        """Test insufficient funds error inherits from transaction error."""
        error = InsufficientFundsError(required=1000000, available=500000)
        assert isinstance(error, TransactionError)
        assert isinstance(error, SecretMCPError)


class TestContractError:
    """Test ContractError exception."""

    def test_contract_error_code(self) -> None:
        """Test contract error has correct code."""
        error = ContractError("Contract execution failed")
        assert error.code == "CONTRACT_ERROR"
        assert error.message == "Contract execution failed"


class TestCacheError:
    """Test CacheError exception."""

    def test_cache_error_code(self) -> None:
        """Test cache error has correct code."""
        error = CacheError("Cache miss")
        assert error.code == "CACHE_ERROR"


class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_configuration_error_code(self) -> None:
        """Test configuration error has correct code."""
        error = ConfigurationError("Invalid configuration")
        assert error.code == "CONFIGURATION_ERROR"

    def test_configuration_error_with_details(self) -> None:
        """Test configuration error with details."""
        error = ConfigurationError(
            "Missing required field",
            details={"field": "api_key", "location": ".env"},
        )
        assert error.details["field"] == "api_key"
        assert error.details["location"] == ".env"


class TestErrorHierarchy:
    """Test error class hierarchy and relationships."""

    def test_all_errors_inherit_from_base(self) -> None:
        """Test all custom errors inherit from SecretMCPError."""
        errors = [
            NetworkError("test"),
            ValidationError("test"),
            AuthenticationError("test"),
            WalletError("test"),
            TransactionError("test"),
            ContractError("test"),
            CacheError("test"),
            ConfigurationError("test"),
        ]

        for error in errors:
            assert isinstance(error, SecretMCPError)
            assert isinstance(error, Exception)

    def test_all_errors_have_unique_codes(self) -> None:
        """Test all error types have unique error codes."""
        errors = [
            NetworkError("test"),
            ValidationError("test"),
            AuthenticationError("test"),
            WalletError("test"),
            TransactionError("test"),
            ContractError("test"),
            CacheError("test"),
            ConfigurationError("test"),
        ]

        codes = [error.code for error in errors]
        assert len(codes) == len(set(codes))  # All codes are unique


class TestErrorRaising:
    """Test error raising and catching."""

    def test_raise_and_catch_secret_mcp_error(self) -> None:
        """Test raising and catching SecretMCPError."""
        with pytest.raises(SecretMCPError) as exc_info:
            raise SecretMCPError("Test error")

        assert str(exc_info.value) == "Test error"

    def test_raise_and_catch_network_error(self) -> None:
        """Test raising and catching NetworkError."""
        with pytest.raises(NetworkError) as exc_info:
            raise NetworkError("Connection timeout")

        assert exc_info.value.code == "NETWORK_ERROR"

    def test_catch_specific_error_as_base_class(self) -> None:
        """Test catching specific error as base class."""
        with pytest.raises(SecretMCPError):
            raise WalletError("Wallet error")

    def test_error_message_in_traceback(self) -> None:
        """Test error message appears in traceback."""
        try:
            raise ValidationError("Invalid format")
        except ValidationError as e:
            assert "Invalid format" in str(e)
            assert e.code == "VALIDATION_ERROR"
