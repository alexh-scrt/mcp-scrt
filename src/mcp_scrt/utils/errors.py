"""Custom exceptions for Secret MCP Server.

This module defines a hierarchy of custom exceptions used throughout the application.
All exceptions inherit from SecretMCPError and provide structured error information
including error codes, messages, details, and suggestions for resolution.
"""

from typing import Any, Dict, List, Optional


class SecretMCPError(Exception):
    """Base exception for all Secret MCP Server errors.

    This is the base class for all custom exceptions in the application.
    It provides a structured way to represent errors with codes, messages,
    details, and suggestions.

    Attributes:
        message: Human-readable error message
        code: Machine-readable error code
        details: Additional error context as a dictionary
        suggestions: List of suggested actions to resolve the error
    """

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
    ) -> None:
        """Initialize SecretMCPError.

        Args:
            message: Human-readable error message
            code: Machine-readable error code (default: "UNKNOWN_ERROR")
            details: Additional error context (default: empty dict)
            suggestions: List of suggested actions (default: empty list)
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.suggestions = suggestions or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation.

        Returns:
            Dictionary containing error code, message, details, and suggestions
        """
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "suggestions": self.suggestions,
        }


class NetworkError(SecretMCPError):
    """Network-related errors.

    Raised when network operations fail, including connection errors,
    timeouts, and HTTP errors when communicating with the blockchain.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize NetworkError.

        Args:
            message: Error message
            **kwargs: Additional arguments passed to SecretMCPError
        """
        super().__init__(message, code="NETWORK_ERROR", **kwargs)


class ValidationError(SecretMCPError):
    """Input validation errors.

    Raised when user input or function arguments fail validation checks,
    such as invalid addresses, amounts, or other parameters.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize ValidationError.

        Args:
            message: Error message
            **kwargs: Additional arguments passed to SecretMCPError
        """
        super().__init__(message, code="VALIDATION_ERROR", **kwargs)


class SecurityError(SecretMCPError):
    """Security-related errors.

    Raised when security operations fail, including encryption/decryption,
    spending limit violations, rate limiting, and other security checks.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize SecurityError.

        Args:
            message: Error message
            **kwargs: Additional arguments passed to SecretMCPError
        """
        super().__init__(message, code="SECURITY_ERROR", **kwargs)


class AuthenticationError(SecretMCPError):
    """Authentication and authorization errors.

    Raised when operations require authentication but no wallet is configured,
    or when authorization checks fail.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize AuthenticationError.

        Args:
            message: Error message
            **kwargs: Additional arguments passed to SecretMCPError
        """
        super().__init__(message, code="AUTHENTICATION_ERROR", **kwargs)


class WalletError(SecretMCPError):
    """Wallet-related errors.

    Raised when wallet operations fail, including wallet creation,
    import, key management, or wallet not found errors.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize WalletError.

        Args:
            message: Error message
            **kwargs: Additional arguments passed to SecretMCPError
        """
        super().__init__(message, code="WALLET_ERROR", **kwargs)


class TransactionError(SecretMCPError):
    """Transaction-related errors.

    Raised when transaction operations fail, including building,
    signing, broadcasting, or executing transactions.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize TransactionError.

        Args:
            message: Error message
            **kwargs: Additional arguments passed to SecretMCPError
        """
        super().__init__(message, code="TRANSACTION_ERROR", **kwargs)


class InsufficientFundsError(TransactionError):
    """Insufficient funds error.

    Raised when an account doesn't have enough balance to complete
    a transaction, including the transaction amount plus fees.

    This is a specialized TransactionError with built-in suggestions
    for resolving insufficient funds issues.
    """

    def __init__(self, required: int, available: int, **kwargs: Any) -> None:
        """Initialize InsufficientFundsError.

        Args:
            required: Required amount in uscrt
            available: Available balance in uscrt
            **kwargs: Additional arguments passed to TransactionError
        """
        message = (
            f"Insufficient funds: required {required} uscrt, " f"available {available} uscrt"
        )

        # Default suggestions if not provided
        if "suggestions" not in kwargs:
            kwargs["suggestions"] = [
                "Check your account balance",
                "Reduce the transfer amount",
                "Add funds to your wallet",
            ]

        # Add amount details if not provided
        if "details" not in kwargs:
            kwargs["details"] = {}
        kwargs["details"]["required"] = required
        kwargs["details"]["available"] = available

        super().__init__(message, **kwargs)


class ContractError(SecretMCPError):
    """Smart contract errors.

    Raised when smart contract operations fail, including upload,
    instantiation, execution, or query errors.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize ContractError.

        Args:
            message: Error message
            **kwargs: Additional arguments passed to SecretMCPError
        """
        super().__init__(message, code="CONTRACT_ERROR", **kwargs)


class CacheError(SecretMCPError):
    """Cache-related errors.

    Raised when cache operations fail, including cache misses,
    invalidation errors, or cache corruption.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize CacheError.

        Args:
            message: Error message
            **kwargs: Additional arguments passed to SecretMCPError
        """
        super().__init__(message, code="CACHE_ERROR", **kwargs)


class ConfigurationError(SecretMCPError):
    """Configuration errors.

    Raised when configuration is invalid or missing required values,
    including environment variables, settings files, or runtime configuration.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize ConfigurationError.

        Args:
            message: Error message
            **kwargs: Additional arguments passed to SecretMCPError
        """
        super().__init__(message, code="CONFIGURATION_ERROR", **kwargs)
