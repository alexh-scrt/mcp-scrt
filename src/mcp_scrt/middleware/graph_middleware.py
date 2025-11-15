"""
Graph middleware for automatic graph database updates.

This middleware provides:
- Automatic graph recording for blockchain operations
- Non-blocking graph updates
- Error isolation (graph failures don't break operations)
- Operation type detection
"""

from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class GraphMiddleware:
    """
    Middleware for automatic graph database updates.

    Features:
    - Auto-record blockchain transactions
    - Non-blocking updates
    - Error isolation
    - Selective recording based on operation type
    """

    # Operations that should trigger graph updates
    GRAPH_OPERATIONS = {
        # Staking
        "secret_delegate": "delegation",
        "secret_undelegate": "undelegation",
        "secret_redelegate": "redelegation",

        # Transfers
        "secret_send_tokens": "transfer",
        "secret_multi_send": "multi_transfer",

        # Governance
        "secret_vote_proposal": "vote",
        "secret_submit_proposal": "proposal_submission",

        # Contracts
        "secret_instantiate_contract": "contract_instantiation",
        "secret_execute_contract": "contract_execution",
    }

    def __init__(
        self,
        graph_service,
        async_mode: bool = True
    ):
        """
        Initialize graph middleware.

        Args:
            graph_service: GraphService instance
            async_mode: Run updates asynchronously (non-blocking)
        """
        self.graph = graph_service
        self.async_mode = async_mode
        logger.info(f"Initialized GraphMiddleware (async_mode={async_mode})")

    def _should_record(self, tool_name: str) -> bool:
        """
        Determine if operation should be recorded in graph.

        Args:
            tool_name: Name of the tool

        Returns:
            True if should be recorded
        """
        return tool_name in self.GRAPH_OPERATIONS

    async def after_execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: Any,
        error: Optional[Exception] = None
    ):
        """
        Execute after tool runs - record in graph if applicable.

        Args:
            tool_name: Name of the tool
            params: Tool parameters
            result: Tool execution result
            error: Exception if tool failed
        """
        # Don't record if error occurred
        if error is not None:
            logger.debug(f"Skipping graph update for {tool_name} due to error")
            return

        # Check if should record
        if not self._should_record(tool_name):
            return

        # Get operation type
        operation_type = self.GRAPH_OPERATIONS[tool_name]

        # Record in graph (async if enabled)
        if self.async_mode:
            # Non-blocking - don't wait for completion
            asyncio.create_task(
                self._record_operation(
                    operation_type,
                    tool_name,
                    params,
                    result
                )
            )
            logger.debug(f"Queued async graph update for {tool_name}")
        else:
            # Blocking - wait for completion
            await self._record_operation(
                operation_type,
                tool_name,
                params,
                result
            )
            logger.debug(f"Completed graph update for {tool_name}")

    async def _record_operation(
        self,
        operation_type: str,
        tool_name: str,
        params: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """
        Record an operation in the graph database.

        Args:
            operation_type: Type of operation
            tool_name: Tool name
            params: Tool parameters
            result: Tool result
        """
        try:
            # Extract transaction hash from result
            tx_hash = result.get("tx_hash") or result.get("txhash")

            if not tx_hash:
                logger.warning(f"No tx_hash in result for {tool_name}")
                return

            timestamp = datetime.utcnow()

            # Route to appropriate graph service method
            if operation_type == "delegation":
                await self.graph.record_delegation(
                    delegator_address=params.get("address") or params.get("delegator"),
                    validator_address=params.get("validator_address") or params.get("validator"),
                    amount=params.get("amount"),
                    tx_hash=tx_hash,
                    timestamp=timestamp
                )

            elif operation_type == "undelegation":
                await self.graph.record_delegation(
                    delegator_address=params.get("address") or params.get("delegator"),
                    validator_address=params.get("validator_address") or params.get("validator"),
                    amount=f"-{params.get('amount')}",  # Negative for undelegation
                    tx_hash=tx_hash,
                    timestamp=timestamp
                )

            elif operation_type == "redelegation":
                # Record as two operations: undelegate from source, delegate to destination
                await self.graph.record_delegation(
                    delegator_address=params.get("address") or params.get("delegator"),
                    validator_address=params.get("dst_validator"),
                    amount=params.get("amount"),
                    tx_hash=tx_hash,
                    timestamp=timestamp
                )

            elif operation_type == "transfer":
                await self.graph.record_transfer(
                    from_address=params.get("address") or params.get("from_address"),
                    to_address=params.get("recipient") or params.get("to_address"),
                    amount=params.get("amount"),
                    tx_hash=tx_hash,
                    timestamp=timestamp
                )

            elif operation_type == "multi_transfer":
                # Record multiple transfers
                recipients = params.get("recipients", [])
                for recipient_data in recipients:
                    await self.graph.record_transfer(
                        from_address=params.get("address"),
                        to_address=recipient_data.get("address"),
                        amount=recipient_data.get("amount"),
                        tx_hash=tx_hash,
                        timestamp=timestamp
                    )

            elif operation_type == "vote":
                await self.graph.record_vote(
                    voter_address=params.get("address") or params.get("voter"),
                    proposal_id=params.get("proposal_id"),
                    vote_option=params.get("vote_option") or params.get("option"),
                    tx_hash=tx_hash,
                    timestamp=timestamp
                )

            elif operation_type == "proposal_submission":
                # Could record proposal node here
                logger.debug(f"Recorded proposal submission: {tx_hash}")

            elif operation_type in ["contract_instantiation", "contract_execution"]:
                await self.graph.record_contract_execution(
                    executor_address=params.get("address") or params.get("sender"),
                    contract_address=params.get("contract_address"),
                    method=params.get("execute_msg", {}).get("method", "unknown"),
                    tx_hash=tx_hash,
                    success=True,
                    timestamp=timestamp
                )

            logger.info(f"Recorded {operation_type} in graph: {tx_hash}")

        except Exception as e:
            # Log error but don't propagate (graph failures shouldn't break operations)
            logger.error(f"Failed to record {operation_type} in graph: {e}")


# Export
__all__ = ["GraphMiddleware"]
