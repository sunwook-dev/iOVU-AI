"""
Blog GEO Analysis Workflow State

This module defines the state structure for blog analysis workflow.
Supports both Naver and Tistory blog platforms.
"""

SCORING_CRITERIA = {
    "eeat": [
        "experience",
        "expertise",
        "authoritativeness",
        "trustworthiness",
    ],
    "geo": [
        "clarity_and_specificity",
        "structured_information",
        "contextual_richness",
        "visual_text_alignment",
        "originality",
        "timeliness_and_event_relevance",
    ],
    "synergy": [
        "consistency",
        "synergy_effect",
    ],
}


from typing import TypedDict, List, Dict, Any, Optional, Literal


class BlogGEOWorkflowState(TypedDict):
    """
    Complete workflow state for blog GEO analysis

    Based on the 2-stage process from the notebook:
    1. Analyze all posts with E-E-A-T and GEO scoring
    2. Select top/bottom performers for deep consulting
    """

    # Platform and brand info
    platform: Literal["naver", "tistory"]  # Blog platform
    brand_id: int
    brand_name: str

    # Configuration
    total_posts_to_process: Optional[int]  # None means all posts
    n_selective: int  # Number of top/bottom posts to consult

    # Data flow
    posts_to_analyze: List[Dict[str, Any]]  # Prepared blog posts
    all_analysis_results: List[Dict[str, Any]]  # E-E-A-T + GEO analysis for all
    posts_for_consulting: List[Dict[str, Any]]  # Selected for deep consulting
    intermediate_reports: List[Dict[str, Any]]  # Consulting with text ideas
    final_reports: List[Dict[str, Any]]  # Final reports with images

    # File paths for outputs
    analysis_report_file: str
    final_consulting_report_file: str

    # API configuration
    model: str  # OpenAI model to use
    temperature: float
    max_tokens: int

    # Error tracking
    errors: List[Dict[str, Any]]


def create_initial_state(
    platform: Literal["naver", "tistory"],
    brand_id: int,
    brand_name: str = "",
    total_posts_to_process: Optional[int] = 10,
    n_selective: int = 2,
    output_dir: str = "../outputs",
) -> BlogGEOWorkflowState:
    """
    Create initial workflow state

    Args:
        platform: Blog platform ("naver" or "tistory")
        brand_id: Brand ID to analyze
        brand_name: Brand name for context
        total_posts_to_process: Max posts to analyze (None for all)
        n_selective: Number of top/bottom posts for consulting
        output_dir: Directory for output files

    Returns:
        Initialized workflow state
    """
    import os
    from datetime import datetime
    from pathlib import Path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_path = Path(output_dir)
    if not output_path.is_absolute():
        # Always resolve relative path from modular_agents directory
        current_file = Path(__file__)  # agent_15_blog_geo/workflow/state.py
        modular_agents_dir = current_file.parent.parent.parent  # Go up to modular_agents
        output_path = modular_agents_dir / output_dir.lstrip("../")  # Remove ../ prefix

    return {
        "platform": platform,
        "brand_id": brand_id,
        "brand_name": brand_name,
        "total_posts_to_process": total_posts_to_process,
        "n_selective": n_selective,
        "posts_to_analyze": [],
        "all_analysis_results": [],
        "posts_for_consulting": [],
        "intermediate_reports": [],
        "final_reports": [],
        "analysis_report_file": str(
            output_path / f"{platform}_analysis_report_{timestamp}.json"
        ),
        "final_consulting_report_file": str(
            output_path / f"{platform}_consulting_report_{timestamp}.json"
        ),
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "max_tokens": 2048,
        "errors": [],
    }


# Analysis result structure from notebook
class AnalysisReport(TypedDict):
    """Structure matching the notebook's analysis output"""

    post_title: str
    eeat_evaluation: Dict[
        str, Dict[str, Any]
    ]  # experience, expertise, authority, trust
    geo_analysis: Dict[str, Dict[str, Any]]  # 6 GEO criteria
    synergy_analysis: Dict[str, Dict[str, Any]]  # consistency, synergy_effect
    summary: Dict[str, Any]  # average_score, strengths, weaknesses


class ConsultingReport(TypedDict):
    """Structure matching the notebook's consulting output"""

    title_consulting: Dict[str, Any]  # problem, strategy_a, strategy_b
    content_consulting: Dict[str, Any]  # problem, strategies, composite_image_idea
    synergy_consulting: Dict[str, Any]  # problem, solution, example
