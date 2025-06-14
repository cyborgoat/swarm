"""
Search command handler for Swarm.
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from swarm.core.config import Config
from swarm.core.exceptions import SwarmError
from swarm.web.search import WebSearch

console = Console()


def handle_search(config: Config, query: str, verbose: bool = False) -> None:
    """
    Handle the search command.
    
    Args:
        config: Application configuration
        query: Search query
        verbose: Whether to show verbose output
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task(f"Searching for '{query}'...", total=None)

            search = WebSearch(config.search)
            results = search.search(query)

            progress.update(task, completed=True)

        # Display results
        if results:
            table = Table(title=f"Search Results for '{query}'", show_lines=True)
            table.add_column("Title", style="bold blue", no_wrap=False, max_width=50)
            table.add_column("URL", style="cyan", no_wrap=False, max_width=60)

            if verbose:
                table.add_column("Description", style="dim", no_wrap=False, max_width=40)

            for result in results[:config.search.results_limit]:
                title = result.get('title', 'N/A')[:100]
                url = result.get('url', 'N/A')

                row = [title, url]
                if verbose:
                    description = result.get('description', 'N/A')[:80] + "..."
                    row.append(description)

                table.add_row(*row)

            console.print(table)
        else:
            console.print(
                Panel(
                    f"No results found for '{query}'\n\n"
                    f"Try different search terms or check your internet connection.",
                    title="Search Results",
                    border_style="yellow",
                )
            )

    except SwarmError as e:
        console.print(f"[red]Search Error: {e.message}[/red]")
        if verbose and e.details:
            console.print(f"[dim]Details: {e.details}[/dim]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
