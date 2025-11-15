"""
Cache middleware for automatic caching of tool operations.

This middleware provides:
- Automatic caching of read operations
- Automatic invalidation on write operations
- Cache key generation from tool name and parameters
- Performance monitoring
"""

from typing import Any, Dict, Optional, Callable, Awaitable
from dataclasses import dataclass
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheContext:
    """Context for cache operations."""
    cache_key: Optional[str] = None
    cache_hit: bool = False
    ttl: Optional[int] = None
    should_cache: bool = True


class CacheMiddleware:
    """
    Middleware for automatic tool result caching.

    Features:
    - Automatic cache key generation
    - Read-through caching
    - Write-through invalidation
    - Selective caching based on tool type
    """

    # Tools that should NOT be cached (write operations, auth, etc.)
    UNCACHEABLE_TOOLS = {
        # Write operations
        "secret_send_tokens",
        "secret_multi_send",
        "secret_delegate",
        "secret_undelegate",
        "secret_redelegate",
        "secret_withdraw_rewards",
        "secret_submit_proposal",
        "secret_vote_proposal",
        "secret_deposit_proposal",
        "secret_instantiate_contract",
        "secret_execute_contract",
        "secret_upload_contract",
        "secret_migrate_contract",
        "secret_ibc_transfer",

        # Wallet operations (sensitive)
        "secret_create_wallet",
        "secret_import_wallet",
        "secret_set_active_wallet",
        "secret_remove_wallet",

        # Knowledge write operations
        "knowledge_add_document",
        "knowledge_update_document",
        "knowledge_delete_document",

        # Graph write operations (handled by graph middleware)
        "graph_create_node",
        "graph_create_relationship",
        "graph_delete_node",
    }

    # Tools with custom cache key patterns
    CACHE_KEY_PATTERNS = {
        "secret_get_balance": "balance:{address}",
        "secret_get_validators": "validators:all",
        "secret_get_validator": "validator:{validator_address}",
        "secret_get_delegations": "delegations:{address}",
        "secret_get_rewards": "rewards:{address}",
        "secret_get_proposals": "proposals:all",
        "secret_get_proposal": "proposal:{proposal_id}",
        "secret_get_block": "block:{height}",
        "secret_get_latest_block": "block:latest",
        "secret_get_transaction": "tx:{tx_hash}",
        "secret_get_code_info": "code_info:{code_id}",
        "secret_get_contract_info": "contract_info:{contract_address}",
        "secret_get_account": "account:{address}:info",
        "secret_get_gas_prices": "gas_price",
        "secret_get_ibc_channels": "ibc:channels",
    }

    def __init__(self, cache_service):
        """
        Initialize cache middleware.

        Args:
            cache_service: CacheService instance
        """
        self.cache = cache_service
        logger.info("Initialized CacheMiddleware")

    def _should_cache_tool(self, tool_name: str) -> bool:
        """
        Determine if a tool's results should be cached.

        Args:
            tool_name: Name of the tool

        Returns:
            True if should be cached
        """
        return tool_name not in self.UNCACHEABLE_TOOLS

    def _generate_cache_key(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> str:
        """
        Generate cache key for tool execution.

        Args:
            tool_name: Name of the tool
            params: Tool parameters

        Returns:
            Cache key string
        """
        # Check if tool has custom key pattern
        if tool_name in self.CACHE_KEY_PATTERNS:
            pattern = self.CACHE_KEY_PATTERNS[tool_name]
            try:
                return pattern.format(**params)
            except KeyError:
                # Missing parameter, fall back to hash-based key
                pass

        # Default: hash-based key
        # Create stable string from parameters
        param_str = json.dumps(params, sort_keys=True, default=str)
        param_hash = hashlib.sha256(param_str.encode()).hexdigest()[:16]

        return f"tool:{tool_name}:{param_hash}"

    async def before_execute(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> CacheContext:
        """
        Execute before tool runs - check cache.

        Args:
            tool_name: Name of the tool
            params: Tool parameters

        Returns:
            Cache context with cache hit data if available
        """
        context = CacheContext()

        # Check if tool should be cached
        if not self._should_cache_tool(tool_name):
            context.should_cache = False
            logger.debug(f"Tool {tool_name} marked as uncacheable")
            return context

        # Generate cache key
        cache_key = self._generate_cache_key(tool_name, params)
        context.cache_key = cache_key

        # Check cache
        cached_result = await self.cache.get(cache_key)

        if cached_result is not None:
            context.cache_hit = True
            logger.info(f"Cache hit for {tool_name}: {cache_key}")
            return context

        logger.debug(f"Cache miss for {tool_name}: {cache_key}")
        return context

    async def after_execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: Any,
        context: CacheContext,
        error: Optional[Exception] = None
    ):
        """
        Execute after tool runs - cache result and handle invalidation.

        Args:
            tool_name: Name of the tool
            params: Tool parameters
            result: Tool execution result
            context: Cache context from before_execute
            error: Exception if tool failed
        """
        # Don't cache if error occurred
        if error is not None:
            logger.debug(f"Not caching {tool_name} due to error: {error}")
            return

        # Don't cache if marked as uncacheable
        if not context.should_cache:
            # But do handle invalidation for write operations
            if tool_name in self.UNCACHEABLE_TOOLS:
                await self._handle_invalidation(tool_name, params)
            return

        # Cache the result
        if context.cache_key:
            await self.cache.set(
                context.cache_key,
                result,
                ttl=context.ttl
            )
            logger.debug(f"Cached result for {tool_name}: {context.cache_key}")

    async def _handle_invalidation(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ):
        """
        Handle cache invalidation for write operations.

        Args:
            tool_name: Name of the tool
            params: Tool parameters
        """
        # Use cache service's invalidation rules
        await self.cache.invalidate_related(tool_name, params)


# Export
__all__ = ["CacheMiddleware", "CacheContext"]
