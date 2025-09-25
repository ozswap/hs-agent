# Exceptions API Reference

## Overview

The HS Agent exception system provides a comprehensive hierarchy of custom exceptions with structured error information. All exceptions include detailed error messages, error codes, and additional context for debugging and error handling.

## 🏗️ Exception Hierarchy

```
HSAgentError (Base)
├── ConfigurationError
├── DataLoadingError
├── ClassificationError
├── AgentError
├── ValidationError
├── ExternalServiceError
├── TimeoutError
└── RateLimitError
```

## 🔧 Base Exception

### HSAgentError

::: hs_agent.core.exceptions.HSAgentError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Base exception class for all HS Agent errors with structured error information.

**Features**:
- Structured error details with error codes
- Cause tracking for exception chaining
- Dictionary serialization for API responses
- Consistent error message formatting

**Attributes**:
- `message`: Human-readable error message
- `error_code`: Machine-readable error code
- `details`: Additional error details dictionary
- `cause`: Original exception that caused this error

**Example**:
```python
from hs_agent.core.exceptions import HSAgentError

try:
    # Some operation that fails
    raise ValueError("Original error")
except ValueError as e:
    raise HSAgentError(
        message="Operation failed",
        error_code="OPERATION_FAILED",
        details={"operation": "data_loading", "file": "data.csv"},
        cause=e
    )
```

## 🚨 Specific Exceptions

### ConfigurationError

::: hs_agent.core.exceptions.ConfigurationError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Raised when there are configuration issues.

**Common Scenarios**:
- Missing required environment variables
- Invalid configuration values
- Missing configuration files
- Invalid file paths

**Example**:
```python
from hs_agent.core.exceptions import ConfigurationError

if not api_key:
    raise ConfigurationError(
        message="Google API key is required",
        error_code="MISSING_API_KEY",
        details={"required_env_var": "GOOGLE_API_KEY"}
    )
```

### DataLoadingError

::: hs_agent.core.exceptions.DataLoadingError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Raised when data loading operations fail.

**Common Scenarios**:
- Missing data files
- Corrupted data files
- Invalid data format
- File permission issues

**Example**:
```python
from hs_agent.core.exceptions import DataLoadingError

try:
    df = pd.read_csv(file_path)
except FileNotFoundError as e:
    raise DataLoadingError(
        message=f"HS codes file not found: {file_path}",
        error_code="FILE_NOT_FOUND",
        details={"file_path": str(file_path), "file_type": "hs_codes"},
        cause=e
    )
```

### ClassificationError

::: hs_agent.core.exceptions.ClassificationError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Raised when HS code classification operations fail.

**Common Scenarios**:
- No candidates found for classification
- LLM API failures
- Invalid product descriptions
- Classification timeout

**Example**:
```python
from hs_agent.core.exceptions import ClassificationError

if not candidates:
    raise ClassificationError(
        message="No HS code candidates found for product",
        error_code="NO_CANDIDATES_FOUND",
        details={
            "product_description": product_description,
            "level": level,
            "search_criteria": criteria
        }
    )
```

### AgentError

::: hs_agent.core.exceptions.AgentError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Raised when agent operations fail.

**Common Scenarios**:
- Agent initialization failures
- Agent execution errors
- Invalid agent configuration
- Model loading failures

**Example**:
```python
from hs_agent.core.exceptions import AgentError

try:
    agent = HSLangGraphAgent(data_loader)
except Exception as e:
    raise AgentError(
        message="Failed to initialize LangGraph agent",
        error_code="AGENT_INITIALIZATION_FAILED",
        details={"agent_type": "langgraph", "model_name": model_name},
        cause=e
    )
```

### ValidationError

::: hs_agent.core.exceptions.ValidationError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Raised when input validation fails.

**Common Scenarios**:
- Invalid request parameters
- Missing required fields
- Data type mismatches
- Value constraint violations

**Example**:
```python
from hs_agent.core.exceptions import ValidationError

if not (1 <= top_k <= 50):
    raise ValidationError(
        message="top_k must be between 1 and 50",
        error_code="INVALID_TOP_K",
        details={"provided_value": top_k, "valid_range": "1-50"}
    )
```

### ExternalServiceError

::: hs_agent.core.exceptions.ExternalServiceError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Raised when external service calls fail.

**Common Scenarios**:
- Google Vertex AI API errors
- Langfuse API errors
- Network connectivity issues
- Service authentication failures

**Example**:
```python
from hs_agent.core.exceptions import ExternalServiceError

try:
    response = await vertex_ai_client.generate(prompt)
except Exception as e:
    raise ExternalServiceError(
        message="Vertex AI API call failed",
        error_code="VERTEX_AI_ERROR",
        details={
            "service": "vertex_ai",
            "operation": "generate",
            "model": model_name
        },
        cause=e
    )
```

### TimeoutError

::: hs_agent.core.exceptions.TimeoutError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Raised when operations timeout.

**Common Scenarios**:
- LLM API timeouts
- Data loading timeouts
- Request processing timeouts
- Network timeouts

**Example**:
```python
from hs_agent.core.exceptions import TimeoutError

if elapsed_time > timeout_seconds:
    raise TimeoutError(
        message=f"Classification timed out after {timeout_seconds} seconds",
        error_code="CLASSIFICATION_TIMEOUT",
        details={
            "operation": "classification",
            "timeout_seconds": timeout_seconds,
            "elapsed_seconds": elapsed_time
        }
    )
```

### RateLimitError

::: hs_agent.core.exceptions.RateLimitError
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Raised when rate limits are exceeded.

**Common Scenarios**:
- API rate limit exceeded
- Too many concurrent requests
- Quota exceeded
- Service throttling

