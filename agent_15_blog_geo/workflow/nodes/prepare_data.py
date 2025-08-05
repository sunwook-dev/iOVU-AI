"""
Data Preparation Node

데이터베이스에서 블로그 데이터를 로드하고 분석을 위해 준비합니다.
"""

import json
from typing import Dict, Any, List
import logging
import sys
import os

# 프로젝트 루트를 경로에 추가
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(project_root)

# from database.queries import DataQueries, BrandQueries
from ...database.queries import DataQueries, BrandQueries
from ..state import BlogGEOWorkflowState

logger = logging.getLogger(__name__)


def prepare_data_node(state: BlogGEOWorkflowState) -> Dict[str, Any]:
    """
    데이터베이스에서 블로그 데이터를 로드하고 준비

    이 노드는:
    1. 데이터베이스에서 원시 블로그 데이터 로드
    2. 분석을 위한 포스트 필터링 및 포맷팅
    3. 설정된 포스트 수로 제한

    Args:
        state: 현재 워크플로우 상태

    Returns:
        posts_to_analyze가 포함된 업데이트된 상태
    """
    logger.info("\n--- === [단계 1] 데이터 준비 ---")

    brand_name = state["brand_name"]
    platform = state["platform"]
    limit = state["total_posts_to_process"]

    # 데이터베이스 쿼리 초기화
    data_queries = DataQueries()

    try:
        # 데이터베이스에서 블로그 데이터 로드
        if platform == "naver":
            raw_data = data_queries.get_raw_naver_data(brand_name, limit=limit)
        elif platform == "tistory":
            raw_data = data_queries.get_raw_tistory_data(brand_name, limit=limit)
        else:
            raise ValueError(f"지원하지 않는 플랫폼: {platform}")

        if not raw_data:
            logger.info(
                f"❌ {platform} 블로그 데이터를 찾을 수 없습니다. brand_name: {brand_name}"
            )
            return {"posts_to_analyze": []}

        # 분석을 위한 포스트 포맷팅
        prepared_data = []

        for i, post in enumerate(raw_data):
            # 플랫폼 구조에 따라 포스트 데이터 추출
            post_data = post.get("data", {})

            if not post_data:
                post_data = post

            # 다양한 데이터 구조 처리
            if isinstance(post_data, list) and post_data:
                # 데이터가 포스트 리스트인 경우
                posts_list = post_data
            elif isinstance(post_data, dict) and "posts" in post_data:
                # 데이터에 'posts' 키가 있는 경우
                posts_list = post_data["posts"]
            else:
                # 단일 포스트 또는 다른 구조
                posts_list = [post_data] if isinstance(post_data, dict) else []

            # 각 포스트 처리
            for j, p in enumerate(posts_list):
                if not isinstance(p, dict):
                    continue
                prepared_post = {
                    "id": f"{i+1}_{j+1}",
                    "title": p.get("title", "제목 없음"),
                    "content": p.get("content") or p.get("full_content", "내용 없음"),
                    "image_urls": [],
                }

                # 이미지 URL 추출
                image_urls = p.get("image_urls", [])

                # 1) 문자열이면 → 리스트로 변환 시도
                if isinstance(image_urls, str):
                    try:
                        image_urls = json.loads(image_urls)  # JSON 문자열
                    except json.JSONDecodeError:
                        # 콤마/공백 구분
                        image_urls = [
                            u.strip() for u in image_urls.split(",") if u.strip()
                        ]

                if isinstance(image_urls, list):
                    # 유효한 URL 필터링
                    prepared_post["image_urls"] = [
                        url
                        for url in image_urls
                        if isinstance(url, str)
                        and url.startswith(("https://", "http://"))
                    ][
                        :5
                    ]  # 포스트당 최대 5개 이미지로 제한

                prepared_data.append(prepared_post)

        # 지정된 경우 제한 적용
        if limit:
            prepared_data = prepared_data[:limit]

        logger.info(
            f"✅ {len(prepared_data)}개의 {platform} 포스트 데이터를 준비했습니다."
        )

        return {"posts_to_analyze": prepared_data}

    except Exception as e:
        logger.error(f"❌ 데이터 준비 중 오류 발생: {e}")
        import traceback

        traceback.print_exc()

        state["errors"].append(
            {
                "node": "prepare_data",
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
        )

        return {"posts_to_analyze": []}
