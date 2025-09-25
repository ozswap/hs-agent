"""Standardized exception handling for HS Agent.

This module defines a hierarchy of custom exceptions that provide
clear, actionable error messages and proper error categorization.
"""

from typing import Optional, Dict, Any


class HSAgentError(Exception):
    """Base exception for all HS Agent errors.
    
    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        details: Additional error details
        cause: Original exception that caused this error
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "type": self.__class__.__name__
        }


class ConfigurationError(HSAgentError):
    """Raised when there are configuration issues.
    
    Examples:
        - Missing required environment variables
        - Invalid configuration values
        - Missing configuration files
    """
    pass


class DataLoadingError(HSAgentError):
    """Raised when data loading fails.
    
    Examples:
        - Missing data files
        - Corrupted data files
        - Invalid data format
    """
    pass


class ClassificationError(HSAgentError):
    """Raised when HS code classification fails.
    
    Examples:
        - No candidates found
        - LLM API failures
        - Invalid product descriptions
    """
    pass


class AgentError(HSAgentError):
    """Raised when agent operations fail.
    
    Examples:
        - Agent initialization failures
        - Agent execution errors
        - Invalid agent configuration
    """
    pass


class ValidationError(HSAgentError):
    """Raised when input validation fails.
    
    Examples:
        - Invalid request parameters
        - Missing required fields
        - Data type mismatches
    """
    pass


class ExternalServiceError(HSAgentError):
    """Raised when external service calls fail.
    
    Examples:
        - Google Vertex AI API errors
        - Langfuse API errors
        - Network connectivity issues
    """
    pass


class TimeoutError(HSAgentError):
    """Raised when operations timeout.
    
    Examples:
        - LLM API timeouts
        - Data loading timeouts
        - Request processing timeouts
    """
    pass


class RateLimitError(HSAgentError):
    """Raised when rate limits are exceeded.
    
    Examples:
        - API rate limit exceeded
        - Too many concurrent requests
        - Quota exceeded
    """
    pass


# Error handling utilities

def handle_external_service_error(
    service_name: str,
    operation: str,
    original_error: Exception
) -> ExternalServiceError:
    """Create a standardized external service error."""
    return ExternalServiceError(
        message=f"Failed to {operation} with {service_name}: {str(original_error)}",
        error_code=f"{service_name.upper()}_ERROR",
        details={
            "service": service_name,
            "operation": operation,
            "original_error": str(original_error),
            "error_type": type(original_error).__name__
        },
        cause=original_error
    )


def handle_validation_error(
    field_name: str,
    field_value: Any,
    expected_type: str,
    additional_info: Optional[str] = None
) -> ValidationError:
    """Create a standardized validation error."""
    message = f"Invalid value for '{field_name}': expected {expected_type}, got {type(field_value).__name__}"
    if additional_info:
        message += f". {additional_info}"
    
    return ValidationError(
        message=message,
        error_code="VALIDATION_ERROR",
        details={
            "field": field_name,
            "value": str(field_value),
            "expected_type": expected_type,
            "actual_type": type(field_value).__name__,
            "additional_info": additional_info
        }
    )


def handle_timeout_error(
    operation: str,
    timeout_seconds: int,
    additional_context: Optional[str] = None
) -> TimeoutError:
    """Create a standardized timeout error."""
    message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"
    if additional_context:
        message += f". {additional_context}"
    
    return TimeoutError(
        message=message,
        error_code="TIMEOUT_ERROR",
        details={
            "operation": operation,
            "timeout_seconds": timeout_seconds,
            "additional_context": additional_context
        }
    )