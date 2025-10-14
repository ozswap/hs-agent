"""Centralized configuration settings for HS Agent.

This module defines all configuration settings using Pydantic Settings,
providing validation, type checking, and environment variable support.
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from enum import Enum


class AgentType(str, Enum):
    """Available agent implementations."""
    TRADITIONAL = "traditional"
    LANGGRAPH = "langgraph"


class LogLevel(str, Enum):
    """Available log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class HSAgentSettings(BaseSettings):
    """Main configuration settings for HS Agent.
    
    All settings can be overridden via environment variables.
    For example, GOOGLE_API_KEY environment variable will override google_api_key.
    """
    
    # === API Keys and Authentication ===
    google_api_key: Optional[str] = Field(
        None,
        description="Google API key for Vertex AI/Gemini models",
        env="GOOGLE_API_KEY"
    )
    
    langfuse_secret_key: Optional[str] = Field(
        None,
        description="Langfuse secret key for observability",
        env="LANGFUSE_SECRET_KEY"
    )
    
    langfuse_public_key: Optional[str] = Field(
        None,
        description="Langfuse public key for observability",
        env="LANGFUSE_PUBLIC_KEY"
    )
    
    langfuse_host: str = Field(
        "https://cloud.langfuse.com",
        description="Langfuse host URL",
        env="LANGFUSE_HOST"
    )
    
    # === Model Configuration ===
    default_model_name: str = Field(
        "gemini-2.5-flash",
        description="Default model name for classification",
        env="DEFAULT_MODEL_NAME"
    )
    
    fallback_model_name: str = Field(
        "gemini-2.5-flash",
        description="Fallback model if default fails",
        env="FALLBACK_MODEL_NAME"
    )
    
    # === Agent Configuration ===
    default_agent_type: AgentType = Field(
        AgentType.LANGGRAPH,
        description="Default agent implementation to use",
        env="DEFAULT_AGENT_TYPE"
    )
    
    default_top_k: int = Field(
        10,
        description="Default number of candidates to consider",
        env="DEFAULT_TOP_K",
        ge=1,
        le=50
    )
    
    root_directory: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent,
        description="Root directory of the project",
        env="ROOT_DIRECTORY"
    )
    
    # === Data Configuration ===
    data_directory: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent / "data",
        description="Directory containing HS codes data",
        env="DATA_DIRECTORY"
    )

    config_directory: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent / "configs",
        description="Directory containing configuration files",
        env="CONFIG_DIRECTORY"
    )
    
    hs_codes_file: str = Field(
        "hs_codes_all.csv",
        description="HS codes CSV file name",
        env="HS_CODES_FILE"
    )
    
    examples_file: str = Field(
        "hs6_examples_cleaned.csv",
        description="Product examples CSV file name",
        env="EXAMPLES_FILE"
    )
    
    tax_codes_file: str = Field(
        "avalara_tax_codes.xlsx",
        description="Avalara tax codes Excel file name",
        env="TAX_CODES_FILE"
    )
    
    # === API Configuration ===
    api_host: str = Field(
        "0.0.0.0",
        description="API server host",
        env="API_HOST"
    )
    
    api_port: int = Field(
        9999,
        description="API server port",
        env="API_PORT",
        ge=1,
        le=65535
    )
    
    api_workers: int = Field(
        1,
        description="Number of API workers",
        env="API_WORKERS",
        ge=1
    )
    
    # === CLI API Client Configuration ===
    api_base_url: str = Field(
        "http://localhost:9999",
        description="Base URL for HS Agent API server",
        env="HS_AGENT_API_URL"
    )
    
    api_timeout: int = Field(
        300,
        description="API client timeout in seconds",
        env="API_TIMEOUT",
        ge=10
    )
    
    use_local_mode: bool = Field(
        False,
        description="Use local agents instead of API client",
        env="USE_LOCAL_MODE"
    )
    
    # === Performance Configuration ===
    enable_caching: bool = Field(
        True,
        description="Enable data caching for performance",
        env="ENABLE_CACHING"
    )
    
    cache_ttl_seconds: int = Field(
        3600,
        description="Cache TTL in seconds",
        env="CACHE_TTL_SECONDS",
        ge=60
    )
    
    max_concurrent_requests: int = Field(
        10,
        description="Maximum concurrent classification requests",
        env="MAX_CONCURRENT_REQUESTS",
        ge=1
    )

    max_output_paths: int = Field(
        20,
        description="Maximum number of classification paths to return in multi-choice mode",
        env="MAX_OUTPUT_PATHS",
        ge=1,
        le=100
    )

    request_timeout_seconds: int = Field(
        300,
        description="Request timeout in seconds",
        env="REQUEST_TIMEOUT_SECONDS",
        ge=30
    )
    
    # === Logging Configuration ===
    log_level: LogLevel = Field(
        LogLevel.INFO,
        description="Logging level",
        env="LOG_LEVEL"
    )
    
    enable_langfuse_logging: bool = Field(
        True,
        description="Enable Langfuse observability logging",
        env="ENABLE_LANGFUSE_LOGGING"
    )
    
    log_file: Optional[Path] = Field(
        None,
        description="Log file path (if None, logs to console)",
        env="LOG_FILE"
    )
    
    # === Development Configuration ===
    debug_mode: bool = Field(
        False,
        description="Enable debug mode",
        env="DEBUG_MODE"
    )
    
    development_mode: bool = Field(
        False,
        description="Enable development mode features",
        env="DEVELOPMENT_MODE"
    )
    
    @field_validator("data_directory")
    @classmethod
    def validate_data_directory(cls, v):
        """Ensure data directory exists."""
        if not v.exists():
            raise ValueError(f"Data directory does not exist: {v}")
        return v
    
    @field_validator("google_api_key")
    @classmethod
    def validate_google_api_key(cls, v):
        """Validate Google API key if provided."""
        if v and v == "your_google_api_key_here":
            raise ValueError(
                "Please replace 'your_google_api_key_here' with a real Google API key. "
                "Get your API key from: https://aistudio.google.com/app/apikey"
            )
        return v
    
    @property
    def google_api_enabled(self) -> bool:
        """Check if Google API is properly configured."""
        return (
            self.google_api_key is not None and
            self.google_api_key != "" and
            self.google_api_key != "your_google_api_key_here"
        )
    
    @property
    def langfuse_enabled(self) -> bool:
        """Check if Langfuse is properly configured."""
        return (
            self.enable_langfuse_logging and
            self.langfuse_secret_key is not None and
            self.langfuse_public_key is not None
        )
    
    @property
    def hs_codes_path(self) -> Path:
        """Full path to HS codes file."""
        return self.data_directory / self.hs_codes_file
    
    @property
    def examples_path(self) -> Path:
        """Full path to examples file."""
        return self.data_directory / self.examples_file
    
    @property
    def tax_codes_path(self) -> Path:
        """Full path to tax codes file."""
        return self.data_directory / self.tax_codes_file
    
    @property
    def api_url(self) -> str:
        """Full API URL for client connections."""
        return self.api_base_url.rstrip('/')
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "validate_assignment": True,
    }


# Global settings instance
settings = HSAgentSettings()