# Configuration Guide

HS Agent uses environment variables for configuration.

For Logfire setup (auth, projects, write tokens), see [Pydantic Logfire docs](https://logfire.pydantic.dev/docs/).

## Required Setup

### Google Cloud Authentication

```bash
# Authenticate
gcloud auth application-default login

# Set project (if needed)
gcloud config set project YOUR_PROJECT_ID
```

### Environment Variables

Create a `.env` file:

```bash
# Logfire Observability
# - Local dev: run `uv run logfire auth` then `uv run logfire projects use <project>`
# - Production: set LOGFIRE_TOKEN in your environment
ENABLE_LOGFIRE=true
LOGFIRE_SERVICE_NAME=hs-agent
LOGFIRE_ENV=local

# Optional: Model Configuration
DEFAULT_MODEL_NAME=gemini-2.5-flash
DEFAULT_TOP_K=10

# Optional: API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Optional: Development
DEBUG_MODE=false
LOG_LEVEL=INFO
```

## Configuration Options

### Model Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_MODEL_NAME` | `gemini-2.5-flash` | AI model to use |
| `DEFAULT_TOP_K` | `10` | Candidates to consider (1-50) |

### API Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |
| `API_WORKERS` | `1` | Number of workers |

### Data Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIRECTORY` | `data` | HS codes data directory |
| `HS_CODES_FILE` | `hs_codes_all.csv` | HS codes filename |
| `EXAMPLES_FILE` | `hs6_examples_cleaned.csv` | Examples filename |

### Logging Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEBUG_MODE` | `false` | Enable debug mode |
| `ENABLE_LOGFIRE` | `true` | Enable Logfire observability |
| `LOGFIRE_SERVICE_NAME` | `hs-agent` | Service name in Logfire |
| `LOGFIRE_ENV` | *(unset)* | Environment tag in Logfire |

## Verify Configuration

```bash
# Check configuration
uv run hs-agent config

# View all settings
uv run hs-agent config --all

# Run health check
uv run hs-agent health
```

## Environment Examples

### Development

```bash
# .env
ENABLE_LOGFIRE=true
LOGFIRE_SERVICE_NAME=hs-agent
LOGFIRE_ENV=dev
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

### Production

```bash
# .env
ENABLE_LOGFIRE=true
# Recommended: set LOGFIRE_TOKEN in your deployment environment / secrets manager
LOGFIRE_SERVICE_NAME=hs-agent
LOGFIRE_ENV=prod
LOG_LEVEL=INFO
API_WORKERS=4
```

## Next Steps

- [Quick Start Guide](quickstart.md)
- [CLI Usage](../user-guide/cli-usage.md)
