"""
Research command - Thin wrapper around the research module.
"""

import asyncio
from typing import Optional
from rich.console import Console
from rich.panel import Panel

from swarm.core.config import Config
from swarm.research import ResearchAssistant

console = Console()


async def handle_research_async(
    config: Config,
    query: str,
    max_results: int = 8,
    output_file: Optional[str] = None,
    verbose: bool = False,
    headless: bool = True,
    include_images: bool = True
) -> None:
    """
    Conduct comprehensive research on a topic.
    
    Args:
        config: Application configuration
        query: Research query
        max_results: Maximum search results to analyze
        output_file: Optional file to save results (auto-generates if None)
        verbose: Show detailed progress
        headless: Run browser in headless mode
        include_images: Include image detection functionality
    """
    # Override browser headless setting
    config.browser.headless = headless
    
    # Initialize research assistant
    research_assistant = ResearchAssistant(
        config=config,
        verbose=verbose,
        include_images=include_images
    )
    
    try:
        # Conduct research
        research_data = await research_assistant.conduct_research(
            query=query,
            max_sources=max_results
        )
        
        # Display results
        research_assistant.display_results(research_data)
        
        # Generate markdown report
        markdown_report = research_assistant.generate_markdown_report(research_data)
        
        # Save results
        if output_file:
            # User provided filename
            if not output_file.endswith('.md'):
                output_file += '.md'
            save_filename = output_file
        else:
            # Auto-generate filename
            save_filename = research_assistant.get_auto_filename()
            console.print(f"[dim]📝 Auto-generating filename: {save_filename}[/dim]")
        
        # Write markdown report to file
        with open(save_filename, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        console.print(f"[green]💾 Report saved to: {save_filename}[/green]")
        
        # Display final completion message
        analysis_results = research_data.get('analysis_results', [])
        console.print(Panel.fit(
            f"✅ [bold green]Research Complete![/bold green]\n"
            f"📊 Sources analyzed: {len(analysis_results)}\n"
            f"🎯 High relevance sources: {sum(1 for r in analysis_results if r.relevance_score >= config.research.relevance_threshold)}\n"
            f"🖼️ Images found: {len(research_data.get('images_found', []))}\n"
            f"🌐 Language: {config.research.output_language}\n"
            f"📝 Report saved: {save_filename}",
            title="🏆 Mission Accomplished",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[red]❌ Research failed: {str(e)}[/red]")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
    finally:
        # Cleanup
        await research_assistant.cleanup()


def handle_research(
    config: Config,
    query: str,
    max_results: int = 8,
    output_file: Optional[str] = None,
    verbose: bool = False,
    headless: bool = True,
    include_images: bool = True
) -> None:
    """
    Synchronous wrapper for research function.
    """
    try:
        asyncio.run(handle_research_async(
            config=config,
            query=query,
            max_results=max_results,
            output_file=output_file,
            verbose=verbose,
            headless=headless,
            include_images=include_images
        ))
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Research interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Research execution failed: {str(e)}[/red]")


# Direct execution support
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Swarm Research Assistant")
    parser.add_argument("query", help="Research query")
    parser.add_argument("--max-results", type=int, default=5, help="Maximum sources to analyze")
    parser.add_argument("--output", help="Output file path (.md extension auto-added)")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")
    parser.add_argument("--include-images", action="store_true", default=True, help="Include image detection")
    
    args = parser.parse_args()
    
    config = Config.from_env()
    handle_research(
        config=config,
        query=args.query,
        max_results=args.max_results,
        output_file=args.output,
        verbose=args.verbose,
        headless=args.headless,
        include_images=args.include_images
    ) 