"""
Consulting Node

Generates improvement strategies for selected posts.
"""

import json
from typing import Dict, Any, List
from openai import OpenAI

from ..state import BlogGEOWorkflowState
from ...tools.prompts import get_consultant_prompt
from ...tools.api_utils import call_api_with_retry


def consult_posts_node(state: BlogGEOWorkflowState) -> Dict[str, Any]:
    """
    Generate consulting reports for selected posts
    
    This node:
    1. Takes analysis results for selected posts
    2. Generates improvement strategies (A & B)
    3. Creates composite image ideas
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with intermediate_reports
    """
    posts = state['posts_for_consulting']
    
    print(f"\n--- [4단계] 총 {len(posts)}개 컨설팅 리포트 생성 ---")
    
    # Initialize OpenAI client
    import os
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = OpenAI(api_key=api_key)
    
    # Get consultant prompt
    system_prompt = get_consultant_prompt()
    
    intermediate_reports = []
    
    for i, post_data in enumerate(posts):
        try:
            title = post_data['source_post']['title']
            score = post_data.get('analysis_report', {}).get('summary', {}).get('average_score', 'N/A')
            print(f"  - 컨설팅 생성 중... ({i+1}/{len(posts)}) - (점수: {score}) {title[:30]}...")
            
            # Prepare analysis report for consulting
            analysis_json = json.dumps(
                post_data['analysis_report'],
                ensure_ascii=False
            )
            
            user_content = (
                f"아래는 분석 결과(JSON)입니다. 이 포스트에 대한 컨설팅 리포트를 생성해 주세요:\n\n"
                f"{analysis_json}"
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            # Generate consulting report
            consulting_report = call_api_with_retry(
                client=client,
                messages=messages,
                model=state['model'],
                temperature=state['temperature'],
                max_tokens=state['max_tokens']
            )
            
            # Add to results
            intermediate_reports.append({
                "id": post_data['source_post']['id'],
                "average_score": score,
                "consulting_report": consulting_report                
            })
            
        except Exception as e:
            print(f"  - [오류] 컨설팅 생성 예외: {e}")
            intermediate_reports.append({
                "id": post_data['source_post']['id'],
                "average_score": score,
                "consulting_report": {"error": str(e)}                
            })
    print("[완료] 모든 컨설팅 리포트 생성 완료.")
    
    return {"intermediate_reports": intermediate_reports}