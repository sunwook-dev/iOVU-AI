# -*- coding: utf-8 -*-
"""
Font utilities for the Instagram Geo Agent
"""

import os
import platform
from PIL import ImageFont


def get_korean_font(size=24):
    """한글 폰트 가져오기 (Windows, Mac 지원)"""
    try:
        system = platform.system()
        
        if system == 'Windows':
            font_paths = [
                "C:/Windows/Fonts/malgun.ttf",      # 맑은 고딕
                "C:/Windows/Fonts/malgunbd.ttf",    # 맑은 고딕 Bold
                "C:/Windows/Fonts/gulim.ttc",       # 굴림
            ]
        elif system == 'Darwin':  # Mac
            font_paths = [
                "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                "/Library/Fonts/AppleGothic.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]
        else:  # Linux
            font_paths = [
                "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, size)
                    print(f"✅ 한글 폰트 발견: {os.path.basename(font_path)}")
                    return font
            except:
                continue
        
        print("⚠️ 시스템 한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
        return ImageFont.load_default()
        
    except Exception as e:
        print(f"⚠️ 폰트 로딩 오류: {e}")
        return ImageFont.load_default()