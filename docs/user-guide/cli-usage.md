# CLI Usage Guide

Complete guide to the `hs-agent` command-line interface.

## Quick Start

```bash
# Classify a product
uv run hs-agent classify "laptop computer"

# Check system health
uv run hs-agent health

# View configuration
uv run hs-agent config
```

## Commands

### `hs-agent classify`

Classify a product description into an HS code.

```bash
uv run hs-agent classify [OPTIONS] PRODUCT_DESCRIPTION
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--top-k` | integer | `10` | Number of candidates (1-50) |
| `--verbose` | flag | `false` | Enable verbose output |
| `--local` | flag | `false` | Force local mode (bypass API) |

**Examples:**

```bash
# Basic classification
uv run hs-agent classify "laptop computer"

# Adjust candidates considered
uv run hs-agent classify "cotton shirt" --top-k 15

# Verbose output with details
uv run hs-agent classify "industrial machinery" --verbose

# Force local processing
uv run hs-agent classify "fresh apples" --local
```

### `hs-agent serve`

Start the API server.

```bash
uv run hs-agent serve [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--host` | string | `0.0.0.0` | Server host |
| `--port` | integer | `8000` | Server port |
| `--reload` | flag | `false` | Auto-reload on changes |

**Examples:**

```bash
# Start server
uv run hs-agent serve

# Development mode with auto-reload
uv run hs-agent serve --reload

# Custom port
uv run hs-agent serve --port 8080
```

Access the interfaces:
- Web UI: http://localhost:8000/classify
- API Docs: http://localhost:8000/docs
- Multi-Path UI: http://localhost:8000/classify-multi

### `hs-agent health`

Run system health checks.

```bash
uv run hs-agent health
```

Checks:
- Configuration validity
- Data file accessibility
- Agent initialization
- Service connectivity

**Example output:**

```
🏥 HS Agent Health Check

⚙️ Configuration... ✅ OK
📊 Data files... ✅ OK (5613 codes loaded)
🤖 Agent initialization... ✅ OK

🎉 All systems operational!
```

### `hs-agent config`

Display configuration settings.

```bash
uv run hs-agent config [--all]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--all` | Show all configuration values |

**Examples:**

```bash
# Show basic configuration
uv run hs-agent config

# Show all settings
uv run hs-agent config --all
```

## Output Format

### Classification Results

The CLI provides rich, formatted output:

```
🎯 HS Classification Result
┌─────────────────────────────────────────────┐
│ ✅ Classification Complete                   │
│                                             │
│ Product: Laptop computer                    │
│ Final HS Code: 847130                       │
│ Confidence: 95.2%                           │
└─────────────────────────────────────────────┘

📊 Hierarchical Breakdown
• Chapter (84): Machinery - 92.0%
• Heading (8471): Data processing - 94.5%
• Subheading (847130): Portable computers - 95.2%
```

### Color Coding

- 🟢 **Green**: Success and high confidence
- 🔴 **Red**: Errors and failures
- 🟡 **Yellow**: Warnings and medium confidence
- 🔵 **Blue**: Information and headers

## Advanced Usage

### Environment Configuration

```bash
# Development
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
uv run hs-agent classify "test product" --verbose

# Production
export LOG_LEVEL=INFO
uv run hs-agent classify "product"
```

### Batch Processing

```bash
#!/bin/bash
# batch_classify.sh

products=(
    "Laptop computer"
    "Cotton t-shirt"
    "Fresh apples"
)

for product in "${products[@]}"; do
    echo "Classifying: $product"
    uv run hs-agent classify "$product"
    echo "---"
done
```

### Output Redirection

```bash
# Save to file
uv run hs-agent classify "product" > result.txt

# Check health status
uv run hs-agent health && echo "OK" || echo "FAILED"
```

## Troubleshooting

### Command Not Found

```bash
# Reinstall
uv sync

# Verify installation
which hs-agent
```

### Configuration Errors

```bash
# Check authentication
gcloud auth application-default login

# Verify configuration
uv run hs-agent config --all

# Run health check
uv run hs-agent health
```

### Data Loading Errors

```bash
# Check data files exist
ls -la data/hs_codes_all.csv
ls -la data/hs6_examples_cleaned.csv

# Run health check for details
uv run hs-agent health
```

### Debug Mode

```bash
# Enable detailed logging
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
uv run hs-agent classify "test" --verbose
```

## Getting Help

```bash
# General help
uv run hs-agent --help

# Command-specific help
uv run hs-agent classify --help
uv run hs-agent serve --help
```

## Next Steps

- [Configuration Guide](../getting-started/configuration.md)
- [System Overview](overview.md)
- [Quick Start](../getting-started/quickstart.md)
