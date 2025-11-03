"""Security module for wallet encryption and transaction safety.

This module provides:
- Wallet data encryption/decryption using Fernet (symmetric encryption)
- Password strength validation
- Spending limit enforcement
- Transaction confirmation logic
- Rate limiting for sensitive operations
- Thread-safe security manager

All sensitive operations are protected with detailed logging.
"""

import base64
import json
import os
import re
import threading
import time
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..config import get_settings
from ..constants import CONFIRMATION_THRESHOLD, DEFAULT_SPENDING_LIMIT
from ..utils.errors import SecurityError, ValidationError
from ..utils.logging import get_logger

# Module logger
logger = get_logger(__name__)

# Type variable for generic functions
F = TypeVar("F", bound=Callable[..., Any])

# Password requirements
MIN_PASSWORD_LENGTH = 12
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$"  # At least one lowercase, uppercase, and digit
)

# Encryption settings
PBKDF2_ITERATIONS = 600_000  # OWASP recommended (2023)
SALT_LENGTH = 16  # 16 bytes for salt


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    pass


class WalletEncryption:
    """Helper class for wallet encryption operations."""

    @staticmethod
    def generate_key(password: str, salt: bytes) -> bytes:
        """Generate encryption key from password using PBKDF2.

        Args:
            password: User password
            salt: Random salt bytes

        Returns:
            Derived key bytes suitable for Fernet
        """
        logger.debug("Generating encryption key from password")

        # Use PBKDF2 to derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # Fernet requires 32 bytes
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
            backend=default_backend(),
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))

        if get_settings().debug:
            logger.debug(
                "Encryption key generated",
                salt_length=len(salt),
                iterations=PBKDF2_ITERATIONS,
            )

        return key

    @staticmethod
    def encrypt(data: bytes, password: str) -> bytes:
        """Encrypt data using password.

        Args:
            data: Data to encrypt
            password: Encryption password

        Returns:
            Encrypted data (salt + encrypted)
        """
        logger.debug("Encrypting data", data_length=len(data))

        # Generate random salt
        salt = os.urandom(SALT_LENGTH)

        # Generate key from password
        key = WalletEncryption.generate_key(password, salt)

        # Create Fernet cipher
        f = Fernet(key)

        # Encrypt data
        encrypted = f.encrypt(data)

        # Prepend salt to encrypted data
        result = salt + encrypted

        logger.info(
            "Data encrypted successfully",
            original_length=len(data),
            encrypted_length=len(result),
        )

        return result

    @staticmethod
    def decrypt(encrypted_data: bytes, password: str) -> bytes:
        """Decrypt data using password.

        Args:
            encrypted_data: Encrypted data (salt + encrypted)
            password: Decryption password

        Returns:
            Decrypted data

        Raises:
            SecurityError: If decryption fails
        """
        logger.debug("Decrypting data", encrypted_length=len(encrypted_data))

        try:
            # Extract salt
            salt = encrypted_data[:SALT_LENGTH]
            encrypted = encrypted_data[SALT_LENGTH:]

            # Generate key from password
            key = WalletEncryption.generate_key(password, salt)

            # Create Fernet cipher
            f = Fernet(key)

            # Decrypt data
            decrypted = f.decrypt(encrypted)

            logger.info("Data decrypted successfully", decrypted_length=len(decrypted))

            return decrypted

        except InvalidToken:
            logger.error("Decryption failed - invalid password or corrupted data")
            raise SecurityError(
                "Failed to decrypt data - invalid password",
                details={"reason": "invalid_token"},
                suggestions=[
                    "Verify the password is correct",
                    "Check that the encrypted data is not corrupted",
                ],
            )
        except Exception as e:
            logger.error("Decryption failed with unexpected error", error=str(e))
            raise SecurityError(
                "Failed to decrypt data",
                details={"error": str(e)},
                suggestions=["Check that the encrypted data is valid"],
            )


def is_strong_password(password: str) -> bool:
    """Check if password meets strength requirements.

    Requirements:
    - At least 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit

    Args:
        password: Password to validate

    Returns:
        True if password is strong, False otherwise
    """
    if not isinstance(password, str):
        return False

    if not password or password.isspace():
        return False

    if len(password) < MIN_PASSWORD_LENGTH:
        return False

    if not PASSWORD_PATTERN.match(password):
        return False

    return True


