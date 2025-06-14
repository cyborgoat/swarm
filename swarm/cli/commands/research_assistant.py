"""
Enhanced Research Assistant for comprehensive topic investigation with detailed progress reporting.
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from swarm.llm.client import LLMClient
from swarm.web.browser import Browser
from swarm.web.search import WebSearch

console = Console()


class EnhancedResearchAssistant:
    """Enhanced AI Research Assistant with comprehensive analysis and progress reporting."""
    
    def __init__(self, browser: Browser, search: WebSearch, llm_client: LLMClient, verbose: bool = False, use_mcp: bool = False):
        self.browser = browser
        self.search = search
        self.llm = llm_client
        self.verbose = verbose
        self.use_mcp = use_mcp
        self.research_data = {
            'query': '',
            'search_results': [],
            'analyzed_sources': [],
            'key_findings': [],
            'intermediate_summaries': [],
            'final_summary': ''
        }
    
    async def conduct_comprehensive_research(self, query: str, max_sources: int = 8) -> Dict[str, Any]:
        """
        Conduct comprehensive research with detailed step-by-step progress reporting.
        
        Args:
            query: Research query
            max_sources: Maximum number of sources to analyze
            
        Returns:
            Complete research results with all intermediate steps
        """
        self.research_data['query'] = query
        
        console.print(Panel.fit(
            f"🔬 [bold cyan]Starting Comprehensive Research[/bold cyan]\n"
            f"📋 Query: [yellow]{query}[/yellow]\n"
            f"🎯 Target Sources: {max_sources}\n"
            f"🔧 Using {'MCP Tools' if self.use_mcp else 'Direct Browser'}",
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
            search_task = progress.add_task("🔍 Phase 1: Searching the web...", total=100)
            search_results = await self._phase_1_web_search(query, max_sources, progress, search_task)
            
            if not search_results:
                console.print(Panel.fit(
                    "❌ No search results found. Please try a different query.",
                    title="Research Failed",
                    border_style="red"
                ))
                return self.research_data
            
            # Phase 2: Source Analysis
            analysis_task = progress.add_task("📄 Phase 2: Analyzing sources...", total=len(search_results))
            analyzed_sources = await self._phase_2_source_analysis(search_results, progress, analysis_task)
            
            # Phase 3: Content Synthesis
            synthesis_task = progress.add_task("🧠 Phase 3: Synthesizing findings...", total=100)
            key_findings = await self._phase_3_content_synthesis(analyzed_sources, progress, synthesis_task)
            
            # Phase 4: Final Summary Generation
            summary_task = progress.add_task("📝 Phase 4: Generating final report...", total=100)
            final_summary = await self._phase_4_final_summary(query, key_findings, progress, summary_task)
        
        # Display comprehensive results
        await self._display_comprehensive_results()
        
        return self.research_data
    
    async def _phase_1_web_search(self, query: str, max_sources: int, progress: Progress, task_id) -> List[Dict[str, Any]]:
        """Phase 1: Comprehensive web search with progress reporting."""
        
        progress.update(task_id, advance=20, description="🔍 Phase 1: Initiating web search...")
        
        try:
            # Perform web search
            if self.use_mcp:
                console.print("🔧 [cyan]Using MCP search_web tool[/cyan]")
            
            search_results = self.search.search(query)[:max_sources]
            progress.update(task_id, advance=40, description=f"🔍 Phase 1: Found {len(search_results)} results...")
            
            # Filter and validate results
            valid_results = []
            for result in search_results:
                if result.get('url') and result.get('title'):
                    valid_results.append(result)
            
            progress.update(task_id, advance=30, description=f"🔍 Phase 1: Validated {len(valid_results)} sources...")
            
            # Display search results summary
            self._display_search_summary(valid_results)
            
            self.research_data['search_results'] = valid_results
            progress.update(task_id, advance=10, description="✅ Phase 1: Search complete!")
            
            return valid_results
            
        except Exception as e:
            progress.update(task_id, advance=100, description=f"❌ Phase 1: Search failed - {str(e)}")
            console.print(f"[red]Search error: {str(e)}[/red]")
            return []
    
    async def _phase_2_source_analysis(self, search_results: List[Dict[str, Any]], progress: Progress, task_id) -> List[Dict[str, Any]]:
        """Phase 2: Detailed source analysis with content extraction."""
        
        analyzed_sources = []
        
        for i, result in enumerate(search_results):
            progress.update(task_id, advance=1, description=f"📄 Phase 2: Analyzing source {i+1}/{len(search_results)}...")
            
            try:
                # Navigate to source
                if self.use_mcp:
                    console.print(f"🔧 [cyan]Using MCP navigate_to_url for: {result['title'][:50]}...[/cyan]")
                
                # Start browser session if not already started
                if not hasattr(self.browser, '_session_active') or not self.browser._session_active:
                    await self.browser.start_session()
                
                # Navigate and extract content
                nav_result = await self.browser.navigate_to_url(result['url'])
                
                if nav_result.get('status') == 'success':
                    # Extract content
                    if self.use_mcp:
                        console.print(f"🔧 [cyan]Using MCP extract_page_content[/cyan]")
                    
                    content_result = await self.browser.extract_page_content(
                        query=self.research_data['query'], 
                        max_length=3000
                    )
                    
                    if content_result.get('status') == 'success' and content_result.get('content'):
                        # Generate intermediate summary for this source
                        source_summary = await self._generate_source_summary(
                            result['title'], 
                            content_result['content'], 
                            self.research_data['query']
                        )
                        
                        analyzed_source = {
                            'title': result['title'],
                            'url': result['url'],
                            'content': content_result['content'],
                            'summary': source_summary,
                            'relevance_score': self._calculate_relevance_score(content_result['content'], self.research_data['query']),
                            'word_count': len(content_result['content'].split())
                        }
                        
                        analyzed_sources.append(analyzed_source)
                        
                        # Display intermediate progress
                        self._display_source_analysis(analyzed_source, i + 1)
                        
                    else:
                        console.print(f"[yellow]⚠️ Could not extract content from: {result['title'][:50]}...[/yellow]")
                else:
                    console.print(f"[yellow]⚠️ Could not navigate to: {result['title'][:50]}...[/yellow]")
                    
            except Exception as e:
                console.print(f"[red]❌ Error analyzing {result['title'][:50]}...: {str(e)}[/red]")
                continue
        
        self.research_data['analyzed_sources'] = analyzed_sources
        progress.update(task_id, description=f"✅ Phase 2: Analyzed {len(analyzed_sources)} sources successfully!")
        
        return analyzed_sources
    
    async def _phase_3_content_synthesis(self, analyzed_sources: List[Dict[str, Any]], progress: Progress, task_id) -> List[Dict[str, Any]]:
        """Phase 3: Synthesize content and extract key findings."""
        
        progress.update(task_id, advance=20, description="🧠 Phase 3: Identifying key themes...")
        
        # Sort sources by relevance
        sorted_sources = sorted(analyzed_sources, key=lambda x: x['relevance_score'], reverse=True)
        
        progress.update(task_id, advance=20, description="🧠 Phase 3: Extracting key findings...")
        
        # Extract key findings from top sources
        key_findings = []
        for i, source in enumerate(sorted_sources[:5]):  # Top 5 most relevant sources
            finding = await self._extract_key_finding(source, self.research_data['query'])
            if finding:
                key_findings.append({
                    'source_title': source['title'],
                    'source_url': source['url'],
                    'finding': finding,
                    'relevance_score': source['relevance_score']
                })
        
        progress.update(task_id, advance=30, description="🧠 Phase 3: Generating intermediate summaries...")
        
        # Generate intermediate summaries by theme
        themes = await self._identify_themes(key_findings)
        intermediate_summaries = []
        
        for theme in themes:
            theme_summary = await self._generate_theme_summary(theme, key_findings)
            intermediate_summaries.append({
                'theme': theme,
                'summary': theme_summary,
                'source_count': len([f for f in key_findings if theme.lower() in f['finding'].lower()])
            })
        
        progress.update(task_id, advance=20, description="🧠 Phase 3: Cross-referencing findings...")
        
        # Display intermediate findings
        self._display_key_findings(key_findings, intermediate_summaries)
        
        self.research_data['key_findings'] = key_findings
        self.research_data['intermediate_summaries'] = intermediate_summaries
        
        progress.update(task_id, advance=10, description="✅ Phase 3: Content synthesis complete!")
        
        return key_findings
    
    async def _phase_4_final_summary(self, query: str, key_findings: List[Dict[str, Any]], progress: Progress, task_id) -> str:
        """Phase 4: Generate comprehensive final summary with improved error handling."""
        
        progress.update(task_id, advance=25, description="📝 Phase 4: Structuring final report...")
        
        # Limit findings to prevent token overflow
        limited_findings = key_findings[:5]  # Only use top 5 findings
        findings_text = "\n\n".join([
            f"Source: {finding['source_title'][:50]}...\nFinding: {finding['finding'][:200]}..."
            for finding in limited_findings
        ])
        
        progress.update(task_id, advance=25, description="📝 Phase 4: Generating comprehensive analysis...")
        
        # Generate final comprehensive summary with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Shorter, more focused prompt to prevent timeouts
                final_prompt = f"""
