# Refactored Code Structure

## Overview

The HS Agent codebase has been comprehensively refactored to improve readability, maintainability, and developer experience. This document explains the new structure and the reasoning behind the architectural decisions.

## 🎯 Refactor Goals

The refactor focused on:

- **Centralized Configuration**: Single source of truth for all settings
- **Standardized Error Handling**: Consistent error patterns across modules
- **Enhanced Logging**: Rich, structured logging with observability
- **Organized Models**: Clear separation of data models by purpose
- **Clean Project Structure**: Proper organization of tests, scripts, and documentation
- **Unified Interfaces**: Consistent CLI and API patterns

## 📁 New Directory Structure

```
hs-agent/
├── hs_agent/                   # Main package
│   ├── __init__.py            # Package exports and version
│   ├── cli.py                 # Unified CLI interface
│   │
│   ├── config/                # Configuration management
│   │   ├── __init__.py        # Configuration exports
│   │   └── settings.py        # Pydantic settings with validation
│   │
│   ├── core/                  # Core functionality
│   │   ├── __init__.py
│   │   ├── data_loader.py     # Enhanced data loading with error handling
│   │   ├── exceptions.py      # Standardized exception hierarchy
│   │   ├── logging.py         # Rich logging system
│   │   │
│   │   └── models/            # Organized data models
│   │       ├── __init__.py    # Model exports
│   │       ├── classification.py  # Classification-specific models
│   │       ├── entities.py    # Domain entities (HSCode, TaxCode, etc.)
│   │       ├── requests.py    # API request models
│   │       └── responses.py   # API response models
│   │
│   ├── agents/                # AI agent implementations
│   │   ├── __init__.py
│   │   ├── langgraph/         # LangGraph-based agents
│   │   │   ├── __init__.py
│   │   │   ├── agents.py      # Updated with centralized config
│   │   │   ├── classifier.py
│   │   │   └── models.py
│   │   │
│   │   └── traditional/       # Pydantic AI agents
│   │       ├── __init__.py
│   │       ├── agents.py      # Updated with centralized config
│   │       └── classifier.py
│   │
│   ├── interfaces/            # User interfaces
│   │   ├── __init__.py
│   │   ├── api/               # FastAPI interfaces
│   │   │   ├── __init__.py
│   │   │   ├── langgraph.py
│   │   │   └── traditional.py
│   │   │
│   │   └── cli/               # CLI interfaces (legacy)
│   │       ├── __init__.py
│   │       ├── langgraph.py
│   │       └── traditional.py
│   │
│   └── workflows/             # High-level workflows
│       ├── __init__.py
│       ├── hs_classification/
│       └── tax_code_mapper.py
│
├── tests/                     # Organized test structure
│   ├── conftest.py           # Pytest configuration and fixtures
│   ├── fixtures/             # Test data and fixtures
│   ├── unit/                 # Unit tests
│   │   ├── test_classifier.py
│   │   ├── test_langfuse.py
│   │   ├── test_search_fix.py
│   │   ├── test_simple.py
│   │   ├── test_hs_lookup.py
│   │   ├── test_edge_cases.py
│   │   └── test_6digit_search.py
│   │
│   └── integration/          # Integration tests
│       ├── test_batch_mapping.py
│       └── test_single_mapping.py
│
├── scripts/                  # Utility and debug scripts
│   ├── debug_search.py
│   ├── debug_computer_detailed.py
│   ├── debug_candidates.py
│   ├── debug_computer.py
│   ├── debug_6digit.py
│   ├── debug_full_flow.py
│   └── debug_flow.py
│
├── docs/                     # Documentation
├── data/                     # HS codes datasets
├── static/                   # Web dashboard assets
├── .env.example             # Environment configuration template
├── pyproject.toml           # Updated with new CLI commands
└── README.md
```

## 🔧 Key Components Explained

### Configuration Management (`hs_agent/config/`)

**Purpose**: Centralized, validated configuration management

