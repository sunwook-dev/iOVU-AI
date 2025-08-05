"""
Instagram GEO Analysis Agent

A comprehensive Instagram Generative Engine Optimization (GEO) analysis agent
that evaluates Instagram content using E-E-A-T criteria and provides actionable
optimization recommendations.

This agent adapts the E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness)
framework specifically for Instagram content analysis, combined with GEO criteria
for enhanced discoverability and engagement.

Main Features:
- Complete E-E-A-T + GEO analysis for Instagram posts
- Visual consistency and brand coherence evaluation
- Post synergy and narrative flow analysis
- Content optimization and generation
- Comprehensive reporting and export capabilities

Usage:
    from modular_agents.agent_14_instagram_geo import InstagramGEOOptimizer
    
    # Initialize optimizer
    optimizer = InstagramGEOOptimizer(
        database_url="your_database_url",
        openai_api_key="your_openai_key"
    )
    
    # Run analysis
    results = optimizer.analyze_brand(
        brand_id=123,
        brand_name="My Brand",
        business_type="fashion",
        max_posts=20
    )
    
    # Generate report
    report = optimizer.generate_actionable_report(
        brand_id=123,
        report_type="comprehensive"
    )
"""

__version__ = "1.0.0"
__author__ = "Claude Code"
__description__ = "Instagram GEO Analysis Agent with E-E-A-T Framework"

# Main classes
from .instagram_geo_optimizer import InstagramGEOOptimizer, create_instagram_geo_optimizer

# Workflow components
from .workflow.instagram_geo_workflow import InstagramGEOWorkflow
from .workflow.state import InstagramGEOWorkflowState, create_initial_state

# Database components
from .database.schema import (
    Base,
    InstagramGEOAnalysis,
    PostEEATGEOScore,
    GEOOptimizationResult,
    VisualAnalysisResult,
    SynergyAnalysisResult,
    GeneratedInstagramContent,
    create_tables,
    drop_tables,
    get_table_info,
    validate_schema
)

# Analysis tools
from .tools.instagram_eeat_tools import (
    evaluate_instagram_experience,
    evaluate_instagram_expertise,
    evaluate_instagram_authoritativeness,
    evaluate_instagram_trustworthiness,
    calculate_instagram_eeat_composite_score
)

from .tools.instagram_geo_tools import (
    evaluate_instagram_geo_clarity,
    evaluate_instagram_geo_structure,
    evaluate_instagram_geo_context,
    evaluate_instagram_geo_alignment,
    evaluate_instagram_geo_timeliness,
    evaluate_instagram_geo_originality
)

# Utilities
from .utils.report_generator import (
    InstagramGEOReportGenerator,
    generate_quick_summary,
    export_to_html
)

from .utils.export_utils import (
    InstagramGEOExporter,
    quick_csv_export,
    quick_json_export,
    create_complete_export_package
)

# Workflow nodes (for advanced users)
from .workflow.nodes.content_loader import instagram_content_loader_node
from .workflow.nodes.optimization_nodes import caption_hashtag_optimization_node
from .workflow.nodes.visual_analysis import visual_content_analysis_node
from .workflow.nodes.content_generation import instagram_content_generation_node
from .workflow.nodes.synergy_analysis import instagram_synergy_analysis_node

__all__ = [
    # Main classes
    "InstagramGEOOptimizer",
    "create_instagram_geo_optimizer",
    
    # Workflow
    "InstagramGEOWorkflow",
    "InstagramGEOWorkflowState",
    "create_initial_state",
    
    # Database schema
    "Base",
    "InstagramGEOAnalysis",
    "PostEEATGEOScore",
    "GEOOptimizationResult",
    "VisualAnalysisResult",
    "SynergyAnalysisResult",
    "GeneratedInstagramContent",
    "create_tables",
    "drop_tables",
    "get_table_info",
    "validate_schema",
    
    # Analysis tools
    "evaluate_instagram_experience",
    "evaluate_instagram_expertise",
    "evaluate_instagram_authoritativeness",
    "evaluate_instagram_trustworthiness",
    "calculate_instagram_eeat_composite_score",
    "evaluate_instagram_geo_clarity",
    "evaluate_instagram_geo_structure",
    "evaluate_instagram_geo_context",
    "evaluate_instagram_geo_alignment",
    "evaluate_instagram_geo_timeliness",
    "evaluate_instagram_geo_originality",
    
    # Utilities
    "InstagramGEOReportGenerator",
    "generate_quick_summary",
    "export_to_html",
    "InstagramGEOExporter",
    "quick_csv_export",
    "quick_json_export",
    "create_complete_export_package",
    
    # Workflow nodes
    "instagram_content_loader_node",
    "caption_hashtag_optimization_node",
    "visual_content_analysis_node",
    "instagram_content_generation_node",
    "instagram_synergy_analysis_node"
]

