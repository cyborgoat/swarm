"""
LLM Factory for easy model instantiation.
Provides a unified interface to create any supported LLM client.
"""

from typing import Dict, Any, Optional, Union
from .base import LLMConfig, StreamConfig, ReasoningConfig, MCPConfig
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .qwen_client import QwenClient
from .gemini_client import GeminiClient
from .deepseek_client import DeepSeekClient


class LLMFactory:
    """Factory class for creating LLM clients."""
    
    # Model mappings
    OPENAI_MODELS = {
        "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
        "gpt-3.5-turbo", "gpt-3.5-turbo-16k",
        "gpt-4-vision-preview", "gpt-4-turbo-preview"
    }
    
    ANTHROPIC_MODELS = {
        "claude-3-opus-20240229", "claude-3-sonnet-20240229", 
        "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022"
    }
    
    QWEN_MODELS = {
        "qwen-turbo", "qwen-plus", "qwen-max", 
        "qwen-coder-turbo", "qwq-32b-preview"
    }
    
    GEMINI_MODELS = {
        "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.5-flash-8b",
        "gemini-2.0-flash-exp", "gemini-pro", "gemini-pro-vision"
    }
    
    DEEPSEEK_MODELS = {
        "deepseek-chat", "deepseek-reasoner", "deepseek-coder"
    }
    
    # Reasoning models
    REASONING_MODELS = {
        "deepseek-reasoner", "qwq-32b-preview"
    }
    
    @classmethod
    def create(
        cls,
        model_name: str,
        api_key: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        show_thinking: bool = False,
        base_url: Optional[str] = None,
        **kwargs
    ) -> Union[OpenAIClient, AnthropicClient, QwenClient, GeminiClient, DeepSeekClient]:
        """
        Create an LLM client based on the model name.
        
        Args:
            model_name: Name of the model to use
            api_key: API key for the service
            stream: Whether to enable streaming
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            show_thinking: Whether to show reasoning process (for reasoning models)
            base_url: Custom base URL for the API
            **kwargs: Additional parameters
            
        Returns:
            Appropriate LLM client instance
        """
        
        # Create configurations
        stream_config = StreamConfig(enabled=stream)
        reasoning_config = ReasoningConfig(show_thinking=show_thinking)
        mcp_config = MCPConfig()
        
        config = LLMConfig(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            stream_config=stream_config,
            reasoning_config=reasoning_config,
            mcp_config=mcp_config,
            extra_params=kwargs
        )
        
        # Determine which client to use based on model name
        if cls._is_openai_model(model_name):
            return OpenAIClient(config)
        elif cls._is_anthropic_model(model_name):
            return AnthropicClient(config)
        elif cls._is_qwen_model(model_name):
            return QwenClient(config)
        elif cls._is_gemini_model(model_name):
            return GeminiClient(config)
        elif cls._is_deepseek_model(model_name):
            return DeepSeekClient(config)
        else:
            raise ValueError(f"Unknown model: {model_name}")
    
    @classmethod
    def create_openai(
        cls,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        **kwargs
    ) -> OpenAIClient:
        """Create an OpenAI client."""
        return cls.create(model, api_key=api_key, **kwargs)
    
    @classmethod
    def create_anthropic(
        cls,
        model: str = "claude-3-sonnet-20240229",
        api_key: Optional[str] = None,
        **kwargs
    ) -> AnthropicClient:
        """Create an Anthropic client."""
        return cls.create(model, api_key=api_key, **kwargs)
    
    @classmethod
    def create_qwen(
        cls,
        model: str = "qwen-turbo",
        api_key: Optional[str] = None,
        **kwargs
    ) -> QwenClient:
        """Create a Qwen client."""
        return cls.create(model, api_key=api_key, **kwargs)
    
    @classmethod
    def create_gemini(
        cls,
        model: str = "gemini-1.5-pro",
        api_key: Optional[str] = None,
        **kwargs
    ) -> GeminiClient:
        """Create a Gemini client."""
        return cls.create(model, api_key=api_key, **kwargs)
    
    @classmethod
    def create_deepseek(
        cls,
        model: str = "deepseek-chat",
        api_key: Optional[str] = None,
        **kwargs
    ) -> DeepSeekClient:
        """Create a DeepSeek client."""
        return cls.create(model, api_key=api_key, **kwargs)
    
    @classmethod
    def create_reasoning_model(
        cls,
        model: str = "deepseek-reasoner",
        api_key: Optional[str] = None,
        show_thinking: bool = True,
        **kwargs
    ) -> Union[DeepSeekClient, QwenClient]:
        """Create a reasoning model with thinking display enabled."""
        if model not in cls.REASONING_MODELS:
            raise ValueError(f"Model {model} is not a reasoning model. "
                           f"Available reasoning models: {list(cls.REASONING_MODELS)}")
        
        return cls.create(
            model, 
            api_key=api_key, 
            show_thinking=show_thinking, 
            **kwargs
        )
    
    @classmethod
    def list_models(cls) -> Dict[str, list]:
        """List all available models by provider."""
        return {
            "openai": list(cls.OPENAI_MODELS),
            "anthropic": list(cls.ANTHROPIC_MODELS),
            "qwen": list(cls.QWEN_MODELS),
            "gemini": list(cls.GEMINI_MODELS),
            "deepseek": list(cls.DEEPSEEK_MODELS)
        }
    
    @classmethod
    def list_reasoning_models(cls) -> list:
        """List all available reasoning models."""
        return list(cls.REASONING_MODELS)
    
    @classmethod
    def _is_openai_model(cls, model_name: str) -> bool:
        """Check if model is an OpenAI model."""
        return model_name in cls.OPENAI_MODELS or model_name.startswith("gpt-")
    
    @classmethod
    def _is_anthropic_model(cls, model_name: str) -> bool:
        """Check if model is an Anthropic model."""
        return model_name in cls.ANTHROPIC_MODELS or model_name.startswith("claude-")
    
    @classmethod
    def _is_qwen_model(cls, model_name: str) -> bool:
        """Check if model is a Qwen model."""
        return model_name in cls.QWEN_MODELS or model_name.startswith(("qwen-", "qwq-"))
    
    @classmethod
    def _is_gemini_model(cls, model_name: str) -> bool:
        """Check if model is a Gemini model."""
        return model_name in cls.GEMINI_MODELS or model_name.startswith("gemini-")
    
    @classmethod
    def _is_deepseek_model(cls, model_name: str) -> bool:
        """Check if model is a DeepSeek model."""
        return model_name in cls.DEEPSEEK_MODELS or model_name.startswith("deepseek-")


