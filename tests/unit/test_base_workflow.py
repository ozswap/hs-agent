"""Tests for BaseWorkflow class.

Tests cover:
- Confidence calculation with weighted averages
- Level name mapping
- Candidates list formatting
- Parent context addition to template variables
"""

import pytest

from hs_agent.models import ClassificationLevel
from hs_agent.workflows.base_workflow import BaseWorkflow


class TestBaseWorkflowConstants:
    """Tests for BaseWorkflow class constants."""

    def test_level_names_mapping(self):
        """Test LEVEL_NAMES constant has correct mappings."""
        assert BaseWorkflow.LEVEL_NAMES == {
            "2": "CHAPTER",
            "4": "HEADING",
            "6": "SUBHEADING",
        }

    def test_confidence_weights_values(self):
        """Test CONFIDENCE_WEIGHTS has correct values."""
        weights = BaseWorkflow.CONFIDENCE_WEIGHTS
        assert weights["chapter"] == 0.3
        assert weights["heading"] == 0.3
        assert weights["subheading"] == 0.4

    def test_confidence_weights_sum_to_one(self):
        """Test confidence weights sum to 1.0."""
        weights = BaseWorkflow.CONFIDENCE_WEIGHTS
        total = weights["chapter"] + weights["heading"] + weights["subheading"]
        assert total == pytest.approx(1.0)


class TestCalculateOverallConfidence:
    """Tests for calculate_overall_confidence class method."""

    def test_equal_confidence_values(self):
        """Test confidence calculation with equal input values."""
        result = BaseWorkflow.calculate_overall_confidence(0.5, 0.5, 0.5)
        # 0.5 * 0.3 + 0.5 * 0.3 + 0.5 * 0.4 = 0.15 + 0.15 + 0.2 = 0.5
        assert result == pytest.approx(0.5)

    def test_weighted_calculation(self):
        """Test weights are applied correctly (0.3, 0.3, 0.4)."""
        # chapter=1.0, heading=0.0, subheading=0.0
        result = BaseWorkflow.calculate_overall_confidence(1.0, 0.0, 0.0)
        assert result == pytest.approx(0.3)  # 1.0 * 0.3 + 0 + 0

        # chapter=0.0, heading=1.0, subheading=0.0
        result = BaseWorkflow.calculate_overall_confidence(0.0, 1.0, 0.0)
        assert result == pytest.approx(0.3)  # 0 + 1.0 * 0.3 + 0

        # chapter=0.0, heading=0.0, subheading=1.0
        result = BaseWorkflow.calculate_overall_confidence(0.0, 0.0, 1.0)
        assert result == pytest.approx(0.4)  # 0 + 0 + 1.0 * 0.4

    def test_all_perfect_confidence(self):
        """Test with all 1.0 confidence values."""
        result = BaseWorkflow.calculate_overall_confidence(1.0, 1.0, 1.0)
        assert result == pytest.approx(1.0)

    def test_all_zero_confidence(self):
        """Test with all 0.0 confidence values."""
        result = BaseWorkflow.calculate_overall_confidence(0.0, 0.0, 0.0)
        assert result == pytest.approx(0.0)

    def test_realistic_values(self):
        """Test with realistic confidence values."""
        # Common scenario: chapter=0.9, heading=0.85, subheading=0.95
        result = BaseWorkflow.calculate_overall_confidence(0.9, 0.85, 0.95)
        # 0.9 * 0.3 + 0.85 * 0.3 + 0.95 * 0.4 = 0.27 + 0.255 + 0.38 = 0.905
        assert result == pytest.approx(0.905)

    def test_boundary_values(self):
        """Test with boundary values 0.0 and 1.0."""
        result = BaseWorkflow.calculate_overall_confidence(0.0, 1.0, 0.5)
        # 0 * 0.3 + 1.0 * 0.3 + 0.5 * 0.4 = 0 + 0.3 + 0.2 = 0.5
        assert result == pytest.approx(0.5)

    def test_subheading_weighted_highest(self):
        """Test that subheading has highest weight (0.4)."""
        # Same delta, but in different positions
        base = 0.5

        # Increase chapter by 0.1
        result_chapter_up = BaseWorkflow.calculate_overall_confidence(
            base + 0.1, base, base
        )
        # Increase subheading by 0.1
        result_subheading_up = BaseWorkflow.calculate_overall_confidence(
            base, base, base + 0.1
        )

        # Subheading increase should have larger effect
        assert result_subheading_up > result_chapter_up


