"""Unit tests for session management."""

import time
from datetime import datetime
from typing import Any

import pytest

from mcp_scrt.core.session import Session, SessionInfo
from mcp_scrt.types import NetworkType, WalletInfo


class TestSessionCreation:
    """Test session creation and initialization."""

    def test_create_session(self) -> None:
        """Test creating a session."""
        session = Session(network=NetworkType.TESTNET)
        assert session is not None
        assert session.network == NetworkType.TESTNET

    def test_create_session_with_mainnet(self) -> None:
        """Test creating a session with mainnet."""
        session = Session(network=NetworkType.MAINNET)
        assert session.network == NetworkType.MAINNET

    def test_initial_state(self) -> None:
        """Test initial session state."""
        session = Session(network=NetworkType.TESTNET)

        assert session.is_active() is False
        assert session.has_wallet() is False
        assert session.get_wallet() is None


class TestSessionLifecycle:
    """Test session lifecycle management."""

    def test_start_session(self) -> None:
        """Test starting a session."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        assert session.is_active() is True

    def test_stop_session(self) -> None:
        """Test stopping a session."""
        session = Session(network=NetworkType.TESTNET)
        session.start()
        session.stop()

        assert session.is_active() is False

    def test_stop_inactive_session(self) -> None:
        """Test stopping an already inactive session."""
        session = Session(network=NetworkType.TESTNET)

        # Should not raise error
        session.stop()
        assert session.is_active() is False

    def test_start_already_active_session(self) -> None:
        """Test starting an already active session."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        # Starting again should not raise error, but might log warning
        session.start()
        assert session.is_active() is True

    def test_session_duration(self) -> None:
        """Test session duration tracking."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        time.sleep(0.1)

        duration = session.get_duration()
        assert duration >= 0.1
        assert duration < 1.0  # Should be less than 1 second

    def test_session_duration_not_started(self) -> None:
        """Test duration when session not started."""
        session = Session(network=NetworkType.TESTNET)

        duration = session.get_duration()
        assert duration == 0.0


class TestWalletManagement:
    """Test wallet management in session."""

    def test_load_wallet(self) -> None:
        """Test loading a wallet."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        wallet = WalletInfo(
            wallet_id="test_wallet_1",
            address="secret1test123456789",
        )

        session.load_wallet(wallet)

        assert session.has_wallet() is True
        assert session.get_wallet() == wallet

    def test_load_wallet_inactive_session(self) -> None:
        """Test loading wallet in inactive session."""
        session = Session(network=NetworkType.TESTNET)

        wallet = WalletInfo(
            wallet_id="test_wallet_1",
            address="secret1test123456789",
        )

        # Should raise error
        with pytest.raises(RuntimeError, match="Session is not active"):
            session.load_wallet(wallet)

    def test_unload_wallet(self) -> None:
        """Test unloading a wallet."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        wallet = WalletInfo(
            wallet_id="test_wallet_1",
            address="secret1test123456789",
        )

        session.load_wallet(wallet)
        session.unload_wallet()

        assert session.has_wallet() is False
        assert session.get_wallet() is None

    def test_unload_when_no_wallet(self) -> None:
        """Test unloading when no wallet is loaded."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        # Should not raise error
        session.unload_wallet()

    def test_replace_wallet(self) -> None:
        """Test replacing an existing wallet."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        wallet1 = WalletInfo(
            wallet_id="test_wallet_1",
            address="secret1test111",
        )

        wallet2 = WalletInfo(
            wallet_id="test_wallet_2",
            address="secret1test222",
        )

        session.load_wallet(wallet1)
        session.load_wallet(wallet2)

        assert session.get_wallet() == wallet2

    def test_wallet_cleared_on_stop(self) -> None:
        """Test that wallet is cleared when session stops."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        wallet = WalletInfo(
            wallet_id="test_wallet_1",
            address="secret1test123456789",
        )

        session.load_wallet(wallet)
        session.stop()

        assert session.has_wallet() is False
        assert session.get_wallet() is None