Based on research about "{query}", provide a structured report using these findings:

{findings_text}

Structure your response as:

## Executive Summary
2-3 sentences overview of key insights.

## Key Findings
- List 3-5 most important discoveries
- Include supporting evidence

## Conclusions
Main takeaways and their importance.

Keep the response concise but comprehensive. Focus on actionable insights.
"""
                
                progress.update(task_id, advance=30, description="📝 Phase 4: Finalizing report structure...")
                
                final_summary = self.llm.generate(final_prompt)
                self.research_data['final_summary'] = final_summary
                
                progress.update(task_id, advance=20, description="✅ Phase 4: Final report complete!")
                
                return final_summary
                
            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(f"[yellow]⚠️ Final summary attempt {attempt + 1} failed, retrying with shorter prompt...[/yellow]")
                    # For retry, use an even shorter prompt
                    final_prompt = f"""
Summarize research findings about "{query}":

{findings_text[:500]}...

Provide:
1. Key insights (2-3 points)
2. Main conclusions
3. Recommendations

Keep response under 300 words.
"""
                    continue
                else:
                    # If all retries fail, provide a structured fallback summary
                    error_summary = f"""
## Research Summary: {query}

### Status
Final summary generation encountered technical difficulties after {max_retries} attempts.
Error: {str(e)}

