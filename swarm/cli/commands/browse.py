"""
Browse command handler for Swarm.
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from swarm.core.config import Config
from swarm.core.exceptions import SwarmError
from swarm.web.browser import Browser

console = Console()


def handle_browse(config: Config, url: str, verbose: bool = False) -> None:
    """
    Handle the browse command.
    
    Args:
        config: Application configuration
        url: URL to browse
        verbose: Whether to show verbose output
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task(f"Browsing {url}...", total=None)

            browser = Browser(config.browser)
            result = browser.browse(url)

            progress.update(task, completed=True)

        # Display results
        title = result.get('title', 'Untitled Page')
        content_length = len(result.get('content', ''))
        links_count = len(result.get('links', []))

        panel_content = (
            f"[bold green]Successfully browsed:[/bold green] {url}\n\n"
            f"[bold]Title:[/bold] {title}\n"
            f"[bold]Content length:[/bold] {content_length:,} characters\n"
            f"[bold]Links found:[/bold] {links_count}"
        )

        if verbose and result.get('content'):
            preview = result['content'][:300].replace('\n', ' ').strip()
            panel_content += f"\n\n[bold]Content preview:[/bold]\n{preview}..."

        if verbose and result.get('links'):
            panel_content += "\n\n[bold]Top links:[/bold]"
            for i, link in enumerate(result['links'][:5], 1):
                link_text = link.get('text', 'No text')[:40]
                panel_content += f"\n  {i}. {link_text}"

        console.print(Panel(panel_content, title="Browse Results", border_style="green"))

    except SwarmError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if verbose and e.details:
            console.print(f"[dim]Details: {e.details}[/dim]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
