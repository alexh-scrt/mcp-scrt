# Getting Started with Secret Network MCP Server

Welcome to the Secret Network MCP Server! This guide will help you get up and running quickly.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Basic Workflows](#basic-workflows)
- [Configuration](#configuration)
- [Common Operations](#common-operations)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

## Prerequisites

### System Requirements

- **Python**: 3.13 or higher
- **Operating System**: Linux, macOS, or Windows
- **Package Manager**: pip or uv (recommended for faster installs)

### Knowledge Prerequisites

Basic familiarity with:
- Python programming
- Blockchain concepts (addresses, transactions, wallets)
- Command line interface

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/mcp-scrt.git
cd mcp-scrt
```

### 2. Install Dependencies

Choose your preferred method:

**Using pip:**
```bash
pip install -e ".[dev]"
```

**Using uv (faster):**
```bash
# Install uv if you don't have it
pip install uv

# Install dependencies
uv pip install -e ".[dev]"
```

### 3. Set Up Environment

Create your environment file:

```bash
cp .env.example .env
```

Edit `.env` to configure your settings:

```bash
# Network - Use testnet for getting started
SECRET_NETWORK=testnet

# Logging - Use DEBUG when learning
LOG_LEVEL=DEBUG
DEBUG=false

# Security - Reasonable defaults for testnet
SPENDING_LIMIT=10000000         # 10 SCRT
CONFIRMATION_THRESHOLD=1000000  # 1 SCRT
```

### 4. Verify Installation

Run the tests to ensure everything is working:

```bash
pytest tests/unit/ -v
```

You should see all tests passing ✅

## Quick Start

### Your First Wallet

Let's create your first wallet and check its balance:

```python
from mcp_scrt.sdk.wallet import HDWallet, generate_mnemonic
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.tools.base import ToolExecutionContext
from mcp_scrt.tools.wallet import CreateWalletTool, ImportWalletTool
from mcp_scrt.tools.bank import GetBalanceTool
from mcp_scrt.types import NetworkType

# 1. Create session and context
session = Session(network=NetworkType.TESTNET)
session.start()

client_pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)

context = ToolExecutionContext(
    session=session,
    client_pool=client_pool,
    network=NetworkType.TESTNET,
)

# 2. Create a new wallet
create_wallet = CreateWalletTool(context)
result = await create_wallet.run({"name": "my_first_wallet"})

print(f"Wallet created!")
print(f"Address: {result['data']['address']}")
print(f"⚠️  SAVE THIS MNEMONIC: {result['data']['mnemonic']}")

# 3. Check balance
balance_tool = GetBalanceTool(context)
balance = await balance_tool.run({})

print(f"Balance: {balance['data']['balances']}")
```

### Get Testnet Funds

To get free testnet tokens:

1. Copy your wallet address from above
2. Visit the Secret Network testnet faucet: https://faucet.pulsar.scrttestnet.com/
3. Paste your address and request tokens
4. Wait a few seconds and check your balance again

## Basic Workflows

### 1. Token Transfer Workflow

Complete workflow from wallet creation to sending tokens:

```python
import asyncio
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.tools.base import ToolExecutionContext
from mcp_scrt.tools.wallet import CreateWalletTool
from mcp_scrt.tools.bank import GetBalanceTool, SendTokensTool
from mcp_scrt.types import NetworkType

async def transfer_workflow():
    # Setup
    session = Session(network=NetworkType.TESTNET)
    session.start()

    client_pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)

    context = ToolExecutionContext(
        session=session,
        client_pool=client_pool,
        network=NetworkType.TESTNET,
    )

    # Create wallet
    create_wallet = CreateWalletTool(context)
    wallet_result = await create_wallet.run({"name": "sender_wallet"})
    print(f"Wallet: {wallet_result['data']['address']}")

    # Check balance
    balance_tool = GetBalanceTool(context)
    balance = await balance_tool.run({})
    print(f"Balance: {balance['data']['balances']}")

    # Send tokens (make sure you have funds first!)
    send_tool = SendTokensTool(context)
    send_result = await send_tool.run({
        "recipient": "secret1recipientaddresshere...",
        "amount": "1000000",  # 1 SCRT
        "denom": "uscrt",
        "memo": "My first transfer!",
    })

    print(f"Transaction: {send_result['data']['txhash']}")

    # Cleanup
    session.end()
    client_pool.close()

# Run the workflow
asyncio.run(transfer_workflow())
```

### 2. Staking Workflow

Delegate tokens to a validator and earn rewards:

```python
import asyncio
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.tools.base import ToolExecutionContext
from mcp_scrt.tools.wallet import ImportWalletTool
from mcp_scrt.tools.staking import GetValidatorsTool, DelegateTool
from mcp_scrt.tools.rewards import GetRewardsTool, WithdrawRewardsTool
from mcp_scrt.types import NetworkType

async def staking_workflow():
    # Setup
    session = Session(network=NetworkType.TESTNET)
    session.start()

    client_pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)

    context = ToolExecutionContext(
        session=session,
        client_pool=client_pool,
        network=NetworkType.TESTNET,
    )

    # Import existing wallet
    import_wallet = ImportWalletTool(context)
    await import_wallet.run({
        "name": "staking_wallet",
        "mnemonic": "your 24 word mnemonic here...",
    })

    # Find validators
    validators_tool = GetValidatorsTool(context)
    validators = await validators_tool.run({
        "status": "BOND_STATUS_BONDED",
        "limit": 5,
    })

    print("Top 5 Validators:")
    for v in validators['data']['validators']:
        print(f"  - {v['moniker']}: {v['voting_power']} voting power")

    # Delegate to first validator
    validator_address = validators['data']['validators'][0]['operator_address']

    delegate_tool = DelegateTool(context)
    delegate_result = await delegate_tool.run({
        "validator_address": validator_address,
        "amount": "5000000",  # 5 SCRT
    })

    print(f"Delegated! TX: {delegate_result['data']['txhash']}")

    # Check rewards (after some time)
    rewards_tool = GetRewardsTool(context)
    rewards = await rewards_tool.run({})
    print(f"Rewards: {rewards['data']['total_rewards']}")

    # Withdraw rewards
    withdraw_tool = WithdrawRewardsTool(context)
    withdraw_result = await withdraw_tool.run({})
    print(f"Withdrew rewards! TX: {withdraw_result['data']['txhash']}")

    # Cleanup
    session.end()
    client_pool.close()

