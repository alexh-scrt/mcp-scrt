"""Unit tests for security module."""

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict

import pytest

from mcp_scrt.core.security import (
    ConfirmationRequired,
    RateLimitExceeded,
    SecurityManager,
    WalletEncryption,
    check_spending_limit,
    encrypt_wallet_data,
    decrypt_wallet_data,
    is_strong_password,
    rate_limit,
)
from mcp_scrt.utils.errors import SecurityError, ValidationError


class TestWalletEncryption:
    """Test wallet encryption and decryption."""

    def test_encrypt_wallet_data(self) -> None:
        """Test encrypting wallet data."""
        wallet_data = {"mnemonic": "test mnemonic phrase", "private_key": "test_key"}
        password = "strong_password_123"

        encrypted = encrypt_wallet_data(wallet_data, password)

        # Should be different from original
        assert encrypted != str(wallet_data)
        # Should be a string
        assert isinstance(encrypted, str)
        # Should be non-empty
        assert len(encrypted) > 0

    def test_decrypt_wallet_data(self) -> None:
        """Test decrypting wallet data."""
        wallet_data = {"mnemonic": "test mnemonic phrase", "private_key": "test_key"}
        password = "strong_password_123"

        encrypted = encrypt_wallet_data(wallet_data, password)
        decrypted = decrypt_wallet_data(encrypted, password)

        assert decrypted == wallet_data

    def test_decrypt_with_wrong_password(self) -> None:
        """Test decrypting with wrong password fails."""
        wallet_data = {"mnemonic": "test mnemonic phrase"}
        password = "strong_password_123"
        wrong_password = "wrong_password"

        encrypted = encrypt_wallet_data(wallet_data, password)

        with pytest.raises(SecurityError, match="(?i)decrypt"):
            decrypt_wallet_data(encrypted, wrong_password)

    def test_encrypt_empty_data(self) -> None:
        """Test encrypting empty data."""
        wallet_data: Dict[str, Any] = {}
        password = "strong_password_123"

        encrypted = encrypt_wallet_data(wallet_data, password)
        decrypted = decrypt_wallet_data(encrypted, password)

        assert decrypted == wallet_data

    def test_encrypt_with_different_passwords(self) -> None:
        """Test encrypting same data with different passwords produces different ciphertexts."""
        wallet_data = {"mnemonic": "test mnemonic phrase"}
        password1 = "password1_abc"
        password2 = "password2_xyz"

        encrypted1 = encrypt_wallet_data(wallet_data, password1)
        encrypted2 = encrypt_wallet_data(wallet_data, password2)

        # Different passwords should produce different encrypted data
        assert encrypted1 != encrypted2

    def test_encrypt_complex_data(self) -> None:
        """Test encrypting complex nested data."""
        wallet_data = {
            "mnemonic": "test mnemonic phrase",
            "accounts": [
                {"index": 0, "address": "secret1abc"},
                {"index": 1, "address": "secret1xyz"},
            ],
            "metadata": {"created": "2024-01-01", "version": 1},
        }
        password = "strong_password_123"

        encrypted = encrypt_wallet_data(wallet_data, password)
        decrypted = decrypt_wallet_data(encrypted, password)

        assert decrypted == wallet_data

    def test_decrypt_invalid_data(self) -> None:
        """Test decrypting invalid encrypted data."""
        invalid_encrypted = "not_valid_encrypted_data"
        password = "password"

        with pytest.raises(SecurityError, match="(?i)decrypt|invalid"):
            decrypt_wallet_data(invalid_encrypted, password)

    def test_encrypt_with_empty_password(self) -> None:
        """Test encrypting with empty password fails."""
        wallet_data = {"mnemonic": "test"}
        password = ""

        with pytest.raises(ValidationError, match="(?i)password"):
            encrypt_wallet_data(wallet_data, password)


