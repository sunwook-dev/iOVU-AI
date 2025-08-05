"""
Image handling utilities
"""

import os
from .config import CONFIG

def get_absolute_image_path(md_path):
    """output 폴더 기준 상대 경로를 절대 경로로 변환"""
    output_folder = os.path.abspath(CONFIG["output_folder"])
    abs_path = os.path.normpath(os.path.join(output_folder, md_path))
    return abs_path

def check_image_exists(image_path):
    """이미지 파일 존재 여부 확인"""
    if os.path.exists(image_path):
        return True
    else:
        print(f"⚠️ 이미지 파일 없음: {image_path}")
        return False
