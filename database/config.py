"""
Database Configuration
"""
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    # Connection settings
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '3306'))
    user: str = os.getenv('DB_USER', 'root')
    password: str = os.getenv('DB_PASSWORD', '')
    database: str = os.getenv('DB_NAME', 'modular_agents_db')
    
    # Connection pool settings
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '10'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    pool_timeout: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    pool_recycle: int = int(os.getenv('DB_POOL_RECYCLE', '3600'))
    
    # Query settings
    echo: bool = os.getenv('DB_ECHO', 'false').lower() == 'true'
    slow_query_threshold: float = float(os.getenv('DB_SLOW_QUERY_THRESHOLD', '1.0'))
    
    # Charset and collation
    charset: str = 'utf8mb4'
    collation: str = 'utf8mb4_unicode_ci'
    
    @property
    def connection_string(self) -> str:
        """Get MySQL connection string"""
        return (
            f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}"
            f"/{self.database}?charset={self.charset}"
        )
    
    @property
    def connection_params(self) -> dict:
        """Get connection parameters as dict"""
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'charset': self.charset,
            'cursorclass': 'DictCursor'  # Return results as dictionaries
        }

# Global config instance
db_config = DatabaseConfig()

# Table name constants
class Tables:
    """Database table names"""
    # Core tables
    BRANDS = '01_brands'
    PRODUCTS = 'products'
    
    # Raw data tables
    RAW_WEB_DATA = '02_raw_web_data'
    RAW_INSTAGRAM_DATA = '03_raw_instagram_data'
    RAW_NAVER_BLOG_DATA = 'raw_naver_blog_data'
    RAW_TISTORY_DATA = '05_raw_tistory_data'
    CRAWL_SESSIONS = 'crawl_sessions'
    
    # Refined data tables
    REFINED_WEB_DATA = '06_refined_web_data'
    INSTAGRAM_DATA = '07_instagram_data'
    REFINED_NAVER_DATA = '08_refined_naver_data'
    REFINED_TISTORY_DATA = '09_refined_tistory_data'
    REFINED_CONTENT = 'refined_content'
    CONTENT_SEGMENTS = 'content_segments'
    EXTRACTED_PRODUCTS_FROM_CONTENT = 'extracted_products_from_content'
    CONTENT_RELATIONSHIPS = 'content_relationships'
    REFINEMENT_LOGS = 'refinement_logs'
    
    # Keyword tables
    WEB_KEYWORD_TITLE = '10_web_keyword_title'
    WEB_KEYWORD_CLEANED_TEXT = '10_web_keyword_cleaned_text'
    KEYWORD_EXTRACTION_JOBS = 'keyword_extraction_jobs'
    EXTRACTED_KEYWORDS = 'extracted_keywords'
    KEYWORD_CLUSTERS = 'keyword_clusters'
    KEYWORD_CLUSTER_MEMBERS = 'keyword_cluster_members'
    KEYWORD_PERFORMANCE = 'keyword_performance'
    BRAND_KEYWORDS = 'brand_keywords'
    
    # Tracking tables
    PROCESSING_PIPELINE = 'processing_pipeline'
    STAGE_LOGS = 'stage_logs'
    API_USAGE_TRACKING = 'api_usage_tracking'
    COST_SUMMARY = 'cost_summary'
    SYSTEM_METRICS = 'system_metrics'
    ALERTS = 'alerts'

# Query timeout settings
QUERY_TIMEOUTS = {
    'default': 30,  # seconds
    'crawl': 60,
    'refine': 120,
    'extract': 90,
    'optimize': 180
}