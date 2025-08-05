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
        self, brand_id: int, limit: Optional[int] = None
    ) -> List[Dict]:
        """Get raw Tistory blog data (네이버와 동일 포맷)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
            SELECT 
                rtd.id,
                rtd.brand_id,
                rtd.blog_id,
                rtd.post_title,
                COALESCE(rc.refined_text, rtd.post_content) AS content,
                rtd.post_url,
                rtd.author,
                rtd.published_date,
                rtd.tags,
                COALESCE(rtd.image_urls, '[]') AS image_urls,
                rtd.view_count,
                rtd.like_count,
                rtd.comment_count,
                rc.refined_text,
                rc.summary,
                rc.key_points,
                rc.quality_score
            FROM raw_tistory_data rtd
            LEFT JOIN refined_content rc ON (
                rc.source_table = 'tistory'
                AND rc.source_id = rtd.id
                AND rc.brand_id = rtd.brand_id
            )
            WHERE rtd.brand_id = %s
            ORDER BY rtd.published_date DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (brand_id,))
            results = cursor.fetchall()

            formatted_results = []
            for row in results:
                post_data = {
                    "id": row["id"],
                    "brand_id": row["brand_id"],
                    "blog_id": row["blog_id"],
                    "title": row["post_title"],
                    "content": row["content"],
                    "full_content": row["content"],
                    "url": row["post_url"],
                    "author": row["author"],
                    "published_date": (
                        row["published_date"].isoformat()
                        if row["published_date"]
                        else None
                    ),
                    "tags": json.loads(row["tags"]) if row["tags"] else [],
                    "image_urls": (
                        json.loads(row["image_urls"]) if row["image_urls"] else []
                    ),
                    "view_count": row["view_count"],
                    "like_count": row["like_count"],
                    "comment_count": row["comment_count"],
                    "refined_text": row["refined_text"],
                    "summary": row["summary"],
                    "key_points": (
                        json.loads(row["key_points"]) if row["key_points"] else []
                    ),
                    "quality_score": row["quality_score"],
                }
                # 네이버와 동일하게 래핑
                formatted_results.append({"data": {"posts": [post_data]}})
            return formatted_results
        finally:
            cursor.close()

    """Queries for blog data"""

    def __init__(self):
        self.db = None

    def _get_connection(self):
        """Get database connection"""
        if not self.db:
            self.db = get_db()
        return self.db

    def get_raw_naver_data(
        self, brand_id: int, limit: Optional[int] = None
    ) -> List[Dict]:
        """Get raw Naver blog data"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
            SELECT 
                rnd.id,
                rnd.brand_id,
                rnd.blog_id,
                rnd.post_title,
                COALESCE(rc.refined_text, rnd.post_content) AS content,
                rnd.post_url,
                rnd.author,
                rnd.published_date,
                rnd.tags,
                COALESCE(rnd.image_urls, '[]') AS image_urls,
                rnd.view_count,
                rnd.like_count,
                rnd.comment_count,
                rc.refined_text,
                rc.summary,
                rc.key_points,
                rc.quality_score
            FROM raw_naver_data rnd
            LEFT JOIN refined_content rc ON (
                rc.source_table = 'naver'
                AND rc.source_id = rnd.id
                AND rc.brand_id = rnd.brand_id
            )
            WHERE rnd.brand_id = %s
            ORDER BY rnd.published_date DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (brand_id,))
            results = cursor.fetchall()

            # Format results
            formatted_results = []
            for row in results:
                post_data = {
                    "id": row["id"],
                    "brand_id": row["brand_id"],
                    "blog_id": row["blog_id"],
                    "title": row["post_title"],
                    "content": row["content"],
                    "full_content": row["content"],
                    "url": row["post_url"],
                    "author": row["author"],
                    "published_date": (
                        row["published_date"].isoformat()
                        if row["published_date"]
                        else None
                    ),
                    "tags": json.loads(row["tags"]) if row["tags"] else [],
                    "image_urls": (
                        json.loads(row["image_urls"]) if row["image_urls"] else []
                    ),
                    "view_count": row["view_count"],
                    "like_count": row["like_count"],
                    "comment_count": row["comment_count"],
                    "refined_text": row["refined_text"],
                    "summary": row["summary"],
                    "key_points": (
                        json.loads(row["key_points"]) if row["key_points"] else []
                    ),
                    "quality_score": row["quality_score"],
                }

                # Wrap in expected format
                formatted_results.append({"data": {"posts": [post_data]}})

            return formatted_results

        finally:
            cursor.close()

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
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
            SELECT 
                id,
                name,
                domain,
                description,
                business_type,
                target_audience,
                main_products
            FROM brands
            WHERE id = %s
            """

            cursor.execute(query, (brand_id,))
            result = cursor.fetchone()

            if result:
                return {
                    "brand_id": result["id"],
                    "brand_official_name": result["name"],
                    "domain": result["domain"],
                    "description": result["description"],
                    "business_type": result["business_type"],
                    "target_audience": (
                        json.loads(result["target_audience"])
                        if result["target_audience"]
                        else []
                    ),
                    "main_products": (
                        json.loads(result["main_products"])
                        if result["main_products"]
                        else []
                    ),
                }

            return None

        finally:
            cursor.close()

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
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
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

            return cursor.lastrowid

        finally:
            cursor.close()

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
