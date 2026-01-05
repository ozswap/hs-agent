"""Tests for MultiPathWorkflow class.

Tests cover:
- Graph structure and node connections
- Multi-selection filtering by parent (startswith logic)
- Path building (cartesian product, sorting, limiting)
- Final code comparison and validation
- _multi_select_codes result handling (empty, invalid, valid)
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from hs_agent.models import ClassificationLevel, ClassificationPath
from hs_agent.workflows.multi_path_workflow import MultiPathWorkflow


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
        "8528": MockHSCode("8528", "Monitors"),
    }
    loader.codes_6digit = {
        "847130": MockHSCode("847130", "Portable computers"),
        "847141": MockHSCode("847141", "Other data processing"),
        "847330": MockHSCode("847330", "Parts for 8471"),
        "850110": MockHSCode("850110", "Electric motors small"),
        "852841": MockHSCode("852841", "Computer monitors"),
    }
    return loader


@pytest.fixture
def mock_retry_policy():
    """Create a mock retry policy."""
    policy = Mock()
    policy.invoke_with_retry = AsyncMock()
    return policy


@pytest.fixture
def mock_chapter_notes_service():
    """Create a mock chapter notes service."""
    service = Mock()
    service.load_chapter_notes = Mock(
        return_value="═══ CHAPTER 84 NOTES ═══\nMachinery chapter notes."
    )
    return service


@pytest.fixture
def sample_configs():
    """Sample workflow configs."""
    return {
        "select_chapter_candidates": {
            "model": {"name": "gemini-2.5-flash"},
            "output_schema": {
                "type": "object",
                "properties": {
                    "selections": {"type": "array", "items": {"type": "object"}}
                },
            },
        },
        "select_heading_candidates": {"model": {"name": "gemini-2.5-flash"}},
        "select_subheading_candidates": {"model": {"name": "gemini-2.5-flash"}},
        "compare_final_codes": {"model": {"name": "gemini-2.5-flash"}},
    }


@pytest.fixture
def workflow(
    mock_data_loader, mock_retry_policy, mock_chapter_notes_service, sample_configs
):
    """Create a MultiPathWorkflow instance."""
    return MultiPathWorkflow(
        data_loader=mock_data_loader,
        model_name="gemini-2.5-flash",
        configs=sample_configs,
        retry_policy=mock_retry_policy,
        chapter_notes_service=mock_chapter_notes_service,
    )


class TestBuildGraph:
    """Tests for graph structure."""

    def test_graph_has_five_nodes(self, workflow):
        """Test graph has expected nodes."""
        graph = workflow.build_graph()

        node_names = list(graph.nodes.keys())
        assert "select_chapters" in node_names
        assert "select_headings" in node_names
        assert "select_subheadings" in node_names
        assert "build_paths" in node_names
        assert "compare_final_codes" in node_names

    def test_graph_compiles_without_error(self, workflow):
        """Test graph compilation succeeds."""
        graph = workflow.build_graph()
        assert graph is not None


class TestMultiSelectChapters:
    """Tests for _multi_select_chapters node."""

    @pytest.mark.asyncio
    async def test_returns_multiple_chapters(self, workflow, mock_retry_policy):
        """Test that multiple chapters can be selected."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selections": [
                {"code": "84", "confidence": 0.9, "reasoning": "Machinery"},
                {"code": "85", "confidence": 0.7, "reasoning": "Electrical"},
            ]
        }

        state = {"product_description": "laptop computer", "max_selections": 3}

        with patch("hs_agent.workflows.multi_path_workflow.ModelFactory"):
            result = await workflow._multi_select_chapters(state)

        assert result["selected_chapters"] == ["84", "85"]
        assert result["chapter_confidences"] == [0.9, 0.7]
        assert len(result["chapter_reasonings"]) == 2


