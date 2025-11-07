"""Main entry point for the Secret Network MCP server.

This module provides the FastMCP server instance and registers all tools,
prompts, and resources for Secret Network blockchain interaction.
"""

import asyncio
from fastmcp import FastMCP

from mcp_scrt.core.session import Session
from mcp_scrt.sdk.client import ClientPool
from mcp_scrt.tools.base import ToolExecutionContext
from mcp_scrt.types import NetworkType
from mcp_scrt.config import get_settings
from mcp_scrt.utils.logging import setup_logging

# Import all tools
from mcp_scrt.tools.network import (
    ConfigureNetworkTool,
    GetNetworkInfoTool,
    GetGasPricesTool,
    HealthCheckTool,
)
from mcp_scrt.tools.wallet import (
    CreateWalletTool,
    ImportWalletTool,
    SetActiveWalletTool,
    GetActiveWalletTool,
    ListWalletsTool,
    RemoveWalletTool,
)
from mcp_scrt.tools.bank import (
    GetBalanceTool,
    SendTokensTool,
    MultiSendTool,
    GetTotalSupplyTool,
    GetDenomMetadataTool,
)
from mcp_scrt.tools.blockchain import (
    GetBlockTool,
    GetLatestBlockTool,
    GetBlockByHashTool,
    GetNodeInfoTool,
    GetSyncingStatusTool,
)
from mcp_scrt.tools.account import (
    GetAccountTool,
    GetAccountTransactionsTool,
    GetAccountTxCountTool,
)
from mcp_scrt.tools.transaction import (
    GetTransactionTool,
    SearchTransactionsTool,
    EstimateGasTool,
    SimulateTransactionTool,
    GetTransactionStatusTool,
)
from mcp_scrt.tools.staking import (
    GetValidatorsTool,
    GetValidatorTool,
    DelegateTool,
    UndelegateTool,
    RedelegateTool,
    GetDelegationsTool,
    GetUnbondingTool,
    GetRedelegationsTool,
)
from mcp_scrt.tools.rewards import (
    GetRewardsTool,
    WithdrawRewardsTool,
    SetWithdrawAddressTool,
    GetCommunityPoolTool,
)
from mcp_scrt.tools.governance import (
    GetProposalsTool,
    GetProposalTool,
    SubmitProposalTool,
    DepositProposalTool,
    VoteProposalTool,
    GetVoteTool,
)
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
from mcp_scrt.tools.ibc import (
    IBCTransferTool,
    GetIBCChannelsTool,
    GetIBCChannelTool,
    GetIBCDenomTraceTool,
)

# Import prompts
from mcp_scrt.prompts.guide import secret_network_guide
from mcp_scrt.prompts.contracts import smart_contracts_guide

# Import resources
from mcp_scrt.resources.session import get_session_state_resource
from mcp_scrt.resources.wallets import get_wallets_list_resource
from mcp_scrt.resources.network import get_network_config_resource
from mcp_scrt.resources.validators import get_top_validators_resource


# Create FastMCP server
mcp = FastMCP(
    name="secret-network-mcp",
)

# Initialize global context
settings = get_settings()

# Configure logging (must be done before any logging occurs)
# IMPORTANT: Logging goes to stderr for MCP compatibility
setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
)

session = Session(network=settings.secret_network)
session.start()

client_pool = ClientPool(
    network=settings.secret_network,
    max_connections=settings.max_connections,
)

context = ToolExecutionContext(
    session=session,
    client_pool=client_pool,
    network=settings.secret_network,
)


# Register all tools using decorators
@mcp.tool()
async def secret_configure_network(network: str) -> dict:
    """Configure the Secret Network (testnet, mainnet, or custom).

    Args:
        network: Network type (testnet, mainnet, or custom)

    Returns:
        Configuration result with network details
    """
    tool = ConfigureNetworkTool(context)
    return await tool.run({"network": network})


@mcp.tool()
async def secret_get_network_info() -> dict:
    """Get current network information including chain ID and endpoints.

    Returns:
        Network information
    """
    tool = GetNetworkInfoTool(context)
    return await tool.run({})


@mcp.tool()
async def secret_get_gas_prices() -> dict:
    """Get current gas prices for the network.

    Returns:
        Gas prices information
    """
    tool = GetGasPricesTool(context)
    return await tool.run({})