# Run the workflow
asyncio.run(staking_workflow())
```

### 3. Smart Contract Workflow

Deploy and interact with a smart contract:

```python
import asyncio
import base64
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.tools.base import ToolExecutionContext
from mcp_scrt.tools.wallet import ImportWalletTool
from mcp_scrt.tools.contract import (
    UploadContractTool,
    InstantiateContractTool,
    ExecuteContractTool,
    QueryContractTool,
)
from mcp_scrt.types import NetworkType

async def contract_workflow():
    # Setup
    session = Session(network=NetworkType.TESTNET)
    session.start()

    client_pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)

    context = ToolExecutionContext(
        session=session,
        client_pool=client_pool,
        network=NetworkType.TESTNET,
    )

    # Import wallet
    import_wallet = ImportWalletTool(context)
    await import_wallet.run({
        "name": "contract_wallet",
        "mnemonic": "your 24 word mnemonic here...",
    })

    # Upload contract
    upload_tool = UploadContractTool(context)

    # Read and encode WASM file
    with open("counter.wasm", "rb") as f:
        wasm_bytes = f.read()
    wasm_base64 = base64.b64encode(wasm_bytes).decode()

    upload_result = await upload_tool.run({
        "wasm_byte_code": wasm_base64,
    })

    code_id = upload_result['data']['code_id']
    print(f"Uploaded contract! Code ID: {code_id}")

    # Instantiate contract
    instantiate_tool = InstantiateContractTool(context)
    instantiate_result = await instantiate_tool.run({
        "code_id": code_id,
        "init_msg": {"count": 0},
        "label": "my_counter_v1",
    })

    contract_address = instantiate_result['data']['contract_address']
    print(f"Contract deployed at: {contract_address}")

    # Query initial state
    query_tool = QueryContractTool(context)
    query_result = await query_tool.run({
        "contract_address": contract_address,
        "query_msg": {"get_count": {}},
    })

    print(f"Initial count: {query_result['data']['query_result']['count']}")

    # Execute: increment counter
    execute_tool = ExecuteContractTool(context)
    execute_result = await execute_tool.run({
        "contract_address": contract_address,
        "execute_msg": {"increment": {}},
    })

    print(f"Incremented! TX: {execute_result['data']['txhash']}")

    # Query new state
    query_result = await query_tool.run({
        "contract_address": contract_address,
        "query_msg": {"get_count": {}},
    })

    print(f"New count: {query_result['data']['query_result']['count']}")

    # Cleanup
    session.end()
    client_pool.close()

