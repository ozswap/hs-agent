"""Pytest configuration and shared fixtures for HS Agent tests.

This module provides common test configuration, fixtures, and utilities
that are shared across all test modules.
"""

import os

# Add the project root to Python path for imports
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hs_agent.config.settings import HSAgentSettings  # noqa: E402


# Simple mock classes for testing - we don't need the full models
class HSCode:
    def __init__(self, code, description, level, parent=None, section=None):
        self.code = code
        self.description = description
        self.level = level
        self.parent = parent
        self.section = section


class TaxCodeEntry:
    def __init__(self, avalara_code, description, additional_info=None):
        self.avalara_code = avalara_code
        self.description = description
        self.additional_info = additional_info


class ProductExample:
    def __init__(self, hs_code, product_description, source, confidence):
        self.hs_code = hs_code
        self.product_description = product_description
        self.source = source
        self.confidence = confidence


@pytest.fixture(scope="session")
def test_settings():
    """Provide test-specific settings."""
    # Override settings for testing
    test_env = {
        "GOOGLE_API_KEY": "test_api_key_for_testing",  # pragma: allowlist secret
        "ENABLE_LOGFIRE": "false",
        "DEBUG_MODE": "true",
        "DEVELOPMENT_MODE": "true",
        "LOG_LEVEL": "DEBUG",
    }

    with patch.dict(os.environ, test_env):
        # Rebuild settings so env overrides apply
        yield HSAgentSettings()


@pytest.fixture
def sample_hs_codes():
    """Provide sample HS codes for testing."""
    return [
        HSCode(
            code="84",
            description="Nuclear reactors, boilers, machinery and mechanical appliances; parts thereof",
            level=2,
            section="XVI",
        ),
        HSCode(
            code="8471",
            description="Automatic data processing machines and units thereof; magnetic or optical readers",
            level=4,
            parent="84",
            section="XVI",
        ),
        HSCode(
            code="847130",
            description="Portable digital automatic data processing machines, weighing not more than 10 kg",
            level=6,
            parent="8471",
            section="XVI",
        ),
    ]


@pytest.fixture
def sample_tax_codes():
    """Provide sample tax codes for testing."""
    return [
        TaxCodeEntry(
            avalara_code="PC040100",
            description="Personal computers and laptops",
            additional_info="Including accessories and peripherals",
        ),
        TaxCodeEntry(
            avalara_code="CL010200",
            description="Cotton clothing and apparel",
            additional_info="T-shirts, shirts, and casual wear",
        ),
    ]


@pytest.fixture
def sample_product_examples():
    """Provide sample product examples for testing."""
    return [
        ProductExample(
            hs_code="847130",
            product_description="Laptop computer with 16GB RAM and 512GB SSD",
            source="test_data",
            confidence=0.95,
        ),
        ProductExample(
            hs_code="620342",
            product_description="Men's cotton t-shirt, size large",
            source="test_data",
            confidence=0.90,
        ),
    ]


@pytest.fixture
def mock_data_loader():
    """Provide a mock data loader for testing."""
    mock_loader = Mock()

    # Mock the codes dictionaries
    mock_loader.codes_2digit = {
        "84": HSCode(code="84", description="Machinery", level=2),
        "62": HSCode(code="62", description="Articles of apparel", level=2),
    }

    mock_loader.codes_4digit = {
        "8471": HSCode(
            code="8471", description="Data processing machines", level=4, parent="84"
        ),
        "6203": HSCode(
            code="6203", description="Men's suits, ensembles", level=4, parent="62"
        ),
    }

    mock_loader.codes_6digit = {
        "847130": HSCode(
            code="847130", description="Portable computers", level=6, parent="8471"
        ),
        "620342": HSCode(
            code="620342", description="Men's cotton trousers", level=6, parent="6203"
        ),
    }

    # Mock methods
    mock_loader.get_codes_by_level.side_effect = lambda level: {
        2: mock_loader.codes_2digit,
        4: mock_loader.codes_4digit,
        6: mock_loader.codes_6digit,
    }[level]

    mock_loader.get_examples_for_code.return_value = [
        "Sample product description 1",
        "Sample product description 2",
    ]

    return mock_loader


