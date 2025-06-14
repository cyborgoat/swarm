"""
Research Results Formatter - Handles display and markdown output of research results.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from rich.syntax import Syntax

from swarm.research.analyzer import AnalysisResult
from swarm.research.language import LanguageHelper

console = Console()


class ResearchFormatter:
    """Handles formatting and display of research results."""
    
    def __init__(self, config, query: str):
        self.config = config
        self.query = query
        self.language_helper = LanguageHelper(config.research.output_language)
        
    def display_results(
        self, 
        analyses: List[AnalysisResult], 
        final_summary: str,
        sources: List[Dict[str, Any]],
        verbose: bool = False
    ) -> None:
        """Display comprehensive research results in the terminal."""
        
        lang = self.language_helper
        
        # Header with language indicator
        lang_display = lang.get_language_display()
        console.print(f"\n🎉 {lang.get_text('research_complete')} [{lang_display}]", style="bold green")
        
        # Statistics
        stats_data = [
            f"📊 {lang.get_text('sources_analyzed')}: {len(sources)}",
            f"🎯 {lang.get_text('themes_identified')}: {len(set(theme for analysis in analyses for theme in analysis.themes))}",
            f"🔍 {lang.get_text('relevance_distribution')}: {self._get_relevance_distribution(analyses)}"
        ]
        
        console.print(Panel(
            "\n".join(stats_data),
            title=f"📋 {lang.get_text('research_complete')}",
            border_style="green"
        ))
        
        # Final Summary
        console.print(f"\n## 📝 {lang.get_text('executive_summary')}")
        console.print(Panel(final_summary, border_style="blue"))
        
        if verbose:
            self._display_detailed_sources(analyses, sources)
    
    def _display_detailed_sources(self, analyses: List[AnalysisResult], sources: List[Dict[str, Any]]) -> None:
        """Display detailed source analysis."""
        lang = self.language_helper
        
        console.print(f"\n## 🔍 {lang.get_text('detailed_source_analysis')}")
        
        for i, (analysis, source) in enumerate(zip(analyses, sources)):
            # Depth indicators
            extraction_indicator = "D" if analysis.extraction_method == "deep" else "N"
            analysis_indicator = "E" if analysis.analysis_method == "enhanced" else "N"
            depth_display = f"[{extraction_indicator}/{analysis_indicator}]"
            
            # Relevance color coding
            relevance_color = self._get_relevance_color(analysis.relevance_score)
            
            # Source panel
            title = f"{i+1}. {source.get('title', 'Unknown')[:60]}... {depth_display}"
            content = f"""
{lang.get_text('relevance_score')}: [{relevance_color}]{analysis.relevance_score:.1f}[/{relevance_color}]/10
{lang.get_text('word_count')}: {analysis.word_count}

{lang.get_text('summary')}: {analysis.summary}

{lang.get_text('finding')}: {analysis.key_finding}
"""
            
            if analysis.themes:
                content += f"\n{lang.get_text('identified_themes')}: {', '.join(analysis.themes[:3])}"
            
            console.print(Panel(content, title=title, border_style="dim"))
        
        # Legend
        console.print(f"\n[dim]{lang.get_text('depth_legend')}[/dim]")
    
    def _get_relevance_color(self, score: float) -> str:
        """Get color for relevance score."""
        if score >= self.config.research.relevance_threshold:
            return "green"
        elif score >= 3.0:
            return "yellow"
        else:
            return "red"
    
    def _get_relevance_distribution(self, analyses: List[AnalysisResult]) -> str:
        """Get relevance distribution summary."""
        lang = self.language_helper
        
        high = sum(1 for a in analyses if a.relevance_score >= self.config.research.relevance_threshold)
        medium = sum(1 for a in analyses if 3.0 <= a.relevance_score < self.config.research.relevance_threshold)
        low = sum(1 for a in analyses if a.relevance_score < 3.0)
        
        return f"{lang.get_text('high')}:{high}, {lang.get_text('medium')}:{medium}, {lang.get_text('low')}:{low}"
    
    def generate_markdown_report(
        self,
        analyses: List[AnalysisResult],
        final_summary: str,
        sources: List[Dict[str, Any]],
        include_images: bool = True
    ) -> str:
        """Generate comprehensive markdown research report."""
        
        lang = self.language_helper
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Statistics
        total_words = sum(analysis.word_count for analysis in analyses)
        avg_relevance = sum(analysis.relevance_score for analysis in analyses) / len(analyses) if analyses else 0
        high_relevance_count = sum(1 for analysis in analyses if analysis.relevance_score >= self.config.research.relevance_threshold)
        
        # Get all themes and count them
        all_themes = {}
        for analysis in analyses:
            for theme in analysis.themes:
                all_themes[theme] = all_themes.get(theme, 0) + 1
        
        top_themes = sorted(all_themes.items(), key=lambda x: x[1], reverse=True)[:8]
        
        # All images
        all_images = []
        if include_images:
            for source in sources:
                all_images.extend(source.get('images', []))
        
        # Generate report
        report = f"""# {lang.get_text('research_report')}: {self.query}

