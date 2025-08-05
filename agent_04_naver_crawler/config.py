import os
from pathlib import Path
from dotenv import load_dotenv

# 상위 디렉토리에서 환경 변수 로드
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Config:
    """네이버 블로그 크롤러 설정"""
    
    # 크롤러 버전
    CRAWLER_VERSION = "1.0.0"
    
    # 크롤링 설정
    MAX_PAGES_PER_BRAND = int(os.getenv("NAVER_MAX_PAGES", "10"))
    POSTS_PER_PAGE = int(os.getenv("NAVER_POSTS_PER_PAGE", "10"))
    CRAWL_DELAY = float(os.getenv("NAVER_CRAWL_DELAY", "0.5"))
    PAGE_DELAY = float(os.getenv("NAVER_PAGE_DELAY", "1.0"))
    REQUEST_TIMEOUT = int(os.getenv("NAVER_REQUEST_TIMEOUT", "10"))
    
    # 데이터베이스 설정 (메인 .env에서 가져옴)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "modular_agents_db")
    
    # 경로
    PROJECT_ROOT = Path(__file__).parent
    LOG_DIR = PROJECT_ROOT / "logs"
    
    @classmethod
    def ensure_directories(cls):
        """필요한 디렉토리가 모두 존재하는지 확인"""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)