# Run the workflow
asyncio.run(contract_workflow())
```

## Configuration

### Environment Variables

All configuration is done through environment variables in `.env`:

#### Network Configuration

```bash
# Choose network
SECRET_NETWORK=testnet  # Options: testnet, mainnet, custom

# Testnet (pulsar-3)
SECRET_TESTNET_URL=https://lcd.testnet.secretsaturn.net
SECRET_TESTNET_CHAIN_ID=pulsar-3

# Mainnet (secret-4)
SECRET_MAINNET_URL=https://lcd.mainnet.secretsaturn.net
SECRET_MAINNET_CHAIN_ID=secret-4
```

#### Security Configuration

```bash
# Transaction limits
SPENDING_LIMIT=10000000         # Maximum per transaction (10 SCRT)
CONFIRMATION_THRESHOLD=1000000  # Require confirmation above (1 SCRT)

# Rate limiting (optional)
RATE_LIMIT_ENABLED=true
MAX_REQUESTS_PER_MINUTE=60
```

#### Logging Configuration

```bash
# Log level
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Log format
LOG_FORMAT=json  # Options: json, console

# Extra debug mode (requires LOG_LEVEL=DEBUG)
DEBUG=false
```

#### Performance Configuration

```bash
# Connection pool
MAX_CONNECTIONS=10
IDLE_TIMEOUT=300  # Seconds

# Caching (seconds)
CACHE_TTL_VALIDATORS=300  # 5 minutes
CACHE_TTL_BALANCE=30      # 30 seconds
CACHE_TTL_CONTRACT=600    # 10 minutes
CACHE_TTL_DEFAULT=60      # 1 minute

# Retries
MAX_RETRIES=3
RETRY_BACKOFF_BASE=1.0
RETRY_BACKOFF_FACTOR=2.0
```

### Switching Networks

To switch from testnet to mainnet:

```bash
# In .env file
SECRET_NETWORK=mainnet
```

Or programmatically:

```python
from mcp_scrt.types import NetworkType

# Use testnet
session = Session(network=NetworkType.TESTNET)

# Or use mainnet
session = Session(network=NetworkType.MAINNET)
```

## Common Operations

### Wallet Management

```python
from mcp_scrt.tools.wallet import (
    CreateWalletTool,
    ImportWalletTool,
    SetActiveWalletTool,
    GetActiveWalletTool,
    ListWalletsTool,
    RemoveWalletTool,
)

# Create new wallet
create_tool = CreateWalletTool(context)
result = await create_tool.run({"name": "my_wallet"})

# Import existing wallet
import_tool = ImportWalletTool(context)
result = await import_tool.run({
    "name": "imported_wallet",
    "mnemonic": "word1 word2 word3 ...",
})

# List all wallets
list_tool = ListWalletsTool(context)
wallets = await list_tool.run({})
print(wallets['data']['wallets'])

# Switch active wallet
set_active = SetActiveWalletTool(context)
await set_active.run({"name": "imported_wallet"})

# Get active wallet
get_active = GetActiveWalletTool(context)
active = await get_active.run({})
print(f"Active: {active['data']['wallet_id']}")

# Remove wallet
remove_tool = RemoveWalletTool(context)
await remove_tool.run({"name": "old_wallet"})
```

### Network Operations

```python
from mcp_scrt.tools.network import (
    GetNetworkInfoTool,
    GetGasPricesTool,
    HealthCheckTool,
)

# Get network info
network_info = GetNetworkInfoTool(context)
info = await network_info.run({})
print(f"Chain: {info['data']['chain_id']}")

# Check gas prices
gas_prices = GetGasPricesTool(context)
prices = await gas_prices.run({})
print(f"Gas: {prices['data']['gas_prices']}")

# Health check
health = HealthCheckTool(context)
status = await health.run({})
print(f"Status: {status['data']['status']}")
```

### Account Operations

```python
from mcp_scrt.tools.account import (
    GetAccountTool,
    GetAccountTransactionsTool,
)

