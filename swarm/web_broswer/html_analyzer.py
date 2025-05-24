"""
HTML Analyzer using web scraping and LLM for content processing.

This module fetches content from a URL, cleans it, and uses an LLM (Qwen model via LLMFactory)
to analyze or summarize the text.
"""

import requests
from bs4 import BeautifulSoup
import os
import json # For loading config.json
from typing import Iterator # Import Iterator

# Import LLMFactory from the swarm.llm module
from swarm.llm import LLMFactory, BaseLLM

# Define the path to the config file, assuming it's in the project root
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config.json")
DEFAULT_MODEL = "qwen-turbo" # Fallback if config.json or specific entry is missing
DEFAULT_PROMPT_INSTRUCTION = "Analyze the following web content and tell me what it's about and its key points:"

def load_config() -> dict:
    """Loads configuration from config.json."""
    try:
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, 'r') as f:
                config_data = json.load(f)
                print(f"Loaded configuration from {CONFIG_FILE_PATH}")
                return config_data
        else:
            print(f"Warning: Configuration file not found at {CONFIG_FILE_PATH}. Using defaults.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {CONFIG_FILE_PATH}. Using defaults.")
    except Exception as e:
        print(f"An error occurred while loading config: {e}. Using defaults.")
    return {}

APP_CONFIG = load_config()

# Default values for token/char limits if not found in config
DEFAULT_MAX_TOKEN_THRESHOLD = 2000
DEFAULT_MAX_CHARS_LLM_FALLBACK = 15000
DEFAULT_TOKEN_TO_CHARS_RATIO = 1 # Heuristic: 1 token ~ 1 char (conservative, adjust as needed)
DEFAULT_STREAM_OUTPUT = False

