"""TypedDict state models for LangGraph."""

from typing import TypedDict, Optional, List, Dict
from hs_agent.models import ClassificationResult


class ClassificationState(TypedDict):
    """State for hierarchical classification graph."""
    product_description: str
    top_k: int

    # Chapter level
    chapter_candidates: Optional[List[Dict]]
    chapter_result: Optional[ClassificationResult]

    # Heading level
    heading_candidates: Optional[List[Dict]]
    heading_result: Optional[ClassificationResult]

    # Subheading level
    subheading_candidates: Optional[List[Dict]]
    subheading_result: Optional[ClassificationResult]

    # Final results
    final_code: Optional[str]
    overall_confidence: Optional[float]