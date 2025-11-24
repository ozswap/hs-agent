# HS Agent

AI-powered Harmonized System (HS) code classification service that automatically maps product descriptions to 6-digit HS codes using hierarchical workflows.

## What It Does

Classifies products into HS codes (international trade classification system) using AI:
- Takes product descriptions as input
- Returns 6-digit HS codes with confidence scores and reasoning
- Supports both API and CLI interfaces

## Quick Start

### Installation

```bash
# Clone and install
git clone https://github.com/yourusername/hs-agent.git
cd hs-agent
uv sync
```

### Setup

**Authenticate with Google Cloud:**

```bash
gcloud auth application-default login
```

**Create a `.env` file:**

```bash
# Langfuse Observability (local development)
LANGFUSE_SECRET_KEY=sk-lf-f048...
LANGFUSE_PUBLIC_KEY=pk-lf-aba5...
LANGFUSE_HOST=http://localhost:3000
```

### Usage

**CLI:**
```bash
# Classify a product
uv run hs-agent classify "laptop computer"

# Start API server
uv run hs-agent serve
```

**API:**
```bash
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{"product_description": "laptop computer"}'
```

**Web UI:**

Access the interactive web interface:
- **Main Classification UI**: http://localhost:8000/classify
- **Multi-Path Classification**: http://localhost:8000/classify-multi
- **API Docs**: http://localhost:8000/docs

The web UI includes:
- Real-time classification with visual feedback
- High Performance Mode toggle for multi-path exploration
- Confidence indicators with color-coded bars
- Hierarchical visualization (Chapter → Heading → Subheading)
- Tree visualization for path exploration
- Expandable reasoning sections with markdown support

## Features

- Hierarchical classification (2-digit → 4-digit → 6-digit HS codes)
- Two agent implementations: Traditional (Pydantic AI) and LangGraph
- FastAPI REST endpoints with interactive Swagger docs
- Interactive web UI with visual path exploration
- CLI with rich formatting
- Langfuse observability for tracking and debugging

## Requirements

- Python 3.12+
- Google Cloud Vertex AI API access

## Documentation

Full documentation in `docs/` directory. Run `uv run mkdocs serve` to view locally.

## License

MIT License
