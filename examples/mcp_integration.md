# Swarm MCP Integration Guide

This guide shows how to integrate Swarm's browser automation tools with LLMs using the Model Context Protocol (MCP).

## Overview

Swarm provides an MCP server that exposes 14 browser automation tools to LLMs:

- **Session Management**: Start/close browser sessions, check status
- **Navigation**: Browse URLs, get page information, navigate back
- **Interaction**: Click elements, fill forms, select dropdowns
- **Content Extraction**: Get page content, links, interactive elements
- **Search**: Web search, page search, search and navigate

## Quick Start

### 1. Start the MCP Server

```bash
# Basic usage
uv run swarm mcp-server

# With verbose output
uv run swarm --verbose mcp-server
```

The server uses stdio transport (not HTTP) as required by the MCP specification.

### 2. Connect from Claude Desktop

Add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "swarm-browser": {
      "command": "uv",
      "args": ["run", "swarm", "mcp-server"],
      "cwd": "/path/to/your/swarm/project"
    }
  }
}
```

### 3. Connect from Python/OpenAI

```python
import subprocess
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def connect_to_swarm():
    # Start the Swarm MCP server
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "swarm", "mcp-server"],
        cwd="/path/to/your/swarm/project"
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # Use a tool
            result = await session.call_tool("start_browser_session", {})
            print(f"Browser session started: {result}")
```

## Available Tools

### Session Management

- `start_browser_session()` - Start a persistent browser session
- `close_browser_session()` - Close browser and cleanup resources  
- `get_session_status()` - Check current session status

### Navigation

- `navigate_to_url(url)` - Browse to a specific URL
- `get_current_page_info()` - Get page title, URL, and basic elements
- `go_back()` - Navigate back to previous page

### Interaction

- `click_element(text)` - Click element by visible text
- `fill_input_field(label, value)` - Fill form field by label
- `select_dropdown_option(label, option)` - Select dropdown option

### Content Extraction

- `extract_page_content(content_type?)` - Get page content with optional filtering
- `get_page_links()` - List all links on the page
- `get_interactive_elements()` - Get all clickable/interactive elements

### Search

- `search_web(query)` - Search the web using DuckDuckGo
- `search_current_page(query)` - Search within current page content
- `search_and_navigate(query)` - Search web and auto-navigate to first result

## Example Workflows

### Basic Web Research

```python
# Start browser session
await session.call_tool("start_browser_session", {})

# Search for information
search_result = await session.call_tool("search_web", {
    "query": "latest AI developments 2024"
})

# Navigate to first result
await session.call_tool("search_and_navigate", {
    "query": "latest AI developments 2024"
})

# Extract content
content = await session.call_tool("extract_page_content", {
    "content_type": "main"
})

# Get all links for further exploration
links = await session.call_tool("get_page_links", {})
```

### Form Interaction

```python
# Navigate to a form page
await session.call_tool("navigate_to_url", {
    "url": "https://example.com/contact"
})

# Fill out the form
await session.call_tool("fill_input_field", {
    "label": "Name",
    "value": "John Doe"
})

await session.call_tool("fill_input_field", {
    "label": "Email", 
    "value": "john@example.com"
})

await session.call_tool("select_dropdown_option", {
    "label": "Country",
    "option": "United States"
})

# Submit the form
await session.call_tool("click_element", {
    "text": "Submit"
})
```

### Page Analysis

```python
# Get page overview
page_info = await session.call_tool("get_current_page_info", {})

# Extract main content
content = await session.call_tool("extract_page_content", {
    "content_type": "main"
})

# Get all interactive elements
elements = await session.call_tool("get_interactive_elements", {})

# Search within page
search_results = await session.call_tool("search_current_page", {
    "query": "pricing information"
})
```

## Error Handling

All tools return structured responses with success/error status:

```python
result = await session.call_tool("navigate_to_url", {
    "url": "https://example.com"
})

if result.get("success"):
    print(f"Navigation successful: {result.get('message')}")
else:
    print(f"Navigation failed: {result.get('error')}")
```

## Best Practices

1. **Always start a browser session** before using other tools
2. **Check session status** if you encounter errors
3. **Use appropriate content filtering** when extracting page content
4. **Handle errors gracefully** - network issues and page changes are common
5. **Close sessions** when done to free resources
6. **Use search_and_navigate** for quick research workflows
7. **Combine tools** for complex automation tasks

## Troubleshooting

### Common Issues

1. **"No active browser session"** - Call `start_browser_session()` first
2. **Element not found** - Check if page has loaded completely
3. **Navigation timeout** - Some pages take longer to load
4. **Form field not found** - Verify the exact label text

### Debug Mode

Run the server with verbose output to see detailed logs:

```bash
uv run swarm --verbose mcp-server
```

This will show all tool calls and responses in real-time.

## Integration Examples

See the `examples/` directory for complete integration examples:

- `smart_search_demo.py` - Demonstrates intelligent search workflows
- `mcp_client_example.py` - Shows how to build custom MCP clients
- `claude_desktop_config.json` - Claude Desktop configuration

## Advanced Usage

### Custom Tool Combinations

You can create sophisticated workflows by combining multiple tools:

```python
async def research_topic(topic: str):
    """Research a topic comprehensively."""
    
    # Start session
    await session.call_tool("start_browser_session", {})
    
    # Search for the topic
    search_result = await session.call_tool("search_web", {"query": topic})
    
    # Navigate to first result
    await session.call_tool("search_and_navigate", {"query": topic})
    
    # Extract main content
    content = await session.call_tool("extract_page_content", {
        "content_type": "main"
    })
    
    # Get related links
    links = await session.call_tool("get_page_links", {})
    
    # Search within page for specific information
    specific_info = await session.call_tool("search_current_page", {
        "query": "key findings conclusions"
    })
    
    return {
        "main_content": content,
        "related_links": links,
        "key_findings": specific_info
    }
```

This comprehensive approach allows LLMs to perform sophisticated web research and automation tasks through the MCP protocol. 