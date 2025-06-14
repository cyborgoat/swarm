#!/usr/bin/env python3
"""
Example client demonstrating how to interact with Swarm MCP Server.

This example shows how an LLM or other client could use the MCP tools
provided by Swarm for browser automation.
"""

import json
from typing import Dict, Any
from swarm.core.config import Config
from swarm.mcp.browser_server import create_browser_mcp_server


def simulate_llm_tool_call(mcp_server, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate an LLM calling an MCP tool.
    
    This would normally be handled by the MCP protocol, but we simulate it here
    for demonstration purposes.
    """
    print(f"🔧 Calling tool: {tool_name}")
    print(f"📝 Arguments: {json.dumps(arguments, indent=2)}")
    
    # In a real MCP setup, this would be handled by the protocol
    # Here we simulate direct tool calls for demonstration
    
    if tool_name == "start_browser_session":
        # Simulate session start
        return {
            "status": "success",
            "message": "Browser session started successfully",
            "headless": arguments.get("headless", False)
        }
    elif tool_name == "navigate_to_url":
        # Simulate navigation
        return {
            "status": "success",
            "url": arguments["url"],
            "title": "Example Page Title",
            "content_length": 1500,
            "links_count": 25,
            "message": f"Successfully navigated to Example Page Title"
        }
    elif tool_name == "search_web":
        # Simulate web search
        return {
            "status": "success",
            "query": arguments["query"],
            "results": [
                {
                    "title": "Python Web Scraping Tutorial",
                    "url": "https://example.com/tutorial1",
                    "description": "Learn web scraping with Python"
                },
                {
                    "title": "Advanced Python Web Automation",
                    "url": "https://example.com/tutorial2", 
                    "description": "Master web automation techniques"
                }
            ],
            "count": 2,
            "message": "Found 2 search results"
        }
    else:
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}


def main():
    """Demonstrate MCP server usage patterns."""
    print("🐝 Swarm MCP Server Example")
    print("=" * 50)
    
    # Initialize the MCP server
    config = Config()
    mcp_server = create_browser_mcp_server(config)
    
    print("✅ MCP Server initialized")
    print(f"📊 Session active: {mcp_server._session_active}")
    
    # Simulate LLM research workflow
    print("\n🧠 Simulating LLM Research Workflow:")
    print("-" * 40)
    
    # Step 1: Start browser session
    result1 = simulate_llm_tool_call(mcp_server, "start_browser_session", {
        "headless": False
    })
    print(f"✅ Result: {result1['message']}")
    
    # Step 2: Search for information
    result2 = simulate_llm_tool_call(mcp_server, "search_web", {
        "query": "Python web scraping tutorial",
        "max_results": 5
    })
    print(f"✅ Result: {result2['message']}")
    print(f"📋 Found {len(result2['results'])} results:")
    for i, result in enumerate(result2['results'], 1):
        print(f"   {i}. {result['title']}")
        print(f"      {result['url']}")
    
    # Step 3: Navigate to first result
    first_url = result2['results'][0]['url']
    result3 = simulate_llm_tool_call(mcp_server, "navigate_to_url", {
        "url": first_url
    })
    print(f"✅ Result: {result3['message']}")
    print(f"📄 Page: {result3['title']}")
    print(f"📏 Content length: {result3['content_length']} characters")
    
    print("\n🎯 MCP Integration Benefits:")
    print("-" * 40)
    print("• LLMs can control browser automation directly")
    print("• Persistent sessions enable complex workflows")
    print("• Context-aware search (page vs web)")
    print("• Natural language element interaction")
    print("• Comprehensive content extraction")
    print("• Intelligent form automation")
    
    print("\n📚 Available MCP Tools:")
    print("-" * 40)
    tools = [
        "start_browser_session - Start persistent browser",
        "close_browser_session - Close browser and cleanup",
        "navigate_to_url - Browse to specific URL",
        "get_current_page_info - Get page details",
        "click_element - Click by text/label",
        "fill_input_field - Fill forms by label",
        "select_dropdown_option - Select dropdown options",
        "extract_page_content - Get page content",
        "get_page_links - List all page links",
        "get_interactive_elements - Get clickable elements",
        "search_web - DuckDuckGo web search",
        "search_current_page - Search within page",
        "search_and_navigate - Search + auto-navigate"
    ]
    
    for tool in tools:
        print(f"• {tool}")
    
    print("\n🚀 To start the actual MCP server:")
    print("   uv run swarm mcp-server")
    print("   uv run swarm mcp-server --port 3000 --verbose")
    
    print("\n🔗 Integration Examples:")
    print("• Claude Desktop: Add to mcpServers config")
    print("• OpenAI API: Use with MCP client library")
    print("• Custom LLM: Connect via MCP protocol")


if __name__ == "__main__":
    main() 