@mcp.tool()
async def secret_health_check() -> dict:
    """Check the health status of the Secret Network node.

    Returns:
        Health check status
    """
    tool = HealthCheckTool(context)
    return await tool.run({})


@mcp.tool()
async def secret_create_wallet(name: str) -> dict:
    """Create a new HD wallet with a generated mnemonic.

    Args:
        name: Unique name for the wallet

    Returns:
        Wallet details including address and mnemonic (SAVE THE MNEMONIC!)
    """
    tool = CreateWalletTool(context)
    return await tool.run({"name": name})


@mcp.tool()
async def secret_import_wallet(name: str, mnemonic: str) -> dict:
    """Import an existing wallet using a mnemonic phrase.

    Args:
        name: Unique name for the wallet
        mnemonic: 12 or 24 word mnemonic phrase

    Returns:
        Wallet details
    """
    tool = ImportWalletTool(context)
    return await tool.run({"name": name, "mnemonic": mnemonic})


@mcp.tool()
async def secret_set_active_wallet(name: str) -> dict:
    """Set the active wallet for operations.

    Args:
        name: Name of the wallet to activate

    Returns:
        Success status
    """
    tool = SetActiveWalletTool(context)
    return await tool.run({"name": name})


@mcp.tool()
async def secret_get_active_wallet() -> dict:
    """Get the currently active wallet.

    Returns:
        Active wallet details
    """
    tool = GetActiveWalletTool(context)
    return await tool.run({})


@mcp.tool()
async def secret_list_wallets() -> dict:
    """List all loaded wallets in the session.

    Returns:
        List of wallet names and addresses
    """
    tool = ListWalletsTool(context)
    return await tool.run({})


@mcp.tool()
async def secret_remove_wallet(name: str) -> dict:
    """Remove a wallet from the session.

    Args:
        name: Name of the wallet to remove

    Returns:
        Success status
    """
    tool = RemoveWalletTool(context)
    return await tool.run({"name": name})


@mcp.tool()
async def secret_get_balance(address: str = None) -> dict:
    """Get token balances for an address or active wallet.

    Args:
        address: Optional Secret Network address (uses active wallet if not provided)

    Returns:
        Token balances
    """
    tool = GetBalanceTool(context)
    params = {"address": address} if address else {}
    return await tool.run(params)


@mcp.tool()
async def secret_send_tokens(
    recipient: str,
    amount: str,
    denom: str = "uscrt",
    memo: str = "",
) -> dict:
    """Send tokens to another address.

    Args:
        recipient: Recipient Secret Network address
        amount: Amount to send (in micro-units, e.g., "1000000" for 1 SCRT)
        denom: Token denomination (default: uscrt)
        memo: Optional transaction memo

    Returns:
        Transaction hash and details
    """
    tool = SendTokensTool(context)
    return await tool.run({
        "to_address": recipient,
        "amount": amount,
        "denom": denom,
        "memo": memo,
    })


@mcp.tool()
async def secret_multi_send(recipients: list) -> dict:
    """Send tokens to multiple recipients in a single transaction.

    Args:
        recipients: List of recipient objects with 'address', 'amount', and 'denom'

    Returns:
        Transaction hash and details
    """
    tool = MultiSendTool(context)
    return await tool.run({"recipients": recipients})


@mcp.tool()
async def secret_get_total_supply(denom: str = None) -> dict:
    """Get total supply of tokens.

    Args:
        denom: Optional token denomination (returns all if not specified)

    Returns:
        Total supply information
    """
    tool = GetTotalSupplyTool(context)
    params = {"denom": denom} if denom else {}
    return await tool.run(params)


@mcp.tool()
async def secret_get_denom_metadata(denom: str) -> dict:
    """Get metadata for a token denomination.

    Args:
        denom: Token denomination

    Returns:
        Denomination metadata
    """
    tool = GetDenomMetadataTool(context)
    return await tool.run({"denom": denom})


@mcp.tool()
async def secret_get_block(height: int) -> dict:
    """Get block information by height.

    Args:
        height: Block height

    Returns:
        Block information
    """
    tool = GetBlockTool(context)
    return await tool.run({"height": height})


@mcp.tool()
async def secret_get_latest_block() -> dict:
    """Get the latest block information.

    Returns:
        Latest block information
    """
    tool = GetLatestBlockTool(context)
    return await tool.run({})


