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
# Langfuse Observability (local development)
LANGFUSE_SECRET_KEY=sk-lf-your-key...
LANGFUSE_PUBLIC_KEY=pk-lf-your-key...
LANGFUSE_HOST=http://localhost:3000
```

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
