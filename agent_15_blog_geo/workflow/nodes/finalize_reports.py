"""
Finalize Reports Node

Saves final consulting reports to file.
"""

import json
import os
from typing import Dict, Any
from ..state import BlogGEOWorkflowState


def finalize_reports_node(state: BlogGEOWorkflowState) -> Dict[str, Any]:
    """
    Save final reports to file
    
    This node:
    1. Takes all processed reports
    2. Saves to JSON file
    3. Updates workflow metadata
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with final_reports
    """
    print(f"\n--- [6단계] 최종 리포트 저장 시작 ---")
    
    final_reports = state['intermediate_reports']
    final_output_file = state['final_consulting_report_file']
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(final_output_file), exist_ok=True)
        
        # Save reports
        with open(final_output_file, 'w', encoding='utf-8') as f:
            json.dump(final_reports, f, ensure_ascii=False, indent=4)
        
        print(f"[완료] 최종 리포트 저장! 파일: '{final_output_file}'")
        # Summary statistics
        total_reports = len(final_reports)
        successful_reports = sum(
            1 for r in final_reports 
            if "error" not in r.get("consulting_report", {})
        )
        images_generated = sum(
            1 for r in final_reports
            if r.get("consulting_report", {}).get("final_blog_image", "").endswith(".png")
        )
        print(f"\n[요약 통계]")
        print(f"  - 전체 컨설팅 리포트: {total_reports}개")
        print(f"  - 성공 리포트: {successful_reports}개")
        print(f"  - 최종 블로그 이미지 생성: {images_generated}개")
    except Exception as e:
        print(f"[오류] 리포트 저장 중 예외 발생: {e}")
        state.setdefault('errors', []).append({
            "node": "finalize_reports",
            "error": str(e)
        })
    return {"final_reports": final_reports}