@mcp.tool()
async def secret_get_block_by_hash(block_hash: str) -> dict:
    """Get block information by hash.

    Args:
        block_hash: Block hash

    Returns:
        Block information
    """
    tool = GetBlockByHashTool(context)
    return await tool.run({"block_hash": block_hash})


@mcp.tool()
async def secret_get_node_info() -> dict:
    """Get node information.

    Returns:
        Node information including version and network
    """
    tool = GetNodeInfoTool(context)
    return await tool.run({})


@mcp.tool()
async def secret_get_syncing_status() -> dict:
    """Get node syncing status.

    Returns:
        Syncing status
    """
    tool = GetSyncingStatusTool(context)
    return await tool.run({})


@mcp.tool()
async def secret_get_account(address: str) -> dict:
    """Get account information.

    Args:
        address: Secret Network address

    Returns:
        Account information including sequence and account number
    """
    tool = GetAccountTool(context)
    return await tool.run({"address": address})


@mcp.tool()
async def secret_get_account_transactions(address: str, limit: int = 100) -> dict:
    """Get transactions for an account.

    Args:
        address: Secret Network address
        limit: Maximum number of transactions (default: 100)

    Returns:
        List of transactions
    """
    tool = GetAccountTransactionsTool(context)
    return await tool.run({"address": address, "limit": limit})


@mcp.tool()
async def secret_get_account_tx_count(address: str) -> dict:
    """Get transaction count for an account.

    Args:
        address: Secret Network address

    Returns:
        Transaction count
    """
    tool = GetAccountTxCountTool(context)
    return await tool.run({"address": address})


@mcp.tool()
async def secret_get_transaction(tx_hash: str) -> dict:
    """Get transaction by hash.

    Args:
        tx_hash: Transaction hash

    Returns:
        Transaction details
    """
    tool = GetTransactionTool(context)
    return await tool.run({"tx_hash": tx_hash})


@mcp.tool()
async def secret_search_transactions(query: str, limit: int = 100) -> dict:
    """Search for transactions.

    Args:
        query: Search query (e.g., "message.sender='secret1...'")
        limit: Maximum number of results (default: 100)

    Returns:
        List of matching transactions
    """
    tool = SearchTransactionsTool(context)
    return await tool.run({"query": query, "limit": limit})


@mcp.tool()
async def secret_estimate_gas(messages: list) -> dict:
    """Estimate gas for messages.

    Args:
        messages: List of messages to estimate

    Returns:
        Estimated gas amount
    """
    tool = EstimateGasTool(context)
    return await tool.run({"messages": messages})


@mcp.tool()
async def secret_simulate_transaction(messages: list) -> dict:
    """Simulate a transaction.

    Args:
        messages: List of messages to simulate

    Returns:
        Simulation result with gas used
    """
    tool = SimulateTransactionTool(context)
    return await tool.run({"messages": messages})


@mcp.tool()
async def secret_get_transaction_status(tx_hash: str) -> dict:
    """Get transaction status.

    Args:
        tx_hash: Transaction hash

    Returns:
        Transaction status (pending, success, failed)
    """
    tool = GetTransactionStatusTool(context)
    return await tool.run({"tx_hash": tx_hash})


@mcp.tool()
async def secret_get_validators(status: str = "BOND_STATUS_BONDED") -> dict:
    """Get list of validators.

    Args:
        status: Validator status filter (default: BOND_STATUS_BONDED)

    Returns:
        List of validators
    """
    tool = GetValidatorsTool(context)
    return await tool.run({"status": status})


@mcp.tool()
async def secret_get_validator(validator_address: str) -> dict:
    """Get validator information.

    Args:
        validator_address: Validator operator address

    Returns:
        Validator details
    """
    tool = GetValidatorTool(context)
    return await tool.run({"validator_address": validator_address})


@mcp.tool()
async def secret_delegate(validator_address: str, amount: str) -> dict:
    """Delegate tokens to a validator.

    Args:
        validator_address: Validator operator address
        amount: Amount to delegate (in micro-units)

    Returns:
        Transaction hash and details
    """
    tool = DelegateTool(context)
    return await tool.run({
        "validator_address": validator_address,
        "amount": amount,
    })


