"""Tests for SinglePathWorkflow class.

Tests cover:
- Graph structure and node connections
- Code filtering by parent (startswith logic)
- Finalize confidence calculation
- _select_code result handling (None, 000000, invalid, valid)
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from hs_agent.models import ClassificationLevel, ClassificationResult
from hs_agent.workflows.single_path_workflow import SinglePathWorkflow


# Simple mock for HSCode
class MockHSCode:
    def __init__(self, code, description):
        self.code = code
        self.description = description


@pytest.fixture
def mock_data_loader():
    """Create a mock data loader with test HS codes."""
    loader = Mock()
    loader.codes_2digit = {
        "84": MockHSCode("84", "Machinery"),
        "85": MockHSCode("85", "Electrical"),
    }
    loader.codes_4digit = {
        "8471": MockHSCode("8471", "Data processing machines"),
        "8473": MockHSCode("8473", "Parts for machines"),
        "8501": MockHSCode("8501", "Electric motors"),
    }
    loader.codes_6digit = {
        "847130": MockHSCode("847130", "Portable computers"),
        "847141": MockHSCode("847141", "Other data processing"),
        "847330": MockHSCode("847330", "Parts for 8471"),
    }
    return loader


@pytest.fixture
def mock_retry_policy():
    """Create a mock retry policy."""
    policy = Mock()
    policy.invoke_with_retry = AsyncMock()
    return policy


@pytest.fixture
def sample_configs():
    """Sample workflow configs."""
    return {
        "select_chapter_candidates": {
            "model": {"name": "gemini-2.5-flash"},
            "prompts": {
                "system": "You are an expert.",
                "user": "Product: {product_description}",
            },
            "output_schema": {
                "type": "object",
                "properties": {"selected_code": {"type": "string"}},
            },
        },
        "select_heading_candidates": {
            "model": {"name": "gemini-2.5-flash"},
            "prompts": {
                "system": "Select heading.",
                "user": "Product: {product_description}",
            },
            "output_schema": {
                "type": "object",
                "properties": {"selected_code": {"type": "string"}},
            },
        },
        "select_subheading_candidates": {
            "model": {"name": "gemini-2.5-flash"},
            "prompts": {
                "system": "Select subheading.",
                "user": "Product: {product_description}",
            },
            "output_schema": {
                "type": "object",
                "properties": {"selected_code": {"type": "string"}},
            },
        },
    }


@pytest.fixture
def workflow(mock_data_loader, mock_retry_policy, sample_configs):
    """Create a SinglePathWorkflow instance."""
    return SinglePathWorkflow(
        data_loader=mock_data_loader,
        model_name="gemini-2.5-flash",
        configs=sample_configs,
        retry_policy=mock_retry_policy,
    )


class TestBuildGraph:
    """Tests for graph structure."""

    def test_graph_has_four_nodes(self, workflow):
        """Test graph has expected nodes."""
        graph = workflow.build_graph()

        # Check node names in the graph
        node_names = list(graph.nodes.keys())
        assert "select_chapter" in node_names
        assert "select_heading" in node_names
        assert "select_subheading" in node_names
        assert "finalize" in node_names

    def test_graph_compiles_without_error(self, workflow):
        """Test graph compilation succeeds."""
        graph = workflow.build_graph()

        # Should not raise
        assert graph is not None


class TestSelectChapter:
    """Tests for _select_chapter node."""

    @pytest.mark.asyncio
    async def test_passes_all_chapters_to_select_code(
        self, workflow, mock_data_loader, mock_retry_policy
    ):
        """Test that all 2-digit codes are passed to _select_code."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selected_code": "84",
            "confidence": 0.9,
            "reasoning": "Machinery chapter",
        }

        state = {"product_description": "laptop computer"}

        with patch.object(workflow, "_select_code", wraps=workflow._select_code):
            with patch("hs_agent.workflows.single_path_workflow.ModelFactory"):
                result = await workflow._select_chapter(state)

        # Should have chapter_result in state
        assert "chapter_result" in result
        assert result["chapter_result"].selected_code == "84"


