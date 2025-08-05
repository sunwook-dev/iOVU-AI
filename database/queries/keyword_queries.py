"""
Keyword-related database queries
"""
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime

from ..utils import get_db
from ..config import Tables

class KeywordQueries:
    """Queries for keyword extraction, clustering, and performance"""
    
    # ========== Keyword Extraction Jobs ==========
    
    @staticmethod
    def create_extraction_job(job_data: Dict[str, Any]) -> int:
        """Create a new keyword extraction job"""
        db = get_db()
        
        # Convert JSON fields
        json_fields = ['algorithm_config', 'extraction_params']
        for field in json_fields:
            if field in job_data and job_data[field] is not None:
                job_data[field] = json.dumps(job_data[field], ensure_ascii=False)
        
        return db.insert(Tables.KEYWORD_EXTRACTION_JOBS, job_data)
    
    @staticmethod
    def get_extraction_job(job_id: int) -> Optional[Dict[str, Any]]:
        """Get extraction job by ID"""
        db = get_db()
        query = f"SELECT * FROM {Tables.KEYWORD_EXTRACTION_JOBS} WHERE id = %s"
        result = db.execute_one(query, (job_id,))
        
        if result:
            # Parse JSON fields
            for field in ['algorithm_config', 'extraction_params']:
                if result.get(field):
                    result[field] = json.loads(result[field])
        
        return result
    
    @staticmethod
    def update_extraction_job(job_id: int, updates: Dict[str, Any]) -> int:
        """Update extraction job status"""
        db = get_db()
        
        if 'status' in updates:
            if updates['status'] == 'running' and 'started_at' not in updates:
                updates['started_at'] = datetime.now()
            elif updates['status'] in ['completed', 'failed'] and 'completed_at' not in updates:
                updates['completed_at'] = datetime.now()
        
        return db.update(Tables.KEYWORD_EXTRACTION_JOBS, updates, "id = %s", (job_id,))
    
    @staticmethod
    def get_pending_jobs(limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending extraction jobs"""
        db = get_db()
        query = f"""
        SELECT * FROM {Tables.KEYWORD_EXTRACTION_JOBS}
        WHERE status = 'pending'
        ORDER BY priority DESC, created_at ASC
        LIMIT %s
        """
        return db.execute(query, (limit,))
    
    # ========== Extracted Keywords ==========
    
    @staticmethod
    def insert_keywords(keywords: List[Dict[str, Any]]) -> int:
        """Batch insert extracted keywords"""
        db = get_db()
        
        if not keywords:
            return 0
        
        # Convert positions to JSON
        for kw in keywords:
            if 'positions' in kw and isinstance(kw['positions'], list):
                kw['positions'] = json.dumps(kw['positions'])
        
        # Batch insert
        columns = keywords[0].keys()
        placeholders = ', '.join(['%s'] * len(columns))
        query = f"""
        INSERT INTO {Tables.EXTRACTED_KEYWORDS} 
        ({', '.join(f'`{col}`' for col in columns)}) 
        VALUES ({placeholders})
        """
        
        values_list = [tuple(kw[col] for col in columns) for kw in keywords]
        return db.execute_many(query, values_list)
    
    @staticmethod
    def get_keywords_by_job(job_id: int) -> List[Dict[str, Any]]:
        """Get all keywords for a job"""
        db = get_db()
        query = f"""
        SELECT * FROM {Tables.EXTRACTED_KEYWORDS}
        WHERE job_id = %s
        ORDER BY combined_score DESC
        """
        results = db.execute(query, (job_id,))
        
        # Parse JSON fields
        for result in results:
            if result.get('positions'):
                result['positions'] = json.loads(result['positions'])
        
        return results
    
    @staticmethod
    def get_top_keywords(brand_id: int, limit: int = 100, 
                        category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get top keywords for a brand"""
        db = get_db()
        query = f"""
        SELECT 
            keyword,
            normalized_keyword,
            semantic_category,
            AVG(combined_score) as avg_score,
            COUNT(*) as frequency,
            MAX(is_brand_specific) as is_brand_specific
        FROM {Tables.EXTRACTED_KEYWORDS}
        WHERE brand_id = %s
        """
        params = [brand_id]
        
        if category:
            query += " AND semantic_category = %s"
            params.append(category)
        
        query += """
        GROUP BY keyword, normalized_keyword, semantic_category
        ORDER BY avg_score DESC
        LIMIT %s
        """
        params.append(limit)
        
        return db.execute(query, tuple(params))
    
    @staticmethod
    def update_keyword_approval(keyword_ids: List[int], approved: bool, 
                               approved_by: str) -> int:
        """Update keyword approval status"""
        db = get_db()
        
        if not keyword_ids:
            return 0
        
        placeholders = ', '.join(['%s'] * len(keyword_ids))
        query = f"""
        UPDATE {Tables.EXTRACTED_KEYWORDS}
        SET is_approved = %s, approved_by = %s, approved_at = %s
        WHERE id IN ({placeholders})
        """
        
        params = [approved, approved_by, datetime.now()] + keyword_ids
        
        with db.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    # ========== Keyword Clusters ==========
    
    @staticmethod
    def create_cluster(cluster_data: Dict[str, Any]) -> int:
        """Create a new keyword cluster"""
        db = get_db()
        
        # Convert JSON fields
        json_fields = ['sub_categories', 'common_attributes', 'algorithm_params']
        for field in json_fields:
            if field in cluster_data and cluster_data[field] is not None:
                cluster_data[field] = json.dumps(cluster_data[field], ensure_ascii=False)
        
        return db.insert(Tables.KEYWORD_CLUSTERS, cluster_data)
    
    @staticmethod
    def add_cluster_members(cluster_id: int, member_data: List[Dict[str, Any]]) -> int:
        """Add keywords to a cluster"""
        db = get_db()
        
        if not member_data:
            return 0
        
        # Add cluster_id to all members
        for member in member_data:
            member['cluster_id'] = cluster_id
        
        # Batch insert
        columns = member_data[0].keys()
        placeholders = ', '.join(['%s'] * len(columns))
        query = f"""
        INSERT INTO {Tables.KEYWORD_CLUSTER_MEMBERS} 
        ({', '.join(f'`{col}`' for col in columns)}) 
        VALUES ({placeholders})
        """
        
        values_list = [tuple(m[col] for col in columns) for m in member_data]
        return db.execute_many(query, values_list)
    
    @staticmethod
    def get_cluster_keywords(cluster_id: int) -> List[Dict[str, Any]]:
        """Get all keywords in a cluster"""
        db = get_db()
        query = f"""
        SELECT 
            k.*,
            cm.membership_score,
            cm.is_representative
        FROM {Tables.KEYWORD_CLUSTER_MEMBERS} cm
        JOIN {Tables.EXTRACTED_KEYWORDS} k ON cm.keyword_id = k.id
        WHERE cm.cluster_id = %s
        ORDER BY cm.membership_score DESC
        """
        return db.execute(query, (cluster_id,))
    
    # ========== Keyword Performance ==========
    
    @staticmethod
    def update_keyword_performance(keyword_id: int, metrics: Dict[str, Any]) -> int:
        """Update or insert keyword performance metrics"""
        db = get_db()
        
        # Check if record exists
        existing = db.execute_one(
            f"SELECT id FROM {Tables.KEYWORD_PERFORMANCE} WHERE keyword_id = %s",
            (keyword_id,)
        )
        
        if 'seasonal_pattern' in metrics and isinstance(metrics['seasonal_pattern'], dict):
            metrics['seasonal_pattern'] = json.dumps(metrics['seasonal_pattern'], ensure_ascii=False)
        
        if existing:
            return db.update(
                Tables.KEYWORD_PERFORMANCE,
                metrics,
                "keyword_id = %s",
                (keyword_id,)
            )
        else:
            metrics['keyword_id'] = keyword_id
            # Get brand_id from keyword
            kw = db.execute_one(
                f"SELECT brand_id FROM {Tables.EXTRACTED_KEYWORDS} WHERE id = %s",
                (keyword_id,)
            )
            if kw:
                metrics['brand_id'] = kw['brand_id']
            
            return db.insert(Tables.KEYWORD_PERFORMANCE, metrics)
    
    @staticmethod
    def increment_keyword_usage(keyword_id: int, usage_type: str = 'general') -> int:
        """Increment keyword usage count"""
        db = get_db()
        
        field_map = {
            'general': 'usage_count',
            'title': 'in_title_count',
            'description': 'in_description_count',
            'geo': 'geo_usage_count'
        }
        
        if usage_type not in field_map:
            usage_type = 'general'
        
        field = field_map[usage_type]
        
        query = f"""
        UPDATE {Tables.KEYWORD_PERFORMANCE}
        SET {field} = {field} + 1
        WHERE keyword_id = %s
        """
        
        with db.cursor() as cursor:
            cursor.execute(query, (keyword_id,))
            if cursor.rowcount == 0:
                # Create new record
                return KeywordQueries.update_keyword_performance(
                    keyword_id, {field: 1}
                )
            return cursor.rowcount
    
    # ========== Brand Keywords ==========
    
    @staticmethod
    def add_brand_keyword(keyword_data: Dict[str, Any]) -> int:
        """Add a brand-specific keyword"""
        db = get_db()
        return db.insert(Tables.BRAND_KEYWORDS, keyword_data)
    
    @staticmethod
    def get_brand_keywords(brand_id: int, 
                          keyword_type: Optional[str] = None,
                          active_only: bool = True) -> List[Dict[str, Any]]:
        """Get brand keywords"""
        db = get_db()
        query = f"""
        SELECT * FROM {Tables.BRAND_KEYWORDS}
        WHERE brand_id = %s
        """
        params = [brand_id]
        
        if keyword_type:
            query += " AND keyword_type = %s"
            params.append(keyword_type)
        
        if active_only:
            query += " AND is_active = TRUE"
            query += " AND (valid_from IS NULL OR valid_from <= CURDATE())"
            query += " AND (valid_until IS NULL OR valid_until >= CURDATE())"
        
        query += " ORDER BY priority DESC, keyword"
        
        return db.execute(query, tuple(params))
    
    @staticmethod
    def update_brand_keyword(keyword_id: int, updates: Dict[str, Any]) -> int:
        """Update brand keyword"""
        db = get_db()
        return db.update(Tables.BRAND_KEYWORDS, updates, "id = %s", (keyword_id,))
    
    # ========== Analytics ==========
    
    @staticmethod
    def get_keyword_statistics(brand_id: int) -> Dict[str, Any]:
        """Get keyword statistics for a brand"""
        db = get_db()
        
        stats = {}
        
        # Total keywords extracted
        query = f"""
        SELECT 
            COUNT(DISTINCT keyword) as unique_keywords,
            COUNT(*) as total_extractions,
            AVG(combined_score) as avg_score
        FROM {Tables.EXTRACTED_KEYWORDS}
        WHERE brand_id = %s
        """
        result = db.execute_one(query, (brand_id,))
        stats['extraction_stats'] = result
        
        # Keywords by category
        query = f"""
        SELECT 
            semantic_category,
            COUNT(DISTINCT keyword) as count
        FROM {Tables.EXTRACTED_KEYWORDS}
        WHERE brand_id = %s AND semantic_category IS NOT NULL
        GROUP BY semantic_category
        """
        results = db.execute(query, (brand_id,))
        stats['by_category'] = {r['semantic_category']: r['count'] for r in results}
        
        # Keywords by algorithm
        query = f"""
        SELECT 
            algorithm,
            COUNT(*) as count,
            AVG(algorithm_score) as avg_score
        FROM {Tables.EXTRACTED_KEYWORDS}
        WHERE brand_id = %s
        GROUP BY algorithm
        """
        results = db.execute(query, (brand_id,))
        stats['by_algorithm'] = results
        
        # Performance metrics
        query = f"""
        SELECT 
            COUNT(*) as tracked_keywords,
            AVG(click_through_rate) as avg_ctr,
            AVG(conversion_rate) as avg_conversion,
            SUM(usage_count) as total_usage
        FROM {Tables.KEYWORD_PERFORMANCE}
        WHERE brand_id = %s
        """
        result = db.execute_one(query, (brand_id,))
        stats['performance'] = result
        
        return stats