@mcp.tool()
async def secret_undelegate(validator_address: str, amount: str) -> dict:
    """Undelegate tokens from a validator.

    Args:
        validator_address: Validator operator address
        amount: Amount to undelegate (in micro-units)

    Returns:
        Transaction hash and details
    """
    tool = UndelegateTool(context)
    return await tool.run({
        "validator_address": validator_address,
        "amount": amount,
    })


@mcp.tool()
async def secret_redelegate(
    src_validator: str,
    dst_validator: str,
    amount: str,
) -> dict:
    """Redelegate tokens from one validator to another.

    Args:
        src_validator: Source validator operator address
        dst_validator: Destination validator operator address
        amount: Amount to redelegate (in micro-units)

    Returns:
        Transaction hash and details
    """
    tool = RedelegateTool(context)
    return await tool.run({
        "src_validator": src_validator,
        "dst_validator": dst_validator,
        "amount": amount,
    })


@mcp.tool()
async def secret_get_delegations(address: str = None) -> dict:
    """Get delegations for an address.

    Args:
        address: Optional address (uses active wallet if not provided)

    Returns:
        List of delegations
    """
    tool = GetDelegationsTool(context)
    params = {"address": address} if address else {}
    return await tool.run(params)


@mcp.tool()
async def secret_get_unbonding(address: str = None) -> dict:
    """Get unbonding delegations for an address.

    Args:
        address: Optional address (uses active wallet if not provided)

    Returns:
        List of unbonding delegations
    """
    tool = GetUnbondingTool(context)
    params = {"address": address} if address else {}
    return await tool.run(params)


@mcp.tool()
async def secret_get_redelegations(address: str = None) -> dict:
    """Get redelegations for an address.

    Args:
        address: Optional address (uses active wallet if not provided)

    Returns:
        List of redelegations
    """
    tool = GetRedelegationsTool(context)
    params = {"address": address} if address else {}
    return await tool.run(params)


@mcp.tool()
async def secret_get_rewards(address: str = None) -> dict:
    """Get staking rewards for an address.

    Args:
        address: Optional address (uses active wallet if not provided)

    Returns:
        Staking rewards
    """
    tool = GetRewardsTool(context)
    params = {"address": address} if address else {}
    return await tool.run(params)


@mcp.tool()
async def secret_withdraw_rewards(validator_address: str = None) -> dict:
    """Withdraw staking rewards.

    Args:
        validator_address: Optional validator address (withdraws from all if not provided)

    Returns:
        Transaction hash and details
    """
    tool = WithdrawRewardsTool(context)
    params = {"validator_address": validator_address} if validator_address else {}
    return await tool.run(params)


@mcp.tool()
async def secret_set_withdraw_address(withdraw_address: str) -> dict:
    """Set the withdraw address for rewards.

    Args:
        withdraw_address: Address to receive rewards

    Returns:
        Transaction hash and details
    """
    tool = SetWithdrawAddressTool(context)
    return await tool.run({"withdraw_address": withdraw_address})


@mcp.tool()
async def secret_get_community_pool() -> dict:
    """Get community pool balance.

    Returns:
        Community pool balance
    """
    tool = GetCommunityPoolTool(context)
    return await tool.run({})


@mcp.tool()
async def secret_get_proposals(status: str = None) -> dict:
    """Get governance proposals.

    Args:
        status: Optional status filter (PROPOSAL_STATUS_VOTING_PERIOD, etc.)

    Returns:
        List of proposals
    """
    tool = GetProposalsTool(context)
    params = {"status": status} if status else {}
    return await tool.run(params)


@mcp.tool()
async def secret_get_proposal(proposal_id: int) -> dict:
    """Get a specific governance proposal.

    Args:
        proposal_id: Proposal ID

    Returns:
        Proposal details
    """
    tool = GetProposalTool(context)
    return await tool.run({"proposal_id": proposal_id})


@mcp.tool()
async def secret_submit_proposal(
    title: str,
    description: str,
    proposal_type: str,
    initial_deposit: str = "0",
) -> dict:
    """Submit a governance proposal.

    Args:
        title: Proposal title
        description: Proposal description
        proposal_type: Type of proposal
        initial_deposit: Initial deposit (default: 0)

    Returns:
        Transaction hash and proposal ID
    """
    tool = SubmitProposalTool(context)
    return await tool.run({
        "title": title,
        "description": description,
        "proposal_type": proposal_type,
        "initial_deposit": initial_deposit,
    })


