"""Tests for contract tools.

This module tests the contract tools for WASM contract operations.
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, patch, AsyncMock
import base64

from mcp_scrt.tools.contract import (
    UploadContractTool,
    GetCodeInfoTool,
    ListCodesTool,
    InstantiateContractTool,
    ExecuteContractTool,
    QueryContractTool,
    BatchExecuteTool,
    GetContractInfoTool,
    GetContractHistoryTool,
    MigrateContractTool,
)
from mcp_scrt.tools.base import ToolCategory, ToolExecutionContext
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.types import NetworkType, WalletInfo
from mcp_scrt.utils.errors import ValidationError


class TestUploadContractTool:
    """Test upload_contract tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = UploadContractTool(context)

        assert tool.name == "upload_contract"
        assert "upload" in tool.description.lower()
        assert tool.category == ToolCategory.CONTRACTS
        assert tool.requires_wallet is True

    def test_validate_params_missing_wasm_byte_code(self) -> None:
        """Test validation fails without wasm_byte_code."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = UploadContractTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "wasm_byte_code" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_upload_contract(self) -> None:
        """Test uploading a contract."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Start session and load wallet
        session.start()
        wallet = WalletInfo(
            wallet_id="test_wallet",
            address="secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
        )
        session.load_wallet(wallet)

        tool = UploadContractTool(context)

        # Mock WASM bytecode (base64 encoded)
        wasm_bytecode = base64.b64encode(b"fake_wasm_code").decode()

        # Mock the signing client
        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_signing = AsyncMock()
            mock_signing.upload = AsyncMock(
                return_value={
                    "txhash": "ABC123",
                    "code": 0,
                    "code_id": 1,
                }
            )
            mock_create.return_value = mock_signing

            result = await tool.run({
                "wasm_byte_code": wasm_bytecode,
            })

            assert result["success"] is True
            assert "code_id" in result["data"]


class TestGetCodeInfoTool:
    """Test get_code_info tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetCodeInfoTool(context)

        assert tool.name == "get_code_info"
        assert "code" in tool.description.lower()
        assert tool.category == ToolCategory.CONTRACTS
        assert tool.requires_wallet is False

    def test_validate_params_missing_code_id(self) -> None:
        """Test validation fails without code_id."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetCodeInfoTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "code_id" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_code_info(self) -> None:
        """Test getting code info."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetCodeInfoTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.wasm = Mock()
            mock_client.wasm.code = AsyncMock(
                return_value={
                    "code_info": {
                        "code_id": "1",
                        "creator": "secret1...",
                        "code_hash": "abc123",
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"code_id": "1"})

            assert result["success"] is True
            assert "code_info" in result["data"]


class TestListCodesTool:
    """Test list_codes tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ListCodesTool(context)

        assert tool.name == "list_codes"
        assert "list" in tool.description.lower() or "codes" in tool.description.lower()
        assert tool.category == ToolCategory.CONTRACTS
        assert tool.requires_wallet is False

    @pytest.mark.asyncio
    async def test_execute_list_codes(self) -> None:
        """Test listing codes."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ListCodesTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.wasm = Mock()
            mock_client.wasm.codes = AsyncMock(
                return_value={
                    "code_infos": [
                        {
                            "code_id": "1",
                            "creator": "secret1...",
                            "code_hash": "abc123",
                        }
                    ],
                    "pagination": {"next_key": None, "total": "1"},
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({})

            assert result["success"] is True
            assert "code_infos" in result["data"]


class TestInstantiateContractTool:
    """Test instantiate_contract tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = InstantiateContractTool(context)

        assert tool.name == "instantiate_contract"
        assert "instantiate" in tool.description.lower()
        assert tool.category == ToolCategory.CONTRACTS
        assert tool.requires_wallet is True

    def test_validate_params_missing_code_id(self) -> None:
        """Test validation fails without code_id."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = InstantiateContractTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "label": "test",
                "init_msg": {},
            })

        assert "code_id" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_instantiate_contract(self) -> None:
        """Test instantiating a contract."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Start session and load wallet
        session.start()
        wallet = WalletInfo(
            wallet_id="test_wallet",
            address="secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
        )
        session.load_wallet(wallet)

        tool = InstantiateContractTool(context)

        # Mock the signing client
        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_signing = AsyncMock()
            mock_signing.instantiate = AsyncMock(
                return_value={
                    "txhash": "ABC123",
                    "code": 0,
                    "contract_address": "secret1contractcontractcontractcontractcontra",
                }
            )
            mock_create.return_value = mock_signing

            result = await tool.run({
                "code_id": "1",
                "label": "test_contract",
                "init_msg": {"count": 0},
            })

            assert result["success"] is True
            assert "contract_address" in result["data"]


