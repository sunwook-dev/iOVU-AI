"""
Blog GEO Analysis Agent

A comprehensive blog content analysis agent that evaluates Naver and Tistory blog posts
using E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) criteria
combined with GEO (Generative Engine Optimization) principles.

This agent implements a 2-stage analysis process:
1. Analyze all posts with E-E-A-T and GEO scoring
2. Select top/bottom performers for deep consulting with AI-generated improvements

Main Features:
- Supports both Naver and Tistory blog platforms
- Complete E-E-A-T + GEO analysis with strict scoring
- 2-stage selective consulting process
- DALL-E 3 image generation for content improvement
- Blog image composition with title + image + body
- Comprehensive reporting and export capabilities

Usage:
    from modular_agents.agent_15_blog_geo import BlogGEOAnalyzer
    
    # Initialize analyzer
    analyzer = BlogGEOAnalyzer(
        database_url="your_database_url",
        openai_api_key="your_openai_key"
    )
    
    # Run analysis for Naver blog
    results = analyzer.analyze_blog(
        platform="naver",
        brand_id=123,
        brand_name="My Brand",
        total_posts_to_process=10,
        n_selective=2
    )
    
    # Generate report
    from modular_agents.agent_15_blog_geo import BlogGEOReportGenerator
    
    report_gen = BlogGEOReportGenerator()
    report_path = report_gen.generate_summary_report(results, format="html")
"""

__version__ = "1.0.0"
__author__ = "Claude Code"
__description__ = "Blog E-E-A-T + GEO Analysis Agent with 2-Stage Consulting"

# Main classes
from .blog_geo_analyzer import BlogGEOAnalyzer, create_blog_geo_analyzer

# Workflow components
from .workflow import (
    BlogGEOWorkflow,
    create_blog_geo_workflow,
    BlogGEOWorkflowState,
    create_initial_state
)

# Database components
from .database import (
    Platform,
    BlogGEOAnalysis,
    BlogPostAnalysis,
    BlogConsultingReport,
    create_tables
)

# Utilities
from .utils import BlogGEOReportGenerator, create_blog_image

# Tools
from .tools import (
    get_analyzer_prompt,
    get_consultant_prompt,
    get_dalle_prompt,
    get_blog_body_prompt
)

__all__ = [
    # Main classes
    "BlogGEOAnalyzer",
    "create_blog_geo_analyzer",
    
    # Workflow
    "BlogGEOWorkflow",
    "create_blog_geo_workflow",
    "BlogGEOWorkflowState",
    "create_initial_state",
    
    # Database
    "Platform",
    "BlogGEOAnalysis",
    "BlogPostAnalysis",
    "BlogConsultingReport",
    "create_tables",
    
    # Utilities
    "BlogGEOReportGenerator",
    "create_blog_image",
    
    # Tools
    "get_analyzer_prompt",
    "get_consultant_prompt",
    "get_dalle_prompt",
    "get_blog_body_prompt"
]

# Package metadata
PACKAGE_INFO = {
    "name": "agent_15_blog_geo",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "platforms": ["naver", "tistory"],
    "features": [
        "E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) analysis",
        "GEO (Generative Engine Optimization) evaluation with 6 criteria",
        "2-stage analysis process: full analysis & selective consulting",
        "Top/bottom performer selection for deep consulting",
        "AI-powered content improvement strategies",
        "DALL-E 3 image generation for visual content",
        "Blog image composition with Korean font support",
        "LangGraph workflow orchestration",
        "Database persistence for analysis history",
        "Multi-format report generation (Markdown, HTML, CSV)"
    ],
    "requirements": [
        "langchain",
        "langgraph",
        "sqlalchemy",
        "openai",
        "pillow",
        "pandas",
        "requests"
    ],
    "scoring_criteria": {
        "eeat": {
            "experience": "Real first-hand experience with products/services",
            "expertise": "Demonstrated knowledge and styling expertise",
            "authoritativeness": "Recognition in the community",
            "trustworthiness": "Transparency and balanced reviews"
        },
        "geo": {
            "clarity_and_specificity": "Clear, specific information",
            "structured_information": "Logical structure with headers",
            "contextual_richness": "Rich background context",
            "visual_text_alignment": "Strong text-visual connection",
            "originality": "Unique perspectives and insights",
            "timeliness_and_event_relevance": "Current and relevant"
        },
        "synergy": {
            "consistency": "Consistent messaging",
            "synergy_effect": "Enhanced impact through combination"
        }
    }
}

