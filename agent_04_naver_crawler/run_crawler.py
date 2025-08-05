#!/usr/bin/env python3
"""
Naver Blog Crawler Runner
네이버 블로그 크롤러 실행 스크립트
"""
import argparse
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler import NaverBlogCrawler
from database.queries.brand_queries import BrandQueries
from config import Config


def crawl_single_brand(brand_official_name):
    """단일 브랜드 크롤링 (공식명 기준)"""
    brand = BrandQueries.get_brand_by_name(brand_official_name)
    if not brand:
        print(f"❌ 브랜드명 '{brand_official_name}'를 찾을 수 없습니다.")
        return

    print(f"🔍 브랜드 정보:")
    print(f"   - 이름: {brand['brand_official_name']}")

    # 크롤러 실행
    crawler = NaverBlogCrawler()
    result = crawler.crawl_brand_blogs(
        brand_official_name=brand["brand_official_name"],
        max_pages=Config.MAX_PAGES_PER_BRAND,
        posts_per_page=Config.POSTS_PER_PAGE,
    )

    return result


def crawl_all_brands():
    """모든 브랜드 크롤링"""
    brands = BrandQueries.list_brands()

    if not brands:
        print("❌ 크롤링할 브랜드가 없습니다.")
        return

    print(f"📋 총 {len(brands)}개 브랜드를 크롤링합니다.")
    print("-" * 60)

    results = []
    for idx, brand in enumerate(brands, 1):
        print(f"\n[{idx}/{len(brands)}] 브랜드: {brand['brand_official_name']}")
        try:
            result = crawl_single_brand(brand["brand_official_name"])
            if result:
                results.append(result)
        except Exception as e:
            print(f"❌ 크롤링 중 오류 발생: {e}")
            continue

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 크롤링 결과 요약:")
    print("-" * 60)

    total_crawled = sum(r["crawled_count"] for r in results)
    total_saved = sum(r["saved_count"] for r in results)

    print(f"✅ 성공한 브랜드: {len(results)}개")
    print(f"📄 크롤링한 포스트: {total_crawled}개")
    print(f"💾 저장된 포스트: {total_saved}개")


def main():
    parser = argparse.ArgumentParser(
        description="네이버 블로그 크롤러",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 특정 브랜드 크롤링
  python run_crawler.py --brand-name 'uniformbridge'
  
  # 모든 브랜드 크롤링
  python run_crawler.py --all
  
  # 커스텀 설정으로 크롤링
  python run_crawler.py --brand-name 'kijun' --max-pages 20
        """,
    )

    # 크롤링 대상 선택
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--brand-name", type=str, help="특정 브랜드 공식명으로 크롤링")
    group.add_argument("--all", action="store_true", help="모든 브랜드 크롤링")

    # 옵션
    parser.add_argument(
        "--max-pages",
        type=int,
        default=Config.MAX_PAGES_PER_BRAND,
        help=f"브랜드당 최대 크롤링 페이지 수 (기본: {Config.MAX_PAGES_PER_BRAND})",
    )

    args = parser.parse_args()

    # 설정 확인
    Config.ensure_directories()

    print("🚀 네이버 블로그 크롤러 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    try:
        if args.brand_name:
            # 커스텀 설정 적용
            if args.max_pages:
                Config.MAX_PAGES_PER_BRAND = args.max_pages

            crawl_single_brand(args.brand_name)
        else:
            crawl_all_brands()

    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()

    print(f"\n⏰ 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
