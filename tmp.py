# Please verify the exact model identifier for the 32B variant you intend to use
import requests
from bs4 import BeautifulSoup
import dashscope
import os

# --- Configuration ---
# IMPORTANT: Set your DashScope API Key as an environment variable
# or replace the placeholder below. Using environment variables is more secure.
# Example: export DASHSCOPE_API_KEY="your_actual_api_key"
DASHSCOPE_API_KEY = ""

# Specify the Qwen model you want to use.
# Examples: "qwen-turbo", "qwen-plus", "qwen-max", "qwen1.5-32b-chat"
# Please verify the exact model identifier for the 32B variant you intend to use
# from the DashScope documentation.
QWEN_MODEL_NAME = "qwen-plus" # Replace if needed

def get_text_from_url(url: str) -> str | None:
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
        response = requests.get(url, headers=headers, timeout=20) # Increased timeout
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        print("Parsing HTML content...")
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script, style, navigation, footer, and other non-essential elements
        for element_type in ["script", "style", "nav", "footer", "aside", "header", "form"]:
            for element in soup.find_all(element_type):
                element.decompose()

        # Attempt to find main content areas (common in many articles/blogs)
        main_content = soup.find('main') or \
                       soup.find('article') or \
                       soup.find(class_='content') or \
                       soup.find(id='content')

        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
        else:
            # Fallback to getting all text if specific content blocks aren't found
            text = soup.get_text(separator=' ', strip=True)

        # Basic cleaning: reduce multiple spaces/newlines to a single space/newline
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

def process_text_with_qwen(text_content: str, api_key: str, model_name: str) -> str | None:
    """
    Sends text content to the Qwen model via DashScope API for processing (e.g., summarization).

    Args:
        text_content: The text to be processed.
        api_key: Your DashScope API key.
        model_name: The Qwen model identifier.

    Returns:
        The processed text (e.g., summary) from Qwen, or None if an error occurs.
    """
    if not api_key or api_key == "YOUR_DASHSCOPE_API_KEY":
        print("Error: DashScope API Key is not configured. Please set it.")
        return None

    dashscope.api_key = api_key

    # You can customize this prompt for different tasks (summarization, Q&A, etc.)
    # For summarization:
    prompt_instruction = "Please provide a concise summary of the following web content:"
    # For general analysis (like your initial request "what does this tell"):
    # prompt_instruction = "Analyze the following web content and tell me what it's about and its key points:"


    # Ensure the text_content isn't excessively long to avoid overwhelming the prompt
    # This is a very basic truncation, more sophisticated methods might be needed for very long texts
    max_chars = 15000 # Adjust as needed based on model context window and typical content
    if len(text_content) > max_chars:
        print(f"Warning: Text content is very long ({len(text_content)} chars). Truncating to {max_chars} chars for API call.")
        text_content = text_content[:max_chars]

    messages = [
        {'role': 'system', 'content': 'You are an AI assistant skilled at understanding and summarizing web content.'},
        {'role': 'user', 'content': f"{prompt_instruction}\n\n---\n\n{text_content}\n\n---\n\nSummary/Analysis:"}
    ]

    print(f"Sending content to Qwen model: {model_name}...")
    try:
        response = dashscope.Generation.call(
            model=model_name,
            messages=messages,
            result_format='message',  # For message-style response
            # You can add other parameters like temperature, top_p, etc.
            # temperature=0.7,
        )

        if response.status_code == 200:
            # The exact path to content depends on the API version and result_format.
            # For result_format='message', it's typically in output.choices[0].message.content
            generated_text = response.output.choices[0]['message']['content']
            print("Successfully received response from Qwen.")
            return generated_text
        else:
            print(f"Error from Qwen API (HTTP Status {response.status_code}):")
            print(f"  Error Code: {response.code}")
            print(f"  Error Message: {response.message}")
            # print(f"  Request ID: {response.request_id}") # Useful for debugging with Aliyun support
            return None
    except Exception as e:
        print(f"An exception occurred while calling the Qwen API: {e}")
        return None

if __name__ == "__main__":
    if not DASHSCOPE_API_KEY or DASHSCOPE_API_KEY == "YOUR_DASHSCOPE_API_KEY":
        print("CRITICAL: DashScope API Key is not set or is still the placeholder.")
        print("Please set the DASHSCOPE_API_KEY environment variable or edit the script.")
        exit(1)

    webpage_url = input("Enter the URL of the webpage to process: ")

    if not webpage_url.startswith(('http://', 'https://')):
        print("Invalid URL. Please include http:// or https://")
        exit(1)

    extracted_text = get_text_from_url(webpage_url)

    if extracted_text:
        qwen_response = process_text_with_qwen(extracted_text, DASHSCOPE_API_KEY, QWEN_MODEL_NAME)
        if qwen_response:
            print("\n--- Response from Qwen (" + QWEN_MODEL_NAME + ") ---")
            print(qwen_response)
        else:
            print("\nFailed to get a response from Qwen.")
    else:
        print("\nCould not extract text from the URL. Cannot proceed with Qwen API call.")