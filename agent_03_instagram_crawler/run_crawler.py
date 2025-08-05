#!/usr/bin/env python3
"""
Instagram 크롤러 실행기
Instagram 게시물을 크롤링하여 JSON 파일과 데이터베이스에 저장
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from crawler import InstagramCrawler, Config


async def main():
    """메인 진입점"""
    parser = argparse.ArgumentParser(description="Instagram 크롤러")
    parser.add_argument(
        "brand_id",
        type=int,
        help="크롤링할 브랜드 ID"
    )
    parser.add_argument(
        "--username",
        help="Instagram 사용자명 (.env 파일 우선)",
        default=None
    )
    parser.add_argument(
        "--password",
        help="Instagram 비밀번호 (.env 파일 우선)",
        default=None
    )
    parser.add_argument(
        "--max-scroll",
        type=int,
        help="최대 스크롤 횟수 (.env 파일 우선)",
        default=None
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="크롤링 배치 크기 (.env 파일 우선)",
        default=None
    )
    
    args = parser.parse_args()
    
    # 명령줄 인수로 설정 덮어쓰기
    if args.max_scroll:
        Config.MAX_SCROLL_ROUND = args.max_scroll
    if args.batch_size:
        Config.CRAWL_BATCH_SIZE = args.batch_size
    
    # 데이터 디렉토리 존재 확인
    Config.ensure_data_dirs()
    
    # 크롤러 인스턴스 생성
    crawler = InstagramCrawler(
        username=args.username,
        password=args.password
    )
    
    print(f"Instagram 크롤러 시작 - 브랜드 ID: {args.brand_id}")
    print(f"최대 스크롤 횟수: {Config.MAX_SCROLL_ROUND}")
    print(f"배치 크기: {Config.CRAWL_BATCH_SIZE}")
    print(f"데이터 디렉토리: {Config.DATA_DIR}")
    
    try:
        # 크롤러 실행
        await crawler.run(args.brand_id)
        print("\n✅ Instagram 크롤링 성공적으로 완료!")
    except Exception as e:
        print(f"\n❌ 크롤링 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())