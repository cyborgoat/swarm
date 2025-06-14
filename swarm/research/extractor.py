"""
Content Extractor - Handles web content extraction from sources.
"""

from typing import Dict, Any, Optional
from rich.console import Console

from swarm.web.browser import Browser

console = Console()


class ContentExtractor:
    """Handles content extraction from web sources with intelligent depth adjustment."""
    
    def __init__(self, browser: Browser, verbose: bool = False):
        self.browser = browser
        self.verbose = verbose
    
    async def extract_source_content(
        self, 
        url: str, 
        title: str, 
        query: str, 
        max_length: int = 3000,
        deep_extraction: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Extract content from a web source with optional deep extraction.
        
        Args:
            url: Source URL
            title: Source title
            query: Research query for focused extraction
            max_length: Maximum content length to extract
            deep_extraction: Whether to extract more content for better analysis
            
        Returns:
            Content data or None if extraction fails
        """
        try:
            # Ensure browser session is active
            if not hasattr(self.browser, '_session_active') or not self.browser._session_active:
                await self.browser.start_session()
            
            # Navigate to the URL
            nav_result = await self.browser.navigate_to_url(url)
            
            if nav_result.get('status') != 'success':
                if self.verbose:
                    console.print(f"[yellow]⚠️ Navigation failed for: {title[:50]}...[/yellow]")
                return None
            
            # Extract page content with appropriate depth
            content_result = await self.browser.extract_page_content(
                query=query,
                max_length=max_length
            )
            
            if content_result.get('status') == 'success' and content_result.get('content'):
                content = content_result['content']
                word_count = len(content.split())
                
                if self.verbose and deep_extraction:
                    console.print(f"[dim]🔍 Deep extraction: {word_count} words from {title[:50]}...[/dim]")
                
                return {
                    'title': title,
                    'url': url,
                    'content': content,
                    'word_count': word_count,
                    'extraction_depth': 'deep' if deep_extraction else 'normal'
                }
            else:
                if self.verbose:
                    console.print(f"[yellow]⚠️ Content extraction failed for: {title[:50]}...[/yellow]")
                return None
                
        except Exception as e:
            if self.verbose:
                console.print(f"[red]❌ Error extracting content from {title[:50]}...: {str(e)}[/red]")
            return None
    
    async def extract_with_retry(
        self,
        url: str,
        title: str,
        query: str,
        config,
        attempt: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Extract content with intelligent retry logic based on relevance and word count.
        
        Args:
            url: Source URL
            title: Source title
            query: Research query
            config: Research configuration
            attempt: Current attempt number
            
        Returns:
            Content data or None if all attempts fail
        """
        # Determine extraction parameters based on attempt
        if attempt == 1:
            max_length = config.content_limit
            deep_extraction = False
        else:
            max_length = config.deep_content_limit
            deep_extraction = True
            
        content_data = await self.extract_source_content(
            url=url,
            title=title,
            query=query,
            max_length=max_length,
            deep_extraction=deep_extraction
        )
        
        if not content_data:
            return None
        
        # Check if we need to retry with deeper extraction
        word_count = content_data['word_count']
        
        if (attempt < config.max_retry_attempts and 
            word_count < config.min_word_count and 
            not deep_extraction):
            
            if self.verbose:
                console.print(f"[yellow]🔄 Low word count ({word_count}), retrying with deep extraction...[/yellow]")
            
            return await self.extract_with_retry(
                url=url,
                title=title,
                query=query,
                config=config,
                attempt=attempt + 1
            )
        
        return content_data 