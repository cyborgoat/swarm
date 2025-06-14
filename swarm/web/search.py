"""
Web search functionality for Swarm.
"""

from typing import Any
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from swarm.core.config import SearchConfig
from swarm.core.exceptions import WebError


class WebSearch:
    """Web search class for searching the internet."""

    def __init__(self, config: SearchConfig) -> None:
        """
        Initialize web search with configuration.

        Args:
            config: Search configuration
        """
        self.config = config
        self.session = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def search(self, query: str) -> list[dict[str, Any]]:
        """
        Search the web for a query.

        Args:
            query: Search query

        Returns:
            List of search results
        """
        if self.config.engine.lower() == "duckduckgo":
            return self._search_duckduckgo(query)
        else:
            raise WebError(f"Search engine '{self.config.engine}' not supported")

    def _search_duckduckgo(self, query: str) -> list[dict[str, Any]]:
        """
        Search using DuckDuckGo.

        Args:
            query: Search query

        Returns:
            List of search results (deduplicated)
        """
        try:
            # DuckDuckGo HTML search
            encoded_query = quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            seen_urls = set()  # Track URLs to prevent duplicates

            # Parse search results - updated selectors for current DuckDuckGo HTML
            # Try multiple selector strategies
            result_containers = []

            # Strategy 1: Look for result divs with class containing 'result'
            result_containers.extend(soup.find_all("div", class_=lambda x: x and "result" in x))

            # Strategy 2: Look for result articles or sections
            if not result_containers:
                result_containers.extend(soup.find_all("article"))
                result_containers.extend(soup.find_all("section"))

            # Strategy 3: Look for links with result-like structure
            if not result_containers:
                # Find all links and group by parent containers
                links = soup.find_all("a", href=True)
                for link in links:
                    if link.get("href", "").startswith("http") and link.get_text(strip=True):
                        parent = link.parent
                        if parent and parent not in result_containers:
                            result_containers.append(parent)

            for container in result_containers:
                try:
                    # Extract title and link
                    title_elem = None
                    link_url = None

                    # Look for title link in various ways
                    title_link = container.find("a", href=True)
                    if title_link and title_link.get("href", "").startswith("http"):
                        title_elem = title_link
                        link_url = title_link.get("href")

                    # Alternative: look for h2/h3 with link
                    if not title_elem:
                        for heading in container.find_all(["h2", "h3", "h4"]):
                            link_in_heading = heading.find("a", href=True)
                            if link_in_heading and link_in_heading.get("href", "").startswith("http"):
                                title_elem = link_in_heading
                                link_url = link_in_heading.get("href")
                                break

                    if not title_elem or not link_url:
                        continue

                    # Skip duplicate URLs
                    if link_url in seen_urls:
                        continue

                    title = title_elem.get_text(strip=True)
                    if not title:
                        continue

                    # Extract description - look for text content near the title
                    description = ""

                    # Look for description in various elements
                    desc_candidates = []
                    desc_candidates.extend(container.find_all("span"))
                    desc_candidates.extend(container.find_all("div"))
                    desc_candidates.extend(container.find_all("p"))

                    for desc_elem in desc_candidates:
                        desc_text = desc_elem.get_text(strip=True)
                        if desc_text and len(desc_text) > 20 and desc_text != title:
                            # Avoid duplicate title text
                            if title.lower() not in desc_text.lower():
                                description = desc_text[:200] + "..." if len(desc_text) > 200 else desc_text
                                break

                    # Skip if we don't have meaningful content
                    if len(title) < 3:
                        continue

                    # Add URL to seen set and add result
                    seen_urls.add(link_url)
                    results.append({"title": title, "url": link_url, "description": description})

                    if len(results) >= self.config.results_limit:
                        break

                except Exception:
                    # Skip individual result parsing errors
                    continue

            # If we still don't have results, try a more aggressive approach
            if not results:
                all_links = soup.find_all("a", href=True)
                for link in all_links:
                    href = link.get("href", "")
                    if href.startswith("http") and not href.startswith("https://duckduckgo.com"):
                        # Skip duplicates
                        if href in seen_urls:
                            continue

                        title = link.get_text(strip=True)
                        if title and len(title) > 3:
                            seen_urls.add(href)
                            results.append({"title": title, "url": href, "description": f"Result from {href}"})
                            if len(results) >= self.config.results_limit:
                                break

            return results

        except Exception as e:
            raise WebError(f"Failed to search DuckDuckGo: {str(e)}")

    def get_page_content(self, url: str) -> dict[str, Any]:
        """
        Get content from a web page.

        Args:
            url: URL to fetch

        Returns:
            Dictionary containing page content
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title
            title_elem = soup.find("title")
            title = title_elem.get_text(strip=True) if title_elem else ""

            # Extract text content
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            text_content = soup.get_text(strip=True, separator=" ")

            return {"url": url, "title": title, "content": text_content, "html": response.text}

        except Exception as e:
            raise WebError(f"Failed to get content from {url}: {str(e)}")

    def __del__(self) -> None:
        """Clean up HTTP session."""
        if hasattr(self, "session"):
            self.session.close()