# Get account info
account_tool = GetAccountTool(context)
account = await account_tool.run({
    "address": "secret1...",
})
print(f"Sequence: {account['data']['sequence']}")

# Get transaction history
tx_history = GetAccountTransactionsTool(context)
history = await tx_history.run({
    "address": "secret1...",
    "limit": 10,
})
print(f"Transactions: {len(history['data']['transactions'])}")
```

### Transaction Operations

```python
from mcp_scrt.tools.transaction import (
    GetTransactionTool,
    EstimateGasTool,
    SimulateTransactionTool,
)

# Get transaction details
tx_tool = GetTransactionTool(context)
tx = await tx_tool.run({"txhash": "ABC123..."})
print(f"Status: {tx['data']['code']}")

# Estimate gas
estimate = EstimateGasTool(context)
gas = await estimate.run({
    "messages": [{"type": "send", "amount": "1000000"}],
})
print(f"Estimated gas: {gas['data']['gas_estimate']}")

# Simulate transaction
simulate = SimulateTransactionTool(context)
result = await simulate.run({
    "messages": [{"type": "send", "amount": "1000000"}],
})
print(f"Simulation: {result['data']['simulation_result']}")
```

## Troubleshooting

### Common Issues

#### 1. "No active wallet" Error

**Problem**: Trying to perform wallet-required operations without a wallet.

**Solution**:
```python
# Always load a wallet first
from mcp_scrt.tools.wallet import CreateWalletTool

create_wallet = CreateWalletTool(context)
await create_wallet.run({"name": "my_wallet"})

# Or import existing wallet
from mcp_scrt.tools.wallet import ImportWalletTool

import_wallet = ImportWalletTool(context)
await import_wallet.run({
    "name": "my_wallet",
    "mnemonic": "your mnemonic here...",
})
```

#### 2. "Insufficient funds" Error

**Problem**: Wallet doesn't have enough tokens.

**Solution**:
- For testnet: Use the faucet at https://faucet.pulsar.scrttestnet.com/
- For mainnet: Transfer tokens from an exchange or another wallet
- Check balance first:
  ```python
  balance_tool = GetBalanceTool(context)
  balance = await balance_tool.run({})
  print(balance['data']['balances'])
  ```

#### 3. "Network connection failed" Error

**Problem**: Can't connect to the blockchain network.

**Solution**:
- Check your internet connection
- Verify network URL in `.env` is correct
- Try a different RPC endpoint
- Check if the network is experiencing issues

#### 4. "Invalid address" Error

**Problem**: Provided address has incorrect format.

**Solution**:
- Secret Network addresses start with `secret1`
- Addresses are case-sensitive
- Ensure no extra spaces or characters
- Example valid address: `secret1ap26qrlp8mcq2pg6r47w43l0y8zkqm8a450s03`

#### 5. "Transaction timeout" Error

**Problem**: Transaction took too long to process.

**Solution**:
- Network might be congested, try again
- Increase gas amount
- Check transaction status manually:
  ```python
  tx_tool = GetTransactionTool(context)
  status = await tx_tool.run({"txhash": "your_tx_hash"})
  ```

### Debugging Tips

#### Enable Debug Logging

```bash
# In .env
LOG_LEVEL=DEBUG
DEBUG=true
```

This will show detailed information about:
- All API calls
- Request/response data
- Internal state changes
- Cache operations

#### Check Tool Response

All tools return structured responses:

```python
result = await some_tool.run(params)

if result['success']:
    print("✅ Success!")
    print(result['data'])
else:
    print("❌ Error!")
    print(f"Message: {result['error']['message']}")
    print(f"Code: {result['error']['code']}")
    print(f"Suggestions: {result['error']['suggestions']}")
```

#### Verify Network Connectivity

```python
from mcp_scrt.tools.network import HealthCheckTool

health = HealthCheckTool(context)
status = await health.run({})

if status['success']:
    print("✅ Network is healthy")
else:
    print("❌ Network issues detected")
