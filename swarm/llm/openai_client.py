"""
OpenAI client implementation with streaming and tool calling support.
"""

from typing import Dict, Any, List, Union, Iterator
import os
from .base import BaseLLM, LLMConfig, ModelType


class OpenAIClient(BaseLLM):
    """OpenAI client with streaming and tool calling support."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._model_type = ModelType.STANDARD
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the OpenAI client."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package is required. Install with: pip install openai")
        
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        base_url = self.config.base_url or "https://api.openai.com/v1"
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    @property
    def supports_mcp(self) -> bool:
        """OpenAI supports MCP through compatible libraries."""
        return True
    
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """Generate response from OpenAI model."""
        if not self.client:
            self._initialize_client()
        
        # Prepare parameters
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
            raise RuntimeError(f"OpenAI API error: {str(e)}")
    
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
            raise RuntimeError(f"OpenAI API error: {str(e)}")
    
    def _stream_response(self, response) -> Iterator[str]:
        """Process streaming response."""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    def _stream_response_with_tools(self, response) -> Iterator[Dict[str, Any]]:
        """Process streaming response with tool calls."""
        tool_calls_buffer = {}
        
        for chunk in response:
            delta = chunk.choices[0].delta
            
            if delta.content is not None:
                yield {"type": "content", "content": delta.content}
            
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
    
    def connect_mcp_server(self, server_url: str, tools: List[str] = None):
        """Connect to an MCP server (placeholder for MCP implementation)."""
        # This would require MCP client implementation
        self.config.mcp_config.enabled = True
        self.config.mcp_config.server_url = server_url
        self.config.mcp_config.tools = tools or []
        print(f"MCP server connection configured: {server_url}")
    
    def list_mcp_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools."""
        if not self.config.mcp_config.enabled:
            return []
        
        # Placeholder - would integrate with actual MCP client
        return [
            {"name": "example_tool", "description": "Example MCP tool"},
        ]
    
    @classmethod
    def create_gpt4(cls, api_key: str = None, **kwargs) -> 'OpenAIClient':
        """Convenience method to create GPT-4 client."""
        config = LLMConfig(
            model_name="gpt-4",
            api_key=api_key,
            **kwargs
        )
        return cls(config)
    
    @classmethod
    def create_gpt35(cls, api_key: str = None, **kwargs) -> 'OpenAIClient':
        """Convenience method to create GPT-3.5 client."""
        config = LLMConfig(
            model_name="gpt-3.5-turbo",
            api_key=api_key,
            **kwargs
        )
        return cls(config) 