```python
# hs_agent/config/settings.py
class HSAgentSettings(BaseSettings):
    # API Keys and Authentication
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    langfuse_secret_key: Optional[str] = Field(None, env="LANGFUSE_SECRET_KEY")
    
    # Model Configuration
    default_model_name: str = Field("gemini-2.5-flash-lite", env="DEFAULT_MODEL_NAME")
    default_agent_type: AgentType = Field(AgentType.LANGGRAPH, env="DEFAULT_AGENT_TYPE")
    
    # Data Configuration
    data_directory: Path = Field(Path("data"), env="DATA_DIRECTORY")
    
    # Performance Configuration
    enable_caching: bool = Field(True, env="ENABLE_CACHING")
    max_concurrent_requests: int = Field(10, env="MAX_CONCURRENT_REQUESTS")
```

**Benefits**:
- Type-safe configuration with automatic validation
- Environment variable support with defaults
- Comprehensive documentation for all settings
- Single source of truth for all configuration

### Error Handling (`hs_agent/core/exceptions.py`)

**Purpose**: Standardized exception hierarchy with structured error information

```python
class HSAgentError(Exception):
    """Base exception with structured error details."""
    
    def __init__(self, message: str, error_code: str = None, 
                 details: Dict[str, Any] = None, cause: Exception = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause

class ClassificationError(HSAgentError):
    """Raised when HS code classification fails."""
    pass

class DataLoadingError(HSAgentError):
    """Raised when data loading fails."""
    pass
```

**Benefits**:
- Consistent error messages across all modules
- Structured error details for debugging
- Clear error categorization
- Better API error responses

### Logging System (`hs_agent/core/logging.py`)

**Purpose**: Rich, structured logging with observability integration

```python
class HSAgentLogger:
    """Centralized logger with rich formatting and structured logging."""
    
    def __init__(self, name: str = "hs_agent"):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        # Rich console handler with beautiful formatting
        console_handler = RichHandler(
            console=Console(stderr=True),
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True
        )
```

**Benefits**:
- Beautiful console output with Rich formatting
- Structured logging for better debugging
- Integration with observability tools
- Configurable log levels and outputs

### Organized Models (`hs_agent/core/models/`)

**Purpose**: Clear separation of data models by purpose

#### Entities (`entities.py`)
Domain objects representing core business concepts:
```python
class HSCode(BaseModel):
    """Represents an HS code with metadata and validation."""
    code: str = Field(..., min_length=2, max_length=10)
    description: str = Field(..., min_length=1)
    level: int = Field(..., ge=2, le=6)
    parent: Optional[str] = None
    section: Optional[str] = None
```

#### Requests (`requests.py`)
API and CLI request models:
```python
class ClassificationRequest(BaseModel):
    """Request for single product HS code classification."""
    product_description: str = Field(..., min_length=3, max_length=1000)
    agent_type: Optional[AgentType] = None
    top_k: Optional[int] = Field(None, ge=1, le=50)
    include_reasoning: bool = True
```

#### Responses (`responses.py`)
API and CLI response models:
```python
class ClassificationResponse(BaseModel):
    """Response for single product HS code classification."""
    product_description: str
    final_hs_code: str
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float
    agent_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
```

**Benefits**:
- Clear separation of concerns
- Comprehensive validation
- Better API documentation
- Improved code organization

### Enhanced Data Loading (`hs_agent/core/data_loader.py`)

**Purpose**: Robust data loading with comprehensive error handling

```python
class HSDataLoader:
    """Enhanced HS codes data loader with caching and error handling."""
    
    def __init__(self):
        # Use centralized configuration
        self.data_dir = settings.data_directory
        self.hs_codes_file = settings.hs_codes_file
        
    def load_all_data(self) -> None:
        """Load all HS codes data with comprehensive error handling."""
        try:
            self._validate_data_files()
            self._load_hierarchical_codes()
            self._load_examples()
            self._validate_loaded_data()
        except Exception as e:
            raise DataLoadingError(
                message=f"Failed to load HS codes data: {str(e)}",
                error_code="DATA_LOADING_FAILED",
                details={"data_dir": str(self.data_dir)},
                cause=e
            )
```

**Benefits**:
- Comprehensive error handling and validation
- Performance monitoring and logging
- Data integrity checks
- Caching support for improved performance