class TestGetLevelName:
    """Tests for _get_level_name method."""

    def test_chapter_level(self):
        """Test level name for CHAPTER."""
        workflow = BaseWorkflow()
        result = workflow._get_level_name(ClassificationLevel.CHAPTER)
        assert result == "CHAPTER"

    def test_heading_level(self):
        """Test level name for HEADING."""
        workflow = BaseWorkflow()
        result = workflow._get_level_name(ClassificationLevel.HEADING)
        assert result == "HEADING"

    def test_subheading_level(self):
        """Test level name for SUBHEADING."""
        workflow = BaseWorkflow()
        result = workflow._get_level_name(ClassificationLevel.SUBHEADING)
        assert result == "SUBHEADING"


class TestFormatCandidatesList:
    """Tests for _format_candidates_list method."""

    def test_format_single_code(self, mock_data_loader):
        """Test formatting a single code."""
        workflow = BaseWorkflow()
        codes_dict = {"84": mock_data_loader.codes_2digit["84"]}

        result = workflow._format_candidates_list(codes_dict)

        assert result == "84: Machinery"

    def test_format_multiple_codes(self, mock_data_loader):
        """Test formatting multiple codes."""
        workflow = BaseWorkflow()

        result = workflow._format_candidates_list(mock_data_loader.codes_2digit)

        # Should have both codes, one per line
        assert "84: Machinery" in result
        assert "62: Articles of apparel" in result
        assert "\n" in result  # Multi-line

    def test_format_empty_dict(self):
        """Test formatting empty codes dictionary."""
        workflow = BaseWorkflow()

        result = workflow._format_candidates_list({})

        assert result == ""

    def test_preserves_code_order(self):
        """Test that order matches dictionary iteration."""
        workflow = BaseWorkflow()

        # Use simple mock objects
        class MockCode:
            def __init__(self, desc):
                self.description = desc

        codes = {
            "01": MockCode("First"),
            "02": MockCode("Second"),
            "03": MockCode("Third"),
        }

        result = workflow._format_candidates_list(codes)
        lines = result.split("\n")

        assert lines[0] == "01: First"
        assert lines[1] == "02: Second"
        assert lines[2] == "03: Third"


class TestAddParentContext:
    """Tests for _add_parent_context method."""

    def test_chapter_level_no_context(self):
        """Test no parent context added for chapter level."""
        workflow = BaseWorkflow()
        template_vars = {"product_description": "test"}

        workflow._add_parent_context(
            template_vars, ClassificationLevel.CHAPTER, parent_code="XX"
        )

        # Chapter level shouldn't add parent context
        assert "parent_chapter" not in template_vars
        assert "parent_heading" not in template_vars

    def test_heading_level_adds_chapter(self):
        """Test parent_chapter added for heading level."""
        workflow = BaseWorkflow()
        template_vars = {"product_description": "test"}

        workflow._add_parent_context(
            template_vars, ClassificationLevel.HEADING, parent_code="84"
        )

        assert template_vars["parent_chapter"] == "84"
        assert "parent_heading" not in template_vars

    def test_subheading_level_adds_heading(self):
        """Test parent_heading added for subheading level."""
        workflow = BaseWorkflow()
        template_vars = {"product_description": "test"}

        workflow._add_parent_context(
            template_vars, ClassificationLevel.SUBHEADING, parent_code="8471"
        )

        assert template_vars["parent_heading"] == "8471"
        assert "parent_chapter" not in template_vars

    def test_no_parent_code_no_context(self):
        """Test no context added when parent_code is None."""
        workflow = BaseWorkflow()
        template_vars = {"product_description": "test"}

        workflow._add_parent_context(
            template_vars, ClassificationLevel.HEADING, parent_code=None
        )

        assert "parent_chapter" not in template_vars
        assert "parent_heading" not in template_vars

    def test_mutates_dict_in_place(self):
        """Test that method mutates the dict in place (no return value)."""
        workflow = BaseWorkflow()
        template_vars = {"existing": "value"}

        result = workflow._add_parent_context(
            template_vars, ClassificationLevel.HEADING, parent_code="84"
        )

        # Method returns None (mutates in place)
        assert result is None
        # Original dict was modified
        assert template_vars["parent_chapter"] == "84"
        assert template_vars["existing"] == "value"

    def test_preserves_existing_vars(self):
        """Test that existing template variables are preserved."""
        workflow = BaseWorkflow()
        template_vars = {
            "product_description": "laptop",
            "candidates_list": "84: Machinery",
            "level": "HEADING",
        }

        workflow._add_parent_context(
            template_vars, ClassificationLevel.HEADING, parent_code="84"
        )

        # All original vars preserved
        assert template_vars["product_description"] == "laptop"
        assert template_vars["candidates_list"] == "84: Machinery"
        assert template_vars["level"] == "HEADING"
        # New var added
        assert template_vars["parent_chapter"] == "84"
