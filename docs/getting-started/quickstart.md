# Quick Start

Get up and running with HS Agent in minutes.

## Prerequisites

- Python 3.12+
- Google Cloud account with Vertex AI enabled
- HS Agent installed (see [Installation](installation.md))

## Basic Classification

### Using Traditional Agents

```python
import asyncio
from hs_agent.agents.traditional.classifier import HSClassifier

async def classify_product():
    # Initialize the classifier
    classifier = HSClassifier(
        data_dir="data",
        model_name="gemini-2.5-flash"
    )

    # Classify a product
    result = await classifier.classify(
        product_description="Pure-bred Arabian mare for breeding",
        top_k=3,
        verbose=True
    )

    print(f"HS Code: {result['final_code']}")
    print(f"Confidence: {result['overall_confidence']:.2f}")

# Run the classification
asyncio.run(classify_product())
```

### Using LangGraph Agents

```python
import asyncio
from hs_agent.agents.langgraph.classifier import create_langgraph_classifier

async def classify_with_langgraph():
    # Create classifier
    classifier = create_langgraph_classifier("data")

    # Classify product
    result = await classifier.classify("Laptop computer Intel processor")

    print(f"Final Classification: {result.final_code}")
    print(f"Confidence: {result.overall_confidence:.2f}")

asyncio.run(classify_with_langgraph())
```

## Using the REST API

### Start the Server

```bash
# Traditional API
uv run python -m hs_agent.interfaces.api.traditional

# LangGraph API
uv run python -m hs_agent.interfaces.api.langgraph
```

### Make API Calls

```python
import requests

# Classification request
response = requests.post(
    "http://localhost:8000/classify",
    json={
        "product_description": "Fresh apples from Washington state",
        "top_k": 5
    }
)

result = response.json()
print(f"HS Code: {result['final_code']}")
```

### Using curl

```bash
curl -X POST "http://localhost:8000/classify" \
     -H "Content-Type: application/json" \
     -d '{"product_description": "Cotton t-shirt for men", "top_k": 3}'
```

## Using the CLI

### Interactive Mode

```bash
# Traditional CLI
uv run python -m hs_agent.interfaces.cli.traditional

# LangGraph CLI
uv run python -m hs_agent.interfaces.cli.langgraph
```

### Batch Processing

```bash
# Process CSV file
uv run python -m hs_agent.interfaces.cli.traditional \
    --batch input.csv \
    --output results.csv
```

## Example Outputs

### Successful Classification

```json
{
  "final_code": "010111",
  "final_description": "Horses; live, pure-bred breeding animals",
  "overall_confidence": 0.92,
  "reasoning": "The product is specifically described as a pure-bred Arabian mare for breeding, which directly matches HS code 010111 for pure-bred breeding horses.",
  "classification_path": {
    "2_digit": {"code": "01", "confidence": 0.98},
    "4_digit": {"code": "0101", "confidence": 0.95},
    "6_digit": {"code": "010111", "confidence": 0.92}
  }
}
```

### Error Handling

```json
{
  "error": "Classification failed",
  "message": "Unable to determine appropriate HS code",
  "suggestions": [
    "Provide more specific product details",
    "Check product description for accuracy"
  ]
}
```

## Next Steps

- Explore the [User Guide](../user-guide/overview.md) for detailed usage
- Review [API Reference](../api-reference/core/data-loader.md) for advanced features
- Check out [Examples](../examples/basic-classification.md) for more use cases