# Convenience functions for quick access
def create_openai_client(model: str = "gpt-4", **kwargs) -> OpenAIClient:
    """Quick function to create OpenAI client."""
    return LLMFactory.create_openai(model, **kwargs)


def create_anthropic_client(model: str = "claude-3-sonnet-20240229", **kwargs) -> AnthropicClient:
    """Quick function to create Anthropic client."""
    return LLMFactory.create_anthropic(model, **kwargs)


def create_qwen_client(model: str = "qwen-turbo", **kwargs) -> QwenClient:
    """Quick function to create Qwen client."""
    return LLMFactory.create_qwen(model, **kwargs)


def create_gemini_client(model: str = "gemini-1.5-pro", **kwargs) -> GeminiClient:
    """Quick function to create Gemini client."""
    return LLMFactory.create_gemini(model, **kwargs)


def create_deepseek_client(model: str = "deepseek-chat", **kwargs) -> DeepSeekClient:
    """Quick function to create DeepSeek client."""
    return LLMFactory.create_deepseek(model, **kwargs)


def create_reasoning_client(model: str = "deepseek-reasoner", show_thinking: bool = True, **kwargs):
    """Quick function to create reasoning model client."""
    return LLMFactory.create_reasoning_model(model, show_thinking=show_thinking, **kwargs) 