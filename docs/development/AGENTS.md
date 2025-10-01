# Repository Guidelines

## Project Structure & Module Organization

The HS Agent is organized into a modular Python package structure:

- **`hs_agent/`** - Main package containing all core functionality
  - **`agents/`** - AI agent implementations (traditional Pydantic AI and LangGraph)
  - **`core/`** - Data loading, models, and shared utilities
  - **`interfaces/`** - CLI and API interfaces for user interaction
  - **`workflows/`** - High-level workflows like tax code mapping
- **`data/`** - HS codes datasets and Avalara tax code mappings
- **`docs/`** - MkDocs documentation source files
- **`tests/`** - Test scripts and debugging utilities (test_*.py, debug_*.py)

## Build, Test, and Development Commands

```bash
# Install dependencies (using uv package manager)
uv sync

# Start the FastAPI development server
uvicorn app:app --host 0.0.0.0 --port 9999 --reload

# Run traditional HS classification CLI
hs-classify "Fresh apples from Washington state"

# Run LangGraph HS classification CLI  
hs-langgraph-classify "Computer keyboard for office use"

# Start traditional API server
hs-api

# Start LangGraph API server
hs-langgraph-api

# Build documentation
mkdocs serve

# Run individual test scripts
python test_classifier.py
python test_single_mapping.py
```

## Coding Style & Naming Conventions

- **Indentation**: 4 spaces (Python standard)
- **File naming**: Snake_case for Python files (e.g., `tax_code_mapper.py`)
- **Function/variable naming**: Snake_case (e.g., `classify_hierarchical`, `hs_code`)
- **Class naming**: PascalCase (e.g., `HSClassifier`, `TaxCodeMapper`)
- **Package structure**: Organized by functionality with clear `__init__.py` files

## Testing Guidelines

- **Framework**: Custom test scripts using asyncio for async testing
- **Test files**: Located in root directory with `test_*.py` and `debug_*.py` naming
- **Running tests**: Execute individual test files directly with Python
- **Coverage**: Tests cover classification, data loading, API endpoints, and edge cases

## Commit & Pull Request Guidelines

- **Commit format**: Descriptive messages focusing on functionality (e.g., "Complete LangGraph HS Classification Implementation")
- **Branch naming**: Feature-based branches (e.g., `feature/langgraph-implementation`)
- **Development**: Active development with modular restructuring and agent framework improvements

---

# Repository Tour

## 🎯 What This Repository Does

HS Agent is an AI-powered Harmonized System (HS) code classification system that automates the complex process of assigning 6-digit HS codes to product descriptions using hierarchical machine learning workflows.

**Key responsibilities:**
- Hierarchical HS code classification (2-digit → 4-digit → 6-digit progression)
- Tax code to HS code mapping for Avalara tax codes
- Multi-framework AI agent support (Traditional Pydantic AI + Modern LangGraph)
- RESTful API and CLI interfaces for integration

---

## 🏗️ Architecture Overview

### System Context
```
[Product Description] → [HS Agent] → [Google Vertex AI] → [6-digit HS Code]
                           ↓
                    [Tax Code Mapper] → [Batch Processing Results]
```

### Key Components
- **Data Loader** - Loads and manages HS codes datasets and product examples
- **Traditional Agents** - Pydantic AI-based classification agents with LLM ranking
- **LangGraph Agents** - Modern workflow-based agents using StateGraph orchestration
- **Tax Code Mapper** - Specialized workflow for mapping Avalara tax codes to HS codes
- **API/CLI Interfaces** - FastAPI REST endpoints and Typer-based command-line tools

### Data Flow
1. **Input Processing** - Product description received via API or CLI
2. **Hierarchical Classification** - Progressive refinement from chapter (2-digit) to subheading (6-digit)
3. **LLM Ranking** - AI-powered candidate ranking and selection at each level
4. **Result Generation** - Final HS code with confidence scores and reasoning
5. **Output Delivery** - Structured response with classification details and tracing

---

## 📁 Project Structure [Partial Directory Tree]

```
hs-agent/
├── hs_agent/                  # Main Python package
│   ├── agents/               # AI agent implementations
│   │   ├── traditional/      # Pydantic AI agents
│   │   └── langgraph/        # LangGraph workflow agents
│   ├── core/                 # Core functionality
│   │   ├── data_loader.py    # HS codes data management
│   │   └── models.py         # Pydantic data models
│   ├── interfaces/           # User interfaces
│   │   ├── api/              # FastAPI REST endpoints
│   │   └── cli/              # Typer command-line interfaces
│   └── workflows/            # High-level workflows
│       └── tax_code_mapper.py # Tax code mapping workflow
├── data/                     # Datasets and mappings
│   ├── hs_codes.csv         # HS codes database
│   ├── hs6_examples_cleaned.csv # Product examples
│   └── avalara_tax_codes.xlsx # Tax code mappings
├── docs/                     # MkDocs documentation
├── static/                   # Web dashboard assets
├── app.py                    # FastAPI application entry point
├── main.py                   # Simple CLI entry point
├── pyproject.toml           # Python project configuration
└── mkdocs.yml               # Documentation configuration
```

