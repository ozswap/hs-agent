"""Unified CLI interface for HS Agent.

This module provides a single, consistent command-line interface for all
HS Agent operations, replacing the scattered CLI commands with a unified approach.
"""

import asyncio
import time
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from hs_agent.config import settings, AgentType
from hs_agent.core.logging import logger, log_classification_start, log_classification_complete
from hs_agent.core.exceptions import HSAgentError
from hs_agent.core.data_loader import HSDataLoader
from hs_agent.agents.langgraph.agents import HSLangGraphAgent
from hs_agent.agents.traditional.agents import HSClassificationAgent
from hs_agent.client.api_client import (
    HSAgentAPIClient, 
    APIConnectionError, 
    APIHealthError, 
    display_api_connection_error,
    check_api_health
)

# Initialize CLI app and console
app = typer.Typer(
    name="hs-agent",
    help="🎯 HS Agent - Intelligent Harmonized System Code Classification",
    rich_markup_mode="rich"
)
console = Console()


async def should_use_local_mode() -> bool:
    """Determine if we should use local mode or API mode.
    
    Returns True if we should use local agents, False if we should use API.
    """
    # If explicitly set to use local mode
    if settings.use_local_mode:
        return True
    
    # Check if API server is available
    try:
        is_healthy = await check_api_health(settings.api_url, timeout=5)
        return not is_healthy  # Use local if API is not healthy
    except Exception:
        return True  # Use local if we can't check API health


def create_agent(agent_type: AgentType, data_loader: HSDataLoader):
    """Create an agent instance based on the specified type."""
    try:
        if agent_type == AgentType.LANGGRAPH:
            return HSLangGraphAgent(data_loader)
        elif agent_type == AgentType.TRADITIONAL:
            return HSClassificationAgent(data_loader)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    except Exception as e:
        console.print(f"[red]❌ Failed to create {agent_type} agent: {str(e)}[/red]")
        raise typer.Exit(1)


def display_classification_result(result: dict, product_description: str, processing_time: float):
    """Display classification results in a formatted table."""
    
    # Create main result panel
    result_panel = Panel(
        f"[bold green]✅ Classification Complete[/bold green]\\n\\n"
        f"[bold]Product:[/bold] {product_description}\\n"
        f"[bold]Final HS Code:[/bold] [cyan]{result['final_code']}[/cyan]\\n"
        f"[bold]Confidence:[/bold] {result['overall_confidence']:.2%}\\n"
        f"[bold]Processing Time:[/bold] {processing_time:.2f}s",
        title="🎯 HS Classification Result",
        border_style="green"
    )
    console.print(result_panel)
    
    # Create hierarchical breakdown table
    table = Table(title="📊 Hierarchical Classification Breakdown")
    table.add_column("Level", style="cyan", no_wrap=True)
    table.add_column("Code", style="magenta")
    table.add_column("Confidence", style="green")
    table.add_column("Reasoning", style="white")
    
    # Add chapter result
    if "chapter" in result:
        chapter = result["chapter"]
        table.add_row(
            "Chapter (2-digit)",
            chapter.selected_code,
            f"{chapter.confidence:.2%}",
            chapter.reasoning[:80] + "..." if len(chapter.reasoning) > 80 else chapter.reasoning
        )
    
    # Add heading result
    if "heading" in result:
        heading = result["heading"]
        table.add_row(
            "Heading (4-digit)",
            heading.selected_code,
            f"{heading.confidence:.2%}",
            heading.reasoning[:80] + "..." if len(heading.reasoning) > 80 else heading.reasoning
        )
    
    # Add subheading result
    if "subheading" in result:
        subheading = result["subheading"]
        table.add_row(
            "Subheading (6-digit)",
            subheading.selected_code,
            f"{subheading.confidence:.2%}",
            subheading.reasoning[:80] + "..." if len(subheading.reasoning) > 80 else subheading.reasoning
        )
    
    console.print(table)


def _classify_sync(
    product_description: str,
    agent_type: Optional[AgentType] = None,
    top_k: Optional[int] = None,
    verbose: bool = False,
    local: bool = False
):
    """Synchronous wrapper for classify command."""
    return asyncio.run(_classify_async(
        product_description, agent_type, top_k, verbose, local
    ))


