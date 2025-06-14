"""
Image Processor - Handles image detection and markdown formatting.
"""

import re
from typing import List, Dict, Any
from rich.console import Console
from urllib.parse import urljoin

from swarm.web.browser import Browser

console = Console()


class ImageProcessor:
    """Handles image extraction and processing for research."""
    
    def __init__(self, browser: Browser, verbose: bool = False):
        self.browser = browser
        self.verbose = verbose
    
    async def extract_images(self, url: str) -> List[Dict[str, str]]:
        """
        Extract relevant images from the current page.
        
        Args:
            url: Source URL for the page
            
        Returns:
            List of image data with markdown formatting
        """
        try:
            # Get page info to extract images
            page_info = await self.browser.get_current_page_info()
            
            if not page_info.get('success'):
                return []
            
            images = []
            
            # Look for image elements in the page content
            if 'content' in page_info:
                # Find image URLs in the page content
                img_pattern = r'<img[^>]*src=["\']([^"\']+)["\'][^>]*(?:alt=["\']([^"\']*)["\'])?[^>]*>'
                matches = re.findall(img_pattern, page_info['content'], re.IGNORECASE)
                
                for match in matches:
                    img_url = match[0]
                    alt_text = match[1] if len(match) > 1 else "Image"
                    
                    # Convert relative URLs to absolute
                    img_url = self._normalize_url(img_url, url)
                    
                    # Filter for likely content images
                    if self._is_content_image(img_url, alt_text):
                        images.append({
                            'url': img_url,
                            'alt': alt_text,
                            'markdown': f"![{alt_text}]({img_url})",
                            'source_page': url
                        })
            
            # Limit to 5 images per page to avoid clutter
            result = images[:5]
            
            if result and self.verbose:
                console.print(f"[dim]🖼️ Found {len(result)} images on page[/dim]")
            
            return result
            
        except Exception as e:
            if self.verbose:
                console.print(f"[yellow]⚠️ Image extraction failed: {str(e)}[/yellow]")
            return []
    
    def _normalize_url(self, img_url: str, base_url: str) -> str:
        """Convert relative URLs to absolute URLs."""
        if img_url.startswith('//'):
            return 'https:' + img_url
        elif img_url.startswith('/'):
            return urljoin(base_url, img_url)
        elif not img_url.startswith(('http://', 'https://')):
            return urljoin(base_url, img_url)
        else:
            return img_url
    
    def _is_content_image(self, img_url: str, alt_text: str) -> bool:
        """
        Determine if an image is likely to be content-relevant.
        
        Args:
            img_url: Image URL
            alt_text: Alt text of the image
            
        Returns:
            True if image appears to be content-relevant
        """
        # Skip common non-content images
        skip_patterns = [
            'icon', 'logo', 'button', 'arrow', 'pixel', 'spacer', 
            'ads', 'tracking', 'analytics', 'beacon', 'counter'
        ]
        
        img_lower = img_url.lower()
        alt_lower = alt_text.lower()
        
        # Skip if URL or alt text contains skip patterns
        for pattern in skip_patterns:
            if pattern in img_lower or pattern in alt_lower:
                return False
        
        # Skip very small likely icon/button images
        small_sizes = ['16x16', '24x24', '32x32', '48x48', '1x1']
        if any(size in img_lower for size in small_sizes):
            return False
        
        # Skip common non-content file patterns
        skip_files = ['favicon', 'sprite', 'thumbnail', 'avatar']
        if any(pattern in img_lower for pattern in skip_files):
            return False
        
        # Include if it has descriptive alt text
        if len(alt_text.strip()) > 10:
            return True
        
        # Include if URL suggests content
        content_indicators = ['content', 'article', 'photo', 'image', 'media', 'gallery']
        if any(indicator in img_lower for indicator in content_indicators):
            return True
        
        # Include images with common content file extensions
        content_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        if any(ext in img_lower for ext in content_extensions):
            # But exclude if it's clearly an icon or small image
            if not any(skip in img_lower for skip in ['icon', 'thumb', 'small']):
                return True
        
        return False 