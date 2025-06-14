"""MCP Server command for exposing browser tools to LLMs."""

import os
import signal
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from swarm.core.config import Config
from swarm.mcp_tools.server import create_mcp_server

console = Console()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    console.print("\n[yellow]🛑 Received shutdown signal, stopping MCP Server...[/yellow]")
    sys.exit(0)


def handle_mcp_server(config: Config, port: int = 8000, verbose: bool = False) -> None:
    """
    Start the consolidated MCP server to expose browser automation tools to LLMs.
    
    Args:
        config: Application configuration
        port: Port parameter (ignored - FastMCP uses stdio transport)
        verbose: Whether to show verbose output
    """
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Set environment variable to indicate MCP tools are being used
    os.environ["SWARM_USE_MCP"] = "true"

    console.print(
        Panel(
            Text.assemble(
                ("🐝 Starting Consolidated Swarm MCP Server\n\n", "bold blue"),
                ("This server exposes browser automation tools that LLMs can use:\n", ""),
                ("• Session Management • Navigation • Interaction\n", "dim"),
                ("• Content Extraction • Search • Screenshots\n", "dim"),
                ("\nLLMs connect via Model Context Protocol (stdio transport).", "yellow"),
            ),
            title="Consolidated MCP Server",
            border_style="blue",
        )
    )

    try:
        mcp_server = create_mcp_server(config)
        console.print("[green]🚀 Consolidated MCP Server starting...[/green]")

        if verbose:
            # Show available tools in a compact table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Tool Name", style="cyan", no_wrap=True)
            table.add_column("Description", style="white")
            table.add_column("Category", style="yellow")

            tools_info = [
                ("start_browser_session", "Start persistent browser session", "Session"),
                ("close_browser_session", "Close browser and cleanup", "Session"),
                ("get_session_status", "Check current session status", "Session"),
                ("navigate_to_url", "Browse to specific URL", "Navigation"),
                ("extract_page_content", "Get page content (20K chars)", "Content"),
                ("click_element", "Click element by visible text", "Interaction"),
                ("fill_input_field", "Fill form fields by label", "Interaction"),
                ("search_web", "DuckDuckGo web search", "Search"),
                ("get_page_elements", "Get clickable elements", "Content"),
                ("take_screenshot", "Take page screenshot", "Content"),
            ]

            for tool_name, description, category in tools_info:
                table.add_row(tool_name, description, category)

            console.print("\n[bold cyan]Available MCP Tools:[/bold cyan]")
            console.print(table)
            console.print(f"[dim]Total: {len(tools_info)} tools available[/dim]")

        console.print("\n[bold green]✅ Consolidated MCP Server is running![/bold green]")
        console.print("[cyan]🔗 LLMs connect via stdio transport[/cyan]")
        console.print("[yellow]💡 Press Ctrl+C to stop[/yellow]")

        if verbose:
            console.print("\n[bold cyan]Integration Examples:[/bold cyan]")
            console.print('[dim]Claude Desktop: "swarm-browser": {"command": "uv", "args": ["run", "swarm", "mcp-server"]}[/dim]')

        # Configure logging for MCP server
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)
        logger.info("🚀 Consolidated MCP Server configured with logging")

        # Run the server (stdio transport) - this blocks until interrupted
        mcp_server.run()

    except KeyboardInterrupt:
        console.print("\n[yellow]🛑 MCP Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
    finally:
        console.print("[green]Thanks for using Swarm! 🐝[/green]")