### Unified CLI Interface (`hs_agent/cli.py`)

**Purpose**: Single, comprehensive CLI with rich formatting

```python
@app.command()
def classify(
    product_description: str = typer.Argument(...),
    agent_type: AgentType = typer.Option(None, "--agent", "-a"),
    top_k: int = typer.Option(None, "--top-k", "-k"),
    verbose: bool = typer.Option(False, "--verbose", "-v")
):
    """🎯 Classify a product description into an HS code."""
    
    # Beautiful progress indicators
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("📊 Loading HS codes data...", total=None)
        # ... classification logic
    
    # Rich formatted output
    display_classification_result(result, product_description, processing_time)
```

**Benefits**:
- Consistent user experience across all operations
- Beautiful terminal output with Rich formatting
- Comprehensive help and documentation
- Health checks and configuration display

## 🔄 Migration from Old Structure

### Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| **Configuration** | Scattered across files | Centralized in `config/settings.py` |
| **Error Handling** | Inconsistent patterns | Standardized exception hierarchy |
| **Logging** | Basic print statements | Rich, structured logging |
| **Models** | Single `models.py` file | Organized by purpose in `models/` |
| **Tests** | Scattered in root | Organized in `tests/` directory |
| **CLI** | Multiple scattered commands | Unified `hs-agent` interface |
| **Documentation** | Basic docstrings | Comprehensive documentation |

### Migration Guide

#### For Users
1. **CLI Commands**: Use new unified interface
   ```bash
   # Old
   hs-langgraph-classify "product description"
   
   # New
   hs-agent classify "product description" --agent langgraph
   ```

2. **Configuration**: Environment variables remain the same
   ```bash
   # Still works
   export GOOGLE_API_KEY="your-key"
   export LANGFUSE_SECRET_KEY="your-key"
   ```

#### For Developers
1. **Imports**: Use new organized imports
   ```python
   # Old
   from hs_agent.core.models import ClassificationResult
   
   # New (still works, but more specific imports available)
   from hs_agent.core.models.classification import ClassificationResult
   from hs_agent.core.models.entities import HSCode
   ```

2. **Error Handling**: Use new exception hierarchy
   ```python
   # New
   from hs_agent.core.exceptions import ClassificationError, DataLoadingError
   
   try:
       result = await agent.classify_hierarchical(description)
   except ClassificationError as e:
       logger.error(f"Classification failed: {e.message}")
       print(f"Error details: {e.details}")
   ```

3. **Configuration**: Use centralized settings
   ```python
   # New
   from hs_agent.config import settings
   
   print(f"Using model: {settings.default_model_name}")
   print(f"Data directory: {settings.data_directory}")
   ```

## 🎯 Benefits Realized

### Immediate Benefits
- ✅ **Much more readable code** with clear organization
- ✅ **Consistent error handling** across all modules
- ✅ **Centralized configuration** eliminates scattered settings
- ✅ **Better developer experience** with rich CLI and logging
- ✅ **Organized project structure** improves maintainability

### Long-term Benefits
- 🚀 **Faster development** with better tooling and structure
- 🛡️ **More reliable** with comprehensive error handling
- 📊 **Better observability** with structured logging
- 🔧 **Easier maintenance** with clear separation of concerns
- 📚 **Better documentation** with comprehensive docstrings

## 🔮 Future Enhancements

The refactored structure provides a solid foundation for future improvements:

### Phase 2: Core Architecture Unification
- Unified agent interface with pluggable implementations
- Enhanced data layer with repository pattern
- Performance optimizations and caching

### Phase 3: Interface Standardization
- Consolidated API endpoints
- Enhanced testing infrastructure
- Comprehensive documentation

### Phase 4: Advanced Features
- Plugin architecture
- Advanced monitoring and metrics
- Performance optimizations

## 📚 Related Documentation

- [Configuration Guide](../getting-started/configuration.md) - Detailed configuration options
- [CLI Usage](../user-guide/cli-usage.md) - Using the new unified CLI
- [API Reference](../api-reference/core/models.md) - Complete model documentation
- [Development Guide](../development/contributing.md) - Contributing to the project