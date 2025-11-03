# Secret Network MCP Server Integration Guide

## Overview

This document provides comprehensive developer-oriented documentation for building an MCP (Model Context Protocol) server that integrates with the Secret Network blockchain using the `secret-sdk-python` package.

The Secret SDK provides a complete toolkit for:
- Account management and key derivation
- Token operations (send, receive, multi-send)
- Staking operations (delegate, undelegate, redelegate)
- Governance (proposals, voting)
- Smart contract operations (upload, instantiate, execute, query)
- IBC transfers (cross-chain operations)
- Blockchain queries (blocks, transactions, validators)
- Privacy-preserving operations with built-in encryption

**Version**: 1.8.2
**Python**: 3.7+
**License**: MIT

---

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Core Architecture](#core-architecture)
3. [Client Initialization](#client-initialization)
4. [Authentication & Key Management](#authentication--key-management)
5. [Wallet Operations](#wallet-operations)
6. [Bank Module (Token Operations)](#bank-module-token-operations)
7. [Staking Module](#staking-module)
8. [Distribution Module (Rewards)](#distribution-module-rewards)
9. [Governance Module](#governance-module)
10. [Smart Contract Operations (WASM)](#smart-contract-operations-wasm)
11. [IBC Operations](#ibc-operations)
12. [Transaction Management](#transaction-management)
13. [Blockchain Queries](#blockchain-queries)
14. [Encryption & Privacy](#encryption--privacy)
15. [Error Handling](#error-handling)
16. [MCP Server Implementation Considerations](#mcp-server-implementation-considerations)
17. [Code Examples](#code-examples)

---

## Installation & Setup

### Installation

```bash
pip install secret-sdk
```

### Dependencies

The SDK has the following core dependencies:

- **aiohttp** (^3.7.3) - Async HTTP client
- **bech32** (^1.2.0) - Address encoding
- **betterproto** (2.0.0b5) - Protocol buffers
- **ecdsa** (^0.16.1) - Signature verification
- **mnemonic** (^0.19) - BIP39 mnemonics
- **miscreant** (^0.3.0) - AES-SIV encryption
- **protobuf** (^3.17.3) - Protocol buffer support
- **nest-asyncio** (^1.5.1) - Nested event loop support

### Network Endpoints

**Mainnet (secret-4)**:
- LCD API: `https://secret-4.api.trivium.network:1317`
- Chain ID: `secret-4`

**Testnet (pulsar-2)**:
- LCD API: `http://testnet.securesecrets.org:1317`
- Chain ID: `pulsar-2`

---

## Core Architecture

### Module Structure

```
secret_sdk/
├── client/
│   └── lcd/
│       ├── lcdclient.py          # Main client (sync & async)
│       ├── wallet.py              # Wallet wrapper for transactions
│       └── api/                   # API modules for each blockchain module
│           ├── auth.py
│           ├── bank.py
│           ├── distribution.py
│           ├── gov.py
│           ├── staking.py
│           ├── wasm.py
│           ├── ibc.py
│           ├── tx.py
│           └── ...
├── core/                          # Core data structures and messages
│   ├── bank/msgs.py
│   ├── staking/msgs.py
│   ├── distribution/msgs.py
│   ├── gov/msgs.py
│   ├── wasm/msgs.py
│   └── ...
├── key/                           # Key management
│   ├── mnemonic.py               # BIP39 mnemonic keys
│   └── raw.py                    # Raw private keys
└── util/
    ├── encrypt_utils.py          # Encryption for Secret contracts
    └── ...
```

### API Modules

The LCDClient exposes the following API modules:

| Module | Property | Purpose | File Location |
|--------|----------|---------|---------------|
| Auth | `client.auth` | Account queries | `secret_sdk/client/lcd/api/auth.py` |
| Bank | `client.bank` | Token balances and transfers | `secret_sdk/client/lcd/api/bank.py` |
| Distribution | `client.distribution` | Staking rewards | `secret_sdk/client/lcd/api/distribution.py` |
| Fee Grant | `client.feegrant` | Fee grant queries | `secret_sdk/client/lcd/api/feegrant.py` |
| Governance | `client.gov` | Proposals and voting | `secret_sdk/client/lcd/api/gov.py` |
| Mint | `client.mint` | Minting parameters | `secret_sdk/client/lcd/api/mint.py` |
| Authz | `client.authz` | Authorization grants | `secret_sdk/client/lcd/api/authz.py` |
| Slashing | `client.slashing` | Validator slashing info | `secret_sdk/client/lcd/api/slashing.py` |
| Staking | `client.staking` | Validators and delegations | `secret_sdk/client/lcd/api/staking.py` |
| Tendermint | `client.tendermint` | Blockchain info | `secret_sdk/client/lcd/api/tendermint.py` |
| WASM | `client.wasm` | Smart contracts | `secret_sdk/client/lcd/api/wasm.py` |
| IBC | `client.ibc` | IBC queries | `secret_sdk/client/lcd/api/ibc.py` |
| IBC Transfer | `client.ibc_transfer` | IBC transfers | `secret_sdk/client/lcd/api/ibc_transfer.py` |
| TX | `client.tx` | Transaction operations | `secret_sdk/client/lcd/api/tx.py` |
| Registration | `client.registration` | Secret Network registration | `secret_sdk/client/lcd/api/registration.py` |

---

## Client Initialization

### Synchronous Client

**File**: `secret_sdk/client/lcd/lcdclient.py:198`

```python
from secret_sdk.client.lcd import LCDClient
from secret_sdk.core import Coins

client = LCDClient(
    url="https://secret-4.api.trivium.network:1317",
    chain_id="secret-4",
    encryption_seed=None,  # Optional: custom encryption seed
    gas_prices=Coins.from_data([{"amount": "0.25", "denom": "uscrt"}]),
    gas_adjustment=1.0,
    custom_fees=None  # Optional: override default fees
)
```

**Parameters**:

- `url` (str, required): LCD server endpoint
- `chain_id` (str, required): Chain identifier
- `encryption_seed` (Optional[bytes]): Custom seed for encryption (auto-generated if None)
- `gas_prices` (Optional[Coins.Input]): Default gas prices (defaults to 0.25 uscrt)
- `gas_adjustment` (Optional[Numeric.Input]): Gas adjustment multiplier (defaults to 1.0)
- `custom_fees` (Optional[dict]): Custom fee configurations
- `_request_config` (Optional[dict]): Request timeout and retry configuration

### Asynchronous Client

**File**: `secret_sdk/client/lcd/lcdclient.py:66`

```python
from secret_sdk.client.lcd import AsyncLCDClient
import asyncio

async def main():
    async with AsyncLCDClient(
        url="https://secret-4.api.trivium.network:1317",
        chain_id="secret-4"
    ) as client:
        result = await client.bank.balance("secret1...")
        print(result)
        await client.session.close()

asyncio.run(main())
```

### Default Fee Configuration

**File**: `secret_sdk/client/lcd/lcdclient.py:39`

| Operation | Gas Limit | Amount (uscrt) |
|-----------|-----------|----------------|
| upload | 1,000,000 | 250,000 |
| init | 500,000 | 125,000 |
| exec | 200,000 | 50,000 |
| send | 80,000 | 20,000 |
| default | 200,000 | 50,000 |

**Default gas price**: 0.25 uscrt per gas unit

### Request Configuration

**File**: `secret_sdk/client/lcd/lcdclient.py:59`

```python
REQUEST_CONFIG = {
    "GET_TIMEOUT": 30,    # GET request timeout (seconds)
    "POST_TIMEOUT": 30,   # POST request timeout (seconds)
    "GET_RETRY": 1        # Number of retries for GET requests
}
```

---

## Authentication & Key Management

### MnemonicKey (Recommended)

**File**: `secret_sdk/key/mnemonic.py:13`

Derives private key from BIP39 mnemonic using BIP44 HD path.

```python
from secret_sdk.key.mnemonic import MnemonicKey

# Create from existing mnemonic
mk = MnemonicKey(
    mnemonic="your 24 word mnemonic phrase here",
    account=0,      # HD path: account number
    index=0,        # HD path: account index
    coin_type=529   # SCRT coin type (default)
)

# Generate new mnemonic
mk = MnemonicKey()  # Auto-generates 24-word mnemonic
print(mk.mnemonic)
```

**HD Path Format**: `m/44'/529'/account'/0/index`

**Coin Type**: 529 (SCRT) - defined in `secret_sdk/key/mnemonic.py:10`

### RawKey

**File**: `secret_sdk/key/raw.py`

Direct private key import.

```python
from secret_sdk.key.raw import RawKey

# Import from raw 32-byte private key
key = RawKey(private_key_bytes)
```

### Key Properties

All key types expose the following properties:

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `acc_address` | AccAddress | Account address | `secret1...` |
| `val_address` | ValAddress | Validator operator address | `secretvaloper1...` |
| `acc_pubkey` | PublicKey | Account public key | - |
| `val_pubkey` | ValConsPubKey | Validator consensus public key | - |
| `public_key` | bytes | Compressed public key bytes | - |

### Key Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `sign(payload: bytes)` | Data to sign | Signature | Sign arbitrary data |
| `sign_tx(tx: Tx, options: SignOptions)` | Transaction, sign options | Signed Tx | Sign transaction |
| `create_signature(sign_doc: SignDoc)` | Sign document | Signature | Create signature object |

---

## Wallet Operations

**File**: `secret_sdk/client/lcd/wallet.py:185`

The Wallet class wraps a Key and provides high-level transaction building and signing.

### Creating a Wallet

```python
from secret_sdk.client.lcd import LCDClient
from secret_sdk.key.mnemonic import MnemonicKey

client = LCDClient(url="...", chain_id="secret-4")
mk = MnemonicKey(mnemonic="...")
wallet = client.wallet(mk)
```

### Wallet Properties

| Property | Type | Description |
|----------|------|-------------|
| `wallet.lcd` | LCDClient | LCD client instance |
| `wallet.key` | Key | Key implementation (MnemonicKey, RawKey, etc.) |

### Core Wallet Methods

#### Account Information

**File**: `secret_sdk/client/lcd/wallet.py:194-207`

| Method | Returns | Description |
|--------|---------|-------------|
| `wallet.account_number()` | int | Fetch account number |
| `wallet.sequence()` | int | Fetch sequence (nonce) |
| `wallet.account_number_and_sequence()` | dict | Fetch both |

#### Transaction Creation

**File**: `secret_sdk/client/lcd/wallet.py:209-259`

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `create_tx(options)` | CreateTxOptions | Tx | Build unsigned transaction |
| `create_and_sign_tx(options)` | CreateTxOptions | Tx | Create and sign transaction |
| `create_and_broadcast_tx(msg_list, memo, gas, ...)` | Messages, options | TxInfo | Create, sign, and broadcast |

#### Convenience Methods

**File**: `secret_sdk/client/lcd/wallet.py:261-384`

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `send_tokens(recipient_addr, transfer_amount, memo, gas, ...)` | Recipient, amount, options | TxInfo | Send native tokens |
| `multi_send_tokens(recipient_addrs, transfer_amounts, ...)` | Recipients, amounts, options | TxInfo | Batch token sends |
| `execute_tx(contract_addr, handle_msg, memo, transfer_amount, ...)` | Contract, message, options | TxInfo | Execute smart contract |
| `multi_execute_tx(input_msgs, memo, gas, ...)` | Messages, options | TxInfo | Batch contract executions |

---

## Bank Module (Token Operations)

### Messages

**File**: `secret_sdk/core/bank/msgs.py`

#### MsgSend

Send tokens from one account to another.

```python
from secret_sdk.core.bank import MsgSend
from secret_sdk.core import Coins

msg = MsgSend(
    from_address="secret1...",
    to_address="secret1...",
    amount=Coins.from_str("1000000uscrt")  # 1 SCRT
)
```

**Parameters**:
- `from_address` (AccAddress): Sender address
- `to_address` (AccAddress): Recipient address
- `amount` (Coins): Amount to send

#### MsgMultiSend

Batch transfer tokens to multiple recipients.

```python
from secret_sdk.core.bank import MsgMultiSend

msg = MsgMultiSend(
    inputs=[{
        'address': 'secret1sender...',
        'coins': Coins.from_str("3000000uscrt")
    }],
    outputs=[
        {'address': 'secret1recipient1...', 'coins': Coins.from_str("1000000uscrt")},
        {'address': 'secret1recipient2...', 'coins': Coins.from_str("2000000uscrt")}
    ]
)
```

### Queries

**File**: `secret_sdk/client/lcd/api/bank.py`

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `balance(address)` | Address | (Coins, Pagination) | Get account balance |
| `balance(address, denom)` | Address, denom | Coin | Get specific denom balance |
| `total()` | - | Coins | Get total supply |
| `total(denom)` | Denom | Coin | Get supply of specific denom |
| `spendable_balances(address)` | Address | Coins | Get spendable balance |

---

## Staking Module

### Messages

**File**: `secret_sdk/core/staking/msgs.py`

#### MsgDelegate

Delegate tokens to a validator.

```python
from secret_sdk.core.staking import MsgDelegate
from secret_sdk.core import Coin

msg = MsgDelegate(
    delegator_address="secret1...",
    validator_address="secretvaloper1...",
    amount=Coin("uscrt", "1000000")  # 1 SCRT
)
```

**Parameters**:
- `delegator_address` (AccAddress): Delegator's address
- `validator_address` (ValAddress): Validator operator address
- `amount` (Coin): Amount to delegate

#### MsgUndelegate

Undelegate tokens from a validator.

```python
from secret_sdk.core.staking import MsgUndelegate

msg = MsgUndelegate(
    delegator_address="secret1...",
    validator_address="secretvaloper1...",
    amount=Coin("uscrt", "1000000")
)
```

#### MsgBeginRedelegate

Redelegate tokens from one validator to another.

```python
from secret_sdk.core.staking import MsgBeginRedelegate

msg = MsgBeginRedelegate(
    delegator_address="secret1...",
    validator_src_address="secretvaloper1...",  # From
    validator_dst_address="secretvaloper2...",  # To
    amount=Coin("uscrt", "1000000")
)
```

#### MsgCreateValidator

Register a new validator.

```python
from secret_sdk.core.staking import MsgCreateValidator, Description, CommissionRates

msg = MsgCreateValidator(
    description=Description(
        moniker="My Validator",
        identity="",
        website="https://...",
        security_contact="...",
        details="..."
    ),
    commission=CommissionRates(
        rate="0.1",
        max_rate="0.2",
        max_change_rate="0.01"
    ),
    min_self_delegation="1000000",
    delegator_address="secret1...",
    validator_address="secretvaloper1...",
    pubkey=pubkey,
    value=Coin("uscrt", "1000000")
)
```

#### MsgEditValidator

Update validator information.

```python
from secret_sdk.core.staking import MsgEditValidator, Description

msg = MsgEditValidator(
    description=Description(moniker="Updated Name", ...),
    validator_address="secretvaloper1...",
    commission_rate="0.15",  # Optional
    min_self_delegation=2000000  # Optional
)
```

### Queries

**File**: `secret_sdk/client/lcd/api/staking.py`

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `delegations(delegator, validator, params)` | Delegator, validator, pagination | (List[Delegation], Pagination) | Get delegations |
| `delegation(delegator, validator)` | Delegator, validator | Delegation | Get single delegation |
| `unbonding_delegations(delegator, validator, params)` | Delegator, validator, pagination | (List[UnbondingDelegation], Pagination) | Get unbonding delegations |
| `unbonding_delegation(delegator, validator)` | Delegator, validator | UnbondingDelegation | Get single unbonding |
| `redelegations(delegator, validator_src, validator_dst, params)` | Delegator, validators, pagination | (List[Redelegation], Pagination) | Get redelegations |
| `bonded_validators(delegator, params)` | Delegator, pagination | (List[Validator], Pagination) | Get delegator's validators |
| `validators(params)` | Pagination | (List[Validator], Pagination) | Get all validators |
| `validator(validator)` | Validator address | Validator | Get validator info |
| `pool()` | - | StakingPool | Get staking pool info |
| `parameters()` | - | dict | Get staking parameters |

---

## Distribution Module (Rewards)

### Messages

**File**: `secret_sdk/core/distribution/msgs.py`

#### MsgWithdrawDelegatorReward

Claim staking rewards from a validator.

```python
from secret_sdk.core.distribution import MsgWithdrawDelegatorReward

msg = MsgWithdrawDelegatorReward(
    delegator_address="secret1...",
    validator_address="secretvaloper1..."
)
```

#### MsgWithdrawValidatorCommission

Withdraw validator commission.

```python
from secret_sdk.core.distribution import MsgWithdrawValidatorCommission

msg = MsgWithdrawValidatorCommission(
    validator_address="secretvaloper1..."
)
```

#### MsgSetWithdrawAddress

Change the address that receives staking rewards.

```python
from secret_sdk.core.distribution import MsgSetWithdrawAddress

msg = MsgSetWithdrawAddress(
    delegator_address="secret1...",
    withdraw_address="secret1..."
)
```

#### MsgFundCommunityPool

Donate to the community pool.

```python
from secret_sdk.core.distribution import MsgFundCommunityPool

msg = MsgFundCommunityPool(
    depositor="secret1...",
    amount=Coins.from_str("1000000uscrt")
)
```

### Queries

**File**: `secret_sdk/client/lcd/api/distribution.py`

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `rewards(delegator)` | Delegator address | dict | Get all staking rewards |
| `rewards(delegator, validator)` | Delegator, validator | Coins | Get rewards from specific validator |
| `validator_commission(validator)` | Validator address | Coins | Get validator commission |
| `validator_outstanding_rewards(validator)` | Validator address | Coins | Get outstanding rewards |
| `withdraw_address(delegator)` | Delegator address | AccAddress | Get withdraw address |
| `community_pool()` | - | Coins | Get community pool balance |
| `parameters()` | - | dict | Get distribution parameters |

---

## Governance Module

### Messages

**File**: `secret_sdk/core/gov/msgs.py`

#### MsgSubmitProposal

Submit a governance proposal.

```python
from secret_sdk.core.gov import MsgSubmitProposal

msg = MsgSubmitProposal(
    content={
        "@type": "/cosmos.gov.v1beta1.TextProposal",
        "title": "Proposal Title",
        "description": "Proposal description"
    },
    initial_deposit=Coins.from_str("1000000uscrt"),
    proposer="secret1..."
)
```

#### MsgDeposit

Deposit tokens to a proposal.

```python
from secret_sdk.core.gov import MsgDeposit

msg = MsgDeposit(
    proposal_id=1,
    depositor="secret1...",
    amount=Coins.from_str("1000000uscrt")
)
```

#### MsgVote

Vote on a proposal.

```python
from secret_sdk.core.gov import MsgVote

msg = MsgVote(
    proposal_id=1,
    voter="secret1...",
    option="VOTE_OPTION_YES"  # YES, NO, NO_WITH_VETO, ABSTAIN
)
```

### Queries

**File**: `secret_sdk/client/lcd/api/gov.py`

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `proposals(params)` | Filters, pagination | (List[Proposal], Pagination) | List proposals |
| `proposal(proposal_id)` | Proposal ID | Proposal | Get proposal details |
| `deposits(proposal_id)` | Proposal ID | List[Deposit] | Get proposal deposits |
| `deposit(proposal_id, depositor)` | Proposal ID, depositor | Deposit | Get single deposit |
| `votes(proposal_id)` | Proposal ID | List[Vote] | Get proposal votes |
| `vote(proposal_id, voter)` | Proposal ID, voter | Vote | Get single vote |
| `tally(proposal_id)` | Proposal ID | TallyResult | Get vote tally |
| `deposit_parameters()` | - | dict | Get deposit params |
| `voting_parameters()` | - | dict | Get voting params |
| `tally_parameters()` | - | dict | Get tally params |

---

## Smart Contract Operations (WASM)

### Messages

**File**: `secret_sdk/core/wasm/msgs.py`

#### MsgStoreCode

Upload a new smart contract WASM binary.

```python
from secret_sdk.core.wasm import MsgStoreCode

with open("contract.wasm", "rb") as f:
    wasm_code = f.read()

msg = MsgStoreCode(
    sender="secret1...",
    wasm_byte_code=wasm_code,
    source="",      # Optional: source code URL
    builder=""      # Optional: builder info
)
```

**Note**: The SDK automatically gzips the WASM code if not already compressed.

#### MsgInstantiateContract

Create a new instance of an uploaded smart contract.

```python
from secret_sdk.core.wasm import MsgInstantiateContract

msg = MsgInstantiateContract(
    sender="secret1...",
    code_id=1,
    label="My Contract Instance",
    init_msg={"count": 0},  # Contract-specific init message
    init_funds=Coins.from_str("1000000uscrt"),  # Optional funds
    code_hash="abcd1234...",  # Optional but recommended
    encryption_utils=client.encrypt_utils  # Required for encryption
)
```

**Important**: The `init_msg` is automatically encrypted by the SDK.

#### MsgExecuteContract

Execute a state-mutating function on a smart contract.

```python
from secret_sdk.core.wasm import MsgExecuteContract

msg = MsgExecuteContract(
    sender="secret1...",
    contract="secret1contract...",
    msg={"increment": {}},  # Contract-specific execute message
    sent_funds=Coins.from_str("1000000uscrt"),  # Optional funds
    code_hash="abcd1234...",  # Optional but recommended
    encryption_utils=client.encrypt_utils  # Required for encryption
)
```

**Important**: The `msg` is automatically encrypted by the SDK.

### Queries

**File**: `secret_sdk/client/lcd/api/wasm.py`

#### Code Queries

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `list_code_info()` | - | list | List all uploaded codes |
| `code_info(code_id)` | Code ID | dict | Get code information |
| `code_hash_by_code_id(code_id)` | Code ID | dict | Get code hash by ID |
| `list_contracts_by_code_id(code_id)` | Code ID | list | List contract instances |

#### Contract Queries

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `contract_info(contract_address)` | Contract address | dict | Get contract info |
| `contract_hash(contract_address)` | Contract address | str | Get contract code hash |
| `contract_query(contract_address, query, contract_code_hash, height, timeout, retry_attempts)` | Address, query, options | Any | Query contract state |
| `contract_execute_msg(sender_address, contract_address, handle_msg, transfer_amount, contract_code_hash)` | Addresses, message, options | MsgExecuteContract | Create execute message |

#### Contract Query Example

**File**: `secret_sdk/client/lcd/api/wasm.py:84`

```python
# Query contract state (automatically encrypts query and decrypts response)
result = client.wasm.contract_query(
    contract_address="secret1...",
    query={"get_count": {}},
    contract_code_hash="abcd1234...",  # Optional but recommended
    height=0,  # Optional: query at specific height
    timeout=15,  # Optional: query timeout in seconds
    retry_attempts=1  # Optional: number of retries
)
```

**Important**:
- The SDK automatically encrypts the query and decrypts the response
- Code hash is cached after first lookup
- Errors from the contract are automatically decrypted

---

## IBC Operations

### Messages

**File**: `secret_sdk/core/ibc_transfer/msgs.py`

#### MsgTransfer

Transfer tokens via IBC to another chain.

```python
from secret_sdk.core.ibc_transfer import MsgTransfer
from secret_sdk.core import Coin

msg = MsgTransfer(
    source_port="transfer",
    source_channel="channel-0",
    token=Coin("uscrt", "1000000"),
    sender="secret1...",
    receiver="cosmos1...",  # Address on destination chain
    timeout_height={"revision_number": 1, "revision_height": 1000000},
    timeout_timestamp=0  # Unix timestamp in nanoseconds
)
```

### Queries

**File**: `secret_sdk/client/lcd/api/ibc.py` and `secret_sdk/client/lcd/api/ibc_transfer.py`

IBC queries include channels, connections, clients, and transfer parameters.

---

## Transaction Management

### CreateTxOptions

**File**: `secret_sdk/client/lcd/api/tx.py`

```python
from secret_sdk.client.lcd.api.tx import CreateTxOptions
from secret_sdk.core import Coins

options = CreateTxOptions(
    msgs=[msg1, msg2],  # List of messages
    memo="Transaction memo",  # Optional
    gas="200000",  # Optional: gas limit (auto-estimated if None)
    gas_prices=Coins.from_str("0.25uscrt"),  # Optional
    gas_adjustment=1.0,  # Optional: adjustment factor
    fee=None,  # Optional: explicit fee (auto-estimated if None)
    account_number=None,  # Optional: fetched if None
    sequence=None,  # Optional: fetched if None
    fee_denoms=None  # Optional: denoms to use for fees
)
```

### Transaction Flow

**File**: `secret_sdk/client/lcd/wallet.py:357-383`

```python
# Method 1: Using wallet convenience method (recommended)
tx_info = wallet.create_and_broadcast_tx(
    msg_list=[msg1, msg2],
    memo="My transaction",
    gas=200000  # Optional: auto-estimated if None
)

# Method 2: Manual steps
from secret_sdk.client.lcd.api.tx import CreateTxOptions
from secret_sdk.key.key import SignOptions
from secret_sdk.protobuf.cosmos.tx.v1beta1 import BroadcastMode

# 1. Create options
options = CreateTxOptions(msgs=[msg], memo="", gas=None)

# 2. Estimate fee (if gas is None)
if options.gas is None:
    fee = client.tx.estimate_fee(options)
    options.fee = fee

# 3. Create unsigned transaction
unsigned_tx = wallet.create_tx(options)

# 4. Sign transaction
signed_tx = wallet.key.sign_tx(
    tx=unsigned_tx,
    options=SignOptions(
        account_number=wallet.account_number(),
        sequence=wallet.sequence(),
        chain_id=client.chain_id
    )
)

# 5. Broadcast transaction
result = client.tx.broadcast(signed_tx, mode=BroadcastMode.BROADCAST_MODE_SYNC)
```

### Broadcast Modes

**File**: `secret_sdk/protobuf/cosmos/tx/v1beta1`

- `BROADCAST_MODE_SYNC`: Wait for CheckTx (recommended)
- `BROADCAST_MODE_ASYNC`: Return immediately
- `BROADCAST_MODE_BLOCK`: Wait for commit (deprecated, slow)

### Transaction Queries

**File**: `secret_sdk/client/lcd/api/tx.py`

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `tx_info(tx_hash)` | Transaction hash | TxInfo | Get transaction by hash |
| `search(events)` | Event filters | List[TxInfo] | Search transactions |
| `estimate_fee(tx_options)` | Transaction options | Fee | Estimate transaction fee |
| `broadcast(tx, mode)` | Signed tx, mode | TxInfo | Broadcast transaction |

---

## Blockchain Queries

### Tendermint API

**File**: `secret_sdk/client/lcd/api/tendermint.py`

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `node_info()` | - | dict | Get node information |
| `syncing()` | - | bool | Check if node is syncing |
| `validator_set(height)` | Block height | dict | Get validator set |
| `block_info(height)` | Block height | dict | Get block information |

### Auth API

**File**: `secret_sdk/client/lcd/api/auth.py`

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `account_info(address)` | Address | Account | Get account info (number, sequence, pubkey) |

### Example: Get Latest Block

```python
block_info = client.tendermint.block_info()
latest_height = block_info['block']['header']['height']
```

---

## Encryption & Privacy

**File**: `secret_sdk/util/encrypt_utils.py`

Secret Network uses privacy-preserving smart contracts. The SDK automatically handles encryption/decryption.

### EncryptionUtils

The `EncryptionUtils` class is automatically initialized when creating an LCDClient.

**File**: `secret_sdk/client/lcd/lcdclient.py:112-113` and `secret_sdk/client/lcd/lcdclient.py:300-301`

```python
# Encryption utils are automatically set up
client = LCDClient(url="...", chain_id="secret-4")
# client.encrypt_utils is ready to use

# Custom encryption seed (optional)
custom_seed = b"your-custom-seed-here"
client = LCDClient(url="...", chain_id="secret-4", encryption_seed=custom_seed)
```

### Key Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `encrypt(contract_code_hash, msg)` | Code hash, message | bytes | Encrypt message for contract |
| `decrypt(ciphertext, nonce)` | Ciphertext, nonce | bytes | Decrypt contract response |
| `generate_new_seed()` | - | bytes | Generate new encryption seed |
| `get_tx_encryption_key(nonce)` | Nonce | bytes | Derive encryption key |

### Automatic Encryption

The SDK automatically handles encryption for:

1. **Contract Instantiation**: `MsgInstantiateContract` - `init_msg` is encrypted
2. **Contract Execution**: `MsgExecuteContract` - `msg` is encrypted
3. **Contract Queries**: `contract_query()` - query is encrypted, response is decrypted

**File**: `secret_sdk/core/wasm/msgs.py:165-169` (Instantiate), `secret_sdk/core/wasm/msgs.py:244-248` (Execute)

```python
# Encryption is handled automatically
result = client.wasm.contract_query(
    contract_address="secret1...",
    query={"get_secret_data": {}}  # Automatically encrypted
)
# Result is automatically decrypted
```

### Consensus I/O Public Key

**File**: `secret_sdk/client/lcd/lcdclient.py:112` and `secret_sdk/client/lcd/lcdclient.py:300`

The SDK fetches the consensus I/O public key from the chain during initialization:

```python
consensus_io_pub_key = client.registration.consensus_io_pub_key()
```

This key is used for all encryption operations.

---

## Error Handling

### LCDResponseError

**File**: `secret_sdk/exceptions.py`

```python
from secret_sdk.exceptions import LCDResponseError

try:
    result = client.bank.balance("invalid-address")
except LCDResponseError as e:
    print(f"Error: {e.message}")
    print(f"Status: {e.response.status}")
```

### Contract Error Decryption

**File**: `secret_sdk/client/lcd/api/wasm.py:122-130`

The SDK automatically decrypts contract execution errors:

```python
try:
    result = client.wasm.contract_query(contract_address, query)
except LCDResponseError as e:
    # Error message is automatically decrypted if it's from a contract
    print(f"Contract error: {e.message}")
```

---

## MCP Server Implementation Considerations

### Recommended Architecture

```
MCP Server
├── Tools (exposed to MCP client)
│   ├── Account Management
│   │   ├── generate_wallet
│   │   ├── import_wallet
│   │   ├── get_balance
│   │   └── get_account_info
│   ├── Token Operations
│   │   ├── send_tokens
│   │   ├── multi_send_tokens
│   │   └── query_balance
│   ├── Staking
│   │   ├── delegate
│   │   ├── undelegate
│   │   ├── redelegate
│   │   ├── claim_rewards
│   │   ├── query_validators
│   │   └── query_delegations
│   ├── Governance
│   │   ├── submit_proposal
│   │   ├── deposit_to_proposal
│   │   ├── vote_on_proposal
│   │   └── query_proposals
│   ├── Smart Contracts
│   │   ├── upload_contract
│   │   ├── instantiate_contract
│   │   ├── execute_contract
│   │   ├── query_contract
│   │   └── get_contract_info
│   └── Blockchain Queries
│       ├── get_block_info
│       ├── get_transaction
│       ├── search_transactions
│       └── get_node_info
└── Resources (state management)
    ├── Wallet Store (encrypted)
    ├── Contract Registry
    └── Transaction History
```

### Key Considerations

#### 1. Async vs Sync

- Use `AsyncLCDClient` for better performance in MCP server
- Handle concurrent requests efficiently
- Implement proper session management

```python
from secret_sdk.client.lcd import AsyncLCDClient

class SecretMCPServer:
    def __init__(self):
        self.client = None

    async def initialize(self):
        self.client = AsyncLCDClient(
            url="https://secret-4.api.trivium.network:1317",
            chain_id="secret-4"
        )

    async def cleanup(self):
        if self.client:
            await self.client.session.close()
```

#### 2. Wallet Management

- Store mnemonics securely (encrypted at rest)
- Use separate wallets for different operations
- Implement wallet derivation paths for HD wallets

```python
from secret_sdk.key.mnemonic import MnemonicKey

def create_wallet(mnemonic: str, account: int = 0, index: int = 0):
    """Create wallet from mnemonic with HD path support"""
    return MnemonicKey(
        mnemonic=mnemonic,
        account=account,
        index=index
    )
```

#### 3. Error Handling

- Wrap all SDK calls in try-except blocks
- Return structured error responses
- Log errors for debugging

```python
async def handle_request(operation, params):
    try:
        result = await operation(**params)
        return {"success": True, "data": result}
    except LCDResponseError as e:
        return {
            "success": False,
            "error": {
                "type": "LCDResponseError",
                "message": e.message,
                "status": e.response.status
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            }
        }
```

#### 4. Gas Estimation

- Always use automatic gas estimation when possible
- Allow users to override gas limits
- Implement gas price oracle for dynamic pricing

```python
async def execute_with_auto_gas(wallet, msgs, memo=""):
    """Execute transaction with automatic gas estimation"""
    return await wallet.create_and_broadcast_tx(
        msg_list=msgs,
        memo=memo,
        gas=None  # Auto-estimate
    )
```

#### 5. Contract Code Hash Caching

**File**: `secret_sdk/client/lcd/api/wasm.py:13`

The SDK caches contract code hashes automatically:

```python
_contract_code_hash = {}  # Global cache
```

This reduces the number of RPC calls for frequently accessed contracts.

#### 6. Pagination

- Implement pagination for list queries
- Use `PaginationOptions` for large datasets

```python
from secret_sdk.client.lcd.params import PaginationOptions

params = PaginationOptions(
    limit=100,
    offset=0,
    count_total=True
)

validators, pagination = await client.staking.validators(params=params)
```

#### 7. Network Configuration

- Support multiple networks (mainnet, testnet)
- Allow custom RPC endpoints
- Implement network switching

```python
NETWORKS = {
    "mainnet": {
        "chain_id": "secret-4",
        "lcd_url": "https://secret-4.api.trivium.network:1317"
    },
    "testnet": {
        "chain_id": "pulsar-2",
        "lcd_url": "http://testnet.securesecrets.org:1317"
    }
}

async def create_client(network: str):
    config = NETWORKS[network]
    return AsyncLCDClient(
        url=config["lcd_url"],
        chain_id=config["chain_id"]
    )
```

#### 8. Transaction Monitoring

- Implement transaction status checking
- Return transaction hashes for tracking
- Support transaction search by events

```python
async def wait_for_transaction(client, tx_hash, timeout=30):
    """Wait for transaction to be included in a block"""
    import asyncio

    for _ in range(timeout):
        try:
            tx_info = await client.tx.tx_info(tx_hash)
            return tx_info
        except:
            await asyncio.sleep(1)

    raise TimeoutError(f"Transaction {tx_hash} not found after {timeout}s")
```

#### 9. Rate Limiting

- Implement rate limiting for RPC requests
- Use connection pooling
- Handle request timeouts gracefully

```python
REQUEST_CONFIG = {
    "GET_TIMEOUT": 30,
    "POST_TIMEOUT": 30,
    "GET_RETRY": 3  # Increase retries for production
}

client = LCDClient(
    url="...",
    chain_id="secret-4",
    _request_config=REQUEST_CONFIG
)
```

#### 10. Privacy Considerations

- Always use code_hash when executing/querying contracts for better performance
- Cache contract code hashes
- Handle encryption errors gracefully

```python
# Get and cache code hash
code_hash = await client.wasm.contract_hash(contract_address)

# Use cached hash for subsequent calls
result = await client.wasm.contract_query(
    contract_address=contract_address,
    query=query,
    contract_code_hash=code_hash
)
```

---

## Code Examples

### Example 1: Complete Token Transfer

```python
from secret_sdk.client.lcd import LCDClient
from secret_sdk.key.mnemonic import MnemonicKey
from secret_sdk.core.bank import MsgSend
from secret_sdk.core import Coins

# Initialize client
client = LCDClient(
    url="https://secret-4.api.trivium.network:1317",
    chain_id="secret-4"
)

# Create wallet
mk = MnemonicKey(mnemonic="your mnemonic here")
wallet = client.wallet(mk)

# Send tokens
tx = wallet.send_tokens(
    recipient_addr="secret1recipient...",
    transfer_amount=Coins.from_str("1000000uscrt"),  # 1 SCRT
    memo="Payment for services"
)

print(f"Transaction hash: {tx.txhash}")
```

### Example 2: Staking Operations

```python
from secret_sdk.client.lcd import LCDClient
from secret_sdk.key.mnemonic import MnemonicKey
from secret_sdk.core.staking import MsgDelegate, MsgWithdrawDelegatorReward
from secret_sdk.core import Coin

client = LCDClient(url="...", chain_id="secret-4")
mk = MnemonicKey(mnemonic="...")
wallet = client.wallet(mk)

# Delegate to validator
delegate_msg = MsgDelegate(
    delegator_address=wallet.key.acc_address,
    validator_address="secretvaloper1...",
    amount=Coin("uscrt", "1000000")
)

# Claim rewards
reward_msg = MsgWithdrawDelegatorReward(
    delegator_address=wallet.key.acc_address,
    validator_address="secretvaloper1..."
)

# Batch both operations
tx = wallet.create_and_broadcast_tx(
    msg_list=[delegate_msg, reward_msg],
    memo="Delegate and claim rewards"
)

print(f"Transaction hash: {tx.txhash}")
```

### Example 3: Smart Contract Execution

```python
from secret_sdk.client.lcd import LCDClient
from secret_sdk.key.mnemonic import MnemonicKey

client = LCDClient(url="...", chain_id="secret-4")
mk = MnemonicKey(mnemonic="...")
wallet = client.wallet(mk)

contract_address = "secret1contract..."

# Execute contract (automatically encrypted)
tx = wallet.execute_tx(
    contract_addr=contract_address,
    handle_msg={"increment": {}},
    memo="Increment counter",
    transfer_amount=None  # No funds sent
)

print(f"Transaction hash: {tx.txhash}")

# Query contract (automatically encrypted/decrypted)
result = client.wasm.contract_query(
    contract_address=contract_address,
    query={"get_count": {}}
)

print(f"Count: {result['count']}")
```

### Example 4: Batch Contract Executions

```python
from secret_sdk.client.lcd import LCDClient
from secret_sdk.key.mnemonic import MnemonicKey

client = LCDClient(url="...", chain_id="secret-4")
mk = MnemonicKey(mnemonic="...")
wallet = client.wallet(mk)

# Execute multiple contract calls in one transaction
input_msgs = [
    {
        'contract_addr': 'secret1contract1...',
        'handle_msg': {'action1': {}},
        'transfer_amount': None
    },
    {
        'contract_addr': 'secret1contract2...',
        'handle_msg': {'action2': {}},
        'transfer_amount': None
    }
]

tx = wallet.multi_execute_tx(
    input_msgs=input_msgs,
    memo="Batch execution"
)

print(f"Transaction hash: {tx.txhash}")
```

### Example 5: Query Validators and Delegations

```python
from secret_sdk.client.lcd import LCDClient

client = LCDClient(url="...", chain_id="secret-4")

# Get all validators
validators, pagination = client.staking.validators()

for validator in validators:
    print(f"Validator: {validator.operator_address}")
    print(f"  Moniker: {validator.description.moniker}")
    print(f"  Commission: {validator.commission.commission_rates.rate}")
    print(f"  Voting Power: {validator.tokens}")

# Get delegations for an address
delegator_address = "secret1..."
delegations, pagination = client.staking.delegations(delegator=delegator_address)

for delegation in delegations:
    print(f"Delegated to: {delegation.validator_address}")
    print(f"  Amount: {delegation.balance}")
```

### Example 6: Async Operations with Multiple Queries

```python
import asyncio
from secret_sdk.client.lcd import AsyncLCDClient

async def get_multiple_balances(addresses):
    async with AsyncLCDClient(
        url="https://secret-4.api.trivium.network:1317",
        chain_id="secret-4"
    ) as client:
        # Execute all queries concurrently
        tasks = [
            client.bank.balance(address)
            for address in addresses
        ]

        results = await asyncio.gather(*tasks)
        await client.session.close()

        return results

# Usage
addresses = ["secret1addr1...", "secret1addr2...", "secret1addr3..."]
balances = asyncio.run(get_multiple_balances(addresses))

for addr, (balance, _) in zip(addresses, balances):
    print(f"{addr}: {balance}")
```

### Example 7: Transaction Search

```python
from secret_sdk.client.lcd import LCDClient

client = LCDClient(url="...", chain_id="secret-4")

# Search for transactions by sender
txs = client.tx.search([
    ("message.sender", "secret1...")
])

for tx in txs:
    print(f"Hash: {tx.txhash}")
    print(f"Height: {tx.height}")
    print(f"Timestamp: {tx.timestamp}")
```

### Example 8: Working with LocalSecret (Testing)

```python
from secret_sdk.client.localsecret import LocalSecret

# Create local test client with pre-configured test wallets
local = LocalSecret()

# Access test wallets
test1 = local.wallets["test1"]
test2 = local.wallets["test2"]
test3 = local.wallets["test3"]

# Send tokens between test accounts
tx = test1.send_tokens(
    recipient_addr=test2.key.acc_address,
    transfer_amount="1000000uscrt"
)

print(f"Test transaction: {tx.txhash}")
```

---

## API Reference Summary

### Core Classes

| Class | Location | Purpose |
|-------|----------|---------|
| `LCDClient` | `secret_sdk/client/lcd/lcdclient.py:198` | Synchronous LCD client |
| `AsyncLCDClient` | `secret_sdk/client/lcd/lcdclient.py:66` | Asynchronous LCD client |
| `Wallet` | `secret_sdk/client/lcd/wallet.py:185` | Transaction builder and signer |
| `AsyncWallet` | `secret_sdk/client/lcd/wallet.py:16` | Async transaction builder |
| `MnemonicKey` | `secret_sdk/key/mnemonic.py:13` | BIP39 mnemonic key |
| `RawKey` | `secret_sdk/key/raw.py` | Raw private key |

### Message Types

| Module | Messages | Location |
|--------|----------|----------|
| Bank | `MsgSend`, `MsgMultiSend` | `secret_sdk/core/bank/msgs.py` |
| Staking | `MsgDelegate`, `MsgUndelegate`, `MsgBeginRedelegate`, `MsgCreateValidator`, `MsgEditValidator` | `secret_sdk/core/staking/msgs.py` |
| Distribution | `MsgWithdrawDelegatorReward`, `MsgWithdrawValidatorCommission`, `MsgSetWithdrawAddress`, `MsgFundCommunityPool` | `secret_sdk/core/distribution/msgs.py` |
| Gov | `MsgSubmitProposal`, `MsgDeposit`, `MsgVote` | `secret_sdk/core/gov/msgs.py` |
| WASM | `MsgStoreCode`, `MsgInstantiateContract`, `MsgExecuteContract` | `secret_sdk/core/wasm/msgs.py` |
| Authz | `MsgGrantAuthorization`, `MsgRevokeAuthorization`, `MsgExecAuthorized` | `secret_sdk/core/authz/msgs.py` |
| Slashing | `MsgUnjail` | `secret_sdk/core/slashing/msgs.py` |
| IBC Transfer | `MsgTransfer` | `secret_sdk/core/ibc_transfer/msgs.py` |
| Fee Grant | `MsgGrantAllowance`, `MsgRevokeAllowance` | `secret_sdk/core/feegrant/msgs.py` |

### API Modules

All API modules are accessible via the LCDClient instance:

- `client.auth` - Account information
- `client.bank` - Token balances and transfers
- `client.distribution` - Staking rewards
- `client.feegrant` - Fee grants
- `client.gov` - Governance
- `client.mint` - Minting parameters
- `client.authz` - Authorization grants
- `client.slashing` - Slashing information
- `client.staking` - Validators and delegations
- `client.tendermint` - Blockchain info
- `client.wasm` - Smart contracts
- `client.ibc` - IBC queries
- `client.ibc_transfer` - IBC transfers
- `client.tx` - Transaction operations
- `client.registration` - Secret Network registration

---

## Additional Resources

- **Official Documentation**: https://docs.scrt.network/
- **GitHub Repository**: https://github.com/secretanalytics/secret-sdk-python
- **Secret Network**: https://scrt.network/
- **API Endpoints**: https://docs.scrt.network/secret-network-documentation/development/resources-api-contract-addresses/connecting-to-the-network/

---

## License

The secret-sdk-python is licensed under the MIT License.

---

**Document Version**: 1.0
**Last Updated**: 2025
**Maintained For**: MCP Server Integration