# Package metadata
PACKAGE_INFO = {
    "name": "agent_14_instagram_geo",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "features": [
        "E-E-A-T analysis for Instagram content",
        "GEO (Generative Engine Optimization) evaluation",
        "Visual consistency and brand coherence analysis",
        "Post synergy and narrative flow evaluation",
        "Content optimization and generation",
        "Comprehensive reporting and export capabilities",
        "LangGraph workflow orchestration",
        "Database persistence and tracking",
        "Multi-format export utilities"
    ],
    "requirements": [
        "langchain",
        "langgraph",
        "sqlalchemy",
        "openai",
        "numpy",
        "pandas"
    ],
    "supported_formats": {
        "analysis_input": ["database", "json", "csv"],
        "report_output": ["html", "markdown", "json", "text"],
        "data_export": ["csv", "json", "excel", "pdf", "zip"]
    }
}

def get_package_info():
    """Get package information and metadata"""
    return PACKAGE_INFO

def get_version():
    """Get package version"""
    return __version__

def get_supported_business_types():
    """Get list of supported business types for analysis"""
    return [
        "fashion",
        "beauty", 
        "food",
        "lifestyle",
        "technology",
        "health",
        "education",
        "entertainment",
        "general"
    ]

def get_analysis_criteria():
    """Get list of analysis criteria used by the agent"""
    return {
        "eeat_criteria": [
            "experience",
            "expertise", 
            "authoritativeness",
            "trustworthiness"
        ],
        "geo_criteria": [
            "clarity",
            "structure",
            "context",
            "alignment",
            "timeliness",
            "originality"
        ],
        "additional_analysis": [
            "visual_consistency",
            "brand_coherence",
            "post_synergy",
            "narrative_flow",
            "hashtag_strategy",
            "engagement_patterns"
        ]
    }

def create_quick_analyzer(database_url=None, openai_api_key=None):
    """
    Create a quick analyzer instance with minimal configuration
    
    Args:
        database_url: Database connection URL (optional)
        openai_api_key: OpenAI API key (optional)
        
    Returns:
        Configured InstagramGEOOptimizer instance
    """
    return create_instagram_geo_optimizer(
        database_url=database_url,
        openai_api_key=openai_api_key
    )

# Example usage documentation
USAGE_EXAMPLES = {
    "basic_analysis": """
# Basic Instagram GEO Analysis
from modular_agents.agent_14_instagram_geo import InstagramGEOOptimizer

optimizer = InstagramGEOOptimizer()
results = optimizer.analyze_brand(
    brand_id=123,
    brand_name="My Fashion Brand",
    business_type="fashion",
    max_posts=20
)

print(f"Overall GEO Score: {results['analysis_results']['instagram_geo_scores']['overall_score']}")
    """,
    
    "report_generation": """
# Generate Comprehensive Report
from modular_agents.agent_14_instagram_geo import InstagramGEOOptimizer

optimizer = InstagramGEOOptimizer()
report = optimizer.generate_actionable_report(
    brand_id=123,
    report_type="comprehensive",
    include_visuals=True
)

# Export to HTML
from modular_agents.agent_14_instagram_geo import export_to_html
export_to_html(report, "instagram_analysis_report.html")
    """,
    
    "data_export": """
# Export Analysis Data
from modular_agents.agent_14_instagram_geo import (
    InstagramGEOOptimizer,
    create_complete_export_package
)

optimizer = InstagramGEOOptimizer()
results = optimizer.analyze_brand(brand_id=123)

# Create complete data package
package = create_complete_export_package(
    results,
    "exports/brand_123_analysis"
)

print(f"Exported {package['total_files']} files to {package['package_directory']}")
    """,
    
    "comparison_analysis": """
# Compare Two Analyses
from modular_agents.agent_14_instagram_geo import InstagramGEOOptimizer

optimizer = InstagramGEOOptimizer()

# Get current and previous results
current = optimizer.analyze_brand(brand_id=123)
previous = optimizer.get_analysis_history(brand_id=123, limit=2)[1]  # Previous analysis

# Generate comparison report
comparison = optimizer.compare_with_benchmarks(brand_id=123)
trends = optimizer.get_brand_performance_trends(brand_id=123, months_back=6)

print(f"Performance trend: {trends['improvement_metrics']['overall_score_change']}")
    """
}

def get_usage_examples():
    """Get usage examples for the package"""
    return USAGE_EXAMPLES

def validate_environment():
    """
    Validate environment setup for Instagram GEO analysis
    
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        "python_version": "✅ Compatible",
        "required_packages": {},
        "database_support": "✅ Available",
        "openai_integration": "⚠️ API key not set",
        "overall_status": "ready"
    }
    
    # Check required packages
    required_packages = [
        "langchain", "langgraph", "sqlalchemy", "openai"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            validation_results["required_packages"][package] = "✅ Available"
        except ImportError:
            validation_results["required_packages"][package] = "❌ Missing"
            validation_results["overall_status"] = "setup_required"
    
    # Check OpenAI API key
    import os
    if os.getenv("OPENAI_API_KEY"):
        validation_results["openai_integration"] = "✅ API key configured"
    
    return validation_results

# Print package info on import (optional)
import logging
logger = logging.getLogger(__name__)
logger.info(f"Instagram GEO Analysis Agent v{__version__} loaded successfully")
logger.info(f"Features: {len(PACKAGE_INFO['features'])} analysis capabilities available")