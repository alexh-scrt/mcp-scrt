"""Input validation for Secret Network operations.

This module provides validation functions for:
- Secret Network addresses (bech32 format)
- Validator addresses
- Contract addresses
- Amounts and balances
- HD wallet paths (BIP44)
- Transaction parameters

All validation functions come in two forms:
- is_valid_*: Returns bool, never raises
- validate_*: Raises ValidationError if invalid
"""

import re
from typing import Any, Dict, Optional, Union

from ..constants import VALIDATION_PATTERNS
from ..utils.errors import ValidationError
from ..utils.logging import get_logger

# Module logger
logger = get_logger(__name__)

# Maximum memo length for transactions (Cosmos standard)
MAX_MEMO_LENGTH = 256


def is_valid_address(address: Any) -> bool:
    """Check if address is a valid Secret Network address.

    Args:
        address: Address to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> is_valid_address("secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03")
        True
        >>> is_valid_address("cosmos1...")
        False
    """
    if not isinstance(address, str):
        return False

    if not address:
        return False

    # Check against regex pattern from constants
    pattern = VALIDATION_PATTERNS["address"]
    return bool(re.match(pattern, address))


def validate_address(address: str, field_name: str = "address") -> None:
    """Validate a Secret Network address, raising error if invalid.

    Args:
        address: Address to validate
        field_name: Name of field for error message

    Raises:
        ValidationError: If address is invalid

    Example:
        >>> validate_address("secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03")
        >>> validate_address("invalid")  # Raises ValidationError
    """
    if not is_valid_address(address):
        logger.error(
            "Address validation failed",
            address=address[:20] + "..." if len(address) > 20 else address,
            field_name=field_name,
        )
        raise ValidationError(
            f"Invalid Secret Network address for {field_name}",
            details={"field": field_name, "value": address},
            suggestions=[
                "Ensure address starts with 'secret1'",
                "Check that address is in bech32 format",
                "Verify address length (typically 45 characters)",
            ],
        )

    logger.debug("Address validation passed", field_name=field_name)


def is_valid_validator_address(address: Any) -> bool:
    """Check if address is a valid Secret Network validator address.

    Validator addresses start with 'secretvaloper' instead of 'secret'.

    Args:
        address: Address to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> is_valid_validator_address("secretvaloper1...")
        True
    """
    if not isinstance(address, str):
        return False

    if not address:
        return False

    pattern = VALIDATION_PATTERNS["validator"]
    return bool(re.match(pattern, address))


def validate_validator_address(address: str, field_name: str = "validator_address") -> None:
    """Validate a validator address, raising error if invalid.

    Args:
        address: Validator address to validate
        field_name: Name of field for error message

    Raises:
        ValidationError: If address is invalid
    """
    if not is_valid_validator_address(address):
        logger.error("Validator address validation failed", field_name=field_name)
        raise ValidationError(
            f"Invalid validator address for {field_name}",
            details={"field": field_name, "value": address},
            suggestions=[
                "Ensure address starts with 'secretvaloper'",
                "Check that address is in bech32 format",
            ],
        )

    logger.debug("Validator address validation passed", field_name=field_name)


def is_valid_contract_address(address: Any) -> bool:
    """Check if address is a valid Secret Network contract address.

    Contract addresses use the same format as regular addresses.

    Args:
        address: Address to validate

    Returns:
        True if valid, False otherwise
    """
    # Contract addresses use same format as regular addresses
    return is_valid_address(address)


def validate_contract_address(address: str, field_name: str = "contract_address") -> None:
    """Validate a contract address, raising error if invalid.

    Args:
        address: Contract address to validate
        field_name: Name of field for error message

    Raises:
        ValidationError: If address is invalid
    """
    if not is_valid_contract_address(address):
        logger.error("Contract address validation failed", field_name=field_name)
        raise ValidationError(
            f"Invalid contract address for {field_name}",
            details={"field": field_name, "value": address},
            suggestions=[
                "Ensure address starts with 'secret1'",
                "Check that address is in bech32 format",
            ],
        )

    logger.debug("Contract address validation passed", field_name=field_name)


def is_valid_amount(
    amount: Any,
    allow_zero: bool = False,
    max_amount: Optional[Union[int, float]] = None,
) -> bool:
    """Check if amount is valid.

    Args:
        amount: Amount to validate (int, float, or string)
        allow_zero: Whether zero is allowed
        max_amount: Optional maximum amount

    Returns:
        True if valid, False otherwise

    Example:
        >>> is_valid_amount(1000)
        True
        >>> is_valid_amount(0, allow_zero=True)
        True
        >>> is_valid_amount(-100)
        False
    """
    # Handle None
    if amount is None:
        return False

    # Try to convert to float
    try:
        if isinstance(amount, str):
            # Don't allow whitespace
            if amount != amount.strip():
                return False
            numeric_amount = float(amount)
        else:
            numeric_amount = float(amount)
    except (ValueError, TypeError):
        return False

    # Check if negative
    if numeric_amount < 0:
        return False

    # Check if zero when not allowed
    if numeric_amount == 0 and not allow_zero:
        return False

    # Check max amount
    if max_amount is not None and numeric_amount > max_amount:
        return False

    return True


