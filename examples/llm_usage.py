"""
Example usage of the Swarm LLM module.
Shows how to use streaming, reasoning models, tool calling, and more.
"""

import asyncio
import os
from swarm.llm import (
    LLMFactory, 
    create_openai_client, 
    create_anthropic_client,
    create_deepseek_client,
    create_qwen_client,
    create_gemini_client,
    create_reasoning_client
)


def basic_usage_example():
    """Basic usage example with different providers."""
    
    # Only create clients if API keys are available
    openai_client = None
    anthropic_client = None
    deepseek_client = None
    
    if os.getenv("OPENAI_API_KEY"):
        openai_client = LLMFactory.create_openai("gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
    
    if os.getenv("ANTHROPIC_API_KEY"):
        anthropic_client = LLMFactory.create_anthropic("claude-3-sonnet-20240229", api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    if os.getenv("DEEPSEEK_API_KEY"):
        deepseek_client = LLMFactory.create_deepseek("deepseek-chat", api_key=os.getenv("DEEPSEEK_API_KEY"))
    
    # Basic generation
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    # Generate responses (only if clients were created)
    if openai_client:
        openai_response = openai_client.generate(messages)
        print("OpenAI:", openai_response)
    else:
        print("OpenAI: Skipped (no API key)")
    
    if anthropic_client:
        anthropic_response = anthropic_client.generate(messages)
        print("Anthropic:", anthropic_response)
    else:
        print("Anthropic: Skipped (no API key)")
    
    if deepseek_client:
        deepseek_response = deepseek_client.generate(messages)
        print("DeepSeek:", deepseek_response)
    else:
        print("DeepSeek: Skipped (no API key)")


def streaming_example():
    """Example of streaming responses."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Skipping streaming example - no OpenAI API key found")
        return
    
    # Create client with streaming enabled
    client = LLMFactory.create("gpt-4", stream=True, api_key=api_key)
    
    messages = [
        {"role": "user", "content": "Write a short story about a robot learning to paint."}
    ]
    
    print("Streaming response:")
    for chunk in client.generate(messages):
        print(chunk, end="", flush=True)
    print()


def reasoning_model_example():
    """Example of using reasoning models with thinking display."""
    
    # Create reasoning model clients
    if os.getenv("DEEPSEEK_API_KEY"):
        deepseek_reasoner = create_reasoning_client(
            "deepseek-reasoner", 
            show_thinking=True,
            api_key=os.getenv("DEEPSEEK_API_KEY")
        )
        
        messages = [
            {"role": "user", "content": "Solve this math problem step by step: If a train travels 120 km in 2 hours, what is its average speed?"}
        ]
        
        # Generate with reasoning
        deepseek_result = deepseek_reasoner.generate_with_reasoning(messages)
        print("DeepSeek Reasoner:")
        print("Content:", deepseek_result["content"])
        if "thinking" in deepseek_result:
            print("Thinking:", deepseek_result["thinking"])
    
    if os.getenv("QWEN_API_KEY"):
        qwq_reasoner = create_reasoning_client(
            "qwq-32b-preview",
            show_thinking=True,
            api_key=os.getenv("QWEN_API_KEY")
        )
        
        messages = [
            {"role": "user", "content": "Solve this math problem step by step: If a train travels 120 km in 2 hours, what is its average speed?"}
        ]
        
        qwq_result = qwq_reasoner.generate_with_reasoning(messages)
        print("\nQwQ Reasoner:")
        print("Content:", qwq_result["content"])
        if "thinking" in qwq_result:
            print("Thinking:", qwq_result["thinking"])


def tool_calling_example():
    """Example of using tool calling with different models."""
    
    # Define tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "The temperature unit"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    messages = [
        {"role": "user", "content": "What's the weather like in New York?"}
    ]
    
    # Test with different models
    if os.getenv("OPENAI_API_KEY"):
        openai_client = create_openai_client("gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
        openai_result = openai_client.generate_with_tools(messages, tools)
        print("OpenAI tool calling:", openai_result)
    
    if os.getenv("ANTHROPIC_API_KEY"):
        anthropic_client = create_anthropic_client("claude-3-sonnet-20240229", api_key=os.getenv("ANTHROPIC_API_KEY"))
        anthropic_result = anthropic_client.generate_with_tools(messages, tools)
        print("Anthropic tool calling:", anthropic_result)


def multimodal_example():
    """Example of using multimodal capabilities with Gemini."""
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Skipping multimodal example - no Google API key found")
        return
    
    gemini_client = create_gemini_client("gemini-1.5-pro", api_key=api_key)
    
    # Text + image message (placeholder - you would need a real base64 image)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What do you see in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."  # base64 image
                    }
                }
            ]
        }
    ]
    
    # Note: This would need a real image to work
    # response = gemini_client.generate_with_multimodal(messages)
    print("Gemini multimodal example configured (need real image data to test)")


def list_available_models():
    """List all available models."""
    
    print("Available models:")
    models = LLMFactory.list_models()
    for provider, model_list in models.items():
        print(f"\n{provider.upper()}:")
        for model in model_list:
            print(f"  - {model}")
    
    print(f"\nReasoning models: {LLMFactory.list_reasoning_models()}")


def error_handling_example():
    """Example of proper error handling."""
    
    try:
        # This will fail without proper API key
        client = LLMFactory.create("gpt-4", api_key="invalid-key")
        response = client.generate([{"role": "user", "content": "Hello"}])
        print(response)
    except ValueError as e:
        print(f"Configuration error: {e}")
    except RuntimeError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def configuration_examples():
    """Examples of different configuration options."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Skipping configuration examples - no OpenAI API key found")
        return
    
    # High temperature for creative tasks
    creative_client = LLMFactory.create(
        "gpt-4",
        temperature=0.9,
        max_tokens=1000,
        api_key=api_key
    )
    
    # Low temperature for factual tasks
    factual_client = LLMFactory.create(
        "gpt-4",
        temperature=0.1,
        max_tokens=500,
        api_key=api_key
    )
    
    # Example usage
    creative_prompt = [{"role": "user", "content": "Write a creative haiku about technology"}]
    factual_prompt = [{"role": "user", "content": "What is the molecular formula of water?"}]
    
    creative_response = creative_client.generate(creative_prompt)
    factual_response = factual_client.generate(factual_prompt)
    
    print("Creative response:", creative_response)
    print("Factual response:", factual_response)


def main():
    """Run all examples."""
    print("Swarm LLM Module Examples")
    print("=" * 30)
    
    print("\n1. Available Models")
    list_available_models()
    
    print("\n2. Error Handling")
    error_handling_example()
    
    print("\n3. Basic Usage (requires API keys)")
    basic_usage_example()
    
    print("\n4. Streaming Example (requires OpenAI API key)")
    streaming_example()
    
    print("\n5. Reasoning Models (requires DeepSeek/Qwen API keys)")
    reasoning_model_example()
    
    print("\n6. Tool Calling (requires API keys)")
    tool_calling_example()
    
    print("\n7. Configuration Examples (requires OpenAI API key)")
    configuration_examples()
    
    print("\n8. Multimodal Example (requires Google API key)")
    multimodal_example()
    
    print("\nTo test with real API calls, set the following environment variables:")
    print("- OPENAI_API_KEY")
    print("- ANTHROPIC_API_KEY") 
    print("- DEEPSEEK_API_KEY")
    print("- QWEN_API_KEY (or DASHSCOPE_API_KEY)")
    print("- GOOGLE_API_KEY (or GEMINI_API_KEY)")


if __name__ == "__main__":
    main() 