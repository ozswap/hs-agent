# Configuration API Reference

## Overview

The HS Agent configuration system provides centralized, type-safe configuration management using Pydantic Settings. All configuration is validated at startup and can be overridden via environment variables.

## 📋 Configuration Classes

### HSAgentSettings

::: hs_agent.config.settings.HSAgentSettings
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Main configuration class that defines all HS Agent settings with validation and documentation.

**Location**: `hs_agent.config.settings.HSAgentSettings`

**Features**:
- Type-safe configuration with Pydantic validation
- Environment variable support with automatic loading
- Comprehensive validation rules and error messages
- Helper properties for computed values

### AgentType

::: hs_agent.config.settings.AgentType
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Enumeration of available agent implementations.

**Values**:
- `TRADITIONAL`: Pydantic AI-based agents
- `LANGGRAPH`: LangGraph workflow-based agents

### LogLevel

::: hs_agent.config.settings.LogLevel
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

Enumeration of available logging levels.

**Values**:
- `DEBUG`: Detailed debugging information
- `INFO`: General information messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical error messages

## 🔧 Configuration Categories

### API Keys and Authentication

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `google_api_key` | `str` | **Required** | Google API key for Vertex AI/Gemini models |
| `langfuse_secret_key` | `Optional[str]` | `None` | Langfuse secret key for observability |
| `langfuse_public_key` | `Optional[str]` | `None` | Langfuse public key for observability |
| `langfuse_host` | `str` | `https://cloud.langfuse.com` | Langfuse host URL |

### Model Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `default_model_name` | `str` | `gemini-2.5-flash` | Default model for classification |
| `fallback_model_name` | `str` | `gemini-2.5-flash` | Fallback model if default fails |

### Agent Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `default_agent_type` | `AgentType` | `LANGGRAPH` | Default agent implementation |
| `default_top_k` | `int` | `10` | Default number of candidates (1-50) |

### Data Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `data_directory` | `Path` | `Path("data")` | Directory containing HS codes data |
| `hs_codes_file` | `str` | `hs_codes_all.csv` | HS codes CSV file name |
| `examples_file` | `str` | `hs6_examples_cleaned.csv` | Product examples CSV file |
| `tax_codes_file` | `str` | `avalara_tax_codes.xlsx` | Tax codes Excel file |

### API Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `api_host` | `str` | `0.0.0.0` | API server host |
| `api_port` | `int` | `9999` | API server port (1-65535) |
| `api_workers` | `int` | `1` | Number of API workers |

### Performance Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enable_caching` | `bool` | `True` | Enable data caching |
| `cache_ttl_seconds` | `int` | `3600` | Cache TTL in seconds (≥60) |
| `max_concurrent_requests` | `int` | `10` | Max concurrent requests |
| `request_timeout_seconds` | `int` | `300` | Request timeout (≥30) |

### Logging Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `log_level` | `LogLevel` | `INFO` | Logging level |
| `enable_langfuse_logging` | `bool` | `True` | Enable Langfuse logging |
| `log_file` | `Optional[Path]` | `None` | Log file path |

### Development Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `debug_mode` | `bool` | `False` | Enable debug mode |
| `development_mode` | `bool` | `False` | Enable development features |

## 🔍 Validation Rules

### Custom Validators

The configuration includes several custom validators:

#### `validate_data_directory`
Ensures the data directory exists and is accessible.

```python
@validator("data_directory")
def validate_data_directory(cls, v):
    if not v.exists():
        raise ValueError(f"Data directory does not exist: {v}")
    return v
```

#### `validate_google_api_key`
Ensures a valid Google API key is provided.

```python
@validator("google_api_key")
def validate_google_api_key(cls, v):
    if not v or v == "your_google_api_key_here":
        raise ValueError(
            "Google API key must be provided. "
            "Set GOOGLE_API_KEY environment variable."
        )
    return v
```

### Field Validation

Many fields include validation constraints:

```python
# Numeric ranges
default_top_k: int = Field(..., ge=1, le=50)
api_port: int = Field(..., ge=1, le=65535)
cache_ttl_seconds: int = Field(..., ge=60)

# String constraints
google_api_key: str = Field(..., min_length=1)
hs_codes_file: str = Field(..., min_length=1)
```

