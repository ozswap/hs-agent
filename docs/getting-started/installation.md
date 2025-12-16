# Installation

Quick guide to set up HS Agent on your machine.

## Prerequisites

- Python 3.12+
- Google Cloud CLI
- Git

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/hs-agent.git
cd hs-agent
```

### 2. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 3. Authenticate with Google Cloud

```bash
gcloud auth application-default login
```

### 4. Set Up Environment

Create a `.env` file:

```bash
# Logfire Observability
# - Local dev: run `uv run logfire auth` then `uv run logfire projects use <project>`
# - Production: set LOGFIRE_TOKEN in your environment
ENABLE_LOGFIRE=true
LOGFIRE_SERVICE_NAME=hs-agent
LOGFIRE_ENV=local
```

See [Pydantic Logfire docs](https://logfire.pydantic.dev/docs/) for authentication and write token details.

## Verification

Test your installation:

```bash
# Check system health
uv run hs-agent health

# Try a classification
uv run hs-agent classify "laptop computer"
```

## Next Steps

- [Quick Start Guide](quickstart.md)
- [Configuration Options](configuration.md)
