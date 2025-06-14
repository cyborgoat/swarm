"""
Main Research Assistant - Coordinates comprehensive research process.
"""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from swarm.core.config import Config
from swarm.web.browser import Browser
from swarm.web.search import WebSearch

from .analyzer import ContentAnalyzer
from .extractor import ContentExtractor
from .formatter import ResearchFormatter
from .image_processor import ImageProcessor

console = Console()


class ResearchAssistant:
    """Main research assistant that coordinates the entire research process."""

    def __init__(self, config: Config, verbose: bool = False, include_images: bool = True):
        self.config = config
        self.verbose = verbose
        self.include_images = include_images

        # Initialize components
        self.browser = Browser(config.browser)
        self.search = WebSearch(config.search)

        # Initialize specialized processors
        self.analyzer = ContentAnalyzer(config)
        self.extractor = ContentExtractor(self.browser, verbose)
        self.image_processor = ImageProcessor(self.browser, verbose) if include_images else None
        self.formatter = None  # Will be initialized with query

        if verbose:
            console.print(f"[dim]🔧 Research Assistant initialized with {config.llm.model}[/dim]")
            console.print(f"[dim]📊 Context: {config.llm.max_tokens} tokens[/dim]")
            console.print(f"[dim]🌐 Language: {config.research.output_language}[/dim]")

    async def conduct_research(self, query: str, max_sources: int = 8) -> dict[str, Any]:
        """
        Conduct comprehensive research on a topic.
        
        Args:
            query: Research query
            max_sources: Maximum number of sources to analyze
            
        Returns:
            Complete research results
        """
        # Initialize formatter with query
        self.formatter = ResearchFormatter(self.config, query)

        # Initialize research data
        research_data = {
            'query': query,
            'search_results': [],
            'analysis_results': [],
            'final_summary': '',
            'images_found': [],
            'model_used': self.config.llm.model,
            'context_size': self.config.llm.max_tokens,
            'language': self.config.research.output_language
        }

        console.print(Panel.fit(
            f"🔬 [bold cyan]Starting Research[/bold cyan]\n"
            f"📋 Query: [yellow]{query}[/yellow]\n"
            f"🎯 Max Sources: {max_sources}\n"
            f"🤖 Model: {self.config.llm.model}\n"
            f"🌐 Language: {self.config.research.output_language}\n"
            f"🖼️ Images: {'Enabled' if self.include_images else 'Disabled'}",
            title="🤖 Research Assistant",
            border_style="blue"
        ))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            # Phase 1: Web Search
            await self._search_phase(query, max_sources, progress, research_data)

            # Phase 2: Content Analysis
            if research_data['search_results']:
                await self._analysis_phase(progress, research_data)

            # Phase 3: Synthesis
            if research_data['analysis_results']:
                await self._synthesis_phase(progress, research_data)

        return research_data

    async def _search_phase(self, query: str, max_sources: int, progress: Progress, research_data: dict[str, Any]):
        """Phase 1: Search for relevant sources."""
        task = progress.add_task("🔍 Searching web sources...", total=100)

        try:
            progress.update(task, advance=30, description="🔍 Performing web search...")
            search_results = self.search.search(query)[:max_sources]

            progress.update(task, advance=40, description="🔍 Filtering results...")
            # Remove duplicates and invalid results
            valid_results = []
            seen_urls = set()
            for result in search_results:
                if result.get('url') and result.get('url') not in seen_urls:
                    valid_results.append(result)
                    seen_urls.add(result['url'])

            research_data['search_results'] = valid_results
            progress.update(task, advance=30, description=f"✅ Found {len(valid_results)} sources")

            if self.verbose:
                console.print(f"[dim]📊 Search completed: {len(valid_results)} valid sources[/dim]")

        except Exception as e:
            progress.update(task, advance=100, description=f"❌ Search failed: {str(e)}")
            console.print(f"[red]Search error: {str(e)}[/red]")

    async def _analysis_phase(self, progress: Progress, research_data: dict[str, Any]):
        """Phase 2: Analyze source content with intelligent depth adjustment."""
        sources = research_data['search_results']
        task = progress.add_task("📄 Analyzing sources...", total=len(sources))

        # Prepare sources for analysis
        prepared_sources = []
        for source in sources:
            progress.update(task, advance=0, description=f"📄 Extracting content from {source['title'][:30]}...")

            try:
                # Extract content with intelligent retry
                content_data = await self.extractor.extract_with_retry(
                    url=source['url'],
                    title=source['title'],
                    query=research_data['query'],
                    config=self.config.research
                )

                if content_data:
                    # Extract images if enabled
                    if self.image_processor:
                        images = await self.image_processor.extract_images(source['url'])
                        content_data['images'] = images
                        if images:
                            research_data['images_found'].extend(images)

                    prepared_sources.append(content_data)

            except Exception as e:
                if self.verbose:
                    console.print(f"[yellow]⚠️ Failed to extract: {source['title'][:50]}... - {str(e)}[/yellow]")
                continue

        # Analyze all sources with intelligent processing
        if prepared_sources:
            analysis_results = await self.analyzer.analyze_sources(
                prepared_sources,
                research_data['query'],
                progress,
                task
            )

            research_data['analysis_results'] = analysis_results

            # Display analysis summary
            avg_relevance = sum(r.relevance_score for r in analysis_results) / len(analysis_results) if analysis_results else 0
            high_relevance_sources = sum(1 for r in analysis_results if r.relevance_score >= self.config.research.relevance_threshold)

            progress.update(task, description=f"✅ Analyzed {len(analysis_results)} sources (avg relevance: {avg_relevance:.1f})")

            if self.verbose:
                console.print(f"[dim]📊 Analysis complete: {high_relevance_sources}/{len(analysis_results)} sources above threshold ({self.config.research.relevance_threshold})[/dim]")

    async def _synthesis_phase(self, progress: Progress, research_data: dict[str, Any]):
        """Phase 3: Synthesize findings and generate final report."""
        task = progress.add_task("🧠 Synthesizing findings...", total=100)

        try:
            progress.update(task, advance=50, description="🧠 Generating final summary...")

            # Generate final summary using all analysis results
            final_summary = await self.analyzer.generate_final_summary(
                research_data['analysis_results'],
                research_data['query']
            )
            research_data['final_summary'] = final_summary

            progress.update(task, advance=50, description="✅ Synthesis complete!")

        except Exception as e:
            progress.update(task, advance=100, description=f"❌ Synthesis failed: {str(e)}")
            console.print(f"[red]Synthesis error: {str(e)}[/red]")

    def display_results(self, research_data: dict[str, Any]) -> None:
        """Display comprehensive research results."""
        if not self.formatter:
            self.formatter = ResearchFormatter(self.config, research_data['query'])

        self.formatter.display_results(
            research_data['analysis_results'],
            research_data['final_summary'],
            research_data['search_results'],
            self.verbose
        )

    def generate_markdown_report(self, research_data: dict[str, Any]) -> str:
        """Generate markdown research report."""
        if not self.formatter:
            self.formatter = ResearchFormatter(self.config, research_data['query'])

        return self.formatter.generate_markdown_report(
            research_data['analysis_results'],
            research_data['final_summary'],
            research_data['search_results'],
            self.include_images
        )

    def get_auto_filename(self) -> str:
        """Generate automatic filename for research results."""
        if not self.formatter:
            return "research_results.md"
        return self.formatter.get_auto_filename()

    async def cleanup(self):
        """Clean up resources."""
        if hasattr(self.browser, '_session_active') and self.browser._session_active:
            await self.browser.close_session()
            if self.verbose:
                console.print("[dim]🧹 Browser session closed[/dim]")
