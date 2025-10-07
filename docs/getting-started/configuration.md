# Configuration Guide

## Overview

HS Agent uses a centralized configuration system built with Pydantic Settings that provides type-safe, validated configuration management. All settings can be configured via environment variables or configuration files.

## 🔧 Configuration Structure

The configuration is organized into logical groups:

- **API Keys & Authentication**: External service credentials
- **Model Configuration**: AI model settings
- **Agent Configuration**: Agent behavior settings
- **Data Configuration**: Data file paths and settings
- **API Configuration**: Server and API settings
- **Performance Configuration**: Caching and concurrency settings
- **Logging Configuration**: Logging behavior and output
- **Development Configuration**: Debug and development features

## 📋 Complete Configuration Reference

### API Keys and Authentication

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `google_api_key` | `GOOGLE_API_KEY` | **Required** | Google API key for Vertex AI/Gemini models |
| `langfuse_secret_key` | `LANGFUSE_SECRET_KEY` | `None` | Langfuse secret key for observability |
| `langfuse_public_key` | `LANGFUSE_PUBLIC_KEY` | `None` | Langfuse public key for observability |
| `langfuse_host` | `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Langfuse host URL |

### Model Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `default_model_name` | `DEFAULT_MODEL_NAME` | `gemini-2.5-flash` | Default model for classification |
| `fallback_model_name` | `FALLBACK_MODEL_NAME` | `gemini-2.5-flash` | Fallback model if default fails |

### Agent Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `default_agent_type` | `DEFAULT_AGENT_TYPE` | `langgraph` | Default agent implementation (`traditional` or `langgraph`) |
| `default_top_k` | `DEFAULT_TOP_K` | `10` | Default number of candidates to consider (1-50) |

### Data Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `data_directory` | `DATA_DIRECTORY` | `data` | Directory containing HS codes data |
| `hs_codes_file` | `HS_CODES_FILE` | `hs_codes_all.csv` | HS codes CSV file name |
| `examples_file` | `EXAMPLES_FILE` | `hs6_examples_cleaned.csv` | Product examples CSV file name |
| `tax_codes_file` | `TAX_CODES_FILE` | `avalara_tax_codes.xlsx` | Avalara tax codes Excel file name |

### API Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `api_host` | `API_HOST` | `0.0.0.0` | API server host |
| `api_port` | `API_PORT` | `9999` | API server port (1-65535) |
| `api_workers` | `API_WORKERS` | `1` | Number of API workers |

### Performance Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `enable_caching` | `ENABLE_CACHING` | `true` | Enable data caching for performance |
| `cache_ttl_seconds` | `CACHE_TTL_SECONDS` | `3600` | Cache TTL in seconds (≥60) |
| `max_concurrent_requests` | `MAX_CONCURRENT_REQUESTS` | `10` | Maximum concurrent classification requests |
| `request_timeout_seconds` | `REQUEST_TIMEOUT_SECONDS` | `300` | Request timeout in seconds (≥30) |

### Logging Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `log_level` | `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `enable_langfuse_logging` | `ENABLE_LANGFUSE_LOGGING` | `true` | Enable Langfuse observability logging |
| `log_file` | `LOG_FILE` | `None` | Log file path (if None, logs to console) |

### Development Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `debug_mode` | `DEBUG_MODE` | `false` | Enable debug mode |
| `development_mode` | `DEVELOPMENT_MODE` | `false` | Enable development mode features |

## 🚀 Quick Setup

### 1. Environment File Setup

Create a `.env` file in your project root:

```bash
# Required: Google API Key
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Langfuse Observability
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_HOST=https://cloud.langfuse.com

# Optional: Model Configuration
DEFAULT_MODEL_NAME=gemini-2.5-flash
DEFAULT_AGENT_TYPE=langgraph

# Optional: Performance Tuning
MAX_CONCURRENT_REQUESTS=5
ENABLE_CACHING=true

# Optional: Development
DEBUG_MODE=false
LOG_LEVEL=INFO
```

### 2. Verify Configuration

Use the CLI to check your configuration:

```bash
# Check basic configuration
hs-agent config

# Check all configuration options
hs-agent config --all

# Run health check
hs-agent health
```

## 🔐 Security Best Practices

### API Key Management

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Rotate keys regularly** and update configuration
4. **Use different keys** for development and production

