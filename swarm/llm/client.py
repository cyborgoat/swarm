"""
LLM client for integrating with various LLM services.
"""

import asyncio
from typing import Any, AsyncGenerator, Callable

import httpx
import ollama
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from swarm.core.config import LLMConfig
from swarm.core.exceptions import LLMConnectionError, LLMError, LLMTimeoutError
from swarm.utils.exception_handler import handle_llm_exceptions


class LLMClient:
    """Client for interacting with LLM services with function calling support."""

    def __init__(self, config: LLMConfig) -> None:
        """
        Initialize LLM client with configuration.

        Args:
            config: LLM configuration
        """
        self.config = config
        self.session = httpx.AsyncClient(
            timeout=120.0,  # Increased timeout for research tasks
            headers={"Content-Type": "application/json", "User-Agent": "Swarm-Agent/1.0"},
        )

        # Add API key if provided
        if hasattr(self.config, "api_key") and self.config.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.config.api_key}"

    @handle_llm_exceptions
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """
        Generate text using the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response
        """
        # Use a synchronous client for sync calls
        with httpx.Client(
            timeout=120.0,
            headers={"Content-Type": "application/json", "User-Agent": "Swarm-Agent/1.0"},
        ) as sync_session:
            if hasattr(self.config, "api_key") and self.config.api_key:
                sync_session.headers["Authorization"] = f"Bearer {self.config.api_key}"
                
            try:
                # Try Ollama API first
                return self._try_ollama_api_sync(prompt, system_prompt, sync_session)
            except LLMError:
                # Re-raise specific LLM errors
                raise
            except Exception as ollama_error:
                try:
                    # Fallback to OpenAI-compatible API
                    return self._try_openai_api_sync(prompt, system_prompt, sync_session)
                except Exception as openai_error:
                    raise LLMConnectionError(
                        f"Both Ollama and OpenAI APIs failed. Ollama: {ollama_error}, OpenAI: {openai_error}",
                        model=getattr(self.config, "model", "unknown"),
                    )

    async def generate_async(self, prompt: str, system_prompt: str | None = None) -> str:
        """
        Async version of generate for compatibility with async analyzers.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response
        """
        return await asyncio.get_event_loop().run_in_executor(None, self.generate, prompt, system_prompt)

    async def generate_streaming(
        self, 
        prompt: str, 
        system_prompt: str | None = None,
        console: Console | None = None,
        title: str = "🤖 AI Processing"
    ) -> str:
        """
        Generate text using streaming with real-time display and final cleanup.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            console: Rich console for display
            title: Title for the streaming panel

        Returns:
            Final generated text response
        """
        if console is None:
            console = Console()

        try:
            # Try streaming from Ollama first
            return await self._try_ollama_streaming(prompt, system_prompt, console, title)
        except LLMError:
            # Re-raise specific LLM errors
            raise
        except Exception as ollama_error:
            try:
                # Fallback to non-streaming
                console.print(f"[yellow]Streaming failed, falling back to standard generation...[/yellow]")
                return await self.generate_async(prompt, system_prompt)
            except Exception as fallback_error:
                raise LLMConnectionError(
                    f"Both streaming and fallback failed. Ollama: {ollama_error}, Fallback: {fallback_error}",
                    model=getattr(self.config, "model", "unknown"),
                )

    async def _try_ollama_streaming(
        self, 
        prompt: str, 
        system_prompt: str | None = None,
        console: Console | None = None,
        title: str = "🤖 AI Processing"
    ) -> str:
        """Try Ollama's streaming API with real-time display."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}"

        payload = {
            "model": getattr(self.config, "model", "llama3.2:latest"),
            "prompt": full_prompt,
            "stream": True,
            "options": {
                "temperature": getattr(self.config, "temperature", 0.7),
                "num_predict": getattr(self.config, "max_tokens", 8192),
            },
        }

        try:
            # Start streaming request
            async with self.session.stream(
                "POST",
                f"{getattr(self.config, 'base_url', 'http://localhost:11434')}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()

                accumulated_text = ""
                display_text = Text()

                # Use Rich Live for real-time updates
                with Live(
                    Panel(display_text, title=title, border_style="cyan"),
                    console=console,
                    refresh_per_second=8,
                    transient=True  # Make transient to not interfere with progress
                ) as live:
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                import json
                                chunk = json.loads(line)
                                if "response" in chunk:
                                    token = chunk["response"]
                                    accumulated_text += token
                                    
                                    # Update display text
                                    display_text = Text(accumulated_text)
                                    live.update(Panel(display_text, title=title, border_style="cyan"))
                                    
                                    # Small delay to make streaming visible
                                    await asyncio.sleep(0.05)
                                
                                # Check if done
                                if chunk.get("done", False):
                                    break
                                    
                            except json.JSONDecodeError:
                                continue

                # Small pause to ensure display is properly finalized
                await asyncio.sleep(0.1)
                
                return accumulated_text.strip()

        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"Ollama streaming timeout: {str(e)}", model=getattr(self.config, "model", "unknown"))
        except httpx.ConnectError as e:
            raise LLMConnectionError(
                f"Ollama streaming connection error: {str(e)}", model=getattr(self.config, "model", "unknown")
            )
        except Exception as e:
            raise LLMError(f"Ollama streaming error: {str(e)}", model=getattr(self.config, "model", "unknown"))

    @handle_llm_exceptions
    def generate_with_functions(
        self,
        prompt: str,
        functions: list[dict[str, Any]],
        system_prompt: str | None = None,
        function_call: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate response with function calling support.

        Args:
            prompt: User prompt
            functions: List of available functions with their schemas
            system_prompt: Optional system prompt
            function_call: Optional specific function to call

        Returns:
            LLM response with potential function call
        """
        try:
            # Use official Ollama package for tool calling
            return self._try_ollama_tool_calling(prompt, functions, system_prompt, function_call)
        except LLMError:
            # Re-raise specific LLM errors
            raise
        except Exception as ollama_error:
            try:
                # Fallback to OpenAI-compatible API with function calling
                return self._try_openai_function_calling(prompt, functions, system_prompt, function_call)
            except Exception as openai_error:
                raise LLMConnectionError(
                    f"Function calling failed. Ollama: {ollama_error}, OpenAI: {openai_error}",
                    model=getattr(self.config, "model", "unknown"),
                )

    def _try_ollama_tool_calling(
        self,
        prompt: str,
        functions: list[dict[str, Any]],
        system_prompt: str | None = None,
        function_call: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Try Ollama's tool calling functionality."""
        # Convert functions to Ollama tools format
        tools = []
        for func in functions:
            tools.append({"type": "function", "function": func})

        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            # Use official ollama package
            response = ollama.chat(
                model=getattr(self.config, "model", "llama3.2:latest"),
                messages=messages,
                tools=tools,
                options={
                    "temperature": getattr(self.config, "temperature", 0.7),
                    "num_predict": getattr(self.config, "max_tokens", 8192),
                },
            )

            message = response.get("message", {})

            # Check if there are tool calls in the response
            if "tool_calls" in message and message["tool_calls"]:
                tool_call = message["tool_calls"][0]  # Take the first tool call
                function_info = tool_call.get("function", {})

                return {
                    "role": "assistant",
                    "content": message.get("content", ""),
                    "function_call": {
                        "name": function_info.get("name"),
                        "arguments": function_info.get("arguments", {}),
                    },
                }
            else:
                # No tool calls, return regular response
                return {"role": "assistant", "content": message.get("content", ""), "function_call": None}

        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg or "timed out" in error_msg:
                raise LLMTimeoutError(
                    f"Ollama tool calling timeout: {str(e)}", model=getattr(self.config, "model", "unknown")
                )
            elif "connection" in error_msg or "connect" in error_msg:
                raise LLMConnectionError(
                    f"Ollama connection error: {str(e)}", model=getattr(self.config, "model", "unknown")
                )
            else:
                raise LLMError(f"Ollama tool calling error: {str(e)}", model=getattr(self.config, "model", "unknown"))

    def _try_ollama_api_sync(self, prompt: str, system_prompt: str | None = None, session: httpx.Client = None) -> str:
        """Try Ollama's native API."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}"

        payload = {
            "model": getattr(self.config, "model", "llama3.2:latest"),
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": getattr(self.config, "temperature", 0.7),
                "num_predict": getattr(self.config, "max_tokens", 8192),
            },
        }

        try:
            response = session.post(
                f"{getattr(self.config, 'base_url', 'http://localhost:11434')}/api/generate", json=payload
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"Ollama API timeout: {str(e)}", model=getattr(self.config, "model", "unknown"))
        except httpx.ConnectError as e:
            raise LLMConnectionError(
                f"Ollama connection error: {str(e)}", model=getattr(self.config, "model", "unknown")
            )
        except Exception as e:
            raise LLMError(f"Ollama API error: {str(e)}", model=getattr(self.config, "model", "unknown"))

    def _try_openai_api_sync(self, prompt: str, system_prompt: str | None = None, session: httpx.Client = None) -> str:
        """Try OpenAI-compatible API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": getattr(self.config, "model", "llama3.2:latest"),
            "messages": messages,
            "temperature": getattr(self.config, "temperature", 0.7),
            "max_tokens": getattr(self.config, "max_tokens", 8192),
        }

        try:
            response = session.post(
                f"{getattr(self.config, 'base_url', 'http://localhost:11434')}/v1/chat/completions", json=payload
            )
            response.raise_for_status()

            result = response.json()
            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"]
            else:
                raise LLMError("No response generated from LLM", model=getattr(self.config, "model", "unknown"))
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"OpenAI API timeout: {str(e)}", model=getattr(self.config, "model", "unknown"))
        except httpx.ConnectError as e:
            raise LLMConnectionError(
                f"OpenAI connection error: {str(e)}", model=getattr(self.config, "model", "unknown")
            )
        except Exception as e:
            raise LLMError(f"OpenAI API error: {str(e)}", model=getattr(self.config, "model", "unknown"))

    def _try_openai_function_calling(
        self,
        prompt: str,
        functions: list[dict[str, Any]],
        system_prompt: str | None = None,
        function_call: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Try OpenAI-compatible API with function calling."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": getattr(self.config, "model", "llama3.2:latest"),
            "messages": messages,
            "functions": functions,
            "temperature": getattr(self.config, "temperature", 0.7),
            "max_tokens": getattr(self.config, "max_tokens", 8192),
        }

        if function_call:
            payload["function_call"] = function_call

        response = self.session.post(
            f"{getattr(self.config, 'base_url', 'http://localhost:11434')}/v1/chat/completions", json=payload
        )
        response.raise_for_status()

        result = response.json()
        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]
        else:
            raise LLMError("No response generated from LLM")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def cleanup(self) -> None:
        """Clean up HTTP session."""
        if hasattr(self, "session"):
            await self.session.aclose()

    def __del__(self) -> None:
        """Clean up HTTP session."""
        if hasattr(self, "session"):
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.session.aclose())
                else:
                    loop.run_until_complete(self.session.aclose())
            except Exception:
                # Ignore cleanup errors during shutdown
                pass
