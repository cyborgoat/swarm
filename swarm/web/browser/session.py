"""
Browser Session Management - Handles browser lifecycle and session state.
"""

import logging
from typing import Any

from playwright.async_api import Browser as PlaywrightBrowser
from playwright.async_api import BrowserContext, Page, async_playwright

from swarm.core.config import BrowserConfig
from swarm.core.exceptions import BrowserSessionError
from swarm.utils.exception_handler import handle_async_browser_exceptions

logger = logging.getLogger(__name__)


class BrowserSession:
    """Manages browser session lifecycle and state."""

    def __init__(self, config: BrowserConfig):
        """Initialize browser session manager."""
        self.config = config
        self.playwright = None
        self.browser: PlaywrightBrowser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self._session_active = False

    @property
    def is_active(self) -> bool:
        """Check if browser session is active."""
        return self._session_active and self.page is not None

    @handle_async_browser_exceptions
    async def start(self) -> dict[str, Any]:
        """
        Start browser session with optimized configuration.

        Returns:
            Session status information
        """
        if self._session_active:
            return {"status": "already_active", "message": "Browser session already running"}

        try:
            # Start Playwright
            self.playwright = await async_playwright().start()

            # Enhanced browser launch options for better performance and compatibility
            launch_options = {
                "headless": self.config.headless,
                "slow_mo": 50 if not self.config.headless else 0,
                "args": self._get_browser_args(),
            }

            # Launch browser with optimized settings
            self.browser = await self.playwright.chromium.launch(**launch_options)

            # Create context with enhanced settings
            context_options = {
                "viewport": {"width": self.config.viewport_width, "height": self.config.viewport_height},
                "user_agent": self._get_user_agent(),
                "extra_http_headers": {
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                },
                "ignore_https_errors": True,  # Better error handling
                "java_script_enabled": True,
            }

            self.context = await self.browser.new_context(**context_options)

            # Create page with optimized settings
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.config.timeout)

            # Set up page-level optimizations
            await self._setup_page_optimizations()

            self._session_active = True

            logger.info("✅ Browser session started successfully")
            return {
                "status": "success",
                "message": "Browser session started",
                "headless": self.config.headless,
                "viewport": f"{self.config.viewport_width}x{self.config.viewport_height}",
                "user_agent": context_options["user_agent"],
            }

        except Exception as e:
            logger.error(f"❌ Failed to start browser session: {e}")
            await self._cleanup_failed_start()
            raise BrowserSessionError(f"Failed to start browser: {str(e)}")

    @handle_async_browser_exceptions
    async def close(self) -> dict[str, Any]:
        """
        Close browser session and cleanup resources.

        Returns:
            Closure status information
        """
        if not self._session_active:
            return {"status": "not_active", "message": "No active session to close"}

        try:
            # Close in proper order
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
            # Force cleanup even if there's an error
            self._force_cleanup()
            raise BrowserSessionError(f"Error closing session: {str(e)}")

    async def get_status(self) -> dict[str, Any]:
        """Get current session status with detailed information."""
        if not self._session_active or not self.page:
            return {
                "active": False,
                "current_url": "about:blank",
                "title": "",
                "headless": self.config.headless,
                "viewport": f"{self.config.viewport_width}x{self.config.viewport_height}",
            }

        try:
            current_url = self.page.url
            title = await self.page.title()

            # Additional status information
            network_idle = await self._check_network_idle()
            page_ready = await self._check_page_ready()

            return {
                "active": True,
                "current_url": current_url,
                "title": title,
                "headless": self.config.headless,
                "viewport": f"{self.config.viewport_width}x{self.config.viewport_height}",
                "network_idle": network_idle,
                "page_ready": page_ready,
            }
        except Exception as e:
            logger.warning(f"Could not get session status: {e}")
            return {
                "active": self._session_active,
                "current_url": "unknown",
                "title": "unknown",
                "headless": self.config.headless,
                "viewport": f"{self.config.viewport_width}x{self.config.viewport_height}",
                "error": str(e),
            }

    def _get_browser_args(self) -> list[str]:
        """Get optimized browser launch arguments."""
        base_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-client-side-phishing-detection",
            "--disable-crash-reporter",
            "--disable-oopr-debug-crash-dump",
            "--no-crash-upload",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-low-res-tiling",
            "--log-level=3",
            "--silent",
        ]

        if not self.config.headless:
            base_args.extend(
                [
                    "--new-window",
                    "--start-maximized",
                ]
            )

        return base_args

    def _get_user_agent(self) -> str:
        """Get realistic user agent string."""
        return (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    async def _setup_page_optimizations(self) -> None:
        """Set up page-level optimizations for better performance."""
        if not self.page:
            return

        # Block unnecessary resources for faster loading
        await self.page.route("**/*", self._route_handler)

        # Set up error handling
        self.page.on("console", self._handle_console_message)
        self.page.on("pageerror", self._handle_page_error)

    async def _route_handler(self, route, request):
        """Handle route requests to block unnecessary resources."""
        # Block ads, analytics, and other non-essential resources
        blocked_types = {"image", "media", "font"} if self.config.headless else {"font"}
        blocked_domains = {
            "google-analytics.com",
            "googletagmanager.com",
            "facebook.com/tr",
            "doubleclick.net",
            "googlesyndication.com",
        }

        request_url = request.url.lower()

        # Block based on resource type or domain
        if request.resource_type in blocked_types or any(domain in request_url for domain in blocked_domains):
            await route.abort()
        else:
            await route.continue_()

    def _handle_console_message(self, msg) -> None:
        """Handle console messages from the page."""
        if msg.type == "error":
            logger.debug(f"Page console error: {msg.text}")

    def _handle_page_error(self, error) -> None:
        """Handle page errors."""
        logger.debug(f"Page error: {error}")

    async def _check_network_idle(self) -> bool:
        """Check if network is idle (no pending requests)."""
        try:
            await self.page.wait_for_load_state("networkidle", timeout=1000)
            return True
        except Exception:
            return False

    async def _check_page_ready(self) -> bool:
        """Check if page is fully loaded and ready."""
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=1000)
            return True
        except Exception:
            return False

    async def _cleanup_failed_start(self) -> None:
        """Cleanup resources after failed session start."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception:
            pass  # Ignore cleanup errors
        finally:
            self._force_cleanup()

    def _force_cleanup(self) -> None:
        """Force cleanup of all resources."""
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        self._session_active = False