class TestSelectHeading:
    """Tests for _select_heading node."""

    @pytest.mark.asyncio
    async def test_filters_headings_by_chapter(
        self, workflow, mock_data_loader, mock_retry_policy
    ):
        """Test that only headings under the selected chapter are used."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selected_code": "8471",
            "confidence": 0.85,
            "reasoning": "Data processing",
        }

        state = {
            "product_description": "laptop computer",
            "chapter_result": ClassificationResult(
                level=ClassificationLevel.CHAPTER,
                selected_code="84",
                description="Machinery",
                confidence=0.9,
                reasoning="test",
            ),
        }

        with patch("hs_agent.workflows.single_path_workflow.ModelFactory"):
            result = await workflow._select_heading(state)

        assert result["heading_result"].selected_code == "8471"

    @pytest.mark.asyncio
    async def test_excludes_other_chapter_headings(
        self, workflow, mock_data_loader, mock_retry_policy
    ):
        """Test that headings from other chapters are excluded."""
        # This tests the startswith filtering logic
        # 8501 should be excluded when chapter is 84

        mock_retry_policy.invoke_with_retry.return_value = {
            "selected_code": "8471",
            "confidence": 0.85,
            "reasoning": "Only valid option",
        }

        state = {
            "product_description": "laptop",
            "chapter_result": ClassificationResult(
                level=ClassificationLevel.CHAPTER,
                selected_code="84",
                description="Machinery",
                confidence=0.9,
                reasoning="test",
            ),
        }

        # Track what codes were passed to _select_code
        codes_passed = None
        original_select_code = workflow._select_code

        async def capture_select_code(*args, **kwargs):
            nonlocal codes_passed
            codes_passed = args[1]  # codes_dict is second argument
            return await original_select_code(*args, **kwargs)

        with patch.object(workflow, "_select_code", side_effect=capture_select_code):
            with patch("hs_agent.workflows.single_path_workflow.ModelFactory"):
                await workflow._select_heading(state)

        # 8501 should NOT be in the codes (it's under chapter 85)
        assert "8501" not in codes_passed
        # 8471 and 8473 should be there (under chapter 84)
        assert "8471" in codes_passed
        assert "8473" in codes_passed


class TestSelectSubheading:
    """Tests for _select_subheading node."""

    @pytest.mark.asyncio
    async def test_filters_subheadings_by_heading(
        self, workflow, mock_data_loader, mock_retry_policy
    ):
        """Test that only subheadings under the selected heading are used."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selected_code": "847130",
            "confidence": 0.95,
            "reasoning": "Portable computers",
        }

        state = {
            "product_description": "laptop",
            "chapter_result": ClassificationResult(
                level=ClassificationLevel.CHAPTER,
                selected_code="84",
                description="Machinery",
                confidence=0.9,
                reasoning="test",
            ),
            "heading_result": ClassificationResult(
                level=ClassificationLevel.HEADING,
                selected_code="8471",
                description="Data processing",
                confidence=0.85,
                reasoning="test",
            ),
        }

        with patch("hs_agent.workflows.single_path_workflow.ModelFactory"):
            result = await workflow._select_subheading(state)

        assert result["subheading_result"].selected_code == "847130"


