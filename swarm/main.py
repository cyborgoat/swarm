"""
Main entry point for the Swarm application.
"""
import os
from dotenv import load_dotenv

load_dotenv('.env.local')


def main():
    """Main entry point for the Swarm application."""
    print("🤖 Welcome to Swarm!")
    print("A comprehensive platform for multi-LLM integration and canvas-like applications")
    print()
    
    # Import and demonstrate LLM module
    try:
        from swarm.llm import LLMFactory
        
        print("📊 Available LLM Models:")
        models = LLMFactory.list_models()
        for provider, model_list in models.items():
            print(f"  {provider.upper()}: {len(model_list)} models")
        
        print(f"\n🧠 Reasoning Models: {LLMFactory.list_reasoning_models()}")
        
        print("\n📖 To get started:")
        print("  1. Set your API keys as environment variables")
        print("  2. Run examples: python examples/llm_usage.py")
        print("  3. Check the documentation in README.md")
        print("  4. Explore the LLM module: from swarm.llm import LLMFactory")
        
    except ImportError as e:
        print(f"❌ Error importing LLM module: {e}")
        print("   Make sure all dependencies are installed: uv pip install -e .")

# Removed if __name__ == "__main__": block 