### Key Findings Discovered
"""
                    for i, finding in enumerate(limited_findings, 1):
                        error_summary += f"\n{i}. **{finding['source_title'][:50]}...**\n"
                        error_summary += f"   Finding: {finding['finding'][:150]}...\n"
                    
                    error_summary += f"""
### Research Statistics
- Sources Analyzed: {len(self.research_data.get('analyzed_sources', []))}
- Key Findings: {len(key_findings)}
- Query: {query}

### Note
While the AI summary generation failed, the raw research findings above provide valuable insights about {query}.
"""
                    
                    self.research_data['final_summary'] = error_summary
                    progress.update(task_id, advance=20, description="⚠️ Phase 4: Fallback report generated")
                    return error_summary
    
    async def _generate_source_summary(self, title: str, content: str, query: str) -> str:
        """Generate a summary for a specific source with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Limit content length to prevent token overflow
                limited_content = content[:1000] if len(content) > 1000 else content
                
                prompt = f"""
Summarize the key points from this source that are relevant to the query "{query}":

Source: {title}
Content: {limited_content}

Provide a concise 2-3 sentence summary focusing on the most relevant information.
"""
                return self.llm.generate(prompt)
            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(f"[yellow]⚠️ Summary generation attempt {attempt + 1} failed, retrying...[/yellow]")
                    continue
                else:
                    return f"Summary generation failed after {max_retries} attempts: {str(e)}"
    
    async def _extract_key_finding(self, source: Dict[str, Any], query: str) -> str:
        """Extract the most important finding from a source with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Limit content length to prevent token overflow
                limited_content = source['content'][:800] if len(source['content']) > 800 else source['content']
                
                prompt = f"""
From this source about "{query}", extract the single most important finding or insight:

Source: {source['title']}
Content: {limited_content}

Provide one key finding in 1-2 sentences that directly addresses the research query.
"""
                return self.llm.generate(prompt)
            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(f"[yellow]⚠️ Key finding extraction attempt {attempt + 1} failed, retrying...[/yellow]")
                    continue
                else:
                    return f"Key finding extraction failed after {max_retries} attempts: {str(e)}"
    
    async def _identify_themes(self, key_findings: List[Dict[str, Any]]) -> List[str]:
        """Identify common themes across findings with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Limit findings to prevent token overflow
                limited_findings = key_findings[:5]  # Only use top 5 findings
                findings_text = "\n".join([f"- {finding['finding'][:100]}..." for finding in limited_findings])
                
                prompt = f"""
Identify 3-5 main themes from these research findings:

{findings_text}

Return only the theme names, one per line, without explanations.
"""
                themes_response = self.llm.generate(prompt)
                themes = [theme.strip().replace('-', '').strip() for theme in themes_response.split('\n') if theme.strip()]
                return themes[:5]  # Limit to 5 themes
            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(f"[yellow]⚠️ Theme identification attempt {attempt + 1} failed, retrying...[/yellow]")
                    continue
                else:
                    return ["General Findings", "Key Insights", "Main Points"]
    
    async def _generate_theme_summary(self, theme: str, key_findings: List[Dict[str, Any]]) -> str:
        """Generate a summary for a specific theme with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                relevant_findings = [f for f in key_findings if theme.lower() in f['finding'].lower()]
                if not relevant_findings:
                    return f"No specific findings related to {theme}"
                
                # Limit findings to prevent token overflow
                limited_findings = relevant_findings[:3]  # Only use top 3 relevant findings
                findings_text = "\n".join([f"- {finding['finding'][:100]}..." for finding in limited_findings])
                
                prompt = f"""
