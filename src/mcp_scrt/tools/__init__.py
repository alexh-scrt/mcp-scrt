"""MCP tools for Secret Network blockchain interaction.

This package contains all MCP tool implementations organized by category.
"""

from mcp_scrt.tools.base import BaseTool, ToolCategory, ToolExecutionContext
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

__all__ = [
    # Base classes
    "BaseTool",
    "ToolCategory",
    "ToolExecutionContext",
    # Network tools
    "ConfigureNetworkTool",
    "GetNetworkInfoTool",
    "GetGasPricesTool",
    "HealthCheckTool",
    # Wallet tools
    "CreateWalletTool",
    "ImportWalletTool",
    "SetActiveWalletTool",
    "GetActiveWalletTool",
    "ListWalletsTool",
    "RemoveWalletTool",
    # Bank tools
    "GetBalanceTool",
    "SendTokensTool",
    "MultiSendTool",
    "GetTotalSupplyTool",
    "GetDenomMetadataTool",
    # Blockchain tools
    "GetBlockTool",
    "GetLatestBlockTool",
    "GetBlockByHashTool",
    "GetNodeInfoTool",
    "GetSyncingStatusTool",
    # Account tools
    "GetAccountTool",
    "GetAccountTransactionsTool",
    "GetAccountTxCountTool",
    # Transaction tools
    "GetTransactionTool",
    "SearchTransactionsTool",
    "EstimateGasTool",
    "SimulateTransactionTool",
    "GetTransactionStatusTool",
    # Staking tools
    "GetValidatorsTool",
    "GetValidatorTool",
    "DelegateTool",
    "UndelegateTool",
    "RedelegateTool",
    "GetDelegationsTool",
    "GetUnbondingTool",
    "GetRedelegationsTool",
    # Rewards tools
    "GetRewardsTool",
    "WithdrawRewardsTool",
    "SetWithdrawAddressTool",
    "GetCommunityPoolTool",
    # Governance tools
    "GetProposalsTool",
    "GetProposalTool",
    "SubmitProposalTool",
    "DepositProposalTool",
    "VoteProposalTool",
    "GetVoteTool",
    # Contract tools
    "UploadContractTool",
    "GetCodeInfoTool",
    "ListCodesTool",
    "InstantiateContractTool",
    "ExecuteContractTool",
    "QueryContractTool",
    "BatchExecuteTool",
    "GetContractInfoTool",
    "GetContractHistoryTool",
    "MigrateContractTool",
    # IBC tools
    "IBCTransferTool",
    "GetIBCChannelsTool",
    "GetIBCChannelTool",
    "GetIBCDenomTraceTool",
]
