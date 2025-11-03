# Secret Network MCP Server - Quick Start Guide

**For Claude Code Implementation**

---

## 🚀 Quick Start Commands

### Day 1: Project Initialization

```bash
# 1. Create project directory
mkdir secret-mcp-server && cd secret-mcp-server

# 2. Use Claude Code to initialize the entire project
claude-code "Initialize the Secret Network MCP Server project with the following:
1. Create complete directory structure as per implementation plan
2. Create pyproject.toml with all dependencies
3. Create .env.example with all configuration options
4. Create .gitignore for Python project
5. Create README.md with project overview
6. Initialize git repository"

# 3. Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install dependencies
pip install -e ".[dev]"

# 5. Set up pre-commit hooks
pre-commit install
```

---

## 📋 Phase-by-Phase Commands

### Phase 1: Foundation (Days 1-7)

#### Step 1.1: Core Infrastructure

```bash
claude-code "Create the following files for Secret MCP Server core infrastructure:

File: src/mcp_scrt/types.py
- NetworkType enum (MAINNET, TESTNET, CUSTOM)
- ToolCategory enum (all 11 categories)
- NetworkConfig dataclass
- WalletInfo dataclass
- ToolRequest, ToolResponse, ErrorResponse models using Pydantic
- CacheEntry model
- TransactionResult dataclass

Include proper type hints and docstrings for all classes."
```

```bash
claude-code "Create src/mcp_scrt/constants.py with:
- Network endpoints (mainnet, testnet)
- Chain IDs
- Gas limits dictionary for different operations
- Cache TTL dictionary
- Security limits
- Retry configuration
- Connection pool settings
- Validation regex patterns
- Native denom constants
Use the values from the implementation plan."
```

```bash
claude-code "Create src/mcp_scrt/config.py:
- Settings class using Pydantic BaseSettings
- Load configuration from environment variables
- Provide get_settings() singleton function
- Include get_network_url() and get_chain_id() helper methods
- Support for mainnet, testnet, and custom networks
Follow the implementation plan structure exactly."
```

```bash
claude-code "Create src/mcp_scrt/utils/errors.py:
- SecretMCPError base exception with code, message, details, suggestions
- NetworkError, ValidationError, AuthenticationError
- WalletError, TransactionError, InsufficientFundsError
- ContractError, CacheError, ConfigurationError
- All with to_dict() method for JSON serialization"
```

```bash
claude-code "Create src/mcp_scrt/utils/logging.py:
- Set up structured logging with structlog
- Support JSON and text formats
- Log levels from environment
- Context variables for request tracking
- get_logger() function
Follow Python logging best practices."
```

```bash
claude-code "Create src/mcp_scrt/utils/retry.py:
- Implement retry decorator with exponential backoff
- Use tenacity library
- Support max retries, backoff multiplier
- Handle specific exception types
- Log retry attempts"
```

#### Step 1.2: Core Business Logic

```bash
claude-code "Create src/mcp_scrt/core/session.py:
Implement SessionManager class with:
- Session state storage (in-memory)
- Network configuration (current network, URL, chain ID)
- Wallet management (active wallet, wallet list)
- State methods: initialize(), reset(), get_state(), set_state()
- Network methods: set_network(), get_network()
- Wallet methods: add_wallet(), remove_wallet(), set_active_wallet(), get_active_wallet()
- Thread-safe with asyncio.Lock
- Proper error handling"
```

```bash
claude-code "Create src/mcp_scrt/core/security.py:
Implement SecurityManager class with:
- Key encryption using cryptography.fernet
- Mnemonic validation (BIP39)
- Address validation (Bech32)
- Spending limit checks
- Confirmation requirement logic
- Secure key storage in memory
- encrypt_key(), decrypt_key() methods
- validate_address(), validate_amount() methods
Never store keys to disk!"
```

```bash
claude-code "Create src/mcp_scrt/core/cache.py:
Implement CacheManager class with:
- In-memory TTL cache using cachetools
- get(), set(), delete(), clear() methods
- Different TTL for different data types (validators, balances, etc.)
- Cache invalidation on transactions
- get_or_fetch() pattern
- Cache statistics (hits, misses)
Thread-safe implementation"
```

```bash
claude-code "Create src/mcp_scrt/core/validation.py:
Implement InputValidator class with:
- Address format validation (secret1..., secretvaloper1...)
- Amount validation (positive, numeric, within limits)
- Denom validation
- Transaction parameter validation
- Smart contract message validation
- Use regex patterns from constants
- Return ValidationError with suggestions"
```

