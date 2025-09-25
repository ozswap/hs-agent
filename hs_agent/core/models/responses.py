"""Response models for HS Agent APIs and interfaces.

This module defines all response models used by the API endpoints
and CLI interfaces, with proper structure and documentation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from hs_agent.core.models.classification import ClassificationResult, HSCandidate


class ClassificationResponse(BaseModel):
    """Response for single product HS code classification.
    
    This model represents the complete response from a single
    product classification operation.
    """
    
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
    
    # Optional detailed information
    chapter_result: Optional[ClassificationResult] = Field(
        None,
        description="2-digit chapter classification details"
    )
    
    heading_result: Optional[ClassificationResult] = Field(
        None,
        description="4-digit heading classification details"
    )
    
    subheading_result: Optional[ClassificationResult] = Field(
        None,
        description="6-digit subheading classification details"
    )
    
    candidates: Optional[Dict[str, List[HSCandidate]]] = Field(
        None,
        description="Candidate codes at each level"
    )
    
    reasoning: Optional[str] = Field(
        None,
        description="Detailed reasoning for the classification"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata about the classification"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Classification timestamp"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "product_description": "Laptop computer with 16GB RAM and 512GB SSD",
                "final_hs_code": "847130",
                "final_description": "Portable digital automatic data processing machines, weighing not more than 10 kg",
                "overall_confidence": 0.92,
                "processing_time_ms": 2450.5,
                "agent_type": "langgraph",
                "reasoning": "This product is clearly a laptop computer, which falls under HS code 847130 for portable computers weighing less than 10kg.",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    }


class BatchClassificationResponse(BaseModel):
    """Response for batch HS code classification.
    
    This model represents the response from a batch
    classification operation.
    """
    
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
        description="Average processing time per product in milliseconds",
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
    
    agent_type: str = Field(
        ...,
        description="Agent type used for classification"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Batch processing timestamp"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_products": 3,
                "successful_classifications": 2,
                "failed_classifications": 1,
                "total_processing_time_ms": 7500.0,
                "average_processing_time_ms": 2500.0,
                "results": [],
                "errors": [
                    {
                        "product_index": 2,
                        "error": "Product description too vague for classification"
                    }
                ],
                "agent_type": "langgraph",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    }


class ErrorResponse(BaseModel):
    """Standardized error response.
    
    This model represents error responses from the API
    with consistent structure and helpful information.
    """
    
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
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "Product description is required and cannot be empty",
                "details": {
                    "field": "product_description",
                    "provided_value": "",
                    "expected": "non-empty string"
                },
                "request_id": "req_123456789",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    }


class HealthResponse(BaseModel):
    """System health check response.
    
    This model represents the response from a system
    health check operation.
    """
    
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
    services: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Status of external services"
    )
    
    system_info: Optional[Dict[str, Any]] = Field(
        None,
        description="System information"
    )
    
    performance_metrics: Optional[Dict[str, float]] = Field(
        None,
        description="Performance metrics"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "uptime_seconds": 3600.0,
                "timestamp": "2024-01-15T10:30:00Z",
                "services": {
                    "google_vertex_ai": {
                        "status": "healthy",
                        "response_time_ms": 150.0
                    },
                    "langfuse": {
                        "status": "healthy",
                        "response_time_ms": 75.0
                    }
                },
                "performance_metrics": {
                    "avg_classification_time_ms": 2500.0,
                    "classifications_per_minute": 24.0
                }
            }
        }
    }


class TaxCodeMappingResponse(BaseModel):
    """Response for tax code to HS code mapping.
    
    This model represents the response from mapping
    an Avalara tax code to an HS code.
    """
    
    avalara_code: str = Field(
        ...,
        description="Original Avalara tax code"
    )
    
    avalara_description: str = Field(
        ...,
        description="Avalara tax code description"
    )
    
    hs_code: str = Field(
        ...,
        description="Mapped HS code"
    )
    
    hs_description: str = Field(
        ...,
        description="HS code description"
    )
    
    confidence: float = Field(
        ...,
        description="Mapping confidence score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    reasoning: str = Field(
        ...,
        description="Reasoning for the mapping"
    )
    
    processing_time_ms: float = Field(
        ...,
        description="Processing time in milliseconds",
        ge=0.0
    )
    
    hierarchical_classification: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed hierarchical classification results"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Mapping timestamp"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "avalara_code": "PC040100",
                "avalara_description": "Personal computers and laptops",
                "hs_code": "847130",
                "hs_description": "Portable digital automatic data processing machines, weighing not more than 10 kg",
                "confidence": 0.95,
                "reasoning": "Tax code clearly describes personal computers and laptops, which directly maps to HS code 847130 for portable computers.",
                "processing_time_ms": 2100.0,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    }