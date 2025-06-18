"""
Browser Extractor - Handles content extraction and page analysis.
"""

import logging
import re
from typing import Any

from playwright.async_api import Page

from swarm.core.exceptions import BrowserError
from swarm.utils.exception_handler import handle_async_browser_exceptions

from .utils import BrowserUtils

logger = logging.getLogger(__name__)


class BrowserExtractor:
    """Handles browser content extraction with enhanced capabilities."""

    def __init__(self, page: Page):
        """Initialize extractor with page reference."""
        self.page = page
        self.utils = BrowserUtils(page)

    @handle_async_browser_exceptions
    async def extract_page_content(self, query: str | None = None, max_length: int = 10000) -> dict[str, Any]:
        """
        Extract page content with enhanced filtering and processing.

        Args:
            query: Optional search query to filter content
            max_length: Maximum content length

        Returns:
            Extracted content information
        """
        if not self.page:
            raise BrowserError("No active page available for content extraction")

        try:
            logger.info(f"📄 Extracting page content (max_length: {max_length})")

            # Extract main content using multiple strategies
            content = await self._extract_main_content()

            if not content:
                # Fallback to body text
                content = await self.page.inner_text("body")

            # Clean and process content
            content = self._clean_content(content)

            # Filter by query if provided
            if query:
                content = self._filter_content_by_query(content, query)

            # Truncate to max_length
            truncated = len(content) > max_length
            if truncated:
                content = content[:max_length] + "..."

            # Extract additional metadata
            metadata = await self._extract_page_metadata()

            logger.info(f"✅ Extracted {len(content)} characters of content")

            return {
                "status": "success",
                "content": content,
                "length": len(content),
                "query": query,
                "truncated": truncated,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"❌ Content extraction failed: {e}")
            raise BrowserError(f"Content extraction failed: {str(e)}")

    async def extract_links(self, filter_internal: bool = False) -> dict[str, Any]:
        """
        Extract all links from the page.

        Args:
            filter_internal: Whether to filter internal links only

        Returns:
            Links information
        """
        try:
            logger.info("🔗 Extracting page links")

            links = []
            current_domain = self._get_domain_from_url(self.page.url)

            # Get all link elements
            link_elements = await self.page.get_by_role("link").all()

            for link in link_elements:
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute("href")

                    if not href or not text.strip():
                        continue

                    # Resolve relative URLs
                    if href.startswith("/"):
                        href = f"{current_domain}{href}"
                    elif href.startswith("//"):
                        href = f"https:{href}"
                    elif not href.startswith(("http://", "https://")):
                        continue

                    link_domain = self._get_domain_from_url(href)
                    is_internal = link_domain == current_domain

                    # Filter if requested
                    if filter_internal and not is_internal:
                        continue

                    links.append(
                        {
                            "text": text.strip()[:100],
                            "href": href,
                            "domain": link_domain,
                            "is_internal": is_internal,
                        }
                    )

                except Exception:
                    continue

            logger.info(f"✅ Extracted {len(links)} links")

            return {
                "status": "success",
                "links": links,
                "total_count": len(links),
                "current_domain": current_domain,
            }

        except Exception as e:
            logger.error(f"❌ Link extraction failed: {e}")
            raise BrowserError(f"Link extraction failed: {str(e)}")

    async def extract_images(self, include_data_urls: bool = False) -> dict[str, Any]:
        """
        Extract all images from the page.

        Args:
            include_data_urls: Whether to include data URLs

        Returns:
            Images information
        """
        try:
            logger.info("🖼️ Extracting page images")

            images = []
            current_domain = self._get_domain_from_url(self.page.url)

            # Get all image elements
            img_elements = await self.page.locator("img").all()

            for img in img_elements:
                try:
                    src = await img.get_attribute("src")
                    alt = await img.get_attribute("alt") or ""
                    title = await img.get_attribute("title") or ""

                    if not src:
                        continue

                    # Skip data URLs if not requested
                    if not include_data_urls and src.startswith("data:"):
                        continue

                    # Resolve relative URLs
                    if src.startswith("/"):
                        src = f"{current_domain}{src}"
                    elif src.startswith("//"):
                        src = f"https:{src}"

                    # Get image dimensions if possible
                    width = await img.get_attribute("width") or ""
                    height = await img.get_attribute("height") or ""

                    images.append(
                        {
                            "src": src,
                            "alt": alt[:100],
                            "title": title[:100],
                            "width": width,
                            "height": height,
                            "is_data_url": src.startswith("data:"),
                        }
                    )

                except Exception:
                    continue

            logger.info(f"✅ Extracted {len(images)} images")

            return {
                "status": "success",
                "images": images,
                "total_count": len(images),
            }

        except Exception as e:
            logger.error(f"❌ Image extraction failed: {e}")
            raise BrowserError(f"Image extraction failed: {str(e)}")

    async def extract_forms(self) -> dict[str, Any]:
        """
        Extract all forms from the page.

        Returns:
            Forms information
        """
        try:
            logger.info("📝 Extracting page forms")

            forms = []

            # Get all form elements
            form_elements = await self.page.locator("form").all()

            for i, form in enumerate(form_elements):
                try:
                    action = await form.get_attribute("action") or ""
                    method = await form.get_attribute("method") or "GET"
                    name = await form.get_attribute("name") or f"form_{i}"

                    # Get form inputs
                    inputs = []
                    input_elements = await form.locator("input, textarea, select").all()

                    for input_elem in input_elements:
                        try:
                            input_type = await input_elem.get_attribute("type") or "text"
                            input_name = await input_elem.get_attribute("name") or ""
                            input_id = await input_elem.get_attribute("id") or ""
                            placeholder = await input_elem.get_attribute("placeholder") or ""
                            required = await input_elem.get_attribute("required") is not None

                            inputs.append(
                                {
                                    "type": input_type,
                                    "name": input_name,
                                    "id": input_id,
                                    "placeholder": placeholder,
                                    "required": required,
                                }
                            )

                        except Exception:
                            continue

                    forms.append(
                        {
                            "index": i,
                            "name": name,
                            "action": action,
                            "method": method.upper(),
                            "inputs": inputs,
                            "input_count": len(inputs),
                        }
                    )

                except Exception:
                    continue

            logger.info(f"✅ Extracted {len(forms)} forms")

            return {
                "status": "success",
                "forms": forms,
                "total_count": len(forms),
            }

        except Exception as e:
            logger.error(f"❌ Form extraction failed: {e}")
            raise BrowserError(f"Form extraction failed: {str(e)}")

    async def take_screenshot(self, path: str | None = None, full_page: bool = True) -> dict[str, Any]:
        """
        Take screenshot with enhanced options.

        Args:
            path: Optional path to save screenshot
            full_page: Whether to capture full page

        Returns:
            Screenshot result information
        """
        try:
            if not path:
                # Generate filename based on page title and URL
                title = await self.page.title()
                safe_title = re.sub(r"[^\w\-_.]", "_", title)[:50]
                path = f"screenshot_{safe_title}.png"

            # Take screenshot with options
            await self.page.screenshot(
                path=path, full_page=full_page, type="png", quality=90 if not full_page else None
            )

            logger.info(f"✅ Screenshot saved: {path}")

            return {
                "status": "success",
                "path": path,
                "full_page": full_page,
                "message": f"Screenshot saved to {path}",
            }

        except Exception as e:
            logger.error(f"❌ Screenshot failed: {e}")
            raise BrowserError(f"Screenshot failed: {str(e)}")

    async def _extract_main_content(self) -> str:
        """Extract main content using semantic selectors."""
        # Common content selectors in order of preference
        content_selectors = [
            "main",
            "article",
            "[role='main']",
            ".content",
            ".main-content",
            "#content",
            "#main",
            ".post-content",
            ".entry-content",
            ".article-content",
        ]

        for selector in content_selectors:
            try:
                elements = await self.page.locator(selector).all()
                if elements:
                    # Get the largest content block
                    largest_content = ""
                    for element in elements:
                        try:
                            text = await element.inner_text()
                            if len(text) > len(largest_content):
                                largest_content = text
                        except Exception:
                            continue

                    if largest_content.strip():
                        return largest_content
            except Exception:
                continue

        return ""

    def _clean_content(self, content: str) -> str:
        """Clean and normalize content."""
        if not content:
            return ""

        # Normalize whitespace
        content = re.sub(r"\s+", " ", content)

        # Remove excessive line breaks
        content = re.sub(r"\n{3,}", "\n\n", content)

        # Clean up common unwanted patterns
        content = re.sub(r"Advertisement\s*", "", content)
        content = re.sub(r"Skip to content\s*", "", content)
        content = re.sub(r"Cookie notice\s*.*?\n", "", content, flags=re.IGNORECASE)

        return content.strip()

    def _filter_content_by_query(self, content: str, query: str) -> str:
        """Filter content based on search query."""
        if not query or not content:
            return content

        query_words = [word.lower() for word in query.split()]
        sentences = content.split(".")
        relevant_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_lower = sentence.lower()

            # Score sentence based on query word matches
            score = sum(1 for word in query_words if word in sentence_lower)

            # Include sentences with at least one query word
            if score > 0:
                relevant_sentences.append((sentence, score))

        if relevant_sentences:
            # Sort by score and take top sentences
            relevant_sentences.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [s[0] for s in relevant_sentences[:20]]  # Top 20 sentences
            return ". ".join(top_sentences)

        return content  # Return full content if no matches

    async def _extract_page_metadata(self) -> dict[str, Any]:
        """Extract page metadata."""
        metadata = {}

        try:
            # Basic metadata
            metadata["title"] = await self.page.title()
            metadata["url"] = self.page.url

            # Meta tags
            meta_elements = await self.page.locator("meta").all()
            meta_data = {}

            for meta in meta_elements:
                try:
                    name = await meta.get_attribute("name")
                    property_attr = await meta.get_attribute("property")
                    content = await meta.get_attribute("content")

                    if content:
                        if name:
                            meta_data[name] = content
                        elif property_attr:
                            meta_data[property_attr] = content
                except Exception:
                    continue

            metadata["meta"] = meta_data

            # Headings structure
            headings = []
            for level in range(1, 7):
                h_elements = await self.page.locator(f"h{level}").all()
                for h in h_elements:
                    try:
                        text = await h.inner_text()
                        if text.strip():
                            headings.append({"level": level, "text": text.strip()[:100]})
                    except Exception:
                        continue

            metadata["headings"] = headings[:10]  # Limit to 10 headings

        except Exception as e:
            logger.debug(f"Could not extract metadata: {e}")

        return metadata

    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            return ""