#### Step 1.3: SDK Wrapper

```bash
claude-code "Create src/mcp_scrt/sdk/client.py:
Implement ClientPool class for managing LCD clients:
- Maintain pool of LCDClient and AsyncLCDClient instances
- get_client() and get_async_client() methods
- Create clients on-demand per network
- Connection reuse
- _get_network_config() helper
- close_all() cleanup method
- Global get_client_pool() function
Use secret-sdk-python LCDClient and AsyncLCDClient"
```

```bash
claude-code "Create src/mcp_scrt/sdk/wallet.py:
Implement WalletManager class:
- Create wallet from mnemonic (MnemonicKey)
- Import wallet from mnemonic
- Get wallet by ID
- Sign transactions
- Derive addresses
- Integration with SecurityManager for key storage
- wallet_to_info() helper to convert to WalletInfo
Use secret-sdk-python Wallet class"
```

```bash
claude-code "Create src/mcp_scrt/sdk/transaction.py:
Implement TransactionBuilder class:
- Build transaction from messages
- Estimate gas
- Simulate transaction
- Sign transaction with wallet
- Broadcast transaction
- Parse transaction result
- Support for batch transactions (multiple messages)
- Integration with LCDClient.wallet()
Use secret-sdk-python transaction building"
```

```bash
claude-code "Create src/mcp_scrt/sdk/encryption.py:
Implement contract encryption utilities:
- encrypt_contract_message() for execute messages
- decrypt_contract_response() for query responses
- get_encryption_utils() to access Secret SDK encryption
- Support for contract code hash
Use secret-sdk-python encrypt_utils"
```

#### Step 1.4: Testing Foundation

```bash
claude-code "Create tests/conftest.py:
- Pytest fixtures for testing
- mock_settings fixture
- mock_client fixture
- mock_wallet fixture
- mock_session_manager fixture
- test_mnemonic fixture
Use pytest and pytest-mock"
```

```bash
claude-code "Create unit tests:
1. tests/unit/test_config.py - test Settings class
2. tests/unit/test_types.py - test data models
3. tests/unit/test_errors.py - test exception classes
4. tests/unit/test_session.py - test SessionManager
5. tests/unit/test_security.py - test SecurityManager
6. tests/unit/test_cache.py - test CacheManager
7. tests/unit/test_validation.py - test InputValidator

Each test file should have >80% coverage of its module."
```

---

### Phase 2: Core Tools (Days 8-18)

#### Step 2.1: Base Tool Handler

```bash
claude-code "Create src/mcp_scrt/tools/base.py:
Implement BaseToolHandler abstract class:
- __init__ with session_manager, client_pool, cache_manager
- execute() abstract method
- validate_input() method using InputValidator
- format_output() method for consistent responses
- handle_error() method with proper error response
- require_wallet() decorator
- require_network() decorator
- log_tool_execution() decorator
Use ABC for abstract base class"
```

#### Step 2.2: Network Tools

```bash
claude-code "Create src/mcp_scrt/tools/network.py:
Implement 4 network tools:

1. secret_configure_network:
   - Parameters: network (mainnet/testnet/custom), custom_url, custom_chain_id
   - Updates session network configuration
   - Returns new network config

2. secret_get_network_info:
   - No parameters
   - Returns: chain_id, url, block_height, network_type
   - Uses client.tendermint.node_info()

3. secret_get_gas_prices:
   - No parameters
   - Returns current gas price recommendations
   - From constants or client

4. secret_health_check:
   - No parameters
   - Tests connection to network
   - Returns: connected (bool), latency, block_height, status

Each tool extends BaseToolHandler."
```

#### Step 2.3: Wallet Tools

```bash
claude-code "Create src/mcp_scrt/tools/wallet.py:
Implement 6 wallet tools:

1. secret_create_wallet:
   - Parameters: save_as (wallet_id)
   - Generates new 24-word mnemonic
   - Stores encrypted in session
   - Returns: wallet_id, address, mnemonic (WARNING: save mnemonic!)

2. secret_import_wallet:
   - Parameters: mnemonic, save_as, account=0, index=0
   - Imports from mnemonic
   - Validates BIP39 mnemonic
   - Returns: wallet_id, address

3. secret_set_active_wallet:
   - Parameters: wallet_id
   - Sets active wallet in session
   - Returns: wallet_id, address

4. secret_get_active_wallet:
   - No parameters
   - Returns: wallet_id, address, balance (from cache)

5. secret_list_wallets:
   - No parameters
   - Returns: list of {wallet_id, address} for all session wallets

6. secret_remove_wallet:
   - Parameters: wallet_id
   - Removes from session (securely wipes keys)
   - Returns: success message

Use SecurityManager for key handling."
```

