"""Unit tests for input validation."""

import pytest

from mcp_scrt.core.validation import (
    is_valid_address,
    is_valid_amount,
    is_valid_contract_address,
    is_valid_hd_path,
    is_valid_validator_address,
    validate_address,
    validate_amount,
    validate_contract_address,
    validate_hd_path,
    validate_transaction_params,
    validate_validator_address,
)
from mcp_scrt.utils.errors import ValidationError


class TestAddressValidation:
    """Test Secret Network address validation."""

    def test_valid_address(self) -> None:
        """Test validating a valid Secret Network address."""
        address = "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"
        assert is_valid_address(address) is True

    def test_valid_address_different_length(self) -> None:
        """Test address with different valid length."""
        address = "secret1test123456789abcdefghijklmnopqrstuvwxyz"
        assert is_valid_address(address) is True

    def test_invalid_address_wrong_prefix(self) -> None:
        """Test address with wrong prefix."""
        address = "cosmos1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"
        assert is_valid_address(address) is False

    def test_invalid_address_too_short(self) -> None:
        """Test address that is too short."""
        address = "secret1test"
        assert is_valid_address(address) is False

    def test_invalid_address_no_prefix(self) -> None:
        """Test address without prefix."""
        address = "ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"
        assert is_valid_address(address) is False

    def test_invalid_address_empty(self) -> None:
        """Test empty address."""
        assert is_valid_address("") is False

    def test_invalid_address_invalid_chars(self) -> None:
        """Test address with invalid characters."""
        address = "secret1!@#$%^&*()"
        assert is_valid_address(address) is False

    def test_validate_address_success(self) -> None:
        """Test validate_address with valid address."""
        address = "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"
        # Should not raise
        validate_address(address)

    def test_validate_address_failure(self) -> None:
        """Test validate_address with invalid address."""
        with pytest.raises(ValidationError, match="Invalid Secret Network address"):
            validate_address("invalid_address")

    def test_validate_address_custom_name(self) -> None:
        """Test validate_address with custom field name."""
        with pytest.raises(ValidationError, match="recipient"):
            validate_address("invalid", field_name="recipient")


class TestValidatorAddressValidation:
    """Test validator address validation."""

    def test_valid_validator_address(self) -> None:
        """Test validating a valid validator address."""
        address = "secretvaloper1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a123456"
        assert is_valid_validator_address(address) is True

    def test_invalid_validator_address_wrong_prefix(self) -> None:
        """Test validator address with wrong prefix."""
        address = "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"
        assert is_valid_validator_address(address) is False

    def test_invalid_validator_address_empty(self) -> None:
        """Test empty validator address."""
        assert is_valid_validator_address("") is False

    def test_validate_validator_address_success(self) -> None:
        """Test validate_validator_address with valid address."""
        address = "secretvaloper1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a123456"
        validate_validator_address(address)

    def test_validate_validator_address_failure(self) -> None:
        """Test validate_validator_address with invalid address."""
        with pytest.raises(ValidationError, match="Invalid validator address"):
            validate_validator_address("invalid_address")


class TestContractAddressValidation:
    """Test contract address validation."""

    def test_valid_contract_address(self) -> None:
        """Test validating a valid contract address."""
        address = "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"
        assert is_valid_contract_address(address) is True

    def test_invalid_contract_address(self) -> None:
        """Test invalid contract address."""
        assert is_valid_contract_address("invalid") is False

    def test_validate_contract_address_success(self) -> None:
        """Test validate_contract_address with valid address."""
        address = "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03"
        validate_contract_address(address)

    def test_validate_contract_address_failure(self) -> None:
        """Test validate_contract_address with invalid address."""
        with pytest.raises(ValidationError, match="Invalid contract address"):
            validate_contract_address("invalid")


