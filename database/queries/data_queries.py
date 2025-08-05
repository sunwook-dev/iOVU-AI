"""
Data-related database queries for crawling, refining, and content management
"""
from typing import Dict, List, Optional, Any, Tuple
import json
import hashlib
from datetime import datetime, timedelta

from ..utils import get_db
from ..config import Tables

class DataQueries:
    """Queries for raw data, refined content, and processing"""
    
    # ========== Raw Data Queries ==========
    
    @staticmethod
    def insert_raw_web_data(data: Dict[str, Any]) -> int:
        """Insert raw web crawling data"""
        db = get_db()
        
        # Calculate content hash if HTML provided
        if 'raw_html' in data and data['raw_html']:
            data['content_hash'] = hashlib.sha256(
                data['raw_html'].encode('utf-8')
            ).hexdigest()
        
        # Convert JSON fields
        json_fields = ['og_data', 'structured_data', 'response_headers']
        for field in json_fields:
            if field in data and data[field] is not None:
                data[field] = json.dumps(data[field], ensure_ascii=False)
        
        return db.insert(Tables.RAW_WEB_DATA, data)
    
    @staticmethod
    def insert_03_raw_instagram_data(data: Dict[str, Any]) -> int:
        """Insert raw Instagram data"""
        db = get_db()
        
        # Convert JSON fields
        json_fields = ['hashtags', 'mentions', 'location_info', 'media_urls', 
                      'sponsor_tags', 'raw_data']
        for field in json_fields:
            if field in data and data[field] is not None:
                data[field] = json.dumps(data[field], ensure_ascii=False)
        
        return db.insert(Tables.RAW_INSTAGRAM_DATA, data)
    
    @staticmethod
    def insert_raw_naver_data(data: Dict[str, Any]) -> int:
        """Insert raw Naver blog data"""
        db = get_db()
        
        # Convert JSON fields
        json_fields = ['images', 'raw_data']
        for field in json_fields:
            if field in data and data[field] is not None:
                data[field] = json.dumps(data[field], ensure_ascii=False)
        
        return db.insert(Tables.RAW_NAVER_BLOG_DATA, data)
    
    @staticmethod
    def insert_raw_tistory_data(data: Dict[str, Any]) -> int:
        """Insert raw Tistory data"""
        db = get_db()
        
        # Convert JSON fields
        json_fields = ['tags', 'images', 'raw_data']
        for field in json_fields:
            if field in data and data[field] is not None:
                data[field] = json.dumps(data[field], ensure_ascii=False)
        
        return db.insert(Tables.RAW_TISTORY_DATA, data)
    
    @staticmethod
    def check_url_exists(brand_id: int, url: str, table: str) -> bool:
        """Check if URL already exists in raw data"""
        db = get_db()
        
        if table == 'web':
            query = f"SELECT id FROM {Tables.RAW_WEB_DATA} WHERE brand_id = %s AND url = %s"
        elif table == 'instagram':
            return False  # Instagram uses post_id, not URL
        elif table == 'naver':
            query = f"SELECT id FROM {Tables.RAW_NAVER_BLOG_DATA} WHERE brand_id = %s AND blog_url = %s"
        elif table == 'tistory':
            query = f"SELECT id FROM {Tables.RAW_TISTORY_DATA} WHERE brand_id = %s AND blog_url = %s"
        else:
            return False
        
        result = db.execute_one(query, (brand_id, url))
        return result is not None
    
    @staticmethod
    def check_instagram_post_exists(brand_id: int, post_id: str) -> bool:
        """Check if Instagram post already exists"""
        db = get_db()
        query = f"SELECT id FROM {Tables.RAW_INSTAGRAM_DATA} WHERE brand_id = %s AND post_id = %s"
        result = db.execute_one(query, (brand_id, post_id))
        return result is not None
    
    @staticmethod
    def get_unprocessed_raw_data(brand_id: int, platform: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get raw data that hasn't been refined yet"""
        db = get_db()
        
        # Map platform to table
        table_map = {
            'web': Tables.RAW_WEB_DATA,
            'instagram': Tables.RAW_INSTAGRAM_DATA,
            'naver': Tables.RAW_NAVER_BLOG_DATA,
            'tistory': Tables.RAW_TISTORY_DATA
        }
        
        if platform not in table_map:
            return []
        
        table = table_map[platform]
        
        # Find records not in refined_content
        query = f"""
        SELECT r.* 
        FROM {table} r
        LEFT JOIN {Tables.REFINED_CONTENT} rc 
            ON rc.source_table = %s AND rc.source_id = r.id
        WHERE r.brand_id = %s AND rc.id IS NULL
        LIMIT %s
        """
        
        return db.execute(query, (platform, brand_id, limit))
    
    # ========== Refined Content Queries ==========
    
    @staticmethod
    def insert_refined_content(data: Dict[str, Any]) -> int:
        """Insert refined content"""
        db = get_db()
        
        # Convert JSON fields
        json_fields = ['key_points', 'entities', 'topics', 'categories']
        for field in json_fields:
            if field in data and data[field] is not None:
                data[field] = json.dumps(data[field], ensure_ascii=False)
        
        return db.insert(Tables.REFINED_CONTENT, data)
    
    @staticmethod
    def get_refined_content(content_id: int) -> Optional[Dict[str, Any]]:
        """Get refined content by ID"""
        db = get_db()
        query = f"SELECT * FROM {Tables.REFINED_CONTENT} WHERE id = %s"
        result = db.execute_one(query, (content_id,))
        
        if result:
            # Parse JSON fields
            json_fields = ['key_points', 'entities', 'topics', 'categories']
            for field in json_fields:
                if result.get(field):
                    result[field] = json.loads(result[field])
        
        return result
    
    @staticmethod
    def list_refined_content(brand_id: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List refined content with filters"""
        db = get_db()
        query = f"SELECT * FROM {Tables.REFINED_CONTENT} WHERE brand_id = %s"
        params = [brand_id]
        
        if filters:
            if 'source_table' in filters:
                query += " AND source_table = %s"
                params.append(filters['source_table'])
            
            if 'quality_score_min' in filters:
                query += " AND quality_score >= %s"
                params.append(filters['quality_score_min'])
            
            if 'language' in filters:
                query += " AND language = %s"
                params.append(filters['language'])
            
            if 'date_from' in filters:
                query += " AND refined_at >= %s"
                params.append(filters['date_from'])
        
        query += " ORDER BY refined_at DESC"
        return db.execute(query, tuple(params))
    
    @staticmethod
    def update_refined_content_quality(content_id: int, scores: Dict[str, float]) -> int:
        """Update quality scores for refined content"""
        db = get_db()
        return db.update(Tables.REFINED_CONTENT, scores, "id = %s", (content_id,))
    
    # ========== Content Segments ==========
    
    @staticmethod
    def insert_content_segments(segments: List[Dict[str, Any]]) -> int:
        """Insert multiple content segments"""
        db = get_db()
        
        if not segments:
            return 0
        
        # Prepare data
        for segment in segments:
            if 'extracted_products' in segment and segment['extracted_products']:
                segment['extracted_products'] = json.dumps(
                    segment['extracted_products'], ensure_ascii=False
                )
        
        # Batch insert
        columns = segments[0].keys()
        placeholders = ', '.join(['%s'] * len(columns))
        query = f"""
        INSERT INTO {Tables.CONTENT_SEGMENTS} 
        ({', '.join(f'`{col}`' for col in columns)}) 
        VALUES ({placeholders})
        """
        
        values_list = [tuple(seg[col] for col in columns) for seg in segments]
        return db.execute_many(query, values_list)
    
    # ========== Crawl Sessions ==========
    
    @staticmethod
    def create_crawl_session(session_data: Dict[str, Any]) -> int:
        """Create a new crawl session"""
        db = get_db()
        
        if 'config' in session_data and isinstance(session_data['config'], dict):
            session_data['config'] = json.dumps(session_data['config'], ensure_ascii=False)
        
        session_data['started_at'] = datetime.now()
        return db.insert(Tables.CRAWL_SESSIONS, session_data)
    
    @staticmethod
    def update_crawl_session(session_id: int, updates: Dict[str, Any]) -> int:
        """Update crawl session status"""
        db = get_db()
        
        if 'error_log' in updates and isinstance(updates['error_log'], list):
            updates['error_log'] = json.dumps(updates['error_log'], ensure_ascii=False)
        
        if 'status' in updates and updates['status'] in ['completed', 'failed', 'cancelled']:
            updates['completed_at'] = datetime.now()
        
        return db.update(Tables.CRAWL_SESSIONS, updates, "id = %s", (session_id,))
    
    @staticmethod
    def get_active_sessions(brand_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get active crawl sessions"""
        db = get_db()
        query = f"""
        SELECT * FROM {Tables.CRAWL_SESSIONS} 
        WHERE status IN ('pending', 'running')
        """
        params = []
        
        if brand_id:
            query += " AND brand_id = %s"
            params.append(brand_id)
        
        query += " ORDER BY created_at DESC"
        return db.execute(query, tuple(params) if params else None)
    
    # ========== Processing Logs ==========
    
    @staticmethod
    def create_refinement_log(log_data: Dict[str, Any]) -> int:
        """Create refinement process log"""
        db = get_db()
        
        if 'error_details' in log_data and isinstance(log_data['error_details'], list):
            log_data['error_details'] = json.dumps(log_data['error_details'], ensure_ascii=False)
        
        log_data['started_at'] = datetime.now()
        return db.insert(Tables.REFINEMENT_LOGS, log_data)
    
    @staticmethod
    def update_refinement_log(log_id: int, updates: Dict[str, Any]) -> int:
        """Update refinement log"""
        db = get_db()
        
        if 'completed_at' not in updates:
            updates['completed_at'] = datetime.now()
        
        return db.update(Tables.REFINEMENT_LOGS, updates, "id = %s", (log_id,))
    
    # ========== Analytics Queries ==========
    
    @staticmethod
    def get_content_statistics(brand_id: int, days: int = 30) -> Dict[str, Any]:
        """Get content statistics for a brand"""
        db = get_db()
        
        date_threshold = datetime.now() - timedelta(days=days)
        stats = {}
        
        # Raw data counts by platform
        for platform, table in [
            ('web', Tables.RAW_WEB_DATA),
            ('instagram', Tables.RAW_INSTAGRAM_DATA),
            ('naver', Tables.RAW_NAVER_BLOG_DATA),
            ('tistory', Tables.RAW_TISTORY_DATA)
        ]:
            query = f"""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN crawled_at >= %s THEN 1 END) as recent
            FROM {table}
            WHERE brand_id = %s
            """
            result = db.execute_one(query, (date_threshold, brand_id))
            stats[f'{platform}_raw'] = {
                'total': result['total'],
                'recent': result['recent']
            }
        
        # Refined content stats
        query = f"""
        SELECT 
            COUNT(*) as total,
            AVG(quality_score) as avg_quality,
            AVG(relevance_score) as avg_relevance,
            COUNT(CASE WHEN quality_score >= 0.7 THEN 1 END) as high_quality_count
        FROM {Tables.REFINED_CONTENT}
        WHERE brand_id = %s
        """
        result = db.execute_one(query, (brand_id,))
        stats['refined'] = {
            'total': result['total'],
            'avg_quality': float(result['avg_quality']) if result['avg_quality'] else 0,
            'avg_relevance': float(result['avg_relevance']) if result['avg_relevance'] else 0,
            'high_quality_count': result['high_quality_count']
        }
        
        return stats
    
    @staticmethod
    def search_content(brand_id: int, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Full-text search in refined content"""
        db = get_db()
        query = f"""
        SELECT id, source_table, source_url, summary, quality_score,
               MATCH(refined_text, summary) AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance
        FROM {Tables.REFINED_CONTENT}
        WHERE brand_id = %s 
          AND MATCH(refined_text, summary) AGAINST(%s IN NATURAL LANGUAGE MODE)
        ORDER BY relevance DESC
        LIMIT %s
        """
        return db.execute(query, (search_term, brand_id, search_term, limit))