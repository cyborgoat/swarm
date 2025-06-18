"""
Browser Navigator - Handles navigation and URL operations.
"""

import logging
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import Page

from swarm.core.exceptions import BrowserNavigationError
from swarm.utils.exception_handler import handle_async_browser_exceptions

logger = logging.getLogger(__name__)


class BrowserNavigator:
    """Handles browser navigation operations with enhanced reliability."""

    def __init__(self, page: Page):
        """Initialize navigator with page reference."""
        self.page = page

    @handle_async_browser_exceptions
    async def navigate_to_url(self, url: str, wait_until: str = "domcontentloaded") -> dict[str, Any]:
        """
        Navigate to URL with enhanced error handling and validation.

        Args:
            url: URL to navigate to
            wait_until: When to consider navigation complete

        Returns:
            Navigation result with page information
        """
        if not self.page:
            raise BrowserNavigationError("No active page available for navigation")

        # Normalize and validate URL
        normalized_url = self._normalize_url(url)
        if not self._is_valid_url(normalized_url):
            raise BrowserNavigationError(f"Invalid URL: {url}")

        try:
            logger.info(f"🌐 Navigating to: {normalized_url}")

            # Navigate with retries and enhanced options
            response = await self._navigate_with_retry(normalized_url, wait_until)

            # Get page information
            title = await self.page.title()
            current_url = self.page.url
            response_status = response.status if response else None

            # Validate successful navigation
            if response_status and response_status >= 400:
                logger.warning(f"⚠️ Navigation returned HTTP {response_status}")

            logger.info(f"✅ Successfully navigated to: {title} ({current_url})")

            return {
                "status": "success",
                "url": current_url,
                "title": title,
                "response_status": response_status,
                "message": f"Successfully navigated to {title}",
                "redirect_chain": await self._get_redirect_chain(response) if response else [],
            }

        except Exception as e:
            logger.error(f"❌ Navigation failed for {normalized_url}: {e}")
            raise BrowserNavigationError(f"Navigation failed: {str(e)}", url=normalized_url)

    async def get_current_url(self) -> str:
        """Get current page URL."""
        if not self.page:
            return "about:blank"
        return self.page.url

    async def get_page_title(self) -> str:
        """Get current page title."""
        if not self.page:
            return ""
        try:
            return await self.page.title()
        except Exception as e:
            logger.warning(f"Could not get page title: {e}")
            return ""

    async def go_back(self) -> dict[str, Any]:
        """Navigate back in browser history."""
        try:
            await self.page.go_back(wait_until="domcontentloaded")
            current_url = await self.get_current_url()
            title = await self.get_page_title()

            return {"status": "success", "url": current_url, "title": title, "message": "Successfully navigated back"}
        except Exception as e:
            logger.error(f"❌ Go back failed: {e}")
            raise BrowserNavigationError(f"Go back failed: {str(e)}")

    async def go_forward(self) -> dict[str, Any]:
        """Navigate forward in browser history."""
        try:
            await self.page.go_forward(wait_until="domcontentloaded")
            current_url = await self.get_current_url()
            title = await self.get_page_title()

            return {
                "status": "success",
                "url": current_url,
                "title": title,
                "message": "Successfully navigated forward",
            }
        except Exception as e:
            logger.error(f"❌ Go forward failed: {e}")
            raise BrowserNavigationError(f"Go forward failed: {str(e)}")

    async def reload(self, wait_until: str = "domcontentloaded") -> dict[str, Any]:
        """Reload the current page."""
        try:
            await self.page.reload(wait_until=wait_until)
            current_url = await self.get_current_url()
            title = await self.get_page_title()

            return {"status": "success", "url": current_url, "title": title, "message": "Page reloaded successfully"}
        except Exception as e:
            logger.error(f"❌ Page reload failed: {e}")
            raise BrowserNavigationError(f"Page reload failed: {str(e)}")

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by adding protocol if missing."""
        url = url.strip()

        # Add protocol if missing
        if not url.startswith(("http://", "https://", "file://", "data:")):
            # Check if it's likely a domain (contains a dot)
            if "." in url and not url.startswith("localhost"):
                url = "https://" + url
            elif url.startswith("localhost") or url.startswith("127.0.0.1"):
                url = "http://" + url
            else:
                # Assume it's a search query if no clear URL structure
                url = "https://" + url

        return url

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            parsed = urlparse(url)
            return all(
                [
                    parsed.scheme in ("http", "https", "file", "data"),
                    parsed.netloc or parsed.path,  # Either domain or path for file URLs
                ]
            )
        except Exception:
            return False

    async def _navigate_with_retry(self, url: str, wait_until: str, max_retries: int = 3):
        """Navigate with retry logic for better reliability."""
        last_error = None

        for attempt in range(max_retries):
            try:
                # Different wait strategies for retries
                if attempt == 0:
                    # First attempt: fast load
                    response = await self.page.goto(url, wait_until=wait_until, timeout=30000)
                elif attempt == 1:
                    # Second attempt: wait for network idle
                    response = await self.page.goto(url, wait_until="networkidle", timeout=45000)
                else:
                    # Final attempt: just load
                    response = await self.page.goto(url, wait_until="load", timeout=60000)

                return response

            except Exception as e:
                last_error = e
                logger.warning(f"Navigation attempt {attempt + 1} failed for {url}: {e}")

                if attempt < max_retries - 1:
                    # Wait before retry
                    await self.page.wait_for_timeout(1000 * (attempt + 1))
                    continue

        # All retries failed
        raise last_error

    async def _get_redirect_chain(self, response) -> list[dict[str, Any]]:
        """Get the redirect chain from the response."""
        try:
            if not response:
                return []

            chain = []
            current = response

            while current:
                chain.append(
                    {
                        "url": current.url,
                        "status": current.status,
                        "headers": dict(current.headers) if hasattr(current, "headers") else {},
                    }
                )

                # Get the next response in the chain
                current = getattr(current, "request", {}).get("redirected_from")
                if not current:
                    break

            return chain
        except Exception as e:
            logger.debug(f"Could not get redirect chain: {e}")
            return []
