#!/usr/bin/env python3
"""
Run Blog GEO Analysis

블로그 E-E-A-T 및 GEO 분석을 실행하는 커맨드라인 인터페이스입니다.
"""


import argparse
import sys
import os
from pathlib import Path

# .env 환경변수 자동 로드
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agent_15_blog_geo.blog_geo_analyzer import create_blog_geo_analyzer


def main():
    """메인 진입점"""
    parser = argparse.ArgumentParser(
        description="블로그 콘텐츠에 대한 E-E-A-T 및 GEO 분석 실행"
    )

    # 필수 인자 (brand_id 제거)
    parser.add_argument(
        "platform", choices=["naver", "tistory"], help="분석할 블로그 플랫폼"
    )

    # 선택적 인자
    parser.add_argument("--brand-name", required=True, help="브랜드명 (필수)")
    parser.add_argument(
        "--posts-limit", type=int, default=10, help="분석할 최대 포스트 수 (기본값: 10)"
    )
    parser.add_argument(
        "--selective-count",
        type=int,
        default=2,
        help="컨설팅할 상위/하위 포스트 수 (기본값: 2)",
    )
    parser.add_argument(
        "--output-dir",
        default="../outputs",
        help="보고서 출력 디렉토리 (기본값: ../outputs)",
    )
    parser.add_argument(
        "--no-database", action="store_true", help="결과를 데이터베이스에 저장하지 않음"
    )
    parser.add_argument("--api-key", help="OpenAI API 키 (환경변수보다 우선)")

    args = parser.parse_args()

    # 분석기 생성
    try:
        from pathlib import Path

        output_path = Path(args.output_dir)
        if not output_path.is_absolute():
            # Always resolve relative path from modular_agents directory
            output_path = Path(__file__).parent / args.output_dir
        analyzer = create_blog_geo_analyzer(
            openai_api_key=args.api_key, output_dir=str(output_path)
        )
    except ValueError as e:
        print(f"❌ 초기화 오류: {e}")
        print(
            "OpenAI API 키를 --api-key 옵션을 사용하거나 OPENAI_API_KEY 환경변수를 설정하세요."
        )
        sys.exit(1)

    # 분석 실행
    print(f"\n=== {args.platform.upper()} 블로그 분석 시작...")
    print(f"   브랜드명: {args.brand_name}")
    print(f"   분석 대상: 최대 {args.posts_limit}개 포스트")
    print(
        f"   선택 대상: 상위 {args.selective_count}개 + 하위 {args.selective_count}개"
    )
    print()

    try:
        results = analyzer.analyze_blog(
            platform=args.platform,
            brand_id=None,
            brand_name=args.brand_name,
            total_posts_to_process=args.posts_limit,
            n_selective=args.selective_count,
            save_to_database=not args.no_database,
        )

        # 결과 요약 출력
        print("\n=== 분석 완료 요약:")
        print(f"   총 포스트: {results['total_posts_analyzed']}")
        print(f"   유효 분석: {results['valid_analyses']}")
        print(f"   컨설팅 대상: {results['posts_consulted']}")

        if results["average_scores"]:
            print(f"\n   평균 점수:")
            print(f"   - E-E-A-T: {results['average_scores']['eeat_average']}")
            print(f"   - GEO: {results['average_scores']['geo_average']}")
            print(f"   - 시너지: {results['average_scores']['synergy_average']}")
            print(f"   - 전체: {results['average_scores']['overall_average']}")

        print(f"\n=== 보고서 파일:")
        print(f"   - 분석 보고서: {results['analysis_report_path']}")
        print(f"   - 컨설팅 보고서: {results['consulting_report_path']}")

        # 생성된 이미지 표시
        image_count = sum(
            1
            for r in results["consulting_results"]
            if r.get("final_blog_image", "").endswith(".png")
        )
        if image_count > 0:
            print(f"\n=== 생성된 블로그 이미지: {image_count}개")
            for r in results["consulting_results"]:
                if r.get("final_blog_image", "").endswith(".png"):
                    print(f"   - {r['final_blog_image']}")

        print(
            f"\n✅ 분석이 완료되었습니다! (처리 시간: {results['processing_time']:.2f}초)"
        )

    except Exception as e:
        print(f"\n❌ 분석 중 오류 발생: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
