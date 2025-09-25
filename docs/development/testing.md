# Testing Guide

## Overview

The HS Agent project uses a comprehensive testing strategy with organized test structure, shared fixtures, and utilities. The refactored testing system provides better organization, reusable components, and clear separation between unit and integration tests.

## 🧪 Testing Structure

### Organized Test Directory

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── fixtures/                # Test data and fixtures
│   ├── sample_data.json
│   └── test_hs_codes.csv
├── unit/                    # Unit tests
│   ├── test_classifier.py
│   ├── test_langfuse.py
│   ├── test_search_fix.py
│   ├── test_simple.py
│   ├── test_hs_lookup.py
│   ├── test_edge_cases.py
│   └── test_6digit_search.py
└── integration/             # Integration tests
    ├── test_batch_mapping.py
    └── test_single_mapping.py
```

### Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and workflows
- **Fixtures**: Reusable test data and mock objects

## 🚀 Quick Start

### Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_classifier.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=hs_agent --cov-report=html
```

### Test Configuration

The `conftest.py` file provides shared configuration and fixtures:

```python
# tests/conftest.py
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to Python path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hs_agent.config import settings
from hs_agent.core.models import HSCode, TaxCodeEntry
```

## 🔧 Shared Fixtures

### Configuration Fixtures

```python
@pytest.fixture(scope="session")
def test_settings():
    """Provide test-specific settings."""
    test_env = {
        "GOOGLE_API_KEY": "test_api_key_for_testing",
        "LANGFUSE_SECRET_KEY": "test_secret_key",
        "DEBUG_MODE": "true",
        "LOG_LEVEL": "DEBUG"
    }
    
    with patch.dict(os.environ, test_env):
        yield settings
```

### Data Fixtures

```python
@pytest.fixture
def sample_hs_codes():
    """Provide sample HS codes for testing."""
    return [
        HSCode(
            code="84",
            description="Nuclear reactors, boilers, machinery",
            level=2,
            section="XVI"
        ),
        HSCode(
            code="8471",
            description="Automatic data processing machines",
            level=4,
            parent="84"
        ),
        HSCode(
            code="847130",
            description="Portable digital automatic data processing machines",
            level=6,
            parent="8471"
        )
    ]

@pytest.fixture
def sample_tax_codes():
    """Provide sample tax codes for testing."""
    return [
        TaxCodeEntry(
            avalara_code="PC040100",
            description="Personal computers and laptops",
            additional_info="Including accessories"
        )
    ]
```

### Mock Fixtures

```python
@pytest.fixture
def mock_data_loader():
    """Provide a mock data loader for testing."""
    mock_loader = Mock()
    
    # Mock the codes dictionaries
    mock_loader.codes_2digit = {
        "84": HSCode(code="84", description="Machinery", level=2)
    }
    mock_loader.codes_6digit = {
        "847130": HSCode(code="847130", description="Portable computers", level=6)
    }
    
    # Mock methods
    mock_loader.get_codes_by_level.side_effect = lambda level: {
        2: mock_loader.codes_2digit,
        6: mock_loader.codes_6digit
    }[level]
    
    return mock_loader

@pytest.fixture
def mock_agent():
    """Provide a mock agent for testing."""
    mock_agent = Mock()
    
    mock_agent.classify_hierarchical.return_value = {
        "chapter": Mock(selected_code="84", confidence=0.9),
        "heading": Mock(selected_code="8471", confidence=0.85),
        "subheading": Mock(selected_code="847130", confidence=0.95),
        "final_code": "847130",
        "overall_confidence": 0.9
    }
    
    return mock_agent
```

## 📝 Writing Tests

### Unit Test Example