class TestExecuteContractTool:
    """Test execute_contract tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ExecuteContractTool(context)

        assert tool.name == "execute_contract"
        assert "execute" in tool.description.lower()
        assert tool.category == ToolCategory.CONTRACTS
        assert tool.requires_wallet is True

    def test_validate_params_missing_contract_address(self) -> None:
        """Test validation fails without contract_address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = ExecuteContractTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"msg": {}})

        assert "contract_address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_execute_contract(self) -> None:
        """Test executing a contract."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Start session and load wallet
        session.start()
        wallet = WalletInfo(
            wallet_id="test_wallet",
            address="secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
        )
        session.load_wallet(wallet)

        tool = ExecuteContractTool(context)

        # Mock the signing client
        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_signing = AsyncMock()
            mock_signing.execute = AsyncMock(
                return_value={
                    "txhash": "ABC123",
                    "code": 0,
                }
            )
            mock_create.return_value = mock_signing

            result = await tool.run({
                "contract_address": "secret1contractcontractcontractcontractcontra",
                "msg": {"increment": {}},
            })

            assert result["success"] is True
            assert "txhash" in result["data"]


class TestQueryContractTool:
    """Test query_contract tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = QueryContractTool(context)

        assert tool.name == "query_contract"
        assert "query" in tool.description.lower()
        assert tool.category == ToolCategory.CONTRACTS
        assert tool.requires_wallet is False

    def test_validate_params_missing_contract_address(self) -> None:
        """Test validation fails without contract_address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = QueryContractTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({"query_msg": {}})

        assert "contract_address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_query_contract(self) -> None:
        """Test querying a contract."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = QueryContractTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.wasm = Mock()
            mock_client.wasm.contract_query = AsyncMock(
                return_value={"count": 42}
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({
                "contract_address": "secret1contractcontractcontractcontractcontra",
                "query_msg": {"get_count": {}},
            })

            assert result["success"] is True
            assert "query_result" in result["data"]


class TestBatchExecuteTool:
    """Test batch_execute tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = BatchExecuteTool(context)

        assert tool.name == "batch_execute"
        assert "batch" in tool.description.lower()
        assert tool.category == ToolCategory.CONTRACTS
        assert tool.requires_wallet is True

    def test_validate_params_missing_executions(self) -> None:
        """Test validation fails without executions."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = BatchExecuteTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "executions" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_batch_execute(self) -> None:
        """Test batch executing contracts."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Start session and load wallet
        session.start()
        wallet = WalletInfo(
            wallet_id="test_wallet",
            address="secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
        )
        session.load_wallet(wallet)

        tool = BatchExecuteTool(context)

        # Mock the signing client
        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_signing = AsyncMock()
            mock_signing.batch_execute = AsyncMock(
                return_value={
                    "txhash": "ABC123",
                    "code": 0,
                }
            )
            mock_create.return_value = mock_signing

            result = await tool.run({
                "executions": [
                    {"contract_address": "secret1contract1contract1contract1contract1c", "msg": {"increment": {}}},
                    {"contract_address": "secret1contract2contract2contract2contract2c", "msg": {"increment": {}}},
                ],
            })

            assert result["success"] is True
            assert "txhash" in result["data"]


class TestGetContractInfoTool:
    """Test get_contract_info tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetContractInfoTool(context)

        assert tool.name == "get_contract_info"
        assert "contract" in tool.description.lower() and "info" in tool.description.lower()
        assert tool.category == ToolCategory.CONTRACTS
        assert tool.requires_wallet is False

    def test_validate_params_missing_contract_address(self) -> None:
        """Test validation fails without contract_address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetContractInfoTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "contract_address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_contract_info(self) -> None:
        """Test getting contract info."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetContractInfoTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.wasm = Mock()
            mock_client.wasm.contract_info = AsyncMock(
                return_value={
                    "contract_info": {
                        "code_id": "1",
                        "creator": "secret1...",
                        "admin": "secret1...",
                        "label": "test_contract",
                    }
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"contract_address": "secret1contractcontractcontractcontractcontra"})

            assert result["success"] is True
            assert "contract_info" in result["data"]


class TestGetContractHistoryTool:
    """Test get_contract_history tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetContractHistoryTool(context)

        assert tool.name == "get_contract_history"
        assert "history" in tool.description.lower()
        assert tool.category == ToolCategory.CONTRACTS
        assert tool.requires_wallet is False

    def test_validate_params_missing_contract_address(self) -> None:
        """Test validation fails without contract_address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetContractHistoryTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({})

        assert "contract_address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_get_contract_history(self) -> None:
        """Test getting contract history."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = GetContractHistoryTool(context)

        # Mock the client pool
        with patch.object(pool, "get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.wasm = Mock()
            mock_client.wasm.contract_history = AsyncMock(
                return_value={
                    "entries": [
                        {
                            "operation": "CONTRACT_CODE_HISTORY_OPERATION_TYPE_INIT",
                            "code_id": "1",
                            "updated": {"block_height": "12345"},
                        }
                    ],
                    "pagination": {"next_key": None, "total": "1"},
                }
            )
            mock_get_client.return_value.__enter__ = Mock(return_value=mock_client)
            mock_get_client.return_value.__exit__ = Mock(return_value=False)

            result = await tool.run({"contract_address": "secret1contractcontractcontractcontractcontra"})

            assert result["success"] is True
            assert "entries" in result["data"]


class TestMigrateContractTool:
    """Test migrate_contract tool."""

    def test_tool_metadata(self) -> None:
        """Test tool metadata is correct."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = MigrateContractTool(context)

        assert tool.name == "migrate_contract"
        assert "migrate" in tool.description.lower()
        assert tool.category == ToolCategory.CONTRACTS
        assert tool.requires_wallet is True

    def test_validate_params_missing_contract_address(self) -> None:
        """Test validation fails without contract_address."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tool = MigrateContractTool(context)

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_params({
                "new_code_id": "2",
                "migrate_msg": {},
            })

        assert "contract_address" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_execute_migrate_contract(self) -> None:
        """Test migrating a contract."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        # Start session and load wallet
        session.start()
        wallet = WalletInfo(
            wallet_id="test_wallet",
            address="secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03",
        )
        session.load_wallet(wallet)

        tool = MigrateContractTool(context)

        # Mock the signing client
        with patch("mcp_scrt.tools.contract.create_signing_client") as mock_create:
            mock_signing = AsyncMock()
            mock_signing.migrate = AsyncMock(
                return_value={
                    "txhash": "ABC123",
                    "code": 0,
                }
            )
            mock_create.return_value = mock_signing

            result = await tool.run({
                "contract_address": "secret1contractcontractcontractcontractcontra",
                "new_code_id": "2",
                "migrate_msg": {},
            })

            assert result["success"] is True
            assert "txhash" in result["data"]


class TestContractToolsIntegration:
    """Test contract tools working together."""

    @pytest.mark.asyncio
    async def test_all_contract_tools_have_correct_metadata(self) -> None:
        """Test all contract tools can be instantiated and have correct metadata."""
        session = Session(network=NetworkType.TESTNET)
        pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)
        context = ToolExecutionContext(
            session=session,
            client_pool=pool,
            network=NetworkType.TESTNET,
        )

        tools = [
            UploadContractTool(context),
            GetCodeInfoTool(context),
            ListCodesTool(context),
            InstantiateContractTool(context),
            ExecuteContractTool(context),
            QueryContractTool(context),
            BatchExecuteTool(context),
            GetContractInfoTool(context),
            GetContractHistoryTool(context),
            MigrateContractTool(context),
        ]

        # All tools should be CONTRACTS category
        for tool in tools:
            assert tool.category == ToolCategory.CONTRACTS
            assert tool.name is not None
            assert tool.description is not None

        # All tool names should be unique
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))

        # Check which tools require wallet
        wallet_required = [tool for tool in tools if tool.requires_wallet]
        wallet_not_required = [tool for tool in tools if not tool.requires_wallet]

        # upload, instantiate, execute, batch_execute, migrate should require wallet
        assert len(wallet_required) == 5
        assert len(wallet_not_required) == 5
