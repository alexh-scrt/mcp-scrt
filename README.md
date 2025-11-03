# Secret Network MCP Server

A production-ready Model Context Protocol (MCP) server for Secret Network blockchain integration, enabling AI assistants to interact with Secret Network through a secure, well-tested interface.

## Status

**Phase 1: Foundation Layer - COMPLETE** ✅

- 11/11 modules implemented
- 372/372 tests passing (100%)
- ~3,850 lines of production code
- ~4,200 lines of test code
- Production-ready with comprehensive error handling

## Features

### Core Infrastructure (Phase 1 Complete)

- **Type System** - Comprehensive Pydantic v2 models for all data structures
- **Configuration Management** - Environment-based settings with validation
- **Error Handling** - Hierarchical exception system with detailed error messages
- **Structured Logging** - Two-level debug logging with structlog
- **Caching Layer** - TTL-based caching with LRU eviction
- **Session Management** - Secure session lifecycle and wallet management
- **Connection Pooling** - Thread-safe LCD client connection pool
- **Input Validation** - Comprehensive validation for addresses, amounts, and transactions
- **Security Module** - Wallet encryption, spending limits, rate limiting
- **HD Wallet** - Full BIP32/BIP44/SLIP10 implementation with multi-account support

### Upcoming (Phase 2)

- 25+ MCP tools for blockchain interaction
- Network, wallet, bank, staking, rewards operations
- Governance, contracts, IBC, transaction tools

## Installation

### Prerequisites

- Python 3.13+
- pip or uv package manager

### Install Dependencies

```bash
# Using pip
pip install -e ".[dev]"

# Or using uv (faster)
uv pip install -e ".[dev]"
```

### Environment Setup

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Configure your environment:

```bash
# Network Configuration
SECRET_NETWORK=testnet  # Options: testnet, mainnet, custom
SECRET_TESTNET_URL=https://lcd.testnet.secretsaturn.net
SECRET_TESTNET_CHAIN_ID=pulsar-3

# Logging
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
DEBUG=false     # Set to true for extra verbose logging

# Security
SPENDING_LIMIT=10000000  # 10 SCRT in uscrt
CONFIRMATION_THRESHOLD=1000000  # 1 SCRT in uscrt

# Connection Pool
MAX_CONNECTIONS=10
IDLE_TIMEOUT=300
```

## Quick Start

### Generate a Wallet

```python
from mcp_scrt.sdk.wallet import HDWallet, generate_mnemonic

# Generate new mnemonic (24 words)
mnemonic = generate_mnemonic(word_count=24)

# Create HD wallet
wallet = HDWallet.from_mnemonic(mnemonic)

# Get address
address = wallet.get_address()
print(f"Address: {address}")

# Get HD path
path = wallet.get_hd_path()
print(f"HD Path: {path}")  # m/44'/529'/0'/0/0
```

### Session Management

```python
from mcp_scrt.core.session import SessionManager
from mcp_scrt.types import NetworkType, WalletInfo

# Create session manager
session = SessionManager(network=NetworkType.TESTNET)

# Start session
session.start()

# Load wallet
wallet_info = WalletInfo(
    address="secret1...",
    wallet_id="unique-wallet-id",
    account=0,
    index=0
)
session.load_wallet(wallet_info)

# Check session status
is_active = session.is_active()
has_wallet = session.has_wallet()
duration = session.get_duration()
```

### Client Pool

```python
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.types import NetworkType

# Create connection pool
pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)

# Use client from pool
with pool.get_client() as client:
    # Query blockchain
    account_info = client.auth.account_info(address)
    balance = client.bank.balance(address)

# Get pool statistics
stats = pool.get_stats()
print(f"Requests served: {stats['requests_served']}")
print(f"Available connections: {stats['available_connections']}")

# Cleanup
pool.close()
```

### Validation

