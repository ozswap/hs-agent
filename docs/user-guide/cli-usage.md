# CLI Usage Guide

## Overview

HS Agent provides a unified, beautiful command-line interface that replaces the previous scattered CLI commands. The new `hs-agent` command offers a consistent experience with rich formatting, progress indicators, and comprehensive help.

## 🚀 Quick Start

### Basic Classification

```bash
# Classify a product description
hs-agent classify "Laptop computer with 16GB RAM and 512GB SSD"

# Use specific agent type
hs-agent classify "Cotton t-shirt, size medium" --agent langgraph

# Adjust number of candidates considered
hs-agent classify "Fresh apples from Washington state" --top-k 5

# Enable verbose output
hs-agent classify "Smartphone with 128GB storage" --verbose
```

### System Management

```bash
# Check system health
hs-agent health

# View configuration
hs-agent config

# View all configuration options
hs-agent config --all

# Show version information
hs-agent version
```

## 📋 Command Reference

### `hs-agent classify`

Classify a product description into an HS code using hierarchical AI classification.

```bash
hs-agent classify [OPTIONS] PRODUCT_DESCRIPTION
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `PRODUCT_DESCRIPTION` | string | ✅ | Product description to classify |

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--agent` | `-a` | choice | `langgraph` | Agent type (`traditional` or `langgraph`) |
| `--top-k` | `-k` | integer | `10` | Number of candidates to consider (1-50) |
| `--verbose` | `-v` | flag | `false` | Enable verbose output |
| `--help` | | flag | | Show help message |

#### Examples

```bash
# Basic classification
hs-agent classify "Laptop computer"

# Use traditional agent
hs-agent classify "Cotton shirt" --agent traditional

# Consider more candidates
hs-agent classify "Electronic device" --top-k 15

# Verbose output with detailed information
hs-agent classify "Industrial machinery" --verbose

# Complex product description
hs-agent classify "Portable digital automatic data processing machine weighing 2.5kg with 16GB RAM, 512GB SSD, and 15.6-inch display"
```

#### Output Format

The classify command provides rich, formatted output:

```
🎯 HS Classification Result
┌─────────────────────────────────────────────────────────────┐
│ ✅ Classification Complete                                   │
│                                                             │
│ Product: Laptop computer with 16GB RAM and 512GB SSD       │
│ Final HS Code: 847130                                       │
│ Confidence: 95.2%                                           │
│ Processing Time: 2.45s                                      │
└─────────────────────────────────────────────────────────────┘

📊 Hierarchical Classification Breakdown
┌─────────────────┬─────────┬────────────┬──────────────────────┐
│ Level           │ Code    │ Confidence │ Reasoning            │
├─────────────────┼─────────┼────────────┼──────────────────────┤
│ Chapter (2-digit)│ 84      │ 92.0%      │ Machinery and mech...│
│ Heading (4-digit)│ 8471    │ 94.5%      │ Data processing ma...│
│ Subheading (6-digit)│ 847130 │ 95.2%   │ Portable computers...│
└─────────────────┴─────────┴────────────┴──────────────────────┘
```

### `hs-agent config`

Display current configuration settings with masked sensitive values.

```bash
hs-agent config [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--all` | flag | `false` | Show all configuration values |
| `--help` | flag | | Show help message |

#### Examples

```bash
# Show basic configuration
hs-agent config

# Show all configuration options
hs-agent config --all
```

#### Output Format

```
⚙️ HS Agent Configuration

Current Settings
┌─────────────────────┬──────────────────────┬─────────────┐
│ Setting             │ Value                │ Source      │
├─────────────────────┼──────────────────────┼─────────────┤
│ Default Agent Type  │ langgraph            │ config      │
│ Default Model       │ gemini-2.5-flash│ config      │
│ Data Directory      │ /path/to/data        │ config      │
│ Log Level           │ INFO                 │ config      │
│ Google API Key      │ AIzaSyAb****xyz     │ environment │
│ Langfuse Enabled    │ ✅ Yes               │ config      │
│ Langfuse Host       │ https://cloud.lang...│ environment │
└─────────────────────┴──────────────────────┴─────────────┘

💡 Use --all to see all configuration options
```

### `hs-agent health`

Perform comprehensive health checks on the HS Agent system.

```bash
hs-agent health
```

#### Health Checks Performed

1. **Configuration Validation**: Verify all required settings
2. **Data File Accessibility**: Check HS codes and examples files
3. **Agent Initialization**: Test agent creation and setup
4. **External Service Connectivity**: Verify API access (if configured)

#### Examples

```bash
# Run health check
hs-agent health
```

#### Output Format

