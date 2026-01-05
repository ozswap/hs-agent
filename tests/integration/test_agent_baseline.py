"""Baseline integration tests for HSAgent before refactoring.

These tests document the expected behavior of HSAgent before the refactoring.
They serve as a safety net to ensure backward compatibility is maintained.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from hs_agent.agent import HSAgent
from hs_agent.data_loader import HSDataLoader
from hs_agent.models import (
    ClassificationLevel,
    ClassificationPath,
    ClassificationResponse,
    ClassificationResult,
    MultiChoiceClassificationResponse,
)


@pytest.fixture
def mock_data_loader():
    """Create a mock data loader with sample HS codes."""
    loader = Mock(spec=HSDataLoader)

    # Mock 2-digit codes (chapters)
    loader.codes_2digit = {
        "84": Mock(description="Machinery"),
        "62": Mock(description="Articles of apparel"),
    }

    # Mock 4-digit codes (headings)
    loader.codes_4digit = {
        "8471": Mock(description="Data processing machines"),
        "6203": Mock(description="Men's suits, ensembles"),
    }

    # Mock 6-digit codes (subheadings)
    loader.codes_6digit = {
        "847130": Mock(description="Portable computers"),
        "620342": Mock(description="Men's cotton trousers"),
    }

    return loader


@pytest.fixture
def mock_llm_responses():
    """Mock LLM responses for testing."""
    return {
        "chapter_selection": {
            "selected_code": "84",
            "confidence": 0.9,
            "reasoning": "Product is machinery/electronic equipment",
        },
        "heading_selection": {
            "selected_code": "8471",
            "confidence": 0.85,
            "reasoning": "Specifically data processing equipment",
        },
        "subheading_selection": {
            "selected_code": "847130",
            "confidence": 0.95,
            "reasoning": "Portable computer classification",
        },
        "multi_selection_chapters": {
            "selections": [
                {"code": "84", "confidence": 0.9, "reasoning": "Primary: Machinery"},
                {"code": "62", "confidence": 0.6, "reasoning": "Alternative: If textile component"},
            ]
        },
        "multi_selection_headings": {
            "selections": [
                {"code": "8471", "confidence": 0.85, "reasoning": "Data processing"},
                {"code": "8473", "confidence": 0.7, "reasoning": "Parts of machines"},
            ]
        },
        "multi_selection_subheadings": {
            "selections": [
                {"code": "847130", "confidence": 0.95, "reasoning": "Portable computers"},
                {"code": "847141", "confidence": 0.75, "reasoning": "Other computing units"},
            ]
        },
        "compare_codes": {
            "selected_code": "847130",
            "confidence": 0.95,
            "reasoning": "Best match based on specifications",
            "comparison_summary": "Compared 2 paths, selected most specific",
        },
    }


class TestHSAgentBaseline:
    """Test HSAgent behavior before refactoring (baseline)."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self, mock_data_loader):
        """Test that agent initializes correctly."""
        agent = HSAgent(
            data_loader=mock_data_loader,
            model_name="gemini-2.5-flash",
            workflow_name="single_path_classification",
        )

        assert agent.data_loader == mock_data_loader
        assert agent.model_name == "gemini-2.5-flash"
        assert agent.workflow_name == "single_path_classification"
        assert agent.graph is not None
        assert agent.multi_graph is not None

    @pytest.mark.asyncio
    async def test_single_path_classification_structure(self, mock_data_loader, mock_llm_responses):
        """Test that single-path classification returns expected structure."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "<test>"}):
            agent = HSAgent(
                data_loader=mock_data_loader, workflow_name="single_path_classification"
            )

            # Mock the graph invocation
            with patch.object(agent.graph, "ainvoke", new_callable=AsyncMock) as mock_invoke:
                mock_invoke.return_value = {
                    "product_description": "laptop computer",
                    "chapter_result": ClassificationResult(
                        level=ClassificationLevel.CHAPTER,
                        selected_code="84",
                        description="Machinery",
                        confidence=0.9,
                        reasoning="Machinery classification",
                    ),
                    "heading_result": ClassificationResult(
                        level=ClassificationLevel.HEADING,
                        selected_code="8471",
                        description="Data processing machines",
                        confidence=0.85,
                        reasoning="Data processing",
                    ),
                    "subheading_result": ClassificationResult(
                        level=ClassificationLevel.SUBHEADING,
                        selected_code="847130",
                        description="Portable computers",
                        confidence=0.95,
                        reasoning="Portable computer",
                    ),
                    "final_code": "847130",
                    "overall_confidence": 0.9,
                }

                result = await agent.classify("laptop computer")

                # Verify response structure
                assert isinstance(result, ClassificationResponse)
                assert result.product_description == "laptop computer"
                assert result.final_code == "847130"
                assert 0.0 <= result.overall_confidence <= 1.0
                assert result.chapter is not None
                assert result.heading is not None
                assert result.subheading is not None
                assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_multi_choice_classification_structure(
        self, mock_data_loader, mock_llm_responses
    ):
        """Test that multi-choice classification returns expected structure."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "<test>"}):
            agent = HSAgent(data_loader=mock_data_loader, workflow_name="wide_net_classification")

            # Mock the multi graph invocation
            with patch.object(agent.multi_graph, "ainvoke", new_callable=AsyncMock) as mock_invoke:
                mock_invoke.return_value = {
                    "product_description": "laptop computer",
                    "paths": [
                        ClassificationPath(
                            chapter_code="84",
                            chapter_description="Machinery",
                            heading_code="8471",
                            heading_description="Data processing machines",
                            subheading_code="847130",
                            subheading_description="Portable computers",
                            path_confidence=0.9,
                            chapter_reasoning="Machinery classification",
                            heading_reasoning="Data processing",
                            subheading_reasoning="Portable computer",
                        )
                    ],
                    "overall_strategy": "Selected 1 path",
                    "final_selected_code": "847130",
                    "final_confidence": 0.95,
                    "final_reasoning": "Best match",
                    "comparison_summary": "Compared paths",
                }

                result = await agent.classify_multi("laptop computer", max_selections=3)

                # Verify response structure
                assert isinstance(result, MultiChoiceClassificationResponse)
                assert result.product_description == "laptop computer"
                assert len(result.paths) >= 1
                assert result.overall_strategy is not None
                assert result.processing_time_ms > 0
                assert result.final_selected_code is not None
                assert result.final_confidence is not None

    @pytest.mark.asyncio
    async def test_agent_has_required_methods(self, mock_data_loader):
        """Test that agent has all required public methods."""
        agent = HSAgent(data_loader=mock_data_loader, workflow_name="single_path_classification")

        # Verify public API methods exist
        assert hasattr(agent, "classify")
        assert callable(agent.classify)
        assert hasattr(agent, "classify_multi")
        assert callable(agent.classify_multi)

    @pytest.mark.asyncio
    async def test_agent_has_workflow_composition(self, mock_data_loader):
        """Test that agent uses workflow composition after refactoring."""
        agent = HSAgent(data_loader=mock_data_loader, workflow_name="single_path_classification")

        # After refactoring: verify agent uses workflow composition pattern
        # Private methods were extracted to:
        # - ModelFactory: _create_base_model, _get_model_for_config
        # - RetryPolicy: _invoke_with_retry
        # - ChapterNotesService: _load_chapter_notes
        # - SinglePathWorkflow: _build_graph, _select_code
        # - MultiPathWorkflow: _build_multi_graph, _multi_select_codes, _compare_final_codes

        assert hasattr(agent, "single_path_workflow")
        assert hasattr(agent, "multi_path_workflow")
        assert hasattr(agent, "retry_policy")
        assert hasattr(agent, "chapter_notes_service")
        assert agent.single_path_workflow is not None
        assert agent.multi_path_workflow is not None
        assert agent.retry_policy is not None
        assert agent.chapter_notes_service is not None


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility after refactoring."""

    @pytest.mark.asyncio
    async def test_import_paths_unchanged(self):
        """Test that import paths remain the same."""
        # These imports should work after refactoring
        from hs_agent.agent import HSAgent
        from hs_agent.data_loader import HSDataLoader
        from hs_agent.models import ClassificationResponse, MultiChoiceClassificationResponse

        assert HSAgent is not None
        assert HSDataLoader is not None
        assert ClassificationResponse is not None
        assert MultiChoiceClassificationResponse is not None

    @pytest.mark.asyncio
    async def test_agent_initialization_api_unchanged(self, mock_data_loader):
        """Test that agent initialization API remains unchanged."""
        # This initialization pattern should work after refactoring
        agent = HSAgent(
            data_loader=mock_data_loader,
            model_name="gemini-2.5-flash",
            workflow_name="single_path_classification",
        )

        assert agent is not None

    @pytest.mark.asyncio
    async def test_classify_api_signature_unchanged(self, mock_data_loader):
        """Test that classify() method signature remains unchanged."""
        agent = HSAgent(data_loader=mock_data_loader, workflow_name="single_path_classification")

        # Mock the graph to avoid actual LLM calls
        with patch.object(agent.graph, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "product_description": "test",
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
                    description="Data processing machines",
                    confidence=0.85,
                    reasoning="test",
                ),
                "subheading_result": ClassificationResult(
                    level=ClassificationLevel.SUBHEADING,
                    selected_code="847130",
                    description="Portable computers",
                    confidence=0.95,
                    reasoning="test",
                ),
                "final_code": "847130",
                "overall_confidence": 0.9,
            }

            # This call signature should work after refactoring
            result = await agent.classify("test product")
            assert isinstance(result, ClassificationResponse)

    @pytest.mark.asyncio
    async def test_classify_multi_api_signature_unchanged(self, mock_data_loader):
        """Test that classify_multi() method signature remains unchanged."""
        agent = HSAgent(data_loader=mock_data_loader, workflow_name="wide_net_classification")

        # Mock the multi graph
        with patch.object(agent.multi_graph, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "product_description": "test",
                "paths": [
                    ClassificationPath(
                        chapter_code="84",
                        chapter_description="Machinery",
                        heading_code="8471",
                        heading_description="Data processing machines",
                        subheading_code="847130",
                        subheading_description="Portable computers",
                        path_confidence=0.9,
                        chapter_reasoning="test",
                        heading_reasoning="test",
                        subheading_reasoning="test",
                    )
                ],
                "overall_strategy": "test",
                "final_selected_code": "847130",
                "final_confidence": 0.95,
                "final_reasoning": "test",
                "comparison_summary": "test",
            }

            # This call signature should work after refactoring
            result = await agent.classify_multi("test product", max_selections=3)
            assert isinstance(result, MultiChoiceClassificationResponse)


@pytest.mark.integration
class TestRefactoringPreparation:
    """Tests to prepare for refactoring."""

    def test_agent_line_count_baseline(self):
        """Record baseline line count before refactoring."""
        import os

        agent_file = "hs_agent/agent.py"

        if os.path.exists(agent_file):
            with open(agent_file) as f:
                lines = len(f.readlines())

            # Document current state
            print(f"\n📊 Baseline: agent.py has {lines} lines")
            assert lines > 0, "agent.py should exist and have content"

    def test_agent_method_count_baseline(self):
        """Record baseline method count before refactoring."""
        import os
        import re

        agent_file = "hs_agent/agent.py"
        if os.path.exists(agent_file):
            with open(agent_file) as f:
                content = f.read()

            # Count methods
            methods = re.findall(r"^\s+(async )?def ", content, re.MULTILINE)

            print(f"\n📊 Baseline: HSAgent has {len(methods)} methods")
            assert len(methods) > 0, "HSAgent should have methods"
