# Core Models Reference

## Overview

The HS Agent core models provide a comprehensive, type-safe foundation for all data structures used throughout the system. The models are organized into focused modules for better maintainability and clear separation of concerns.

## 📁 Model Organization

The models are organized into four main categories:

- **[Classification Models](#classification-models)**: Core classification data structures
- **[Entity Models](#entity-models)**: Domain entities representing business concepts
- **[Request Models](#request-models)**: API and CLI request structures
- **[Response Models](#response-models)**: API and CLI response structures

## 🎯 Classification Models

Located in `hs_agent.core.models.classification`

### ClassificationLevel

Enumeration of HS classification levels.

```python
class ClassificationLevel(str, Enum):
    """HS classification levels."""
    CHAPTER = "2"      # 2-digit chapter level
    HEADING = "4"      # 4-digit heading level
    SUBHEADING = "6"   # 6-digit subheading level
```

**Usage:**
```python
from hs_agent.core.models import ClassificationLevel

level = ClassificationLevel.CHAPTER
print(level.value)  # "2"
```

### HSCandidate

Represents a candidate HS code with relevance scoring.

```python
class HSCandidate(BaseModel):
    """A candidate HS code with justification."""
    
    code: str = Field(description="The HS code")
    description: str = Field(description="Description of the HS code")
    relevance_score: float = Field(
        description="Relevance score from 0 to 1",
        ge=0.0,
        le=1.0
    )
    justification: str = Field(
        description="Detailed justification for why this code is relevant"
    )
```

**Example:**
```python
candidate = HSCandidate(
    code="847130",
    description="Portable digital automatic data processing machines",
    relevance_score=0.95,
    justification="Perfect match for laptop computer description"
)
```

### ClassificationResult

Result of HS code classification at a specific level.

```python
class ClassificationResult(BaseModel):
    """Result of HS code classification at a specific level."""
    
    level: ClassificationLevel = Field(description="The classification level")
    product_description: str = Field(description="The product being classified")
    candidates: List[HSCandidate] = Field(description="Top candidate HS codes")
    selected_code: str = Field(description="The selected HS code")
    confidence: float = Field(
        description="Confidence in the selection from 0 to 1",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(description="Reasoning for the final selection")
```

### FinalClassification

Complete hierarchical HS classification result.

```python
class FinalClassification(BaseModel):
    """Complete hierarchical HS classification result."""
    
    product_description: str = Field(description="The product being classified")
    chapter_result: ClassificationResult = Field(description="2-digit chapter classification")
    heading_result: Optional[ClassificationResult] = Field(description="4-digit heading classification")
    subheading_result: Optional[ClassificationResult] = Field(description="6-digit subheading classification")
    final_hs_code: str = Field(description="The final 6-digit HS code")
    overall_confidence: float = Field(
        description="Overall confidence in the classification",
        ge=0.0,
        le=1.0
    )
```

## 🏢 Entity Models

Located in `hs_agent.core.models.entities`

### HSCode

Core entity representing an HS code with metadata.

```python
class HSCode(BaseModel):
    """Represents an HS code with its metadata."""
    
    code: str = Field(
        ...,
        description="The HS code (e.g., '84', '8471', '847130')",
        min_length=2,
        max_length=10
    )
    description: str = Field(
        ...,
        description="Human-readable description of the HS code",
        min_length=1
    )
    level: int = Field(
        ...,
        description="The digit level of the code (2, 4, or 6)",
        ge=2,
        le=6
    )
    parent: Optional[str] = Field(
        None,
        description="Parent code for hierarchical navigation"
    )
    section: Optional[str] = Field(
        None,
        description="Section identifier for grouping"
    )
    category: Optional[str] = Field(
        None,
        description="Category classification"
    )
```

**Properties:**
```python
hs_code = HSCode(code="847130", description="Portable computers", level=6, parent="8471")

# Convenience properties
print(hs_code.is_chapter)      # False
print(hs_code.is_heading)      # False
print(hs_code.is_subheading)   # True
print(hs_code.chapter_code)    # "84"
print(hs_code.heading_code)    # "8471"
```

**Validation:**
- Code must contain only digits
- Level must match code length
- Level must be 2, 4, or 6

### TaxCodeEntry

Represents an Avalara tax code for mapping to HS codes.

```python
class TaxCodeEntry(BaseModel):
    """Represents an Avalara tax code entry for mapping to HS codes."""
    
    avalara_code: str = Field(
        ...,
        description="Avalara tax code identifier",
        min_length=1
    )
    description: str = Field(
        ...,
        description="Description of the tax code",
        min_length=1
    )
    additional_info: Optional[str] = Field(
        None,
        description="Additional information about the tax code"
    )
    category: Optional[str] = Field(
        None,
        description="Tax code category"
    )
```

**Properties:**
```python
tax_code = TaxCodeEntry(
    avalara_code="PC040100",
    description="Personal computers and laptops",
    additional_info="Including accessories"
)

# Combined description
print(tax_code.combined_description)
# "Personal computers and laptops. Including accessories"
```

### ProductExample

Represents a product example for HS code classification.

```python
class ProductExample(BaseModel):
    """Represents a product example for HS code classification."""
    
    hs_code: str = Field(
        ...,
        description="Associated HS code",
        min_length=6,
        max_length=6
    )
    product_description: str = Field(
        ...,
        description="Product description",
        min_length=1
    )
    source: Optional[str] = Field(
        None,
        description="Source of the example"
    )
    confidence: Optional[float] = Field(
        None,
        description="Confidence in the HS code assignment",
        ge=0.0,
        le=1.0
    )
```

## 📥 Request Models

Located in `hs_agent.core.models.requests`

### ClassificationRequest

Request for single product HS code classification.

```python
class ClassificationRequest(BaseModel):
    """Request for single product HS code classification."""
    
    product_description: str = Field(
        ...,
        description="Description of the product to classify",
        min_length=3,
        max_length=1000
    )
    agent_type: Optional[AgentType] = Field(
        None,
        description="Preferred agent type for classification"
    )
    top_k: Optional[int] = Field(
        None,
        description="Number of candidates to consider at each level",
        ge=1,
        le=50
    )
    include_reasoning: bool = Field(
        True,
        description="Include detailed reasoning in the response"
    )
    include_candidates: bool = Field(
        False,
        description="Include candidate codes in the response"
    )
```

**Example:**
```python
request = ClassificationRequest(
    product_description="Laptop computer with 16GB RAM",
    agent_type=AgentType.LANGGRAPH,
    top_k=10,
    include_reasoning=True
)
```

### BatchClassificationRequest

Request for batch HS code classification.

```python
class BatchClassificationRequest(BaseModel):
    """Request for batch HS code classification."""
    
    products: List[str] = Field(
        ...,
        description="List of product descriptions to classify",
        min_items=1,
        max_items=100
    )
    agent_type: Optional[AgentType] = Field(
        None,
        description="Preferred agent type for classification"
    )
    max_concurrent: Optional[int] = Field(
        None,
        description="Maximum concurrent classifications",
        ge=1,
        le=20
    )
```

### TaxCodeMappingRequest

Request for mapping Avalara tax codes to HS codes.

```python
class TaxCodeMappingRequest(BaseModel):
    """Request for mapping Avalara tax codes to HS codes."""
    
    avalara_code: str = Field(
        ...,
        description="Avalara tax code identifier",
        min_length=1
    )
    description: str = Field(
        ...,
        description="Description of the tax code",
        min_length=1
    )
    confidence_threshold: Optional[float] = Field(
        None,
        description="Minimum confidence threshold for mapping",
        ge=0.0,
        le=1.0
    )
```

## 📤 Response Models

Located in `hs_agent.core.models.responses`

### ClassificationResponse

Response for single product HS code classification.

```python
class ClassificationResponse(BaseModel):
    """Response for single product HS code classification."""
    
    product_description: str = Field(
        ...,
        description="Original product description"
    )
    final_hs_code: str = Field(
        ...,
        description="Final 6-digit HS code classification"
    )
    final_description: str = Field(
        ...,
        description="Description of the final HS code"
    )
    overall_confidence: float = Field(
        ...,
        description="Overall confidence score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    processing_time_ms: float = Field(
        ...,
        description="Processing time in milliseconds",
        ge=0.0
    )
    agent_type: str = Field(
        ...,
        description="Agent type used for classification"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Classification timestamp"
    )
    
    # Optional detailed information
    chapter_result: Optional[ClassificationResult] = None
    heading_result: Optional[ClassificationResult] = None
    subheading_result: Optional[ClassificationResult] = None
    candidates: Optional[Dict[str, List[HSCandidate]]] = None
    reasoning: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

### BatchClassificationResponse

Response for batch HS code classification.

```python
class BatchClassificationResponse(BaseModel):
    """Response for batch HS code classification."""
    
    total_products: int = Field(
        ...,
        description="Total number of products processed",
        ge=0
    )
    successful_classifications: int = Field(
        ...,
        description="Number of successful classifications",
        ge=0
    )
    failed_classifications: int = Field(
        ...,
        description="Number of failed classifications",
        ge=0
    )
    total_processing_time_ms: float = Field(
        ...,
        description="Total processing time in milliseconds",
        ge=0.0
    )
    average_processing_time_ms: float = Field(
        ...,
        description="Average processing time per product",
        ge=0.0
    )
    results: List[ClassificationResponse] = Field(
        ...,
        description="Individual classification results"
    )
    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Errors encountered during processing"
    )
```

### ErrorResponse

Standardized error response structure.

```python
class ErrorResponse(BaseModel):
    """Standardized error response."""
    
    error: str = Field(
        ...,
        description="Error code or type"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    request_id: Optional[str] = Field(
        None,
        description="Request ID for tracking"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Error timestamp"
    )
```

### HealthResponse

System health check response.

```python
class HealthResponse(BaseModel):
    """System health check response."""
    
    status: str = Field(
        ...,
        description="Overall system status (healthy, degraded, unhealthy)"
    )
    version: str = Field(
        ...,
        description="Application version"
    )
    uptime_seconds: float = Field(
        ...,
        description="System uptime in seconds",
        ge=0.0
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Health check timestamp"
    )
    
    # Optional detailed information
    services: Optional[Dict[str, Dict[str, Any]]] = None
    system_info: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, float]] = None
```

## 🔧 Usage Examples

### Basic Classification Workflow

```python
from hs_agent.core.models import (
    ClassificationRequest,
    ClassificationResponse,
    HSCode,
    ClassificationLevel
)

# Create a classification request
request = ClassificationRequest(
    product_description="Laptop computer with 16GB RAM",
    agent_type=AgentType.LANGGRAPH,
    include_reasoning=True
)

# Process classification (pseudo-code)
response = await agent.classify(request)

# Access results
print(f"HS Code: {response.final_hs_code}")
print(f"Confidence: {response.overall_confidence:.2%}")
print(f"Processing Time: {response.processing_time_ms:.1f}ms")
```

### Working with HS Codes

```python
from hs_agent.core.models.entities import HSCode

# Create HS code entity
hs_code = HSCode(
    code="847130",
    description="Portable digital automatic data processing machines",
    level=6,
    parent="8471",
    section="XVI"
)

# Use convenience properties
if hs_code.is_subheading:
    print(f"Chapter: {hs_code.chapter_code}")
    print(f"Heading: {hs_code.heading_code}")
    print(f"Full code: {hs_code.code}")
```

### Error Handling

```python
from hs_agent.core.models.responses import ErrorResponse
from hs_agent.core.exceptions import ClassificationError

try:
    result = await agent.classify_hierarchical(description)
except ClassificationError as e:
    error_response = ErrorResponse(
        error=e.error_code,
        message=e.message,
        details=e.details
    )
    print(f"Classification failed: {error_response.message}")
```

## 🔍 Model Validation

All models include comprehensive validation:

### Automatic Validation

```python
from hs_agent.core.models.entities import HSCode
from pydantic import ValidationError

try:
    # This will raise ValidationError
    invalid_code = HSCode(
        code="abc",  # Must be digits only
        description="",  # Must not be empty
        level=8  # Must be 2, 4, or 6
    )
except ValidationError as e:
    print(f"Validation errors: {e.errors()}")
```

### Custom Validators

Many models include custom validators for business logic:

```python
# HSCode validates that level matches code length
hs_code = HSCode(
    code="84",
    description="Machinery",
    level=2  # Must match code length
)

# ClassificationRequest validates product description
request = ClassificationRequest(
    product_description="   Laptop computer   ",  # Whitespace is cleaned
    top_k=25  # Must be between 1 and 50
)
```

## 📚 Related Documentation

- [Configuration Guide](../../getting-started/configuration.md) - Model configuration options
- [CLI Usage](../../user-guide/cli-usage.md) - Using models with CLI
- [API Usage](../../user-guide/api-usage.md) - Using models with API
- [Refactored Structure](../../architecture/refactored-structure.md) - Architecture overview