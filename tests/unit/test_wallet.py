"""Unit tests for HD wallet operations."""

import pytest

from mcp_scrt.sdk.wallet import (
    HDWallet,
    generate_mnemonic,
    is_valid_mnemonic,
    validate_mnemonic,
    derive_address_from_pubkey,
    derive_key_at_path,
    sign_transaction,
)
from mcp_scrt.types import WalletInfo
from mcp_scrt.utils.errors import ValidationError, WalletError


class TestMnemonicGeneration:
    """Test mnemonic generation."""

    def test_generate_mnemonic_default(self) -> None:
        """Test generating mnemonic with default word count (24)."""
        mnemonic = generate_mnemonic()

        words = mnemonic.split()
        assert len(words) == 24
        assert is_valid_mnemonic(mnemonic) is True

    def test_generate_mnemonic_12_words(self) -> None:
        """Test generating 12-word mnemonic."""
        mnemonic = generate_mnemonic(word_count=12)

        words = mnemonic.split()
        assert len(words) == 12
        assert is_valid_mnemonic(mnemonic) is True

    def test_generate_mnemonic_15_words(self) -> None:
        """Test generating 15-word mnemonic."""
        mnemonic = generate_mnemonic(word_count=15)

        words = mnemonic.split()
        assert len(words) == 15
        assert is_valid_mnemonic(mnemonic) is True

    def test_generate_mnemonic_18_words(self) -> None:
        """Test generating 18-word mnemonic."""
        mnemonic = generate_mnemonic(word_count=18)

        words = mnemonic.split()
        assert len(words) == 18
        assert is_valid_mnemonic(mnemonic) is True

    def test_generate_mnemonic_21_words(self) -> None:
        """Test generating 21-word mnemonic."""
        mnemonic = generate_mnemonic(word_count=21)

        words = mnemonic.split()
        assert len(words) == 21
        assert is_valid_mnemonic(mnemonic) is True

    def test_generate_mnemonic_24_words(self) -> None:
        """Test generating 24-word mnemonic."""
        mnemonic = generate_mnemonic(word_count=24)

        words = mnemonic.split()
        assert len(words) == 24
        assert is_valid_mnemonic(mnemonic) is True

    def test_generate_mnemonic_invalid_word_count(self) -> None:
        """Test generating mnemonic with invalid word count."""
        with pytest.raises(ValidationError, match="(?i)word.count|invalid"):
            generate_mnemonic(word_count=10)

    def test_generate_mnemonic_uniqueness(self) -> None:
        """Test that generated mnemonics are unique."""
        mnemonic1 = generate_mnemonic()
        mnemonic2 = generate_mnemonic()

        assert mnemonic1 != mnemonic2


class TestMnemonicValidation:
    """Test mnemonic validation."""

    def test_valid_mnemonic_24_words(self) -> None:
        """Test validating a valid 24-word mnemonic."""
        # Generate a valid mnemonic for testing
        mnemonic = generate_mnemonic(word_count=24)
        assert is_valid_mnemonic(mnemonic) is True

    def test_valid_mnemonic_12_words(self) -> None:
        """Test validating a valid 12-word mnemonic."""
        mnemonic = generate_mnemonic(word_count=12)
        assert is_valid_mnemonic(mnemonic) is True

    def test_invalid_mnemonic_wrong_word_count(self) -> None:
        """Test mnemonic with wrong word count."""
        mnemonic = "word " * 10  # 10 words
        assert is_valid_mnemonic(mnemonic) is False

    def test_invalid_mnemonic_invalid_words(self) -> None:
        """Test mnemonic with invalid words."""
        mnemonic = "invalid notaword fakemnemonic " * 8  # 24 invalid words
        assert is_valid_mnemonic(mnemonic) is False

    def test_invalid_mnemonic_empty(self) -> None:
        """Test empty mnemonic."""
        assert is_valid_mnemonic("") is False

    def test_invalid_mnemonic_whitespace_only(self) -> None:
        """Test mnemonic with only whitespace."""
        assert is_valid_mnemonic("   ") is False

    def test_validate_mnemonic_success(self) -> None:
        """Test validate_mnemonic with valid mnemonic."""
        mnemonic = generate_mnemonic()
        # Should not raise
        validate_mnemonic(mnemonic)

    def test_validate_mnemonic_failure(self) -> None:
        """Test validate_mnemonic with invalid mnemonic."""
        with pytest.raises(ValidationError, match="(?i)invalid.mnemonic"):
            validate_mnemonic("invalid mnemonic phrase")

    def test_mnemonic_case_sensitive(self) -> None:
        """Test that mnemonic validation is case sensitive (BIP39 standard)."""
        mnemonic_lower = generate_mnemonic()
        mnemonic_upper = mnemonic_lower.upper()

        # BIP39 mnemonics are case-sensitive
        assert is_valid_mnemonic(mnemonic_lower) is True
        # Uppercase should be invalid (not in BIP39 wordlist)
        assert is_valid_mnemonic(mnemonic_upper) is False

    def test_mnemonic_extra_whitespace(self) -> None:
        """Test mnemonic with extra whitespace."""
        mnemonic = generate_mnemonic()
        mnemonic_spaces = "  ".join(mnemonic.split())  # Double spaces

        # Should handle extra whitespace gracefully
        assert is_valid_mnemonic(mnemonic_spaces) is True