### Key Files to Know

| File | Purpose | When You'd Touch It |
|------|---------|---------------------|
| `hs_agent/core/data_loader.py` | HS codes data loading and search | Adding new data sources |
| `hs_agent/agents/langgraph/agents.py` | LangGraph workflow implementation | Modifying classification logic |
| `hs_agent/workflows/tax_code_mapper.py` | Tax code mapping workflow | Batch processing improvements |
| `app.py` | FastAPI web application | Adding new API endpoints |
| `pyproject.toml` | Project dependencies and scripts | Managing dependencies |
| `.env.example` | Environment configuration template | Setting up API keys |

---

## 🔧 Technology Stack

### Core Technologies
- **Language:** Python 3.12+ - Modern async/await support and type hints
- **AI Framework:** Pydantic AI + LangGraph - Dual agent framework approach
- **LLM Provider:** Google Vertex AI (Gemini models) - Advanced language understanding
- **Web Framework:** FastAPI - High-performance async API framework

### Key Libraries
- **pydantic-ai-slim[google]** - Structured AI agent framework with Google integration
- **langgraph** - Workflow orchestration for multi-step AI processes
- **langchain-google-vertexai** - Google Vertex AI integration for LangChain
- **langfuse** - LLM observability and tracing platform
- **typer** - Modern CLI framework with rich formatting
- **pandas** - Data manipulation for HS codes and tax mappings

### Development Tools
- **uvicorn** - ASGI server for FastAPI applications
- **mkdocs-material** - Documentation site generation
- **rich** - Terminal formatting and progress indicators
- **tqdm** - Progress bars for batch processing

---

## 🌐 External Dependencies

### Required Services
- **Google Vertex AI** - Primary LLM provider for classification logic (critical)
- **Langfuse** - Observability and tracing for AI agent workflows (optional)

### Data Sources
- **HS Codes Database** - Harmonized System codes with descriptions (hs_codes.csv)
- **Product Examples** - Training examples for classification (hs6_examples_cleaned.csv)
- **Avalara Tax Codes** - Tax code to HS code mapping data (avalara_tax_codes.xlsx)

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=          # Google Vertex AI API key for Gemini models

# Optional
LANGFUSE_SECRET_KEY=     # Langfuse project secret key
LANGFUSE_PUBLIC_KEY=     # Langfuse project public key
LANGFUSE_HOST=           # Langfuse host URL (default: cloud)
```

---

## 🔄 Common Workflows

### Single Product Classification
1. **Input Processing** - Product description received via CLI or API
2. **Data Loading** - HS codes database loaded into memory with search indexing
3. **Hierarchical Classification** - Progressive classification through chapter → heading → subheading
4. **LLM Ranking** - AI-powered candidate evaluation and selection at each level
5. **Result Assembly** - Final 6-digit HS code with confidence scores and reasoning

**Code path:** `interfaces/cli` → `agents/langgraph` → `core/data_loader` → `Google Vertex AI`

### Tax Code Batch Mapping
1. **Excel Loading** - Avalara tax codes loaded from spreadsheet
2. **Batch Processing** - Concurrent classification of multiple tax codes
3. **Progress Tracking** - Real-time progress indicators and error handling
4. **Result Aggregation** - JSON and CSV output with metadata and statistics
5. **Quality Analysis** - Confidence scoring and high-confidence filtering

**Code path:** `workflows/tax_code_mapper` → `agents/langgraph` → `batch processing` → `file output`

---

## 📈 Performance & Scale

### Performance Considerations
- **Concurrent Processing** - Async/await for handling multiple classification requests
- **Data Caching** - In-memory HS codes database for fast lookups
- **Batch Optimization** - Configurable batch sizes for throughput vs. resource balance

### Monitoring
- **Langfuse Integration** - Automatic tracing of LLM calls and agent workflows
- **Processing Metrics** - Timing, confidence scores, and success rates
- **Error Tracking** - Comprehensive error handling with detailed logging

---

## 🚨 Things to Be Careful About

### 🔒 Security Considerations
- **API Key Management** - Google API keys stored in environment variables only
- **Rate Limiting** - Vertex AI API has usage limits and quotas
- **Data Privacy** - Product descriptions may contain sensitive business information

### ⚠️ Classification Limitations
- **Digital Products** - HS system designed for physical goods; digital products often classified under residual categories
- **Confidence Thresholds** - Lower confidence scores may indicate ambiguous or edge-case classifications
- **Context Dependency** - Same product description may have different HS codes based on intended use or market

### 🔧 Development Notes
- **Async Patterns** - All classification workflows use async/await; ensure proper async context
- **LLM Costs** - Vertex AI charges per token; batch processing can incur significant costs
- **Data Dependencies** - HS codes database must be current; outdated data affects classification accuracy

*Updated at: 2025-01-27 15:30:00 UTC*