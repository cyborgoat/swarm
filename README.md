# 🐝 Swarm

A comprehensive CLI-based agent for web browsing, automation, and deep research with LLM integration.

## ✨ Features

- **🌐 Interactive Web Browsing**: Visible browser automation with step-by-step control
- **🤖 AI-Powered Research**: Enhanced research assistant with comprehensive 4-phase analysis
- **🔍 Smart Search**: Context-aware search with DuckDuckGo integration and intelligent result selection
- **📝 Content Analysis**: Extract and analyze web page content with natural language queries
- **⚡ MCP Server**: Expose browser automation tools to LLMs via Model Context Protocol with full logging
- **🎯 Natural Language Control**: Interact with web pages using conversational commands
- **🔧 Transparent Tool Usage**: Complete visibility into MCP tool calls and results
- **📊 Research Reports**: Generate comprehensive research reports with structured analysis

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/swarm.git
cd swarm

# Install dependencies with UV
uv sync

# Install Playwright browsers
uv run playwright install

# Install Ollama (for LLM features)
# Visit https://ollama.ai and install for your platform
# Then pull a model:
ollama pull llama3.2:latest
```

### Configuration

Create a `.env` file with your settings (copy from `.env.example`):

```bash
# LLM Configuration (for AI features)
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2:latest
LLM_API_KEY=
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=8192

# Browser Configuration (set to false for interactive mode)
BROWSER_HEADLESS=false
BROWSER_TIMEOUT=60000
BROWSER_VIEWPORT_WIDTH=1280
BROWSER_VIEWPORT_HEIGHT=720

# Web Search Configuration
SEARCH_ENGINE=duckduckgo
SEARCH_RESULTS_LIMIT=10

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=swarm.log

# Performance Settings
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=120
```

### Usage

#### Enhanced Research Mode (New!)

Conduct comprehensive research with AI-powered analysis:

```bash
# Basic research with 5 sources
uv run python swarm/cli/commands/research.py "best gaming headsets 2024"

# Advanced research with custom settings
uv run python swarm/cli/commands/research.py "artificial intelligence trends" --limit 8 --output ai_research.txt --verbose

# Research with visible browser (for debugging)
uv run python swarm/cli/commands/research.py "python web frameworks" --limit 5 --verbose
```

**Research Features:**
- 🔍 **Phase 1**: Web search with duplicate URL elimination
- 📄 **Phase 2**: Source analysis with relevance scoring and content extraction
- 🧠 **Phase 3**: Content synthesis with key findings and theme identification
- 📝 **Phase 4**: Final report generation with structured summaries

#### Interactive Mode (Recommended)

Start the intelligent interactive mode with natural language processing:

```bash
uv run swarm interactive
```

The interactive mode automatically detects if an MCP server is running and switches between:
- **🔧 MCP Mode**: Uses MCP server with full tool logging when server is detected
- **🌐 Direct Mode**: Uses direct browser automation when no MCP server is running

**Natural Language Examples:**
- "Browse github.com"
- "Search for Python web scraping tutorials"
- "What is this page about?"
- "Click the login button"
- "Fill in the email field with john@example.com"
- "Select United States from the country dropdown"

#### MCP Server (For LLM Integration)

Start the MCP server to expose browser automation tools to LLMs:

```bash
# Start MCP server with full logging
uv run swarm --verbose mcp-server

# Run in background for use with interactive mode
uv run swarm --verbose mcp-server &
```

When the MCP server is running, you'll see detailed logging of all tool calls:

```
🔧 MCP Tool: start_browser_session called with headless=False
✅ MCP Tool: start_browser_session -> success
🔧 MCP Tool: navigate_to_url called with url=https://example.com
✅ MCP Tool: navigate_to_url -> success to Example Page
```

The MCP server provides **14 tools** to LLMs:

**Session Management:**
- `start_browser_session` - Start persistent browser session
- `close_browser_session` - Close browser and cleanup
- `get_session_status` - Check current session status

**Navigation:**
- `navigate_to_url` - Browse to specific URL
- `get_current_page_info` - Get page details and elements

**Interaction:**
- `click_element` - Click element by visible text
- `fill_input_field` - Fill form fields by label
- `select_dropdown_option` - Select dropdown options

**Content Extraction:**
- `extract_page_content` - Get page content with filtering
- `get_page_links` - List all page links
- `get_interactive_elements` - Get clickable elements

**Search:**
- `search_web` - DuckDuckGo web search
- `search_current_page` - Search within current page
- `search_and_navigate` - Search + auto-navigate

#### Basic Commands

```bash
# Browse a specific URL
uv run swarm browse https://example.com

