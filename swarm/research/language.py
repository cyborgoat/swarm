"""
Language Support - Handles internationalization for research output.
"""

from typing import Dict, Any

# Language translations for UI elements
TRANSLATIONS = {
    "english": {
        "research_report": "Research Report",
        "generated": "Generated",
        "model": "Model", 
        "context_size": "Context Size",
        "sources_analyzed": "Sources Analyzed",
        "images_found": "Images Found",
        "executive_summary": "Executive Summary",
        "key_findings": "Key Findings",
        "detailed_key_findings": "Detailed Key Findings",
        "finding": "Finding",
        "source": "Source",
        "relevance_score": "Relevance Score",
        "relevant_images": "Relevant Images",
        "identified_themes": "Identified Themes",
        "supporting_sources": "Supporting Sources",
        "detailed_source_analysis": "Detailed Source Analysis",
        "word_count": "Word Count",
        "summary": "Summary",
        "content_preview": "Content Preview",
        "all_search_results": "All Search Results",
        "depth_legend": "Depth Legend: N/N=Normal, D/N=Deep Extract, N/E=Enhanced Analysis, D/E=Deep+Enhanced",
        "relevance_distribution": "Relevance Distribution",
        "high": "High",
        "medium": "Medium", 
        "low": "Low",
        "research_complete": "Research Complete!",
        "sources_found": "Sources Found",
        "themes_identified": "Themes Identified",
        "tokens": "tokens"
    },
    "chinese": {
        "research_report": "研究报告",
        "generated": "生成时间",
        "model": "模型",
        "context_size": "上下文大小", 
        "sources_analyzed": "已分析来源",
        "images_found": "发现图片",
        "executive_summary": "执行摘要",
        "key_findings": "关键发现",
        "detailed_key_findings": "详细关键发现",
        "finding": "发现",
        "source": "来源",
        "relevance_score": "相关性评分",
        "relevant_images": "相关图片",
        "identified_themes": "识别主题",
        "supporting_sources": "支持来源",
        "detailed_source_analysis": "详细来源分析",
        "word_count": "字数统计",
        "summary": "摘要",
        "content_preview": "内容预览",
        "all_search_results": "所有搜索结果",
        "depth_legend": "深度图例: N/N=正常, D/N=深度提取, N/E=增强分析, D/E=深度+增强",
        "relevance_distribution": "相关性分布",
        "high": "高",
        "medium": "中", 
        "low": "低",
        "research_complete": "研究完成！",
        "sources_found": "发现来源",
        "themes_identified": "识别主题",
        "tokens": "令牌"
    }
}

# Language-specific LLM prompts
LLM_PROMPTS = {
    "english": {
        "source_summary": """
Summarize key points from this source relevant to "{query}":

Source: {title}
Content: {content}

Provide 2-3 sentences focusing on the most relevant information.
""",
        "enhanced_summary": """
Perform an enhanced deep analysis of this source for the query "{query}":

Source: {title}
Content: {content}

Please provide:
1. Key points directly relevant to the query
2. Secondary insights that might be related
3. Important context or background information
4. Any actionable findings

Provide a comprehensive 4-5 sentence summary focusing on maximizing relevance to the research query.
""",
        "key_finding": """
Extract the most important finding about "{query}" from this source:

Source: {title}
Content: {content}

Provide one key finding in 1-2 sentences.
""",
        "final_summary": """
Create a comprehensive research summary for: "{query}"

Key Findings:
{findings}

Main Themes:
{themes}

Structure your response as markdown:

## Executive Summary
2-3 sentences overview of key insights.

## Key Findings
- List 3-5 most important discoveries
- Include supporting evidence

## Main Themes
Brief analysis of identified patterns

## Conclusions
Main takeaways and recommendations.

Keep response focused and under 500 words.
"""
    },
    "chinese": {
        "source_summary": """
总结此来源中与"{query}"相关的要点：

来源：{title}
内容：{content}

请提供2-3句话，重点关注最相关的信息。
""",
        "enhanced_summary": """
对此来源进行关于"{query}"查询的增强深度分析：

来源：{title}
内容：{content}

请提供：
1. 与查询直接相关的要点
2. 可能相关的次要见解
3. 重要的背景信息或上下文
4. 任何可操作的发现

请提供一个全面的4-5句话摘要，重点最大化与研究查询的相关性。
""",
        "key_finding": """
从此来源中提取关于"{query}"最重要的发现：

来源：{title}
内容：{content}

用1-2句话提供一个关键发现。
""",
        "final_summary": """
为"{query}"创建综合研究摘要

关键发现：
{findings}

主要主题：
{themes}

请用Markdown格式构建回应：

## 执行摘要
2-3句话概述关键见解。

## 关键发现
- 列出3-5个最重要的发现
- 包含支持证据

## 主要主题
对识别模式的简要分析

## 结论
主要要点和建议。

保持回应重点突出且在500字以内。
"""
    }
}


class LanguageHelper:
    """Helper class for multi-language support in research output."""
    
    def __init__(self, language: str = "english"):
        self.language = language.lower()
        if self.language not in TRANSLATIONS:
            self.language = "english"  # Fallback to English
    
    def get_text(self, key: str) -> str:
        """Get translated text for a given key."""
        return TRANSLATIONS[self.language].get(key, TRANSLATIONS["english"].get(key, key))
    
    def get_prompt(self, prompt_type: str, **kwargs) -> str:
        """Get language-specific LLM prompt with formatting."""
        template = LLM_PROMPTS[self.language].get(
            prompt_type, 
            LLM_PROMPTS["english"].get(prompt_type, "")
        )
        return template.format(**kwargs)
    
    def is_chinese(self) -> bool:
        """Check if current language is Chinese."""
        return self.language == "chinese"
    
    def get_language_display(self) -> str:
        """Get display name for current language."""
        return "中文" if self.is_chinese() else "English" 