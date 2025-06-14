"""
Research module for Swarm - AI-powered topic investigation.

This module provides comprehensive research capabilities with:
- Web search and content analysis
- Image detection and extraction
- LLM-powered synthesis
- Professional report generation
"""

from .assistant import ResearchAssistant
from .formatter import ResearchFormatter

__all__ = ['ResearchAssistant', 'ResearchFormatter']
