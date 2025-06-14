#!/usr/bin/env python3
"""
Basic usage example for Swarm.

This example demonstrates how to use Swarm programmatically
without the CLI interface.
"""

from swarm.core.config import Config
from swarm.llm.client import LLMClient
from swarm.web.browser import Browser
from swarm.web.search import WebSearch


def main():
    """Main example function."""
    print("🐝 Swarm Basic Usage Example")
    print("=" * 40)

    # Load configuration
    config = Config.from_env()
    print("✓ Configuration loaded")
    print(f"  - LLM: {config.llm.model} at {config.llm.base_url}")
    print(f"  - Browser: {'Headless' if config.browser.headless else 'GUI'}")
    print(f"  - Search: {config.search.engine}")

    try:
        # Example 1: Web Search
        print("\n1. Web Search Example")
        print("-" * 20)

        search = WebSearch(config.search)
        results = search.search("Python web automation")

        print(f"Found {len(results)} search results:")
        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. {result['title']}")
            print(f"     {result['url']}")

        # Example 2: Web Browsing
        print("\n2. Web Browsing Example")
        print("-" * 22)

        browser = Browser(config.browser)
        result = browser.browse("https://httpbin.org/html")

        print(f"✓ Browsed: {result['url']}")
        print(f"  Title: {result['title'] or 'Untitled'}")
        print(f"  Content length: {len(result['content'])} characters")
        print(f"  Links found: {len(result['links'])}")

        # Example 3: LLM Integration
        print("\n3. LLM Integration Example")
        print("-" * 25)

        # Note: This will only work if you have an LLM service running
        try:
            llm = LLMClient(config.llm)
            analysis = llm.analyze_webpage(
                result['content'][:1000],  # First 1000 chars
                result['url']
            )
            print("✓ LLM Analysis:")
            print(f"  {analysis[:200]}...")
        except Exception as e:
            print(f"⚠ LLM service not available: {str(e)}")
            print("  (This is expected if no LLM service is running)")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

    print("\n🎉 Example completed!")


if __name__ == "__main__":
    main()
