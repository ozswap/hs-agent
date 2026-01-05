"""Base workflow class with shared utilities for HS code classification.

This module provides common functionality shared by both single-path and
multi-path classification workflows to reduce code duplication.
"""

from hs_agent.models import ClassificationLevel


class BaseWorkflow:
    """Base class for HS code classification workflows.

    Provides common utilities:
    - Level name mapping and formatting
    - Candidates list formatting
    - Template variable building with parent context
    - Confidence calculation with weighted averages
    """

    # Class-level constants
    LEVEL_NAMES = {"2": "CHAPTER", "4": "HEADING", "6": "SUBHEADING"}

    # Confidence weights for overall score calculation
    # Chapter decisions are foundational but less certain at high level
    # Subheading is the final decision and carries most weight
    CONFIDENCE_WEIGHTS = {
        "chapter": 0.3,
        "heading": 0.3,
        "subheading": 0.4,
    }

    @classmethod
    def calculate_overall_confidence(
        cls, chapter_conf: float, heading_conf: float, subheading_conf: float
    ) -> float:
        """Calculate weighted overall confidence score.

        Args:
            chapter_conf: Chapter selection confidence (0.0-1.0)
            heading_conf: Heading selection confidence (0.0-1.0)
            subheading_conf: Subheading selection confidence (0.0-1.0)

        Returns:
            Weighted average confidence score
        """
        weights = cls.CONFIDENCE_WEIGHTS
        return (
            chapter_conf * weights["chapter"]
            + heading_conf * weights["heading"]
            + subheading_conf * weights["subheading"]
        )

    def _get_level_name(self, level: ClassificationLevel) -> str:
        """Get human-readable level name.

        Args:
            level: Classification level enum

        Returns:
            Human-readable level name (e.g., "CHAPTER", "HEADING", "SUBHEADING")
        """
        return self.LEVEL_NAMES[level.value]

    def _format_candidates_list(self, codes_dict: dict) -> str:
        """Format HS codes dictionary into a human-readable candidates list.

        Args:
            codes_dict: Dictionary mapping code strings to HSCode objects

        Returns:
            Formatted string with one candidate per line: "code: description"
        """
        return "\n".join([f"{code}: {hs.description}" for code, hs in codes_dict.items()])

    def _add_parent_context(
        self, template_vars: dict, level: ClassificationLevel, parent_code: str = None
    ) -> None:
        """Add parent code context to template variables (mutates dict in place).

        Args:
            template_vars: Template variables dictionary (modified in place)
            level: Current classification level
            parent_code: Parent code (chapter for heading, heading for subheading)
        """
        if parent_code:
            if level == ClassificationLevel.HEADING:
                template_vars["parent_chapter"] = parent_code
            elif level == ClassificationLevel.SUBHEADING:
                template_vars["parent_heading"] = parent_code
