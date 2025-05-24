# LLM Package - Easy to use modules for various LLM providers
# Supports streaming, reasoning models, and Model Context Protocol

from .base import BaseLLM, ReasoningConfig, StreamConfig
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .qwen_client import QwenClient
from .gemini_client import GeminiClient
from .deepseek_client import DeepSeekClient

# Model factory for easy instantiation
from .factory import (
    LLMFactory,
    create_openai_client,
    create_anthropic_client,
    create_qwen_client,
    create_gemini_client,
    create_deepseek_client,
    create_reasoning_client
)

__all__ = [
    'BaseLLM',
    'ReasoningConfig', 
    'StreamConfig',
    'OpenAIClient',
    'AnthropicClient', 
    'QwenClient',
    'GeminiClient',
    'DeepSeekClient',
    'LLMFactory',
    'create_openai_client',
    'create_anthropic_client',
    'create_qwen_client', 
    'create_gemini_client',
    'create_deepseek_client',
    'create_reasoning_client'
]

__version__ = "1.0.0"
