# Swarm

A comprehensive platform for multi-LLM integration and canvas-like applications. Swarm provides a unified interface for working with multiple Large Language Model providers, supporting streaming, reasoning models, tool calling, multimodal inputs, and Model Context Protocol.

## Features

### 🧠 LLM Module
- **Multiple Providers**: OpenAI, Anthropic, Qwen, Gemini, DeepSeek
- **Streaming Support**: Real-time response streaming for all providers
- **Reasoning Models**: Special support for reasoning models (DeepSeek-R1, QwQ) with thinking display
- **Tool Calling**: Function calling support across compatible models
- **Multimodal**: Image and text input support (Gemini)
- **Model Context Protocol**: Preparatory support for MCP integration
- **Unified Interface**: Same API across all providers
- **Easy Configuration**: Simple factory pattern for model instantiation

### 🎨 Canvas-like Application Platform
- Extensible architecture for building interactive applications
- Modular design for easy component integration

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Clone the repository
git clone <repository-url>
cd swarm

# Install dependencies with uv
uv pip install -e .

# For development
uv pip install -e ".[dev]"
```

## Quick Start

### Basic LLM Usage

```python
from swarm.llm import LLMFactory

# Create any model with a simple interface
client = LLMFactory.create("gpt-4", api_key="your-api-key")

# Generate a response
messages = [{"role": "user", "content": "Hello!"}]
response = client.generate(messages)
print(response)
```

### Running the Application

```bash
# Run the main application
python -m swarm

# Or using the installed script
swarm
```

### Running Examples

```bash
# Run LLM examples
python examples/llm_usage.py
```

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

Set API keys using environment variables:

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
