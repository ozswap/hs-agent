"""Core models for HS Agent."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
from enum import Enum


class ClassificationLevel(str, Enum):
    """HS code classification levels."""
    CHAPTER = "2"  # 2-digit
    HEADING = "4"  # 4-digit
    SUBHEADING = "6"  # 6-digit


# === Core HS Code Models ===

class HSCode(BaseModel):
    """HS code with description."""
    code: str
    description: str


class HSCandidate(BaseModel):
    """HS code candidate with confidence score."""
    code: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None


# === LLM Output Models ===

class RankedCandidate(BaseModel):
    """Ranked HS code candidate from LLM."""
    code: str
    description: str
    relevance_score: float
    justification: str


class RankingOutput(BaseModel):
    """LLM output for ranking candidates."""
    ranked_candidates: List[RankedCandidate]
    reasoning: str


class SelectionOutput(BaseModel):
    """LLM output for selecting best candidate."""
    selected_code: str
    confidence: float
    reasoning: str


class MultiSelectionOutput(BaseModel):
    """LLM output for selecting multiple candidates (1 to N codes)."""
    selected_codes: List[str] = Field(min_length=1, description="1 to N selected codes")
    individual_confidences: List[float] = Field(min_length=1, description="Confidence for each selected code")
    overall_confidence: float
    reasoning: str

    @model_validator(mode='after')
    def validate_confidences_match_codes(self):
        """Ensure confidences match codes length."""
        if len(self.individual_confidences) != len(self.selected_codes):
            # Pad with overall confidence if too short
            if len(self.individual_confidences) < len(self.selected_codes):
                self.individual_confidences = self.individual_confidences + [self.overall_confidence] * (
                    len(self.selected_codes) - len(self.individual_confidences)
                )
            else:
                # Truncate if too long
                self.individual_confidences = self.individual_confidences[:len(self.selected_codes)]
        return self


# === Classification Results ===

class ClassificationResult(BaseModel):
    """Result at one classification level."""
    level: ClassificationLevel
    selected_code: str
    description: str
    confidence: float
    reasoning: str


class ClassificationPath(BaseModel):
    """Complete classification path (chapter -> heading -> subheading)."""
    chapter_code: str
    chapter_description: str
    heading_code: str
    heading_description: str
    subheading_code: str
    subheading_description: str
    path_confidence: float
    chapter_reasoning: str
    heading_reasoning: str
    subheading_reasoning: str


# === API Request/Response Models ===

class ClassificationRequest(BaseModel):
    """API request for single (one-to-one) classification.

    Returns a single HS code path.
    """
    product_description: str
    top_k: int = Field(
        default=10,
        description="Number of top candidates to consider during ranking phase (performance optimization)",
        ge=1,
        le=50
    )


class MultiChoiceClassificationRequest(BaseModel):
    """API request for multi-choice (one-to-many) classification.

    Returns 1-N HS code paths for ambiguous products.
    """
    product_description: str
    top_k: int = Field(
        default=10,
        description="Number of top candidates to RANK at each level (e.g., rank top 10 from all chapters)",
        ge=1,
        le=50
    )
    max_selections: int = Field(
        default=3,
        description="Maximum codes to SELECT from ranked candidates at each level (e.g., select best 1-3 from top 10)",
        ge=1,
        le=10
    )


class ClassificationResponse(BaseModel):
    """API response for classification."""
    product_description: str
    final_code: str
    overall_confidence: float
    chapter: ClassificationResult
    heading: ClassificationResult
    subheading: ClassificationResult
    processing_time_ms: float


class MultiChoiceClassificationResponse(BaseModel):
    """API response for multi-choice classification (1-N paths)."""
    product_description: str
    paths: List[ClassificationPath] = Field(min_length=1, description="1 to N classification paths")
    overall_strategy: str
    processing_time_ms: float