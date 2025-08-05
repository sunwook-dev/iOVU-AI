"""
DALL-E Image Generation Node

Generates images based on consulting recommendations.
"""

import base64
import uuid
import os
from typing import Dict, Any, List, Optional
from openai import OpenAI

from ..state import BlogGEOWorkflowState
from ...tools.prompts import get_dalle_prompt
from ...tools.api_utils import generate_dalle_image


def generate_images_node(state: BlogGEOWorkflowState) -> Dict[str, Any]:
    """
    Generate DALL-E images based on consulting ideas
    
    This node:
    1. Takes composite image ideas from consulting
    2. Generates images using DALL-E 3
    3. Saves images to disk
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with image paths added to reports
    """
    reports = state['intermediate_reports']
    
    print(f"\n--- [5단계] 총 {len(reports)}개 컨설팅 아이디어 이미지 생성 ---")
    
    # Initialize OpenAI client
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = OpenAI(api_key=api_key)
    
    # Create image directory (modular_agents/outputs)
    from pathlib import Path
    current_file = Path(__file__)  # agent_15_blog_geo/workflow/nodes/generate_images.py
    modular_agents_dir = current_file.parent.parent.parent.parent  # Go up to modular_agents
    IMAGE_DIR = str(modular_agents_dir / "outputs")
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    for report in reports:
        if "error" in report.get("consulting_report", {}):
            continue
        
        consulting_report_data = report.get("consulting_report", {})
        report_id = report.get('id', 'N/A')
        
        # Get title and image idea
        generated_title = (
            consulting_report_data.get("title_consulting", {})
            .get("strategy_a", {})
            .get("example_after", f"제목 없음 {report_id}")
        )
        
        composite_image_idea = (
            consulting_report_data.get("content_consulting", {})
            .get("composite_image_idea", "")
        )
        
        if not composite_image_idea:
            print(f"  - [경고] 리포트 ID: {report_id}에 이미지 아이디어가 없습니다. 이미지를 생성하지 않습니다.")
            report.setdefault("consulting_report", {}).setdefault(
                "content_consulting", {}
            ).update({"after_image_file": "NO_IMAGE_IDEA"})
            continue
        
        # Generate DALL-E prompt
        dalle_prompt = get_dalle_prompt(generated_title, composite_image_idea)
        
        print(f"  - 이미지 생성 프롬프트 (ID: {report_id}): {dalle_prompt[:120]}...")
        
        try:
            # Generate image
            img_b64 = generate_dalle_image(client, dalle_prompt)
            
            if img_b64:
                # Save image
                img_bytes = base64.b64decode(img_b64)
                filename = f"img_{report['id']}_{uuid.uuid4().hex[:8]}.png"
                file_path = os.path.join(IMAGE_DIR, filename)
                
                with open(file_path, "wb") as f:
                    f.write(img_bytes)
                
                print(f"    [완료] 이미지 저장: {file_path}")
                
                # Update report with image path
                report.setdefault("consulting_report", {}).setdefault(
                    "content_consulting", {}
                ).update({"after_image_file": file_path})
            else:
                print(f"    [오류] 이미지 생성 실패")
                report.setdefault("consulting_report", {}).setdefault(
                    "content_consulting", {}
                ).update({"after_image_file": "IMAGE_GENERATION_FAILED"})
        except Exception as e:
            print(f"    [오류] 이미지 생성 중 예외 발생: {e}")
            report.setdefault("consulting_report", {}).setdefault(
                "content_consulting", {}
            ).update({"after_image_file": "IMAGE_GENERATION_FAILED"})
    
    print("[완료] 모든 컨설팅 이미지 생성 및 저장 완료.")
    
    return {"intermediate_reports": reports}