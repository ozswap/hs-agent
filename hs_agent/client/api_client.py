"""API client for HS Agent FastAPI server.

This module provides a client to interact with the HS Agent API server,
including health checks, classification requests, and error handling.
"""

import asyncio
import time
from typing import Dict, Any, Optional
import httpx
from rich.console import Console

from hs_agent.config import settings, AgentType
from hs_agent.core.logging import get_logger

logger = get_logger(__name__)
console = Console()


class APIConnectionError(Exception):
    """Raised when unable to connect to the API server."""
    pass


class APIHealthError(Exception):
    """Raised when the API server is not healthy."""
    pass


class HSAgentAPIClient:
    """Client for interacting with HS Agent FastAPI server."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        """Initialize the API client.
        
        Args:
            base_url: Base URL for the API server (defaults to settings.api_url)
            timeout: Request timeout in seconds (defaults to settings.api_timeout)
        """
        self.base_url = (base_url or settings.api_url).rstrip('/')
        self.timeout = timeout or settings.api_timeout
        
        # Create HTTP client with timeout configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True
        )
        
        logger.info(
            "🌐 API client initialized",
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    async def check_health(self, raise_on_error: bool = True) -> Dict[str, Any]:
        """Check if the API server is healthy.
        
        Args:
            raise_on_error: Whether to raise an exception if unhealthy
            
        Returns:
            Health check response data
            
        Raises:
            APIConnectionError: If unable to connect to the server
            APIHealthError: If the server is not healthy
        """
        try:
            response = await self.client.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                logger.debug("✅ API health check passed", **health_data)
                return health_data
            else:
                error_msg = f"API health check failed with status {response.status_code}"
                if raise_on_error:
                    raise APIHealthError(error_msg)
                logger.warning(error_msg)
                return {"status": "unhealthy", "error": error_msg}
                
        except httpx.ConnectError as e:
            error_msg = f"Unable to connect to API server at {self.base_url}"
            logger.error(error_msg, error=str(e))
            if raise_on_error:
                raise APIConnectionError(error_msg) from e
            return {"status": "unreachable", "error": error_msg}
        except httpx.TimeoutException as e:
            error_msg = f"API health check timed out after {self.timeout}s"
            logger.error(error_msg, error=str(e))
            if raise_on_error:
                raise APIConnectionError(error_msg) from e
            return {"status": "timeout", "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during health check: {str(e)}"
            logger.error(error_msg, error=str(e))
            if raise_on_error:
                raise APIConnectionError(error_msg) from e
            return {"status": "error", "error": error_msg}
    
    async def classify_product(
        self,
        product_description: str,
        agent_type: Optional[AgentType] = None,
        top_k: Optional[int] = None,
        include_reasoning: bool = True,
        include_candidates: bool = False
    ) -> Dict[str, Any]:
        """Classify a product description using the API.
        
        Args:
            product_description: Description of the product to classify
            agent_type: Agent type to use for classification
            top_k: Number of candidates to consider at each level
            include_reasoning: Include detailed reasoning in response
            include_candidates: Include candidate codes in response
            
        Returns:
            Classification result data
            
        Raises:
            APIConnectionError: If unable to connect to the server
            APIHealthError: If the classification request fails
        """
        # Prepare request data
        request_data = {
            "product_description": product_description,
            "include_reasoning": include_reasoning,
            "include_candidates": include_candidates
        }
        
        if agent_type:
            request_data["agent_type"] = agent_type.value
        if top_k:
            request_data["top_k"] = top_k
        
        try:
            logger.info(
                "🎯 Sending classification request",
                product_description=product_description,
                agent_type=agent_type.value if agent_type else None,
                top_k=top_k
            )
            
            response = await self.client.post(
                f"{self.base_url}/api/classify",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(
                    "✅ Classification completed",
                    final_code=result.get("final_hs_code"),
                    confidence=result.get("overall_confidence")
                )
                return result
            else:
                error_msg = f"Classification request failed with status {response.status_code}"
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                    error_msg += f": {error_detail}"
                except:
                    pass
                logger.error(error_msg)
                raise APIHealthError(error_msg)
                
        except httpx.ConnectError as e:
            error_msg = f"Unable to connect to API server at {self.base_url}"
            logger.error(error_msg, error=str(e))
            raise APIConnectionError(error_msg) from e
        except httpx.TimeoutException as e:
            error_msg = f"Classification request timed out after {self.timeout}s"
            logger.error(error_msg, error=str(e))
            raise APIConnectionError(error_msg) from e
        except APIHealthError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error during classification: {str(e)}"
            logger.error(error_msg, error=str(e))
            raise APIConnectionError(error_msg) from e
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information and configuration.
        
        Returns:
            Server information data
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/info")
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"Server info request failed with status {response.status_code}"
                raise APIHealthError(error_msg)
                
        except httpx.ConnectError as e:
            error_msg = f"Unable to connect to API server at {self.base_url}"
            raise APIConnectionError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error getting server info: {str(e)}"
            raise APIConnectionError(error_msg) from e


def create_api_client(base_url: Optional[str] = None, timeout: Optional[int] = None) -> HSAgentAPIClient:
    """Factory function to create an API client.
    
    Args:
        base_url: Base URL for the API server
        timeout: Request timeout in seconds
        
    Returns:
        Configured API client instance
    """
    return HSAgentAPIClient(base_url=base_url, timeout=timeout)


async def check_api_health(base_url: Optional[str] = None, timeout: int = 10) -> bool:
    """Quick health check for the API server.
    
    Args:
        base_url: Base URL for the API server
        timeout: Request timeout in seconds
        
    Returns:
        True if the server is healthy, False otherwise
    """
    try:
        async with create_api_client(base_url=base_url, timeout=timeout) as client:
            await client.check_health(raise_on_error=True)
            return True
    except (APIConnectionError, APIHealthError):
        return False
    except Exception:
        return False


def display_api_connection_error(base_url: str):
    """Display a helpful error message when API connection fails."""
    console.print("\\n[bold red]❌ Unable to connect to HS Agent API server[/bold red]")
    console.print(f"[dim]Attempted to connect to: {base_url}[/dim]\\n")
    
    console.print("[yellow]🚀 To start the FastAPI server, run one of these commands:[/yellow]")
    console.print("[cyan]   uv run python app.py[/cyan]")
    console.print("[cyan]   uvicorn app:app --host 0.0.0.0 --port 9999 --reload[/cyan]")
    
    console.print("\\n[yellow]💡 Alternative options:[/yellow]")
    console.print("[dim]   • Set HS_AGENT_API_URL environment variable to use a different server[/dim]")
    console.print("[dim]   • Use --local flag to run classification locally (if available)[/dim]")
    console.print("[dim]   • Check if the server is running: curl http://localhost:9999/health[/dim]")