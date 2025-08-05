"""
Ranking and Selection Node

Ranks analysis results and selects top/bottom performers for consulting.
"""

from typing import Dict, Any, List
from ..state import BlogGEOWorkflowState


def rank_and_select_node(state: BlogGEOWorkflowState) -> Dict[str, Any]:
    """
    Rank posts by score and select for consulting
    
    This node:
    1. Filters valid analysis results
    2. Sorts by average score
    3. Selects top N and bottom N posts for deep consulting
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with posts_for_consulting
    """
    print("\n--- [3단계] 점수 기반 컨설팅 대상 선정 ---")
    
    n_selective = state['n_selective']
    
    # Filter results with valid scores
    results_with_score = [
        res for res in state['all_analysis_results']
        if 'error' not in res and 
        res.get('analysis_report', {}).get('summary', {}).get('average_score') is not None
    ]
    
    # Sort by average score (ascending - lowest first)
    results_with_score.sort(
        key=lambda x: x['analysis_report']['summary']['average_score']
    )
    
    # Select posts for consulting
    if len(results_with_score) >= (n_selective * 2):
        # Get top N (highest scores) and bottom N (lowest scores)
        # Reverse to get highest scores first in each group
        selected_posts = (
            list(reversed(results_with_score[-n_selective:])) +  # Top N
            list(reversed(results_with_score[:n_selective]))    # Bottom N
        )
        
        print(f"  - 상위 {n_selective}개, 하위 {n_selective}개 포스트를 컨설팅 대상으로 선정합니다.")
        
        # Print selected posts
        print(f"\n  [상위 {n_selective}개]")
        for i, post in enumerate(selected_posts[:n_selective]):
            score = post['analysis_report']['summary']['average_score']
            title = post['source_post']['title'][:50]
            print(f"    {i+1}. (점수: {score}) {title}...")
        print(f"\n  [하위 {n_selective}개]")
        for i, post in enumerate(selected_posts[n_selective:]):
            score = post['analysis_report']['summary']['average_score']
            title = post['source_post']['title'][:50]
            print(f"    {i+1}. (점수: {score}) {title}...")
    else:
        # Not enough posts, select all sorted by score (descending)
        selected_posts = sorted(
            results_with_score,
            key=lambda x: x['analysis_report']['summary']['average_score'],
            reverse=True
        )
        print(f"  - 포스트 수가 적어, 전체를 점수순(내림차순)으로 컨설팅 대상으로 선정합니다.")
        for i, post in enumerate(selected_posts):
            score = post['analysis_report']['summary']['average_score']
            title = post['source_post']['title'][:50]
            print(f"    {i+1}. (점수: {score}) {title}...")
    print(f"\n  - 총 {len(selected_posts)}개 포스트가 컨설팅 대상으로 선정되었습니다.")
    
    return {"posts_for_consulting": selected_posts}