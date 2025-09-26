# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HS Agent is an AI-powered Harmonized System (HS) code classification service that maps product descriptions and tax codes to appropriate 6-digit HS codes using hierarchical machine learning workflows. The system supports both traditional Pydantic AI agents and modern LangGraph-based agents with comprehensive observability.

## Architecture

### Core Components

- **Agents**: Two implementations for HS code classification
  - `hs_agent/agents/langgraph/` - Modern LangGraph-based agents with state management
  - `hs_agent/agents/traditional/` - Traditional Pydantic AI agents
- **Data Loader** (`hs_agent/core/data_loader.py`) - Centralized HS codes data management with caching
- **Workflows** (`hs_agent/workflows/`) - Tax code mapping and batch processing workflows
- **API Server** (`app.py`) - FastAPI application with REST endpoints and dashboard
- **CLI** (`hs_agent/cli.py`) - Unified command-line interface with both API and local modes

### Data Flow

1. **Data Loading**: HSDataLoader loads HS codes from CSV files and organizes hierarchically (2-digit chapters → 4-digit headings → 6-digit subheadings)
2. **Classification**: Agents perform hierarchical classification using AI models (Google Vertex AI)
3. **Mapping**: TaxCodeMapper handles bulk tax code to HS code mappings
4. **Observability**: Langfuse integration tracks all agent interactions and performance

### Agent Architecture

- **LangGraph Agents**: Use StateGraph for complex multi-step workflows with candidate ranking and selection phases
- **Traditional Agents**: Direct Pydantic AI implementation with structured outputs
- Both support configurable top-k candidate selection and confidence scoring

## Development Commands

### Installation and Setup
```bash
# Install dependencies (uses pyproject.toml)
pip install -e .

# Alternative: use uv for faster installs
uv install -e .
```

### CLI Usage
```bash
# Classify single product
hs-agent classify "laptop computer"

# Use specific agent type
hs-agent classify "cotton t-shirt" --agent langgraph

# Force local mode (bypass API server)
hs-agent classify "fresh apples" --local

# Start API server
hs-agent serve

# Check system health
hs-agent health

# View configuration
hs-agent config
```

### Testing
```bash
# Run all tests with pytest
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=hs_agent

# Run single test file
pytest tests/unit/test_classifier.py
```

### API Server Development
```bash
# Start development server with auto-reload
hs-agent serve --reload

# Start on specific port
hs-agent serve --port 8080

# Access API documentation at http://localhost:8000/docs
# Access dashboard at http://localhost:8000/dashboard
```

### Scripts and Debugging
- `scripts/debug_*.py` - Various debugging utilities for testing classification flows
- Batch processing scripts in root directory (run_*.py) for large-scale mappings

## Configuration

### Environment Variables
- `GOOGLE_API_KEY` - Required for AI model access
- `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY` - Optional, for observability
- `LANGFUSE_HOST` - Langfuse server URL
- `DEBUG_MODE` - Enable debug logging

### Data Files
- `data/hs_codes_all.csv` - Complete HS codes database
- `data/hs6_examples_cleaned.csv` - Product examples for each HS code
- `data/avalara_tax_codes.xlsx` - Tax codes for mapping workflows

## Key Patterns

### Agent Usage
```python
# Initialize data loader
loader = HSDataLoader()
loader.load_all_data()

# Create and use LangGraph agent
agent = HSLangGraphAgent(loader)
result = await agent.classify_hierarchical("product description")
```

### Error Handling
- Custom exception hierarchy in `hs_agent/core/exceptions.py`
- Comprehensive logging with structured data using loguru
- Graceful degradation between API and local modes

### Testing Strategy
- Unit tests with mocked dependencies in `tests/unit/`
- Integration tests for full workflows in `tests/integration/`
- Shared fixtures in `tests/conftest.py` with sample data
- Mock agents and data loaders for isolated testing

## Observability

- Langfuse integration for tracking agent performance and costs
- Structured logging with classification start/complete events
- Health check endpoints for monitoring system status
- Processing time tracking and confidence score monitoring