class TestHDWalletCreation:
    """Test HD wallet creation."""

    def test_create_wallet_from_mnemonic(self) -> None:
        """Test creating wallet from mnemonic."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        assert wallet.mnemonic == mnemonic
        assert wallet.account_index == 0
        assert wallet.address_index == 0

    def test_create_wallet_with_account_index(self) -> None:
        """Test creating wallet with specific account index."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic, account_index=5)

        assert wallet.account_index == 5

    def test_create_wallet_with_address_index(self) -> None:
        """Test creating wallet with specific address index."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic, address_index=3)

        assert wallet.address_index == 3

    def test_create_wallet_invalid_mnemonic(self) -> None:
        """Test creating wallet with invalid mnemonic."""
        with pytest.raises(ValidationError, match="(?i)invalid.mnemonic"):
            HDWallet.from_mnemonic("invalid mnemonic phrase")

    def test_create_wallet_negative_account_index(self) -> None:
        """Test creating wallet with negative account index."""
        mnemonic = generate_mnemonic()
        with pytest.raises(ValidationError, match="(?i)account.index|negative"):
            HDWallet.from_mnemonic(mnemonic, account_index=-1)

    def test_create_wallet_negative_address_index(self) -> None:
        """Test creating wallet with negative address index."""
        mnemonic = generate_mnemonic()
        with pytest.raises(ValidationError, match="(?i)address.index|negative"):
            HDWallet.from_mnemonic(mnemonic, address_index=-1)


class TestAddressDerivation:
    """Test address derivation from HD wallet."""

    def test_derive_address(self) -> None:
        """Test deriving Secret Network address."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        address = wallet.get_address()

        assert address.startswith("secret1")
        assert len(address) >= 39  # secret1 + at least 38 chars
        assert len(address) <= 46  # secret1 + at most 45 chars

    def test_derive_address_consistency(self) -> None:
        """Test that same mnemonic produces same address."""
        mnemonic = generate_mnemonic()

        wallet1 = HDWallet.from_mnemonic(mnemonic)
        wallet2 = HDWallet.from_mnemonic(mnemonic)

        assert wallet1.get_address() == wallet2.get_address()

    def test_derive_address_different_accounts(self) -> None:
        """Test that different accounts produce different addresses."""
        mnemonic = generate_mnemonic()

        wallet1 = HDWallet.from_mnemonic(mnemonic, account_index=0)
        wallet2 = HDWallet.from_mnemonic(mnemonic, account_index=1)

        assert wallet1.get_address() != wallet2.get_address()

    def test_derive_address_different_indices(self) -> None:
        """Test that different address indices produce different addresses."""
        mnemonic = generate_mnemonic()

        wallet1 = HDWallet.from_mnemonic(mnemonic, address_index=0)
        wallet2 = HDWallet.from_mnemonic(mnemonic, address_index=1)

        assert wallet1.get_address() != wallet2.get_address()

    def test_derive_address_at_path(self) -> None:
        """Test deriving address at specific HD path."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        # Derive at account 2, index 5
        address = wallet.derive_address_at(account=2, index=5)

        assert address.startswith("secret1")
        assert isinstance(address, str)

    def test_derive_pubkey_from_address(self) -> None:
        """Test deriving public key and converting to address."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        pubkey = wallet.get_pubkey()
        address_from_pubkey = derive_address_from_pubkey(pubkey)

        assert address_from_pubkey == wallet.get_address()