class TestSessionInfo:
    """Test session information."""

    def test_get_session_info(self) -> None:
        """Test getting session information."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        info = session.get_info()

        assert isinstance(info, SessionInfo)
        assert info.is_active is True
        assert info.network == NetworkType.TESTNET
        assert info.has_wallet is False
        assert info.session_id is not None
        assert isinstance(info.start_time, datetime)

    def test_session_info_with_wallet(self) -> None:
        """Test session info with wallet loaded."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        wallet = WalletInfo(
            wallet_id="test_wallet_1",
            address="secret1test123456789",
        )

        session.load_wallet(wallet)
        info = session.get_info()

        assert info.has_wallet is True
        assert info.wallet_address == "secret1test123456789"

    def test_session_info_inactive(self) -> None:
        """Test session info when inactive."""
        session = Session(network=NetworkType.TESTNET)

        info = session.get_info()

        assert info.is_active is False
        assert info.start_time is None
        assert info.duration == 0.0

    def test_session_id_unique(self) -> None:
        """Test that each session has unique ID."""
        session1 = Session(network=NetworkType.TESTNET)
        session2 = Session(network=NetworkType.TESTNET)

        session1.start()
        session2.start()

        info1 = session1.get_info()
        info2 = session2.get_info()

        assert info1.session_id != info2.session_id

    def test_session_id_persists(self) -> None:
        """Test that session ID persists during session."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        info1 = session.get_info()
        time.sleep(0.1)
        info2 = session.get_info()

        assert info1.session_id == info2.session_id

    def test_session_id_changes_on_restart(self) -> None:
        """Test that session ID changes when session is restarted."""
        session = Session(network=NetworkType.TESTNET)

        session.start()
        info1 = session.get_info()

        session.stop()
        session.start()
        info2 = session.get_info()

        assert info1.session_id != info2.session_id


class TestSessionReset:
    """Test session reset functionality."""

    def test_reset_session(self) -> None:
        """Test resetting a session."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        wallet = WalletInfo(
            wallet_id="test_wallet_1",
            address="secret1test123456789",
        )

        session.load_wallet(wallet)
        session.reset()

        assert session.is_active() is False
        assert session.has_wallet() is False

    def test_reset_inactive_session(self) -> None:
        """Test resetting an inactive session."""
        session = Session(network=NetworkType.TESTNET)

        # Should not raise error
        session.reset()

    def test_reset_clears_all_state(self) -> None:
        """Test that reset clears all state."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        wallet = WalletInfo(
            wallet_id="test_wallet_1",
            address="secret1test123456789",
        )

        session.load_wallet(wallet)

        info_before = session.get_info()
        session.reset()

        # Start new session
        session.start()
        info_after = session.get_info()

        # Should have new session ID
        assert info_before.session_id != info_after.session_id


class TestSessionThreadSafety:
    """Test session thread safety."""

    def test_concurrent_wallet_operations(self) -> None:
        """Test concurrent wallet load/unload operations."""
        import threading

        session = Session(network=NetworkType.TESTNET)
        session.start()
        errors: list[Exception] = []

        def load_wallet(thread_id: int) -> None:
            try:
                wallet = WalletInfo(
                    wallet_id=f"test_wallet_{thread_id}",
                    address=f"secret1test{thread_id}",
                )
                session.load_wallet(wallet)
                time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=load_wallet, args=(i,)) for i in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have one wallet loaded
        assert session.has_wallet() is True
        # No errors should occur
        assert len(errors) == 0

    def test_concurrent_start_stop(self) -> None:
        """Test concurrent start/stop operations."""
        import threading

        session = Session(network=NetworkType.TESTNET)
        errors: list[Exception] = []

        def start_stop() -> None:
            try:
                session.start()
                time.sleep(0.01)
                session.stop()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=start_stop) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # No errors should occur
        assert len(errors) == 0


class TestSessionEdgeCases:
    """Test session edge cases."""

    def test_multiple_starts_without_stop(self) -> None:
        """Test multiple starts without stop."""
        session = Session(network=NetworkType.TESTNET)

        session.start()
        time.sleep(0.1)
        session.start()

        # Duration should continue from first start
        duration = session.get_duration()
        assert duration >= 0.1

    def test_get_duration_after_stop(self) -> None:
        """Test getting duration after session stopped."""
        session = Session(network=NetworkType.TESTNET)
        session.start()
        time.sleep(0.1)
        session.stop()

        # Duration should be frozen at stop time
        duration1 = session.get_duration()
        time.sleep(0.1)
        duration2 = session.get_duration()

        # Should not increase after stop
        assert duration1 == duration2

    def test_wallet_address_format(self) -> None:
        """Test wallet address format validation."""
        session = Session(network=NetworkType.TESTNET)
        session.start()

        wallet = WalletInfo(
            wallet_id="test_wallet_1",
            address="secret1testaddress",
        )

        session.load_wallet(wallet)
        info = session.get_info()

        assert info.wallet_address is not None
        assert info.wallet_address.startswith("secret1")
