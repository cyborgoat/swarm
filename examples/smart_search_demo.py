#!/usr/bin/env python3
"""
Demonstration of Swarm's enhanced smart search behavior and visual improvements.

This script shows how the interactive mode now intelligently handles search queries
based on context and provides visual feedback for MCP tool usage.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def main():
    """Demonstrate the enhanced features."""
    console.print(
        Panel(
            Text.assemble(
                ("🐝 Swarm Enhanced Features Demo\n\n", "bold blue"),
                ("This demo showcases the new smart search behavior and visual improvements.", ""),
            ),
            title="Demo",
            border_style="blue",
        )
    )

    # Feature 1: Smart Search Behavior
    console.print("\n[bold cyan]🔍 Feature 1: Smart Search Behavior[/bold cyan]")
    console.print("When you have a current page open and make a search query, Swarm now asks:")

    search_table = Table(show_header=True, header_style="bold magenta")
    search_table.add_column("Option", style="cyan", width=8)
    search_table.add_column("Description", style="white")
    search_table.add_column("Use Case", style="yellow")

    search_table.add_row(
        "1",
        "Search within current page",
        "Find specific content on the page you're viewing"
    )
    search_table.add_row(
        "2",
        "Search web with DuckDuckGo",
        "Start fresh search for new information"
    )
    search_table.add_row(
        "3",
        "Use page's search bar",
        "Utilize the website's own search functionality"
    )

    console.print(search_table)

    # Feature 2: Visual MCP Server
    console.print("\n[bold cyan]⚡ Feature 2: Enhanced MCP Server[/bold cyan]")
    console.print("The MCP server now provides rich visual feedback:")

    mcp_table = Table(show_header=True, header_style="bold magenta")
    mcp_table.add_column("Feature", style="cyan")
    mcp_table.add_column("Description", style="white")

    mcp_table.add_row("Verbose Mode", "Detailed tool listing with categories")
    mcp_table.add_row("Live Status", "Real-time server status display")
    mcp_table.add_row("Tool Categories", "Organized by Session, Navigation, Interaction, Content, Search")
    mcp_table.add_row("Connection Info", "Clear connection details for LLMs")

    console.print(mcp_table)

    # Feature 3: Interactive Mode Improvements
    console.print("\n[bold cyan]🎯 Feature 3: Interactive Mode Enhancements[/bold cyan]")

    interactive_features = [
        "🔍 Smart search context awareness",
        "📊 Enhanced status command showing session details",
        "💡 Improved help system with examples",
        "🎨 Better visual feedback and progress indicators",
        "🤖 Intelligent query routing based on current page",
        "⚙️ Graceful error handling with helpful messages"
    ]

    for feature in interactive_features:
        console.print(f"  • {feature}")

    # Usage Examples
    console.print("\n[bold cyan]📋 Usage Examples[/bold cyan]")

    console.print("\n[bold yellow]1. Start MCP Server with Visual Feedback:[/bold yellow]")
    console.print("   [dim]uv run swarm --verbose mcp-server[/dim]")

    console.print("\n[bold yellow]2. Interactive Mode with Smart Search:[/bold yellow]")
    console.print("   [dim]uv run swarm interactive[/dim]")
    console.print("   [dim]> Browse github.com[/dim]")
    console.print("   [dim]> Search for Python tutorials  # Will ask: page vs web vs search bar[/dim]")

    console.print("\n[bold yellow]3. MCP Tools Available to LLMs:[/bold yellow]")

    tools_table = Table(show_header=True, header_style="bold magenta")
    tools_table.add_column("Category", style="cyan")
    tools_table.add_column("Tools", style="white")

    tools_table.add_row(
        "Session",
        "start_browser_session, close_browser_session, get_session_status"
    )
    tools_table.add_row(
        "Navigation",
        "navigate_to_url, get_current_page_info"
    )
    tools_table.add_row(
        "Interaction",
        "click_element, fill_input_field, select_dropdown_option"
    )
    tools_table.add_row(
        "Content",
        "extract_page_content, get_page_links, get_interactive_elements"
    )
    tools_table.add_row(
        "Search",
        "search_web, search_current_page, search_and_navigate"
    )

    console.print(tools_table)

    # Benefits
    console.print("\n[bold cyan]🎉 Key Benefits[/bold cyan]")

    benefits = [
        "🧠 Context-aware search decisions",
        "👀 Visual feedback for all operations",
        "🔧 15 comprehensive MCP tools for LLMs",
        "🎯 Intelligent query routing",
        "📱 Better user experience with Rich UI",
        "🔄 Persistent browser sessions",
        "⚡ Fast, efficient web automation"
    ]

    for benefit in benefits:
        console.print(f"  • {benefit}")

    console.print(
        Panel(
            Text.assemble(
                ("🚀 Ready to try the enhanced Swarm?\n\n", "bold green"),
                ("Start with: ", ""), ("uv run swarm interactive", "cyan"), (" or ", ""),
                ("uv run swarm --verbose mcp-server", "cyan"),
            ),
            title="Get Started",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