class TestMultiSelectHeadings:
    """Tests for _multi_select_headings node."""

    @pytest.mark.asyncio
    async def test_filters_headings_by_chapter(self, workflow, mock_retry_policy):
        """Test that headings are filtered by parent chapter."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selections": [
                {"code": "8471", "confidence": 0.85, "reasoning": "Data processing"}
            ]
        }

        state = {
            "product_description": "laptop",
            "max_selections": 3,
            "selected_chapters": ["84"],
            "chapter_confidences": [0.9],
            "chapter_reasonings": ["Machinery"],
        }

        # Track what codes are passed
        codes_passed = {}
        original_multi_select = workflow._multi_select_codes

        async def capture_multi_select(*args, **kwargs):
            codes_passed.update(args[1])  # codes_dict is second argument
            return await original_multi_select(*args, **kwargs)

        with patch.object(
            workflow, "_multi_select_codes", side_effect=capture_multi_select
        ):
            with patch("hs_agent.workflows.multi_path_workflow.ModelFactory"):
                await workflow._multi_select_headings(state)

        # 8501 and 8528 should NOT be passed (under chapter 85)
        assert "8501" not in codes_passed
        assert "8528" not in codes_passed
        # 8471 and 8473 should be passed (under chapter 84)
        assert "8471" in codes_passed
        assert "8473" in codes_passed


class TestMultiSelectSubheadings:
    """Tests for _multi_select_subheadings node."""

    @pytest.mark.asyncio
    async def test_filters_subheadings_by_heading(self, workflow, mock_retry_policy):
        """Test that subheadings are filtered by parent heading."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selections": [
                {"code": "847130", "confidence": 0.95, "reasoning": "Portable"}
            ]
        }

        state = {
            "product_description": "laptop",
            "max_selections": 3,
            "selected_chapters": ["84"],
            "selected_headings_by_chapter": {"84": ["8471"]},
            "heading_confidences_by_chapter": {"84": [0.85]},
            "heading_reasonings_by_chapter": {"84": ["Data processing"]},
        }

        # Track what codes are passed
        codes_passed = {}
        original_multi_select = workflow._multi_select_codes

        async def capture_multi_select(*args, **kwargs):
            codes_passed.update(args[1])
            return await original_multi_select(*args, **kwargs)

        with patch.object(
            workflow, "_multi_select_codes", side_effect=capture_multi_select
        ):
            with patch("hs_agent.workflows.multi_path_workflow.ModelFactory"):
                await workflow._multi_select_subheadings(state)

        # Only 8471xx codes should be passed
        assert "847130" in codes_passed
        assert "847141" in codes_passed
        # 847330 and 850110 should NOT be passed
        assert "847330" not in codes_passed
        assert "850110" not in codes_passed


class TestMultiBuildPaths:
    """Tests for _multi_build_paths node."""

    @pytest.mark.asyncio
    async def test_builds_cartesian_product_of_paths(self, workflow, mock_data_loader):
        """Test that all combinations are built."""
        state = {
            "product_description": "laptop",
            "max_selections": 3,
            "selected_chapters": ["84"],
            "chapter_confidences": [0.9],
            "chapter_reasonings": ["Machinery"],
            "selected_headings_by_chapter": {"84": ["8471", "8473"]},
            "heading_confidences_by_chapter": {"84": [0.85, 0.75]},
            "heading_reasonings_by_chapter": {"84": ["Data", "Parts"]},
            "selected_subheadings_by_heading": {
                "8471": ["847130", "847141"],
                "8473": ["847330"],
            },
            "subheading_confidences_by_heading": {
                "8471": [0.95, 0.8],
                "8473": [0.7],
            },
            "subheading_reasonings_by_heading": {
                "8471": ["Portable", "Other"],
                "8473": ["Parts"],
            },
        }

        result = await workflow._multi_build_paths(state)

        # Should have 3 paths: (84->8471->847130), (84->8471->847141), (84->8473->847330)
        assert len(result["paths"]) == 3

    @pytest.mark.asyncio
    async def test_sorts_paths_by_confidence_descending(self, workflow):
        """Test that paths are sorted by confidence descending."""
        state = {
            "product_description": "laptop",
            "max_selections": 3,
            "selected_chapters": ["84", "85"],
            "chapter_confidences": [0.5, 0.9],  # 85 has higher confidence
            "chapter_reasonings": ["Machinery", "Electrical"],
            "selected_headings_by_chapter": {"84": ["8471"], "85": ["8501"]},
            "heading_confidences_by_chapter": {"84": [0.5], "85": [0.9]},
            "heading_reasonings_by_chapter": {"84": ["Data"], "85": ["Motors"]},
            "selected_subheadings_by_heading": {
                "8471": ["847130"],
                "8501": ["850110"],
            },
            "subheading_confidences_by_heading": {
                "8471": [0.5],
                "8501": [0.9],
            },
            "subheading_reasonings_by_heading": {
                "8471": ["Portable"],
                "8501": ["Small motors"],
            },
        }

        result = await workflow._multi_build_paths(state)

        # First path should have higher confidence (85 path)
        assert result["paths"][0].chapter_code == "85"
        assert result["paths"][0].path_confidence > result["paths"][1].path_confidence

    @pytest.mark.asyncio
    async def test_limits_to_max_output_paths(self, workflow):
        """Test that paths are limited by settings.max_output_paths."""
        # Create many paths
        state = {
            "product_description": "laptop",
            "max_selections": 3,
            "selected_chapters": ["84", "85"],
            "chapter_confidences": [0.9, 0.8],
            "chapter_reasonings": ["A", "B"],
            "selected_headings_by_chapter": {
                "84": ["8471", "8473"],
                "85": ["8501", "8528"],
            },
            "heading_confidences_by_chapter": {
                "84": [0.9, 0.8],
                "85": [0.7, 0.6],
            },
            "heading_reasonings_by_chapter": {
                "84": ["A", "B"],
                "85": ["C", "D"],
            },
            "selected_subheadings_by_heading": {
                "8471": ["847130", "847141"],
                "8473": ["847330"],
                "8501": ["850110"],
                "8528": ["852841"],
            },
            "subheading_confidences_by_heading": {
                "8471": [0.9, 0.8],
                "8473": [0.7],
                "8501": [0.6],
                "8528": [0.5],
            },
            "subheading_reasonings_by_heading": {
                "8471": ["A", "B"],
                "8473": ["C"],
                "8501": ["D"],
                "8528": ["E"],
            },
        }

        with patch("hs_agent.workflows.multi_path_workflow.settings") as mock_settings:
            mock_settings.max_output_paths = 3  # Limit to 3
            result = await workflow._multi_build_paths(state)

        assert len(result["paths"]) == 3


