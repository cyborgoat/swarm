"""
Browser Interactor - Handles element interactions like click, fill, and select operations.
"""

import logging
from typing import Any

from playwright.async_api import Page

from swarm.core.exceptions import BrowserElementError
from swarm.utils.exception_handler import handle_async_browser_exceptions

from .utils import BrowserUtils

logger = logging.getLogger(__name__)


class BrowserInteractor:
    """Handles browser element interactions with enhanced reliability."""

    def __init__(self, page: Page):
        """Initialize interactor with page reference."""
        self.page = page
        self.utils = BrowserUtils(page)

    @handle_async_browser_exceptions
    async def click_element_by_text(self, text: str, exact: bool = True, timeout: int = 5000) -> dict[str, Any]:
        """
        Click element by text with enhanced reliability and multiple strategies.

        Args:
            text: Text to search for and click
            exact: Whether to match exact text
            timeout: Timeout for finding element

        Returns:
            Click result information
        """
        if not self.page:
            raise BrowserElementError("No active page available for interaction", element=text)

        try:
            logger.info(f"🖱️ Attempting to click element with text: '{text}'")

            # Find element using utility
            locator = await self.utils.find_element_by_text(text, exact)

            if not locator:
                # Try partial match if exact match failed
                if exact:
                    logger.debug(f"Exact match failed, trying partial match for: {text}")
                    locator = await self.utils.find_element_by_text(text, exact=False)

                if not locator:
                    raise BrowserElementError(f"Could not find clickable element with text: {text}", element=text)

            # Wait for element to be clickable
            if not await self.utils.wait_for_element_clickable(locator, timeout):
                # Try scrolling to element
                await self.utils.scroll_to_element(locator)
                if not await self.utils.wait_for_element_clickable(locator, timeout):
                    raise BrowserElementError(f"Element with text '{text}' is not clickable", element=text)

            # Perform click with retry logic
            await self._click_with_retry(locator, text)

            logger.info(f"✅ Successfully clicked element with text: '{text}'")

            return {
                "status": "success",
                "message": f"Successfully clicked element with text: '{text}'",
                "text": text,
                "exact_match": exact,
            }

        except BrowserElementError:
            raise
        except Exception as e:
            logger.error(f"❌ Click failed for text '{text}': {e}")
            raise BrowserElementError(f"Click failed: {str(e)}", element=text)

    @handle_async_browser_exceptions
    async def fill_input_by_label(
        self, label: str, value: str, clear_first: bool = True, timeout: int = 5000
    ) -> dict[str, Any]:
        """
        Fill input field by label with enhanced reliability.

        Args:
            label: Label text to find input field
            value: Value to fill
            clear_first: Whether to clear field before filling
            timeout: Timeout for finding element

        Returns:
            Fill result information
        """
        if not self.page:
            raise BrowserElementError("No active page available for interaction", element=label)

        try:
            logger.info(f"✏️ Attempting to fill input '{label}' with: '{value}'")

            # Find input using utility
            locator = await self.utils.find_input_by_label(label)

            if not locator:
                raise BrowserElementError(f"Could not find input field for label: {label}", element=label)

            # Wait for element to be visible and enabled
            if not await self.utils.wait_for_element_visible(locator, timeout):
                raise BrowserElementError(f"Input field with label '{label}' is not visible", element=label)

            if not await self.utils.is_element_enabled(locator):
                raise BrowserElementError(f"Input field with label '{label}' is disabled", element=label)

            # Scroll to element if needed
            await self.utils.scroll_to_element(locator)

            # Clear and fill with enhanced reliability
            await self._fill_with_retry(locator, value, clear_first, label)

            logger.info(f"✅ Successfully filled input '{label}' with: '{value}'")

            return {
                "status": "success",
                "message": f"Successfully filled '{label}' with '{value}'",
                "label": label,
                "value": value,
                "cleared_first": clear_first,
            }

        except BrowserElementError:
            raise
        except Exception as e:
            logger.error(f"❌ Fill failed for label '{label}': {e}")
            raise BrowserElementError(f"Fill failed: {str(e)}", element=label)

    @handle_async_browser_exceptions
    async def select_dropdown_option(
        self, dropdown_label: str, option_value: str, timeout: int = 5000
    ) -> dict[str, Any]:
        """
        Select dropdown option with enhanced reliability.

        Args:
            dropdown_label: Dropdown label or identifier
            option_value: Option value or text to select
            timeout: Timeout for finding element

        Returns:
            Selection result information
        """
        if not self.page:
            raise BrowserElementError("No active page available for interaction", element=dropdown_label)

        try:
            logger.info(f"📋 Attempting to select option '{option_value}' in dropdown '{dropdown_label}'")

            # Find select element using utility
            locator = await self.utils.find_select_by_label(dropdown_label)

            if not locator:
                raise BrowserElementError(
                    f"Could not find dropdown with label: {dropdown_label}", element=dropdown_label
                )

            # Wait for element to be visible and enabled
            if not await self.utils.wait_for_element_visible(locator, timeout):
                raise BrowserElementError(
                    f"Dropdown with label '{dropdown_label}' is not visible", element=dropdown_label
                )

            if not await self.utils.is_element_enabled(locator):
                raise BrowserElementError(f"Dropdown with label '{dropdown_label}' is disabled", element=dropdown_label)

            # Scroll to element if needed
            await self.utils.scroll_to_element(locator)

            # Select option with multiple strategies
            await self._select_with_retry(locator, option_value, dropdown_label)

            logger.info(f"✅ Successfully selected option '{option_value}' in dropdown '{dropdown_label}'")

            return {
                "status": "success",
                "message": f"Successfully selected option '{option_value}' in dropdown '{dropdown_label}'",
                "dropdown_label": dropdown_label,
                "option_value": option_value,
            }

        except BrowserElementError:
            raise
        except Exception as e:
            logger.error(f"❌ Select failed for dropdown '{dropdown_label}': {e}")
            raise BrowserElementError(f"Select failed: {str(e)}", element=dropdown_label)

    async def hover_element_by_text(self, text: str, timeout: int = 5000) -> dict[str, Any]:
        """
        Hover over element by text.

        Args:
            text: Text to search for and hover
            timeout: Timeout for finding element

        Returns:
            Hover result information
        """
        try:
            logger.info(f"🎯 Attempting to hover over element with text: '{text}'")

            # Find element using utility
            locator = await self.utils.find_element_by_text(text)

            if not locator:
                raise BrowserElementError(f"Could not find element with text: {text}", element=text)

            # Wait for element to be visible
            if not await self.utils.wait_for_element_visible(locator, timeout):
                raise BrowserElementError(f"Element with text '{text}' is not visible", element=text)

            # Scroll to element and hover
            await self.utils.scroll_to_element(locator)
            await locator.hover()

            logger.info(f"✅ Successfully hovered over element with text: '{text}'")

            return {
                "status": "success",
                "message": f"Successfully hovered over element with text: '{text}'",
                "text": text,
            }

        except Exception as e:
            logger.error(f"❌ Hover failed for text '{text}': {e}")
            raise BrowserElementError(f"Hover failed: {str(e)}", element=text)

    async def double_click_element_by_text(self, text: str, timeout: int = 5000) -> dict[str, Any]:
        """
        Double-click element by text.

        Args:
            text: Text to search for and double-click
            timeout: Timeout for finding element

        Returns:
            Double-click result information
        """
        try:
            logger.info(f"🖱️🖱️ Attempting to double-click element with text: '{text}'")

            # Find element using utility
            locator = await self.utils.find_element_by_text(text)

            if not locator:
                raise BrowserElementError(f"Could not find element with text: {text}", element=text)

            # Wait for element to be clickable
            if not await self.utils.wait_for_element_clickable(locator, timeout):
                raise BrowserElementError(f"Element with text '{text}' is not clickable", element=text)

            # Scroll to element and double-click
            await self.utils.scroll_to_element(locator)
            await locator.dblclick()

            logger.info(f"✅ Successfully double-clicked element with text: '{text}'")

            return {
                "status": "success",
                "message": f"Successfully double-clicked element with text: '{text}'",
                "text": text,
            }

        except Exception as e:
            logger.error(f"❌ Double-click failed for text '{text}': {e}")
            raise BrowserElementError(f"Double-click failed: {str(e)}", element=text)

    async def _click_with_retry(self, locator, text: str, max_retries: int = 3) -> None:
        """Click element with retry logic."""
        last_error = None

        for attempt in range(max_retries):
            try:
                # Try different click strategies
                if attempt == 0:
                    # Standard click
                    await locator.click()
                elif attempt == 1:
                    # Force click with position
                    await locator.click(force=True)
                else:
                    # Click with JavaScript
                    await locator.evaluate("element => element.click()")

                return  # Success

            except Exception as e:
                last_error = e
                logger.debug(f"Click attempt {attempt + 1} failed for '{text}': {e}")

                if attempt < max_retries - 1:
                    await self.page.wait_for_timeout(500)  # Wait before retry

        # All retries failed
        raise last_error

    async def _fill_with_retry(self, locator, value: str, clear_first: bool, label: str, max_retries: int = 3) -> None:
        """Fill input with retry logic."""
        last_error = None

        for attempt in range(max_retries):
            try:
                if clear_first:
                    # Clear field first
                    await locator.clear()

                # Fill value
                await locator.fill(value)

                # Verify the value was set correctly
                current_value = await locator.input_value()
                if current_value == value:
                    return  # Success
                else:
                    # Value mismatch, try different strategy
                    if attempt < max_retries - 1:
                        await locator.clear()
                        await locator.type(value)  # Use type instead of fill
                    else:
                        logger.warning(f"Value mismatch: expected '{value}', got '{current_value}'")
                        return  # Accept partial success

            except Exception as e:
                last_error = e
                logger.debug(f"Fill attempt {attempt + 1} failed for '{label}': {e}")

                if attempt < max_retries - 1:
                    await self.page.wait_for_timeout(500)  # Wait before retry

        # All retries failed
        raise last_error

    async def _select_with_retry(self, locator, option_value: str, dropdown_label: str, max_retries: int = 3) -> None:
        """Select option with retry logic and multiple strategies."""
        last_error = None

        for attempt in range(max_retries):
            try:
                # Try different selection strategies
                if attempt == 0:
                    # Try by value first
                    await locator.select_option(value=option_value)
                elif attempt == 1:
                    # Try by label/text
                    await locator.select_option(label=option_value)
                else:
                    # Try by index if option_value is numeric
                    try:
                        index = int(option_value)
                        await locator.select_option(index=index)
                    except ValueError:
                        # If not numeric, try partial text match
                        options = await locator.locator("option").all()
                        for i, option in enumerate(options):
                            option_text = await option.inner_text()
                            if option_value.lower() in option_text.lower():
                                await locator.select_option(index=i)
                                return
                        raise ValueError(f"Could not find option containing '{option_value}'")

                return  # Success

            except Exception as e:
                last_error = e
                logger.debug(f"Select attempt {attempt + 1} failed for '{dropdown_label}': {e}")

                if attempt < max_retries - 1:
                    await self.page.wait_for_timeout(500)  # Wait before retry

        # All retries failed
        raise last_error