```python
from mcp_scrt.core.validation import (
    validate_address,
    validate_amount,
    validate_transaction_params,
    ValidationError
)

# Validate address
try:
    validate_address("secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03")
    print("Valid address!")
except ValidationError as e:
    print(f"Invalid: {e.message}")
    print(f"Suggestions: {e.suggestions}")

# Validate amount
validate_amount(1000000, field_name="amount", max_amount=10000000)

# Validate transaction parameters
params = {
    "from_address": "secret1...",
    "to_address": "secret1...",
    "amount": "1000000",
    "memo": "Payment for services"
}
validate_transaction_params(params)
```

### Security

```python
from mcp_scrt.core.security import (
    SecurityManager,
    encrypt_wallet_data,
    decrypt_wallet_data,
    rate_limit
)

# Encrypt wallet data
wallet_data = {"mnemonic": "word1 word2 ...", "accounts": [...]}
password = "MySecureP@ss123"
encrypted = encrypt_wallet_data(wallet_data, password)

# Decrypt wallet data
decrypted = decrypt_wallet_data(encrypted, password)

# Security manager
manager = SecurityManager(
    spending_limit=5_000_000,      # 5 SCRT
    confirmation_threshold=1_000_000  # 1 SCRT
)

# Validate transaction
result = manager.validate_transaction(amount=2_000_000)
if result["allowed"]:
    if result["confirmation_required"]:
        print(result["message"])

# Rate limiting
limiter = rate_limit(max_calls=5, time_window=60.0)

# Check rate limit
limiter.check("sensitive_operation")

# Or use as decorator
@rate_limit(max_calls=3, time_window=60.0)
def sensitive_function():
    return "executed"
```

## Architecture

### Module Overview

```
mcp-scrt/
├── src/mcp_scrt/
│   ├── types.py              # Pydantic models and enums
│   ├── constants.py          # Network, gas, cache, security constants
│   ├── config.py             # Configuration management
│   ├── utils/
│   │   ├── errors.py         # Custom exception hierarchy
│   │   └── logging.py        # Structured logging setup
│   ├── core/
│   │   ├── cache.py          # TTL-based caching with LRU eviction
│   │   ├── session.py        # Session lifecycle management
│   │   ├── validation.py     # Input validation
│   │   └── security.py       # Encryption, spending limits, rate limiting
│   └── sdk/
│       ├── client.py         # Thread-safe LCD client pool
│       └── wallet.py         # HD wallet operations
└── tests/
    └── unit/                 # Comprehensive unit tests (372 tests)
```

### Key Design Patterns

- **Test-Driven Development (TDD)** - All modules developed with tests first
- **Thread Safety** - RLock protection for all shared state
- **Connection Pooling** - Efficient LCD client reuse
- **Two-Level Logging** - Configurable verbosity for production vs development
- **Hierarchical Exceptions** - Domain-specific errors with structured details
- **Singleton Configuration** - Centralized settings management
- **Context Managers** - Automatic resource cleanup

### Type System

All data structures use Pydantic v2 for validation:

- `NetworkType` - TESTNET, MAINNET, CUSTOM
- `NetworkConfig` - Network connection settings
- `WalletInfo` - HD wallet information
- `ToolRequest/ToolResponse` - MCP tool interaction
- `ErrorResponse` - Standardized error reporting
- `CacheEntry` - Cache metadata with TTL
- `TransactionResult` - Transaction execution results

### Error Hierarchy

```
SecretMCPError (base)
├── NetworkError (NET001)
├── ValidationError (VAL001)
├── SecurityError (SEC001)
├── AuthenticationError (AUTH001)
├── WalletError (WAL001)
├── TransactionError (TX001)
│   └── InsufficientFundsError (TX002)
├── ContractError (CTR001)
├── CacheError (CACHE001)
└── ConfigurationError (CFG001)
```

## Development

### Run Tests

```bash
# Run all tests
pytest

# Run specific module tests
pytest tests/unit/test_wallet.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=mcp_scrt --cov-report=html
```

### Test Results

```
Total Tests: 372
Passing: 372 (100%)

Module Breakdown:
- types.py: 20 tests
- constants.py: 22 tests
- errors.py: 26 tests
- config.py: 28 tests
- logging.py: 7 tests
- cache.py: 33 tests
- session.py: 29 tests
- client.py: 27 tests
- validation.py: 62 tests
- security.py: 57 tests
- wallet.py: 61 tests
```

