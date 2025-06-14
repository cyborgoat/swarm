"""
Main CLI entry point for Swarm.
"""

import typer
from typing import Optional
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

from swarm import __version__
from swarm.core.config import Config
from swarm.cli.commands.research import handle_research
from swarm.cli.commands.interactive import handle_interactive
from swarm.cli.commands.mcp_server import handle_mcp_server

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
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Save results to file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed progress"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode"),
) -> None:
    """🔬 Research a topic using AI and web browsing."""
    config = Config.from_env()
    handle_research(config, query, max_results, output_file, verbose, headless)


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