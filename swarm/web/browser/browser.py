"""
Main Browser Class - Orchestrates all browser components in a clean, modular design.
"""

import logging
from typing import Any

from swarm.core.config import BrowserConfig
from swarm.core.exceptions import BrowserError, BrowserSessionError

from .extractor import BrowserExtractor
from .interactor import BrowserInteractor
from .navigator import BrowserNavigator
from .session import BrowserSession
from .utils import BrowserUtils

logger = logging.getLogger(__name__)


class Browser:
    """
    Main browser automation class that orchestrates all components.

    This class provides a clean, modular interface to browser automation
    by composing focused components for different responsibilities.
    """

    def __init__(self, config: BrowserConfig):
        """
        Initialize browser with configuration.

        Args:
            config: Browser configuration
        """
        self.config = config

        # Core session management
        self.session = BrowserSession(config)

        # Component modules (initialized after session starts)
        self.navigator: BrowserNavigator | None = None
        self.interactor: BrowserInteractor | None = None
        self.extractor: BrowserExtractor | None = None
        self.utils: BrowserUtils | None = None

    @property
    def is_active(self) -> bool:
        """Check if browser session is active."""
        return self.session.is_active

    @property
    def page(self):
        """Get current page reference."""
        return self.session.page

    async def start_session(self) -> dict[str, Any]:
        """
        Start browser session and initialize all components.

        Returns:
            Session status information
        """
        try:
            # Start the session
            result = await self.session.start()

            if result["status"] == "success" and self.session.page:
                # Initialize all components with the active page
                self._initialize_components()

                logger.info("🚀 Browser session and all components initialized successfully")

            return result

        except Exception as e:
            logger.error(f"❌ Failed to start browser session: {e}")
            raise

    async def close_session(self) -> dict[str, Any]:
        """
        Close browser session and cleanup all components.

        Returns:
            Closure status information
        """
        try:
            # Clean up components
            self._cleanup_components()

            # Close the session
            result = await self.session.close()

            logger.info("🔒 Browser session and components closed successfully")
            return result

        except Exception as e:
            logger.error(f"❌ Error closing browser session: {e}")
            raise

    # Navigation Methods
    async def navigate_to_url(self, url: str, wait_until: str = "domcontentloaded") -> dict[str, Any]:
        """Navigate to URL using the navigator component."""
        self._ensure_active()
        return await self.navigator.navigate_to_url(url, wait_until)

    async def get_current_url(self) -> str:
        """Get current page URL."""
        self._ensure_active()
        return await self.navigator.get_current_url()

    async def get_page_title(self) -> str:
        """Get current page title."""
        self._ensure_active()
        return await self.navigator.get_page_title()

    async def go_back(self) -> dict[str, Any]:
        """Navigate back in browser history."""
        self._ensure_active()
        return await self.navigator.go_back()

    async def go_forward(self) -> dict[str, Any]:
        """Navigate forward in browser history."""
        self._ensure_active()
        return await self.navigator.go_forward()

    async def reload(self, wait_until: str = "domcontentloaded") -> dict[str, Any]:
        """Reload the current page."""
        self._ensure_active()
        return await self.navigator.reload(wait_until)

    # Interaction Methods
    async def click_element_by_text(self, text: str, exact: bool = True, timeout: int = 5000) -> dict[str, Any]:
        """Click element by text using the interactor component."""
        self._ensure_active()
        return await self.interactor.click_element_by_text(text, exact, timeout)

    async def fill_input_by_label(
        self, label: str, value: str, clear_first: bool = True, timeout: int = 5000
    ) -> dict[str, Any]:
        """Fill input field by label using the interactor component."""
        self._ensure_active()
        return await self.interactor.fill_input_by_label(label, value, clear_first, timeout)

    async def select_dropdown_option(
        self, dropdown_label: str, option_value: str, timeout: int = 5000
    ) -> dict[str, Any]:
        """Select dropdown option using the interactor component."""
        self._ensure_active()
        return await self.interactor.select_dropdown_option(dropdown_label, option_value, timeout)

    async def hover_element_by_text(self, text: str, timeout: int = 5000) -> dict[str, Any]:
        """Hover over element by text."""
        self._ensure_active()
        return await self.interactor.hover_element_by_text(text, timeout)

    async def double_click_element_by_text(self, text: str, timeout: int = 5000) -> dict[str, Any]:
        """Double-click element by text."""
        self._ensure_active()
        return await self.interactor.double_click_element_by_text(text, timeout)

    # Content Extraction Methods
    async def extract_page_content(self, query: str | None = None, max_length: int = 10000) -> dict[str, Any]:
        """Extract page content using the extractor component."""
        self._ensure_active()
        return await self.extractor.extract_page_content(query, max_length)

    async def extract_links(self, filter_internal: bool = False) -> dict[str, Any]:
        """Extract all links from the page."""
        self._ensure_active()
        return await self.extractor.extract_links(filter_internal)

    async def extract_images(self, include_data_urls: bool = False) -> dict[str, Any]:
        """Extract all images from the page."""
        self._ensure_active()
        return await self.extractor.extract_images(include_data_urls)

    async def extract_forms(self) -> dict[str, Any]:
        """Extract all forms from the page."""
        self._ensure_active()
        return await self.extractor.extract_forms()

    async def take_screenshot(self, path: str | None = None, full_page: bool = True) -> dict[str, Any]:
        """Take screenshot using the extractor component."""
        self._ensure_active()
        return await self.extractor.take_screenshot(path, full_page)

    # Utility Methods
    async def get_page_elements(self) -> dict[str, list[dict[str, Any]]]:
        """Get summary of interactive elements on the page."""
        self._ensure_active()
        return await self.utils.get_page_elements_summary()

    async def get_session_status(self) -> dict[str, Any]:
        """Get current browser session status."""
        return await self.session.get_status()

    async def wait_for_element_visible(self, text: str, timeout: int = 5000) -> bool:
        """Wait for element with text to be visible."""
        self._ensure_active()
        locator = await self.utils.find_element_by_text(text)
        if locator:
            return await self.utils.wait_for_element_visible(locator, timeout)
        return False

    async def scroll_to_element_by_text(self, text: str) -> bool:
        """Scroll to element with specified text."""
        self._ensure_active()
        locator = await self.utils.find_element_by_text(text)
        if locator:
            return await self.utils.scroll_to_element(locator)
        return False

    # Legacy Compatibility Methods
    def browse_persistent(self, url: str) -> dict[str, Any]:
        """Legacy method for compatibility - synchronous wrapper."""
        import asyncio

        async def _browse():
            nav_result = await self.navigate_to_url(url)
            if nav_result["status"] == "success":
                content_result = await self.extract_page_content(max_length=5000)
                links_result = await self.extract_links()

                return {
                    "url": nav_result["url"],
                    "title": nav_result["title"],
                    "content": content_result.get("content", ""),
                    "links": [link["href"] for link in links_result.get("links", [])[:10]],
                }
            else:
                raise BrowserError(nav_result["message"], url=url)

        try:
            # Try to get current running loop
            asyncio.get_running_loop()
            # If we're in an async context, we need to create a task
            return asyncio.create_task(_browse())
        except RuntimeError:
            # No running loop, we can run directly
            return asyncio.run(_browse())

    def extract_text_content(self, query: str | None = None) -> str:
        """Legacy method for compatibility - synchronous wrapper."""
        import asyncio

        async def _extract():
            try:
                result = await self.extract_page_content(query, max_length=10000)
                return result.get("content", "") if result["status"] == "success" else ""
            except Exception:
                return ""

        try:
            asyncio.get_running_loop()
            return asyncio.create_task(_extract())
        except RuntimeError:
            return asyncio.run(_extract())

    # Enhanced Methods
    async def smart_search_and_click(self, search_terms: list[str], timeout: int = 10000) -> dict[str, Any]:
        """
        Smart search for elements using multiple search terms and click the best match.

        Args:
            search_terms: List of search terms in order of preference
            timeout: Timeout for finding element

        Returns:
            Click result information
        """
        self._ensure_active()

        for term in search_terms:
            try:
                result = await self.click_element_by_text(term, exact=False, timeout=timeout // len(search_terms))
                if result["status"] == "success":
                    return {
                        "status": "success",
                        "message": f"Successfully clicked element with term: '{term}'",
                        "matched_term": term,
                        "original_terms": search_terms,
                    }
            except Exception as e:
                logger.debug(f"Failed to click with term '{term}': {e}")
                continue

        raise BrowserError(f"Could not find clickable element with any of the terms: {search_terms}")

    async def smart_fill_form(self, form_data: dict[str, str], timeout: int = 5000) -> dict[str, Any]:
        """
        Smart form filling that attempts to fill multiple fields.

        Args:
            form_data: Dictionary of label -> value mappings
            timeout: Timeout for finding each element

        Returns:
            Form filling results
        """
        self._ensure_active()

        results = []
        successful_fills = 0

        for label, value in form_data.items():
            try:
                result = await self.fill_input_by_label(label, value, timeout=timeout)
                results.append(
                    {"label": label, "value": value, "status": result["status"], "message": result.get("message", "")}
                )
                if result["status"] == "success":
                    successful_fills += 1
            except Exception as e:
                results.append({"label": label, "value": value, "status": "error", "message": str(e)})

        return {
            "status": "success" if successful_fills > 0 else "error",
            "successful_fills": successful_fills,
            "total_fields": len(form_data),
            "results": results,
            "message": f"Successfully filled {successful_fills}/{len(form_data)} fields",
        }

    def _initialize_components(self) -> None:
        """Initialize all browser components with the active page."""
        if not self.session.page:
            raise BrowserSessionError("No active page available for component initialization")

        self.navigator = BrowserNavigator(self.session.page)
        self.interactor = BrowserInteractor(self.session.page)
        self.extractor = BrowserExtractor(self.session.page)
        self.utils = BrowserUtils(self.session.page)

        logger.debug("✅ All browser components initialized")

    def _cleanup_components(self) -> None:
        """Clean up all browser components."""
        self.navigator = None
        self.interactor = None
        self.extractor = None
        self.utils = None

        logger.debug("🧹 All browser components cleaned up")

    def _ensure_active(self) -> None:
        """Ensure browser session is active and components are initialized."""
        if not self.is_active:
            raise BrowserSessionError("Browser session is not active. Call start_session() first.")

        if not all([self.navigator, self.interactor, self.extractor, self.utils]):
            raise BrowserSessionError("Browser components not initialized. Session may have been corrupted.")

    def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.is_active:
            await self.close_session()
