"""
File handling utilities
"""

import os
import json

def load_json_file(file_path):
    """JSON 파일 로드"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return None
    except Exception as e:
        print(f"파일 로드 오류: {file_path} - {e}")
        return None

def save_markdown_file(content, file_path):
    """마크다운 파일 저장"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"파일 저장 오류: {file_path} - {e}")
        return False

def load_all_data(config):
    """모든 데이터 파일 로드"""
    all_data = {}
    input_folder = config["input_folder"]
    
    for key, filename in config["data_files"].items():
        file_path = os.path.join(input_folder, filename)
        data = load_json_file(file_path)
        if data is not None:
            all_data[key] = data
            print(f"✅ 로드됨: {filename}")
        else:
            all_data[key] = {}
            print(f"⚠️ 파일 없음: {filename}")
    
    return all_data
