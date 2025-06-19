"""
Streaming utilities for managing real-time LLM output display.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


@asynccontextmanager
async def streaming_display(
    title: str = "🤖 AI Processing",
    console: Console | None = None,
    border_style: str = "cyan",
    show_completion: bool = True,
    clear_after: bool = True
) -> AsyncGenerator[tuple[callable, callable], None]:
    """
    Context manager for streaming LLM output display.
    
    Args:
        title: Title for the streaming panel
        console: Rich console for display
        border_style: Border style for the panel
        show_completion: Whether to show completion message
        clear_after: Whether to clear display after completion
        
    Yields:
        Tuple of (update_function, get_text_function)
    """
    if console is None:
        console = Console()
        
    accumulated_text = ""
    display_text = Text()
    
    def update_display(new_token: str) -> None:
        """Update the streaming display with new token."""
        nonlocal accumulated_text, display_text
        accumulated_text += new_token
        display_text = Text(accumulated_text)
        
    def get_accumulated_text() -> str:
        """Get the accumulated text."""
        return accumulated_text
    
    # Start the live display
    with Live(
        Panel(display_text, title=title, border_style=border_style),
        console=console,
        refresh_per_second=10,
        transient=clear_after
    ) as live:
        
        # Provide update function to caller
        def live_update(token: str) -> None:
            update_display(token)
            live.update(Panel(display_text, title=title, border_style=border_style))
            
        try:
            yield live_update, get_accumulated_text
        finally:
            # Show completion and optionally clear
            if show_completion:
                if clear_after:
                    console.clear()
                console.print(f"[green]✅ {title} - Complete[/green]")


class StreamingCollector:
    """Collects streaming tokens and manages display updates."""
    
    def __init__(self, update_callback: callable):
        self.accumulated_text = ""
        self.update_callback = update_callback
        
    def add_token(self, token: str) -> None:
        """Add a new token to the stream."""
        self.accumulated_text += token
        self.update_callback(token)
        
    def get_text(self) -> str:
        """Get the complete accumulated text."""
        return self.accumulated_text
        
    def clear(self) -> None:
        """Clear the accumulated text."""
        self.accumulated_text = ""


async def stream_with_delay(tokens: list[str], delay: float = 0.05) -> AsyncGenerator[str, None]:
    """
    Stream tokens with a delay for visual effect.
    
    Args:
        tokens: List of tokens to stream
        delay: Delay between tokens in seconds
        
    Yields:
        Individual tokens
    """
    for token in tokens:
        yield token
        await asyncio.sleep(delay) 