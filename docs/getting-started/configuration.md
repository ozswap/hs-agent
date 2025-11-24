# Configuration Guide

HS Agent uses environment variables for configuration.

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
# Langfuse Observability (local development)
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_HOST=http://localhost:3000

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
| `ENABLE_LANGFUSE_LOGGING` | `true` | Enable Langfuse |

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
LANGFUSE_SECRET_KEY=sk-lf-dev...
LANGFUSE_PUBLIC_KEY=pk-lf-dev...
LANGFUSE_HOST=http://localhost:3000
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

### Production

```bash
# .env
LANGFUSE_SECRET_KEY=sk-lf-prod...
LANGFUSE_PUBLIC_KEY=pk-lf-prod...
LANGFUSE_HOST=https://cloud.langfuse.com
LOG_LEVEL=INFO
API_WORKERS=4
```

## Next Steps

- [Quick Start Guide](quickstart.md)
- [CLI Usage](../user-guide/cli-usage.md)
