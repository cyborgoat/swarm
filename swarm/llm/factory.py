"""
LLM Factory for easy model instantiation.
Provides a unified interface to create any supported LLM client.
"""

import json
import os
from typing import Dict, Any, Optional, Union, Type
from .base import LLMConfig, StreamConfig, ReasoningConfig, MCPConfig, BaseLLM
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .qwen_client import QwenClient
from .gemini_client import GeminiClient
from .deepseek_client import DeepSeekClient

# Define a mapping for API key names based on provider type
# This helps in fetching the correct API key from config or environment
PROVIDER_API_KEY_NAMES = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "qwen": "DASHSCOPE_API_KEY", # Qwen typically uses Dashscope
    "gemini": "GOOGLE_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}

class LLMFactory:
    """Factory class for creating LLM clients, now driven by config.json."""
    
    _config_data: Optional[Dict[str, Any]] = None
    _llm_configurations: Optional[Dict[str, Dict[str, Any]]] = None
    _api_keys_from_config: Optional[Dict[str, str]] = None

    # Model mappings (could also be moved to config or dynamically determined)
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
    def _load_json_config(cls, config_path: Optional[str] = None) -> None:
        """Loads configurations from the specified JSON file or default 'llm_config.json'."""
        if cls._config_data is not None: # Already loaded
            return

        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
            default_config_path = os.path.join(project_root, "llm_config.json")
            config_path = default_config_path

        try:
            print(f"LLMFactory: Loading LLM configuration from {config_path}")
            with open(config_path, 'r') as f:
                cls._config_data = json.load(f)
            
            cls._llm_configurations = cls._config_data.get("llm_configurations", {})
            cls._api_keys_from_config = cls._config_data.get("api_keys", {})
            if not cls._llm_configurations:
                 print("LLMFactory: 'llm_configurations' not found or empty in llm_config.json.")
            if not cls._api_keys_from_config:
                 print("LLMFactory: 'api_keys' not found or empty in llm_config.json.")

        except FileNotFoundError:
            print(f"LLMFactory: LLM configuration file {config_path} not found. Using defaults and environment variables.")
            cls._config_data = {}
            cls._llm_configurations = {}
            cls._api_keys_from_config = {}
        except json.JSONDecodeError:
            print(f"LLMFactory: Error decoding JSON from LLM configuration file {config_path}. Using defaults.")
            cls._config_data = {}
            cls._llm_configurations = {}
            cls._api_keys_from_config = {}

    @classmethod
    def _get_provider_for_model(cls, model_name: str) -> Optional[str]:
        """Determines the provider (openai, anthropic, etc.) for a given model name."""
        model_name_lower = model_name.lower()
        if model_name_lower in cls.OPENAI_MODELS or model_name_lower.startswith("gpt-"): return "openai"
        if model_name_lower in cls.ANTHROPIC_MODELS or model_name_lower.startswith("claude-"): return "anthropic"
        if model_name_lower in cls.QWEN_MODELS or model_name_lower.startswith(("qwen-", "qwq-")): return "qwen"
        if model_name_lower in cls.GEMINI_MODELS or model_name_lower.startswith("gemini-"): return "gemini"
        if model_name_lower in cls.DEEPSEEK_MODELS or model_name_lower.startswith("deepseek-"): return "deepseek"
        # Fallback: check if any provider key is a prefix of the model name
        for provider in PROVIDER_API_KEY_NAMES.keys():
            if model_name_lower.startswith(provider + "-"): # e.g. "openai-gpt-4"
                return provider
        print(f"LLMFactory: Could not determine provider for model: {model_name}")
        return None

    @classmethod
    def _resolve_api_key(cls, model_name: str, config_api_key: Optional[str]) -> Optional[str]:
        """Resolves API key: config > api_keys section in config > environment variable."""
        cls._load_json_config() # Ensure API keys from config are loaded

        if config_api_key: # API key directly in the LLM configuration
            return config_api_key

        provider = cls._get_provider_for_model(model_name)
        if provider:
            api_key_name = PROVIDER_API_KEY_NAMES.get(provider)
            if api_key_name:
                # Check in "api_keys" section of config.json
                key_from_config_section = cls._api_keys_from_config.get(api_key_name)
                if key_from_config_section and key_from_config_section not in ["", f"YOUR_{api_key_name}_OR_LEAVE_BLANK_IF_ENV_SET"]: # Check if placeholder
                    return key_from_config_section
                # Check environment variable (clients typically handle this, but good for completeness)
                # The actual client constructors will also look for env vars if api_key is None.
                # env_key = os.getenv(api_key_name)
                # if env_key: return env_key 
        return None # Let the client try to find it in env or raise error

    @classmethod
    def _create_client_from_llm_config(cls, llm_config: LLMConfig) -> BaseLLM:
        """Internal: Creates the LLM client instance from a fully resolved LLMConfig."""
        model_name = llm_config.model_name
        provider = cls._get_provider_for_model(model_name)

        client_class: Optional[Type[BaseLLM]] = None
        if provider == "openai": client_class = OpenAIClient
        elif provider == "anthropic": client_class = AnthropicClient
        elif provider == "qwen": client_class = QwenClient
        elif provider == "gemini": client_class = GeminiClient
        elif provider == "deepseek": client_class = DeepSeekClient
        
        if client_class:
            return client_class(llm_config)
        else:
            # Fallback or attempt to guess based on common prefixes if not explicitly known
            # This part can be expanded or made more robust
            if model_name.startswith("gpt-") or model_name in cls.OPENAI_MODELS:
                 return OpenAIClient(llm_config)
            if model_name.startswith("claude-") or model_name in cls.ANTHROPIC_MODELS:
                 return AnthropicClient(llm_config)
            if model_name.startswith(("qwen-", "qwq-")) or model_name in cls.QWEN_MODELS:
                 return QwenClient(llm_config)
            if model_name.startswith("gemini-") or model_name in cls.GEMINI_MODELS:
                 return GeminiClient(llm_config)
            if model_name.startswith("deepseek-") or model_name in cls.DEEPSEEK_MODELS:
                 return DeepSeekClient(llm_config)
            raise ValueError(f"LLMFactory: Unknown or unsupported model provider for: {model_name}")

    @classmethod
    def create_from_config(
        cls,
        config_name: str,
        config_path: Optional[str] = None,
        **override_kwargs
    ) -> BaseLLM:
        """
        Creates an LLM client based on a named configuration from llm_config.json.
        Overrides from kwargs take precedence.
        """
        cls._load_json_config(config_path)

        if not cls._llm_configurations:
            raise ValueError("LLMFactory: No LLM configurations loaded. Check llm_config.json.")
        
        base_config_dict = cls._llm_configurations.get(config_name)
        if not base_config_dict:
            raise ValueError(f"LLMFactory: Configuration '{config_name}' not found in llm_config.json.")

        # Create a mutable copy and override with kwargs
        effective_config_dict = base_config_dict.copy()
        effective_config_dict.update(override_kwargs)
        
        # Extract nested config objects or use defaults
        # Handle cases where the override might be a dict or already a config object
        stream_config_val = effective_config_dict.pop("stream_config", {})
        if isinstance(stream_config_val, StreamConfig):
            stream_config = stream_config_val
        elif isinstance(stream_config_val, dict):
            stream_config = StreamConfig(**stream_config_val)
        else:
            stream_config = StreamConfig() # Default

        reasoning_config_val = effective_config_dict.pop("reasoning_config", {})
        if isinstance(reasoning_config_val, ReasoningConfig):
            reasoning_config = reasoning_config_val
        elif isinstance(reasoning_config_val, dict):
            reasoning_config = ReasoningConfig(**reasoning_config_val)
        else:
            reasoning_config = ReasoningConfig() # Default

        mcp_config_val = effective_config_dict.pop("mcp_config", {})
        if isinstance(mcp_config_val, MCPConfig):
            mcp_config = mcp_config_val
        elif isinstance(mcp_config_val, dict):
            mcp_config = MCPConfig(**mcp_config_val)
        else:
            mcp_config = MCPConfig() # Default

        # Resolve API key
        model_name = effective_config_dict.get("model_name")
        if not model_name:
            raise ValueError("LLMFactory: 'model_name' is required in the configuration.")
        
        # API key from the llm_configuration entry itself takes highest precedence IF NOT NULL
        config_entry_api_key = effective_config_dict.get("api_key")
        
        final_api_key = cls._resolve_api_key(model_name, config_entry_api_key)

        llm_config_obj = LLMConfig(
            model_name=model_name,
            api_key=final_api_key,
            base_url=effective_config_dict.get("base_url"),
            temperature=float(effective_config_dict.get("temperature", 0.7)),
            max_tokens=int(effective_config_dict["max_tokens"]) if effective_config_dict.get("max_tokens") is not None else None,
            stream_config=stream_config,
            reasoning_config=reasoning_config,
            mcp_config=mcp_config,
            extra_params=effective_config_dict.get("extra_params", {})
        )
        
        return cls._create_client_from_llm_config(llm_config_obj)

    @classmethod
    def create(
        cls,
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False, # Kept for backward compatibility / direct creation
        show_thinking: bool = False, # Kept for backward compatibility
        # mcp specific params could be added here if direct creation needs them
        **kwargs # For extra_params and other potential overrides
    ) -> BaseLLM:
        """
        Creates an LLM client directly with specified parameters.
        Consider using create_from_config for managed configurations.
        """
        cls._load_json_config() # Load api_keys for potential fallback

        # Resolve API key if not directly provided
        resolved_api_key = api_key
        if not resolved_api_key:
             resolved_api_key = cls._resolve_api_key(model_name, None) # Check config api_keys and env

        stream_config = StreamConfig(enabled=stream, chunk_size=kwargs.pop("stream_chunk_size", None), timeout=kwargs.pop("stream_timeout", None))
        reasoning_config = ReasoningConfig(show_thinking=show_thinking, max_thinking_tokens=kwargs.pop("reasoning_max_tokens", None), reasoning_effort=kwargs.pop("reasoning_effort", None))
        mcp_config = MCPConfig(enabled=kwargs.pop("mcp_enabled", False), server_url=kwargs.pop("mcp_server_url", None), tools=kwargs.pop("mcp_tools", None), max_tokens=kwargs.pop("mcp_max_tokens", None))
        
        config = LLMConfig(
            model_name=model_name,
            api_key=resolved_api_key, # Use the resolved one
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            stream_config=stream_config,
            reasoning_config=reasoning_config,
            mcp_config=mcp_config,
            extra_params=kwargs # Remaining kwargs are passed as extra_params
        )
        
        return cls._create_client_from_llm_config(config)

    # Convenience methods (can be updated or removed if create_from_config is preferred)
    @classmethod
    def create_openai(cls, model: str = "gpt-4o", **kwargs) -> OpenAIClient: # Ensure return type matches BaseLLM or its subtypes
        return cls.create(model_name=model, **kwargs) # type: ignore

    @classmethod
    def create_anthropic(cls, model: str = "claude-3-sonnet-20240229", **kwargs) -> AnthropicClient:
        return cls.create(model_name=model, **kwargs) # type: ignore

    @classmethod
    def create_qwen(cls, model: str = "qwen-turbo", **kwargs) -> QwenClient:
        return cls.create(model_name=model, **kwargs) # type: ignore

    @classmethod
    def create_gemini(cls, model: str = "gemini-1.5-pro", **kwargs) -> GeminiClient:
        return cls.create(model_name=model, **kwargs) # type: ignore

    @classmethod
    def create_deepseek(cls, model: str = "deepseek-chat", **kwargs) -> DeepSeekClient:
        return cls.create(model_name=model, **kwargs) # type: ignore
    
    @classmethod
    def create_reasoning_model(
        cls,
        model: str = "deepseek-reasoner", # Default to a known reasoning model
        show_thinking: bool = True,
        **kwargs
    ) -> BaseLLM: # Return BaseLLM
        if model not in cls.REASONING_MODELS:
            # Attempt to find if a config for this model exists and if it enables reasoning
            cls._load_json_config()
            config_entry = cls._llm_configurations.get(model, {}) if cls._llm_configurations else {}
            reasoning_config = config_entry.get("reasoning_config", {})
            if not reasoning_config.get("show_thinking", False) and not show_thinking : # if not enabled by default or override
                 print(f"LLMFactory: Warning - Model {model} might not be pre-configured for reasoning or reasoning is not explicitly enabled.")
        
        # Pass show_thinking to the create method
        return cls.create(model_name=model, show_thinking=show_thinking, **kwargs)

    @classmethod
    def list_models(cls) -> Dict[str, list]:
        return {
            "openai": list(cls.OPENAI_MODELS),
            "anthropic": list(cls.ANTHROPIC_MODELS),
            "qwen": list(cls.QWEN_MODELS),
            "gemini": list(cls.GEMINI_MODELS),
            "deepseek": list(cls.DEEPSEEK_MODELS),
        }

    @classmethod
    def list_reasoning_models(cls) -> list:
        return list(cls.REASONING_MODELS)

    @classmethod
    def list_available_configs(cls) -> list:
        cls._load_json_config()
        return list(cls._llm_configurations.keys()) if cls._llm_configurations else []

