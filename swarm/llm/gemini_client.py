"""
Gemini client implementation supporting Gemini 1.5 and Gemini 2 models.
Supports multimodal capabilities and streaming.
"""

from typing import Dict, Any, List, Union, Iterator
import os
from .base import BaseLLM, LLMConfig, ModelType


class GeminiClient(BaseLLM):
    """Gemini client with multimodal support and streaming."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._model_type = ModelType.MULTIMODAL
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Gemini client."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai package is required. Install with: pip install google-generativeai")
        
        api_key = self.config.api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key is required (GOOGLE_API_KEY or GEMINI_API_KEY)")
        
        genai.configure(api_key=api_key)
        
        # Configure generation settings
        self.generation_config = genai.types.GenerationConfig(
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
            **self.config.extra_params
        )
        
        # Initialize the model
        self.client = genai.GenerativeModel(
            model_name=self.config.model_name,
            generation_config=self.generation_config
        )
        
        # Store the genai module for later use
        self.genai = genai
    
    @property
    def supports_mcp(self) -> bool:
        """Gemini may support MCP through extensions."""
        return False  # Not natively supported yet
    
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """Generate response from Gemini model."""
        if not self.client:
            self._initialize_client()
        
        # Convert messages to Gemini format
        gemini_messages = self._convert_messages(messages)
        
        try:
            if self.config.stream_config.enabled:
                response = self.client.generate_content(
                    gemini_messages,
                    stream=True,
                    **kwargs
                )
                return self._stream_response(response)
            else:
                response = self.client.generate_content(
                    gemini_messages,
                    **kwargs
                )
                return response.text
                
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")
    
    def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """Generate response with tool calling support."""
        if not self.client:
            self._initialize_client()
        
        # Convert tools to Gemini format
        gemini_tools = self._convert_tools(tools)
        gemini_messages = self._convert_messages(messages)
        
        try:
            if self.config.stream_config.enabled:
                response = self.client.generate_content(
                    gemini_messages,
                    tools=gemini_tools,
                    stream=True,
                    **kwargs
                )
                return self._stream_response_with_tools(response)
            else:
                response = self.client.generate_content(
                    gemini_messages,
                    tools=gemini_tools,
                    **kwargs
                )
                
                # Check for function calls
                if response.candidates[0].content.parts:
                    tool_calls = []
                    content = ""
                    
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call'):
                            tool_calls.append({
                                "function": part.function_call.name,
                                "arguments": dict(part.function_call.args)
                            })
                        else:
                            content += part.text
                    
                    if tool_calls:
                        return {
                            "content": content,
                            "tool_calls": tool_calls
                        }
                
                return response.text
                
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")
    
    def generate_with_multimodal(
        self,
        messages: List[Dict[str, Any]],  # Can include images, videos, etc.
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """Generate response with multimodal input (text, images, videos)."""
        if not self.client:
            self._initialize_client()
        
        # Convert multimodal messages
        gemini_content = self._convert_multimodal_messages(messages)
        
        try:
            if self.config.stream_config.enabled:
                response = self.client.generate_content(
                    gemini_content,
                    stream=True,
                    **kwargs
                )
                return self._stream_response(response)
            else:
                response = self.client.generate_content(
                    gemini_content,
                    **kwargs
                )
                return response.text
                
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert OpenAI-style messages to Gemini format."""
        gemini_messages = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                # Gemini doesn't have system messages, prepend to first user message
                if gemini_messages and gemini_messages[0]["role"] == "user":
                    gemini_messages[0]["parts"] = [f"System: {content}\n\nUser: {gemini_messages[0]['parts'][0]}"]
                else:
                    gemini_messages.insert(0, {
                        "role": "user",
                        "parts": [f"System: {content}"]
                    })
            elif role == "user":
                gemini_messages.append({
                    "role": "user",
                    "parts": [content]
                })
            elif role == "assistant":
                gemini_messages.append({
                    "role": "model",
                    "parts": [content]
                })
        
        return gemini_messages
    
    def _convert_multimodal_messages(self, messages: List[Dict[str, Any]]) -> List[Any]:
        """Convert multimodal messages to Gemini format."""
        gemini_content = []
        
        for msg in messages:
            if msg["role"] == "user":
                if isinstance(msg["content"], list):
                    # Multimodal message
                    parts = []
                    for content_part in msg["content"]:
                        if content_part["type"] == "text":
                            parts.append(content_part["text"])
                        elif content_part["type"] == "image_url":
                            # Handle image URL or base64
                            image_data = content_part["image_url"]["url"]
                            if image_data.startswith("data:"):
                                # Base64 image
                                import base64
                                import io
                                from PIL import Image
                                
                                header, data = image_data.split(",", 1)
                                image_bytes = base64.b64decode(data)
                                image = Image.open(io.BytesIO(image_bytes))
                                parts.append(image)
                            else:
                                # URL - would need to download
                                parts.append(f"[Image URL: {image_data}]")
                    
                    gemini_content.extend(parts)
                else:
                    gemini_content.append(msg["content"])
        
        return gemini_content
    
    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Any]:
        """Convert OpenAI-style tools to Gemini format."""
        gemini_tools = []
        
        for tool in tools:
            if "function" in tool:
                func = tool["function"]
                gemini_tools.append(
                    self.genai.types.FunctionDeclaration(
                        name=func["name"],
                        description=func["description"],
                        parameters=func["parameters"]
                    )
                )
        
        return [self.genai.types.Tool(function_declarations=gemini_tools)]
    
    def _stream_response(self, response) -> Iterator[str]:
        """Process streaming response."""
        for chunk in response:
            if chunk.text:
                yield chunk.text
    
    def _stream_response_with_tools(self, response) -> Iterator[Dict[str, Any]]:
        """Process streaming response with tool calls."""
        for chunk in response:
            if chunk.candidates[0].content.parts:
                for part in chunk.candidates[0].content.parts:
                    if hasattr(part, 'function_call'):
                        yield {
                            "type": "tool_call",
                            "tool_call": {
                                "function": part.function_call.name,
                                "arguments": dict(part.function_call.args)
                            }
                        }
                    elif part.text:
                        yield {"type": "content", "content": part.text}
    
    @classmethod
    def create_gemini_15_pro(cls, api_key: str = None, **kwargs) -> 'GeminiClient':
        """Convenience method to create Gemini 1.5 Pro client."""
        config = LLMConfig(
            model_name="gemini-1.5-pro",
            api_key=api_key,
            **kwargs
        )
        return cls(config)
    
    @classmethod
    def create_gemini_15_flash(cls, api_key: str = None, **kwargs) -> 'GeminiClient':
        """Convenience method to create Gemini 1.5 Flash client."""
        config = LLMConfig(
            model_name="gemini-1.5-flash",
            api_key=api_key,
            **kwargs
        )
        return cls(config)
    
    @classmethod
    def create_gemini_2_flash_exp(cls, api_key: str = None, **kwargs) -> 'GeminiClient':
        """Convenience method to create Gemini 2.0 Flash Experimental client."""
        config = LLMConfig(
            model_name="gemini-2.0-flash-exp",
            api_key=api_key,
            **kwargs
        )
        return cls(config)
    
    @classmethod
    def create_gemini_pro_vision(cls, api_key: str = None, **kwargs) -> 'GeminiClient':
        """Convenience method to create Gemini Pro Vision client."""
        config = LLMConfig(
            model_name="gemini-pro-vision",
            api_key=api_key,
            **kwargs
        )
        return cls(config) 