class TestPasswordValidation:
    """Test password strength validation."""

    def test_strong_password(self) -> None:
        """Test strong password validation."""
        assert is_strong_password("Strong_Pass123") is True
        assert is_strong_password("MyP@ssw0rd12") is True  # 12 chars
        assert is_strong_password("SecureP@ss123") is True

    def test_weak_password_too_short(self) -> None:
        """Test password that is too short."""
        assert is_strong_password("Short1!") is False
        assert is_strong_password("abc") is False

    def test_weak_password_no_numbers(self) -> None:
        """Test password without numbers."""
        assert is_strong_password("NoNumbersHere!") is False

    def test_weak_password_no_uppercase(self) -> None:
        """Test password without uppercase letters."""
        assert is_strong_password("lowercase123!") is False

    def test_weak_password_no_lowercase(self) -> None:
        """Test password without lowercase letters."""
        assert is_strong_password("UPPERCASE123!") is False

    def test_weak_password_simple(self) -> None:
        """Test simple password."""
        assert is_strong_password("password") is False
        assert is_strong_password("12345678") is False

    def test_password_edge_cases(self) -> None:
        """Test password edge cases."""
        assert is_strong_password("") is False
        assert is_strong_password("   ") is False

    def test_password_minimum_length(self) -> None:
        """Test minimum password length (12 characters)."""
        assert is_strong_password("Short1!") is False  # 7 chars
        assert is_strong_password("Valid_Pass12") is True  # 12 chars


class TestSpendingLimits:
    """Test spending limit enforcement."""

    def test_check_spending_limit_under_limit(self) -> None:
        """Test transaction under spending limit."""
        # Should not raise
        check_spending_limit(amount=500_000, limit=1_000_000)

    def test_check_spending_limit_at_limit(self) -> None:
        """Test transaction at spending limit."""
        # Should not raise
        check_spending_limit(amount=1_000_000, limit=1_000_000)

    def test_check_spending_limit_over_limit(self) -> None:
        """Test transaction over spending limit."""
        with pytest.raises(SecurityError, match="(?i)spending limit"):
            check_spending_limit(amount=2_000_000, limit=1_000_000)

    def test_check_spending_limit_default(self) -> None:
        """Test using default spending limit."""
        from mcp_scrt.constants import DEFAULT_SPENDING_LIMIT

        # Under default limit - should not raise
        check_spending_limit(amount=5_000_000)

        # Over default limit - should raise
        with pytest.raises(SecurityError):
            check_spending_limit(amount=DEFAULT_SPENDING_LIMIT + 1_000_000)

    def test_check_spending_limit_zero(self) -> None:
        """Test zero amount with spending limit."""
        # Zero should be allowed
        check_spending_limit(amount=0, limit=1_000_000)

    def test_check_spending_limit_negative(self) -> None:
        """Test negative amount raises error."""
        with pytest.raises(ValidationError, match="(?i)positive|negative"):
            check_spending_limit(amount=-1000, limit=1_000_000)


class TestConfirmationRequired:
    """Test transaction confirmation logic."""

    def test_confirmation_required_over_threshold(self) -> None:
        """Test confirmation required for amount over threshold."""
        result = ConfirmationRequired.check(amount=2_000_000, threshold=1_000_000)
        assert result is True

    def test_confirmation_not_required_under_threshold(self) -> None:
        """Test confirmation not required for amount under threshold."""
        result = ConfirmationRequired.check(amount=500_000, threshold=1_000_000)
        assert result is False

    def test_confirmation_at_threshold(self) -> None:
        """Test confirmation at exact threshold."""
        result = ConfirmationRequired.check(amount=1_000_000, threshold=1_000_000)
        assert result is False  # At threshold, no confirmation needed

    def test_confirmation_just_over_threshold(self) -> None:
        """Test confirmation just over threshold."""
        result = ConfirmationRequired.check(amount=1_000_001, threshold=1_000_000)
        assert result is True

    def test_confirmation_default_threshold(self) -> None:
        """Test using default confirmation threshold."""
        from mcp_scrt.constants import CONFIRMATION_THRESHOLD

        # Under threshold - no confirmation
        result = ConfirmationRequired.check(amount=CONFIRMATION_THRESHOLD - 1)
        assert result is False

        # Over threshold - confirmation required
        result = ConfirmationRequired.check(amount=CONFIRMATION_THRESHOLD + 1)
        assert result is True

    def test_confirmation_with_message(self) -> None:
        """Test getting confirmation message."""
        msg = ConfirmationRequired.get_message(
            amount=2_000_000, denom="uscrt", recipient="secret1abc..."
        )
        assert "2000000" in msg or "2,000,000" in msg
        assert "uscrt" in msg
        assert "secret1abc" in msg