@mcp.tool()
async def secret_deposit_proposal(proposal_id: int, amount: str) -> dict:
    """Deposit tokens to a proposal.

    Args:
        proposal_id: Proposal ID
        amount: Amount to deposit (in micro-units)

    Returns:
        Transaction hash and details
    """
    tool = DepositProposalTool(context)
    return await tool.run({
        "proposal_id": proposal_id,
        "amount": amount,
    })


@mcp.tool()
async def secret_vote_proposal(proposal_id: int, vote_option: str) -> dict:
    """Vote on a governance proposal.

    Args:
        proposal_id: Proposal ID
        vote_option: Vote option (VOTE_OPTION_YES, VOTE_OPTION_NO, etc.)

    Returns:
        Transaction hash and details
    """
    tool = VoteProposalTool(context)
    return await tool.run({
        "proposal_id": proposal_id,
        "vote_option": vote_option,
    })


@mcp.tool()
async def secret_get_vote(proposal_id: int, voter: str = None) -> dict:
    """Get vote for a proposal.

    Args:
        proposal_id: Proposal ID
        voter: Optional voter address (uses active wallet if not provided)

    Returns:
        Vote details
    """
    tool = GetVoteTool(context)
    params = {"proposal_id": proposal_id}
    if voter:
        params["voter"] = voter
    return await tool.run(params)


@mcp.tool()
async def secret_upload_contract(wasm_file_path: str) -> dict:
    """Upload a smart contract WASM file.

    Args:
        wasm_file_path: Path to the WASM file

    Returns:
        Code ID and transaction hash
    """
    tool = UploadContractTool(context)
    return await tool.run({"wasm_file_path": wasm_file_path})


@mcp.tool()
async def secret_get_code_info(code_id: int) -> dict:
    """Get information about uploaded contract code.

    Args:
        code_id: Contract code ID

    Returns:
        Code information
    """
    tool = GetCodeInfoTool(context)
    return await tool.run({"code_id": code_id})


@mcp.tool()
async def secret_list_codes() -> dict:
    """List all uploaded contract codes.

    Returns:
        List of code IDs and information
    """
    tool = ListCodesTool(context)
    return await tool.run({})


@mcp.tool()
async def secret_instantiate_contract(
    code_id: int,
    init_msg: dict,
    label: str,
    admin: str = None,
) -> dict:
    """Instantiate a smart contract.

    Args:
        code_id: Contract code ID
        init_msg: Instantiation message
        label: Contract label
        admin: Optional admin address

    Returns:
        Contract address and transaction hash
    """
    tool = InstantiateContractTool(context)
    params = {
        "code_id": code_id,
        "init_msg": init_msg,
        "label": label,
    }
    if admin:
        params["admin"] = admin
    return await tool.run(params)


@mcp.tool()
async def secret_execute_contract(
    contract_address: str,
    execute_msg: dict,
    funds: list = None,
) -> dict:
    """Execute a smart contract.

    Args:
        contract_address: Contract address
        execute_msg: Execution message
        funds: Optional funds to send with execution

    Returns:
        Transaction hash and execution result
    """
    tool = ExecuteContractTool(context)
    params = {
        "contract_address": contract_address,
        "execute_msg": execute_msg,
    }
    if funds:
        params["funds"] = funds
    return await tool.run(params)


@mcp.tool()
async def secret_query_contract(contract_address: str, query_msg: dict) -> dict:
    """Query a smart contract.

    Args:
        contract_address: Contract address
        query_msg: Query message

    Returns:
        Query result
    """
    tool = QueryContractTool(context)
    return await tool.run({
        "contract_address": contract_address,
        "query_msg": query_msg,
    })


@mcp.tool()
async def secret_batch_execute(executions: list) -> dict:
    """Execute multiple contract operations in a batch.

    Args:
        executions: List of execution objects with 'contract_address', 'execute_msg', and optional 'funds'

    Returns:
        Transaction hash and batch execution results
    """
    tool = BatchExecuteTool(context)
    return await tool.run({"executions": executions})


@mcp.tool()
async def secret_get_contract_info(contract_address: str) -> dict:
    """Get contract information.

    Args:
        contract_address: Contract address

    Returns:
        Contract information including code ID and admin
    """
    tool = GetContractInfoTool(context)
    return await tool.run({"contract_address": contract_address})


