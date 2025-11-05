"""Secret Network MCP Server Guide Prompt.

This module provides a comprehensive guide prompt for using the Secret Network MCP server.
"""

from typing import Optional


def secret_network_guide(
    topic: Optional[str] = None,
) -> str:
    """Generate a comprehensive guide for using the Secret Network MCP server.

    This prompt provides an overview of the MCP server capabilities, getting started
    instructions, common operations, security notes, and error handling guidance.

    Args:
        topic: Optional topic to focus on (network, wallet, tokens, staking, contracts, governance, ibc)

    Returns:
        A formatted guide string for the Secret Network MCP server
    """
    base_guide = """# Secret Network MCP Server Guide

## Overview

This MCP server provides comprehensive access to the Secret Network blockchain, enabling:
- Network configuration and monitoring
- Wallet management and operations
- Token transfers and balance queries
- Staking and delegation operations
- Governance participation
- Smart contract interactions (with privacy features)
- IBC cross-chain transfers
- Transaction monitoring and gas estimation

## Getting Started

### 1. Configure Network
Use `secret_configure_network` to set your network environment:
- **testnet**: For testing and development (recommended for first-time users)
- **mainnet**: For production operations

Example:
```
secret_configure_network(network="testnet")
```

### 2. Create or Import Wallet
Create a new wallet or import an existing one:
- **Create new**: `secret_create_wallet(name="my_wallet")`
- **Import existing**: `secret_import_wallet(name="my_wallet", mnemonic="your 24 word phrase")`

The active wallet is automatically set after creation/import.

### 3. Check Balance
Verify your wallet balance:
```
secret_get_balance(address="secret1...")
```

Or check the active wallet's balance:
```
secret_get_balance()
```

## Common Operations

### Token Transfers
- **Get balance**: `secret_get_balance(address?)`
  - Returns balance for specified address or active wallet
  - Shows all denominations available

- **Send tokens**: `secret_send_tokens(recipient, amount, denom="uscrt")`
  - Send tokens to another address
  - Requires active wallet
  - Amount is in micro-units (1 SCRT = 1,000,000 uscrt)

- **Multi-send**: `secret_multi_send(recipients=[{address, amount}], memo?)`
  - Send tokens to multiple recipients in one transaction
  - More gas-efficient for multiple transfers

### Staking Operations
- **List validators**: `secret_get_validators(status?, limit?)`
  - Get active validators sorted by voting power
  - Filter by status: "bonded", "unbonding", "unbonded"

- **Delegate tokens**: `secret_delegate(validator_address, amount)`
  - Delegate SCRT to a validator to earn rewards
  - Requires active wallet
  - Tokens are locked during delegation

- **Check rewards**: `secret_get_rewards(delegator?)`
  - View accumulated staking rewards
  - Shows rewards per validator

- **Withdraw rewards**: `secret_withdraw_rewards(validator_address?)`
  - Claim staking rewards
  - Withdraw from specific validator or all validators

- **Undelegate**: `secret_undelegate(validator_address, amount)`
  - Start unbonding process (21-day unbonding period)

- **Redelegate**: `secret_redelegate(src_validator, dst_validator, amount)`
  - Move delegation between validators without unbonding

### Smart Contracts
Secret Network supports privacy-preserving smart contracts with automatic encryption.

- **Query contract**: `secret_query_contract(contract_address, query_msg)`
  - Read contract state (no gas cost)
  - Query messages are automatically encrypted
  - Responses are automatically decrypted

- **Execute contract**: `secret_execute_contract(contract_address, execute_msg, funds?)`
  - Modify contract state (requires gas)
  - All messages are automatically encrypted
  - Can attach tokens with the `funds` parameter

- **Upload contract**: `secret_upload_contract(wasm_byte_code)`
  - Deploy new contract code to the blockchain
  - Returns a code_id for instantiation

- **Instantiate contract**: `secret_instantiate_contract(code_id, init_msg, label)`
  - Create a contract instance from uploaded code
  - Returns contract address

- **Batch execute**: `secret_batch_execute(messages)`
  - Execute multiple contract calls in a single transaction
  - More efficient for complex operations

### Governance
- **List proposals**: `secret_get_proposals(status?, voter?)`
  - View active and past governance proposals
  - Filter by status or voting participation

- **Vote on proposal**: `secret_vote_proposal(proposal_id, vote)`
  - Vote options: "yes", "no", "abstain", "no_with_veto"
  - Requires active wallet with staked tokens

- **Submit proposal**: `secret_submit_proposal(proposal_type, ...)`
  - Create new governance proposals
  - Requires minimum deposit

### IBC (Inter-Blockchain Communication)
- **Transfer tokens**: `secret_ibc_transfer(channel_id, recipient, amount, denom?)`
  - Send tokens to other IBC-enabled chains
  - Requires channel_id for destination chain

- **List channels**: `secret_get_ibc_channels()`
  - View all active IBC channels

- **Get channel info**: `secret_get_ibc_channel(channel_id)`
  - View details of specific IBC channel

## Security Notes

### Wallet Security
- **Private keys** are stored encrypted in memory only (never persisted to disk)
- **Mnemonics** must be saved securely by the user - the server does NOT store them
- **Wallet removal** permanently deletes the encrypted private key from memory
- **Large transactions** (>10,000 SCRT) may require additional confirmation

### Network Security
- All RPC communications use HTTPS endpoints
- Transaction signing happens client-side with encrypted keys
- Query permits for contract interactions are generated automatically

### Best Practices
1. **Always test on testnet first** before mainnet operations
2. **Verify addresses** before sending tokens (Secret addresses start with "secret1")
3. **Start with small amounts** when testing new operations
4. **Save your mnemonic** in a secure location (paper backup recommended)
5. **Use hardware wallets** for large amounts (future support planned)
6. **Monitor gas prices** to optimize transaction costs

## Error Handling

The server provides detailed error messages with:
- **Error codes**: Categorize the type of error
- **Suggestions**: Actionable steps to resolve the issue
- **Details**: Additional context about what went wrong

### Common Errors

#### Network Errors
- **Connection failures**: Check network connectivity and node availability
- **Timeout errors**: May indicate network congestion, retry after a delay
- **Node sync issues**: Use `secret_health_check()` to verify node status

#### Wallet Errors
- **No active wallet**: Load a wallet using `secret_set_active_wallet(name)`
- **Invalid address**: Verify address format (should start with "secret1")
- **Insufficient balance**: Check balance before transactions

#### Validation Errors
- **Missing parameters**: Check that all required parameters are provided
- **Invalid amounts**: Ensure amounts are positive integers in micro-units
- **Invalid format**: Follow the suggested format in error messages

#### Transaction Errors
- **Insufficient gas**: Increase gas amount or use `secret_estimate_gas()` first
- **Transaction timeout**: Check transaction status with `secret_get_transaction(txhash)`
- **Failed execution**: Review error details for contract execution failures

### Automatic Retry
Network errors are automatically retried with exponential backoff (up to 3 attempts).

## Transaction Gas

All transactions require gas fees paid in SCRT:
- **Estimate gas**: `secret_estimate_gas(messages)` - Preview gas cost before execution
- **Simulate transaction**: `secret_simulate_transaction(messages)` - Test execution without broadcasting
- **Default gas**: The server uses safe default gas amounts for common operations
- **Gas prices**: Check current gas prices with `secret_get_gas_prices()`

## Additional Resources

- **Network info**: `secret_get_network_info()` - View current network configuration
- **Node info**: `secret_get_node_info()` - Get blockchain node details
- **Latest block**: `secret_get_latest_block()` - View most recent block
- **Account info**: `secret_get_account(address)` - Get account details and sequence number
- **Transaction search**: `secret_search_transactions(query)` - Find transactions by criteria
"""

    # If a specific topic is requested, provide focused guidance
    topic_guides = {
        "network": """
# Network Configuration Guide

## Available Networks

### Testnet (pulsar-3)
- RPC: https://lcd.testnet.secretsaturn.net
- For development and testing
- Faucet available for test tokens
- No real value

### Mainnet (secret-4)
- RPC: https://lcd.mainnet.secretsaturn.net
- Production environment
- Real SCRT tokens with value
- Use with caution

## Configuration
```
secret_configure_network(network="testnet")
```

## Network Monitoring
- `secret_health_check()` - Verify node health
- `secret_get_network_info()` - View current configuration
- `secret_get_node_info()` - Get node details
- `secret_get_syncing_status()` - Check sync status
""",
        "wallet": """
# Wallet Management Guide

## Creating Wallets
```
secret_create_wallet(name="my_wallet")
```
Returns mnemonic - SAVE IT SECURELY!

## Importing Wallets
```
secret_import_wallet(name="existing_wallet", mnemonic="word1 word2 ...")
```

## Managing Wallets
- `secret_list_wallets()` - View all wallets
- `secret_get_active_wallet()` - Check active wallet
- `secret_set_active_wallet(name)` - Switch active wallet
- `secret_remove_wallet(name)` - Delete wallet (use with caution!)

## Security
- Private keys encrypted in memory only
- Mnemonics NOT stored by server
- Save mnemonic in secure physical location
""",
        "tokens": """
# Token Operations Guide

## Checking Balances
```
secret_get_balance(address="secret1...")
secret_get_balance()  # For active wallet
```

## Sending Tokens
```
secret_send_tokens(
    recipient="secret1...",
    amount="1000000",  # 1 SCRT (1 million uscrt)
    denom="uscrt"
)
```

## Multi-Send
```
secret_multi_send(
    recipients=[
        {"address": "secret1...", "amount": "1000000"},
        {"address": "secret1...", "amount": "2000000"}
    ]
)
```

## Amount Formats
- 1 SCRT = 1,000,000 uscrt
- Always use micro-units in parameters
- Amounts are strings to prevent precision loss
""",
        "staking": """
# Staking Guide

## Delegation
```
# Find validators
secret_get_validators(status="bonded", limit=10)

# Delegate
secret_delegate(
    validator_address="secretvaloper1...",
    amount="1000000"
)
```

## Rewards
```
# Check rewards
secret_get_rewards()

# Withdraw from all validators
secret_withdraw_rewards()

# Withdraw from specific validator
secret_withdraw_rewards(validator_address="secretvaloper1...")
```

## Unbonding
```
secret_undelegate(
    validator_address="secretvaloper1...",
    amount="1000000"
)
```
Note: 21-day unbonding period

## Redelegation
```
secret_redelegate(
    src_validator="secretvaloper1...",
    dst_validator="secretvaloper1...",
    amount="1000000"
)
```
No unbonding period when redelegating!
""",
        "contracts": """
# Smart Contracts Guide

## Contract Lifecycle

### 1. Upload Code
```
secret_upload_contract(wasm_byte_code="base64_encoded_wasm")
# Returns code_id
```

### 2. Instantiate Contract
```
secret_instantiate_contract(
    code_id=1,
    init_msg={"count": 0},
    label="my_counter"
)
# Returns contract_address
```

### 3. Query Contract (Read)
```
secret_query_contract(
    contract_address="secret1...",
    query_msg={"get_count": {}}
)
```

### 4. Execute Contract (Write)
```
secret_execute_contract(
    contract_address="secret1...",
    execute_msg={"increment": {}},
    funds=[{"denom": "uscrt", "amount": "1000000"}]  # Optional
)
```

## Privacy Features
- All messages automatically encrypted
- Responses automatically decrypted
- Uses Secret Network's encryption utils
- No additional configuration needed

## Batch Operations
```
secret_batch_execute(
    messages=[
        {
            "contract_address": "secret1...",
            "execute_msg": {"action1": {}}
        },
        {
            "contract_address": "secret1...",
            "execute_msg": {"action2": {}}
        }
    ]
)
```

## Best Practices
- Test on testnet first
- Verify code hash before interactions
- Handle encrypted responses correctly
- Use batch operations for efficiency
""",
        "governance": """
# Governance Guide

## Viewing Proposals
```
# All proposals
secret_get_proposals()

# Active proposals only
secret_get_proposals(status="voting_period")

# Proposals I voted on
secret_get_proposals(voter="secret1...")
```

## Voting
```
secret_vote_proposal(
    proposal_id=1,
    vote="yes"  # Options: yes, no, abstain, no_with_veto
)
```

## Submitting Proposals
```
secret_submit_proposal(
    proposal_type="text",
    title="Proposal Title",
    description="Detailed description",
    initial_deposit="1000000000"  # Min deposit required
)
```

## Depositing
```
secret_deposit_proposal(
    proposal_id=1,
    amount="1000000000"
)
```

## Voting Power
- Based on staked tokens
- Delegators can override their validator's vote
- Votes can be changed before voting period ends
""",
        "ibc": """
# IBC (Inter-Blockchain Communication) Guide

## Listing Channels
```
secret_get_ibc_channels()
```

## Channel Details
```
secret_get_ibc_channel(channel_id="channel-0")
```

## IBC Transfers
```
secret_ibc_transfer(
    channel_id="channel-0",
    recipient="cosmos1...",  # Address on destination chain
    amount="1000000",
    denom="uscrt",
    timeout_height="1000",  # Optional
    memo="Cross-chain transfer"  # Optional
)
```

## Denom Traces
```
secret_get_ibc_denom_trace(
    hash="27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2"
)
```

## Common Channels
- Cosmos Hub: channel-0 (typical)
- Osmosis: channel-1 (typical)
- Check current channels with `secret_get_ibc_channels()`

## Important Notes
- Verify channel ID before transfers
- Recipient address must be valid for destination chain
- IBC transfers have timeout parameters
- Monitor transfer status with transaction hash
""",
    }

    if topic and topic.lower() in topic_guides:
        return topic_guides[topic.lower()]

    return base_guide
