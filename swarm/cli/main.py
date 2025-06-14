"""
Main CLI entry point for Swarm.
"""


import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from swarm import __version__
from swarm.cli.commands.interactive import handle_interactive
from swarm.cli.commands.mcp_server import handle_mcp_server
from swarm.cli.commands.research import handle_research
from swarm.core.config import Config

app = typer.Typer(
    name="swarm",
    help="🐝 Swarm - AI-powered research assistant with browser automation",
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def research(
    query: str = typer.Argument(..., help="Research query to investigate"),
    max_results: int = typer.Option(10, "--max-results", "-n", help="Maximum search results to analyze"),
    output_file: str | None = typer.Option(None, "--output", "-o", help="Save results to file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed progress"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode"),
    context_size: int | None = typer.Option(None, "--context-size", "-c", help="Override LLM context size (max tokens)"),
    model: str | None = typer.Option(None, "--model", "-m", help="Override LLM model (e.g., llama3.2:latest, gemma3:12b)"),
    include_images: bool = typer.Option(True, "--include-images/--no-images", help="Include images in research results"),
    relevance_threshold: float | None = typer.Option(None, "--relevance-threshold", "-r", help="Minimum relevance score threshold (default: 5.0)"),
    min_word_count: int | None = typer.Option(None, "--min-words", "-w", help="Minimum word count for content (default: 300)"),
    deep_content_limit: int | None = typer.Option(None, "--deep-content", "-d", help="Deep content extraction limit (default: 8192)"),
    language: str | None = typer.Option(None, "--language", "-l", help="Output language: english or chinese (default: english)"),
) -> None:
    """🔬 Research a topic using AI and web browsing."""
    config = Config.from_env()

    # Override configuration with CLI parameters if provided
    if context_size:
        config.llm.max_tokens = context_size
        console.print(f"[dim]🔧 Using custom context size: {context_size} tokens[/dim]")

    if model:
        config.llm.model = model
        console.print(f"[dim]🤖 Using custom model: {model}[/dim]")

    if relevance_threshold is not None:
        config.research.relevance_threshold = relevance_threshold
        console.print(f"[dim]🎯 Using custom relevance threshold: {relevance_threshold}[/dim]")

    if min_word_count is not None:
        config.research.min_word_count = min_word_count
        console.print(f"[dim]📝 Using custom minimum word count: {min_word_count}[/dim]")

    if deep_content_limit is not None:
        config.research.deep_content_limit = deep_content_limit
        console.print(f"[dim]🔍 Using custom deep content limit: {deep_content_limit}[/dim]")

    if language is not None:
        # Validate language parameter
        if language.lower() not in ["english", "chinese"]:
            console.print(f"[red]❌ Invalid language: {language}. Must be 'english' or 'chinese'[/red]")
            raise typer.Exit(1)
        config.research.output_language = language.lower()
        lang_display = "中文" if language.lower() == "chinese" else "English"
        console.print(f"[dim]🌐 Using language: {lang_display}[/dim]")

    handle_research(config, query, max_results, output_file, verbose, headless, include_images)


@app.command()
def interactive(
    use_mcp: bool = typer.Option(True, "--use-mcp/--no-mcp", help="Use MCP server for browser automation"),
    headless: bool = typer.Option(False, "--headless/--no-headless", help="Run browser in headless mode"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
) -> None:
    """🎯 Start interactive research assistant."""
    config = Config.from_env()

    if verbose:
        console.print(f"[dim]Starting interactive mode with MCP: {use_mcp}, Headless: {headless}[/dim]")

    handle_interactive(config, use_mcp=use_mcp, headless=headless, verbose=verbose)


@app.command(name="mcp-server")
def mcp_server(
    port: int = typer.Option(8000, "--port", "-p", help="Server port (ignored for stdio transport)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed server information"),
) -> None:
    """🔧 Start MCP server for LLM integration."""
    config = Config.from_env()
    handle_mcp_server(config, port=port, verbose=verbose)


@app.command()
def version() -> None:
    """Show version information."""
    console.print("🐝 [bold blue]Swarm[/bold blue] v0.1.0")
    console.print("AI-powered research assistant with browser automation")


@app.command()
def info() -> None:
    """Show information about Swarm."""
    console.print(
        Panel(
            Text.assemble(
                ("🐝 Swarm ", "bold blue"),
                f"v{__version__}\n\n",
                ("CLI-based web browsing and automation agent.\n\n", ""),
                ("Features: ", "bold"),
                ("Interactive browsing • LLM integration • MCP server\n\n", "dim"),
                ("Commands:\n", "bold"),
                ("• swarm interactive - Interactive mode\n", "dim"),
                ("• swarm mcp-server - MCP server for LLMs\n", "dim"),
                ("• swarm research <query> - Research topic\n", "dim"),
            ),
            title="About Swarm",
            border_style="blue",
        )
    )


if __name__ == "__main__":
    app()
