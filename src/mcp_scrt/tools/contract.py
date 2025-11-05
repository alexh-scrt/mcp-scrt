"""Contract tools for Secret Network WASM contract operations.

This module provides tools for uploading, instantiating, executing, and querying contracts.
"""

from typing import Any, Dict, List, Optional
import base64
import json

from mcp_scrt.tools.base import BaseTool, ToolCategory
from mcp_scrt.utils.errors import ValidationError, NetworkError, WalletError
from mcp_scrt.core.validation import validate_address


# Helper function to create a signing client (placeholder for now)
async def create_signing_client(wallet_name: str, network: str):
    """Create a signing client for wallet operations.

    This is a placeholder that will be replaced with actual signing client implementation.
    """
    # This will be implemented with actual Secret Network signing client
    class MockSigningClient:
        async def upload(self, wasm_byte_code: bytes):
            return {"txhash": "mock_hash", "code": 0, "code_id": 1}

        async def instantiate(
            self, code_id: int, init_msg: dict, label: str, funds: list = None
        ):
            return {
                "txhash": "mock_hash",
                "code": 0,
                "contract_address": "secret1contract...",
            }

        async def execute(self, contract_address: str, msg: dict, funds: list = None):
            return {"txhash": "mock_hash", "code": 0}

        async def batch_execute(self, executions: list):
            return {"txhash": "mock_hash", "code": 0}

        async def migrate(self, contract_address: str, new_code_id: int, migrate_msg: dict):
            return {"txhash": "mock_hash", "code": 0}

    return MockSigningClient()