async def _classify_async(
    product_description: str,
    agent_type: Optional[AgentType] = None,
    top_k: Optional[int] = None,
    verbose: bool = False,
    local: bool = False
):
    """Async implementation of classify command."""
    # Use configured defaults if not specified
    agent_type = agent_type or settings.default_agent_type
    top_k = top_k or settings.default_top_k
    
    console.print(f"[bold blue]🎯 HS Agent Classification[/bold blue]")
    console.print(f"[dim]Agent: {agent_type.value} | Top-K: {top_k}[/dim]\\n")
    
    try:
        # Determine if we should use local mode
        use_local = local or (await should_use_local_mode())
        
        if use_local:
            await _classify_local_mode(product_description, agent_type, top_k, verbose)
        else:
            await _classify_api_mode(product_description, agent_type, top_k, verbose)
            
    except (APIConnectionError, APIHealthError) as e:
        console.print(f"[red]❌ API Error: {str(e)}[/red]")
        display_api_connection_error(settings.api_url)
        
        # Offer to retry in local mode
        if not local:
            console.print("\\n[yellow]🔄 Retrying in local mode...[/yellow]")
            try:
                await _classify_local_mode(product_description, agent_type, top_k, verbose)
            except Exception as local_e:
                console.print(f"[red]❌ Local classification also failed: {str(local_e)}[/red]")
                raise typer.Exit(1)
        else:
            raise typer.Exit(1)
            
    except HSAgentError as e:
        console.print(f"[red]❌ Classification failed: {e.message}[/red]")
        if verbose:
            console.print(f"[dim]Error details: {e.details}[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {str(e)}[/red]")
        logger.exception("Unexpected error during classification")
        raise typer.Exit(1)


@app.command()
def classify(
    product_description: str = typer.Argument(..., help="Product description to classify"),
    agent_type: AgentType = typer.Option(
        None,
        "--agent",
        "-a",
        help="Agent type to use for classification"
    ),
    top_k: int = typer.Option(
        None,
        "--top-k",
        "-k",
        help="Number of candidates to consider at each level"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    ),
    local: bool = typer.Option(
        False,
        "--local",
        "-l",
        help="Force local mode (bypass API server)"
    )
):
    """🎯 Classify a product description into an HS code.
    
    This command performs hierarchical HS code classification using AI agents
    to determine the most appropriate 6-digit Harmonized System code.
    
    Examples:
        hs-agent classify "Laptop computer with 16GB RAM"
        hs-agent classify "Cotton t-shirt" --agent langgraph
        hs-agent classify "Fresh apples" --top-k 5 --verbose
    """
    return _classify_sync(product_description, agent_type, top_k, verbose, local)


