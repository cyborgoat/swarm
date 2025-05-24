import os
from dotenv import load_dotenv
import sys

# Adjust path to import from the swarm package
# Assuming examples/ is at the same level as the swarm/ directory
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from swarm.web_broswer.html_analyzer import HTMLAnalyzer, APP_CONFIG, DEFAULT_PROMPT_INSTRUCTION

def main():
    # Load environment variables (e.g., from .env.local)
    # This is good practice if API keys are not passed directly or managed by a higher-level system.
    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env.local")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        print(f"Loaded .env file from: {dotenv_path}")
    else:
        print(f"No .env.local file found at {dotenv_path}. Relying on globally set environment variables for API keys.")

    # --- Model and Prompt Configuration ---
    # The HTMLAnalyzer will now pick the model from config.json or use its internal default if not specified.
    # API keys are expected to be in environment variables if not passed to the constructor.
    analyzer = HTMLAnalyzer() # Uses model from config.json or default
    # To override: 
    # analyzer = HTMLAnalyzer(model_name="gpt-4")
    # If you needed to pass an API key directly (less common with LLMFactory handling env vars):
    # analyzer = HTMLAnalyzer(model_name="qwen-max", api_key=os.getenv("MY_SPECIFIC_QWEN_KEY"))

    default_prompt_for_example = APP_CONFIG.get("html_analyzer_default_prompt", DEFAULT_PROMPT_INSTRUCTION)
    # Stream setting is now handled internally by HTMLAnalyzer based on APP_CONFIG

    webpage_url = input(f"Enter the URL of the webpage to process (or press Enter for default test URL): ")
    if not webpage_url:
        webpage_url = "https://www.example.com" # A simple, safe default for testing
        print(f"No URL entered, using default: {webpage_url}")

    if not webpage_url.startswith(('http://', 'https://')):
        print("Invalid URL. Please include http:// or https://")
        exit(1)

    # Example: Get analysis using the default or config-defined prompt
    analysis_result = analyzer.get_and_analyze_url(webpage_url, prompt_instruction=default_prompt_for_example)
    
    if analysis_result:
        print(f"\n--- Analysis from {analyzer.llm_client.config.model_name} (Stream: {analyzer.stream_output}) ---")
        if analyzer.stream_output: # Check if it was configured to stream
            print("Streaming output:")
            full_response = ""
            try:
                for chunk in analysis_result: # analysis_result is an iterator here
                    print(chunk, end="", flush=True)
                    full_response += chunk
                print("\n--- End of stream ---")
                # You can use full_response here if needed after streaming
            except TypeError: # Handle cases where analysis_result might not be iterable (e.g. if an error upstream returned None)
                print("\nError: Expected a stream but did not receive an iterable.")
                print("Failed to get an analysis from the LLM.")
        else: # Non-streaming
            print(analysis_result) # analysis_result is a string here
    else:
        print("\nFailed to get an analysis from the LLM.")
        print("Possible reasons: API key not set/invalid for the selected model, network issue, or content extraction failed.")
        print(f"Selected model for analysis: {analyzer.llm_client.config.model_name}")
        print("Please ensure the relevant API key (e.g., OPENAI_API_KEY, QWEN_API_KEY, etc.) is set in your environment or .env.local file.")

if __name__ == "__main__":
    main() 