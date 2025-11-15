"""
Telemetry middleware for performance monitoring and analytics.

This middleware provides:
- Tool execution time tracking
- Success/failure rate monitoring
- Parameter size tracking
- Result size tracking
- Usage analytics
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetrics:
    """Metrics for a single tool execution."""
    tool_name: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    params_size: int
    result_size: int
    error_type: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class ToolStatistics:
    """Aggregated statistics for a tool."""
    tool_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    total_duration_ms: float


class TelemetryMiddleware:
    """
    Middleware for performance monitoring and analytics.

    Features:
    - Execution time tracking
    - Success/failure monitoring
    - Size metrics
    - Usage analytics
    - Performance statistics
    """

    def __init__(
        self,
        redis_client,
        retention_limit: int = 10000
    ):
        """
        Initialize telemetry middleware.

        Args:
            redis_client: Redis client for storing metrics
            retention_limit: Maximum number of metric records to retain
        """
        self.redis = redis_client
        self.retention_limit = retention_limit
        logger.info("Initialized TelemetryMiddleware")

    def before_execute(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute before tool runs - record start time.

        Args:
            tool_name: Name of the tool
            params: Tool parameters

        Returns:
            Context dict with start time and sizes
        """
        context = {
            "tool_name": tool_name,
            "start_time": time.time(),
            "params_size": len(str(params))
        }

        return context

    async def after_execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: Any,
        context: Dict[str, Any],
        error: Optional[Exception] = None
    ):
        """
        Execute after tool runs - record metrics.

        Args:
            tool_name: Name of the tool
            params: Tool parameters
            result: Tool execution result
            context: Context from before_execute
            error: Exception if tool failed
        """
        end_time = time.time()
        start_time = context.get("start_time", end_time)
        duration = end_time - start_time
        duration_ms = duration * 1000

        # Create metrics
        metrics = ExecutionMetrics(
            tool_name=tool_name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            success=error is None,
            params_size=context.get("params_size", 0),
            result_size=len(str(result)) if result else 0,
            error_type=type(error).__name__ if error else None
        )

        # Store metrics
        await self._store_metrics(metrics)

        # Update statistics
        await self._update_statistics(metrics)

        # Log metrics
        status = "SUCCESS" if metrics.success else "FAILURE"
        logger.info(
            f"[{status}] {tool_name} completed in {duration_ms:.2f}ms"
        )

    async def _store_metrics(self, metrics: ExecutionMetrics):
        """
        Store execution metrics in Redis.

        Args:
            metrics: Execution metrics
        """
        # Store in time-series list
        self.redis.redis.lpush(
            "telemetry:metrics:all",
            metrics.__dict__
        )

        # Trim to retention limit
        self.redis.redis.ltrim(
            "telemetry:metrics:all",
            0,
            self.retention_limit - 1
        )

        # Store by tool name
        self.redis.redis.lpush(
            f"telemetry:metrics:tool:{metrics.tool_name}",
            metrics.__dict__
        )
        self.redis.redis.ltrim(
            f"telemetry:metrics:tool:{metrics.tool_name}",
            0,
            999  # Keep last 1000 per tool
        )

    async def _update_statistics(self, metrics: ExecutionMetrics):
        """
        Update aggregated statistics.

        Args:
            metrics: Execution metrics
        """
        tool_name = metrics.tool_name

        # Update counters
        self.redis.hincrby("telemetry:stats:total_executions", tool_name, 1)

        if metrics.success:
            self.redis.hincrby("telemetry:stats:successful", tool_name, 1)
        else:
            self.redis.hincrby("telemetry:stats:failed", tool_name, 1)
            # Track error types
            if metrics.error_type:
                self.redis.hincrby(
                    f"telemetry:stats:errors:{tool_name}",
                    metrics.error_type,
                    1
                )

        # Update duration statistics (using sorted set for min/max/avg)
        self.redis.redis.zadd(
            f"telemetry:stats:durations:{tool_name}",
            {metrics.timestamp: metrics.duration_ms}
        )

        # Keep only recent durations (last 1000)
        self.redis.redis.zremrangebyrank(
            f"telemetry:stats:durations:{tool_name}",
            0,
            -1001
        )

    async def get_tool_statistics(
        self,
        tool_name: str
    ) -> Optional[ToolStatistics]:
        """
        Get aggregated statistics for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool statistics or None if no data
        """
        # Get counters
        total = int(
            self.redis.hget("telemetry:stats:total_executions", tool_name) or 0
        )

        if total == 0:
            return None

        successful = int(
            self.redis.hget("telemetry:stats:successful", tool_name) or 0
        )
        failed = int(
            self.redis.hget("telemetry:stats:failed", tool_name) or 0
        )

        success_rate = (successful / total * 100) if total > 0 else 0.0

        # Get duration statistics
        durations_key = f"telemetry:stats:durations:{tool_name}"
        durations = [
            float(score)
            for score in self.redis.redis.zrange(
                durations_key, 0, -1, withscores=True
            )[1::2]  # Get only scores
        ]

        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            total_duration = sum(durations)
        else:
            avg_duration = 0.0
            min_duration = 0.0
            max_duration = 0.0
            total_duration = 0.0

        return ToolStatistics(
            tool_name=tool_name,
            total_executions=total,
            successful_executions=successful,
            failed_executions=failed,
            success_rate=success_rate,
            avg_duration_ms=avg_duration,
            min_duration_ms=min_duration,
            max_duration_ms=max_duration,
            total_duration_ms=total_duration
        )

    async def get_all_statistics(self) -> Dict[str, ToolStatistics]:
        """
        Get statistics for all tools.

        Returns:
            Dict mapping tool name to statistics
        """
        # Get all tool names from counters
        tool_counts = self.redis.hgetall("telemetry:stats:total_executions")

        statistics = {}
        for tool_name in tool_counts.keys():
            stats = await self.get_tool_statistics(tool_name)
            if stats:
                statistics[tool_name] = stats

        return statistics

    async def get_recent_metrics(
        self,
        tool_name: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Get recent execution metrics.

        Args:
            tool_name: Optional tool name filter
            limit: Maximum number of metrics to return

        Returns:
            List of recent metrics
        """
        if tool_name:
            key = f"telemetry:metrics:tool:{tool_name}"
        else:
            key = "telemetry:metrics:all"

        metrics_data = self.redis.redis.lrange(key, 0, limit - 1)

        return [
            ExecutionMetrics(**data)
            for data in metrics_data
        ]

    async def get_error_breakdown(
        self,
        tool_name: str
    ) -> Dict[str, int]:
        """
        Get breakdown of errors for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Dict mapping error type to count
        """
        return self.redis.hgetall(f"telemetry:stats:errors:{tool_name}")

    async def reset_statistics(self):
        """Reset all telemetry statistics."""
        patterns = [
            "telemetry:stats:*",
            "telemetry:metrics:*"
        ]

        for pattern in patterns:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)

        logger.info("Telemetry statistics reset")


# Export
__all__ = ["TelemetryMiddleware", "ExecutionMetrics", "ToolStatistics"]