class TestHDPathDerivation:
    """Test HD path derivation."""

    def test_get_hd_path_default(self) -> None:
        """Test getting HD path with default indices."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        path = wallet.get_hd_path()

        assert path == "m/44'/529'/0'/0/0"

    def test_get_hd_path_custom_account(self) -> None:
        """Test getting HD path with custom account."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic, account_index=3)

        path = wallet.get_hd_path()

        assert path == "m/44'/529'/3'/0/0"

    def test_get_hd_path_custom_address_index(self) -> None:
        """Test getting HD path with custom address index."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic, address_index=7)

        path = wallet.get_hd_path()

        assert path == "m/44'/529'/0'/0/7"

    def test_derive_key_at_path_function(self) -> None:
        """Test derive_key_at_path helper function."""
        mnemonic = generate_mnemonic()
        path = "m/44'/529'/0'/0/0"

        private_key = derive_key_at_path(mnemonic, path)

        assert isinstance(private_key, bytes)
        assert len(private_key) == 32  # 32 bytes for secp256k1


class TestWalletInfo:
    """Test WalletInfo generation."""

    def test_get_wallet_info(self) -> None:
        """Test getting WalletInfo from wallet."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic, account_index=2, address_index=5)

        info = wallet.get_wallet_info()

        assert isinstance(info, WalletInfo)
        assert info.address == wallet.get_address()
        assert info.wallet_id is not None
        assert info.account == 2
        assert info.index == 5

    def test_wallet_info_unique_id(self) -> None:
        """Test that wallet_id is unique per wallet."""
        mnemonic1 = generate_mnemonic()
        mnemonic2 = generate_mnemonic()

        wallet1 = HDWallet.from_mnemonic(mnemonic1)
        wallet2 = HDWallet.from_mnemonic(mnemonic2)

        info1 = wallet1.get_wallet_info()
        info2 = wallet2.get_wallet_info()

        assert info1.wallet_id != info2.wallet_id

    def test_wallet_info_consistency(self) -> None:
        """Test that wallet_id is consistent for same wallet."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        info1 = wallet.get_wallet_info()
        info2 = wallet.get_wallet_info()

        assert info1.wallet_id == info2.wallet_id


class TestTransactionSigning:
    """Test transaction signing."""

    def test_sign_transaction(self) -> None:
        """Test signing a transaction."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        tx_data = b"test transaction data"
        signature = wallet.sign(tx_data)

        assert isinstance(signature, bytes)
        assert len(signature) > 0

    def test_sign_transaction_consistency(self) -> None:
        """Test that signing same data produces same signature."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        tx_data = b"test transaction data"
        signature1 = wallet.sign(tx_data)
        signature2 = wallet.sign(tx_data)

        assert signature1 == signature2

    def test_sign_transaction_different_data(self) -> None:
        """Test that different data produces different signatures."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        tx_data1 = b"test transaction data 1"
        tx_data2 = b"test transaction data 2"

        signature1 = wallet.sign(tx_data1)
        signature2 = wallet.sign(tx_data2)

        assert signature1 != signature2

    def test_sign_transaction_different_wallets(self) -> None:
        """Test that different wallets produce different signatures."""
        mnemonic1 = generate_mnemonic()
        mnemonic2 = generate_mnemonic()

        wallet1 = HDWallet.from_mnemonic(mnemonic1)
        wallet2 = HDWallet.from_mnemonic(mnemonic2)

        tx_data = b"test transaction data"
        signature1 = wallet1.sign(tx_data)
        signature2 = wallet2.sign(tx_data)

        assert signature1 != signature2

    def test_sign_empty_data(self) -> None:
        """Test signing empty data."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        signature = wallet.sign(b"")
        assert isinstance(signature, bytes)

    def test_sign_transaction_helper_function(self) -> None:
        """Test sign_transaction helper function."""
        mnemonic = generate_mnemonic()
        tx_data = b"test transaction data"

        signature = sign_transaction(mnemonic, tx_data)

        assert isinstance(signature, bytes)
        assert len(signature) > 0


class TestPublicKeyOperations:
    """Test public key operations."""

    def test_get_pubkey(self) -> None:
        """Test getting public key."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        pubkey = wallet.get_pubkey()

        assert isinstance(pubkey, bytes)
        assert len(pubkey) == 33  # Compressed secp256k1 pubkey

    def test_get_pubkey_consistency(self) -> None:
        """Test that public key is consistent."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        pubkey1 = wallet.get_pubkey()
        pubkey2 = wallet.get_pubkey()

        assert pubkey1 == pubkey2

    def test_get_pubkey_different_accounts(self) -> None:
        """Test different accounts have different public keys."""
        mnemonic = generate_mnemonic()

        wallet1 = HDWallet.from_mnemonic(mnemonic, account_index=0)
        wallet2 = HDWallet.from_mnemonic(mnemonic, account_index=1)

        assert wallet1.get_pubkey() != wallet2.get_pubkey()


class TestPrivateKeyOperations:
    """Test private key operations."""

    def test_get_private_key(self) -> None:
        """Test getting private key."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        privkey = wallet.get_private_key()

        assert isinstance(privkey, bytes)
        assert len(privkey) == 32  # secp256k1 private key

    def test_private_key_consistency(self) -> None:
        """Test that private key is consistent."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        privkey1 = wallet.get_private_key()
        privkey2 = wallet.get_private_key()

        assert privkey1 == privkey2

    def test_private_key_different_mnemonics(self) -> None:
        """Test different mnemonics produce different private keys."""
        mnemonic1 = generate_mnemonic()
        mnemonic2 = generate_mnemonic()

        wallet1 = HDWallet.from_mnemonic(mnemonic1)
        wallet2 = HDWallet.from_mnemonic(mnemonic2)

        assert wallet1.get_private_key() != wallet2.get_private_key()


class TestMultiAccountSupport:
    """Test multi-account support."""

    def test_derive_multiple_accounts(self) -> None:
        """Test deriving multiple accounts."""
        mnemonic = generate_mnemonic()
        addresses = []

        for account in range(5):
            wallet = HDWallet.from_mnemonic(mnemonic, account_index=account)
            addresses.append(wallet.get_address())

        # All addresses should be unique
        assert len(addresses) == len(set(addresses))

    def test_derive_multiple_address_indices(self) -> None:
        """Test deriving multiple address indices."""
        mnemonic = generate_mnemonic()
        addresses = []

        for index in range(5):
            wallet = HDWallet.from_mnemonic(mnemonic, address_index=index)
            addresses.append(wallet.get_address())

        # All addresses should be unique
        assert len(addresses) == len(set(addresses))

    def test_account_independence(self) -> None:
        """Test that accounts are independent."""
        mnemonic = generate_mnemonic()

        wallet0 = HDWallet.from_mnemonic(mnemonic, account_index=0)
        wallet1 = HDWallet.from_mnemonic(mnemonic, account_index=1)

        # Different addresses
        assert wallet0.get_address() != wallet1.get_address()

        # Different public keys
        assert wallet0.get_pubkey() != wallet1.get_pubkey()

        # Different private keys
        assert wallet0.get_private_key() != wallet1.get_private_key()


class TestWalletSerialization:
    """Test wallet serialization."""

    def test_export_mnemonic(self) -> None:
        """Test exporting mnemonic."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        exported = wallet.export_mnemonic()

        assert exported == mnemonic

    def test_restore_from_mnemonic(self) -> None:
        """Test restoring wallet from mnemonic."""
        mnemonic = generate_mnemonic()

        wallet1 = HDWallet.from_mnemonic(mnemonic, account_index=3, address_index=5)
        address1 = wallet1.get_address()

        # Export and restore
        exported_mnemonic = wallet1.export_mnemonic()
        wallet2 = HDWallet.from_mnemonic(exported_mnemonic, account_index=3, address_index=5)
        address2 = wallet2.get_address()

        assert address1 == address2


