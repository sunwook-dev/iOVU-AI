#!/usr/bin/env python3
"""
Agent 03 Instagram Crawler DB 버전 실행 스크립트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from crawler.instagram_crawler_db import InstagramCrawlerDB

async def main():
    """메인 실행 함수"""
    print("Agent 03 Instagram Crawler (DB 버전) 시작")
    print("=" * 50)
    
    try:
        crawler = InstagramCrawlerDB()
        brand_id = 1  # kijun 브랜드 ID
        await crawler.run(brand_id)
        
    except Exception as e:
        print(f"크롤러 실행 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())