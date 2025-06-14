"""
Logging utilities for Swarm.
"""

import logging

from rich.console import Console
from rich.logging import RichHandler

from swarm.core.config import LoggingConfig


def setup_logging(config: LoggingConfig) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        config: Logging configuration

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("swarm")
    logger.setLevel(getattr(logging, config.level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Create console handler with Rich
    console = Console()
    console_handler = RichHandler(console=console, show_time=True, show_path=False, markup=True)
    console_handler.setLevel(getattr(logging, config.level.upper()))

    # Create formatter
    formatter = logging.Formatter("%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(formatter)

    # Add console handler
    logger.addHandler(console_handler)

    # Add file handler if specified
    if config.file:
        file_handler = logging.FileHandler(config.file)
        file_handler.setLevel(getattr(logging, config.level.upper()))

        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)

        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "swarm") -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