### Logging Levels

**Level 1: LOG_LEVEL=DEBUG**
- Detailed operation logs
- Request/response tracking
- Cache operations
- Session lifecycle

**Level 2: DEBUG=true (requires LOG_LEVEL=DEBUG)**
- Internal state dumps
- Extra verbose details
- Performance metrics
- Thread-safe operation details

Example:

```bash
# Production
LOG_LEVEL=INFO DEBUG=false

# Development
LOG_LEVEL=DEBUG DEBUG=false

# Deep debugging
LOG_LEVEL=DEBUG DEBUG=true
```

### Code Quality

- **Linting**: ruff (configured in pyproject.toml)
- **Formatting**: black (configured in pyproject.toml)
- **Type Checking**: mypy (planned)
- **Testing**: pytest with comprehensive coverage

## Configuration

### Environment Variables

All configuration is managed through environment variables with sensible defaults:

```bash
# Network
SECRET_NETWORK=testnet
SECRET_TESTNET_URL=https://lcd.testnet.secretsaturn.net
SECRET_TESTNET_CHAIN_ID=pulsar-3
SECRET_MAINNET_URL=https://lcd.mainnet.secretsaturn.net
SECRET_MAINNET_CHAIN_ID=secret-4

# Security
SPENDING_LIMIT=10000000         # 10 SCRT
CONFIRMATION_THRESHOLD=1000000  # 1 SCRT

# Cache TTL (seconds)
CACHE_TTL_VALIDATORS=300        # 5 minutes
CACHE_TTL_BALANCE=30            # 30 seconds
CACHE_TTL_CONTRACT=600          # 10 minutes
CACHE_TTL_DEFAULT=60            # 1 minute

# Connection Pool
MAX_CONNECTIONS=10
IDLE_TIMEOUT=300                # 5 minutes

# Retry Configuration
MAX_RETRIES=3
RETRY_BACKOFF_BASE=1.0
RETRY_BACKOFF_FACTOR=2.0
RETRY_MAX_DELAY=30.0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json                 # Options: json, console
DEBUG=false
```

### Network Configuration

```python
from mcp_scrt.config import get_settings

settings = get_settings()

# Get current network URL
url = settings.get_network_url()

# Get current chain ID
chain_id = settings.get_chain_id()

# Check network type
if settings.network == "testnet":
    print(f"Using testnet: {url}")
```

## HD Wallet Implementation

### BIP44 Derivation Path

```
m / purpose' / coin_type' / account' / change / address_index

Secret Network:
m / 44' / 529' / 0' / 0 / 0
    │     │      │    │   │
    │     │      │    │   └─ Address index (0, 1, 2, ...)
    │     │      │    └───── Change (always 0 for Secret Network)
    │     │      └────────── Account (0, 1, 2, ...)
    │     └───────────────── Coin type (529 for Secret Network)
    └─────────────────────── Purpose (44 for BIP44)
```

### Multi-Account Support

```python
from mcp_scrt.sdk.wallet import HDWallet

# Same mnemonic, different accounts
mnemonic = generate_mnemonic()

account_0 = HDWallet.from_mnemonic(mnemonic, account_index=0)
account_1 = HDWallet.from_mnemonic(mnemonic, account_index=1)
account_2 = HDWallet.from_mnemonic(mnemonic, account_index=2)

# Different addresses from same mnemonic
print(account_0.get_address())  # m/44'/529'/0'/0/0
print(account_1.get_address())  # m/44'/529'/1'/0/0
print(account_2.get_address())  # m/44'/529'/2'/0/0
```

## Security Features

### Wallet Encryption

- **Algorithm**: Fernet symmetric encryption (cryptography library)
- **Key Derivation**: PBKDF2 with 600,000 iterations (OWASP 2023 standard)
- **Hash Function**: SHA-256
- **Salt**: 16-byte random salt per encryption
- **Encoding**: Base64 for string representation

### Password Requirements

