"""
HTML Analyzer using web scraping and LLM for content processing.

This module fetches content from a URL, cleans it, and uses an LLM (Qwen model via LLMFactory)
to analyze or summarize the text.
"""

import requests
from bs4 import BeautifulSoup
import os
import json # For loading config.json
from typing import Iterator, Optional # Added Optional

# Import LLMFactory from the swarm.llm module
from swarm.llm import LLMFactory, BaseLLM, StreamConfig # Imported StreamConfig

# Define the path to the config file, assuming it's in the project root
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config.json")
DEFAULT_MODEL = "qwen-turbo" # Fallback if config.json or specific entry is missing
DEFAULT_PROMPT_INSTRUCTION = "Analyze the following web content and tell me what it's about and its key points:"

# Define the path to the agent_config.json file
AGENT_CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agent_config.json")

# --- Default values for HTMLAnalyzer if not found in agent_config.json ---
# These are fallback values if agent_config.json is missing or html_analyzer section is incomplete.
FALLBACK_HTML_ANALYZER_LLM_CONFIG_NAME = "default_qwen_streaming" # Fallback LLM config name
FALLBACK_HTML_ANALYZER_PROMPT = "Analyze the following web content and tell me what it's about and its key points:"
FALLBACK_HTML_ANALYZER_MAX_TOKEN_THRESHOLD = 2000
FALLBACK_HTML_ANALYZER_MAX_CHARS_LLM_FALLBACK = 15000
FALLBACK_HTML_ANALYZER_TOKEN_TO_CHARS_RATIO = 1
FALLBACK_HTML_ANALYZER_STREAM_OUTPUT = False # Default for streaming if not in config

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

def load_agent_config() -> dict:
    """Loads agent configuration from agent_config.json."""
    try:
        if os.path.exists(AGENT_CONFIG_FILE_PATH):
            with open(AGENT_CONFIG_FILE_PATH, 'r') as f:
                config_data = json.load(f)
                print(f"Loaded agent configuration from {AGENT_CONFIG_FILE_PATH}")
                return config_data
        else:
            print(f"Warning: Agent configuration file not found at {AGENT_CONFIG_FILE_PATH}. Using fallbacks.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {AGENT_CONFIG_FILE_PATH}. Using fallbacks.")
    except Exception as e:
        print(f"An error occurred while loading agent config: {e}. Using fallbacks.")
    return {} # Return empty dict on error, fallbacks will be used

AGENT_SETTINGS = load_agent_config()
HTML_ANALYZER_SETTINGS = AGENT_SETTINGS.get("html_analyzer", {})

