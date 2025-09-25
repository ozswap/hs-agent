"""Pydantic models for HS classification."""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ClassificationLevel(str, Enum):
    """HS classification levels."""
    CHAPTER = "2"  # 2-digit chapter level
    HEADING = "4"  # 4-digit heading level
    SUBHEADING = "6"  # 6-digit subheading level


class HSCandidate(BaseModel):
    """A candidate HS code with justification."""
    code: str = Field(description="The HS code")
    description: str = Field(description="Description of the HS code")
    relevance_score: float = Field(description="Relevance score from 0 to 1")
    justification: str = Field(description="Detailed justification for why this code is relevant")


class ClassificationResult(BaseModel):
    """Result of HS code classification at a specific level."""
    level: ClassificationLevel = Field(description="The classification level")
    product_description: str = Field(description="The product being classified")
    candidates: List[HSCandidate] = Field(description="Top candidate HS codes")
    selected_code: str = Field(description="The selected HS code")
    confidence: float = Field(description="Confidence in the selection from 0 to 1")
    reasoning: str = Field(description="Reasoning for the final selection")


class FinalClassification(BaseModel):
    """Complete hierarchical HS classification result."""
    product_description: str = Field(description="The product being classified")
    chapter_result: ClassificationResult = Field(description="2-digit chapter classification")
    heading_result: Optional[ClassificationResult] = Field(description="4-digit heading classification")
    subheading_result: Optional[ClassificationResult] = Field(description="6-digit subheading classification")
    final_hs_code: str = Field(description="The final 6-digit HS code")
    overall_confidence: float = Field(description="Overall confidence in the classification")


class RankingRequest(BaseModel):
    """Request for ranking HS codes."""
    product_description: str = Field(description="Description of the product to classify")
    candidates: List[dict] = Field(description="List of candidate HS codes with their descriptions")
    level: ClassificationLevel = Field(description="Classification level")


class RankingResponse(BaseModel):
    """Response from ranking agent."""
    ranked_candidates: List[HSCandidate] = Field(description="Candidates ranked by relevance")
    reasoning: str = Field(description="Overall reasoning for the ranking")