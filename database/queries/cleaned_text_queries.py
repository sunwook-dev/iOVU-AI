"""
Cleaned text table queries
"""

from typing import Dict, List, Optional, Any
from ..utils import get_db


class CleanedTextQueries:
    """06_refined_web_data 테이블 관련 쿼리"""
    
    @staticmethod
    def get_cleaned_text_stats(brand_id: Optional[int] = None) -> Dict[str, Any]:
        """cleaned_text 통계 조회"""
        db = get_db()
        
        where_clause = ""
        params = []
        if brand_id:
            where_clause = "WHERE brand_id = %s"
            params = [brand_id]
        
        query = f"""
        SELECT 
            COUNT(*) as total_cleaned,
            AVG(word_count) as avg_word_count,
            AVG(unique_word_ratio) as avg_unique_ratio,
            SUM(word_count) as total_words,
            COUNT(DISTINCT brand_id) as total_01_brands,
            SUM(CASE WHEN cleaned_metadata IS NOT NULL THEN 1 ELSE 0 END) as with_metadata,
            SUM(brand_mentions_removed) as total_brand_mentions_removed
        FROM `06_refined_web_data`
        {where_clause}
        """
        
        return db.execute_one(query, params)
    
    @staticmethod
    def get_recent_cleaned_texts(limit: int = 10, brand_id: Optional[int] = None) -> List[Dict]:
        """최근 정제된 텍스트 조회"""
        db = get_db()
        
        where_clause = ""
        params = []
        if brand_id:
            where_clause = "WHERE cwt.brand_id = %s"
            params = [brand_id]
        
        query = f"""
        SELECT 
            cwt.id,
            cwt.brand_id,
            cwt.title,
            cwt.source_url,
            cwt.word_count,
            cwt.unique_word_ratio,
            cwt.cleaned_at,
            b.brand_official_name,
            b.brand_name_korean
        FROM `06_refined_web_data` cwt
        JOIN 01_brands b ON cwt.brand_id = b.id
        {where_clause}
        ORDER BY cwt.cleaned_at DESC
        LIMIT %s
        """
        
        params.append(limit)
        return db.execute(query, params)
    
    @staticmethod
    def search_cleaned_texts(keyword: str, brand_id: Optional[int] = None) -> List[Dict]:
        """정제된 텍스트 검색"""
        db = get_db()
        
        where_clauses = ["MATCH(cleaned_text) AGAINST(%s IN NATURAL LANGUAGE MODE)"]
        params = [keyword]
        
        if brand_id:
            where_clauses.append("brand_id = %s")
            params.append(brand_id)
        
        query = f"""
        SELECT 
            id,
            brand_id,
            title,
            source_url,
            SUBSTRING(cleaned_text, 1, 200) as excerpt,
            word_count,
            cleaned_at,
            MATCH(cleaned_text) AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance
        FROM `06_refined_web_data`
        WHERE {' AND '.join(where_clauses)}
        ORDER BY relevance DESC
        LIMIT 50
        """
        
        params.append(keyword)  # For relevance calculation
        return db.execute(query, params)
    
    @staticmethod
    def get_metadata_stats() -> Dict[str, Any]:
        """메타데이터 통계"""
        db = get_db()
        
        query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN cleaned_metadata IS NOT NULL THEN 1 ELSE 0 END) as with_metadata,
            SUM(CASE WHEN JSON_EXTRACT(cleaned_metadata, '$.keywords') IS NOT NULL 
                     AND JSON_LENGTH(JSON_EXTRACT(cleaned_metadata, '$.keywords')) > 0 
                THEN 1 ELSE 0 END) as with_keywords,
            SUM(CASE WHEN JSON_EXTRACT(cleaned_metadata, '$.og_data') IS NOT NULL 
                     AND JSON_LENGTH(JSON_EXTRACT(cleaned_metadata, '$.og_data')) > 0 
                THEN 1 ELSE 0 END) as with_og_data,
            SUM(CASE WHEN JSON_EXTRACT(cleaned_metadata, '$.structured_data') IS NOT NULL 
                     AND JSON_LENGTH(JSON_EXTRACT(cleaned_metadata, '$.structured_data')) > 0 
                THEN 1 ELSE 0 END) as with_structured_data
        FROM `06_refined_web_data`
        """
        
        return db.execute_one(query)
    
    
    @staticmethod
    def get_cleaning_performance_stats() -> Dict[str, Any]:
        """클리닝 성능 통계"""
        db = get_db()
        
        query = """
        SELECT 
            cleaning_version,
            COUNT(*) as count,
            AVG(processing_time_ms) as avg_processing_time,
            MIN(processing_time_ms) as min_processing_time,
            MAX(processing_time_ms) as max_processing_time,
            AVG(word_count) as avg_word_count
        FROM `06_refined_web_data`
        GROUP BY cleaning_version
        ORDER BY cleaning_version DESC
        """
        
        return db.execute(query)
    
    @staticmethod
    def update_cleaned_metadata(cleaned_text_id: int, metadata: Dict) -> bool:
        """cleaned_metadata 업데이트"""
        db = get_db()
        
        import json
        metadata_json = json.dumps(metadata, ensure_ascii=False)
        
        query = """
        UPDATE `06_refined_web_data`
        SET 
            cleaned_metadata = %s,
            updated_at = NOW()
        WHERE id = %s
        """
        
        return db.execute_one(query, (metadata_json, cleaned_text_id)) is not None