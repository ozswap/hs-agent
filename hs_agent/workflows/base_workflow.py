"""Base workflow class with shared utilities for HS code classification.

This module provides common functionality shared by both single-path and
multi-path classification workflows to reduce code duplication.
"""

from typing import Dict
from hs_agent.models import ClassificationLevel


class BaseWorkflow:
    """Base class for HS code classification workflows.

    Provides common utilities:
    - Level name mapping and formatting
    - Candidates list formatting
    - Template variable building with parent context
    """

    # Class-level constants
    LEVEL_NAMES = {"2": "CHAPTER", "4": "HEADING", "6": "SUBHEADING"}

    def _get_level_name(self, level: ClassificationLevel) -> str:
        """Get human-readable level name.

        Args:
            level: Classification level enum

        Returns:
            Human-readable level name (e.g., "CHAPTER", "HEADING", "SUBHEADING")
        """
        return self.LEVEL_NAMES[level.value]

    def _format_candidates_list(self, codes_dict: Dict) -> str:
        """Format HS codes dictionary into a human-readable candidates list.

        Args:
            codes_dict: Dictionary mapping code strings to HSCode objects

        Returns:
            Formatted string with one candidate per line: "code: description"
        """
        return "\n".join([
            f"{code}: {hs.description}"
            for code, hs in codes_dict.items()
        ])

    def _add_parent_context(
        self,
        template_vars: Dict,
        level: ClassificationLevel,
        parent_code: str = None
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
