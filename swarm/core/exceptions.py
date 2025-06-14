"""
Custom exceptions for Swarm.
"""


class SwarmError(Exception):
    """Base exception for all Swarm errors."""

    def __init__(self, message: str, details: str = "") -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)


class LLMError(SwarmError):
    """Exception raised for LLM-related errors."""

    pass


class BrowserError(SwarmError):
    """Exception raised for browser automation errors."""

    pass


class WebError(SwarmError):
    """Exception raised for web-related errors."""

    pass


class ConfigError(SwarmError):
    """Exception raised for configuration errors."""

    pass


class ValidationError(SwarmError):
    """Exception raised for validation errors."""

    pass
