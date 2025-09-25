"""Centralized logging configuration for HS Agent.

This module provides a standardized logging setup with support for
console and file logging, structured logging, and integration with
observability tools like Langfuse.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console

from hs_agent.config import settings


class HSAgentLogger:
    """Centralized logger for HS Agent with rich formatting and structured logging."""
    
    def __init__(self, name: str = "hs_agent"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure the logger with appropriate handlers and formatting."""
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(getattr(logging, settings.log_level.value))
        
        # Create console handler with rich formatting
        console = Console(stderr=True)
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True
        )
        console_handler.setLevel(getattr(logging, settings.log_level.value))
        
        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        
        # Add console handler
        self.logger.addHandler(console_handler)
        
        # Add file handler if specified
        if settings.log_file:
            file_handler = logging.FileHandler(settings.log_file)
            file_handler.setLevel(getattr(logging, settings.log_level.value))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional structured data."""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional structured data."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional structured data."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional structured data."""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional structured data."""
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)


# Global logger instance
logger = HSAgentLogger()


def get_logger(name: str) -> HSAgentLogger:
    """Get a logger instance for a specific module or component.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
    
    Returns:
        Configured logger instance
    """
    return HSAgentLogger(name)


def log_classification_start(product_description: str, agent_type: str):
    """Log the start of a classification operation."""
    logger.info(
        f"🎯 Starting HS classification",
        product_description=product_description,
        agent_type=agent_type,
        operation="classification_start"
    )


def log_classification_complete(
    product_description: str,
    final_code: str,
    confidence: float,
    processing_time_ms: float
):
    """Log the completion of a classification operation."""
    logger.info(
        f"✅ HS classification complete: {final_code} (confidence: {confidence:.2f})",
        product_description=product_description,
        final_code=final_code,
        confidence=confidence,
        processing_time_ms=processing_time_ms,
        operation="classification_complete"
    )


def log_classification_error(product_description: str, error: Exception):
    """Log a classification error."""
    logger.error(
        f"❌ HS classification failed: {str(error)}",
        product_description=product_description,
        error_type=type(error).__name__,
        error_message=str(error),
        operation="classification_error"
    )


def log_agent_operation(agent_type: str, operation: str, details: dict):
    """Log an agent operation with structured details."""
    logger.info(
        f"🤖 Agent operation: {operation}",
        agent_type=agent_type,
        operation=operation,
        **details
    )


def log_data_loading(file_path: str, record_count: int, loading_time_ms: float):
    """Log data loading operation."""
    logger.info(
        f"📊 Data loaded: {record_count} records from {file_path}",
        file_path=file_path,
        record_count=record_count,
        loading_time_ms=loading_time_ms,
        operation="data_loading"
    )


def log_api_request(endpoint: str, method: str, status_code: int, response_time_ms: float):
    """Log API request."""
    logger.info(
        f"🌐 API {method} {endpoint} -> {status_code}",
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time_ms=response_time_ms,
        operation="api_request"
    )