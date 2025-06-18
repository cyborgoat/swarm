"""
Browse command for navigating to URLs.
"""

import asyncio
import logging

from rich.console import Console
from rich.panel import Panel

from swarm.core.config import Config
from swarm.core.exceptions import (
    BrowserError,
    BrowserNavigationError,
    BrowserSessionError,
    SwarmError,
    WebError,
)
from swarm.utils.exception_handler import ExceptionContext, log_exception
from swarm.web.browser import Browser

console = Console()
logger = logging.getLogger(__name__)


def handle_browse(config: Config, url: str, verbose: bool = False) -> None:
    """
    Handle browse command with improved exception handling.

    Args:
        config: Application configuration
        url: URL to browse to
        verbose: Whether to show verbose output
    """
    if verbose:
        logging.basicConfig(level=logging.INFO)

    # Use the new exception context manager
    with ExceptionContext("browse command", reraise=False, log_errors=verbose) as ctx:
        asyncio.run(_async_browse(config, url, verbose))

        # Check if there was an exception and handle it appropriately
        if ctx.exception:
            if isinstance(ctx.exception, BrowserSessionError):
                console.print(f"[red]❌ Browser Session Error: {ctx.exception.message}[/red]")
                if verbose and ctx.exception.details:
                    console.print(f"[dim]Details: {ctx.exception.details}[/dim]")
                console.print("[yellow]💡 Try restarting the browser or checking your system resources.[/yellow]")

            elif isinstance(ctx.exception, BrowserNavigationError):
                console.print(f"[red]❌ Navigation Error: {ctx.exception.message}[/red]")
                if verbose and ctx.exception.url:
                    console.print(f"[dim]URL: {ctx.exception.url}[/dim]")
                console.print("[yellow]💡 Check if the URL is valid and accessible.[/yellow]")

            elif isinstance(ctx.exception, BrowserError):
                console.print(f"[red]❌ Browser Error: {ctx.exception.message}[/red]")
                if verbose and ctx.exception.details:
                    console.print(f"[dim]Details: {ctx.exception.details}[/dim]")

            elif isinstance(ctx.exception, WebError):
                console.print(f"[red]❌ Web Error: {ctx.exception.message}[/red]")
                if verbose and ctx.exception.url:
                    console.print(f"[dim]URL: {ctx.exception.url}[/dim]")
                if verbose and ctx.exception.status_code:
                    console.print(f"[dim]Status Code: {ctx.exception.status_code}[/dim]")

            elif isinstance(ctx.exception, SwarmError):
                console.print(f"[red]❌ {ctx.exception.error_code}: {ctx.exception.message}[/red]")
                if verbose and ctx.exception.details:
                    console.print(f"[dim]Details: {ctx.exception.details}[/dim]")

            else:
                console.print(f"[red]❌ Unexpected error: {str(ctx.exception)}[/red]")
                if verbose:
                    log_exception(ctx.exception, "browse command", include_traceback=True)


async def _async_browse(config: Config, url: str, verbose: bool) -> None:
    """
    Async implementation of browse functionality.

    Args:
        config: Application configuration
        url: URL to browse to
        verbose: Whether to show verbose output
    """
    browser = Browser(config.browser)

    try:
        # Start browser session
        console.print("[yellow]🔄 Starting browser session...[/yellow]")
        session_result = await browser.start_session()

        if verbose:
            console.print(f"[dim]Session: {session_result}[/dim]")

        # Navigate to URL
        console.print(f"[yellow]🌐 Navigating to: {url}[/yellow]")
        nav_result = await browser.navigate_to_url(url)

        # Display success
        console.print(
            Panel.fit(
                f"✅ [bold green]Successfully browsed to:[/bold green]\n"
                f"🌐 **URL:** {nav_result.get('url', url)}\n"
                f"📄 **Title:** {nav_result.get('title', 'Unknown')}\n"
                f"📊 **Status:** {nav_result.get('response_status', 'Unknown')}",
                title="🌐 Browse Complete",
                border_style="green",
            )
        )

        # Get page info if verbose
        if verbose:
            try:
                current_url = await browser.get_current_url()
                page_title = await browser.get_page_title()
                console.print(f"[dim]Current URL: {current_url}[/dim]")
                console.print(f"[dim]Page Title: {page_title}[/dim]")
            except BrowserError as e:
                # Log but don't fail for page info errors
                logger.warning(f"Could not get additional page info: {e.message}")
            except Exception as e:
                # Convert any other exceptions to BrowserError
                logger.warning(f"Could not get additional page info: {e}")

    finally:
        # Always try to close the browser session
        try:
            console.print("[yellow]🔄 Closing browser session...[/yellow]")
            await browser.close_session()
            console.print("[green]✅ Browser session closed[/green]")
        except BrowserSessionError as e:
            # Log but don't fail for cleanup errors
            logger.warning(f"Error during browser cleanup: {e.message}")
            console.print("[yellow]⚠️ Browser session may not have closed properly[/yellow]")
        except Exception as e:
            # Convert any other exceptions to BrowserSessionError for cleanup
            logger.warning(f"Error during browser cleanup: {e}")
            console.print("[yellow]⚠️ Browser session may not have closed properly[/yellow]")