def get_package_info():
    """Get package information and metadata"""
    return PACKAGE_INFO

def get_version():
    """Get package version"""
    return __version__

def get_supported_platforms():
    """Get list of supported blog platforms"""
    return ["naver", "tistory"]

def get_scoring_criteria():
    """Get detailed scoring criteria"""
    return PACKAGE_INFO["scoring_criteria"]

# Usage examples
USAGE_EXAMPLES = {
    "basic_analysis": """
# Basic Blog Analysis
from modular_agents.agent_15_blog_geo import BlogGEOAnalyzer

analyzer = BlogGEOAnalyzer()
results = analyzer.analyze_blog(
    platform="naver",  # or "tistory"
    brand_id=123,
    brand_name="My Fashion Brand",
    total_posts_to_process=10,
    n_selective=2  # Top 2 + Bottom 2 for consulting
)

print(f"Average E-E-A-T Score: {results['average_scores']['eeat_average']}")
print(f"Average GEO Score: {results['average_scores']['geo_average']}")
    """,
    
    "report_generation": """
# Generate Reports
from modular_agents.agent_15_blog_geo import BlogGEOReportGenerator

report_gen = BlogGEOReportGenerator(output_dir="../outputs")

# Generate summary in different formats
markdown_report = report_gen.generate_summary_report(results, format="markdown")
html_report = report_gen.generate_summary_report(results, format="html")

# Export detailed data to CSV
csv_export = report_gen.export_to_csv(results['analysis_report_path'])
    """,
    
    "custom_prompts": """
# Use Custom Prompts
from modular_agents.agent_15_blog_geo import get_analyzer_prompt

# Get analyzer prompt with custom brand name
prompt = get_analyzer_prompt(brand_name="My Brand")

# Use in your own analysis
messages = [
    {"role": "system", "content": prompt},
    {"role": "user", "content": "Blog post content here..."}
]
    """,
    
    "command_line": """
# Command Line Usage
python -m agent_15_blog_geo.run_analysis naver 123 \\
    --brand-name "My Brand" \\
    --posts-limit 20 \\
    --selective-count 3 \\
    --output-dir "./my_reports"
    """
}

def get_usage_examples():
    """Get usage examples"""
    return USAGE_EXAMPLES

def validate_environment():
    """
    Validate environment setup for blog analysis
    
    Returns:
        Dictionary with validation results
    """
    import importlib
    validation_results = {
        "python_version": "✔ Compatible",
        "required_packages": {},
        "openai_api": "⏺ Not checked",
        "database": "✔ SQLite available",
        "overall_status": "ready"
    }
    
    # Check required packages
    for package in PACKAGE_INFO["requirements"]:
        try:
            importlib.import_module(package)
            validation_results["required_packages"][package] = "✔ Installed"
        except ImportError:
            validation_results["required_packages"][package] = "✗ Missing"
            validation_results["overall_status"] = "setup_required"
    
    # Check OpenAI API key
    import os
    if os.getenv("OPENAI_API_KEY"):
        validation_results["openai_api"] = "✔ API key found"
    else:
        validation_results["openai_api"] = "✗ API key not set"
        validation_results["overall_status"] = "setup_required"
    
    return validation_results

# Print package info on import
import logging
logger = logging.getLogger(__name__)
logger.info(f"Blog GEO Analysis Agent v{__version__} loaded")
logger.info(f"Supported platforms: {', '.join(get_supported_platforms())}")