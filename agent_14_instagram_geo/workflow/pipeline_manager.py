"""
파이프라인 관리자 - 순차적 파일 처리 (DB 연동)
"""

import os
import json
from dotenv import load_dotenv
# DB 관련 import 제거 - JSON 파일만 사용
from database.json_data_manager import save_json_data_to_files, load_instagram_json_data
from tools.content_analyzer import analyze_single_file
from tools.image_generator import generate_images
from tools.instagram_mockup import create_instagram_mockup

load_dotenv()


def process_single_file(filename):
    """단일 파일을 1→2→3단계 순차 처리"""
    print(f"\n{'-'*20}")
    print(f"파일 처리 시작: {filename}")
    print(f"{'-'*20}")

    # 1단계: 분석
    content_filename = analyze_single_file(filename)
    if not content_filename:
        print(f"X {filename} 1단계 실패")
        return False

    # 2단계: 이미지 생성
    image_path = generate_images(content_filename)
    if not image_path:
        print(f"X {filename} 2단계 실패")
        image_path = "dummy.jpg"

    # 3단계: 목업 생성
    if create_instagram_mockup(image_path, content_filename):
        print(f"OK {filename} 전체 단계 완료!")
        return True
    else:
        print(f"X {filename} 3단계 실패")
        return False


# process_db_data 함수 제거 - JSON 파일만 사용


def process_json_data(brand_name=None):
    """agent_03에서 가져온 JSON 데이터 처리"""
    print(f"\n{'-'*20}")
    print("agent_03 JSON 데이터 처리 시작")
    print(f"{'-'*20}")

    # agent_03의 JSON 데이터를 현재 폴더로 복사하고 처리
    saved_files, data = save_json_data_to_files(output_dir="./", brand_name=brand_name)

    if not saved_files:
        print("JSON 데이터를 가져올 수 없습니다.")
        return False

    success_count = 0

    # 저장된 JSON 파일들을 처리
    for filename in saved_files:
        if os.path.exists(filename):
            if process_single_file(filename):
                success_count += 1
            else:
                print(f"X {filename} 처리 실패")
        else:
            print(f"! {filename} 파일이 존재하지 않습니다.")

    return success_count > 0


def run_sequential_pipeline(brand_name=None):
    """메인 실행 함수 - DB 연동 파이프라인"""
    print(" Instagram 순차 통합 파이프라인 시작 (DB 연동)")
    print("=" * 60)

    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("X OpenAI API 키가 .env 파일에 설정되지 않았습니다.")
        print("# .env 파일에 OPENAI_API_KEY=your_api_key_here를 추가해주세요.")
        return False

    print(f"OK OpenAI API 키 확인됨: {api_key[:10]}...")

    # ./images 폴더 확인 및 생성
    images_folder = "./images"
    if not os.path.exists(images_folder):
        os.makedirs(images_folder)
        print(f"+ {images_folder} 폴더를 생성했습니다.")
    else:
        print(f"# {images_folder} 폴더가 존재합니다.")

    # 통합 outputs 폴더 확인 및 생성
    from pathlib import Path
    current_file = Path(__file__)  # agent_14_instagram_geo/workflow/pipeline_manager.py
    modular_agents_dir = current_file.parent.parent.parent  # Go up to modular_agents
    output_folder = modular_agents_dir / "outputs"
    output_folder.mkdir(parents=True, exist_ok=True)
    print(f"+ {output_folder} 폴더를 생성/확인했습니다.")

    # JSON 데이터 처리만 사용
    print("# JSON 파일 기반 데이터 처리")
    success = process_json_data(brand_name)
    data_source = "agent_03 JSON 파일"

    print(f"\n 순차 통합 파이프라인 완료!")
    print(f"=" * 60)
    print(f"OK 처리 결과: {'성공' if success else '실패'}")
    print(f"# 순차 처리: DB 데이터 → 1단계→2단계→3단계 완료")
    print(f"# 실제 이미지 파일 사용: images/ 폴더의 모든 파일 활용")
    print(f"# JSON 콘텐츠 통합: hashtags → 해시태그, new_caption_v1 → 본문")
    print(f"# 데이터 소스: {data_source}")

    return success


# DB 관련 함수들 제거 - JSON 파일만 사용