def validate_amount(
    amount: Union[int, float, str],
    field_name: str = "amount",
    allow_zero: bool = False,
    max_amount: Optional[Union[int, float]] = None,
) -> None:
    """Validate an amount, raising error if invalid.

    Args:
        amount: Amount to validate
        field_name: Name of field for error message
        allow_zero: Whether zero is allowed
        max_amount: Optional maximum amount

    Raises:
        ValidationError: If amount is invalid

    Example:
        >>> validate_amount(1000)
        >>> validate_amount(-100)  # Raises ValidationError
    """
    if not is_valid_amount(amount, allow_zero=allow_zero, max_amount=max_amount):
        # Determine specific error
        try:
            numeric_amount = float(amount) if isinstance(amount, (int, float, str)) else None
        except (ValueError, TypeError):
            numeric_amount = None

        if numeric_amount is None:
            error_msg = f"Invalid {field_name}: must be a valid number"
            suggestions = ["Provide a numeric value", "Check for typos in the amount"]
        elif numeric_amount < 0:
            error_msg = f"Invalid {field_name}: must be positive"
            suggestions = ["Provide a positive amount"]
        elif numeric_amount == 0 and not allow_zero:
            error_msg = f"Invalid {field_name}: must be positive (zero not allowed)"
            suggestions = ["Provide an amount greater than zero"]
        elif max_amount is not None and numeric_amount > max_amount:
            error_msg = f"Invalid {field_name}: exceeds maximum of {max_amount}"
            suggestions = [f"Provide an amount less than or equal to {max_amount}"]
        else:
            error_msg = f"Invalid {field_name}"
            suggestions = ["Check the amount value"]

        logger.error(
            "Amount validation failed",
            field_name=field_name,
            amount=amount,
            allow_zero=allow_zero,
            max_amount=max_amount,
        )

        raise ValidationError(
            error_msg,
            details={
                "field": field_name,
                "value": str(amount),
                "allow_zero": allow_zero,
                "max_amount": max_amount,
            },
            suggestions=suggestions,
        )

    logger.debug(
        "Amount validation passed",
        field_name=field_name,
        amount=amount,
    )


def is_valid_hd_path(path: Any) -> bool:
    """Check if HD path is valid for Secret Network (BIP44).

    Valid format: m/44'/529'/account'/0/index
    Where 529 is the Secret Network coin type.

    Args:
        path: HD path to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> is_valid_hd_path("m/44'/529'/0'/0/0")
        True
        >>> is_valid_hd_path("m/44'/60'/0'/0/0")  # Ethereum
        False
    """
    if not isinstance(path, str):
        return False

    if not path:
        return False

    # Pattern: m/44'/529'/account'/0/index
    # Purpose: 44 (BIP44)
    # Coin type: 529 (Secret Network)
    # Account: any number with '
    # Change: 0
    # Index: any number
    pattern = r"^m/44'/529'/\d+'/0/\d+$"
    return bool(re.match(pattern, path))


def validate_hd_path(path: str, field_name: str = "hd_path") -> None:
    """Validate an HD path, raising error if invalid.

    Args:
        path: HD path to validate
        field_name: Name of field for error message

    Raises:
        ValidationError: If path is invalid

    Example:
        >>> validate_hd_path("m/44'/529'/0'/0/0")
        >>> validate_hd_path("invalid")  # Raises ValidationError
    """
    if not is_valid_hd_path(path):
        logger.error("HD path validation failed", path=path, field_name=field_name)
        raise ValidationError(
            f"Invalid HD path for {field_name}",
            details={"field": field_name, "value": path},
            suggestions=[
                "Use format: m/44'/529'/account'/0/index",
                "Ensure coin type is 529 (Secret Network)",
                "Common path: m/44'/529'/0'/0/0",
            ],
        )

    logger.debug("HD path validation passed", path=path)


def validate_transaction_params(params: Dict[str, Any]) -> None:
    """Validate transaction parameters.

    Args:
        params: Transaction parameters dict with:
            - from_address: Sender address (required)
            - to_address: Recipient address (required)
            - amount: Amount to send (required)
            - memo: Optional memo (max 256 chars)
            - gas: Optional gas limit

    Raises:
        ValidationError: If any parameter is invalid

    Example:
        >>> validate_transaction_params({
        ...     "from_address": "secret1...",
        ...     "to_address": "secret1...",
        ...     "amount": "1000",
        ... })
    """
    logger.debug("Validating transaction params", param_keys=list(params.keys()))

    # Check required fields
    required_fields = ["from_address", "to_address", "amount"]
    for field in required_fields:
        if field not in params:
            logger.error("Missing required field", field=field)
            raise ValidationError(
                f"Missing required field: {field}",
                details={"missing_field": field, "provided_fields": list(params.keys())},
                suggestions=[f"Provide '{field}' in transaction parameters"],
            )

    # Validate from_address
    try:
        validate_address(params["from_address"], field_name="from_address")
    except ValidationError:
        # Re-raise with transaction context
        raise

    # Validate to_address
    try:
        validate_address(params["to_address"], field_name="to_address")
    except ValidationError:
        raise

    # Validate amount
    try:
        validate_amount(params["amount"], field_name="amount", allow_zero=False)
    except ValidationError:
        raise

    # Validate optional memo
    if "memo" in params and params["memo"]:
        memo = params["memo"]
        if len(memo) > MAX_MEMO_LENGTH:
            logger.error("Memo too long", memo_length=len(memo), max_length=MAX_MEMO_LENGTH)
            raise ValidationError(
                f"Memo exceeds maximum length of {MAX_MEMO_LENGTH} characters",
                details={
                    "field": "memo",
                    "length": len(memo),
                    "max_length": MAX_MEMO_LENGTH,
                },
                suggestions=[f"Shorten memo to {MAX_MEMO_LENGTH} characters or less"],
            )

    # Validate optional gas
    if "gas" in params:
        try:
            validate_amount(params["gas"], field_name="gas", allow_zero=False)
        except ValidationError:
            raise

    logger.info("Transaction params validation passed")
