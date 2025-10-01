"""TypedDict state models for LangGraph."""

from typing import TypedDict, Optional, List, Dict
from hs_agent.models import ClassificationResult, ClassificationPath


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


class MultiChoiceState(TypedDict):
    """State for multi-choice classification graph (returns 1-3 paths)."""
    product_description: str
    top_k: int

    # Chapter level (multi-selection)
    chapter_candidates: Optional[List[Dict]]
    selected_chapters: Optional[List[str]]  # 1-3 chapter codes
    chapter_confidences: Optional[List[float]]
    chapter_reasonings: Optional[List[str]]

    # Heading level (multi-selection per chapter)
    heading_candidates_by_chapter: Optional[Dict[str, List[Dict]]]  # chapter -> headings
    selected_headings_by_chapter: Optional[Dict[str, List[str]]]  # chapter -> 1-3 headings
    heading_confidences_by_chapter: Optional[Dict[str, List[float]]]
    heading_reasonings_by_chapter: Optional[Dict[str, List[str]]]

    # Subheading level (multi-selection per heading)
    subheading_candidates_by_heading: Optional[Dict[str, List[Dict]]]  # heading -> subheadings
    selected_subheadings_by_heading: Optional[Dict[str, List[str]]]  # heading -> 1-3 subheadings
    subheading_confidences_by_heading: Optional[Dict[str, List[float]]]
    subheading_reasonings_by_heading: Optional[Dict[str, List[str]]]

    # Final results (1-3 complete paths)
    paths: Optional[List[ClassificationPath]]
    overall_strategy: Optional[str]