"""
Blog Image Generation Node

Composes final blog images with title, DALL-E image, and body text.
"""

import os
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI

from ..state import BlogGEOWorkflowState
from ...tools.prompts import get_blog_body_prompt
from ...tools.api_utils import create_chat_completion
from ...utils.image_utils import create_blog_image


def generate_blog_images_and_enhance_report_node(state: BlogGEOWorkflowState) -> Dict[str, Any]:
    """
    Generate composed blog images and enhance reports
    
    This node:
    1. Generates blog body text based on strategies
    2. Composes final images with title + DALL-E image + body
    3. Updates reports with final image paths
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with final blog images
    """
    print("\n--- [5.5단계] 블로그 최종 이미지 합성 및 리포트 반영 ---")
    consulting_reports = state.get('intermediate_reports', [])
    if not consulting_reports:
        print("[경고] 컨설팅 리포트가 비어 있습니다. 블로그 이미지 생성을 건너뜁니다.")
        return state
    
    # Initialize OpenAI client
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = OpenAI(api_key=api_key)
    
    # Create output directory (modular_agents/outputs)
    from pathlib import Path
    current_file = Path(__file__)  # agent_15_blog_geo/workflow/nodes/generate_blog_images.py
    modular_agents_dir = current_file.parent.parent.parent.parent  # Go up to modular_agents
    IMAGE_DIR = str(modular_agents_dir / "outputs")
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    updated_reports = []
    brand_name = state['brand_name']
    
    for i, report_data in enumerate(consulting_reports):
        report_id = report_data.get('id', i + 1)
        print(f"\n--- 컨설팅 리포트 ID: {report_id} 블로그 이미지 합성 시작 ---")
        
        consulting_report = report_data.get('consulting_report', {})
        if 'error' in consulting_report:
            updated_reports.append(report_data)
            continue
        
        # Get title and text strategies
        title_after = (
            consulting_report.get('title_consulting', {})
            .get('strategy_a', {})
            .get('example_after', f"컨설팅 제목 {report_id}")
        )
        
        strategy_a_text = (
            consulting_report.get('content_consulting', {})
            .get('strategy_a', {})
            .get('text_example', "")
        )
        
        strategy_b_text = (
            consulting_report.get('content_consulting', {})
            .get('strategy_b', {})
            .get('text_example', "")
        )
        
        # Generate blog body text
        generated_blog_body = "본문 생성 실패."
        
        if strategy_a_text or strategy_b_text:
            try:
                print("  - AI로 블로그 본문 생성 중...")
                
                blog_body_prompt = get_blog_body_prompt(
                    brand_name,
                    strategy_a_text,
                    strategy_b_text
                )
                
                generated_blog_body = create_chat_completion(
                    client=client,
                    system_prompt=f"You are a professional fashion blogger for the {brand_name} brand.",
                    user_prompt=blog_body_prompt,
                    model=state['model'],
                    temperature=0.7
                )
                
                if generated_blog_body:
                    print("  - 블로그 본문 생성 완료.")
                else:
                    generated_blog_body = "블로그 본문 생성 실패"
            except Exception as e:
                print(f"  - [오류] 블로그 본문 생성 실패: {e}")
                generated_blog_body = f"블로그 본문 생성 예외: {e}"
        
        # Get DALL-E image path
        current_image_path = (
            consulting_report.get('content_consulting', {})
            .get('after_image_file')
        )
        
        if not current_image_path or current_image_path in ["IMAGE_GENERATION_FAILED", "NO_IMAGE_IDEA"]:
            print(f"  - [오류] 리포트 ID: {report_id}에 DALL-E 이미지가 없습니다. 블로그 이미지 생성을 건너뜁니다.")
            report_data['consulting_report']['final_blog_image'] = "BLOG_IMAGE_GENERATION_SKIPPED_OR_FAILED"
            updated_reports.append(report_data)
            continue
        
        # Create composed blog image
        output_filename = f"{state['platform']}_blog_post_consulting_id_{report_id}.png"
        
        try:
            generated_file_path = create_blog_image(
                title=title_after,
                body_text=generated_blog_body,
                image_path=current_image_path,
                output_filename=output_filename,
                output_dir=IMAGE_DIR
            )
            
            if generated_file_path:
                report_data['consulting_report']['final_blog_image'] = generated_file_path
                print(f"[완료] 리포트 ID: {report_id}의 'final_blog_image': '{generated_file_path}' 저장 완료.")
            else:
                report_data['consulting_report']['final_blog_image'] = "BLOG_IMAGE_GENERATION_FAILED_INTERNAL_ERROR"
        except Exception as e:
            print(f"  - [오류] 블로그 이미지 생성 예외: {e}")
            report_data['consulting_report']['final_blog_image'] = "BLOG_IMAGE_GENERATION_FAILED_INTERNAL_ERROR"
        
        updated_reports.append(report_data)
    
    print("\n--- [완료] 모든 블로그 이미지 합성 및 리포트 반영 완료 ---")
    
    return {"intermediate_reports": updated_reports}