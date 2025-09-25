"""Enhanced models for HS Agent with better organization and validation.

This module provides comprehensive Pydantic models for all data structures
used throughout the HS Agent system, with proper validation and documentation.
"""

from hs_agent.core.models.classification import (
    ClassificationLevel,
    HSCandidate,
    ClassificationResult,
    FinalClassification,
    RankingRequest,
    RankingResponse
)
from hs_agent.core.models.entities import HSCode, TaxCodeEntry, ProductExample
from hs_agent.core.models.requests import (
    ClassificationRequest,
    BatchClassificationRequest,
    TaxCodeMappingRequest
)
from hs_agent.core.models.responses import (
    ClassificationResponse,
    BatchClassificationResponse,
    ErrorResponse,
    HealthResponse
)

__all__ = [
    # Classification models
    "ClassificationLevel",
    "HSCandidate", 
    "ClassificationResult",
    "FinalClassification",
    "RankingRequest",
    "RankingResponse",
    
    # Entity models
    "HSCode",
    "TaxCodeEntry",
    "ProductExample",
    
    # Request models
    "ClassificationRequest",
    "BatchClassificationRequest", 
    "TaxCodeMappingRequest",
    
    # Response models
    "ClassificationResponse",
    "BatchClassificationResponse",
    "ErrorResponse",
    "HealthResponse"
]