```

## Next Steps

### Learn More

- **Architecture**: See [Architecture.md](./Architecture.md) for system design details
- **MCP Integration**: See [MCP-INTEGRATION.md](./MCP-INTEGRATION.md) for MCP server setup
- **Implementation Plan**: See [Implementation-Plan.md](./Implementation-Plan.md) for development roadmap

### Explore Advanced Features

1. **Smart Contracts**: Learn about privacy-preserving contracts
2. **IBC Transfers**: Cross-chain token transfers
3. **Governance**: Participate in on-chain governance
4. **Multi-signature**: Secure multi-party wallets (coming soon)

### Get Help

- **Documentation**: Read the comprehensive guides in `/docs`
- **Examples**: Check `/examples` for more code samples
- **Issues**: Report bugs or request features on GitHub
- **Community**: Join the Secret Network Discord

### Best Practices

1. **Always use testnet first** - Test all operations before using mainnet
2. **Save your mnemonics securely** - Store them offline in a safe place
3. **Start with small amounts** - Test with minimal funds when learning
4. **Check balances first** - Verify you have enough funds before transactions
5. **Use try/except** - Always handle errors gracefully in your code
6. **Monitor transactions** - Keep track of transaction hashes
7. **Enable logging** - Use DEBUG mode during development
8. **Read error messages** - Error messages include helpful suggestions

### Example: Production-Ready Script

Here's a complete example with proper error handling:

```python
import asyncio
import logging
from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.tools.base import ToolExecutionContext
from mcp_scrt.tools.wallet import ImportWalletTool
from mcp_scrt.tools.bank import GetBalanceTool, SendTokensTool
from mcp_scrt.types import NetworkType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def safe_transfer(recipient: str, amount: str, mnemonic: str):
    """Safely transfer tokens with proper error handling."""
    session = None
    client_pool = None

    try:
        # Initialize
        session = Session(network=NetworkType.TESTNET)
        session.start()

        client_pool = ClientPool(network=NetworkType.TESTNET, max_connections=5)

        context = ToolExecutionContext(
            session=session,
            client_pool=client_pool,
            network=NetworkType.TESTNET,
        )

        # Import wallet
        logger.info("Importing wallet...")
        import_wallet = ImportWalletTool(context)
        wallet_result = await import_wallet.run({
            "name": "transfer_wallet",
            "mnemonic": mnemonic,
        })

        if not wallet_result['success']:
            logger.error(f"Failed to import wallet: {wallet_result['error']['message']}")
            return False

        logger.info(f"Wallet imported: {wallet_result['data']['address']}")

        # Check balance
        logger.info("Checking balance...")
        balance_tool = GetBalanceTool(context)
        balance_result = await balance_tool.run({})

        if not balance_result['success']:
            logger.error(f"Failed to get balance: {balance_result['error']['message']}")
            return False

        balances = balance_result['data']['balances']
        scrt_balance = next((b for b in balances if b['denom'] == 'uscrt'), None)

        if not scrt_balance or int(scrt_balance['amount']) < int(amount):
            logger.error(f"Insufficient balance. Have: {scrt_balance['amount'] if scrt_balance else 0}, Need: {amount}")
            return False

        logger.info(f"Balance sufficient: {scrt_balance['amount']} uscrt")

        # Send tokens
        logger.info(f"Sending {amount} uscrt to {recipient}...")
        send_tool = SendTokensTool(context)
        send_result = await send_tool.run({
            "recipient": recipient,
            "amount": amount,
            "denom": "uscrt",
            "memo": "Automated transfer",
        })

        if not send_result['success']:
            logger.error(f"Transfer failed: {send_result['error']['message']}")
            logger.error(f"Suggestions: {send_result['error']['suggestions']}")
            return False

        logger.info(f"✅ Transfer successful!")
        logger.info(f"TX Hash: {send_result['data']['txhash']}")
        return True

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False

    finally:
        # Cleanup
        if session:
            session.end()
        if client_pool:
            client_pool.close()
        logger.info("Cleanup complete")

# Usage
if __name__ == "__main__":
    recipient_address = "secret1recipientaddress..."
    amount_to_send = "1000000"  # 1 SCRT
    my_mnemonic = "your 24 word mnemonic here..."

    success = asyncio.run(safe_transfer(recipient_address, amount_to_send, my_mnemonic))

    if success:
        print("Transfer completed successfully!")
    else:
        print("Transfer failed. Check logs for details.")
```

---

## Summary

You now have everything you need to start building with the Secret Network MCP Server:

✅ Environment configured
✅ Wallet created
✅ Basic workflows understood
✅ Common operations learned
✅ Troubleshooting guide available
✅ Best practices in hand

Happy building with Secret Network! 🚀
