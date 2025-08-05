"""
파일 처리 유틸리티
"""
import os
import json


def load_json_data(filename):
    """JSON 파일 로드"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ JSON 파일 로드 실패: {filename} - {e}")
        return None


def save_json_data(data, filename):
    """JSON 파일 저장"""
    try:
        # Ensure directory exists for the file
        from pathlib import Path
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"❌ JSON 파일 저장 실패: {filename} - {e}")
        return False


def ensure_directory(directory_path):
    """디렉토리 존재 확인 및 생성"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"📁 {directory_path} 폴더를 생성했습니다.")
        return True
    else:
        print(f"📁 {directory_path} 폴더가 존재합니다.")
        return False


def get_base_filename_from_content_file(content_filename):
    """콘텐츠 파일명에서 기본 파일명 추출"""
    if content_filename:
        return content_filename.replace('_ugc_generated_content.json', '').replace('_generated_content.json', '')
    return "default"


def check_required_files(required_files):
    """필수 파일들 존재 확인"""
    for file in required_files:
        if os.path.exists(file):
            return True
    return False