def encrypt_wallet_data(wallet_data: Dict[str, Any], password: str) -> str:
    """Encrypt wallet data dictionary.

    Args:
        wallet_data: Wallet data to encrypt (will be JSON serialized)
        password: Encryption password

    Returns:
        Base64-encoded encrypted data string

    Raises:
        ValidationError: If password is empty
        SecurityError: If encryption fails
    """
    logger.info("Encrypting wallet data")

    # Validate password
    if not password:
        logger.error("Encryption attempted with empty password")
        raise ValidationError(
            "Password cannot be empty",
            details={"field": "password"},
            suggestions=["Provide a valid password"],
        )

    if get_settings().debug:
        logger.debug(
            "Encrypting wallet data",
            data_keys=list(wallet_data.keys()),
            password_length=len(password),
        )

    try:
        # Serialize wallet data to JSON
        json_data = json.dumps(wallet_data)
        data_bytes = json_data.encode("utf-8")

        # Encrypt
        encrypted_bytes = WalletEncryption.encrypt(data_bytes, password)

        # Encode to base64 for string representation
        encrypted_str = base64.b64encode(encrypted_bytes).decode("utf-8")

        logger.info(
            "Wallet data encrypted successfully", encrypted_length=len(encrypted_str)
        )

        return encrypted_str

    except Exception as e:
        logger.error("Failed to encrypt wallet data", error=str(e))
        raise SecurityError(
            "Failed to encrypt wallet data",
            details={"error": str(e)},
            suggestions=["Check wallet data format", "Verify password is valid"],
        )


def decrypt_wallet_data(encrypted_str: str, password: str) -> Dict[str, Any]:
    """Decrypt wallet data string.

    Args:
        encrypted_str: Base64-encoded encrypted data
        password: Decryption password

    Returns:
        Decrypted wallet data dictionary

    Raises:
        SecurityError: If decryption fails
    """
    logger.info("Decrypting wallet data")

    if get_settings().debug:
        logger.debug(
            "Decrypting wallet data",
            encrypted_length=len(encrypted_str),
            password_length=len(password),
        )

    try:
        # Decode from base64
        encrypted_bytes = base64.b64decode(encrypted_str.encode("utf-8"))

        # Decrypt
        decrypted_bytes = WalletEncryption.decrypt(encrypted_bytes, password)

        # Deserialize from JSON
        json_data = decrypted_bytes.decode("utf-8")
        wallet_data = json.loads(json_data)

        logger.info(
            "Wallet data decrypted successfully",
            data_keys=list(wallet_data.keys()) if isinstance(wallet_data, dict) else None,
        )

        return wallet_data

    except SecurityError:
        # Re-raise security errors as-is
        raise
    except Exception as e:
        logger.error("Failed to decrypt wallet data", error=str(e))
        raise SecurityError(
            "Failed to decrypt wallet data - invalid format or corrupted",
            details={"error": str(e)},
            suggestions=[
                "Verify the encrypted data is valid",
                "Check that the data was encrypted with this tool",
            ],
        )


def check_spending_limit(
    amount: int, limit: Optional[int] = None, field_name: str = "amount"
) -> None:
    """Check if amount is within spending limit.

    Args:
        amount: Amount to check (in base units, e.g., uscrt)
        limit: Optional spending limit (uses DEFAULT_SPENDING_LIMIT if None)
        field_name: Field name for error messages

    Raises:
        ValidationError: If amount is negative
        SecurityError: If amount exceeds limit
    """
    # Validate amount is not negative
    if amount < 0:
        logger.error("Negative amount in spending limit check", amount=amount)
        raise ValidationError(
            f"Amount must be positive: {field_name}",
            details={"field": field_name, "value": amount},
            suggestions=["Provide a positive amount"],
        )

    # Use default limit if not provided
    actual_limit = limit if limit is not None else DEFAULT_SPENDING_LIMIT

    logger.debug(
        "Checking spending limit", amount=amount, limit=actual_limit, field_name=field_name
    )

    if amount > actual_limit:
        logger.warning(
            "Amount exceeds spending limit",
            amount=amount,
            limit=actual_limit,
            excess=amount - actual_limit,
        )
        raise SecurityError(
            f"Amount exceeds spending limit of {actual_limit}",
            details={
                "field": field_name,
                "amount": amount,
                "limit": actual_limit,
                "excess": amount - actual_limit,
            },
            suggestions=[
                f"Reduce amount to {actual_limit} or less",
                "Increase spending limit if authorized",
            ],
        )

    logger.debug("Spending limit check passed", amount=amount, limit=actual_limit)


