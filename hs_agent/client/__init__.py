"""API client for HS Agent services.

This module provides client functionality to interact with the HS Agent
FastAPI server, including health checks and classification requests.
"""

from .api_client import HSAgentAPIClient, APIHealthError, APIConnectionError

__all__ = ["HSAgentAPIClient", "APIHealthError", "APIConnectionError"]