#### Step 2.4: Bank Tools

```bash
claude-code "Create src/mcp_scrt/tools/bank.py:
Implement 5 bank tools:

1. secret_get_balance:
   - Parameters: address (optional, defaults to active), denom (optional)
   - Uses client.bank.balance()
   - Caches result with 30s TTL
   - Returns: {denom: amount} or list of balances

2. secret_send_tokens:
   - Parameters: recipient, amount, denom='uscrt', memo (optional)
   - Requires active wallet
   - Validates addresses and amount
   - Creates MsgSend
   - Checks confirmation threshold
   - Broadcasts transaction
   - Returns: txhash, success

3. secret_multi_send:
   - Parameters: recipients [{address, amount, denom}], memo
   - Creates MsgMultiSend
   - Returns: txhash, success

4. secret_get_total_supply:
   - Parameters: denom (optional)
   - Uses client.bank.total_supply()
   - Returns: total supply by denom

5. secret_get_denom_metadata:
   - Parameters: denom
   - Uses client.bank.denom_metadata()
   - Returns: denom details

Use secret-sdk-python bank module."
```

#### Step 2.5: Transaction & Blockchain Tools

```bash
claude-code "Create src/mcp_scrt/tools/transactions.py:
Implement 5 transaction tools:

1. secret_get_transaction:
   - Parameters: tx_hash
   - Uses client.tx.tx_info()
   - Returns: full transaction details

2. secret_search_transactions:
   - Parameters: events (list of tuples), limit=100, order_by='desc'
   - Uses client.tx.search()
   - Returns: transaction list

3. secret_estimate_gas:
   - Parameters: messages (list of message dicts)
   - Simulates transaction
   - Returns: gas estimate

4. secret_simulate_transaction:
   - Parameters: messages
   - Dry-run without broadcasting
   - Returns: simulation result

5. secret_get_transaction_status:
   - Parameters: tx_hash
   - Checks if tx successful
   - Returns: success (bool), error_message, events

Use secret-sdk-python tx module."
```

```bash
claude-code "Create src/mcp_scrt/tools/blockchain.py:
Implement 5 blockchain tools:

1. secret_get_block:
   - Parameters: height (optional)
   - Uses client.tendermint.block_info()
   - Returns: block details

2. secret_get_latest_block:
   - No parameters
   - Gets latest block
   - Returns: block details

3. secret_get_block_by_hash:
   - Parameters: block_hash
   - Returns: block details

4. secret_get_node_info:
   - No parameters
   - Uses client.tendermint.node_info()
   - Returns: node information

5. secret_get_syncing_status:
   - No parameters
   - Uses client.tendermint.syncing()
   - Returns: syncing status

Cache block info with 10s TTL."
```

#### Step 2.6: Account Tools

```bash
claude-code "Create src/mcp_scrt/tools/accounts.py:
Implement 3 account tools:

1. secret_get_account:
   - Parameters: address (optional)
   - Uses client.auth.account_info()
   - Returns: account_number, sequence, pubkey

2. secret_get_account_transactions:
   - Parameters: address (optional), limit=100, order_by='desc'
   - Searches transactions by sender/recipient
   - Returns: transaction list

3. secret_get_account_tx_count:
   - Parameters: address (optional)
   - Counts transactions
   - Returns: total count

Use client.auth module."
```

#### Step 2.7: Testing Phase 2

```bash
claude-code "Create comprehensive unit tests for Phase 2:
1. tests/unit/test_tools/test_base.py
2. tests/unit/test_tools/test_network.py
3. tests/unit/test_tools/test_wallet.py
4. tests/unit/test_tools/test_bank.py
5. tests/unit/test_tools/test_transactions.py
6. tests/unit/test_tools/test_blockchain.py
7. tests/unit/test_tools/test_accounts.py

Each should test success cases, error cases, and validation.
Use mocks for SDK calls."
```

---

### Phase 3: Advanced Tools (Days 19-32)

#### Step 3.1: Staking Tools

