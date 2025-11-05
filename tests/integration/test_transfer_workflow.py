"""Integration tests for token transfer workflow.

Tests the complete end-to-end token transfer workflow including:
1. Configure network (testnet)
2. Import/create test wallet
3. Check balance
4. Send tokens to another address
5. Verify transaction
6. Check new balance
"""

import pytest
from unittest.mock import patch, AsyncMock

from mcp_scrt.tools.network import ConfigureNetworkTool
from mcp_scrt.tools.wallet import ImportWalletTool, CreateWalletTool, GetActiveWalletTool
from mcp_scrt.tools.bank import GetBalanceTool, SendTokensTool
from mcp_scrt.tools.transaction import GetTransactionTool
from mcp_scrt.types import NetworkType


class TestTransferWorkflow:
    """Integration tests for complete transfer workflow."""

    @pytest.mark.asyncio
    async def test_complete_transfer_workflow(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        recipient_address,
        mock_signing_client,
        mock_lcd_client,
    ):
        """Test complete token transfer workflow from start to finish.

        This test simulates a real user workflow:
        1. Configure network to testnet
        2. Import a wallet with funds
        3. Check initial balance
        4. Send tokens to recipient
        5. Verify transaction was successful
        6. Check balances were updated
        """
        # Step 1: Configure network to testnet
        configure_tool = ConfigureNetworkTool(tool_context)
        config_result = await configure_tool.run({"network": "testnet"})

        assert config_result["success"] is True
        assert "testnet" in config_result["data"]["message"].lower()

        # Step 2: Import test wallet
        import_tool = ImportWalletTool(tool_context)

        # Mock the wallet import
        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address

            import_result = await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        assert import_result["success"] is True
        assert import_result["data"]["address"] == test_wallet_with_funds.address

        # Step 3: Check initial balance
        balance_tool = GetBalanceTool(tool_context)

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            initial_balance_result = await balance_tool.run({})

        assert initial_balance_result["success"] is True
        initial_balances = initial_balance_result["data"]["balances"]
        assert len(initial_balances) > 0

        # Find SCRT balance
        initial_scrt_balance = next(
            (b for b in initial_balances if b["denom"] == "uscrt"),
            None
        )
        assert initial_scrt_balance is not None
        initial_amount = int(initial_scrt_balance["amount"])

        # Step 4: Send tokens to recipient
        send_tool = SendTokensTool(tool_context)
        transfer_amount = "1000000"  # 1 SCRT

        with patch("mcp_scrt.tools.bank.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            send_result = await send_tool.run({
                "recipient": recipient_address,
                "amount": transfer_amount,
                "denom": "uscrt",
            })

        assert send_result["success"] is True
        assert "txhash" in send_result["data"]
        txhash = send_result["data"]["txhash"]

        # Step 5: Verify transaction was successful
        tx_tool = GetTransactionTool(tool_context)

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            tx_result = await tx_tool.run({"txhash": txhash})

        assert tx_result["success"] is True
        assert tx_result["data"]["txhash"] == txhash
        assert tx_result["data"]["code"] == 0  # Success code

        # Step 6: Check new balance (should be reduced by transfer amount + gas)
        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            # Mock new balance (reduced by transfer amount)
            mock_lcd_client.bank.balance = AsyncMock(
                return_value={
                    "balances": [
                        {"denom": "uscrt", "amount": str(initial_amount - int(transfer_amount) - 5000)}  # minus gas
                    ]
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            final_balance_result = await balance_tool.run({})

        assert final_balance_result["success"] is True
        final_balances = final_balance_result["data"]["balances"]
        final_scrt_balance = next(
            (b for b in final_balances if b["denom"] == "uscrt"),
            None
        )
        assert final_scrt_balance is not None
        final_amount = int(final_scrt_balance["amount"])

        # Verify balance decreased (by transfer amount + gas)
        assert final_amount < initial_amount
        assert final_amount == initial_amount - int(transfer_amount) - 5000

    @pytest.mark.asyncio
    async def test_transfer_with_insufficient_balance(
        self,
        tool_context,
        session,
        test_wallet,
        recipient_address,
        mock_signing_client,
        mock_lcd_client,
    ):
        """Test transfer fails gracefully with insufficient balance."""
        # Import test wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet.address
            await import_tool.run({
                "name": test_wallet.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Mock balance query with low balance
        mock_lcd_client.bank.balance = AsyncMock(
            return_value={
                "balances": [
                    {"denom": "uscrt", "amount": "1000"}  # Very low balance
                ]
            }
        )

        # Mock signing client to raise insufficient funds error
        mock_signing_client.send = AsyncMock(
            side_effect=Exception("insufficient funds")
        )

        # Try to send more than available
        send_tool = SendTokensTool(tool_context)

        with patch("mcp_scrt.tools.bank.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            send_result = await send_tool.run({
                "recipient": recipient_address,
                "amount": "1000000",  # Way more than balance
                "denom": "uscrt",
            })

        # Should fail with error
        assert send_result["success"] is False
        assert "error" in send_result
        assert "insufficient" in send_result["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_multi_send_workflow(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        mock_signing_client,
        mock_lcd_client,
    ):
        """Test multi-send to multiple recipients in one transaction."""
        # Import test wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Mock multi-send transaction
        mock_signing_client.multi_send = AsyncMock(
            return_value={
                "txhash": "MULTI_SEND_TXHASH",
                "code": 0,
            }
        )

        # Perform multi-send
        from mcp_scrt.tools.bank import MultiSendTool
        multi_send_tool = MultiSendTool(tool_context)

        with patch("mcp_scrt.tools.bank.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            result = await multi_send_tool.run({
                "recipients": [
                    {
                        "address": "secret1recipient1recipient1recipient1recipie",
                        "amount": "1000000",
                    },
                    {
                        "address": "secret1recipient2recipient2recipient2recipie",
                        "amount": "2000000",
                    },
                ]
            })

        assert result["success"] is True
        assert "txhash" in result["data"]
        assert result["data"]["recipient_count"] == 2
        assert result["data"]["total_amount"] == "3000000"

    @pytest.mark.asyncio
    async def test_transfer_with_memo(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        recipient_address,
        mock_signing_client,
    ):
        """Test token transfer with a memo."""
        # Import test wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Send tokens with memo
        send_tool = SendTokensTool(tool_context)
        test_memo = "Integration test transfer"

        with patch("mcp_scrt.tools.bank.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            result = await send_tool.run({
                "recipient": recipient_address,
                "amount": "1000000",
                "denom": "uscrt",
                "memo": test_memo,
            })

        assert result["success"] is True
        assert "txhash" in result["data"]

        # Verify memo was included in the call
        call_args = mock_signing_client.send.call_args
        assert call_args is not None
        if call_args[1]:  # kwargs
            assert call_args[1].get("memo") == test_memo

    @pytest.mark.asyncio
    async def test_check_balance_for_specific_address(
        self,
        tool_context,
        mock_lcd_client,
    ):
        """Test checking balance for a specific address (not active wallet)."""
        balance_tool = GetBalanceTool(tool_context)
        target_address = "secret1targetaddresstargetaddresstargetaddresst"

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            result = await balance_tool.run({"address": target_address})

        assert result["success"] is True
        assert result["data"]["address"] == target_address
        assert "balances" in result["data"]
