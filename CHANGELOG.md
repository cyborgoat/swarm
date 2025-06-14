# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-06-14

### Added
- **Enhanced Research System**: Comprehensive 4-phase research workflow
  - Phase 1: Web search with duplicate URL elimination
  - Phase 2: Source analysis with relevance scoring
  - Phase 3: Content synthesis with key findings extraction
  - Phase 4: Final report generation with structured summaries
- **Research Command**: Direct command-line research tool with argument parsing
- **Rich Progress Reporting**: Detailed visual progress indicators during research
- **Structured Report Generation**: Comprehensive research reports with statistics
- **URL Deduplication**: Prevents duplicate search results from being processed
- **Retry Logic**: Robust error handling with automatic retries for LLM calls
- **Content Limiting**: Prevents token overflow by limiting content length
- **Async Browser Support**: Full async Playwright integration

### Fixed
- **LLM Timeout Issues**: Resolved timeout errors during research summary generation
- **Duplicate URL Problem**: Fixed search engine returning identical URLs multiple times
- **Threading Conflicts**: Eliminated "Cannot switch to a different thread" errors
- **Token Overflow**: Prevented LLM calls from exceeding token limits
- **Error Recovery**: Improved error handling with fallback strategies

### Changed
- **Increased Timeouts**: HTTP timeout increased from 30s to 120s
- **Enhanced Token Limits**: Max tokens increased from 4096 to 8192
- **Updated Default Model**: Changed from `gemma3:12b` to `llama3.2:latest`
- **Improved Configuration**: Better default settings for research tasks
- **Enhanced Error Messages**: More informative error reporting with retry indicators

### Technical Improvements
- Full async/await support throughout the codebase
- Optimized content processing for better performance
- Enhanced LLM client with multiple fallback strategies
- Improved search result parsing with multiple selector strategies
- Better memory management during long research sessions

## [1.0.0] - 2025-06-13

### Added
- Initial release with basic web browsing and automation
- MCP server integration for LLM tool calling
- Interactive mode with natural language processing
- DuckDuckGo search integration
- Playwright browser automation
- Basic research capabilities

### Features
- 14 MCP tools for browser automation
- Interactive CLI with rich formatting
- Web search and content extraction
- Form automation and element interaction
- Session management and persistence 