@mcp.tool()
async def secret_get_contract_history(contract_address: str) -> dict:
    """Get contract history.

    Args:
        contract_address: Contract address

    Returns:
        Contract history
    """
    tool = GetContractHistoryTool(context)
    return await tool.run({"contract_address": contract_address})


@mcp.tool()
async def secret_migrate_contract(
    contract_address: str,
    new_code_id: int,
    migrate_msg: dict,
) -> dict:
    """Migrate a contract to new code.

    Args:
        contract_address: Contract address
        new_code_id: New code ID
        migrate_msg: Migration message

    Returns:
        Transaction hash and migration result
    """
    tool = MigrateContractTool(context)
    return await tool.run({
        "contract_address": contract_address,
        "new_code_id": new_code_id,
        "migrate_msg": migrate_msg,
    })


@mcp.tool()
async def secret_ibc_transfer(
    recipient: str,
    amount: str,
    source_channel: str,
    denom: str = "uscrt",
    timeout_height: int = None,
    timeout_timestamp: int = None,
    memo: str = "",
) -> dict:
    """Transfer tokens via IBC.

    Args:
        recipient: Recipient address on destination chain
        amount: Amount to transfer (in micro-units)
        source_channel: IBC source channel ID
        denom: Token denomination (default: uscrt)
        timeout_height: Optional timeout height
        timeout_timestamp: Optional timeout timestamp
        memo: Optional memo

    Returns:
        Transaction hash and IBC transfer details
    """
    tool = IBCTransferTool(context)
    params = {
        "recipient": recipient,
        "amount": amount,
        "source_channel": source_channel,
        "denom": denom,
        "memo": memo,
    }
    if timeout_height:
        params["timeout_height"] = timeout_height
    if timeout_timestamp:
        params["timeout_timestamp"] = timeout_timestamp
    return await tool.run(params)


@mcp.tool()
async def secret_get_ibc_channels() -> dict:
    """Get all IBC channels.

    Returns:
        List of IBC channels
    """
    tool = GetIBCChannelsTool(context)
    return await tool.run({})


@mcp.tool()
async def secret_get_ibc_channel(channel_id: str, port_id: str = "transfer") -> dict:
    """Get IBC channel information.

    Args:
        channel_id: Channel ID
        port_id: Port ID (default: transfer)

    Returns:
        Channel information
    """
    tool = GetIBCChannelTool(context)
    return await tool.run({
        "channel_id": channel_id,
        "port_id": port_id,
    })


@mcp.tool()
async def secret_get_ibc_denom_trace(ibc_denom: str) -> dict:
    """Get IBC denomination trace.

    Args:
        ibc_denom: IBC denomination hash

    Returns:
        Denom trace with path and base denom
    """
    tool = GetIBCDenomTraceTool(context)
    return await tool.run({"ibc_denom": ibc_denom})


# Register prompts
@mcp.prompt()
def secret_network_help(topic: str = None) -> str:
    """Get comprehensive help for using the Secret Network MCP server.

    Args:
        topic: Optional topic (network, wallet, tokens, staking, contracts, governance, ibc)

    Returns:
        Detailed help documentation
    """
    return secret_network_guide(topic)


@mcp.prompt()
def smart_contracts_help(operation: str = None) -> str:
    """Get help for Secret Network smart contract operations.

    Args:
        operation: Optional operation (upload, instantiate, execute, query, migrate, batch)

    Returns:
        Smart contracts documentation
    """
    return smart_contracts_guide(operation)


# Register resources
@mcp.resource("secret://session/state")
def session_state() -> dict:
    """Get current session state including network and active wallet."""
    return get_session_state_resource(session)


@mcp.resource("secret://wallets/list")
def wallets_list() -> dict:
    """Get list of all loaded wallets."""
    return get_wallets_list_resource(session)


@mcp.resource("secret://network/config")
def network_config() -> dict:
    """Get current network configuration."""
    return get_network_config_resource(context.network)


@mcp.resource("secret://validators/top")
async def top_validators() -> dict:
    """Get top validators by voting power."""
    return await get_top_validators_resource(client_pool)


def main():
    """Main entry point for the MCP server."""
    # Run the FastMCP server
    mcp.run()


if __name__ == "__main__":
    main()
