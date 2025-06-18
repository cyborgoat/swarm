"""
Browser Utilities - Helper functions for element finding and common operations.
"""

import logging
from typing import Any

from playwright.async_api import Locator, Page

logger = logging.getLogger(__name__)


class BrowserUtils:
    """Utility functions for browser operations and element finding."""

    def __init__(self, page: Page):
        """Initialize utils with page reference."""
        self.page = page

    async def find_element_by_text(self, text: str, exact: bool = True) -> Locator | None:
        """
        Find element by text with multiple strategies.

        Args:
            text: Text to search for
            exact: Whether to match exact text

        Returns:
            Locator if found, None otherwise
        """
        if not self.page:
            return None

        strategies = [
            # Strategy 1: Button role
            lambda: self.page.get_by_role("button", name=text, exact=exact),
            # Strategy 2: Link role
            lambda: self.page.get_by_role("link", name=text, exact=exact),
            # Strategy 3: Generic text
            lambda: self.page.get_by_text(text, exact=exact),
            # Strategy 4: Text selector
            lambda: self.page.locator(f"text={text}"),
        ]

        for strategy in strategies:
            try:
                locator = strategy()
                if await locator.count() > 0:
                    logger.debug(f"Found element with text '{text}' using strategy")
                    return locator.first
            except Exception as e:
                logger.debug(f"Strategy failed for text '{text}': {e}")
                continue

        return None

    async def find_input_by_label(self, label: str) -> Locator | None:
        """
        Find input/textarea by associated label.

        Args:
            label: Label text or placeholder

        Returns:
            Locator if found, None otherwise
        """
        if not self.page:
            return None

        strategies = [
            # Strategy 1: Direct label association
            lambda: self.page.get_by_label(label),
            # Strategy 2: Placeholder text
            lambda: self.page.get_by_placeholder(label),
            # Strategy 3: Label has-text with input
            lambda: self.page.locator(f"label:has-text('{label}') >> input, label:has-text('{label}') >> textarea"),
            # Strategy 4: Name attribute contains label
            lambda: self.page.locator(f"input[name*='{label}'], textarea[name*='{label}']"),
            # Strategy 5: Placeholder contains label
            lambda: self.page.locator(f"input[placeholder*='{label}'], textarea[placeholder*='{label}']"),
        ]

        for strategy in strategies:
            try:
                locator = strategy()
                if await locator.count() > 0:
                    logger.debug(f"Found input with label '{label}' using strategy")
                    return locator.first
            except Exception as e:
                logger.debug(f"Strategy failed for label '{label}': {e}")
                continue

        return None

    async def find_select_by_label(self, label: str) -> Locator | None:
        """
        Find select element by label.

        Args:
            label: Label text

        Returns:
            Locator if found, None otherwise
        """
        if not self.page:
            return None

        strategies = [
            # Strategy 1: Direct label association
            lambda: self.page.get_by_label(label),
            # Strategy 2: Combobox role
            lambda: self.page.get_by_role("combobox", name=label),
            # Strategy 3: Name attribute
            lambda: self.page.locator(f"select[name*='{label}']"),
            # Strategy 4: Label has-text with select
            lambda: self.page.locator(f"label:has-text('{label}') >> select"),
        ]

        for strategy in strategies:
            try:
                locator = strategy()
                if await locator.count() > 0:
                    logger.debug(f"Found select with label '{label}' using strategy")
                    return locator.first
            except Exception as e:
                logger.debug(f"Strategy failed for select '{label}': {e}")
                continue

        return None

    async def wait_for_element_visible(self, locator: Locator, timeout: int = 5000) -> bool:
        """
        Wait for element to be visible.

        Args:
            locator: Element locator
            timeout: Timeout in milliseconds

        Returns:
            True if element became visible, False otherwise
        """
        try:
            await locator.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    async def wait_for_element_clickable(self, locator: Locator, timeout: int = 5000) -> bool:
        """
        Wait for element to be clickable.

        Args:
            locator: Element locator
            timeout: Timeout in milliseconds

        Returns:
            True if element became clickable, False otherwise
        """
        try:
            # Check if element is visible and enabled
            await locator.wait_for(state="visible", timeout=timeout)
            if await locator.is_enabled():
                return True
            return False
        except Exception:
            return False

    async def scroll_to_element(self, locator: Locator) -> bool:
        """
        Scroll element into view.

        Args:
            locator: Element locator

        Returns:
            True if scroll was successful, False otherwise
        """
        try:
            await locator.scroll_into_view_if_needed()
            return True
        except Exception as e:
            logger.debug(f"Scroll to element failed: {e}")
            return False

    async def get_element_text(self, locator: Locator) -> str:
        """
        Get text content from element.

        Args:
            locator: Element locator

        Returns:
            Element text content
        """
        try:
            return await locator.inner_text()
        except Exception:
            return ""

    async def get_element_attribute(self, locator: Locator, attribute: str) -> str:
        """
        Get attribute value from element.

        Args:
            locator: Element locator
            attribute: Attribute name

        Returns:
            Attribute value or empty string
        """
        try:
            value = await locator.get_attribute(attribute)
            return value or ""
        except Exception:
            return ""

    async def is_element_visible(self, locator: Locator) -> bool:
        """
        Check if element is visible.

        Args:
            locator: Element locator

        Returns:
            True if visible, False otherwise
        """
        try:
            return await locator.is_visible()
        except Exception:
            return False

    async def is_element_enabled(self, locator: Locator) -> bool:
        """
        Check if element is enabled.

        Args:
            locator: Element locator

        Returns:
            True if enabled, False otherwise
        """
        try:
            return await locator.is_enabled()
        except Exception:
            return False

    async def get_page_elements_summary(self) -> dict[str, list[dict[str, Any]]]:
        """
        Get summary of interactive elements on the page.

        Returns:
            Dictionary with categorized elements
        """
        elements = {"buttons": [], "inputs": [], "links": [], "selects": []}

        try:
            # Get buttons
            buttons = await self.page.get_by_role("button").all()
            for i, button in enumerate(buttons):
                try:
                    text = await button.inner_text()
                    if text.strip():
                        elements["buttons"].append(
                            {
                                "index": i,
                                "text": text.strip()[:100],  # Limit text length
                                "visible": await button.is_visible(),
                                "enabled": await button.is_enabled(),
                            }
                        )
                except Exception:
                    continue

            # Get input fields
            inputs = await self.page.locator("input, textarea").all()
            for i, input_elem in enumerate(inputs):
                try:
                    input_type = await input_elem.get_attribute("type") or "text"
                    placeholder = await input_elem.get_attribute("placeholder") or ""
                    name = await input_elem.get_attribute("name") or ""

                    # Try to find associated label
                    label = ""
                    try:
                        input_id = await input_elem.get_attribute("id")
                        if input_id:
                            label_elem = self.page.locator(f"label[for='{input_id}']")
                            if await label_elem.count() > 0:
                                label = await label_elem.inner_text()
                    except Exception:
                        pass

                    elements["inputs"].append(
                        {
                            "index": i,
                            "type": input_type,
                            "label": label[:50] if label else "",
                            "placeholder": placeholder[:50] if placeholder else "",
                            "name": name[:50] if name else "",
                            "visible": await input_elem.is_visible(),
                            "enabled": await input_elem.is_enabled(),
                        }
                    )
                except Exception:
                    continue

            # Get links
            links = await self.page.get_by_role("link").all()
            for i, link in enumerate(links):
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute("href") or ""
                    if text.strip():
                        elements["links"].append(
                            {
                                "index": i,
                                "text": text.strip()[:100],
                                "href": href[:100] if href else "",
                                "visible": await link.is_visible(),
                            }
                        )
                except Exception:
                    continue

            # Get select elements
            selects = await self.page.locator("select").all()
            for i, select in enumerate(selects):
                try:
                    name = await select.get_attribute("name") or ""

                    # Try to find associated label
                    label = ""
                    try:
                        select_id = await select.get_attribute("id")
                        if select_id:
                            label_elem = self.page.locator(f"label[for='{select_id}']")
                            if await label_elem.count() > 0:
                                label = await label_elem.inner_text()
                    except Exception:
                        pass

                    # Get options
                    options = []
                    try:
                        option_elements = await select.locator("option").all()
                        for option in option_elements:
                            option_text = await option.inner_text()
                            option_value = await option.get_attribute("value") or ""
                            if option_text.strip():
                                options.append({"text": option_text.strip()[:50], "value": option_value[:50]})
                    except Exception:
                        pass

                    elements["selects"].append(
                        {
                            "index": i,
                            "name": name[:50] if name else "",
                            "label": label[:50] if label else "",
                            "options": options[:10],  # Limit options
                            "visible": await select.is_visible(),
                            "enabled": await select.is_enabled(),
                        }
                    )
                except Exception:
                    continue

        except Exception as e:
            logger.error(f"Failed to get page elements summary: {e}")

        return elements

    async def take_element_screenshot(self, locator: Locator, path: str) -> bool:
        """
        Take screenshot of a specific element.

        Args:
            locator: Element locator
            path: File path to save screenshot

        Returns:
            True if screenshot was taken successfully
        """
        try:
            await locator.screenshot(path=path)
            return True
        except Exception as e:
            logger.error(f"Failed to take element screenshot: {e}")
            return False
