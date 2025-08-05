"""
Instagram 크롤러 실행 스크립트 (JSON 저장용)
"""
import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 파이썬 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from crawler.instagram_crawler import InstagramCrawler

async def main():
    """메인 실행 함수"""
    
    # 크롤링할 Instagram 핸들 설정
    instagram_handle = "kijun_official"  # 여기에 원하는 Instagram 핸들을 입력
    
    # 명령행 인수로 핸들을 받을 수 있도록 설정
    if len(sys.argv) > 1:
        instagram_handle = sys.argv[1]
        print(f"📋 명령행에서 Instagram 핸들 설정: @{instagram_handle}")
    
    # 환경 변수 확인
    from dotenv import load_dotenv
    load_dotenv()
    
    username = os.getenv('INSTAGRAM_USERNAME')
    password = os.getenv('INSTAGRAM_PASSWORD')
    
    if not username or not password:
        print("❌ Instagram 로그인 정보가 설정되지 않았습니다.")
        print("📝 .env 파일에 다음을 추가하세요:")
        print("INSTAGRAM_USERNAME=your_username")
        print("INSTAGRAM_PASSWORD=your_password")
        return
    
    try:
        # 크롤러 초기화
        crawler = InstagramCrawler(username=username, password=password)
        
        print(f"🚀 Instagram 크롤링 시작: @{instagram_handle}")
        print("📁 JSON 파일로 저장됩니다.")
        print("-" * 50)
        
        # 크롤링 실행
        await crawler.run(instagram_handle)
        
        print("-" * 50)
        print("✅ 크롤링 완료!")
        print(f"📂 저장 위치: {crawler.data_dir}")
        print("📄 저장된 파일:")
        print(f"   - {instagram_handle}.json (기본 게시물)")
        print(f"   - {instagram_handle}_detailed.json (상세 정보)")
        print(f"   - {instagram_handle}_tagged.json (태그된 게시물)")
        print(f"   - {instagram_handle}_tagged_detailed.json (태그된 게시물 상세)")
        
    except Exception as e:
        print(f"❌ 크롤링 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(main())
