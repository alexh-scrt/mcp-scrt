"""Integration tests for error handling scenarios.

Tests various error conditions and verifies proper error messages and handling:
1. Insufficient funds
2. Invalid addresses
3. Network errors
4. Contract errors
5. Validation errors
"""

import pytest
from unittest.mock import patch, AsyncMock

from mcp_scrt.tools.wallet import ImportWalletTool
from mcp_scrt.tools.bank import SendTokensTool, GetBalanceTool
from mcp_scrt.tools.staking import DelegateTool
from mcp_scrt.tools.contract import ExecuteContractTool, QueryContractTool
from mcp_scrt.utils.errors import ValidationError, WalletError, NetworkError


class TestErrorScenarios:
    """Integration tests for error handling."""

    @pytest.mark.asyncio
    async def test_insufficient_funds_error(
        self,
        tool_context,
        session,
        test_wallet,
        recipient_address,
        mock_signing_client,
        mock_lcd_client,
    ):
        """Test sending tokens with insufficient balance."""
        # Import wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet.address
            await import_tool.run({
                "name": test_wallet.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Mock low balance
        mock_lcd_client.bank.balance = AsyncMock(
            return_value={
                "balances": [
                    {"denom": "uscrt", "amount": "100"}  # Very low
                ]
            }
        )

        # Mock signing client to raise insufficient funds
        mock_signing_client.send = AsyncMock(
            side_effect=Exception("insufficient funds: 100uscrt is smaller than 1000000uscrt")
        )

        # Try to send more than available
        send_tool = SendTokensTool(tool_context)

        with patch("mcp_scrt.tools.bank.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            result = await send_tool.run({
                "recipient": recipient_address,
                "amount": "1000000",
                "denom": "uscrt",
            })

        assert result["success"] is False
        assert "error" in result
        assert "insufficient" in result["error"]["message"].lower()
        assert "suggestions" in result["error"]

    @pytest.mark.asyncio
    async def test_invalid_address_error(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        mock_signing_client,
    ):
        """Test sending to invalid address."""
        # Import wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Try to send to invalid address
        send_tool = SendTokensTool(tool_context)
        invalid_address = "invalid_address_format"

        result = await send_tool.run({
            "recipient": invalid_address,
            "amount": "1000000",
            "denom": "uscrt",
        })

        assert result["success"] is False
        assert "error" in result
        assert ("invalid" in result["error"]["message"].lower() or
                "address" in result["error"]["message"].lower())

    @pytest.mark.asyncio
    async def test_network_connection_error(
        self,
        tool_context,
        mock_lcd_client,
    ):
        """Test handling of network connection errors."""
        balance_tool = GetBalanceTool(tool_context)

        # Mock network error
        mock_lcd_client.bank.balance = AsyncMock(
            side_effect=Exception("Connection refused: Unable to connect to RPC endpoint")
        )

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            result = await balance_tool.run({
                "address": "secret1addressaddressaddressaddressaddressad"
            })

        assert result["success"] is False
        assert "error" in result
        assert ("connection" in result["error"]["message"].lower() or
                "network" in result["error"]["message"].lower() or
                "failed" in result["error"]["message"].lower())
        assert "suggestions" in result["error"]

    @pytest.mark.asyncio
    async def test_contract_execution_error(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        mock_signing_client,
    ):
        """Test contract execution failure."""
        # Import wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Mock contract execution error
        mock_signing_client.execute = AsyncMock(
            side_effect=Exception("Contract execution failed: unauthorized")
        )

        execute_tool = ExecuteContractTool(tool_context)

        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            result = await execute_tool.run({
                "contract_address": "secret1contractcontractcontractcontractcontra",
                "execute_msg": {"restricted_action": {}},
            })

        assert result["success"] is False
        assert "error" in result
        assert "failed" in result["error"]["message"].lower()
        assert "suggestions" in result["error"]

    @pytest.mark.asyncio
    async def test_contract_query_error(
        self,
        tool_context,
        mock_lcd_client,
    ):
        """Test contract query failure."""
        query_tool = QueryContractTool(tool_context)

        # Mock query error
        mock_lcd_client.wasm.contract_query = AsyncMock(
            side_effect=Exception("Query failed: contract not found")
        )

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            result = await query_tool.run({
                "contract_address": "secret1contractcontractcontractcontractcontra",
                "query_msg": {"get_data": {}},
            })

        assert result["success"] is False
        assert "error" in result
        assert "failed" in result["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_no_active_wallet_error(
        self,
        tool_context,
    ):
        """Test operations that require wallet without active wallet."""
        send_tool = SendTokensTool(tool_context)

        # Try to send without active wallet
        result = await send_tool.run({
            "recipient": "secret1recipientrecipientrecipientrecipientrecip",
            "amount": "1000000",
            "denom": "uscrt",
        })

        assert result["success"] is False
        assert "error" in result
        assert ("wallet" in result["error"]["message"].lower() or
                "active" in result["error"]["message"].lower())
        assert "suggestions" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_required_parameter(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
    ):
        """Test validation error for missing required parameters."""
        # Import wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Try to send without amount
        send_tool = SendTokensTool(tool_context)

        result = await send_tool.run({
            "recipient": "secret1recipientrecipientrecipientrecipientrecip",
            # Missing "amount" parameter
            "denom": "uscrt",
        })

        assert result["success"] is False
        assert "error" in result
        assert ("missing" in result["error"]["message"].lower() or
                "required" in result["error"]["message"].lower() or
                "amount" in result["error"]["message"].lower())

    @pytest.mark.asyncio
    async def test_invalid_amount_format(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
    ):
        """Test validation error for invalid amount format."""
        # Import wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        send_tool = SendTokensTool(tool_context)

        # Try with negative amount
        result = await send_tool.run({
            "recipient": "secret1recipientrecipientrecipientrecipientrecip",
            "amount": "-1000000",
            "denom": "uscrt",
        })

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_delegation_to_invalid_validator(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        mock_signing_client,
    ):
        """Test delegation to invalid or non-existent validator."""
        # Import wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Mock delegation error
        mock_signing_client.delegate = AsyncMock(
            side_effect=Exception("validator not found")
        )

        delegate_tool = DelegateTool(tool_context)

        with patch("mcp_scrt.tools.staking.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            result = await delegate_tool.run({
                "validator_address": "secretvaloper1invalidvalidatorinvalidvalidatorin",
                "amount": "1000000",
            })

        assert result["success"] is False
        assert "error" in result
        assert "suggestions" in result["error"]

    @pytest.mark.asyncio
    async def test_transaction_timeout(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        mock_signing_client,
    ):
        """Test transaction timeout error handling."""
        # Import wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Mock timeout error
        mock_signing_client.send = AsyncMock(
            side_effect=Exception("Transaction timed out after 60 seconds")
        )

        send_tool = SendTokensTool(tool_context)

        with patch("mcp_scrt.tools.bank.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            result = await send_tool.run({
                "recipient": "secret1recipientrecipientrecipientrecipientrecip",
                "amount": "1000000",
                "denom": "uscrt",
            })

        assert result["success"] is False
        assert "error" in result
        assert ("timeout" in result["error"]["message"].lower() or
                "timed" in result["error"]["message"].lower())

    @pytest.mark.asyncio
    async def test_error_messages_include_helpful_suggestions(
        self,
        tool_context,
    ):
        """Test that all error messages include helpful suggestions."""
        # Test with no active wallet
        send_tool = SendTokensTool(tool_context)

        result = await send_tool.run({
            "recipient": "secret1recipientrecipientrecipientrecipientrecip",
            "amount": "1000000",
            "denom": "uscrt",
        })

        assert result["success"] is False
        assert "error" in result
        assert "suggestions" in result["error"]
        assert len(result["error"]["suggestions"]) > 0
        assert isinstance(result["error"]["suggestions"], list)

        # Verify suggestions are helpful strings
        for suggestion in result["error"]["suggestions"]:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0
