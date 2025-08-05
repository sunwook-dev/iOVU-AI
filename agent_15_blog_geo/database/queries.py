"""
Database queries for Blog GEO Analysis
"""

import sys
import os
from typing import List, Dict, Optional, Any
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from database.utils import get_db


class DataQueries:
    def get_raw_tistory_data(
        self, brand_name: str, limit: Optional[int] = None
    ) -> List[Dict]:
        """Get raw Tistory blog data (brand_name 기준)"""

        query = """
        SELECT
            rtd.id,
            rtd.brand_name,
            rtd.blog_name            AS blog_id,        -- 블로그 ID
            rtd.post_title           AS title,          -- 별칭
            rtd.post_content         AS content,        -- 원본 본문
            rtd.blog_url             AS post_url,
            rtd.author_name,
            rtd.posted_at            AS published_date,
            rtd.tags,
            COALESCE(rtd.images, '[]') AS image_urls   -- images → image_urls
        FROM 05_raw_tistory_data rtd
        WHERE rtd.brand_name = %s
        ORDER BY rtd.posted_at DESC
        """

        if limit:
            query += " LIMIT %s"
            params = (brand_name, limit)
        else:
            params = (brand_name,)

        # ---------- 3) 실행 ----------
        with get_db() as conn, conn.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        # ---------- 4) 분석 파이프라인이 기대하는 포맷으로 변환 ----------
        formatted: List[Dict[str, Any]] = []
        for row in rows:
            post = {
                "id": row["id"],
                "brand_name": row["brand_name"],
                "blog_id": row["blog_id"],
                "title": row["title"],
                "content": row["content"],
                "full_content": row["content"],
                "url": row["post_url"],
                "author": row.get("author_name", ""),
                "published_date": (
                    row["published_date"].isoformat() if row["published_date"] else None
                ),
                "tags": json.loads(row["tags"] or "[]"),
                "image_urls": json.loads(row["image_urls"] or "[]"),
                # view_count, like_count, comment_count 컬럼이 없으므로 기본값 0
                "view_count": 0,
                "like_count": 0,
                "comment_count": 0,
            }
            formatted.append({"data": {"posts": [post]}})

        return formatted

    """Queries for blog data"""

    def __init__(self):
        self.db = None

    def _get_connection(self):
        """Get database connection"""
        if not self.db:
            self.db = get_db()
        return self.db

    def get_raw_naver_data(
        self, brand_name: str, limit: Optional[int] = None
    ) -> List[Dict]:
        """Get raw Naver blog data (brand_name 기준)"""

        query = """
        SELECT
            id,
            brand_name,
            blog_id,
            post_title      AS title,
            post_content    AS content,
            blog_url        AS post_url,
            author_name,                                
            COALESCE(images, '[]') AS image_urls,
            posted_at       AS published_date,
            tags,
            view_count,
            like_count,
            comment_count
        FROM raw_naver_blog_data
        WHERE brand_name = %s
        ORDER BY posted_at DESC
        """

        if limit:
            query += " LIMIT %s"
            params = (brand_name, limit)
        else:
            params = (brand_name,)

        with get_db() as conn, conn.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        formatted: List[Dict[str, Any]] = []
        for row in rows:
            post = {
                "id": row["id"],
                "brand_name": row["brand_name"],
                "blog_id": row["blog_id"],
                "title": row["title"],
                "content": row["content"],
                "full_content": row["content"],
                "url": row["post_url"],
                "author": row.get("author_name", ""),
                "published_date": (
                    row["published_date"].isoformat() if row["published_date"] else None
                ),
                "tags": json.loads(row["tags"] or "[]"),
                "image_urls": json.loads(row["image_urls"] or "[]"),
                "view_count": row["view_count"],
                "like_count": row["like_count"],
                "comment_count": row["comment_count"],
            }
            formatted.append({"data": {"posts": [post]}})

        return formatted

    def __del__(self):
        """Clean up database connection"""
        if self.db:
            self.db.close()


