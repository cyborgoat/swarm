"""
Tests for configuration management.
"""

import pytest
from swarm.core.config import Config, LLMConfig, BrowserConfig


def test_default_config():
    """Test default configuration values."""
    config = Config()
    
    assert config.llm.base_url == "http://localhost:11434"
    assert config.llm.model == "llama2"
    assert config.llm.temperature == 0.7
    assert config.llm.max_tokens == 2048
    
    assert config.browser.headless is True
    assert config.browser.timeout == 30000
    assert config.browser.viewport_width == 1280
    assert config.browser.viewport_height == 720
    
    assert config.search.engine == "duckduckgo"
    assert config.search.results_limit == 10


def test_llm_config():
    """Test LLM configuration."""
    llm_config = LLMConfig(
        base_url="http://localhost:8000",
        model="gpt-4",
        temperature=0.5,
        max_tokens=1024
    )
    
    assert llm_config.base_url == "http://localhost:8000"
    assert llm_config.model == "gpt-4"
    assert llm_config.temperature == 0.5
    assert llm_config.max_tokens == 1024


def test_browser_config():
    """Test browser configuration."""
    browser_config = BrowserConfig(
        headless=False,
        timeout=60000,
        viewport_width=1920,
        viewport_height=1080
    )
    
    assert browser_config.headless is False
    assert browser_config.timeout == 60000
    assert browser_config.viewport_width == 1920
    assert browser_config.viewport_height == 1080


def test_config_validation():
    """Test configuration validation."""
    # Test invalid temperature
    with pytest.raises(ValueError):
        LLMConfig(temperature=3.0)  # Should be <= 2.0
    
    # Test invalid max_tokens
    with pytest.raises(ValueError):
        LLMConfig(max_tokens=0)  # Should be > 0 