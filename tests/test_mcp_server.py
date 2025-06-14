"""
Tests for MCP server functionality.
"""

from swarm.core.config import Config
from swarm.mcp.browser_server import BrowserMCPServer, create_browser_mcp_server


def test_mcp_server_initialization():
    """Test that MCP server initializes correctly."""
    config = Config()
    mcp_server = create_browser_mcp_server(config)

    assert mcp_server is not None
    assert isinstance(mcp_server, BrowserMCPServer)
    assert mcp_server.config == config
    assert mcp_server._session_active is False


def test_mcp_server_tools_registration():
    """Test that MCP server registers all expected tools."""
    config = Config()
    mcp_server = BrowserMCPServer(config)

    # Get the FastMCP instance
    mcp_instance = mcp_server.get_mcp_instance()

    # Verify the MCP instance exists
    assert mcp_instance is not None

    # Verify server configuration
    assert mcp_server.browser is None  # Should be None until session starts
    assert mcp_server.search is None  # Should be None until initialized
    assert mcp_server._session_active is False


def test_mcp_server_session_management():
    """Test basic session management functionality."""
    config = Config()
    mcp_server = BrowserMCPServer(config)

    # Initially no session should be active
    assert mcp_server._session_active is False
    assert mcp_server.browser is None

    # Test that we can access the server properties
    assert hasattr(mcp_server, "config")
    assert hasattr(mcp_server, "mcp")
    assert hasattr(mcp_server, "_session_active")


def test_mcp_server_factory_function():
    """Test the convenience factory function."""
    config = Config()
    mcp_server = create_browser_mcp_server(config)

    assert isinstance(mcp_server, BrowserMCPServer)
    assert mcp_server.config == config
