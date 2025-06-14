"""
Swarm - A comprehensive CLI-based agent for web browsing and automation with LLM integration.
"""

__version__ = "0.1.0"
__author__ = "Swarm Team"
__description__ = "A comprehensive CLI based agent for web browsing, testing, and automation with LLM integration"

from swarm.core.config import Config
from swarm.core.exceptions import SwarmError

__all__ = ["Config", "SwarmError", "__version__"]