```bash
claude-code "Create src/mcp_scrt/tools/staking.py:
Implement 8 staking tools:

1. secret_get_validators - list validators with filtering
2. secret_get_validator - get specific validator details
3. secret_delegate - delegate tokens
4. secret_undelegate - undelegate tokens
5. secret_redelegate - redelegate between validators
6. secret_get_delegations - get delegations for address
7. secret_get_unbonding_delegations - get unbonding delegations
8. secret_get_redelegations - get redelegations

Use secret-sdk-python staking module and MsgDelegate, MsgUndelegate, MsgBeginRedelegate."
```

#### Step 3.2: Rewards Tools

```bash
claude-code "Create src/mcp_scrt/tools/rewards.py:
Implement 4 rewards tools:

1. secret_get_rewards - get staking rewards
2. secret_withdraw_rewards - withdraw rewards (single or all)
3. secret_set_withdraw_address - set withdrawal address
4. secret_get_community_pool - get community pool balance

Use distribution module and MsgWithdrawDelegatorReward."
```

#### Step 3.3: Governance Tools

```bash
claude-code "Create src/mcp_scrt/tools/governance.py:
Implement 6 governance tools:

1. secret_get_proposals - list proposals with status filter
2. secret_get_proposal - get specific proposal
3. secret_submit_proposal - submit new proposal
4. secret_deposit_proposal - deposit to proposal
5. secret_vote_proposal - vote on proposal
6. secret_get_vote - get vote for proposal

Use gov module and MsgSubmitProposal, MsgDeposit, MsgVote."
```

#### Step 3.4: Smart Contract Tools

```bash
claude-code "Create src/mcp_scrt/tools/contracts.py:
Implement 10 contract tools:

1. secret_upload_contract - upload WASM
2. secret_get_code_info - get code info
3. secret_list_codes - list uploaded codes
4. secret_instantiate_contract - instantiate from code
5. secret_execute_contract - execute contract (with encryption)
6. secret_query_contract - query contract (with encryption/decryption)
7. secret_batch_execute_contracts - batch executions
8. secret_get_contract_info - get contract info
9. secret_get_contract_history - get contract history
10. secret_migrate_contract - migrate contract

Use wasm module, encryption utils, and wallet.execute_tx(), wallet.multi_execute_tx()."
```

#### Step 3.5: IBC Tools

```bash
claude-code "Create src/mcp_scrt/tools/ibc.py:
Implement 4 IBC tools:

1. secret_ibc_transfer - transfer tokens via IBC
2. secret_get_ibc_channels - list IBC channels
3. secret_get_ibc_channel - get specific channel
4. secret_get_ibc_denom_trace - get denom trace

Use ibc and ibc_transfer modules and MsgTransfer."
```

---

### Phase 4: MCP Server Integration (Days 33-35)

```bash
claude-code "Create src/mcp_scrt/server.py:
Implement main MCP server using FastMCP:

1. Import all tool handlers
2. Create MCP server instance
3. Register all 70+ tools using @mcp.tool() decorator
4. Register resources (session/state, wallets/list, network/config, etc.)
5. Register prompts (guide, contracts)
6. Initialize session manager, client pool, cache manager
7. Health check endpoint
8. Graceful shutdown
9. Error handling middleware

Follow FastMCP patterns from documentation."
```

```bash
claude-code "Create src/mcp_scrt/__main__.py:
Entry point for CLI:
- Parse command line arguments
- Load configuration
- Initialize logging
- Start MCP server
- Handle SIGTERM/SIGINT for graceful shutdown"
```

```bash
claude-code "Create src/mcp_scrt/resources/__init__.py and resource handlers:
1. session.py - session state resource
2. wallets.py - wallets list resource
3. network.py - network config resource
4. validators.py - top validators resource

Each resource provides JSON data via MCP resource protocol."
```

```bash
claude-code "Create src/mcp_scrt/prompts/__init__.py and prompt templates:
1. guide.py - comprehensive usage guide
2. contracts.py - smart contract interaction guide

Use MCP prompt format with variables."
```

---

### Phase 5: Testing & Documentation (Days 36-40)

```bash
claude-code "Create integration tests in tests/integration/:
1. test_transfer_workflow.py - complete transfer workflow
2. test_staking_workflow.py - stake, query, unstake
3. test_contract_workflow.py - upload, instantiate, execute, query
4. test_error_scenarios.py - test error handling
5. test_caching.py - test cache behavior

Use testnet for integration tests."
```

```bash
claude-code "Create E2E tests in tests/e2e/:
1. test_new_user_journey.py - create wallet, get balance, send tokens
2. test_staking_journey.py - complete staking cycle
3. test_governance_journey.py - proposal creation and voting

Run against testnet."
```