# Search the web
uv run swarm search "Python tutorials"

# Show information
uv run swarm info
```

## 🏗️ Architecture

### Core Components

- **🧠 LLM Client**: Connects to Ollama, VLLM, or OpenAI-compatible APIs with enhanced timeout handling
- **🌐 Browser Engine**: Playwright-based automation with persistent sessions and async support
- **🔍 Search Engine**: DuckDuckGo integration with duplicate URL elimination
- **⚡ MCP Server**: Model Context Protocol server for LLM tool integration with full logging
- **🎨 CLI Interface**: Rich terminal interface with progress indicators
- **🔧 Smart Detection**: Automatic MCP server detection and mode switching
- **📊 Research Assistant**: Enhanced 4-phase research system with comprehensive analysis

### Enhanced Research System

The research assistant conducts comprehensive analysis in 4 phases:

1. **🔍 Phase 1 - Web Search**: 
   - DuckDuckGo search with duplicate URL elimination
   - Intelligent result filtering and validation
   - Progress tracking with visual feedback

2. **📄 Phase 2 - Source Analysis**:
   - Content extraction from each source
   - Relevance scoring based on query matching
   - Individual source summaries with retry logic
   - Error handling for inaccessible sources

3. **🧠 Phase 3 - Content Synthesis**:
   - Key findings extraction from each source
   - Theme identification across all sources
   - Cross-source pattern recognition
   - Structured data organization

4. **📝 Phase 4 - Final Report Generation**:
   - Comprehensive executive summary
   - Structured key findings with evidence
   - Theme analysis with supporting sources
   - Detailed source-by-source breakdown
   - Complete research statistics

### Technical Improvements

- **🔧 Timeout Handling**: Increased timeouts (120s) and retry logic for LLM calls
- **🚫 Duplicate Prevention**: URL deduplication in search results
- **📊 Token Management**: Optimized token usage with content limiting
- **⚡ Async Operations**: Full async support eliminating threading conflicts
- **🛡️ Error Recovery**: Comprehensive error handling with fallback strategies

## 📖 Usage Examples

### Comprehensive Research Workflow

```bash
# Research with detailed progress reporting
uv run python swarm/cli/commands/research.py "best wireless earbuds 2024" --limit 5 --output earbuds_research.txt --verbose

# Output includes:
# - Search results table with URLs and titles
# - Individual source analysis panels
# - Key findings extraction
# - Theme identification
# - Final structured report
# - Complete research statistics
```

### Research Workflow with MCP Logging

```python
# LLM can perform sophisticated research with full visibility:
start_browser_session()  # 🔧 MCP Tool: start_browser_session -> success
search_and_navigate("latest AI research papers", auto_select=True)  # 🔧 MCP Tool: search_and_navigate -> success
content = extract_page_content("machine learning trends")  # 🔧 MCP Tool: extract_page_content -> success (2451 chars)
click_element("Next Page")  # 🔧 MCP Tool: click_element -> success
more_content = extract_page_content("deep learning")  # 🔧 MCP Tool: extract_page_content -> success
# LLM analyzes and synthesizes information
close_browser_session()  # 🔧 MCP Tool: close_browser_session -> success
```

### Interactive Search Session

```bash
# Start MCP server in background
uv run swarm --verbose mcp-server &

# Start interactive mode (automatically detects MCP server)
uv run swarm interactive

# Example interaction:
🐝 What would you like me to do?: search for best gaming mouse
🔍 Searching the web for: 'search for best gaming mouse'
🔧 MCP Tool [search_web] - Searching the web
🔍 Found 10 search results:
[Results displayed in table format]

# Navigate to a result
🐝 What would you like me to do?: browse result 4
🔧 MCP Tool: navigate_to_url called with url=https://www.ign.com/articles/best-gaming-mouse
✅ MCP Tool: navigate_to_url -> success to The Best Gaming Mouse: Our Top Reviewed Picks

# Search within the page
🐝 What would you like me to do?: search for wireless gaming mouse
🔍 Searching within current page for: 'wireless gaming mouse'
🔧 MCP Tool: extract_page_content called with query=wireless gaming mouse
✅ Found 5 relevant matches on this page
```

### Form Automation

```python
# Automate complex form filling with logging:
navigate_to_url("https://example.com/signup")  # 🔧 MCP Tool: navigate_to_url -> success
fill_input_field("Email", "user@example.com")  # 🔧 MCP Tool: fill_input_field -> success
fill_input_field("Password", "secure_password")  # 🔧 MCP Tool: fill_input_field -> success
select_dropdown_option("Country", "United States")  # 🔧 MCP Tool: select_dropdown_option -> success
click_element("Create Account")  # 🔧 MCP Tool: click_element -> success
```

## 🔧 Development

### Setup

```bash
# Install development dependencies
uv sync --group dev