async def _classify_api_mode(
    product_description: str, 
    agent_type: AgentType, 
    top_k: int, 
    verbose: bool
):
    """Perform classification using the API server."""
    console.print("[dim]🌐 Using API server mode[/dim]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Check API health
        task = progress.add_task("🏥 Checking API server health...", total=None)
        
        async with HSAgentAPIClient() as client:
            health = await client.check_health()
            progress.update(task, description="✅ API server is healthy")
            
            # Perform classification
            progress.update(task, description="🔍 Classifying product via API...")
            
            start_time = time.time()
            result = await client.classify_product(
                product_description=product_description,
                agent_type=agent_type,
                top_k=top_k,
                include_reasoning=True
            )
            processing_time = time.time() - start_time
            
            progress.update(task, description="✅ Classification completed")
    
    # Convert API response to local format for display
    display_result = {
        "final_code": result["final_hs_code"],
        "overall_confidence": result["overall_confidence"],
        "chapter": result.get("chapter_result"),
        "heading": result.get("heading_result"),
        "subheading": result.get("subheading_result")
    }
    
    # Log and display results
    log_classification_start(product_description, agent_type.value)
    log_classification_complete(
        product_description,
        result["final_hs_code"],
        result["overall_confidence"],
        result["processing_time_ms"]
    )
    
    display_classification_result(display_result, product_description, processing_time)
    
    if verbose:
        console.print(f"\\n[dim]🌐 API URL: {settings.api_url}[/dim]")
        console.print(f"[dim]⏱️ Server processing time: {result['processing_time_ms']:.1f}ms[/dim]")
        console.print("\\n[dim]💡 Use --local to force local mode[/dim]")


async def _classify_local_mode(
    product_description: str, 
    agent_type: AgentType, 
    top_k: int, 
    verbose: bool
):
    """Perform classification using local agents."""
    console.print("[dim]🏠 Using local agent mode[/dim]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Load data
        task = progress.add_task("📊 Loading HS codes data...", total=None)
        data_loader = HSDataLoader()
        data_loader.load_all_data()
        progress.update(task, description="✅ Data loaded successfully")
        
        # Create agent
        progress.update(task, description=f"🤖 Initializing {agent_type.value} agent...")
        agent = create_agent(agent_type, data_loader)
        progress.update(task, description="✅ Agent initialized")
        
        # Perform classification
        progress.update(task, description="🔍 Classifying product...")
        
    # Log classification start
    log_classification_start(product_description, agent_type.value)
    
    # Run classification
    start_time = time.time()
    result = await agent.classify_hierarchical(product_description, top_k=top_k)
    processing_time = time.time() - start_time
    
    # Log classification complete
    log_classification_complete(
        product_description,
        result["final_code"],
        result["overall_confidence"],
        processing_time * 1000
    )
    
    # Display results
    display_classification_result(result, product_description, processing_time)
    
    if verbose:
        console.print("\\n[dim]🏠 Local mode - agents running directly[/dim]")
        console.print("\\n[dim]💡 Use --help for more options[/dim]")


@app.command()
def config(
    show_all: bool = typer.Option(
        False,
        "--all",
        help="Show all configuration values"
    )
):
    """⚙️ Display current configuration settings.
    
    Shows the current HS Agent configuration, including API keys (masked),
    model settings, and data paths.
    """
    
    console.print("[bold blue]⚙️ HS Agent Configuration[/bold blue]\\n")
    
    # Create configuration table
    table = Table(title="Current Settings")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_column("Source", style="dim")
    
    # Core settings
    table.add_row(
        "Default Agent Type",
        settings.default_agent_type.value,
        "config"
    )
    table.add_row(
        "Default Model",
        settings.default_model_name,
        "config"
    )
    table.add_row(
        "Data Directory",
        str(settings.data_directory),
        "config"
    )
    table.add_row(
        "Log Level",
        settings.log_level.value,
        "config"
    )
    
    # API Keys (masked)
    if settings.google_api_key:
        google_key = settings.google_api_key
        masked_google_key = f"{google_key[:8]}...{google_key[-4:]}" if len(google_key) > 12 else "***"
        table.add_row(
            "Google API Key",
            masked_google_key,
            "environment"
        )
    else:
        table.add_row(
            "Google API Key",
            "[red]Not configured[/red]",
            "environment"
        )
    
    # API Configuration
    table.add_row(
        "API Server URL",
        settings.api_url,
        "config"
    )
    
    table.add_row(
        "Use Local Mode",
        "✅ Yes" if settings.use_local_mode else "❌ No",
        "config"
    )
    
    if settings.langfuse_enabled:
        table.add_row(
            "Langfuse Enabled",
            "✅ Yes",
            "config"
        )
        table.add_row(
            "Langfuse Host",
            settings.langfuse_host,
            "environment"
        )
    else:
        table.add_row(
            "Langfuse Enabled",
            "❌ No",
            "config"
        )
    
    if show_all:
        # Add more detailed settings
        table.add_row("API Host", settings.api_host, "config")
        table.add_row("API Port", str(settings.api_port), "config")
        table.add_row("Cache Enabled", "✅ Yes" if settings.enable_caching else "❌ No", "config")
        table.add_row("Debug Mode", "✅ Yes" if settings.debug_mode else "❌ No", "config")
    
    console.print(table)
    
    if not show_all:
        console.print("\\n[dim]💡 Use --all to see all configuration options[/dim]")


def _health_sync():
    """Synchronous wrapper for health command."""
    return asyncio.run(_health_async())


async def _health_async():
    """Async implementation of health command."""
    console.print("[bold blue]🏥 HS Agent Health Check[/bold blue]\\n")
    
    health_status = True
    
    # Check API server first
    try:
        console.print("🌐 API Server... ", end="")
        is_healthy = await check_api_health(settings.api_url, timeout=10)
        if is_healthy:
            console.print(f"[green]✅ OK ({settings.api_url})[/green]")
            
            # Get detailed server info if available
            try:
                async with HSAgentAPIClient() as client:
                    server_info = await client.get_server_info()
                    console.print(f"[dim]   Server version: {server_info.get('version', 'unknown')}[/dim]")
                    console.print(f"[dim]   Data loaded: {server_info.get('data_statistics', {}).get('subheadings', 'unknown')} codes[/dim]")
            except Exception:
                pass
        else:
            console.print(f"[yellow]⚠️ UNAVAILABLE ({settings.api_url})[/yellow]")
            console.print("[dim]   Will fall back to local mode[/dim]")
    except Exception as e:
        console.print(f"[red]❌ FAILED: {str(e)}[/red]")
        console.print("[dim]   Will fall back to local mode[/dim]")
    
    # Check configuration
    try:
        console.print("⚙️ Configuration... ", end="")
        # Basic configuration validation
        if settings.google_api_key and settings.google_api_key != "your_google_api_key_here":
            console.print("[green]✅ OK[/green]")
        else:
            console.print("[yellow]⚠️ Google API key not configured[/yellow]")
            health_status = False
        
        if not settings.data_directory.exists():
            console.print(f"[red]❌ Data directory not found: {settings.data_directory}[/red]")
            health_status = False
    except Exception as e:
        console.print(f"[red]❌ FAILED: {str(e)}[/red]")
        health_status = False
    
    # Check data files (local mode)
    try:
        console.print("📊 Data files (local)... ", end="")
        data_loader = HSDataLoader()
        data_loader.load_all_data()
        stats = data_loader.data_statistics
        console.print(f"[green]✅ OK ({stats['subheadings']} codes loaded)[/green]")
    except Exception as e:
        console.print(f"[red]❌ FAILED: {str(e)}[/red]")
        health_status = False
    
    # Check agent initialization (local mode)
    try:
        console.print("🤖 Local agents... ", end="")
        agent = create_agent(settings.default_agent_type, data_loader)
        console.print("[green]✅ OK[/green]")
    except Exception as e:
        console.print(f"[red]❌ FAILED: {str(e)}[/red]")
        health_status = False
    
    # Overall status
    console.print()
    if health_status:
        console.print("[bold green]🎉 All systems operational![/bold green]")
        console.print("[dim]Both API and local modes are available[/dim]")
    else:
        console.print("[bold yellow]⚠️ Some issues detected.[/bold yellow]")
        console.print("[dim]Check configuration and ensure the API server is running[/dim]")
        console.print("[dim]Use 'hs-agent serve' to start the server[/dim]")
        raise typer.Exit(1)


@app.command()
def health():
    """🏥 Check system health and connectivity.
    
    Performs health checks on the HS Agent system, including:
    - Configuration validation
    - Data file accessibility
    - External service connectivity
    """
    return _health_sync()


@app.command()
def serve(
    host: str = typer.Option(
        None,
        "--host",
        "-h",
        help="Host to bind the server to"
    ),
    port: int = typer.Option(
        None,
        "--port",
        "-p",
        help="Port to bind the server to"
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Enable auto-reload for development"
    ),
    workers: int = typer.Option(
        None,
        "--workers",
        "-w",
        help="Number of worker processes"
    )
):
    """🚀 Start the HS Agent API server.
    
    Starts the FastAPI server for HS code classification and tax code mapping.
    The server provides REST API endpoints for classification and a web dashboard.
    
    Examples:
        hs-agent serve                    # Start with default settings
        hs-agent serve --port 8080        # Start on port 8080
        hs-agent serve --host 127.0.0.1   # Bind to localhost only
        hs-agent serve --reload           # Enable auto-reload for development
    """
    import uvicorn
    
    # Use provided values or fall back to settings
    server_host = host or settings.api_host
    server_port = port or settings.api_port
    server_workers = workers or settings.api_workers
    
    console.print(f"[bold blue]🚀 Starting HS Agent API Server[/bold blue]")
    console.print(f"[dim]Host: {server_host} | Port: {server_port} | Workers: {server_workers}[/dim]\\n")
    
    try:
        console.print(f"[green]✅ Server starting at http://{server_host}:{server_port}[/green]")
        console.print(f"[dim]📊 Dashboard: http://{server_host}:{server_port}/dashboard[/dim]")
        console.print(f"[dim]📚 API docs: http://{server_host}:{server_port}/docs[/dim]")
        console.print(f"[dim]🏥 Health check: http://{server_host}:{server_port}/health[/dim]")
        console.print("\\n[yellow]Press Ctrl+C to stop the server[/yellow]\\n")
        
        # Start the server
        uvicorn.run(
            "app:app",
            host=server_host,
            port=server_port,
            workers=server_workers if not reload else 1,  # Workers don't work with reload
            reload=reload,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        console.print("\\n[yellow]🛑 Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Failed to start server: {str(e)}[/red]")
        logger.exception("Server startup failed")
        raise typer.Exit(1)


@app.command()
def version():
    """📋 Show version information."""
    from hs_agent import __version__
    
    console.print(f"[bold blue]HS Agent v{__version__}[/bold blue]")
    console.print(f"Configuration: {settings.default_agent_type.value} agent")
    console.print(f"Model: {settings.default_model_name}")
    console.print(f"Default API: http://{settings.api_host}:{settings.api_port}")


def main():
    """Main entry point for the CLI."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\\n[yellow]⚠️ Operation cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {str(e)}[/red]")
        logger.exception("Unexpected CLI error")
        raise typer.Exit(1)


if __name__ == "__main__":
    main()