# Convenience functions (might need update or removal if factory methods are primary)
# These would ideally call LLMFactory.create directly.
# Example:
# def create_openai_client(model: str = "gpt-4", **kwargs) -> OpenAIClient:
#     return LLMFactory.create_openai(model, **kwargs) # This is fine

# ... (other convenience functions remain similar for now)
# Keeping convenience functions as they delegate to the updated LLMFactory.create
def create_openai_client(model: str = "gpt-4o", **kwargs) -> OpenAIClient:
    return LLMFactory.create_openai(model, **kwargs)

def create_anthropic_client(model: str = "claude-3-sonnet-20240229", **kwargs) -> AnthropicClient:
    return LLMFactory.create_anthropic(model, **kwargs)

def create_qwen_client(model: str = "qwen-turbo", **kwargs) -> QwenClient:
    return LLMFactory.create_qwen(model, **kwargs)

def create_gemini_client(model: str = "gemini-1.5-pro", **kwargs) -> GeminiClient:
    return LLMFactory.create_gemini(model, **kwargs)

def create_deepseek_client(model: str = "deepseek-chat", **kwargs) -> DeepSeekClient:
    return LLMFactory.create_deepseek(model, **kwargs)

def create_reasoning_client(model: str = "deepseek-reasoner", show_thinking: bool = True, **kwargs) -> BaseLLM:
    return LLMFactory.create_reasoning_model(model, show_thinking=show_thinking, **kwargs) 