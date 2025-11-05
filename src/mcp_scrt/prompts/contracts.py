"""Secret Smart Contracts Guide Prompt.

This module provides a comprehensive guide prompt for working with Secret Network smart contracts.
"""

from typing import Optional


def smart_contracts_guide(
    operation: Optional[str] = None,
) -> str:
    """Generate a comprehensive guide for Secret Network smart contract operations.

    This prompt provides detailed information about the contract lifecycle, privacy features,
    examples, and best practices for working with Secret smart contracts.

    Args:
        operation: Optional operation to focus on (upload, instantiate, execute, query, migrate, batch)

    Returns:
        A formatted guide string for Secret Network smart contracts
    """
    base_guide = """# Secret Smart Contracts Guide

## Overview

Secret Network smart contracts are privacy-preserving programs that run on the blockchain with:
- **Encrypted state**: Contract data is encrypted and only accessible by authorized parties
- **Private execution**: Contract logic executes in secure enclaves (Trusted Execution Environments)
- **Selective disclosure**: Developers control what data is visible and to whom
- **Full composability**: Contracts can interact while preserving privacy

All contract interactions through this MCP server are automatically encrypted and decrypted.

## Contract Lifecycle

### 1. Upload Contract Code

Upload WASM bytecode to the blockchain:

```
secret_upload_contract(wasm_byte_code="<base64_encoded_wasm>")
```

**Returns**: `code_id` - A unique identifier for the uploaded code

**Notes**:
- WASM file must be base64 encoded
- Requires active wallet with sufficient gas
- Code is immutable once uploaded
- Multiple contracts can be instantiated from one code_id

**Example**:
```python
import base64

# Read WASM file
with open("contract.wasm", "rb") as f:
    wasm_bytes = f.read()

# Base64 encode
wasm_base64 = base64.b64encode(wasm_bytes).decode()

# Upload
result = secret_upload_contract(wasm_byte_code=wasm_base64)
code_id = result["code_id"]
```

### 2. Instantiate Contract

Create a contract instance from uploaded code:

```
secret_instantiate_contract(
    code_id=1,
    init_msg={"count": 0, "owner": "secret1..."},
    label="my_counter_v1",
    funds=[{"denom": "uscrt", "amount": "1000000"}]  # Optional
)
```

**Returns**: `contract_address` - The address of the new contract instance

**Parameters**:
- `code_id`: The code_id from upload
- `init_msg`: Initialization message (contract-specific JSON)
- `label`: Human-readable label (must be unique)
- `funds`: Optional tokens to send to contract

**Notes**:
- Label must be unique per wallet
- Init message structure depends on the contract
- Contract address is deterministic based on code_id, creator, and label

### 3. Execute Contract (Write)

Modify contract state by executing a message:

```
secret_execute_contract(
    contract_address="secret1contractcontractcontractcontractcontra",
    execute_msg={"increment": {}},
    funds=[{"denom": "uscrt", "amount": "1000000"}]  # Optional
)
```

**Parameters**:
- `contract_address`: Address of the contract instance
- `execute_msg`: Execution message (contract-specific JSON)
- `funds`: Optional tokens to send with execution

**Notes**:
- Requires active wallet
- Costs gas (transaction fee)
- Messages are automatically encrypted
- Can attach tokens if contract accepts them
- State changes are permanent

**Common Patterns**:
```
# Simple action
{"action_name": {}}

# Action with parameters
{"transfer": {"recipient": "secret1...", "amount": "1000"}}

# Action with nested data
{"update_config": {"new_owner": "secret1...", "new_settings": {...}}}
```

### 4. Query Contract (Read)

Read contract state without modifying it:

```
secret_query_contract(
    contract_address="secret1contractcontractcontractcontractcontra",
    query_msg={"get_count": {}}
)
```

**Parameters**:
- `contract_address`: Address of the contract instance
- `query_msg`: Query message (contract-specific JSON)

**Notes**:
- No gas cost (read-only)
- Queries are automatically encrypted
- Responses are automatically decrypted
- Does not require active wallet (usually)
- Cannot modify state

**Common Query Patterns**:
```
# Get simple value
{"get_value": {}}

# Get with parameters
{"balance": {"address": "secret1..."}}

# Get paginated data
{"list_items": {"start_after": "key", "limit": 10}}
```

### 5. Batch Execute (Multiple Operations)

Execute multiple contract calls in a single transaction:

```
secret_batch_execute(
    messages=[
        {
            "contract_address": "secret1contractcontractcontractcontractcontra",
            "execute_msg": {"action1": {}},
            "funds": []
        },
        {
            "contract_address": "secret1othercontractcontractcontractcontract",
            "execute_msg": {"action2": {}},
            "funds": [{"denom": "uscrt", "amount": "1000000"}]
        }
    ]
)
```

**Benefits**:
- Atomic execution (all succeed or all fail)
- Lower gas costs than separate transactions
- Maintain state consistency across operations
- Useful for complex workflows

### 6. Migrate Contract (Upgrade)

Upgrade a contract to new code:

```
secret_migrate_contract(
    contract_address="secret1contractcontractcontractcontractcontra",
    new_code_id=2,
    migrate_msg={"upgrade": {"version": "2.0"}}
)
```

**Requirements**:
- Contract must be designed as migratable
- Caller must be the contract admin
- New code must be compatible

## Privacy Features

### Automatic Encryption

All contract interactions are automatically encrypted by this MCP server:

1. **Execute messages**: Encrypted before sending to chain
2. **Query messages**: Encrypted before sending to chain
3. **Responses**: Automatically decrypted when received
4. **State**: Encrypted at rest in the blockchain

### Viewing Keys and Permits

Some contracts use viewing keys or permits for authorization:

**Viewing Keys** (older pattern):
```
# Create viewing key
secret_execute_contract(
    contract_address="secret1...",
    execute_msg={"create_viewing_key": {"entropy": "random_string"}}
)

# Use viewing key in queries
secret_query_contract(
    contract_address="secret1...",
    query_msg={
        "balance": {
            "address": "secret1...",
            "key": "viewing_key_string"
        }
    }
)
```

**Query Permits** (newer, better pattern):
- Automatically handled by Secret Network SDK
- More secure and flexible
- No need for manual key management

### Privacy Best Practices

1. **Minimize on-chain data**: Only store what's necessary
2. **Use query permits**: Prefer permits over viewing keys
3. **Validate inputs**: Always validate in contract code
4. **Audit contracts**: Review privacy guarantees before use
5. **Test thoroughly**: Privacy bugs are harder to detect

## Examples

### Example 1: Counter Contract

```
# 1. Upload
upload_result = secret_upload_contract(wasm_byte_code=counter_wasm_base64)
code_id = upload_result["code_id"]

# 2. Instantiate
init_result = secret_instantiate_contract(
    code_id=code_id,
    init_msg={"count": 0},
    label="my_counter_v1"
)
contract_address = init_result["contract_address"]

# 3. Query initial state
count = secret_query_contract(
    contract_address=contract_address,
    query_msg={"get_count": {}}
)
# Returns: {"count": 0}

# 4. Increment
secret_execute_contract(
    contract_address=contract_address,
    execute_msg={"increment": {}}
)

# 5. Query updated state
count = secret_query_contract(
    contract_address=contract_address,
    query_msg={"get_count": {}}
)
# Returns: {"count": 1}
```

### Example 2: SNIP-20 Token (Secret Network Token Standard)

```
# Instantiate token
token_result = secret_instantiate_contract(
    code_id=snip20_code_id,
    init_msg={
        "name": "My Secret Token",
        "symbol": "MST",
        "decimals": 6,
        "initial_balances": [
            {"address": "secret1...", "amount": "1000000000"}
        ],
        "prng_seed": "random_entropy"
    },
    label="my_secret_token"
)
token_address = token_result["contract_address"]

# Create viewing key
vk_result = secret_execute_contract(
    contract_address=token_address,
    execute_msg={"create_viewing_key": {"entropy": "my_random_string"}}
)
viewing_key = vk_result["viewing_key"]

# Check balance
balance = secret_query_contract(
    contract_address=token_address,
    query_msg={
        "balance": {
            "address": "secret1...",
            "key": viewing_key
        }
    }
)

# Transfer tokens
secret_execute_contract(
    contract_address=token_address,
    execute_msg={
        "transfer": {
            "recipient": "secret1...",
            "amount": "1000000"
        }
    }
)
```

### Example 3: NFT Contract (SNIP-721)

```
# Mint NFT
secret_execute_contract(
    contract_address=nft_contract,
    execute_msg={
        "mint_nft": {
            "token_id": "1",
            "owner": "secret1...",
            "public_metadata": {
                "name": "Secret NFT #1",
                "description": "A private NFT"
            },
            "private_metadata": {
                "secret_attribute": "only_owner_can_see"
            }
        }
    }
)

# Query public info (anyone can see)
public_info = secret_query_contract(
    contract_address=nft_contract,
    query_msg={"nft_info": {"token_id": "1"}}
)

# Query private info (requires viewing key or permit)
private_info = secret_query_contract(
    contract_address=nft_contract,
    query_msg={
        "private_metadata": {
            "token_id": "1",
            "viewer": {"address": "secret1...", "viewing_key": "..."}
        }
    }
)
```

### Example 4: Batch Operations

```
# Batch execute multiple token transfers
secret_batch_execute(
    messages=[
        {
            "contract_address": token_address,
            "execute_msg": {
                "transfer": {
                    "recipient": "secret1...",
                    "amount": "1000000"
                }
            }
        },
        {
            "contract_address": token_address,
            "execute_msg": {
                "transfer": {
                    "recipient": "secret1...",
                    "amount": "2000000"
                }
            }
        }
    ]
)
```

## Best Practices

### Development

1. **Test on testnet first**
   - Always deploy to pulsar-3 (testnet) before mainnet
   - Test all functions thoroughly
   - Verify privacy guarantees

2. **Use proper error handling**
   - Check return values
   - Handle contract errors gracefully
   - Validate inputs before sending

3. **Optimize gas usage**
   - Use batch operations when possible
   - Minimize storage writes
   - Estimate gas before execution

4. **Version your contracts**
   - Use semantic versioning in labels
   - Document changes between versions
   - Plan migration paths

### Security

1. **Verify code hashes**
   - Check uploaded code matches expected hash
   - Use `secret_get_code_info(code_id)` to verify

2. **Audit before production**
   - Review contract code for vulnerabilities
   - Test edge cases
   - Consider professional audits for high-value contracts

3. **Manage admin keys carefully**
   - Use multisig for contract admin
   - Consider making contracts immutable if appropriate
   - Document admin capabilities

4. **Monitor contract activity**
   - Track contract transactions
   - Set up alerts for unusual activity
   - Regular security reviews

### Privacy

1. **Understand privacy guarantees**
   - Know what data is private vs public
   - Document privacy expectations
   - Test privacy features thoroughly

2. **Use query permits**
   - Prefer permits over viewing keys
   - Implement permit verification in contracts
   - Educate users on permit usage

3. **Minimize data leakage**
   - Be careful with public events
   - Avoid timing-based information leaks
   - Consider MEV implications

### Operations

1. **Keep good records**
   - Save code_ids and contract addresses
   - Document initialization parameters
   - Maintain deployment history

2. **Plan for upgrades**
   - Design contracts as migratable when appropriate
   - Test migration process on testnet
   - Have rollback plan

3. **Monitor gas costs**
   - Use `secret_estimate_gas()` before operations
   - Check `secret_get_gas_prices()` for current rates
   - Optimize for cost when possible

## Common Patterns

### Factory Pattern
```
# Deploy factory contract
factory_result = secret_instantiate_contract(
    code_id=factory_code_id,
    init_msg={"template_code_id": template_code_id},
    label="token_factory"
)

# Use factory to create instances
secret_execute_contract(
    contract_address=factory_result["contract_address"],
    execute_msg={
        "create_token": {
            "name": "New Token",
            "symbol": "NEW"
        }
    }
)
```

### Proxy/Upgrade Pattern
```
# Deploy proxy contract
proxy_result = secret_instantiate_contract(
    code_id=proxy_code_id,
    init_msg={"implementation": implementation_address},
    label="upgradeable_contract"
)

# Later, upgrade implementation
secret_execute_contract(
    contract_address=proxy_result["contract_address"],
    execute_msg={
        "upgrade": {
            "new_implementation": new_implementation_address
        }
    }
)
```

### Access Control Pattern
```
# Execute with role check
secret_execute_contract(
    contract_address=contract_address,
    execute_msg={
        "admin_action": {
            "action": "update_config",
            "params": {...}
        }
    }
)
# Contract internally verifies caller has admin role
```

## Troubleshooting

### Common Issues

**Contract not found**
- Verify contract address is correct
- Check you're on the right network (testnet vs mainnet)
- Ensure contract was successfully instantiated

**Execution failed**
- Check error message for details
- Verify execute_msg format matches contract expectations
- Ensure sufficient gas and funds
- Confirm wallet has necessary permissions

**Query returns error**
- Verify query_msg format
- Check if query requires viewing key/permit
- Ensure contract is properly initialized

**Gas estimation fails**
- Validate message format
- Check contract state is compatible with operation
- Verify you have active wallet loaded

### Getting Help

1. **Check contract documentation**: Each contract should document its messages
2. **Use contract info**: `secret_get_contract_info(address)` for details
3. **Review contract history**: `secret_get_contract_history(address)` for update history
4. **Inspect transactions**: `secret_get_transaction(txhash)` to debug failures
5. **Test on testnet**: Always debug on testnet first

## Additional Tools

### Contract Information
```
# Get contract details
secret_get_contract_info(contract_address="secret1...")

# Get contract history
secret_get_contract_history(contract_address="secret1...")

# Get code info
secret_get_code_info(code_id=1)

# List all uploaded codes
secret_list_codes()
```

### Gas Management
```
# Estimate gas for execution
secret_estimate_gas(
    messages=[{
        "contract_address": "secret1...",
        "execute_msg": {...}
    }]
)

# Simulate without broadcasting
secret_simulate_transaction(
    messages=[{
        "contract_address": "secret1...",
        "execute_msg": {...}
    }]
)
```

## Resources

- **Secret Network Docs**: https://docs.scrt.network
- **Contract Templates**: https://github.com/scrtlabs/secret-template
- **SNIP Standards**: Token (SNIP-20), NFT (SNIP-721), etc.
- **Secret Toolkit**: Helper libraries for contract development
- **Secret IDE**: https://www.secretsaturn.net/devtools

## Summary

Secret Network smart contracts provide powerful privacy features while maintaining blockchain security and decentralization. Key points:

- **Privacy by default**: All interactions are encrypted
- **Simple workflow**: Upload → Instantiate → Execute/Query
- **Flexible patterns**: Supports upgrades, factories, and more
- **Test thoroughly**: Use testnet before mainnet
- **Monitor carefully**: Track gas costs and contract activity

Start with simple contracts on testnet, learn the patterns, and gradually build more complex privacy-preserving applications!
"""

    # If a specific operation is requested, provide focused guidance
    operation_guides = {
        "upload": """
# Upload Contract Guide

## Overview
Uploading stores WASM bytecode on the blockchain, creating reusable code that can be instantiated multiple times.

## Preparation

### 1. Compile Contract
```bash
# Using cargo in contract directory
cargo build --release --target wasm32-unknown-unknown

# Optimize (recommended)
docker run --rm -v $(pwd):/code \
  --mount type=volume,source=registry_cache,target=/usr/local/cargo/registry \
  cosmwasm/rust-optimizer:0.12.13
```

### 2. Base64 Encode
```python
import base64

with open("contract.wasm", "rb") as f:
    wasm_bytes = f.read()

wasm_base64 = base64.b64encode(wasm_bytes).decode()
```

## Upload

```
result = secret_upload_contract(wasm_byte_code=wasm_base64)
code_id = result["code_id"]
```

## Verification

```
# Get code info
info = secret_get_code_info(code_id=code_id)

# Verify code hash matches expected
expected_hash = "sha256_hash_of_your_wasm"
assert info["code_hash"] == expected_hash
```

## Tips
- Optimize WASM before upload (reduces gas)
- Save code_id for future instantiations
- Verify code hash after upload
- Code is immutable once uploaded
""",
        "instantiate": """
# Instantiate Contract Guide

## Overview
Instantiation creates a contract instance from uploaded code with its own state and address.

## Parameters

```
result = secret_instantiate_contract(
    code_id=1,                    # From upload
    init_msg={...},               # Contract-specific
    label="unique_label_v1",      # Must be unique
    funds=[{                      # Optional
        "denom": "uscrt",
        "amount": "1000000"
    }]
)
contract_address = result["contract_address"]
```

## Init Message Structure

The `init_msg` varies by contract. Common patterns:

### Simple Config
```json
{
  "owner": "secret1...",
  "config": {
    "fee": "100",
    "enabled": true
  }
}
```

### Token (SNIP-20)
```json
{
  "name": "My Token",
  "symbol": "MTK",
  "decimals": 6,
  "initial_balances": [
    {"address": "secret1...", "amount": "1000000"}
  ],
  "prng_seed": "random_entropy_string"
}
```

### NFT (SNIP-721)
```json
{
  "name": "My NFT Collection",
  "symbol": "MNFT",
  "admin": "secret1...",
  "entropy": "random_string",
  "config": {
    "public_token_supply": true,
    "enable_burn": true
  }
}
```

## Tips
- Label must be unique per wallet
- Test init_msg format on testnet first
- Save contract address securely
- Can instantiate same code_id multiple times
- Optional funds are sent to contract during init
""",
        "execute": """
# Execute Contract Guide

## Overview
Execute operations modify contract state and require gas fees.

## Basic Execution

```
result = secret_execute_contract(
    contract_address="secret1...",
    execute_msg={...},
    funds=[]  # Optional
)
txhash = result["txhash"]
```

## Common Execute Patterns

### Simple Action
```json
{"increment": {}}
{"reset": {}}
{"pause": {}}
```

### Action with Parameters
```json
{
  "transfer": {
    "recipient": "secret1...",
    "amount": "1000000"
  }
}
```

### Complex Actions
```json
{
  "update_config": {
    "owner": "secret1...",
    "settings": {
      "fee_rate": "100",
      "enabled": true
    }
  }
}
```

### With Funds
```python
secret_execute_contract(
    contract_address="secret1...",
    execute_msg={"deposit": {}},
    funds=[{"denom": "uscrt", "amount": "5000000"}]
)
```

## Gas Management

### Estimate First
```
estimate = secret_estimate_gas(
    messages=[{
        "contract_address": "secret1...",
        "execute_msg": {...}
    }]
)
```

### Simulate
```
simulation = secret_simulate_transaction(
    messages=[{
        "contract_address": "secret1...",
        "execute_msg": {...}
    }]
)
```

## Error Handling

Check transaction status:
```
tx = secret_get_transaction(txhash=result["txhash"])
if tx["code"] != 0:
    print(f"Execution failed: {tx['raw_log']}")
```

## Tips
- Always validate execute_msg format
- Estimate gas for expensive operations
- Check balance before attaching funds
- Monitor transaction status
- Messages are automatically encrypted
""",
        "query": """
# Query Contract Guide

## Overview
Query operations read contract state without modifying it. No gas cost.

## Basic Query

```
result = secret_query_contract(
    contract_address="secret1...",
    query_msg={...}
)
```

## Common Query Patterns

### Simple Getters
```json
{"get_count": {}}
{"get_config": {}}
{"get_owner": {}}
```

### With Parameters
```json
{
  "balance": {
    "address": "secret1..."
  }
}
```

### Pagination
```json
{
  "list_items": {
    "start_after": "key",
    "limit": 10
  }
}
```

### With Viewing Key
```json
{
  "balance": {
    "address": "secret1...",
    "key": "viewing_key_string"
  }
}
```

### With Query Permit
```json
{
  "balance": {
    "address": "secret1...",
    "permit": {
      "params": {...},
      "signature": {...}
    }
  }
}
```

## Creating Viewing Keys

```
# Create key
vk_result = secret_execute_contract(
    contract_address="secret1...",
    execute_msg={
        "create_viewing_key": {
            "entropy": "random_string"
        }
    }
)
viewing_key = vk_result["viewing_key"]

# Use in query
result = secret_query_contract(
    contract_address="secret1...",
    query_msg={
        "balance": {
            "address": "secret1...",
            "key": viewing_key
        }
    }
)
```

## Tips
- Queries don't cost gas
- Responses are automatically decrypted
- Most queries don't need active wallet
- Use viewing keys/permits for private data
- Check contract docs for available queries
""",
        "migrate": """
# Migrate Contract Guide

## Overview
Migration upgrades a contract to new code while preserving its state and address.

## Requirements

1. **Contract must be migratable**: Set during instantiation
2. **Must be admin**: Only admin can migrate
3. **New code must be compatible**: State structure should match

## Migration Process

### 1. Upload New Code
```
new_result = secret_upload_contract(wasm_byte_code=new_wasm_base64)
new_code_id = new_result["code_id"]
```

### 2. Migrate Contract
```
migrate_result = secret_migrate_contract(
    contract_address="secret1...",
    new_code_id=new_code_id,
    migrate_msg={
        "upgrade": {
            "version": "2.0",
            "new_features": ["feature1", "feature2"]
        }
    }
)
```

### 3. Verify Migration
```
# Check contract info
info = secret_get_contract_info(contract_address="secret1...")
assert info["code_id"] == new_code_id

# Test new functionality
result = secret_query_contract(
    contract_address="secret1...",
    query_msg={"get_version": {}}
)
```

## Migration Message

The `migrate_msg` format depends on the new contract code:

```json
{
  "upgrade": {
    "version": "2.0",
    "migrate_data": true
  }
}
```

## Best Practices

1. **Test migration on testnet first**
2. **Backup important data** before migration
3. **Document state changes** in migration
4. **Have rollback plan** ready
5. **Notify users** of planned migration

## Making Contracts Migratable

In contract instantiation:
```
secret_instantiate_contract(
    code_id=code_id,
    init_msg={
        "admin": "secret1...",  # Admin can migrate
        ...
    },
    label="migratable_contract"
)
```

## Tips
- Only admin can migrate
- Contract address stays the same
- State must be compatible
- Test thoroughly before mainnet migration
- Consider making contracts immutable if not needed
""",
        "batch": """
# Batch Execute Guide

## Overview
Batch execution runs multiple contract operations in a single transaction, providing atomicity and gas efficiency.

## Basic Batch

```
result = secret_batch_execute(
    messages=[
        {
            "contract_address": "secret1...",
            "execute_msg": {"action1": {}},
            "funds": []
        },
        {
            "contract_address": "secret1...",
            "execute_msg": {"action2": {}},
            "funds": [{"denom": "uscrt", "amount": "1000000"}]
        }
    ]
)
```

## Use Cases

### 1. Multi-Token Transfer
```
secret_batch_execute(
    messages=[
        {
            "contract_address": token1_address,
            "execute_msg": {
                "transfer": {
                    "recipient": "secret1...",
                    "amount": "1000000"
                }
            }
        },
        {
            "contract_address": token2_address,
            "execute_msg": {
                "transfer": {
                    "recipient": "secret1...",
                    "amount": "2000000"
                }
            }
        }
    ]
)
```

### 2. Approve and Execute
```
secret_batch_execute(
    messages=[
        {
            "contract_address": token_address,
            "execute_msg": {
                "increase_allowance": {
                    "spender": dex_address,
                    "amount": "1000000"
                }
            }
        },
        {
            "contract_address": dex_address,
            "execute_msg": {
                "swap": {
                    "offer_asset": "token1",
                    "amount": "1000000"
                }
            }
        }
    ]
)
```

### 3. Complex Workflow
```
secret_batch_execute(
    messages=[
        {
            "contract_address": contract1,
            "execute_msg": {"prepare": {}}
        },
        {
            "contract_address": contract2,
            "execute_msg": {"process": {}}
        },
        {
            "contract_address": contract3,
            "execute_msg": {"finalize": {}}
        }
    ]
)
```

## Benefits

1. **Atomicity**: All operations succeed or all fail
2. **Gas Efficiency**: Lower total gas than separate transactions
3. **State Consistency**: No intermediate states visible
4. **Convenience**: One transaction to track

## Limitations

- All operations must succeed
- Gas limit applies to entire batch
- Cannot use results from earlier operations in later ones
- Order matters

## Tips
- Estimate gas for entire batch first
- Order operations logically
- Handle errors gracefully
- Use for related operations
- Test batch on testnet first
""",
    }

    if operation and operation.lower() in operation_guides:
        return operation_guides[operation.lower()]

    return base_guide