class TestRateLimiting:
    """Test rate limiting for sensitive operations."""

    def test_rate_limit_allows_within_limit(self) -> None:
        """Test rate limit allows operations within limit."""
        limiter = rate_limit(max_calls=5, time_window=1.0)

        # Should allow 5 calls
        for _ in range(5):
            limiter.check("test_operation")

    def test_rate_limit_blocks_over_limit(self) -> None:
        """Test rate limit blocks operations over limit."""
        limiter = rate_limit(max_calls=3, time_window=1.0)

        # First 3 calls should succeed
        for _ in range(3):
            limiter.check("test_operation")

        # 4th call should raise
        with pytest.raises(RateLimitExceeded, match="(?i)rate limit"):
            limiter.check("test_operation")

    def test_rate_limit_resets_after_time_window(self) -> None:
        """Test rate limit resets after time window."""
        limiter = rate_limit(max_calls=2, time_window=0.5)

        # First 2 calls should succeed
        limiter.check("test_operation")
        limiter.check("test_operation")

        # 3rd call should fail
        with pytest.raises(RateLimitExceeded):
            limiter.check("test_operation")

        # Wait for time window to pass
        time.sleep(0.6)

        # Should allow calls again
        limiter.check("test_operation")
        limiter.check("test_operation")

    def test_rate_limit_different_operations(self) -> None:
        """Test rate limit tracks different operations separately."""
        limiter = rate_limit(max_calls=2, time_window=1.0)

        # Each operation should have its own limit
        limiter.check("operation1")
        limiter.check("operation1")

        limiter.check("operation2")
        limiter.check("operation2")

        # Both should be at limit now
        with pytest.raises(RateLimitExceeded):
            limiter.check("operation1")

        with pytest.raises(RateLimitExceeded):
            limiter.check("operation2")

    def test_rate_limit_decorator(self) -> None:
        """Test rate limit as function decorator."""

        @rate_limit(max_calls=3, time_window=1.0)
        def sensitive_operation(value: int) -> int:
            return value * 2

        # Should allow 3 calls
        assert sensitive_operation(5) == 10
        assert sensitive_operation(6) == 12
        assert sensitive_operation(7) == 14

        # 4th call should raise
        with pytest.raises(RateLimitExceeded):
            sensitive_operation(8)

    def test_rate_limit_get_stats(self) -> None:
        """Test getting rate limit statistics."""
        limiter = rate_limit(max_calls=5, time_window=1.0)

        limiter.check("test_op")
        limiter.check("test_op")

        stats = limiter.get_stats("test_op")
        assert stats["calls"] == 2
        assert stats["limit"] == 5
        assert stats["remaining"] == 3