class TestAmountValidation:
    """Test amount validation."""

    def test_valid_amount_integer(self) -> None:
        """Test valid integer amount."""
        assert is_valid_amount(1000) is True

    def test_valid_amount_string(self) -> None:
        """Test valid string amount."""
        assert is_valid_amount("1000") is True

    def test_valid_amount_zero(self) -> None:
        """Test zero amount with allow_zero."""
        assert is_valid_amount(0, allow_zero=True) is True

    def test_invalid_amount_zero_not_allowed(self) -> None:
        """Test zero amount when not allowed."""
        assert is_valid_amount(0, allow_zero=False) is False

    def test_invalid_amount_negative(self) -> None:
        """Test negative amount."""
        assert is_valid_amount(-100) is False

    def test_invalid_amount_string_negative(self) -> None:
        """Test negative string amount."""
        assert is_valid_amount("-100") is False

    def test_invalid_amount_non_numeric_string(self) -> None:
        """Test non-numeric string amount."""
        assert is_valid_amount("not_a_number") is False

    def test_invalid_amount_empty_string(self) -> None:
        """Test empty string amount."""
        assert is_valid_amount("") is False

    def test_valid_amount_with_max(self) -> None:
        """Test amount within max limit."""
        assert is_valid_amount(100, max_amount=1000) is True

    def test_invalid_amount_exceeds_max(self) -> None:
        """Test amount exceeding max limit."""
        assert is_valid_amount(1000, max_amount=100) is False

    def test_validate_amount_success(self) -> None:
        """Test validate_amount with valid amount."""
        validate_amount(1000)

    def test_validate_amount_failure_negative(self) -> None:
        """Test validate_amount with negative amount."""
        with pytest.raises(ValidationError, match="must be positive"):
            validate_amount(-100)

    def test_validate_amount_failure_zero(self) -> None:
        """Test validate_amount with zero when not allowed."""
        with pytest.raises(ValidationError, match="must be positive"):
            validate_amount(0, allow_zero=False)

    def test_validate_amount_success_zero_allowed(self) -> None:
        """Test validate_amount with zero when allowed."""
        validate_amount(0, allow_zero=True)

    def test_validate_amount_failure_exceeds_max(self) -> None:
        """Test validate_amount exceeding max."""
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_amount(1000, max_amount=100)

    def test_validate_amount_custom_field_name(self) -> None:
        """Test validate_amount with custom field name."""
        with pytest.raises(ValidationError, match="transfer_amount"):
            validate_amount(-100, field_name="transfer_amount")


class TestHDPathValidation:
    """Test HD path validation."""

    def test_valid_hd_path_default(self) -> None:
        """Test valid default HD path."""
        path = "m/44'/529'/0'/0/0"
        assert is_valid_hd_path(path) is True

    def test_valid_hd_path_different_account(self) -> None:
        """Test valid HD path with different account."""
        path = "m/44'/529'/5'/0/0"
        assert is_valid_hd_path(path) is True

    def test_valid_hd_path_different_index(self) -> None:
        """Test valid HD path with different index."""
        path = "m/44'/529'/0'/0/10"
        assert is_valid_hd_path(path) is True

    def test_invalid_hd_path_wrong_purpose(self) -> None:
        """Test HD path with wrong purpose."""
        path = "m/43'/529'/0'/0/0"
        assert is_valid_hd_path(path) is False

    def test_invalid_hd_path_wrong_coin_type(self) -> None:
        """Test HD path with wrong coin type."""
        path = "m/44'/60'/0'/0/0"  # Ethereum coin type
        assert is_valid_hd_path(path) is False

    def test_invalid_hd_path_missing_parts(self) -> None:
        """Test HD path with missing parts."""
        path = "m/44'/529'/0'"
        assert is_valid_hd_path(path) is False

    def test_invalid_hd_path_empty(self) -> None:
        """Test empty HD path."""
        assert is_valid_hd_path("") is False

    def test_invalid_hd_path_no_prefix(self) -> None:
        """Test HD path without m/ prefix."""
        path = "44'/529'/0'/0/0"
        assert is_valid_hd_path(path) is False

    def test_validate_hd_path_success(self) -> None:
        """Test validate_hd_path with valid path."""
        validate_hd_path("m/44'/529'/0'/0/0")

    def test_validate_hd_path_failure(self) -> None:
        """Test validate_hd_path with invalid path."""
        with pytest.raises(ValidationError, match="Invalid HD path"):
            validate_hd_path("invalid_path")


