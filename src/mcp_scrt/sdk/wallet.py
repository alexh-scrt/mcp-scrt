"""HD Wallet operations for Secret Network.

This module provides HD wallet functionality including:
- Mnemonic generation and validation (BIP39)
- HD key derivation (BIP32/BIP44/SLIP10)
- Secret Network address generation
- Transaction signing
- Multi-account support

All operations follow the BIP44 standard with Secret Network's coin type (529):
  m/44'/529'/account'/0/index
"""

import hashlib
import uuid
from typing import Optional

from mnemonic import Mnemonic
from secret_sdk.key.mnemonic import MnemonicKey

from ..config import get_settings
from ..core.validation import validate_hd_path
from ..types import WalletInfo
from ..utils.errors import ValidationError, WalletError
from ..utils.logging import get_logger

# Module logger
logger = get_logger(__name__)

# BIP39 word counts
VALID_WORD_COUNTS = [12, 15, 18, 21, 24]

# Secret Network coin type (BIP44)
SECRET_COIN_TYPE = 529


def generate_mnemonic(word_count: int = 24) -> str:
    """Generate a new BIP39 mnemonic phrase.

    Args:
        word_count: Number of words (12, 15, 18, 21, or 24). Default: 24

    Returns:
        Generated mnemonic phrase

    Raises:
        ValidationError: If word_count is invalid

    Example:
        >>> mnemonic = generate_mnemonic(word_count=24)
        >>> words = mnemonic.split()
        >>> len(words)
        24
    """
    logger.debug("Generating mnemonic", word_count=word_count)

    if word_count not in VALID_WORD_COUNTS:
        logger.error(
            "Invalid word count for mnemonic",
            word_count=word_count,
            valid_counts=VALID_WORD_COUNTS,
        )
        raise ValidationError(
            f"Invalid word count: {word_count}",
            details={"word_count": word_count, "valid_counts": VALID_WORD_COUNTS},
            suggestions=[f"Use one of: {', '.join(map(str, VALID_WORD_COUNTS))}"],
        )

    # Calculate strength in bits
    # 12 words = 128 bits, 24 words = 256 bits
    strength = (word_count * 11) - (word_count // 3)

    mnemo = Mnemonic("english")
    mnemonic = mnemo.generate(strength=strength)

    logger.info("Mnemonic generated successfully", word_count=word_count)

    if get_settings().debug:
        logger.debug("Mnemonic generation complete", mnemonic_length=len(mnemonic))

    return mnemonic


def is_valid_mnemonic(mnemonic: str) -> bool:
    """Check if mnemonic is valid according to BIP39.

    Args:
        mnemonic: Mnemonic phrase to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> mnemonic = generate_mnemonic()
        >>> is_valid_mnemonic(mnemonic)
        True
        >>> is_valid_mnemonic("invalid mnemonic phrase")
        False
    """
    if not isinstance(mnemonic, str):
        return False

    if not mnemonic or mnemonic.isspace():
        return False

    # Normalize whitespace
    normalized = " ".join(mnemonic.split())

    # Check word count
    words = normalized.split()
    if len(words) not in VALID_WORD_COUNTS:
        return False

    # Validate using mnemonic library
    mnemo = Mnemonic("english")
    return mnemo.check(normalized)


def validate_mnemonic(mnemonic: str) -> None:
    """Validate mnemonic phrase, raising error if invalid.

    Args:
        mnemonic: Mnemonic phrase to validate

    Raises:
        ValidationError: If mnemonic is invalid

    Example:
        >>> validate_mnemonic("valid mnemonic phrase...")  # OK
        >>> validate_mnemonic("invalid")  # Raises ValidationError
    """
    if not is_valid_mnemonic(mnemonic):
        logger.error("Mnemonic validation failed")
        raise ValidationError(
            "Invalid mnemonic phrase",
            details={"mnemonic_length": len(mnemonic.split()) if mnemonic else 0},
            suggestions=[
                "Ensure mnemonic has correct number of words (12, 15, 18, 21, or 24)",
                "Check that all words are from the BIP39 wordlist",
                "Verify mnemonic checksum",
            ],
        )

    logger.debug("Mnemonic validation passed")


def derive_key_at_path(mnemonic: str, hd_path: str) -> bytes:
    """Derive private key at specific HD path.

    Args:
        mnemonic: BIP39 mnemonic phrase
        hd_path: BIP44 derivation path (e.g., "m/44'/529'/0'/0/0")

    Returns:
        32-byte private key

    Raises:
        ValidationError: If mnemonic or path is invalid
        WalletError: If key derivation fails

    Example:
        >>> mnemonic = generate_mnemonic()
        >>> key = derive_key_at_path(mnemonic, "m/44'/529'/0'/0/0")
        >>> len(key)
        32
    """
    logger.debug("Deriving key at path", hd_path=hd_path)

    # Validate inputs
    validate_mnemonic(mnemonic)
    validate_hd_path(hd_path)

    try:
        # Use secret-sdk's MnemonicKey for derivation
        mk = MnemonicKey(mnemonic=mnemonic, coin_type=SECRET_COIN_TYPE)

        # Get private key bytes
        private_key = mk.private_key

        logger.info("Key derived successfully", hd_path=hd_path)

        return private_key

    except Exception as e:
        logger.error("Key derivation failed", error=str(e), hd_path=hd_path)
        raise WalletError(
            f"Failed to derive key at path {hd_path}",
            details={"hd_path": hd_path, "error": str(e)},
            suggestions=["Verify mnemonic is valid", "Check HD path format"],
        )


def derive_address_from_pubkey(pubkey: bytes) -> str:
    """Derive Secret Network address from public key.

    Args:
        pubkey: 33-byte compressed secp256k1 public key

    Returns:
        Bech32-encoded Secret Network address (secret1...)

    Example:
        >>> pubkey = wallet.get_pubkey()
        >>> address = derive_address_from_pubkey(pubkey)
        >>> address.startswith('secret1')
        True
    """
    logger.debug("Deriving address from public key", pubkey_length=len(pubkey))

    try:
        # Hash public key (SHA256 then RIPEMD160)
        sha256_hash = hashlib.sha256(pubkey).digest()
        ripemd160_hash = hashlib.new("ripemd160", sha256_hash).digest()

        # Encode as bech32
        import bech32

        converted = bech32.convertbits(ripemd160_hash, 8, 5)
        if converted is None:
            raise WalletError("Failed to convert address bits")

        address = bech32.bech32_encode("secret", converted)

        logger.info("Address derived from public key", address=address[:15] + "...")

        return address

    except Exception as e:
        logger.error("Address derivation failed", error=str(e))
        raise WalletError(
            "Failed to derive address from public key",
            details={"error": str(e)},
            suggestions=["Verify public key is valid", "Check public key format"],
        )


def sign_transaction(mnemonic: str, tx_data: bytes, hd_path: str = "m/44'/529'/0'/0/0") -> bytes:
    """Sign transaction data with private key derived from mnemonic.

    Args:
        mnemonic: BIP39 mnemonic phrase
        tx_data: Transaction data to sign
        hd_path: Optional HD path (default: m/44'/529'/0'/0/0)

    Returns:
        Transaction signature bytes

    Raises:
        ValidationError: If mnemonic or path is invalid
        WalletError: If signing fails

    Example:
        >>> mnemonic = generate_mnemonic()
        >>> tx_data = b"transaction data"
        >>> signature = sign_transaction(mnemonic, tx_data)
        >>> len(signature) > 0
        True
    """
    logger.debug("Signing transaction", data_length=len(tx_data), hd_path=hd_path)

    # Validate mnemonic
    validate_mnemonic(mnemonic)

    try:
        # Create wallet and sign
        mk = MnemonicKey(mnemonic=mnemonic, coin_type=SECRET_COIN_TYPE)

        # Sign using secret-sdk's signing
        signature = mk.sign(tx_data)

        logger.info("Transaction signed successfully", signature_length=len(signature))

        return signature

    except Exception as e:
        logger.error("Transaction signing failed", error=str(e))
        raise WalletError(
            "Failed to sign transaction",
            details={"error": str(e), "hd_path": hd_path},
            suggestions=["Verify mnemonic is valid", "Check transaction data"],
        )


class HDWallet:
    """HD Wallet for Secret Network.

    Provides hierarchical deterministic wallet functionality following BIP44
    standard with Secret Network's coin type (529).

    HD Path format: m/44'/529'/account'/0/index

    Example:
        >>> mnemonic = generate_mnemonic()
        >>> wallet = HDWallet.from_mnemonic(mnemonic)
        >>> address = wallet.get_address()
        >>> print(address)
        secret1...

        >>> # Multi-account support
        >>> wallet_account_1 = HDWallet.from_mnemonic(mnemonic, account_index=1)
        >>> address_1 = wallet_account_1.get_address()
    """

    def __init__(
        self,
        mnemonic: str,
        account_index: int = 0,
        address_index: int = 0,
    ):
        """Initialize HD wallet.

        Args:
            mnemonic: BIP39 mnemonic phrase
            account_index: BIP44 account index (default: 0)
            address_index: BIP44 address index (default: 0)

        Raises:
            ValidationError: If mnemonic or indices are invalid
        """
        logger.debug(
            "Initializing HD wallet",
            account_index=account_index,
            address_index=address_index,
        )

        # Validate mnemonic
        validate_mnemonic(mnemonic)

        # Validate indices
        if account_index < 0:
            raise ValidationError(
                "Account index must be non-negative",
                details={"account_index": account_index},
                suggestions=["Provide account index >= 0"],
            )

        if address_index < 0:
            raise ValidationError(
                "Address index must be non-negative",
                details={"address_index": address_index},
                suggestions=["Provide address index >= 0"],
            )

        self.mnemonic = mnemonic
        self.account_index = account_index
        self.address_index = address_index

        # Create MnemonicKey for this wallet
        # Note: secret-sdk's MnemonicKey uses account=0, index=0 by default
        # We'll derive custom paths when needed
        self._mk = MnemonicKey(
            mnemonic=mnemonic,
            coin_type=SECRET_COIN_TYPE,
            account=account_index,
            index=address_index,
        )

        # Generate wallet ID (hash of mnemonic + indices)
        wallet_data = f"{mnemonic}:{account_index}:{address_index}"
        self._wallet_id = hashlib.sha256(wallet_data.encode()).hexdigest()[:16]

        logger.info(
            "HD wallet initialized",
            wallet_id=self._wallet_id,
            account_index=account_index,
            address_index=address_index,
        )

        if get_settings().debug:
            logger.debug(
                "HD wallet details",
                hd_path=self.get_hd_path(),
                wallet_id=self._wallet_id,
            )

    @classmethod
    def from_mnemonic(
        cls,
        mnemonic: str,
        account_index: int = 0,
        address_index: int = 0,
    ) -> "HDWallet":
        """Create HD wallet from mnemonic phrase.

        Args:
            mnemonic: BIP39 mnemonic phrase
            account_index: BIP44 account index (default: 0)
            address_index: BIP44 address index (default: 0)

        Returns:
            HDWallet instance

        Example:
            >>> mnemonic = generate_mnemonic()
            >>> wallet = HDWallet.from_mnemonic(mnemonic)
            >>> wallet.get_address()
            'secret1...'
        """
        return cls(mnemonic, account_index=account_index, address_index=address_index)

    def get_hd_path(self) -> str:
        """Get BIP44 derivation path for this wallet.

        Returns:
            HD path string (e.g., "m/44'/529'/0'/0/0")

        Example:
            >>> wallet = HDWallet.from_mnemonic(mnemonic, account_index=2, address_index=5)
            >>> wallet.get_hd_path()
            "m/44'/529'/2'/0/5"
        """
        return f"m/44'/529'/{self.account_index}'/0/{self.address_index}"

    def get_address(self) -> str:
        """Get Secret Network address for this wallet.

        Returns:
            Bech32-encoded address (secret1...)

        Example:
            >>> wallet = HDWallet.from_mnemonic(mnemonic)
            >>> wallet.get_address()
            'secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03'
        """
        logger.debug("Getting wallet address", wallet_id=self._wallet_id)

        address = self._mk.acc_address

        if get_settings().debug:
            logger.debug("Wallet address retrieved", address=address[:15] + "...")

        return address

    def get_pubkey(self) -> bytes:
        """Get compressed public key for this wallet.

        Returns:
            33-byte compressed secp256k1 public key

        Example:
            >>> wallet = HDWallet.from_mnemonic(mnemonic)
            >>> pubkey = wallet.get_pubkey()
            >>> len(pubkey)
            33
        """
        logger.debug("Getting public key", wallet_id=self._wallet_id)

        # secret-sdk returns SimplePublicKey object, extract raw bytes
        pubkey_obj = self._mk.public_key
        pubkey = pubkey_obj.key  # Get the raw bytes from SimplePublicKey

        return pubkey

    def get_private_key(self) -> bytes:
        """Get private key for this wallet.

        WARNING: Keep private keys secure and never expose them.

        Returns:
            32-byte secp256k1 private key

        Example:
            >>> wallet = HDWallet.from_mnemonic(mnemonic)
            >>> privkey = wallet.get_private_key()
            >>> len(privkey)
            32
        """
        logger.debug("Getting private key", wallet_id=self._wallet_id)

        privkey = self._mk.private_key

        if get_settings().debug:
            logger.debug("Private key retrieved", key_length=len(privkey))

        return privkey

    def sign(self, data: bytes) -> bytes:
        """Sign data with this wallet's private key.

        Args:
            data: Data to sign

        Returns:
            Signature bytes

        Example:
            >>> wallet = HDWallet.from_mnemonic(mnemonic)
            >>> data = b"transaction data"
            >>> signature = wallet.sign(data)
            >>> len(signature) > 0
            True
        """
        logger.debug(
            "Signing data",
            wallet_id=self._wallet_id,
            data_length=len(data),
        )

        try:
            signature = self._mk.sign(data)

            logger.info(
                "Data signed successfully",
                wallet_id=self._wallet_id,
                signature_length=len(signature),
            )

            return signature

        except Exception as e:
            logger.error(
                "Signing failed",
                wallet_id=self._wallet_id,
                error=str(e),
            )
            raise WalletError(
                "Failed to sign data",
                details={"error": str(e)},
                suggestions=["Verify data is valid bytes"],
            )

    def derive_address_at(self, account: int, index: int) -> str:
        """Derive address at specific account and index.

        Args:
            account: Account index
            index: Address index

        Returns:
            Secret Network address

        Example:
            >>> wallet = HDWallet.from_mnemonic(mnemonic)
            >>> address = wallet.derive_address_at(account=1, index=5)
            >>> address.startswith('secret1')
            True
        """
        logger.debug(
            "Deriving address at indices",
            account=account,
            index=index,
        )

        # Create temporary wallet with different indices
        temp_wallet = HDWallet.from_mnemonic(
            self.mnemonic,
            account_index=account,
            address_index=index,
        )

        return temp_wallet.get_address()

    def export_mnemonic(self) -> str:
        """Export mnemonic phrase.

        WARNING: Keep mnemonic phrase secure and never share it.

        Returns:
            BIP39 mnemonic phrase

        Example:
            >>> wallet = HDWallet.from_mnemonic(mnemonic)
            >>> exported = wallet.export_mnemonic()
            >>> exported == mnemonic
            True
        """
        logger.warning(
            "Mnemonic exported",
            wallet_id=self._wallet_id,
        )

        return self.mnemonic

    def get_wallet_info(self) -> WalletInfo:
        """Get WalletInfo object for this wallet.

        Returns:
            WalletInfo with address, wallet_id, account, and index

        Example:
            >>> wallet = HDWallet.from_mnemonic(mnemonic)
            >>> info = wallet.get_wallet_info()
            >>> info.address
            'secret1...'
        """
        logger.debug("Getting wallet info", wallet_id=self._wallet_id)

        info = WalletInfo(
            address=self.get_address(),
            wallet_id=self._wallet_id,
            account=self.account_index,
            index=self.address_index,
        )

        return info