```python
# tests/unit/test_data_loader.py
import pytest
from unittest.mock import patch, Mock
from hs_agent.core.data_loader import HSDataLoader
from hs_agent.core.exceptions import DataLoadingError

class TestHSDataLoader:
    """Test suite for HSDataLoader."""
    
    def test_initialization(self, test_settings):
        """Test data loader initialization."""
        loader = HSDataLoader()
        
        assert loader.data_dir == test_settings.data_directory
        assert loader.hs_codes_file == test_settings.hs_codes_file
        assert not loader.is_loaded
    
    def test_load_data_success(self, temp_data_dir, mock_pandas_read_csv):
        """Test successful data loading."""
        with patch('hs_agent.core.data_loader.settings') as mock_settings:
            mock_settings.data_directory = temp_data_dir
            mock_settings.hs_codes_file = "hs_codes_all.csv"
            
            loader = HSDataLoader()
            loader.load_all_data()
            
            assert loader.is_loaded
            assert len(loader.codes_2digit) > 0
            assert loader.loading_time_ms is not None
    
    def test_load_data_file_not_found(self, temp_data_dir):
        """Test data loading with missing file."""
        with patch('hs_agent.core.data_loader.settings') as mock_settings:
            mock_settings.data_directory = temp_data_dir
            mock_settings.hs_codes_file = "nonexistent.csv"
            
            loader = HSDataLoader()
            
            with pytest.raises(DataLoadingError) as exc_info:
                loader.load_data()
            
            assert "HS codes file not found" in str(exc_info.value)
    
    def test_get_codes_by_level(self, sample_hs_codes):
        """Test getting codes by level."""
        loader = HSDataLoader()
        loader.codes_2digit = {"84": sample_hs_codes[0]}
        loader.codes_6digit = {"847130": sample_hs_codes[2]}
        loader._data_loaded = True
        
        codes_2digit = loader.get_codes_by_level(2)
        codes_6digit = loader.get_codes_by_level(6)
        
        assert "84" in codes_2digit
        assert "847130" in codes_6digit
    
    def test_get_codes_invalid_level(self):
        """Test getting codes with invalid level."""
        loader = HSDataLoader()
        loader._data_loaded = True
        
        with pytest.raises(ValidationError):
            loader.get_codes_by_level(8)
```

### Integration Test Example

```python
# tests/integration/test_classification_workflow.py
import pytest
import asyncio
from hs_agent.core.data_loader import HSDataLoader
from hs_agent.agents.langgraph.agents import HSLangGraphAgent

class TestClassificationWorkflow:
    """Integration tests for complete classification workflow."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_classification(self, test_settings, temp_data_dir):
        """Test complete classification workflow."""
        # Setup
        loader = HSDataLoader()
        loader.load_all_data()
        
        agent = HSLangGraphAgent(loader)
        
        # Execute
        result = await agent.classify_hierarchical(
            "Laptop computer with 16GB RAM"
        )
        
        # Verify
        assert "final_code" in result
        assert result["final_code"].isdigit()
        assert len(result["final_code"]) == 6
        assert 0.0 <= result["overall_confidence"] <= 1.0
        assert "chapter" in result
        assert "heading" in result
        assert "subheading" in result
    
    @pytest.mark.asyncio
    async def test_batch_classification(self, mock_agent):
        """Test batch classification workflow."""
        products = [
            "Laptop computer",
            "Cotton t-shirt",
            "Fresh apples"
        ]
        
        results = []
        for product in products:
            result = await mock_agent.classify_hierarchical(product)
            results.append(result)
        
        assert len(results) == 3
        for result in results:
            assert "final_code" in result
            assert "overall_confidence" in result
```

### Testing with Mocks

```python
# tests/unit/test_agents.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from hs_agent.agents.langgraph.agents import HSLangGraphAgent

class TestHSLangGraphAgent:
    """Test suite for HSLangGraphAgent."""
    
    @patch('hs_agent.agents.langgraph.agents.ChatVertexAI')
    def test_agent_initialization(self, mock_chat_vertex, mock_data_loader, test_settings):
        """Test agent initialization."""
        agent = HSLangGraphAgent(mock_data_loader)
        
        assert agent.data_loader == mock_data_loader
        assert agent.model_name == test_settings.default_model_name
        mock_chat_vertex.assert_called_once()
    
    @patch('hs_agent.agents.langgraph.agents.ChatVertexAI')
    def test_agent_initialization_failure(self, mock_chat_vertex, mock_data_loader):
        """Test agent initialization failure."""
        mock_chat_vertex.side_effect = Exception("API connection failed")
        
        with pytest.raises(AgentError) as exc_info:
            HSLangGraphAgent(mock_data_loader)
        
        assert "Failed to initialize LangGraph agent" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_classify_hierarchical_success(self, mock_agent, mock_llm_response):
        """Test successful hierarchical classification."""
        # Mock LLM responses
        with patch.object(mock_agent, 'ranking_model') as mock_ranking:
            with patch.object(mock_agent, 'selection_model') as mock_selection:
                mock_ranking.ainvoke = AsyncMock(return_value=mock_llm_response["ranking_response"])
                mock_selection.ainvoke = AsyncMock(return_value=mock_llm_response["selection_response"])
                
                result = await mock_agent.classify_hierarchical("Test product")
                
                assert result["final_code"] == "847130"
                assert result["overall_confidence"] > 0.0
```

