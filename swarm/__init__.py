"""
Swarm - A comprehensive platform for multi-LLM integration and canvas-like applications.
"""

# Import LLM module for easy access
try:
    from . import llm
    from .llm import LLMFactory
except ImportError:
    # LLM module might not be available if dependencies aren't installed
    llm = None
    LLMFactory = None

__version__ = "0.1.0"
__all__ = ["llm", "LLMFactory"] 