@pytest.fixture
def mock_llm_response():
    """Provide mock LLM responses for testing."""
    return {
        "ranking_response": {
            "ranked_candidates": [
                {
                    "code": "847130",
                    "description": "Portable computers",
                    "relevance_score": 0.95,
                    "justification": "Perfect match for laptop computer",
                }
            ],
            "reasoning": "Clear match for computer equipment",
        },
        "selection_response": {
            "selected_code": "847130",
            "confidence": 0.95,
            "reasoning": "This is clearly a laptop computer",
        },
    }


@pytest.fixture
def temp_data_dir():
    """Provide a temporary directory with test data files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create sample CSV files
        hs_codes_file = temp_path / "hs_codes_all.csv"
        hs_codes_file.write_text(
            "hscode,description,level,parent,section\n"
            "84,Machinery,2,,XVI\n"
            "8471,Data processing machines,4,84,XVI\n"
            "847130,Portable computers,6,8471,XVI\n"
        )

        examples_file = temp_path / "hs6_examples_cleaned.csv"
        examples_file.write_text(
            "hs6_code,product_description\n847130,Laptop computer\n847130,Notebook computer\n"
        )

        yield temp_path


@pytest.fixture
def mock_agent():
    """Provide a mock agent for testing."""
    mock_agent = Mock()

    # Mock classification methods
    mock_agent.classify_hierarchical.return_value = {
        "chapter": Mock(selected_code="84", confidence=0.9),
        "heading": Mock(selected_code="8471", confidence=0.85),
        "subheading": Mock(selected_code="847130", confidence=0.95),
        "final_code": "847130",
        "overall_confidence": 0.9,
    }

    return mock_agent


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


# ========== New Fixtures for Workflow Testing ==========


@pytest.fixture
def mock_retry_policy():
    """Provide a mock RetryPolicy with AsyncMock for invoke_with_retry."""
    from hs_agent.policies.retry_policy import RetryPolicy

    mock_policy = Mock(spec=RetryPolicy)
    mock_policy.invoke_with_retry = AsyncMock(
        return_value={
            "selected_code": "847130",
            "confidence": 0.95,
            "reasoning": "Test reasoning for laptop computer",
        }
    )
    return mock_policy


@pytest.fixture
def mock_retry_policy_multi_selection():
    """Provide a mock RetryPolicy for multi-selection workflows."""
    from hs_agent.policies.retry_policy import RetryPolicy

    mock_policy = Mock(spec=RetryPolicy)
    mock_policy.invoke_with_retry = AsyncMock(
        return_value={
            "selections": [
                {"code": "84", "confidence": 0.9, "reasoning": "Machinery chapter"},
                {"code": "85", "confidence": 0.7, "reasoning": "Electrical chapter"},
            ]
        }
    )
    return mock_policy


@pytest.fixture
def mock_chapter_notes_service():
    """Provide a mock ChapterNotesService."""
    from hs_agent.services.chapter_notes_service import ChapterNotesService

    mock_service = Mock(spec=ChapterNotesService)
    mock_service.load_chapter_notes.return_value = (
        "=== Chapter 84 Notes ===\n"
        "This chapter covers machinery and mechanical appliances.\n"
        "Exclusions: Articles of Chapter 85 if primarily electrical."
    )
    return mock_service


@pytest.fixture
def sample_workflow_config():
    """Provide a sample workflow configuration dictionary."""
    return {
        "model": {
            "name": "gemini-2.5-flash",
            "parameters": {"temperature": 0.1, "max_tokens": 8192, "top_p": 0.95},
        },
        "prompts": {
            "system": "You are an HS code classification expert.",
            "user": "Product: {product_description}\nCandidates:\n{candidates_list}",
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "selected_code": {"type": "string"},
                "confidence": {"type": "number"},
                "reasoning": {"type": "string"},
            },
            "required": ["selected_code", "confidence", "reasoning"],
        },
    }


@pytest.fixture
def temp_config_dir():
    """Provide a temporary directory with config files for testing config_loader."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create config folder structure
        config_folder = temp_path / "select_chapter_candidates"
        config_folder.mkdir()
        prompts_folder = config_folder / "prompts"
        prompts_folder.mkdir()

        # Create config.yaml
        (config_folder / "config.yaml").write_text(
            "model:\n"
            "  name: gemini-2.5-flash\n"
            "  parameters:\n"
            "    temperature: 0.1\n"
            "prompts:\n"
            "  system: prompts/system.md\n"
            "  user: prompts/user.md\n"
        )

        # Create prompt files
        (prompts_folder / "system.md").write_text(
            "You are an HS code classification expert.\n"
            "Select the best chapter for the product."
        )
        (prompts_folder / "user.md").write_text(
            "Product: {product_description}\n\n"
            "Available chapters:\n{candidates_list}"
        )

        yield temp_path