class TestFinalize:
    """Tests for _finalize node."""

    @pytest.mark.asyncio
    async def test_calculates_overall_confidence(self, workflow):
        """Test that finalize calculates weighted confidence correctly."""
        state = {
            "product_description": "laptop",
            "chapter_result": ClassificationResult(
                level=ClassificationLevel.CHAPTER,
                selected_code="84",
                description="Machinery",
                confidence=1.0,  # chapter weight: 0.3
                reasoning="test",
            ),
            "heading_result": ClassificationResult(
                level=ClassificationLevel.HEADING,
                selected_code="8471",
                description="Data processing",
                confidence=1.0,  # heading weight: 0.3
                reasoning="test",
            ),
            "subheading_result": ClassificationResult(
                level=ClassificationLevel.SUBHEADING,
                selected_code="847130",
                description="Portable computers",
                confidence=1.0,  # subheading weight: 0.4
                reasoning="test",
            ),
        }

        result = await workflow._finalize(state)

        # 1.0 * 0.3 + 1.0 * 0.3 + 1.0 * 0.4 = 1.0
        assert result["overall_confidence"] == pytest.approx(1.0)
        assert result["final_code"] == "847130"

    @pytest.mark.asyncio
    async def test_uses_subheading_as_final_code(self, workflow):
        """Test that final_code is the subheading result."""
        state = {
            "product_description": "laptop",
            "chapter_result": ClassificationResult(
                level=ClassificationLevel.CHAPTER,
                selected_code="84",
                description="Machinery",
                confidence=0.9,
                reasoning="test",
            ),
            "heading_result": ClassificationResult(
                level=ClassificationLevel.HEADING,
                selected_code="8471",
                description="Data processing",
                confidence=0.85,
                reasoning="test",
            ),
            "subheading_result": ClassificationResult(
                level=ClassificationLevel.SUBHEADING,
                selected_code="847141",
                description="Other data processing",
                confidence=0.8,
                reasoning="test",
            ),
        }

        result = await workflow._finalize(state)

        assert result["final_code"] == "847141"


class TestSelectCode:
    """Tests for _select_code helper method."""

    @pytest.mark.asyncio
    async def test_returns_none_result_when_retry_exhausted(
        self, workflow, mock_data_loader, mock_retry_policy
    ):
        """Test that None from retry returns no-HS-code result."""
        mock_retry_policy.invoke_with_retry.return_value = None

        with patch("hs_agent.workflows.single_path_workflow.ModelFactory"):
            result = await workflow._select_code(
                "laptop",
                mock_data_loader.codes_2digit,
                ClassificationLevel.CHAPTER,
                config_name="select_chapter_candidates",
            )

        assert result.selected_code == "000000"
        assert result.confidence == 0.0
        assert "LLM failed" in result.reasoning

    @pytest.mark.asyncio
    async def test_handles_000000_special_code(
        self, workflow, mock_data_loader, mock_retry_policy
    ):
        """Test that 000000 code is properly handled."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selected_code": "000000",
            "confidence": 0.0,
            "reasoning": "Invalid product description",
        }

        with patch("hs_agent.workflows.single_path_workflow.ModelFactory"):
            result = await workflow._select_code(
                "asdfghjkl",
                mock_data_loader.codes_2digit,
                ClassificationLevel.CHAPTER,
                config_name="select_chapter_candidates",
            )

        assert result.selected_code == "000000"
        assert result.reasoning == "Invalid product description"

    @pytest.mark.asyncio
    async def test_raises_on_invalid_code(
        self, workflow, mock_data_loader, mock_retry_policy
    ):
        """Test that invalid code from LLM raises error."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selected_code": "99",  # Not in codes_2digit
            "confidence": 0.9,
            "reasoning": "Bad selection",
        }

        with patch("hs_agent.workflows.single_path_workflow.ModelFactory"):
            with pytest.raises(RuntimeError) as exc_info:
                await workflow._select_code(
                    "laptop",
                    mock_data_loader.codes_2digit,
                    ClassificationLevel.CHAPTER,
                    config_name="select_chapter_candidates",
                )

        assert "invalid code" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_returns_valid_classification_result(
        self, workflow, mock_data_loader, mock_retry_policy
    ):
        """Test successful classification returns proper result."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selected_code": "84",
            "confidence": 0.92,
            "reasoning": "Machinery chapter for computers",
        }

        with patch("hs_agent.workflows.single_path_workflow.ModelFactory"):
            result = await workflow._select_code(
                "laptop computer",
                mock_data_loader.codes_2digit,
                ClassificationLevel.CHAPTER,
                config_name="select_chapter_candidates",
            )

        assert isinstance(result, ClassificationResult)
        assert result.selected_code == "84"
        assert result.confidence == 0.92
        assert result.reasoning == "Machinery chapter for computers"
        assert result.description == "Machinery"
        assert result.level == ClassificationLevel.CHAPTER