class TestSecurityManager:
    """Test SecurityManager class."""

    def test_security_manager_creation(self) -> None:
        """Test creating security manager."""
        manager = SecurityManager(
            spending_limit=5_000_000, confirmation_threshold=1_000_000
        )

        assert manager.spending_limit == 5_000_000
        assert manager.confirmation_threshold == 1_000_000

    def test_security_manager_default_limits(self) -> None:
        """Test security manager with default limits."""
        from mcp_scrt.constants import CONFIRMATION_THRESHOLD, DEFAULT_SPENDING_LIMIT

        manager = SecurityManager()

        assert manager.spending_limit == DEFAULT_SPENDING_LIMIT
        assert manager.confirmation_threshold == CONFIRMATION_THRESHOLD

    def test_security_manager_validate_transaction(self) -> None:
        """Test validating transaction through security manager."""
        manager = SecurityManager(
            spending_limit=10_000_000, confirmation_threshold=1_000_000
        )

        # Under both limits - should not raise or require confirmation
        result = manager.validate_transaction(amount=500_000)
        assert result["allowed"] is True
        assert result["confirmation_required"] is False

    def test_security_manager_validate_over_spending_limit(self) -> None:
        """Test transaction over spending limit."""
        manager = SecurityManager(spending_limit=5_000_000)

        with pytest.raises(SecurityError, match="(?i)spending limit"):
            manager.validate_transaction(amount=10_000_000)

    def test_security_manager_validate_requires_confirmation(self) -> None:
        """Test transaction requiring confirmation."""
        manager = SecurityManager(
            spending_limit=10_000_000, confirmation_threshold=1_000_000
        )

        # Over confirmation threshold but under spending limit
        result = manager.validate_transaction(amount=2_000_000)
        assert result["allowed"] is True
        assert result["confirmation_required"] is True
        assert "message" in result

    def test_security_manager_encrypt_decrypt_wallet(self) -> None:
        """Test encrypting and decrypting wallet through security manager."""
        manager = SecurityManager()
        wallet_data = {"mnemonic": "test mnemonic phrase"}
        password = "Strong_Pass123"

        # Encrypt
        encrypted = manager.encrypt_wallet(wallet_data, password)
        assert encrypted != str(wallet_data)

        # Decrypt
        decrypted = manager.decrypt_wallet(encrypted, password)
        assert decrypted == wallet_data

    def test_security_manager_update_limits(self) -> None:
        """Test updating security limits."""
        manager = SecurityManager(spending_limit=5_000_000)

        manager.update_spending_limit(10_000_000)
        assert manager.spending_limit == 10_000_000

        manager.update_confirmation_threshold(2_000_000)
        assert manager.confirmation_threshold == 2_000_000

    def test_security_manager_reset_limits(self) -> None:
        """Test resetting to default limits."""
        from mcp_scrt.constants import CONFIRMATION_THRESHOLD, DEFAULT_SPENDING_LIMIT

        manager = SecurityManager(spending_limit=5_000_000, confirmation_threshold=500_000)

        manager.reset_to_defaults()

        assert manager.spending_limit == DEFAULT_SPENDING_LIMIT
        assert manager.confirmation_threshold == CONFIRMATION_THRESHOLD

    def test_security_manager_get_limits(self) -> None:
        """Test getting current limits."""
        manager = SecurityManager(
            spending_limit=7_000_000, confirmation_threshold=1_500_000
        )

        limits = manager.get_limits()
        assert limits["spending_limit"] == 7_000_000
        assert limits["confirmation_threshold"] == 1_500_000


class TestWalletEncryptionClass:
    """Test WalletEncryption helper class."""

    def test_wallet_encryption_generate_key(self) -> None:
        """Test generating encryption key from password."""
        password = "test_password_123"
        salt = b"test_salt_16bytes"

        key = WalletEncryption.generate_key(password, salt)

        assert isinstance(key, bytes)
        assert len(key) > 0

    def test_wallet_encryption_same_password_same_key(self) -> None:
        """Test same password and salt generate same key."""
        password = "test_password_123"
        salt = b"test_salt_16bytes"

        key1 = WalletEncryption.generate_key(password, salt)
        key2 = WalletEncryption.generate_key(password, salt)

        assert key1 == key2

    def test_wallet_encryption_different_salt_different_key(self) -> None:
        """Test different salt generates different key."""
        password = "test_password_123"
        salt1 = b"salt1_16bytes123"
        salt2 = b"salt2_16bytes456"

        key1 = WalletEncryption.generate_key(password, salt1)
        key2 = WalletEncryption.generate_key(password, salt2)

        assert key1 != key2

    def test_wallet_encryption_encrypt_decrypt(self) -> None:
        """Test encrypting and decrypting data."""
        data = b"sensitive wallet data"
        password = "Strong_Pass123"

        encrypted = WalletEncryption.encrypt(data, password)
        assert encrypted != data

        decrypted = WalletEncryption.decrypt(encrypted, password)
        assert decrypted == data


