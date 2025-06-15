"""
Exception handling utilities for Swarm.
"""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from swarm.core.exceptions import (
    BrowserElementError,
    BrowserError,
    BrowserNavigationError,
    BrowserSessionError,
    LLMConnectionError,
    LLMError,
    LLMTimeoutError,
    MCPError,
    MCPToolError,
    ResearchError,
    SwarmError,
    WebContentError,
    WebError,
    WebSearchError,
    create_exception_from_generic,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


def handle_browser_exceptions(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle browser-related exceptions consistently.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with browser exception handling
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except (BrowserError, BrowserSessionError, BrowserNavigationError, BrowserElementError):
            # Re-raise specific browser errors
            raise
        except Exception as e:
            # Convert generic exceptions to specific browser errors
            error_msg = str(e).lower()
            if "session" in error_msg:
                raise BrowserSessionError(str(e), details=f"Function: {func.__name__}")
            elif "navigation" in error_msg or "navigate" in error_msg:
                raise BrowserNavigationError(str(e), details=f"Function: {func.__name__}")
            elif "element" in error_msg or "click" in error_msg or "fill" in error_msg:
                raise BrowserElementError(str(e), details=f"Function: {func.__name__}")
            else:
                raise BrowserError(str(e), details=f"Function: {func.__name__}")

    return wrapper


def handle_web_exceptions(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle web-related exceptions consistently.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with web exception handling
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except (WebError, WebSearchError, WebContentError):
            # Re-raise specific web errors
            raise
        except Exception as e:
            # Convert generic exceptions to specific web errors
            error_msg = str(e).lower()
            if "search" in error_msg:
                raise WebSearchError(str(e), details=f"Function: {func.__name__}")
            elif "content" in error_msg or "extract" in error_msg:
                raise WebContentError(str(e), details=f"Function: {func.__name__}")
            else:
                raise WebError(str(e), details=f"Function: {func.__name__}")

    return wrapper


def handle_llm_exceptions(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle LLM-related exceptions consistently.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with LLM exception handling
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except (LLMError, LLMTimeoutError, LLMConnectionError):
            # Re-raise specific LLM errors
            raise
        except Exception as e:
            # Convert generic exceptions to specific LLM errors
            error_msg = str(e).lower()
            if "timeout" in error_msg or "timed out" in error_msg:
                raise LLMTimeoutError(str(e), details=f"Function: {func.__name__}")
            elif "connection" in error_msg or "connect" in error_msg:
                raise LLMConnectionError(str(e), details=f"Function: {func.__name__}")
            else:
                raise LLMError(str(e), details=f"Function: {func.__name__}")

    return wrapper


def handle_mcp_exceptions(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle MCP-related exceptions consistently.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with MCP exception handling
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except (MCPError, MCPToolError):
            # Re-raise specific MCP errors
            raise
        except Exception as e:
            # Convert generic exceptions to specific MCP errors
            error_msg = str(e).lower()
            if "tool" in error_msg:
                raise MCPToolError(str(e), details=f"Function: {func.__name__}")
            else:
                raise MCPError(str(e), details=f"Function: {func.__name__}")

    return wrapper


def handle_research_exceptions(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle research-related exceptions consistently.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with research exception handling
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except ResearchError:
            # Re-raise specific research errors
            raise
        except Exception as e:
            # Convert generic exceptions to research errors
            raise ResearchError(str(e), details=f"Function: {func.__name__}")

    return wrapper


def safe_execute(
    func: Callable[..., T], *args, default_return: Any = None, context: str = "", log_errors: bool = True, **kwargs
) -> T | Any:
    """
    Safely execute a function with comprehensive error handling.

    Args:
        func: Function to execute
        *args: Positional arguments for the function
        default_return: Value to return if function fails
        context: Context information for error logging
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for the function

    Returns:
        Function result or default_return if function fails
    """
    try:
        return func(*args, **kwargs)
    except SwarmError as e:
        if log_errors:
            logger.error(f"Swarm error in {context or func.__name__}: {e}")
        return default_return
    except Exception as e:
        if log_errors:
            logger.error(f"Unexpected error in {context or func.__name__}: {e}")
        return default_return


def convert_generic_exception(exception: Exception, context: str = "", **kwargs) -> SwarmError:
    """
    Convert a generic exception to an appropriate SwarmError.

    Args:
        exception: The original exception
        context: Context about where the error occurred
        **kwargs: Additional arguments for the specific exception

    Returns:
        An appropriate SwarmError instance
    """
    return create_exception_from_generic(exception, context, **kwargs)


def log_exception(
    exception: Exception, context: str = "", level: int = logging.ERROR, include_traceback: bool = False
) -> None:
    """
    Log an exception with appropriate formatting.

    Args:
        exception: The exception to log
        context: Context about where the error occurred
        level: Logging level
        include_traceback: Whether to include full traceback
    """
    if isinstance(exception, SwarmError):
        message = f"[{exception.error_code}] {exception.message}"
        if exception.details:
            message += f" | Details: {exception.details}"
    else:
        message = f"Unexpected error: {str(exception)}"

    if context:
        message = f"{context}: {message}"

    logger.log(level, message)

    if include_traceback:
        logger.log(level, "Traceback:", exc_info=True)


# Context managers for exception handling
class ExceptionContext:
    """Context manager for handling exceptions in specific contexts."""

    def __init__(self, context: str, default_return: Any = None, reraise: bool = True, log_errors: bool = True):
        self.context = context
        self.default_return = default_return
        self.reraise = reraise
        self.log_errors = log_errors
        self.exception = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.exception = exc_val

            if self.log_errors:
                log_exception(exc_val, self.context)

            if not self.reraise:
                return True  # Suppress the exception

        return False  # Let the exception propagate


# Async versions of decorators
def handle_async_browser_exceptions(func: Callable[..., T]) -> Callable[..., T]:
    """Async version of handle_browser_exceptions."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        try:
            return await func(*args, **kwargs)
        except (BrowserError, BrowserSessionError, BrowserNavigationError, BrowserElementError):
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "session" in error_msg:
                raise BrowserSessionError(str(e), details=f"Function: {func.__name__}")
            elif "navigation" in error_msg or "navigate" in error_msg:
                raise BrowserNavigationError(str(e), details=f"Function: {func.__name__}")
            elif "element" in error_msg or "click" in error_msg or "fill" in error_msg:
                raise BrowserElementError(str(e), details=f"Function: {func.__name__}")
            else:
                raise BrowserError(str(e), details=f"Function: {func.__name__}")

    return wrapper


def handle_async_web_exceptions(func: Callable[..., T]) -> Callable[..., T]:
    """Async version of handle_web_exceptions."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        try:
            return await func(*args, **kwargs)
        except (WebError, WebSearchError, WebContentError):
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "search" in error_msg:
                raise WebSearchError(str(e), details=f"Function: {func.__name__}")
            elif "content" in error_msg or "extract" in error_msg:
                raise WebContentError(str(e), details=f"Function: {func.__name__}")
            else:
                raise WebError(str(e), details=f"Function: {func.__name__}")

    return wrapper