## 🏗️ Helper Properties

### Computed Properties

The settings class provides several computed properties:

#### `langfuse_enabled`
Checks if Langfuse is properly configured.

```python
@property
def langfuse_enabled(self) -> bool:
    return (
        self.enable_langfuse_logging and
        self.langfuse_secret_key is not None and
        self.langfuse_public_key is not None
    )
```

#### File Path Properties
Convenient access to full file paths:

```python
@property
def hs_codes_path(self) -> Path:
    return self.data_directory / self.hs_codes_file

@property
def examples_path(self) -> Path:
    return self.data_directory / self.examples_file

@property
def tax_codes_path(self) -> Path:
    return self.data_directory / self.tax_codes_file
```

## 🚀 Usage Examples

### Basic Usage

```python
from hs_agent.config import settings

# Access configuration values
print(f"Using model: {settings.default_model_name}")
print(f"Data directory: {settings.data_directory}")
print(f"API port: {settings.api_port}")

# Check computed properties
if settings.langfuse_enabled:
    print("Langfuse observability is enabled")

# Get file paths
print(f"HS codes file: {settings.hs_codes_path}")
```

### Environment Variable Override

```python
import os
from hs_agent.config.settings import HSAgentSettings

# Set environment variables
os.environ["DEFAULT_MODEL_NAME"] = "gemini-2.5-flash"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["MAX_CONCURRENT_REQUESTS"] = "20"

# Create new settings instance (or restart application)
custom_settings = HSAgentSettings()
print(f"Model: {custom_settings.default_model_name}")  # gemini-2.5-flash
print(f"Log level: {custom_settings.log_level}")       # DEBUG
```

### Configuration Validation

```python
from hs_agent.config.settings import HSAgentSettings
from pydantic import ValidationError

try:
    # This will raise ValidationError if invalid
    settings = HSAgentSettings(
        google_api_key="",  # Invalid: empty key
        default_top_k=100,  # Invalid: exceeds maximum
        api_port=70000      # Invalid: exceeds port range
    )
except ValidationError as e:
    print(f"Configuration errors: {e.errors()}")
```

### Using with Dependency Injection

```python
from hs_agent.config import settings
from hs_agent.core.data_loader import HSDataLoader
from hs_agent.agents.langgraph.agents import HSLangGraphAgent

# Configuration is automatically injected
loader = HSDataLoader()  # Uses settings.data_directory
agent = HSLangGraphAgent(loader)  # Uses settings.default_model_name
```

## 🔧 Configuration File Support

### .env File Loading

The configuration automatically loads from `.env` files:

```bash
# .env
GOOGLE_API_KEY=your_api_key_here
LANGFUSE_SECRET_KEY=sk-lf-your-secret
DEFAULT_MODEL_NAME=gemini-2.5-flash
LOG_LEVEL=DEBUG
```

### Multiple Environment Files

```python
from hs_agent.config.settings import HSAgentSettings

# Load from specific file
settings = HSAgentSettings(_env_file=".env.production")

# Load from multiple files (later files override earlier ones)
settings = HSAgentSettings(_env_file=[".env", ".env.local"])
```

## 🐛 Error Handling

### Configuration Errors

The configuration system provides detailed error messages:

```python
from pydantic import ValidationError

try:
    settings = HSAgentSettings()
except ValidationError as e:
    for error in e.errors():
        print(f"Field: {error['loc']}")
        print(f"Error: {error['msg']}")
        print(f"Value: {error['input']}")
```

### Common Error Messages

- `"Google API key must be provided"`: Missing or invalid API key
- `"Data directory does not exist"`: Invalid data directory path
- `"ensure this value is greater than or equal to 1"`: Numeric constraint violation
- `"field required"`: Missing required field

## 📚 Related Documentation

- [Configuration Guide](../../getting-started/configuration.md) - Detailed setup instructions
- [CLI Usage](../../user-guide/cli-usage.md) - Using configuration with CLI
- [Testing Guide](../../development/testing.md) - Testing with configuration
- [Refactored Structure](../../architecture/refactored-structure.md) - Architecture overview