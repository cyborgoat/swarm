"""
Module for executing Selenium actions on a web page.
"""
import time
import logging
from typing import List, Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

logger = logging.getLogger(__name__)

class SeleniumExecutor:
    """
    Executes specific Selenium actions on a web page using a WebDriver instance.
    """
    def __init__(self, driver: webdriver.Chrome):
        """
        Initializes the SeleniumExecutor.

        Args:
            driver: The Selenium WebDriver instance to use for actions.
        """
        if not driver:
            logger.critical("SeleniumExecutor: WebDriver not provided during initialization.")
            raise ValueError("SeleniumExecutor requires a WebDriver instance.")
        self.driver = driver
        logger.info("SeleniumExecutor initialized.")

    def list_open_tabs(self) -> List[Dict[str, str]]:
        """Lists all open tabs with their handles, titles, and URLs."""
        tabs_info = []
        original_handle = self.driver.current_window_handle
        try:
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                tabs_info.append({
                    "handle": handle,
                    "title": self.driver.title,
                    "url": self.driver.current_url
                })
            self.driver.switch_to.window(original_handle) # Switch back to original
        except Exception as e:
            logger.error(f"Error listing open tabs: {e}", exc_info=True)
            # Attempt to switch back to original handle even on error
            try:
                self.driver.switch_to.window(original_handle)
            except Exception as e_switch_back:
                logger.error(f"Could not switch back to original tab after error in list_open_tabs: {e_switch_back}")
        return tabs_info

    def switch_to_tab(self, target_identifier: str) -> bool:
        """
        Switches focus to a tab identified by its handle, title, or URL (partial match for title/URL).
        Returns True if switch was successful or target was already active, False otherwise.
        """
        if not target_identifier:
            logger.warning("switch_to_tab: No target_identifier provided.")
            return False

        current_handles = self.driver.window_handles
        original_handle = self.driver.current_window_handle

        # Try direct handle match first
        if target_identifier in current_handles:
            if target_identifier == original_handle:
                logger.info(f"Already on tab with handle: {target_identifier}")
                return True
            try:
                self.driver.switch_to.window(target_identifier)
                logger.info(f"Switched to tab with handle: {target_identifier} (Title: {self.driver.title})")
                return True
            except Exception as e:
                logger.error(f"Error switching to tab by handle '{target_identifier}': {e}", exc_info=True)
                return False
        
        # Try matching by title or URL if not a handle
        logger.info(f"Target '{target_identifier}' not a direct handle. Attempting to match by title/URL.")
        for handle in current_handles:
            try:
                self.driver.switch_to.window(handle)
                current_title = self.driver.title
                current_url = self.driver.current_url
                if target_identifier.lower() in current_title.lower() or target_identifier.lower() in current_url.lower():
                    if handle == original_handle:
                        logger.info(f"Already on tab matching '{target_identifier}' (Title: {current_title})")
                        # No need to switch back to original_handle as we are already on the target.
                        return True 
                    logger.info(f"Switched to tab matching '{target_identifier}' (Handle: {handle}, Title: {current_title})")
                    # No need to switch back to original_handle as we successfully switched to the target.
                    return True
            except Exception as e:
                logger.debug(f"Error inspecting tab {handle} for switching: {e}")
                continue # Try next handle
        
        logger.warning(f"Could not find a tab matching '{target_identifier}' by handle, title, or URL.")
        self.driver.switch_to.window(original_handle) # Ensure we are back to where we started if no match found
        return False

    def _find_element_by_ref(self, ref: str) -> Optional[WebElement]:
        """Finds an element using the 'ref' string from the simplified DOM."""
        if not self.driver or not ref: return None
        logger.info(f"Attempting to find element by ref: '{ref}'")
        
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
            # Strategy 1: ID-Primary Lookup
            if id_val:
                try:
                    candidate_element = self.driver.find_element(By.ID, id_val)
                    if candidate_element.tag_name.lower() == tag_name_from_ref.lower():
                        element = candidate_element
                        logger.info(f"Found element by ID '{id_val}' with matching tag '{tag_name_from_ref}'.")
                        # Optional: Log warnings if other ref attributes don't match this ID-found element
                        if name_val and element.get_attribute('name') != name_val: 
                            logger.debug(f"  (ID-found element name '{element.get_attribute('name')}' mismatches ref name '{name_val}')")
                        if type_val and element.get_attribute('type') != type_val: 
                            logger.debug(f"  (ID-found element type '{element.get_attribute('type')}' mismatches ref type '{type_val}')")
                        if role_val and element.get_attribute('role') != role_val: 
                            logger.debug(f"  (ID-found element role '{element.get_attribute('role')}' mismatches ref role '{role_val}')")
                    else:
                        logger.debug(f"Element with ID '{id_val}' found, but its tag '{candidate_element.tag_name.lower()}' mismatched ref tag '{tag_name_from_ref.lower()}'.")
                except NoSuchElementException:
                    logger.debug(f"Element with ID '{id_val}' not found by By.ID search.")

            # Strategy 2: Name-Primary Lookup (if not found by ID or id_val not in ref)
            if not element and name_val:
                candidates_by_name = self.driver.find_elements(By.NAME, name_val)
                if candidates_by_name:
                    found_by_name = False
                    for cand in candidates_by_name:
                        if cand.tag_name.lower() == tag_name_from_ref.lower():
                            element = cand
                            found_by_name = True
                            logger.info(f"Found element by Name '{name_val}' with matching tag '{tag_name_from_ref}'. Selected first match.")
                            # Optional: Log warnings if other ref attributes don't match this Name-found element
                            if id_val and element.get_attribute('id') != id_val: 
                                logger.debug(f"  (Name-found element ID '{element.get_attribute('id')}' mismatches ref ID '{id_val}')")
                            if type_val and element.get_attribute('type') != type_val: 
                                logger.debug(f"  (Name-found element type '{element.get_attribute('type')}' mismatches ref type '{type_val}')")
                            if role_val and element.get_attribute('role') != role_val: 
                                logger.debug(f"  (Name-found element role '{element.get_attribute('role')}' mismatches ref role '{role_val}')")
                            break # Take the first one that matches name and tag
                    if not found_by_name:
                        logger.debug(f"Found elements by Name '{name_val}', but none matched tag '{tag_name_from_ref}'.")
                else:
                    logger.debug(f"No elements found with Name '{name_val}'.")

            # Strategy 3: Tag-and-Filter Lookup (if not found by specific ID or Name)
            if not element:
                logger.debug(f"Element not found by ID/Name or ID/Name not in ref. Attempting tag-based search with full filtering for ref: {ref}")
                all_tags_of_type = self.driver.find_elements(By.TAG_NAME, tag_name_from_ref)
                potential_matches = []
                for cand_tag_element in all_tags_of_type:
                    passes_all_filters = True
                    if id_val and cand_tag_element.get_attribute('id') != id_val: passes_all_filters = False
                    if name_val and cand_tag_element.get_attribute('name') != name_val: passes_all_filters = False
                    if type_val and cand_tag_element.get_attribute('type') != type_val: passes_all_filters = False
                    if role_val and cand_tag_element.get_attribute('role') != role_val: passes_all_filters = False
                    
                    if passes_all_filters:
                        potential_matches.append(cand_tag_element)
                
                if idx_val is not None:
                    try:
                        index = int(idx_val)
                        visible_potential_matches = [el for el in potential_matches if el.is_displayed()]
                        if 0 <= index < len(visible_potential_matches):
                            element = visible_potential_matches[index]
                            logger.info(f"Found element by tag '{tag_name_from_ref}', filtered by all attributes in ref, then selected by index {index} from visible matches.")
                        else:
                            logger.warning(f"Index {index} out of bounds for visible, filtered '{tag_name_from_ref}' elements matching ref '{ref}'. Found {len(visible_potential_matches)} such elements after filtering.")
                    except ValueError:
                        logger.warning(f"Invalid index '{idx_val}' in ref '{ref}'.")
                elif potential_matches:
                    visible_matches = [el for el in potential_matches if el.is_displayed()]
                    if visible_matches:
                        element = visible_matches[0]
                        logger.info(f"Found element by tag '{tag_name_from_ref}' and filtering by all attributes in ref (chose first visible).")
                    elif potential_matches: # No visible matches, but non-visible matches exist
                        element = potential_matches[0]
                        logger.info(f"Found element by tag '{tag_name_from_ref}' and filtering by all attributes in ref (chose first, non-visible, as no visible ones matched filters).")
                
                if not element and potential_matches: # Should not happen if potential_matches had items, but as a safeguard
                    logger.debug(f"Tag-and-filter found {len(potential_matches)} potential matches for ref '{ref}', but none were selected (e.g. visibility or index issue).")
                elif not potential_matches:
                     logger.debug(f"No element found for tag '{tag_name_from_ref}' after filtering by all attributes in ref '{ref}'.")

            # Final check for visibility and enabled status
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

    def execute_selenium_action(self, action: Dict[str, Any]) -> bool:
        """
        Executes a single Selenium-specific browser action.

        Args:
            action: A dictionary representing the action to perform.
                    Expected keys: "action_type", and others like "ref", "text", "url", "seconds".
        
        Returns:
            True if the action was attempted (not necessarily succeeded), False if critical params missing.
        """
        action_type = action.get("action_type")
        logger.info(f"SeleniumExecutor: Attempting to execute action: {action}")

        try:
            if action_type == "type":
                ref, text_to_type = action.get("ref"), action.get("text")
                if ref is None or text_to_type is None:
                    logger.warning(f"Skipping 'type' action due to missing 'ref' or 'text': {action}")
                    return False
                element = self._find_element_by_ref(ref)
                if element:
                    # Check if the element is suitable for typing
                    if element.tag_name.lower() not in ['input', 'textarea', 'select']:
                        logger.warning(f"Attempted to 'type' into a non-typable element '{ref}' with tag '{element.tag_name}'. Skipping type operation.")
                        return True # Action was "attempted" in the sense it was processed

                    element.clear()
                    element.send_keys(text_to_type)
                    logger.info(f"Typed '{text_to_type}' (using send_keys) into element '{ref}'")
                    
                    # Check if it looks like a date input and try JS as a fallback if value not set correctly
                    # This is primarily for <input type="text"> being used for dates.
                    # For <input type="date">, send_keys("YYYY-MM-DD") is often better.
                    is_input_tag = element.tag_name.lower() == 'input'
                    looks_like_date_text = (
                        isinstance(text_to_type, str) and 
                        (text_to_type.count('/') == 2 or text_to_type.count('-') == 2) and
                        any(char.isdigit() for char in text_to_type)
                    )
                    current_value = element.get_attribute('value')

                    if is_input_tag and looks_like_date_text and current_value != text_to_type:
                        logger.info(f"Value for '{ref}' after send_keys is '{current_value}', attempting JS fallback for date text '{text_to_type}'.")
                        try:
                            self.driver.execute_script("arguments[0].value = arguments[1];", element, text_to_type)
                            logger.info(f"Set value for '{ref}' using JavaScript to '{text_to_type}'.")
                            # Optionally, trigger change/input events if the site relies on them
                            # self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
                            # self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element)
                        except Exception as js_ex:
                            logger.warning(f"Failed to set value for '{ref}' using JavaScript: {js_ex}")
                else:
                    logger.warning(f"Failed to type: Element with ref '{ref}' not found or text not provided.")
                return True

            elif action_type == "click":
                ref = action.get("ref")
                if ref is None:
                    logger.warning(f"Skipping 'click' action due to missing 'ref': {action}")
                    return False
                element = self._find_element_by_ref(ref)
                if element:
                    try:
                        handles_before_click = set(self.driver.window_handles)
                        element.click()
                        logger.info(f"Clicked element '{ref}'")
                        
                        # Check for new tabs and switch if one appeared
                        handles_after_click = set(self.driver.window_handles)
                        new_handles = handles_after_click - handles_before_click
                        if new_handles:
                            new_handle = new_handles.pop() # Get the new handle
                            logger.info(f"New tab detected after click (Handle: {new_handle}). Switching to it.")
                            self.driver.switch_to.window(new_handle)
                            logger.info(f"Switched to new tab. Title: {self.driver.title}, URL: {self.driver.current_url}")
                        elif len(handles_after_click) > 0 and self.driver.current_window_handle not in handles_after_click:
                            # Edge case: current handle closed, switch to any available if current is invalid
                            logger.warning("Current window handle seems to have closed after click. Switching to first available tab.")
                            self.driver.switch_to.window(self.driver.window_handles[0])

                    except Exception as click_err:
                         logger.error(f"Error clicking element '{ref}': {click_err}", exc_info=True)
                else:
                    logger.warning(f"Failed to click: Element with ref '{ref}' not found.")
                return True

            elif action_type == "navigate":
                url = action.get("url")
                if url:
                    if not url.startswith(('http://', 'https://')):
                        url = 'http://' + url
                    logger.info(f"Navigating to URL: {url}")
                    self.driver.get(url)
                    logger.info(f"Successfully navigated to: {self.driver.title}")
                else:
                    logger.warning("Failed to navigate: URL not provided.")
                return True
            
            elif action_type == "wait":
                seconds = action.get("seconds")
                if isinstance(seconds, (int, float)) and seconds > 0:
                    wait_time = min(float(seconds), 5.0)
                    logger.info(f"Waiting for {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"Invalid or missing 'seconds' for wait action: {seconds}. Waiting 1s by default.")
                    time.sleep(1)
                return True
            
            else:
                logger.warning(f"SeleniumExecutor: Unknown or unsupported action type: {action_type}")
                return False
        
        except TimeoutException as te:
            logger.error(f"SeleniumExecutor: Timeout during action {action}: {te}", exc_info=True)
            return True # Action was attempted
        except Exception as e:
            logger.error(f"SeleniumExecutor: Error executing action {action}: {e}", exc_info=True)
            return True # Action was attempted 