"""
AI-Powered Interactive Mode for Swarm.

This module provides an intelligent interactive research assistant that uses
LLM function calling to control browser automation through MCP tools with proper context management.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown
import os
import subprocess
import time
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
import sys

from swarm.core.config import Config
from swarm.llm.client import LLMClient
from swarm.mcp_tools.server import SwarmMCPServer
from fastmcp import Client
from swarm.web.browser import Browser
from swarm.web.search import WebSearch

console = Console()
logger = logging.getLogger(__name__)


class AIResearchAssistant:
    """AI-powered research assistant with LLM-driven browser automation and context management."""
    
    def __init__(self, config: Config, use_mcp: bool = True, headless: bool = False):
        """Initialize AI Research Assistant."""
        self.config = config
        self.use_mcp = use_mcp
        self.headless = headless
        
        # Initialize LLM client
        self.llm_client = LLMClient(config.llm)
        
        if use_mcp:
            # Initialize MCP server and client
            self.mcp_server = SwarmMCPServer(config)
            self.mcp_client = Client(self.mcp_server.get_mcp_instance())
            
            # Auto-start browser session (will be done in async method)
            console.print("[cyan]🚀 Starting browser session automatically...[/cyan]")
            console.print("[green]✅ Browser session will start when first needed![/green]")
        else:
            # Direct browser control (legacy mode)
            self.browser = Browser(config.browser)
            self.search = WebSearch(config.search)
        
        # Context management
        self.conversation_history = []
        self.current_context = {
            "current_url": None,
            "page_title": None,
            "last_search_results": None,
            "browser_active": False
        }
        
        # Available MCP tools (will be populated dynamically)
        self.available_functions = []
    
    async def _ensure_browser_started(self) -> bool:
        """Ensure browser session is started (async helper)."""
        if not self.use_mcp:
            return True
            
        try:
            async with self.mcp_client:
                result = await self.mcp_client.call_tool("start_browser_session", {"headless": self.headless})
                if isinstance(result, list) and len(result) > 0:
                    result_content = result[0]
                    if hasattr(result_content, 'text'):
                        try:
                            result_data = json.loads(result_content.text)
                        except json.JSONDecodeError:
                            result_data = {"status": "error"}
                    else:
                        result_data = {"status": "error"}
                else:
                    result_data = result if isinstance(result, dict) else {"status": "error"}
                
                return result_data.get("status") in ["success", "already_active"]
        except Exception as e:
            logger.error(f"Failed to start browser session: {e}")
            return False
    
    async def _update_context(self):
        """Update the current context with browser state."""
        if not self.mcp_client:
            return
        
        try:
            async with self.mcp_client:
                # Get current session status
                status = await self.mcp_client.call_tool("get_session_status")
                if status and len(status) > 0:
                    status_data = json.loads(status[0].text) if hasattr(status[0], 'text') else {}
                    self.current_context.update({
                        "browser_active": status_data.get("active", False),
                        "current_url": status_data.get("current_url"),
                        "page_title": status_data.get("title")
                    })
        except Exception as e:
            logger.error(f"Failed to update context: {e}")
    
    async def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from the MCP server dynamically."""
        if not self.mcp_client:
            return []
        
        try:
            async with self.mcp_client:
                tools = await self.mcp_client.list_tools()
                
                # Convert MCP tools to function calling format
                function_definitions = []
                for tool in tools:
                    func_def = {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                    
                    # Parse input schema if available
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        if hasattr(tool.inputSchema, 'properties'):
                            func_def["parameters"]["properties"] = tool.inputSchema.properties
                        if hasattr(tool.inputSchema, 'required'):
                            func_def["parameters"]["required"] = tool.inputSchema.required
                    
                    function_definitions.append(func_def)
                
                return function_definitions
        except Exception as e:
            logger.error(f"Failed to get tools: {e}")
            return []
    
    def _build_context_prompt(self) -> str:
        """Build a context-aware system prompt."""
        context_info = []
        
        if self.current_context["browser_active"]:
            context_info.append("✅ Browser session is active")
            if self.current_context["current_url"]:
                context_info.append(f"📍 Current page: {self.current_context['current_url']}")
            if self.current_context["page_title"]:
                context_info.append(f"📄 Page title: {self.current_context['page_title']}")
        else:
            context_info.append("❌ No active browser session")
        
        if self.current_context["last_search_results"]:
            context_info.append(f"🔍 Last search found {len(self.current_context['last_search_results'])} results")
        
        context_str = "\n".join(context_info) if context_info else "No current context"
        
        # Enhanced system prompt for better tool vs chat distinction
        system_prompt = f"""You are an AI research assistant with browser automation capabilities.

CRITICAL INSTRUCTIONS:
1. For CASUAL CONVERSATION (greetings, questions about yourself), respond normally WITHOUT calling any tools
2. For ANY ACTION REQUEST, you MUST call the appropriate tool:

ALWAYS USE TOOLS FOR:
- "search for X" → use search_web
- "go to X", "browse X", "navigate to X" → use navigate_to_url  
- "what's on this page", "summarize this page", "get page content" → use extract_page_content
- "take a screenshot", "capture the page" → use take_screenshot (if available)
- "click X", "click on X" → use click_element_by_text
- "fill X with Y", "enter Y in X" → use fill_input_by_label
- "what's the status", "browser status" → use get_session_status

NEVER give text responses for action requests - ALWAYS use the appropriate tool.

Current context: {context_str}

Remember: If the user asks for ANY action, use tools. Only chat normally for greetings and questions about yourself."""
        
        return system_prompt

    def create_system_prompt(self, context_summary: str) -> str:
        """Create system prompt with context awareness."""
        return f"""You are an AI research assistant with browser automation capabilities.

CRITICAL INSTRUCTIONS:
1. For CASUAL CONVERSATION (greetings, questions about yourself), respond normally WITHOUT calling any tools
2. For ANY ACTION REQUEST, you MUST call the appropriate tool:

ALWAYS USE TOOLS FOR:
- "search for X" → use search_web
- "go to X", "browse X", "navigate to X" → use navigate_to_url  
- "what's on this page", "summarize this page", "get page content" → use extract_page_content
- "take a screenshot", "capture the page" → use take_screenshot (if available)
- "click X", "click on X" → use click_element_by_text
- "fill X with Y", "enter Y in X" → use fill_input_by_label
- "what's the status", "browser status" → use get_session_status

NEVER give text responses for action requests - ALWAYS use the appropriate tool.

Current context: {context_summary}

Remember: If the user asks for ANY action, use tools. Only chat normally for greetings and questions about yourself."""

    async def process_user_query(self, user_input: str) -> str:
        """Process user query with LLM and potentially execute tools."""
        try:
            # Check if this is casual conversation that doesn't need tools
            # Be more specific to avoid catching legitimate tool requests
            casual_patterns = [
                "who are you", "what are you", "hello", "hi there", "hey there", 
                "how are you", "what's up", "good morning", "good afternoon", "good evening",
                "thanks", "thank you", "bye", "goodbye", "help me understand", "explain"
            ]
            
            user_lower = user_input.lower().strip()
            
            # Only treat as casual if it's an exact match or very close match
            is_casual = False
            for pattern in casual_patterns:
                if user_lower == pattern or user_lower.startswith(pattern + " ") or user_lower.endswith(" " + pattern):
                    is_casual = True
                    break
            
            # Special case for "help" - only casual if it's just "help" alone
            if user_lower == "help":
                is_casual = True
            
            if is_casual:
                # Handle casual conversation without tools
                if "who are you" in user_lower or "what are you" in user_lower:
                    return "I'm an AI research assistant with browser automation capabilities. I can help you search the web, navigate to websites, extract content from pages, and perform various browser actions. Just ask me to search for something or browse to a website!"
                elif any(greeting in user_lower for greeting in ["hello", "hi", "hey"]):
                    return "Hello! I'm your AI research assistant. I can help you with web browsing, searching, and automation tasks. What would you like me to do?"
                elif "how are you" in user_lower:
                    return "I'm doing great and ready to help! I can browse websites, search for information, and automate web tasks for you. What can I assist you with?"
                elif user_lower == "help":
                    return """I'm an AI research assistant with browser automation capabilities. Here's what I can do:

🔍 **Search**: "search for gaming mice" or "find information about Python"
🌐 **Navigate**: "go to github.com" or "browse stackoverflow.com"  
📄 **Extract**: "what's on this page" or "get page content"
🖱️ **Interact**: "click the login button" or "fill email with john@example.com"
📸 **Screenshot**: "take a screenshot" or "capture the page"

Just tell me what you'd like to do in natural language!"""
                elif any(thanks in user_lower for thanks in ["thanks", "thank you"]):
                    return "You're welcome! Let me know if you need help with anything else."
                elif any(bye in user_lower for bye in ["bye", "goodbye"]):
                    return "Goodbye! Feel free to come back anytime you need help with web research or automation."
                else:
                    return "I'm here to help! You can ask me to search for information, browse websites, or perform web automation tasks."
            
            # For non-casual queries, ensure browser is started first
            if self.use_mcp:
                browser_ready = await self._ensure_browser_started()
                if not browser_ready:
                    return "❌ Failed to start browser session. Please try again or check the system status."
            
            # For non-casual queries, proceed with LLM + tools
            context_summary = await self.get_context_summary()
            system_prompt = self.create_system_prompt(context_summary)
            
            # Get available tools
            tools = await self.get_available_tools()
            
            # Call LLM with function calling
            response = self.llm_client.generate_with_functions(
                prompt=user_input,
                functions=tools,
                system_prompt=system_prompt
            )
            
            print(f"DEBUG: LLM response type: {type(response)}")
            print(f"DEBUG: Has function_call: {response.get('function_call') is not None}")
            print(f"DEBUG: Response content: {response.get('content', '')[:100]}...")
            
            # Check if LLM wants to call a function
            function_call = response.get('function_call')
            if function_call and function_call.get('name'):
                function_name = function_call['name']
                arguments = function_call.get('arguments', {})
                
                # Clean up arguments - ensure proper types and defaults
                if function_name == "search_web":
                    # Ensure max_results has a proper default
                    if 'max_results' not in arguments or arguments['max_results'] is None:
                        arguments['max_results'] = 10
                    elif not isinstance(arguments['max_results'], int):
                        try:
                            arguments['max_results'] = int(arguments['max_results'])
                        except (ValueError, TypeError):
                            arguments['max_results'] = 10
                
                elif function_name == "extract_page_content":
                    # Ensure max_length has a proper default
                    if 'max_length' not in arguments or arguments['max_length'] is None:
                        arguments['max_length'] = 20000
                    elif not isinstance(arguments['max_length'], int):
                        try:
                            arguments['max_length'] = int(arguments['max_length'])
                        except (ValueError, TypeError):
                            arguments['max_length'] = 20000
                
                print(f"🔧 LLM CHOSE TOOL: {function_name}")
                print(f"   Parameters: {arguments}")
                
                # Execute the tool
                async with self.mcp_client:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn(f"🔧 Executing {function_name}..."),
                        console=console,
                        transient=True
                    ) as progress:
                        progress.add_task("executing", total=None)
                        
                        try:
                            result = await self.mcp_client.call_tool(function_name, arguments)
                            console.print(f"✅ TOOL SUCCESS: {function_name}")
                            
                            # Handle different result formats from MCP client
                            if isinstance(result, list) and len(result) > 0:
                                # Extract content from MCP response
                                result_content = result[0]
                                if hasattr(result_content, 'text'):
                                    try:
                                        result_data = json.loads(result_content.text)
                                    except json.JSONDecodeError:
                                        result_data = {"status": "success", "content": result_content.text}
                                else:
                                    result_data = {"status": "success", "content": str(result_content)}
                            else:
                                result_data = result if isinstance(result, dict) else {"status": "success", "content": str(result)}
                            
                            # Pass the tool result back to LLM for human-readable interpretation
                            interpretation_prompt = f"""The user asked: "{user_input}"

I executed the tool '{function_name}' with parameters: {arguments}

Tool result: {json.dumps(result_data, indent=2)}

Please provide a clear, human-readable response to the user based on this result. Be specific and helpful."""

                            # Get LLM interpretation of the result
                            interpretation_response = self.llm_client.generate_with_functions(
                                prompt=interpretation_prompt,
                                functions=[],  # No tools for interpretation
                                system_prompt="You are an AI assistant interpreting tool results for users. Provide clear, helpful responses based on the tool execution results. Do not call any tools - just interpret and explain the results."
                            )
                            
                            interpreted_result = interpretation_response.get('content', 'Tool executed successfully.')
                            
                            # Also show a visual summary based on function type
                            if function_name == "search_web":
                                # Handle different possible result structures
                                search_results = None
                                results = []
                                
                                # Try to extract results from different possible structures
                                if isinstance(result_data, dict):
                                    # Check if results are directly in result_data
                                    if 'results' in result_data:
                                        results = result_data['results']
                                    # Check if results are nested in content
                                    elif 'content' in result_data:
                                        content = result_data['content']
                                        if isinstance(content, dict) and 'results' in content:
                                            results = content['results']
                                        elif isinstance(content, list):
                                            results = content
                                    # Check if result_data itself is a list
                                    elif isinstance(result_data.get('content'), str):
                                        try:
                                            # Try to parse content as JSON
                                            parsed_content = json.loads(result_data['content'])
                                            if isinstance(parsed_content, dict) and 'results' in parsed_content:
                                                results = parsed_content['results']
                                        except:
                                            pass
                                
                                if results and len(results) > 0:
                                    results_count = len(results)
                                    
                                    # Display search results in detail
                                    console.print(Panel.fit(
                                        f"🔍 Found {results_count} search results for: {arguments.get('query', 'N/A')}",
                                        title="🤖 Search Results",
                                        border_style="green"
                                    ))
                                    
                                    # Show top results with better formatting
                                    for i, result_item in enumerate(results[:5], 1):
                                        if isinstance(result_item, dict):
                                            title = result_item.get('title', 'No title')
                                            url = result_item.get('url', 'No URL')
                                            description = result_item.get('description', '')
                                            
                                            console.print(f"\n[bold cyan]{i}. {title}[/bold cyan]")
                                            console.print(f"   [blue]🔗 {url}[/blue]")
                                            if description and description != 'No description':
                                                # Limit description length and clean it up
                                                clean_desc = description.strip()[:200]
                                                if len(description) > 200:
                                                    clean_desc += "..."
                                                console.print(f"   [dim]{clean_desc}[/dim]")
                                        else:
                                            # Handle case where result_item is not a dict
                                            console.print(f"\n[bold cyan]{i}. {str(result_item)}[/bold cyan]")
                                    
                                    if results_count > 5:
                                        console.print(f"\n[dim]... and {results_count - 5} more results[/dim]")
                                else:
                                    # No results found or couldn't parse results
                                    console.print(Panel.fit(
                                        f"No search results found for: {arguments.get('query', 'N/A')}\n"
                                        f"Raw result: {str(result_data)[:200]}...",
                                        title="🤖 Search Results",
                                        border_style="yellow"
                                    ))
                            
                            elif function_name == "navigate_to_url":
                                url = result_data.get('url', arguments.get('url', 'Unknown'))
                                title = result_data.get('title', 'Unknown')
                                
                                console.print(Panel.fit(
                                    f"🌐 Navigated to: **{title}**\n"
                                    f"URL: {url}",
                                    title="🤖 Navigation Complete",
                                    border_style="green"
                                ))
                            
                            elif function_name == "extract_page_content":
                                content = result_data.get('content', '')
                                length = result_data.get('length', 0)
                                
                                if content:
                                    # Show a preview of the content
                                    preview = content[:300] + "..." if len(content) > 300 else content
                                    console.print(Panel.fit(
                                        f"📄 Extracted {length} characters:\n\n{preview}",
                                        title="🤖 Page Content Preview",
                                        border_style="green"
                                    ))
                            
                            elif function_name == "get_session_status":
                                status_info = result_data if isinstance(result_data, dict) else {}
                                active = status_info.get('active', False)
                                current_url = status_info.get('current_url', 'None')
                                
                                console.print(Panel.fit(
                                    f"🌐 Browser Status: {'✅ Active' if active else '❌ Inactive'}\n"
                                    f"Current URL: {current_url}",
                                    title="🤖 Session Status",
                                    border_style="green"
                                ))
                            
                            elif function_name == "click_element_by_text":
                                text = arguments.get('text', 'Unknown')
                                success = result_data.get('status') == 'success'
                                message = result_data.get('message', 'Click completed')
                                
                                console.print(Panel.fit(
                                    f"🖱️ {'✅ Successfully' if success else '❌ Failed to'} clicked element:\n"
                                    f"Text: '{text}'\n"
                                    f"Result: {message}",
                                    title="🤖 Click Action",
                                    border_style="green" if success else "red"
                                ))
                            
                            elif function_name == "fill_input_by_label":
                                label = arguments.get('label', 'Unknown')
                                value = arguments.get('value', 'Unknown')
                                success = result_data.get('status') == 'success'
                                message = result_data.get('message', 'Fill completed')
                                
                                console.print(Panel.fit(
                                    f"📝 {'✅ Successfully' if success else '❌ Failed to'} filled input field:\n"
                                    f"Field: '{label}'\n"
                                    f"Value: '{value}'\n"
                                    f"Result: {message}",
                                    title="🤖 Fill Action",
                                    border_style="green" if success else "red"
                                ))
                            
                            elif function_name == "get_page_elements":
                                elements = result_data if isinstance(result_data, dict) else {}
                                buttons = elements.get('buttons', [])
                                inputs = elements.get('inputs', [])
                                links = elements.get('links', [])
                                selects = elements.get('selects', [])
                                total = elements.get('total_count', 0)
                                
                                element_summary = []
                                if buttons:
                                    element_summary.append(f"🔘 {len(buttons)} buttons")
                                if inputs:
                                    element_summary.append(f"📝 {len(inputs)} inputs")
                                if links:
                                    element_summary.append(f"🔗 {len(links)} links")
                                if selects:
                                    element_summary.append(f"📋 {len(selects)} dropdowns")
                                
                                console.print(Panel.fit(
                                    f"🔍 Found {total} interactive elements:\n" + 
                                    ", ".join(element_summary),
                                    title="🤖 Page Elements",
                                    border_style="green"
                                ))
                                
                                # Show some examples of each type
                                if buttons:
                                    console.print(f"\n[bold]Available Buttons:[/bold] {', '.join(buttons[:5])}")
                                    if len(buttons) > 5:
                                        console.print(f"[dim]... and {len(buttons) - 5} more[/dim]")
                                
                                if inputs:
                                    console.print(f"\n[bold]Available Input Fields:[/bold] {', '.join(inputs[:5])}")
                                    if len(inputs) > 5:
                                        console.print(f"[dim]... and {len(inputs) - 5} more[/dim]")
                            
                            elif function_name == "take_screenshot":
                                path = result_data.get('path', 'Unknown')
                                success = result_data.get('status') == 'success'
                                message = result_data.get('message', 'Screenshot completed')
                                
                                console.print(Panel.fit(
                                    f"📸 {'✅ Successfully' if success else '❌ Failed to'} take screenshot:\n"
                                    f"Path: {path}\n"
                                    f"Result: {message}",
                                    title="🤖 Screenshot",
                                    border_style="green" if success else "red"
                                ))
                            
                            else:
                                # Generic tool result
                                success = result_data.get('status') == 'success'
                                message = result_data.get('message', 'Tool executed successfully')
                                console.print(Panel.fit(
                                    f"{'✅' if success else '❌'} {function_name} completed:\n{message}",
                                    title="🤖 Tool Result",
                                    border_style="green" if success else "red"
                                ))
                            
                            # Return the LLM's interpretation
                            return interpreted_result
                            
                        except Exception as e:
                            console.print(f"❌ TOOL EXECUTION ERROR: {function_name}")
                            console.print(f"   Error: {str(e)}")
                            console.print(Panel.fit(
                                f"Failed to execute {function_name}: {str(e)}",
                                title="🤖 AI Assistant",
                                border_style="red"
                            ))
                            return f"❌ Failed to execute {function_name}: {str(e)}"
            
            else:
                # No function call, but this might be an issue - let's be more explicit
                content = response.get('content', '')
                if content:
                    console.print("⚠️ LLM provided text response instead of using tools:")
                    console.print(f"Response: {content}")
                    console.print("\n💡 Try being more specific about what action you want me to take.")
                    return f"I understood your request but didn't use any tools. {content}"
                else:
                    return "I'm ready to help! Please tell me what specific action you'd like me to take (search, navigate, extract content, etc.)"
                
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            print(f"❌ Unexpected error: {e}")
            import traceback
            print(f"DEBUG: {traceback.format_exc()}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def run_interactive_loop(self) -> None:
        """Run the main interactive loop."""
        console.print(Panel.fit(
            "[bold green]🐝 AI Research Assistant[/bold green]\n"
            "[dim]Powered by LLM + Browser Automation with Context Awareness[/dim]\n\n"
            "[cyan]Examples:[/cyan]\n"
            "• 'Search for Python web scraping tutorials'\n"
            "• 'Browse github.com'\n"
            "• 'What is this page about?'\n"
            "• 'Click the login button'\n"
            "• 'Fill email with john@example.com'\n\n"
            "[dim]Type 'help' for commands, 'quit' to exit[/dim]",
            border_style="green"
        ))
        
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in an event loop, create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._async_interactive_loop())
                future.result()
        except RuntimeError:
            # No event loop running, we can use asyncio.run
            asyncio.run(self._async_interactive_loop())
    
    async def _async_interactive_loop(self) -> None:
        """Async interactive loop implementation."""
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]🐝 What would you like me to do?[/bold cyan]").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    if self.mcp_server and self.mcp_server._session_active:
                        console.print("[yellow]🔄 Closing browser session...[/yellow]")
                        self.mcp_server.close_session()
                    console.print("[green]👋 Goodbye![/green]")
                    break
                
                elif user_input.lower() in ['help', 'h']:
                    self._show_help()
                    continue
                
                elif user_input.lower() in ['status', 'info']:
                    await self._show_status()
                    continue
                
                elif user_input.lower() in ['clear', 'cls']:
                    console.clear()
                    continue
                
                # Process the query with AI
                console.print()
                response = await self.process_user_query(user_input)
                
                # Display the response
                console.print(Panel(
                    Markdown(response),
                    title="🤖 AI Assistant",
                    border_style="blue"
                ))
                
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠️ Interrupted by user[/yellow]")
                if Confirm.ask("Do you want to quit?"):
                    if self.mcp_server and self.mcp_server._session_active:
                        console.print("[yellow]🔄 Closing browser session...[/yellow]")
                        self.mcp_server.close_session()
                    break
            except Exception as e:
                console.print(f"[red]❌ Unexpected error: {str(e)}[/red]")
                import traceback
                console.print(f"[dim]DEBUG: {traceback.format_exc()}[/dim]")
    
    def _show_help(self) -> None:
        """Show help information."""
        help_text = """
[bold cyan]🐝 AI Research Assistant Commands[/bold cyan]

[bold green]Natural Language Examples:[/bold green]
• "Search for Python tutorials" - Search the web
• "Browse github.com" - Navigate to a website
• "What is this page about?" - Analyze current page
• "Click the login button" - Click elements
• "Fill email with john@example.com" - Fill forms
• "Take a screenshot" - Capture current page

[bold yellow]Special Commands:[/bold yellow]
• help, h - Show this help
• status, info - Show current session status and context
• clear, cls - Clear the screen
• quit, exit, q - Exit the assistant

[bold blue]Features:[/bold blue]
• 🤖 AI-powered query understanding with context awareness
• 🌐 Visible browser automation
• 🔍 Web search integration
• 📄 Content extraction and analysis
• 🎯 Smart element interaction
• 📸 Screenshot capabilities
• 🧠 Context-aware responses based on current browser state

The AI automatically knows your current browser state and will suggest appropriate actions!
        """
        console.print(Panel(help_text, border_style="cyan"))
    
    async def _show_status(self) -> None:
        """Show current session status and context."""
        if not self.mcp_server:
            console.print("[red]❌ MCP server not available[/red]")
            return
        
        # Update context
        await self._update_context()
        
        table = Table(title="🔍 Session Status & Context")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Browser Active", "✅ Yes" if self.current_context["browser_active"] else "❌ No")
        table.add_row("Current URL", self.current_context.get("current_url", "None"))
        table.add_row("Page Title", self.current_context.get("page_title", "None"))
        table.add_row("Available Tools", str(len(self.available_functions)))
        table.add_row("LLM Model", self.config.llm.model)
        table.add_row("Headless Mode", "❌ No (Visible)" if not self.headless else "✅ Yes")
        
        if self.current_context["last_search_results"]:
            table.add_row("Last Search Results", f"{len(self.current_context['last_search_results'])} results")
        
        console.print(table)

    async def get_context_summary(self) -> str:
        """Get a summary of the current context."""
        try:
            # Get session status through MCP
            async with self.mcp_client:
                result = await self.mcp_client.call_tool("get_session_status", {})
                if isinstance(result, list) and len(result) > 0:
                    result_content = result[0]
                    if hasattr(result_content, 'text'):
                        try:
                            status_data = json.loads(result_content.text)
                        except json.JSONDecodeError:
                            status_data = {"active": False}
                    else:
                        status_data = {"active": False}
                else:
                    status_data = {"active": False}
                
                browser_active = status_data.get("active", False)
                current_url = status_data.get("current_url", "None")
                
                return f"Browser {'active' if browser_active else 'inactive'}, Current URL: {current_url}"
        except Exception as e:
            return f"Browser status unknown (error: {str(e)})"
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools."""
        try:
            async with self.mcp_client:
                tools_result = await self.mcp_client.list_tools()
                
                # Handle different response formats
                if isinstance(tools_result, list):
                    tools_list = tools_result
                elif hasattr(tools_result, 'tools'):
                    tools_list = tools_result.tools
                else:
                    logger.warning(f"Unexpected tools result format: {type(tools_result)}")
                    return []
                
                # Convert MCP tools to function calling format
                functions = []
                for tool in tools_list:
                    # Handle different tool object formats
                    if hasattr(tool, 'name'):
                        tool_name = tool.name
                        tool_description = getattr(tool, 'description', f"Execute {tool_name}")
                    elif isinstance(tool, dict):
                        tool_name = tool.get('name', 'unknown')
                        tool_description = tool.get('description', f"Execute {tool_name}")
                    else:
                        continue
                    
                    function_def = {
                        "name": tool_name,
                        "description": tool_description,
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                    
                    # Add input schema if available
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        function_def["parameters"] = tool.inputSchema
                    elif isinstance(tool, dict) and 'inputSchema' in tool:
                        function_def["parameters"] = tool['inputSchema']
                    
                    functions.append(function_def)
                
                logger.info(f"Retrieved {len(functions)} available tools")
                return functions
        except Exception as e:
            logger.error(f"Failed to get available tools: {e}")
            return []


def handle_interactive(config: Config, use_mcp: bool = True, headless: bool = False, verbose: bool = False) -> None:
    """
    Handle interactive mode with AI-powered browser automation and context management.
    
    Args:
        config: Application configuration
        use_mcp: Whether to use MCP server for browser automation
        headless: Whether to run browser in headless mode
        verbose: Whether to show verbose output
    """
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    try:
        # Create AI research assistant
        assistant = AIResearchAssistant(config, use_mcp=use_mcp, headless=headless)
        
        # Run interactive loop
        assistant.run_interactive_loop()
        
    except Exception as e:
        console.print(f"[red]❌ Failed to start interactive mode: {str(e)}[/red]")
        raise 