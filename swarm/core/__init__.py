"""
Core functionality for the Swarm agent.
"""

from swarm.core.config import Config
from swarm.core.exceptions import (
    BrowserElementError,
    BrowserError,
    BrowserNavigationError,
    BrowserSessionError,
    ConfigError,
    LLMConnectionError,
    LLMError,
    LLMTimeoutError,
    MCPConnectionError,
    MCPError,
    MCPToolError,
    ResearchAnalysisError,
    ResearchError,
    ResearchExtractionError,
    SwarmError,
    ValidationError,
    WebContentError,
    WebError,
    WebSearchError,
    create_exception_from_generic,
    get_appropriate_exception,
)

__all__ = [
    "Config",
    "SwarmError",
    "LLMError",
    "LLMTimeoutError",
    "LLMConnectionError",
    "BrowserError",
    "BrowserSessionError",
    "BrowserNavigationError",
    "BrowserElementError",
    "WebError",
    "WebSearchError",
    "WebContentError",
    "ConfigError",
    "ValidationError",
    "MCPError",
    "MCPToolError",
    "MCPConnectionError",
    "ResearchError",
    "ResearchAnalysisError",
    "ResearchExtractionError",
    "get_appropriate_exception",
    "create_exception_from_generic",
]
