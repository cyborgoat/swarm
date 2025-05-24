"""
Web Actions module: Integrates Selenium and LLM for interactive web automation.
Allows users to specify a URL, state their intention, and have an LLM
attempt to perform actions on the webpage using Selenium.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
import logging # Added for more structured logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

from swarm.llm import LLMFactory, BaseLLM

# Configuration
MAX_INTERACTION_RETRIES = 3
DEFAULT_LLM_CONFIG_NAME_FOR_WEB_ACTIONS = "web_actions" # Default config name from config.json
ENV_VAR_WEB_ACTIONS_LLM_CONFIG = "WEB_ACTIONS_LLM_CONFIG_NAME" # Env var to specify the config name

# Setup logging
logger = logging.getLogger(__name__)
# To see logs from this module, you can configure logging, e.g.:
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class WebActions:
    """
    Manages Selenium WebDriver and LLM interaction for web automation.
    """

    def __init__(self, llm_config_name: Optional[str] = None, headless: bool = True):
        """
        Initializes the WebActions class.

        Args:
            llm_config_name: The name of the LLM configuration (from config.json) to use.
                             If None, uses WEB_ACTIONS_LLM_CONFIG_NAME env var, then a default.
            headless: Whether to run the browser in headless mode.
        """
        logger.info("Initializing WebActions...")
        self.driver: Optional[webdriver.Chrome] = None # Type hint for clarity
        try:
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--log-level=3")
            options.add_experimental_option('excludeSwitches', ['enable-logging'])

            logger.info("Setting up ChromeDriver...")
            self.driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=options
            )
            logger.info("WebDriver initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing WebDriver: {e}", exc_info=True)
            if self.driver:
                self.driver.quit()
            raise

        # Determine LLM configuration
        chosen_llm_config_name = llm_config_name or \
                                 os.getenv(ENV_VAR_WEB_ACTIONS_LLM_CONFIG) or \
                                 DEFAULT_LLM_CONFIG_NAME_FOR_WEB_ACTIONS
        
        logger.info(f"Initializing LLM client with configuration: {chosen_llm_config_name}")
        try:
            # LLMFactory will try to load config.json from a default path if not already loaded
            # It will look for 'config.json' in the parent directory of the 'swarm' package.
            self.llm_client: BaseLLM = LLMFactory.create_from_config(chosen_llm_config_name)
            logger.info(f"LLM client created successfully using config: {chosen_llm_config_name}")
        except ValueError as ve:
            logger.error(f"Failed to create LLM from config '{chosen_llm_config_name}': {ve}", exc_info=True)
            # Fallback to a direct creation with a known safe default if config loading fails catastrophically
            # This is a last resort and indicates a setup issue with config.json or the factory.
            logger.warning("Falling back to direct LLM creation with default parameters (gpt-4o). Check config.json and LLMFactory setup.")
            try:
                self.llm_client: BaseLLM = LLMFactory.create(model_name="gpt-4o", temperature=0.5, max_tokens=2000)
            except Exception as e:
                logger.error(f"Critical error: Fallback LLM creation also failed: {e}", exc_info=True)
                self.close() # Close webdriver if open
                raise # Re-raise the critical error
        except Exception as e:
            logger.error(f"An unexpected error occurred during LLM client initialization: {e}", exc_info=True)
            self.close()
            raise
            
        logger.info("WebActions initialized.")

    def open_url(self, url: str):
        """Opens the specified URL in the browser."""
        if not self.driver: logger.warning("WebDriver not initialized."); return
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        logger.info(f"Navigating to URL: {url}")
        try:
            self.driver.get(url)
            logger.info(f"Successfully opened: {self.driver.title}")
        except TimeoutException:
            logger.warning(f"Timeout loading URL: {url}")
        except Exception as e:
            logger.error(f"Error opening URL {url}: {e}", exc_info=True)

    def get_simplified_dom(self) -> str:
        """
        Extracts a simplified representation of the current page's DOM,
        focusing on interactive elements.
        """
        if not self.driver: return "WebDriver not initialized."
        logger.info("Extracting simplified DOM...")
        elements_info = []
        # Prioritize input, button, a, select, textarea for interactivity
        # Then add other common tags for context
        tag_priority = ['input', 'button', 'a', 'select', 'textarea', 'label', 'form']
        other_tags = ['div', 'span', 'li', 'h1', 'h2', 'h3', 'p', 'img', 'nav', 'footer', 'main', 'article', 'section']
        
        processed_elements_count = 0
        max_elements_to_process = 200 # Limit to prevent overly long DOM strings

        for tag_name in tag_priority + other_tags:
            if processed_elements_count >= max_elements_to_process:
                logger.info(f"Reached max elements ({max_elements_to_process}) for simplified DOM.")
                break
            try:
                elements = self.driver.find_elements(By.TAG_NAME, tag_name)
                for i, element in enumerate(elements):
                    if processed_elements_count >= max_elements_to_process: break
                    try:
                        if not element.is_displayed(): continue
                        is_enabled = True
                        if tag_name in ['input', 'button', 'select', 'textarea']:
                            is_enabled = element.is_enabled()
                        if not is_enabled: continue

                        element_id = element.get_attribute('id')
                        element_name = element.get_attribute('name')
                        element_text = element.text.strip() if element.text else ""
                        element_type = element.get_attribute('type')
                        href = element.get_attribute('href') if tag_name == 'a' else None
                        aria_label = element.get_attribute('aria-label')
                        placeholder = element.get_attribute('placeholder')
                        role = element.get_attribute('role')
                        value = element.get_attribute('value') if tag_name in ['input', 'textarea'] else None
                        alt_text = element.get_attribute('alt') if tag_name == 'img' else None


                        # Create a more robust ref
                        ref_parts = [tag_name]
                        if element_id: ref_parts.append(f"id#{element_id}")
                        if element_name: ref_parts.append(f"name#{element_name}")
                        if element_type: ref_parts.append(f"type#{element_type}")
                        if role: ref_parts.append(f"role#{role}")
                        # Fallback to index if not enough unique identifiers
                        if len(ref_parts) == 1 or not (element_id or element_name) :
                           ref_parts.append(f"idx#{i}")
                        
                        llm_ref = "_".join(ref_parts)
                        
                        info = f"<{tag_name} ref='{llm_ref}'"
                        if element_id: info += f" id='{element_id}'"
                        if element_name: info += f" name='{element_name}'"
                        if element_type: info += f" type='{element_type}'"
                        if role: info += f" role='{role}'"
                        if href and href.strip() and href.strip() != '#': info += f" href='{href.strip()}'"
                        if aria_label: info += f" aria-label='{aria_label}'"
                        if placeholder: info += f" placeholder='{placeholder}'"
                        if value: info += f" value='{(value[:30] + '...') if len(value) > 30 else value}'" # Preview value
                        if alt_text: info += f" alt='{alt_text}'"
                        
                        text_content_parts = [t for t in [element_text, aria_label, placeholder, alt_text] if t]
                        text_content = " | ".join(text_content_parts)
                        
                        text_preview = (text_content[:70] + '...') if text_content and len(text_content) > 70 else text_content
                        
                        if text_preview: info += f">{text_preview.replace('<', '&lt;').replace('>', '&gt;')}</{tag_name}>"
                        else: info += " />"
                        elements_info.append(info)
                        processed_elements_count += 1
                    except StaleElementReferenceException: 
                        logger.debug(f"Stale element encountered for tag {tag_name}, skipping.")
                        continue
                    except Exception as el_ex: 
                        logger.debug(f"Error processing an element of tag {tag_name}: {el_ex}", exc_info=False)
                        continue 
            except Exception as find_ex: 
                logger.debug(f"Error finding elements for tag {tag_name}: {find_ex}", exc_info=False)
                continue 
        simplified_dom = "\n".join(elements_info)
        if not simplified_dom: return "No interactive elements found or page not loaded."
        # logger.info(f"Simplified DOM (first 500 chars):\n{simplified_dom[:500]}")
        return simplified_dom

    def plan_actions_with_llm(self, user_intention: str, dom_info: str) -> Optional[List[Dict[str, Any]]]:
        """
        Uses the LLM to understand user intention and plan Selenium actions.
        """
        prompt_parts = [
            "You are an expert web automation assistant. Based on the provided simplified DOM and the user's intention, ",
            "determine a sequence of Selenium actions to achieve the goal. Focus on using the 'ref' attribute of elements.",
            "Prioritize elements like inputs, buttons, and links that are clearly identifiable by their 'ref'.",
            "If multiple elements seem relevant, choose the one with the most specific 'ref' (e.g., with id or name).",
            "Available actions:",
            "1. type(ref, text): Type text into an input field, textarea, or select.",
            "   - ref: The 'ref' attribute of the element from the DOM (e.g., 'input_id#user_login').",
            "   - text: The text to type.",
            "2. click(ref): Click on a button, link, or other clickable element.",
            "   - ref: The 'ref' attribute of the element from the DOM.",
            "3. navigate(url): Navigate to a new URL. Use this if the intention is to go to a new page not linked in the current DOM.",
            "   - url: The full URL to navigate to.",
            "4. wait(seconds): Wait for a specified number of seconds (e.g., for dynamic content to load). Max 5 seconds.",
            "   - seconds: Number of seconds to wait.",
            "Current Page URL (for context): " + (self.driver.current_url if self.driver else "Unknown"),
            f"Simplified DOM:\n---\n{dom_info}\n---",
            f'User Intention: "{user_intention}"',
            "Output the actions as a JSON list of dictionaries. Each dictionary must have an \"action_type\" ",
            "(e.g., \"type\", \"click\", \"navigate\", \"wait\"), and other necessary parameters based on the action_type ",
            "(e.g., \"ref\", \"text\", \"url\", \"seconds\"). ",
            "Ensure the output is ONLY the JSON list, starting with [ and ending with ].",
            "Example for typing and clicking:",
            "```json",
            "[",
            "  {\"action_type\": \"type\", \"ref\": \"input_id#search_query_type#text\", \"text\": \"hello world\"},",
            "  {\"action_type\": \"click\", \"ref\": \"button_id#search_button\"}",
            "]",
            "```",
            "Example for navigation:",
            "```json",
            "[",
            "  {\"action_type\": \"navigate\", \"url\": \"https://www.example.com\"}",
            "]",
            "```",
            "Example for waiting:",
            "```json",
            "[",
            "  {\"action_type\": \"wait\", \"seconds\": 3}",
            "]",
            "```",
            "If the intention cannot be achieved with the available elements/actions, or if the DOM is empty, output an empty list [].",
            "Only use the 'ref' attributes provided in the simplified DOM to identify elements.",
            "If a 'ref' includes 'idx#', it means it's a less specific identifier, try to use refs with 'id#' or 'name#' if available for the same logical element.",
            "Be very careful to output valid JSON. The response MUST be a single JSON array."
        ]
        prompt = "\n".join(prompt_parts)

        logger.info("Sending request to LLM for action planning...")
        # logger.debug(f"LLM Prompt for planning:\n{prompt}") # Can be very verbose
        messages = [{"role": "user", "content": prompt}]
        response_text, json_str = None, None
        try:
            if not self.llm_client:
                logger.error("LLM client not available for planning actions.")
                return None
            response_text = self.llm_client.generate(messages)
            if not response_text: logger.warning("LLM returned empty response."); return None
            logger.info(f"LLM Raw Response for planning:\n{response_text}")
            
            # Extract JSON from markdown code block if present
            if "```json" in response_text:
                json_str = response_text.split("```json\n", 1)[1].split("\n```", 1)[0]
            elif response_text.strip().startswith("[") and response_text.strip().endswith("]"):
                 json_str = response_text.strip()
            else: 
                json_start = response_text.find('[')
                json_end = response_text.rfind(']')
                if json_start != -1 and json_end != -1 and json_start < json_end:
                    json_str = response_text[json_start : json_end + 1]
                else: 
                    logger.warning(f"Could not find valid JSON list in LLM response: {response_text}")
                    return None

            actions = json.loads(json_str)
            if not isinstance(actions, list): 
                logger.warning(f"LLM response is not valid JSON list after parsing: {json_str}")
                return None
            return actions
        except json.JSONDecodeError as e:
            err_msg = f"Error decoding LLM JSON. Error: {e}.\nLLM Raw Response: {response_text}\nAttempted to parse: {json_str}"
            logger.error(err_msg)
            return None
        except Exception as e:
            logger.error(f"Error in LLM action planning: {e}", exc_info=True)
            return None

    def _find_element_by_ref(self, ref: str) -> Optional[WebElement]:
        """Finds an element using the 'ref' string from the simplified DOM."""
        if not self.driver or not ref: return None
        logger.info(f"Attempting to find element by ref: '{ref}'")
        
        # Strategy: Prioritize ID, then Name, then fall back to more complex parsing if needed.
        # The ref format is tag_id#ID_val_type#TYPE_val_name#NAME_val_role#ROLE_val_idx#INDEX_val
        
        parts = ref.split('_')
        tag_name_from_ref = parts[0]

        id_val, name_val, type_val, role_val, idx_val = None, None, None, None, None

        for part in parts[1:]:
            if part.startswith("id#"): id_val = part.split("#",1)[1]
            elif part.startswith("name#"): name_val = part.split("#",1)[1]
            elif part.startswith("type#"): type_val = part.split("#",1)[1]
            elif part.startswith("role#"): role_val = part.split("#",1)[1]
            elif part.startswith("idx#"): idx_val = part.split("#",1)[1]
        
        element: Optional[WebElement] = None
        
        try:
            if id_val:
                try:
                    element = self.driver.find_element(By.ID, id_val)
                    # Verify tag name if we have it, to avoid ID clashes across different tags
                    if element and tag_name_from_ref and element.tag_name.lower() != tag_name_from_ref.lower():
                         logger.warning(f"Ref specified tag '{tag_name_from_ref}' but ID '{id_val}' matched a '{element.tag_name}'. Mismatch.")
                         # element = None # Decide if this should invalidate or just warn
                    if element: logger.info(f"Found element by ID: {id_val}"); #return element
                except NoSuchElementException:
                    logger.debug(f"Element with ID '{id_val}' not found by direct ID search.")
                    # Pass, try other methods if ID search fails or to confirm it's the right one

            if not element and name_val: # If not found by ID, try by name
                candidates = self.driver.find_elements(By.NAME, name_val)
                # Filter by tag, type, role if available
                for cand in candidates:
                    if tag_name_from_ref and cand.tag_name.lower() != tag_name_from_ref.lower(): continue
                    if type_val and cand.get_attribute('type') != type_val: continue
                    if role_val and cand.get_attribute('role') != role_val: continue
                    element = cand; break
                if element: logger.info(f"Found element by name: {name_val}, filtered by other attributes."); #return element
                else: logger.debug(f"No element matched name '{name_val}' after filtering or name not found.")


            if not element and idx_val is not None: # Fallback to tag and index
                try:
                    index = int(idx_val)
                    all_tags = self.driver.find_elements(By.TAG_NAME, tag_name_from_ref)
                    visible_tags = [el for el in all_tags if el.is_displayed()]
                    
                    # Try to further filter visible_tags by type or role if provided, before picking by index
                    filtered_visible_tags = []
                    if type_val or role_val:
                        for el_vis in visible_tags:
                            matches_criteria = True
                            if type_val and el_vis.get_attribute('type') != type_val: matches_criteria = False
                            if role_val and el_vis.get_attribute('role') != role_val: matches_criteria = False
                            if matches_criteria: filtered_visible_tags.append(el_vis)
                    else:
                        filtered_visible_tags = visible_tags

                    if 0 <= index < len(filtered_visible_tags):
                        element = filtered_visible_tags[index]
                        logger.info(f"Found element by tag '{tag_name_from_ref}' and index {index} from filtered list.")
                    else:
                        logger.warning(f"Index {index} out of bounds for visible '{tag_name_from_ref}' elements matching ref '{ref}'. Found {len(filtered_visible_tags)} such elements.")
                except ValueError:
                    logger.warning(f"Invalid index '{idx_val}' in ref '{ref}'.")
                except NoSuchElementException: # Should be caught by find_elements being empty
                    logger.debug(f"No elements found for tag '{tag_name_from_ref}' during index-based search for ref '{ref}'.")
            
            if element and element.is_displayed():
                if element.tag_name in ['input', 'button', 'select', 'textarea'] and not element.is_enabled():
                    logger.warning(f"Element '{ref}' found but not enabled."); return None
                logger.info(f"Successfully found and verified element for ref '{ref}' -> Tag: {element.tag_name}, ID: {element.id}")
                return element
            
            if element and not element.is_displayed(): logger.warning(f"Element '{ref}' found but not visible.")
            elif not element: logger.warning(f"Element with ref '{ref}' not found by any strategy.")
            return None

        except StaleElementReferenceException:
            logger.warning(f"Element with ref '{ref}' became stale during search.")
            return None
        except Exception as e:
            logger.error(f"Generic error finding element by ref '{ref}': {e}", exc_info=True)
            return None

    def execute_actions(self, actions: List[Dict[str, Any]]):
        """Executes a list of Selenium actions planned by the LLM."""
        if not self.driver: logger.warning("WebDriver not initialized."); return
        if not actions: logger.info("No actions to execute."); return

        for action_dict in actions: 
            action_type = action_dict.get("action_type")
            logger.info(f"Executing action: {action_dict}")

            try:
                if action_type == "type":
                    ref, text_to_type = action_dict.get("ref"), action_dict.get("text")
                    if ref is None or text_to_type is None: # Ensure both are present
                        logger.warning(f"Skipping 'type' action due to missing 'ref' or 'text': {action_dict}")
                        continue
                    element = self._find_element_by_ref(ref)
                    if element:
                        element.clear() 
                        element.send_keys(text_to_type)
                        logger.info(f"Typed '{text_to_type}' into element '{ref}'")
                    else:
                        logger.warning(f"Failed to type: Element with ref '{ref}' not found or text not provided.")

                elif action_type == "click":
                    ref = action_dict.get("ref")
                    if ref is None:
                        logger.warning(f"Skipping 'click' action due to missing 'ref': {action_dict}")
                        continue
                    element = self._find_element_by_ref(ref)
                    if element:
                        try:
                            element.click()
                            logger.info(f"Clicked element '{ref}'")
                        except Exception as click_err: # Catch errors during click, e.g. element not interactable
                             logger.error(f"Error clicking element '{ref}': {click_err}", exc_info=True)
                    else:
                        logger.warning(f"Failed to click: Element with ref '{ref}' not found.")

                elif action_type == "navigate":
                    url = action_dict.get("url")
                    if url:
                        self.open_url(url)
                    else:
                        logger.warning("Failed to navigate: URL not provided.")
                
                elif action_type == "wait":
                    seconds = action_dict.get("seconds")
                    if isinstance(seconds, (int, float)) and seconds > 0:
                        # Max wait time to prevent LLM from specifying too long waits
                        wait_time = min(float(seconds), 5.0) 
                        logger.info(f"Waiting for {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.warning(f"Invalid or missing 'seconds' for wait action: {seconds}. Waiting 1s by default.")
                        time.sleep(1)


                else:
                    logger.warning(f"Unknown action type: {action_type}")

                # Delay after action for page to potentially update
                # Consider making this configurable or more intelligent (e.g., wait for specific conditions)
                time.sleep(2) 

            except Exception as e: # Catch-all for errors during a single action's execution
                logger.error(f"Error executing action {action_dict}: {e}", exc_info=True)

    def interact(self):
        """Starts an interactive loop for web actions."""
        if not self.driver: logger.critical("WebDriver not initialized. Cannot start interaction."); return
        
        # Configure logging for the interactive session if not already done by user
        if not logging.getLogger().hasHandlers(): # Check if root logger has handlers
            logging.basicConfig(level=logging.INFO, 
                                format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S')
            logger.info("Basic logging configured for interactive session.")


        logger.info("\nWelcome to WebActions! (Type 'quit' to exit)")

        try:
            url = input("Enter URL: ").strip()
            if url.lower() == 'quit': return
            if not url: logger.info("No URL entered, exiting."); return
            self.open_url(url)

            retries = 0
            while True:
                if not self.driver: break 
                current_url = self.driver.current_url
                page_title = self.driver.title
                logger.info(f"\nCurrent page: '{page_title[:60]}' ({current_url[:70]})")

                intention = input("Your action/intention? ('refresh','back','forward','quit', or describe task): ").strip()

                if intention.lower() == 'quit': break
                if intention.lower() == 'refresh': self.driver.refresh(); logger.info("Page refreshed."); continue
                if intention.lower() == 'back': self.driver.back(); logger.info("Navigated back."); continue
                if intention.lower() == 'forward': self.driver.forward(); logger.info("Navigated forward."); continue
                if not intention: logger.info("No intention provided, try again."); continue


                dom_before_action = self.get_simplified_dom()
                if "No interactive elements" in dom_before_action and not self.driver.page_source.strip():
                    logger.warning("Page appears to be empty or not loaded correctly.")
                    # Maybe ask user to try navigating again or check URL
                    continue

                actions = self.plan_actions_with_llm(intention, dom_before_action)

                if actions:
                    logger.info(f"LLM planned actions: {actions}")
                    self.execute_actions(actions)
                    retries = 0 # Reset retries on successful planning
                else:
                    logger.warning("LLM could not plan actions or planning failed.")
                    retries += 1
                    if retries >= MAX_INTERACTION_RETRIES:
                        logger.error(f"Max retries ({MAX_INTERACTION_RETRIES}) reached for intention: {intention}. Please try a different approach or check the page.")
                        retries = 0 # Reset for next user intention
                
                time.sleep(1) 

        except KeyboardInterrupt:
            logger.info("\nUser quit interaction.")
        except Exception as e:
            logger.error(f"An error occurred during interaction: {e}", exc_info=True)
        finally:
            self.close()

    def close(self):
        """Closes the browser and quits the WebDriver."""
        if self.driver:
            logger.info("Closing WebDriver...")
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully.")
            except Exception as e:
                logger.error(f"Error during WebDriver quit: {e}", exc_info=True)
            self.driver = None


if __name__ == '__main__':
    # Setup basic logging for the script execution if run directly
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    from dotenv import load_dotenv
    # Construct path to .env.local relative to this script's location
    # __file__ is swarm/web_broswer/web_actions.py
    # want <project_root>/.env.local
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env.local")
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path, verbose=True)
        logger.info(f"Loaded environment variables from: {env_path}")
    else:
        logger.info(f".env.local file not found at {env_path}, relying on globally set environment variables for API keys if needed.")

    actor = None
    try:
        # Example: Override headless mode for debugging when running script directly
        # You can also set WEB_ACTIONS_LLM_CONFIG_NAME in your .env.local or environment
        # to use a specific LLM config, e.g., WEB_ACTIONS_LLM_CONFIG_NAME="deepseek_coder_streaming"
        actor = WebActions(headless=False) 
        actor.interact()
    except Exception as e:
        # Logger already active, so this will be captured
        logger.critical(f"A critical error occurred in main execution: {e}", exc_info=True)
    finally:
        # Ensure WebDriver is closed even if WebActions.close() was already called or failed
        if actor and actor.driver:
            logger.info("Final attempt to close WebDriver from __main__ finally block.")
            try:
                actor.driver.quit()
            except Exception as e_quit:
                 logger.error(f"Error in final attempt to close WebDriver: {e_quit}", exc_info=True)