**{lang.get_text('generated')}:** {timestamp}  
**{lang.get_text('model')}:** {self.config.llm.model}  
**{lang.get_text('context_size')}:** {self.config.llm.max_tokens:,} {lang.get_text('tokens')}  
**{lang.get_text('sources_analyzed')}:** {len(sources)}  
**{lang.get_text('images_found')}:** {len(all_images)}

---

## {lang.get_text('executive_summary')}

{final_summary}

---

## {lang.get_text('key_findings')}

"""
        
        # Key findings from high-relevance sources
        key_findings = [
            analysis for analysis in analyses 
            if analysis.relevance_score >= max(3.0, self.config.research.relevance_threshold - 2.0)
        ][:6]
        
        for i, analysis in enumerate(key_findings, 1):
            report += f"""
### {lang.get_text('finding')} {i}

**{lang.get_text('relevance_score')}:** {analysis.relevance_score:.1f}/10  
**{lang.get_text('source')}:** {sources[analyses.index(analysis)].get('title', 'Unknown')}

{analysis.key_finding}

"""
        
        # Main themes
        if top_themes:
            report += f"""---

## {lang.get_text('identified_themes')}

"""
            for theme, count in top_themes:
                supporting_sources = [
                    sources[i].get('title', 'Unknown')[:50] 
                    for i, analysis in enumerate(analyses) 
                    if theme in analysis.themes
                ][:3]
                
                report += f"""
### {theme}

**{lang.get_text('supporting_sources')}:** {count}  
**{lang.get_text('sources_found')}:** {', '.join(supporting_sources)}

"""
        
        # Images section
        if include_images and all_images:
            report += f"""---

## {lang.get_text('relevant_images')}

"""
            for i, image in enumerate(all_images[:12], 1):  # Limit to 12 images
                if image.get('alt_text') or image.get('caption'):
                    description = image.get('alt_text') or image.get('caption')
                    report += f"""
### Image {i}: {description[:100]}...

![{description}]({image['url']})

"""
                else:
                    report += f"""
### Image {i}

![Research Image {i}]({image['url']})

"""
        
        # Detailed source analysis
        report += f"""---

## {lang.get_text('detailed_source_analysis')}

"""
        
        for i, (analysis, source) in enumerate(zip(analyses, sources), 1):
            # Depth indicators
            extraction_depth = "🔍 Deep" if analysis.extraction_method == "deep" else "📄 Normal"
            analysis_depth = "🧠 Enhanced" if analysis.analysis_method == "enhanced" else "🔍 Standard"
            
            report += f"""
### {i}. {source.get('title', 'Unknown')}

**URL:** {source.get('url', 'N/A')}  
**{lang.get_text('relevance_score')}:** {analysis.relevance_score:.1f}/10  
**{lang.get_text('word_count')}:** {analysis.word_count:,}  
**Extraction:** {extraction_depth} | **Analysis:** {analysis_depth}

#### {lang.get_text('summary')}
{analysis.summary}

#### {lang.get_text('key_findings')}
{analysis.key_finding}

"""
            
            if analysis.themes:
                report += f"**{lang.get_text('identified_themes')}:** {', '.join(analysis.themes)}\n\n"
            
            # Content preview
            content_preview = source.get('content', '')[:300]
            if content_preview:
                report += f"""
#### {lang.get_text('content_preview')}
```
{content_preview}...
```

"""
        
        # Final statistics
        report += f"""---

## {lang.get_text('all_search_results')}

| # | {lang.get_text('source')} | {lang.get_text('relevance_score')} | {lang.get_text('word_count')} | Depth |
|---|-------|------------|------|-------|
"""
        
        for i, (analysis, source) in enumerate(zip(analyses, sources), 1):
            title = source.get('title', 'Unknown')[:40]
            extraction_indicator = "D" if analysis.extraction_method == "deep" else "N"
            analysis_indicator = "E" if analysis.analysis_method == "enhanced" else "N"
            depth_display = f"{extraction_indicator}/{analysis_indicator}"
            
            report += f"| {i} | [{title}...]({source.get('url', '#')}) | {analysis.relevance_score:.1f} | {analysis.word_count:,} | {depth_display} |\n"
        
        report += f"""

### {lang.get_text('depth_legend')}
- **N/N**: Normal extraction, Standard analysis
- **D/N**: Deep extraction, Standard analysis  
- **N/E**: Normal extraction, Enhanced analysis
- **D/E**: Deep extraction, Enhanced analysis

### Research Statistics
- **Total Words Analyzed:** {total_words:,}
- **Average Relevance Score:** {avg_relevance:.1f}/10
- **High Relevance Sources:** {high_relevance_count}/{len(analyses)}
- **Unique Themes Identified:** {len(all_themes)}
- **Language:** {lang.get_language_display()}

---

*{lang.get_text('research_report')} generated by Swarm Research Assistant*
"""
        
        return report
    
    def get_auto_filename(self) -> str:
        """Generate automatic filename for research report."""
        # Sanitize query for filename
        safe_query = "".join(c for c in self.query if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_query = safe_query.replace(' ', '_')[:50]  # Limit length
        
        # Add timestamp and model info
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        model_name = self.config.llm.model.replace(':', '_').replace('/', '_')
        
        # Add language suffix
        lang_suffix = "_zh" if self.language_helper.is_chinese() else "_en"
        
        return f"research_{safe_query}_{model_name}_{timestamp}{lang_suffix}.md" 