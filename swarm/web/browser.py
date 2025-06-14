"""
Browser automation using native Playwright async APIs.

This module provides a clean, simple interface to Playwright's browser automation
capabilities, following official Playwright documentation patterns.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from playwright.async_api import async_playwright, Browser as PlaywrightBrowser, Page, BrowserContext
from playwright.sync_api import sync_playwright, Browser as SyncPlaywrightBrowser, Page as SyncPage, BrowserContext as SyncBrowserContext

from swarm.core.config import BrowserConfig
from swarm.core.exceptions import BrowserError

logger = logging.getLogger(__name__)


class Browser:
    """
    Simplified browser automation using native Playwright async APIs.
    
    Based on official Playwright documentation:
    - https://playwright.dev/python/docs/input
    - https://playwright.dev/python/docs/actionability  
    - https://playwright.dev/python/docs/navigations
    """
    
    def __init__(self, config: BrowserConfig):
        """
        Initialize browser with configuration.
        
        Args:
            config: Browser configuration
        """
        self.config = config
        self.playwright = None
        self.browser: Optional[PlaywrightBrowser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._session_active = False
        
    async def start_session(self) -> Dict[str, Any]:
        """
        Start browser session using native Playwright async APIs.
        
        Returns:
            Session status information
        """
        if self._session_active:
            return {"status": "already_active", "message": "Browser session already running"}
            
        try:
            # Start Playwright - async API
            self.playwright = await async_playwright().start()
            
            # Launch browser - async API with proper options
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.headless,
                slow_mo=50 if not self.config.headless else 0,  # Slow down for visibility
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--new-window'  # Force new window to open
                ] if not self.config.headless else [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context - async API with proper viewport
            self.context = await self.browser.new_context(
                viewport={
                    'width': self.config.viewport_width,
                    'height': self.config.viewport_height
                },
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Create page - async API
            self.page = await self.context.new_page()
            
            # Set default timeout - async API
            self.page.set_default_timeout(self.config.timeout)
            
            self._session_active = True
            
            logger.info("✅ Browser session started successfully")
            return {
                "status": "success",
                "message": "Browser session started",
                "headless": self.config.headless,
                "viewport": f"{self.config.viewport_width}x{self.config.viewport_height}"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to start browser session: {e}")
            return {"status": "error", "message": f"Failed to start browser: {str(e)}"}
    
    async def close_session(self) -> Dict[str, Any]:
        """
        Close browser session and cleanup resources.
        
        Returns:
            Closure status information
        """
        if not self._session_active:
            return {"status": "not_active", "message": "No active session to close"}
            
        try:
            # Close in proper order - async API
            if self.page:
                await self.page.close()
                self.page = None
                
            if self.context:
                await self.context.close()
                self.context = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            self._session_active = False
            
            logger.info("✅ Browser session closed successfully")
            return {"status": "success", "message": "Browser session closed"}
            
        except Exception as e:
            logger.error(f"❌ Error closing browser session: {e}")
            return {"status": "error", "message": f"Error closing session: {str(e)}"}
    
    async def navigate_to_url(self, url: str) -> Dict[str, Any]:
        """
        Navigate to URL using native Playwright async navigation.
        
        Args:
            url: URL to navigate to
            
        Returns:
            Navigation result with page information
        """
        if not self._session_active or not self.page:
            return {"status": "error", "message": "No active browser session"}
            
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        try:
            # Navigate using native Playwright async API
            response = await self.page.goto(url, wait_until='domcontentloaded')
            
            # Get page info using async APIs
            title = await self.page.title()
            current_url = self.page.url
            
            logger.info(f"✅ Navigated to: {title} ({current_url})")
            
            return {
                "status": "success",
                "url": current_url,
                "title": title,
                "response_status": response.status if response else None,
                "message": f"Successfully navigated to {title}"
            }
            
        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return {"status": "error", "message": f"Navigation failed: {str(e)}"}
    
    async def get_current_url(self) -> str:
        """Get current page URL using async Playwright API."""
        if not self._session_active or not self.page:
            return "about:blank"
        return self.page.url
    
    async def get_page_title(self) -> str:
        """Get current page title using async Playwright API."""
        if not self._session_active or not self.page:
            return ""
        try:
            return await self.page.title()
        except Exception as e:
            logger.warning(f"Could not get page title: {e}")
            return ""
    
    async def extract_page_content(self, query: Optional[str] = None, max_length: int = 10000) -> Dict[str, Any]:
        """
        Extract page content using async Playwright APIs.
        
        Args:
            query: Optional search query to filter content
            max_length: Maximum content length (increased from 2000)
            
        Returns:
            Extracted content information
        """
        if not self._session_active or not self.page:
            return {"status": "error", "message": "No active browser session"}
            
        try:
            # Extract text content using async Playwright API
            # This gets all visible text content from the page
            content = await self.page.inner_text('body')
            
            # Clean up the content
            content = ' '.join(content.split())  # Normalize whitespace
            
            # Filter by query if provided
            if query:
                query_words = query.lower().split()
                sentences = content.split('.')
                relevant_sentences = []
                
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(word in sentence_lower for word in query_words):
                        relevant_sentences.append(sentence.strip())
                
                if relevant_sentences:
                    content = '. '.join(relevant_sentences)
                else:
                    # If no specific matches, return full content
                    pass
            
            # Truncate to max_length
            if len(content) > max_length:
                content = content[:max_length] + "..."
                
            logger.info(f"✅ Extracted {len(content)} characters of content")
            
            return {
                "status": "success",
                "content": content,
                "length": len(content),
                "query": query,
                "truncated": len(content) >= max_length
            }
            
        except Exception as e:
            logger.error(f"❌ Content extraction failed: {e}")
            return {"status": "error", "message": f"Content extraction failed: {str(e)}"}
    
    async def click_element_by_text(self, text: str) -> Dict[str, Any]:
        """
        Click element by text using async Playwright APIs with multiple strategies.
        
        Args:
            text: Text to search for and click
            
        Returns:
            Click result information
        """
        if not self._session_active or not self.page:
            return {"status": "error", "message": "No active browser session"}
            
        try:
            # Strategy 1: Use get_by_role for buttons (most reliable)
            try:
                locator = self.page.get_by_role("button", name=text)
                if await locator.count() > 0:
                    await locator.click()
                    logger.info(f"✅ Clicked button with text: {text} (using get_by_role)")
                    return {
                        "status": "success",
                        "message": f"Successfully clicked button with text: {text} using get_by_role",
                        "text": text,
                        "method": "get_by_role_button"
                    }
            except Exception as e:
                logger.debug(f"get_by_role button failed: {e}")
            
            # Strategy 2: Use get_by_role for links
            try:
                locator = self.page.get_by_role("link", name=text)
                if await locator.count() > 0:
                    await locator.click()
                    logger.info(f"✅ Clicked link with text: {text} (using get_by_role)")
                    return {
                        "status": "success",
                        "message": f"Successfully clicked link with text: {text} using get_by_role",
                        "text": text,
                        "method": "get_by_role_link"
                    }
            except Exception as e:
                logger.debug(f"get_by_role link failed: {e}")
            
            # Strategy 3: Use get_by_text (general text locator)
            try:
                locator = self.page.get_by_text(text)
                if await locator.count() > 0:
                    await locator.click()
                    logger.info(f"✅ Clicked element with text: {text} (using get_by_text)")
                    return {
                        "status": "success",
                        "message": f"Successfully clicked element with text: {text} using get_by_text",
                        "text": text,
                        "method": "get_by_text"
                    }
            except Exception as e:
                logger.debug(f"get_by_text failed: {e}")
            
            # Strategy 4: Use text selector (legacy Playwright syntax)
            try:
                await self.page.click(f"text={text}")
                logger.info(f"✅ Clicked element with text: {text} (using text selector)")
                return {
                    "status": "success",
                    "message": f"Successfully clicked element with text: {text} using text selector",
                    "text": text,
                    "method": "text_selector"
                }
            except Exception as e:
                logger.debug(f"text selector failed: {e}")
            
            # Strategy 5: Partial text match
            try:
                locator = self.page.get_by_text(text, exact=False)
                if await locator.count() > 0:
                    await locator.click()
                    logger.info(f"✅ Clicked element with partial text: {text} (using partial match)")
                    return {
                        "status": "success",
                        "message": f"Successfully clicked element with partial text: {text}",
                        "text": text,
                        "method": "partial_text_match"
                    }
            except Exception as e:
                logger.debug(f"partial text match failed: {e}")
            
            # If all strategies fail
            logger.error(f"❌ Could not find clickable element with text: {text}")
            return {"status": "error", "message": f"Could not find clickable element with text: {text}"}
            
        except Exception as e:
            logger.error(f"❌ Click failed: {e}")
            return {"status": "error", "message": f"Click failed: {str(e)}"}
    
    async def fill_input_by_label(self, label: str, value: str) -> Dict[str, Any]:
        """
        Fill input field or textarea by label using async Playwright APIs with multiple strategies.
        
        Args:
            label: Label text to find input field or textarea
            value: Value to fill
            
        Returns:
            Fill result information
        """
        if not self._session_active or not self.page:
            return {"status": "error", "message": "No active browser session"}
            
        try:
            # Strategy 1: Use get_by_label (most reliable for accessibility)
            try:
                locator = self.page.get_by_label(label)
                if await locator.count() > 0:
                    await locator.fill(value)
                    logger.info(f"✅ Filled input '{label}' with: {value} (using get_by_label)")
                    return {
                        "status": "success",
                        "message": f"Successfully filled '{label}' with '{value}' using get_by_label",
                        "label": label,
                        "value": value,
                        "method": "get_by_label"
                    }
            except Exception as e:
                logger.debug(f"get_by_label failed: {e}")
            
            # Strategy 2: Use get_by_placeholder
            try:
                locator = self.page.get_by_placeholder(label)
                if await locator.count() > 0:
                    await locator.fill(value)
                    logger.info(f"✅ Filled input '{label}' with: {value} (using get_by_placeholder)")
                    return {
                        "status": "success",
                        "message": f"Successfully filled '{label}' with '{value}' using get_by_placeholder",
                        "label": label,
                        "value": value,
                        "method": "get_by_placeholder"
                    }
            except Exception as e:
                logger.debug(f"get_by_placeholder failed: {e}")
            
            # Strategy 3: Use CSS selector for label association (input and textarea)
            try:
                # Find input or textarea associated with label
                locator = self.page.locator(f"label:has-text('{label}') >> input, label:has-text('{label}') >> textarea")
                if await locator.count() > 0:
                    await locator.fill(value)
                    logger.info(f"✅ Filled input '{label}' with: {value} (using label association)")
                    return {
                        "status": "success",
                        "message": f"Successfully filled '{label}' with '{value}' using label association",
                        "label": label,
                        "value": value,
                        "method": "label_association"
                    }
            except Exception as e:
                logger.debug(f"label association failed: {e}")
            
            # Strategy 4: Find input/textarea by name attribute
            try:
                locator = self.page.locator(f"input[name*='{label}'], textarea[name*='{label}']")
                if await locator.count() > 0:
                    await locator.fill(value)
                    logger.info(f"✅ Filled input '{label}' with: {value} (using name attribute)")
                    return {
                        "status": "success",
                        "message": f"Successfully filled '{label}' with '{value}' using name attribute",
                        "label": label,
                        "value": value,
                        "method": "name_attribute"
                    }
            except Exception as e:
                logger.debug(f"name attribute failed: {e}")
            
            # Strategy 5: Find by partial text match in placeholder or name
            try:
                locator = self.page.locator(f"input[placeholder*='{label}'], textarea[placeholder*='{label}'], input[name*='{label.lower()}'], textarea[name*='{label.lower()}']")
                if await locator.count() > 0:
                    await locator.fill(value)
                    logger.info(f"✅ Filled input '{label}' with: {value} (using partial match)")
                    return {
                        "status": "success",
                        "message": f"Successfully filled '{label}' with '{value}' using partial match",
                        "label": label,
                        "value": value,
                        "method": "partial_match"
                    }
            except Exception as e:
                logger.debug(f"partial match failed: {e}")
            
            # If all strategies fail
            logger.error(f"❌ Could not find input field for label: {label}")
            return {"status": "error", "message": f"Could not find input field for label: {label}"}
            
        except Exception as e:
            logger.error(f"❌ Fill failed: {e}")
            return {"status": "error", "message": f"Fill failed: {str(e)}"}
    
    async def select_dropdown_option(self, dropdown_label: str, option_value: str) -> Dict[str, Any]:
        """
        Select dropdown option using native Playwright select APIs.
        
        Args:
            dropdown_label: Dropdown label or identifier
            option_value: Option value or text to select
            
        Returns:
            Selection result information
        """
        if not self._session_active or not self.page:
            return {"status": "error", "message": "No active browser session"}
            
        try:
            # Use native Playwright select APIs as per official docs
            locator = None
            
            # Strategy 1: get_by_label for select element
            try:
                locator = self.page.get_by_label(dropdown_label)
                if locator.count() > 0:
                    # Try selecting by value first, then by label
                    try:
                        locator.select_option(value=option_value)
                        logger.info(f"✅ Selected option by value: {option_value}")
                        return {"status": "success", "message": f"Selected option: {option_value}", "method": "select_by_value"}
                    except:
                        locator.select_option(label=option_value)
                        logger.info(f"✅ Selected option by label: {option_value}")
                        return {"status": "success", "message": f"Selected option: {option_value}", "method": "select_by_label"}
            except:
                pass
            
            # Strategy 2: get_by_role for combobox
            try:
                locator = self.page.get_by_role("combobox", name=dropdown_label)
                if locator.count() > 0:
                    locator.select_option(label=option_value)
                    logger.info(f"✅ Selected combobox option: {option_value}")
                    return {"status": "success", "message": f"Selected option: {option_value}", "method": "get_by_role_combobox"}
            except:
                pass
            
            return {"status": "error", "message": f"Dropdown '{dropdown_label}' not found or option '{option_value}' not available"}
            
        except Exception as e:
            logger.error(f"❌ Select dropdown failed: {e}")
            return {"status": "error", "message": f"Select dropdown failed: {str(e)}"}
    
    async def get_page_elements(self) -> Dict[str, List[str]]:
        """
        Get interactive page elements using native Playwright locators.
        
        Returns:
            Dictionary of element types and their text content
        """
        if not self._session_active or not self.page:
            return {"buttons": [], "inputs": [], "links": [], "selects": []}
            
        try:
            elements = {
                "buttons": [],
                "inputs": [],
                "links": [],
                "selects": []
            }
            
            # Get buttons using native Playwright role locator
            buttons = await self.page.get_by_role("button").all()
            for button in buttons:
                try:
                    text = await button.inner_text()
                    if text.strip():
                        elements["buttons"].append(text.strip())
                except:
                    pass
            
            # Get input fields
            inputs = await self.page.locator("input, textarea").all()
            for input_elem in inputs:
                try:
                    # Get label, placeholder, or name
                    label = ""
                    try:
                        label = await input_elem.get_attribute("placeholder") or ""
                    except:
                        pass
                    try:
                        if not label:
                            label = await input_elem.get_attribute("name") or ""
                    except:
                        pass
                    try:
                        if not label:
                            # Try to find associated label
                            input_id = await input_elem.get_attribute("id")
                            if input_id:
                                label_elem = await self.page.locator(f"label[for='{input_id}']").first
                                if label_elem:
                                    label = await label_elem.inner_text()
                    except:
                        pass
                    if label:
                        elements["inputs"].append(label.strip())
                except:
                    pass
            
            # Get links using native Playwright role locator
            links = await self.page.get_by_role("link").all()
            for link in links:
                try:
                    text = await link.inner_text()
                    if text.strip():
                        elements["links"].append(text.strip()[:50])  # Limit link text length
                except:
                    pass
            
            # Get select elements
            selects = await self.page.locator("select").all()
            for select in selects:
                try:
                    # Try to get associated label
                    label = ""
                    try:
                        label = await select.get_attribute("name") or ""
                    except:
                        pass
                    try:
                        if not label:
                            select_id = await select.get_attribute("id")
                            if select_id:
                                label_elem = await self.page.locator(f"label[for='{select_id}']").first
                                if label_elem:
                                    label = await label_elem.inner_text()
                    except:
                        pass
                    if label:
                        elements["selects"].append(label.strip())
                except:
                    pass
            
            logger.info(f"✅ Found {sum(len(v) for v in elements.values())} interactive elements")
            return elements
            
        except Exception as e:
            logger.error(f"❌ Get page elements failed: {e}")
            return {"buttons": [], "inputs": [], "links": [], "selects": []}
    
    def take_screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Take screenshot using native Playwright API.
        
        Args:
            path: Optional path to save screenshot
            
        Returns:
            Screenshot result information
        """
        if not self._session_active or not self.page:
            return {"status": "error", "message": "No active browser session"}
            
        try:
            if not path:
                path = f"screenshot_{self.page.url.replace('://', '_').replace('/', '_')}.png"
                
            # Use native Playwright screenshot API
            self.page.screenshot(path=path, full_page=True)
            
            logger.info(f"✅ Screenshot saved: {path}")
            return {"status": "success", "path": path, "message": f"Screenshot saved to {path}"}
            
        except Exception as e:
            logger.error(f"❌ Screenshot failed: {e}")
            return {"status": "error", "message": f"Screenshot failed: {str(e)}"}
    
    async def get_session_status(self) -> Dict[str, Any]:
        """Get current browser session status using async APIs."""
        if not self._session_active or not self.page:
            return {
                "active": False,
                "current_url": "about:blank",
                "title": "",
                "headless": self.config.headless,
                "viewport": f"{self.config.viewport_width}x{self.config.viewport_height}"
            }
        
        try:
            current_url = self.page.url
            title = await self.page.title()
            
            return {
                "active": True,
                "current_url": current_url,
                "title": title,
                "headless": self.config.headless,
                "viewport": f"{self.config.viewport_width}x{self.config.viewport_height}"
            }
        except Exception as e:
            logger.warning(f"Could not get session status: {e}")
            return {
                "active": self._session_active,
                "current_url": "unknown",
                "title": "unknown",
                "headless": self.config.headless,
                "viewport": f"{self.config.viewport_width}x{self.config.viewport_height}"
            }
    
    # Legacy compatibility methods
    def browse_persistent(self, url: str) -> Dict[str, Any]:
        """Legacy method for compatibility."""
        nav_result = self.navigate_to_url(url)
        if nav_result["status"] == "success":
            content_result = self.extract_page_content(max_length=5000)
            return {
                "url": nav_result["url"],
                "title": nav_result["title"],
                "content": content_result.get("content", ""),
                "links": []
            }
        else:
            raise Exception(nav_result["message"])
    
    def extract_text_content(self, query: Optional[str] = None) -> str:
        """Legacy method for compatibility."""
        result = self.extract_page_content(query, max_length=10000)
        return result.get("content", "") if result["status"] == "success" else "" 