# Run tests
uv run pytest

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy .
```

### Project Structure

```
swarm/
├── cli/                 # CLI commands and interface
│   ├── commands/        # Individual command handlers
│   │   ├── interactive.py         # Interactive mode with MCP detection
│   │   ├── research.py           # Research command with argument parsing
│   │   └── research_assistant.py # Enhanced 4-phase research assistant
│   └── main.py         # Main CLI entry point
├── core/               # Core configuration and exceptions
│   └── config.py       # Enhanced configuration with better defaults
├── web/                # Web automation components
│   ├── browser.py      # Async Playwright browser automation
│   └── search.py       # DuckDuckGo search with duplicate elimination
├── llm/                # LLM client and integration
│   └── client.py       # Enhanced LLM client with timeout handling
├── mcp/                # Model Context Protocol server
│   └── browser_server.py    # MCP server with 14 tools and logging
└── utils/              # Utility functions
```

## 🤝 LLM Integration

### Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "swarm-browser": {
      "command": "uv",
      "args": ["run", "swarm", "mcp-server"],
      "cwd": "/path/to/swarm"
    }
  }
}
```

### OpenAI API

```python
import openai
from mcp_client import MCPClient

mcp_client = MCPClient("http://localhost:8000")
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Research Python web frameworks"}],
    tools=mcp_client.get_available_tools()
)
```

## 🧪 Testing & Verification

The project includes comprehensive testing to ensure:

- ✅ **MCP Server Detection**: Correctly detects when MCP server is running
- ✅ **Tool Integration**: All 14 MCP tools work with proper logging
- ✅ **Search Functionality**: Query detection and term extraction work correctly
- ✅ **Content Analysis**: Page content extraction with search filtering
- ✅ **Error Handling**: Robust error handling and recovery
- ✅ **Research System**: 4-phase research with duplicate elimination and timeout handling

Run verification tests:

```bash
# Test MCP integration and search functionality
python -c "
from swarm.cli.commands.interactive import _check_mcp_server_running, is_search_query, extract_search_terms
print('MCP Detection:', _check_mcp_server_running())
print('Search Query:', is_search_query('search for python tutorials'))
print('Search Terms:', extract_search_terms('search for python tutorials'))
"

# Test research functionality
uv run python swarm/cli/commands/research.py "test query" --limit 2 --verbose
```

## 📚 Documentation

- [MCP Integration Guide](examples/mcp_integration.md) - Comprehensive MCP server usage
- [Basic Usage Examples](examples/basic_usage.py) - Simple automation examples
- [Smart Search Demo](examples/smart_search_demo.py) - Advanced search patterns

## 🛠️ Technologies

- **[Playwright](https://playwright.dev/python/)**: Browser automation with async support
- **[FastMCP](https://gofastmcp.com/)**: Model Context Protocol server
- **[Click](https://click.palletsprojects.com/)**: CLI framework
- **[Rich](https://rich.readthedocs.io/)**: Terminal formatting and progress indicators
- **[Pydantic](https://docs.pydantic.dev/)**: Configuration management
- **[UV](https://docs.astral.sh/uv/)**: Fast Python package manager
- **[Ollama](https://ollama.ai/)**: Local LLM integration

## 🚀 Recent Improvements

### v2.0 - Enhanced Research System
- **🔍 Duplicate URL Elimination**: Fixed search returning duplicate results
- **⏱️ Timeout Handling**: Resolved LLM timeout issues with retry logic
- **📊 4-Phase Research**: Comprehensive research workflow with structured analysis
- **🛡️ Error Recovery**: Robust error handling with fallback strategies
- **⚡ Async Operations**: Full async support eliminating threading conflicts
- **📝 Rich Reporting**: Detailed progress reporting and structured output

### Technical Fixes
- Increased HTTP timeouts from 30s to 120s
- Enhanced token management (4096 → 8192 tokens)
- Added URL deduplication in search results
- Implemented retry logic for all LLM calls
- Optimized content limiting to prevent token overflow
- Updated default model to `llama3.2:latest`

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## 📄 License

This project is licensed under the MIT License.

---

*Transform your web browsing and research workflows with AI-powered automation and comprehensive analysis! 🐝* 