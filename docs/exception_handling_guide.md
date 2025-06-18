# Exception Handling Guide

This guide explains how to use the enhanced exception handling system in Swarm, which provides specific, contextual exceptions instead of generic `Exception` handling.

## Overview

The Swarm project now uses a comprehensive exception hierarchy that provides:

- **Specific Exception Types**: Instead of catching generic `Exception`, use specific exceptions like `BrowserSessionError`, `LLMTimeoutError`, etc.
- **Rich Context Information**: Exceptions include additional context like URLs, error codes, model names, etc.
- **Automatic Exception Mapping**: Generic exceptions are automatically converted to appropriate specific exceptions
- **Consistent Error Handling**: Decorators and utilities for consistent exception handling across the codebase

## Exception Hierarchy

### Base Exception
```python
SwarmError(message, details="", error_code="")
```
- Base class for all Swarm exceptions
- Includes error codes for categorization
- Provides structured error information

### Browser Exceptions
```python
BrowserError(message, details="", url="", error_code="BROWSER_ERROR")
├── BrowserSessionError(message, error_code="BROWSER_SESSION")
├── BrowserNavigationError(message, error_code="BROWSER_NAVIGATION") 
└── BrowserElementError(message, element="", error_code="BROWSER_ELEMENT")
```

### Web Exceptions
```python
WebError(message, details="", url="", status_code=0, error_code="WEB_ERROR")
├── WebSearchError(message, query="", error_code="WEB_SEARCH")
└── WebContentError(message, error_code="WEB_CONTENT")
```

### LLM Exceptions
```python
LLMError(message, details="", model="", error_code="LLM_ERROR")
├── LLMTimeoutError(message, timeout=0, error_code="LLM_TIMEOUT")
└── LLMConnectionError(message, error_code="LLM_CONNECTION")
```

### MCP Exceptions
```python
MCPError(message, details="", tool_name="", error_code="MCP_ERROR")
├── MCPToolError(message, error_code="MCP_TOOL")
└── MCPConnectionError(message, error_code="MCP_CONNECTION")
```

### Research Exceptions
```python
ResearchError(message, details="", phase="", error_code="RESEARCH_ERROR")
├── ResearchAnalysisError(message, error_code="RESEARCH_ANALYSIS")
└── ResearchExtractionError(message, error_code="RESEARCH_EXTRACTION")
```

## Usage Examples

### 1. Using Specific Exceptions

**Before (Generic Exception Handling):**
```python
try:
    await browser.navigate_to_url(url)
except Exception as e:
    print(f"Error: {e}")
```

**After (Specific Exception Handling):**
```python
from swarm.core.exceptions import BrowserNavigationError, BrowserSessionError

try:
    await browser.navigate_to_url(url)
except BrowserNavigationError as e:
    print(f"Navigation failed: {e.message}")
    print(f"URL: {e.url}")
    print(f"Error Code: {e.error_code}")
except BrowserSessionError as e:
    print(f"Browser session error: {e.message}")
    print("Try restarting the browser")
```

### 2. Using Exception Decorators

**Browser Operations:**
```python
from swarm.utils.exception_handler import handle_async_browser_exceptions

@handle_async_browser_exceptions
async def my_browser_function():
    # This will automatically convert generic exceptions to specific browser exceptions
    await browser.click_element("button")
```

**Web Operations:**
```python
from swarm.utils.exception_handler import handle_web_exceptions

@handle_web_exceptions
def search_web(query):
    # Automatically handles web-related exceptions
    return web_search.search(query)
```

**LLM Operations:**
```python
from swarm.utils.exception_handler import handle_llm_exceptions

@handle_llm_exceptions
def generate_text(prompt):
    # Handles LLM timeouts, connection errors, etc.
    return llm_client.generate(prompt)
```

### 3. Using Exception Context Manager

```python
from swarm.utils.exception_handler import ExceptionContext

def process_data():
    with ExceptionContext("data processing", reraise=False) as ctx:
        # Your code here
        risky_operation()
        
        # Check if there was an exception
        if ctx.exception:
            if isinstance(ctx.exception, BrowserError):
                print("Browser-related error occurred")
            elif isinstance(ctx.exception, LLMError):
                print("LLM-related error occurred")
```

### 4. Safe Execution

```python
from swarm.utils.exception_handler import safe_execute

# Execute with default return value on error
result = safe_execute(
    risky_function,
    arg1, arg2,
    default_return=[],
    context="processing user data",
    log_errors=True
)
```

### 5. Exception Conversion

```python
from swarm.core.exceptions import create_exception_from_generic

try:
    some_third_party_function()
except Exception as e:
    # Convert to appropriate Swarm exception
    swarm_exception = create_exception_from_generic(
        e, 
        context="third party integration",
        url="https://api.example.com"
    )
    raise swarm_exception
```

