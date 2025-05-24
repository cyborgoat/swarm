"""
Module for planning web actions using an LLM.
"""
import json
import logging
from typing import List, Dict, Any, Optional

from swarm.llm import BaseLLM

logger = logging.getLogger(__name__)

class ActionPlanner:
    """
    Uses an LLM to understand user intention and plan Selenium actions
    based on a simplified DOM.
    """
    def __init__(self, llm_client: BaseLLM):
        """
        Initializes the ActionPlanner.

        Args:
            llm_client: The LLM client to use for planning.
        """
        if not llm_client:
            logger.critical("ActionPlanner: LLM client not provided during initialization.")
            raise ValueError("ActionPlanner requires an LLM client.")
        self.llm_client = llm_client
        logger.info(f"ActionPlanner initialized with LLM: {self.llm_client.config.model_name}")

    def plan_actions(self, user_intention: str, simplified_dom: str, current_url: Optional[str]) -> Optional[List[Dict[str, Any]]]:
        """
        Uses the LLM to understand user intention and plan actions.

        Args:
            user_intention: The user's stated goal.
            simplified_dom: A simplified string representation of the page's DOM.
            current_url: The current URL of the web page for context.

        Returns:
            A list of action dictionaries, or None if planning fails.
        """
        prompt_parts = [
            "You are an expert web automation assistant. Based on the provided simplified DOM and the user's intention, ",
            "determine a sequence of actions to achieve the goal. Focus on using the 'ref' attribute of elements for interactions.",
            "Available actions:",
            "1. type(ref, text): Type text into an input field, textarea, or select. CRITICAL: Only use this action with elements that are actual input fields (e.g., <input>, <textarea>, <select>). Do NOT use this on labels, divs, spans, or other non-input elements.",
            "   - ref: The 'ref' attribute of the element from the DOM.",
            "   - text: The text to type.",
            "2. click(ref): Click on a button, link, or other clickable element.",
            "   - ref: The 'ref' attribute of the element from the DOM.",
            "3. navigate(url): Navigate to a new URL.",
            "   - url: The full URL to navigate to.",
            "4. wait(seconds): Wait for a specified number of seconds (e.g., for dynamic content to load). Max 5 seconds.",
            "   - seconds: Number of seconds to wait.",
            "5. analyze_page_content(question_for_analyzer): Use this if the user is asking a question about the content of the current page itself (e.g., 'Summarize this page', 'What is the main topic?', 'Find information about X on this page').",
            "   - question_for_analyzer: The specific question or analysis task based on the user's intention.",
            "6. list_tabs(): List all currently open browser tabs with their titles and URLs.",
            "7. switch_tab(target): Switch focus to a specific browser tab. Use a unique part of the tab's title, URL, or its handle (from list_tabs) as the target.",
            "   - target: A string to identify the target tab (e.g., a handle, partial title, or partial URL).",
            "Current Page URL (for context): " + (current_url if current_url else "Unknown"),
            f"Simplified DOM:\n---\n{simplified_dom}\n---",
            f'User Intention: "{user_intention}"',
            "Output the actions as a JSON list of dictionaries. Each dictionary must have an \"action_type\" ",
            "(e.g., \"type\", \"click\", \"navigate\", \"wait\", \"analyze_page_content\", \"list_tabs\", \"switch_tab\"), and other necessary parameters based on the action_type ",
            "(e.g., \"ref\", \"text\", \"url\", \"seconds\", \"question_for_analyzer\", \"target\"). ",
            "Guidance for clicking links (<a> tags for navigation):",
            "  - Pay close attention to the link's text content, its `aria-label`, and its `href` attribute as shown in the simplified DOM.",
            "  - Prefer links where the text, `aria-label`, or `href` clearly matches the user's stated navigation goal.",
            "  - Example: If the user says 'go to the careers page', look for a link with text like 'Careers' or an href like '/careers'.",
            "  - If you must use an `idx#` reference for a link (e.g., `a_idx#3`), be very careful. This index is 0-based relative to the visible `<a>` tags presented in the simplified DOM.",
            "  - Double-check that the chosen `idx#` is valid and the link is the most plausible one based on all available information (text, href, context).",
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
            "Example for page content analysis:",
            "```json",
            "[",
            "  {\"action_type\": \"analyze_page_content\", \"question_for_analyzer\": \"What are the main services offered on this page?\"}",
            "]",
            "```",
            "Example for listing tabs:",
            "```json",
            "[",
            "  {\"action_type\": \"list_tabs\"}",
            "]",
            "```",
            "Example for switching tab (e.g., to a tab containing 'Order Confirmation' in its title or URL, or by its handle):",
            "```json",
            "[",
            "  {\"action_type\": \"switch_tab\", \"target\": \"Order Confirmation\"}",
            "]",
            "```",
            "If the intention cannot be achieved with the available elements/actions, or if the DOM is empty, output an empty list [].",
            "Only use the 'ref' attributes provided in the simplified DOM to identify elements.",
            "If a 'ref' includes 'idx#', it means it's a less specific identifier, try to use refs with 'id#' or 'name#' if available for the same logical element.",
            "Be very careful to output valid JSON. The response MUST be a single JSON array."
        ]
        prompt = "\n".join(prompt_parts)

        logger.info("ActionPlanner: Sending request to LLM for action planning...")
        # logger.debug(f"LLM Prompt for planning:\n{prompt}") # Can be very verbose
        
        messages = [{"role": "user", "content": prompt}]
        response_text, json_str = None, None
        
        try:
            response_text = self.llm_client.generate(messages)
            if not response_text: 
                logger.warning("ActionPlanner: LLM returned empty response for planning.")
                return None
            logger.info(f"ActionPlanner: LLM Raw Response for planning:\n{response_text}")
            
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
                    logger.warning(f"ActionPlanner: Could not find valid JSON list in LLM response: {response_text}")
                    return None

            actions = json.loads(json_str)
            if not isinstance(actions, list): 
                logger.warning(f"ActionPlanner: LLM response is not valid JSON list after parsing: {json_str}")
                return None
            return actions
        except json.JSONDecodeError as e:
            err_msg = f"ActionPlanner: Error decoding LLM JSON. Error: {e}.\nLLM Raw Response: {response_text}\nAttempted to parse: {json_str}"
            logger.error(err_msg)
            return None
        except Exception as e:
            logger.error(f"ActionPlanner: Error in LLM action planning: {e}", exc_info=True)
            return None 