class TestCompareFinalCodes:
    """Tests for _compare_final_codes node."""

    @pytest.mark.asyncio
    async def test_loads_chapter_notes(
        self, workflow, mock_chapter_notes_service, mock_retry_policy
    ):
        """Test that chapter notes are loaded for path chapters."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selected_code": "847130",
            "confidence": 0.95,
            "reasoning": "Best match",
            "comparison_summary": "Compared paths",
        }

        paths = [
            ClassificationPath(
                chapter_code="84",
                chapter_description="Machinery",
                heading_code="8471",
                heading_description="Data processing",
                subheading_code="847130",
                subheading_description="Portable computers",
                path_confidence=0.9,
                chapter_reasoning="test",
                heading_reasoning="test",
                subheading_reasoning="test",
            )
        ]

        state = {"product_description": "laptop", "paths": paths}

        with patch("hs_agent.workflows.multi_path_workflow.ModelFactory"):
            await workflow._compare_final_codes(state)

        mock_chapter_notes_service.load_chapter_notes.assert_called_once_with(["84"])

    @pytest.mark.asyncio
    async def test_returns_000000_on_none_result(self, workflow, mock_retry_policy):
        """Test that None result returns 000000."""
        mock_retry_policy.invoke_with_retry.return_value = None

        paths = [
            ClassificationPath(
                chapter_code="84",
                chapter_description="Machinery",
                heading_code="8471",
                heading_description="Data processing",
                subheading_code="847130",
                subheading_description="Portable computers",
                path_confidence=0.9,
                chapter_reasoning="test",
                heading_reasoning="test",
                subheading_reasoning="test",
            )
        ]

        state = {"product_description": "laptop", "paths": paths}

        with patch("hs_agent.workflows.multi_path_workflow.ModelFactory"):
            result = await workflow._compare_final_codes(state)

        assert result["final_selected_code"] == "000000"
        assert result["final_confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_raises_on_invalid_code(self, workflow, mock_retry_policy):
        """Test that selecting code not in paths raises error."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selected_code": "999999",  # Not in paths
            "confidence": 0.9,
            "reasoning": "Bad selection",
            "comparison_summary": "Failed",
        }

        paths = [
            ClassificationPath(
                chapter_code="84",
                chapter_description="Machinery",
                heading_code="8471",
                heading_description="Data processing",
                subheading_code="847130",
                subheading_description="Portable computers",
                path_confidence=0.9,
                chapter_reasoning="test",
                heading_reasoning="test",
                subheading_reasoning="test",
            )
        ]

        state = {"product_description": "laptop", "paths": paths}

        with patch("hs_agent.workflows.multi_path_workflow.ModelFactory"):
            with pytest.raises(RuntimeError) as exc_info:
                await workflow._compare_final_codes(state)

        assert "invalid code" in str(exc_info.value).lower()


