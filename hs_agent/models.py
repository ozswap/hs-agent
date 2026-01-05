"""Core models for HS Agent."""

from enum import Enum

from pydantic import BaseModel, Field


class ClassificationLevel(str, Enum):
    """HS code classification levels."""

    CHAPTER = "2"  # 2-digit
    HEADING = "4"  # 4-digit
    SUBHEADING = "6"  # 6-digit


# === Special Code Constants ===

NO_HS_CODE = "000000"
NO_HS_CODE_DESCRIPTION = "No HS Code - Invalid or unclassifiable description"


def is_no_hs_code(code: str) -> bool:
    """Check if the given code is the special 'no HS code' marker.

    Args:
        code: The HS code to check

    Returns:
        True if the code is the special "000000" marker, False otherwise
    """
    return code == NO_HS_CODE


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
    reasoning: str | None = None


# === LLM Output Models ===
# Note: LLM output models are now defined in config files as the single source of truth.
# Dynamic models are created at runtime from config schemas.


# === Classification Results ===


class ClassificationResult(BaseModel):
    """Result at one classification level."""

    level: ClassificationLevel
    selected_code: str
    description: str
    confidence: float
    reasoning: str


def create_no_hs_code_result(
    level: ClassificationLevel, confidence: float, reasoning: str
) -> ClassificationResult:
    """Create a ClassificationResult for the special 'no HS code' case.

    Args:
        level: The classification level
        confidence: Confidence score for this result
        reasoning: Explanation for why no HS code could be assigned

    Returns:
        ClassificationResult with the special "000000" code
    """
    return ClassificationResult(
        level=level,
        selected_code=NO_HS_CODE,
        description=NO_HS_CODE_DESCRIPTION,
        confidence=confidence,
        reasoning=reasoning,
    )


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
    high_performance: bool = Field(
        default=False,
        description="Use wide net approach: explores multiple paths and applies chapter notes for highest accuracy (slower but more accurate)",
    )
    max_selections: int = Field(
        default=3,
        description="Only used with high_performance=True. Number of paths to explore at each level.",
        ge=1,
        le=10,
    )


class MultiChoiceClassificationRequest(BaseModel):
    """API request for multi-choice (one-to-many) classification.

    Returns 1-N HS code paths for ambiguous products.
    """

    product_description: str
    max_selections: int = Field(
        default=3,
        description="Maximum codes to SELECT at each level (e.g., select best 1-3 codes)",
        ge=1,
        le=10,
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
    # High performance mode results (only present when high_performance=True)
    paths_explored: list[ClassificationPath] | None = Field(
        None, description="All paths explored in high performance mode"
    )
    comparison_reasoning: str | None = Field(
        None, description="Reasoning for final selection using chapter notes"
    )
    comparison_summary: str | None = Field(None, description="Summary of path comparison")


class MultiChoiceClassificationResponse(BaseModel):
    """API response for multi-choice classification (1-N paths)."""

    product_description: str
    paths: list[ClassificationPath] = Field(min_length=1, description="1 to N classification paths")
    overall_strategy: str
    processing_time_ms: float
    # Final comparison results (optional - only if comparison is performed)
    final_selected_code: str | None = Field(
        None, description="Single best HS code selected from all paths"
    )
    final_confidence: float | None = Field(None, description="Confidence in the final selection")
    final_reasoning: str | None = Field(None, description="Reasoning for the final selection")
    comparison_summary: str | None = Field(None, description="Summary of the comparison process")
