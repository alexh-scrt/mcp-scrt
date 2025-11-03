# Claude Code Command Reference - Secret Network MCP Server

**Quick Copy-Paste Commands for Implementation**

---

## 📋 Table of Contents

- [Project Initialization](#project-initialization)
- [Phase 1: Foundation](#phase-1-foundation)
- [Phase 2: Core Tools](#phase-2-core-tools)
- [Phase 3: Advanced Tools](#phase-3-advanced-tools)
- [Phase 4: Integration](#phase-4-integration)
- [Phase 5: Testing](#phase-5-testing)
- [Phase 6: Deployment](#phase-6-deployment)

---

## Project Initialization

### Command 1: Complete Project Setup
```
Initialize a Python MCP server project for Secret Network blockchain with this exact structure:

secret-mcp-server/
├── src/mcp_scrt/{core,sdk,tools,resources,prompts,utils}/
├── tests/{unit,integration,e2e,fixtures}/
├── docs/{tools,examples}/
├── scripts/
└── examples/

Create these files:
1. pyproject.toml with:
   - Python 3.11+ requirement
   - Dependencies: secret-sdk>=1.8.2, fastmcp, pydantic>=2.0, python-dotenv, aiohttp>=3.9, cryptography>=41.0, cachetools>=5.3, tenacity>=8.2, structlog>=23.1
   - Dev dependencies: pytest, pytest-asyncio, pytest-cov, pytest-mock, black, ruff, mypy, pre-commit
   - Entry point: secret-mcp = "mcp_scrt.__main__:main"

2. .env.example with all config options from the implementation plan

3. .gitignore for Python project (venv/, __pycache__/, .env, *.log, etc.)

4. README.md with project overview, installation, and usage

5. LICENSE (MIT)

6. .pre-commit-config.yaml with black, ruff, mypy hooks

7. All __init__.py files in package directories

Initialize git repository and make initial commit.
```

---

## Phase 1: Foundation

### Command 2: Type Definitions
```
Create src/mcp_scrt/types.py with complete type definitions:

1. NetworkType enum: MAINNET, TESTNET, CUSTOM
2. ToolCategory enum: NETWORK, WALLET, BANK, STAKING, REWARDS, GOVERNANCE, CONTRACTS, IBC, TRANSACTIONS, BLOCKCHAIN, ACCOUNTS
3. NetworkConfig dataclass: network_type, url, chain_id, gas_prices="0.25uscrt", gas_adjustment=1.0
4. WalletInfo dataclass: wallet_id, address, account=0, index=0
5. ToolRequest model (Pydantic): tool_name, parameters, request_id
6. ToolResponse model: success, data, error, metadata
7. ErrorResponse model: code, message, details, suggestions
8. CacheEntry model: key, value, timestamp, ttl
9. TransactionResult dataclass: txhash, success, height, gas_used, gas_wanted, raw_log, events

Use proper type hints (from typing import Any, Dict, List, Optional, Union).
Add docstrings to all classes.
Follow Python dataclass and Pydantic best practices.
```

### Command 3: Constants
```
Create src/mcp_scrt/constants.py with all constants from the implementation plan:

Network endpoints:
- MAINNET_URL = "https://secret-4.api.trivium.network:1317"
- TESTNET_URL = "http://testnet.securesecrets.org:1317"
- MAINNET_CHAIN_ID = "secret-4"
- TESTNET_CHAIN_ID = "pulsar-2"

GAS_LIMITS dict: upload=1000000, init=500000, exec=200000, send=80000, default=200000
CACHE_TTL dict: validators=300, balances=30, contracts=600, blocks=10, accounts=60, tx_results=3600

Security: DEFAULT_SPENDING_LIMIT=10000000, CONFIRMATION_THRESHOLD=1000000
Retry: MAX_RETRIES=3, RETRY_BACKOFF_BASE=2, RETRY_BACKOFF_MAX=30
Connection: MAX_CONNECTIONS=10, IDLE_TIMEOUT=300, CONNECTION_KEEPALIVE=True

Validation patterns for addresses (regex)
NATIVE_DENOM = "uscrt", NATIVE_DENOM_DECIMALS = 6
TOOL_CATEGORIES list

Add type hints and docstrings.
```

### Command 4: Configuration
```
Create src/mcp_scrt/config.py with Settings management:

Settings class (Pydantic BaseSettings):
- Load from environment variables
- All network settings (mainnet/testnet URLs and chain IDs, custom network support)
- Gas configuration (default_gas_price, gas_adjustment)
- Cache TTL for each data type
- Security settings (spending_limit_uscrt, require_confirmation_above_uscrt)
- Logging (log_level, log_format)
- Connection pool settings
- Retry configuration

Methods:
- get_network_url() -> str: returns URL based on current network
- get_chain_id() -> str: returns chain ID based on current network

Global functions:
- get_settings() -> Settings: singleton pattern
- reload_settings() -> Settings: reload from environment

Use pydantic_settings.BaseSettings.
Support .env file loading with python-dotenv.
Validate all settings with Pydantic validators.
```

### Command 5: Error Classes
```
Create src/mcp_scrt/utils/errors.py with exception hierarchy:

Base: SecretMCPError(Exception)
- __init__(message, code="UNKNOWN_ERROR", details=None, suggestions=None)
- to_dict() method for JSON serialization

Derived exceptions:
- NetworkError(code="NETWORK_ERROR")
- ValidationError(code="VALIDATION_ERROR")
- AuthenticationError(code="AUTHENTICATION_ERROR")
- WalletError(code="WALLET_ERROR")
- TransactionError(code="TRANSACTION_ERROR")
- InsufficientFundsError(TransactionError): special init with required/available amounts
- ContractError(code="CONTRACT_ERROR")
- CacheError(code="CACHE_ERROR")
- ConfigurationError(code="CONFIGURATION_ERROR")

Each exception should have helpful error messages and suggestions.
Add type hints and docstrings.
```

### Command 6: Logging Setup
```
Create src/mcp_scrt/utils/logging.py with structured logging:

Use structlog for structured logging:
- Configure JSON and text formatters based on LOG_FORMAT env var
- Set log level from LOG_LEVEL env var
- Add context processors for timestamps, log levels, logger names
- Add request_id tracking in context
- Configure standard library logging integration

Functions:
- setup_logging() -> None: initialize logging configuration
- get_logger(name: str) -> BoundLogger: get logger instance with name

Follow structlog best practices.
Support both JSON (for production) and colored text (for development) output.
```

### Command 7: Retry Logic
```
Create src/mcp_scrt/utils/retry.py with retry decorator:

Use tenacity library:
- retry_with_backoff decorator
- Exponential backoff: wait_exponential(multiplier=RETRY_BACKOFF_BASE, max=RETRY_BACKOFF_MAX)
- Max attempts: stop_after_attempt(MAX_RETRIES)
- Retry on specific exceptions: NetworkError, aiohttp.ClientError, asyncio.TimeoutError
- Log retry attempts with structlog
- Support both sync and async functions

Decorator signature: @retry_with_backoff(max_attempts=None, backoff_base=None)
Parameters override defaults from constants.

Add comprehensive docstring with examples.
```

### Command 8: Session Manager
```
Create src/mcp_scrt/core/session.py with SessionManager class:

SessionManager manages application state:

State storage:
- _network: NetworkType
- _active_wallet_id: Optional[str]
- _wallets: Dict[str, WalletInfo]
- _metadata: Dict[str, Any]
- _lock: asyncio.Lock for thread safety

Methods:
- initialize() -> None: initialize session
- reset() -> None: reset to clean state
- is_initialized() -> bool
- set_network(network: NetworkType) -> None
- get_network() -> NetworkType
- add_wallet(wallet_info: WalletInfo) -> None
- remove_wallet(wallet_id: str) -> None: secure cleanup
- set_active_wallet(wallet_id: str) -> None
- get_active_wallet() -> Optional[WalletInfo]
- list_wallets() -> List[WalletInfo]
- get_wallet(wallet_id: str) -> Optional[WalletInfo]
- get_state() -> Dict[str, Any]: serialize state
- set_metadata(key: str, value: Any) -> None
- get_metadata(key: str) -> Optional[Any]

All methods should be thread-safe using asyncio.Lock.
Raise appropriate errors (WalletError, etc.).
Add logging for state changes.
Add comprehensive docstrings.
```

### Command 9: Security Manager
```
Create src/mcp_scrt/core/security.py with SecurityManager class:

SecurityManager handles encryption and validation:

Use cryptography.fernet for key encryption:
- Generate encryption key on init (stored in memory only)
- Never persist keys to disk

Methods:
- encrypt_key(key_data: bytes) -> bytes: encrypt private key
- decrypt_key(encrypted_data: bytes) -> bytes: decrypt private key
- validate_mnemonic(mnemonic: str) -> bool: BIP39 validation
- validate_address(address: str, prefix: str = "secret") -> bool: Bech32 validation
- validate_amount(amount: str) -> bool: numeric and positive validation
- check_spending_limit(amount: int) -> bool: compare against limit
- requires_confirmation(amount: int) -> bool: check if confirmation needed
- secure_wipe(data: Any) -> None: securely clear sensitive data from memory

Use regex patterns from constants for address validation.
Log security events (without sensitive data).
Raise ValidationError for invalid inputs with helpful suggestions.
Add comprehensive docstrings.
```

### Command 10: Cache Manager
```
Create src/mcp_scrt/core/cache.py with CacheManager class:

CacheManager provides TTL-based caching:

Use cachetools.TTLCache:
- Multiple caches with different TTLs per data type
- Thread-safe with locks

Cache types (from CACHE_TTL constant):
- validators_cache: TTL 300s
- balances_cache: TTL 30s
- contracts_cache: TTL 600s
- blocks_cache: TTL 10s
- accounts_cache: TTL 60s
- tx_results_cache: TTL 3600s

Methods:
- get(cache_type: str, key: str) -> Optional[Any]
- set(cache_type: str, key: str, value: Any) -> None
- delete(cache_type: str, key: str) -> None
- clear(cache_type: str = None) -> None: clear specific or all caches
- invalidate_on_transaction(address: str) -> None: invalidate balance caches
- get_stats() -> Dict[str, Any]: cache statistics (hits, misses, size)
- get_or_fetch(cache_type: str, key: str, fetch_fn: Callable) -> Any: cache pattern

Use proper type hints including Callable.
Thread-safe implementation.
Add logging for cache operations.
Add comprehensive docstrings.
```

### Command 11: Input Validator
```
Create src/mcp_scrt/core/validation.py with InputValidator class:

InputValidator validates all user inputs:

Methods:
- validate_address(address: str, address_type: str = "account") -> None
  Types: "account" (secret1...), "validator" (secretvaloper1...), "contract" (secret1...)
  Use ADDRESS_PATTERN, VALIDATOR_PATTERN, CONTRACT_PATTERN from constants
  Raise ValidationError with suggestions if invalid

- validate_amount(amount: Union[str, int], min_amount: int = 1) -> int
  Convert to int, check positive and >= min_amount
  Raise ValidationError with suggestions

- validate_denom(denom: str) -> None
  Check valid denomination format
  Raise ValidationError

- validate_gas_limit(gas: int) -> None
  Check reasonable gas limit (>0, <10000000)
  Raise ValidationError

- validate_memo(memo: Optional[str], max_length: int = 256) -> None
  Check memo length if provided
  Raise ValidationError

- validate_contract_message(msg: Dict[str, Any]) -> None
  Check msg is valid JSON-serializable dict
  Raise ValidationError

- validate_transaction_params(params: Dict[str, Any]) -> None
  Validate all transaction parameters
  Raise ValidationError with specific field errors

Use regex patterns from constants.
Provide helpful error messages with suggestions.
Add comprehensive docstrings with examples.
```

### Command 12: SDK Client Pool
```
Create src/mcp_scrt/sdk/client.py with ClientPool class:

ClientPool manages LCD client connections to Secret Network:

Import: from secret_sdk.client.lcd import LCDClient, AsyncLCDClient
Import: from secret_sdk.core import Coins

State:
- _clients: Dict[str, LCDClient] (keyed by network type)
- _async_clients: Dict[str, AsyncLCDClient]
- _lock: asyncio.Lock
- settings: Settings

Methods:
- get_client(network: Optional[NetworkType] = None) -> LCDClient
  Get or create sync client for network
  Default to settings.secret_network
  Create LCDClient with url, chain_id, gas_prices, gas_adjustment

- get_async_client(network: Optional[NetworkType] = None) -> AsyncLCDClient
  Get or create async client for network
  Thread-safe with lock

- _get_network_config(network: NetworkType) -> NetworkConfig
  Helper to get NetworkConfig for any network type
  Raise NetworkError if configuration invalid

- close_all() -> None (async)
  Close all async client sessions
  Clear async_clients dict

- __del__(): cleanup sync clients

Global singleton:
- get_client_pool() -> ClientPool

Use secret-sdk-python LCDClient and AsyncLCDClient.
Add logging for client creation and closure.
Handle network errors gracefully.
Add comprehensive docstrings.
```

### Command 13: SDK Wallet Manager
```
Create src/mcp_scrt/sdk/wallet.py with WalletManager class:

WalletManager handles wallet operations:

Import: from secret_sdk.key.mnemonic import MnemonicKey
Import: from secret_sdk.client.lcd import Wallet

Dependencies: SecurityManager, ClientPool

Methods:
- create_wallet(client_pool: ClientPool, network: NetworkType) -> Tuple[MnemonicKey, str, str]
  Generate new 24-word mnemonic
  Create MnemonicKey
  Derive address (key.acc_address)
  Return: (key, address, mnemonic)

- import_wallet(mnemonic: str, account: int = 0, index: int = 0) -> Tuple[MnemonicKey, str]
  Validate mnemonic with SecurityManager
  Create MnemonicKey(mnemonic, account, index)
  Derive address
  Return: (key, address)

- get_wallet(client: LCDClient, key: MnemonicKey) -> Wallet
  Create Wallet instance: client.wallet(key)
  Return configured Wallet for transactions

- wallet_to_info(wallet_id: str, key: MnemonicKey, account: int, index: int) -> WalletInfo
  Convert MnemonicKey to WalletInfo dataclass
  Return: WalletInfo(wallet_id, key.acc_address, account, index)

Handle mnemonic validation errors.
Add logging (without logging keys!).
Add comprehensive docstrings.
```

### Command 14: SDK Transaction Builder
```
Create src/mcp_scrt/sdk/transaction.py with TransactionBuilder class:

TransactionBuilder builds and broadcasts transactions:

Import: from secret_sdk.client.lcd import Wallet
Import: from secret_sdk.core.tx import Tx

Methods:
- build_and_sign(wallet: Wallet, msgs: List[Msg], memo: str = "") -> Tx
  Build transaction with messages
  Sign with wallet
  Return signed Tx

- estimate_gas(wallet: Wallet, msgs: List[Msg]) -> int
  Simulate transaction
  Return gas estimate

- simulate(wallet: Wallet, msgs: List[Msg]) -> Dict[str, Any]
  Dry-run transaction
  Return simulation result

- broadcast(wallet: Wallet, tx: Tx) -> TransactionResult
  Broadcast signed transaction
  Wait for confirmation
  Parse result
  Return: TransactionResult

- build_and_broadcast(wallet: Wallet, msgs: List[Msg], memo: str = "") -> TransactionResult
  Convenience method: build, sign, and broadcast
  Return: TransactionResult

- parse_tx_result(tx_response: Any) -> TransactionResult
  Convert SDK tx response to TransactionResult
  Extract: txhash, success, height, gas_used, events
  Return: TransactionResult

Handle all transaction errors.
Add retry logic for broadcasts.
Add comprehensive logging.
Add comprehensive docstrings.
```

### Command 15: SDK Encryption Utils
```
Create src/mcp_scrt/sdk/encryption.py with contract encryption utilities:

Import: from secret_sdk.util import encrypt_utils

Functions:
- encrypt_contract_message(contract_address: str, code_hash: str, msg: Dict[str, Any]) -> bytes
  Encrypt execute message for Secret contract
  Use encrypt_utils from SDK
  Return encrypted bytes

- decrypt_contract_response(response: bytes) -> Dict[str, Any]
  Decrypt query response from Secret contract
  Parse JSON from decrypted bytes
  Return parsed dict

- get_code_hash(client: LCDClient, contract_address: str) -> str
  Get contract code hash for encryption
  Query via client.wasm
  Cache result
  Return code hash

Handle encryption/decryption errors.
Add logging (without logging sensitive data).
Add comprehensive docstrings with examples.
```

### Command 16: Foundation Tests
```
Create comprehensive unit tests for foundation components:

1. tests/conftest.py:
   - mock_settings fixture
   - mock_client fixture
   - mock_wallet fixture
   - mock_session_manager fixture
   - test_mnemonic fixture (valid 24-word mnemonic for testing)

2. tests/unit/test_config.py:
   - Test Settings loading
   - Test get_network_url() for all network types
   - Test get_chain_id()
   - Test environment variable overrides

3. tests/unit/test_types.py:
   - Test all dataclasses and enums
   - Test Pydantic model validation
   - Test to_dict() methods

4. tests/unit/test_errors.py:
   - Test all exception classes
   - Test to_dict() serialization
   - Test error messages and suggestions

5. tests/unit/test_session.py:
   - Test session initialization
   - Test wallet add/remove/set active
   - Test network switching
   - Test state serialization
   - Test thread safety

6. tests/unit/test_security.py:
   - Test key encryption/decryption
   - Test mnemonic validation
   - Test address validation (all types)
   - Test amount validation
   - Test spending limit checks
   - Mock cryptography operations

7. tests/unit/test_cache.py:
   - Test cache set/get/delete
   - Test TTL expiration
   - Test get_or_fetch pattern
   - Test cache invalidation
   - Test statistics

8. tests/unit/test_validation.py:
   - Test all validation methods
   - Test error cases with helpful messages
   - Test edge cases

Use pytest, pytest-mock, pytest-asyncio.
Mock all external dependencies (SDK, network calls).
Aim for >80% coverage.
Add docstrings to all test functions.
```

---

## Phase 2: Core Tools

### Command 17: Base Tool Handler
```
Create src/mcp_scrt/tools/base.py with BaseToolHandler abstract class:

BaseToolHandler is the abstract base for all tools:

Import: from abc import ABC, abstractmethod
Import: from typing import Any, Dict, Optional

Constructor dependencies:
- session_manager: SessionManager
- client_pool: ClientPool
- cache_manager: CacheManager
- security_manager: SecurityManager
- validator: InputValidator

Abstract methods:
- execute(**kwargs) -> ToolResponse: implement in subclasses

Provided methods:
- validate_input(params: Dict[str, Any]) -> None: validate parameters
- format_output(data: Any, success: bool = True) -> ToolResponse: format response
- handle_error(error: Exception) -> ToolResponse: convert exception to response
- get_client() -> LCDClient: get client from pool
- get_active_wallet() -> WalletInfo: get active wallet, raise if none
- requires_wallet() -> None: check active wallet exists

Decorators:
- @require_wallet: decorator that calls requires_wallet()
- @require_network: decorator that checks network configured
- @log_execution: decorator that logs tool execution

Add comprehensive error handling.
Add logging for all operations.
Add comprehensive docstrings.
```

### Command 18: Network Tools
```
Create src/mcp_scrt/tools/network.py with 4 network tools (all extend BaseToolHandler):

1. ConfigureNetworkTool:
   execute(network: str, custom_url: Optional[str] = None, custom_chain_id: Optional[str] = None) -> ToolResponse
   - Validate network is valid NetworkType
   - If custom, require custom_url and custom_chain_id
   - Update session with session_manager.set_network()
   - Test connection to new network
   - Return: {network, url, chain_id, status}

2. GetNetworkInfoTool:
   execute() -> ToolResponse
   - Get current network from session
   - Get node info via client.tendermint.node_info()
   - Get latest block height
   - Return: {network, chain_id, url, block_height, node_version}

3. GetGasPricesTool:
   execute() -> ToolResponse
   - Get current network
   - Get gas prices from config
   - Return: {gas_price, denom, recommendation}

4. HealthCheckTool:
   execute() -> ToolResponse
   - Test connection to network
   - Measure latency
   - Get latest block
   - Return: {connected, latency_ms, block_height, status}

Use retry decorator for network calls.
Add comprehensive error handling.
Cache appropriate data.
Add logging.
Add docstrings.
```

### Command 19: Wallet Tools
```
Create src/mcp_scrt/tools/wallet.py with 6 wallet tools (all extend BaseToolHandler):

1. CreateWalletTool:
   execute(save_as: str) -> ToolResponse
   - Call wallet_manager.create_wallet()
   - Encrypt mnemonic with security_manager
   - Store in session via session_manager.add_wallet()
   - Return: {wallet_id, address, mnemonic, warning: "Save mnemonic securely!"}

2. ImportWalletTool:
   execute(mnemonic: str, save_as: str, account: int = 0, index: int = 0) -> ToolResponse
   - Validate mnemonic with security_manager
   - Import via wallet_manager.import_wallet()
   - Encrypt and store in session
   - Return: {wallet_id, address}

3. SetActiveWalletTool:
   execute(wallet_id: str) -> ToolResponse
   - Verify wallet exists in session
   - session_manager.set_active_wallet(wallet_id)
   - Return: {wallet_id, address, active: true}

4. GetActiveWalletTool:
   execute() -> ToolResponse
   - Get active wallet from session
   - Get balance from cache or client
   - Return: {wallet_id, address, balance}

5. ListWalletsTool:
   execute() -> ToolResponse
   - session_manager.list_wallets()
   - Mark active wallet
   - Return: {wallets: [{wallet_id, address, active}]}

6. RemoveWalletTool:
   execute(wallet_id: str) -> ToolResponse
   - Verify not active wallet
   - security_manager.secure_wipe() on keys
   - session_manager.remove_wallet()
   - Return: {success, wallet_id, message}

Never log sensitive data (keys, mnemonics).
Add comprehensive error handling.
Add security warnings in responses.
Add docstrings.
```

### Command 20: Bank Tools  
```
Create src/mcp_scrt/tools/bank.py with 5 bank tools (all extend BaseToolHandler):

1. GetBalanceTool:
   @require_network
   execute(address: Optional[str] = None, denom: Optional[str] = None) -> ToolResponse
   - Default address to active wallet
   - Validate address
   - Check cache first
   - Query client.bank.balance(address)
   - Filter by denom if provided
   - Cache result (30s TTL)
   - Return: {address, balances: [{denom, amount}]}

2. SendTokensTool:
   @require_wallet
   @require_network
   execute(recipient: str, amount: str, denom: str = "uscrt", memo: str = "") -> ToolResponse
   - Validate recipient address
   - Validate and convert amount to int
   - Check balance sufficient
   - Check spending limit
   - Check if confirmation required
   - Create MsgSend
   - Build and broadcast transaction
   - Invalidate balance cache
   - Return: {txhash, success, amount_sent}

3. MultiSendTool:
   @require_wallet
   @require_network
   execute(recipients: List[Dict], memo: str = "") -> ToolResponse
   - Validate all recipients
   - Calculate total amount
   - Check balance sufficient
   - Create MsgMultiSend
   - Broadcast transaction
   - Return: {txhash, success, total_amount, recipient_count}

4. GetTotalSupplyTool:
   execute(denom: Optional[str] = None) -> ToolResponse
   - Query client.bank.total()
   - Filter by denom if provided
   - Return: {supply: [{denom, amount}]}

5. GetDenomMetadataTool:
   execute(denom: str) -> ToolResponse
   - Query client.bank.denom_metadata(denom)
   - Return: {denom, description, base, display, decimals}

Use secret-sdk-python bank module and MsgSend.
Add retry logic for queries.
Cache where appropriate.
Add comprehensive error handling.
Add logging for transactions.
Add docstrings.
```

### Command 21: Transaction Tools
```
Create src/mcp_scrt/tools/transactions.py with 5 transaction tools:

1. GetTransactionTool:
   execute(tx_hash: str) -> ToolResponse
   - Validate tx_hash format
   - Check cache first (1 hour TTL)
   - Query client.tx.tx_info(tx_hash)
   - Cache result
   - Return: {txhash, height, success, gas_used, timestamp, events, raw_log}

2. SearchTransactionsTool:
   execute(events: List[Tuple[str, str]], limit: int = 100, order_by: str = "desc") -> ToolResponse
   - Validate events format
   - Query client.tx.search(events, limit=limit)
   - Return: {transactions: [tx details], count}

3. EstimateGasTool:
   execute(messages: List[Dict]) -> ToolResponse
   - Parse message dicts to Msg objects
   - Use transaction_builder.estimate_gas()
   - Return: {estimated_gas, recommended_gas_limit}

4. SimulateTransactionTool:
   @require_wallet
   execute(messages: List[Dict]) -> ToolResponse
   - Parse messages
   - Use transaction_builder.simulate()
   - Return: {success, gas_used, events, result}

5. GetTransactionStatusTool:
   execute(tx_hash: str) -> ToolResponse
   - Get transaction info
   - Parse success/failure
   - Extract error message if failed
   - Return: {txhash, success, error_message, events}

Use secret-sdk-python tx module.
Add retry logic.
Cache transaction results.
Add docstrings.
```

### Command 22: Blockchain Tools
```
Create src/mcp_scrt/tools/blockchain.py with 5 blockchain query tools:

1. GetBlockTool:
   execute(height: Optional[int] = None) -> ToolResponse
   - Query client.tendermint.block_info(height)
   - Cache result (10s TTL)
   - Return: {height, hash, time, proposer, tx_count, transactions}

2. GetLatestBlockTool:
   execute() -> ToolResponse
   - Query client.tendermint.block_info()
   - Cache result (10s TTL)
   - Return: {height, hash, time, proposer, tx_count}

3. GetBlockByHashTool:
   execute(block_hash: str) -> ToolResponse
   - Search for block by hash
   - Return: {height, hash, time, proposer, tx_count}

4. GetNodeInfoTool:
   execute() -> ToolResponse
   - Query client.tendermint.node_info()
   - Return: {node_id, network, version, moniker, protocol_version}

5. GetSyncingStatusTool:
   execute() -> ToolResponse
   - Query client.tendermint.syncing()
   - Return: {syncing, catching_up, latest_block_height}

Use secret-sdk-python tendermint module.
Cache block data appropriately.
Add retry logic.
Add docstrings.
```

### Command 23: Account Tools
```
Create src/mcp_scrt/tools/accounts.py with 3 account tools:

1. GetAccountTool:
   execute(address: Optional[str] = None) -> ToolResponse
   - Default to active wallet address
   - Validate address
   - Check cache (60s TTL)
   - Query client.auth.account_info(address)
   - Cache result
   - Return: {address, account_number, sequence, pubkey, type}

2. GetAccountTransactionsTool:
   execute(address: Optional[str] = None, limit: int = 100, order_by: str = "desc") -> ToolResponse
   - Default to active wallet
   - Search transactions by sender and recipient
   - Combine results
   - Sort by height
   - Return: {address, transactions: [tx details], total_count}

3. GetAccountTxCountTool:
   execute(address: Optional[str] = None) -> ToolResponse
   - Get all transactions (with high limit)
   - Count results
   - Return: {address, transaction_count}

Use secret-sdk-python auth module.
Cache account info.
Add pagination support.
Add docstrings.
```

### Command 24: Core Tools Tests
```
Create unit tests for Phase 2 tools:

1. tests/unit/test_tools/test_base.py:
   - Test BaseToolHandler methods
   - Test decorators (require_wallet, require_network)
   - Test error handling
   - Test response formatting

2. tests/unit/test_tools/test_network.py:
   - Test all 4 network tools
   - Mock client.tendermint calls
   - Test network switching
   - Test error scenarios

3. tests/unit/test_tools/test_wallet.py:
   - Test all 6 wallet tools
   - Mock wallet_manager calls
   - Test wallet creation, import, management
   - Test mnemonic security
   - Test error scenarios

4. tests/unit/test_tools/test_bank.py:
   - Test all 5 bank tools
   - Mock client.bank calls
   - Test balance queries
   - Test token sends
   - Test validation errors

5. tests/unit/test_tools/test_transactions.py:
   - Test all 5 transaction tools
   - Mock client.tx calls
   - Test transaction queries
   - Test gas estimation

6. tests/unit/test_tools/test_blockchain.py:
   - Test all 5 blockchain tools
   - Mock client.tendermint calls
   - Test block queries

7. tests/unit/test_tools/test_accounts.py:
   - Test all 3 account tools
   - Mock client.auth calls
   - Test account queries

Mock all SDK calls.
Test success and error paths.
Test validation.
Test caching behavior.
Aim for >80% coverage per tool.
```

---

## Phase 3: Advanced Tools

### Command 25: Staking Tools
```
Create src/mcp_scrt/tools/staking.py with 8 staking tools:

1. GetValidatorsTool:
   execute(status: Optional[str] = None, limit: int = 100) -> ToolResponse
   - Query client.staking.validators(status=status)
   - Cache result (5 min TTL)
   - Return: {validators: [{operator_address, moniker, commission, voting_power, status}]}

2. GetValidatorTool:
   execute(validator_address: str) -> ToolResponse
   - Validate validator address
   - Query client.staking.validator(validator_address)
   - Return: {operator_address, moniker, commission, voting_power, status, details}

3. DelegateTool:
   @require_wallet
   execute(validator_address: str, amount: str, denom: str = "uscrt", memo: str = "") -> ToolResponse
   - Validate validator address and amount
   - Check balance
   - Create MsgDelegate
   - Broadcast transaction
   - Return: {txhash, success, delegated_amount, validator}

4. UndelegateTool:
   @require_wallet
   execute(validator_address: str, amount: str, denom: str = "uscrt", memo: str = "") -> ToolResponse
   - Create MsgUndelegate
   - Calculate unbonding time (21 days)
   - Broadcast transaction
   - Return: {txhash, success, undelegated_amount, completion_time}

5. RedelegateTool:
   @require_wallet
   execute(src_validator: str, dst_validator: str, amount: str, denom: str = "uscrt", memo: str = "") -> ToolResponse
   - Validate both validator addresses
   - Create MsgBeginRedelegate
   - Broadcast transaction
   - Return: {txhash, success, amount, from_validator, to_validator}

6. GetDelegationsTool:
   execute(delegator: Optional[str] = None, validator: Optional[str] = None) -> ToolResponse
   - Default delegator to active wallet
   - Query client.staking.delegations(delegator, validator)
   - Return: {delegations: [{validator, amount, shares}]}

7. GetUnbondingDelegationsTool:
   execute(delegator: Optional[str] = None) -> ToolResponse
   - Query client.staking.unbonding_delegations(delegator)
   - Return: {unbonding_delegations: [{validator, amount, completion_time}]}

8. GetRedelegationsTool:
   execute(delegator: Optional[str] = None) -> ToolResponse
   - Query client.staking.redelegations(delegator)
   - Return: {redelegations: [{src_validator, dst_validator, amount, completion_time}]}

Use secret-sdk-python staking module and MsgDelegate, MsgUndelegate, MsgBeginRedelegate.
Cache validator lists.
Add comprehensive error handling.
Add docstrings.
```

### Command 26: Rewards Tools
```
Create src/mcp_scrt/tools/rewards.py with 4 rewards tools:

1. GetRewardsTool:
   execute(delegator: Optional[str] = None, validator: Optional[str] = None) -> ToolResponse
   - Default delegator to active wallet
   - Query client.distribution.rewards(delegator, validator)
   - Return: {total_rewards, rewards_by_validator: [{validator, amount}]}

2. WithdrawRewardsTool:
   @require_wallet
   execute(validator_address: Optional[str] = None, memo: str = "") -> ToolResponse
   - If validator_address provided: withdraw from one validator
   - If None: withdraw from all validators
   - Create MsgWithdrawDelegatorReward (one or multiple)
   - Broadcast transaction
   - Return: {txhash, success, withdrawn_amount, validators: []}

3. SetWithdrawAddressTool:
   @require_wallet
   execute(withdraw_address: str, memo: str = "") -> ToolResponse
   - Validate withdraw_address
   - Create MsgSetWithdrawAddress
   - Broadcast transaction
   - Return: {txhash, success, withdraw_address}

4. GetCommunityPoolTool:
   execute() -> ToolResponse
   - Query client.distribution.community_pool()
   - Return: {pool: [{denom, amount}]}

Use secret-sdk-python distribution module and MsgWithdrawDelegatorReward, MsgSetWithdrawAddress.
Add error handling.
Add docstrings.
```

### Command 27: Governance Tools
```
Create src/mcp_scrt/tools/governance.py with 6 governance tools:

1. GetProposalsTool:
   execute(status: Optional[str] = None, limit: int = 100) -> ToolResponse
   - Query client.gov.proposals(status=status)
   - Return: {proposals: [{id, title, status, submit_time, voting_end_time, yes_votes, no_votes}]}

2. GetProposalTool:
   execute(proposal_id: int) -> ToolResponse
   - Query client.gov.proposal(proposal_id)
   - Get votes and deposits
   - Return: {id, title, description, status, submit_time, deposit_end_time, voting_start_time, voting_end_time, final_tally, total_deposit}

3. SubmitProposalTool:
   @require_wallet
   execute(proposal_type: str, title: str, description: str, initial_deposit: str, proposal_content: Dict, memo: str = "") -> ToolResponse
   - Validate proposal parameters
   - Create MsgSubmitProposal
   - Broadcast transaction
   - Return: {txhash, success, proposal_id}

4. DepositProposalTool:
   @require_wallet
   execute(proposal_id: int, amount: str, denom: str = "uscrt", memo: str = "") -> ToolResponse
   - Create MsgDeposit
   - Broadcast transaction
   - Return: {txhash, success, proposal_id, deposited_amount}

5. VoteProposalTool:
   @require_wallet
   execute(proposal_id: int, option: str, memo: str = "") -> ToolResponse
   - Validate option (yes, no, abstain, no_with_veto)
   - Create MsgVote
   - Broadcast transaction
   - Return: {txhash, success, proposal_id, vote_option}

6. GetVoteTool:
   execute(proposal_id: int, voter: Optional[str] = None) -> ToolResponse
   - Default voter to active wallet
   - Query client.gov.vote(proposal_id, voter)
   - Return: {proposal_id, voter, option, vote_time}

Use secret-sdk-python gov module and MsgSubmitProposal, MsgDeposit, MsgVote.
Add validation for proposal types and vote options.
Add docstrings.
```

### Command 28: Smart Contract Tools
```
Create src/mcp_scrt/tools/contracts.py with 10 contract tools:

1. UploadContractTool:
   @require_wallet
   execute(wasm_file_path: str, source: Optional[str] = None, builder: Optional[str] = None, memo: str = "") -> ToolResponse
   - Read WASM file
   - Create MsgStoreCode
   - Broadcast transaction (high gas limit)
   - Extract code_id from events
   - Return: {txhash, success, code_id}

2. GetCodeInfoTool:
   execute(code_id: int) -> ToolResponse
   - Query client.wasm.code_info(code_id)
   - Return: {code_id, creator, checksum, permissions}

3. ListCodesTool:
   execute(limit: int = 100) -> ToolResponse
   - Query client.wasm.codes()
   - Return: {codes: [{code_id, creator, checksum}]}

4. InstantiateContractTool:
   @require_wallet
   execute(code_id: int, init_msg: Dict, label: str, funds: Optional[List[Dict]] = None, admin: Optional[str] = None, memo: str = "") -> ToolResponse
   - Validate init_msg
   - Create MsgInstantiateContract
   - Broadcast transaction
   - Extract contract_address from events
   - Return: {txhash, success, contract_address, label}

5. ExecuteContractTool:
   @require_wallet
   execute(contract_address: str, execute_msg: Dict, funds: Optional[List[Dict]] = None, memo: str = "") -> ToolResponse
   - Get code hash via encryption utils
   - Encrypt execute_msg
   - Create MsgExecuteContract
   - Broadcast transaction
   - Return: {txhash, success, contract_address}

6. QueryContractTool:
   execute(contract_address: str, query_msg: Dict) -> ToolResponse
   - Get code hash
   - Encrypt query_msg
   - Query client.wasm.contract_query()
   - Decrypt response
   - Return: {contract_address, query_result}

7. BatchExecuteContractsTool:
   @require_wallet
   execute(executions: List[Dict], memo: str = "") -> ToolResponse
   - For each execution: encrypt message
   - Create multiple MsgExecuteContract
   - Combine in one transaction
   - Broadcast
   - Return: {txhash, success, execution_count}

8. GetContractInfoTool:
   execute(contract_address: str) -> ToolResponse
   - Query client.wasm.contract_info(contract_address)
   - Cache result (10 min TTL)
   - Return: {address, code_id, creator, admin, label}

9. GetContractHistoryTool:
   execute(contract_address: str) -> ToolResponse
   - Query client.wasm.contract_history(contract_address)
   - Return: {contract_address, history: [{operation, code_id, updated}]}

10. MigrateContractTool:
    @require_wallet
    execute(contract_address: str, new_code_id: int, migrate_msg: Dict, memo: str = "") -> ToolResponse
    - Check admin permissions
    - Encrypt migrate_msg
    - Create MsgMigrateContract
    - Broadcast transaction
    - Return: {txhash, success, contract_address, new_code_id}

Use secret-sdk-python wasm module and encryption utils.
Use wallet.execute_tx() and wallet.multi_execute_tx() for convenience.
Add comprehensive error handling for contract errors.
Add logging (without sensitive data).
Add docstrings.
```

### Command 29: IBC Tools
```
Create src/mcp_scrt/tools/ibc.py with 4 IBC tools:

1. IBCTransferTool:
   @require_wallet
   execute(channel_id: str, recipient: str, amount: str, denom: str = "uscrt", timeout_height: Optional[int] = None, timeout_timestamp: Optional[int] = None, memo: str = "") -> ToolResponse
   - Validate channel_id and recipient
   - Calculate default timeout if not provided (10 minutes)
   - Create MsgTransfer
   - Broadcast transaction
   - Return: {txhash, success, amount, recipient, channel_id}

2. GetIBCChannelsTool:
   execute(connection_id: Optional[str] = None) -> ToolResponse
   - Query client.ibc.channels(connection_id)
   - Return: {channels: [{channel_id, port_id, connection_hops, state, counterparty}]}

3. GetIBCChannelTool:
   execute(channel_id: str, port_id: str = "transfer") -> ToolResponse
   - Query client.ibc.channel(port_id, channel_id)
   - Return: {channel_id, port_id, state, counterparty, connection_hops}

4. GetIBCDenomTraceTool:
   execute(hash: str) -> ToolResponse
   - Query client.ibc_transfer.denom_trace(hash)
   - Return: {hash, base_denom, path}

Use secret-sdk-python ibc and ibc_transfer modules and MsgTransfer.
Add timeout calculations.
Add docstrings.
```

### Command 30: Advanced Tools Tests
```
Create unit tests for Phase 3 tools:

1. tests/unit/test_tools/test_staking.py:
   - Test all 8 staking tools
   - Mock client.staking calls
   - Test delegation operations
   - Test validator queries

2. tests/unit/test_tools/test_rewards.py:
   - Test all 4 rewards tools
   - Mock client.distribution calls
   - Test reward queries and withdrawals

3. tests/unit/test_tools/test_governance.py:
   - Test all 6 governance tools
   - Mock client.gov calls
   - Test proposal operations
   - Test voting

4. tests/unit/test_tools/test_contracts.py:
   - Test all 10 contract tools
   - Mock client.wasm calls
   - Mock encryption/decryption
   - Test contract lifecycle
   - Test error scenarios

5. tests/unit/test_tools/test_ibc.py:
   - Test all 4 IBC tools
   - Mock client.ibc calls
   - Test IBC transfers

Mock all SDK calls and encryption.
Test success and error paths.
Test message construction.
Aim for >80% coverage.
```

---

## Phase 4: Integration

### Command 31: MCP Server Implementation
```
Create src/mcp_scrt/server.py - main MCP server:

Import FastMCP framework (adjust based on actual MCP library).
Import all tool classes from tools/ directory.
Import resource handlers from resources/ directory.
Import prompt templates from prompts/ directory.

Initialize components:
- session_manager = SessionManager()
- client_pool = get_client_pool()
- cache_manager = CacheManager()
- security_manager = SecurityManager()
- validator = InputValidator()
- wallet_manager = WalletManager()
- transaction_builder = TransactionBuilder()

Create MCP server instance.

Register all 70+ tools:
- Network tools (4)
- Wallet tools (6)
- Bank tools (5)
- Staking tools (8)
- Rewards tools (4)
- Governance tools (6)
- Contract tools (10)
- IBC tools (4)
- Transaction tools (5)
- Blockchain tools (5)
- Account tools (3)

Each tool registration:
- Tool name (e.g., "secret_get_balance")
- Tool description
- Parameter schema (JSON Schema)
- Handler function that instantiates tool class and calls execute()

Register resources:
- secret://session/state - session state
- secret://wallets/list - wallet list
- secret://network/config - network config
- secret://validators/top - top validators
- secret://contracts/recent - recent contracts

Register prompts:
- secret_network_guide - comprehensive guide
- secret_smart_contracts_guide - contract guide

Add health check endpoint.

Add graceful shutdown handler:
- Close all clients
- Clear sensitive data
- Log shutdown

Export run() function to start server.

Add comprehensive logging.
Add error handling middleware.
Add request/response logging.
```

### Command 32: CLI Entry Point
```
Create src/mcp_scrt/__main__.py:

Import: argparse, logging, sys
Import: server module
Import: get_settings, setup_logging

def main() -> int:
    """Main entry point."""
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Secret Network MCP Server")
    parser.add_argument("--network", choices=["mainnet", "testnet", "custom"], help="Network to connect to")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    parser.add_argument("--config", help="Path to config file")
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    # Load configuration
    settings = get_settings()
    if args.network:
        # Override network from CLI
        pass
    
    # Log startup info
    logger.info(
        "Starting Secret Network MCP Server",
        network=settings.secret_network,
        url=settings.get_network_url(),
        chain_id=settings.get_chain_id(),
    )
    
    # Run server
    try:
        server.run()
        return 0
    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down")
        return 0
    except Exception as e:
        logger.error("Fatal error", error=str(e), exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())

Add signal handlers for SIGTERM/SIGINT.
Add proper error handling.
Add startup banner with version info.
```

### Command 33: Resource Handlers
```
Create resource handlers in src/mcp_scrt/resources/:

1. session.py - SessionStateResource:
   - Provide current session state as JSON
   - Include: network, active_wallet, wallet_count, metadata
   - Update on state changes
   - URI: secret://session/state

2. wallets.py - WalletsListResource:
   - Provide list of session wallets
   - Include: wallet_id, address (no keys!)
   - Mark active wallet
   - URI: secret://wallets/list

3. network.py - NetworkConfigResource:
   - Provide current network configuration
   - Include: network_type, url, chain_id, gas_prices
   - Update on network change
   - URI: secret://network/config

4. validators.py - TopValidatorsResource:
   - Provide top validators by voting power
   - Cache for 5 minutes
   - Include: operator_address, moniker, voting_power, commission
   - URI: secret://validators/top

Each resource:
- Implements MCP resource protocol
- Returns JSON data
- Updates automatically on relevant changes
- Has proper error handling

Add docstrings.
```

### Command 34: Prompt Templates
```
Create prompt templates in src/mcp_scrt/prompts/:

1. guide.py - SecretNetworkGuidePrompt:
   """
   # Secret Network MCP Server Guide
   
   ## Overview
   This MCP server provides comprehensive access to Secret Network blockchain.
   
   ## Getting Started
   1. Configure network: secret_configure_network
   2. Create or import wallet: secret_create_wallet or secret_import_wallet
   3. Check balance: secret_get_balance
   
   ## Common Operations
   
   ### Token Transfers
   - Get balance: secret_get_balance(address?)
   - Send tokens: secret_send_tokens(recipient, amount, denom)
   - Multi-send: secret_multi_send(recipients, memo)
   
   ### Staking
   - List validators: secret_get_validators(status?, limit?)
   - Delegate: secret_delegate(validator_address, amount)
   - Check rewards: secret_get_rewards(delegator?)
   - Withdraw rewards: secret_withdraw_rewards(validator_address?)
   
   ### Smart Contracts
   - Query contract: secret_query_contract(contract_address, query_msg)
   - Execute contract: secret_execute_contract(contract_address, execute_msg, funds?)
   - All contract interactions are automatically encrypted
   
   ## Security Notes
   - Private keys are stored encrypted in memory only
   - Mnemonics must be saved securely by user
   - Large transactions require confirmation
   
   ## Error Handling
   - All errors include error codes and suggestions
   - Network errors automatically retry
   - Validation errors provide helpful messages
   """
   
2. contracts.py - SmartContractsGuidePrompt:
   """
   # Secret Smart Contracts Guide
   
   ## Contract Lifecycle
   1. Upload: secret_upload_contract(wasm_file_path)
   2. Instantiate: secret_instantiate_contract(code_id, init_msg, label)
   3. Execute: secret_execute_contract(contract_address, execute_msg)
   4. Query: secret_query_contract(contract_address, query_msg)
   
   ## Privacy Features
   - All contract messages are automatically encrypted
   - Query responses are automatically decrypted
   - Uses Secret Network's encryption utils
   
   ## Examples
   [Include contract interaction examples]
   
   ## Best Practices
   - Always test on testnet first
   - Verify code hash before interactions
   - Handle encrypted responses correctly
   """

Each prompt:
- Implements MCP prompt protocol
- Supports variables
- Provides clear examples
- Includes security warnings

Add comprehensive content.
```

---

## Phase 5: Testing

### Command 35: Integration Tests
```
Create integration tests in tests/integration/:

1. test_transfer_workflow.py:
   """Test complete token transfer workflow."""
   - Configure network (testnet)
   - Import test wallet
   - Check balance
   - Send tokens to another address
   - Verify transaction
   - Check new balance
   
2. test_staking_workflow.py:
   """Test staking lifecycle."""
   - Get validators
   - Delegate to validator
   - Check delegation
   - Query rewards
   - Withdraw rewards
   - Undelegate
   - Check unbonding

3. test_contract_workflow.py:
   """Test contract deployment and interaction."""
   - Upload contract (use test WASM)
   - Instantiate contract
   - Execute contract
   - Query contract
   - Verify encrypted communication

4. test_error_scenarios.py:
   """Test error handling."""
   - Test insufficient funds
   - Test invalid addresses
   - Test network errors
   - Test contract errors
   - Verify error messages

5. test_caching.py:
   """Test cache behavior."""
   - Query data (miss)
   - Query again (hit)
   - Wait for TTL expiry
   - Query again (miss)
   - Invalidate on transaction
   - Verify cache stats

Use pytest-asyncio for async tests.
Use testnet for real blockchain interactions.
Clean up test transactions.
Add proper fixtures for test wallets.
Add comprehensive assertions.
```

### Command 36: E2E Tests
```
Create E2E tests in tests/e2e/:

1. test_new_user_journey.py:
   """Test complete new user experience."""
   - Start server
   - Create new wallet
   - Save mnemonic (simulate)
   - Check balance (should be 0)
   - Get testnet tokens (external)
   - Check new balance
   - Send tokens to another address
   - Verify transaction successful

2. test_staking_journey.py:
   """Test complete staking experience."""
   - Import wallet with funds
   - List validators
   - Select validator (highest voting power)
   - Delegate 1 SCRT
   - Wait for rewards to accumulate
   - Check rewards
   - Withdraw rewards
   - Verify reward transaction

3. test_governance_journey.py:
   """Test governance participation."""
   - Get active proposals
   - Check proposal details
   - Vote on proposal
   - Verify vote recorded

Run on testnet.
Use real MCP server instance.
Test through MCP protocol.
Simulate user interactions.
Add timing tests.
Add comprehensive logging.
```

---

## Phase 6: Deployment

### Command 37: Dockerfile
```
Create Dockerfile:

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements
COPY pyproject.toml setup.py ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir -e .

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 mcpuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application
COPY --chown=mcpuser:mcpuser . .

# Switch to non-root user
USER mcpuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD secret-mcp --help || exit 1

# Entry point
ENTRYPOINT ["secret-mcp"]
CMD ["--network", "mainnet"]

Optimize for size and security.
Use multi-stage build.
Run as non-root user.
Add health check.
Add labels and metadata.
```

### Command 38: Docker Compose
```
Create docker-compose.yml:

version: '3.8'

services:
  secret-mcp:
    build: .
    image: secret-mcp-server:latest
    container_name: secret-mcp
    
    environment:
      - SECRET_NETWORK=${SECRET_NETWORK:-mainnet}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - LOG_FORMAT=${LOG_FORMAT:-json}
    
    env_file:
      - .env
    
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
    
    ports:
      - "8080:8080"
    
    restart: unless-stopped
    
    networks:
      - secret-mcp-network
    
    healthcheck:
      test: ["CMD", "secret-mcp", "--help"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  secret-mcp-network:
    driver: bridge

Include .env.example.
Add comments for configuration.
Support development and production profiles.
Add volume mounts for config and logs.
```

### Command 39: CI/CD Workflow
```
Create .github/workflows/ci.yml:

name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Lint with ruff
      run: ruff check src/
    
    - name: Format check with black
      run: black --check src/
    
    - name: Type check with mypy
      run: mypy src/
    
    - name: Run tests
      run: pytest -v --cov=mcp_scrt --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
  
  build:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t secret-mcp-server:test .
    
    - name: Test Docker image
      run: docker run --rm secret-mcp-server:test --help

Add badge to README.
Run on push and pull request.
Test multiple Python versions.
Upload coverage reports.
Build and test Docker image.
```

### Command 40: Release Workflow
```
Create .github/workflows/release.yml:

name: Release

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  release:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install build twine
        pip install -e ".[dev]"
    
    - name: Run tests
      run: pytest
    
    - name: Build package
      run: python -m build
    
    - name: Create GitHub Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        draft: false
        prerelease: false
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          username/secret-mcp-server:latest
          username/secret-mcp-server:${{ github.ref_name }}

Trigger on version tags.
Run full test suite.
Build Python package.
Create GitHub release.
Build and push Docker image.
Generate changelog.
```

---

## 🎉 Final Validation

### Command 41: Full Test Suite
```
Run complete test suite and validation:

# All unit tests
pytest tests/unit/ -v

# All integration tests (requires testnet)
pytest tests/integration/ -v

# All E2E tests
pytest tests/e2e/ -v

# Coverage report
pytest --cov=mcp_scrt --cov-report=html --cov-report=term

# Lint checks
ruff check src/
black --check src/
mypy src/

# Build documentation
mkdocs build

# Build Docker image
docker build -t secret-mcp-server:latest .

# Test Docker container
docker run --rm secret-mcp-server:latest --help

# Full integration test
docker-compose up -d
docker-compose logs -f
docker-compose down

Verify all tests pass.
Check coverage >80%.
Verify Docker builds successfully.
Test MCP server responds correctly.
```

---

## 📚 Documentation

### Command 42: Generate Documentation
```
Generate comprehensive documentation:

1. API documentation from docstrings
2. Tool reference (all 70+ tools)
3. Configuration guide
4. Deployment guide
5. Security guide
6. Examples for each tool category
7. Troubleshooting guide

Use mkdocs with material theme.
Auto-generate from source code docstrings.
Include architecture diagrams.
Add usage examples.
Publish to GitHub Pages.
```

---

**End of Command Reference**

These commands provide copy-paste instructions for Claude Code to implement every component of the Secret Network MCP Server. Follow the order, validate each phase, and maintain high code quality throughout.