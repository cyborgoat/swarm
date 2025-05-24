# Swarm

A comprehensive platform for multi-LLM integration and agent-based web interaction. Swarm provides a unified interface for working with multiple Large Language Model providers and includes agents for web page analysis and interactive browser automation.

## Features

### 🧠 LLM Module (`swarm.llm`)
- **Multiple Providers**: OpenAI, Anthropic, Qwen, Gemini, DeepSeek.
- **Unified Interface**: Consistent API (`generate`, `generate_with_tools`) across all providers.
- **Configuration Driven**: Load LLM setups from `llm_config.json`, including API keys, model parameters, and specific endpoints.
- **Streaming Support**: Real-time response streaming.
- **Reasoning Models**: Support for models with explicit thinking/reasoning steps.
- **Tool Calling**: Function calling capabilities.
- **Multimodal**: Image and text input support (provider-dependent, e.g., Gemini).

### 🌐 Web Browser Module (`swarm.web_broswer`)
- **`HTMLAnalyzer`**: Fetches web content, cleans HTML, and uses an LLM to analyze or summarize it. Configurable via `agent_config.json`.
- **`WebActions`**: Integrates Selenium and an LLM for interactive web automation. Users specify intentions, and the LLM plans and executes actions (type, click, navigate) on web pages. Configurable via `agent_config.json`.

### ⚙️ Configuration
- **`llm_config.json`**: Centralized configuration for all LLM providers, including API keys and detailed model parameters for named configurations (e.g., "default_openai", "deepseek_coder_streaming").
- **`agent_config.json`**: Configuration for agents like `HTMLAnalyzer` and `WebActions`, specifying which LLM configuration (by name from `llm_config.json`) to use, and other agent-specific settings.
- **`.env.local`**: For storing sensitive API keys, which are then referenced by `llm_config.json` or directly by the LLM clients.

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Clone the repository
git clone <repository-url>
cd swarm

# Install core dependencies
uv pip install -e .

# Install development dependencies (for linting, testing, etc.)
uv pip install -e ".[dev]"
```

## Configuration Setup

1.  **Copy `.env.sample` to `.env.local`**:
    ```bash
    cp .env.sample .env.local
    ```
    Edit `.env.local` to add your actual API keys for the LLM providers you intend to use.

2.  **Review `llm_config.json`**:
    This file contains definitions for various LLM setups (e.g., "default_openai", "default_qwen_streaming").
    - API keys within specific configurations can be set to `null` to use the corresponding key from the `api_keys` section or environment variables.
    - The `api_keys` section maps generic key names (e.g., `OPENAI_API_KEY`) to placeholders. These are primarily resolved via `.env.local`.

3.  **Review `agent_config.json`**:
    This file defines settings for agents.
    - `html_analyzer.default_llm_config_name` points to an LLM setup in `llm_config.json` for the HTML analyzer.
    - `web_actions.default_llm_config_name` points to an LLM setup for the web automation agent.
    - You can customize which LLM configurations your agents use by changing these names.

## Quick Start

### 1. Using the LLM Module

```python
# examples/llm_usage.py (Simplified)
from swarm.llm import LLMFactory
from dotenv import load_dotenv
import os

# Load .env.local (if you have API keys there)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env.local"))

# Option 1: Create an LLM using a predefined configuration from llm_config.json
try:
    # LLMFactory will load llm_config.json by default
    llm_from_config = LLMFactory.create_from_config("default_openai")
    print(f"Created LLM from config: {llm_from_config.config.model_name}")
    response = llm_from_config.generate([{"role": "user", "content": "Hello from configured LLM!"}])
    print(f"Response: {response}")
except ValueError as e:
    print(f"Error creating LLM from config: {e}")
    print("Ensure 'default_openai' is defined in llm_config.json and API keys are set.")

# Option 2: Create an LLM by specifying model name directly (API key will be sourced)
try:
    direct_llm = LLMFactory.create(model_name="gpt-3.5-turbo") # API key from env or llm_config.json
    print(f"Created LLM directly: {direct_llm.config.model_name}")
    response = direct_llm.generate([{"role": "user", "content": "Hello from direct LLM!"}])
    print(f"Response: {response}")
except Exception as e:
    print(f"Error creating direct LLM: {e}")

```
Run: `python examples/llm_usage.py`

### 2. Using the HTML Analyzer Agent

```python
# examples/html_analyzer_usage.py (Simplified)
from swarm.web_broswer import HTMLAnalyzer
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env.local"))

