"""
Browser automation module with modular design.

This module provides a clean, modular interface to browser automation
using Playwright, split into focused components for better maintainability.
"""

from .browser import Browser

__all__ = ["Browser"]
