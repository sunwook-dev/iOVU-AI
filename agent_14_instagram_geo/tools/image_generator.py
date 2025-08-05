"""
이미지 생성기
"""
import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def generate_images(content_filename):
    """2단계: 이미지 생성"""
    print(f"\n🎨 2단계: 이미지 생성 시작")
    
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API 키가 .env 파일에 설정되지 않았습니다.")
        return False
    
    client = OpenAI(api_key=api_key)
    
    try:
        with open(content_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        low_score_revisions = data.get('low_score_revisions', [])
        if not low_score_revisions:
            print("⚠️ low_score_revisions 데이터를 찾을 수 없습니다.")
            return False
        
        draft = low_score_revisions[0]
        image_generation_prompt = draft.get('new_image_idea', '')
        
        if image_generation_prompt:
            print(f"▶ 이미지 생성 프롬프트: \"{image_generation_prompt[:100]}...\"")
            
            # DALL-E 3 API 호출
            response = client.images.generate(
                model="dall-e-3",
                prompt=f"Instagram fashion post style: {image_generation_prompt}",
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            generated_image_url = response.data[0].url
            print("✅ 이미지 생성 완료!")
            
            # 이미지 다운로드 및 저장
            image_data = requests.get(generated_image_url).content
            
            # Always save to modular_agents/outputs directory
            from pathlib import Path
            current_file = Path(__file__)  # agent_14_instagram_geo/tools/image_generator.py
            modular_agents_dir = current_file.parent.parent.parent  # Go up to modular_agents
            output_path = modular_agents_dir / "outputs"
            output_path.mkdir(parents=True, exist_ok=True)
            save_path = output_path / "final_generated_image_kijun.jpg"
            
            with open(save_path, "wb") as f:
                f.write(image_data)
            save_path = str(save_path)
            print(f"✅ 2단계 완료 - 생성 이미지 저장: {save_path}")
            
            return save_path
        else:
            print("❌ new_image_idea를 찾을 수 없습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 이미지 생성 실패: {e}")
        return False


class ImageGenerator:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
    
    def generate_image(self, content_filename):
        """콘텐츠 파일을 기반으로 이미지 생성"""
        return generate_images(content_filename)
