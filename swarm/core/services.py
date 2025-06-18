"""
Service Container - Clean dependency injection for Swarm services.

This module provides a centralized service container that eliminates
the need to pass configuration objects deep into the call stack.
"""

from typing import TypeVar

from swarm.core.config import Config
from swarm.llm.client import LLMClient
from swarm.web.browser import Browser
from swarm.web.search import WebSearch

T = TypeVar("T")


class ServiceContainer:
    """
    Dependency injection container for Swarm services.

    This eliminates the need to pass config objects throughout the application
    and provides a clean way to access services from anywhere.
    """

    _instance = None
    _services = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, config: Config) -> None:
        """Initialize the service container with configuration."""
        container = cls()
        container._config = config
        container._services = {}

        # Register core services
        container._services["browser"] = Browser(config.browser)
        container._services["search"] = WebSearch(config.search)
        container._services["llm"] = LLMClient(config.llm)

    @classmethod
    def get_browser(cls) -> Browser:
        """Get the browser service."""
        return cls()._services["browser"]

    @classmethod
    def get_search(cls) -> WebSearch:
        """Get the search service."""
        return cls()._services["search"]

    @classmethod
    def get_llm(cls) -> LLMClient:
        """Get the LLM service."""
        return cls()._services["llm"]

    @classmethod
    def get_config(cls) -> Config:
        """Get the configuration."""
        return cls()._config

    @classmethod
    def reset(cls) -> None:
        """Reset the container (useful for testing)."""
        cls._instance = None


class ServiceMixin:
    """
    Mixin class that provides easy access to services.

    Classes can inherit from this to get clean access to services
    without needing config objects passed around.
    """

    @property
    def browser(self) -> Browser:
        """Get browser service."""
        return ServiceContainer.get_browser()

    @property
    def search(self) -> WebSearch:
        """Get search service."""
        return ServiceContainer.get_search()

    @property
    def llm(self) -> LLMClient:
        """Get LLM service."""
        return ServiceContainer.get_llm()

    @property
    def config(self) -> Config:
        """Get configuration."""
        return ServiceContainer.get_config()