## 🔍 Test Utilities

### Assertion Helpers

```python
# tests/conftest.py
def assert_valid_hs_code(code: str):
    """Assert that a string is a valid HS code format."""
    assert isinstance(code, str), "HS code must be a string"
    assert code.isdigit(), "HS code must contain only digits"
    assert len(code) in [2, 4, 6], "HS code must be 2, 4, or 6 digits"

def assert_confidence_score(score: float):
    """Assert that a confidence score is valid."""
    assert isinstance(score, (int, float)), "Confidence must be a number"
    assert 0.0 <= score <= 1.0, "Confidence must be between 0.0 and 1.0"

def create_test_classification_result(code: str, confidence: float = 0.9):
    """Create a test classification result."""
    from hs_agent.core.models import ClassificationResult
    
    return ClassificationResult(
        selected_code=code,
        confidence=confidence,
        reasoning=f"Test classification for {code}"
    )
```

### Test Data Factories

```python
# tests/fixtures/factories.py
from hs_agent.core.models.entities import HSCode, TaxCodeEntry

class HSCodeFactory:
    """Factory for creating test HS codes."""
    
    @staticmethod
    def create_chapter(code: str = "84", description: str = "Machinery") -> HSCode:
        return HSCode(
            code=code,
            description=description,
            level=2,
            section="XVI"
        )
    
    @staticmethod
    def create_subheading(code: str = "847130", parent: str = "8471") -> HSCode:
        return HSCode(
            code=code,
            description="Portable computers",
            level=6,
            parent=parent,
            section="XVI"
        )

class TaxCodeFactory:
    """Factory for creating test tax codes."""
    
    @staticmethod
    def create_computer_tax_code() -> TaxCodeEntry:
        return TaxCodeEntry(
            avalara_code="PC040100",
            description="Personal computers and laptops",
            additional_info="Including accessories"
        )
```

## 🎯 Testing Best Practices

### Test Organization

1. **Group related tests** in classes
2. **Use descriptive test names** that explain what is being tested
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **Keep tests independent** and isolated

### Mocking Guidelines

1. **Mock external dependencies** (APIs, databases, file systems)
2. **Use fixtures for reusable mocks**
3. **Verify mock interactions** when relevant
4. **Don't over-mock** - test real logic when possible

### Test Data Management

1. **Use factories** for creating test objects
2. **Keep test data minimal** but realistic
3. **Use temporary directories** for file operations
4. **Clean up resources** after tests

### Async Testing

```python
# Mark async tests
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None

# Use AsyncMock for async mocks
from unittest.mock import AsyncMock

mock_function = AsyncMock(return_value="test_result")
```

## 🔧 Test Configuration

### Pytest Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --disable-warnings
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests that may take longer to run
    external: Tests that require external services
```

### Coverage Configuration

```ini
# .coveragerc
[run]
source = hs_agent
omit = 
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

## 🚀 Running Tests in CI/CD

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.12]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run tests
      env:
        GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
      run: |
        pytest --cov=hs_agent --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

## 🐛 Debugging Tests

### Running Specific Tests

```bash
# Run single test
pytest tests/unit/test_classifier.py::TestClassifier::test_initialization

# Run tests matching pattern
pytest -k "test_classification"

# Run tests with specific marker
pytest -m unit

# Run failed tests only
pytest --lf
```

### Debug Mode

```bash
# Run with debug output
pytest -s -vv

# Drop into debugger on failure
pytest --pdb

# Set breakpoints in code
import pdb; pdb.set_trace()
```

### Test Output

```bash
# Capture print statements
pytest -s

# Show local variables on failure
pytest --tb=long

# Generate HTML report
pytest --html=report.html
```

## 📚 Related Documentation

- [Configuration Guide](../getting-started/configuration.md) - Test configuration
- [Contributing Guide](contributing.md) - Development workflow
- [CLI Usage](../user-guide/cli-usage.md) - Testing CLI commands
- [API Reference](../api-reference/core/models.md) - Model testing