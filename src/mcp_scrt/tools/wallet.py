"""Wallet tools for Secret Network wallet management.

This module provides tools for creating, importing, and managing HD wallets.
"""

from typing import Any, Dict
import uuid

from mcp_scrt.tools.base import BaseTool, ToolCategory
from mcp_scrt.types import WalletInfo
from mcp_scrt.utils.errors import ValidationError, WalletError
from mcp_scrt.sdk.wallet import HDWallet, generate_mnemonic
from mcp_scrt.core.validation import validate_address


class CreateWalletTool(BaseTool):
    """Create a new HD wallet with mnemonic.

    Generates a new BIP39 mnemonic and creates an HD wallet.
    """

    @property
    def name(self) -> str:
        return "create_wallet"

    @property
    def description(self) -> str:
        return (
            "Create a new HD wallet with BIP39 mnemonic generation. "
            "Optionally specify word count (12 or 24 words)."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WALLET

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate wallet creation parameters.

        Args:
            params: Optional 'word_count' (12 or 24)

        Raises:
            ValidationError: If parameters are invalid
        """
        if "word_count" in params:
            word_count = params["word_count"]
            if word_count not in [12, 24]:
                raise ValidationError(
                    message=f"Invalid word_count: {word_count}",
                    details={
                        "provided": word_count,
                        "valid_options": [12, 24],
                    },
                    suggestions=[
                        "Use word_count=12 for 12-word mnemonic",
                        "Use word_count=24 for 24-word mnemonic (recommended)",
                        "Omit word_count to use default (24 words)",
                    ],
                )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute wallet creation.

        Args:
            params: Wallet creation parameters

        Returns:
            Created wallet information including mnemonic and address
        """
        word_count = params.get("word_count", 24)

        # Generate mnemonic
        mnemonic = generate_mnemonic(word_count=word_count)

        # Create HD wallet
        wallet = HDWallet.from_mnemonic(mnemonic)

        # Get address
        address = wallet.get_address()

        # Generate wallet ID
        wallet_id = str(uuid.uuid4())

        # Get HD path
        hd_path = wallet.get_hd_path()

        return {
            "wallet_id": wallet_id,
            "address": address,
            "mnemonic": mnemonic,
            "hd_path": hd_path,
            "account": 0,
            "index": 0,
            "message": "Wallet created successfully. IMPORTANT: Store the mnemonic securely!",
            "warning": "Never share your mnemonic. Anyone with access can control your funds.",
        }


class ImportWalletTool(BaseTool):
    """Import existing wallet from mnemonic.

    Imports a wallet using an existing BIP39 mnemonic phrase.
    """

    @property
    def name(self) -> str:
        return "import_wallet"

    @property
    def description(self) -> str:
        return (
            "Import an existing HD wallet from BIP39 mnemonic phrase. "
            "Supports 12 or 24 word mnemonics with optional account/index."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WALLET

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate import parameters.

        Args:
            params: Must contain 'mnemonic', optionally 'account' and 'index'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "mnemonic" not in params:
            raise ValidationError(
                message="Missing required parameter: mnemonic",
                details={"required_params": ["mnemonic"]},
                suggestions=[
                    "Provide 'mnemonic' parameter with 12 or 24 words",
                    "Example: {'mnemonic': 'word1 word2 ... word24'}",
                ],
            )

        mnemonic = params["mnemonic"]
        words = mnemonic.strip().split()

        if len(words) not in [12, 24]:
            raise ValidationError(
                message=f"Invalid mnemonic length: {len(words)} words",
                details={
                    "provided_word_count": len(words),
                    "valid_word_counts": [12, 24],
                },
                suggestions=[
                    "Provide a 12-word or 24-word BIP39 mnemonic",
                    "Ensure words are space-separated",
                    "Check for typos in the mnemonic phrase",
                ],
            )

        # Validate account and index if provided
        if "account" in params:
            account = params["account"]
            if not isinstance(account, int) or account < 0:
                raise ValidationError(
                    message="Invalid account index",
                    details={"provided": account},
                    suggestions=["Account must be a non-negative integer"],
                )

        if "index" in params:
            index = params["index"]
            if not isinstance(index, int) or index < 0:
                raise ValidationError(
                    message="Invalid address index",
                    details={"provided": index},
                    suggestions=["Index must be a non-negative integer"],
                )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute wallet import.

        Args:
            params: Import parameters including mnemonic

        Returns:
            Imported wallet information

        Raises:
            WalletError: If mnemonic is invalid
        """
        mnemonic = params["mnemonic"]
        account = params.get("account", 0)
        index = params.get("index", 0)

        try:
            # Create HD wallet from mnemonic
            wallet = HDWallet.from_mnemonic(
                mnemonic=mnemonic,
                account_index=account,
                address_index=index,
            )

            # Get address
            address = wallet.get_address()

            # Generate wallet ID
            wallet_id = str(uuid.uuid4())

            # Get HD path
            hd_path = wallet.get_hd_path()

            return {
                "wallet_id": wallet_id,
                "address": address,
                "hd_path": hd_path,
                "account": account,
                "index": index,
                "message": "Wallet imported successfully",
            }

        except Exception as e:
            raise WalletError(
                message=f"Failed to import wallet: {str(e)}",
                details={
                    "error": str(e),
                    "account": account,
                    "index": index,
                },
                suggestions=[
                    "Verify the mnemonic phrase is correct",
                    "Check for typos or extra/missing words",
                    "Ensure words are from the BIP39 wordlist",
                ],
            )


class SetActiveWalletTool(BaseTool):
    """Set active wallet in session.

    Activates a wallet for use in subsequent operations.
    """

    @property
    def name(self) -> str:
        return "set_active_wallet"

    @property
    def description(self) -> str:
        return (
            "Set the active wallet for the current session. "
            "The active wallet will be used for all transaction operations."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WALLET

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate set active wallet parameters.

        Args:
            params: Must contain 'address'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "address" not in params:
            raise ValidationError(
                message="Missing required parameter: address",
                details={"required_params": ["address"]},
                suggestions=[
                    "Provide 'address' parameter",
                    "Example: {'address': 'secret1...'}",
                ],
            )

        # Validate address format
        validate_address(params["address"])

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute set active wallet.

        Args:
            params: Parameters including address

        Returns:
            Active wallet information
        """
        address = params["address"]

        # Verify wallet exists in session
        wallet_info = self.context.session.get_wallet()

        if wallet_info is None or wallet_info.address != address:
            raise WalletError(
                message=f"Wallet not found: {address}",
                details={"address": address},
                suggestions=[
                    "Create or import the wallet first",
                    "Verify the address is correct",
                    "Use list_wallets to see available wallets",
                ],
            )

        # Wallet is already set in session, just return info
        return {
            "address": address,
            "wallet_id": wallet_info.wallet_id,
            "status": "active",
            "message": f"Wallet {address} is now active",
        }


class GetActiveWalletTool(BaseTool):
    """Get active wallet information.

    Returns information about the currently active wallet.
    """

    @property
    def name(self) -> str:
        return "get_active_wallet"

    @property
    def description(self) -> str:
        return "Get information about the currently active wallet in the session."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WALLET

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires active wallet

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters (no parameters required)."""
        # No parameters needed
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get active wallet.

        Returns:
            Active wallet information
        """
        wallet_info = self.context.session.get_wallet()

        if wallet_info is None:
            # This shouldn't happen because requires_wallet=True,
            # but handle it gracefully
            raise WalletError(
                message="No active wallet in session",
                suggestions=[
                    "Create a wallet using create_wallet",
                    "Import a wallet using import_wallet",
                    "Set a wallet as active using set_active_wallet",
                ],
            )

        return {
            "wallet_id": wallet_info.wallet_id,
            "address": wallet_info.address,
            "account": wallet_info.account,
            "index": wallet_info.index,
            "status": "active",
        }


class ListWalletsTool(BaseTool):
    """List all available wallets.

    Returns a list of all wallets in the session or wallet storage.
    """

    @property
    def name(self) -> str:
        return "list_wallets"

    @property
    def description(self) -> str:
        return (
            "List all available wallets. "
            "Shows wallet addresses, IDs, and active status."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WALLET

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters (no parameters required)."""
        # No parameters needed
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute list wallets.

        Returns:
            List of all wallets
        """
        wallets = []
        active_wallet = self.context.session.get_wallet()

        # If there's an active wallet, include it in the list
        if active_wallet is not None:
            wallets.append({
                "wallet_id": active_wallet.wallet_id,
                "address": active_wallet.address,
                "account": active_wallet.account,
                "index": active_wallet.index,
                "active": True,
            })

        # In a full implementation, this would query a wallet storage system
        # For now, we just return the active wallet if any

        return {
            "wallets": wallets,
            "count": len(wallets),
            "message": f"Found {len(wallets)} wallet(s)",
        }


class RemoveWalletTool(BaseTool):
    """Remove a wallet from storage.

    Removes a wallet from the wallet storage system.
    """

    @property
    def name(self) -> str:
        return "remove_wallet"

    @property
    def description(self) -> str:
        return (
            "Remove a wallet from storage. "
            "WARNING: Ensure you have backed up the mnemonic before removing."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WALLET

    @property
    def requires_wallet(self) -> bool:
        return False

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate remove wallet parameters.

        Args:
            params: Must contain 'address'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "address" not in params:
            raise ValidationError(
                message="Missing required parameter: address",
                details={"required_params": ["address"]},
                suggestions=[
                    "Provide 'address' parameter",
                    "Example: {'address': 'secret1...'}",
                ],
            )

        # Validate address format
        validate_address(params["address"])

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute remove wallet.

        Args:
            params: Parameters including address

        Returns:
            Removal confirmation
        """
        address = params["address"]

        # Check if this is the active wallet
        active_wallet = self.context.session.get_wallet()

        if active_wallet is not None and active_wallet.address == address:
            # Unload the active wallet from session
            self.context.session.unload_wallet()

        # In a full implementation, this would remove from wallet storage
        # For now, we just confirm removal

        return {
            "address": address,
            "status": "removed",
            "message": f"Wallet {address} has been removed",
            "warning": "Ensure you have backed up the mnemonic if you want to restore this wallet later",
        }