## Best Practices

### 1. Catch Specific Exceptions First

```python
try:
    await browser.navigate_to_url(url)
except BrowserNavigationError as e:
    # Handle navigation-specific errors
    handle_navigation_error(e)
except BrowserSessionError as e:
    # Handle session-specific errors
    handle_session_error(e)
except BrowserError as e:
    # Handle general browser errors
    handle_browser_error(e)
except SwarmError as e:
    # Handle any other Swarm errors
    handle_swarm_error(e)
```

### 2. Use Decorators for Consistent Handling

```python
# Apply appropriate decorators to functions
@handle_async_browser_exceptions
async def browser_operation():
    pass

@handle_web_exceptions  
def web_operation():
    pass

@handle_llm_exceptions
def llm_operation():
    pass
```

### 3. Provide Rich Error Context

```python
# When raising exceptions, include relevant context
raise BrowserNavigationError(
    "Failed to navigate to page",
    url=url,
    details=f"Timeout after {timeout}s"
)

raise LLMTimeoutError(
    "LLM request timed out",
    model="llama3.2:latest",
    timeout=120.0
)
```

### 4. Log Exceptions Appropriately

```python
from swarm.utils.exception_handler import log_exception

try:
    risky_operation()
except SwarmError as e:
    log_exception(e, "operation context", include_traceback=True)
    # Handle the error appropriately
```

## Error Codes Reference

| Error Code | Exception Type | Description |
|------------|----------------|-------------|
| `BROWSER_ERROR` | BrowserError | General browser automation error |
| `BROWSER_SESSION` | BrowserSessionError | Browser session management error |
| `BROWSER_NAVIGATION` | BrowserNavigationError | Page navigation error |
| `BROWSER_ELEMENT` | BrowserElementError | Element interaction error |
| `WEB_ERROR` | WebError | General web-related error |
| `WEB_SEARCH` | WebSearchError | Web search operation error |
| `WEB_CONTENT` | WebContentError | Content extraction error |
| `LLM_ERROR` | LLMError | General LLM operation error |
| `LLM_TIMEOUT` | LLMTimeoutError | LLM request timeout |
| `LLM_CONNECTION` | LLMConnectionError | LLM connection error |
| `MCP_ERROR` | MCPError | General MCP protocol error |
| `MCP_TOOL` | MCPToolError | MCP tool execution error |
| `MCP_CONNECTION` | MCPConnectionError | MCP connection error |
| `RESEARCH_ERROR` | ResearchError | General research operation error |
| `RESEARCH_ANALYSIS` | ResearchAnalysisError | Research analysis error |
| `RESEARCH_EXTRACTION` | ResearchExtractionError | Content extraction during research |
| `CONFIG_ERROR` | ConfigError | Configuration-related error |
| `VALIDATION_ERROR` | ValidationError | Data validation error |

## Migration Guide

### From Generic Exception Handling

**Old Code:**
```python
try:
    result = browser.navigate(url)
except Exception as e:
    print(f"Error: {e}")
    return {"status": "error", "message": str(e)}
```

**New Code:**
```python
from swarm.core.exceptions import BrowserError, BrowserNavigationError

try:
    result = await browser.navigate_to_url(url)
except BrowserNavigationError as e:
    print(f"Navigation Error [{e.error_code}]: {e.message}")
    if e.url:
        print(f"Failed URL: {e.url}")
    return {"status": "error", "error_code": e.error_code, "message": e.message}
except BrowserError as e:
    print(f"Browser Error [{e.error_code}]: {e.message}")
    return {"status": "error", "error_code": e.error_code, "message": e.message}
```

### Adding Exception Handling to New Functions

1. **Import appropriate exceptions:**
   ```python
   from swarm.core.exceptions import BrowserError, WebError, LLMError
   ```

2. **Add appropriate decorator:**
   ```python
   from swarm.utils.exception_handler import handle_async_browser_exceptions
   
   @handle_async_browser_exceptions
   async def my_function():
       pass
   ```

3. **Handle specific exceptions:**
   ```python
   try:
       result = await my_function()
   except BrowserNavigationError as e:
       # Handle navigation errors specifically
       pass
   except BrowserError as e:
       # Handle general browser errors
       pass
   ```

## Testing Exception Handling

```python
import pytest
from swarm.core.exceptions import BrowserNavigationError

def test_navigation_error_handling():
    with pytest.raises(BrowserNavigationError) as exc_info:
        # Code that should raise BrowserNavigationError
        pass
    
    assert exc_info.value.error_code == "BROWSER_NAVIGATION"
    assert "navigation" in exc_info.value.message.lower()
```

This enhanced exception handling system provides better error diagnosis, more targeted error handling, and improved debugging capabilities throughout the Swarm application. 