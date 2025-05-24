"""
Qwen client implementation supporting Qwen3 and QwQ series models.
QwQ models have reasoning capabilities.
"""

from typing import Dict, Any, List, Union, Iterator, Optional
import os
from .base import BaseLLM, ReasoningLLM, LLMConfig, ModelType


class QwenClient(ReasoningLLM):
    """Qwen client supporting Qwen3 and QwQ series with reasoning support."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        # QwQ models are reasoning models
        if "qwq" in config.model_name.lower():
            self._model_type = ModelType.REASONING
        else:
            self._model_type = ModelType.STANDARD
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Qwen client."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package is required for Qwen. Install with: pip install openai")
        
        api_key = self.config.api_key or os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("Qwen API key is required (QWEN_API_KEY or DASHSCOPE_API_KEY)")
        
        # Qwen uses OpenAI-compatible API through DashScope
        base_url = self.config.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """Generate response from Qwen model."""
        if not self.client:
            self._initialize_client()
        
        # For QwQ reasoning models, use specialized method
        if self._model_type == ModelType.REASONING:
            show_thinking = self.config.reasoning_config.show_thinking
            result = self.generate_with_reasoning(messages, show_thinking=show_thinking, **kwargs)
            
            if self.config.stream_config.enabled:
                # Extract content from reasoning response
                def extract_content():
                    for chunk in result:
                        if isinstance(chunk, dict) and "content" in chunk:
                            yield chunk["content"]
                return extract_content()
            else:
                return result.get("content", "") if isinstance(result, dict) else result
        
        # Standard generation for Qwen3 models
        params = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": self.config.temperature,
            "stream": self.config.stream_config.enabled,
            **self.config.extra_params,
            **kwargs
        }
        
        if self.config.max_tokens:
            params["max_tokens"] = self.config.max_tokens
        
        try:
            response = self.client.chat.completions.create(**params)
            
            if self.config.stream_config.enabled:
                return self._stream_response(response)
            else:
                return response.choices[0].message.content
                
        except Exception as e:
            raise RuntimeError(f"Qwen API error: {str(e)}")
    
    def generate_with_reasoning(
        self,
        messages: List[Dict[str, str]], 
        show_thinking: Optional[bool] = None,
        **kwargs
    ) -> Union[Dict[str, str], Iterator[Dict[str, str]]]:
        """Generate response with reasoning support for QwQ models."""
        if not self.client:
            self._initialize_client()
        
        if show_thinking is None:
            show_thinking = self.config.reasoning_config.show_thinking
        
        # Prepare parameters for QwQ reasoning model
        params = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": self.config.temperature,
            "stream": self.config.stream_config.enabled,
            **self.config.extra_params,
            **kwargs
        }
        
        if self.config.max_tokens:
            params["max_tokens"] = self.config.max_tokens
        
        # Add reasoning-specific parameters for QwQ
        if self.config.reasoning_config.max_thinking_tokens:
            params["max_thinking_tokens"] = self.config.reasoning_config.max_thinking_tokens
        
        try:
            response = self.client.chat.completions.create(**params)
            
            if self.config.stream_config.enabled:
                return self._stream_reasoning_response(response, show_thinking)
            else:
                choice = response.choices[0]
                result = {"content": choice.message.content}
                
                # Extract thinking process if available and requested
                if show_thinking and hasattr(choice.message, 'reasoning_content'):
                    result["thinking"] = choice.message.reasoning_content
                
                return result
                
        except Exception as e:
            raise RuntimeError(f"Qwen API error: {str(e)}")
    
    def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """Generate response with tool calling support."""
        if not self.client:
            self._initialize_client()
        
        params = {
            "model": self.config.model_name,
            "messages": messages,
            "tools": tools,
            "temperature": self.config.temperature,
            "stream": self.config.stream_config.enabled,
            **self.config.extra_params,
            **kwargs
        }
        
        if self.config.max_tokens:
            params["max_tokens"] = self.config.max_tokens
        
        try:
            response = self.client.chat.completions.create(**params)
            
            if self.config.stream_config.enabled:
                return self._stream_response_with_tools(response)
            else:
                choice = response.choices[0]
                if choice.message.tool_calls:
                    return {
                        "content": choice.message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "function": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                            for tc in choice.message.tool_calls
                        ]
                    }
                return choice.message.content
                
        except Exception as e:
            raise RuntimeError(f"Qwen API error: {str(e)}")
    
    def _stream_response(self, response) -> Iterator[str]:
        """Process streaming response."""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    def _stream_reasoning_response(self, response, show_thinking: bool) -> Iterator[Dict[str, str]]:
        """Process streaming response with reasoning support."""
        for chunk in response:
            delta = chunk.choices[0].delta
            
            result = {}
            if delta.content is not None:
                result["content"] = delta.content
            
            # Handle thinking content if available and requested
            if show_thinking and hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                result["thinking"] = delta.reasoning_content
            
            if result:
                yield result
    
    def _stream_response_with_tools(self, response) -> Iterator[Dict[str, Any]]:
        """Process streaming response with tool calls."""
        content_buffer = ""
        tool_calls_buffer = {}
        
        for chunk in response:
            delta = chunk.choices[0].delta
            
            # Handle content
            if delta.content is not None:
                content_buffer += delta.content
                yield {"type": "content", "content": delta.content}
            
            # Handle tool calls
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.id not in tool_calls_buffer:
                        tool_calls_buffer[tc.id] = {
                            "id": tc.id,
                            "function": tc.function.name if tc.function.name else "",
                            "arguments": tc.function.arguments if tc.function.arguments else ""
                        }
                    else:
                        if tc.function.arguments:
                            tool_calls_buffer[tc.id]["arguments"] += tc.function.arguments
                
                yield {"type": "tool_call", "tool_calls": list(tool_calls_buffer.values())}
    
    @classmethod
    def create_qwen3_turbo(cls, api_key: str = None, **kwargs) -> 'QwenClient':
        """Convenience method to create Qwen3-Turbo client."""
        config = LLMConfig(
            model_name="qwen-turbo",
            api_key=api_key,
            **kwargs
        )
        return cls(config)
    
    @classmethod
    def create_qwen3_plus(cls, api_key: str = None, **kwargs) -> 'QwenClient':
        """Convenience method to create Qwen3-Plus client."""
        config = LLMConfig(
            model_name="qwen-plus",
            api_key=api_key,
            **kwargs
        )
        return cls(config)
    
    @classmethod
    def create_qwen3_max(cls, api_key: str = None, **kwargs) -> 'QwenClient':
        """Convenience method to create Qwen3-Max client."""
        config = LLMConfig(
            model_name="qwen-max",
            api_key=api_key,
            **kwargs
        )
        return cls(config)
    
    @classmethod
    def create_qwq_32b_preview(cls, api_key: str = None, show_thinking: bool = False, **kwargs) -> 'QwenClient':
        """Convenience method to create QwQ-32B-Preview reasoning client."""
        from .base import ReasoningConfig
        config = LLMConfig(
            model_name="qwq-32b-preview",
            api_key=api_key,
            reasoning_config=ReasoningConfig(show_thinking=show_thinking),
            **kwargs
        )
        return cls(config)
    
    @classmethod
    def create_qwen_coder_turbo(cls, api_key: str = None, **kwargs) -> 'QwenClient':
        """Convenience method to create Qwen-Coder-Turbo client."""
        config = LLMConfig(
            model_name="qwen-coder-turbo",
            api_key=api_key,
            **kwargs
        )
        return cls(config) 