class TestSecurityThreadSafety:
    """Test thread safety of security operations."""

    def test_concurrent_rate_limiting(self) -> None:
        """Test rate limiter with concurrent access."""
        limiter = rate_limit(max_calls=10, time_window=1.0)
        successful_calls = []

        def make_call(call_id: int) -> None:
            try:
                limiter.check("concurrent_test")
                successful_calls.append(call_id)
            except RateLimitExceeded:
                pass

        # Try 20 concurrent calls (only 10 should succeed)
        with ThreadPoolExecutor(max_workers=20) as executor:
            list(executor.map(make_call, range(20)))

        # Should allow exactly 10 calls
        assert len(successful_calls) == 10

    def test_concurrent_encryption(self) -> None:
        """Test concurrent encryption operations."""
        wallet_data = {"mnemonic": "test phrase"}
        password = "Strong_Pass123"
        results = []

        def encrypt_data(thread_id: int) -> None:
            encrypted = encrypt_wallet_data(wallet_data, password)
            results.append((thread_id, encrypted))

        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(encrypt_data, range(5)))

        # All should succeed
        assert len(results) == 5

    def test_concurrent_security_manager_validation(self) -> None:
        """Test concurrent transaction validation."""
        manager = SecurityManager(spending_limit=10_000_000)
        results = []

        def validate_tx(amount: int) -> None:
            try:
                result = manager.validate_transaction(amount=amount)
                results.append(("success", result))
            except SecurityError as e:
                results.append(("error", str(e)))

        amounts = [500_000, 1_000_000, 2_000_000, 15_000_000, 3_000_000]

        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(validate_tx, amounts))

        # Should have 4 successes and 1 error (15M over limit)
        successes = [r for r in results if r[0] == "success"]
        errors = [r for r in results if r[0] == "error"]

        assert len(successes) == 4
        assert len(errors) == 1


class TestSecurityEdgeCases:
    """Test edge cases in security module."""

    def test_encrypt_very_large_data(self) -> None:
        """Test encrypting very large data."""
        large_data = {"data": "x" * 100000}  # 100KB of data
        password = "Strong_Pass123"

        encrypted = encrypt_wallet_data(large_data, password)
        decrypted = decrypt_wallet_data(encrypted, password)

        assert decrypted == large_data

    def test_rate_limit_zero_time_window(self) -> None:
        """Test rate limiter with zero time window."""
        with pytest.raises(ValidationError, match="(?i)time.window|positive"):
            rate_limit(max_calls=5, time_window=0.0)

    def test_rate_limit_zero_max_calls(self) -> None:
        """Test rate limiter with zero max calls."""
        with pytest.raises(ValidationError, match="(?i)max.calls|positive"):
            rate_limit(max_calls=0, time_window=1.0)

    def test_spending_limit_boundary(self) -> None:
        """Test spending limit at exact boundary."""
        limit = 1_000_000

        # Exactly at limit should pass
        check_spending_limit(amount=limit, limit=limit)

        # One over limit should fail
        with pytest.raises(SecurityError):
            check_spending_limit(amount=limit + 1, limit=limit)

    def test_security_manager_negative_limits(self) -> None:
        """Test security manager rejects negative limits."""
        with pytest.raises(ValidationError, match="(?i)positive|negative"):
            SecurityManager(spending_limit=-1000)

        with pytest.raises(ValidationError, match="(?i)positive|negative"):
            SecurityManager(confirmation_threshold=-1000)

    def test_password_with_special_characters(self) -> None:
        """Test password validation with various special characters."""
        assert is_strong_password("P@ssw0rd!#$%") is True
        assert is_strong_password("Secur3_P@ss!") is True

    def test_wallet_encryption_unicode_data(self) -> None:
        """Test encrypting wallet data with unicode characters."""
        wallet_data = {"mnemonic": "test 测试 тест 🔐"}
        password = "Strong_Pass123"

        encrypted = encrypt_wallet_data(wallet_data, password)
        decrypted = decrypt_wallet_data(encrypted, password)

        assert decrypted == wallet_data
