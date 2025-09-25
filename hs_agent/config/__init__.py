"""Configuration management for HS Agent.

This module provides centralized configuration management using Pydantic settings.
All configuration should be accessed through the settings instance.

Example:
    from hs_agent.config import settings
    
    # Access configuration
    api_key = settings.google_api_key
    model_name = settings.default_model_name
"""

from hs_agent.config.settings import settings, AgentType, LogLevel

__all__ = ["settings", "AgentType", "LogLevel"]