# -*- coding: utf-8 -*-
"""
JSON 데이터 매니저 - agent_03_instagram_crawler 데이터 연동
"""

import os
import json
import shutil
from pathlib import Path


def copy_agent03_data_to_agent14():
    """agent_03의 Instagram JSON 데이터를 agent_14로 복사"""
    print("agent_03 Instagram 데이터를 agent_14로 복사 중...")
    
    # 경로 설정
    agent_03_data_path = Path(__file__).parent.parent.parent / "agent_03_instagram_crawler" / "data" / "instagram"
    agent_14_path = Path(__file__).parent.parent
    
    # 복사할 파일 목록
    files_to_copy = [
        "kijun_official.json",
        "kijun_official_tagged.json",
        "kijun_official_detailed.json", 
        "kijun_official_tagged_detailed.json"
    ]
    
    copied_files = []
    
    for filename in files_to_copy:
        source_file = agent_03_data_path / filename
        dest_file = agent_14_path / filename
        
        if source_file.exists():
            try:
                shutil.copy2(source_file, dest_file)
                print(f"[OK] 복사 완료: {filename}")
                copied_files.append(str(dest_file))
            except Exception as e:
                print(f"[ERROR] 복사 실패 {filename}: {e}")
        else:
            print(f"⚠️ 파일 없음: {filename}")
    
    return copied_files


def get_json_data_files(brand_name=None):
    """agent_14에서 사용할 JSON 데이터 파일 목록 반환"""
    brand_name = brand_name or "kijun"
    agent_14_path = Path(__file__).parent.parent
    
    # 우선순위: agent_14 로컬 -> agent_03 원본
    json_files = {
        "official": None,
        "tagged": None
    }
    
    # agent_14에서 파일 찾기
    local_official = agent_14_path / f"{brand_name}_official.json"
    local_tagged = agent_14_path / f"{brand_name}_official_tagged.json"
    
    if local_official.exists():
        json_files["official"] = str(local_official)
        print(f"[OK] 로컬 공식 데이터 발견: {local_official}")
    
    if local_tagged.exists():
        json_files["tagged"] = str(local_tagged)
        print(f"[OK] 로컬 UGC 데이터 발견: {local_tagged}")
    
    # 없으면 agent_03에서 찾기
    if not json_files["official"] or not json_files["tagged"]:
        agent_03_data_path = Path(__file__).parent.parent.parent / "agent_03_instagram_crawler" / "data" / "instagram"
        
        if not json_files["official"]:
            agent03_official = agent_03_data_path / f"{brand_name}_official.json"
            if agent03_official.exists():
                json_files["official"] = str(agent03_official)
                print(f"[OK] agent_03 공식 데이터 발견: {agent03_official}")
        
        if not json_files["tagged"]:
            agent03_tagged = agent_03_data_path / f"{brand_name}_official_tagged.json"
            if agent03_tagged.exists():
                json_files["tagged"] = str(agent03_tagged)
                print(f"[OK] agent_03 UGC 데이터 발견: {agent03_tagged}")
    
    return json_files


def load_instagram_json_data(brand_name=None):
    """Instagram JSON 데이터 로드"""
    print(f"Instagram JSON 데이터 로드 중... (브랜드: {brand_name or 'kijun'})")
    
    json_files = get_json_data_files(brand_name)
    
    data = {
        "official": [],
        "tagged": [],
        "all": []
    }
    
    # 공식 데이터 로드
    if json_files["official"]:
        try:
            with open(json_files["official"], 'r', encoding='utf-8') as f:
                official_data = json.load(f)
                data["official"] = official_data
                data["all"].extend(official_data)
                print(f"[OK] 공식 데이터 로드: {len(official_data)}개 게시물")
        except Exception as e:
            print(f"[ERROR] 공식 데이터 로드 실패: {e}")
    
    # UGC 데이터 로드  
    if json_files["tagged"]:
        try:
            with open(json_files["tagged"], 'r', encoding='utf-8') as f:
                tagged_data = json.load(f)
                data["tagged"] = tagged_data
                data["all"].extend(tagged_data)
                print(f"[OK] UGC 데이터 로드: {len(tagged_data)}개 게시물")
        except Exception as e:
            print(f"[ERROR] UGC 데이터 로드 실패: {e}")
    
    print(f"[INFO] 총 데이터: 공식 {len(data['official'])}개, UGC {len(data['tagged'])}개, 전체 {len(data['all'])}개")
    
    return data


def save_json_data_to_files(output_dir="./", brand_name=None):
    """JSON 데이터를 파일로 저장 (기존 파일명 형태로)"""
    print("JSON 데이터를 파일로 저장 중...")
    
    data = load_instagram_json_data(brand_name)
    
    if not data["official"] and not data["tagged"]:
        print("[ERROR] 저장할 데이터가 없습니다.")
        return None, None
    
    saved_files = []
    
    brand_name = brand_name or "kijun"
    
    # 공식 데이터 저장
    if data["official"]:
        official_filename = os.path.join(output_dir, f"{brand_name}_official.json")
        with open(official_filename, 'w', encoding='utf-8') as f:
            json.dump(data["official"], f, ensure_ascii=False, indent=2)
        print(f"[OK] 공식 데이터 저장: {official_filename}")
        saved_files.append(official_filename)
    
    # UGC 데이터 저장
    if data["tagged"]:
        tagged_filename = os.path.join(output_dir, f"{brand_name}_official_tagged.json")
        with open(tagged_filename, 'w', encoding='utf-8') as f:
            json.dump(data["tagged"], f, ensure_ascii=False, indent=2)
        print(f"[OK] UGC 데이터 저장: {tagged_filename}")
        saved_files.append(tagged_filename)
    
    return saved_files, data["all"]