try:
    # HTMLAnalyzer loads its LLM config name from agent_config.json
    # LLMFactory then loads the details from llm_config.json
    analyzer = HTMLAnalyzer()
    
    url_to_analyze = "https://www.python.org/"
    print(f"Analyzing URL: {url_to_analyze}")
    
    # Analysis can be a string or a generator if streaming is enabled for the LLM config
    analysis_result = analyzer.get_and_analyze_url(url_to_analyze)
    
    if hasattr(analysis_result, '__iter__') and not isinstance(analysis_result, str):
        print("\n--- Streaming Analysis ---")
        for chunk in analysis_result:
            print(chunk, end="", flush=True)
        print("\n------------------------")
    elif analysis_result:
        print("\n--- Full Analysis ---")
        print(analysis_result)
        print("---------------------")
    else:
        print("Failed to get analysis.")
        
except Exception as e:
    print(f"An error occurred: {e}")
    print("Ensure configurations in agent_config.json and llm_config.json are correct and API keys are set.")
```
Run: `python examples/html_analyzer_usage.py`

### 3. Using the Web Actions Agent (Interactive)

The `WebActions` agent is typically run interactively.

```bash
# Ensure API keys and configurations are set in .env.local, llm_config.json, and agent_config.json
# The WebActions agent will use the LLM configuration specified in agent_config.json 
# (or overridden by WEB_ACTIONS_LLM_CONFIG_NAME env var).

python -m swarm.web_broswer.web_actions 
```
This will start an interactive session in your terminal:
```
Enter URL: <your_target_url>
Current page: ...
Your action/intention? ('refresh','back','forward','quit', or describe task): <describe_what_you_want_to_do>
```

## Project Structure

```
swarm/
├── swarm/                 # Main package
│   ├── __init__.py
│   ├── llm/              # LLM module
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── factory.py
│   │   └── (client implementations: openai_client.py, etc.)
│   └── web_broswer/      # Web Browser Agents
│       ├── __init__.py
│       ├── html_analyzer.py
│       └── web_actions.py
├── examples/             # Usage examples
│   ├── llm_usage.py
│   └── html_analyzer_usage.py
├── .env.sample           # Sample environment file
├── .gitignore
├── agent_config.json     # Agent configurations
├── llm_config.json       # LLM provider and model configurations
├── pyproject.toml        # Project configuration and dependencies
└── README.md             # This file
```

## Environment Variables for API Keys

API keys are primarily managed through `.env.local` (copied from `.env.sample`). `llm_config.json` references these or they can be picked up by the SDKs if set directly in your environment.

Key names expected in `.env.local` or your environment:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `DASHSCOPE_API_KEY` (for Qwen models via Aliyun DashScope)
- `GOOGLE_API_KEY` (for Gemini models)
- `DEEPSEEK_API_KEY`

## Detailed API Reference

### `swarm.llm.LLMFactory`

The primary way to get LLM client instances.

-   **`LLMFactory.create_from_config(config_name: str, config_path: Optional[str] = None, **override_kwargs) -> BaseLLM`**
    -   Loads an LLM client based on a named configuration from `llm_config.json` (or `config_path` if specified).
    -   `override_kwargs` can be used to dynamically change parameters of the loaded configuration (e.g., `temperature=0.5`, `stream_config=StreamConfig(enabled=True)`).
-   **`LLMFactory.create(model_name: str, api_key: Optional[str] = None, ..., **kwargs) -> BaseLLM`**
    -   Creates an LLM client by specifying parameters directly. API key resolution will check `llm_config.json` and environment variables if not provided.
-   **`LLMFactory.list_available_configs() -> List[str]`**: Lists all LLM configuration names found in `llm_config.json`.
-   Provider-specific helpers like `LLMFactory.create_openai(...)` are also available.

### `swarm.llm.BaseLLM` (and its clients)

All LLM clients provide:
-   `generate(messages: List[Dict[str, str]], **kwargs) -> Union[str, Iterator[str]]`
-   `generate_with_tools(messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **kwargs) -> Union[str, Iterator[str], Dict]`
-   `config: LLMConfig` (contains the resolved configuration for the client)
-   Properties like `supports_streaming`, `supports_reasoning`.

### `swarm.web_broswer.HTMLAnalyzer`

Analyzes HTML content from a URL using an LLM.
-   `__init__(self, llm_config_name: Optional[str] = None, **llm_override_kwargs)`:
    -   `llm_config_name`: Name of the LLM configuration from `llm_config.json` to use. Defaults to value in `agent_config.json`.
    -   `**llm_override_kwargs`: Override parameters for the chosen LLM configuration.
-   `get_text_from_url(self, url: str) -> str | None`: Fetches and cleans text from a URL.
-   `analyze_text_content(self, text_content: str, prompt_instruction: Optional[str] = None) -> str | None | Iterator[str]`: Sends text to LLM.
-   `get_and_analyze_url(self, url: str, prompt_instruction: Optional[str] = None) -> str | None | Iterator[str]`: Combines fetching and analysis.

### `swarm.web_broswer.WebActions`

Integrates Selenium and LLM for interactive web automation.
-   `__init__(self, llm_config_name: Optional[str] = None, headless: bool = True, **llm_override_kwargs)`:
    -   `llm_config_name`: Name of LLM config from `llm_config.json`. Defaults based on `agent_config.json` or `WEB_ACTIONS_LLM_CONFIG_NAME` env var. Streaming is always disabled for the planning LLM.
    -   `headless`: Run browser headlessly.
    -   `**llm_override_kwargs`: Overrides for the LLM config.
-   `open_url(self, url: str)`
-   `get_simplified_dom(self) -> str`: Extracts interactive elements from the current page.
-   `plan_actions_with_llm(self, user_intention: str, dom_info: str) -> Optional[List[Dict[str, Any]]]`
-   `execute_actions(self, actions: List[Dict[str, Any]])`
-   `interact(self)`: Starts the interactive command loop.
-   `close(self)`: Closes the browser.

## Supported LLM Models

### OpenAI
- `gpt-4`, `gpt-4-turbo`, `gpt-4o`, `gpt-4o-mini`
- `gpt-3.5-turbo`, `gpt-3.5-turbo-16k`

### Anthropic
- `claude-3-opus-20240229`, `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`, `claude-3-5-sonnet-20241022`

### DeepSeek
- `deepseek-chat` (DeepSeek-V3)
- `deepseek-reasoner` (DeepSeek-R1) - Reasoning model
- `deepseek-coder`

### Qwen
- `qwen-turbo`, `qwen-plus`, `qwen-max`
- `qwq-32b-preview` - Reasoning model
- `qwen-coder-turbo`

### Gemini
- `gemini-1.5-pro`, `gemini-1.5-flash`
- `gemini-2.0-flash-exp`
- `gemini-pro-vision` - Multimodal

## Usage Examples

### Streaming Responses

```python
from swarm.llm import LLMFactory