class TestWalletEdgeCases:
    """Test edge cases and error handling."""

    def test_very_long_mnemonic(self) -> None:
        """Test handling of very long mnemonic (24 words)."""
        mnemonic = generate_mnemonic(word_count=24)
        wallet = HDWallet.from_mnemonic(mnemonic)

        assert wallet.get_address().startswith("secret1")

    def test_maximum_account_index(self) -> None:
        """Test with very large account index."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic, account_index=999)

        assert wallet.account_index == 999
        assert wallet.get_hd_path() == "m/44'/529'/999'/0/0"

    def test_maximum_address_index(self) -> None:
        """Test with very large address index."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic, address_index=999)

        assert wallet.address_index == 999
        assert wallet.get_hd_path() == "m/44'/529'/0'/0/999"

    def test_sign_large_data(self) -> None:
        """Test signing large transaction data."""
        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        large_data = b"x" * 100000  # 100KB
        signature = wallet.sign(large_data)

        assert isinstance(signature, bytes)

    def test_mnemonic_with_unicode(self) -> None:
        """Test that unicode in mnemonic fails validation."""
        invalid_mnemonic = "test 测试 invalid mnemonic phrase words"
        assert is_valid_mnemonic(invalid_mnemonic) is False


class TestWalletThreadSafety:
    """Test thread safety of wallet operations."""

    def test_concurrent_address_derivation(self) -> None:
        """Test concurrent address derivation from same mnemonic."""
        from concurrent.futures import ThreadPoolExecutor

        mnemonic = generate_mnemonic()
        addresses = []

        def derive_address(index: int) -> str:
            wallet = HDWallet.from_mnemonic(mnemonic, address_index=index)
            return wallet.get_address()

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(derive_address, range(10)))

        # All addresses should be unique
        assert len(results) == 10
        assert len(set(results)) == 10

    def test_concurrent_signing(self) -> None:
        """Test concurrent transaction signing."""
        from concurrent.futures import ThreadPoolExecutor

        mnemonic = generate_mnemonic()
        wallet = HDWallet.from_mnemonic(mnemonic)

        def sign_data(data_index: int) -> bytes:
            data = f"test data {data_index}".encode()
            return wallet.sign(data)

        with ThreadPoolExecutor(max_workers=5) as executor:
            signatures = list(executor.map(sign_data, range(10)))

        # All signatures should be present
        assert len(signatures) == 10
        # All signatures should be different (different data)
        assert len(set(signatures)) == 10
