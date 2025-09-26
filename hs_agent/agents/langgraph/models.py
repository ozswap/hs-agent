"""LangGraph-specific models and state definitions for HS code classification."""

from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import operator

# Import shared models from core
from hs_agent.core.models.classification import (
    ClassificationLevel,
    HSCandidate,
    ClassificationResult,
    FinalClassification,
    RankingRequest,
    RankingResponse
)


# LangGraph-specific simplified result model for internal use
class SimpleClassificationResult(BaseModel):
    """Simplified result for LangGraph internal state management."""
    selected_code: str = Field(description="The selected HS code")
    confidence: float = Field(description="Confidence score from 0 to 1")
    reasoning: str = Field(description="Reasoning for the selection")


# Structured output models for LLM responses
class RankedCandidate(BaseModel):
    """A ranked HS code candidate."""
    code: str = Field(description="The HS code")
    description: str = Field(description="Description of the HS code")
    relevance_score: float = Field(description="Relevance score from 0.0 to 1.0")
    justification: str = Field(description="Detailed justification for the score")


class RankingOutput(BaseModel):
    """Output from HS code ranking."""
    ranked_candidates: List[RankedCandidate] = Field(description="Candidates ranked by relevance")
    reasoning: str = Field(description="Overall reasoning for the ranking")


class SelectionOutput(BaseModel):
    """Output from final HS code selection."""
    selected_code: str = Field(description="The selected HS code")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    reasoning: str = Field(description="Reasoning for the selection")


# Multi-choice selection models
class MultiSelectionOutput(BaseModel):
    """Output from multi-choice HS code selection."""
    selected_codes: List[str] = Field(description="List of selected HS codes", min_items=1)
    individual_confidences: List[float] = Field(description="Confidence scores for each selected code")
    overall_confidence: float = Field(description="Overall confidence for the selection set")
    reasoning: str = Field(description="Reasoning for selecting these codes")


class ClassificationPath(BaseModel):
    """A complete classification path from chapter to subheading."""
    chapter_code: str = Field(description="2-digit chapter code")
    heading_code: str = Field(description="4-digit heading code")
    subheading_code: str = Field(description="6-digit subheading code")
    path_confidence: float = Field(description="Overall confidence for this complete path")
    chapter_reasoning: str = Field(description="Reasoning for chapter selection")
    heading_reasoning: str = Field(description="Reasoning for heading selection")
    subheading_reasoning: str = Field(description="Reasoning for subheading selection")


# LangGraph State Definitions
class HSClassificationState(TypedDict):
    """Main state for HS classification workflow."""

    # Input
    product_description: str
    top_k: int

    # Progress tracking
    current_level: Optional[ClassificationLevel]

    # Chapter level (2-digit)
    chapter_candidates: Optional[List[Dict[str, Any]]]
    chapter_result: Optional[SimpleClassificationResult]

    # Heading level (4-digit)
    heading_candidates: Optional[List[Dict[str, Any]]]
    heading_result: Optional[SimpleClassificationResult]

    # Subheading level (6-digit)
    subheading_candidates: Optional[List[Dict[str, Any]]]
    subheading_result: Optional[SimpleClassificationResult]

    # Final results
    final_code: Optional[str]
    overall_confidence: Optional[float]
    processing_time: Optional[float]

    # Error handling
    error: Optional[str]

    # Metadata for tracing
    trace_context: Optional[Dict[str, Any]]


# Multi-choice state for looping workflows
class HSMultiChoiceState(TypedDict):
    """State for multi-choice HS classification workflow with looping."""

    # Input
    product_description: str
    initial_ranking_k: int  # High K for broad initial ranking (e.g., 20-50)
    max_selections_per_level: int  # Max codes to select at each level (1 to max_n range)
    min_confidence_threshold: float  # Minimum confidence to continue processing

    # Initial candidates from ranking
    chapter_candidates: Optional[List[Dict[str, Any]]]

    # Selected codes for processing (simplified lists)
    selected_chapters: List[str]  # Chapters selected for processing
    chapters_to_process: List[str]  # Chapters still to be processed

    # Simplified heading processing
    headings_to_process: List[str]  # All headings to process (flattened from all chapters)
    heading_parent_mapping: Dict[str, str]  # heading -> parent chapter mapping

    # Subheading candidates (not needed in simplified approach)
    subheading_candidates: Dict[str, List[Dict[str, Any]]]  # heading -> subheading candidates

    # Current processing context (removed - not needed in simplified approach)
    current_processing_chapter: Optional[str]  # Kept for compatibility
    current_processing_heading: Optional[str]  # Kept for compatibility

    # Accumulated results - all complete classification paths
    all_classification_paths: List[ClassificationPath]

    # Processing metadata
    processing_stats: Dict[str, int]  # Track number of paths processed, etc.
    overall_confidence: Optional[float]

    # Error handling
    error: Optional[str]

    # Tracing
    trace_context: Optional[Dict[str, Any]]


class LevelState(TypedDict):
    """State for individual level classification."""
    product_description: str
    level: ClassificationLevel
    parent_code: Optional[str]
    top_k: int
    candidates: List[Dict[str, Any]]
    ranked_candidates: Optional[List[HSCandidate]]
    result: Optional[SimpleClassificationResult]
    error: Optional[str]