**Example**:
```python
from hs_agent.core.exceptions import RateLimitError

if concurrent_requests > max_concurrent:
    raise RateLimitError(
        message="Maximum concurrent requests exceeded",
        error_code="CONCURRENT_LIMIT_EXCEEDED",
        details={
            "current_requests": concurrent_requests,
            "max_allowed": max_concurrent
        }
    )
```

## 🛠️ Error Handling Utilities

### handle_external_service_error

::: hs_agent.core.exceptions.handle_external_service_error
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Utility function to create standardized external service errors.

**Example**:
```python
from hs_agent.core.exceptions import handle_external_service_error

try:
    result = await google_api_call()
except Exception as e:
    raise handle_external_service_error(
        service_name="google_vertex_ai",
        operation="classification",
        original_error=e
    )
```

### handle_validation_error

::: hs_agent.core.exceptions.handle_validation_error
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Utility function to create standardized validation errors.

**Example**:
```python
from hs_agent.core.exceptions import handle_validation_error

if not isinstance(top_k, int):
    raise handle_validation_error(
        field_name="top_k",
        field_value=top_k,
        expected_type="integer",
        additional_info="Must be between 1 and 50"
    )
```

### handle_timeout_error

::: hs_agent.core.exceptions.handle_timeout_error
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Utility function to create standardized timeout errors.

**Example**:
```python
from hs_agent.core.exceptions import handle_timeout_error

if time.time() - start_time > timeout:
    raise handle_timeout_error(
        operation="hs_classification",
        timeout_seconds=timeout,
        additional_context="Large product description"
    )
```

## 🎯 Usage Patterns

### Basic Error Handling

```python
from hs_agent.core.exceptions import HSAgentError, ClassificationError

try:
    result = await agent.classify_hierarchical(description)
except ClassificationError as e:
    logger.error(f"Classification failed: {e.message}")
    return {"error": e.to_dict()}
except HSAgentError as e:
    logger.error(f"HS Agent error: {e.message}")
    return {"error": e.to_dict()}
except Exception as e:
    logger.exception("Unexpected error")
    return {"error": "Internal server error"}
```

### API Error Responses

```python
from fastapi import HTTPException
from hs_agent.core.exceptions import HSAgentError

try:
    result = await classify_product(request)
    return result
except HSAgentError as e:
    # Convert to HTTP exception with structured error
    raise HTTPException(
        status_code=400,
        detail=e.to_dict()
    )
```

### Error Logging with Context

```python
from hs_agent.core.exceptions import DataLoadingError
from hs_agent.core.logging import logger

try:
    data_loader.load_all_data()
except DataLoadingError as e:
    logger.error(
        "Data loading failed",
        error_code=e.error_code,
        error_details=e.details,
        cause=str(e.cause) if e.cause else None
    )
    raise
```

### Exception Chaining

```python
from hs_agent.core.exceptions import AgentError, ExternalServiceError

try:
    # Lower-level operation
    response = await llm_api_call()
except Exception as e:
    # Wrap in service-specific error
    service_error = ExternalServiceError(
        message="LLM API call failed",
        error_code="LLM_API_ERROR",
        cause=e
    )
    
    # Chain to higher-level error
    raise AgentError(
        message="Agent classification failed",
        error_code="CLASSIFICATION_FAILED",
        details={"step": "llm_ranking"},
        cause=service_error
    )
```

## 🔍 Error Analysis

### Error Dictionary Structure

All exceptions can be serialized to dictionaries for API responses:

```python
{
    "error": "CLASSIFICATION_ERROR",
    "message": "No HS code candidates found for product",
    "details": {
        "product_description": "vague description",
        "level": "6",
        "search_criteria": {...}
    },
    "type": "ClassificationError"
}
```

### Error Code Conventions

Error codes follow a consistent naming pattern:

- `CONFIGURATION_ERROR`: Configuration-related issues
- `DATA_LOADING_FAILED`: Data loading failures
- `CLASSIFICATION_TIMEOUT`: Classification timeouts
- `AGENT_INITIALIZATION_FAILED`: Agent setup failures
- `VALIDATION_ERROR`: Input validation failures
- `EXTERNAL_SERVICE_ERROR`: External API failures

### Error Context

Exceptions include rich context information:

```python
{
    "error_code": "DATA_LOADING_FAILED",
    "message": "HS codes file not found",
    "details": {
        "file_path": "/data/hs_codes.csv",
        "file_type": "hs_codes",
        "data_directory": "/data",
        "expected_files": ["hs_codes_all.csv"]
    },
    "cause": "FileNotFoundError: [Errno 2] No such file or directory"
}
```

## 🐛 Debugging with Exceptions

### Exception Inspection

```python
from hs_agent.core.exceptions import HSAgentError

try:
    # Some operation
    pass
except HSAgentError as e:
    print(f"Error Code: {e.error_code}")
    print(f"Message: {e.message}")
    print(f"Details: {e.details}")
    print(f"Cause: {e.cause}")
    
    # Full error dictionary
    error_dict = e.to_dict()
    print(f"Full error: {error_dict}")
```

### Stack Trace Preservation

```python
import traceback
from hs_agent.core.exceptions import HSAgentError

try:
    # Some operation
    pass
except HSAgentError as e:
    # Original stack trace is preserved in e.cause
    if e.cause:
        print("Original error:")
        traceback.print_exception(type(e.cause), e.cause, e.cause.__traceback__)
    
    # Current stack trace
    print("Current error:")
    traceback.print_exc()
```

## 📚 Related Documentation

- [Configuration Guide](../../getting-started/configuration.md) - Configuration error handling
- [CLI Usage](../../user-guide/cli-usage.md) - CLI error handling
- [API Usage](../../user-guide/api-usage.md) - API error responses
- [Testing Guide](../../development/testing.md) - Testing error scenarios