class TestTransactionParamsValidation:
    """Test transaction parameter validation."""

    def test_valid_transaction_params_minimal(self) -> None:
        """Test valid transaction params with minimal fields."""
        params = {
            "from_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
            "to_address": "secret1test123456789abcdefghijklmnopqrstuvwxyz",
            "amount": "1000",
        }
        validate_transaction_params(params)

    def test_valid_transaction_params_with_memo(self) -> None:
        """Test valid transaction params with memo."""
        params = {
            "from_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
            "to_address": "secret1test123456789abcdefghijklmnopqrstuvwxyz",
            "amount": "1000",
            "memo": "Test transfer",
        }
        validate_transaction_params(params)

    def test_valid_transaction_params_with_gas(self) -> None:
        """Test valid transaction params with gas."""
        params = {
            "from_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
            "to_address": "secret1test123456789abcdefghijklmnopqrstuvwxyz",
            "amount": "1000",
            "gas": "200000",
        }
        validate_transaction_params(params)

    def test_invalid_transaction_params_missing_from(self) -> None:
        """Test transaction params missing from_address."""
        params = {
            "to_address": "secret1test123456789abcdefghijklmnopqrstuvwxyz",
            "amount": "1000",
        }
        with pytest.raises(ValidationError, match="from_address"):
            validate_transaction_params(params)

    def test_invalid_transaction_params_missing_to(self) -> None:
        """Test transaction params missing to_address."""
        params = {
            "from_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
            "amount": "1000",
        }
        with pytest.raises(ValidationError, match="to_address"):
            validate_transaction_params(params)

    def test_invalid_transaction_params_missing_amount(self) -> None:
        """Test transaction params missing amount."""
        params = {
            "from_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
            "to_address": "secret1test123456789abcdefghijklmnopqrstuvwxyz",
        }
        with pytest.raises(ValidationError, match="amount"):
            validate_transaction_params(params)

    def test_invalid_transaction_params_invalid_from(self) -> None:
        """Test transaction params with invalid from_address."""
        params = {
            "from_address": "invalid_address",
            "to_address": "secret1test123456789abcdefghijklmnopqrstuvwxyz",
            "amount": "1000",
        }
        with pytest.raises(ValidationError, match="from_address"):
            validate_transaction_params(params)

    def test_invalid_transaction_params_invalid_to(self) -> None:
        """Test transaction params with invalid to_address."""
        params = {
            "from_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
            "to_address": "invalid_address",
            "amount": "1000",
        }
        with pytest.raises(ValidationError, match="to_address"):
            validate_transaction_params(params)

    def test_invalid_transaction_params_invalid_amount(self) -> None:
        """Test transaction params with invalid amount."""
        params = {
            "from_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
            "to_address": "secret1test123456789abcdefghijklmnopqrstuvwxyz",
            "amount": "-1000",
        }
        with pytest.raises(ValidationError, match="amount"):
            validate_transaction_params(params)

    def test_invalid_transaction_params_empty_memo(self) -> None:
        """Test transaction params with empty memo should be ok."""
        params = {
            "from_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
            "to_address": "secret1test123456789abcdefghijklmnopqrstuvwxyz",
            "amount": "1000",
            "memo": "",
        }
        # Empty memo should be allowed
        validate_transaction_params(params)

    def test_invalid_transaction_params_memo_too_long(self) -> None:
        """Test transaction params with memo that's too long."""
        params = {
            "from_address": "secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
            "to_address": "secret1test123456789abcdefghijklmnopqrstuvwxyz",
            "amount": "1000",
            "memo": "x" * 300,  # Too long
        }
        with pytest.raises(ValidationError, match="(?i)memo"):  # Case-insensitive
            validate_transaction_params(params)


class TestValidationEdgeCases:
    """Test edge cases in validation."""

    def test_address_with_whitespace(self) -> None:
        """Test address with leading/trailing whitespace."""
        address = "  secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03  "
        # Whitespace should make it invalid
        assert is_valid_address(address) is False

    def test_amount_with_whitespace(self) -> None:
        """Test amount string with whitespace."""
        assert is_valid_amount("  1000  ") is False

    def test_amount_float_string(self) -> None:
        """Test amount as float string."""
        # Should be valid as it can be converted to number
        assert is_valid_amount("1000.5") is True

    def test_amount_very_large(self) -> None:
        """Test very large amount."""
        large_amount = 10**18
        assert is_valid_amount(large_amount) is True

    def test_hd_path_with_large_numbers(self) -> None:
        """Test HD path with large account/index numbers."""
        path = "m/44'/529'/999'/0/999"
        assert is_valid_hd_path(path) is True

    def test_none_values(self) -> None:
        """Test None values in validation."""
        assert is_valid_address(None) is False  # type: ignore
        assert is_valid_amount(None) is False  # type: ignore
        assert is_valid_hd_path(None) is False  # type: ignore
