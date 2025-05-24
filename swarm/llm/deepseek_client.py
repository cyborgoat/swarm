"""
DeepSeek client implementation with reasoning model support.
Based on DeepSeek API docs: https://api-docs.deepseek.com/
"""

from typing import Dict, Any, List, Union, Iterator, Optional
import os
from .base import BaseLLM, ReasoningLLM, LLMConfig, ModelType


class DeepSeekClient(ReasoningLLM):
    """DeepSeek client with reasoning model support (DeepSeek-R1)."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        # DeepSeek-reasoner is a reasoning model
        if "reasoner" in config.model_name.lower():
            self._model_type = ModelType.REASONING
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the DeepSeek client using OpenAI-compatible API."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package is required for DeepSeek. Install with: pip install openai")
        
        api_key = self.config.api_key or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DeepSeek API key is required")
        
        # DeepSeek uses OpenAI-compatible API
        base_url = self.config.base_url or "https://api.deepseek.com"
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """Generate response from DeepSeek model."""
        if not self.client:
            self._initialize_client()
        
        # For reasoning models, use specialized method
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
        
        # Standard generation for non-reasoning models
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
            raise RuntimeError(f"DeepSeek API error: {str(e)}")
    
    def generate_with_reasoning(
        self,
        messages: List[Dict[str, str]], 
        show_thinking: Optional[bool] = None,
        **kwargs
    ) -> Union[Dict[str, str], Iterator[Dict[str, str]]]:
        """Generate response with reasoning support for DeepSeek-R1."""
        if not self.client:
            self._initialize_client()
        
        if show_thinking is None:
            show_thinking = self.config.reasoning_config.show_thinking
        
        # Prepare parameters for reasoning model
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
        
        # Add reasoning-specific parameters
        if self.config.reasoning_config.reasoning_effort:
            params["reasoning_effort"] = self.config.reasoning_config.reasoning_effort
        
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
            raise RuntimeError(f"DeepSeek API error: {str(e)}")
    
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
            raise RuntimeError(f"DeepSeek API error: {str(e)}")
    
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
    def create_deepseek_chat(cls, api_key: str = None, **kwargs) -> 'DeepSeekClient':
        """Convenience method to create DeepSeek-V3 (deepseek-chat) client."""
        config = LLMConfig(
            model_name="deepseek-chat",
            api_key=api_key,
            **kwargs
        )
        return cls(config)
    
    @classmethod
    def create_deepseek_reasoner(cls, api_key: str = None, show_thinking: bool = False, **kwargs) -> 'DeepSeekClient':
        """Convenience method to create DeepSeek-R1 (deepseek-reasoner) client."""
        from .base import ReasoningConfig
        config = LLMConfig(
            model_name="deepseek-reasoner",
            api_key=api_key,
            reasoning_config=ReasoningConfig(show_thinking=show_thinking),
            **kwargs
        )
        return cls(config)
    
    @classmethod
    def create_deepseek_coder(cls, api_key: str = None, **kwargs) -> 'DeepSeekClient':
        """Convenience method to create DeepSeek Coder client."""
        config = LLMConfig(
            model_name="deepseek-coder",
            api_key=api_key,
            **kwargs
        )
        return cls(config) 