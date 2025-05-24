"""
Base classes and configurations for LLM clients.
Provides common interface for all LLM providers with streaming, reasoning, and MCP support.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Iterator, Union, List
from enum import Enum


class ModelType(Enum):
    """Types of models available."""
    STANDARD = "standard"
    REASONING = "reasoning"
    CODE = "code"
    MULTIMODAL = "multimodal"


@dataclass
class StreamConfig:
    """Configuration for streaming responses."""
    enabled: bool = False
    chunk_size: Optional[int] = None
    timeout: Optional[float] = None


@dataclass
class ReasoningConfig:
    """Configuration for reasoning models."""
    show_thinking: bool = False
    max_thinking_tokens: Optional[int] = None
    reasoning_effort: Optional[str] = None  # "low", "medium", "high"


@dataclass
class MCPConfig:
    """Configuration for Model Context Protocol support."""
    enabled: bool = False
    server_url: Optional[str] = None
    tools: Optional[List[str]] = None
    max_tokens: Optional[int] = None


@dataclass
class LLMConfig:
    """Complete configuration for LLM client."""
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream_config: StreamConfig = field(default_factory=StreamConfig)
    reasoning_config: ReasoningConfig = field(default_factory=ReasoningConfig)
    mcp_config: MCPConfig = field(default_factory=MCPConfig)
    extra_params: Dict[str, Any] = field(default_factory=dict)


class BaseLLM(ABC):
    """Abstract base class for all LLM clients."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._model_type = ModelType.STANDARD
        
    @property
    def model_type(self) -> ModelType:
        """Get the type of this model."""
        return self._model_type
    
    @property
    def supports_streaming(self) -> bool:
        """Whether this model supports streaming."""
        return True
    
    @property
    def supports_reasoning(self) -> bool:
        """Whether this model supports reasoning display."""
        return self._model_type == ModelType.REASONING
    
    @property
    def supports_mcp(self) -> bool:
        """Whether this model supports Model Context Protocol."""
        return False
    
    @abstractmethod
    def _initialize_client(self):
        """Initialize the underlying client."""
        pass
    
    @abstractmethod
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """
        Generate response from the model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters
            
        Returns:
            String response or iterator of string chunks if streaming
        """
        pass
    
    @abstractmethod
    def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """Generate response with tool calling support."""
        pass
    
    def validate_config(self) -> bool:
        """Validate the configuration."""
        if not self.config.model_name:
            raise ValueError("model_name is required")
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        return {
            "model_name": self.config.model_name,
            "model_type": self.model_type.value,
            "supports_streaming": self.supports_streaming,
            "supports_reasoning": self.supports_reasoning,
            "supports_mcp": self.supports_mcp,
            "base_url": self.config.base_url
        }


class ReasoningLLM(BaseLLM):
    """Base class for reasoning models with thinking display support."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._model_type = ModelType.REASONING
    
    @abstractmethod
    def generate_with_reasoning(
        self,
        messages: List[Dict[str, str]], 
        show_thinking: Optional[bool] = None,
        **kwargs
    ) -> Union[Dict[str, str], Iterator[Dict[str, str]]]:
        """
        Generate response with reasoning support.
        
        Args:
            messages: List of message dictionaries
            show_thinking: Whether to show the thinking process
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with 'content' and optionally 'thinking' keys
            or iterator of such dictionaries if streaming
        """
        pass


class MCPSupportedLLM(BaseLLM):
    """Base class for models that support Model Context Protocol."""
    
    @property
    def supports_mcp(self) -> bool:
        return True
    
    @abstractmethod
    def connect_mcp_server(self, server_url: str, tools: List[str] = None):
        """Connect to an MCP server."""
        pass
    
    @abstractmethod
    def list_mcp_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools."""
        pass 