class HTMLAnalyzer:
    """Analyzes HTML content from a URL using an LLM."""

    def __init__(self, llm_config_name: Optional[str] = None, **llm_override_kwargs):
        """
        Initializes the HTMLAnalyzer.

        Args:
            llm_config_name: Optional. The name of the LLM configuration (from llm_config.json) to use.
                             If None, uses the default from agent_config.json, then a hardcoded fallback.
            **llm_override_kwargs: Optional keyword arguments to override specific settings within the chosen LLM configuration.
        """
        chosen_llm_config_name = llm_config_name or \
                                 HTML_ANALYZER_SETTINGS.get("default_llm_config_name", FALLBACK_HTML_ANALYZER_LLM_CONFIG_NAME)
        
        print(f"HTMLAnalyzer: Using LLM configuration named: {chosen_llm_config_name}")

        # Other HTMLAnalyzer specific settings from agent_config.json or fallbacks
        self.default_prompt_instruction = HTML_ANALYZER_SETTINGS.get("default_prompt_instruction", FALLBACK_HTML_ANALYZER_PROMPT)
        self.max_token_threshold = HTML_ANALYZER_SETTINGS.get("max_token_threshold", FALLBACK_HTML_ANALYZER_MAX_TOKEN_THRESHOLD)
        self.max_chars_llm_fallback = HTML_ANALYZER_SETTINGS.get("max_chars_llm_fallback", FALLBACK_HTML_ANALYZER_MAX_CHARS_LLM_FALLBACK)
        self.token_to_chars_ratio_heuristic = HTML_ANALYZER_SETTINGS.get("token_to_chars_ratio_heuristic", FALLBACK_HTML_ANALYZER_TOKEN_TO_CHARS_RATIO)
        # Stream preference can be part of the LLM config itself, but can also be an agent-level override if needed.
        # For now, we assume stream setting is primarily managed by the LLM configuration from llm_config.json
        # However, if agent_config.json specifies `stream_output` for html_analyzer, that implies an override intention for the chosen config.
        # The llm_override_kwargs can be used for this: e.g. HTMLAnalyzer(stream_config={'enabled': True})

        # If agent_config.json has a specific stream_output for html_analyzer, pass it as an override
        agent_stream_pref = HTML_ANALYZER_SETTINGS.get("stream_output")
        final_llm_kwargs = llm_override_kwargs.copy()
        if agent_stream_pref is not None and "stream_config" not in final_llm_kwargs:
            # Only apply if not already specified in direct overrides
            # This sets the stream_config at the top level of overrides for LLMFactory
            final_llm_kwargs["stream_config"] = StreamConfig(enabled=agent_stream_pref)
        elif agent_stream_pref is not None and "stream_config" in final_llm_kwargs and isinstance(final_llm_kwargs["stream_config"], dict):
            # If stream_config is already a dict in overrides, merge the enabled flag
            final_llm_kwargs["stream_config"].setdefault("enabled", agent_stream_pref)

        try:
            self.llm_client: BaseLLM = LLMFactory.create_from_config(
                config_name=chosen_llm_config_name,
                **final_llm_kwargs # Pass overrides here
            )
            # The actual stream setting will be from the LLM's config after factory processing
            self.stream_output = self.llm_client.config.stream_config.enabled
            print(f"HTMLAnalyzer initialized. LLM: {self.llm_client.config.model_name}, Effective Stream: {self.stream_output}")

        except ValueError as ve:
            print(f"HTMLAnalyzer: Error creating LLM from config '{chosen_llm_config_name}': {ve}. Check llm_config.json and agent_config.json.")
            # Fallback to direct creation with a known safe default
            print(f"HTMLAnalyzer: Falling back to direct LLM creation with model '{FALLBACK_HTML_ANALYZER_LLM_CONFIG_NAME}' (or its underlying model if it's a config name). ")
            try:
                # Try to see if FALLBACK_HTML_ANALYZER_LLM_CONFIG_NAME is a config name itself
                self.llm_client = LLMFactory.create_from_config(FALLBACK_HTML_ANALYZER_LLM_CONFIG_NAME, **final_llm_kwargs)
            except ValueError:
                 # If not a config name, assume it might be a raw model name (less ideal)
                 print(f"HTMLAnalyzer: Fallback LLM config '{FALLBACK_HTML_ANALYZER_LLM_CONFIG_NAME}' not found. Attempting direct creation with it as model name.")
                 self.llm_client = LLMFactory.create(model_name=FALLBACK_HTML_ANALYZER_LLM_CONFIG_NAME, stream=FALLBACK_HTML_ANALYZER_STREAM_OUTPUT, **final_llm_kwargs)
            self.stream_output = self.llm_client.config.stream_config.enabled # Update stream status from fallback client
            print(f"HTMLAnalyzer initialized with fallback LLM. Model: {self.llm_client.config.model_name}, Effective Stream: {self.stream_output}")
        except Exception as e:
            print(f"HTMLAnalyzer: Critical error during LLM client initialization: {e}")
            raise # Re-raise critical errors

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

    def analyze_html_content(self, html_content: str, prompt_instruction: Optional[str] = None) -> str | None | Iterator[str]:
        """
        Parses provided HTML content, extracts clean text, and then sends it to the LLM for processing.
        This method is intended for use when HTML content is already available (e.g., from Selenium).

        Args:
            html_content: The raw HTML content string.
            prompt_instruction: Optional specific instruction for the LLM.

        Returns:
            The LLM's analysis of the webpage content.
            If streaming is enabled, returns an iterator yielding text chunks.
            Returns None if an error occurs or no text is extracted.
        """
        if not html_content:
            print("HTMLAnalyzer.analyze_html_content: Error - No HTML content provided.")
            return None

        print("HTMLAnalyzer.analyze_html_content: Parsing provided HTML content...")
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Same decomposition logic as in get_text_from_url
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
                print("HTMLAnalyzer.analyze_html_content: Warning - No text could be extracted from the provided HTML.")
                return None

            print(f"HTMLAnalyzer.analyze_html_content: Successfully extracted {len(text)} characters from provided HTML.")
            return self.analyze_text_content(text, prompt_instruction)
        except Exception as e:
            print(f"HTMLAnalyzer.analyze_html_content: An unexpected error occurred during HTML parsing or text extraction: {e}")
            return None

    def analyze_text_content(self, text_content: str, prompt_instruction: Optional[str] = None) -> str | None | Iterator[str]:
        """
        Sends text content to the configured LLM for processing.

        Args:
            text_content: The text to be processed.
            prompt_instruction: Optional specific instruction for the LLM (e.g., "Summarize this text").
                                If None, a default analysis prompt from agent_config is used.

        Returns:
            The processed text (e.g., summary or analysis) from LLM.
            If streaming is enabled, returns an iterator yielding text chunks.
            Returns None if an error occurs.
        """
        if not self.llm_client:
            print("Error: LLM client not initialized.")
            return None

        # Determine which instruction is active for length calculation and for the prompt logic
        active_instruction = prompt_instruction if prompt_instruction else self.default_prompt_instruction

        # Use configured limits
        max_token_threshold = self.max_token_threshold
        max_chars_llm_fallback = self.max_chars_llm_fallback
        token_to_chars_ratio = self.token_to_chars_ratio_heuristic

        llm_configured_max_tokens = self.llm_client.config.max_tokens
        # Prefer LLM's configured max_tokens if it's higher than agent's threshold, but still respect agent's threshold as a cap
        if llm_configured_max_tokens is not None and llm_configured_max_tokens > 0: # Ensure it's a positive number
            # Effective max tokens for the LLM call, considering both its own limit and the agent's general threshold
            # We want to use the smaller of the LLM's capacity or a potentially larger threshold if agent allows more
            # Actually, max_token_threshold is the agent's desired cap for *this* task, not a general LLM cap override.
            # So, we should use the agent's max_token_threshold to calculate max_chars_llm, and the LLM will respect its own internal max_tokens if it's smaller.
            # The primary goal here is to not send *too much* text to the LLM based on agent settings.
            pass # max_token_threshold from agent config is the one we use for char calculation.
        
        # Calculate max characters for LLM input based on the agent's token threshold setting for this task
        max_chars_llm = int(max_token_threshold * token_to_chars_ratio) 
        # If the LLM itself has a smaller max_tokens that would result in fewer chars, that's handled by the LLM client or API.
        # This calculation is primarily for *our* truncation before sending.

        if len(text_content) + len(active_instruction) > max_chars_llm:
            # Calculate available characters for text_content, reserving space for instruction and some buffer (e.g., for newlines, "Text:", "Question:")
            # The buffer of 200 was arbitrary; let's make it more related to the prompt structure itself.
            # Approximate length of prompt boilerplate (e.g., "Based on...Text:...Question:...Answer:")
            boilerplate_char_estimate = 100 
            available_chars = max_chars_llm - len(active_instruction) - boilerplate_char_estimate
            if available_chars < 100: # If very little space left for actual content
                print(f"Error: Prompt instruction ('{active_instruction[:50]}...', {len(active_instruction)} chars) is too long for configured max_chars_llm ({max_chars_llm}) with boilerplate.")
                return None
            print(f"Warning: Content too long ({len(text_content)} chars), truncating to fit ~{available_chars} chars for LLM input (instruction: {len(active_instruction)} chars, max_chars_llm: {max_chars_llm}).")
            text_content = text_content[:available_chars]

        system_message = "You are an AI assistant skilled at understanding and processing web content. Your primary task is to answer specific questions based on the provided text. If a specific question is not provided, you should summarize the text or follow the given instruction."
        
        user_message_content = ""
        if prompt_instruction: # A specific question or instruction was passed
            user_message_content = (
                f"Based on the following text, please answer the question or follow the instruction accurately and concisely.\n\n"
                f"Text:\n{text_content}\n\n"
                f"Question/Instruction: {prompt_instruction}\n\n"
                f"Answer/Response:"
            )
        else: # No specific question, use default summarization/analysis prompt
            user_message_content = (
                f"{self.default_prompt_instruction}\n\n"
                f"---\n\n"
                f"{text_content}\n\n"
                f"---\n\n"
                f"Summary/Analysis:"
            )

        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': user_message_content}
        ]

        print(f"HTMLAnalyzer: Sending content to LLM: {self.llm_client.config.model_name} (Stream: {self.stream_output})...")
        try:
            # LLMFactory's create_from_config would have set up the LLMConfig with stream settings.
            # The generate method of the client should respect this config.
            response = self.llm_client.generate(messages=messages)

            if self.stream_output:
                # print("HTMLAnalyzer: Streaming response from LLM...")
                if response is None:
                    print("Error: LLM returned None when expecting a stream.")
                    return None
                # Ensure it's an iterator, not a string if stream_output is true
                if isinstance(response, str):
                    print("Error: LLM returned a string but stream_output is True. Check LLM client stream handling.")
                    # As a fallback, yield the string as a single chunk
                    def single_chunk_stream(): yield response
                    return single_chunk_stream()
                return response # Expected to be an iterator
            else:
                if response:
                    # print("HTMLAnalyzer: Successfully received non-streaming response from LLM.")
                    return str(response) 
                else:
                    print("Error: LLM returned an empty or None response for non-streaming.")
                    return None
        except Exception as e:
            print(f"HTMLAnalyzer: An exception occurred while calling the LLM: {e}")
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