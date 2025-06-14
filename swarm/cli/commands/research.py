"""Enhanced Research command for comprehensive topic investigation with detailed progress reporting."""

import asyncio
from typing import Optional
from rich.console import Console
from rich.panel import Panel

from swarm.core.config import Config
from swarm.web.browser import Browser
from swarm.web.search import WebSearch
from swarm.llm.client import LLMClient
from swarm.cli.commands.research_assistant import EnhancedResearchAssistant

console = Console()


async def handle_research_async(
    config: Config,
    query: str,
    max_results: int = 8,
    output_file: Optional[str] = None,
    verbose: bool = False,
    headless: bool = True
) -> None:
    """
    Conduct comprehensive research on a topic with detailed step-by-step analysis.
    
    Args:
        config: Application configuration
        query: Research query
        max_results: Maximum search results to analyze (default: 8)
        output_file: Optional file to save results
        verbose: Show detailed progress
        headless: Run browser in headless mode
    """
    console.print(
        Panel(
            f"🔬 [bold cyan]Enhanced Research Assistant[/bold cyan]\n"
            f"📋 Query: [yellow]{query}[/yellow]\n"
            f"🎯 Max Sources: {max_results}\n"
            f"💾 Output File: {output_file or 'Console only'}\n"
            f"🔧 Mode: {'Headless' if headless else 'Visible'} Browser\n"
            f"📊 Verbose: {'Enabled' if verbose else 'Disabled'}",
            title="🤖 Research Configuration",
            border_style="blue",
        )
    )
    
    try:
        # Initialize components with enhanced configuration
        browser_config = config.browser
        browser_config.headless = headless
        
        console.print("[dim]🔧 Initializing research components...[/dim]")
        
        browser = Browser(browser_config)
        search = WebSearch(config.search)
        llm_client = LLMClient(config.llm)
        
        # Create enhanced research assistant
        research_assistant = EnhancedResearchAssistant(
            browser=browser,
            search=search,
            llm_client=llm_client,
            verbose=verbose,
            use_mcp=False  # Direct browser usage for research command
        )
        
        if verbose:
            console.print("[dim]✅ All components initialized successfully[/dim]")
        
        # Conduct comprehensive research
        console.print("\n" + "="*80)
        console.print("[bold green]🚀 Starting Enhanced Research Process[/bold green]")
        console.print("="*80 + "\n")
        
        research_results = await research_assistant.conduct_comprehensive_research(
            query=query,
            max_sources=max_results
        )
        
        # Save results to file if requested
        if output_file:
            await save_research_results(research_results, output_file, query)
            console.print(f"\n[green]💾 Complete research results saved to: {output_file}[/green]")
        
        # Display final statistics
        console.print("\n" + "="*80)
        console.print(Panel.fit(
            f"✅ [bold green]Research Mission Accomplished![/bold green]\n\n"
            f"📊 [bold]Final Statistics:[/bold]\n"
            f"🔍 Search Results Found: {len(research_results.get('search_results', []))}\n"
            f"📄 Sources Successfully Analyzed: {len(research_results.get('analyzed_sources', []))}\n"
            f"💡 Key Findings Extracted: {len(research_results.get('key_findings', []))}\n"
            f"🎯 Themes Identified: {len(research_results.get('intermediate_summaries', []))}\n"
            f"📝 Final Report: {'Generated' if research_results.get('final_summary') else 'Failed'}\n"
            f"💾 Saved to File: {'Yes' if output_file else 'No'}",
            title="🏆 Research Complete",
            border_style="green"
        ))
        
        # Cleanup
        if hasattr(browser, '_session_active') and browser._session_active:
            await browser.close_session()
            if verbose:
                console.print("[dim]🧹 Browser session closed[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Research failed: {str(e)}[/red]")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")


