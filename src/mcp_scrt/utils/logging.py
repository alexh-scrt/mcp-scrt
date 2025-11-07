"""Logging configuration for Secret MCP Server.

This module sets up structured logging using structlog, providing
consistent, machine-readable logs across the application.
"""

import logging
import sys
from typing import Any, Optional

import structlog
from structlog.typing import EventDict, Processor


def add_log_level(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add log level to event dict.

    Args:
        logger: Logger instance
        method_name: Name of the logging method
        event_dict: Event dictionary

    Returns:
        Modified event dictionary with level field
    """
    if method_name == "warn":
        # Structlog uses "warn", but we want "warning"
        event_dict["level"] = "warning"
    else:
        event_dict["level"] = method_name
    return event_dict


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
) -> None:
    """Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ("json" or "console")
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard library logging
    # IMPORTANT: Use stderr for MCP servers (stdout is for JSON-RPC only)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=numeric_level,
    )

    # Common processors for all formats
    common_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    # Choose renderer based on format
    if log_format == "json":
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        # Use ConsoleRenderer for human-readable output
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog
    structlog.configure(
        processors=[
            *common_processors,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure processor formatter for standard library logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=common_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Set up handler
    # IMPORTANT: Use stderr for MCP servers (stdout is for JSON-RPC only)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (usually __name__). If None, returns root logger.

    Returns:
        Configured structlog logger instance
    """
    return structlog.get_logger(name)


# Module-level logger
logger = get_logger(__name__)
