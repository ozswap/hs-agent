# Quick Start

Get up and running with HS Agent in minutes.

## CLI Usage

### Basic Classification

```bash
# Classify a product
uv run hs-agent classify "laptop computer"

# Adjust top-k candidates
uv run hs-agent classify "cotton t-shirt" --top-k 5

# Enable verbose output
uv run hs-agent classify "fresh apples" --verbose
```

### System Management

```bash
# Check system health
uv run hs-agent health

# View configuration
uv run hs-agent config

# View all settings
uv run hs-agent config --all
```

## API Server

### Start the Server

```bash
uv run hs-agent serve

# With auto-reload for development
uv run hs-agent serve --reload

# Custom port
uv run hs-agent serve --port 8080
```

### Using the API

```bash
# Classify via API
curl -X POST "http://localhost:8000/api/classify" \
  -H "Content-Type: application/json" \
  -d '{"product_description": "laptop computer"}'
```

### Web UI

Open your browser to:
- **Main UI**: http://localhost:8000/classify
- **Multi-Path**: http://localhost:8000/classify-multi
- **API Docs**: http://localhost:8000/docs

## Python Usage

```python
import asyncio
from hs_agent.agent import HSAgent
from hs_agent.data_loader import HSDataLoader

async def classify_product():
    # Initialize data loader
    loader = HSDataLoader()
    loader.load_all_data()

    # Create agent
    agent = HSAgent(loader)

    # Classify product
    result = await agent.classify("laptop computer")

    print(f"HS Code: {result.final_code}")
    print(f"Confidence: {result.overall_confidence:.2%}")

asyncio.run(classify_product())
```

## Next Steps

- [Full CLI Documentation](../user-guide/cli-usage.md)
- [Configuration Guide](configuration.md)
- [System Overview](../user-guide/overview.md)
