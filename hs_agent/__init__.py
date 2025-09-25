"""HS Agent - Intelligent Harmonized System Code Classification.

This package provides AI-powered classification of product descriptions
into appropriate Harmonized System (HS) codes using hierarchical machine
learning workflows.

Key Features:
- Hierarchical classification (2-digit → 4-digit → 6-digit)
- Multiple AI agent implementations (Traditional Pydantic AI + Modern LangGraph)
- Comprehensive observability with Langfuse integration
- RESTful API and CLI interfaces
- Tax code to HS code mapping workflows

Example Usage:
    from hs_agent import HSDataLoader, HSLangGraphAgent
    
    # Load HS codes data
    loader = HSDataLoader()
    loader.load_all_data()
    
    # Create agent and classify
    agent = HSLangGraphAgent(loader)
    result = await agent.classify_hierarchical("Laptop computer")
    print(f"HS Code: {result['final_code']}")
"""

__version__ = "0.1.0"

# Import key components for easy access
from hs_agent.config import settings
from hs_agent.core.data_loader import HSDataLoader
from hs_agent.core.models import (
    ClassificationRequest,
    ClassificationResponse
)
from hs_agent.core.models.entities import HSCode, TaxCodeEntry
from hs_agent.core.exceptions import (
    HSAgentError,
    ClassificationError,
    DataLoadingError,
    ConfigurationError
)

# Import agents
from hs_agent.agents.langgraph.agents import HSLangGraphAgent
from hs_agent.agents.traditional.agents import HSClassificationAgent

__all__ = [
    # Core components
    "settings",
    "HSDataLoader",
    
    # Models
    "ClassificationRequest",
    "ClassificationResponse", 
    "HSCode",
    "TaxCodeEntry",
    
    # Exceptions
    "HSAgentError",
    "ClassificationError",
    "DataLoadingError",
    "ConfigurationError",
    
    # Agents
    "HSLangGraphAgent",
    "HSClassificationAgent",
    
    # Version
    "__version__"
]