"""
Configuration management for Swarm.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class LLMConfig(BaseModel):
    """Configuration for LLM integration."""
    
    base_url: str = Field(default="http://localhost:11434")
    model: str = Field(default="llama3.2:latest")
    api_key: Optional[str] = Field(default=None)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=8192, gt=0)


class BrowserConfig(BaseModel):
    """Configuration for browser automation."""
    
    headless: bool = Field(default=False)
    timeout: int = Field(default=60000)
    viewport_width: int = Field(default=1280)
    viewport_height: int = Field(default=720)


class SearchConfig(BaseModel):
    """Configuration for web search."""
    
    engine: str = Field(default="duckduckgo")
    results_limit: int = Field(default=10, gt=0)


class LoggingConfig(BaseModel):
    """Configuration for logging."""
    
    level: str = Field(default="INFO")
    file: str = Field(default="swarm.log")


class PerformanceConfig(BaseModel):
    """Configuration for performance settings."""
    
    max_concurrent_requests: int = Field(default=5, gt=0)
    request_timeout: int = Field(default=120, gt=0)


class Config(BaseModel):
    """Main configuration class for Swarm."""
    
    llm: LLMConfig = Field(default_factory=LLMConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            llm=LLMConfig(
                base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434"),
                model=os.getenv("LLM_MODEL", "llama3.2:latest"),
                api_key=os.getenv("LLM_API_KEY"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "8192")),
            ),
            browser=BrowserConfig(
                headless=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
                timeout=int(os.getenv("BROWSER_TIMEOUT", "60000")),
                viewport_width=int(os.getenv("BROWSER_VIEWPORT_WIDTH", "1280")),
                viewport_height=int(os.getenv("BROWSER_VIEWPORT_HEIGHT", "720")),
            ),
            search=SearchConfig(
                engine=os.getenv("SEARCH_ENGINE", "duckduckgo"),
                results_limit=int(os.getenv("SEARCH_RESULTS_LIMIT", "10")),
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
                file=os.getenv("LOG_FILE", "swarm.log"),
            ),
            performance=PerformanceConfig(
                max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "5")),
                request_timeout=int(os.getenv("REQUEST_TIMEOUT", "120")),
            ),
        ) 