- Minimum length: 12 characters
- Must contain uppercase letters
- Must contain lowercase letters
- Must contain digits
- Strong password enforcement

### Spending Limits

- Configurable per-transaction limits
- Default: 10 SCRT (10,000,000 uscrt)
- Automatic validation before transactions
- Customizable per user/session

### Rate Limiting

- Thread-safe per-operation tracking
- Configurable max calls and time windows
- Automatic old call cleanup
- Can be used as decorator or direct check

## Testing

### Test Organization

All modules follow TDD methodology with comprehensive test coverage:

```bash
tests/unit/
├── test_types.py         # Type definitions (20 tests)
├── test_constants.py     # Constants validation (22 tests)
├── test_config.py        # Configuration (28 tests)
├── test_errors.py        # Exception hierarchy (26 tests)
├── test_logging.py       # Logging setup (7 tests)
├── test_cache.py         # Caching layer (33 tests)
├── test_session.py       # Session management (29 tests)
├── test_client.py        # Client pool (27 tests)
├── test_validation.py    # Input validation (62 tests)
├── test_security.py      # Security module (57 tests)
└── test_wallet.py        # HD wallet (61 tests)
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_wallet.py

# Specific test class
pytest tests/unit/test_wallet.py::TestHDWalletCreation

# Specific test method
pytest tests/unit/test_wallet.py::TestHDWalletCreation::test_create_wallet_from_mnemonic

# With verbose output
pytest -v

# With output capture disabled (show prints)
pytest -s

# With coverage
pytest --cov=mcp_scrt --cov-report=html
```

## Contributing

This project is under active development. Phase 1 (Foundation) is complete. Phase 2 (MCP Tools) is next.

### Development Workflow

1. Write tests first (TDD)
2. Implement minimal code to pass tests
3. Refactor for quality
4. Add debug logging
5. Run full test suite
6. Update documentation

### Code Standards

- Follow PEP 8 style guide
- Use type hints for all functions
- Add docstrings with examples
- Include error handling with structured errors
- Add debug logging at appropriate levels
- Write comprehensive tests (aim for 100% coverage)

## Dependencies

### Core Dependencies

- `fastmcp` - MCP protocol implementation
- `secret-sdk` - Secret Network Python SDK
- `pydantic` - Data validation and settings
- `structlog` - Structured logging
- `cryptography` - Wallet encryption (Fernet, PBKDF2)
- `mnemonic` - BIP39 mnemonic generation
- `bech32` - Address encoding

### Development Dependencies

- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support
- `ruff` - Fast Python linter
- `black` - Code formatter

## Roadmap

### Phase 1: Foundation Layer ✅ COMPLETE

- [x] Type system and constants
- [x] Error handling hierarchy
- [x] Logging infrastructure
- [x] Configuration management
- [x] Caching layer
- [x] Session management
- [x] Connection pooling
- [x] Input validation
- [x] Security module
- [x] HD wallet implementation

### Phase 2: MCP Tools (In Progress)

- [ ] Network tools (info, blocks, validators)
- [ ] Wallet tools (create, import, export)
- [ ] Bank tools (balance, send, supply)
- [ ] Transaction tools (query, simulate, history)
- [ ] Blockchain tools (account, search)
- [ ] Staking tools (delegate, undelegate, rewards)
- [ ] Governance tools (proposals, voting)
- [ ] Contract tools (query, execute, info)
- [ ] IBC tools (transfer, channels)

### Phase 3: Advanced Features (Planned)

- [ ] WebSocket support for real-time updates
- [ ] Advanced caching strategies
- [ ] Batch transaction support
- [ ] Multi-signature wallet support
- [ ] Hardware wallet integration
- [ ] Monitoring and metrics
- [ ] Performance optimization

## License

[To be determined]

## Links

- [Secret Network Documentation](https://docs.scrt.network/)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [BIP39 Standard](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
- [BIP44 Standard](https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki)

## Support

For issues, questions, or contributions, please open an issue in the repository.

---

**Built with Test-Driven Development** | **Production-Ready Security** | **Comprehensive Documentation**
