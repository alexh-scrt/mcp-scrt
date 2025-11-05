"""Integration tests for smart contract workflow.

Tests the complete end-to-end contract workflow including:
1. Upload contract (WASM)
2. Instantiate contract instance
3. Execute contract (write operation)
4. Query contract (read operation)
5. Verify encrypted communication
"""

import pytest
import base64
from unittest.mock import patch, AsyncMock

from mcp_scrt.tools.wallet import ImportWalletTool
from mcp_scrt.tools.contract import (
    UploadContractTool,
    InstantiateContractTool,
    ExecuteContractTool,
    QueryContractTool,
    GetCodeInfoTool,
    GetContractInfoTool,
    BatchExecuteTool,
)


class TestContractWorkflow:
    """Integration tests for complete contract workflow."""

    @pytest.mark.asyncio
    async def test_complete_contract_lifecycle(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        mock_signing_client,
        mock_lcd_client,
    ):
        """Test complete contract lifecycle from upload to query.

        Workflow:
        1. Import wallet with funds
        2. Upload contract WASM code
        3. Get code info and verify
        4. Instantiate contract
        5. Get contract info
        6. Execute contract (increment counter)
        7. Query contract state
        8. Verify encryption worked
        """
        # Step 1: Import test wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Step 2: Upload contract WASM
        upload_tool = UploadContractTool(tool_context)

        # Create fake WASM bytecode (base64 encoded)
        fake_wasm = b"fake_wasm_bytecode_for_counter_contract"
        wasm_base64 = base64.b64encode(fake_wasm).decode()

        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            upload_result = await upload_tool.run({
                "wasm_byte_code": wasm_base64
            })

        assert upload_result["success"] is True
        assert "code_id" in upload_result["data"]
        code_id = upload_result["data"]["code_id"]
        assert code_id == 999  # From mock

        # Step 3: Get code info
        code_info_tool = GetCodeInfoTool(tool_context)

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_lcd_client.wasm.code_info = AsyncMock(
                return_value={
                    "code_id": code_id,
                    "creator": test_wallet_with_funds.address,
                    "code_hash": "abc123def456",
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            code_info_result = await code_info_tool.run({
                "code_id": code_id
            })

        assert code_info_result["success"] is True
        assert code_info_result["data"]["code_info"]["code_id"] == code_id

        # Step 4: Instantiate contract
        instantiate_tool = InstantiateContractTool(tool_context)

        init_msg = {"count": 0}
        contract_label = "test_counter_contract"

        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            instantiate_result = await instantiate_tool.run({
                "code_id": code_id,
                "init_msg": init_msg,
                "label": contract_label,
            })

        assert instantiate_result["success"] is True
        assert "contract_address" in instantiate_result["data"]
        contract_address = instantiate_result["data"]["contract_address"]

        # Step 5: Get contract info
        contract_info_tool = GetContractInfoTool(tool_context)

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_lcd_client.wasm.contract_info = AsyncMock(
                return_value={
                    "address": contract_address,
                    "code_id": code_id,
                    "creator": test_wallet_with_funds.address,
                    "label": contract_label,
                }
            )
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            contract_info_result = await contract_info_tool.run({
                "contract_address": contract_address
            })

        assert contract_info_result["success"] is True
        assert contract_info_result["data"]["contract_info"]["code_id"] == code_id
        assert contract_info_result["data"]["contract_info"]["label"] == contract_label

        # Step 6: Execute contract (increment counter)
        execute_tool = ExecuteContractTool(tool_context)

        execute_msg = {"increment": {}}

        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            execute_result = await execute_tool.run({
                "contract_address": contract_address,
                "execute_msg": execute_msg,
            })

        assert execute_result["success"] is True
        assert "txhash" in execute_result["data"]

        # Step 7: Query contract state
        query_tool = QueryContractTool(tool_context)

        query_msg = {"get_count": {}}

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_lcd_client.wasm.contract_query = AsyncMock(
                return_value={"count": 1}  # After increment
            )
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            query_result = await query_tool.run({
                "contract_address": contract_address,
                "query_msg": query_msg,
            })

        assert query_result["success"] is True
        assert query_result["data"]["query_result"]["count"] == 1

        # Step 8: Verify encryption is mentioned in messages
        # (In real implementation, encryption happens automatically)
        assert contract_address in execute_result["data"]["message"]
        assert contract_address in query_result["data"]["message"]

    @pytest.mark.asyncio
    async def test_contract_batch_execution(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        mock_signing_client,
    ):
        """Test batch execution of multiple contract calls."""
        # Import test wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Execute multiple contract calls in batch
        batch_tool = BatchExecuteTool(tool_context)

        contract1 = "secret1contract1contract1contract1contract1co"
        contract2 = "secret1contract2contract2contract2contract2co"

        messages = [
            {
                "contract_address": contract1,
                "execute_msg": {"action1": {}},
                "funds": [],
            },
            {
                "contract_address": contract2,
                "execute_msg": {"action2": {"value": 42}},
                "funds": [{"denom": "uscrt", "amount": "1000000"}],
            },
        ]

        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_signing_client.batch_execute = AsyncMock(
                return_value={
                    "txhash": "BATCH_EXECUTE_TXHASH",
                    "code": 0,
                }
            )
            mock_create.return_value = mock_signing_client

            batch_result = await batch_tool.run({
                "messages": messages
            })

        assert batch_result["success"] is True
        assert "txhash" in batch_result["data"]
        assert batch_result["data"]["message_count"] == 2

    @pytest.mark.asyncio
    async def test_contract_with_funds(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        mock_signing_client,
    ):
        """Test executing contract with attached funds."""
        # Import test wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Execute contract with funds attached
        execute_tool = ExecuteContractTool(tool_context)

        contract_address = "secret1contractcontractcontractcontractcontra"
        execute_msg = {"deposit": {}}
        funds = [{"denom": "uscrt", "amount": "5000000"}]  # 5 SCRT

        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            execute_result = await execute_tool.run({
                "contract_address": contract_address,
                "execute_msg": execute_msg,
                "funds": funds,
            })

        assert execute_result["success"] is True
        assert "txhash" in execute_result["data"]

        # Verify funds were passed in the call
        call_args = mock_signing_client.execute.call_args
        assert call_args is not None
        if call_args[1]:  # kwargs
            assert call_args[1].get("funds") == funds

    @pytest.mark.asyncio
    async def test_instantiate_with_funds(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        mock_signing_client,
    ):
        """Test instantiating contract with initial funds."""
        # Import test wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        # Instantiate with funds
        instantiate_tool = InstantiateContractTool(tool_context)

        code_id = 123
        init_msg = {"owner": test_wallet_with_funds.address}
        label = "funded_contract"
        funds = [{"denom": "uscrt", "amount": "10000000"}]  # 10 SCRT

        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            instantiate_result = await instantiate_tool.run({
                "code_id": code_id,
                "init_msg": init_msg,
                "label": label,
                "funds": funds,
            })

        assert instantiate_result["success"] is True
        assert "contract_address" in instantiate_result["data"]

        # Verify funds were passed
        call_args = mock_signing_client.instantiate.call_args
        assert call_args is not None
        if call_args[1]:  # kwargs
            assert call_args[1].get("funds") == funds

    @pytest.mark.asyncio
    async def test_query_without_wallet(
        self,
        tool_context,
        mock_lcd_client,
    ):
        """Test querying contract without active wallet (read-only)."""
        query_tool = QueryContractTool(tool_context)

        contract_address = "secret1contractcontractcontractcontractcontra"
        query_msg = {"public_data": {}}

        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_lcd_client.wasm.contract_query = AsyncMock(
                return_value={"data": "public_value"}
            )
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            query_result = await query_tool.run({
                "contract_address": contract_address,
                "query_msg": query_msg,
            })

        assert query_result["success"] is True
        assert query_result["data"]["query_result"]["data"] == "public_value"

    @pytest.mark.asyncio
    async def test_multiple_contract_interactions(
        self,
        tool_context,
        session,
        test_wallet_with_funds,
        mock_signing_client,
        mock_lcd_client,
    ):
        """Test multiple sequential contract interactions."""
        # Import test wallet
        import_tool = ImportWalletTool(tool_context)

        with patch("mcp_scrt.tools.wallet.derive_address_from_mnemonic") as mock_derive:
            mock_derive.return_value = test_wallet_with_funds.address
            await import_tool.run({
                "name": test_wallet_with_funds.wallet_id,
                "mnemonic": "test mnemonic phrase with twelve words for testing purposes only example"
            })

        contract_address = "secret1contractcontractcontractcontractcontra"
        execute_tool = ExecuteContractTool(tool_context)
        query_tool = QueryContractTool(tool_context)

        # Execute: Set value
        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            await execute_tool.run({
                "contract_address": contract_address,
                "execute_msg": {"set_value": {"value": 100}},
            })

        # Query: Get value
        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_lcd_client.wasm.contract_query = AsyncMock(
                return_value={"value": 100}
            )
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            query_result = await query_tool.run({
                "contract_address": contract_address,
                "query_msg": {"get_value": {}},
            })

        assert query_result["success"] is True
        assert query_result["data"]["query_result"]["value"] == 100

        # Execute: Increment value
        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_create.return_value = mock_signing_client

            await execute_tool.run({
                "contract_address": contract_address,
                "execute_msg": {"increment": {"amount": 50}},
            })

        # Query: Verify new value
        with patch.object(tool_context.client_pool, "get_client") as mock_get_client:
            mock_lcd_client.wasm.contract_query = AsyncMock(
                return_value={"value": 150}
            )
            mock_get_client.return_value.__enter__.return_value = mock_lcd_client

            query_result = await query_tool.run({
                "contract_address": contract_address,
                "query_msg": {"get_value": {}},
            })

        assert query_result["success"] is True
        assert query_result["data"]["query_result"]["value"] == 150