```bash
claude-code "Generate comprehensive documentation:
1. docs/installation.md - installation guide
2. docs/configuration.md - configuration options
3. docs/quickstart.md - quick start guide
4. docs/tools/ - documentation for each tool category
5. docs/examples/ - usage examples
6. docs/api.md - API reference
7. Update README.md with overview

Use docstrings and generate with mkdocs."
```

---

### Phase 6: Docker & Deployment (Days 41-42)

```bash
claude-code "Create Dockerfile:
- Base image: python:3.11-slim
- Install dependencies
- Copy source code
- Set up entrypoint
- Expose necessary ports
- Health check

Optimize for size and security."
```

```bash
claude-code "Create docker-compose.yml:
- MCP server service
- Environment variables
- Volume mounts for config
- Network configuration
- Resource limits

Include example .env file."
```

```bash
claude-code "Create .github/workflows/ci.yml:
GitHub Actions workflow for:
- Run tests on push/PR
- Lint checks (ruff, black, mypy)
- Build Docker image
- Run security scans
- Upload coverage

Trigger on: push to main, pull requests."
```

```bash
claude-code "Create .github/workflows/release.yml:
GitHub Actions workflow for releases:
- Build and test
- Create GitHub release
- Build and push Docker image to registry
- Generate changelog
- Update documentation

Trigger on: version tags (v*.*.*)."
```

---

## 🎯 Validation Checkpoints

After each phase, run:

```bash
# Run all tests
pytest -v

# Check coverage
pytest --cov=mcp_scrt --cov-report=html

# Lint checks
ruff check src/
black --check src/
mypy src/

# Try importing
python -c "from mcp_scrt import server; print('Success!')"
```

---

## 📊 Progress Tracking

Use this checklist to track implementation:

```markdown
## Foundation (Phase 1)
- [ ] Core types and constants
- [ ] Configuration management
- [ ] Error handling
- [ ] Session management
- [ ] Security manager
- [ ] Cache manager
- [ ] Validation
- [ ] SDK client pool
- [ ] SDK wallet manager
- [ ] SDK transaction builder
- [ ] SDK encryption utils
- [ ] Foundation tests (>80% coverage)

## Core Tools (Phase 2)
- [ ] Base tool handler
- [ ] Network tools (4)
- [ ] Wallet tools (6)
- [ ] Bank tools (5)
- [ ] Transaction tools (5)
- [ ] Blockchain tools (5)
- [ ] Account tools (3)
- [ ] Core tools tests

## Advanced Tools (Phase 3)
- [ ] Staking tools (8)
- [ ] Rewards tools (4)
- [ ] Governance tools (6)
- [ ] Contract tools (10)
- [ ] IBC tools (4)
- [ ] Advanced tools tests

## Integration (Phase 4)
- [ ] MCP server implementation
- [ ] Resource handlers
- [ ] Prompt templates
- [ ] CLI entry point

## Quality (Phase 5)
- [ ] Integration tests
- [ ] E2E tests
- [ ] Documentation complete
- [ ] >80% code coverage

## Deployment (Phase 6)
- [ ] Dockerfile
- [ ] docker-compose.yml
- [ ] CI/CD workflows
- [ ] Release process
```

---

## 🚨 Common Issues & Solutions

### Issue: SDK import errors
```bash
# Solution: Ensure secret-sdk installed
pip install secret-sdk>=1.8.2
```

### Issue: Connection timeout
```bash
# Solution: Check network configuration
python -c "from secret_sdk.client.lcd import LCDClient; c = LCDClient('https://secret-4.api.trivium.network:1317', 'secret-4'); print(c.tendermint.node_info())"
```

### Issue: Encryption errors
```bash
# Solution: Verify SDK encryption utils
python -c "from secret_sdk.util import encrypt_utils; print('OK')"
```

---

## 📞 Getting Help

If you encounter issues:

1. Check the implementation plan for detailed specs
2. Review secret-sdk-python documentation
3. Check MCP protocol documentation
4. Look at similar MCP server implementations
5. Ask Claude Code for specific implementation help

---

## 🎉 Completion

When all checkboxes are complete:

1. Run full test suite: `pytest`
2. Build Docker image: `docker build -t secret-mcp-server .`
3. Test Docker: `docker-compose up`
4. Generate documentation: `mkdocs build`
5. Create release tag: `git tag v0.1.0`
6. Push to GitHub: `git push --tags`

Congratulations! You've built a production-ready Secret Network MCP Server! 🚀