# Enable streaming
client = LLMFactory.create("gpt-4", stream=True, api_key="your-key")

messages = [{"role": "user", "content": "Write a story"}]

for chunk in client.generate(messages):
    print(chunk, end="", flush=True)
```

### Reasoning Models

```python
from swarm.llm import create_reasoning_client

# Create reasoning model with thinking display
reasoner = create_reasoning_client(
    "deepseek-reasoner", 
    show_thinking=True,
    api_key="your-deepseek-key"
)

messages = [{"role": "user", "content": "Solve: 2x + 5 = 17"}]

result = reasoner.generate_with_reasoning(messages)
print("Answer:", result["content"])
print("Thinking:", result["thinking"])  # Shows reasoning process
```

### Tool Calling

```python
# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            }
        }
    }
]

client = LLMFactory.create("gpt-4", api_key="your-key")
messages = [{"role": "user", "content": "What's the weather in Paris?"}]

result = client.generate_with_tools(messages, tools)
if isinstance(result, dict) and "tool_calls" in result:
    print("Tool calls:", result["tool_calls"])
```

### Multimodal (Gemini)

```python
from swarm.llm import create_gemini_client

client = create_gemini_client("gemini-1.5-pro", api_key="your-google-key")

messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64,<base64-image>"}
            }
        ]
    }
]

response = client.generate_with_multimodal(messages)
```

## Environment Variables

Copy the `.env.sample` file to `.env.local` and fill in your API keys.

```bash
cp .env.sample .env.local
# Now edit .env.local with your actual keys
```

Alternatively, set API keys directly as environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# DeepSeek
export DEEPSEEK_API_KEY="sk-..."

# Qwen (Alibaba Cloud)
export QWEN_API_KEY="sk-..."
# or
export DASHSCOPE_API_KEY="sk-..."

# Gemini (Google)
export GOOGLE_API_KEY="AIza..."
# or
export GEMINI_API_KEY="AIza..."
```

## Project Structure

```
swarm/
├── swarm/                 # Main package
│   ├── __init__.py
│   ├── main.py           # Application entry point
│   └── llm/              # LLM module
│       ├── __init__.py
│       ├── base.py       # Base classes and configurations
│       ├── factory.py    # LLM factory for easy instantiation
│       ├── openai_client.py
│       ├── anthropic_client.py
│       ├── deepseek_client.py
│       ├── qwen_client.py
│       └── gemini_client.py
├── examples/             # Usage examples
│   └── llm_usage.py
├── pyproject.toml        # Project configuration
├── README.md            # This file
└── LICENSE
```

