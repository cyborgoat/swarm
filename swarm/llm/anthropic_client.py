"""
Anthropic client implementation with streaming and tool calling support.
"""

from typing import Dict, Any, List, Union, Iterator
import os
from .base import BaseLLM, LLMConfig, ModelType


class AnthropicClient(BaseLLM):
    """Anthropic Claude client with streaming and tool calling support."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._model_type = ModelType.STANDARD
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Anthropic client."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package is required. Install with: pip install anthropic")
        
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        self.client = anthropic.Anthropic(
            api_key=api_key,
            base_url=self.config.base_url
        )
    
    @property
    def supports_mcp(self) -> bool:
        """Anthropic supports MCP natively."""
        return True
    
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """Generate response from Anthropic model."""
        if not self.client:
            self._initialize_client()
        
        # Convert messages to Anthropic format
        system_message = None
        formatted_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                formatted_messages.append(msg)
        
        # Prepare parameters
        params = {
            "model": self.config.model_name,
            "messages": formatted_messages,
            "temperature": self.config.temperature,
            "stream": self.config.stream_config.enabled,
            **self.config.extra_params,
            **kwargs
        }
        
        if system_message:
            params["system"] = system_message
        
        if self.config.max_tokens:
            params["max_tokens"] = self.config.max_tokens
        else:
            params["max_tokens"] = 4096  # Anthropic requires max_tokens
        
        try:
            if self.config.stream_config.enabled:
                response = self.client.messages.stream(**params)
                return self._stream_response(response)
            else:
                response = self.client.messages.create(**params)
                return response.content[0].text
                
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")
    
    def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """Generate response with tool calling support."""
        if not self.client:
            self._initialize_client()
        
        # Convert messages to Anthropic format
        system_message = None
        formatted_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                formatted_messages.append(msg)
        
        # Convert tools to Anthropic format
        anthropic_tools = []
        for tool in tools:
            if "function" in tool:
                anthropic_tools.append({
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "input_schema": tool["function"]["parameters"]
                })
        
        params = {
            "model": self.config.model_name,
            "messages": formatted_messages,
            "tools": anthropic_tools,
            "temperature": self.config.temperature,
            "stream": self.config.stream_config.enabled,
            **self.config.extra_params,
            **kwargs
        }
        
        if system_message:
            params["system"] = system_message
        
        if self.config.max_tokens:
            params["max_tokens"] = self.config.max_tokens
        else:
            params["max_tokens"] = 4096
        
        try:
            if self.config.stream_config.enabled:
                response = self.client.messages.stream(**params)
                return self._stream_response_with_tools(response)
            else:
                response = self.client.messages.create(**params)
                
                # Check for tool calls
                tool_calls = []
                content = ""
                
                for content_block in response.content:
                    if content_block.type == "text":
                        content += content_block.text
                    elif content_block.type == "tool_use":
                        tool_calls.append({
                            "id": content_block.id,
                            "function": content_block.name,
                            "arguments": content_block.input
                        })
                
                if tool_calls:
                    return {
                        "content": content,
                        "tool_calls": tool_calls
                    }
                return content
                
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")
    
    def _stream_response(self, response) -> Iterator[str]:
        """Process streaming response."""
        with response as stream:
            for chunk in stream:
                if chunk.type == "content_block_delta" and chunk.delta.type == "text_delta":
                    yield chunk.delta.text
    
    def _stream_response_with_tools(self, response) -> Iterator[Dict[str, Any]]:
        """Process streaming response with tool calls."""
        with response as stream:
            for chunk in stream:
                if chunk.type == "content_block_delta":
                    if chunk.delta.type == "text_delta":
                        yield {"type": "content", "content": chunk.delta.text}
                    elif chunk.delta.type == "input_json_delta":
                        # Tool call input streaming
                        yield {"type": "tool_call_delta", "content": chunk.delta.partial_json}
                elif chunk.type == "content_block_start" and chunk.content_block.type == "tool_use":
                    yield {
                        "type": "tool_call_start",
                        "tool_call": {
                            "id": chunk.content_block.id,
                            "function": chunk.content_block.name
                        }
                    }
    
    def connect_mcp_server(self, server_url: str, tools: List[str] = None):
        """Connect to an MCP server."""
        # Anthropic has native MCP support
        self.config.mcp_config.enabled = True
        self.config.mcp_config.server_url = server_url
        self.config.mcp_config.tools = tools or []
        print(f"MCP server connection configured: {server_url}")
    
    def list_mcp_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools."""
        if not self.config.mcp_config.enabled:
            return []
        
        # Would integrate with Anthropic's MCP implementation
        return [
            {"name": "anthropic_mcp_tool", "description": "Anthropic MCP tool"},
        ]
    
    @classmethod
    def create_claude3_opus(cls, api_key: str = None, **kwargs) -> 'AnthropicClient':
        """Convenience method to create Claude 3 Opus client."""
        config = LLMConfig(
            model_name="claude-3-opus-20240229",
            api_key=api_key,
            **kwargs
        )
        return cls(config)
    
    @classmethod
    def create_claude3_sonnet(cls, api_key: str = None, **kwargs) -> 'AnthropicClient':
        """Convenience method to create Claude 3 Sonnet client."""
        config = LLMConfig(
            model_name="claude-3-sonnet-20240229",
            api_key=api_key,
            **kwargs
        )
        return cls(config)
    
    @classmethod
    def create_claude3_haiku(cls, api_key: str = None, **kwargs) -> 'AnthropicClient':
        """Convenience method to create Claude 3 Haiku client."""
        config = LLMConfig(
            model_name="claude-3-haiku-20240307",
            api_key=api_key,
            **kwargs
        )
        return cls(config) 