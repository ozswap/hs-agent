"""Unified CLI for HS Agent using Typer."""

import asyncio
import logging
import os
import sys
import warnings

import typer
from rich.console import Console
from rich.table import Table

# Enable LangChain/LangGraph OpenTelemetry tracing (LangSmith OTEL) early.
# Per Logfire docs (https://logfire.pydantic.dev/docs/integrations/llms/langchain/),
# these env vars must be set before importing langchain/langgraph.
os.environ.setdefault("LANGSMITH_OTEL_ENABLED", "true")
os.environ.setdefault("LANGSMITH_TRACING", "true")

# Suppress noisy LangSmith 401 / upload-failure logs (we don't have LangSmith API key)
logging.getLogger("langsmith.client").setLevel(logging.CRITICAL)
logging.getLogger("langsmith.utils").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", message=".*LangSmithAuthError.*")
warnings.filterwarnings("ignore", message=".*Failed to multipart ingest runs.*")

# Imports must come after env var setup for LangSmith OTEL tracing
from hs_agent.agent import HSAgent  # noqa: E402
from hs_agent.config.settings import settings  # noqa: E402
from hs_agent.data_loader import HSDataLoader  # noqa: E402

app = typer.Typer(
    name="hs-agent", help="AI-powered HS code classification service", add_completion=False
)
console = Console()


def print_single_result(result):
    """Print single classification result in a nice format."""
    console.print("\n" + "=" * 80, style="bold blue")
    console.print(f"Product: {result.product_description}", style="bold")
    console.print("=" * 80, style="bold blue")

    console.print(f"\n📊 CHAPTER: [bold cyan]{result.chapter.selected_code}[/bold cyan]")
    console.print(f"   Confidence: [green]{result.chapter.confidence:.2f}[/green]")
    console.print(f"   Reasoning: {result.chapter.reasoning[:100]}...")

    console.print(f"\n📋 HEADING: [bold cyan]{result.heading.selected_code}[/bold cyan]")
    console.print(f"   Confidence: [green]{result.heading.confidence:.2f}[/green]")
    console.print(f"   Reasoning: {result.heading.reasoning[:100]}...")

    console.print(f"\n🎯 SUBHEADING: [bold cyan]{result.subheading.selected_code}[/bold cyan]")
    console.print(f"   Confidence: [green]{result.subheading.confidence:.2f}[/green]")
    console.print(f"   Reasoning: {result.subheading.reasoning[:100]}...")

    console.print(f"\n✅ FINAL HS CODE: [bold green]{result.final_code}[/bold green]")
    console.print(
        f"🎯 OVERALL CONFIDENCE: [bold yellow]{result.overall_confidence:.2f}[/bold yellow]"
    )
    console.print(f"⏱️  Processing time: [dim]{result.processing_time_ms:.0f}ms[/dim]")
    console.print("=" * 80 + "\n", style="bold blue")


def print_multi_result(result):
    """Print multi-choice classification result in a nice format."""
    console.print("\n" + "=" * 80, style="bold magenta")
    console.print(f"Product: {result.product_description}", style="bold")
    console.print(f"Strategy: {result.overall_strategy}", style="dim")
    console.print("=" * 80, style="bold magenta")

    for i, path in enumerate(result.paths, 1):
        console.print(f"\n🔹 Path {i}:", style="bold cyan")
        console.print(f"   Chapter:    {path.chapter_code}")
        console.print(f"   Heading:    {path.heading_code}")
        console.print(f"   Subheading: [bold green]{path.subheading_code}[/bold green]")
        console.print(f"   Confidence: [yellow]{path.path_confidence:.2f}[/yellow]")
        console.print(f"   Chapter reasoning:    {path.chapter_reasoning[:80]}...")
        console.print(f"   Heading reasoning:    {path.heading_reasoning[:80]}...")
        console.print(f"   Subheading reasoning: {path.subheading_reasoning[:80]}...")

    console.print(f"\n⏱️  Processing time: [dim]{result.processing_time_ms:.0f}ms[/dim]")
    console.print("=" * 80 + "\n", style="bold magenta")


