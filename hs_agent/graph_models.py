"""TypedDict state models for LangGraph."""

from typing import TypedDict

from hs_agent.models import ClassificationPath, ClassificationResult


class ClassificationState(TypedDict):
    """State for hierarchical classification graph."""

    product_description: str

    # Chapter level
    chapter_result: ClassificationResult | None

    # Heading level
    heading_result: ClassificationResult | None

    # Subheading level
    subheading_result: ClassificationResult | None

    # Final results
    final_code: str | None
    overall_confidence: float | None


class MultiChoiceState(TypedDict):
    """State for multi-choice classification graph (returns 1-N paths)."""

    product_description: str
    max_selections: int  # Max number of codes to select at each level (1 to N)

    # Chapter level (multi-selection)
    selected_chapters: list[str] | None  # 1-N chapter codes
    chapter_confidences: list[float] | None
    chapter_reasonings: list[str] | None

    # Heading level (multi-selection per chapter)
    selected_headings_by_chapter: dict[str, list[str]] | None  # chapter -> 1-N headings
    heading_confidences_by_chapter: dict[str, list[float]] | None
    heading_reasonings_by_chapter: dict[str, list[str]] | None

    # Subheading level (multi-selection per heading)
    selected_subheadings_by_heading: dict[str, list[str]] | None  # heading -> 1-N subheadings
    subheading_confidences_by_heading: dict[str, list[float]] | None
    subheading_reasonings_by_heading: dict[str, list[str]] | None

    # Final results (1-N complete paths)
    paths: list[ClassificationPath] | None
    overall_strategy: str | None

    # Final comparison results (single best code from all paths)
    final_selected_code: str | None
    final_confidence: float | None
    final_reasoning: str | None
    comparison_summary: str | None