class BrandQueries:
    """Queries for brand information"""

    def __init__(self):
        self.db = None

    def _get_connection(self):
        """Get database connection"""
        if not self.db:
            self.db = get_db()
        return self.db

    def get_brand_by_id(self, brand_id: int) -> Optional[Dict]:
        """Get brand information by ID"""

        query = """
        SELECT 
            id,
            brand_official_name,
            brand_domain_tree,
            founding_year,
            hq_country,
            price_positioning,
            mission_tagline,
            primary_demographics,
            geographic_targets,
            brand_personality,
            brand_story,
            created_at,
            updated_at
        FROM brands
        WHERE id = %s
        """

        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (brand_id,))
                row = cursor.fetchone()

        if not row:
            return None

        # JSON 컬럼들은 파싱
        jloads = lambda x: json.loads(x) if x else []

        return {
            "brand_id": row["id"],
            "brand_official_name": row["brand_official_name"],
            "domain_tree": row["brand_domain_tree"],
            "founding_year": row["founding_year"],
            "hq_country": row["hq_country"],
            "price_positioning": row["price_positioning"],
            "mission_tagline": row["mission_tagline"],
            "primary_demographics": jloads(row["primary_demographics"]),
            "geographic_targets": jloads(row["geographic_targets"]),
            "brand_personality": jloads(row["brand_personality"]),
            "brand_story": row["brand_story"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        }

    def __del__(self):
        """Clean up database connection"""
        if self.db:
            self.db.close()


class BlogGEOQueries:
    """Queries for Blog GEO analysis results"""

    def __init__(self):
        self.db = None

    def _get_connection(self):
        """Get database connection"""
        if not self.db:
            self.db = get_db()
        return self.db

    def save_analysis_result(self, analysis_data: Dict) -> int:
        """Save blog GEO analysis result"""

        with get_db() as conn:
            with conn.cursor() as cursor:
                query = """
                INSERT INTO blog_geo_analyses (
                    brand_id,
                    platform,
                    total_posts_analyzed,
                    posts_consulted,
                    n_selective,
                    created_at,
                    completed_at,
                    analysis_report_path,
                    consulting_report_path,
                    average_eeat_score,
                    average_geo_score,
                    average_synergy_score,
                    overall_score,
                    summary
                ) VALUES (
                    %(brand_id)s,
                    %(platform)s,
                    %(total_posts_analyzed)s,
                    %(posts_consulted)s,
                    %(n_selective)s,
                    %(created_at)s,
                    %(completed_at)s,
                    %(analysis_report_path)s,
                    %(consulting_report_path)s,
                    %(average_eeat_score)s,
                    %(average_geo_score)s,
                    %(average_synergy_score)s,
                    %(overall_score)s,
                    %(summary)s
                )
                """

                # Convert summary to JSON string
                if "summary" in analysis_data and not isinstance(
                    analysis_data["summary"], str
                ):
                    analysis_data["summary"] = json.dumps(
                        analysis_data["summary"], ensure_ascii=False
                    )

                cursor.execute(query, analysis_data)
                conn.commit()

                last_id = cursor.lastrowid

        return last_id

    def get_analysis_history(
        self, brand_id: int, platform: Optional[str] = None, limit: int = 10
    ) -> List[Dict]:
        """Get analysis history for a brand"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
            SELECT 
                id,
                platform,
                created_at,
                total_posts_analyzed,
                posts_consulted,
                overall_score,
                analysis_report_path,
                consulting_report_path
            FROM blog_geo_analyses
            WHERE brand_id = %s
            """

            params = [brand_id]

            if platform:
                query += " AND platform = %s"
                params.append(platform)

            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            results = cursor.fetchall()

            return [
                {
                    "id": row["id"],
                    "platform": row["platform"],
                    "created_at": (
                        row["created_at"].isoformat() if row["created_at"] else None
                    ),
                    "posts_analyzed": row["total_posts_analyzed"],
                    "posts_consulted": row["posts_consulted"],
                    "overall_score": row["overall_score"],
                    "report_paths": {
                        "analysis": row["analysis_report_path"],
                        "consulting": row["consulting_report_path"],
                    },
                }
                for row in results
            ]

        finally:
            cursor.close()

    def __del__(self):
        """Clean up database connection"""
        if self.db:
            self.db.close()
