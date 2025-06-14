"""
Consolidated MCP Server for Browser Automation.

This module provides a complete MCP server implementation with browser automation
capabilities, combining server, adapter, and tool functionality in one place.
"""

import logging
import signal
import sys
from typing import Any

from fastmcp import FastMCP

from swarm.core.config import Config
from swarm.web.browser import Browser
from swarm.web.search import WebSearch

logger = logging.getLogger(__name__)


class SwarmMCPServer:
    """
    Consolidated MCP Server for Swarm browser automation.

    This class provides both the MCP server functionality and adapter interface
    for seamless integration with the interactive mode.
    """

    def __init__(self, config: Config):
        """Initialize the consolidated MCP server."""
        self.config = config
        self.mcp = FastMCP("Swarm Browser Automation 🐝")

        # Initialize browser components
        self.browser = Browser(config.browser)
        self.search = WebSearch(config.search)
        self._session_active = False

        # Register all MCP tools
        self._register_all_tools()

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print("\n🛑 Received shutdown signal, stopping MCP Server...")
        logger.info("🛑 MCP Server shutdown signal received")
        if self._session_active and self.browser:
            try:
                self.browser.close_session()
                print("✅ Browser session closed")
            except Exception as e:
                print(f"⚠️ Error closing browser: {e}")
        sys.exit(0)

    def _register_all_tools(self):
        """Register all MCP tools in one place."""

        # Store tool function references for direct calling
        self._tool_functions = {}

        @self.mcp.tool
        async def start_browser_session(headless: bool = False) -> dict[str, Any]:
            """
            Start browser session using native Playwright APIs.

            Args:
                headless: Whether to run browser in headless mode

            Returns:
                Session status
            """
            logger.info(f"🔧 MCP Tool: start_browser_session(headless={headless})")
            print(f"🔧 MCP Tool: start_browser_session(headless={headless})")

            try:
                # Check if session is already active
                if self.browser._session_active:
                    logger.info("✅ already_active")
                    print("✅ already_active")
                    return {"status": "already_active", "message": "Browser session already running"}

                # Update headless setting
                self.browser.config.headless = headless

                # Start browser session using async API
                result = await self.browser.start_session()
                if result.get("status") == "success":
                    self._session_active = True

                logger.info("✅ Browser session started")
                print("✅ Browser session started")
                return result

            except Exception as e:
                error_msg = f"Browser session start failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                print(f"❌ {error_msg}")
                return {"status": "error", "message": error_msg}

        @self.mcp.tool
        async def close_browser_session() -> dict[str, Any]:
            """
            Close browser session.

            Returns:
                Close status
            """
            logger.info("🔧 MCP Tool: close_browser_session()")
            print("🔧 MCP Tool: close_browser_session()")

            try:
                if not self.browser._session_active:
                    return {"status": "not_active", "message": "No active session to close"}

                result = await self.browser.close_session()
                if result.get("status") == "success":
                    self._session_active = False

                logger.info("✅ Browser session closed")
                print("✅ Browser session closed")
                return result

            except Exception as e:
                error_msg = f"Browser session close failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                print(f"❌ {error_msg}")
                return {"status": "error", "message": error_msg}

        @self.mcp.tool
        async def navigate_to_url(url: str) -> dict[str, Any]:
            """
            Navigate to URL using browser.

            Args:
                url: URL to navigate to

            Returns:
                Navigation result
            """
            logger.info(f"🔧 MCP Tool: navigate_to_url(url={url})")
            print(f"🔧 MCP Tool: navigate_to_url(url={url})")

            try:
                result = await self.browser.navigate_to_url(url)

                logger.info(f"✅ Navigation completed: {result.get('message', 'Success')}")
                print(f"✅ Navigation completed: {result.get('message', 'Success')}")
                return result

            except Exception as e:
                error_msg = f"Navigation failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                print(f"❌ {error_msg}")
                return {"status": "error", "message": error_msg}

        @self.mcp.tool
        async def extract_page_content(query: str | None = None, max_length: int = 20000) -> dict[str, Any]:
            """
            Extract content from current page.

            Args:
                query: Optional search query to filter content
                max_length: Maximum content length (default 20000)

            Returns:
                Extracted content
            """
            logger.info(f"🔧 MCP Tool: extract_page_content(query={query}, max_length={max_length})")
            print(f"🔧 MCP Tool: extract_page_content(query={query}, max_length={max_length})")

            try:
                result = await self.browser.extract_page_content(query, max_length)

                logger.info(f"✅ Content extracted: {result.get('length', 0)} characters")
                print(f"✅ Content extracted: {result.get('length', 0)} characters")
                return result

            except Exception as e:
                error_msg = f"Content extraction failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                print(f"❌ {error_msg}")
                return {"status": "error", "message": error_msg}

        @self.mcp.tool
        async def get_session_status() -> dict[str, Any]:
            """
            Get current browser session status.

            Returns:
                Session status information
            """
            try:
                result = await self.browser.get_session_status()
                return result

            except Exception as e:
                error_msg = f"Session status check failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                print(f"❌ {error_msg}")
                return {"status": "error", "message": error_msg}

        @self.mcp.tool
        async def click_element_by_text(text: str) -> dict[str, Any]:
            """
            Click element by visible text.

            Args:
                text: Text to search for and click

            Returns:
                Click result
            """
            logger.info(f"🔧 MCP Tool: click_element_by_text(text={text})")
            print(f"🔧 MCP Tool: click_element_by_text(text={text})")

            try:
                result = await self.browser.click_element_by_text(text)

                logger.info(f"✅ Click completed: {result.get('message', 'Success')}")
                print(f"✅ Click completed: {result.get('message', 'Success')}")
                return result

            except Exception as e:
                error_msg = f"Click failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                print(f"❌ {error_msg}")
                return {"status": "error", "message": error_msg}

        @self.mcp.tool
        async def fill_input_by_label(label: str, value: str) -> dict[str, Any]:
            """
            Fill input field by label.

            Args:
                label: Label text to find input field
                value: Value to fill

            Returns:
                Fill result
            """
            logger.info(f"🔧 MCP Tool: fill_input_by_label(label={label}, value={value})")
            print(f"🔧 MCP Tool: fill_input_by_label(label={label}, value={value})")

            try:
                result = await self.browser.fill_input_by_label(label, value)

                logger.info(f"✅ Fill completed: {result.get('message', 'Success')}")
                print(f"✅ Fill completed: {result.get('message', 'Success')}")
                return result

            except Exception as e:
                error_msg = f"Fill failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                print(f"❌ {error_msg}")
                return {"status": "error", "message": error_msg}

        self._tool_functions["start_browser_session"] = start_browser_session
        self._tool_functions["close_browser_session"] = close_browser_session
        self._tool_functions["navigate_to_url"] = navigate_to_url
        self._tool_functions["extract_page_content"] = extract_page_content
        self._tool_functions["get_session_status"] = get_session_status
        self._tool_functions["click_element_by_text"] = click_element_by_text
        self._tool_functions["fill_input_by_label"] = fill_input_by_label

        @self.mcp.tool
        def search_web(query: str, max_results: int = 10) -> dict[str, Any]:
            """
            Search the web using DuckDuckGo.

            Args:
                query: Search query string
                max_results: Maximum number of results to return (default: 10)

            Returns:
                Search results with status and results list
            """
            logger.info(f"🔧 MCP Tool: search_web(query={query}, max_results={max_results})")
            print(f"🔧 MCP Tool: search_web(query={query}, max_results={max_results})")

            # Ensure max_results is a valid integer
            if max_results is None or max_results <= 0:
                max_results = 10

            try:
                # Use the WebSearch instance to search
                results = self.search.search(query)[:max_results]

                logger.info(f"✅ Found {len(results)} search results")
                print(f"✅ Found {len(results)} search results")

                return {
                    "status": "success",
                    "query": query,
                    "results": results,
                    "count": len(results),
                    "message": f"Found {len(results)} search results",
                }

            except Exception as e:
                result = {"status": "error", "message": f"Web search failed: {str(e)}"}
                logger.error(f"❌ {result['message']}")
                print(f"❌ {result['message']}")
                return result

        self._tool_functions["search_web"] = search_web

        @self.mcp.tool
        async def get_page_elements() -> dict[str, Any]:
            """Get interactive elements from current page."""
            if not self._session_active or not self.browser:
                return {"status": "error", "message": "No active browser session"}

            try:
                elements = await self.browser.get_page_elements()
                total = sum(len(v) for v in elements.values())

                return {
                    "status": "success",
                    "buttons": elements.get("buttons", []),
                    "inputs": elements.get("inputs", []),
                    "links": elements.get("links", []),
                    "selects": elements.get("selects", []),
                    "total_count": total,
                    "message": f"Found {total} interactive elements",
                }

            except Exception as e:
                return {"status": "error", "message": f"Failed to get elements: {str(e)}"}

        self._tool_functions["get_page_elements"] = get_page_elements

        @self.mcp.tool
        def take_screenshot(path: str | None = None) -> dict[str, Any]:
            """
            Take screenshot of current page.

            Args:
                path: Optional path to save screenshot (default: auto-generated)

            Returns:
                Screenshot result with file path
            """
            if not self._session_active or not self.browser:
                return {"status": "error", "message": "No active browser session"}

            try:
                return self.browser.take_screenshot(path)
            except Exception as e:
                return {"status": "error", "message": f"Screenshot failed: {str(e)}"}

        self._tool_functions["take_screenshot"] = take_screenshot

    # Adapter interface methods for compatibility with interactive mode
    def start_session(self, headless: bool = False) -> dict[str, Any]:
        """Adapter method: Start browser session."""
        return self._call_tool("start_browser_session", {"headless": headless})

    def close_session(self) -> dict[str, Any]:
        """Adapter method: Close browser session."""
        return self._call_tool("close_browser_session", {})

    def navigate_to_url(self, url: str) -> dict[str, Any]:
        """Adapter method: Navigate to URL."""
        return self._call_tool("navigate_to_url", {"url": url})

    def extract_page_content(self, query: str | None = None, max_length: int = 20000) -> dict[str, Any]:
        """Adapter method: Extract page content."""
        return self._call_tool("extract_page_content", {"query": query, "max_length": max_length})

    def click_element_by_text(self, text: str) -> dict[str, Any]:
        """Adapter method: Click element by text."""
        return self._call_tool("click_element_by_text", {"text": text})

    def fill_input_by_label(self, label: str, value: str) -> dict[str, Any]:
        """Adapter method: Fill input field."""
        return self._call_tool("fill_input_by_label", {"label": label, "value": value})

    def search_web(self, query: str, max_results: int = 10) -> dict[str, Any]:
        """Adapter method: Search web."""
        return self._call_tool("search_web", {"query": query, "max_results": max_results})

    def get_session_status(self) -> dict[str, Any]:
        """Adapter method: Get session status."""
        return self._call_tool("get_session_status", {})

    def get_current_url(self) -> str:
        """Adapter method: Get current URL."""
        if self.browser:
            return self.browser.get_current_url()
        return "about:blank"

    def get_page_title(self) -> str:
        """Adapter method: Get page title."""
        if self.browser:
            return self.browser.get_page_title()
        return ""

    def _call_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Internal method to call MCP tools directly."""
        try:
            # Call the tool functions directly by accessing the registered functions
            if not hasattr(self, "_tool_functions"):
                return {"status": "error", "message": "Tool functions not initialized"}

            if tool_name in self._tool_functions:
                func = self._tool_functions[tool_name]
                # If it's a FunctionTool object, get the actual function
                if hasattr(func, "fn"):
                    func = func.fn

                if tool_name == "start_browser_session":
                    return func(args.get("headless", False))
                elif tool_name == "close_browser_session":
                    return func()
                elif tool_name == "navigate_to_url":
                    return func(args["url"])
                elif tool_name == "extract_page_content":
                    return func(args.get("query"), args.get("max_length", 20000))
                elif tool_name == "click_element_by_text":
                    return func(args["text"])
                elif tool_name == "fill_input_by_label":
                    return func(args["label"], args["value"])
                elif tool_name == "search_web":
                    return func(args["query"], args.get("max_results", 10))
                else:
                    return func()
            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"status": "error", "message": f"Tool call failed: {str(e)}"}

    # Legacy compatibility methods
    def browse_persistent(self, url: str) -> dict[str, Any]:
        """Legacy method for compatibility."""
        nav_result = self.navigate_to_url(url)
        if nav_result["status"] == "success":
            content_result = self.extract_page_content(max_length=5000)
            return {
                "url": nav_result.get("url", url),
                "title": nav_result.get("title", ""),
                "content": content_result.get("content", ""),
                "links": [],
            }
        else:
            raise Exception(nav_result.get("message", "Navigation failed"))

    def extract_text_content(self, query: str | None = None) -> str:
        """Legacy method for compatibility."""
        result = self.extract_page_content(query, max_length=20000)
        return result.get("content", "") if result["status"] == "success" else ""

    def get_page_elements_legacy(self) -> dict[str, Any]:
        """Legacy method for compatibility."""
        result = self._call_tool("get_page_elements", {})
        if result["status"] == "success":
            return {
                "buttons": result.get("buttons", []),
                "inputs": result.get("inputs", []),
                "links": result.get("links", []),
                "selects": result.get("selects", []),
            }
        return {"buttons": [], "inputs": [], "links": [], "selects": []}

    # MCP Server methods
    def run(self, **kwargs):
        """Run the MCP server."""
        return self.mcp.run(**kwargs)

    def get_mcp_instance(self):
        """Get the FastMCP instance."""
        return self.mcp


def create_mcp_server(config: Config) -> SwarmMCPServer:
    """
    Create and configure the consolidated MCP server.

    Args:
        config: Application configuration

    Returns:
        Configured SwarmMCPServer instance
    """
    return SwarmMCPServer(config)