@pytest.fixture
def temp_chapter_notes_dir():
    """Provide a temporary directory with chapter notes for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create chapters_markdown folder
        notes_dir = temp_path / "chapters_markdown"
        notes_dir.mkdir()

        # Create sample chapter notes
        (notes_dir / "chapter_84_notes.md").write_text(
            "# Chapter 84 Notes\n\n"
            "This chapter covers machinery and mechanical appliances.\n\n"
            "## Exclusions\n"
            "- Electrical machinery (Chapter 85)\n"
        )
        (notes_dir / "chapter_85_notes.md").write_text(
            "# Chapter 85 Notes\n\n"
            "This chapter covers electrical machinery and equipment.\n"
        )

        yield temp_path


@pytest.fixture
def sample_classification_state():
    """Provide a sample ClassificationState for single-path workflow testing."""
    from hs_agent.models import ClassificationLevel, ClassificationResult

    return {
        "product_description": "laptop computer with 16GB RAM",
        "chapter_result": ClassificationResult(
            level=ClassificationLevel.CHAPTER,
            selected_code="84",
            description="Machinery",
            confidence=0.9,
            reasoning="Computer equipment falls under machinery",
        ),
        "heading_result": None,
        "subheading_result": None,
        "final_code": None,
        "overall_confidence": None,
    }


@pytest.fixture
def sample_multi_choice_state():
    """Provide a sample MultiChoiceState for multi-path workflow testing."""
    return {
        "product_description": "laptop computer with 16GB RAM",
        "max_selections": 3,
        "selected_chapters": ["84", "85"],
        "chapter_confidences": [0.9, 0.7],
        "chapter_reasonings": ["Machinery chapter", "Electrical chapter"],
        "selected_headings_by_chapter": {"84": ["8471"], "85": ["8528"]},
        "heading_confidences_by_chapter": {"84": [0.85], "85": [0.6]},
        "heading_reasonings_by_chapter": {
            "84": ["Data processing"],
            "85": ["Monitors"],
        },
        "selected_subheadings_by_heading": {"8471": ["847130"], "8528": ["852841"]},
        "subheading_confidences_by_heading": {"8471": [0.95], "8528": [0.5]},
        "subheading_reasonings_by_heading": {
            "8471": ["Portable computers"],
            "8528": ["Monitors"],
        },
        "paths": [],
        "overall_strategy": None,
        "final_selected_code": None,
        "final_confidence": None,
        "final_reasoning": None,
        "comparison_summary": None,
    }


# Test utilities


def assert_valid_hs_code(code: str):
    """Assert that a string is a valid HS code format."""
    assert isinstance(code, str), "HS code must be a string"
    assert code.isdigit(), "HS code must contain only digits"
    assert len(code) in [2, 4, 6], "HS code must be 2, 4, or 6 digits"


def assert_confidence_score(score: float):
    """Assert that a confidence score is valid."""
    assert isinstance(score, int | float), "Confidence must be a number"
    assert 0.0 <= score <= 1.0, "Confidence must be between 0.0 and 1.0"


def create_test_classification_result(code: str, confidence: float = 0.9):
    """Create a test classification result."""
    from hs_agent.models import ClassificationLevel, ClassificationResult

    return ClassificationResult(
        level=ClassificationLevel.SUBHEADING,
        selected_code=code,
        description=f"Test description for {code}",
        confidence=confidence,
        reasoning=f"Test classification for {code}",
    )
