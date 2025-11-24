"""TypedDict state models for LangGraph."""

from typing import TypedDict, Optional, List, Dict
from hs_agent.models import ClassificationResult, ClassificationPath


class ClassificationState(TypedDict):
    """State for hierarchical classification graph."""
    product_description: str

    # Chapter level
    chapter_result: Optional[ClassificationResult]

    # Heading level
    heading_result: Optional[ClassificationResult]

    # Subheading level
    subheading_result: Optional[ClassificationResult]

    # Final results
    final_code: Optional[str]
    overall_confidence: Optional[float]


class MultiChoiceState(TypedDict):
    """State for multi-choice classification graph (returns 1-N paths)."""
    product_description: str
    max_selections: int  # Max number of codes to select at each level (1 to N)

    # Chapter level (multi-selection)
    selected_chapters: Optional[List[str]]  # 1-N chapter codes
    chapter_confidences: Optional[List[float]]
    chapter_reasonings: Optional[List[str]]

    # Heading level (multi-selection per chapter)
    selected_headings_by_chapter: Optional[Dict[str, List[str]]]  # chapter -> 1-N headings
    heading_confidences_by_chapter: Optional[Dict[str, List[float]]]
    heading_reasonings_by_chapter: Optional[Dict[str, List[str]]]

    # Subheading level (multi-selection per heading)
    selected_subheadings_by_heading: Optional[Dict[str, List[str]]]  # heading -> 1-N subheadings
    subheading_confidences_by_heading: Optional[Dict[str, List[float]]]
    subheading_reasonings_by_heading: Optional[Dict[str, List[str]]]

    # Final results (1-N complete paths)
    paths: Optional[List[ClassificationPath]]
    overall_strategy: Optional[str]

    # Final comparison results (single best code from all paths)
    final_selected_code: Optional[str]
    final_confidence: Optional[float]
    final_reasoning: Optional[str]
    comparison_summary: Optional[str]