@app.command()
def classify(
    product_description: str = typer.Argument(..., help="Product description to classify"),
):
    """
    Classify a product description to a single HS code (one-to-one).

    Example:
        hs-agent classify "laptop computer"
    """

    async def run():
        with console.status("[bold green]Initializing HS Agent..."):
            loader = HSDataLoader()
            loader.load_all_data()
            agent = HSAgent(loader)

        console.print(f"\n[bold]Classifying:[/bold] {product_description}\n")

        with console.status("[bold yellow]Processing..."):
            result = await agent.classify(product_description)

        print_single_result(result)

    asyncio.run(run())


@app.command()
def classify_multi(
    product_description: str = typer.Argument(..., help="Product description to classify"),
    max_selections: int = typer.Option(
        3, "--max-selections", "-m", help="Maximum number of codes to select at each level (1 to N)"
    ),
):
    """
    Classify a product description to 1-N possible HS codes (one-to-many).

    Example:
        hs-agent classify-multi "cotton shirt" --max-selections 3
    """

    async def run():
        with console.status("[bold green]Initializing HS Agent..."):
            loader = HSDataLoader()
            loader.load_all_data()
            agent = HSAgent(loader)

        console.print(f"\n[bold]Multi-classifying:[/bold] {product_description}")
        console.print(f"[dim]Max selections per level: {max_selections}[/dim]\n")

        with console.status("[bold yellow]Processing multiple paths..."):
            result = await agent.classify_multi(product_description, max_selections=max_selections)

        print_multi_result(result)

    asyncio.run(run())


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(None, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
):
    """
    Start the FastAPI server.

    Example:
        hs-agent serve --port 8080 --reload
    """
    import uvicorn

    from hs_agent.config.settings import settings

    actual_port = port if port is not None else settings.api_port

    console.print("\n[bold green]Starting HS Agent API server...[/bold green]")
    console.print(f"  Host: {host}")
    console.print(f"  Port: {actual_port}")
    console.print(
        f"  Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{actual_port}/docs\n"
    )

    uvicorn.run("app:app", host=host, port=actual_port, reload=reload)


@app.command()
def health():
    """
    Check the health status of the HS Agent system.

    Example:
        hs-agent health
    """

    async def run():
        try:
            with console.status("[bold green]Checking system health..."):
                loader = HSDataLoader()
                loader.load_all_data()
                agent = HSAgent(loader)

            table = Table(
                title="HS Agent Health Status", show_header=True, header_style="bold magenta"
            )
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Details", style="dim")

            table.add_row("System", "✅ Healthy", "All components initialized")
            table.add_row("Model", "✅ Ready", settings.default_model_name)
            table.add_row("Chapters", "✅ Loaded", str(len(agent.data_loader.codes_2digit)))
            table.add_row("Headings", "✅ Loaded", str(len(agent.data_loader.codes_4digit)))
            table.add_row("Subheadings", "✅ Loaded", str(len(agent.data_loader.codes_6digit)))

            console.print()
            console.print(table)
            console.print()

        except Exception as e:
            console.print("\n[bold red]❌ Health Check Failed[/bold red]")
            console.print(f"Error: {e}\n")
            sys.exit(1)

    asyncio.run(run())


@app.command()
def config():
    """
    Display current configuration settings.

    Example:
        hs-agent config
    """
    table = Table(title="HS Agent Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Default Model", settings.default_model_name)
    table.add_row("API Port", str(settings.api_port))
    table.add_row("Max Output Paths", str(settings.max_output_paths))
    table.add_row("Logfire Enabled", str(settings.logfire_enabled))
    if settings.logfire_enabled:
        table.add_row("Logfire Service", settings.logfire_service_name)
        if settings.logfire_environment:
            table.add_row("Logfire Environment", settings.logfire_environment)

    console.print()
    console.print(table)
    console.print()


def main():
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