class UploadContractTool(BaseTool):
    """Upload contract code.

    Upload WASM bytecode to the blockchain.
    """

    @property
    def name(self) -> str:
        return "upload_contract"

    @property
    def description(self) -> str:
        return (
            "Upload WASM contract bytecode to the blockchain. "
            "Requires active wallet. Returns code ID for instantiation."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTRACTS

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet to sign transaction

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate upload contract parameters.

        Args:
            params: Must contain 'wasm_byte_code'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "wasm_byte_code" not in params:
            raise ValidationError(
                message="Missing required parameter: wasm_byte_code",
                details={"required_params": ["wasm_byte_code"]},
                suggestions=[
                    "Provide 'wasm_byte_code' parameter (base64 encoded)",
                    "Example: {'wasm_byte_code': 'AGFzbQ...'}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute upload contract.

        Args:
            params: Parameters including wasm_byte_code

        Returns:
            Transaction result with code ID
        """
        wasm_byte_code = params["wasm_byte_code"]

        # Get active wallet
        wallet_info = self.context.session.get_wallet()
        if not wallet_info:
            raise WalletError(
                message="No active wallet set",
                details={},
                suggestions=["Load a wallet using load_wallet"],
            )

        wallet_name = wallet_info.wallet_id
        uploader = wallet_info.address

        try:
            # Decode base64 WASM bytecode
            wasm_bytes = base64.b64decode(wasm_byte_code)

            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            # Upload contract
            result = await signing_client.upload(wasm_byte_code=wasm_bytes)

            return {
                "uploader": uploader,
                "code_id": result.get("code_id"),
                "txhash": result.get("txhash"),
                "message": f"Successfully uploaded contract code. Code ID: {result.get('code_id')}",
            }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to upload contract: {str(e)}",
                details={"uploader": uploader, "error": str(e)},
                suggestions=[
                    "Check that the WASM bytecode is valid",
                    "Verify network connectivity",
                ],
            )


class GetCodeInfoTool(BaseTool):
    """Get code info.

    Query information about uploaded contract code.
    """

    @property
    def name(self) -> str:
        return "get_code_info"

    @property
    def description(self) -> str:
        return (
            "Get information about uploaded contract code. "
            "Returns creator, code hash, and other metadata."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTRACTS

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get code info parameters.

        Args:
            params: Must contain 'code_id'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "code_id" not in params:
            raise ValidationError(
                message="Missing required parameter: code_id",
                details={"required_params": ["code_id"]},
                suggestions=[
                    "Provide 'code_id' parameter",
                    "Example: {'code_id': '1'}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get code info.

        Args:
            params: Parameters including code_id

        Returns:
            Code information
        """
        code_id = str(params["code_id"])

        try:
            # Query code info using client pool
            with self.context.client_pool.get_client() as client:
                code_response = await client.wasm.code(code_id)

                code_info = code_response.get("code_info", {})

                return {
                    "code_id": code_id,
                    "code_info": code_info,
                    "message": f"Code {code_id} retrieved successfully",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get code info: {str(e)}",
                details={"code_id": code_id, "error": str(e)},
                suggestions=[
                    "Check that the code ID exists",
                    "Verify network connectivity",
                ],
            )


class ListCodesTool(BaseTool):
    """List contract codes.

    List all uploaded contract codes.
    """

    @property
    def name(self) -> str:
        return "list_codes"

    @property
    def description(self) -> str:
        return "List all uploaded contract codes. Returns code IDs and metadata."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTRACTS

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate list codes parameters.

        Args:
            params: Optional pagination parameters

        Raises:
            ValidationError: If parameters are invalid
        """
        # No required parameters
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute list codes.

        Args:
            params: Optional pagination parameters

        Returns:
            List of code infos
        """
        try:
            # Query codes using client pool
            with self.context.client_pool.get_client() as client:
                codes_response = await client.wasm.codes()

                code_infos = codes_response.get("code_infos", [])
                pagination = codes_response.get("pagination", {})

                return {
                    "code_infos": code_infos,
                    "count": len(code_infos),
                    "pagination": pagination,
                    "message": f"Retrieved {len(code_infos)} code(s)",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to list codes: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Verify network connectivity",
                    "Try again later",
                ],
            )


class InstantiateContractTool(BaseTool):
    """Instantiate contract.

    Create a new contract instance from uploaded code.
    """

    @property
    def name(self) -> str:
        return "instantiate_contract"

    @property
    def description(self) -> str:
        return (
            "Instantiate a contract from uploaded code. "
            "Requires active wallet. Returns contract address."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTRACTS

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet to sign transaction

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate instantiate contract parameters.

        Args:
            params: Must contain 'code_id', 'label', 'init_msg'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "code_id" not in params:
            raise ValidationError(
                message="Missing required parameter: code_id",
                details={"required_params": ["code_id", "label", "init_msg"]},
                suggestions=[
                    "Provide 'code_id' parameter",
                    "Example: {'code_id': '1', 'label': 'my_contract', 'init_msg': {}}",
                ],
            )

        if "label" not in params:
            raise ValidationError(
                message="Missing required parameter: label",
                details={"required_params": ["code_id", "label", "init_msg"]},
                suggestions=[
                    "Provide 'label' parameter",
                    "Example: {'code_id': '1', 'label': 'my_contract', 'init_msg': {}}",
                ],
            )

        if "init_msg" not in params:
            raise ValidationError(
                message="Missing required parameter: init_msg",
                details={"required_params": ["code_id", "label", "init_msg"]},
                suggestions=[
                    "Provide 'init_msg' parameter",
                    "Example: {'code_id': '1', 'label': 'my_contract', 'init_msg': {}}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute instantiate contract.

        Args:
            params: Parameters including code_id, label, init_msg, optional funds

        Returns:
            Transaction result with contract address
        """
        code_id = int(params["code_id"])
        label = params["label"]
        init_msg = params["init_msg"]
        funds = params.get("funds", [])

        # Get active wallet
        wallet_info = self.context.session.get_wallet()
        if not wallet_info:
            raise WalletError(
                message="No active wallet set",
                details={},
                suggestions=["Load a wallet using load_wallet"],
            )

        wallet_name = wallet_info.wallet_id
        creator = wallet_info.address

        try:
            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            # Instantiate contract
            result = await signing_client.instantiate(
                code_id=code_id, init_msg=init_msg, label=label, funds=funds
            )

            return {
                "creator": creator,
                "code_id": code_id,
                "label": label,
                "contract_address": result.get("contract_address"),
                "txhash": result.get("txhash"),
                "message": f"Successfully instantiated contract at {result.get('contract_address')}",
            }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to instantiate contract: {str(e)}",
                details={
                    "creator": creator,
                    "code_id": code_id,
                    "label": label,
                    "error": str(e),
                },
                suggestions=[
                    "Check that the code ID exists",
                    "Verify the init_msg format is correct",
                    "Verify network connectivity",
                ],
            )


class ExecuteContractTool(BaseTool):
    """Execute contract.

    Execute a contract function.
    """

    @property
    def name(self) -> str:
        return "execute_contract"

    @property
    def description(self) -> str:
        return (
            "Execute a contract function. "
            "Requires active wallet. Can send funds with the execution."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTRACTS

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet to sign transaction

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate execute contract parameters.

        Args:
            params: Must contain 'contract_address' and 'msg'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "contract_address" not in params:
            raise ValidationError(
                message="Missing required parameter: contract_address",
                details={"required_params": ["contract_address", "msg"]},
                suggestions=[
                    "Provide 'contract_address' parameter",
                    "Example: {'contract_address': 'secret1...', 'msg': {}}",
                ],
            )

        if "msg" not in params:
            raise ValidationError(
                message="Missing required parameter: msg",
                details={"required_params": ["contract_address", "msg"]},
                suggestions=[
                    "Provide 'msg' parameter",
                    "Example: {'contract_address': 'secret1...', 'msg': {}}",
                ],
            )

        # Validate contract address
        validate_address(params["contract_address"])

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute execute contract.

        Args:
            params: Parameters including contract_address, msg, optional funds

        Returns:
            Transaction result
        """
        contract_address = params["contract_address"]
        msg = params["msg"]
        funds = params.get("funds", [])

        # Get active wallet
        wallet_info = self.context.session.get_wallet()
        if not wallet_info:
            raise WalletError(
                message="No active wallet set",
                details={},
                suggestions=["Load a wallet using load_wallet"],
            )

        wallet_name = wallet_info.wallet_id
        sender = wallet_info.address

        try:
            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            # Execute contract
            result = await signing_client.execute(
                contract_address=contract_address, msg=msg, funds=funds
            )

            return {
                "sender": sender,
                "contract_address": contract_address,
                "txhash": result.get("txhash"),
                "message": f"Successfully executed contract {contract_address}",
            }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to execute contract: {str(e)}",
                details={
                    "sender": sender,
                    "contract_address": contract_address,
                    "error": str(e),
                },
                suggestions=[
                    "Check that the contract address is correct",
                    "Verify the msg format is correct",
                    "Verify network connectivity",
                ],
            )


class QueryContractTool(BaseTool):
    """Query contract.

    Query a contract's state.
    """

    @property
    def name(self) -> str:
        return "query_contract"

    @property
    def description(self) -> str:
        return (
            "Query a contract's state. "
            "Read-only operation that doesn't require wallet."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTRACTS

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate query contract parameters.

        Args:
            params: Must contain 'contract_address' and 'query_msg'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "contract_address" not in params:
            raise ValidationError(
                message="Missing required parameter: contract_address",
                details={"required_params": ["contract_address", "query_msg"]},
                suggestions=[
                    "Provide 'contract_address' parameter",
                    "Example: {'contract_address': 'secret1...', 'query_msg': {}}",
                ],
            )

        if "query_msg" not in params:
            raise ValidationError(
                message="Missing required parameter: query_msg",
                details={"required_params": ["contract_address", "query_msg"]},
                suggestions=[
                    "Provide 'query_msg' parameter",
                    "Example: {'contract_address': 'secret1...', 'query_msg': {}}",
                ],
            )

        # Validate contract address
        validate_address(params["contract_address"])

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query contract.

        Args:
            params: Parameters including contract_address and query_msg

        Returns:
            Query result
        """
        contract_address = params["contract_address"]
        query_msg = params["query_msg"]

        try:
            # Query contract using client pool
            with self.context.client_pool.get_client() as client:
                query_result = await client.wasm.contract_query(
                    contract_address, query_msg
                )

                return {
                    "contract_address": contract_address,
                    "query_result": query_result,
                    "message": f"Successfully queried contract {contract_address}",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to query contract: {str(e)}",
                details={
                    "contract_address": contract_address,
                    "query_msg": query_msg,
                    "error": str(e),
                },
                suggestions=[
                    "Check that the contract address is correct",
                    "Verify the query_msg format is correct",
                    "Verify network connectivity",
                ],
            )


class BatchExecuteTool(BaseTool):
    """Batch execute contracts.

    Execute multiple contract calls in a single transaction.
    """

    @property
    def name(self) -> str:
        return "batch_execute"

    @property
    def description(self) -> str:
        return (
            "Batch execute multiple contract calls in a single transaction. "
            "Requires active wallet. All executions succeed or fail together."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTRACTS

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet to sign transaction

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate batch execute parameters.

        Args:
            params: Must contain 'executions' (list of contract calls)

        Raises:
            ValidationError: If parameters are invalid
        """
        if "executions" not in params:
            raise ValidationError(
                message="Missing required parameter: executions",
                details={"required_params": ["executions"]},
                suggestions=[
                    "Provide 'executions' parameter as a list",
                    "Example: {'executions': [{'contract_address': '...', 'msg': {}}]}",
                ],
            )

        executions = params["executions"]
        if not isinstance(executions, list) or len(executions) == 0:
            raise ValidationError(
                message="Executions must be a non-empty list",
                details={"provided_type": type(executions).__name__},
                suggestions=[
                    "Provide at least one execution",
                    "Example: {'executions': [{'contract_address': '...', 'msg': {}}]}",
                ],
            )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute batch execute.

        Args:
            params: Parameters including executions list

        Returns:
            Transaction result
        """
        executions = params["executions"]

        # Get active wallet
        wallet_info = self.context.session.get_wallet()
        if not wallet_info:
            raise WalletError(
                message="No active wallet set",
                details={},
                suggestions=["Load a wallet using load_wallet"],
            )

        wallet_name = wallet_info.wallet_id
        sender = wallet_info.address

        try:
            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            # Batch execute contracts
            result = await signing_client.batch_execute(executions=executions)

            return {
                "sender": sender,
                "executions_count": len(executions),
                "txhash": result.get("txhash"),
                "message": f"Successfully executed {len(executions)} contract call(s)",
            }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to batch execute contracts: {str(e)}",
                details={
                    "sender": sender,
                    "executions_count": len(executions),
                    "error": str(e),
                },
                suggestions=[
                    "Check that all contract addresses are correct",
                    "Verify all msg formats are correct",
                    "Verify network connectivity",
                ],
            )


class GetContractInfoTool(BaseTool):
    """Get contract info.

    Query information about an instantiated contract.
    """

    @property
    def name(self) -> str:
        return "get_contract_info"

    @property
    def description(self) -> str:
        return (
            "Get information about an instantiated contract. "
            "Returns code ID, creator, admin, and label."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTRACTS

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get contract info parameters.

        Args:
            params: Must contain 'contract_address'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "contract_address" not in params:
            raise ValidationError(
                message="Missing required parameter: contract_address",
                details={"required_params": ["contract_address"]},
                suggestions=[
                    "Provide 'contract_address' parameter",
                    "Example: {'contract_address': 'secret1...'}",
                ],
            )

        # Validate contract address
        validate_address(params["contract_address"])

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get contract info.

        Args:
            params: Parameters including contract_address

        Returns:
            Contract information
        """
        contract_address = params["contract_address"]

        try:
            # Query contract info using client pool
            with self.context.client_pool.get_client() as client:
                info_response = await client.wasm.contract_info(contract_address)

                contract_info = info_response.get("contract_info", {})

                return {
                    "contract_address": contract_address,
                    "contract_info": contract_info,
                    "message": f"Contract {contract_address} retrieved successfully",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get contract info: {str(e)}",
                details={"contract_address": contract_address, "error": str(e)},
                suggestions=[
                    "Check that the contract address is correct",
                    "Verify the contract exists",
                    "Verify network connectivity",
                ],
            )


class GetContractHistoryTool(BaseTool):
    """Get contract history.

    Query the history of a contract (init, migrate events).
    """

    @property
    def name(self) -> str:
        return "get_contract_history"

    @property
    def description(self) -> str:
        return (
            "Get the history of a contract. "
            "Returns all init and migrate events for the contract."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTRACTS

    @property
    def requires_wallet(self) -> bool:
        return False  # Read-only query

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate get contract history parameters.

        Args:
            params: Must contain 'contract_address'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "contract_address" not in params:
            raise ValidationError(
                message="Missing required parameter: contract_address",
                details={"required_params": ["contract_address"]},
                suggestions=[
                    "Provide 'contract_address' parameter",
                    "Example: {'contract_address': 'secret1...'}",
                ],
            )

        # Validate contract address
        validate_address(params["contract_address"])

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get contract history.

        Args:
            params: Parameters including contract_address

        Returns:
            Contract history
        """
        contract_address = params["contract_address"]

        try:
            # Query contract history using client pool
            with self.context.client_pool.get_client() as client:
                history_response = await client.wasm.contract_history(contract_address)

                entries = history_response.get("entries", [])
                pagination = history_response.get("pagination", {})

                return {
                    "contract_address": contract_address,
                    "entries": entries,
                    "count": len(entries),
                    "pagination": pagination,
                    "message": f"Retrieved {len(entries)} history entry/entries for {contract_address}",
                }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to get contract history: {str(e)}",
                details={"contract_address": contract_address, "error": str(e)},
                suggestions=[
                    "Check that the contract address is correct",
                    "Verify the contract exists",
                    "Verify network connectivity",
                ],
            )


class MigrateContractTool(BaseTool):
    """Migrate contract.

    Migrate a contract to new code.
    """

    @property
    def name(self) -> str:
        return "migrate_contract"

    @property
    def description(self) -> str:
        return (
            "Migrate a contract to new code. "
            "Requires active wallet and admin permissions."
        )

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTRACTS

    @property
    def requires_wallet(self) -> bool:
        return True  # Requires wallet to sign transaction

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate migrate contract parameters.

        Args:
            params: Must contain 'contract_address', 'new_code_id', 'migrate_msg'

        Raises:
            ValidationError: If parameters are invalid
        """
        if "contract_address" not in params:
            raise ValidationError(
                message="Missing required parameter: contract_address",
                details={
                    "required_params": [
                        "contract_address",
                        "new_code_id",
                        "migrate_msg",
                    ]
                },
                suggestions=[
                    "Provide 'contract_address' parameter",
                    "Example: {'contract_address': 'secret1...', 'new_code_id': '2', 'migrate_msg': {}}",
                ],
            )

        if "new_code_id" not in params:
            raise ValidationError(
                message="Missing required parameter: new_code_id",
                details={
                    "required_params": [
                        "contract_address",
                        "new_code_id",
                        "migrate_msg",
                    ]
                },
                suggestions=[
                    "Provide 'new_code_id' parameter",
                    "Example: {'contract_address': 'secret1...', 'new_code_id': '2', 'migrate_msg': {}}",
                ],
            )

        if "migrate_msg" not in params:
            raise ValidationError(
                message="Missing required parameter: migrate_msg",
                details={
                    "required_params": [
                        "contract_address",
                        "new_code_id",
                        "migrate_msg",
                    ]
                },
                suggestions=[
                    "Provide 'migrate_msg' parameter",
                    "Example: {'contract_address': 'secret1...', 'new_code_id': '2', 'migrate_msg': {}}",
                ],
            )

        # Validate contract address
        validate_address(params["contract_address"])

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute migrate contract.

        Args:
            params: Parameters including contract_address, new_code_id, migrate_msg

        Returns:
            Transaction result
        """
        contract_address = params["contract_address"]
        new_code_id = int(params["new_code_id"])
        migrate_msg = params["migrate_msg"]

        # Get active wallet
        wallet_info = self.context.session.get_wallet()
        if not wallet_info:
            raise WalletError(
                message="No active wallet set",
                details={},
                suggestions=["Load a wallet using load_wallet"],
            )

        wallet_name = wallet_info.wallet_id
        sender = wallet_info.address

        try:
            # Create signing client
            signing_client = await create_signing_client(
                wallet_name, str(self.context.network.value)
            )

            # Migrate contract
            result = await signing_client.migrate(
                contract_address=contract_address,
                new_code_id=new_code_id,
                migrate_msg=migrate_msg,
            )

            return {
                "sender": sender,
                "contract_address": contract_address,
                "new_code_id": new_code_id,
                "txhash": result.get("txhash"),
                "message": f"Successfully migrated contract {contract_address} to code ID {new_code_id}",
            }

        except Exception as e:
            raise NetworkError(
                message=f"Failed to migrate contract: {str(e)}",
                details={
                    "sender": sender,
                    "contract_address": contract_address,
                    "new_code_id": new_code_id,
                    "error": str(e),
                },
                suggestions=[
                    "Check that you are the contract admin",
                    "Verify the new code ID exists",
                    "Verify the migrate_msg format is correct",
                    "Verify network connectivity",
                ],
            )