class HTMLAnalyzer:
    """Analyzes HTML content from a URL using an LLM."""

    def __init__(self, model_name: str | None = None, api_key: str | None = None):
        """
        Initializes the HTMLAnalyzer.

        Args:
            model_name: Optional. The LLM model to use.
                        If None, tries to load from config.json, then uses a default.
            api_key: Optional API key. If None, LLMFactory will try to read from env variables
                     or potentially from the config.json if LLMFactory is extended to do so.
        """
        chosen_model_name = model_name
        if chosen_model_name is None:
            chosen_model_name = APP_CONFIG.get("html_analyzer_default_model", DEFAULT_MODEL)
            print(f"No model_name provided, using from config/default: {chosen_model_name}")
        else:
            print(f"Using provided model_name: {chosen_model_name}")

        self.stream_output = APP_CONFIG.get("html_analyzer_stream_output", DEFAULT_STREAM_OUTPUT)
        print(f"HTMLAnalyzer configured to stream output: {self.stream_output}")

        self.llm_client: BaseLLM = LLMFactory.create(
            model_name=chosen_model_name,
            api_key=api_key, # LLMFactory handles env var lookup
            stream=self.stream_output # Pass stream preference to factory
        )
        print(f"HTMLAnalyzer initialized with model: {self.llm_client.config.model_name}, Stream: {self.llm_client.config.stream_config.enabled}")

    def get_text_from_url(self, url: str) -> str | None:
        """
        Fetches HTML content from a URL and extracts clean text.

        Args:
            url: The URL of the webpage.

        Returns:
            The extracted text content as a string, or None if an error occurs.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            print(f"Fetching content from: {url}")
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()

            print("Parsing HTML content...")
            soup = BeautifulSoup(response.content, 'html.parser')

            for element_type in ["script", "style", "nav", "footer", "aside", "header", "form", "img", "svg"]:
                for element in soup.find_all(element_type):
                    element.decompose()

            main_content = soup.find('main') or \
                           soup.find('article') or \
                           soup.find(class_='content') or \
                           soup.find(id='content')

            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)

            text = ' '.join(text.split())
            text = '\n'.join([line.strip() for line in text.splitlines() if line.strip()])

            if not text:
                print("Warning: No text could be extracted from the page.")
                return None

            print(f"Successfully extracted {len(text)} characters.")
            return text
        except requests.exceptions.Timeout:
            print(f"Error: Timeout while fetching URL: {url}")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"Error: HTTP error while fetching URL: {url} - {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error: Could not fetch URL: {url} - {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during text extraction: {e}")
            return None

    def analyze_text_content(self, text_content: str, prompt_instruction: str | None = None) -> str | None | Iterator[str]:
        """
        Sends text content to the configured LLM for processing.

        Args:
            text_content: The text to be processed.
            prompt_instruction: Optional specific instruction for the LLM (e.g., "Summarize this text").
                                If None, a default analysis prompt is used.

        Returns:
            The processed text (e.g., summary or analysis) from LLM.
            If streaming is enabled, returns an iterator yielding text chunks.
            Returns None if an error occurs.
        """
        if not self.llm_client:
            print("Error: LLM client not initialized.")
            return None

        if prompt_instruction is None:
            prompt_instruction = "Analyze the following web content and tell me what it's about and its key points:"

        # Load configurations for token/char limits
        max_token_threshold = APP_CONFIG.get("html_analyzer_max_token_threshold", DEFAULT_MAX_TOKEN_THRESHOLD)
        max_chars_llm_fallback = APP_CONFIG.get("html_analyzer_max_chars_llm_fallback", DEFAULT_MAX_CHARS_LLM_FALLBACK)
        # Heuristic: Ratio to convert model's max_tokens to a character limit for input.
        token_to_chars_ratio = APP_CONFIG.get("html_analyzer_token_to_chars_ratio_heuristic", DEFAULT_TOKEN_TO_CHARS_RATIO)


        # Determine the maximum characters for LLM input based on model's configured max_tokens
        llm_configured_max_tokens = self.llm_client.config.max_tokens
        if llm_configured_max_tokens is not None and llm_configured_max_tokens > max_token_threshold:
            # If model's max_tokens is significant, use it with a ratio for a char limit.
            max_chars_llm = int(llm_configured_max_tokens * token_to_chars_ratio)
        else:
            # Fallback if model's max_tokens is not set, too small, or below threshold.
            max_chars_llm = max_chars_llm_fallback

        # Basic truncation if text_content + prompt_instruction exceeds calculated max_chars_llm
        # TODO: Implement more sophisticated text splitting/chunking for very large content.
        if len(text_content) + len(prompt_instruction) > max_chars_llm:
            available_chars = max_chars_llm - len(prompt_instruction) - 200 # Buffer for prompt structure & safety
            if available_chars < 100: # Ensure reasonable truncation
                print(f"Error: Prompt instruction is too long ({len(prompt_instruction)}) for max_chars_llm ({max_chars_llm}).")
                return None
            print(f"Warning: Content too long, truncating to fit ~{available_chars} chars for LLM input.")
            text_content = text_content[:available_chars]

        messages = [
            {'role': 'system', 'content': 'You are an AI assistant skilled at understanding and processing web content.'},
            {'role': 'user', 'content': f"{prompt_instruction}\n\n---\n\n{text_content}\n\n---\n\nAnalysis:"}
        ]

        print(f"Sending content to LLM: {self.llm_client.config.model_name}...")
        try:
            response_generator = self.llm_client.generate(messages=messages) # generate should handle stream internally

            if self.stream_output:
                print("Streaming response from LLM...")
                # Ensure the generator is not None before trying to iterate
                if response_generator is None:
                    print("Error: LLM returned None when expecting a stream.")
                    return None
                def stream_handler():
                    for chunk in response_generator:
                        yield chunk
                return stream_handler()
            else:
                # Non-streaming: response_generator is expected to be the full string or None
                if response_generator:
                    print("Successfully received non-streaming response from LLM.")
                    return str(response_generator) # Ensure it's a string
                else:
                    print("Error: LLM returned an empty or None response for non-streaming.")
                    return None
        except Exception as e:
            print(f"An exception occurred while calling the LLM: {e}")
            return None

    def get_and_analyze_url(self, url: str, prompt_instruction: str | None = None) -> str | None | Iterator[str]:
        """
        Fetches text from a URL and then analyzes it using the LLM.

        Args:
            url: The URL of the webpage.
            prompt_instruction: Optional specific instruction for the LLM.

        Returns:
            The LLM's analysis of the webpage content.
            If streaming is enabled, returns an iterator yielding text chunks.
            Returns None if an error occurs.
        """
        extracted_text = self.get_text_from_url(url)
        if extracted_text:
            return self.analyze_text_content(extracted_text, prompt_instruction)
        else:
            print("\nCould not extract text from the URL. Cannot proceed with LLM analysis.")
            return None