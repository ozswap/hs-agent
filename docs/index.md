# HS Agent Documentation

AI-powered Harmonized System (HS) code classification service.

## Overview

HS Agent automatically classifies products into 6-digit HS codes using hierarchical AI workflows. It provides CLI, API, and Web UI interfaces for easy integration.

## Key Features

- **Hierarchical Classification**: Progressive refinement from 2-digit → 4-digit → 6-digit HS codes
- **Multiple Workflows**: Standard, Wide Net, and Multi-Choice classification approaches
- **RESTful API**: FastAPI-based endpoints with interactive docs
- **Interactive Web UI**: Visual classification with path exploration
- **CLI Interface**: Beautiful command-line interface with rich formatting
- **Logfire Observability**: Trace and debug classifications

## Quick Links

### Getting Started
- [Installation](getting-started/installation.md) - Set up the project
- [Quick Start](getting-started/quickstart.md) - Basic usage examples
- [Configuration](getting-started/configuration.md) - Environment setup

### User Guide
- [CLI Usage](user-guide/cli-usage.md) - Command-line interface
- [System Overview](user-guide/overview.md) - How it works

### Technical Details
- [Wide Net Classification](wide_net_classification_explained.md) - High-performance approach

## Quick Start

### Installation

```bash
git clone https://github.com/your-org/hs-agent.git
cd hs-agent
uv sync
gcloud auth application-default login
```

### Usage

```bash
# CLI
uv run hs-agent classify "laptop computer"

# API Server
uv run hs-agent serve

# Web UI at http://localhost:8000/classify
```

## Architecture

```
Product Description
       ↓
   Data Loader (HS codes + examples)
       ↓
   HSAgent (hierarchical workflow)
       ↓
   Classification Result
   • Chapter (2-digit)
   • Heading (4-digit)
   • Subheading (6-digit)
   • Confidence scores
   • Reasoning
```

## Support

- **Issues**: Report bugs on GitHub
- **Documentation**: Full docs in this directory
- **Health Check**: Run `uv run hs-agent health`
