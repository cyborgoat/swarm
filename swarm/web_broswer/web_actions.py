"""
Web Actions module: Integrates Selenium and LLM for interactive web automation.
Allows users to specify a URL, state their intention, and have an LLM
attempt to perform actions on the webpage using Selenium.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Iterator
import logging # Added for more structured logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

from swarm.llm import LLMFactory, BaseLLM, StreamConfig # Added StreamConfig for type hints
from .html_analyzer import HTMLAnalyzer # Import HTMLAnalyzer
from .action_planner import ActionPlanner # New import
from .selenium_executor import SeleniumExecutor # New import

# Configuration
# MAX_INTERACTION_RETRIES = 3 # Will be loaded from agent_config.json
# DEFAULT_LLM_CONFIG_NAME_FOR_WEB_ACTIONS = "web_actions" # Will be loaded from agent_config.json
ENV_VAR_WEB_ACTIONS_LLM_CONFIG = "WEB_ACTIONS_LLM_CONFIG_NAME" # Env var to specify the config name

# Setup logging
logger = logging.getLogger(__name__)
# To see logs from this module, you can configure logging, e.g.:
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Load Agent Configuration ---
AGENT_CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agent_config.json")

def load_web_actions_specific_config() -> dict:
    """Loads the 'web_actions' section from agent_config.json."""
    try:
        if os.path.exists(AGENT_CONFIG_FILE_PATH):
            with open(AGENT_CONFIG_FILE_PATH, 'r') as f:
                full_config = json.load(f)
                web_actions_settings = full_config.get("web_actions", {})
                if web_actions_settings:
                    print(f"Loaded 'web_actions' settings from {AGENT_CONFIG_FILE_PATH}")
                else:
                    print(f"Warning: 'web_actions' section not found in {AGENT_CONFIG_FILE_PATH}. Using fallbacks.")
                return web_actions_settings
        else:
            print(f"Warning: Agent configuration file not found at {AGENT_CONFIG_FILE_PATH}. Using fallbacks for WebActions.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {AGENT_CONFIG_FILE_PATH}. Using fallbacks for WebActions.")
    except Exception as e:
        print(f"An error occurred while loading agent config for WebActions: {e}. Using fallbacks.")
    return {} # Return empty dict on error, fallbacks will be used

WEB_ACTIONS_SETTINGS = load_web_actions_specific_config()

# --- Fallback values for WebActions if not in agent_config.json or section is incomplete ---
# FALLBACK_WEB_ACTIONS_LLM_CONFIG_NAME = "web_actions_openai_gpt4o" # Removed: No hardcoded fallback for LLM config name
FALLBACK_WEB_ACTIONS_MAX_RETRIES = 3
FALLBACK_DOM_MAX_ELEMENTS = 150 # Default max elements for simplified DOM
FALLBACK_DOM_TEXT_PREVIEW_LENGTH = 60 # Default preview length for text in DOM

class WebActions:
    """
    Manages Selenium WebDriver and LLM interaction for web automation.
    """

    def __init__(self, llm_config_name: Optional[str] = None, headless: bool = True, **llm_override_kwargs):
        """
        Initializes the WebActions class.

        Args:
            llm_config_name: The name of the LLM configuration (from llm_config.json) to use.
                             If None, uses WEB_ACTIONS_LLM_CONFIG_NAME env var, then default from agent_config.json.
                             This configuration must exist in llm_config.json.
            headless: Whether to run the browser in headless mode.
            **llm_override_kwargs: Optional keyword arguments to override specific settings within the chosen LLM configuration.
        """
        logger.info("Initializing WebActions...")
        self.driver: Optional[webdriver.Chrome] = None
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

        # Determine LLM configuration name for the planner
        if llm_config_name:
            chosen_llm_config_name_for_planner = llm_config_name
        elif os.getenv(ENV_VAR_WEB_ACTIONS_LLM_CONFIG):
            chosen_llm_config_name_for_planner = os.getenv(ENV_VAR_WEB_ACTIONS_LLM_CONFIG)
        else:
            chosen_llm_config_name_for_planner = WEB_ACTIONS_SETTINGS.get("default_llm_config_name")

        if not chosen_llm_config_name_for_planner:
            err_msg = "WebActions: LLM configuration name for ActionPlanner not provided. Please specify via argument, environment variable, or in agent_config.json."
            logger.critical(err_msg)
            self.close() 
            raise ValueError(err_msg)
        
        self.max_interaction_retries = WEB_ACTIONS_SETTINGS.get("max_interaction_retries", FALLBACK_WEB_ACTIONS_MAX_RETRIES)
        self.dom_max_elements = WEB_ACTIONS_SETTINGS.get("dom_max_elements", FALLBACK_DOM_MAX_ELEMENTS)
        self.dom_text_preview_length = WEB_ACTIONS_SETTINGS.get("dom_text_preview_length", FALLBACK_DOM_TEXT_PREVIEW_LENGTH)

        logger.info(f"WebActions: LLM for ActionPlanner: {chosen_llm_config_name_for_planner}, Max Retries: {self.max_interaction_retries}, DOM Max Elements: {self.dom_max_elements}, DOM Text Preview Length: {self.dom_text_preview_length}")
        
        planning_llm_overrides = llm_override_kwargs.copy()
        planning_llm_overrides["stream_config"] = StreamConfig(enabled=False)

        try:
            # Initialize LLM client specifically for the ActionPlanner
            planner_llm_client: BaseLLM = LLMFactory.create_from_config(
                config_name=chosen_llm_config_name_for_planner, 
                **planning_llm_overrides
            )
            logger.info(f"LLM client for ActionPlanner created successfully using config: {chosen_llm_config_name_for_planner} (streaming explicitly disabled for planning)")
            self.action_planner = ActionPlanner(planner_llm_client)
        except ValueError as ve: 
            err_msg = f"WebActions: Failed to create LLM for ActionPlanner from config '{chosen_llm_config_name_for_planner}': {ve}."
            logger.critical(err_msg, exc_info=True)
            self.close()
            raise ValueError(err_msg) from ve
        except Exception as e: 
            err_msg = f"WebActions: Unexpected error initializing LLM/ActionPlanner with config '{chosen_llm_config_name_for_planner}': {e}"
            logger.critical(err_msg, exc_info=True)
            self.close()
            raise Exception(err_msg) from e
            
        # Initialize HTMLAnalyzer
        try:
            logger.info("WebActions: Initializing internal HTMLAnalyzer...")
            self.html_analyzer = HTMLAnalyzer() 
            logger.info("WebActions: Internal HTMLAnalyzer initialized successfully.")
        except Exception as e_analyzer:
            logger.error(f"WebActions: Failed to initialize internal HTMLAnalyzer: {e_analyzer}", exc_info=True)
            logger.warning("WebActions: HTMLAnalyzer could not be initialized. Content analysis capabilities will be unavailable.")
            self.html_analyzer = None

        # Initialize SeleniumExecutor
        if self.driver:
            self.selenium_executor = SeleniumExecutor(self.driver)
        else:
            # This case should ideally not be reached if driver initialization above succeeded or raised
            logger.critical("WebActions: WebDriver not available for SeleniumExecutor initialization.")
            raise Exception("WebActions: WebDriver not available for SeleniumExecutor initialization.")

        logger.info("WebActions initialized with ActionPlanner, SeleniumExecutor, and HTMLAnalyzer.")

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
        # Use configured max_elements_to_process
        # max_elements_to_process = 200 # Limit to prevent overly long DOM strings
        # Derived lengths for attribute text previews to be more concise
        attribute_value_preview_length = max(15, self.dom_text_preview_length // 3)
        value_attr_preview_length = max(20, self.dom_text_preview_length // 2)


        for tag_name in tag_priority + other_tags:
            if processed_elements_count >= self.dom_max_elements: # Use configured limit
                logger.info(f"Reached max elements ({self.dom_max_elements}) for simplified DOM.")
                break
            
            try:
                all_elements_for_tag = self.driver.find_elements(By.TAG_NAME, tag_name)
            except Exception as find_ex:
                logger.debug(f"Error finding elements for tag {tag_name}: {find_ex}", exc_info=False)
                continue

            visible_idx_for_llm_this_tag = 0 # Reset for each tag type

            for element in all_elements_for_tag:
                if processed_elements_count >= self.dom_max_elements: 
                    # Need to break outer loop too if global limit reached mid-tag processing
                    # This break only breaks the inner loop. Consider a flag or restructuring if this becomes an issue.
                    break 
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
                    
                    # If no strong identifiers, use the visible_idx_for_llm_this_tag for this tag
                    if len(ref_parts) == 1 or not (element_id or element_name) :
                       ref_parts.append(f"idx#{visible_idx_for_llm_this_tag}")
                    
                    llm_ref = "_".join(ref_parts)
                    
                    info = f"<{tag_name} ref='{llm_ref}'"
                    if element_id: info += f" id='{element_id}'"
                    if element_name: info += f" name='{element_name}'"
                    if element_type: info += f" type='{element_type}'"
                    if role: info += f" role='{role}'"
                    if href and href.strip() and href.strip() != '#': info += f" href='{href.strip()}'"
                    
                    # Add other attributes with truncation
                    if aria_label: info += f" aria-label='{(aria_label[:attribute_value_preview_length] + '...') if len(aria_label) > attribute_value_preview_length else aria_label}'"
                    if placeholder: info += f" placeholder='{(placeholder[:attribute_value_preview_length] + '...') if len(placeholder) > attribute_value_preview_length else placeholder}'"
                    if value: info += f" value='{(value[:value_attr_preview_length] + '...') if len(value) > value_attr_preview_length else value}'"
                    if alt_text: info += f" alt='{(alt_text[:attribute_value_preview_length] + '...') if len(alt_text) > attribute_value_preview_length else alt_text}'"
                    
                    text_content_parts = [t for t in [element_text, aria_label, placeholder, alt_text] if t]
                    text_content = " | ".join(text_content_parts)
                    
                    # Use configured dom_text_preview_length for the main text node
                    text_preview = (text_content[:self.dom_text_preview_length] + '...') if text_content and len(text_content) > self.dom_text_preview_length else text_content
                    
                    if text_preview: info += f">{text_preview.replace('<', '&lt;').replace('>', '&gt;')}</{tag_name}>"
                    else: info += " />"
                    elements_info.append(info)
                    processed_elements_count += 1
                    visible_idx_for_llm_this_tag += 1 # Increment for the next valid element of this tag
                    
                except StaleElementReferenceException: 
                    logger.debug(f"Stale element encountered for tag {tag_name}, skipping.")
                    continue
                except Exception as el_ex: 
                    logger.debug(f"Error processing an element of tag {tag_name}: {el_ex}", exc_info=False)
                    continue 
        simplified_dom = "\n".join(elements_info)
        if not simplified_dom: return "No interactive elements found or page not loaded."
        # logger.info(f"Simplified DOM (first 500 chars):\n{simplified_dom[:500]}")
        return simplified_dom

    def execute_actions(self, actions: List[Dict[str, Any]]):
        """Executes a list of actions planned by the ActionPlanner."""
        if not self.driver: 
            logger.warning("WebDriver not initialized. Cannot execute actions.")
            return
        if not actions: 
            logger.info("No actions to execute.")
            return

        for action_dict in actions: 
            action_type = action_dict.get("action_type")
            logger.info(f"WebActions: Processing action: {action_dict}")

            if action_type in ["type", "click", "navigate", "wait"]:
                if self.selenium_executor:
                    self.selenium_executor.execute_selenium_action(action_dict)
                else:
                    logger.error("SeleniumExecutor not available. Cannot execute browser action.")
            elif action_type == "analyze_page_content":
                question = action_dict.get("question_for_analyzer")
                if not question:
                    logger.warning("Skipping 'analyze_page_content' action: 'question_for_analyzer' not provided.")
                    continue
                if not self.html_analyzer:
                    logger.error("HTMLAnalyzer not available. Cannot execute 'analyze_page_content'.")
                    print("SYSTEM: Sorry, I cannot analyze the page content right now as the analyzer module is not working.")
                    continue
                
                current_page_url = self.driver.current_url
                page_html_content = self.driver.page_source

                if not page_html_content:
                    logger.warning("Could not get page source from the browser. Cannot analyze content.")
                    print("SYSTEM: Could not retrieve current page content for analysis.")
                    continue

                logger.info(f"Using HTMLAnalyzer to process content from current page: '{current_page_url}' with question: '{question}'")
                print(f"SYSTEM: Analyzing current page content with HTMLAnalyzer for: \"{question}\" (this may take a moment)...")
                
                analysis_result = self.html_analyzer.analyze_html_content(page_html_content, prompt_instruction=question)
                
                print("\n--- HTMLAnalyzer Response ---")
                if hasattr(analysis_result, '__iter__') and not isinstance(analysis_result, str):
                    for chunk in analysis_result: # type: ignore
                        print(chunk, end="", flush=True)
                    print("\n-----------------------------\n")
                elif analysis_result:
                    print(str(analysis_result))
                    print("-----------------------------\n")
                else:
                    print("HTMLAnalyzer returned no information or an error occurred.")
                    logger.warning("HTMLAnalyzer returned no information or an error for 'analyze_page_content'.")
            elif action_type == "list_tabs":
                if self.selenium_executor:
                    tabs = self.selenium_executor.list_open_tabs()
                    if tabs:
                        print("\n--- Open Tabs ---")
                        for i, tab in enumerate(tabs):
                            active_marker = "*" if tab["handle"] == self.driver.current_window_handle else " "
                            print(f"  {active_marker} [{i}] Handle: {tab['handle']}, Title: '{tab['title'][:60]}', URL: '{tab['url'][:70]}'")
                        print("-----------------")
                    else:
                        print("SYSTEM: No tabs found or error listing tabs.")
                else:
                    logger.error("SeleniumExecutor not available. Cannot list tabs.")
                    print("SYSTEM: Unable to list tabs at the moment.")
            elif action_type == "switch_tab":
                target = action_dict.get("target")
                if not target:
                    logger.warning("Skipping 'switch_tab' action: 'target' not provided.")
                    print("SYSTEM: Please specify a target for switching tabs (e.g., handle, title, or URL part).")
                    continue
                if self.selenium_executor:
                    success = self.selenium_executor.switch_to_tab(target)
                    if success:
                        print(f"SYSTEM: Switched to tab related to '{target}'. Current page: '{self.driver.title}'")
                    else:
                        print(f"SYSTEM: Could not switch to a tab related to '{target}'.")
                else:
                    logger.error("SeleniumExecutor not available. Cannot switch tabs.")
                    print("SYSTEM: Unable to switch tabs at the moment.")
            else:
                logger.warning(f"WebActions: Unknown action type: {action_type}")

            # Delay after action for page to potentially update
            # Consider making this configurable or more intelligent
            if action_type not in ["analyze_page_content"] : # No need to sleep after analysis
                 time.sleep(2) 

    def interact(self):
        """Starts an interactive loop for web actions."""
        if not self.driver: logger.critical("WebDriver not initialized. Cannot start interaction."); return
        
        if not logging.getLogger().hasHandlers():
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
                    continue

                # Use the ActionPlanner to get actions
                if self.action_planner:
                    actions = self.action_planner.plan_actions(
                        user_intention=intention, 
                        simplified_dom=dom_before_action, 
                        current_url=self.driver.current_url
                    )
                else:
                    logger.error("ActionPlanner not available. Cannot plan actions.")
                    actions = None

                if actions:
                    logger.info(f"LLM planned actions: {actions}")
                    self.execute_actions(actions)
                    retries = 0 
                else:
                    logger.warning("LLM could not plan actions or planning failed.")
                    retries += 1
                    if retries >= self.max_interaction_retries: # Use instance variable
                        logger.error(f"Max retries ({self.max_interaction_retries}) reached for intention: {intention}. Please try a different approach or check the page.")
                        retries = 0 
                
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