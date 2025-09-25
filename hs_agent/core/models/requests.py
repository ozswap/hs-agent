"""Request models for HS Agent APIs and interfaces.

This module defines all request models used by the API endpoints
and CLI interfaces, with proper validation and documentation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from hs_agent.config import AgentType


class ClassificationRequest(BaseModel):
    """Request for single product HS code classification.
    
    This model represents a request to classify a single product
    description into an appropriate HS code.
    """
    
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
    
    @field_validator("product_description")
    @classmethod
    def validate_product_description(cls, v):
        """Validate product description content."""
        # Remove excessive whitespace
        v = " ".join(v.split())
        
        # Check for meaningful content
        if len(v.strip()) < 3:
            raise ValueError("Product description must be at least 3 characters")
        
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "product_description": "Laptop computer with 16GB RAM and 512GB SSD",
                "agent_type": "langgraph",
                "top_k": 10,
                "include_reasoning": True,
                "include_candidates": False
            }
        }
    }


class BatchClassificationRequest(BaseModel):
    """Request for batch HS code classification.
    
    This model represents a request to classify multiple products
    in a single batch operation.
    """
    
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
    
    top_k: Optional[int] = Field(
        None,
        description="Number of candidates to consider at each level",
        ge=1,
        le=50
    )
    
    include_reasoning: bool = Field(
        False,
        description="Include detailed reasoning in responses"
    )
    
    include_candidates: bool = Field(
        False,
        description="Include candidate codes in responses"
    )
    
    max_concurrent: Optional[int] = Field(
        None,
        description="Maximum concurrent classifications",
        ge=1,
        le=20
    )
    
    @field_validator("products")
    @classmethod
    def validate_products(cls, v):
        """Validate product descriptions."""
        validated_products = []
        for i, product in enumerate(v):
            # Clean up whitespace
            product = " ".join(product.split())
            
            if len(product.strip()) < 3:
                raise ValueError(f"Product {i+1} description too short")
            
            validated_products.append(product)
        
        return validated_products
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "products": [
                    "Laptop computer with 16GB RAM",
                    "Cotton t-shirt, size medium",
                    "Fresh apples from Washington state"
                ],
                "agent_type": "langgraph",
                "top_k": 10,
                "include_reasoning": False,
                "max_concurrent": 5
            }
        }
    }


class TaxCodeMappingRequest(BaseModel):
    """Request for mapping Avalara tax codes to HS codes.
    
    This model represents a request to map tax codes to
    appropriate HS codes for trade classification.
    """
    
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
    
    agent_type: Optional[AgentType] = Field(
        None,
        description="Preferred agent type for classification"
    )
    
    confidence_threshold: Optional[float] = Field(
        None,
        description="Minimum confidence threshold for mapping",
        ge=0.0,
        le=1.0
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "avalara_code": "PC040100",
                "description": "Personal computers and laptops",
                "additional_info": "Including accessories and peripherals",
                "agent_type": "langgraph",
                "confidence_threshold": 0.7
            }
        }
    }


class HealthCheckRequest(BaseModel):
    """Request for system health check.
    
    This model represents a request to check the health
    and status of the HS Agent system.
    """
    
    include_details: bool = Field(
        False,
        description="Include detailed system information"
    )
    
    check_external_services: bool = Field(
        False,
        description="Check external service connectivity"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "include_details": True,
                "check_external_services": True
            }
        }
    }