def handle_research(
    config: Config,
    query: str,
    max_results: int = 8,
    output_file: Optional[str] = None,
    verbose: bool = False,
    headless: bool = True
) -> None:
    """
    Synchronous wrapper for the enhanced research function.
    
    Args:
        config: Application configuration
        query: Research query
        max_results: Maximum search results to analyze
        output_file: Optional file to save results
        verbose: Show detailed progress
        headless: Run browser in headless mode
    """
    try:
        # Run the async research function
        asyncio.run(handle_research_async(
            config=config,
            query=query,
            max_results=max_results,
            output_file=output_file,
            verbose=verbose,
            headless=headless
        ))
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Research interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Research execution failed: {str(e)}[/red]")


async def save_research_results(research_data: dict, output_file: str, query: str) -> None:
    """
    Save comprehensive research results to file with detailed formatting.
    
    Args:
        research_data: Complete research results
        output_file: Path to output file
        query: Original research query
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("="*80 + "\n")
            f.write(f"COMPREHENSIVE RESEARCH REPORT\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Query: {query}\n")
            f.write(f"Generated by: Enhanced Research Assistant\n")
            f.write(f"Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Executive Summary
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 40 + "\n")
            if research_data.get('final_summary'):
                f.write(research_data['final_summary'])
                f.write("\n\n")
            
            # Research Statistics
            f.write("RESEARCH STATISTICS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Sources Found: {len(research_data.get('search_results', []))}\n")
            f.write(f"Sources Analyzed: {len(research_data.get('analyzed_sources', []))}\n")
            f.write(f"Key Findings: {len(research_data.get('key_findings', []))}\n")
            f.write(f"Themes Identified: {len(research_data.get('intermediate_summaries', []))}\n\n")
            
            # Key Findings
            if research_data.get('key_findings'):
                f.write("KEY FINDINGS\n")
                f.write("-" * 40 + "\n")
                for i, finding in enumerate(research_data['key_findings'], 1):
                    f.write(f"{i}. {finding['finding']}\n")
                    f.write(f"   Source: {finding['source_title']}\n")
                    f.write(f"   URL: {finding['source_url']}\n")
                    f.write(f"   Relevance Score: {finding['relevance_score']:.1f}\n\n")
            
            # Theme Analysis
            if research_data.get('intermediate_summaries'):
                f.write("THEME ANALYSIS\n")
                f.write("-" * 40 + "\n")
                for theme_data in research_data['intermediate_summaries']:
                    f.write(f"Theme: {theme_data['theme']}\n")
                    f.write(f"Summary: {theme_data['summary']}\n")
                    f.write(f"Supporting Sources: {theme_data['source_count']}\n\n")
            
            # Detailed Source Analysis
            if research_data.get('analyzed_sources'):
                f.write("DETAILED SOURCE ANALYSIS\n")
                f.write("-" * 40 + "\n")
                for i, source in enumerate(research_data['analyzed_sources'], 1):
                    f.write(f"Source {i}: {source['title']}\n")
                    f.write(f"URL: {source['url']}\n")
                    f.write(f"Relevance Score: {source['relevance_score']:.1f}\n")
                    f.write(f"Word Count: {source['word_count']}\n")
                    f.write(f"Summary: {source['summary']}\n")
                    f.write(f"Content Preview: {source['content'][:300]}...\n")
                    f.write("-" * 60 + "\n\n")
            
            # All Search Results
            if research_data.get('search_results'):
                f.write("ALL SEARCH RESULTS\n")
                f.write("-" * 40 + "\n")
                for i, result in enumerate(research_data['search_results'], 1):
                    f.write(f"{i}. {result.get('title', 'No title')}\n")
                    f.write(f"   URL: {result.get('url', 'No URL')}\n")
                    if result.get('description'):
                        f.write(f"   Description: {result['description']}\n")
                    f.write("\n")
            
            f.write("="*80 + "\n")
            f.write("END OF REPORT\n")
            f.write("="*80 + "\n")
            
    except Exception as e:
        console.print(f"[red]❌ Failed to save results to file: {str(e)}[/red]")


if __name__ == "__main__":
    import argparse
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(description="Enhanced Research Assistant")
    parser.add_argument("query", help="Research query")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of sources to analyze")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config.from_env()
    
    # Run research
    handle_research(
        config=config,
        query=args.query,
        max_results=args.limit,
        output_file=args.output,
        verbose=args.verbose,
        headless=args.headless
    ) 