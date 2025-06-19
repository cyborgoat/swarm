"""
Content Analyzer - Handles LLM-based analysis of research content.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

from rich.console import Console
from rich.progress import Progress

from swarm.core.services import ServiceMixin
from swarm.research.language import LanguageHelper

console = Console()


@dataclass
class AnalysisResult:
    """Container for analysis results."""

    summary: str
    relevance_score: float
    key_finding: str
    themes: list[str]
    word_count: int
    extraction_method: str = "normal"  # normal, deep, enhanced
    analysis_method: str = "normal"  # normal, enhanced


class ContentAnalyzer(ServiceMixin):
    """Handles intelligent analysis of research content using LLM."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.language_helper = LanguageHelper(self.config.research.output_language)

    async def analyze_sources(
        self, sources: list[dict[str, Any]], query: str, progress: Progress | None = None, task_id: int | None = None
    ) -> list[AnalysisResult]:
        """Analyze all sources and return structured results."""

        # Intelligent content processing with depth adjustment
        processed_sources = []

        for i, source in enumerate(sources):
            if progress and task_id:
                progress.update(task_id, advance=1)

            # Process source with intelligent depth adjustment
            analysis = await self._analyze_source_with_intelligence(source, query)
            processed_sources.append(analysis)

            # Brief pause to show progress
            await asyncio.sleep(0.1)

        # Check if we need additional source search based on relevance
        high_relevance_count = sum(
            1 for r in processed_sources if r.relevance_score >= self.config.research.relevance_threshold
        )

        if high_relevance_count < 3 and len(processed_sources) < self.config.research.max_sources:
            console.print(
                f"[yellow]🔍 Found only {high_relevance_count} high-relevance sources. "
                f"Consider expanding search.[/yellow]"
            )

        return processed_sources

    async def _analyze_source_with_intelligence(self, source: dict[str, Any], query: str) -> AnalysisResult:
        """Analyze a single source with intelligent depth adjustment."""

        # First pass: Quick analysis
        analysis = await self._analyze_source(source, query, method="normal")

        # Intelligence check: Is this source worth deeper analysis?
        needs_enhancement = (
            analysis.relevance_score < self.config.research.relevance_threshold
            or analysis.word_count < self.config.research.min_word_count
        )

        if needs_enhancement and self.config.research.max_retry_attempts > 0:
            # Enhanced extraction if content is shallow
            if analysis.word_count < self.config.research.min_word_count:
                # Deep content extraction
                enhanced_content = await self._extract_deep_content(source)
                if enhanced_content:
                    source["content"] = enhanced_content
                    analysis = await self._analyze_source(source, query, method="enhanced")
                    analysis.extraction_method = "deep"
                    analysis.analysis_method = "enhanced"

            # Enhanced analysis if relevance is low but content is substantial
            elif analysis.relevance_score < self.config.research.relevance_threshold:
                analysis = await self._analyze_source(source, query, method="enhanced")
                analysis.analysis_method = "enhanced"

        return analysis

    async def _extract_deep_content(self, source: dict[str, Any]) -> str | None:
        """Extract deeper content from a source if available."""
        # This would be implemented to extract more content from the source
        # For now, we'll just return the existing content
        content = source.get("content", "")

        # Truncate to deep content limit if needed
        if len(content) > self.config.research.deep_content_limit:
            content = content[: self.config.research.deep_content_limit] + "..."

        return content if content else None

    async def _analyze_source(self, source: dict[str, Any], query: str, method: str = "normal") -> AnalysisResult:
        """Analyze a single source using LLM."""

        title = source.get("title", "Unknown")
        content = source.get("content", "")

        if not content:
            return AnalysisResult(
                summary="No content available for analysis",
                relevance_score=0.0,
                key_finding="Unable to extract content",
                themes=[],
                word_count=0,
                extraction_method="normal",
                analysis_method=method,
            )

        # Word count
        word_count = len(content.split())

        # Use language-specific prompts
        if method == "enhanced":
            prompt_template = self.language_helper.get_prompt(
                "enhanced_summary", query=query, title=title, content=content
            )
        else:
            prompt_template = self.language_helper.get_prompt(
                "source_summary", query=query, title=title, content=content
            )

        try:
            # Only use streaming when verbose mode is on to avoid progress bar conflicts
            use_streaming = self.config.llm.enable_streaming and self.verbose
            
            if use_streaming:
                # Get summary with streaming display
                summary_title = f"📝 Analyzing: {title[:30]}..."
                summary_response = await self.llm.generate_streaming(
                    prompt_template, 
                    console=console, 
                    title=summary_title
                )
                summary = summary_response.strip()

                # Get key finding with streaming display
                finding_prompt = self.language_helper.get_prompt("key_finding", query=query, title=title, content=content)
                finding_title = f"🔍 Extracting Key Finding..."
                finding_response = await self.llm.generate_streaming(
                    finding_prompt, 
                    console=console, 
                    title=finding_title
                )
                key_finding = finding_response.strip()
            else:
                # Use regular async generation without streaming
                summary_response = await self.llm.generate_async(prompt_template)
                summary = summary_response.strip()

                # Get key finding
                finding_prompt = self.language_helper.get_prompt("key_finding", query=query, title=title, content=content)
                finding_response = await self.llm.generate_async(finding_prompt)
                key_finding = finding_response.strip()

            # Calculate relevance score (simple heuristic)
            relevance_score = await self._calculate_relevance_score(content, query, summary)

            # Extract themes (simplified)
            themes = await self._extract_themes(content, query)

            return AnalysisResult(
                summary=summary,
                relevance_score=relevance_score,
                key_finding=key_finding,
                themes=themes,
                word_count=word_count,
                extraction_method="normal",
                analysis_method=method,
            )

        except Exception as e:
            console.print(f"[red]Error analyzing source: {str(e)}[/red]")
            return AnalysisResult(
                summary=f"Error analyzing content: {str(e)}",
                relevance_score=1.0,
                key_finding="Analysis failed",
                themes=[],
                word_count=word_count,
                extraction_method="normal",
                analysis_method=method,
            )

    async def _calculate_relevance_score(self, content: str, query: str, summary: str) -> float:
        """Calculate relevance score based on content and query."""

        # Simple scoring based on keyword overlap and content quality
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        summary_words = set(summary.lower().split())

        # Keyword overlap score
        content_overlap = len(query_words.intersection(content_words)) / len(query_words) if query_words else 0
        summary_overlap = len(query_words.intersection(summary_words)) / len(query_words) if query_words else 0

        # Content quality score
        content_quality = min(len(content.split()) / 100, 1.0)  # Normalize to 1.0

        # Combined score (0-10 scale)
        relevance_score = (content_overlap * 4 + summary_overlap * 4 + content_quality * 2) * 10

        return min(relevance_score, 10.0)

    async def _extract_themes(self, content: str, query: str) -> list[str]:
        """Extract main themes from content."""

        # Simple theme extraction based on frequent meaningful words
        words = content.lower().split()

        # Filter out common words and short words
        meaningful_words = [
            word
            for word in words
            if len(word) > 4
            and word
            not in [
                "that",
                "this",
                "with",
                "from",
                "they",
                "have",
                "will",
                "been",
                "were",
                "said",
                "what",
                "when",
                "where",
                "would",
                "could",
                "should",
                "about",
                "which",
                "their",
                "there",
                "these",
                "those",
            ]
        ]

        # Count frequency
        word_freq = {}
        for word in meaningful_words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Get top themes
        themes = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return [theme[0].title() for theme in themes if theme[1] > 1]

    async def generate_final_summary(self, analyses: list[AnalysisResult], query: str) -> str:
        """Generate final research summary using LLM."""

        # Prepare findings and themes
        findings = []
        all_themes = []

        for analysis in analyses:
            if analysis.relevance_score >= 3.0:  # Include reasonably relevant findings
                findings.append(f"• {analysis.key_finding}")
                all_themes.extend(analysis.themes)

        # Get most common themes
        theme_counts = {}
        for theme in all_themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

        top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        themes_text = "\n".join([f"• {theme[0]} (mentioned {theme[1]} times)" for theme in top_themes])

        # Generate final summary using language-specific prompt
        prompt = self.language_helper.get_prompt(
            "final_summary", query=query, findings="\n".join(findings), themes=themes_text
        )

        try:
            # Only use streaming when verbose mode is on to avoid progress bar conflicts
            use_streaming = self.config.llm.enable_streaming and self.verbose
            
            if use_streaming:
                summary = await self.llm.generate_streaming(
                    prompt, 
                    console=console, 
                    title="📋 Generating Final Research Summary"
                )
            else:
                summary = await self.llm.generate_async(prompt)
                
            return summary.strip()
        except Exception as e:
            console.print(f"[red]Error generating final summary: {str(e)}[/red]")
            return f"Error generating summary: {str(e)}"
