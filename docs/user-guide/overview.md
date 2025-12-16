# System Overview

HS Agent is an AI-powered classification system that maps product descriptions to Harmonized System (HS) codes.

## What are HS Codes?

The Harmonized Commodity Description and Coding System (HS) is an internationally standardized system for classifying traded products:

- **2-digit codes**: Chapters (e.g., 84 = Machinery)
- **4-digit codes**: Headings (e.g., 8471 = Data processing machines)
- **6-digit codes**: Subheadings (e.g., 847130 = Portable computers)

## How It Works

### 1. Data Loading

- Loads HS codes from CSV files
- Builds hierarchical relationships (chapters → headings → subheadings)
- Indexes product examples for similarity search

### 2. Classification Process

The system uses a hierarchical approach:

1. **Chapter Selection** (2-digit)
   - Finds candidate chapters using text similarity
   - AI ranks candidates and selects best match

2. **Heading Selection** (4-digit)
   - Within selected chapter, finds candidate headings
   - AI evaluates and selects best match

3. **Subheading Selection** (6-digit)
   - Within selected heading, finds candidate subheadings
   - AI provides final classification with reasoning

### 3. Confidence Scoring

Each level returns:
- Selected code
- Description
- Confidence score (0-100%)
- Reasoning for selection

## Classification Workflows

### Standard (Fast)

Single-path classification:
- Selects one best option at each level
- Fast and efficient
- Best for clear, unambiguous products

### Wide Net (High Performance)

Multi-path exploration with chapter notes:
- Explores multiple paths at each level
- Applies chapter notes and precedence rules
- Compares all paths to select best
- Slower but more accurate for complex products

### Multi-Choice

Adaptive path exploration:
- Returns 1-N possible classifications
- Shows alternative interpretations
- Useful for ambiguous products

## Integration Options

### Command Line Interface (CLI)

```bash
uv run hs-agent classify "laptop computer"
```

### REST API

```bash
curl -X POST "http://localhost:8000/api/classify" \
  -H "Content-Type: application/json" \
  -d '{"product_description": "laptop computer"}'
```

### Web UI

Interactive interface at http://localhost:8000/classify with:
- Visual classification flow
- Confidence indicators
- Path exploration tree
- Expandable reasoning

### Python SDK

```python
from hs_agent.agent import HSAgent
from hs_agent.data_loader import HSDataLoader

loader = HSDataLoader()
loader.load_all_data()

agent = HSAgent(loader)
result = await agent.classify("laptop computer")
```

## Performance

### Accuracy
- Chapter Level: >95%
- Heading Level: >90%
- Subheading Level: >85%

### Latency
- Single Classification: 3-10 seconds
- Data Loading: 2-5 seconds (cached)

### Throughput
- Standard Mode: ~10-20 classifications/minute
- Wide Net Mode: ~5-15 classifications/minute

## Observability

- Logfire tracing (OpenTelemetry-based) for request + agent run observability
- Structured logging with rich formatting
- Health check endpoints
- Performance monitoring