class TestMultiSelectCodes:
    """Tests for _multi_select_codes helper method."""

    @pytest.mark.asyncio
    async def test_returns_000000_on_none_result(
        self, workflow, mock_data_loader, mock_retry_policy
    ):
        """Test that None from retry returns 000000."""
        mock_retry_policy.invoke_with_retry.return_value = None

        with patch("hs_agent.workflows.multi_path_workflow.ModelFactory"):
            result = await workflow._multi_select_codes(
                "laptop",
                mock_data_loader.codes_2digit,
                "select_chapter_candidates",
                ClassificationLevel.CHAPTER,
                max_selections=3,
            )

        assert result["codes"] == ["000000"]
        assert result["confidences"] == [0.0]

    @pytest.mark.asyncio
    async def test_returns_000000_on_empty_selections(
        self, workflow, mock_data_loader, mock_retry_policy
    ):
        """Test that empty selections returns 000000."""
        mock_retry_policy.invoke_with_retry.return_value = {"selections": []}

        with patch("hs_agent.workflows.multi_path_workflow.ModelFactory"):
            result = await workflow._multi_select_codes(
                "laptop",
                mock_data_loader.codes_2digit,
                "select_chapter_candidates",
                ClassificationLevel.CHAPTER,
                max_selections=3,
            )

        assert result["codes"] == ["000000"]
        assert "empty" in result["reasonings"][0].lower()

    @pytest.mark.asyncio
    async def test_filters_invalid_codes(
        self, workflow, mock_data_loader, mock_retry_policy
    ):
        """Test that invalid codes are filtered out."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selections": [
                {"code": "84", "confidence": 0.9, "reasoning": "Valid"},
                {
                    "code": "99",
                    "confidence": 0.8,
                    "reasoning": "Invalid",
                },  # Not in codes
            ]
        }

        with patch("hs_agent.workflows.multi_path_workflow.ModelFactory"):
            result = await workflow._multi_select_codes(
                "laptop",
                mock_data_loader.codes_2digit,
                "select_chapter_candidates",
                ClassificationLevel.CHAPTER,
                max_selections=3,
            )

        # Only valid code should be returned
        assert result["codes"] == ["84"]
        assert len(result["confidences"]) == 1

    @pytest.mark.asyncio
    async def test_returns_000000_when_all_codes_invalid(
        self, workflow, mock_data_loader, mock_retry_policy
    ):
        """Test that all invalid codes returns 000000."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selections": [
                {"code": "99", "confidence": 0.9, "reasoning": "Invalid1"},
                {"code": "98", "confidence": 0.8, "reasoning": "Invalid2"},
            ]
        }

        with patch("hs_agent.workflows.multi_path_workflow.ModelFactory"):
            result = await workflow._multi_select_codes(
                "laptop",
                mock_data_loader.codes_2digit,
                "select_chapter_candidates",
                ClassificationLevel.CHAPTER,
                max_selections=3,
            )

        assert result["codes"] == ["000000"]

    @pytest.mark.asyncio
    async def test_returns_valid_selections(
        self, workflow, mock_data_loader, mock_retry_policy
    ):
        """Test successful multi-selection returns proper results."""
        mock_retry_policy.invoke_with_retry.return_value = {
            "selections": [
                {"code": "84", "confidence": 0.9, "reasoning": "Machinery chapter"},
                {"code": "85", "confidence": 0.7, "reasoning": "Electrical chapter"},
            ]
        }

        with patch("hs_agent.workflows.multi_path_workflow.ModelFactory"):
            result = await workflow._multi_select_codes(
                "laptop",
                mock_data_loader.codes_2digit,
                "select_chapter_candidates",
                ClassificationLevel.CHAPTER,
                max_selections=3,
            )

        assert result["codes"] == ["84", "85"]
        assert result["confidences"] == [0.9, 0.7]
        assert result["reasonings"] == ["Machinery chapter", "Electrical chapter"]