## API Reference

### LLMFactory

Main factory class for creating LLM clients.

```python
# Create any supported model
client = LLMFactory.create(model_name, api_key=None, **kwargs)

# Provider-specific creation methods
openai_client = LLMFactory.create_openai(model, api_key=None, **kwargs)
anthropic_client = LLMFactory.create_anthropic(model, api_key=None, **kwargs)
qwen_client = LLMFactory.create_qwen(model, api_key=None, **kwargs)
gemini_client = LLMFactory.create_gemini(model, api_key=None, **kwargs)
deepseek_client = LLMFactory.create_deepseek(model, api_key=None, **kwargs)

# Reasoning model creation
reasoning_client = LLMFactory.create_reasoning_model(model, show_thinking=True, **kwargs)
```

### BaseLLM

All clients inherit from BaseLLM and provide these methods:

```python
# Generate text response
response = client.generate(messages, **kwargs)

# Generate with tool calling
response = client.generate_with_tools(messages, tools, **kwargs)

# Get model information
info = client.get_model_info()

# Check capabilities
client.supports_streaming  # bool
client.supports_reasoning  # bool
client.supports_mcp       # bool
```

### ReasoningLLM

Reasoning models (DeepSeek-R1, QwQ) provide additional methods:

```python
# Generate with reasoning display
result = client.generate_with_reasoning(messages, show_thinking=True, **kwargs)
# Returns: {"content": "answer", "thinking": "reasoning process"}
```

## Development

### Setup

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Lint code
ruff check .
```

### Running Examples

```bash
# Run LLM usage examples
python examples/llm_usage.py

# Run with specific API keys for testing
OPENAI_API_KEY=your_key python examples/llm_usage.py
```

## Provider-Specific Notes

### DeepSeek
- Uses OpenAI-compatible API at `https://api.deepseek.com`
- `deepseek-reasoner` model supports reasoning with thinking display
- Based on [DeepSeek API docs](https://api-docs.deepseek.com/)

### Qwen
- Uses OpenAI-compatible API through Alibaba Cloud DashScope
- `qwq-32b-preview` is a reasoning model
- Requires QWEN_API_KEY or DASHSCOPE_API_KEY

### Gemini
- Native Google Generative AI SDK
- Supports multimodal inputs (text + images)
- Requires GOOGLE_API_KEY or GEMINI_API_KEY

### Anthropic
- Native Anthropic SDK with streaming support
- Tool calling uses Anthropic's format
- Built-in MCP support preparation

### OpenAI
- Native OpenAI SDK
- Supports all OpenAI features including vision models
- MCP support through compatible libraries

## Model Context Protocol (MCP)

Preparatory support for MCP is included:

```python
# Connect to MCP server (when available)
client.connect_mcp_server("ws://localhost:8000", tools=["calculator"])

# List MCP tools
tools = client.list_mcp_tools()
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the terms specified in the LICENSE file.

### LLM Module API Reference

(Details on `LLMFactory`, `BaseLLM`, specific clients, and configuration dataclasses would go here.)

### Supported LLM Models

The Swarm LLM module currently supports the following models through their respective clients:

**OpenAI:**
- gpt-4
- gpt-4-turbo
- gpt-4o
- gpt-4o-mini
- gpt-3.5-turbo
- gpt-3.5-turbo-16k
- gpt-4-vision-preview
- gpt-4-turbo-preview

**Anthropic:**
- claude-3-opus-20240229
- claude-3-sonnet-20240229
- claude-3-haiku-20240307
- claude-3-5-sonnet-20241022
- claude-3-5-haiku-20241022

**Qwen (via DashScope):**
- qwen-turbo
- qwen-plus
- qwen-max
- qwen-coder-turbo
- qwq-32b-preview (Reasoning Model)

**Gemini (Google):**
- gemini-1.5-pro
- gemini-1.5-flash
- gemini-1.5-flash-8b
- gemini-2.0-flash-exp
- gemini-pro
- gemini-pro-vision

**DeepSeek:**
- deepseek-chat
- deepseek-reasoner (Reasoning Model)
- deepseek-coder

**Reasoning Models (Specialized):**
- deepseek-reasoner
- qwq-32b-preview

These models can be instantiated using the `LLMFactory.create("model-name-here")` method.

### Web Browser Module (`swarm.web_broswer`)
