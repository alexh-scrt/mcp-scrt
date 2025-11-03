"""Session management for Secret MCP Server.

This module manages the session state including active wallet,
network configuration, and session lifecycle with detailed debug logging.
"""

import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..config import get_settings
from ..types import NetworkType, WalletInfo
from ..utils.logging import get_logger

# Module logger
logger = get_logger(__name__)


@dataclass
class SessionInfo:
    """Session information snapshot.

    Attributes:
        session_id: Unique session identifier
        is_active: Whether session is currently active
        network: Network type (testnet, mainnet, custom)
        has_wallet: Whether a wallet is loaded
        wallet_address: Address of loaded wallet (if any)
        start_time: Session start timestamp (if active)
        duration: Session duration in seconds
    """

    session_id: Optional[str]
    is_active: bool
    network: NetworkType
    has_wallet: bool
    wallet_address: Optional[str] = None
    start_time: Optional[datetime] = None
    duration: float = 0.0


class Session:
    """Thread-safe session management with detailed logging.

    This class manages the MCP server session state including:
    - Session lifecycle (start, stop, reset)
    - Wallet loading and unloading
    - Session metadata and timing
    - Thread-safe operations

    The logging behavior depends on configuration:
    - LOG_LEVEL=DEBUG: Shows detailed operation logs
    - DEBUG=true: Shows extra verbose internal state logs
    """

    def __init__(self, network: NetworkType = NetworkType.TESTNET) -> None:
        """Initialize session.

        Args:
            network: Network to connect to (default: TESTNET)
        """
        self.network = network
        self._active = False
        self._wallet: Optional[WalletInfo] = None
        self._session_id: Optional[str] = None
        self._start_time: Optional[float] = None
        self._stop_time: Optional[float] = None
        self._lock = threading.RLock()

        # Get settings for logging
        settings = get_settings()
        self._debug_enabled = settings.debug and settings.log_level.upper() == "DEBUG"

        logger.debug(
            "Session initialized",
            network=network.value,
            debug_enabled=self._debug_enabled,
        )

        if self._debug_enabled:
            logger.debug(
                "Session initial state",
                active=self._active,
                wallet_loaded=self._wallet is not None,
                session_id=self._session_id,
            )

    def start(self) -> None:
        """Start the session.

        Creates a new session ID and marks session as active.
        If already active, logs a warning but continues.
        """
        with self._lock:
            logger.debug("Starting session", network=self.network.value)

            if self._active:
                logger.warning(
                    "Session already active, continuing with existing session",
                    session_id=self._session_id,
                )
                return

            # Generate new session ID
            self._session_id = str(uuid.uuid4())
            self._start_time = time.time()
            self._stop_time = None
            self._active = True

            logger.info(
                "Session started",
                session_id=self._session_id,
                network=self.network.value,
            )

            if self._debug_enabled:
                logger.debug(
                    "Session start details",
                    session_id=self._session_id,
                    start_time=self._start_time,
                    timestamp=datetime.fromtimestamp(self._start_time).isoformat(),
                )

    def stop(self) -> None:
        """Stop the session.

        Clears wallet and marks session as inactive.
        Safe to call on inactive session.
        """
        with self._lock:
            logger.debug("Stopping session", session_id=self._session_id)

            if not self._active:
                logger.debug("Session already inactive, nothing to stop")
                return

            # Record stop time before clearing state
            self._stop_time = time.time()
            duration = self._stop_time - (self._start_time or 0)

            # Clear wallet
            if self._wallet:
                logger.debug("Unloading wallet on session stop", address=self._wallet.address)
                self._wallet = None

            self._active = False

            logger.info(
                "Session stopped",
                session_id=self._session_id,
                duration=f"{duration:.2f}s",
            )

            if self._debug_enabled:
                logger.debug(
                    "Session stop details",
                    session_id=self._session_id,
                    start_time=self._start_time,
                    stop_time=self._stop_time,
                    duration_seconds=duration,
                )

    def reset(self) -> None:
        """Reset the session.

        Stops the session and clears all state including timing information.
        """
        with self._lock:
            logger.debug("Resetting session", session_id=self._session_id)

            if self._active:
                self.stop()

            # Clear all timing state
            self._session_id = None
            self._start_time = None
            self._stop_time = None

            logger.info("Session reset complete")

            if self._debug_enabled:
                logger.debug("Session state after reset", session_id=None, active=False)

    def load_wallet(self, wallet: WalletInfo) -> None:
        """Load a wallet into the session.

        Args:
            wallet: Wallet information to load

        Raises:
            RuntimeError: If session is not active
        """
        with self._lock:
            logger.debug("Loading wallet", address=wallet.address)

            if not self._active:
                logger.error(
                    "Cannot load wallet: session not active",
                    address=wallet.address,
                )
                raise RuntimeError("Session is not active")

            # Warn if replacing existing wallet
            if self._wallet:
                logger.warning(
                    "Replacing existing wallet",
                    old_address=self._wallet.address,
                    new_address=wallet.address,
                )

            self._wallet = wallet

            logger.info("Wallet loaded", address=wallet.address)

            if self._debug_enabled:
                logger.debug(
                    "Wallet load details",
                    wallet_id=wallet.wallet_id,
                    address=wallet.address,
                    account=wallet.account,
                    index=wallet.index,
                    session_id=self._session_id,
                )

    def unload_wallet(self) -> None:
        """Unload the current wallet from the session.

        Safe to call when no wallet is loaded.
        """
        with self._lock:
            logger.debug("Unloading wallet")

            if not self._wallet:
                logger.debug("No wallet loaded, nothing to unload")
                return

            address = self._wallet.address
            self._wallet = None

            logger.info("Wallet unloaded", address=address)

            if self._debug_enabled:
                logger.debug(
                    "Wallet unload details",
                    previous_address=address,
                    session_id=self._session_id,
                )

    def is_active(self) -> bool:
        """Check if session is active.

        Returns:
            True if session is active, False otherwise
        """
        with self._lock:
            active = self._active

            if self._debug_enabled:
                logger.debug("Session active check", active=active, session_id=self._session_id)

            return active

    def has_wallet(self) -> bool:
        """Check if a wallet is loaded.

        Returns:
            True if wallet is loaded, False otherwise
        """
        with self._lock:
            has_wallet = self._wallet is not None

            if self._debug_enabled:
                logger.debug(
                    "Wallet loaded check",
                    has_wallet=has_wallet,
                    address=self._wallet.address if self._wallet else None,
                )

            return has_wallet

    def get_wallet(self) -> Optional[WalletInfo]:
        """Get the currently loaded wallet.

        Returns:
            Loaded wallet or None if no wallet loaded
        """
        with self._lock:
            if self._debug_enabled:
                logger.debug(
                    "Getting wallet",
                    has_wallet=self._wallet is not None,
                    address=self._wallet.address if self._wallet else None,
                )

            return self._wallet

    def get_duration(self) -> float:
        """Get session duration in seconds.

        Returns:
            Duration in seconds, or 0.0 if session not started
        """
        with self._lock:
            if not self._start_time:
                return 0.0

            # If stopped, use stop time; otherwise use current time
            end_time = self._stop_time if self._stop_time else time.time()
            duration = end_time - self._start_time

            if self._debug_enabled:
                logger.debug(
                    "Session duration calculated",
                    duration_seconds=duration,
                    active=self._active,
                    session_id=self._session_id,
                )

            return duration

    def get_info(self) -> SessionInfo:
        """Get session information snapshot.

        Returns:
            SessionInfo with current session state
        """
        with self._lock:
            logger.debug("Getting session info", session_id=self._session_id)

            info = SessionInfo(
                session_id=self._session_id,
                is_active=self._active,
                network=self.network,
                has_wallet=self._wallet is not None,
                wallet_address=self._wallet.address if self._wallet else None,
                start_time=datetime.fromtimestamp(self._start_time) if self._start_time else None,
                duration=self.get_duration(),
            )

            if self._debug_enabled:
                logger.debug(
                    "Session info retrieved",
                    session_id=info.session_id,
                    is_active=info.is_active,
                    has_wallet=info.has_wallet,
                    network=info.network.value,
                    duration=f"{info.duration:.2f}s",
                )

            return info