class ConfirmationRequired:
    """Helper class for transaction confirmation logic."""

    @staticmethod
    def check(amount: int, threshold: Optional[int] = None) -> bool:
        """Check if transaction requires user confirmation.

        Args:
            amount: Transaction amount (in base units)
            threshold: Optional confirmation threshold (uses CONFIRMATION_THRESHOLD if None)

        Returns:
            True if confirmation is required, False otherwise
        """
        actual_threshold = threshold if threshold is not None else CONFIRMATION_THRESHOLD

        logger.debug(
            "Checking confirmation requirement", amount=amount, threshold=actual_threshold
        )

        requires_confirmation = amount > actual_threshold

        if requires_confirmation:
            logger.info(
                "Transaction requires confirmation",
                amount=amount,
                threshold=actual_threshold,
            )
        else:
            logger.debug("Transaction does not require confirmation", amount=amount)

        return requires_confirmation

    @staticmethod
    def get_message(amount: int, denom: str, recipient: str) -> str:
        """Get confirmation message for transaction.

        Args:
            amount: Transaction amount
            denom: Token denomination (e.g., 'uscrt')
            recipient: Recipient address

        Returns:
            Formatted confirmation message
        """
        message = (
            f"Please confirm transaction:\n"
            f"  Amount: {amount:,} {denom}\n"
            f"  Recipient: {recipient}\n"
            f"\nThis transaction exceeds the confirmation threshold."
        )

        logger.debug("Generated confirmation message", amount=amount, recipient=recipient)

        return message


