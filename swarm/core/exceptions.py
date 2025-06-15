"""
Custom exceptions for Swarm.
"""


class SwarmError(Exception):
    """Base exception for all Swarm errors."""

    def __init__(self, message: str, details: str = "", error_code: str = "") -> None:
        self.message = message
        self.details = details
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return formatted error message."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class LLMError(SwarmError):
    """Exception raised for LLM-related errors."""

    def __init__(self, message: str, details: str = "", model: str = "", error_code: str = "LLM_ERROR") -> None:
        super().__init__(message, details, error_code)
        self.model = model


class LLMTimeoutError(LLMError):
    """Exception raised when LLM requests timeout."""

    def __init__(self, message: str = "LLM request timed out", timeout: float = 0, **kwargs) -> None:
        super().__init__(message, error_code="LLM_TIMEOUT", **kwargs)
        self.timeout = timeout


class LLMConnectionError(LLMError):
    """Exception raised when LLM connection fails."""

    def __init__(self, message: str = "Failed to connect to LLM service", **kwargs) -> None:
        super().__init__(message, error_code="LLM_CONNECTION", **kwargs)


class BrowserError(SwarmError):
    """Exception raised for browser automation errors."""

    def __init__(self, message: str, details: str = "", url: str = "", error_code: str = "BROWSER_ERROR") -> None:
        super().__init__(message, details, error_code)
        self.url = url


class BrowserSessionError(BrowserError):
    """Exception raised when browser session operations fail."""

    def __init__(self, message: str = "Browser session error", **kwargs) -> None:
        super().__init__(message, error_code="BROWSER_SESSION", **kwargs)


class BrowserNavigationError(BrowserError):
    """Exception raised when browser navigation fails."""

    def __init__(self, message: str = "Navigation failed", **kwargs) -> None:
        super().__init__(message, error_code="BROWSER_NAVIGATION", **kwargs)


class BrowserElementError(BrowserError):
    """Exception raised when browser element interaction fails."""

    def __init__(self, message: str = "Element interaction failed", element: str = "", **kwargs) -> None:
        super().__init__(message, error_code="BROWSER_ELEMENT", **kwargs)
        self.element = element


class WebError(SwarmError):
    """Exception raised for web-related errors."""

    def __init__(
        self, message: str, details: str = "", url: str = "", status_code: int = 0, error_code: str = "WEB_ERROR"
    ) -> None:
        super().__init__(message, details, error_code)
        self.url = url
        self.status_code = status_code


class WebSearchError(WebError):
    """Exception raised when web search fails."""

    def __init__(self, message: str = "Web search failed", query: str = "", **kwargs) -> None:
        super().__init__(message, error_code="WEB_SEARCH", **kwargs)
        self.query = query


class WebContentError(WebError):
    """Exception raised when web content extraction fails."""

    def __init__(self, message: str = "Content extraction failed", **kwargs) -> None:
        super().__init__(message, error_code="WEB_CONTENT", **kwargs)


class ConfigError(SwarmError):
    """Exception raised for configuration errors."""

    def __init__(self, message: str, details: str = "", config_key: str = "", error_code: str = "CONFIG_ERROR") -> None:
        super().__init__(message, details, error_code)
        self.config_key = config_key


class ValidationError(SwarmError):
    """Exception raised for validation errors."""

    def __init__(self, message: str, details: str = "", field: str = "", error_code: str = "VALIDATION_ERROR") -> None:
        super().__init__(message, details, error_code)
        self.field = field


class MCPError(SwarmError):
    """Exception raised for MCP (Model Context Protocol) errors."""

    def __init__(self, message: str, details: str = "", tool_name: str = "", error_code: str = "MCP_ERROR") -> None:
        super().__init__(message, details, error_code)
        self.tool_name = tool_name


class MCPToolError(MCPError):
    """Exception raised when MCP tool execution fails."""

    def __init__(self, message: str = "MCP tool execution failed", **kwargs) -> None:
        super().__init__(message, error_code="MCP_TOOL", **kwargs)


class MCPConnectionError(MCPError):
    """Exception raised when MCP connection fails."""

    def __init__(self, message: str = "MCP connection failed", **kwargs) -> None:
        super().__init__(message, error_code="MCP_CONNECTION", **kwargs)


class ResearchError(SwarmError):
    """Exception raised for research-related errors."""

    def __init__(self, message: str, details: str = "", phase: str = "", error_code: str = "RESEARCH_ERROR") -> None:
        super().__init__(message, details, error_code)
        self.phase = phase


class ResearchAnalysisError(ResearchError):
    """Exception raised when research analysis fails."""

    def __init__(self, message: str = "Research analysis failed", **kwargs) -> None:
        super().__init__(message, error_code="RESEARCH_ANALYSIS", **kwargs)


class ResearchExtractionError(ResearchError):
    """Exception raised when content extraction during research fails."""

    def __init__(self, message: str = "Content extraction failed", **kwargs) -> None:
        super().__init__(message, error_code="RESEARCH_EXTRACTION", **kwargs)


# Exception mapping for common error patterns
EXCEPTION_MAPPING = {
    # Browser-related errors
    "browser session": BrowserSessionError,
    "navigation": BrowserNavigationError,
    "element": BrowserElementError,
    "click": BrowserElementError,
    "fill": BrowserElementError,
    # Web-related errors
    "search": WebSearchError,
    "content": WebContentError,
    "extract": WebContentError,
    # LLM-related errors
    "timeout": LLMTimeoutError,
    "connection": LLMConnectionError,
    "llm": LLMError,
    # MCP-related errors
    "mcp": MCPError,
    "tool": MCPToolError,
    # Research-related errors
    "research": ResearchError,
    "analysis": ResearchAnalysisError,
}


def get_appropriate_exception(error_message: str, context: str = "") -> type[SwarmError]:
    """
    Get the most appropriate exception class based on error message and context.

    Args:
        error_message: The error message
        context: Additional context about where the error occurred

    Returns:
        The most appropriate exception class
    """
    error_lower = error_message.lower()
    context_lower = context.lower()

    # Check context first for more specific matching
    for keyword, exception_class in EXCEPTION_MAPPING.items():
        if keyword in context_lower or keyword in error_lower:
            return exception_class

    # Default to base SwarmError
    return SwarmError


def create_exception_from_generic(generic_exception: Exception, context: str = "", **kwargs) -> SwarmError:
    """
    Create a specific SwarmError from a generic exception.

    Args:
        generic_exception: The original generic exception
        context: Context about where the error occurred
        **kwargs: Additional arguments for the specific exception

    Returns:
        A specific SwarmError instance
    """
    error_message = str(generic_exception)
    exception_class = get_appropriate_exception(error_message, context)

    return exception_class(
        message=error_message, details=f"Original exception: {type(generic_exception).__name__}", **kwargs
    )