Summarize the findings related to "{theme}":

{findings_text}

Provide a 2-3 sentence summary of this theme.
"""
                return self.llm.generate(prompt)
            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(f"[yellow]⚠️ Theme summary attempt {attempt + 1} failed, retrying...[/yellow]")
                    continue
                else:
                    return f"Theme summary generation failed after {max_retries} attempts: {str(e)}"
    
    def _calculate_relevance_score(self, content: str, query: str) -> float:
        """Calculate relevance score based on query terms in content."""
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        score = 0
        for term in query_terms:
            score += content_lower.count(term)
        
        # Normalize by content length
        return score / max(len(content.split()), 1) * 100
    
    def _display_search_summary(self, results: List[Dict[str, Any]]) -> None:
        """Display search results summary."""
        table = Table(title="🔍 Search Results Summary")
        table.add_column("No.", style="cyan", width=4)
        table.add_column("Title", style="yellow", width=50)
        table.add_column("URL", style="blue", width=40)
        
        for i, result in enumerate(results[:8], 1):
            title = result.get('title', 'No title')[:47] + "..." if len(result.get('title', '')) > 50 else result.get('title', 'No title')
            url = result.get('url', 'No URL')[:37] + "..." if len(result.get('url', '')) > 40 else result.get('url', 'No URL')
            table.add_row(str(i), title, url)
        
        console.print(table)
    
    def _display_source_analysis(self, source: Dict[str, Any], index: int) -> None:
        """Display analysis of individual source."""
        console.print(Panel.fit(
            f"📄 [bold]Source {index}:[/bold] {source['title'][:60]}...\n"
            f"🔗 URL: {source['url'][:70]}...\n"
            f"📊 Relevance Score: {source['relevance_score']:.1f}\n"
            f"📝 Word Count: {source['word_count']}\n"
            f"💡 [dim]Summary: {source['summary'][:100]}...[/dim]",
            title=f"Source Analysis #{index}",
            border_style="green"
        ))
    
    def _display_key_findings(self, key_findings: List[Dict[str, Any]], intermediate_summaries: List[Dict[str, Any]]) -> None:
        """Display key findings and intermediate summaries."""
        # Display key findings
        console.print(Panel.fit(
            "🔍 [bold cyan]Key Findings Extracted[/bold cyan]\n" +
            "\n".join([f"• {finding['finding'][:100]}..." for finding in key_findings[:5]]),
            title="🧠 Research Insights",
            border_style="yellow"
        ))
        
        # Display theme summaries
        if intermediate_summaries:
            console.print(Panel.fit(
                "📋 [bold magenta]Identified Themes[/bold magenta]\n" +
                "\n".join([f"🎯 {summary['theme']}: {summary['summary'][:80]}..." for summary in intermediate_summaries]),
                title="🎨 Theme Analysis",
                border_style="magenta"
            ))
    
    async def _display_comprehensive_results(self) -> None:
        """Display the final comprehensive research results."""
        console.print("\n" + "="*80)
        console.print(Panel.fit(
            f"🎉 [bold green]Research Complete![/bold green]\n"
            f"📋 Query: [yellow]{self.research_data['query']}[/yellow]\n"
            f"🔍 Sources Found: {len(self.research_data['search_results'])}\n"
            f"📄 Sources Analyzed: {len(self.research_data['analyzed_sources'])}\n"
            f"💡 Key Findings: {len(self.research_data['key_findings'])}\n"
            f"🎯 Themes Identified: {len(self.research_data['intermediate_summaries'])}",
            title="📊 Research Statistics",
            border_style="green"
        ))
        
        # Display final summary
        console.print(Panel(
            self.research_data['final_summary'],
            title=f"📝 Final Research Report: {self.research_data['query']}",
            border_style="blue"
        ))
        
        # Display sources used
        if self.research_data['analyzed_sources']:
            console.print("\n📚 [bold]Sources Analyzed:[/bold]")
            for i, source in enumerate(self.research_data['analyzed_sources'], 1):
                console.print(f"  {i}. [blue]{source['title']}[/blue]")
                console.print(f"     {source['url']}")
                console.print(f"     Relevance: {source['relevance_score']:.1f} | Words: {source['word_count']}") 