```bash
# Good: Use environment variables
export GOOGLE_API_KEY="your-actual-key"

# Bad: Don't hardcode in files
GOOGLE_API_KEY="your-actual-key"  # Don't do this!
```

### Environment Separation

Use different configuration for different environments:

```bash
# Development
export ENVIRONMENT=development
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG

# Production
export ENVIRONMENT=production
export DEBUG_MODE=false
export LOG_LEVEL=INFO
```

## 🎯 Configuration Examples

### Basic Setup (Minimal)

```bash
# .env file
GOOGLE_API_KEY=your_google_api_key_here
```

### Development Setup

```bash
# .env file
GOOGLE_API_KEY=your_google_api_key_here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
DEBUG_MODE=true
LOG_LEVEL=DEBUG
DEVELOPMENT_MODE=true
```

### Production Setup

```bash
# .env file
GOOGLE_API_KEY=your_production_api_key
LANGFUSE_SECRET_KEY=sk-lf-your-production-secret
LANGFUSE_PUBLIC_KEY=pk-lf-your-production-public
LANGFUSE_HOST=https://your-langfuse-instance.com
LOG_LEVEL=INFO
ENABLE_CACHING=true
MAX_CONCURRENT_REQUESTS=20
API_WORKERS=4
```

### High-Performance Setup

```bash
# .env file
GOOGLE_API_KEY=your_api_key
DEFAULT_MODEL_NAME=gemini-2.5-flash  # Faster model
MAX_CONCURRENT_REQUESTS=50
ENABLE_CACHING=true
CACHE_TTL_SECONDS=7200
API_WORKERS=8
REQUEST_TIMEOUT_SECONDS=120
```

## 🔧 Programmatic Configuration

### Accessing Configuration

```python
from hs_agent.config import settings

# Access configuration values
print(f"Using model: {settings.default_model_name}")
print(f"Data directory: {settings.data_directory}")
print(f"Langfuse enabled: {settings.langfuse_enabled}")

# Configuration is type-safe and validated
assert isinstance(settings.default_top_k, int)
assert 1 <= settings.default_top_k <= 50
```

### Configuration Properties

The settings object provides helpful properties:

```python
from hs_agent.config import settings

# Check if Langfuse is properly configured
if settings.langfuse_enabled:
    print("Langfuse observability is enabled")

# Get full file paths
print(f"HS codes file: {settings.hs_codes_path}")
print(f"Examples file: {settings.examples_path}")
print(f"Tax codes file: {settings.tax_codes_path}")
```

### Runtime Configuration Updates

```python
from hs_agent.config import settings

# Note: Settings are validated on creation
# For runtime updates, create new settings instance
import os
os.environ["LOG_LEVEL"] = "DEBUG"

# Reload settings (in practice, restart application)
from hs_agent.config.settings import HSAgentSettings
new_settings = HSAgentSettings()
```

## 🐛 Troubleshooting

### Common Configuration Issues

#### 1. Missing Google API Key

**Error**: `ValidationError: Google API key must be provided`

**Solution**:
```bash
# Set the API key
export GOOGLE_API_KEY="your-actual-api-key"

# Or add to .env file
echo "GOOGLE_API_KEY=your-actual-api-key" >> .env
```

#### 2. Data Directory Not Found

**Error**: `ConfigurationError: Data directory does not exist`

**Solution**:
```bash
# Create the data directory
mkdir -p data

# Or set custom data directory
export DATA_DIRECTORY="/path/to/your/data"
```

#### 3. Invalid Configuration Values

**Error**: `ValidationError: ensure this value is greater than or equal to 1`

**Solution**:
```bash
# Check valid ranges in the configuration reference above
export DEFAULT_TOP_K=10  # Must be 1-50
export API_PORT=8080     # Must be 1-65535
```

### Configuration Validation

Use the health check to validate your configuration:

```bash
# Run comprehensive health check
hs-agent health

# Check specific configuration
hs-agent config --all
```

### Debug Configuration Issues

Enable debug mode for detailed configuration information:

```bash
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
hs-agent health
```

## 📚 Related Documentation

- [Installation Guide](installation.md) - Setting up the project
- [Quick Start](quickstart.md) - Basic usage examples
- [CLI Usage](../user-guide/cli-usage.md) - Command-line interface
- [API Usage](../user-guide/api-usage.md) - REST API examples
- [Refactored Structure](../architecture/refactored-structure.md) - Architecture overview