class RateLimiter:
    """Rate limiter for sensitive operations.

    Thread-safe rate limiting with separate tracking per operation.
    """

    def __init__(self, max_calls: int, time_window: float):
        """Initialize rate limiter.

        Args:
            max_calls: Maximum calls allowed in time window
            time_window: Time window in seconds

        Raises:
            ValidationError: If parameters are invalid
        """
        if max_calls <= 0:
            raise ValidationError(
                "max_calls must be positive",
                details={"max_calls": max_calls},
                suggestions=["Provide a positive max_calls value"],
            )

        if time_window <= 0:
            raise ValidationError(
                "time_window must be positive",
                details={"time_window": time_window},
                suggestions=["Provide a positive time_window value"],
            )

        self.max_calls = max_calls
        self.time_window = time_window
        self._calls: Dict[str, list[float]] = {}
        self._lock = threading.RLock()

        logger.info(
            "Rate limiter initialized",
            max_calls=max_calls,
            time_window=time_window,
        )

    def check(self, operation: str) -> None:
        """Check if operation is within rate limit.

        Args:
            operation: Operation identifier

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        with self._lock:
            current_time = time.time()

            # Initialize operation tracking if needed
            if operation not in self._calls:
                self._calls[operation] = []

            # Remove old calls outside time window
            self._calls[operation] = [
                t for t in self._calls[operation] if current_time - t < self.time_window
            ]

            call_count = len(self._calls[operation])

            logger.debug(
                "Rate limit check",
                operation=operation,
                current_calls=call_count,
                max_calls=self.max_calls,
            )

            # Check if limit exceeded
            if call_count >= self.max_calls:
                logger.warning(
                    "Rate limit exceeded",
                    operation=operation,
                    calls=call_count,
                    limit=self.max_calls,
                )
                raise RateLimitExceeded(
                    f"Rate limit exceeded for '{operation}': "
                    f"{call_count}/{self.max_calls} calls in {self.time_window}s window"
                )

            # Record this call
            self._calls[operation].append(current_time)

            logger.debug(
                "Rate limit check passed",
                operation=operation,
                total_calls=len(self._calls[operation]),
            )

    def get_stats(self, operation: str) -> Dict[str, Any]:
        """Get rate limit statistics for operation.

        Args:
            operation: Operation identifier

        Returns:
            Statistics dictionary with calls, limit, remaining
        """
        with self._lock:
            current_time = time.time()

            # Initialize if needed
            if operation not in self._calls:
                self._calls[operation] = []

            # Remove old calls
            self._calls[operation] = [
                t for t in self._calls[operation] if current_time - t < self.time_window
            ]

            call_count = len(self._calls[operation])
            remaining = max(0, self.max_calls - call_count)

            return {
                "calls": call_count,
                "limit": self.max_calls,
                "remaining": remaining,
                "time_window": self.time_window,
            }

    def __call__(self, func: F) -> F:
        """Use as decorator for functions.

        Args:
            func: Function to rate limit

        Returns:
            Decorated function
        """

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            operation_name = func.__name__
            self.check(operation_name)
            return func(*args, **kwargs)

        return cast(F, wrapper)


def rate_limit(max_calls: int, time_window: float) -> RateLimiter:
    """Create a rate limiter.

    Args:
        max_calls: Maximum calls allowed in time window
        time_window: Time window in seconds

    Returns:
        RateLimiter instance that can be used as decorator or called directly

    Example:
        >>> limiter = rate_limit(max_calls=10, time_window=60.0)
        >>> limiter.check("sensitive_operation")

        Or as decorator:
        >>> @rate_limit(max_calls=5, time_window=60.0)
        >>> def sensitive_function():
        >>>     pass
    """
    return RateLimiter(max_calls=max_calls, time_window=time_window)


class SecurityManager:
    """Main security manager for wallet and transaction operations.

    Provides:
    - Spending limit enforcement
    - Transaction confirmation logic
    - Wallet encryption/decryption
    - Security limit management
    """

    def __init__(
        self,
        spending_limit: Optional[int] = None,
        confirmation_threshold: Optional[int] = None,
    ):
        """Initialize security manager.

        Args:
            spending_limit: Optional spending limit (uses DEFAULT_SPENDING_LIMIT if None)
            confirmation_threshold: Optional confirmation threshold (uses CONFIRMATION_THRESHOLD if None)

        Raises:
            ValidationError: If limits are invalid
        """
        # Validate limits if provided
        if spending_limit is not None and spending_limit < 0:
            raise ValidationError(
                "Spending limit must be positive",
                details={"spending_limit": spending_limit},
                suggestions=["Provide a positive spending limit"],
            )

        if confirmation_threshold is not None and confirmation_threshold < 0:
            raise ValidationError(
                "Confirmation threshold must be positive",
                details={"confirmation_threshold": confirmation_threshold},
                suggestions=["Provide a positive confirmation threshold"],
            )

        self.spending_limit = (
            spending_limit if spending_limit is not None else DEFAULT_SPENDING_LIMIT
        )
        self.confirmation_threshold = (
            confirmation_threshold
            if confirmation_threshold is not None
            else CONFIRMATION_THRESHOLD
        )

        self._lock = threading.RLock()

        logger.info(
            "Security manager initialized",
            spending_limit=self.spending_limit,
            confirmation_threshold=self.confirmation_threshold,
        )

    def validate_transaction(self, amount: int) -> Dict[str, Any]:
        """Validate transaction against security policies.

        Args:
            amount: Transaction amount

        Returns:
            Dictionary with:
                - allowed: bool - Whether transaction is allowed
                - confirmation_required: bool - Whether confirmation is needed
                - message: Optional[str] - Confirmation message if required

        Raises:
            SecurityError: If transaction exceeds spending limit
        """
        with self._lock:
            logger.debug(
                "Validating transaction",
                amount=amount,
                spending_limit=self.spending_limit,
                confirmation_threshold=self.confirmation_threshold,
            )

            # Check spending limit
            check_spending_limit(amount, limit=self.spending_limit)

            # Check if confirmation required
            requires_confirmation = ConfirmationRequired.check(
                amount, threshold=self.confirmation_threshold
            )

            result = {
                "allowed": True,
                "confirmation_required": requires_confirmation,
            }

            if requires_confirmation:
                result["message"] = ConfirmationRequired.get_message(
                    amount=amount, denom="uscrt", recipient="(to be specified)"
                )

            logger.info(
                "Transaction validation passed",
                amount=amount,
                confirmation_required=requires_confirmation,
            )

            return result

    def encrypt_wallet(self, wallet_data: Dict[str, Any], password: str) -> str:
        """Encrypt wallet data.

        Args:
            wallet_data: Wallet data to encrypt
            password: Encryption password

        Returns:
            Encrypted wallet data string
        """
        logger.info("Encrypting wallet via security manager")
        return encrypt_wallet_data(wallet_data, password)

    def decrypt_wallet(self, encrypted: str, password: str) -> Dict[str, Any]:
        """Decrypt wallet data.

        Args:
            encrypted: Encrypted wallet data
            password: Decryption password

        Returns:
            Decrypted wallet data
        """
        logger.info("Decrypting wallet via security manager")
        return decrypt_wallet_data(encrypted, password)

    def update_spending_limit(self, limit: int) -> None:
        """Update spending limit.

        Args:
            limit: New spending limit
        """
        with self._lock:
            old_limit = self.spending_limit
            self.spending_limit = limit

            logger.info(
                "Spending limit updated", old_limit=old_limit, new_limit=limit
            )

    def update_confirmation_threshold(self, threshold: int) -> None:
        """Update confirmation threshold.

        Args:
            threshold: New confirmation threshold
        """
        with self._lock:
            old_threshold = self.confirmation_threshold
            self.confirmation_threshold = threshold

            logger.info(
                "Confirmation threshold updated",
                old_threshold=old_threshold,
                new_threshold=threshold,
            )

    def reset_to_defaults(self) -> None:
        """Reset limits to default values."""
        with self._lock:
            self.spending_limit = DEFAULT_SPENDING_LIMIT
            self.confirmation_threshold = CONFIRMATION_THRESHOLD

            logger.info(
                "Security limits reset to defaults",
                spending_limit=self.spending_limit,
                confirmation_threshold=self.confirmation_threshold,
            )

    def get_limits(self) -> Dict[str, int]:
        """Get current security limits.

        Returns:
            Dictionary with spending_limit and confirmation_threshold
        """
        with self._lock:
            return {
                "spending_limit": self.spending_limit,
                "confirmation_threshold": self.confirmation_threshold,
            }