```
🏥 HS Agent Health Check

⚙️ Configuration... ✅ OK
📊 Data files... ✅ OK (5613 codes loaded)
🤖 Agent initialization... ✅ OK

🎉 All systems operational!
```

### `hs-agent version`

Display version and build information.

```bash
hs-agent version
```

#### Output Format

```
HS Agent v0.1.0
Configuration: langgraph agent
Model: gemini-2.5-flash
```

## 🎨 Rich Terminal Features

### Progress Indicators

The CLI provides beautiful progress indicators during long operations:

```bash
hs-agent classify "Complex product description"
```

```
📊 Loading HS codes data... ⠋
🤖 Initializing langgraph agent... ⠙
🔍 Classifying product... ⠹
```

### Color-Coded Output

- 🟢 **Green**: Success messages and positive results
- 🔴 **Red**: Error messages and failures
- 🟡 **Yellow**: Warnings and important notices
- 🔵 **Blue**: Information and headers
- ⚪ **Gray**: Secondary information and details

### Interactive Help

```bash
# Get help for main command
hs-agent --help

# Get help for specific subcommand
hs-agent classify --help
hs-agent config --help
hs-agent health --help
```

## 🔧 Advanced Usage

### Environment-Specific Configuration

```bash
# Development environment
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
hs-agent classify "test product" --verbose

# Production environment
export LOG_LEVEL=INFO
export MAX_CONCURRENT_REQUESTS=20
hs-agent classify "production product"
```

### Batch Processing with Shell Scripts

```bash
#!/bin/bash
# batch_classify.sh

products=(
    "Laptop computer"
    "Cotton t-shirt"
    "Fresh apples"
    "Smartphone"
)

for product in "${products[@]}"; do
    echo "Classifying: $product"
    hs-agent classify "$product" --agent langgraph
    echo "---"
done
```

### Integration with Other Tools

```bash
# Pipe output to file
hs-agent classify "Product description" > classification_result.txt

# Use with jq for JSON processing (if JSON output is added)
hs-agent classify "Product" --format json | jq '.final_hs_code'

# Integration with monitoring
hs-agent health && echo "System healthy" || echo "System issues detected"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Command Not Found

**Error**: `hs-agent: command not found`

**Solution**:
```bash
# Install the package
pip install -e .

# Or use uv
uv sync

# Verify installation
which hs-agent
```

#### 2. Configuration Errors

**Error**: `ConfigurationError: Google API key must be provided`

**Solution**:
```bash
# Set required environment variables
export GOOGLE_API_KEY="your-api-key"

# Or create .env file
echo "GOOGLE_API_KEY=your-api-key" > .env

# Verify configuration
hs-agent config
```

#### 3. Data Loading Errors

**Error**: `DataLoadingError: HS codes file not found`

**Solution**:
```bash
# Check data directory exists
ls -la data/

# Verify required files
ls -la data/hs_codes_all.csv
ls -la data/hs6_examples_cleaned.csv

# Run health check
hs-agent health
```

#### 4. Agent Initialization Errors

**Error**: `AgentError: Failed to initialize langgraph agent`

**Solution**:
```bash
# Check API key is valid
hs-agent health

# Try different agent type
hs-agent classify "test" --agent traditional

# Enable debug mode
export DEBUG_MODE=true
hs-agent classify "test" --verbose
```

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
hs-agent classify "test product" --verbose
```

### Getting Help

```bash
# General help
hs-agent --help

# Command-specific help
hs-agent classify --help

# Check system status
hs-agent health

# View configuration
hs-agent config --all
```

## 🔄 Migration from Legacy Commands

### Command Mapping

| Legacy Command | New Unified Command |
|----------------|-------------------|
| `hs-classify "product"` | `hs-agent classify "product" --agent traditional` |
| `hs-langgraph-classify "product"` | `hs-agent classify "product" --agent langgraph` |
| `hs-api` | Use FastAPI directly or new API interface |
| `hs-langgraph-api` | Use FastAPI directly or new API interface |

### Migration Script

```bash
#!/bin/bash
# migrate_commands.sh

# Replace legacy commands in scripts
sed -i 's/hs-classify/hs-agent classify --agent traditional/g' *.sh
sed -i 's/hs-langgraph-classify/hs-agent classify --agent langgraph/g' *.sh

echo "Migration complete. Please review and test your scripts."
```

## 📚 Related Documentation

- [Configuration Guide](../getting-started/configuration.md) - Detailed configuration options
- [API Usage](api-usage.md) - REST API interface
- [Quick Start](../getting-started/quickstart.md) - Getting started guide
- [Refactored Structure](../architecture/refactored-structure.md) - Architecture overview