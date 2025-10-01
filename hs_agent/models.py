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
    """LLM output for selecting multiple candidates."""
    selected_codes: List[str] = Field(min_items=1, max_items=3)
    individual_confidences: List[float] = Field(min_items=1, max_items=3)
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
    confidence: float
    reasoning: str


class ClassificationPath(BaseModel):
    """Complete classification path (chapter -> heading -> subheading)."""
    chapter_code: str
    heading_code: str
    subheading_code: str
    path_confidence: float
    chapter_reasoning: str
    heading_reasoning: str
    subheading_reasoning: str


# === API Request/Response Models ===

class ClassificationRequest(BaseModel):
    """API request for classification."""
    product_description: str
    top_k: int = 10


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
    """API response for multi-choice classification (1-3 paths)."""
    product_description: str
    paths: List[ClassificationPath] = Field(min_items=1, max_items=3)
    overall_strategy: str
    processing_time_ms: float